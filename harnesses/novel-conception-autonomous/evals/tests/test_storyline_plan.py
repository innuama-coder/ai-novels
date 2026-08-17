from __future__ import annotations

import copy
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
subject = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.storyline_plan"
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
AUTHORITATIVE_SCHEMAS = (
    REPOSITORY_ROOT
    / "harnesses"
    / "novel-conception-autonomous"
    / "evals"
    / "schemas"
)


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rt.canonical_json(value), encoding="utf-8", newline="")


class StorylinePlanContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="storyline-plan-contract-"
        )
        self.repository = Path(self.temporary.name) / "repository"
        self.evals = self.repository / "evals"
        schema_root = self.evals / "schemas"
        schema_root.mkdir(parents=True)
        for name in (
            "eval-case-manifest.v1.schema.json",
            "storyline-plan.v1.schema.json",
        ):
            (schema_root / name).write_bytes(
                (AUTHORITATIVE_SCHEMAS / name).read_bytes()
            )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _fixture() -> dict[str, Any]:
        return {
            "schema_version": "TEST",
            "fixture_id": "minimal-storyline-case",
            "run_id": "RUN-STORYLINE-PLAN-001",
            "interviews": [
                {
                    "control_id": "CTRL-PUBLIC",
                    "hardness": "author_locked",
                    "authority": "author_locked",
                    "heading": "Public obligation",
                    "value": "Public promise must remain consequential.",
                },
                {
                    "control_id": "CTRL-PRIVATE",
                    "hardness": "author_locked",
                    "authority": "author_locked",
                    "heading": "Private pressure",
                    "value": "Private survival rewards breaking the promise.",
                },
                {
                    "control_id": "CTRL-OPEN",
                    "hardness": "author_open",
                    "authority": "author_open",
                    "heading": "Unresolved reform",
                    "value": "Whether inherited rank survives remains unresolved.",
                },
            ],
            "semantic_assertions": [
                {
                    "anchor_id": "ANCHOR-LOCKED",
                    "required_source_ids": [
                        "CTRL-PUBLIC",
                        "CTRL-PRIVATE",
                    ],
                    "required_terms": [
                        "Public promise must remain consequential.",
                        "Private survival rewards breaking the promise.",
                    ],
                    "assurance": "author_locked",
                },
                {
                    "anchor_id": "ANCHOR-DERIVED",
                    "required_source_ids": ["CTRL-PUBLIC"],
                    "required_terms": ["two approaches converge"],
                    "assurance": "derived_unsealed",
                },
                {
                    "anchor_id": "ANCHOR-OPEN",
                    "required_source_ids": ["CTRL-OPEN"],
                    "required_terms": [
                        "Whether inherited rank survives remains unresolved."
                    ],
                    "required_status": "author_open",
                    "assurance": "author_open",
                },
            ],
        }

    @staticmethod
    def _requirement(
        stage: str,
        prefix: str,
        index: int,
        line_id: str,
        demand_ids: list[str],
    ) -> dict[str, Any]:
        return {
            "id": f"{prefix}-{index:03d}",
            "target_stage": stage,
            "line_id": line_id,
            "demand_ids": demand_ids,
            "responsibility": f"{stage} must realize {line_id}.",
            "required_capability": f"Carry the state changes of {line_id}.",
            "constraints": [f"Preserve every demand assigned to {line_id}."],
            "acceptance_checks": [f"The result binds {line_id} explicitly."],
            "downstream_freedom": "Concrete realization remains downstream.",
        }

    def _plan(
        self,
        fixture: dict[str, Any],
        fixture_reference: dict[str, str],
    ) -> dict[str, Any]:
        line_ids = ["SL-OPTIONAL", "SL-MAIN"]
        downstream = {}
        for stage, prefix in (
            ("W1", "WR"),
            ("E1", "END"),
            ("T1", "EVD"),
            ("C1", "CHD"),
        ):
            downstream[stage] = [
                self._requirement(
                    stage,
                    prefix,
                    1,
                    "SL-OPTIONAL",
                    ["SLD-OPEN"],
                ),
                self._requirement(
                    stage,
                    prefix,
                    2,
                    "SL-MAIN",
                    ["SLD-PUBLIC", "SLD-PRIVATE"],
                ),
            ]
        return {
            "schema_version": "1.0",
            "kind": "eval-owned-autonomous-storyline-plan",
            "plan_id": "SPLAN-MINIMAL-001",
            "fixture_binding": {
                "fixture": fixture_reference,
                "fixture_id": fixture["fixture_id"],
                "run_id": fixture["run_id"],
                "control_inventory_sha256": rt.canonical_sha256(
                    subject.control_inventory(fixture)
                ),
                "anchor_inventory_sha256": rt.canonical_sha256(
                    subject.anchor_inventory(fixture)
                ),
            },
            "ownership": {
                "owner": "eval_harness",
                "authority": "eval_owned_autonomous_proposal",
                "author_authority": False,
                "usage": "S1_phase_payload_only",
            },
            "design_decisions": [
                {
                    "id": "DEC-CONVERGENCE",
                    "source_control_ids": [
                        "CTRL-PUBLIC",
                        "CTRL-PRIVATE",
                    ],
                    "source_anchor_ids": [
                        "ANCHOR-LOCKED",
                        "ANCHOR-DERIVED",
                    ],
                    "gap": "Choose how the competing approaches meet.",
                    "options": [
                        "Keep the approaches separate.",
                        "Let two approaches converge.",
                    ],
                    "selection": "Let two approaches converge.",
                    "authority_basis": (
                        "This is a reversible evaluation-owned structural proposal."
                    ),
                    "reversibility": "reversible",
                    "projection_ids": ["SL-MAIN", "SLC-REVEAL"],
                }
            ],
            "demands": [
                {
                    "id": "SLD-PUBLIC",
                    "source_control_id": "CTRL-PUBLIC",
                    "obligation": (
                        "Public obligation: Public promise must remain "
                        "consequential."
                    ),
                    "disposition": "merged",
                    "realization_line_ids": ["SL-MAIN"],
                    "rationale": "The public obligation belongs to the main choice.",
                },
                {
                    "id": "SLD-PRIVATE",
                    "source_control_id": "CTRL-PRIVATE",
                    "obligation": (
                        "Private pressure: Private survival rewards breaking "
                        "the promise."
                    ),
                    "disposition": "merged",
                    "realization_line_ids": ["SL-MAIN"],
                    "rationale": "The private pressure tests the same main choice.",
                },
                {
                    "id": "SLD-OPEN",
                    "source_control_id": "CTRL-OPEN",
                    "obligation": (
                        "Unresolved reform: Whether inherited rank survives "
                        "remains unresolved."
                    ),
                    "disposition": "optional_melody",
                    "realization_line_ids": ["SL-OPTIONAL"],
                    "rationale": "The unresolved reform remains an optional echo.",
                },
            ],
            "lines": [
                {
                    "id": "SL-OPTIONAL",
                    "type": "optional_melody",
                    "responsibility": (
                        "Keep Whether inherited rank survives remains unresolved."
                    ),
                    "actor_slot_ids": ["SLOT-COMMUNITY"],
                    "demand_ids": ["SLD-OPEN"],
                    "goal": "Expose the reform question without deciding it.",
                    "pressure": "The unresolved rank question survives the crisis.",
                    "states": [
                        {
                            "id": "SLS-OPTIONAL-START",
                            "phase": "start",
                            "description": "The reform question is latent.",
                        },
                        {
                            "id": "SLS-OPTIONAL-END",
                            "phase": "end",
                            "description": "The reform question remains unresolved.",
                        },
                    ],
                    "connection_ids": ["SLC-REVEAL"],
                    "decision_ids": [],
                    "downstream_freedom": "Its later prominence remains optional.",
                },
                {
                    "id": "SL-MAIN",
                    "type": "main",
                    "responsibility": (
                        "Test Public promise must remain consequential. against "
                        "Private survival rewards breaking the promise."
                    ),
                    "actor_slot_ids": ["SLOT-CUSTODIAN"],
                    "demand_ids": ["SLD-PUBLIC", "SLD-PRIVATE"],
                    "goal": "Make a consequential stewardship choice.",
                    "pressure": "Private survival makes breach immediately rewarding.",
                    "states": [
                        {
                            "id": "SLS-MAIN-START",
                            "phase": "start",
                            "description": "The public promise still appears binding.",
                        },
                        {
                            "id": "SLS-MAIN-CHANGE",
                            "phase": "change",
                            "description": "The two approaches converge under proof.",
                        },
                        {
                            "id": "SLS-MAIN-END",
                            "phase": "end",
                            "description": "The choice creates a public consequence.",
                        },
                    ],
                    "connection_ids": ["SLC-REVEAL"],
                    "decision_ids": ["DEC-CONVERGENCE"],
                    "downstream_freedom": "Events and concrete places remain open.",
                },
            ],
            "connections": [
                {
                    "id": "SLC-REVEAL",
                    "type": "reveal",
                    "relation": "associative",
                    "from_line_id": "SL-OPTIONAL",
                    "to_line_id": "SL-MAIN",
                    "from_state_id": "SLS-OPTIONAL-END",
                    "to_state_id": "SLS-MAIN-CHANGE",
                    "responsibility": (
                        "The unresolved public question makes two approaches "
                        "converge."
                    ),
                }
            ],
            "architecture": {
                "id": "ARCH-MINIMAL",
                "main_line_id": "SL-MAIN",
                "entry_line_ids": ["SL-MAIN"],
                "terminal_line_ids": ["SL-MAIN"],
                "subject": "Shared obligation under private survival pressure.",
                "opening_condition": "The public rule is disputed.",
                "development_logic": "Pressure turns dispute into a tested choice.",
                "turning_logic": "Proof makes two approaches converge.",
                "resolution_condition": "The choice has a public consequence.",
                "theme_test": "The ending tests stewardship without closing reform.",
                "line_order": line_ids,
            },
            "anchor_bindings": [
                {
                    "id": "AB-LOCKED",
                    "semantic_anchor_id": "ANCHOR-LOCKED",
                    "assurance": "author_locked",
                    "source_control_ids": [
                        "CTRL-PUBLIC",
                        "CTRL-PRIVATE",
                    ],
                    "target_ids": ["SL-MAIN"],
                    "treatment": "locked_constraint",
                    "evidence": "Both locked meanings appear in the main line.",
                },
                {
                    "id": "AB-DERIVED",
                    "semantic_anchor_id": "ANCHOR-DERIVED",
                    "assurance": "derived_unsealed",
                    "source_control_ids": ["CTRL-PUBLIC"],
                    "target_ids": ["SLC-REVEAL"],
                    "treatment": "reversible_hypothesis",
                    "evidence": "The convergence remains an eval hypothesis.",
                },
                {
                    "id": "AB-OPEN",
                    "semantic_anchor_id": "ANCHOR-OPEN",
                    "assurance": "author_open",
                    "source_control_ids": ["CTRL-OPEN"],
                    "target_ids": ["OPEN-REFORM", "SL-OPTIONAL"],
                    "treatment": "preserved_open",
                    "evidence": "No outcome is selected.",
                },
            ],
            "consistency_evidence": [
                {
                    "id": "SLCHECK-TIME",
                    "dimension": "time",
                    "line_ids": line_ids,
                    "witness_ids": ["SLS-OPTIONAL-END", "SLC-REVEAL"],
                    "claim": "The reveal occurs after the optional line changes.",
                    "failure_condition": "The target change precedes the reveal.",
                },
                {
                    "id": "SLCHECK-CAUSALITY",
                    "dimension": "causality",
                    "line_ids": line_ids,
                    "witness_ids": ["SLD-PUBLIC", "DEC-CONVERGENCE"],
                    "claim": "The public demand motivates the main choice.",
                    "failure_condition": "The main choice ignores the demand.",
                },
                {
                    "id": "SLCHECK-INFORMATION",
                    "dimension": "information",
                    "line_ids": line_ids,
                    "witness_ids": ["AB-LOCKED", "SLS-MAIN-CHANGE"],
                    "claim": "Locked information is present before the choice.",
                    "failure_condition": "The choice uses unavailable information.",
                },
                {
                    "id": "SLCHECK-AUTHORITY",
                    "dimension": "authority",
                    "line_ids": line_ids,
                    "witness_ids": ["AB-OPEN", "OPEN-REFORM"],
                    "claim": "The reform question remains author-open.",
                    "failure_condition": "The plan resolves the reform question.",
                },
                {
                    "id": "SLCHECK-STATE",
                    "dimension": "state",
                    "line_ids": line_ids,
                    "witness_ids": ["SLS-MAIN-START", "SLC-REVEAL"],
                    "claim": "Every connection binds declared states.",
                    "failure_condition": "A connection names an absent state.",
                },
                {
                    "id": "SLCHECK-THEME",
                    "dimension": "theme",
                    "line_ids": line_ids,
                    "witness_ids": ["SLD-PUBLIC", "ARCH-MINIMAL"],
                    "claim": "The main choice tests shared stewardship.",
                    "failure_condition": "The ending avoids the public obligation.",
                },
            ],
            "downstream_requirements": downstream,
            "open_control_treatments": [
                {
                    "id": "OPEN-REFORM",
                    "source_control_id": "CTRL-OPEN",
                    "status": "preserved_open",
                    "question": (
                        "Whether inherited rank survives remains unresolved."
                    ),
                    "target_ids": ["SL-OPTIONAL"],
                }
            ],
        }

    def _publish(
        self,
        name: str,
        *,
        mutate_fixture: Callable[[dict[str, Any]], None] | None = None,
        mutate_plan: Callable[[dict[str, Any]], None] | None = None,
        mutate_manifest: Callable[[dict[str, Any]], None] | None = None,
    ) -> Path:
        case_root = self.evals / "fixtures" / name
        fixture = self._fixture()
        if mutate_fixture is not None:
            mutate_fixture(fixture)
        fixture_path = case_root / "fixture.json"
        _write(fixture_path, fixture)
        fixture_reference = rt.artifact_reference(
            fixture_path, root=self.evals
        )
        plan = self._plan(fixture, fixture_reference)
        if mutate_plan is not None:
            mutate_plan(plan)
        plan_path = case_root / "storyline-plan.v1.json"
        _write(plan_path, plan)
        manifest = {
            "schema_version": "1.0",
            "kind": "novel-conception-eval-case",
            "manifest_id": f"ECASE-{name.upper()}",
            "fixture": fixture_reference,
            "storyline_plan": rt.artifact_reference(
                plan_path, root=self.evals
            ),
            "storyline_plan_schema": rt.artifact_reference(
                self.evals / "schemas" / "storyline-plan.v1.schema.json",
                root=self.evals,
            ),
            "storyline_quality_gate": {
                "path": f"fixtures/{name}/quality-gate.v1.json",
                "sha256": "0" * 64,
            },
            "storyline_quality_gate_schema": {
                "path": (
                    "schemas/"
                    "storyline-proposal-quality-gate.v1.schema.json"
                ),
                "sha256": "0" * 64,
            },
        }
        if mutate_manifest is not None:
            mutate_manifest(manifest)
        manifest_path = self.evals / "manifests" / f"{name}.v1.json"
        _write(manifest_path, manifest)
        return manifest_path

    def _load(self, path: Path) -> Any:
        return subject.load_eval_case(
            path,
            repository_root=self.repository,
            evals_root=self.evals,
        )

    def test_valid_case_loads_with_exact_inventory_and_relations(self) -> None:
        loaded = self._load(self._publish("valid"))
        self.assertEqual("ready", loaded.validation["status"])
        self.assertEqual(3, loaded.validation["control_count"])
        self.assertEqual(3, loaded.validation["anchor_count"])
        self.assertEqual(2, loaded.validation["line_count"])
        self.assertEqual(
            sorted(subject.CONSISTENCY_DIMENSIONS),
            loaded.validation["consistency_dimensions"],
        )
        self.assertEqual(
            ["W1", "E1", "T1", "C1"],
            loaded.validation["downstream_stages"],
        )

    def test_plan_id_is_part_of_the_global_identity_registry(self) -> None:
        def collide_control(fixture: dict[str, Any]) -> None:
            fixture["interviews"][0]["control_id"] = "SPLAN-MINIMAL-001"
            for anchor in fixture["semantic_assertions"]:
                anchor["required_source_ids"] = [
                    "SPLAN-MINIMAL-001"
                    if source_id == "CTRL-PUBLIC"
                    else source_id
                    for source_id in anchor["required_source_ids"]
                ]

        mutations = {
            "fixture": {
                "mutate_fixture": lambda value: value.update(
                    {"fixture_id": "SPLAN-MINIMAL-001"}
                )
            },
            "control": {"mutate_fixture": collide_control},
            "anchor": {
                "mutate_fixture": lambda value: value[
                    "semantic_assertions"
                ][0].update({"anchor_id": "SPLAN-MINIMAL-001"})
            },
            "nested-plan-id": {
                "mutate_plan": lambda value: value[
                    "downstream_requirements"
                ]["W1"][0].update({"id": "SPLAN-MINIMAL-001"})
            },
        }
        for name, kwargs in mutations.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                subject.StorylinePlanError,
                "STORYLINE_PLAN_ID_(COLLISION|DUPLICATE)",
            ):
                self._load(self._publish(f"plan-id-{name}", **kwargs))

    def test_relation_validator_rechecks_fixed_ownership(self) -> None:
        loaded = self._load(self._publish("ownership-relation"))
        plan = copy.deepcopy(loaded.plan)
        plan["ownership"]["author_authority"] = True
        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_OWNERSHIP_INVALID",
        ):
            subject.validate_storyline_plan(
                plan,
                loaded.fixture,
                fixture_reference=loaded.manifest["fixture"],
            )

    def test_design_selection_must_be_one_declared_option(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["design_decisions"][0]["selection"] = (
                "Combine both choices without declaring a combined option."
            )

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_DECISION_SELECTION_INVALID",
        ):
            self._load(
                self._publish("selection-not-option", mutate_plan=mutate)
            )

    def test_schema_rejects_extra_manifest_or_plan_fields(self) -> None:
        for target in ("manifest", "plan"):
            with self.subTest(target=target):
                kwargs: dict[str, Any] = {}
                kwargs[f"mutate_{target}"] = lambda value: value.update(
                    {"unexpected": True}
                )
                path = self._publish(f"extra-{target}", **kwargs)
                with self.assertRaisesRegex(
                    subject.StorylinePlanError,
                    "STORYLINE_PLAN_.*SCHEMA_INVALID",
                ):
                    self._load(path)

    def test_manifest_requires_explicit_plan_reference(self) -> None:
        path = self._publish(
            "no-plan-reference",
            mutate_manifest=lambda value: value.pop("storyline_plan"),
        )
        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_MANIFEST_SCHEMA_INVALID",
        ):
            self._load(path)

    def test_manifest_rejects_unsafe_paths_and_hash_drift(self) -> None:
        mutations = {
            "traversal": lambda value: value["storyline_plan"].update(
                {"path": "../storyline-plan.v1.json"}
            ),
            "backslash": lambda value: value["storyline_plan"].update(
                {"path": "fixtures\\case\\storyline-plan.v1.json"}
            ),
            "absolute": lambda value: value["storyline_plan"].update(
                {"path": "/tmp/storyline-plan.v1.json"}
            ),
            "hash": lambda value: value["storyline_plan"].update(
                {"sha256": "0" * 64}
            ),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name):
                path = self._publish(
                    f"bad-path-{name}", mutate_manifest=mutation
                )
                with self.assertRaises(subject.StorylinePlanError):
                    self._load(path)

    def test_manifest_cannot_substitute_another_plan_schema_path(self) -> None:
        alternate = self.evals / "schemas" / "alternate.schema.json"
        alternate.write_bytes(
            (
                self.evals
                / "schemas"
                / "storyline-plan.v1.schema.json"
            ).read_bytes()
        )

        def mutate(value: dict[str, Any]) -> None:
            value["storyline_plan_schema"] = rt.artifact_reference(
                alternate, root=self.evals
            )

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_SCHEMA_REFERENCE_INVALID",
        ):
            self._load(
                self._publish("alternate-schema", mutate_manifest=mutate)
            )

    def test_schema_files_are_code_pinned_before_use(self) -> None:
        manifest_path = self._publish("trusted-schema")
        manifest_schema = (
            self.evals / "schemas" / "eval-case-manifest.v1.schema.json"
        )
        original_manifest_schema = manifest_schema.read_bytes()
        manifest_schema.write_bytes(original_manifest_schema + b"\n")
        try:
            with self.assertRaisesRegex(
                subject.StorylinePlanError,
                "STORYLINE_PLAN_MANIFEST_SCHEMA_UNTRUSTED",
            ):
                self._load(manifest_path)
        finally:
            manifest_schema.write_bytes(original_manifest_schema)

        plan_schema = (
            self.evals / "schemas" / "storyline-plan.v1.schema.json"
        )
        original_plan_schema = plan_schema.read_bytes()
        plan_schema.write_bytes(original_plan_schema + b"\n")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["storyline_plan_schema"]["sha256"] = rt.sha256_file(
            plan_schema
        )
        _write(manifest_path, manifest)
        try:
            with self.assertRaisesRegex(
                subject.StorylinePlanError,
                "STORYLINE_PLAN_SCHEMA_REFERENCE_INVALID",
            ):
                self._load(manifest_path)
        finally:
            plan_schema.write_bytes(original_plan_schema)

    def test_manifest_plan_schema_self_hash_must_equal_code_pin(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["storyline_plan_schema"]["sha256"] = "0" * 64

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_SCHEMA_REFERENCE_INVALID",
        ):
            self._load(
                self._publish(
                    "schema-self-hash", mutate_manifest=mutate
                )
            )

    def test_duplicate_json_keys_fail_closed_for_all_case_documents(
        self,
    ) -> None:
        for target, code in (
            ("manifest", "STORYLINE_PLAN_MANIFEST_UNREADABLE"),
            ("fixture", "STORYLINE_PLAN_FIXTURE_UNREADABLE"),
            ("plan", "STORYLINE_PLAN_UNREADABLE"),
        ):
            with self.subTest(target=target):
                manifest_path = self._publish(f"duplicate-key-{target}")
                manifest = json.loads(
                    manifest_path.read_text(encoding="utf-8")
                )
                if target == "manifest":
                    target_path = manifest_path
                    duplicate_value = '"1.0"'
                else:
                    reference_name = (
                        "fixture"
                        if target == "fixture"
                        else "storyline_plan"
                    )
                    target_path = self.evals.joinpath(
                        *manifest[reference_name]["path"].split("/")
                    )
                    duplicate_value = (
                        '"TEST"' if target == "fixture" else '"1.0"'
                    )
                raw = target_path.read_text(encoding="utf-8")
                target_path.write_text(
                    '{"schema_version":'
                    + duplicate_value
                    + ","
                    + raw[1:],
                    encoding="utf-8",
                    newline="",
                )
                if target != "manifest":
                    reference_name = (
                        "fixture"
                        if target == "fixture"
                        else "storyline_plan"
                    )
                    manifest[reference_name]["sha256"] = rt.sha256_file(
                        target_path
                    )
                    _write(manifest_path, manifest)
                with self.assertRaisesRegex(
                    subject.StorylinePlanError, code
                ):
                    self._load(manifest_path)

    def test_symbolic_links_are_not_case_artifacts(self) -> None:
        manifest_path = self._publish("symlink-plan")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        plan_path = self.evals.joinpath(
            *manifest["storyline_plan"]["path"].split("/")
        )
        real_plan = plan_path.with_name("real-storyline-plan.v1.json")
        real_plan.write_bytes(plan_path.read_bytes())
        plan_path.unlink()
        try:
            plan_path.symlink_to(real_plan)
        except OSError as error:
            self.skipTest(f"file symlinks are unavailable: {error}")
        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_REFERENCE_SYMLINK_INVALID",
        ):
            self._load(manifest_path)

    def test_loaded_documents_are_defensive_copies(self) -> None:
        manifest_path = self._publish("defensive-copy")
        first = self._load(manifest_path)
        first.manifest["kind"] = "mutated"
        first.fixture["interviews"][0]["value"] = "mutated"
        first.plan["architecture"]["subject"] = "mutated"
        first.validation["status"] = "mutated"

        second = self._load(manifest_path)
        self.assertEqual(
            "novel-conception-eval-case", second.manifest["kind"]
        )
        self.assertEqual(
            "Public promise must remain consequential.",
            second.fixture["interviews"][0]["value"],
        )
        self.assertEqual(
            "Shared obligation under private survival pressure.",
            second.plan["architecture"]["subject"],
        )
        self.assertEqual("ready", second.validation["status"])

    def test_each_json_artifact_uses_one_hash_parse_snapshot(self) -> None:
        manifest_path = self._publish("single-read-snapshot")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_paths = {
            manifest_path.resolve(),
            (
                self.evals
                / "schemas"
                / "eval-case-manifest.v1.schema.json"
            ).resolve(),
            self.evals.joinpath(
                *manifest["fixture"]["path"].split("/")
            ).resolve(),
            self.evals.joinpath(
                *manifest["storyline_plan"]["path"].split("/")
            ).resolve(),
            self.evals.joinpath(
                *manifest["storyline_plan_schema"]["path"].split("/")
            ).resolve(),
        }
        original = Path.read_bytes
        calls: dict[Path, int] = {}

        def counted(path: Path) -> bytes:
            resolved = path.resolve()
            calls[resolved] = calls.get(resolved, 0) + 1
            raw = original(path)
            if calls[resolved] > 1:
                return b'{"drifted":true}'
            return raw

        with mock.patch.object(Path, "read_bytes", counted):
            loaded = self._load(manifest_path)
        self.assertEqual("ready", loaded.validation["status"])
        self.assertEqual(
            {path: 1 for path in expected_paths},
            {path: calls[path] for path in expected_paths},
        )

    def test_fixture_binding_and_inventories_fail_closed(self) -> None:
        mutations = {
            "fixture-id": lambda value: value["fixture_binding"].update(
                {"fixture_id": "another-fixture"}
            ),
            "run-id": lambda value: value["fixture_binding"].update(
                {"run_id": "another-run"}
            ),
            "control-inventory": lambda value: value[
                "fixture_binding"
            ].update({"control_inventory_sha256": "0" * 64}),
            "anchor-inventory": lambda value: value[
                "fixture_binding"
            ].update({"anchor_inventory_sha256": "0" * 64}),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaisesRegex(
                subject.StorylinePlanError,
                "STORYLINE_PLAN_FIXTURE_BINDING_MISMATCH",
            ):
                self._load(
                    self._publish(
                        f"binding-{name}", mutate_plan=mutation
                    )
                )

    def test_demand_exact_coverage_and_meaning_are_enforced(self) -> None:
        mutations = {
            "missing": lambda value: value["demands"].pop(),
            "duplicate-source": lambda value: value["demands"][2].update(
                {"source_control_id": "CTRL-PUBLIC"}
            ),
            "duplicate-id": lambda value: value["demands"][2].update(
                {"id": "SLD-PUBLIC"}
            ),
            "missing-meaning": lambda value: value["demands"][0].update(
                {"obligation": "A generic obligation."}
            ),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaises(
                subject.StorylinePlanError
            ):
                self._load(
                    self._publish(f"demand-{name}", mutate_plan=mutation)
                )

    def test_not_applicable_is_explicitly_unsupported_in_v1(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["demands"][2]["disposition"] = "not_applicable"

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_NOT_APPLICABLE_UNSUPPORTED",
        ):
            self._load(
                self._publish("not-applicable", mutate_plan=mutate)
            )

    def test_line_assignment_and_disposition_are_enforced(self) -> None:
        mutations = {
            "assignment": lambda value: value["lines"][0][
                "demand_ids"
            ].append("SLD-PUBLIC"),
            "merged-single": lambda value: value["lines"][0].update(
                {"type": "supporting"}
            )
            or value["demands"][2].update({"disposition": "merged"}),
            "optional-type": lambda value: value["lines"][0].update(
                {"type": "supporting"}
            ),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaises(
                subject.StorylinePlanError
            ):
                self._load(
                    self._publish(f"line-{name}", mutate_plan=mutation)
                )

    def test_topology_state_and_architecture_fail_closed(self) -> None:
        mutations = {
            "no-main": lambda value: value["lines"][1].update(
                {"type": "supporting"}
            ),
            "state-order": lambda value: value["lines"][1]["states"][
                0
            ].update({"phase": "change"}),
            "dangling-state": lambda value: value["connections"][0].update(
                {"from_state_id": "SLS-NOT-THERE"}
            ),
            "reciprocal": lambda value: value["lines"][0].update(
                {"connection_ids": []}
            ),
            "line-order": lambda value: value["architecture"].update(
                {"line_order": ["SL-MAIN"]}
            ),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaises(
                subject.StorylinePlanError
            ):
                self._load(
                    self._publish(f"topology-{name}", mutate_plan=mutation)
                )

    def test_association_does_not_constrain_line_order(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["architecture"]["line_order"] = [
                "SL-MAIN",
                "SL-OPTIONAL",
            ]

        loaded = self._load(
            self._publish("association-order", mutate_plan=mutate)
        )
        self.assertEqual("ready", loaded.validation["status"])

    def test_optional_causal_link_is_rejected(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["connections"][0]["relation"] = "causal"

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_OPTIONAL_CAUSAL_LINK_FORBIDDEN",
        ):
            self._load(
                self._publish("optional-causal", mutate_plan=mutate)
            )

    def test_legacy_connection_without_relation_is_not_guessed(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["connections"][0].pop("relation")

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_SCHEMA_INVALID",
        ):
            self._load(
                self._publish("legacy-connection", mutate_plan=mutate)
            )

    def test_optional_line_requires_structural_association(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["connections"] = []
            for line in value["lines"]:
                line["connection_ids"] = []

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_OPTIONAL_ASSOCIATION_MISSING",
        ):
            self._load(
                self._publish("optional-unattached", mutate_plan=mutate)
            )

    def test_structural_line_requires_causal_path_to_main(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["lines"][0]["type"] = "supporting"
            value["demands"][2]["disposition"] = "independent_line"

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_STRUCTURAL_CAUSAL_CLOSURE_MISSING",
        ):
            self._load(
                self._publish("structural-association", mutate_plan=mutate)
            )

    def test_causal_line_order_is_topological(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["lines"][0]["type"] = "supporting"
            value["demands"][2]["disposition"] = "independent_line"
            value["connections"][0]["relation"] = "causal"
            value["architecture"]["line_order"] = [
                "SL-MAIN",
                "SL-OPTIONAL",
            ]
            value["architecture"]["entry_line_ids"] = ["SL-OPTIONAL"]

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_ARCHITECTURE_INVALID",
        ):
            self._load(
                self._publish("causal-order", mutate_plan=mutate)
            )

    def test_anchor_coverage_assurance_and_terms_are_enforced(self) -> None:
        mutations = {
            "missing": lambda value: value["anchor_bindings"].pop(),
            "assurance": lambda value: value["anchor_bindings"][1].update(
                {"assurance": "author_locked"}
            ),
            "treatment": lambda value: value["anchor_bindings"][2].update(
                {"treatment": "locked_constraint"}
            ),
            "term": lambda value: value["connections"][0].update(
                {"responsibility": "A generic structural link."}
            ),
            "source": lambda value: value["anchor_bindings"][2].update(
                {"source_control_ids": ["CTRL-PUBLIC"]}
            ),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaises(
                subject.StorylinePlanError
            ):
                self._load(
                    self._publish(f"anchor-{name}", mutate_plan=mutation)
                )

    def test_author_open_binding_cannot_cross_bind_another_treatment(
        self,
    ) -> None:
        def mutate_fixture(value: dict[str, Any]) -> None:
            value["interviews"][1].update(
                {
                    "hardness": "author_open",
                    "authority": "author_open",
                }
            )
            value["semantic_assertions"][0]["assurance"] = "author_open"

        def mutate_plan(value: dict[str, Any]) -> None:
            decision = value["design_decisions"][0]
            decision["source_control_ids"] = ["CTRL-PUBLIC"]
            decision["source_anchor_ids"] = ["ANCHOR-DERIVED"]
            locked_binding = value["anchor_bindings"][0]
            locked_binding["assurance"] = "author_open"
            locked_binding["treatment"] = "preserved_open"
            locked_binding["target_ids"].append("OPEN-REFORM")
            open_binding = value["anchor_bindings"][2]
            open_binding["target_ids"] = ["OPEN-PRIVATE", "SL-OPTIONAL"]
            value["open_control_treatments"].append(
                {
                    "id": "OPEN-PRIVATE",
                    "source_control_id": "CTRL-PRIVATE",
                    "status": "preserved_open",
                    "question": (
                        "Private survival rewards breaking the promise."
                    ),
                    "target_ids": ["SL-MAIN"],
                }
            )

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_ANCHOR_OPEN_TREATMENT_MISMATCH",
        ):
            self._load(
                self._publish(
                    "open-cross-binding",
                    mutate_fixture=mutate_fixture,
                    mutate_plan=mutate_plan,
                )
            )

    def test_open_controls_cannot_be_omitted_or_decided(self) -> None:
        mutations = {
            "omitted": lambda value: value.update(
                {"open_control_treatments": []}
            ),
            "question": lambda value: value[
                "open_control_treatments"
            ][0].update({"question": "The rank is abolished."}),
            "decision-source": lambda value: value["design_decisions"][
                0
            ]["source_anchor_ids"].append("ANCHOR-OPEN"),
            "decision-control": lambda value: value[
                "design_decisions"
            ][0]["source_control_ids"].append("CTRL-OPEN"),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaises(
                subject.StorylinePlanError
            ):
                self._load(
                    self._publish(f"open-{name}", mutate_plan=mutation)
                )

    def test_derived_unsealed_requires_a_reversible_decision(self) -> None:
        def mutate(value: dict[str, Any]) -> None:
            value["design_decisions"][0]["reversibility"] = "costly"

        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_DERIVED_AUTHORITY_VIOLATION",
        ):
            self._load(
                self._publish("derived-locked", mutate_plan=mutate)
            )

    def test_consistency_requires_all_dimensions_lines_and_valid_witnesses(
        self,
    ) -> None:
        mutations = {
            "missing-dimension": lambda value: value[
                "consistency_evidence"
            ].pop(),
            "line-coverage": lambda value: value[
                "consistency_evidence"
            ][0].update({"line_ids": ["SL-MAIN"]}),
            "wrong-witness": lambda value: value[
                "consistency_evidence"
            ][0].update({"witness_ids": ["DEC-CONVERGENCE"]}),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaises(
                subject.StorylinePlanError
            ):
                self._load(
                    self._publish(
                        f"consistency-{name}", mutate_plan=mutation
                    )
                )

    def test_downstream_requirements_are_exact_per_stage_and_line(self) -> None:
        mutations = {
            "missing-line": lambda value: value[
                "downstream_requirements"
            ]["W1"].pop(),
            "wrong-stage": lambda value: value[
                "downstream_requirements"
            ]["E1"][0].update({"target_stage": "W1"}),
            "wrong-demands": lambda value: value[
                "downstream_requirements"
            ]["T1"][1].update({"demand_ids": ["SLD-PUBLIC"]}),
        }
        for name, mutation in mutations.items():
            with self.subTest(name=name), self.assertRaises(
                subject.StorylinePlanError
            ):
                self._load(
                    self._publish(
                        f"downstream-{name}", mutate_plan=mutation
                    )
                )

    def test_manifest_itself_must_be_inside_declared_evals_root(self) -> None:
        manifest = self._publish("manifest-outside")
        outside = self.repository / "outside-manifest.json"
        outside.write_bytes(manifest.read_bytes())
        with self.assertRaisesRegex(
            subject.StorylinePlanError,
            "STORYLINE_PLAN_MANIFEST_OUTSIDE_EVALS",
        ):
            self._load(outside)

    def test_formal_fixture_bytes_remain_locked(self) -> None:
        fixture_root = (
            REPOSITORY_ROOT
            / "harnesses"
            / "novel-conception-autonomous"
            / "evals"
            / "fixtures"
        )
        self.assertEqual(
            "0867a1a2d56bfa72ebccc840d2de835c7e247a9b15e1896b3ca7ac54bdce0f28",
            rt.sha256_file(fixture_root / "generic" / "fixture.json"),
        )
        self.assertEqual(
            "c2cac509af0549dfac3d31045c812226c19e9c6dd95d17cc5ebb22f882129798",
            rt.sha256_file(fixture_root / "duanxian" / "fixture.json"),
        )

    def test_formal_fixture_control_and_anchor_inventories_normalize(
        self,
    ) -> None:
        fixture_root = (
            REPOSITORY_ROOT
            / "harnesses"
            / "novel-conception-autonomous"
            / "evals"
            / "fixtures"
        )
        expected = {
            "generic": (6, 3),
            "duanxian": (22, 16),
        }
        for name, counts in expected.items():
            with self.subTest(name=name):
                fixture = json.loads(
                    (fixture_root / name / "fixture.json").read_text(
                        encoding="utf-8"
                    )
                )
                controls = subject.control_inventory(fixture)
                anchors = subject.anchor_inventory(fixture)
                self.assertEqual(counts, (len(controls), len(anchors)))
                self.assertEqual(
                    len(controls),
                    len({item["control_id"] for item in controls}),
                )
                self.assertEqual(
                    len(anchors),
                    len({item["anchor_id"] for item in anchors}),
                )


if __name__ == "__main__":
    unittest.main()
