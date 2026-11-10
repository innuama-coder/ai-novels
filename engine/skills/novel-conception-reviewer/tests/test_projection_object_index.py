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
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

q1 = importlib.import_module("skills.novel-conception-reviewer.scripts.run_v2")


def _event_pair(identifier: str = "EV-A") -> tuple[dict, dict]:
    planned = {
        "id": identifier,
        "kind": "process",
        "milestone_id": "MS-A",
        "world_time_slot": "[WT:000001]",
        "storyline_ids": ["SL-A"],
        "changed_subject": {
            "subject_id": "PSS-A",
            "before": "before",
            "after": "after",
            "subject_kind": "t1_process_record",
        },
        "environment_id": "ENV-A",
        "affordance_ids": ["AFF-A"],
        "initiating_action": "act",
        "e1_capability_step_ids": ["CSTEP-A"],
        "capability_step_occurrences": [
            {"occurrence_id": "CSO-A", "step_id": "CSTEP-A", "ordinal": 1}
        ],
        "requires_capability_fact_ids": [],
        "produces_capability_fact_ids": ["FACT-A"],
        "requires_token_instance_ids": [],
        "consumes_token_instance_ids": [],
        "produces_token_instance_ids": [],
        "lifecycle_effects": [],
        "requires_proposition_ids": [],
        "produces_proposition_ids": ["PROP-A"],
        "discloses_proposition_ids": [],
        "initial_anchor_refs": [],
        "predecessor_event_ids": [],
        "preconditions": ["ready"],
        "direct_result": "result",
        "next_pressure": "pressure",
        "source_ids": ["EVD-A"],
        "atomicity_reason": "atomic",
    }
    canonical = {
        "id": identifier,
        "responsibility": "canonical-only responsibility",
        "world_time": planned["world_time_slot"],
        "storyline_ids": copy.deepcopy(planned["storyline_ids"]),
        "environment_id": planned["environment_id"],
        "participant_slot_ids": ["SLOT-A"],
        "initiator_slot_id": "SLOT-A",
        "counter_slot_ids": [],
        "preconditions": copy.deepcopy(planned["preconditions"]),
        "initiating_action": planned["initiating_action"],
        "complication": "canonical-only complication",
        "decisive_change": "canonical-only decisive change",
        "direct_result": planned["direct_result"],
        "before_state": {"PSS-A": "before"},
        "after_state": {"PSS-A": "after"},
        "next_pressure": planned["next_pressure"],
        "requires_proposition_ids": [],
        "produces_proposition_ids": ["PROP-A"],
        "discloses_proposition_ids": [],
        "information_changes": [],
        "predecessor_event_ids": [],
        "event_kind": planned["kind"],
        "milestone_id": planned["milestone_id"],
        "subject_id": "PSS-A",
        "subject_kind": "t1_process_record",
        "affordance_ids": ["AFF-A"],
        "e1_capability_step_ids": ["CSTEP-A"],
        "capability_step_occurrences": copy.deepcopy(
            planned["capability_step_occurrences"]
        ),
        "requires_capability_fact_ids": [],
        "produces_capability_fact_ids": ["FACT-A"],
        "requires_token_instance_ids": [],
        "consumes_token_instance_ids": [],
        "produces_token_instance_ids": [],
        "lifecycle_effects": [],
        "initial_anchor_refs": [],
        "source_ids": ["EVD-A"],
        "atomicity_reason": "atomic",
    }
    return planned, canonical


def _model(version: str = "2.4") -> dict:
    planned, canonical = _event_pair()
    if version != "2.5":
        for event in (planned, canonical):
            event.pop("consumes_token_instance_ids")
            event.pop("lifecycle_effects")
    proposition = {
        "id": "PROP-A",
        "statement": "statement",
        "source_ids": ["EVD-A"],
        "audience": "both",
        "initially_true": False,
        "terminality": "ordinary",
        "initial_anchor_refs": [],
        "producer_event_ids": ["EV-A"],
    }
    edge = {
        "id": "CE-A",
        "from_event_id": "EV-A",
        "to_event_id": "EV-B",
        "edge_kind": "sequencing",
        "payload_ids": [],
        "mechanism": "sequence",
        "necessary_condition": "ordered",
    }
    return {
        "schema_version": version,
        "planned_event_registry": [planned],
        "major_events": [canonical],
        "planned_proposition_registry": [copy.deepcopy(proposition)],
        "proposition_registry": [proposition],
        "planned_causal_edges": [copy.deepcopy(edge)],
        "causal_edges": [edge],
        "other": [{"id": "EVD-A", "value": "demand"}],
    }


