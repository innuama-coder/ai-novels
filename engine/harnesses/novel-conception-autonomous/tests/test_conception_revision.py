from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path


runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.conception_revision"
)
canonical = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.canonical"
)
baseline = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.baseline"
)
orchestrator = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)


TARGETS = {
    "I3": (
        ("CHR-GU-HENG-MEMORY", "author_locked", "顾衡的记忆"),
        ("CHR-ROLE-TIERS", "author_locked", "角色层级"),
    ),
    "I4": (
        ("CAU-AUDIT-BOUNDARY", "author_locked", "审计边界"),
        ("CAU-GLOBAL-SPINE", "author_locked", "全局主线"),
        ("CAU-MAJOR-NODES", "author_locked", "主要节点"),
    ),
    "I5": (
        ("NAR-FAIRNESS", "author_locked", "叙事公平"),
        ("NAR-POV-ARCHITECTURE", "author_locked", "视角结构"),
    ),
}


class ConceptionRevisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="authority-revision-unit-")
        self.root = Path(self.temp.name)
        self.parent = self.root / "parent-run"
        self.parent.mkdir()
        self.hld = self.root / "hld-run"
        self.hld.mkdir()
        self.sources = self.root / "sources"
        self.sources.mkdir()
        self.review_root = self.root / "independent-review"
        self.review_root.mkdir()
        self.target = self.root / "revision-run"
        self.evidence_roots = {"parent": self.parent, "hld": self.hld}
        labels = sorted(runtime.REQUIRED_EVIDENCE_LABELS)
        self.evidence_bindings = {}
        for label in labels:
            root_name = "parent" if label.startswith("parent_") else "hld"
            path = self.evidence_roots[root_name] / f"{label}.json"
            path.write_text(
                json.dumps({"label": label}, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
                newline="",
            )
            self.evidence_bindings[label] = {
                "root": root_name,
                "artifact": {"path": path.name, "sha256": canonical.sha256_file(path)},
            }
        self.edits = []
        for domain, controls in TARGETS.items():
            path = self.sources / f"{domain}.md"
            chunks = []
            for source_id, hardness, title in controls:
                chunks.append(f"## [{source_id}][{hardness}] {title}\nold-{source_id}\n")
            path.write_text("\n".join(chunks), encoding="utf-8", newline="")
            data = path.read_bytes()
            parent_ref = {"path": path.name, "sha256": canonical.sha256_file(path)}
            for index, (source_id, hardness, title) in enumerate(controls):
                old_text = f"old-{source_id}"
                new_text = f"new-{source_id}"
                start = data.index(old_text.encode("utf-8"))
                self.edits.append(
                    {
                        "source_id": source_id,
                        "domain": domain,
                        "hardness": hardness,
                        "title": title,
                        "control_index": index,
                        "parent_artifact": parent_ref,
                        "parent_value_sha256": canonical.canonical_sha256(old_text),
                        "effective_value_sha256": canonical.canonical_sha256(new_text),
                        "start_byte": start,
                        "end_byte": start + len(old_text.encode("utf-8")),
                        "old_text": old_text,
                        "old_text_sha256": hashlib.sha256(old_text.encode("utf-8")).hexdigest(),
                        "new_text": new_text,
                        "new_text_sha256": hashlib.sha256(new_text.encode("utf-8")).hexdigest(),
                        "directive_clause_refs": ["DIR-001"],
                    }
                )
        self.arguments = {
            "run_id": "revision-unit-01",
            "source_root": self.sources,
            "evidence_roots": self.evidence_roots,
            "evidence_bindings": self.evidence_bindings,
            "author_text": "修正顾衡状态与事件时序，其他构思保持不变。",
            "directive_clauses": [
                {
                    "clause_id": "DIR-001",
                    "text": "只修正已指出的七项构思定义。",
                    "evidence_labels": ["author_event", "hld_answer", "hld_resolution"],
                }
            ],
            "text_edits": self.edits,
            "producer_identity": {
                "actor_id": "producer",
                "session_id": "producer-session",
                "implementation_sha256": "1" * 64,
            },
        }
        material = runtime.build_authority_revision_review_material(
            run_id=self.arguments["run_id"],
            evidence_bindings=self.arguments["evidence_bindings"],
            author_text=self.arguments["author_text"],
            directive_clauses=self.arguments["directive_clauses"],
            text_edits=self.arguments["text_edits"],
            producer_identity=self.arguments["producer_identity"],
        )
        self.review = {
            "schema_version": "1.0",
            "kind": "authority-revision-semantic-review",
            "review_id": "independent-review-001",
            "transaction_id": material["candidate_material_sha256"][:24],
            "run_id": self.arguments["run_id"],
            "candidate_material_sha256": material["candidate_material_sha256"],
            "reviewer": {
                "actor_id": "reviewer",
                "session_id": "review-session",
                "implementation_sha256": "2" * 64,
            },
            "producer": self.arguments["producer_identity"],
            "covered_ids": sorted(runtime.AUTHORITY_REVISION_ALLOWSET),
            "item_reviews": [
                {"source_id": source_id, "verdict": "pass", "findings": []}
                for source_id in sorted(runtime.AUTHORITY_REVISION_ALLOWSET)
            ],
            "reviewer_produced_patch": False,
            "verdict": "pass",
            "status": "sealed",
        }
        self._write_review(self.review)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _run(self, **overrides):
        arguments = copy.deepcopy(self.arguments)
        arguments.update(overrides)
        return runtime.initialize_conception_revision_run(
            self.parent, self.target, **arguments
        )

    def _write_review(self, review, *, canonical_bytes=True, update_reference=True):
        path = self.review_root / "semantic-review.json"
        if canonical_bytes:
            payload = canonical.canonical_json(review).encode("utf-8")
        else:
            payload = json.dumps(review, ensure_ascii=False, indent=2).encode("utf-8")
        path.write_bytes(payload)
        if update_reference:
            self.arguments["semantic_review_root"] = self.review_root
            self.arguments["semantic_review"] = {
                "path": path.name,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }

    def _reseal_for(self, **argument_updates):
        self.arguments.update(argument_updates)
        material = runtime.build_authority_revision_review_material(
            run_id=self.arguments["run_id"],
            evidence_bindings=self.arguments["evidence_bindings"],
            author_text=self.arguments["author_text"],
            directive_clauses=self.arguments["directive_clauses"],
            text_edits=self.arguments["text_edits"],
            producer_identity=self.arguments["producer_identity"],
        )
        review = copy.deepcopy(self.review)
        review["transaction_id"] = material["candidate_material_sha256"][:24]
        review["run_id"] = self.arguments["run_id"]
        review["candidate_material_sha256"] = material["candidate_material_sha256"]
        review["producer"] = copy.deepcopy(self.arguments["producer_identity"])
        self._write_review(review)

    def _use_real_json_projections(self):
        edits = []
        for domain, controls in TARGETS.items():
            path = self.sources / f"{domain}.json"
            projection = {
                "controls": [
                    {
                        "id": source_id,
                        "hardness": hardness,
                        "heading": title,
                        "value": f"old-{source_id}",
                    }
                    for source_id, hardness, title in controls
                ]
            }
            path.write_bytes(canonical.canonical_json(projection).encode("utf-8"))
            data = path.read_bytes()
            parent_ref = {"path": path.name, "sha256": canonical.sha256_file(path)}
            for index, (source_id, hardness, title) in enumerate(controls):
                old_text = f"old-{source_id}"
                new_text = f"new-{source_id}"
                start = data.index(old_text.encode("utf-8"))
                edits.append(
                    {
                        "source_id": source_id,
                        "domain": domain,
                        "hardness": hardness,
                        "title": title,
                        "control_index": index,
                        "parent_artifact": parent_ref,
                        "parent_value_sha256": canonical.canonical_sha256(old_text),
                        "effective_value_sha256": canonical.canonical_sha256(new_text),
                        "start_byte": start,
                        "end_byte": start + len(old_text.encode("utf-8")),
                        "old_text": old_text,
                        "old_text_sha256": hashlib.sha256(old_text.encode("utf-8")).hexdigest(),
                        "new_text": new_text,
                        "new_text_sha256": hashlib.sha256(new_text.encode("utf-8")).hexdigest(),
                        "directive_clause_refs": ["DIR-001"],
                    }
                )
        self.edits = edits
        self._reseal_for(text_edits=edits)
        return edits

    def test_review_material_builder_is_write_free_and_order_stable(self) -> None:
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        first = runtime.build_authority_revision_review_material(
            run_id=self.arguments["run_id"],
            evidence_bindings=self.arguments["evidence_bindings"],
            author_text=self.arguments["author_text"],
            directive_clauses=self.arguments["directive_clauses"],
            text_edits=self.arguments["text_edits"],
            producer_identity=self.arguments["producer_identity"],
        )
        second = runtime.build_authority_revision_review_material(
            run_id=self.arguments["run_id"],
            evidence_bindings=self.arguments["evidence_bindings"],
            author_text=self.arguments["author_text"],
            directive_clauses=self.arguments["directive_clauses"],
            text_edits=list(reversed(self.arguments["text_edits"])),
            producer_identity=self.arguments["producer_identity"],
        )
        after = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        self.assertEqual(before, after)
        self.assertEqual(first, second)
        self.assertEqual(
            canonical.canonical_sha256(
                {key: value for key, value in first.items() if key != "candidate_material_sha256"}
            ),
            first["candidate_material_sha256"],
        )

    def test_real_json_projection_fork_preserves_plain_headings(self) -> None:
        self._use_real_json_projections()
        created = self._run()
        self.assertEqual(3, len(created.patch_plan.data["artifacts"]))
        for artifact in created.patch_plan.data["artifacts"]:
            effective = self.target / artifact["effective_artifact"]["path"]
            controls = baseline.extract_controls(effective, artifact["domain"])
            expected = {source_id: title for source_id, _, title in TARGETS[artifact["domain"]]}
            self.assertEqual(
                expected,
                {control["id"]: control["heading"] for control in controls},
            )

    def test_real_json_projection_rejects_wrong_title_fail_closed(self) -> None:
        edits = self._use_real_json_projections()
        edits = copy.deepcopy(edits)
        edits[0]["title"] = "错误标题"
        self._reseal_for(text_edits=edits)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_PATCH_PARENT_PROJECTION_MISMATCH"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_real_json_projection_rejects_wrong_hardness_fail_closed(self) -> None:
        edits = self._use_real_json_projections()
        edits = copy.deepcopy(edits)
        edits[0]["hardness"] = "autonomous_owned"
        self._reseal_for(text_edits=edits)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_PATCH_PARENT_PROJECTION_MISMATCH"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_bootstrap_is_atomic_hash_bound_and_exactly_replayable(self) -> None:
        parent_before = canonical.canonical_sha256(
            {path.name: canonical.sha256_file(path) for path in sorted(self.parent.iterdir())}
        )
        source_before = {
            path.name: canonical.sha256_file(path) for path in sorted(self.sources.iterdir())
        }
        first = self._run()
        self.assertFalse(first.replayed)
        self.assertEqual("authority_revision", first.production.state.data["source_kind"])
        self.assertFalse(first.directive_binding.data["author_approved_bytes"])
        self.assertFalse(first.semantic_review.data["reviewer_produced_patch"])
        self.assertEqual(
            (self.review_root / self.arguments["semantic_review"]["path"]).read_bytes(),
            (self.target / first.semantic_review.reference["path"]).read_bytes(),
        )
        self.assertEqual(sorted(runtime.AUTHORITY_REVISION_ALLOWSET), first.patch_plan.data["allowset"])
        self.assertEqual(source_before, {
            path.name: canonical.sha256_file(path) for path in sorted(self.sources.iterdir())
        })
        self.assertEqual(parent_before, canonical.canonical_sha256(
            {path.name: canonical.sha256_file(path) for path in sorted(self.parent.iterdir())}
        ))
        second = self._run()
        self.assertTrue(second.replayed)
        self.assertEqual(first.transaction_id, second.transaction_id)
        self.assertEqual(first.bootstrap_completion.reference, second.bootstrap_completion.reference)
        validated = runtime.validate_conception_revision_run(self.target)
        self.assertTrue(validated.replayed)
        self.assertEqual(first.finalization.reference, validated.finalization.reference)

    def test_validation_is_anchored_to_bootstrap_after_later_active_return(self) -> None:
        created = self._run()
        bootstrap = created.production.state
        later = copy.deepcopy(bootstrap.data)
        later["revision"] = 1
        later["previous_state"] = bootstrap.reference
        later["active_return"] = {
            "path": "returns/later-active-return.json",
            "sha256": "a" * 64,
        }
        later_path = self.target / "state" / "revision-001.json"
        later_path.write_bytes(canonical.canonical_json(later).encode("utf-8"))
        (self.target / "orchestration" / "current-state.json").write_bytes(
            canonical.canonical_json(
                {
                    "schema_version": "2.0",
                    "state": {
                        "path": "state/revision-001.json",
                        "sha256": canonical.sha256_file(later_path),
                    },
                }
            ).encode("utf-8")
        )

        validated = runtime.validate_conception_revision_run(self.target)

        self.assertEqual(bootstrap.reference, validated.production.state.reference)
        self.assertEqual(0, validated.production.state.data["revision"])
        self.assertIsNone(validated.production.coordinator.state.get("active_return"))
        self.assertEqual(created.finalization.reference, validated.finalization.reference)

        finalization_path = self.target / created.finalization.reference["path"]
        state_chain = baseline._authority_revision_gate_state_chain(
            self.target,
            input_gate={
                "run_state": {
                    "path": "state/revision-001.json",
                    "sha256": canonical.sha256_file(later_path),
                }
            },
            finalization=created.finalization.data,
            finalization_path=finalization_path,
            bootstrap_state_path=self.target / bootstrap.reference["path"],
            run_id=self.arguments["run_id"],
            runtime=created.production.store.runtime,
            require_current_pointer=True,
        )
        self.assertEqual(
            ["revision-000.json", "revision-001.json"],
            [path.name for path in state_chain],
        )
        with self.assertRaisesRegex(
            baseline.BaselineError, "B0_SOURCE_STATE_MISMATCH"
        ):
            baseline._authority_revision_gate_state_chain(
                self.target,
                input_gate={
                    "run_state": {
                        "path": "state/revision-001.json",
                        "sha256": "0" * 64,
                    }
                },
                finalization=created.finalization.data,
                finalization_path=finalization_path,
                bootstrap_state_path=self.target / bootstrap.reference["path"],
                run_id=self.arguments["run_id"],
                runtime=created.production.store.runtime,
                require_current_pointer=True,
            )

        valid_later_reference = {
            "path": "state/revision-001.json",
            "sha256": canonical.sha256_file(later_path),
        }
        (self.target / "orchestration" / "current-state.json").write_bytes(
            canonical.canonical_json(
                {"schema_version": "2.0", "state": bootstrap.reference}
            ).encode("utf-8")
        )
        with self.assertRaisesRegex(
            baseline.BaselineError, "B0_SOURCE_STATE_MISMATCH"
        ):
            baseline._authority_revision_gate_state_chain(
                self.target,
                input_gate={"run_state": valid_later_reference},
                finalization=created.finalization.data,
                finalization_path=finalization_path,
                bootstrap_state_path=self.target / bootstrap.reference["path"],
                run_id=self.arguments["run_id"],
                runtime=created.production.store.runtime,
                require_current_pointer=True,
            )

        wrong_source = copy.deepcopy(later)
        wrong_source["source_interview_state"] = {
            "path": "authority-revision/evidence/parent_state.json",
            "sha256": "b" * 64,
        }
        later_path.write_bytes(canonical.canonical_json(wrong_source).encode("utf-8"))
        wrong_reference = {
            "path": "state/revision-001.json",
            "sha256": canonical.sha256_file(later_path),
        }
        (self.target / "orchestration" / "current-state.json").write_bytes(
            canonical.canonical_json(
                {"schema_version": "2.0", "state": wrong_reference}
            ).encode("utf-8")
        )
        with self.assertRaisesRegex(
            baseline.BaselineError, "B0_SOURCE_STATE_MISMATCH"
        ):
            baseline._authority_revision_gate_state_chain(
                self.target,
                input_gate={"run_state": wrong_reference},
                finalization=created.finalization.data,
                finalization_path=finalization_path,
                bootstrap_state_path=self.target / bootstrap.reference["path"],
                run_id=self.arguments["run_id"],
                runtime=created.production.store.runtime,
                require_current_pointer=True,
            )

    def test_rejects_non_independent_review_before_target_write(self) -> None:
        for field in ("actor_id", "session_id", "implementation_sha256"):
            with self.subTest(field=field):
                review = copy.deepcopy(self.review)
                review["reviewer"][field] = self.arguments["producer_identity"][field]
                self._write_review(review)
                with self.assertRaisesRegex(
                    runtime.ConceptionRevisionError, "REV_REVIEW_NOT_INDEPENDENT"
                ):
                    self._run()
                self.assertFalse(self.target.exists())

    def test_requires_external_review_before_target_write(self) -> None:
        missing = {"path": "missing.json", "sha256": "0" * 64}
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_ARTIFACT_INVALID"
        ):
            self._run(semantic_review=missing)
        self.assertFalse(self.target.exists())

    def test_rejects_noncanonical_review_before_target_write(self) -> None:
        self._write_review(self.review, canonical_bytes=False)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_NOT_CANONICAL"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_tampered_review_before_target_write(self) -> None:
        path = self.review_root / self.arguments["semantic_review"]["path"]
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_ARTIFACT_INVALID"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_review_for_wrong_candidate_before_target_write(self) -> None:
        review = copy.deepcopy(self.review)
        review["candidate_material_sha256"] = "3" * 64
        review["transaction_id"] = "3" * 24
        self._write_review(review)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_BINDING_INVALID"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_replay_rejects_a_different_review_for_same_candidate(self) -> None:
        created = self._run()
        review = copy.deepcopy(self.review)
        review["review_id"] = "independent-review-002"
        self._write_review(review)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_REPLAY_MISMATCH"
        ):
            self._run()
        self.assertTrue(self.target.is_dir())
        self.assertEqual(
            created.semantic_review.reference,
            runtime.validate_conception_revision_run(self.target).semantic_review.reference,
        )

    def test_rejects_review_with_wrong_producer_before_target_write(self) -> None:
        review = copy.deepcopy(self.review)
        review["producer"]["actor_id"] = "forged-producer"
        self._write_review(review)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_BINDING_INVALID"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_incomplete_review_coverage_before_target_write(self) -> None:
        review = copy.deepcopy(self.review)
        review["covered_ids"].pop()
        review["item_reviews"].pop()
        self._write_review(review)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_SCHEMA_INVALID"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_nonpassing_review_before_target_write(self) -> None:
        review = copy.deepcopy(self.review)
        review["verdict"] = "fail"
        self._write_review(review)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_SCHEMA_INVALID"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_reviewer_patch_authorship_before_target_write(self) -> None:
        review = copy.deepcopy(self.review)
        review["reviewer_produced_patch"] = True
        self._write_review(review)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_SCHEMA_INVALID"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_item_finding_before_target_write(self) -> None:
        review = copy.deepcopy(self.review)
        review["item_reviews"][0]["findings"] = ["unresolved"]
        self._write_review(review)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_SCHEMA_INVALID"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_forged_reviewer_identity_before_target_write(self) -> None:
        review = copy.deepcopy(self.review)
        review["reviewer"]["implementation_sha256"] = "not-a-digest"
        self._write_review(review)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_REVIEW_SCHEMA_INVALID"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_patch_outside_exact_allowset(self) -> None:
        edits = copy.deepcopy(self.edits)
        edits.pop()
        with self.assertRaisesRegex(runtime.ConceptionRevisionError, "REV_PATCH_ALLOWSET_INVALID"):
            self._run(text_edits=edits)
        self.assertFalse(self.target.exists())

    def test_rejects_wrong_offset_without_promoting_target(self) -> None:
        edits = copy.deepcopy(self.edits)
        edits[0]["start_byte"] += 1
        edits[0]["end_byte"] += 1
        self._reseal_for(text_edits=edits)
        with self.assertRaisesRegex(runtime.ConceptionRevisionError, "REV_PATCH_OFFSET_MISMATCH"):
            self._run()
        self.assertFalse(self.target.exists())

    def test_rejects_wrong_parent_hardness_without_promoting_target(self) -> None:
        edits = copy.deepcopy(self.edits)
        edits[0]["hardness"] = "autonomous_owned"
        self._reseal_for(text_edits=edits)
        with self.assertRaisesRegex(
            runtime.ConceptionRevisionError, "REV_PATCH_PARENT_PROJECTION_MISMATCH"
        ):
            self._run()
        self.assertFalse(self.target.exists())

    def test_foreign_staging_fails_closed_and_is_not_deleted(self) -> None:
        foreign = self.root / ".revision-run.authority-revision-foreign.staging"
        foreign.mkdir()
        with self.assertRaisesRegex(runtime.ConceptionRevisionError, "REV_STAGING_AMBIGUOUS"):
            self._run()
        self.assertTrue(foreign.is_dir())
        self.assertFalse(self.target.exists())

    def test_read_only_validation_rejects_effective_byte_tamper(self) -> None:
        created = self._run()
        effective = created.patch_plan.data["artifacts"][0]["effective_artifact"]
        path = self.target / Path(effective["path"])
        path.write_bytes(path.read_bytes() + b"tamper")
        with self.assertRaisesRegex(runtime.ConceptionRevisionError, "REV_PATCH_STALE"):
            runtime.validate_conception_revision_run(self.target)

    def test_b0_authority_revision_gate_resolves_only_three_effective_domains(self) -> None:
        created = self._run()
        finalization, effective, _, _ = baseline._authority_revision_material(
            self.target,
            self.target / "authority-revision" / "finalization.json",
            run_id=self.arguments["run_id"],
            runtime=created.production.store.runtime,
        )
        self.assertEqual("authority_revision", finalization["source_kind"])
        self.assertEqual({"I3", "I4", "I5"}, set(effective))
        self.assertTrue(all(path.is_file() for path in effective.values()))

    def test_promoted_revision_context_can_issue_the_real_b0_work_order(self) -> None:
        created = self._run()
        gate, order = orchestrator.issue_stage_work(
            created.production,
            action="B0",
            inputs={"authority_revision": created.finalization.reference},
        )
        self.assertEqual("B0", gate.data["target_stage"])
        self.assertEqual("baseline-controller", order.data["required_actor"])
        self.assertEqual(created.production.state.reference, order.data["state"])


if __name__ == "__main__":
    unittest.main()
