from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
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
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


proposal = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.proposal_adapter"
)

EVALS = Path(proposal.__file__).resolve().parent
GENERIC_MANIFEST = EVALS / "manifests" / "generic.v1.json"
DUANXIAN_MANIFEST = EVALS / "manifests" / "duanxian.v1.json"


def _project(
    manifest: Path,
) -> tuple[
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    adapter = proposal.DeclarativeProposalAdapter.from_manifest(manifest)
    case = adapter.formal_case_snapshot
    fixture = case.structural_case.fixture
    controls = [
        {
            "id": item["control_id"],
            "hardness": item["hardness"],
            "heading": (
                f"[{item['control_id']}]"
                f"[{item['hardness']}] {item['heading']}"
            ),
            "value": copy.deepcopy(item["value"]),
            "domain": item["stage"],
        }
        for item in fixture["interviews"]
    ]
    baseline = {
        "run_id": fixture["run_id"],
        "control_registry": copy.deepcopy(controls),
        "fact_dependencies": copy.deepcopy(fixture["fact_dependencies"]),
    }
    gate = {"path": "input-gate.json", "sha256": "a" * 64}
    source_artifacts = [
        {
            "path": "sources/B0/author-control-baseline.json",
            "sha256": "b" * 64,
        }
    ]
    storyline = adapter.storyline(
        run_id=fixture["run_id"],
        gate_reference=gate,
        source_artifacts=source_artifacts,
        controls=controls,
    )
    common = {
        "run_id": fixture["run_id"],
        "gate_reference": gate,
        "source_artifacts": source_artifacts,
        "baseline": baseline,
        "storyline": storyline,
    }
    world = adapter.world(**common)
    environment = adapter.environment(**common, world=world)
    timeline = adapter.event(
        **common,
        world=world,
        environment=environment,
    )
    proposal.runtime.ContractRuntime().validate(
        timeline,
        "event-timeline.schema.json",
    )
    character = adapter.character(
        **common,
        world=world,
        environment=environment,
        timeline=timeline,
    )
    return storyline, world, environment, timeline, character


class FormalT1ProposalProjectionTests(unittest.TestCase):
    def _assert_projection(
        self,
        manifest: Path,
        *,
        event_count: int,
        edge_count: int,
        realization_count: int,
    ) -> None:
        storyline, world, environment, timeline, character = _project(
            manifest
        )
        repeated = _project(manifest)
        self.assertEqual(
            (storyline, world, environment, timeline, character),
            repeated,
        )
        self.assertEqual(event_count, len(timeline["major_events"]))
        self.assertEqual(edge_count, len(timeline["causal_edges"]))
        self.assertEqual(
            realization_count,
            len(timeline["connection_realization"]),
        )

        lines = {item["id"]: item for item in storyline["storylines"]}
        world_requirements = {
            item["id"]: next(
                source_id
                for source_id in item["source_ids"]
                if source_id in lines
            )
            for item in storyline["world_requirements"]
        }
        world_demands = {
            item["id"]: item for item in world["environment_demands"]
        }
        hosted_demands = [
            next(
                source_id
                for source_id in record["source_ids"]
                if source_id in world_demands
            )
            for record in environment["storyline_hosting_ledger"]
        ]
        self.assertEqual(list(world_demands), hosted_demands)
        self.assertEqual(
            set(lines),
            {
                world_requirements[
                    next(
                        source_id
                        for source_id in world_demands[demand_id][
                            "source_ids"
                        ]
                        if source_id in world_requirements
                    )
                ]
                for demand_id in hosted_demands
            },
        )
        events = {item["id"]: item for item in timeline["major_events"]}
        sequences = {
            item["storyline_id"]: item
            for item in timeline["storyline_event_sequences"]
        }
        for line_id, line in lines.items():
            states = [
                line["start_state"],
                *line["state_changes"],
                line["end_state"],
            ]
            event_ids = sequences[line_id]["event_ids"]
            self.assertEqual(len(states) - 1, len(event_ids))
            role_positions: list[int] = []
            for index, event_id in enumerate(event_ids):
                event = events[event_id]
                self.assertEqual(
                    {line_id: states[index]},
                    event["before_state"],
                )
                self.assertEqual(
                    {line_id: states[index + 1]},
                    event["after_state"],
                )
                for group_index, group in enumerate(proposal.ROLES):
                    if any(
                        f"[RESP:{role}]" in event["responsibility"]
                        for role in group
                    ):
                        role_positions.append(group_index)
            self.assertEqual(sorted(role_positions), role_positions)
            terminal = events[event_ids[-1]]
            self.assertIn("[RESP:result]", terminal["responsibility"])
            self.assertIn("[RESP:aftermath]", terminal["responsibility"])
            self.assertEqual(
                line["end_state"],
                terminal["after_state"][line_id],
            )
            for event_id in event_ids[:-1]:
                self.assertNotIn(
                    "[RESP:result]",
                    events[event_id]["responsibility"],
                )
                self.assertNotIn(
                    "[RESP:aftermath]",
                    events[event_id]["responsibility"],
                )

        edges = {item["id"]: item for item in timeline["causal_edges"]}
        causal_connection_count = sum(
            item["relation"] == "causal"
            for item in storyline["connections"]
        )
        self.assertEqual(
            sum(
                len(item["event_ids"]) - 1
                for item in sequences.values()
            )
            + causal_connection_count,
            len(timeline["causal_edges"]),
        )
        timing = {
            item["id"]: item
            for item in timeline["narrative_timing_constraints"]
        }
        realizations = {
            item["connection_id"]: item
            for item in timeline["connection_realization"]
        }
        for connection in storyline["connections"]:
            record = realizations[connection["id"]]
            source_index = connection["from_state_index"]
            target_index = connection["to_state_index"]
            source_events = sequences[
                connection["from_storyline_id"]
            ]["event_ids"]
            target_events = sequences[
                connection["to_storyline_id"]
            ]["event_ids"]
            expected_source_event = source_events[max(source_index - 1, 0)]
            expected_target_event = target_events[max(target_index - 1, 0)]
            self.assertEqual(
                expected_source_event,
                record["source_anchor"]["event_id"],
            )
            self.assertEqual(
                expected_target_event,
                record["target_anchor"]["event_id"],
            )
            self.assertEqual(
                connection["from_state"],
                record["source_anchor"]["state"],
            )
            self.assertEqual(
                connection["to_state"],
                record["target_anchor"]["state"],
            )
            timing_record = timing[record["timing_constraint_ids"][0]]
            if connection["relation"] == "causal":
                self.assertEqual("causal_handoff", record["realization_kind"])
                self.assertEqual(1, len(record["causal_edge_ids"]))
                edge = edges[record["causal_edge_ids"][0]]
                self.assertEqual(
                    (expected_source_event, expected_target_event),
                    (edge["from_event_id"], edge["to_event_id"]),
                )
                self.assertIn(
                    expected_source_event,
                    events[expected_target_event]["predecessor_event_ids"],
                )
                self.assertIn(
                    "[REL:convergence]",
                    timing_record["constraint"],
                )
            else:
                self.assertEqual(
                    "associative_alignment",
                    record["realization_kind"],
                )
                self.assertEqual([], record["causal_edge_ids"])
                self.assertNotIn(
                    expected_source_event,
                    events[expected_target_event]["predecessor_event_ids"],
                )
                self.assertFalse(
                    any(
                        edge["from_event_id"] == expected_source_event
                        and edge["to_event_id"] == expected_target_event
                        for edge in edges.values()
                    )
                )
                self.assertIn(
                    "[REL:association]",
                    timing_record["constraint"],
                )

        main = next(
            item
            for item in storyline["storylines"]
            if item["type"] == "main"
        )
        first_main_event = events[sequences[main["id"]]["event_ids"][0]]
        slot_to_character = {
            item["slot_id"]: item["character_id"]
            for item in character["slot_resolution"]
        }
        self.assertEqual(
            slot_to_character[first_main_event["initiator_slot_id"]],
            character["three_layer_networks"][0]["core_character_id"],
        )

    def test_generic_formal_projection(self) -> None:
        self._assert_projection(
            GENERIC_MANIFEST,
            event_count=14,
            edge_count=12,
            realization_count=4,
        )

    def test_duanxian_formal_projection(self) -> None:
        self._assert_projection(
            DUANXIAN_MANIFEST,
            event_count=18,
            edge_count=16,
            realization_count=5,
        )

    def test_eight_transition_roles_do_not_cycle(self) -> None:
        self.assertEqual(
            [
                ("background", "setup"),
                ("trigger",),
                ("development",),
                ("development",),
                ("development",),
                ("turn_or_crisis",),
                ("turn_or_crisis",),
                ("result", "aftermath"),
            ],
            proposal._event_role_groups(8),
        )

    def test_formal_q1_consistency_uses_exact_t1_e1_w1_lineage(
        self,
    ) -> None:
        canonical_names = {
            "B0": "author-control-baseline.json",
            "S1": "storyline-architecture.json",
            "W1": "world-model.json",
            "E1": "environment-system.json",
            "T1": "event-timeline.json",
            "C1": "character-system.json",
        }
        for manifest in (GENERIC_MANIFEST, DUANXIAN_MANIFEST):
            with self.subTest(manifest=manifest.name):
                storyline, world, environment, timeline, character = (
                    _project(manifest)
                )
                models = {
                    "B0": {
                        "controls": [
                            {
                                "id": "B0-CONTROL",
                                "meaning": (
                                    "The admitted formal author control "
                                    "baseline."
                                ),
                            }
                        ]
                    },
                    "S1": storyline,
                    "W1": world,
                    "E1": environment,
                    "T1": timeline,
                    "C1": character,
                }
                with tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    package_roots = {}
                    for stage, model in models.items():
                        stage_root = root / stage
                        stage_root.mkdir()
                        (stage_root / canonical_names[stage]).write_text(
                            json.dumps(model, ensure_ascii=False),
                            encoding="utf-8",
                        )
                        package_roots[stage] = str(stage_root)
                    adapter = proposal.Q1ProposalAdapter(
                        {"package_roots": package_roots}
                    )
                    payloads = adapter.semantic_payloads()
                    with (
                        mock.patch.object(
                            proposal,
                            "_eval_causal_story_path",
                            proposal._eval_story_path,
                        ),
                        mock.patch.object(
                            proposal,
                            "_eval_cross_story_path",
                            proposal._eval_story_path,
                        ),
                    ):
                        legacy_payloads = adapter.semantic_payloads()
                    object_index = proposal.q1._story_object_index(
                        adapter.frozen
                    )
                    proposal.q1._validate_assertion_bindings(
                        payloads["domain-challenges"],
                        object_index=object_index,
                        phase="domain-challenges",
                    )
                    proposal.q1._validate_assertion_bindings(
                        payloads["cross-domain-challenges"],
                        object_index=object_index,
                        phase="cross-domain-challenges",
                    )
                    allowlist = [
                        {
                            "path": f"inputs/file-{index}.json",
                            "sha256": f"{index:064x}",
                        }
                        for index in range(12)
                    ]
                    handoff = adapter.handoff_payload(
                        allowlist=allowlist
                    )
                    proposal.q1._validate_handoff_payload(
                        handoff,
                        allowlist,
                        object_index=object_index,
                    )
                    semantic_bindings = {
                        item["check_id"]: item
                        for phase in (
                            "domain-challenges",
                            "cross-domain-challenges",
                        )
                        for item in payloads[phase][
                            "assertion_bindings"
                        ]
                    }
                    handoff_bindings = {
                        item["check_id"]: item
                        for item in handoff["assertion_bindings"]
                    }
                    expected_paths = {
                        "CHK-T1": [["/mechanism"]],
                        "CHK-C1": [["/chosen_action"]],
                        "CHK-COVERAGE": [
                            ["/evidence", "/source_ids"],
                            ["/responsibility"],
                        ],
                        "CHK-CAUSE": [
                            [
                                "/source_anchor/state",
                                "/causal_edge_ids",
                            ],
                            ["/mechanism"],
                        ],
                        "CHK-EASY": [
                            ["/selection", "/impact_ids"],
                            ["/statement"],
                        ],
                        "CHK-CROSS": [
                            ["/evidence", "/source_ids"],
                            ["/responsibility"],
                        ],
                        "CHK-CONSISTENCY": [
                            ["/to_state", "/allowed_by_ids"],
                            ["/responsibility", "/evidence_ids"],
                            ["/statement"],
                        ],
                    }
                    for check_id, paths in expected_paths.items():
                        self.assertEqual(
                            paths,
                            [
                                [
                                    projection["path"]
                                    for projection in evidence[
                                        "projections"
                                    ]
                                ]
                                for evidence in semantic_bindings[
                                    check_id
                                ]["evidence_objects"]
                            ],
                        )
                    expected_handoff_paths = {
                        "HANDOFF-TRACE": [
                            ["/evidence", "/source_ids"],
                            ["/responsibility"],
                        ],
                        "HANDOFF-EVENT": [
                            ["/from_state", "/allowed_by_ids"],
                            ["/responsibility"],
                        ],
                        "HANDOFF-CHOICE": [
                            ["/chosen_action", "/event_ids"],
                            ["/responsibility"],
                        ],
                    }
                    for check_id, paths in expected_handoff_paths.items():
                        self.assertEqual(
                            paths,
                            [
                                [
                                    projection["path"]
                                    for projection in evidence[
                                        "projections"
                                    ]
                                ]
                                for evidence in handoff_bindings[
                                    check_id
                                ]["evidence_objects"]
                            ],
                        )
                    if manifest == GENERIC_MANIFEST:
                        choice = handoff_bindings["HANDOFF-CHOICE"]
                        agency_id = choice["assertion"]["subject_id"]
                        agency = next(
                            item["value"]
                            for item in adapter.by_stage["C1"]
                            if item["id"] == agency_id
                        )
                        self.assertNotEqual(
                            agency["event_ids"][0],
                            choice["assertion"]["target_id"],
                        )
                        self.assertIn(
                            choice["assertion"]["target_id"],
                            agency["event_ids"],
                        )
                    coverage_source_id = semantic_bindings[
                        "CHK-COVERAGE"
                    ]["assertion"]["subject_id"]
                    coverage_source = next(
                        item
                        for item in adapter.by_stage["T1"]
                        if item["id"] == coverage_source_id
                    )
                    damaged_coverage_source = copy.deepcopy(
                        coverage_source
                    )
                    damaged_coverage_source["value"].pop("evidence")
                    damaged_coverage_source["value_sha256"] = (
                        proposal.runtime.canonical_sha256(
                            damaged_coverage_source["value"]
                        )
                    )
                    with self.assertRaisesRegex(
                        proposal.ProposalEvidenceError,
                        "Q1_PROPOSAL_COVERAGE_STORY_PROJECTION_MISSING",
                    ):
                        proposal._eval_coverage_story_path(
                            damaged_coverage_source["value"]
                        )
                    coverage_target_id = semantic_bindings[
                        "CHK-COVERAGE"
                    ]["assertion"]["target_id"]
                    coverage_target = next(
                        item
                        for item in adapter.by_stage["S1"]
                        if item["id"] == coverage_target_id
                    )
                    isolated = object.__new__(
                        proposal.Q1ProposalAdapter
                    )
                    isolated.by_stage = {
                        "T1": [damaged_coverage_source],
                        "S1": [coverage_target],
                    }
                    with self.assertRaisesRegex(
                        proposal.ProposalEvidenceError,
                        "Q1_PROPOSAL_RELATION_MISSING",
                    ):
                        isolated._bind(
                            isolated._check(
                                "CHK-COVERAGE", "coverage"
                            ),
                            stages=["T1"],
                            predicate="covers",
                            operator="recompute-coverage",
                            target_stage="S1",
                            story_path_selector=(
                                proposal._eval_coverage_story_path
                            ),
                            relation_path_selector=(
                                lambda value, identifier: (
                                    proposal._eval_allowed_relation_path(
                                        value,
                                        identifier,
                                        paths=("/source_ids",),
                                    )
                                )
                            ),
                        )
                    self.assertEqual(
                        payloads["review-plan"],
                        legacy_payloads["review-plan"],
                    )
                    for phase in (
                        "domain-challenges",
                        "cross-domain-challenges",
                    ):
                        fixed_checks = {
                            item["id"]: item
                            for field, values in payloads[phase].items()
                            if field != "assertion_bindings"
                            for item in values
                        }
                        legacy_checks = {
                            item["id"]: item
                            for field, values in legacy_payloads[
                                phase
                            ].items()
                            if field != "assertion_bindings"
                            for item in values
                        }
                        fixed_bindings = {
                            item["check_id"]: item
                            for item in payloads[phase][
                                "assertion_bindings"
                            ]
                        }
                        legacy_bindings = {
                            item["check_id"]: item
                            for item in legacy_payloads[phase][
                                "assertion_bindings"
                            ]
                        }
                        for check_id in (
                            set(fixed_checks)
                            - {
                                "CHK-T1",
                                "CHK-C1",
                                "CHK-COVERAGE",
                                "CHK-CAUSE",
                                "CHK-EASY",
                                "CHK-CROSS",
                                "CHK-CONSISTENCY",
                            }
                        ):
                            self.assertEqual(
                                legacy_checks[check_id],
                                fixed_checks[check_id],
                            )
                            self.assertEqual(
                                legacy_bindings[check_id],
                                fixed_bindings[check_id],
                            )

                    def reverse_mapping_order(value):
                        if isinstance(value, dict):
                            return {
                                key: reverse_mapping_order(value[key])
                                for key in reversed(list(value))
                            }
                        if isinstance(value, list):
                            return [
                                reverse_mapping_order(item)
                                for item in value
                            ]
                        return value

                    for stage, model in models.items():
                        (
                            Path(package_roots[stage])
                            / canonical_names[stage]
                        ).write_text(
                            json.dumps(
                                reverse_mapping_order(model),
                                ensure_ascii=False,
                            ),
                            encoding="utf-8",
                        )
                    reordered_payloads = proposal.Q1ProposalAdapter(
                        {"package_roots": package_roots}
                    ).semantic_payloads()
                    reordered_handoff = proposal.Q1ProposalAdapter(
                        {"package_roots": package_roots}
                    ).handoff_payload(allowlist=allowlist)
                    fixed_cross_check = payloads[
                        "cross-domain-challenges"
                    ]["cross_domain_checks"][0]
                    reordered_cross_check = reordered_payloads[
                        "cross-domain-challenges"
                    ]["cross_domain_checks"][0]
                    self.assertEqual(
                        fixed_cross_check,
                        reordered_cross_check,
                    )
                    self.assertEqual(
                        next(
                            item
                            for item in payloads[
                                "cross-domain-challenges"
                            ]["assertion_bindings"]
                            if item["check_id"] == "CHK-CROSS"
                        ),
                        next(
                            item
                            for item in reordered_payloads[
                                "cross-domain-challenges"
                            ]["assertion_bindings"]
                            if item["check_id"] == "CHK-CROSS"
                        ),
                    )
                    for phase, check_ids in (
                        (
                            "domain-challenges",
                            {
                                "CHK-T1",
                                "CHK-C1",
                                "CHK-COVERAGE",
                                "CHK-CAUSE",
                                "CHK-EASY",
                            },
                        ),
                        (
                            "cross-domain-challenges",
                            {"CHK-CROSS", "CHK-CONSISTENCY"},
                        ),
                    ):
                        fixed = {
                            item["check_id"]: item
                            for item in payloads[phase][
                                "assertion_bindings"
                            ]
                        }
                        reordered = {
                            item["check_id"]: item
                            for item in reordered_payloads[phase][
                                "assertion_bindings"
                            ]
                        }
                        for check_id in check_ids:
                            self.assertEqual(
                                fixed[check_id],
                                reordered[check_id],
                            )
                    fixed_handoff = {
                        item["check_id"]: item
                        for item in handoff["assertion_bindings"]
                    }
                    reversed_handoff = {
                        item["check_id"]: item
                        for item in reordered_handoff[
                            "assertion_bindings"
                        ]
                    }
                    for check_id in (
                        "HANDOFF-TRACE",
                        "HANDOFF-EVENT",
                        "HANDOFF-CHOICE",
                    ):
                        self.assertEqual(
                            fixed_handoff[check_id],
                            reversed_handoff[check_id],
                        )
                consistency = payloads[
                    "cross-domain-challenges"
                ]["assertion_bindings"][1]
                objects = consistency["evidence_objects"]
                self.assertEqual(
                    ["T1", "E1", "W1"],
                    [item["stage"] for item in objects],
                )
                self.assertEqual("world-fact", objects[-1]["kind"])
                self.assertIn(
                    "/allowed_by_ids",
                    [item["path"] for item in objects[0]["projections"]],
                )
                self.assertIn(
                    "/evidence_ids",
                    [item["path"] for item in objects[1]["projections"]],
                )
                self.assertEqual(
                    objects[0]["id"],
                    consistency["assertion"]["subject_id"],
                )
                self.assertEqual(
                    objects[-1]["id"],
                    consistency["assertion"]["target_id"],
                )
                cause_check = payloads["domain-challenges"][
                    "causal_challenges"
                ][0]
                cause_binding = next(
                    item
                    for item in payloads["domain-challenges"][
                        "assertion_bindings"
                    ]
                    if item["check_id"] == cause_check["id"]
                )
                self.assertIn(
                    "/source_anchor/state",
                    [
                        item["path"]
                        for item in cause_binding["evidence_objects"][0][
                            "projections"
                        ]
                    ],
                )
                self.assertIn(
                    "/mechanism",
                    [
                        item["path"]
                        for item in cause_binding["evidence_objects"][1][
                            "projections"
                        ]
                    ],
                )
                self.assertNotEqual(
                    f"{cause_check['id']}: "
                    f"{cause_binding['assertion']['target_id']}",
                    cause_check["conclusion"],
                )
                paraphrased = copy.deepcopy(
                    payloads["domain-challenges"]
                )
                paraphrased["causal_challenges"][0][
                    "conclusion"
                ] = "A paraphrase that cites no frozen story value."
                with self.assertRaisesRegex(
                    proposal.q1.Q1Error,
                    "Q1_GENERIC_SEMANTIC_EVIDENCE",
                ):
                    proposal.q1._validate_assertion_bindings(
                        paraphrased,
                        object_index=object_index,
                        phase="domain-challenges",
                    )
                hash_drift = copy.deepcopy(
                    payloads["domain-challenges"]
                )
                cause_drift = next(
                    item
                    for item in hash_drift["assertion_bindings"]
                    if item["check_id"] == "CHK-CAUSE"
                )
                cause_drift["evidence_objects"][0]["projections"][0][
                    "value_sha256"
                ] = "0" * 64
                with self.assertRaisesRegex(
                    proposal.q1.Q1Error,
                    "Q1_ASSERTION_BINDING_INVALID",
                ):
                    proposal.q1._validate_assertion_bindings(
                        hash_drift,
                        object_index=object_index,
                        phase="domain-challenges",
                    )
                for mutation, error in (
                    ("drop-story", "Q1_GENERIC_SEMANTIC_EVIDENCE"),
                    ("drop-relation", "Q1_ASSERTION_BINDING_INVALID"),
                    ("id-conclusion", "Q1_GENERIC_SEMANTIC_EVIDENCE"),
                ):
                    invalid_handoff = copy.deepcopy(handoff)
                    trace_check = next(
                        item
                        for item in invalid_handoff["handoff_checks"]
                        if item["id"] == "HANDOFF-TRACE"
                    )
                    trace_binding = next(
                        item
                        for item in invalid_handoff[
                            "assertion_bindings"
                        ]
                        if item["check_id"] == "HANDOFF-TRACE"
                    )
                    if mutation == "drop-story":
                        trace_binding["evidence_objects"][0][
                            "projections"
                        ] = [
                            item
                            for item in trace_binding[
                                "evidence_objects"
                            ][0]["projections"]
                            if item["path"] != "/evidence"
                        ]
                        target_evidence = trace_binding[
                            "evidence_objects"
                        ][1]
                        target_record = next(
                            item
                            for item in adapter.by_stage[
                                target_evidence["stage"]
                            ]
                            if item["id"] == target_evidence["id"]
                        )
                        target_evidence["projections"] = [
                            {
                                "path": "/target_stage",
                                "value_sha256": (
                                    proposal.runtime.canonical_sha256(
                                        proposal._eval_pointer_value(
                                            target_record["value"],
                                            "/target_stage",
                                        )
                                    )
                                ),
                            }
                        ]
                        unsigned = {
                            key: copy.deepcopy(value)
                            for key, value in trace_binding.items()
                            if key != "assertion_sha256"
                        }
                        digest = proposal.runtime.canonical_sha256(
                            unsigned
                        )
                        trace_binding["assertion_sha256"] = digest
                        trace_check["method"] = (
                            f"story-assertion:{digest}"
                        )
                    elif mutation == "drop-relation":
                        trace_binding["evidence_objects"][0][
                            "projections"
                        ] = [
                            item
                            for item in trace_binding[
                                "evidence_objects"
                            ][0]["projections"]
                            if item["path"] != "/source_ids"
                        ]
                    else:
                        trace_check["conclusion"] = (
                            trace_binding["assertion"]["target_id"]
                        )
                    with (
                        self.subTest(
                            manifest=manifest.name,
                            handoff_mutation=mutation,
                        ),
                        self.assertRaisesRegex(
                            proposal.q1.Q1Error,
                            error,
                        ),
                    ):
                        proposal.q1._validate_handoff_payload(
                            invalid_handoff,
                            allowlist,
                            object_index=object_index,
                        )

    def test_causal_selector_rejects_ids_and_missing_edge(self) -> None:
        with self.assertRaisesRegex(
            proposal.ProposalEvidenceError,
            "Q1_PROPOSAL_CAUSAL_STORY_PROJECTION_MISSING",
        ):
            proposal._eval_causal_story_path(
                {
                    "from_event_id": "EV-FROM-IDENTIFIER",
                    "source_anchor": {
                        "state": "EV-STATE-IDENTIFIER",
                    },
                }
            )

        def record(identifier: str, value: dict[str, object]) -> dict:
            return {
                "id": identifier,
                "stage": "T1",
                "kind": "governance",
                "value": {"id": identifier, **value},
                "value_sha256": proposal.runtime.canonical_sha256(
                    {"id": identifier, **value}
                ),
            }

        adapter = object.__new__(proposal.Q1ProposalAdapter)
        adapter.by_stage = {
            "T1": [
                record(
                    "CR-A",
                    {
                        "causal_edge_ids": [],
                        "source_anchor": {
                            "state": (
                                "A measured consequence changes the "
                                "available choice."
                            )
                        },
                    },
                ),
                record(
                    "CE-A",
                    {
                        "from_event_id": "EV-A",
                        "mechanism": (
                            "The first event creates the next condition."
                        ),
                    },
                ),
            ]
        }
        with self.assertRaisesRegex(
            proposal.ProposalEvidenceError,
            "Q1_PROPOSAL_RELATION_MISSING",
        ):
            adapter._bind(
                adapter._check("CHK-CAUSE", "causality"),
                stages=["T1"],
                predicate="causal-dependency",
                operator="break-cause",
                target_stage="T1",
                story_path_selector=proposal._eval_causal_story_path,
            )

    def test_formal_event_projection_rejects_missing_relation_or_index(
        self,
    ) -> None:
        storyline, _, _, _, _ = _project(GENERIC_MANIFEST)
        adapter = proposal.DeclarativeProposalAdapter.from_manifest(
            GENERIC_MANIFEST
        )
        fixture = adapter.formal_case_snapshot.structural_case.fixture
        controls = [
            {
                "id": item["control_id"],
                "hardness": item["hardness"],
                "heading": (
                    f"[{item['control_id']}]"
                    f"[{item['hardness']}] {item['heading']}"
                ),
                "value": copy.deepcopy(item["value"]),
                "domain": item["stage"],
            }
            for item in fixture["interviews"]
        ]
        baseline = {
            "run_id": fixture["run_id"],
            "control_registry": controls,
            "fact_dependencies": fixture["fact_dependencies"],
        }
        gate = {"path": "input-gate.json", "sha256": "a" * 64}
        sources = [{"path": "source.json", "sha256": "b" * 64}]
        common = {
            "run_id": fixture["run_id"],
            "gate_reference": gate,
            "source_artifacts": sources,
            "baseline": baseline,
            "storyline": storyline,
        }
        world = adapter.world(**common)
        environment = adapter.environment(**common, world=world)
        for field in ("relation", "from_state_index", "to_state_index"):
            invalid = copy.deepcopy(storyline)
            invalid["connections"][0].pop(field)
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(
                    proposal.ProposalEvidenceError,
                    "T1_PROPOSAL_CONNECTION_CONTRACT_MISSING",
                ),
            ):
                proposal._event_proposal(
                    run_id=fixture["run_id"],
                    gate_reference=gate,
                    source_artifacts=sources,
                    baseline=baseline,
                    storyline=invalid,
                    world=world,
                    environment=environment,
                )


if __name__ == "__main__":
    unittest.main()