class ProjectionAwareObjectIndexTests(unittest.TestCase):
    def test_projection_protocol_files_are_implementation_bound(self) -> None:
        paths = q1._implementation_paths()
        self.assertIn("skill/references/isolation-protocol.md", paths)
        self.assertIn("workflow/conception-autonomous-workflow-v2.md", paths)
        self.assertTrue(all(path.is_file() for path in paths.values()))

    def test_implementation_identity_rejects_item_and_digest_mutation(self) -> None:
        current = q1._implementation_identity()
        self.assertEqual(
            current["canonical_digest"],
            q1._canonical_sha256(current["catalog"]),
        )
        item = copy.deepcopy(current)
        item["catalog"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
            q1._validate_implementation_identity(item)
        digest = copy.deepcopy(current)
        digest["canonical_digest"] = "0" * 64
        with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
            q1._validate_implementation_identity(digest)

    def test_runtime_protocol_and_schema_source_drift_are_rejected(self) -> None:
        sealed = q1._implementation_identity()
        identities = (
            "skill/run_v2.py",
            "skill/references/isolation-protocol.md",
            "schemas/conception-review.schema.json",
        )
        for identity in identities:
            with self.subTest(identity=identity):
                changed = copy.deepcopy(sealed)
                item = next(
                    item for item in changed["catalog"]
                    if item["identity"] == identity
                )
                item["sha256"] = "f" * 64
                changed["canonical_digest"] = q1._canonical_sha256(
                    changed["catalog"]
                )
                with mock.patch.object(
                    q1, "_implementation_identity", return_value=changed
                ):
                    with self.assertRaisesRegex(
                        q1.Q1Error, "Q1_IMPLEMENTATION_STALE"
                    ):
                        q1._validate_implementation_identity(sealed)

    def test_controller_validation_rejects_old_and_mutated_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            controller = Path(temporary)
            current = q1._implementation_identity()
            state = {
                "revision": 0,
                "implementation_identity": copy.deepcopy(current),
            }
            q1._write(
                controller / "frozen-inputs.json",
                {"implementation_identity": copy.deepcopy(current)},
            )
            self.assertEqual(
                q1._validate_controller_implementation(controller, state),
                current,
            )
            state["implementation_identity"]["canonical_digest"] = "0" * 64
            with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
                q1._validate_controller_implementation(controller, state)
            state["implementation_identity"] = copy.deepcopy(current)
            with mock.patch.object(
                q1,
                "_implementation_identity",
                return_value={
                    **current,
                    "canonical_digest": "f" * 64,
                },
            ):
                with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
                    q1._validate_controller_implementation(controller, state)

    def test_partial_semantic_rejects_stale_implementation_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = root / "controller"
            semantic = root / "semantic"
            controller.mkdir()
            semantic.mkdir()
            current = q1._implementation_identity()
            state = {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "revision": 0,
                "status": "semantic_running",
                "previous_state_sha256": None,
                "input_gate": {"path": "gate.json", "sha256": "1" * 64},
                "semantic_identity": {
                    "task_id": "semantic-task",
                    "thread_id": "semantic-thread",
                },
                "semantic_session_id": "SEM-1",
                "completed_phases": [],
                "implementation_identity": copy.deepcopy(current),
            }
            q1._write(controller / "state/revision-000.json", state)
            q1._write(
                controller / "frozen-inputs.json",
                {
                    "implementation_identity": {
                        **copy.deepcopy(current),
                        "canonical_digest": "0" * 64,
                    }
                },
            )
            before = q1._exact_tree(root)
            with mock.patch.dict(
                q1.os.environ,
                {
                    "CODEX_TASK_ID": "semantic-task",
                    "CODEX_THREAD_ID": "semantic-thread",
                    "Q1_TEST_AGENT_FIXTURE": "1",
                },
                clear=False,
            ):
                with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
                    q1.submit_semantic_phase(
                        controller,
                        semantic,
                        phase="review-plan",
                        payload={"review_plan": {}},
                    )
            self.assertEqual(q1._exact_tree(root), before)

    def test_handoff_start_rejects_stale_implementation_before_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = root / "controller"
            controller.mkdir()
            current = q1._implementation_identity()
            state = {
                "revision": 0,
                "status": "semantic_p1_p3_complete",
                "implementation_identity": copy.deepcopy(current),
            }
            q1._write(controller / "state/revision-000.json", state)
            stale = copy.deepcopy(current)
            stale["catalog"][0]["sha256"] = "0" * 64
            stale["canonical_digest"] = q1._canonical_sha256(stale["catalog"])
            q1._write(
                controller / "frozen-inputs.json",
                {"implementation_identity": stale},
            )
            handoff = root / "handoff"
            with mock.patch.dict(
                q1.os.environ,
                {
                    "CODEX_TASK_ID": "handoff-task",
                    "CODEX_THREAD_ID": "handoff-thread",
                    "Q1_TEST_AGENT_FIXTURE": "1",
                },
                clear=False,
            ):
                with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
                    q1.start_handoff_review(
                        controller,
                        handoff,
                        baseline_package=root / "B0",
                        storyline_package=root / "S1",
                        world_package=root / "W1",
                        environment_package=root / "E1",
                        event_package=root / "T1",
                        character_package=root / "C1",
                    )
            self.assertFalse(handoff.exists())

    def test_partial_handoff_seal_rejects_stale_implementation_zero_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            controller = root / "controller"
            handoff = root / "handoff"
            controller.mkdir()
            handoff.mkdir()
            current = q1._implementation_identity()
            state = {
                "revision": 0,
                "status": "handoff_running",
                "implementation_identity": copy.deepcopy(current),
            }
            q1._write(controller / "state/revision-000.json", state)
            stale = copy.deepcopy(current)
            stale["catalog"][0]["sha256"] = "0" * 64
            stale["canonical_digest"] = q1._canonical_sha256(stale["catalog"])
            q1._write(
                controller / "frozen-inputs.json",
                {"implementation_identity": stale},
            )
            q1._write(handoff / "handoff-session.json", {"partial": True})
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*") if path.is_file()
            }
            with mock.patch.dict(
                q1.os.environ,
                {
                    "CODEX_TASK_ID": "handoff-task",
                    "CODEX_THREAD_ID": "handoff-thread",
                    "Q1_TEST_AGENT_FIXTURE": "1",
                },
                clear=False,
            ):
                with self.assertRaisesRegex(q1.Q1Error, "Q1_IMPLEMENTATION_STALE"):
                    q1.seal_handoff_review(
                        controller,
                        handoff,
                        payload={"stale": True},
                    )
            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*") if path.is_file()
            }
            self.assertEqual(after, before)

    def test_t1_22_through_25_use_canonical_representatives(self) -> None:
        for version in ("2.2", "2.3", "2.4", "2.5"):
            with self.subTest(version=version):
                model = _model(version)
                output: dict = {}
                q1._index_stage_model(model, stage="T1", output=output)
                self.assertEqual(set(output), {
                    ("T1", "EV-A"), ("T1", "PROP-A"),
                    ("T1", "CE-A"), ("T1", "EVD-A"),
                })
                event = output[("T1", "EV-A")]
                self.assertEqual(event["value"], model["major_events"][0])
                self.assertEqual(event["source_pointer"], "/major_events/0")
                self.assertEqual(
                    event["projection_source_pointer"],
                    "/planned_event_registry/0",
                )
                self.assertEqual(
                    event["value_sha256"],
                    q1._canonical_sha256(model["major_events"][0]),
                )

    def test_registry_reordering_does_not_change_canonical_fingerprints(self) -> None:
        model = _model()
        second_planned, second_canonical = _event_pair("EV-B")
        second_planned["predecessor_event_ids"] = ["EV-A"]
        second_canonical["predecessor_event_ids"] = ["EV-A"]
        model["planned_event_registry"].append(second_planned)
        model["major_events"].append(second_canonical)
        left: dict = {}
        q1._index_stage_model(model, stage="T1", output=left)
        reordered = copy.deepcopy(model)
        reordered["planned_event_registry"].reverse()
        reordered["major_events"].reverse()
        right: dict = {}
        q1._index_stage_model(reordered, stage="T1", output=right)
        self.assertEqual(
            {key: value["value_sha256"] for key, value in left.items()},
            {key: value["value_sha256"] for key, value in right.items()},
        )

    def test_legacy_20_and_21_only_merge_exact_duplicates(self) -> None:
        for version in ("2.0", "2.1"):
            with self.subTest(version=version):
                model = {
                    "schema_version": version,
                    "left": [{"id": "EV-A", "value": "same"}],
                    "right": [{"id": "EV-A", "value": "same"}],
                }
                output: dict = {}
                q1._index_stage_model(model, stage="T1", output=output)
                self.assertEqual(len(output[("T1", "EV-A")]["source_pointers"]), 2)
                model["right"][0]["value"] = "drift"
                with self.assertRaisesRegex(q1.Q1Error, "Q1_STORY_OBJECT_AMBIGUOUS"):
                    q1._index_stage_model(model, stage="T1", output={})

    def test_projection_mutants_fail_closed(self) -> None:
        mutations = []
        event = _model()
        event["major_events"][0]["direct_result"] = "drift"
        mutations.append(event)
        subject = _model()
        subject["major_events"][0]["after_state"] = {"PSS-A": "drift"}
        mutations.append(subject)
        proposition = _model()
        proposition["proposition_registry"][0]["statement"] = "drift"
        mutations.append(proposition)
        edge = _model()
        edge["causal_edges"][0]["mechanism"] = "drift"
        mutations.append(edge)
        missing = _model()
        missing["major_events"] = []
        mutations.append(missing)
        third_source = _model()
        third_source["third"] = [copy.deepcopy(third_source["major_events"][0])]
        mutations.append(third_source)
        for index, mutant in enumerate(mutations):
            with self.subTest(index=index), self.assertRaisesRegex(
                q1.Q1Error,
                "Q1_STORY_OBJECT_(PROJECTION_INVALID|AMBIGUOUS)",
            ):
                q1._index_stage_model(mutant, stage="T1", output={})

    def test_t1_25_consumption_and_lifecycle_projection_fail_closed(self) -> None:
        for field, drift in (
            ("consumes_token_instance_ids", ["ATI-DRIFT"]),
            ("lifecycle_effects", [{"drift": True}]),
        ):
            with self.subTest(field=field):
                model = _model("2.5")
                model["planned_event_registry"][0][field] = drift
                with self.assertRaisesRegex(
                    q1.Q1Error,
                    rf"Q1_STORY_OBJECT_PROJECTION_INVALID: T1:EV-A\.{field}",
                ):
                    q1._index_stage_model(model, stage="T1", output={})

    def test_t1_24_does_not_require_25_projection_fields(self) -> None:
        model = _model("2.4")
        output: dict = {}
        q1._index_stage_model(model, stage="T1", output=output)
        baseline = copy.deepcopy(output)

        model["planned_event_registry"][0]["consumes_token_instance_ids"] = [
            "ATI-IGNORED"
        ]
        model["planned_event_registry"][0]["lifecycle_effects"] = [
            {"legacy": "ignored"}
        ]
        output = {}
        q1._index_stage_model(model, stage="T1", output=output)
        self.assertEqual(output, baseline)

    def test_story_and_handoff_indexes_share_projection_logic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package_roots = {}
            handoff = root / "handoff"
            for stage, canonical in q1.STAGE_CANONICAL.items():
                model = _model() if stage == "T1" else {
                    "schema_version": "2.0", "objects": [{"id": f"{stage}-A"}]
                }
                package = root / "packages" / stage
                package.mkdir(parents=True)
                (package / canonical).write_text(json.dumps(model), encoding="utf-8")
                package_roots[stage] = str(package)
                target = handoff / "inputs" / stage
                target.mkdir(parents=True)
                (target / canonical).write_text(json.dumps(model), encoding="utf-8")
            story = q1._story_object_index({"package_roots": package_roots})
            projected = q1._handoff_object_index(handoff)
            self.assertEqual(
                {key: value["value_sha256"] for key, value in story.items()},
                {key: value["value_sha256"] for key, value in projected.items()},
            )


if __name__ == "__main__":
    unittest.main()
