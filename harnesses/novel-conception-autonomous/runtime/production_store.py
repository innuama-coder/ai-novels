"""Durable control-plane storage for the production conception runner.

The portable coordinator deliberately keeps state in memory.  This store is
the single persistence owner used by the production orchestrator: snapshots
remain append-only, a mutable pointer is only a cache, and recovery always
rebuilds the hash-linked chain before selecting the latest revision.
"""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Mapping

from .canonical import canonical_json, canonical_sha256, sha256_file
from .contracts import ContractRuntime, ContractValidationError
from .coordinator import AutonomousCoordinator, CoordinatorError, SealedDocument
from .production_coordinator import ProductionCoordinator


class ProductionStoreError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise ProductionStoreError(code, message)


class ProductionRunStore:
    """Append-only state/workspace store rooted in one run directory."""

    def __init__(self, root: str | Path, *, runtime: ContractRuntime | None = None):
        self.root = Path(root).resolve()
        self.runtime = runtime or ContractRuntime()

    def _path(self, logical: str) -> Path:
        pure = PurePosixPath(logical)
        if pure.is_absolute() or not pure.parts or ".." in pure.parts:
            _fail("PROD_PATH_INVALID", logical)
        candidate = self.root / Path(*pure.parts)
        target = self._without_windows_extended_prefix(
            self.physical_path(candidate).resolve()
        )
        try:
            target.relative_to(self.root)
        except ValueError:
            _fail("PROD_PATH_ESCAPE", logical)
        return target

    @staticmethod
    def _without_windows_extended_prefix(path: str | Path) -> Path:
        raw = str(path)
        if raw.startswith("\\\\?\\UNC\\"):
            return Path("\\\\" + raw[8:])
        if raw.startswith("\\\\?\\"):
            return Path(raw[4:])
        return Path(raw)

    def physical_path(self, path: str | Path) -> Path:
        """Return the filesystem spelling used for every package I/O.

        Windows' normal namespace reports false negatives once an attempt
        workspace exceeds MAX_PATH.  Logical references never contain this
        prefix; it exists only at the physical I/O boundary.
        """

        candidate = Path(path)
        if os.name != "nt" or str(candidate).startswith("\\\\?\\"):
            return candidate
        if not candidate.is_absolute():
            candidate = self.root / candidate
        raw = str(candidate.absolute())
        if raw.startswith("\\\\"):
            return Path("\\\\?\\UNC\\" + raw[2:])
        return Path("\\\\?\\" + raw)

    def resolve_physical_path(self, path: str | Path) -> Path:
        """Resolve one physical candidate and prove it remains in this run."""

        resolved = self.physical_path(path).resolve()
        normal = self._without_windows_extended_prefix(resolved)
        try:
            normal.relative_to(self.root)
        except ValueError:
            _fail("PROD_PATH_ESCAPE", str(path))
        return normal

    def physical_exists(self, path: str | Path) -> bool:
        return os.path.lexists(str(self.physical_path(path)))

    def physical_is_file(self, path: str | Path) -> bool:
        physical = self.physical_path(path)
        return os.path.lexists(str(physical)) and physical.is_file()

    def physical_sha256(self, path: str | Path) -> str:
        return sha256_file(self.physical_path(path))

    def physical_read_text(self, path: str | Path) -> str:
        return self.physical_path(path).read_text(encoding="utf-8")

    def _document_candidate_paths(self, logical: str) -> tuple[Path, ...]:
        """Return the only physical locations allowed for one logical ref.

        Stage owners may publish an attempt-qualified logical package such as
        ``E1/attempt-11/stage-completion.json`` while the durable worker
        workspace is ``workspaces/E1-attempt-11/package``.  The mapping is
        structural and deliberately narrow; arbitrary workspace discovery is
        never used as provenance.
        """

        direct = self._path(logical)
        pure = PurePosixPath(logical)
        candidates = [direct]
        if (
            len(pure.parts) >= 3
            and re.fullmatch(r"[A-Z][0-9]", pure.parts[0]) is not None
            and re.fullmatch(r"attempt-[a-z0-9]+(?:-[a-z0-9]+)*", pure.parts[1])
            is not None
        ):
            stage, attempt, *tail = pure.parts
            workspace = self._path(
                PurePosixPath(
                    "workspaces", f"{stage}-{attempt}", "package", *tail
                ).as_posix()
            )
            if workspace != direct:
                candidates.append(workspace)
        return tuple(candidates)

    def resolve_document_path(self, reference: Mapping[str, str]) -> Path:
        """Resolve a sealed logical reference to one unambiguous physical file.

        Both a legacy in-place package and an attempt workspace remain valid,
        but two extant roots are rejected even when their bytes agree.  This
        prevents a shadow package from silently changing provenance.
        """

        logical = reference.get("path")
        digest = reference.get("sha256")
        if (
            not isinstance(logical, str)
            or not isinstance(digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None
        ):
            _fail("PROD_DOCUMENT_REFERENCE_INVALID", str(reference))
        pure = PurePosixPath(logical)
        stage = reference.get("stage")
        workspace_stage = None
        if (
            len(pure.parts) >= 4
            and pure.parts[0] == "workspaces"
            and pure.parts[2] == "package"
        ):
            match = re.fullmatch(
                r"([A-Z][0-9])-attempt-[a-z0-9]+(?:-[a-z0-9]+)*",
                pure.parts[1],
            )
            if match is not None:
                workspace_stage = match.group(1)
        if (
            stage is not None
            and (
                not isinstance(stage, str)
                or not pure.parts
                or (pure.parts[0] != stage and workspace_stage != stage)
            )
        ):
            _fail("PROD_PACKAGE_PROVENANCE_INVALID", str(reference))
        extant = [
            path
            for path in self._document_candidate_paths(logical)
            if self.physical_exists(path)
        ]
        if len(extant) > 1:
            # A committed stage completion is also persisted at its logical
            # control-plane path.  Treat that singleton as a mirror only when
            # exactly one candidate root proves the completion's manifest and
            # validation sibling chain.  Two complete roots remain ambiguous.
            package_roots = [
                path
                for path in extant
                if self._completion_root_has_bound_siblings(path, logical)
            ]
            if len(package_roots) == 1:
                extant = package_roots
            else:
                _fail("PROD_DOCUMENT_ROOT_AMBIGUOUS", logical)
        if len(extant) != 1:
            _fail("PROD_DOCUMENT_STALE", str(reference))
        path = extant[0]
        if not self.physical_is_file(path) or self.physical_sha256(path) != digest:
            _fail("PROD_DOCUMENT_STALE", str(reference))
        return path

    def resolve_completion_package_root(
        self, reference: Mapping[str, str], *, expected_stage: str
    ) -> Path:
        """Resolve one ready completion to its uniquely sealed package root.

        The completion, manifest, and validation must be same-parent siblings
        in both the logical namespace and the physical namespace.  This is the
        only supported bridge from a gate/state completion reference to a
        worker's physical package input.
        """

        completion = self.load_document(reference)
        completion_path = self.resolve_document_path(reference)
        logical_root = PurePosixPath(reference.get("path", "")).parent
        if (
            completion.data.get("stage") != expected_stage
            or completion.data.get("status") != "ready"
            or reference.get("stage") not in {None, expected_stage}
        ):
            _fail("PROD_COMPLETION_STAGE_INVALID", str(reference))
        for field, filename in (
            ("manifest", "package-manifest.json"),
            ("validation", "validation.json"),
        ):
            sibling_reference = completion.data.get(field)
            if not isinstance(sibling_reference, Mapping):
                _fail("PROD_COMPLETION_SIBLING_MISSING", f"{expected_stage}:{field}")
            sibling_logical = PurePosixPath(sibling_reference.get("path", ""))
            if (
                sibling_logical.name != filename
                or sibling_logical.parent != logical_root
            ):
                _fail("PROD_COMPLETION_SIBLING_INVALID", f"{expected_stage}:{field}")
            sibling = self.load_document(sibling_reference)
            sibling_path = self.resolve_document_path(sibling_reference)
            if sibling_path.parent != completion_path.parent:
                _fail("PROD_COMPLETION_SIBLING_INVALID", f"{expected_stage}:{field}")
            if field == "manifest" and (
                sibling.data.get("stage") != expected_stage
                or sibling.data.get("verdict") != "ready"
            ):
                _fail("PROD_COMPLETION_MANIFEST_INVALID", expected_stage)
            if field == "validation" and sibling.data.get(
                "verdict", sibling.data.get("status")
            ) != "ready":
                _fail("PROD_COMPLETION_VALIDATION_INVALID", expected_stage)
        return self.physical_path(completion_path.parent)

    def _completion_root_has_bound_siblings(self, path: Path, logical: str) -> bool:
        if path.name != "stage-completion.json":
            return False
        try:
            body = json.loads(self.physical_read_text(path))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return False
        logical_root = PurePosixPath(logical).parent
        for key in ("manifest", "validation"):
            reference = body.get(key)
            if not isinstance(reference, Mapping):
                return False
            sibling_logical = reference.get("path")
            sibling_digest = reference.get("sha256")
            if not isinstance(sibling_logical, str) or not isinstance(
                sibling_digest, str
            ):
                return False
            sibling_pure = PurePosixPath(sibling_logical)
            if sibling_pure.parent == logical_root:
                relative = PurePosixPath(sibling_pure.name)
            elif len(sibling_pure.parts) == 1:
                relative = sibling_pure
            else:
                return False
            sibling = path.parent / Path(*relative.parts)
            if (
                not self.physical_is_file(sibling)
                or self.physical_sha256(sibling) != sibling_digest
            ):
                return False
        return True

    @contextmanager
    def lock(self) -> Iterator[None]:
        """Take an OS-held exclusive lock which is released on process death."""

        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / "orchestration" / "run.lock"
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = path.open("a+b")
        try:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
        finally:
            if os.name == "nt":
                import msvcrt

                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()

    def _write_new(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            if path.read_bytes() != data:
                _fail("PROD_IMMUTABLE_CONFLICT", str(path))

    def preflight_immutable_documents(
        self, documents: Iterator[SealedDocument] | list[SealedDocument] | tuple[SealedDocument, ...]
    ) -> None:
        """Prove an entire append-only write set before its first write."""

        planned: dict[Path, bytes] = {}
        for document in documents:
            body = canonical_json(document.data).encode("utf-8")
            if canonical_sha256(document.data) != document.reference.get("sha256"):
                _fail("PROD_DOCUMENT_HASH_MISMATCH", str(document.reference))
            path = self._path(str(document.reference.get("path")))
            prior = planned.get(path)
            if prior is not None and prior != body:
                _fail("PROD_IMMUTABLE_CONFLICT", str(path))
            planned[path] = body
        for path, body in planned.items():
            if path.exists() and (not path.is_file() or path.read_bytes() != body):
                _fail("PROD_IMMUTABLE_CONFLICT", str(path))

    def _replace(self, path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        body = canonical_json(value).encode("utf-8")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def persist_document(self, document: SealedDocument) -> Path:
        if canonical_sha256(document.data) != document.reference.get("sha256"):
            _fail("PROD_DOCUMENT_HASH_MISMATCH", str(document.reference))
        path = self._path(str(document.reference["path"]))
        self._write_new(path, canonical_json(document.data).encode("utf-8"))
        if sha256_file(path) != document.reference["sha256"]:
            _fail("PROD_DOCUMENT_WRITE_MISMATCH", str(path))
        return path

    def persist_state(self, document: SealedDocument) -> Path:
        self.runtime.validate(document.data, "autonomous-run-state.schema.json")
        revision = int(document.data["revision"])
        expected = f"state/revision-{revision:03d}.json"
        if document.reference.get("path") != expected:
            _fail("PROD_STATE_PATH_INVALID", str(document.reference.get("path")))
        path = self.persist_document(document)
        self._replace(
            self.root / "orchestration" / "current-state.json",
            {"schema_version": "2.0", "state": dict(document.reference)},
        )
        return path

    def ensure_uninitialized(self) -> None:
        """Reject every pre-existing run; an empty caller-created root is fine."""

        allowed_lock = self.root / "orchestration" / "run.lock"
        residue = [
            path
            for path in self.root.rglob("*")
            if path != allowed_lock
            and not (path.is_dir() and path == allowed_lock.parent)
        ]
        if residue:
            _fail("PROD_RUN_EXISTS", str(self.root))

    def load_document(self, reference: Mapping[str, str]) -> SealedDocument:
        path = self.resolve_document_path(reference)
        data = json.loads(self.physical_read_text(path))
        if canonical_sha256(data) != reference["sha256"]:
            _fail("PROD_DOCUMENT_NONCANONICAL", str(path))
        return SealedDocument(data=data, reference=dict(reference))

    def latest_state(self) -> SealedDocument:
        def revision_of(path: Path) -> int:
            try:
                return int(path.stem.split("-")[-1])
            except ValueError:
                _fail("PROD_STATE_FILENAME_INVALID", path.name)

        files = sorted(
            (self.root / "state").glob("revision-*.json"), key=revision_of
        )
        if not files:
            _fail("PROD_STATE_MISSING", str(self.root))
        previous: SealedDocument | None = None
        for expected_revision, path in enumerate(files):
            try:
                revision = int(path.stem.split("-")[-1])
            except ValueError:
                _fail("PROD_STATE_FILENAME_INVALID", path.name)
            if revision != expected_revision:
                _fail("PROD_STATE_CHAIN_GAP", path.name)
            data = json.loads(path.read_text(encoding="utf-8"))
            try:
                self.runtime.validate(data, "autonomous-run-state.schema.json")
            except ContractValidationError as error:
                _fail("PROD_STATE_SCHEMA_INVALID", str(error))
            reference = {
                "path": f"state/revision-{revision:03d}.json",
                "sha256": sha256_file(path),
            }
            if canonical_sha256(data) != reference["sha256"]:
                _fail("PROD_STATE_NONCANONICAL", path.name)
            if revision == 0:
                if data["previous_state"] is not None:
                    _fail("PROD_STATE_CHAIN_INVALID", path.name)
            elif previous is None or data["previous_state"] != previous.reference:
                _fail("PROD_STATE_CHAIN_INVALID", path.name)
            previous = SealedDocument(data=data, reference=reference)
        assert previous is not None
        return previous

    def persist_workspace(self, workspace: SealedDocument) -> Path:
        self.runtime.validate(workspace.data, "h1-workspace-state.schema.json")
        path = self.persist_document(workspace)
        self._replace(
            self.root / "orchestration" / "current-h1-workspace.json",
            {"schema_version": "2.0", "workspace": workspace.reference},
        )
        return path

    def latest_workspace(self) -> SealedDocument:
        pointer = self.root / "orchestration" / "current-h1-workspace.json"
        if not pointer.is_file():
            _fail("PROD_H1_WORKSPACE_MISSING", str(pointer))
        value = json.loads(pointer.read_text(encoding="utf-8"))
        return self.load_document(value["workspace"])

    def issue_work_order(
        self,
        *,
        run_id: str,
        action: str,
        state: SealedDocument,
        input_gate: SealedDocument | None,
        h1_workspace: SealedDocument | None,
        required_actor: str,
        inputs: Mapping[str, Any],
    ) -> SealedDocument:
        body = {
            "schema_version": "2.0",
            "run_id": run_id,
            "action": action,
            "state": dict(state.reference),
            "input_gate": (
                dict(input_gate.reference) if input_gate is not None else None
            ),
            "h1_workspace": (
                dict(h1_workspace.reference)
                if h1_workspace is not None
                else None
            ),
            "required_actor": required_actor,
            "inputs": dict(inputs),
            "status": "pending",
        }
        work_id = canonical_sha256(body)[:24]
        document = SealedDocument(
            data={**body, "work_id": work_id},
            reference={
                "path": f"orchestration/work-orders/{work_id}.json",
                "sha256": canonical_sha256({**body, "work_id": work_id}),
            },
        )
        pointer_path = self.root / "orchestration" / "current-work-order.json"
        if pointer_path.is_file():
            pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
            prior = self.load_document(pointer["work_order"])
            consumed = self.root / "orchestration" / "work-orders" / (
                f"{prior.data['work_id']}.consumed.json"
            )
            rejected = self.root / "orchestration" / "work-orders" / (
                f"{prior.data['work_id']}.rejected.json"
            )
            if not consumed.exists() and not rejected.exists():
                if prior.reference == document.reference and prior.data == document.data:
                    return prior
                _fail("PROD_PENDING_WORK_EXISTS", prior.data["work_id"])
        self.persist_document(document)
        self._replace(
            self.root / "orchestration" / "current-work-order.json",
            {"schema_version": "2.0", "work_order": document.reference},
        )
        return document

    def pending_work_order(self) -> SealedDocument | None:
        """Return the current unconsumed work order, if one exists."""

        current = self.root / "orchestration" / "current-work-order.json"
        if not current.is_file():
            return None
        pointer = json.loads(current.read_text(encoding="utf-8"))
        order = self.load_document(pointer["work_order"])
        consumed = self.root / "orchestration" / "work-orders" / (
            f"{order.data['work_id']}.consumed.json"
        )
        rejected = self.root / "orchestration" / "work-orders" / (
            f"{order.data['work_id']}.rejected.json"
        )
        if consumed.is_file():
            return None
        trusted = self.trusted_contract_upgrade_markers()
        rejected_logical = rejected.relative_to(self.root).as_posix()
        if rejected.is_file():
            if rejected_logical not in trusted["work_order_rejections"]:
                _fail("PROD_UNTRUSTED_PROCESSED_MARKER", rejected_logical)
            return None
        return order

    def _validate_bootstrap_qualification(self, receipt: SealedDocument) -> None:
        legacy_fields = {
            "schema_version", "migration_id", "reason",
            "old_contract_digest", "new_contract_digest",
            "invalidated_stages", "production_versions",
            "session_invalidation_receipts",
            "work_order_invalidation_receipts",
            "completion_invalidation_receipts", "status",
        }
        expected_fields = legacy_fields | {"production_contract"}
        versions = receipt.data.get("production_versions")
        digest = receipt.data.get("new_contract_digest")
        production_contract = receipt.data.get("production_contract")
        expected_id = canonical_sha256(
            ["contract_bootstrap", digest, versions]
        )[:24]
        if (
            frozenset(receipt.data)
            not in {frozenset(legacy_fields), frozenset(expected_fields)}
            or receipt.data.get("schema_version") != "1.0"
            or receipt.data.get("reason") != "contract_bootstrap"
            or receipt.data.get("status") != "complete"
            or not isinstance(digest, str)
            or receipt.data.get("old_contract_digest") != digest
            or not isinstance(versions, Mapping)
            or set(versions) != {"E1", "T1"}
            or not all(isinstance(value, str) and value for value in versions.values())
            or receipt.data.get("invalidated_stages") != []
            or any(
                receipt.data.get(field) != []
                for field in (
                    "session_invalidation_receipts",
                    "work_order_invalidation_receipts",
                    "completion_invalidation_receipts",
                )
            )
            or receipt.data.get("migration_id") != expected_id
            or receipt.reference.get("path") != (
                f"orchestration/contract-upgrades/{expected_id}.complete.json"
            )
            or (
                "production_contract" in receipt.data
                and (
                    not isinstance(production_contract, Mapping)
                    or canonical_sha256(production_contract) != digest
                    or any(
                        not isinstance(production_contract.get(stage), Mapping)
                        or production_contract[stage].get("model_schema_version")
                        != versions.get(stage)
                        for stage in ("E1", "T1")
                    )
                )
            )
        ):
            _fail(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                receipt.reference.get("path", "bootstrap"),
            )

    def _validate_upgrade_transaction_replay(
        self,
        receipt: SealedDocument,
        *,
        state_references: Mapping[str, Mapping[str, str]],
        successor_override: SealedDocument | None = None,
    ) -> tuple[SealedDocument, tuple[SealedDocument, ...], bool]:
        """Validate and replay one reachable qualification transaction."""

        legacy_receipt_fields = {
            "schema_version", "migration_id", "reason", "plan",
            "predecessor_state", "successor_state", "return_request",
            "old_contract_digest", "new_contract_digest",
            "invalidated_stages", "production_versions",
            "session_invalidation_receipts",
            "work_order_invalidation_receipts",
            "completion_invalidation_receipts", "status",
        }
        legacy_plan_fields = {
            "schema_version", "migration_id", "reason", "predecessor_state",
            "successor_state", "successor_snapshot", "return_request",
            "old_contract_digest", "new_contract_digest", "invalidated_stages",
            "production_versions", "session_references", "work_order_references",
            "completion_references", "pending_work_order",
            "pending_commit_intent", "status",
        }
        try:
            plan = self.load_document(receipt.data["plan"])
            predecessor = self.load_document(plan.data["predecessor_state"])
            successor = successor_override or self.load_document(
                plan.data["successor_state"]
            )
            request = self.load_document(plan.data["return_request"])
        except (ProductionStoreError, KeyError, TypeError) as error:
            _fail(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                f"{receipt.reference.get('path')}: {error}",
            )
        if (
            state_references.get(predecessor.reference["path"])
            != predecessor.reference
            or (
                state_references.get(successor.reference["path"])
                != successor.reference
                and successor_override is None
            )
            or plan.data.get("predecessor_state") != predecessor.reference
            or plan.data.get("successor_state") != successor.reference
            or plan.data.get("successor_snapshot") != successor.data
            or successor.data.get("previous_state") != predecessor.reference
            or successor.data.get("revision") != predecessor.data.get("revision", -2) + 1
            or predecessor.reference == successor.reference
            or receipt.data.get("predecessor_state") != predecessor.reference
            or receipt.data.get("successor_state") != successor.reference
            or receipt.data.get("return_request") != request.reference
        ):
            _fail(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                receipt.reference["path"],
            )
        modern = "transition_mode" in receipt.data or "transition_mode" in plan.data
        if modern:
            try:
                replay_plan, legacy_refresh_shape = (
                    self._normalize_contract_upgrade_plan_for_replay(plan)
                )
            except ProductionStoreError as error:
                _fail(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    f"{receipt.reference['path']}: {error.code}",
                )
            mode = replay_plan.data["transition_mode"]
        else:
            if set(receipt.data) != legacy_receipt_fields or set(plan.data) != legacy_plan_fields:
                _fail(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    receipt.reference["path"],
                )
            replay_plan = plan
            legacy_refresh_shape = None
            mode = "new_return"
        expected_migration_id = canonical_sha256(
            [
                predecessor.reference,
                request.reference,
                plan.data.get("old_contract_digest"),
                plan.data.get("new_contract_digest"),
            ]
        )[:24]
        if (
            plan.data.get("migration_id") != expected_migration_id
            or receipt.data.get("migration_id") != expected_migration_id
            or plan.reference.get("path") != (
                "orchestration/contract-upgrades/"
                f"{expected_migration_id}.prepared.json"
            )
            or receipt.reference.get("path") != (
                "orchestration/contract-upgrades/"
                f"{expected_migration_id}.complete.json"
            )
        ):
            _fail(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                receipt.reference["path"],
            )
        active_reference = predecessor.data.get("active_return")
        if (
            (
                mode in {
                    "new_return", "stage_return", "internal_h1_fragment_return",
                    "internal_h1_readability_return"
                }
                and active_reference is not None
            )
            or (
                mode == "active_return_refresh"
                and active_reference != request.reference
            )
            or (
                mode == "active_return_escalation"
                and active_reference != replay_plan.data.get("superseded_return")
            )
            or (
                mode == "active_stage_return_refresh"
                and active_reference != replay_plan.data.get("superseded_return")
            )
            or (
                mode == "internal_h1_html_readability_return"
                and active_reference != replay_plan.data.get("superseded_return")
            )
        ):
            _fail(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                receipt.reference["path"],
            )
        try:
            active_request = request
            if mode in {
                "active_return_escalation",
                "active_stage_return_refresh",
                "internal_h1_html_readability_return",
            }:
                active_request = self.load_document(
                    replay_plan.data["superseded_return"]
                )
            coordinator_type = (
                ProductionCoordinator
                if mode in {
                    "active_stage_return_refresh",
                    "internal_h1_html_readability_return",
                }
                else AutonomousCoordinator
            )
            coordinator = coordinator_type.from_snapshot(
                predecessor.data,
                predecessor.reference,
                active_return_request=(
                    active_request if active_reference is not None else None
                ),
                runtime=self.runtime,
            )
            if mode == "active_return_refresh":
                transition = coordinator.refresh_active_return(
                    request=request,
                    next_state_path=successor.reference["path"],
                )
            elif mode == "active_return_escalation":
                transition = coordinator.supersede_active_return(
                    request=request,
                    next_state_path=successor.reference["path"],
                )
            elif mode == "active_stage_return_refresh":
                transition = coordinator.refresh_active_stage_return(
                    request=request,
                    next_state_path=successor.reference["path"],
                )
            elif mode == "internal_h1_html_readability_return":
                transition = coordinator.narrow_active_h1_return(
                    request=request,
                    next_state_path=successor.reference["path"],
                )
            else:
                transition = coordinator.apply_return_request(
                    request=request,
                    next_state_path=successor.reference["path"],
                )
        except CoordinatorError as error:
            _fail(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                f"{receipt.reference['path']}: {error.code}",
            )
        if transition.snapshot != successor.data or transition.reference != successor.reference:
            _fail(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                receipt.reference["path"],
            )
        if mode in {
            "active_return_escalation",
            "active_stage_return_refresh",
            "stage_return",
            "internal_h1_fragment_return",
            "internal_h1_readability_return",
            "internal_h1_html_readability_return",
        }:
            post = [
                SealedDocument(data=dict(item["data"]), reference=dict(item["reference"]))
                for item in replay_plan.data.get("post_upgrade_documents", [])
            ]
            gates = [
                item for item in post
                if item.reference["path"].startswith("orchestration/input-gates/")
            ]
            orders = [
                item for item in post
                if item.reference == replay_plan.data.get("post_upgrade_work_order")
            ]
            if len(gates) != 1 or len(orders) != 1:
                _fail(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    receipt.reference["path"],
                )
            try:
                expected_gate = coordinator.build_input_gate(
                    replay_plan.data["target_stage"],
                    gates[0].reference["path"],
                    active_return_request=request,
                )
            except CoordinatorError as error:
                _fail(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    f"{receipt.reference['path']}: {error.code}",
                )
            order = orders[0]
            expected_action = replay_plan.data["target_stage"]
            h1_implementation_refresh = (
                mode == "active_stage_return_refresh"
                and expected_action == "H1"
                and isinstance(
                    replay_plan.data["stale_identity"].get(
                        "initialized_workspace"
                    ),
                    Mapping,
                )
            )
            if mode in {
                "stage_return", "internal_h1_fragment_return",
                "internal_h1_readability_return",
                "internal_h1_html_readability_return",
            } and expected_action == "H1" or h1_implementation_refresh:
                expected_action = replay_plan.data["stale_identity"].get(
                    "resume_point"
                )
            order_core = {
                key: value for key, value in order.data.items() if key != "work_id"
            }
            expected_work_id = canonical_sha256(order_core)[:24]
            if (
                gates[0] != expected_gate
                or order.data.get("schema_version") != "2.0"
                or order.data.get("run_id") != successor.data.get("run_id")
                or order.data.get("action") != expected_action
                or order.data.get("state") != successor.reference
                or order.data.get("input_gate") != expected_gate.reference
                or (
                    order.data.get("h1_workspace")
                    != replay_plan.data["stale_identity"].get(
                        "restored_workspace",
                        replay_plan.data["stale_identity"].get(
                            "planned_workspace",
                            replay_plan.data["stale_identity"].get(
                                "initialized_workspace"
                            ),
                        ),
                    )
                    if mode in {
                        "internal_h1_fragment_return",
                        "internal_h1_readability_return",
                        "internal_h1_html_readability_return",
                    } or h1_implementation_refresh
                    else order.data.get("h1_workspace") is not None
                )
                or not isinstance(order.data.get("required_actor"), str)
                or not isinstance(order.data.get("inputs"), Mapping)
                or order.data.get("status") != "pending"
                or order.data.get("work_id") != expected_work_id
                or order.reference["path"]
                != f"orchestration/work-orders/{expected_work_id}.json"
            ):
                _fail(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    receipt.reference["path"],
                )
        expected, derived = self.build_contract_upgrade_completion(
            replay_plan, successor=successor
        )
        if modern:
            if not self._contract_upgrade_receipt_matches_replay_shape(
                receipt,
                expected,
                legacy_refresh_shape=legacy_refresh_shape,
            ):
                _fail(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    receipt.reference["path"],
                )
        elif not self._contract_upgrade_receipt_matches(receipt, expected):
            _fail(
                "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                receipt.reference["path"],
            )
        return expected, derived, modern

    def _normalize_contract_upgrade_plan_for_replay(
        self, plan: SealedDocument
    ) -> tuple[SealedDocument, str | None]:
        """Expand only exact published refresh shapes with current no-op fields."""

        current_fields = {
            "schema_version", "migration_id", "reason", "predecessor_state",
            "successor_state", "successor_snapshot", "return_request",
            "old_contract_digest", "new_contract_digest", "invalidated_stages",
            "production_versions", "session_references", "work_order_references",
            "completion_references", "pending_work_order",
            "pending_commit_intent", "transition_mode", "refresh_generation",
            "prior_qualification", "target_stage", "stale_identity",
            "production_contract", "inventory_sha256", "superseded_return",
            "status", "post_upgrade_documents", "post_upgrade_work_order",
            "post_upgrade_inputs",
        }
        legacy_shapes = {
            frozenset({"post_upgrade_inputs"}): (
                "refresh-without-post-inputs",
                {"post_upgrade_inputs": None},
            ),
            frozenset({
                "superseded_return",
                "post_upgrade_documents",
                "post_upgrade_work_order",
                "post_upgrade_inputs",
            }): (
                "refresh-before-escalation-fields",
                {
                    "superseded_return": None,
                    "post_upgrade_documents": [],
                    "post_upgrade_work_order": None,
                    "post_upgrade_inputs": None,
                },
            ),
        }
        observed_fields = set(plan.data)
        missing = frozenset(current_fields - observed_fields)
        if observed_fields - current_fields:
            _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))

        normalized = dict(plan.data)
        legacy_shape: str | None = None
        if missing:
            legacy = legacy_shapes.get(missing)
            if legacy is None:
                _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
            legacy_shape, defaults = legacy
            if (
                plan.data.get("transition_mode") != "active_return_refresh"
                or plan.data.get("refresh_generation") != 1
                or canonical_sha256(plan.data) != plan.reference.get("sha256")
            ):
                _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
            normalized.update(defaults)

        validated = self.build_contract_upgrade_plan(normalized)
        if validated.data != normalized:
            _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
        if legacy_shape is None and validated.reference != plan.reference:
            _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
        return SealedDocument(
            data=validated.data,
            reference=dict(plan.reference),
        ), legacy_shape

    @staticmethod
    def _contract_upgrade_receipt_matches_replay_shape(
        receipt: SealedDocument,
        expected: SealedDocument,
        *,
        legacy_refresh_shape: str | None,
    ) -> bool:
        """Compare one receipt against an exact current or published shape."""

        if receipt.reference.get("path") != expected.reference.get("path"):
            return False
        if legacy_refresh_shape is None:
            return receipt.data == expected.data and receipt.reference == expected.reference

        omissions_by_shape = {
            "refresh-without-post-inputs": frozenset(),
            "refresh-before-escalation-fields": frozenset({
                "superseded_return",
                "post_upgrade_documents",
                "post_upgrade_work_order",
            }),
        }
        omissions = omissions_by_shape.get(legacy_refresh_shape)
        if omissions is None:
            return False
        allowed_field_sets = {
            frozenset(expected.data) - omissions,
            frozenset(expected.data),
        }
        if frozenset(receipt.data) not in allowed_field_sets:
            return False
        return all(
            receipt.data[field] == expected.data[field]
            for field in receipt.data
        )

    def _scan_untrusted_processed_markers(
        self, trusted: Mapping[str, Any]
    ) -> None:
        marker_patterns = {
            "work_order_rejections": "orchestration/work-orders/*.rejected.json",
            "session_invalidations": "orchestration/session-invalidations/*.json",
            "completion_invalidations": "orchestration/completion-invalidations/*.json",
            "intent_abandonments": "orchestration/commit-intents/*.abandoned.json",
        }
        for category, pattern in marker_patterns.items():
            for path in self.root.glob(pattern):
                logical = path.relative_to(self.root).as_posix()
                if logical not in trusted[category]:
                    _fail("PROD_UNTRUSTED_PROCESSED_MARKER", logical)

    @staticmethod
    def _allow_upgrade_marker(
        trusted: dict[str, Any], item: SealedDocument
    ) -> None:
        logical = item.reference["path"]
        if logical.endswith(".rejected.json"):
            category = "work_order_rejections"
        elif "session-invalidations" in logical:
            category = "session_invalidations"
            trusted["invalidated_sessions"].add(
                (item.data["session"]["path"], item.data["session"]["sha256"])
            )
        elif "completion-invalidations" in logical:
            category = "completion_invalidations"
        elif logical.endswith(".abandoned.json"):
            category = "intent_abandonments"
        else:
            return
        trusted[category][logical] = dict(item.reference)

    def trusted_contract_upgrade_markers(
        self, *, scan_orphans: bool = True
    ) -> dict[str, Any]:
        """Resolve processed markers only from exact, state-bound receipts."""

        trusted: dict[str, Any] = {
            "work_order_rejections": {},
            "session_invalidations": {},
            "completion_invalidations": {},
            "intent_abandonments": {},
            "invalidated_sessions": set(),
        }
        self.latest_state()
        state_references = {
            f"state/{path.name}": {
                "path": f"state/{path.name}",
                "sha256": sha256_file(path),
            }
            for path in (self.root / "state").glob("revision-*.json")
        }
        current = self.current_contract_upgrade()
        explicit_chain: set[tuple[str, str]] = set()
        chain: list[SealedDocument] = []
        cursor = current
        while cursor is not None:
            key = (cursor.reference["path"], cursor.reference["sha256"])
            if key in explicit_chain:
                _fail("PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", key[0])
            explicit_chain.add(key)
            chain.append(cursor)
            prior = cursor.data.get("prior_qualification")
            if isinstance(prior, Mapping):
                try:
                    cursor = self.load_document(prior)
                except ProductionStoreError as error:
                    _fail(
                        "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                        f"{key[0]}: {error.code}",
                    )
            elif prior is None:
                cursor = None
            else:
                _fail("PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", key[0])

        for index, receipt in enumerate(chain):
            key = (receipt.reference["path"], receipt.reference["sha256"])
            if receipt.data.get("reason") == "contract_bootstrap":
                if index != len(chain) - 1:
                    _fail("PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", key[0])
                self._validate_bootstrap_qualification(receipt)
                continue
            if receipt.data.get("reason") != "contract_upgrade":
                _fail("PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", key[0])
            _expected, derived, modern = self._validate_upgrade_transaction_replay(
                receipt, state_references=state_references
            )
            if index + 1 < len(chain):
                prior = chain[index + 1]
                if (
                    receipt.data.get("prior_qualification") != prior.reference
                    or receipt.data.get("old_contract_digest")
                    != prior.data.get("new_contract_digest")
                    or (
                        receipt.data.get("transition_mode")
                        in {
                            "active_return_refresh",
                            "active_return_escalation",
                            "active_stage_return_refresh",
                            "stage_return",
                            "internal_h1_fragment_return",
                            "internal_h1_readability_return",
                            "internal_h1_html_readability_return",
                        }
                        and receipt.data.get("refresh_generation")
                        != prior.data.get("refresh_generation", 0) + 1
                    )
                ):
                    _fail("PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", key[0])
            elif modern:
                _fail("PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", key[0])
            for item in derived:
                logical = item.reference["path"]
                persisted = self.load_document(item.reference)
                if persisted.data != item.data:
                    _fail("PROD_PROCESSED_MARKER_INVALID", logical)
                self._allow_upgrade_marker(trusted, item)
        if scan_orphans:
            self._scan_untrusted_processed_markers(trusted)
        return trusted

    def build_contract_upgrade_plan(
        self, plan: Mapping[str, Any]
    ) -> SealedDocument:
        """Validate and seal a migration intent without writing it."""

        required = {
            "schema_version", "migration_id", "reason", "predecessor_state",
            "successor_state", "successor_snapshot", "return_request",
            "old_contract_digest", "new_contract_digest", "invalidated_stages",
            "production_versions", "session_references", "work_order_references",
            "completion_references", "pending_work_order",
            "pending_commit_intent", "transition_mode", "refresh_generation",
            "prior_qualification", "target_stage", "stale_identity",
            "production_contract", "inventory_sha256", "superseded_return", "status",
            "post_upgrade_documents", "post_upgrade_work_order",
            "post_upgrade_inputs",
        }
        inventory = {
            "session_references": plan.get("session_references"),
            "work_order_references": plan.get("work_order_references"),
            "completion_references": plan.get("completion_references"),
            "pending_work_order": plan.get("pending_work_order"),
            "pending_commit_intent": plan.get("pending_commit_intent"),
        }
        production_contract = plan.get("production_contract")
        production_versions = plan.get("production_versions")
        versions_match_contract = (
            isinstance(production_contract, Mapping)
            and isinstance(production_versions, Mapping)
            and all(
                isinstance(production_contract.get(stage), Mapping)
                and production_contract[stage].get("model_schema_version")
                == production_versions.get(stage)
                for stage in ("E1", "T1")
            )
        )
        if (
            set(plan) != required
            or plan.get("schema_version") != "1.0"
            or plan.get("reason") != "contract_upgrade"
            or plan.get("status") != "prepared"
            or plan.get("transition_mode")
            not in {
                "new_return",
                "active_return_refresh",
                "active_return_escalation",
                "active_stage_return_refresh",
                "stage_return",
                "internal_h1_fragment_return",
                "internal_h1_readability_return",
                "internal_h1_html_readability_return",
            }
            or not isinstance(plan.get("refresh_generation"), int)
            or plan.get("refresh_generation", -1) < 0
            or (
                plan.get("transition_mode") == "new_return"
                and plan.get("refresh_generation") != 0
            )
            or (
                plan.get("transition_mode") == "active_return_refresh"
                and (
                    plan.get("refresh_generation", 0) < 1
                    or not isinstance(plan.get("prior_qualification"), Mapping)
                )
            )
            or (
                plan.get("transition_mode") == "active_return_escalation"
                and (
                    plan.get("refresh_generation", 0) < 1
                    or not isinstance(plan.get("prior_qualification"), Mapping)
                    or not isinstance(plan.get("superseded_return"), Mapping)
                )
            )
            or (
                plan.get("transition_mode") == "active_stage_return_refresh"
                and (
                    plan.get("refresh_generation", 0) < 1
                    or not isinstance(plan.get("prior_qualification"), Mapping)
                    or not isinstance(plan.get("superseded_return"), Mapping)
                )
            )
            or (
                plan.get("transition_mode") in {
                    "stage_return", "internal_h1_fragment_return",
                    "internal_h1_readability_return",
                }
                and (
                    plan.get("refresh_generation", 0) < 1
                    or not isinstance(plan.get("prior_qualification"), Mapping)
                    or plan.get("superseded_return") is not None
                )
            )
            or (
                plan.get("transition_mode")
                == "internal_h1_html_readability_return"
                and (
                    plan.get("refresh_generation", 0) < 1
                    or not isinstance(plan.get("prior_qualification"), Mapping)
                    or not isinstance(plan.get("superseded_return"), Mapping)
                )
            )
            or (
                plan.get("transition_mode")
                not in {
                    "active_return_escalation",
                    "active_stage_return_refresh",
                    "stage_return",
                    "internal_h1_fragment_return",
                    "internal_h1_readability_return",
                    "internal_h1_html_readability_return",
                }
                and plan.get("target_stage") not in {"E1", "T1"}
            )
            or (
                plan.get("transition_mode")
                in {
                    "active_return_escalation",
                    "active_stage_return_refresh",
                    "stage_return",
                    "internal_h1_fragment_return",
                    "internal_h1_readability_return",
                    "internal_h1_html_readability_return",
                }
                and plan.get("target_stage")
                not in {"B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"}
            )
            or not isinstance(plan.get("stale_identity"), Mapping)
            or not isinstance(plan.get("production_contract"), Mapping)
            or not versions_match_contract
            or canonical_sha256(plan.get("production_contract"))
            != plan.get("new_contract_digest")
            or canonical_sha256(inventory) != plan.get("inventory_sha256")
            or canonical_sha256(plan.get("successor_snapshot"))
            != plan.get("successor_state", {}).get("sha256")
            or not isinstance(plan.get("post_upgrade_documents"), list)
            or (
                plan.get("transition_mode")
                not in {
                    "active_return_escalation",
                    "active_stage_return_refresh",
                    "stage_return",
                    "internal_h1_fragment_return",
                    "internal_h1_readability_return",
                    "internal_h1_html_readability_return",
                }
                and (
                    plan.get("post_upgrade_documents") != []
                    or plan.get("post_upgrade_work_order") is not None
                    or plan.get("post_upgrade_inputs") is not None
                )
            )
            or (
                plan.get("transition_mode")
                in {
                    "active_return_escalation",
                    "active_stage_return_refresh",
                    "stage_return",
                    "internal_h1_fragment_return",
                    "internal_h1_readability_return",
                    "internal_h1_html_readability_return",
                }
                and (
                    not isinstance(plan.get("post_upgrade_work_order"), Mapping)
                    or not isinstance(plan.get("post_upgrade_inputs"), Mapping)
                    or "_contract_qualification" in plan.get("post_upgrade_inputs", {})
                )
            )
        ):
            _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.get("migration_id")))
        post_documents: list[SealedDocument] = []
        for item in plan["post_upgrade_documents"]:
            if (
                not isinstance(item, Mapping)
                or set(item) != {"data", "reference"}
                or not isinstance(item.get("data"), Mapping)
                or not isinstance(item.get("reference"), Mapping)
                or set(item["reference"]) != {"path", "sha256"}
                or canonical_sha256(item["data"]) != item["reference"].get("sha256")
            ):
                _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.get("migration_id")))
            self._path(item["reference"].get("path", ""))
            post_documents.append(
                SealedDocument(data=dict(item["data"]), reference=dict(item["reference"]))
            )
        if plan["transition_mode"] in {
            "active_return_escalation",
            "active_stage_return_refresh",
            "stage_return",
            "internal_h1_fragment_return",
            "internal_h1_readability_return",
            "internal_h1_html_readability_return",
        }:
            pointer = plan["post_upgrade_work_order"]
            matching = [item for item in post_documents if item.reference == pointer]
            gates = [
                item for item in post_documents
                if item.reference["path"].startswith("orchestration/input-gates/")
            ]
            expected_inputs = dict(plan["post_upgrade_inputs"])
            expected_action = plan["target_stage"]
            h1_implementation_refresh = (
                plan["transition_mode"] == "active_stage_return_refresh"
                and plan["target_stage"] == "H1"
                and isinstance(
                    plan["stale_identity"].get("initialized_workspace"),
                    Mapping,
                )
            )
            if (
                plan["transition_mode"] in {
                    "stage_return", "internal_h1_fragment_return",
                    "internal_h1_readability_return",
                    "internal_h1_html_readability_return",
                }
                and plan["target_stage"] == "H1"
            ) or h1_implementation_refresh:
                expected_action = plan["stale_identity"].get("resume_point")
            if plan["target_stage"] in {"E1", "T1"}:
                prior = self.load_document(plan["prior_qualification"])
                versions = plan["production_versions"]
                expected_inputs["_contract_qualification"] = {
                    "contract_upgrade_receipt": dict(prior.reference),
                    "contract_digest": plan["new_contract_digest"],
                    "owner_stage": plan["target_stage"],
                    "owner_schema_version": versions[plan["target_stage"]],
                    "upstream_schema_versions": (
                        {"E1": versions["E1"]}
                        if plan["target_stage"] == "T1" else {}
                    ),
                }
            if (
                len(post_documents)
                != (
                    3
                    if (
                        plan["transition_mode"] == "internal_h1_readability_return"
                        or h1_implementation_refresh
                    )
                    else 2
                )
                or len(matching) != 1
                or len(gates) != 1
                or not matching[0].reference["path"].startswith(
                    "orchestration/work-orders/"
                )
                or matching[0].data.get("status") != "pending"
                or matching[0].data.get("state") != plan.get("successor_state")
                or matching[0].data.get("action") != expected_action
                or matching[0].data.get("input_gate") != gates[0].reference
                or (
                    matching[0].data.get("h1_workspace")
                    != plan["stale_identity"].get(
                        "restored_workspace",
                        plan["stale_identity"].get(
                            "planned_workspace",
                            plan["stale_identity"].get("initialized_workspace"),
                        ),
                    )
                    if plan["transition_mode"] in {
                        "internal_h1_fragment_return",
                        "internal_h1_readability_return",
                        "internal_h1_html_readability_return",
                    } or h1_implementation_refresh
                    else matching[0].data.get("h1_workspace") is not None
                )
                or not isinstance(matching[0].data.get("required_actor"), str)
                or matching[0].data.get("inputs") != expected_inputs
                or (
                    plan["transition_mode"] == "internal_h1_readability_return"
                    and len(
                        [
                            item for item in post_documents
                            if item.reference
                            == plan["stale_identity"].get("initialized_workspace")
                            and item.data.get("state") == "initialized"
                        ]
                    )
                    != 1
                )
                or (
                    h1_implementation_refresh
                    and len(
                        [
                            item for item in post_documents
                            if item.reference
                            == plan["stale_identity"].get(
                                "initialized_workspace"
                            )
                            and item.data.get("state") == "initialized"
                        ]
                    )
                    != 1
                )
            ):
                _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.get("migration_id")))
        document = SealedDocument(
            data=dict(plan),
            reference={
                "path": (
                    "orchestration/contract-upgrades/"
                    f"{plan['migration_id']}.prepared.json"
                ),
                "sha256": canonical_sha256(plan),
            },
        )
        return document

    def prepare_contract_upgrade(self, plan: Mapping[str, Any]) -> SealedDocument:
        """Persist an immutable migration intent before changing run-state."""

        document = self.build_contract_upgrade_plan(plan)
        self.persist_document(document)
        return document

    @staticmethod
    def _sealed_json(body: Mapping[str, Any], path: str) -> SealedDocument:
        data = dict(body)
        return SealedDocument(
            data=data,
            reference={"path": path, "sha256": canonical_sha256(data)},
        )

    def build_contract_upgrade_completion(
        self, plan: SealedDocument, *, successor: SealedDocument
    ) -> tuple[SealedDocument, tuple[SealedDocument, ...]]:
        """Purely derive every immutable receipt in one upgrade transaction."""

        if (
            plan.data.get("status") != "prepared"
            or plan.data.get("successor_state") != successor.reference
            or plan.data.get("successor_snapshot") != successor.data
        ):
            _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
        migration_id = plan.data["migration_id"]
        derived: list[SealedDocument] = []
        work_order_receipts: list[dict[str, str]] = []
        for pending in plan.data.get("work_order_references", []):
            order = self.load_document(pending)
            body = {
                "schema_version": "1.0",
                "migration_id": migration_id,
                "work_order": dict(pending),
                "reason": "contract_upgrade",
                "successor_state": dict(successor.reference),
                "status": "rejected",
            }
            document = self._sealed_json(
                body,
                f"orchestration/work-orders/{order.data['work_id']}.rejected.json",
            )
            derived.append(document)
            work_order_receipts.append(dict(document.reference))
        pending_intent = plan.data.get("pending_commit_intent")
        intent_receipts: list[dict[str, str]] = []
        if pending_intent is not None:
            intent = self.load_document(pending_intent)
            body = {
                "schema_version": "1.0",
                "migration_id": migration_id,
                "commit_intent": dict(pending_intent),
                "reason": "contract_upgrade",
                "successor_state": dict(successor.reference),
                "status": "abandoned",
            }
            work_id = Path(intent.reference["path"]).stem
            document = self._sealed_json(
                body,
                f"orchestration/commit-intents/{work_id}.abandoned.json",
            )
            derived.append(document)
            intent_receipts.append(dict(document.reference))
        session_receipts: list[dict[str, str]] = []
        for reference in plan.data["session_references"]:
            body = {
                "schema_version": "1.0",
                "migration_id": migration_id,
                "session": dict(reference),
                "reason": "contract_upgrade",
                "successor_state": dict(successor.reference),
                "status": "invalidated",
            }
            receipt_id = canonical_sha256(reference)[:24]
            document = self._sealed_json(
                body, f"orchestration/session-invalidations/{receipt_id}.json"
            )
            derived.append(document)
            session_receipts.append(dict(document.reference))
        completion_receipts: list[dict[str, str]] = []
        for item in plan.data.get("completion_references", []):
            reference = item["completion"]
            self.load_document(reference)
            body = {
                "schema_version": "1.0",
                "migration_id": migration_id,
                "stage": item["stage"],
                "completion": dict(reference),
                "reason": "contract_upgrade",
                "successor_state": dict(successor.reference),
                "status": "invalidated",
            }
            receipt_id = canonical_sha256([item["stage"], reference])[:24]
            document = self._sealed_json(
                body, f"orchestration/completion-invalidations/{receipt_id}.json"
            )
            derived.append(document)
            completion_receipts.append(dict(document.reference))
        post_upgrade_receipts: list[dict[str, str]] = []
        for item in plan.data.get("post_upgrade_documents", []):
            document = SealedDocument(
                data=dict(item["data"]), reference=dict(item["reference"])
            )
            derived.append(document)
            post_upgrade_receipts.append(dict(document.reference))
        h1_implementation_refresh = (
            plan.data.get("transition_mode") == "active_stage_return_refresh"
            and plan.data.get("target_stage") == "H1"
            and isinstance(
                plan.data.get("stale_identity", {}).get(
                    "initialized_workspace"
                ),
                Mapping,
            )
        )
        if plan.data.get("transition_mode") in {
            "internal_h1_fragment_return", "internal_h1_readability_return",
            "internal_h1_html_readability_return",
        } or h1_implementation_refresh:
            stale = plan.data["stale_identity"]
            failure_reference = stale.get(
                "fidelity_failure",
                stale.get(
                    "readability_failure", stale.get("implementation_failure")
                ),
            )
            restored_workspace = stale.get(
                "restored_workspace",
                stale.get("planned_workspace", stale.get("initialized_workspace")),
            )
            body = {
                "schema_version": "1.0",
                "migration_id": migration_id,
                "h1_workspace": copy.deepcopy(stale["current_workspace"]),
                "fidelity_failure": copy.deepcopy(failure_reference),
                "restored_workspace": copy.deepcopy(restored_workspace),
                "successor_state": dict(successor.reference),
                "status": "superseded",
            }
            manifest_reference = (
                stale.get("html_manifest")
                if plan.data.get("transition_mode")
                == "internal_h1_html_readability_return"
                else stale.get("fragment_manifest")
            )
            manifest_field = (
                "html_manifest"
                if plan.data.get("transition_mode")
                == "internal_h1_html_readability_return"
                else "fragment_manifest"
            )
            body[manifest_field] = copy.deepcopy(manifest_reference)
            marker_id = canonical_sha256(
                [
                    manifest_reference,
                    failure_reference,
                ]
            )[:24]
            derived.append(self._sealed_json(
                body,
                f"orchestration/h1-artifact-invalidations/{marker_id}.json",
            ))
        body = {
            "schema_version": "1.0",
            "migration_id": migration_id,
            "reason": "contract_upgrade",
            "plan": dict(plan.reference),
            "predecessor_state": dict(plan.data["predecessor_state"]),
            "successor_state": dict(successor.reference),
            "return_request": dict(plan.data["return_request"]),
            "old_contract_digest": plan.data["old_contract_digest"],
            "new_contract_digest": plan.data["new_contract_digest"],
            "invalidated_stages": list(plan.data["invalidated_stages"]),
            "production_versions": dict(plan.data["production_versions"]),
            "transition_mode": plan.data.get("transition_mode", "new_return"),
            "refresh_generation": plan.data.get("refresh_generation", 0),
            "prior_qualification": plan.data.get("prior_qualification"),
            "target_stage": plan.data.get("target_stage"),
            "stale_identity": plan.data.get("stale_identity"),
            "production_contract": plan.data.get("production_contract"),
            "inventory_sha256": plan.data.get("inventory_sha256"),
            "superseded_return": plan.data.get("superseded_return"),
            "post_upgrade_documents": post_upgrade_receipts,
            "post_upgrade_work_order": plan.data.get("post_upgrade_work_order"),
            "session_invalidation_receipts": session_receipts,
            "work_order_invalidation_receipts": work_order_receipts,
            "completion_invalidation_receipts": completion_receipts,
            "commit_intent_abandonment_receipts": intent_receipts,
            "status": "complete",
        }
        receipt = self._sealed_json(
            body,
            f"orchestration/contract-upgrades/{migration_id}.complete.json",
        )
        return receipt, tuple(derived)

    def preflight_contract_upgrade_transaction(
        self,
        *,
        request: SealedDocument,
        plan: SealedDocument,
        successor: SealedDocument,
        complete_receipt: SealedDocument | None = None,
    ) -> SealedDocument:
        """Preflight the complete immutable upgrade write set and pointers."""

        if plan.data.get("return_request") != request.reference:
            _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
        expected_receipt, derived = self.build_contract_upgrade_completion(
            plan, successor=successor
        )
        receipt = complete_receipt or expected_receipt
        if complete_receipt is not None and not self._contract_upgrade_receipt_matches(
            complete_receipt, expected_receipt
        ):
            _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
        self.preflight_immutable_documents(
            (request, plan, successor, *derived, receipt)
        )
        # Mutable pointers are published only after all immutable writes pass.
        # Validate their exact targets and serializability during preflight.
        state_pointer = {
            "schema_version": "2.0",
            "state": dict(successor.reference),
        }
        qualification_pointer = {
            "schema_version": "1.0",
            "receipt": dict(receipt.reference),
        }
        self._path("orchestration/current-state.json")
        self._path("orchestration/current-contract-upgrade.json")
        if plan.data.get("post_upgrade_work_order") is not None:
            canonical_json({
                "schema_version": "2.0",
                "work_order": dict(plan.data["post_upgrade_work_order"]),
            })
            self._path("orchestration/current-work-order.json")
        if plan.data.get("transition_mode") in {
            "internal_h1_fragment_return", "internal_h1_readability_return",
            "internal_h1_html_readability_return",
        } or (
            plan.data.get("transition_mode") == "active_stage_return_refresh"
            and plan.data.get("target_stage") == "H1"
            and isinstance(
                plan.data.get("stale_identity", {}).get(
                    "initialized_workspace"
                ),
                Mapping,
            )
        ):
            stale = plan.data.get("stale_identity", {})
            restored = stale.get(
                "restored_workspace",
                stale.get("planned_workspace", stale.get("initialized_workspace")),
            )
            if not isinstance(restored, Mapping):
                _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
            canonical_json({
                "schema_version": "2.0",
                "workspace": dict(restored),
            })
            self._path("orchestration/current-h1-workspace.json")
        canonical_json(state_pointer)
        canonical_json(qualification_pointer)
        return receipt

    @staticmethod
    def _contract_upgrade_receipt_matches(
        receipt: SealedDocument,
        expected: SealedDocument,
    ) -> bool:
        """Compare a complete receipt while admitting the legacy core shape."""

        required = (
            "schema_version", "migration_id", "reason", "plan",
            "predecessor_state", "successor_state", "return_request",
            "old_contract_digest", "new_contract_digest",
            "invalidated_stages", "production_versions",
            "session_invalidation_receipts",
            "work_order_invalidation_receipts",
            "completion_invalidation_receipts", "status",
        )
        optional = (
            "transition_mode", "refresh_generation", "prior_qualification",
            "target_stage", "stale_identity", "production_contract",
            "inventory_sha256", "commit_intent_abandonment_receipts",
            "superseded_return", "post_upgrade_documents",
            "post_upgrade_work_order",
        )
        return all(
            receipt.data.get(field) == expected.data.get(field)
            for field in required
        ) and all(
            field not in receipt.data
            or receipt.data[field] == expected.data.get(field)
            for field in optional
        )

    def complete_contract_upgrade(
        self, plan: SealedDocument, *, successor: SealedDocument
    ) -> SealedDocument:
        """Write deterministic rejection/abandonment/session receipts."""

        if (
            plan.data.get("status") != "prepared"
            or plan.data.get("successor_state") != successor.reference
            or plan.data.get("successor_snapshot") != successor.data
            or self.latest_state().reference != successor.reference
        ):
            _fail("PROD_CONTRACT_UPGRADE_PLAN_INVALID", str(plan.reference))
        receipt, derived = self.build_contract_upgrade_completion(
            plan, successor=successor
        )
        self.preflight_immutable_documents((*derived, receipt))
        for document in derived:
            self.persist_document(document)
        self.persist_document(receipt)
        if plan.data.get("post_upgrade_work_order") is not None:
            self._replace(
                self.root / "orchestration" / "current-work-order.json",
                {
                    "schema_version": "2.0",
                    "work_order": plan.data["post_upgrade_work_order"],
                },
            )
        if plan.data.get("transition_mode") in {
            "internal_h1_fragment_return", "internal_h1_readability_return",
            "internal_h1_html_readability_return",
        } or (
            plan.data.get("transition_mode") == "active_stage_return_refresh"
            and plan.data.get("target_stage") == "H1"
            and isinstance(
                plan.data.get("stale_identity", {}).get(
                    "initialized_workspace"
                ),
                Mapping,
            )
        ):
            restored = plan.data["stale_identity"].get(
                "restored_workspace",
                plan.data["stale_identity"].get(
                    "planned_workspace",
                    plan.data["stale_identity"].get("initialized_workspace"),
                ),
            )
            self._replace(
                self.root / "orchestration" / "current-h1-workspace.json",
                {
                    "schema_version": "2.0",
                    "workspace": restored,
                },
            )
        self._replace(
            self.root / "orchestration" / "current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": receipt.reference},
        )
        return receipt

    def current_contract_upgrade(self) -> SealedDocument | None:
        pointer = self.root / "orchestration" / "current-contract-upgrade.json"
        if not pointer.is_file():
            return None
        value = json.loads(pointer.read_text(encoding="utf-8"))
        return self.load_document(value["receipt"])

    def install_initial_contract_qualification(
        self,
        *,
        contract_digest: str,
        production_versions: Mapping[str, str],
        production_contract: Mapping[str, Any],
    ) -> SealedDocument:
        """Install the immutable qualification for a newly initialized run."""
        if self.current_contract_upgrade() is not None:
            _fail("PROD_CONTRACT_QUALIFICATION_EXISTS", contract_digest)
        if canonical_sha256(production_contract) != contract_digest:
            _fail("PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", contract_digest)
        qualification_id = canonical_sha256(
            ["contract_bootstrap", contract_digest, dict(production_versions)]
        )[:24]
        body = {
            "schema_version": "1.0",
            "migration_id": qualification_id,
            "reason": "contract_bootstrap",
            "old_contract_digest": contract_digest,
            "new_contract_digest": contract_digest,
            "invalidated_stages": [],
            "production_versions": dict(production_versions),
            "production_contract": copy.deepcopy(dict(production_contract)),
            "session_invalidation_receipts": [],
            "work_order_invalidation_receipts": [],
            "completion_invalidation_receipts": [],
            "status": "complete",
        }
        document = SealedDocument(
            data=body,
            reference={
                "path": (
                    "orchestration/contract-upgrades/"
                    f"{qualification_id}.complete.json"
                ),
                "sha256": canonical_sha256(body),
            },
        )
        self.persist_document(document)
        self._replace(
            self.root / "orchestration" / "current-contract-upgrade.json",
            {"schema_version": "1.0", "receipt": document.reference},
        )
        return document

    def reconcile_contract_upgrades(
        self,
        latest: SealedDocument,
        *,
        transaction_validator: Any | None = None,
    ) -> SealedDocument:
        """Validate every prepared upgrade before committing any recovery write."""

        trusted_markers = self.trusted_contract_upgrade_markers(
            scan_orphans=False
        )
        qualification = self.current_contract_upgrade()
        reachable: set[tuple[str, str]] = set()
        cursor: SealedDocument | None = qualification
        while cursor is not None:
            reachable.add((cursor.reference["path"], cursor.reference["sha256"]))
            prior = cursor.data.get("prior_qualification")
            cursor = self.load_document(prior) if isinstance(prior, Mapping) else None

        raw: list[dict[str, Any]] = []
        for path in sorted(
            (self.root / "orchestration" / "contract-upgrades").glob(
                "*.prepared.json"
            )
        ):
            plan = self.load_document(
                {
                    "path": path.relative_to(self.root).as_posix(),
                    "sha256": sha256_file(path),
                }
            )
            successor = SealedDocument(
                data=plan.data.get("successor_snapshot", {}),
                reference=plan.data.get("successor_state", {}),
            )
            complete_path = path.with_name(
                path.name.replace(".prepared.json", ".complete.json")
            )
            existing_receipt = None
            if complete_path.is_file():
                existing_receipt = self.load_document(
                    {
                        "path": complete_path.relative_to(self.root).as_posix(),
                        "sha256": sha256_file(complete_path),
                    }
                )
                if (
                    existing_receipt.reference["path"],
                    existing_receipt.reference["sha256"],
                ) in reachable:
                    continue
            raw.append(
                {
                    "plan": plan,
                    "successor": successor,
                    "existing_receipt": existing_receipt,
                }
            )
        if not raw:
            self._scan_untrusted_processed_markers(trusted_markers)
            return latest
        if qualification is None:
            _fail("PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID", "missing pointer")

        # Find the oldest unresolved transaction.  A crash may have published
        # its successor already, so either its predecessor or successor may be
        # the latest persisted state.  Remaining plans must then form one chain.
        successor_starts = [
            item
            for item in raw
            if item["plan"].data.get("successor_state") == latest.reference
        ]
        predecessor_starts = [
            item
            for item in raw
            if item["plan"].data.get("predecessor_state") == latest.reference
        ]
        starts = successor_starts or predecessor_starts
        if len(starts) != 1:
            _fail("PROD_CONTRACT_UPGRADE_RECOVERY_CONFLICT", "prepared fork")
        first = starts[0]
        if first["plan"].data.get("successor_state") == latest.reference:
            ordered = [first]
            next_predecessor = latest.reference
        else:
            ordered = [first]
            next_predecessor = first["successor"].reference
        remaining = [item for item in raw if item is not first]
        while remaining:
            matches = [
                item
                for item in remaining
                if item["plan"].data.get("predecessor_state") == next_predecessor
            ]
            if len(matches) != 1:
                _fail("PROD_CONTRACT_UPGRADE_RECOVERY_CONFLICT", "prepared fork")
            item = matches[0]
            ordered.append(item)
            remaining.remove(item)
            next_predecessor = item["successor"].reference

        virtual_qualification = qualification
        state_references = {
            f"state/{path.name}": {
                "path": f"state/{path.name}",
                "sha256": sha256_file(path),
            }
            for path in (self.root / "state").glob("revision-*.json")
        }
        write_set: list[SealedDocument] = []
        for item in ordered:
            plan = item["plan"]
            successor = item["successor"]
            existing = item["existing_receipt"]
            expected, derived = self.build_contract_upgrade_completion(
                plan, successor=successor
            )
            receipt = existing or expected
            if existing is not None and existing != expected:
                _fail(
                    "PROD_CONTRACT_UPGRADE_RECOVERY_CONFLICT",
                    plan.data.get("migration_id", ""),
                )
            if (
                plan.data.get("prior_qualification")
                != virtual_qualification.reference
                or plan.data.get("old_contract_digest")
                != virtual_qualification.data.get("new_contract_digest")
                or (
                    plan.data.get("transition_mode")
                    in {
                        "active_return_refresh",
                        "active_return_escalation",
                        "active_stage_return_refresh",
                        "stage_return",
                        "internal_h1_fragment_return",
                        "internal_h1_readability_return",
                        "internal_h1_html_readability_return",
                    }
                    and plan.data.get("refresh_generation")
                    != virtual_qualification.data.get("refresh_generation", 0) + 1
                )
            ):
                _fail(
                    "PROD_CONTRACT_QUALIFICATION_CHAIN_INVALID",
                    plan.reference["path"],
                )
            replay_states = dict(state_references)
            replay_states[successor.reference["path"]] = successor.reference
            self._validate_upgrade_transaction_replay(
                receipt,
                state_references=replay_states,
                successor_override=successor,
            )
            if transaction_validator is not None:
                transaction_validator(
                    plan=plan,
                    receipt=receipt,
                    predecessor=self.load_document(plan.data["predecessor_state"]),
                    successor=successor,
                    request=self.load_document(plan.data["return_request"]),
                    qualification=virtual_qualification,
                )
            request = self.load_document(plan.data["return_request"])
            write_set.extend((request, plan, successor, *derived, receipt))
            for marker in derived:
                self._allow_upgrade_marker(trusted_markers, marker)
            virtual_qualification = receipt
            state_references[successor.reference["path"]] = successor.reference
        self._scan_untrusted_processed_markers(trusted_markers)
        self.preflight_immutable_documents(write_set)

        current = latest
        for item in ordered:
            plan = item["plan"]
            successor = item["successor"]
            if current.reference == plan.data["predecessor_state"]:
                self.persist_state(successor)
                current = successor
            elif current.reference != successor.reference:
                _fail(
                    "PROD_CONTRACT_UPGRADE_RECOVERY_CONFLICT",
                    plan.data["migration_id"],
                )
            self.complete_contract_upgrade(plan, successor=successor)
        return current

    def _persist_commit_intent(
        self,
        work_order: SealedDocument,
        *,
        successor: SealedDocument,
        successor_kind: str,
        evidence: SealedDocument,
    ) -> SealedDocument:
        """Prepare an immutable exact-successor journal before publication."""

        if successor_kind not in {"state", "h1-workspace"}:
            _fail("PROD_COMMIT_KIND_INVALID", successor_kind)
        if canonical_sha256(successor.data) != successor.reference.get("sha256"):
            _fail("PROD_COMMIT_SUCCESSOR_INVALID", str(successor.reference))
        try:
            self.runtime.validate(
                successor.data,
                (
                    "autonomous-run-state.schema.json"
                    if successor_kind == "state"
                    else "h1-workspace-state.schema.json"
                ),
            )
        except ContractValidationError as error:
            _fail("PROD_COMMIT_SUCCESSOR_INVALID", str(error))
        body = {
            "schema_version": "2.0",
            "work_order": dict(work_order.reference),
            "action": work_order.data["action"],
            "required_actor": work_order.data["required_actor"],
            "predecessor_state": dict(work_order.data["state"]),
            "input_gate": work_order.data.get("input_gate"),
            "h1_workspace": work_order.data.get("h1_workspace"),
            "successor_kind": successor_kind,
            "successor": dict(successor.reference),
            "admission_evidence": dict(evidence.reference),
            "status": "prepared",
        }
        intent = SealedDocument(
            data=body,
            reference={
                "path": (
                    "orchestration/commit-intents/"
                    f"{work_order.data['work_id']}.json"
                ),
                "sha256": canonical_sha256(body),
            },
        )
        self.persist_document(intent)
        return intent

    def _load_commit_intent(
        self, work_order: SealedDocument
    ) -> SealedDocument | None:
        path = (
            self.root
            / "orchestration"
            / "commit-intents"
            / f"{work_order.data['work_id']}.json"
        )
        if not path.is_file():
            return None
        abandoned = path.with_name(f"{work_order.data['work_id']}.abandoned.json")
        if abandoned.is_file():
            _fail("PROD_COMMIT_INTENT_ABANDONED", work_order.data["work_id"])
        reference = {
            "path": (
                "orchestration/commit-intents/"
                f"{work_order.data['work_id']}.json"
            ),
            "sha256": sha256_file(path),
        }
        intent = self.load_document(reference)
        expected = {
            "schema_version": "2.0",
            "work_order": dict(work_order.reference),
            "action": work_order.data["action"],
            "required_actor": work_order.data["required_actor"],
            "predecessor_state": dict(work_order.data["state"]),
            "input_gate": work_order.data.get("input_gate"),
            "h1_workspace": work_order.data.get("h1_workspace"),
            "successor_kind": intent.data.get("successor_kind"),
            "successor": intent.data.get("successor"),
            "admission_evidence": intent.data.get("admission_evidence"),
            "status": "prepared",
        }
        if intent.data != expected:
            _fail("PROD_COMMIT_INTENT_INVALID", work_order.data["work_id"])
        return intent

    def require_current_work_order(
        self, work_order: SealedDocument, *, state: SealedDocument
    ) -> None:
        current = self.root / "orchestration" / "current-work-order.json"
        if not current.is_file():
            _fail("PROD_WORK_ORDER_MISSING", str(current))
        pointer = json.loads(current.read_text(encoding="utf-8"))
        if pointer.get("work_order") != work_order.reference:
            _fail("PROD_WORK_ORDER_NOT_CURRENT", work_order.data.get("work_id", ""))
        persisted = self.load_document(pointer["work_order"])
        if persisted.reference != work_order.reference or persisted.data != work_order.data:
            _fail("PROD_WORK_ORDER_FORGED", work_order.data.get("work_id", ""))
        rejected = self.root / "orchestration" / "work-orders" / (
            f"{work_order.data['work_id']}.rejected.json"
        )
        if rejected.exists():
            _fail("PROD_WORK_ORDER_REJECTED", work_order.data["work_id"])
        if work_order.data.get("state") != state.reference:
            _fail("PROD_WORK_ORDER_STALE", work_order.data.get("work_id", ""))
        consumed = self.root / "orchestration" / "work-orders" / (
            f"{work_order.data['work_id']}.consumed.json"
        )
        if consumed.exists():
            _fail("PROD_WORK_ORDER_CONSUMED", work_order.data["work_id"])

    def mark_work_order_consumed(
        self,
        work_order: SealedDocument,
        *,
        successor: SealedDocument,
        successor_relocation: SealedDocument | None = None,
    ) -> Path:
        intent = self._load_commit_intent(work_order)
        relocation_specs = {
            "H1-B": (
                "fragments_ready",
                "fragment_manifest",
                "h1-fragments-manifest-sha256-prefix-v1",
            ),
            "H1-C": (
                "rendered",
                "html_manifest",
                "h1-rendered-manifest-sha256-prefix-v1",
            ),
        }
        relocation_spec = relocation_specs.get(str(work_order.data.get("action")))
        original = intent.data.get("successor") if intent else None
        evidence = intent.data.get("admission_evidence") if intent else None
        next_state = relocation_spec[0] if relocation_spec else None
        artifact_key = relocation_spec[1] if relocation_spec else None
        algorithm = relocation_spec[2] if relocation_spec else None
        expected_original_path = (
            f"H1/{successor.data.get('session_id')}/workspace-{next_state}.json"
            if next_state is not None
            else None
        )
        expected_effective_path = (
            f"H1/{successor.data.get('session_id')}/workspace-{next_state}-"
            f"{evidence.get('sha256', '')[:24]}.json"
            if next_state is not None and isinstance(evidence, Mapping)
            else None
        )
        collision = (
            successor_relocation.data.get("collision")
            if successor_relocation is not None
            else None
        )
        receipt_digest = (
            canonical_sha256(successor_relocation.data)
            if successor_relocation is not None
            else None
        )
        expected_receipt_path = (
            "orchestration/h1-workspace-relocations/"
            f"{receipt_digest[:24]}.json"
            if receipt_digest is not None
            else None
        )
        collision_document = None
        marker_match = False
        if (
            isinstance(collision, Mapping)
            and collision.get("path") == expected_original_path
            and isinstance(collision.get("sha256"), str)
        ):
            try:
                collision_document = self.load_document(collision)
            except ProductionStoreError:
                collision_document = None
        if collision_document is not None and artifact_key is not None:
            marker_root = self.root / "orchestration/h1-artifact-invalidations"
            for marker_path in sorted(marker_root.glob("*.json")):
                try:
                    marker = self.load_document(
                        {
                            "path": marker_path.relative_to(self.root).as_posix(),
                            "sha256": sha256_file(marker_path),
                        }
                    )
                except ProductionStoreError:
                    continue
                marker_id = canonical_sha256(
                    [
                        marker.data.get(artifact_key),
                        marker.data.get("fidelity_failure"),
                    ]
                )[:24]
                migration_id = marker.data.get("migration_id")
                qualification = None
                current_qualification = None
                if isinstance(migration_id, str) and re.fullmatch(
                    r"[0-9a-f]{24}", migration_id
                ):
                    qualification_path = (
                        self.root / "orchestration/contract-upgrades"
                        / f"{migration_id}.complete.json"
                    )
                    if qualification_path.is_file():
                        try:
                            qualification = self.load_document(
                                {
                                    "path": qualification_path.relative_to(
                                        self.root
                                    ).as_posix(),
                                    "sha256": sha256_file(qualification_path),
                                }
                            )
                        except ProductionStoreError:
                            qualification = None
                if qualification is not None:
                    try:
                        current_qualification = self.current_contract_upgrade()
                    except (ProductionStoreError, KeyError, TypeError, ValueError):
                        current_qualification = None
                expected_mode = (
                    "internal_h1_fragment_return"
                    if next_state == "fragments_ready"
                    else "internal_h1_html_readability_return"
                )
                stale = (
                    qualification.data.get("stale_identity", {})
                    if qualification is not None
                    else {}
                )
                failure_key = (
                    "fidelity_failure"
                    if next_state == "fragments_ready"
                    else "readability_failure"
                )
                restored_key = (
                    "planned_workspace"
                    if next_state == "fragments_ready"
                    else "restored_workspace"
                )
                expected_marker_data = {
                    "schema_version": "1.0",
                    "migration_id": migration_id,
                    "h1_workspace": collision,
                    "fidelity_failure": stale.get(failure_key),
                    "restored_workspace": work_order.data.get("h1_workspace"),
                    "successor_state": work_order.data.get("state"),
                    "status": "superseded",
                    artifact_key: collision_document.data.get("artifacts", {}).get(
                        artifact_key
                    ),
                }
                if (
                    qualification is not None
                    and qualification == current_qualification
                    and qualification.data.get("status") == "complete"
                    and qualification.data.get("transition_mode") == expected_mode
                    and qualification.data.get("successor_state")
                    == work_order.data.get("state")
                    and stale.get("current_workspace") == collision
                    and stale.get(restored_key) == work_order.data.get("h1_workspace")
                    and stale.get(artifact_key)
                    == collision_document.data.get("artifacts", {}).get(artifact_key)
                    and marker.data == expected_marker_data
                    and marker.reference.get("path")
                    == (
                        "orchestration/h1-artifact-invalidations/"
                        f"{marker_id}.json"
                    )
                    and marker.data.get("status") == "superseded"
                    and marker.data.get("h1_workspace") == collision
                    and marker.data.get("restored_workspace")
                    == work_order.data.get("h1_workspace")
                    and marker.data.get("successor_state")
                    == work_order.data.get("state")
                    and marker.data.get(artifact_key)
                    == collision_document.data.get("artifacts", {}).get(artifact_key)
                ):
                    marker_match = True
                    break
        relocated = (
            successor_relocation is not None
            and relocation_spec is not None
            and isinstance(original, Mapping)
            and isinstance(evidence, Mapping)
            and isinstance(collision, Mapping)
            and intent is not None
            and intent.data.get("successor_kind") == "h1-workspace"
            and original.get("path") == expected_original_path
            and original.get("sha256") == successor.reference.get("sha256")
            and successor.reference.get("path") == expected_effective_path
            and successor.data.get("state") == next_state
            and canonical_sha256(successor.data) == successor.reference.get("sha256")
            and collision.get("path") == expected_original_path
            and collision.get("sha256") != original.get("sha256")
            and collision_document is not None
            and marker_match
            and successor_relocation.data
            == {
                "schema_version": "1.0",
                "kind": "h1-workspace-successor-relocation",
                "work_order": work_order.reference,
                "commit_intent": intent.reference if intent else None,
                "original_successor": original,
                "effective_successor": successor.reference,
                "collision": collision,
                "algorithm": algorithm,
                "status": "complete",
            }
            and successor_relocation.reference
            == {"path": expected_receipt_path, "sha256": receipt_digest}
        )
        if (
            intent is None
            or (
                intent.data.get("successor") != successor.reference
                and not relocated
            )
        ):
            _fail("PROD_COMMIT_INTENT_MISSING", work_order.data["work_id"])
        if relocated:
            self.load_document(successor_relocation.reference)
        committed = self.load_document(successor.reference)
        if committed.data != successor.data:
            _fail("PROD_COMMIT_SUCCESSOR_INVALID", work_order.data["work_id"])
        if intent.data["successor_kind"] == "state":
            current = self.latest_state()
        else:
            current = self.latest_workspace()
        if current.reference != successor.reference or current.data != successor.data:
            _fail("PROD_COMMIT_SUCCESSOR_NOT_CURRENT", work_order.data["work_id"])
        body = {
            "schema_version": "2.0",
            "work_order": dict(work_order.reference),
            "successor": dict(successor.reference),
            "status": "consumed",
        }
        path = self.root / "orchestration" / "work-orders" / (
            f"{work_order.data['work_id']}.consumed.json"
        )
        self._write_new(path, canonical_json(body).encode("utf-8"))
        return path


__all__ = ["ProductionRunStore", "ProductionStoreError"]
