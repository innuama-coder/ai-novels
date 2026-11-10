from __future__ import annotations

import copy
import importlib
import inspect
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


runtime = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime"
)
s1 = importlib.import_module(
    "skills.novel-storyline-architecture-designer.scripts.run_v2"
)
baseline_test = importlib.import_module(
    "harnesses.novel-conception-autonomous.tests.test_baseline"
)


class S1ImplementationDependencyRegistryTests(unittest.TestCase):
    def test_registry_binds_s1_and_excludes_downstream_schemas(self) -> None:
        identities = set(s1._implementation_paths())
        self.assertIn("skill/run_v2.py", identities)
        self.assertIn("schemas/storyline-architecture.schema.json", identities)
        self.assertIn("schemas/canonical-common.schema.json", identities)
        self.assertIn("runtime/stage_implementation_identity.py", identities)
        self.assertNotIn("runtime/baseline.py", identities)
        self.assertNotIn("schemas/world-model.schema.json", identities)
        self.assertNotIn("schemas/environment-system.schema.json", identities)
        self.assertNotIn("runtime/b0_completion.py", identities)


def line_claim_ledger(
    payload: dict[str, object],
    controls: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Test Agent classifications for the runtime's deterministic span universe."""

    result = []
    for claim in s1.inspect_s1_line_claims(payload, controls):
        matching_controls = sorted(
            str(control["id"])
            for control in controls
            if claim["text"]
            in {
                str(control["heading"]),
                (
                    control["value"]
                    if isinstance(control["value"], str)
                    else runtime.canonical_json(control["value"])
                ),
            }
        )
        if matching_controls:
            disposition = "source_bound"
            decision_ids = []
        else:
            disposition = "s1_structural_derivation"
            parts = claim["pointer"].strip("/").split("/")
            index = int(parts[1])
            if parts[0] == "design_decisions":
                decision_ids = [payload["design_decisions"][index]["id"]]
            else:
                decision_ids = list(
                    payload["storylines"][index]["source_decision_ids"]
                )
        result.append(
            {
                **claim,
                "disposition": disposition,
                "source_control_ids": matching_controls,
                "decision_ids": decision_ids,
                "target_stage": None,
                "target_requirement_id": None,
                "open_item_id": None,
            }
        )
    return result


def agent_proposal(
    *,
    run_id: str,
    gate_reference: dict[str, str],
    source_artifacts: list[dict[str, str]],
    controls: list[dict[str, object]],
) -> dict[str, object]:
    """A test Agent's authored proposal; production code never synthesizes it."""

    demands = []
    storylines = []
    decisions = []
    coverage = []
    line_by_control = {}
    for index, control in enumerate(controls, 1):
        control_id = str(control["id"])
        value = (
            control["value"]
            if isinstance(control["value"], str)
            else runtime.canonical_json(control["value"])
        )
        line_id = "SL-MAIN" if index == 1 else f"SL-{index:03d}"
        demand_id = f"SLD-{index:03d}"
        decision_id = f"DEC-{index:03d}"
        line_by_control[control_id] = line_id
        demands.append(
            {
                "id": demand_id,
                "source_ids": [control_id],
                "obligation": (
                    f"Agent interpretation of {control['heading']}. "
                    f"Source meaning (verbatim): {value}"
                ),
                "disposition": (
                    "optional_melody"
                    if control["hardness"] == "author_open"
                    else "merged"
                    if index == 1
                    else "independent_line"
                ),
            }
        )
        decisions.append(
            {
                "id": decision_id,
                "gap": f"Choose dramatic ownership for {control_id}.",
                "options": ["Merge into main line.", "Create a connected line."],
                "selection": (
                    "Merge into main line."
                    if index == 1
                    else "Create a connected line."
                ),
                "owner": "S1",
                "authority_basis": f"S1 owns storyline projection of {control_id}.",
                "compatibility": (
                    f"Preserves {control['heading']} and its source meaning: {value}"
                ),
                "impact_ids": [line_id],
                "cost": "Creates one explicit dramatic responsibility.",
                "reversibility": "costly",
                "downstream_freedom": "Concrete realization remains downstream.",
                "projection_ids": [line_id],
            }
        )
        storylines.append(
            {
                "id": line_id,
                "type": (
                    "optional_melody"
                    if control["hardness"] == "author_open"
                    else "main"
                    if index == 1
                    else "supporting"
                ),
                "responsibility": (
                    f"Carry {control_id} / {control['heading']}: {value}"
                ),
                "actor_slot_ids": [f"SLOT-{index:03d}"],
                "goal": f"Make this meaning actionable without changing it: {value}",
                "pressure": f"Ignoring this meaning leaves the story incomplete: {value}",
                "start_state": f"The obligation is latent: {value}",
                "state_changes": [
                    f"Pressure exposes the obligation: {value}",
                    f"A choice changes its consequences: {value}",
                ],
                "end_state": f"The obligation has a visible consequence: {value}",
                "connection_ids": [],
                "source_decision_ids": [decision_id],
                "downstream_freedom": "World, place, event, actor identity and prose are open.",
            }
        )
        coverage.append(
            {
                "id": f"COV-{index:03d}",
                "source_ids": [demand_id],
                "realization_ids": [line_id],
                "status": "covered",
                "evidence": f"{demand_id} is assigned once to {line_id}.",
            }
        )
    main = storylines[0]
    for line in storylines:
        line["closure_mode"] = (
            "converges_to_main"
            if line["type"] not in {"main", "optional_melody"}
            else None
        )
        line["terminal_source_anchor"] = None
        line["terminal_entry_connection_id"] = None
    connections = []
    for index, line in enumerate(storylines[1:], 1):
        connection_id = f"SLC-{index:03d}"
        connections.append(
            {
                "id": connection_id,
                "type": "collision",
                "relation": (
                    "associative"
                    if line["type"] == "optional_melody"
                    else "causal"
                ),
                "from_storyline_id": line["id"],
                "to_storyline_id": "SL-MAIN",
                "from_state": line["end_state"],
                "from_state_index": len(line["state_changes"]) + 1,
                "to_state": main["state_changes"][-1],
                "to_state_index": len(main["state_changes"]),
            }
        )
        line["connection_ids"].append(connection_id)
        main["connection_ids"].append(connection_id)
    demand_by_line = {
        line_by_control[str(control["id"])]: f"SLD-{index:03d}"
        for index, control in enumerate(controls, 1)
    }
    requirements = {}
    for field, prefix, stage in (
        ("world_requirements", "WR", "W1"),
        ("environment_requirements", "END", "E1"),
        ("event_requirements", "EVD", "T1"),
        ("character_requirements", "CHD", "C1"),
    ):
        requirements[field] = []
        for index, line in enumerate(storylines, 1):
            requirements[field].append(
                {
                    "id": f"{prefix}-{index:03d}",
                    "target_stage": stage,
                    "responsibility": f"Realize {line['responsibility']}",
                    "source_ids": [line["id"], demand_by_line[line["id"]]],
                    "required_capability": (
                        f"Support {line['start_state']} through {line['end_state']}"
                    ),
                    "constraints": [line["goal"], line["pressure"]],
                    "acceptance_checks": [
                        f"The result cites {line['id']}.",
                        f"The result preserves {line['end_state']}.",
                    ],
                    "downstream_freedom": line["downstream_freedom"],
                }
            )
    architecture = {
        "subject": "All approved obligations form one connected causal whole.",
        "opening_condition": main["start_state"],
        "development_logic": "Each line changes state before joining the main trunk.",
        "turning_logic": "Every connection changes the pressure on the main trunk.",
        "resolution_condition": main["end_state"],
        "theme_test": "The ending answers locked controls and preserves open controls.",
        "line_order": [
            *[line["id"] for line in storylines if line["id"] != "SL-MAIN"],
            "SL-MAIN",
        ],
    }
    all_line_ids = [line["id"] for line in storylines]
    phase_ids = ["TPH-OPEN", "TPH-PROBE", "TPH-CONVERGE", "TPH-END"]
    milestones = [
        {
            "id": "MS-OPEN",
            "order": 1,
            "phase_id": "TPH-OPEN",
            "temporal_label": "T1",
            "title": "Open every declared line",
            "storyline_ids": all_line_ids,
            "state_refs": [
                {
                    "storyline_id": line["id"],
                    "state_index": 0,
                    "state": line["start_state"],
                }
                for line in storylines
            ],
            "development": "All approved obligations become visible before they collide.",
            "outcome": "The reader can see what each line must eventually change.",
            "connection_ids": [],
        },
        {
            "id": "MS-PROBE",
            "order": 2,
            "phase_id": "TPH-PROBE",
            "temporal_label": "T2",
            "title": "Probe the latent obligations",
            "storyline_ids": all_line_ids,
            "state_refs": [
                {
                    "storyline_id": line["id"],
                    "state_index": 1,
                    "state": line["state_changes"][0],
                }
                for line in storylines
            ],
            "development": "Pressure tests how each line responds before convergence.",
            "outcome": "Observable responses distinguish active obligations from exposition.",
            "connection_ids": [],
        },
        {
            "id": "MS-CONVERGE",
            "order": 3,
            "phase_id": "TPH-CONVERGE",
            "temporal_label": "T3",
            "title": "Supporting lines change the main trunk",
            "storyline_ids": all_line_ids,
            "state_refs": [
                {
                    "storyline_id": line["id"],
                    "state_index": (
                        2 if line["id"] == "SL-MAIN"
                        else len(line["state_changes"]) + 1
                    ),
                    "state": (
                        line["state_changes"][-1]
                        if line["id"] == "SL-MAIN"
                        else line["end_state"]
                    ),
                }
                for line in [
                    *[item for item in storylines if item["id"] != "SL-MAIN"],
                    main,
                ]
            ],
            "development": "Every causal attachment is realized at its declared endpoint states.",
            "outcome": "The main trunk receives consequences rather than summaries.",
            "connection_ids": [item["id"] for item in connections],
        },
        {
            "id": "MS-END",
            "order": 4,
            "phase_id": "TPH-END",
            "temporal_label": "T4",
            "title": "Resolve the main trunk",
            "storyline_ids": ["SL-MAIN"],
            "state_refs": [
                {
                    "storyline_id": "SL-MAIN",
                    "state_index": len(main["state_changes"]) + 1,
                    "state": main["end_state"],
                }
            ],
            "development": "The changed main trunk makes its final choice.",
            "outcome": "The ending visibly answers the approved obligations.",
            "connection_ids": [],
        },
    ]
    phases = [
        {
            "id": phase_id,
            "order": index,
            "temporal_label": f"P{index}",
            "title": title,
            "responsibility": responsibility,
            "active_storyline_ids": milestone["storyline_ids"],
        }
        for index, (phase_id, title, responsibility, milestone) in enumerate(
            [
                ("TPH-OPEN", "Opening", "Establish all lines.", milestones[0]),
                ("TPH-PROBE", "Probe", "Test all lines.", milestones[1]),
                ("TPH-CONVERGE", "Convergence", "Join causal pressures.", milestones[2]),
                ("TPH-END", "Resolution", "Resolve the main trunk.", milestones[3]),
            ],
            1,
        )
    ]
    markers = [
        {"id": "NM-SETUP", "kind": "setup", "milestone_id": "MS-OPEN", "storyline_ids": all_line_ids, "label": "Obligation setup", "function": "Plant every approved obligation before its consequence.", "reader_question": "How will these obligations collide?", "observable_signal": "Every line begins in a distinct latent state.", "reference_marker_ids": [], "resolution": "opened"},
        {"id": "NM-PROBE", "kind": "probe", "milestone_id": "MS-PROBE", "storyline_ids": all_line_ids, "label": "Response probe", "function": "Test whether each obligation changes observable behavior.", "reader_question": "Which pressure can change the main trunk?", "observable_signal": "Every line produces a different response under pressure.", "reference_marker_ids": ["NM-SETUP"], "resolution": "advanced"},
        {"id": "NM-TURN", "kind": "turning_point", "milestone_id": "MS-CONVERGE", "storyline_ids": all_line_ids, "label": "Causal convergence", "function": "Make supporting consequences irreversibly alter the main trunk.", "reader_question": None, "observable_signal": "All declared causal connections reach their endpoint states.", "reference_marker_ids": ["NM-PROBE"], "resolution": "resolved"},
        {"id": "NM-CLIMAX", "kind": "climax", "milestone_id": "MS-CONVERGE", "storyline_ids": all_line_ids, "label": "Structural climax", "function": "Converge the structural lines at maximum pressure.", "reader_question": None, "observable_signal": "The main trunk must choose under combined consequences.", "reference_marker_ids": ["NM-TURN"], "resolution": "resolved"},
        {"id": "NM-PAYOFF", "kind": "payoff", "milestone_id": "MS-END", "storyline_ids": ["SL-MAIN"], "label": "Obligation payoff", "function": "Answer the setup through the final visible consequence.", "reader_question": None, "observable_signal": "The main ending answers the approved obligations.", "reference_marker_ids": ["NM-SETUP"], "resolution": "resolved"},
    ]
    temporal = {
        "progression_logic": "Open, probe, converge, then resolve the shared multi-line structure.",
        "phases": phases,
        "milestones": milestones,
        "markers": markers,
    }
    story_claim_units = s1._expected_claim_units(controls)
    line_by_id = {item["id"]: item for item in storylines}
    source_sequence_realizations = []
    for sequence_index, unit in enumerate(
        (item for item in story_claim_units if s1._source_unit_is_ordered(item)),
        1,
    ):
        line = line_by_id[line_by_control[unit["control_id"]]]
        source_sequence_realizations.append(
            {
                "id": f"SSR-{sequence_index:03d}",
                "source_unit_id": unit["id"],
                "from_anchor": {
                    "storyline_id": line["id"],
                    "state_index": 0,
                    "state": line["start_state"],
                },
                "to_anchor": {
                    "storyline_id": line["id"],
                    "state_index": len(line["state_changes"]) + 1,
                    "state": line["end_state"],
                },
                "boundary_from_anchor": None,
                "boundary_to_anchor": None,
                "realization_scope": "within_line",
                "reserved_connection_id": None,
                "phase3_fulfillment_kind": None,
                "expected_witness_type": None,
                "consistency_dimension": None,
                "rationale": "The complete ordered source transition is realized from this line's opening to its terminal state.",
            }
        )
    units_by_control = {
        str(control["id"]): [
            item
            for item in story_claim_units
            if item["control_id"] == str(control["id"])
        ]
        for control in controls
    }
    story_claim_atoms = []
    story_obligations = []
    obligation_coverage = []
    for index, control in enumerate(controls, 1):
        control_id = str(control["id"])
        line = next(item for item in storylines if item["id"] == line_by_control[control_id])
        obligation_id = f"SOB-{index:03d}"
        atom_ids = []
        for unit_index, unit in enumerate(units_by_control[control_id], 1):
            atom_id = f"SCA-{index:03d}-{unit_index:03d}"
            atom_ids.append(atom_id)
            story_claim_atoms.append(
                {
                    "id": atom_id,
                    "source_unit_id": unit["id"],
                    "control_id": control_id,
                    "source_locator": copy.deepcopy(control["source_locator"]),
                    "claim": f"Atomic interpretation of {unit['text']}",
                    "atom_kind": (
                        "causal_relation"
                        if control["hardness"] == "author_locked"
                        else "author_open"
                    ),
                    "consistency_dimensions": [],
                    "obligation_ids": (
                        [obligation_id]
                        if control["hardness"] == "author_locked"
                        else []
                    ),
                    "rationale": f"The exact source unit {unit['id']} is disposed once.",
                    "review_required": False,
                }
            )
        if control["hardness"] == "author_locked":
            story_obligations.append(
                {
                    "id": obligation_id,
                    "kind": "causes",
                    "source_claim_atom_ids": atom_ids,
                    "source_control_ids": [control_id],
                    "source_locators": [copy.deepcopy(control["source_locator"])],
                    "antecedent_anchors": [
                        {
                            "storyline_id": line["id"],
                            "state_index": 0,
                            "state": line["start_state"],
                        }
                    ],
                    "consequent_anchor": {
                        "storyline_id": line["id"],
                        "state_index": 1,
                        "state": line["state_changes"][0],
                    },
                    "proposition_id": None,
                    "audience": None,
                    "rationale": f"The locked control {control_id} requires one causal progression.",
                    "acceptance_check": f"The consequent cannot occur unless {control_id}'s antecedent occurs first.",
                }
            )
            disposition = "obligated"
            obligation_ids = [obligation_id]
            review_required = False
        else:
            disposition = "author_open"
            obligation_ids = []
            review_required = False
        obligation_coverage.append(
            {
                "id": f"SOC-{index:03d}",
                "control_id": control_id,
                "source_locator": copy.deepcopy(control["source_locator"]),
                "disposition": disposition,
                "claim_atom_ids": atom_ids,
                "obligation_ids": obligation_ids,
                "rationale": (
                    f"{control_id} is bound to explicit story obligations."
                    if disposition == "obligated"
                    else f"{control_id} remains an author-open choice."
                ),
                "review_required": review_required,
            }
        )
    temporal_ids = [
        *phase_ids,
        *[item["id"] for item in milestones],
        *[item["id"] for item in markers],
    ]
    story_obligation_ids = [item["id"] for item in story_obligations]
    story_claim_unit_ids = [item["id"] for item in story_claim_units]
    story_claim_atom_ids = [item["id"] for item in story_claim_atoms]
    obligation_coverage_ids = [item["id"] for item in obligation_coverage]
    line_claim_authority = line_claim_ledger(
        {"design_decisions": decisions, "storylines": storylines},
        controls,
    )
    line_claim_ids = [item["claim_id"] for item in line_claim_authority]
    model = {
        "schema_version": "2.0",
        "skill": "novel-storyline-architecture-designer",
        "stage": "S1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": [
                str(item["id"])
                for item in controls
                if item["hardness"] == "author_locked"
            ],
            "autonomous_owned": [
                *[item["id"] for item in decisions],
                *[item["id"] for item in storylines],
                *temporal_ids,
                *story_claim_unit_ids,
                *story_claim_atom_ids,
                *story_obligation_ids,
                *obligation_coverage_ids,
                *line_claim_ids,
                *[item["id"] for item in source_sequence_realizations],
            ],
            "downstream_freedom": [
                item["id"] for values in requirements.values() for item in values
            ],
            "author_open": [
                str(item["id"])
                for item in controls
                if item["hardness"] == "author_open"
            ],
        },
        "design_decisions": decisions,
        "derivation_claims": [
            {
                "id": f"DRV-{index:03d}",
                "value_sha256": runtime.canonical_sha256(line),
                "source_ids": [str(controls[index - 1]["id"])],
                "decision_ids": [f"DEC-{index:03d}"],
                "projection_ids": [line["id"]],
            }
            for index, line in enumerate(storylines, 1)
        ]
        + [
            {
                "id": "DRV-ARCHITECTURE",
                "value_sha256": runtime.canonical_sha256(architecture),
                "source_ids": [str(item["id"]) for item in controls],
                "decision_ids": [item["id"] for item in decisions],
                "projection_ids": [item["id"] for item in storylines],
            },
            {
                "id": "DRV-TEMPORAL-ARCHITECTURE",
                "value_sha256": runtime.canonical_sha256(temporal),
                "source_ids": [str(item["id"]) for item in controls],
                "decision_ids": [item["id"] for item in decisions],
                "projection_ids": temporal_ids,
            },
            {
                "id": "DRV-STORY-OBLIGATIONS",
                "value_sha256": runtime.canonical_sha256(
                    {
                        "story_claim_units": story_claim_units,
                        "story_claim_atoms": story_claim_atoms,
                        "story_obligation_register": story_obligations,
                        "story_obligation_coverage": obligation_coverage,
                    }
                ),
                "source_ids": [str(item["id"]) for item in controls],
                "decision_ids": [item["id"] for item in decisions],
                "projection_ids": [
                    *story_claim_unit_ids,
                    *story_claim_atom_ids,
                    *story_obligation_ids,
                    *obligation_coverage_ids,
                ],
            },
        ],
        "storyline_demands": demands,
        "storylines": storylines,
        "line_claim_authority": line_claim_authority,
        "source_sequence_realizations": source_sequence_realizations,
        "connections": connections,
        "architecture": architecture,
        "temporal_architecture": temporal,
        "story_claim_units": story_claim_units,
        "story_claim_atoms": story_claim_atoms,
        "story_obligation_register": story_obligations,
        "story_obligation_coverage": obligation_coverage,
        "cross_line_consistency": [
            {
                "id": f"SLCHECK-{dimension.upper()}",
                "dimension": dimension,
                "witness_ids": (
                    [line["id"] for line in storylines]
                    + (phase_ids + [item["id"] for item in milestones] if dimension == "time" else [])
                    + (story_obligation_ids if dimension in {"time", "causality"} else [])
                    + ([item["id"] for item in milestones] + [item["id"] for item in markers] if dimension == "information" else [])
                    + ([item["id"] for item in milestones] if dimension == "state" else [])
                    + ([item["id"] for item in markers] if dimension == "theme" else [])
                ),
                "source_claim_atom_ids": [],
                "source_control_ids": [],
                "claim": (
                    f"Every storyline has a declared {dimension} relation "
                    "that remains consistent with the complete architecture."
                ),
                "failure_condition": (
                    f"The {dimension} relation fails if any declared "
                    "storyline contradicts another line or the architecture."
                ),
            }
            for dimension in (
                "time",
                "causality",
                "information",
                "authority",
                "state",
                "theme",
            )
        ],
        **requirements,
        "coverage_ledger": coverage,
        "open_items": [
            {
                "id": f"OPEN-{index:03d}",
                "question": (
                    f"Preserve {control['heading']}: "
                    f"{control['value']}"
                ),
                "source_ids": [str(control["id"])],
                "status": "author_open",
            }
            for index, control in enumerate(
                [item for item in controls if item["hardness"] == "author_open"],
                1,
            )
        ],
    }
    return model


class AgentTextEncodingGateTests(unittest.TestCase):
    def _session(self) -> dict[str, object]:
        return {
            "run_id": "RUN-ENCODING-001",
            "session_id": "S1-ENCODING-SESSION",
            "thread_id": "thread-encoding",
            "input_gate": {"path": "S1/input-gate.json", "sha256": "a" * 64},
            "state_before": {"path": "state/revision-001.json", "sha256": "b" * 64},
            "input_manifest": {"stage": "B0", "path": "B0/stage-completion.json", "sha256": "c" * 64},
            "control_bindings": [],
        }

    def _payload(self, phase: str, text: str) -> dict[str, object]:
        if phase == "final-storyline-model":
            return {"model": {"nested": [{"semantic_text": text}]}}
        return {
            field: {"nested": [{"semantic_text": text}]}
            for field in s1.LEGACY_PHASE_FIELDS[phase]
        }

    def test_submit_accepts_normal_chinese_questions_and_writes_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            text = "这是真的吗？可以继续吗?"
            with mock.patch.object(
                s1,
                "_validated_session",
                return_value=(self._session(), {}, []),
            ), mock.patch.object(s1, "_validate_phase_semantics"):
                s1.submit_s1_phase(
                    workspace,
                    baseline_package=workspace / "B0",
                    input_gate=object(),
                    phase="demand-scan",
                    payload=self._payload("demand-scan", text),
                )
            evidence = json.loads(
                (
                    workspace
                    / "generation-evidence"
                    / "01-demand-scan.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                text,
                evidence["payload"]["storyline_demands"]["nested"][0][
                    "semantic_text"
                ],
            )

    def test_every_phase_rejects_nested_question_mark_and_replacement_damage(self) -> None:
        for phase in s1.PHASES:
            for damaged in ("字段已经变成???无法读取", "字段含有�替换字符"):
                with self.subTest(phase=phase, damaged=damaged):
                    with tempfile.TemporaryDirectory() as directory:
                        workspace = Path(directory)
                        evidence_root = workspace / "generation-evidence"
                        evidence_root.mkdir(parents=True)
                        phase_index = s1.PHASES.index(phase)
                        for index, previous in enumerate(
                            s1.PHASES[:phase_index], 1
                        ):
                            (evidence_root / f"{index:02d}-{previous}.json").write_text(
                                "{}", encoding="utf-8"
                            )
                        with mock.patch.object(
                            s1,
                            "_validated_session",
                            return_value=(self._session(), {}, []),
                        ):
                            with self.assertRaises(s1.S1Error) as caught:
                                s1.submit_s1_phase(
                                    workspace,
                                    baseline_package=workspace / "B0",
                                    input_gate=object(),
                                    phase=phase,
                                    payload=self._payload(phase, damaged),
                                )
                        self.assertEqual(
                            "S1_TEXT_ENCODING_CORRUPT", caught.exception.code
                        )
                        self.assertFalse(
                            (
                                evidence_root
                                / f"{phase_index + 1:02d}-{phase}.json"
                            ).exists()
                        )

    def test_high_confidence_mojibake_is_rejected_but_single_a_tilde_is_not(self) -> None:
        s1._validate_agent_text({"name": "João Ãlvaro"})
        for damaged in ("锟斤拷", "Ã¤Â¸"):
            with self.subTest(damaged=damaged):
                with self.assertRaisesRegex(
                    s1.S1Error, "S1_TEXT_ENCODING_CORRUPT"
                ):
                    s1._validate_agent_text({"nested": damaged})


class PhaseSemanticGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.control = {
            "id": "INT-001",
            "domain": "I0",
            "hardness": "author_locked",
            "heading": "Locked identity",
            "value": "Approved protagonist identity and authority boundary.",
            "source_locator": {
                "control_id": "INT-001",
                "artifact": {"path": "sources/I0.json", "sha256": "d" * 64},
                "selector": "control:INT-001",
                "value_sha256": "e" * 64,
            },
        }
        self.session = {
            "run_id": "RUN-PHASE-001",
            "session_id": "S1-PHASE-SESSION",
            "thread_id": "thread-phase",
            "input_gate": {"path": "S1/input-gate.json", "sha256": "a" * 64},
            "state_before": {"path": "state/revision-001.json", "sha256": "b" * 64},
            "input_manifest": {"stage": "B0", "path": "B0/stage-completion.json", "sha256": "c" * 64},
            "source_artifacts": [],
            "control_bindings": [],
        }
        self.demand = {
            "storyline_demands": [
                {
                    "id": "SLD-001",
                    "source_ids": ["INT-001"],
                    "obligation": (
                        "Locked identity: "
                        "Approved protagonist identity and authority boundary."
                    ),
                    "disposition": "merged",
                }
            ]
        }

    def _submit(
        self, workspace: Path, phase: str, payload: dict[str, object]
    ) -> None:
        with mock.patch.object(
            s1,
            "_validated_session",
            return_value=(self.session, {}, [self.control]),
        ):
            s1.submit_s1_phase(
                workspace,
                baseline_package=workspace / "B0",
                input_gate=object(),
                phase=phase,
                payload=payload,
            )

    def _valid_line(self) -> dict[str, object]:
        payload = {
            "design_decisions": [
                {
                    "id": "DEC-001",
                    "owner": "S1",
                    "projection_ids": ["SL-MAIN"],
                    "impact_ids": ["SL-MAIN"],
                    "compatibility": (
                        "Locked identity: "
                        "Approved protagonist identity and authority boundary."
                    ),
                }
            ],
            "storylines": [
                {
                    "id": "SL-MAIN",
                    "type": "main",
                    "source_decision_ids": ["DEC-001"],
                    "responsibility": (
                        "Locked identity: Approved protagonist identity and "
                        "authority boundary."
                    ),
                    "goal": "Turn the approved control into a coherent story line.",
                }
            ],
        }
        payload["line_claim_authority"] = line_claim_ledger(
            payload, [self.control]
        )
        return payload

    def _review(
        self,
        workspace: Path,
        payload: dict[str, object],
        *,
        failed_claim_ids: set[str] | None = None,
        reviewer_thread: str = "thread-independent-reviewer",
    ) -> str:
        s1._write(workspace / "generation-session.json", self.session)
        with mock.patch.object(
            s1,
            "_validated_session",
            return_value=(self.session, {}, [self.control]),
        ):
            request = s1.start_s1_line_claim_review(
                workspace,
                baseline_package=workspace / "B0",
                input_gate=object(),
                payload=payload,
            )
        failed = failed_claim_ids or set()
        verdicts = [
            {
                "claim_id": claim_id,
                "verdict": "fail" if claim_id in failed else "pass",
                "rationale": (
                    "The residual assertion exceeds S1 authority."
                    if claim_id in failed
                    else "The span matches its declared authority disposition."
                ),
            }
            for claim_id in request["claim_ids"]
        ]
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": reviewer_thread}, clear=False
        ):
            s1.submit_s1_line_claim_review(
                workspace,
                candidate_sha256=request["candidate_sha256"],
                verdicts=verdicts,
            )
        return request["candidate_sha256"]

    def test_demand_scan_rejects_missing_exact_author_value_before_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            bad = copy.deepcopy(self.demand)
            bad["storyline_demands"][0]["obligation"] = "Locked identity only"
            with self.assertRaises(s1.S1Error) as caught:
                self._submit(workspace, "demand-scan", bad)
            self.assertEqual(
                "S1_DEMAND_PHASE_SEMANTIC_INVALID", caught.exception.code
            )
            self.assertFalse(
                (workspace / "generation-evidence" / "01-demand-scan.json").exists()
            )

    def test_line_design_rejects_wrong_name_and_unauthorized_facts_without_source_participation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self._submit(workspace, "demand-scan", self.demand)
            bad = self._valid_line()
            bad["storylines"][0]["responsibility"] = (
                "A renamed protagonist gains refusal, copying, personal-guarantee "
                "and public-override powers not present in the source."
            )
            bad["design_decisions"][0]["compatibility"] = (
                "Choose the renamed protagonist and the new powers."
            )
            with self.assertRaises(s1.S1Error) as caught:
                self._submit(workspace, "line-design", bad)
            self.assertEqual(
                "S1_LINE_PHASE_SEMANTIC_INVALID", caught.exception.code
            )
            self.assertFalse(
                (workspace / "generation-evidence" / "02-line-design.json").exists()
            )

    def test_line_design_accepts_exact_b0_heading_value_and_reciprocal_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self._submit(workspace, "demand-scan", self.demand)
            payload = self._valid_line()
            self._review(workspace, payload)
            self._submit(workspace, "line-design", payload)
            self.assertTrue(
                (workspace / "generation-evidence" / "02-line-design.json").is_file()
            )

    def test_additive_out_of_scope_fact_is_rejected_by_independent_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self._submit(workspace, "demand-scan", self.demand)
            payload = self._valid_line()
            payload["storylines"][0]["responsibility"] += (
                "The protagonist receives an additional binding power"
            )
            payload["line_claim_authority"] = line_claim_ledger(
                payload, [self.control]
            )
            residual = next(
                item
                for item in payload["line_claim_authority"]
                if item["pointer"] == "/storylines/0/responsibility"
                and "additional binding power" in item["text"]
            )
            self.assertNotEqual("source_bound", residual["disposition"])
            self._review(
                workspace,
                payload,
                failed_claim_ids={residual["claim_id"]},
            )
            with self.assertRaises(s1.S1Error) as caught:
                self._submit(workspace, "line-design", payload)
            self.assertEqual(
                "S1_LINE_CLAIM_AUTHORITY_INVALID", caught.exception.code
            )
            self.assertFalse(
                (workspace / "generation-evidence" / "02-line-design.json").exists()
            )

    def test_missing_claim_is_rejected_before_line_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self._submit(workspace, "demand-scan", self.demand)
            payload = self._valid_line()
            payload["line_claim_authority"].pop()
            with self.assertRaises(s1.S1Error) as caught:
                self._submit(workspace, "line-design", payload)
            self.assertEqual(
                "S1_LINE_PHASE_SEMANTIC_INVALID", caught.exception.code
            )
            self.assertFalse(
                (workspace / "generation-evidence" / "02-line-design.json").exists()
            )

    def test_same_thread_reviewer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self._submit(workspace, "demand-scan", self.demand)
            payload = self._valid_line()
            with self.assertRaises(s1.S1Error) as caught:
                self._review(
                    workspace,
                    payload,
                    reviewer_thread=self.session["thread_id"],
                )
            self.assertEqual(
                "S1_LINE_REVIEW_NOT_INDEPENDENT", caught.exception.code
            )
            self.assertFalse(
                (workspace / "generation-evidence" / "02-line-design.json").exists()
            )

    def test_legitimate_s1_structural_derivation_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self._submit(workspace, "demand-scan", self.demand)
            payload = self._valid_line()
            structural = [
                item
                for item in payload["line_claim_authority"]
                if item["disposition"] == "s1_structural_derivation"
            ]
            self.assertTrue(structural)
            self._review(workspace, payload)
            self._submit(workspace, "line-design", payload)
            self.assertTrue(
                (workspace / "generation-evidence" / "02-line-design.json").is_file()
            )

    def test_downstream_and_open_claims_remain_noncanonical_and_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self._submit(workspace, "demand-scan", self.demand)
            payload = self._valid_line()
            payload["storylines"][0]["downstream_freedom"] = (
                "A later stage must choose the concrete realization."
            )
            payload["storylines"][0]["pressure"] = (
                "Whether this possibility is used remains unresolved."
            )
            payload["line_claim_authority"] = line_claim_ledger(
                payload, [self.control]
            )
            downstream = next(
                item
                for item in payload["line_claim_authority"]
                if item["pointer"] == "/storylines/0/downstream_freedom"
            )
            downstream.update(
                {
                    "disposition": "downstream_requirement",
                    "decision_ids": [],
                    "target_stage": "W1",
                    "target_requirement_id": "WR-001",
                }
            )
            open_claim = next(
                item
                for item in payload["line_claim_authority"]
                if item["pointer"] == "/storylines/0/pressure"
            )
            open_claim.update(
                {
                    "disposition": "open_item",
                    "decision_ids": [],
                    "open_item_id": "OPEN-001",
                }
            )
            self.assertFalse(downstream["source_control_ids"])
            self.assertFalse(open_claim["source_control_ids"])
            self._review(workspace, payload)
            self._submit(workspace, "line-design", payload)
            self.assertTrue(
                (workspace / "generation-evidence" / "02-line-design.json").is_file()
            )

    def test_rejected_review_does_not_poison_revised_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            self._submit(workspace, "demand-scan", self.demand)
            rejected = self._valid_line()
            rejected["storylines"][0]["goal"] += " Unapproved assertion"
            rejected["line_claim_authority"] = line_claim_ledger(
                rejected, [self.control]
            )
            rejected_claim = next(
                item
                for item in rejected["line_claim_authority"]
                if "Unapproved assertion" in item["text"]
            )
            rejected_hash = self._review(
                workspace,
                rejected,
                failed_claim_ids={rejected_claim["claim_id"]},
            )
            with self.assertRaises(s1.S1Error):
                self._submit(workspace, "line-design", rejected)

            revised = self._valid_line()
            revised["storylines"][0]["goal"] = (
                "Build a distinct structural progression for the approved control."
            )
            revised["line_claim_authority"] = line_claim_ledger(
                revised, [self.control]
            )
            revised_hash = self._review(workspace, revised)
            self.assertNotEqual(rejected_hash, revised_hash)
            self.assertTrue(
                (
                    workspace
                    / "line-claim-reviews"
                    / rejected_hash
                    / "review.json"
                ).is_file()
            )
            self._submit(workspace, "line-design", revised)
            self.assertTrue(
                (workspace / "generation-evidence" / "02-line-design.json").is_file()
            )


class SourceSequenceRealizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controls = [
            {
                "id": "CAU-001",
                "domain": "I4",
                "hardness": "author_locked",
                "heading": "Ordered handoffs",
                "value": "Four ordered A/B handoffs.",
            }
        ]
        self.units = [
            {
                "id": f"SCU-ORDER-{index}",
                "kind": "ordered_link",
                "relation_mode": "required",
                "text": f"step {index} before step {index + 1}",
            }
            for index in range(1, 5)
        ]
        self.lines = [
            {
                "id": "SL-A",
                "start_state": "A0",
                "state_changes": ["A1", "A2", "A3", "A4"],
                "end_state": "A5",
                "connection_ids": ["SLC-1", "SLC-2", "SLC-3", "SLC-4"],
            },
            {
                "id": "SL-B",
                "start_state": "B0",
                "state_changes": ["B1", "B2", "B3", "B4"],
                "end_state": "B5",
                "connection_ids": ["SLC-1", "SLC-2", "SLC-3", "SLC-4"],
            },
        ]

    def _payload(self, connection_ids: list[str]) -> dict[str, object]:
        realizations = []
        for index, (unit, connection_id) in enumerate(
            zip(self.units, connection_ids), 1
        ):
            from_line, to_line = (
                (self.lines[0], self.lines[1])
                if index % 2
                else (self.lines[1], self.lines[0])
            )
            realizations.append(
                {
                    "id": f"SSR-{index}",
                    "source_unit_id": unit["id"],
                    "from_anchor": {
                        "storyline_id": from_line["id"],
                        "state_index": index,
                        "state": from_line["state_changes"][index - 1],
                    },
                    "to_anchor": {
                        "storyline_id": to_line["id"],
                        "state_index": index,
                        "state": to_line["state_changes"][index - 1],
                    },
                    "boundary_from_anchor": {
                        "storyline_id": from_line["id"],
                        "state_index": index,
                        "state": from_line["state_changes"][index - 1],
                    },
                    "boundary_to_anchor": {
                        "storyline_id": to_line["id"],
                        "state_index": index,
                        "state": to_line["state_changes"][index - 1],
                    },
                    "realization_scope": "cross_line",
                    "reserved_connection_id": connection_id,
                    "phase3_fulfillment_kind": None,
                    "expected_witness_type": None,
                    "consistency_dimension": None,
                    "rationale": "This exact cross-line handoff realizes the ordered transition.",
                }
            )
        return {
            "design_decisions": [],
            "storylines": copy.deepcopy(self.lines),
            "line_claim_authority": [],
            "source_sequence_realizations": realizations,
        }

    def _assert_sequence_review_rejects(
        self,
        payload: dict[str, object],
        unit: dict[str, object],
        rationale: str,
    ) -> None:
        session = {
            "run_id": "RUN-SEQUENCE-DISPOSITION",
            "session_id": "S1-SEQUENCE-DISPOSITION",
            "thread_id": "thread-generation",
            "line_review_protocol": s1.LINE_REVIEW_PROTOCOL,
        }
        with mock.patch.object(s1, "_expected_claim_units", return_value=[unit]):
            with tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory)
                s1._write(workspace / "generation-session.json", session)
                request = s1._expected_line_review_request(
                    session, payload, self.controls
                )
                request_path, _ = s1._line_review_paths(
                    workspace, request["candidate_sha256"]
                )
                s1._write(request_path, request)
                item = payload["source_sequence_realizations"][0]
                with mock.patch.dict(
                    os.environ, {"CODEX_THREAD_ID": "thread-reviewer"}, clear=False
                ):
                    s1.submit_s1_line_claim_review(
                        workspace,
                        candidate_sha256=request["candidate_sha256"],
                        review={
                            "claim_verdicts": [],
                            "source_sequence_verdicts": [
                                {
                                    "realization_id": item["id"],
                                    "source_unit_id": item["source_unit_id"],
                                    "verdict": "fail",
                                    "rationale": rationale,
                                }
                            ],
                        },
                    )
                with self.assertRaisesRegex(s1.S1Error, "independent review rejected"):
                    s1._validate_line_claim_review(
                        workspace, payload, session, self.controls
                    )

    def test_four_cross_line_handoffs_with_only_two_reservations_fail(self) -> None:
        payload = self._payload(["SLC-1", "SLC-2", "SLC-1", "SLC-2"])
        with mock.patch.object(s1, "_expected_claim_units", return_value=self.units):
            with self.assertRaisesRegex(
                s1.S1Error, "different ordered transitions reuse one reserved connection"
            ):
                s1._validate_source_sequence_realizations(
                    payload, self.controls, required=True
                )

    def test_four_cross_line_handoffs_with_four_reservations_pass(self) -> None:
        payload = self._payload(["SLC-1", "SLC-2", "SLC-3", "SLC-4"])
        with mock.patch.object(s1, "_expected_claim_units", return_value=self.units):
            self.assertEqual(
                ["SSR-1", "SSR-2", "SSR-3", "SSR-4"],
                s1._validate_source_sequence_realizations(
                    payload, self.controls, required=True
                ),
            )

    def test_candidate_ordered_link_accepts_reviewed_non_relation(self) -> None:
        unit = {
            "id": "SCU-CANDIDATE",
            "kind": "ordered_link",
            "relation_mode": "candidate",
            "text": "Numbered neighboring classifications.",
        }
        payload = self._payload(["SLC-1"])
        payload["source_sequence_realizations"] = [
            {
                "id": "SSR-CANDIDATE",
                "source_unit_id": unit["id"],
                "from_anchor": None,
                "to_anchor": None,
                "boundary_from_anchor": None,
                "boundary_to_anchor": None,
                "realization_scope": "non_relational_candidate",
                "reserved_connection_id": None,
                "phase3_fulfillment_kind": None,
                "expected_witness_type": None,
                "consistency_dimension": None,
                "rationale": "Independent review found no source relation to promote.",
            }
        ]
        with mock.patch.object(s1, "_expected_claim_units", return_value=[unit]):
            self.assertEqual(
                ["SSR-CANDIDATE"],
                s1._validate_source_sequence_realizations(
                    payload, self.controls, required=True
                ),
            )
            request = s1._expected_line_review_request(
                {
                    "run_id": "RUN-CANDIDATE",
                    "session_id": "S1-CANDIDATE",
                    "thread_id": "thread-generation",
                    "line_review_protocol": s1.LINE_REVIEW_PROTOCOL,
                    "contract_revision": s1.CURRENT_CONTRACT_REVISION,
                },
                payload,
                self.controls,
            )
        self.assertIn(
            "non_relational_candidate",
            request["review_contract"]["source_sequence_rule"],
        )
        topology = {
            "story_claim_units": [unit],
            "story_claim_atoms": [
                {
                    "id": "SCA-CANDIDATE",
                    "source_unit_id": unit["id"],
                    "control_id": "CAU-001",
                    "atom_kind": "non_relational",
                    "obligation_ids": [],
                    "review_required": False,
                }
            ],
            "story_obligation_register": [],
            "temporal_architecture": {"markers": []},
            "cross_line_consistency": [],
        }
        s1._validate_semantic_constraint_fulfillment(payload, topology)

    def test_non_relation_scope_rejects_required_or_non_null_fields(self) -> None:
        payload = self._payload(["SLC-1"])
        item = payload["source_sequence_realizations"][0]
        item["realization_scope"] = "non_relational_candidate"
        for field in (
            "from_anchor", "to_anchor", "boundary_from_anchor",
            "boundary_to_anchor", "reserved_connection_id",
        ):
            item[field] = None
        with mock.patch.object(
            s1, "_expected_claim_units", return_value=[self.units[0]]
        ):
            with self.assertRaisesRegex(
                s1.S1Error, "S1_SOURCE_SEQUENCE_REALIZATION_INVALID"
            ):
                s1._validate_source_sequence_realizations(
                    payload, self.controls, required=True
                )

    def test_historical_boundaryless_registry_remains_read_only_compatible(
        self,
    ) -> None:
        payload = self._payload(["SLC-1", "SLC-2", "SLC-3", "SLC-4"])
        for item in payload["source_sequence_realizations"]:
            item.pop("boundary_from_anchor")
            item.pop("boundary_to_anchor")
            item.pop("consistency_dimension")
        with mock.patch.object(s1, "_expected_claim_units", return_value=self.units):
            s1._validate_source_sequence_realizations(
                payload, self.controls, required=False
            )

    def _causal_path_payload(self) -> dict[str, object]:
        payload = self._payload(["SLC-1", "SLC-2", "SLC-3", "SLC-4"])
        item = payload["source_sequence_realizations"][0]
        payload["source_sequence_realizations"] = [item]
        item["from_anchor"] = {
            "storyline_id": "SL-A", "state_index": 1, "state": "A1"
        }
        item["to_anchor"] = {
            "storyline_id": "SL-B", "state_index": 4, "state": "B4"
        }
        item["boundary_from_anchor"] = {
            "storyline_id": "SL-A", "state_index": 3, "state": "A3"
        }
        item["boundary_to_anchor"] = {
            "storyline_id": "SL-B", "state_index": 2, "state": "B2"
        }
        item["rationale"] = (
            "A1 and B4 are the semantic endpoints; A3 and B2 are the forward "
            "implementation boundary for the reserved cross-line edge."
        )
        return payload

    def test_cross_line_causal_path_uses_boundary_connection_and_ordered_milestones(
        self,
    ) -> None:
        payload = self._causal_path_payload()
        with mock.patch.object(s1, "_expected_claim_units", return_value=[self.units[0]]):
            s1._validate_source_sequence_realizations(
                payload, self.controls, required=True
            )
        connection = {
            "id": "SLC-1",
            "relation": "causal",
            "from_storyline_id": "SL-A",
            "from_state_index": 3,
            "from_state": "A3",
            "to_storyline_id": "SL-B",
            "to_state_index": 2,
            "to_state": "B2",
        }
        s1._validate_reserved_source_sequence_connections(
            payload, {"SLC-1": connection}
        )
        milestones = {
            "MS-1": {
                "order": 1,
                "state_refs": [
                    {"storyline_id": "SL-A", "state_index": 1},
                    {"storyline_id": "SL-B", "state_index": 0},
                ],
            },
            "MS-2": {
                "order": 2,
                "state_refs": [
                    {"storyline_id": "SL-A", "state_index": 3},
                    {"storyline_id": "SL-B", "state_index": 2},
                ],
            },
            "MS-3": {
                "order": 3,
                "state_refs": [
                    {"storyline_id": "SL-B", "state_index": 4},
                ],
            },
        }
        visits = {
            "SL-A": [(1, 1), (2, 3)],
            "SL-B": [(1, 0), (2, 2), (3, 4)],
        }
        s1._validate_milestone_line_state_progression(visits)
        s1._validate_global_temporal_semantics(
            {"story_obligation_register": []},
            connections={"SLC-1": connection},
            milestones=milestones,
            line_state_visits=visits,
        )

    def test_cross_line_causal_path_rejects_reverse_or_wrong_line_boundary(
        self,
    ) -> None:
        for boundary in (
            {"storyline_id": "SL-A", "state_index": 0, "state": "A0"},
            {"storyline_id": "SL-B", "state_index": 3, "state": "B3"},
        ):
            with self.subTest(boundary=boundary):
                payload = self._causal_path_payload()
                payload["source_sequence_realizations"][0][
                    "boundary_from_anchor"
                ] = boundary
                with mock.patch.object(
                    s1, "_expected_claim_units", return_value=[self.units[0]]
                ):
                    with self.assertRaisesRegex(
                        s1.S1Error, "boundary anchors do not form forward line paths"
                    ):
                        s1._validate_source_sequence_realizations(
                            payload, self.controls, required=True
                        )

    def test_phase3_rejects_semantic_endpoints_instead_of_boundary_endpoints(
        self,
    ) -> None:
        payload = self._causal_path_payload()
        direct_semantic_connection = {
            "from_storyline_id": "SL-A",
            "from_state_index": 1,
            "from_state": "A1",
            "to_storyline_id": "SL-B",
            "to_state_index": 4,
            "to_state": "B4",
        }
        with self.assertRaisesRegex(
            s1.S1Error, "S1_SOURCE_SEQUENCE_CONNECTION_MISMATCH"
        ):
            s1._validate_reserved_source_sequence_connections(
                payload, {"SLC-1": direct_semantic_connection}
            )

    def test_old_direct_semantic_cooccurrence_still_regresses_source_line(self) -> None:
        with self.assertRaisesRegex(
            s1.S1Error, "S1_MILESTONE_LINE_STATE_REGRESSION"
        ):
            s1._validate_milestone_line_state_progression(
                {
                    "SL-A": [(1, 1), (2, 3), (3, 1)],
                    "SL-B": [(1, 0), (2, 2), (3, 4)],
                }
            )

    def test_review_contract_forbids_late_boundary_replacing_global_endpoint(
        self,
    ) -> None:
        payload = self._causal_path_payload()
        session = {
            "run_id": "RUN-SEQUENCE-CONTEXT",
            "session_id": "S1-SEQUENCE-CONTEXT",
            "thread_id": "thread-generation",
            "line_review_protocol": s1.LINE_REVIEW_PROTOCOL,
        }
        with mock.patch.object(s1, "_expected_claim_units", return_value=[self.units[0]]):
            request = s1._expected_line_review_request(
                session, payload, self.controls
            )
        rule = request["review_contract"]["source_sequence_rule"]
        self.assertIn("neighboring states", rule)
        self.assertIn("boundary substituted for the source endpoint", rule)
        self._assert_sequence_review_rejects(
            payload,
            self.units[0],
            "A3 is only a late implementation boundary and cannot replace semantic endpoint A1.",
        )

    def test_within_line_same_anchor_and_reverse_order_fail(self) -> None:
        unit = self.units[0]
        payload = self._payload(["SLC-1", "SLC-2", "SLC-3", "SLC-4"])
        payload["source_sequence_realizations"] = [
            {
                "id": "SSR-1",
                "source_unit_id": unit["id"],
                "from_anchor": {
                    "storyline_id": "SL-A", "state_index": 2, "state": "A2"
                },
                "to_anchor": {
                    "storyline_id": "SL-A", "state_index": 1, "state": "A1"
                },
                "boundary_from_anchor": None,
                "boundary_to_anchor": None,
                "realization_scope": "within_line",
                "reserved_connection_id": None,
                "phase3_fulfillment_kind": None,
                "expected_witness_type": None,
                "consistency_dimension": None,
                "rationale": "Candidate mapping for a locked ordered transition.",
            }
        ]
        with mock.patch.object(s1, "_expected_claim_units", return_value=[unit]):
            with self.assertRaisesRegex(s1.S1Error, "within-line anchors are reversed"):
                s1._validate_source_sequence_realizations(
                    payload, self.controls, required=True
                )
            payload["source_sequence_realizations"][0]["to_anchor"] = copy.deepcopy(
                payload["source_sequence_realizations"][0]["from_anchor"]
            )
            with self.assertRaisesRegex(s1.S1Error, "collapses an ordered transition"):
                s1._validate_source_sequence_realizations(
                    payload, self.controls, required=True
                )

    def test_semantically_early_endpoint_can_be_rejected_by_exact_review(self) -> None:
        payload = self._payload(["SLC-1", "SLC-2", "SLC-3", "SLC-4"])
        payload["source_sequence_realizations"] = [
            payload["source_sequence_realizations"][0]
        ]
        unit = self.units[0]
        session = {
            "run_id": "RUN-SEQUENCE-REVIEW",
            "session_id": "S1-SEQUENCE-SESSION",
            "thread_id": "thread-generation",
            "line_review_protocol": s1.LINE_REVIEW_PROTOCOL,
        }
        with mock.patch.object(s1, "_expected_claim_units", return_value=[unit]):
            with tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory)
                s1._write(workspace / "generation-session.json", session)
                request = s1._expected_line_review_request(
                    session, payload, self.controls
                )
                request_path, _ = s1._line_review_paths(
                    workspace, request["candidate_sha256"]
                )
                s1._write(request_path, request)
                with mock.patch.dict(
                    os.environ, {"CODEX_THREAD_ID": "thread-reviewer"}, clear=False
                ):
                    s1.submit_s1_line_claim_review(
                        workspace,
                        candidate_sha256=request["candidate_sha256"],
                        review={
                            "claim_verdicts": [],
                            "source_sequence_verdicts": [
                                {
                                    "realization_id": "SSR-1",
                                    "source_unit_id": unit["id"],
                                    "verdict": "fail",
                                    "rationale": (
                                        "The selected target is an early intermediate "
                                        "state, not the ordered source endpoint."
                                    ),
                                }
                            ],
                        },
                    )
                with self.assertRaisesRegex(
                    s1.S1Error, "independent review rejected"
                ):
                    s1._validate_line_claim_review(
                        workspace, payload, session, self.controls
                    )

    def test_current_protocol_rejects_legacy_or_partial_review_submission(self) -> None:
        payload = self._payload(["SLC-1", "SLC-2", "SLC-3", "SLC-4"])
        payload["source_sequence_realizations"] = [
            payload["source_sequence_realizations"][0]
        ]
        unit = self.units[0]
        session = {
            "run_id": "RUN-SEQUENCE-ENVELOPE",
            "session_id": "S1-SEQUENCE-ENVELOPE",
            "thread_id": "thread-generation",
            "line_review_protocol": s1.LINE_REVIEW_PROTOCOL,
        }
        with mock.patch.object(s1, "_expected_claim_units", return_value=[unit]):
            with tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory)
                s1._write(workspace / "generation-session.json", session)
                request = s1._expected_line_review_request(
                    session, payload, self.controls
                )
                request_path, _ = s1._line_review_paths(
                    workspace, request["candidate_sha256"]
                )
                s1._write(request_path, request)
                with mock.patch.dict(
                    os.environ, {"CODEX_THREAD_ID": "thread-reviewer"}, clear=False
                ):
                    with self.assertRaisesRegex(
                        s1.S1Error, "complete claim and source-sequence review envelope"
                    ):
                        s1.submit_s1_line_claim_review(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            verdicts=[],
                        )

    def test_topology_must_realize_reserved_id_and_exact_endpoint_anchors(self) -> None:
        payload = self._payload(["SLC-1", "SLC-2", "SLC-3", "SLC-4"])
        connections = {}
        for realization in payload["source_sequence_realizations"]:
            from_anchor = realization["from_anchor"]
            to_anchor = realization["to_anchor"]
            connections[realization["reserved_connection_id"]] = {
                "from_storyline_id": from_anchor["storyline_id"],
                "from_state_index": from_anchor["state_index"],
                "from_state": from_anchor["state"],
                "to_storyline_id": to_anchor["storyline_id"],
                "to_state_index": to_anchor["state_index"],
                "to_state": to_anchor["state"],
            }
        s1._validate_reserved_source_sequence_connections(payload, connections)
        connections["SLC-3"]["to_state_index"] = 4
        connections["SLC-3"]["to_state"] = "A4"
        with self.assertRaisesRegex(
            s1.S1Error, "reserved connection does not realize exact endpoints"
        ):
            s1._validate_reserved_source_sequence_connections(payload, connections)

    def test_normative_fairness_constraint_passes_and_phase3_is_traceable(self) -> None:
        unit = {
            "id": "SCU-NAR-FAIRNESS-009",
            "control_id": "NAR-FAIRNESS",
            "kind": "ordered_link",
            "relation_mode": "candidate",
            "text": "Every judgment needs evidence; reliable narration must not lie.",
        }
        payload = {
            "design_decisions": [],
            "storylines": copy.deepcopy(self.lines),
            "line_claim_authority": [],
            "source_sequence_realizations": [
                {
                    "id": "SSR-FAIRNESS",
                    "source_unit_id": unit["id"],
                    "from_anchor": None,
                    "to_anchor": None,
                    "boundary_from_anchor": None,
                    "boundary_to_anchor": None,
                    "realization_scope": "semantic_constraint",
                    "reserved_connection_id": None,
                    "phase3_fulfillment_kind": "obligation",
                    "expected_witness_type": "story_obligation",
                    "consistency_dimension": None,
                    "rationale": (
                        "This is a narration-wide fairness rule, not a story-state transition."
                    ),
                }
            ],
        }
        with mock.patch.object(s1, "_expected_claim_units", return_value=[unit]):
            s1._validate_source_sequence_realizations(
                payload, self.controls, required=True
            )
        topology = {
            "story_claim_units": [unit],
            "story_claim_atoms": [
                {
                    "id": "SCA-FAIRNESS",
                    "source_unit_id": unit["id"],
                    "control_id": unit["control_id"],
                    "atom_kind": "information_window",
                }
            ],
            "story_obligation_register": [
                {
                    "id": "SOB-FAIRNESS",
                    "source_claim_atom_ids": ["SCA-FAIRNESS"],
                    "source_control_ids": ["NAR-FAIRNESS"],
                }
            ],
            "temporal_architecture": {"markers": []},
            "cross_line_consistency": [],
        }
        s1._validate_semantic_constraint_fulfillment(payload, topology)
        topology["story_claim_atoms"][0]["atom_kind"] = "non_relational"
        with self.assertRaisesRegex(s1.S1Error, "lacks a relational source atom"):
            s1._validate_semantic_constraint_fulfillment(payload, topology)
        topology["story_claim_atoms"][0]["atom_kind"] = "information_window"
        topology["story_obligation_register"] = []
        with self.assertRaisesRegex(s1.S1Error, "no traceable obligation witness"):
            s1._validate_semantic_constraint_fulfillment(payload, topology)

    def test_arbitrary_state_mapping_for_normative_rule_is_reviewer_rejected(self) -> None:
        unit = {
            "id": "SCU-NAR-FAIRNESS-009",
            "control_id": "NAR-FAIRNESS",
            "kind": "ordered_link",
            "relation_mode": "candidate",
            "text": "Every judgment needs evidence; reliable narration must not lie.",
        }
        payload = self._payload(["SLC-1", "SLC-2", "SLC-3", "SLC-4"])
        item = payload["source_sequence_realizations"][0]
        payload["source_sequence_realizations"] = [item]
        item["source_unit_id"] = unit["id"]
        self._assert_sequence_review_rejects(
            payload,
            unit,
            "The chosen story states are arbitrary and do not realize this narration-wide rule.",
        )

    def test_global_spine_cannot_escape_as_semantic_constraint(self) -> None:
        unit = {
            "id": "SCU-CAU-GLOBAL-SPINE-008",
            "control_id": "CAU-GLOBAL-SPINE",
            "kind": "arrow_link",
            "relation_mode": "required",
            "text": "R-07 decides to protect others -> the attack is stopped.",
        }
        payload = {
            "design_decisions": [],
            "storylines": copy.deepcopy(self.lines),
            "line_claim_authority": [],
            "source_sequence_realizations": [
                {
                    "id": "SSR-GLOBAL-SPINE",
                    "source_unit_id": unit["id"],
                    "from_anchor": None,
                    "to_anchor": None,
                    "boundary_from_anchor": None,
                    "boundary_to_anchor": None,
                    "realization_scope": "semantic_constraint",
                    "reserved_connection_id": None,
                    "phase3_fulfillment_kind": "obligation",
                    "expected_witness_type": "story_obligation",
                    "consistency_dimension": None,
                    "rationale": "Candidate attempts to classify a causal spine as a rule.",
                }
            ],
        }
        with mock.patch.object(s1, "_expected_claim_units", return_value=[unit]):
            s1._validate_source_sequence_realizations(
                payload, self.controls, required=True
            )
        self._assert_sequence_review_rejects(
            payload,
            unit,
            "This is a genuine causal state sequence and may not escape state anchors.",
        )


class SourceSequenceStructuralClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.unit = {
            "id": "SCU-EVIDENCE-GEO",
            "kind": "ordered_link",
            "relation_mode": "required",
            "text": "Evidence pressure reaches the geographic background.",
        }
        self.controls = [
            {
                "id": "CAU-EVIDENCE-GEO",
                "domain": "I4",
                "hardness": "author_locked",
                "heading": "Evidence and geography",
                "value": "Evidence pressure reaches the geographic background.",
            }
        ]
        self.payload = {
            "storylines": [
                {
                    "id": "SL-MAIN",
                    "type": "main",
                    "start_state": "Main begins",
                    "state_changes": ["Main changes"],
                    "end_state": "Main ends",
                    "connection_ids": ["SLC-EVIDENCE-MAIN"],
                },
                {
                    "id": "SL-EVIDENCE",
                    "type": "supporting",
                    "start_state": "Evidence begins",
                    "state_changes": ["Evidence changes"],
                    "end_state": "Evidence ends",
                    "connection_ids": [
                        "SLC-EVIDENCE-MAIN",
                        "SLC-EVIDENCE-GEO",
                    ],
                },
                {
                    "id": "SL-GEO",
                    "type": "background",
                    "start_state": "Geography begins",
                    "state_changes": ["Geography changes"],
                    "end_state": "Geography ends",
                    "connection_ids": ["SLC-EVIDENCE-GEO"],
                },
            ],
            "source_sequence_realizations": [
                {
                    "id": "SSR-EVIDENCE-GEO",
                    "source_unit_id": self.unit["id"],
                    "from_anchor": {
                        "storyline_id": "SL-EVIDENCE",
                        "state_index": 1,
                        "state": "Evidence changes",
                    },
                    "to_anchor": {
                        "storyline_id": "SL-GEO",
                        "state_index": 1,
                        "state": "Geography changes",
                    },
                    "boundary_from_anchor": {
                        "storyline_id": "SL-EVIDENCE",
                        "state_index": 1,
                        "state": "Evidence changes",
                    },
                    "boundary_to_anchor": {
                        "storyline_id": "SL-GEO",
                        "state_index": 1,
                        "state": "Geography changes",
                    },
                    "realization_scope": "cross_line",
                    "reserved_connection_id": "SLC-EVIDENCE-GEO",
                    "phase3_fulfillment_kind": None,
                    "expected_witness_type": None,
                    "consistency_dimension": None,
                    "rationale": "The reserved edge fixes the evidence-to-geography direction.",
                }
            ],
        }

    def _validate_source_sequence_then_closure(self) -> None:
        with mock.patch.object(s1, "_expected_claim_units", return_value=[self.unit]):
            s1._validate_source_sequence_realizations(
                self.payload, self.controls, required=True
            )
        s1._validate_source_sequence_structural_closure(self.payload)

    def test_sink_background_with_only_incoming_reservation_fails(self) -> None:
        with self.assertRaisesRegex(
            s1.S1Error, "S1_SOURCE_SEQUENCE_STRUCTURAL_CLOSURE_MISSING.*SL-GEO"
        ):
            self._validate_source_sequence_then_closure()

    def test_unreserved_shared_connection_proves_bidirectional_capacity(self) -> None:
        free_id = "SLC-GEO-MAIN-FREE"
        self.payload["storylines"][0]["connection_ids"].append(free_id)
        self.payload["storylines"][2]["connection_ids"].append(free_id)
        self._validate_source_sequence_then_closure()

    def test_declared_terminal_consequence_is_not_forced_back_to_main(self) -> None:
        main, evidence, terminal = self.payload["storylines"]
        main.update({
            "closure_mode": None,
            "terminal_source_anchor": None,
            "terminal_entry_connection_id": None,
        })
        evidence.update({
            "closure_mode": "converges_to_main",
            "terminal_source_anchor": None,
            "terminal_entry_connection_id": None,
        })
        terminal.update({
            "closure_mode": "terminal_consequence",
            "terminal_source_anchor": {
                "storyline_id": "SL-EVIDENCE",
                "state_index": 1,
                "state": "Evidence changes",
            },
            "terminal_entry_connection_id": "SLC-EVIDENCE-GEO",
        })
        s1._validate_source_sequence_structural_closure(
            self.payload, require_closure_declarations=True
        )

    def test_terminal_consequence_rejects_causal_outbound(self) -> None:
        lines = copy.deepcopy(self.payload["storylines"])
        for line in lines:
            line.update({
                "closure_mode": (
                    "terminal_consequence"
                    if line["id"] == "SL-GEO"
                    else "converges_to_main"
                    if line["id"] != "SL-MAIN"
                    else None
                ),
                "terminal_source_anchor": None,
                "terminal_entry_connection_id": None,
            })
        terminal = lines[2]
        terminal["terminal_source_anchor"] = {
            "storyline_id": "SL-EVIDENCE",
            "state_index": 1,
            "state": "Evidence changes",
        }
        terminal["terminal_entry_connection_id"] = "SLC-EVIDENCE-GEO"
        connections = [
            {
                "id": "SLC-EVIDENCE-GEO", "relation": "causal",
                "from_storyline_id": "SL-EVIDENCE", "from_state_index": 1,
                "from_state": "Evidence changes", "to_storyline_id": "SL-GEO",
                "to_state_index": 1, "to_state": "Geography changes",
            },
            {
                "id": "SLC-OUT", "relation": "causal",
                "from_storyline_id": "SL-GEO", "from_state_index": 1,
                "from_state": "Geography changes", "to_storyline_id": "SL-MAIN",
                "to_state_index": 1, "to_state": "Main changes",
            },
        ]
        with self.assertRaisesRegex(
            s1.S1Error, "S1_TERMINAL_CAUSAL_OUTBOUND_FORBIDDEN"
        ):
            s1._validate_line_closure_declarations(
                {"storylines": lines}, required=True, connections=connections
            )


class LineReviewContractSelectionTests(unittest.TestCase):
    def _start_review(
        self,
        workspace: Path,
        *,
        session: dict[str, object],
        storylines: list[dict[str, object]],
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "design_decisions": [],
            "storylines": storylines,
            "line_claim_authority": [],
        }
        if session.get("line_review_protocol") == s1.LINE_REVIEW_PROTOCOL:
            payload["source_sequence_realizations"] = []

        def validate_closure(
            _demand: dict[str, object],
            line_payload: dict[str, object],
            _controls: list[dict[str, object]],
            *,
            require_source_sequences: bool = False,
            require_current_contract: bool = False,
        ) -> None:
            del require_source_sequences
            s1._validate_source_sequence_structural_closure(
                line_payload,
                require_closure_declarations=require_current_contract,
            )

        request = {"candidate_sha256": "a" * 64}
        with (
            mock.patch.object(
                s1, "_validated_session", return_value=(session, {}, [])
            ),
            mock.patch.object(
                s1,
                "_sealed_phase_payload",
                return_value={"storyline_demands": []},
            ),
            mock.patch.object(
                s1, "_validate_line_phase_semantics", side_effect=validate_closure
            ),
            mock.patch.object(
                s1, "_expected_line_review_request", return_value=request
            ),
        ):
            return s1.start_s1_line_claim_review(
                workspace,
                baseline_package=workspace / "B0",
                input_gate=object(),
                payload=payload,
            )

    @staticmethod
    def _current_terminal_lines() -> list[dict[str, object]]:
        return [
            {
                "id": "SL-MAIN",
                "type": "main",
                "start_state": "Main begins",
                "state_changes": ["Main changes"],
                "end_state": "Main ends",
                "connection_ids": ["SLC-MAIN-TERMINAL"],
                "closure_mode": None,
                "terminal_source_anchor": None,
                "terminal_entry_connection_id": None,
            },
            {
                "id": "SL-TERMINAL",
                "type": "background",
                "start_state": "Consequence begins",
                "state_changes": ["Consequence lands"],
                "end_state": "Consequence remains",
                "connection_ids": ["SLC-MAIN-TERMINAL"],
                "closure_mode": "terminal_consequence",
                "terminal_source_anchor": {
                    "storyline_id": "SL-MAIN",
                    "state_index": 1,
                    "state": "Main changes",
                },
                "terminal_entry_connection_id": "SLC-MAIN-TERMINAL",
            },
        ]

    def test_current_review_start_accepts_valid_terminal_consequence(self) -> None:
        session = {
            "run_id": "RUN-CURRENT-TERMINAL",
            "session_id": "S1-CURRENT-TERMINAL",
            "thread_id": "thread-current",
            "line_review_protocol": s1.LINE_REVIEW_PROTOCOL,
            "contract_revision": s1.CURRENT_CONTRACT_REVISION,
        }
        with tempfile.TemporaryDirectory() as directory:
            request = self._start_review(
                Path(directory),
                session=session,
                storylines=self._current_terminal_lines(),
            )
        self.assertEqual("a" * 64, request["candidate_sha256"])

    def test_legacy_review_start_keeps_implicit_closure_compatibility(self) -> None:
        session = {
            "run_id": "RUN-LEGACY-CLOSURE",
            "session_id": "S1-LEGACY-CLOSURE",
            "thread_id": "thread-legacy",
        }
        storylines = [
            {
                "id": "SL-MAIN",
                "type": "main",
                "connection_ids": ["SLC-LEGACY"],
            },
            {
                "id": "SL-SUPPORT",
                "type": "supporting",
                "connection_ids": ["SLC-LEGACY"],
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            request = self._start_review(
                Path(directory), session=session, storylines=storylines
            )
        self.assertEqual("a" * 64, request["candidate_sha256"])

    def test_current_review_start_still_rejects_invalid_terminal_consequence(
        self,
    ) -> None:
        session = {
            "run_id": "RUN-CURRENT-INVALID-TERMINAL",
            "session_id": "S1-CURRENT-INVALID-TERMINAL",
            "thread_id": "thread-current",
            "line_review_protocol": s1.LINE_REVIEW_PROTOCOL,
            "contract_revision": s1.CURRENT_CONTRACT_REVISION,
        }
        storylines = self._current_terminal_lines()
        storylines[1]["terminal_source_anchor"] = {
            "storyline_id": "SL-MAIN",
            "state_index": 1,
            "state": "Stale main state",
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(
                s1.S1Error, "S1_STORYLINE_CLOSURE_DECLARATION_INVALID"
            ):
                self._start_review(
                    Path(directory), session=session, storylines=storylines
                )


class SemanticConsistencyWitnessTests(unittest.TestCase):
    def _model(
        self, *, declared_dimension: str = "causality", witness_dimension: str = "causality"
    ) -> dict[str, object]:
        return {
            "source_sequence_realizations": [
                {
                    "id": "SSR-CONSISTENCY",
                    "source_unit_id": "SCU-GLOBAL-RULE",
                    "from_anchor": None,
                    "to_anchor": None,
                    "boundary_from_anchor": None,
                    "boundary_to_anchor": None,
                    "realization_scope": "semantic_constraint",
                    "reserved_connection_id": None,
                    "phase3_fulfillment_kind": "consistency",
                    "expected_witness_type": "consistency_check",
                    "consistency_dimension": declared_dimension,
                    "rationale": "The global semantic rule is traced in one exact dimension.",
                }
            ],
            "story_claim_units": [
                {"id": "SCU-GLOBAL-RULE", "control_id": "CTL-GLOBAL-RULE"}
            ],
            "story_claim_atoms": [
                {
                    "id": "SCA-GLOBAL-RULE",
                    "source_unit_id": "SCU-GLOBAL-RULE",
                    "control_id": "CTL-GLOBAL-RULE",
                    "atom_kind": "temporal_relation",
                }
            ],
            "story_obligation_register": [],
            "temporal_architecture": {"markers": []},
            "cross_line_consistency": [
                {
                    "dimension": witness_dimension,
                    "witness_ids": ["SCA-GLOBAL-RULE", "CTL-GLOBAL-RULE"],
                }
            ],
        }

    def test_declared_pair_is_allowed_only_in_matching_dimension(self) -> None:
        model = self._model()
        allowances = s1._semantic_consistency_witness_allowances(model)
        self.assertEqual(
            {"SCA-GLOBAL-RULE", "CTL-GLOBAL-RULE"}, allowances["causality"]
        )
        self.assertFalse(allowances["time"])
        s1._validate_consistency_witness_subset(
            "causality",
            {"SCA-GLOBAL-RULE", "CTL-GLOBAL-RULE"},
            allowances["causality"],
        )
        s1._validate_semantic_constraint_fulfillment(model, model)

    def test_wrong_dimension_remains_rejected(self) -> None:
        model = self._model(witness_dimension="time")
        allowances = s1._semantic_consistency_witness_allowances(model)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_WITNESS_INVALID"
        ):
            s1._validate_consistency_witness_subset(
                "time",
                {"SCA-GLOBAL-RULE", "CTL-GLOBAL-RULE"},
                allowances["time"],
            )
        with self.assertRaisesRegex(
            s1.S1Error, "S1_SOURCE_SEQUENCE_FULFILLMENT_INVALID"
        ):
            s1._validate_semantic_constraint_fulfillment(model, model)

    def test_undeclared_pair_remains_rejected(self) -> None:
        model = self._model()
        model["source_sequence_realizations"] = []
        allowances = s1._semantic_consistency_witness_allowances(model)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_WITNESS_INVALID"
        ):
            s1._validate_consistency_witness_subset(
                "causality",
                {"SCA-GLOBAL-RULE", "CTL-GLOBAL-RULE"},
                allowances["causality"],
            )


class StoryObligationValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        artifact = {"path": "sources/I0/control-projection.json", "sha256": "a" * 64}
        self.locator = {
            "control_id": "INT-001",
            "artifact": artifact,
            "selector": "control:INT-001",
            "value_sha256": "b" * 64,
        }
        self.open_locator = {
            "control_id": "NAR-001",
            "artifact": {"path": "sources/I5/control-projection.json", "sha256": "c" * 64},
            "selector": "control:NAR-001",
            "value_sha256": "d" * 64,
        }
        self.controls = {
            "INT-001": {
                "id": "INT-001",
                "hardness": "author_locked",
                "value": "A locked causal statement.",
                "source_locator": self.locator,
            },
            "NAR-001": {
                "id": "NAR-001",
                "hardness": "author_open",
                "value": "An author-open statement.",
                "source_locator": self.open_locator,
            },
        }
        self.lines = {
            "SL-A": {
                "start_state": "A starts",
                "state_changes": ["A changes"],
                "end_state": "A ends",
            },
            "SL-B": {
                "start_state": "B starts",
                "state_changes": ["B changes"],
                "end_state": "B ends",
            },
        }
        self.units = s1._expected_claim_units(list(self.controls.values()))
        locked_unit = next(item for item in self.units if item["control_id"] == "INT-001")
        open_unit = next(item for item in self.units if item["control_id"] == "NAR-001")
        self.atoms = [
            {
                "id": "SCA-001",
                "source_unit_id": locked_unit["id"],
                "control_id": "INT-001",
                "source_locator": copy.deepcopy(self.locator),
                "claim": "The first state causes the second state.",
                "atom_kind": "causal_relation",
                "obligation_ids": ["SOB-001"],
                "rationale": "One exact source unit has one causal disposition.",
                "review_required": False,
            },
            {
                "id": "SCA-002",
                "source_unit_id": open_unit["id"],
                "control_id": "NAR-001",
                "source_locator": copy.deepcopy(self.open_locator),
                "claim": "The author keeps this exact source unit open.",
                "atom_kind": "author_open",
                "obligation_ids": [],
                "rationale": "The source control is author-open.",
                "review_required": False,
            },
        ]
        self.model = {
            "connections": [],
            "story_claim_units": copy.deepcopy(self.units),
            "story_claim_atoms": copy.deepcopy(self.atoms),
            "story_obligation_register": [
                {
                    "id": "SOB-001",
                    "kind": "causes",
                    "source_claim_atom_ids": ["SCA-001"],
                    "source_control_ids": ["INT-001"],
                    "source_locators": [copy.deepcopy(self.locator)],
                    "antecedent_anchors": [
                        {"storyline_id": "SL-A", "state_index": 0, "state": "A starts"}
                    ],
                    "consequent_anchor": {
                        "storyline_id": "SL-A",
                        "state_index": 1,
                        "state": "A changes",
                    },
                    "proposition_id": None,
                    "audience": None,
                    "rationale": "The locked cause changes the line state.",
                    "acceptance_check": "The second state requires the first state.",
                }
            ],
            "story_obligation_coverage": [
                {
                    "id": "SOC-001",
                    "control_id": "INT-001",
                    "source_locator": copy.deepcopy(self.locator),
                    "disposition": "obligated",
                    "claim_atom_ids": ["SCA-001"],
                    "obligation_ids": ["SOB-001"],
                    "rationale": "The locked control has one explicit causal obligation.",
                    "review_required": False,
                },
                {
                    "id": "SOC-002",
                    "control_id": "NAR-001",
                    "source_locator": copy.deepcopy(self.open_locator),
                    "disposition": "author_open",
                    "claim_atom_ids": ["SCA-002"],
                    "obligation_ids": [],
                    "rationale": "The author-open control remains open.",
                    "review_required": False,
                },
            ],
        }

    def test_accepts_exact_source_complete_register(self) -> None:
        unit_ids, atom_ids, obligation_ids, coverage_ids = s1._validate_story_obligations(
            self.model, self.controls, self.lines
        )
        self.assertEqual({item["id"] for item in self.units}, unit_ids)
        self.assertEqual({"SCA-001", "SCA-002"}, atom_ids)
        self.assertEqual({"SOB-001"}, obligation_ids)
        self.assertEqual({"SOC-001", "SOC-002"}, coverage_ids)

    def test_rejects_stale_source_locator(self) -> None:
        model = copy.deepcopy(self.model)
        model["story_obligation_register"][0]["source_locators"][0][
            "value_sha256"
        ] = "e" * 64
        with self.assertRaisesRegex(s1.S1Error, "S1_STORY_OBLIGATION_SOURCE_STALE"):
            s1._validate_story_obligations(model, self.controls, self.lines)

    def test_rejects_missing_control_disposition(self) -> None:
        model = copy.deepcopy(self.model)
        model["story_obligation_coverage"].pop()
        with self.assertRaisesRegex(
            s1.S1Error, "S1_STORY_OBLIGATION_COVERAGE_MISMATCH"
        ):
            s1._validate_story_obligations(model, self.controls, self.lines)

    def test_rejects_reversed_same_line_anchor(self) -> None:
        model = copy.deepcopy(self.model)
        model["story_obligation_register"][0]["antecedent_anchors"][0] = {
            "storyline_id": "SL-A",
            "state_index": 2,
            "state": "A ends",
        }
        with self.assertRaisesRegex(
            s1.S1Error, "S1_STORY_OBLIGATION_LINE_ORDER_INVALID"
        ):
            s1._validate_story_obligations(model, self.controls, self.lines)

    def test_rejects_cross_line_obligation_cycle(self) -> None:
        model = copy.deepcopy(self.model)
        second = copy.deepcopy(model["story_obligation_register"][0])
        second.update(
            {
                "id": "SOB-002",
                "kind": "causes",
                "antecedent_anchors": [
                    {"storyline_id": "SL-B", "state_index": 0, "state": "B starts"}
                ],
                "consequent_anchor": {
                    "storyline_id": "SL-A",
                    "state_index": 0,
                    "state": "A starts",
                },
            }
        )
        model["story_obligation_register"][0]["consequent_anchor"] = {
            "storyline_id": "SL-B",
            "state_index": 0,
            "state": "B starts",
        }
        model["story_obligation_coverage"][0]["obligation_ids"] = [
            "SOB-001",
            "SOB-002",
        ]
        model["story_claim_atoms"][0]["obligation_ids"] = ["SOB-001", "SOB-002"]
        model["story_obligation_register"].append(second)
        with self.assertRaisesRegex(s1.S1Error, "S1_STORY_OBLIGATION_CYCLE"):
            s1._validate_story_obligations(model, self.controls, self.lines)

    def test_rejects_incomplete_information_window(self) -> None:
        model = copy.deepcopy(self.model)
        model["story_claim_atoms"][0]["atom_kind"] = "information_window"
        for item in model["story_obligation_register"]:
            item.update(
                {
                    "kind": "first_disclosure",
                    "proposition_id": "PROP-SECRET",
                    "audience": "reader",
                }
            )
        second = copy.deepcopy(model["story_obligation_register"][0])
        second["id"] = "SOB-002"
        second["consequent_anchor"] = {
            "storyline_id": "SL-A",
            "state_index": 2,
            "state": "A ends",
        }
        model["story_obligation_register"].append(second)
        model["story_obligation_coverage"][0]["obligation_ids"] = [
            "SOB-001",
            "SOB-002",
        ]
        model["story_claim_atoms"][0]["obligation_ids"] = ["SOB-001", "SOB-002"]
        with self.assertRaisesRegex(s1.S1Error, "S1_INFORMATION_WINDOW_INCOMPLETE"):
            s1._validate_story_obligations(model, self.controls, self.lines)

    def _model_for_locked_value(
        self, value: str, *, relational: bool, branching: bool = False
    ) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
        controls = copy.deepcopy(self.controls)
        controls["INT-001"]["value"] = value
        units = s1._expected_claim_units(list(controls.values()))
        locked_units = [item for item in units if item["control_id"] == "INT-001"]
        open_unit = next(item for item in units if item["control_id"] == "NAR-001")
        atoms = []
        obligations = []
        for index, unit in enumerate(locked_units, 1):
            atom_id = f"SCA-LINK-{index:03d}"
            obligation_id = f"SOB-LINK-{index:03d}"
            atoms.append(
                {
                    "id": atom_id,
                    "source_unit_id": unit["id"],
                    "control_id": "INT-001",
                    "source_locator": copy.deepcopy(self.locator),
                    "claim": f"Exact disposition for {unit['text']}",
                    "atom_kind": "causal_relation" if relational else "non_relational",
                    "obligation_ids": [obligation_id] if relational else [],
                    "rationale": "The deterministic unit is disposed independently.",
                    "review_required": (
                        not relational and unit["relation_mode"] == "candidate"
                    ),
                }
            )
            if relational:
                source_index = 0 if branching else min(index - 1, 1)
                target_index = min(index, 2)
                states = ["A starts", "A changes", "A ends"]
                obligations.append(
                    {
                        "id": obligation_id,
                        "kind": "causes",
                        "source_claim_atom_ids": [atom_id],
                        "source_control_ids": ["INT-001"],
                        "source_locators": [copy.deepcopy(self.locator)],
                        "antecedent_anchors": [{"storyline_id": "SL-A", "state_index": source_index, "state": states[source_index]}],
                        "consequent_anchor": {"storyline_id": "SL-A", "state_index": target_index, "state": states[target_index]},
                        "proposition_id": None,
                        "audience": None,
                        "rationale": "One source relation maps to one adjacent story obligation.",
                        "acceptance_check": "The adjacent consequent requires its declared antecedent.",
                    }
                )
        atoms.append(
            {
                "id": "SCA-OPEN",
                "source_unit_id": open_unit["id"],
                "control_id": "NAR-001",
                "source_locator": copy.deepcopy(self.open_locator),
                "claim": "The author-open source unit remains open.",
                "atom_kind": "author_open",
                "obligation_ids": [],
                "rationale": "Author authority remains unchanged.",
                "review_required": False,
            }
        )
        locked_atom_ids = [item["id"] for item in atoms if item["control_id"] == "INT-001"]
        model = {
            "connections": [],
            "story_claim_units": units,
            "story_claim_atoms": atoms,
            "story_obligation_register": obligations,
            "story_obligation_coverage": [
                {
                    "id": "SOC-001",
                    "control_id": "INT-001",
                    "source_locator": copy.deepcopy(self.locator),
                    "disposition": "obligated" if relational else "no_relational_obligation",
                    "claim_atom_ids": locked_atom_ids,
                    "obligation_ids": [item["id"] for item in obligations],
                    "rationale": "All deterministic units are indexed without aggregation.",
                    "review_required": not relational,
                },
                {
                    "id": "SOC-002",
                    "control_id": "NAR-001",
                    "source_locator": copy.deepcopy(self.open_locator),
                    "disposition": "author_open",
                    "claim_atom_ids": ["SCA-OPEN"],
                    "obligation_ids": [],
                    "rationale": "The author-open control remains open.",
                    "review_required": False,
                },
            ],
        }
        return model, controls

    def test_arrow_chain_requires_each_adjacent_relation(self) -> None:
        model, controls = self._model_for_locked_value("A → B → C", relational=True)
        locked_units = [item for item in model["story_claim_units"] if item["control_id"] == "INT-001"]
        self.assertEqual(["A → B", "B → C"], [item["text"] for item in locked_units])
        self.assertEqual(2, len(model["story_obligation_register"]))
        s1._validate_story_obligations(model, controls, self.lines)

    def test_multibranch_causes_keep_independent_obligations(self) -> None:
        model, controls = self._model_for_locked_value(
            "A → B\nA → C", relational=True, branching=True
        )
        self.assertEqual(2, len(model["story_obligation_register"]))
        s1._validate_story_obligations(model, controls, self.lines)

    def test_fake_endpoint_coverage_cannot_replace_adjacent_links(self) -> None:
        model, controls = self._model_for_locked_value("A → B → C", relational=True)
        first, second = model["story_claim_atoms"][:2]
        second["obligation_ids"] = list(first["obligation_ids"])
        model["story_obligation_register"] = [model["story_obligation_register"][0]]
        model["story_obligation_register"][0]["source_claim_atom_ids"] = [
            first["id"], second["id"]
        ]
        model["story_obligation_coverage"][0]["obligation_ids"] = list(first["obligation_ids"])
        with self.assertRaisesRegex(s1.S1Error, "S1_REQUIRED_RELATION_NOT_ATOMIC"):
            s1._validate_story_obligations(model, controls, self.lines)

    def test_information_window_requires_disclosure_and_unknown_pair(self) -> None:
        model = copy.deepcopy(self.model)
        atom = model["story_claim_atoms"][0]
        atom["atom_kind"] = "information_window"
        atom["obligation_ids"] = ["SOB-DISCLOSE", "SOB-UNKNOWN"]
        disclosure = copy.deepcopy(model["story_obligation_register"][0])
        disclosure.update({"id": "SOB-DISCLOSE", "kind": "first_disclosure", "proposition_id": "PROP-SECRET", "audience": "reader"})
        unknown = copy.deepcopy(disclosure)
        unknown.update({"id": "SOB-UNKNOWN", "kind": "must_remain_unknown", "antecedent_anchors": []})
        model["story_obligation_register"] = [disclosure, unknown]
        model["story_obligation_coverage"][0]["obligation_ids"] = ["SOB-DISCLOSE", "SOB-UNKNOWN"]
        s1._validate_story_obligations(model, self.controls, self.lines)

    def test_numbered_classification_list_is_reviewed_not_forced_temporal(self) -> None:
        model, controls = self._model_for_locked_value(
            "1. Red category\n2. Blue category", relational=False
        )
        ordered = [item for item in model["story_claim_units"] if item["kind"] == "ordered_link"]
        self.assertEqual(1, len(ordered))
        atom = next(item for item in model["story_claim_atoms"] if item["source_unit_id"] == ordered[0]["id"])
        self.assertEqual("non_relational", atom["atom_kind"])
        self.assertTrue(atom["review_required"])
        s1._validate_story_obligations(model, controls, self.lines)

    def test_numbered_norms_use_consistency_atoms_and_reviewed_candidate(self) -> None:
        model, controls = self._model_for_locked_value(
            "1. Keep clocks aligned.\n2. Keep identity stable.", relational=False
        )
        units = {item["id"]: item for item in model["story_claim_units"]}
        candidate_atom = None
        for atom in model["story_claim_atoms"]:
            atom["consistency_dimensions"] = []
            unit = units[atom["source_unit_id"]]
            if unit["kind"] == "numbered_step":
                atom.update(
                    {
                        "atom_kind": "consistency_constraint",
                        "consistency_dimensions": ["time", "state"],
                        "review_required": True,
                    }
                )
            elif unit["kind"] == "ordered_link":
                atom["review_required"] = False
                candidate_atom = atom
        candidate_unit = units[candidate_atom["source_unit_id"]]
        model["source_sequence_realizations"] = [
            {
                "id": "SSR-NUMBERED-NO-RELATION",
                "source_unit_id": candidate_unit["id"],
                "from_anchor": None,
                "to_anchor": None,
                "boundary_from_anchor": None,
                "boundary_to_anchor": None,
                "realization_scope": "non_relational_candidate",
                "reserved_connection_id": None,
                "phase3_fulfillment_kind": None,
                "expected_witness_type": None,
                "consistency_dimension": None,
                "rationale": "The numbered adjacency carries no relation to promote.",
            }
        ]
        s1._validate_story_obligations(
            model,
            controls,
            self.lines,
            require_current_contract=True,
        )
        numbered_atoms = [
            atom
            for atom in model["story_claim_atoms"]
            if units[atom["source_unit_id"]]["kind"] == "numbered_step"
        ]
        self.assertTrue(numbered_atoms)
        self.assertTrue(
            all(atom["atom_kind"] == "consistency_constraint" for atom in numbered_atoms)
        )
        self.assertEqual("non_relational", candidate_atom["atom_kind"])
        self.assertFalse(candidate_atom["review_required"])

    def test_same_line_forward_cause_is_reachable(self) -> None:
        s1._validate_story_obligations(self.model, self.controls, self.lines)

    def test_cross_line_cause_without_causal_connection_is_rejected(self) -> None:
        model = copy.deepcopy(self.model)
        model["story_obligation_register"][0]["consequent_anchor"] = {
            "storyline_id": "SL-B",
            "state_index": 1,
            "state": "B changes",
        }
        model["connections"] = [
            {
                "relation": "associative",
                "from_storyline_id": "SL-A",
                "from_state_index": 0,
                "to_storyline_id": "SL-B",
                "to_state_index": 0,
            }
        ]
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CAUSAL_OBLIGATION_UNREACHABLE"
        ):
            s1._validate_story_obligations(model, self.controls, self.lines)

    def test_earlier_reverse_connection_cannot_satisfy_later_cause(self) -> None:
        model = copy.deepcopy(self.model)
        obligation = model["story_obligation_register"][0]
        obligation["antecedent_anchors"] = [
            {"storyline_id": "SL-A", "state_index": 1, "state": "A changes"}
        ]
        obligation["consequent_anchor"] = {
            "storyline_id": "SL-B",
            "state_index": 1,
            "state": "B changes",
        }
        model["connections"] = [
            {
                "relation": "causal",
                "from_storyline_id": "SL-B",
                "from_state_index": 0,
                "to_storyline_id": "SL-A",
                "to_state_index": 1,
            }
        ]
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CAUSAL_OBLIGATION_UNREACHABLE"
        ):
            s1._validate_story_obligations(model, self.controls, self.lines)

    def test_multihop_causal_connections_satisfy_cross_line_cause(self) -> None:
        lines = copy.deepcopy(self.lines)
        lines["SL-C"] = {
            "start_state": "C starts",
            "state_changes": ["C changes"],
            "end_state": "C ends",
        }
        model = copy.deepcopy(self.model)
        obligation = model["story_obligation_register"][0]
        obligation["antecedent_anchors"] = [
            {"storyline_id": "SL-A", "state_index": 1, "state": "A changes"}
        ]
        obligation["consequent_anchor"] = {
            "storyline_id": "SL-C",
            "state_index": 1,
            "state": "C changes",
        }
        model["connections"] = [
            {"relation": "causal", "from_storyline_id": "SL-A", "from_state_index": 1, "to_storyline_id": "SL-B", "to_state_index": 0},
            {"relation": "causal", "from_storyline_id": "SL-B", "from_state_index": 1, "to_storyline_id": "SL-C", "to_state_index": 0},
        ]
        s1._validate_story_obligations(model, self.controls, lines)

    def test_requires_all_checks_every_antecedent_reachability(self) -> None:
        lines = copy.deepcopy(self.lines)
        lines["SL-C"] = {
            "start_state": "C starts",
            "state_changes": ["C changes"],
            "end_state": "C ends",
        }
        model = copy.deepcopy(self.model)
        model["story_claim_atoms"][0]["atom_kind"] = "all_prerequisites"
        obligation = model["story_obligation_register"][0]
        obligation["kind"] = "requires_all"
        obligation["antecedent_anchors"] = [
            {"storyline_id": "SL-A", "state_index": 0, "state": "A starts"},
            {"storyline_id": "SL-B", "state_index": 0, "state": "B starts"},
        ]
        obligation["consequent_anchor"] = {
            "storyline_id": "SL-C",
            "state_index": 1,
            "state": "C changes",
        }
        model["connections"] = [
            {"relation": "causal", "from_storyline_id": "SL-A", "from_state_index": 0, "to_storyline_id": "SL-C", "to_state_index": 0},
            {"relation": "causal", "from_storyline_id": "SL-B", "from_state_index": 0, "to_storyline_id": "SL-C", "to_state_index": 0},
        ]
        s1._validate_story_obligations(model, self.controls, lines)
        model["connections"].pop()
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CAUSAL_OBLIGATION_UNREACHABLE"
        ):
            s1._validate_story_obligations(model, self.controls, lines)

    def test_relation_realization_collision_needs_unordered_audited_group(self) -> None:
        model, controls = self._model_for_locked_value(
            {"left": "first claim", "right": "second claim"}, relational=True
        )
        first, second = model["story_obligation_register"][:2]
        second["antecedent_anchors"] = copy.deepcopy(first["antecedent_anchors"])
        second["consequent_anchor"] = copy.deepcopy(first["consequent_anchor"])
        with self.assertRaisesRegex(
            s1.S1Error, "S1_RELATION_REALIZATION_COLLISION"
        ):
            s1._validate_story_obligations(model, controls, self.lines)
        for atom in model["story_claim_atoms"][:2]:
            atom["co_realization_group"] = "CO-SHARED"
            atom["co_realization_justification"] = (
                "The source leaves these independent leaves semantically unordered."
            )
            atom["co_realization_witness_ids"] = [first["id"]]
        s1._validate_story_obligations(model, controls, self.lines)

    def test_ordered_source_rejects_co_realization_even_with_justification(self) -> None:
        model, controls = self._model_for_locked_value("A -> B -> C", relational=True)
        atom = model["story_claim_atoms"][0]
        atom["co_realization_group"] = "CO-ORDERED"
        atom["co_realization_justification"] = "Attempted collapse of ordered source."
        atom["co_realization_witness_ids"] = ["SOB-LINK-001"]
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CO_REALIZATION_ORDERED_SOURCE_INVALID"
        ):
            s1._validate_story_obligations(model, controls, self.lines)


def passing_topology_verdicts(
    request: dict[str, object],
) -> list[dict[str, object]]:
    universe = request["coverage_universe"]
    verdicts = []
    for dimension in s1.TOPOLOGY_SEMANTIC_REVIEW_DIMENSIONS:
        source_ids = list(request["source_unit_ids"])
        pointers = []
        source_order = []
        milestone_order = []
        witness_ids = []
        visibility = "not_applicable"
        visibility_exemptions = []
        if dimension == "time":
            pointers = universe["milestone_pointers"]
            milestone_order = universe["milestone_ids"]
            witness_ids = universe["milestone_ids"]
        elif dimension == "causality":
            pointers = universe["connection_endpoint_pointers"]
            milestone_order = universe["milestone_ids"]
            witness_ids = universe["connection_ids"]
        elif dimension == "information":
            source_ids = universe["information_source_unit_ids"]
            pointers = universe["information_atom_pointers"]
            witness_ids = universe["information_atom_ids"] or universe["milestone_ids"]
            if universe["visibility_control_ids"]:
                visibility = "preserved"
            exemption_witness_id = witness_ids[0] if witness_ids else None
            visibility_exemptions = [
                {
                    "control_id": control_id,
                    "justification": (
                        "This control constrains presentation but declares no "
                        "disclosure window."
                    ),
                    "witness_ids": [exemption_witness_id],
                }
                for control_id in universe["visibility_exemption_control_ids"]
            ]
        elif dimension == "state":
            pointers = universe["milestone_state_pointers"]
            milestone_order = universe["milestone_ids"]
            witness_ids = universe["milestone_ids"]
        elif dimension == "source-sequence":
            source_ids = universe["ordered_source_unit_ids"]
            pointers = (
                universe["milestone_pointers"]
                if universe["ordered_source_unit_ids"]
                else []
            )
            source_order = universe["ordered_source_unit_ids"]
            milestone_order = (
                universe["milestone_ids"]
                if universe["ordered_source_unit_ids"]
                else []
            )
            witness_ids = universe["ordered_source_unit_ids"]
        else:
            pointers = universe["milestone_pointers"]
            source_order = universe["ordered_source_unit_ids"]
            milestone_order = universe["milestone_ids"]
            witness_ids = [
                *universe["milestone_ids"],
                *universe["ordered_source_unit_ids"],
            ]
        verdicts.append(
            {
                "dimension": dimension,
                "verdict": "pass",
                "source_unit_ids": list(source_ids),
                "candidate_pointers": list(pointers),
                "witness_ids": list(witness_ids),
                "source_order": list(source_order),
                "milestone_order": list(milestone_order),
                "visibility_result": visibility,
                "visibility_exemptions": visibility_exemptions,
                "rationale": "Exact structural coverage confirms this dimension.",
            }
        )
    return verdicts


class GlobalTemporalAndTopologyReviewTests(unittest.TestCase):
    def _anchor(self, line: str, index: int) -> dict[str, object]:
        return {"storyline_id": line, "state_index": index, "state": f"{line}-{index}"}

    def _milestones(self, *, reverse: bool = False) -> dict[str, dict[str, object]]:
        refs = [self._anchor("SL-A", 0), self._anchor("SL-B", 0)]
        if reverse:
            refs.reverse()
        return {
            "MS-1": {"id": "MS-1", "order": 1, "state_refs": refs},
            "MS-2": {
                "id": "MS-2", "order": 2,
                "state_refs": [self._anchor("SL-A", 1), self._anchor("SL-B", 1)],
            },
        }

    def test_global_first_occurrence_rejects_reversed_cause(self) -> None:
        connection = {
            "relation": "causal", "from_storyline_id": "SL-A",
            "from_state_index": 0, "to_storyline_id": "SL-B", "to_state_index": 0,
        }
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CAUSAL_FIRST_OCCURRENCE_REVERSED"
        ):
            s1._validate_global_temporal_semantics(
                {"story_obligation_register": []},
                connections={"SLC-1": connection},
                milestones=self._milestones(reverse=True),
                line_state_visits={},
            )

    def test_same_milestone_order_controls_strict_and_information_windows(self) -> None:
        obligations = [
            {
                "id": "SOB-STRICT", "kind": "strict_before",
                "antecedent_anchors": [self._anchor("SL-A", 0)],
                "consequent_anchor": self._anchor("SL-B", 0),
                "proposition_id": None, "audience": None,
            },
            {
                "id": "SOB-DISCLOSE", "kind": "first_disclosure",
                "antecedent_anchors": [],
                "consequent_anchor": self._anchor("SL-A", 0),
                "proposition_id": "PROP-X", "audience": "reader",
            },
            {
                "id": "SOB-UNKNOWN", "kind": "must_remain_unknown",
                "antecedent_anchors": [],
                "consequent_anchor": self._anchor("SL-B", 0),
                "proposition_id": "PROP-X", "audience": "reader",
            },
        ]
        with self.assertRaisesRegex(
            s1.S1Error, "S1_GLOBAL_INFORMATION_WINDOW_INVALID"
        ):
            s1._validate_global_temporal_semantics(
                {"story_obligation_register": obligations}, connections={},
                milestones=self._milestones(), line_state_visits={},
            )
        obligations[1]["consequent_anchor"], obligations[2]["consequent_anchor"] = (
            obligations[2]["consequent_anchor"], obligations[1]["consequent_anchor"]
        )
        s1._validate_global_temporal_semantics(
            {"story_obligation_register": obligations}, connections={},
            milestones=self._milestones(), line_state_visits={},
        )

    def _review_fixture(self) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
        body = {
            "story_claim_units": [
                {"id": "SCU-1", "kind": "ordered_link", "relation_mode": "candidate"},
                {"id": "SCU-2", "kind": "structured_leaf", "relation_mode": "none"},
            ],
            "story_claim_atoms": [
                {"id": "SCA-INFO", "source_unit_id": "SCU-2", "control_id": "I5-001", "atom_kind": "information_window"}
            ],
            "temporal_architecture": {"milestones": list(self._milestones().values())},
            "connections": [
                {"id": "SLC-1", "relation": "associative", "from_state_index": 0, "to_state_index": 0}
            ],
        }
        session = {
            "run_id": "RUN-REVIEW", "session_id": "S1-SESSION",
            "thread_id": "thread-generation",
        }
        controls = [
            {"id": "I5-001", "domain": "I5", "hardness": "author_locked", "heading": "Visibility", "value": "Bounded disclosure"}
        ]
        return session, body, controls

    def _passing_verdicts(self, request: dict[str, object]) -> list[dict[str, object]]:
        return passing_topology_verdicts(request)

    def test_topology_review_exact_cover_and_distinct_thread(self) -> None:
        session, body, controls = self._review_fixture()
        request = s1._expected_topology_review_request(session, {}, body, controls)
        verdicts = self._passing_verdicts(request)
        self.assertTrue(s1._topology_verdicts_valid(request, verdicts))
        broken = copy.deepcopy(verdicts)
        broken[1]["candidate_pointers"].pop()
        self.assertFalse(s1._topology_verdicts_valid(request, broken))
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            s1._write(workspace / "generation-session.json", session)
            request_path, review_path = s1._topology_review_paths(
                workspace, request["candidate_sha256"]
            )
            s1._write(request_path, request)
            with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": session["thread_id"]}):
                with self.assertRaisesRegex(
                    s1.S1Error, "S1_TOPOLOGY_REVIEW_NOT_INDEPENDENT"
                ):
                    s1.submit_s1_topology_semantic_review(
                        workspace, candidate_sha256=request["candidate_sha256"],
                        verdicts=verdicts,
                    )
            with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": "thread-reviewer"}):
                s1.submit_s1_topology_semantic_review(
                    workspace, candidate_sha256=request["candidate_sha256"],
                    verdicts=verdicts,
                )
            self.assertTrue(review_path.is_file())

    def test_visibility_control_without_window_requires_audited_exemption(self) -> None:
        session, body, controls = self._review_fixture()
        body["story_claim_atoms"] = []
        request = s1._expected_topology_review_request(session, {}, body, controls)
        verdicts = self._passing_verdicts(request)
        information = verdicts[2]
        information["visibility_exemptions"] = []
        self.assertFalse(s1._topology_verdicts_valid(request, verdicts))
        information["visibility_result"] = "preserved"
        information["visibility_exemptions"] = [
            {
                "control_id": "I5-001",
                "justification": "This control constrains presentation but declares no disclosure window.",
                "witness_ids": ["MS-1"],
            }
        ]
        self.assertTrue(s1._topology_verdicts_valid(request, verdicts))

    def test_current_topology_review_exposes_source_semantic_dispositions(self) -> None:
        session, body, controls = self._review_fixture()
        session["contract_revision"] = s1.CURRENT_CONTRACT_REVISION
        body["story_claim_atoms"].append(
            {
                "id": "SCA-CONSISTENCY",
                "source_unit_id": "SCU-1",
                "control_id": "I5-001",
                "atom_kind": "consistency_constraint",
                "consistency_dimensions": ["time", "state"],
            }
        )
        line_payload = {
            "source_sequence_realizations": [
                {
                    "source_unit_id": "SCU-1",
                    "realization_scope": "non_relational_candidate",
                }
            ]
        }
        request = s1._expected_topology_review_request(
            session, line_payload, body, controls
        )
        universe = request["coverage_universe"]
        self.assertEqual(
            ["SCA-CONSISTENCY"], universe["consistency_constraint_atom_ids"]
        )
        self.assertEqual(
            ["SCU-1"],
            universe["reviewed_non_relational_candidate_source_unit_ids"],
        )
        self.assertIn("consistency_source_rule", request["review_contract"])
        self.assertIn(
            "non_relational_candidate_rule", request["review_contract"]
        )

    def test_generic_014_017_018_ordered_units_require_exact_coverage(self) -> None:
        session, body, controls = self._review_fixture()
        body["story_claim_units"] = [
            {
                "id": f"SCU-GENERIC-{suffix}",
                "kind": "ordered_link",
                "relation_mode": "required",
            }
            for suffix in ("014", "017", "018")
        ] + [
            {"id": "SCU-INFO", "kind": "structured_leaf", "relation_mode": "none"}
        ]
        body["story_claim_atoms"][0]["source_unit_id"] = "SCU-INFO"
        request = s1._expected_topology_review_request(session, {}, body, controls)
        verdicts = self._passing_verdicts(request)
        expected = [
            "SCU-GENERIC-014", "SCU-GENERIC-017", "SCU-GENERIC-018"
        ]
        self.assertEqual(
            expected, request["coverage_universe"]["ordered_source_unit_ids"]
        )
        self.assertTrue(s1._topology_verdicts_valid(request, verdicts))
        verdicts[4]["source_order"].remove("SCU-GENERIC-017")
        self.assertFalse(s1._topology_verdicts_valid(request, verdicts))


class StateCausalGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.lines = {
            "SL-A": {
                "type": "main",
                "start_state": "A0",
                "state_changes": ["A1"],
                "end_state": "A2",
            },
            "SL-B": {
                "type": "supporting",
                "start_state": "B0",
                "state_changes": ["B1"],
                "end_state": "B2",
            },
        }

    def test_accepts_legal_cross_line_return_to_later_state(self) -> None:
        graph = s1._build_state_causal_graph(
            self.lines,
            [
                {"relation": "causal", "from_storyline_id": "SL-A", "from_state_index": 0, "to_storyline_id": "SL-B", "to_state_index": 0},
                {"relation": "causal", "from_storyline_id": "SL-B", "from_state_index": 1, "to_storyline_id": "SL-A", "to_state_index": 2},
            ],
        )
        s1._validate_state_causal_dag(graph)
        s1._validate_structural_state_closure(self.lines, graph)
        self.assertTrue(s1._state_reachable(graph, ("SL-A", 0), ("SL-A", 2)))

    def test_rejects_direct_state_cycle(self) -> None:
        graph = s1._build_state_causal_graph(
            self.lines,
            [
                {"relation": "causal", "from_storyline_id": "SL-A", "from_state_index": 0, "to_storyline_id": "SL-B", "to_state_index": 0},
                {"relation": "causal", "from_storyline_id": "SL-B", "from_state_index": 0, "to_storyline_id": "SL-A", "to_state_index": 0},
            ],
        )
        with self.assertRaisesRegex(s1.S1Error, "S1_STATE_CAUSAL_CYCLE"):
            s1._validate_state_causal_dag(graph)

    def test_rejects_multihop_state_cycle(self) -> None:
        graph = s1._build_state_causal_graph(
            self.lines,
            [
                {"relation": "causal", "from_storyline_id": "SL-A", "from_state_index": 1, "to_storyline_id": "SL-B", "to_state_index": 0},
                {"relation": "causal", "from_storyline_id": "SL-B", "from_state_index": 1, "to_storyline_id": "SL-A", "to_state_index": 0},
            ],
        )
        with self.assertRaisesRegex(s1.S1Error, "S1_STATE_CAUSAL_CYCLE"):
            s1._validate_state_causal_dag(graph)

    def test_rejects_structural_line_without_state_path_to_main(self) -> None:
        graph = s1._build_state_causal_graph(self.lines, [])
        with self.assertRaisesRegex(
            s1.S1Error, "S1_STRUCTURAL_CAUSAL_CLOSURE_MISSING"
        ):
            s1._validate_structural_state_closure(self.lines, graph)

    def test_phase3_still_rejects_wrongly_directed_structural_edge(self) -> None:
        graph = s1._build_state_causal_graph(
            self.lines,
            [
                {
                    "relation": "causal",
                    "from_storyline_id": "SL-A",
                    "from_state_index": 1,
                    "to_storyline_id": "SL-B",
                    "to_state_index": 1,
                }
            ],
        )
        s1._validate_state_causal_dag(graph)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_STRUCTURAL_CAUSAL_CLOSURE_MISSING"
        ):
            s1._validate_structural_state_closure(self.lines, graph)


class Phase3SharedValidatorAuditTests(unittest.TestCase):
    def test_upstream_inventory_is_complete_and_on_the_shared_prefix(self) -> None:
        inventory = s1.UPSTREAM_ONLY_SEMANTIC_ERROR_CODES
        self.assertEqual(46, len(inventory))
        self.assertEqual(len(inventory), len(set(inventory)))

        shared = inspect.getsource(s1._validate_model)
        helpers = "\n".join(
            inspect.getsource(helper)
            for helper in (
                s1._validate_global_temporal_semantics,
                s1._validate_milestone_line_state_progression,
                s1._validate_consistency_witness_subset,
            )
        )
        for code in inventory:
            with self.subTest(code=code):
                self.assertIn(code, shared + helpers)

        boundary = shared.index("if upstream_only:\n        return")
        for call in (
            "_validate_line_phase_semantics(",
            "_validate_story_obligations(",
            "_validate_global_temporal_semantics(",
            "_validate_consistency_witness_subset(",
        ):
            with self.subTest(shared_call=call):
                self.assertLess(shared.index(call), boundary)

    def test_both_phase3_gates_and_full_model_use_one_semantic_owner(self) -> None:
        phase3 = inspect.getsource(s1._validate_topology_phase_semantics)
        self.assertEqual(1, phase3.count("_validate_model("))
        self.assertIn("upstream_only=True", phase3)
        self.assertIn('"upstreamPhasePayload"', phase3)

        review_gate = inspect.getsource(s1.start_s1_topology_semantic_review)
        submit_gate = inspect.getsource(s1._validate_phase_semantics)
        self.assertIn("_validate_topology_phase_semantics(", review_gate)
        self.assertIn("baseline=baseline", review_gate)
        self.assertIn("_validate_topology_phase_semantics(", submit_gate)
        self.assertIn("baseline=baseline", submit_gate)

        signature = inspect.signature(s1._validate_model)
        self.assertFalse(signature.parameters["upstream_only"].default)


class S1RebuiltB0ReferenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.sources = baseline_test.SourceFixture(self.work / "sources")
        self.coordinator = runtime.AutonomousCoordinator.initialize(
            run_id=self.sources.run_id,
            source_interview_state={
                "path": "interview/interview-state.json",
                "sha256": runtime.sha256_file(self.sources.state),
            },
            state_path="state/revision-000.json",
        )
        b0_gate = self.coordinator.build_input_gate(
            "B0", "orchestration/input-gates/revision-000-b0/input-gate.json"
        )
        self.b0 = self.work / "run" / "workspaces" / "B0-attempt-01" / "package"
        runtime.build_baseline_package(**self.sources.build_args(self.b0, b0_gate))
        self.b0_receipt = runtime.complete_b0(
            self.b0,
            coordinator=self.coordinator,
            input_gate=b0_gate,
            logical_package_path="workspaces/B0-attempt-01/package",
            next_state_path="state/revision-001.json",
        )
        self.gate = self.coordinator.build_input_gate(
            "S1", "orchestration/input-gates/revision-001-s1/input-gate.json"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _start(self, workspace: Path, gate: object | None = None) -> dict[str, object]:
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-rebuilt-b0"}, clear=False
        ):
            return s1.start_s1_session(
                workspace,
                baseline_package=self.b0,
                input_gate=self.gate if gate is None else gate,
            )

    def test_start_accepts_current_gate_sealed_rebuilt_b0_path(self) -> None:
        workspace = self.work / "workspace" / "S1-rebuilt"
        session = self._start(workspace)
        self.assertEqual(
            self.b0_receipt.completion.reference,
            session["input_manifest"],
        )
        self.assertEqual(
            "workspaces/B0-attempt-01/package/stage-completion.json",
            session["input_manifest"]["path"],
        )

    def test_run_and_validate_accept_current_gate_sealed_rebuilt_b0_path(
        self,
    ) -> None:
        baseline = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        controls = s1._controls(self.b0, baseline)
        proposal = agent_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=s1._source_artifacts(self.b0),
            controls=controls,
        )
        workspace = self.work / "workspace" / "S1-rebuilt-full"
        package = self.work / "run" / "S1-rebuilt"
        common = {
            "baseline_package": self.b0,
            "input_gate": self.gate,
        }
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-rebuilt-b0-full"}, clear=False
        ):
            s1.start_s1_session(workspace, **common)
            for phase in s1.PHASES:
                payload = (
                    {"model": proposal}
                    if phase == "final-storyline-model"
                    else {
                        field: proposal[field]
                        for field in s1.PHASE_FIELDS[phase]
                    }
                )
                if phase == "line-design":
                    request = s1.start_s1_line_claim_review(
                        workspace, payload=payload, **common
                    )
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-rebuilt-line-review"},
                        clear=False,
                    ):
                        s1.submit_s1_line_claim_review(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            review={
                                "claim_verdicts": [
                                    {
                                        "claim_id": claim_id,
                                        "verdict": "pass",
                                        "rationale": "Exact source and authority binding passes.",
                                    }
                                    for claim_id in request["claim_ids"]
                                ],
                                "source_sequence_verdicts": [
                                    {
                                        "realization_id": item["id"],
                                        "source_unit_id": item["source_unit_id"],
                                        "verdict": "pass",
                                        "rationale": "Ordered source anchors remain exact.",
                                    }
                                    for item in payload["source_sequence_realizations"]
                                ],
                            },
                        )
                if phase == "topology-and-consistency":
                    request = s1.start_s1_topology_semantic_review(
                        workspace, payload=payload, **common
                    )
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-rebuilt-topology-review"},
                        clear=False,
                    ):
                        s1.submit_s1_topology_semantic_review(
                            workspace,
                            candidate_sha256=request["candidate_sha256"],
                            verdicts=passing_topology_verdicts(request),
                        )
                s1.submit_s1_phase(
                    workspace, phase=phase, payload=payload, **common
                )
            s1.run_s1(
                package,
                **common,
                coordinator=self.coordinator,
                controlled_workspace=workspace,
                logical_package_path="S1/rebuilt",
                next_state_path="state/revision-002.json",
            )
        self.assertEqual("ready", s1.validate_s1_package(package)["verdict"])
        self.assertEqual(
            self.b0_receipt.completion.reference,
            json.loads((package / "execution-record.json").read_text(encoding="utf-8"))[
                "input_manifest"
            ],
        )

    def test_start_rejects_foreign_logical_path_before_writes(self) -> None:
        data = copy.deepcopy(self.gate.data)
        data["baseline_completion"]["path"] = (
            "workspaces/foreign/package/stage-completion.json"
        )
        forged = runtime.seal_document(data, self.gate.reference["path"])
        workspace = self.work / "workspace" / "S1-foreign"
        with self.assertRaises(s1.S1Error) as caught:
            self._start(workspace, forged)
        self.assertEqual("S1_B0_INVALID", caught.exception.code)
        self.assertFalse(workspace.exists())

    def test_start_rejects_stale_completion_hash_before_writes(self) -> None:
        data = copy.deepcopy(self.gate.data)
        data["baseline_completion"]["sha256"] = "f" * 64
        stale = runtime.seal_document(data, self.gate.reference["path"])
        workspace = self.work / "workspace" / "S1-stale"
        with self.assertRaises(s1.S1Error) as caught:
            self._start(workspace, stale)
        self.assertEqual("S1_B0_INVALID", caught.exception.code)
        self.assertFalse(workspace.exists())

    def test_start_rejects_tampered_completion_body_before_writes(self) -> None:
        completion_path = self.b0 / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["run_id"] = "foreign-run"
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8", newline=""
        )
        workspace = self.work / "workspace" / "S1-tampered"
        with self.assertRaises(s1.S1Error) as caught:
            self._start(workspace)
        self.assertEqual("S1_B0_INVALID", caught.exception.code)
        self.assertFalse(workspace.exists())


class S1RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.work = Path(self.temporary.name)
        self.sources = baseline_test.SourceFixture(self.work / "sources")
        self.coordinator = runtime.AutonomousCoordinator.initialize(
            run_id=self.sources.run_id,
            source_interview_state={
                "path": "interview/interview-state.json",
                "sha256": runtime.sha256_file(self.sources.state),
            },
            state_path="state/revision-000.json",
        )
        b0_gate = self.coordinator.build_input_gate("B0", "B0/input-gate.json")
        self.b0 = self.work / "run" / "B0"
        runtime.build_baseline_package(
            **self.sources.build_args(self.b0, b0_gate)
        )
        runtime.complete_b0(
            self.b0,
            coordinator=self.coordinator,
            input_gate=b0_gate,
            logical_package_path="B0",
            next_state_path="state/revision-001.json",
        )
        self.gate = self.coordinator.build_input_gate(
            "S1", "S1/input-gate.json"
        )
        self.package = self.work / "run" / "S1"
        self.workspace = self.work / "workspace" / "S1"
        baseline_model = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(encoding="utf-8")
        )
        controls = s1._controls(self.b0, baseline_model)
        source_artifacts = [
            {
                "path": f"sources/B0/{name}",
                "sha256": runtime.sha256_file(self.b0 / name),
            }
            for name in (
                "author-control-baseline.json",
                "package-manifest.json",
                "stage-completion.json",
            )
        ]
        self.proposal = agent_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=source_artifacts,
            controls=controls,
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-s1"}, clear=False
        ):
            s1.start_s1_session(
                self.workspace,
                baseline_package=self.b0,
                input_gate=self.gate,
            )
            for phase in s1.PHASES:
                payload = (
                    {"model": self.proposal}
                    if phase == "final-storyline-model"
                    else {
                        field: self.proposal[field]
                        for field in s1.PHASE_FIELDS[phase]
                    }
                )
                if phase == "line-design":
                    request = s1.start_s1_line_claim_review(
                        self.workspace,
                        baseline_package=self.b0,
                        input_gate=self.gate,
                        payload=payload,
                    )
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-independent-line-review"},
                        clear=False,
                    ):
                        s1.submit_s1_line_claim_review(
                            self.workspace,
                            candidate_sha256=request["candidate_sha256"],
                            review={
                                "claim_verdicts": [
                                    {
                                        "claim_id": claim_id,
                                        "verdict": "pass",
                                        "rationale": (
                                            "The claim stays within its declared "
                                            "source or S1 structural authority."
                                        ),
                                    }
                                    for claim_id in request["claim_ids"]
                                ],
                                "source_sequence_verdicts": [
                                    {
                                        "realization_id": item["id"],
                                        "source_unit_id": item["source_unit_id"],
                                        "verdict": "pass",
                                        "rationale": (
                                            "The exact anchors preserve this ordered "
                                            "source transition without collapsing its endpoint."
                                        ),
                                    }
                                    for item in payload["source_sequence_realizations"]
                                ],
                            },
                        )
                if phase == "topology-and-consistency":
                    request = s1.start_s1_topology_semantic_review(
                        self.workspace,
                        baseline_package=self.b0,
                        input_gate=self.gate,
                        payload=payload,
                    )
                    with mock.patch.dict(
                        os.environ,
                        {"CODEX_THREAD_ID": "thread-independent-topology-review"},
                        clear=False,
                    ):
                        s1.submit_s1_topology_semantic_review(
                            self.workspace,
                            candidate_sha256=request["candidate_sha256"],
                            verdicts=passing_topology_verdicts(request),
                        )
                s1.submit_s1_phase(
                    self.workspace,
                    baseline_package=self.b0,
                    input_gate=self.gate,
                    phase=phase,
                    payload=payload,
                )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_s1(self) -> s1.S1RunReceipt:
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-s1"}, clear=False
        ):
            return s1.run_s1(
                self.package,
                baseline_package=self.b0,
                coordinator=self.coordinator,
                input_gate=self.gate,
                controlled_workspace=self.workspace,
                logical_package_path="S1",
                next_state_path="state/revision-002.json",
            )

    def _validate(self, model: dict[str, object]) -> None:
        baseline = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(encoding="utf-8")
        )
        s1._validate_model(
            model,
            baseline,
            s1._controls(self.b0, baseline),
            runtime.ContractRuntime(),
            expected_gate=self.gate.reference,
            expected_sources=self.proposal["source_artifacts"],
            require_current_contract=True,
        )

    def _refresh_derivations(self, model: dict[str, object]) -> None:
        lines = {item["id"]: item for item in model["storylines"]}
        for claim in model["derivation_claims"]:
            if (
                len(claim["projection_ids"]) == 1
                and claim["projection_ids"][0] in lines
            ):
                claim["value_sha256"] = runtime.canonical_sha256(
                    lines[claim["projection_ids"][0]]
                )
            elif claim["id"] == "DRV-ARCHITECTURE":
                claim["value_sha256"] = runtime.canonical_sha256(
                    model["architecture"]
                )
            elif claim["id"] == "DRV-TEMPORAL-ARCHITECTURE":
                claim["value_sha256"] = runtime.canonical_sha256(
                    model["temporal_architecture"]
                )
            elif claim["id"] == "DRV-STORY-OBLIGATIONS":
                claim["value_sha256"] = runtime.canonical_sha256(
                    {
                        "story_claim_units": model["story_claim_units"],
                        "story_claim_atoms": model["story_claim_atoms"],
                        "story_obligation_register": model[
                            "story_obligation_register"
                        ],
                        "story_obligation_coverage": model[
                            "story_obligation_coverage"
                        ],
                    }
                )

    def _topology_phase_payload(self) -> dict[str, object]:
        return {
            field: copy.deepcopy(self.proposal[field])
            for field in s1.PHASE_FIELDS["topology-and-consistency"]
        }

    def _validate_phase3_model(self, model: dict[str, object]) -> None:
        baseline = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        controls = s1._controls(self.b0, baseline)
        payloads = {
            phase: {
                field: copy.deepcopy(model[field])
                for field in s1.PHASE_FIELDS[phase]
            }
            for phase in (
                "demand-scan",
                "line-design",
                "topology-and-consistency",
            )
        }
        s1._validate_topology_phase_semantics(
            payloads["demand-scan"],
            payloads["line-design"],
            payloads["topology-and-consistency"],
            controls,
            baseline=baseline,
            runtime=runtime.ContractRuntime(),
            require_current_contract=True,
        )

    def _phase3_active_line_mismatch(self) -> dict[str, object]:
        payload = self._topology_phase_payload()
        phase = payload["temporal_architecture"]["phases"][0]
        self.assertGreater(len(phase["active_storyline_ids"]), 1)
        phase["active_storyline_ids"] = phase["active_storyline_ids"][:-1]
        return payload

    def _submit_isolated_topology_phase(
        self,
        workspace: Path,
        payload: dict[str, object],
    ) -> None:
        """Exercise the phase-3 submit gate without requiring phase-4 fields."""

        evidence_root = workspace / "generation-evidence"
        evidence_root.mkdir(parents=True)
        for index, phase in enumerate(("demand-scan", "line-design"), 1):
            (evidence_root / f"{index:02d}-{phase}.json").write_text(
                "{}", encoding="utf-8"
            )
        session = json.loads(
            (self.workspace / "generation-session.json").read_text(
                encoding="utf-8"
            )
        )
        baseline = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        controls = s1._controls(self.b0, baseline)
        prior = {
            phase: {
                field: copy.deepcopy(self.proposal[field])
                for field in s1.PHASE_FIELDS[phase]
            }
            for phase in ("demand-scan", "line-design")
        }
        with mock.patch.object(
            s1,
            "_validated_session",
            return_value=(session, baseline, controls),
        ), mock.patch.object(
            s1,
            "_sealed_phase_payload",
            side_effect=lambda _root, phase, _session: copy.deepcopy(
                prior[phase]
            ),
        ), mock.patch.object(s1, "_validate_topology_semantic_review"):
            s1.submit_s1_phase(
                workspace,
                baseline_package=self.b0,
                input_gate=self.gate,
                phase="topology-and-consistency",
                payload=payload,
            )

    def _start_isolated_topology_review(
        self,
        workspace: Path,
        payload: dict[str, object],
    ) -> dict[str, object]:
        """Exercise the phase-3 review-request gate before phase 4 exists."""

        session = json.loads(
            (self.workspace / "generation-session.json").read_text(
                encoding="utf-8"
            )
        )
        baseline = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        controls = s1._controls(self.b0, baseline)
        prior = {
            phase: {
                field: copy.deepcopy(self.proposal[field])
                for field in s1.PHASE_FIELDS[phase]
            }
            for phase in ("demand-scan", "line-design")
        }
        with mock.patch.object(
            s1,
            "_validated_session",
            return_value=(session, baseline, controls),
        ), mock.patch.object(
            s1,
            "_sealed_phase_payload",
            side_effect=lambda _root, phase, _session: copy.deepcopy(
                prior[phase]
            ),
        ):
            return s1.start_s1_topology_semantic_review(
                workspace,
                baseline_package=self.b0,
                input_gate=self.gate,
                payload=payload,
            )

    def test_topology_phase_schema_accepts_normal_candidate_before_phase4(self) -> None:
        workspace = self.work / "phase3-schema-normal"
        self._submit_isolated_topology_phase(
            workspace,
            self._topology_phase_payload(),
        )
        self.assertTrue(
            (
                workspace
                / "generation-evidence"
                / "03-topology-and-consistency.json"
            ).is_file()
        )

    def test_topology_phase_schema_rejects_forbidden_nested_field_before_sealing(
        self,
    ) -> None:
        workspace = self.work / "phase3-schema-extra-field"
        payload = self._topology_phase_payload()
        payload["architecture"]["progression_logic"] = (
            "This field belongs only to temporal_architecture."
        )
        with self.assertRaises(s1.S1Error) as caught:
            self._submit_isolated_topology_phase(workspace, payload)
        self.assertEqual(
            "S1_TOPOLOGY_PHASE_SEMANTIC_INVALID", caught.exception.code
        )
        self.assertIn("V2_SCHEMA_ADDITIONAL_PROPERTIES", str(caught.exception))
        self.assertFalse(
            (
                workspace
                / "generation-evidence"
                / "03-topology-and-consistency.json"
            ).exists()
        )

    def test_topology_phase_schema_rejects_requires_all_with_one_antecedent(
        self,
    ) -> None:
        workspace = self.work / "phase3-schema-requires-all"
        payload = self._topology_phase_payload()
        obligation = payload["story_obligation_register"][0]
        obligation["kind"] = "requires_all"
        source_atom_ids = set(obligation["source_claim_atom_ids"])
        for atom in payload["story_claim_atoms"]:
            if atom["id"] in source_atom_ids:
                atom["atom_kind"] = "all_prerequisites"
        with self.assertRaises(s1.S1Error) as caught:
            self._submit_isolated_topology_phase(workspace, payload)
        self.assertEqual(
            "S1_TOPOLOGY_PHASE_SEMANTIC_INVALID", caught.exception.code
        )
        self.assertIn("V2_SCHEMA_MIN_ITEMS", str(caught.exception))
        self.assertFalse(
            (
                workspace
                / "generation-evidence"
                / "03-topology-and-consistency.json"
            ).exists()
        )

    def test_topology_review_request_accepts_normal_phase3_without_phase4(
        self,
    ) -> None:
        workspace = self.work / "phase3-review-schema-normal"
        payload = self._topology_phase_payload()
        self.assertEqual(
            set(s1.PHASE_FIELDS["topology-and-consistency"]),
            set(payload),
        )
        request = self._start_isolated_topology_review(workspace, payload)
        self.assertTrue(
            (
                workspace
                / "topology-semantic-reviews"
                / request["candidate_sha256"]
                / "request.json"
            ).is_file()
        )

    def test_topology_review_request_rejects_forbidden_nested_field_without_write(
        self,
    ) -> None:
        workspace = self.work / "phase3-review-schema-extra-field"
        payload = self._topology_phase_payload()
        payload["architecture"]["progression_logic"] = (
            "This field belongs only to temporal_architecture."
        )
        with self.assertRaises(s1.S1Error) as caught:
            self._start_isolated_topology_review(workspace, payload)
        self.assertEqual(
            "S1_TOPOLOGY_PHASE_SEMANTIC_INVALID", caught.exception.code
        )
        self.assertFalse(
            (workspace / "topology-semantic-reviews").exists()
        )

    def test_phase3_temporal_coverage_mismatch_rejects_before_review_request(
        self,
    ) -> None:
        workspace = self.work / "phase3-review-temporal-coverage-mismatch"
        with self.assertRaises(s1.S1Error) as caught:
            self._start_isolated_topology_review(
                workspace,
                self._phase3_active_line_mismatch(),
            )
        self.assertEqual(
            "S1_TOPOLOGY_PHASE_SEMANTIC_INVALID", caught.exception.code
        )
        self.assertIn(
            "S1_TEMPORAL_PHASE_COVERAGE_MISMATCH", str(caught.exception)
        )
        self.assertFalse((workspace / "topology-semantic-reviews").exists())

    def test_phase3_temporal_coverage_mismatch_rejects_before_evidence(
        self,
    ) -> None:
        workspace = self.work / "phase3-submit-temporal-coverage-mismatch"
        with self.assertRaises(s1.S1Error) as caught:
            self._submit_isolated_topology_phase(
                workspace,
                self._phase3_active_line_mismatch(),
            )
        self.assertEqual(
            "S1_TOPOLOGY_PHASE_SEMANTIC_INVALID", caught.exception.code
        )
        self.assertIn(
            "S1_TEMPORAL_PHASE_COVERAGE_MISMATCH", str(caught.exception)
        )
        self.assertFalse(
            (
                workspace
                / "generation-evidence"
                / "03-topology-and-consistency.json"
            ).exists()
        )

    def test_phase3_does_not_require_phase4_claim_realization(self) -> None:
        model = copy.deepcopy(self.proposal)
        claim = next(
            item
            for item in model["line_claim_authority"]
            if item["disposition"] == "s1_structural_derivation"
        )
        claim.update(
            {
                "disposition": "downstream_requirement",
                "source_control_ids": [],
                "decision_ids": [],
                "target_stage": "W1",
                "target_requirement_id": "WR-UPSTREAM-PENDING",
                "open_item_id": None,
            }
        )
        self._validate_phase3_model(model)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_LINE_CLAIM_AUTHORITY_INVALID"
        ):
            self._validate(model)

    def test_shared_phase3_prefix_rejects_representative_family_mutants(
        self,
    ) -> None:
        def demand_control(model: dict[str, object]) -> None:
            model["storyline_demands"][0]["obligation"] = (
                "A detailed but deliberately unbound demand statement."
            )

        def line_design(model: dict[str, object]) -> None:
            model["storylines"][1]["id"] = model["storylines"][0]["id"]

        def connection_binding(model: dict[str, object]) -> None:
            connection = model["connections"][0]
            connection["from_state_index"] = (
                connection["from_state_index"] + 1
            )

        def architecture_order(model: dict[str, object]) -> None:
            model["architecture"]["line_order"].pop()

        def story_obligation(model: dict[str, object]) -> None:
            for obligation in model["story_obligation_register"]:
                consequent = obligation["consequent_anchor"]
                for antecedent in obligation["antecedent_anchors"]:
                    if antecedent["storyline_id"] != consequent["storyline_id"]:
                        continue
                    line = next(
                        item
                        for item in model["storylines"]
                        if item["id"] == consequent["storyline_id"]
                    )
                    final_index = len(line["state_changes"]) + 1
                    if final_index > consequent["state_index"]:
                        antecedent.update(
                            {
                                "state_index": final_index,
                                "state": line["end_state"],
                            }
                        )
                        return
            self.fail("fixture has no reversible same-line obligation")

        def temporal_phase(model: dict[str, object]) -> None:
            phase = model["temporal_architecture"]["phases"][0]
            self.assertGreater(len(phase["active_storyline_ids"]), 1)
            phase["active_storyline_ids"] = phase["active_storyline_ids"][:-1]

        def milestone_binding(model: dict[str, object]) -> None:
            model["temporal_architecture"]["milestones"][0][
                "phase_id"
            ] = "TPH-UNKNOWN"

        def global_temporal(model: dict[str, object]) -> None:
            connection = next(
                item
                for item in model["connections"]
                if item["relation"] == "causal"
            )
            milestone = next(
                item
                for item in model["temporal_architecture"]["milestones"]
                if connection["id"] in item["connection_ids"]
            )
            source = (
                connection["from_storyline_id"],
                connection["from_state_index"],
            )
            target = (
                connection["to_storyline_id"],
                connection["to_state_index"],
            )
            refs = milestone["state_refs"]
            source_ref = next(
                item
                for item in refs
                if (item["storyline_id"], item["state_index"]) == source
            )
            target_ref = next(
                item
                for item in refs
                if (item["storyline_id"], item["state_index"]) == target
            )
            refs.remove(source_ref)
            refs.remove(target_ref)
            refs[:0] = [target_ref, source_ref]

        def narrative_marker(model: dict[str, object]) -> None:
            payoff = next(
                item
                for item in model["temporal_architecture"]["markers"]
                if item["kind"] == "payoff"
            )
            payoff["kind"] = "aftermath"

        def consistency(model: dict[str, object]) -> None:
            model["cross_line_consistency"][0]["witness_ids"].remove(
                model["storylines"][0]["id"]
            )

        cases = (
            ("demand/control", demand_control, "S1_CONTROL_MEANING_UNBOUND"),
            ("line design", line_design, "S1_LINE_PHASE_SEMANTIC_INVALID"),
            ("connection", connection_binding, "S1_CONNECTION_STATE_INVALID"),
            ("architecture", architecture_order, "S1_LINE_ORDER_INVALID"),
            (
                "story obligation",
                story_obligation,
                "S1_STORY_OBLIGATION_LINE_ORDER_INVALID",
            ),
            (
                "temporal phase",
                temporal_phase,
                "S1_TEMPORAL_PHASE_COVERAGE_MISMATCH",
            ),
            ("milestone", milestone_binding, "S1_MILESTONE_PHASE_DANGLING"),
            (
                "global temporal",
                global_temporal,
                "S1_CAUSAL_FIRST_OCCURRENCE_REVERSED",
            ),
            (
                "narrative marker",
                narrative_marker,
                "S1_NARRATIVE_MARKER_KIND_MISSING",
            ),
            (
                "consistency",
                consistency,
                "S1_CONSISTENCY_LINE_COVERAGE_MISSING",
            ),
        )
        for family, mutate, expected in cases:
            with self.subTest(family=family):
                model = copy.deepcopy(self.proposal)
                mutate(model)
                with self.assertRaises(s1.S1Error) as phase3_error:
                    self._validate_phase3_model(model)
                with self.assertRaises(s1.S1Error) as final_error:
                    self._validate(model)
                self.assertIn(expected, str(phase3_error.exception))
                self.assertIn(expected, str(final_error.exception))

    def test_authority_partition_rejects_overlap_before_deep_validation(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["authority_partition"]["downstream_freedom"].append(
            model["authority_partition"]["autonomous_owned"][0]
        )
        with self.assertRaisesRegex(
            s1.S1Error, "S1_AUTHORITY_PARTITION_OVERLAP"
        ):
            self._validate(model)

    def test_authority_partition_requires_all_four_exact_sets(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["authority_partition"]["autonomous_owned"].pop()
        with self.assertRaisesRegex(
            s1.S1Error, "S1_AUTHORITY_PARTITION_MISMATCH"
        ):
            self._validate(model)

    def test_connection_relation_is_required(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["connections"][0].pop("relation")
        with self.assertRaisesRegex(s1.S1Error, "S1_MODEL_SCHEMA_INVALID"):
            self._validate(model)

    def test_connection_state_index_and_text_are_one_binding(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["connections"][0]["from_state_index"] = 0
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONNECTION_STATE_INVALID"
        ):
            self._validate(model)

    def test_duplicate_physical_connection_with_new_id_is_rejected(self) -> None:
        model = copy.deepcopy(self.proposal)
        duplicate = copy.deepcopy(model["connections"][0])
        duplicate["id"] = "SLC-DUPLICATE-PHYSICAL"
        model["connections"].append(duplicate)
        for line in model["storylines"]:
            if line["id"] in {
                duplicate["from_storyline_id"], duplicate["to_storyline_id"]
            }:
                line["connection_ids"].append(duplicate["id"])
        milestone = next(
            item
            for item in model["temporal_architecture"]["milestones"]
            if model["connections"][0]["id"] in item["connection_ids"]
        )
        milestone["connection_ids"].append(duplicate["id"])
        self._refresh_derivations(model)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONNECTION_ENDPOINT_DUPLICATE"
        ):
            self._validate(model)

    def test_causal_connection_cannot_be_registered_after_target_first_occurs(
        self,
    ) -> None:
        model = copy.deepcopy(self.proposal)
        connection = model["connections"][0]
        milestones = model["temporal_architecture"]["milestones"]
        convergence = next(
            item for item in milestones if connection["id"] in item["connection_ids"]
        )
        convergence["connection_ids"].remove(connection["id"])
        for milestone in milestones:
            if milestone["order"] >= 4:
                milestone["order"] += 1
        late = copy.deepcopy(convergence)
        late.update(
            {
                "id": "MS-LATE-CONNECTION",
                "order": 4,
                "title": "Belated connection registration",
                "storyline_ids": [
                    connection["from_storyline_id"],
                    connection["to_storyline_id"],
                ],
                "state_refs": [
                    item
                    for item in convergence["state_refs"]
                    if item["storyline_id"]
                    in {
                        connection["from_storyline_id"],
                        connection["to_storyline_id"],
                    }
                ],
                "connection_ids": [connection["id"]],
            }
        )
        milestones.append(late)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CAUSAL_TARGET_FIRST_OCCURRENCE_MISMATCH"
        ):
            self._validate(model)

    def test_current_consistency_sources_are_exact_semantic_provenance(self) -> None:
        model = copy.deepcopy(self.proposal)
        atom = model["story_claim_atoms"][0]
        obligation_id = atom["obligation_ids"][0]
        atom.update(
            {
                "atom_kind": "consistency_constraint",
                "consistency_dimensions": ["causality"],
                "obligation_ids": [],
                "review_required": True,
            }
        )
        model["story_obligation_register"] = [
            item
            for item in model["story_obligation_register"]
            if item["id"] != obligation_id
        ]
        model["authority_partition"]["autonomous_owned"].remove(obligation_id)
        next(
            item
            for item in model["derivation_claims"]
            if item["id"] == "DRV-STORY-OBLIGATIONS"
        )["projection_ids"].remove(obligation_id)
        coverage = next(
            item
            for item in model["story_obligation_coverage"]
            if atom["id"] in item["claim_atom_ids"]
        )
        coverage.update(
            {
                "disposition": "no_relational_obligation",
                "obligation_ids": [],
                "review_required": True,
            }
        )
        for check in model["cross_line_consistency"]:
            if obligation_id in check["witness_ids"]:
                check["witness_ids"].remove(obligation_id)
            if check["dimension"] == "causality":
                check["source_claim_atom_ids"] = [atom["id"]]
                check["source_control_ids"] = [atom["control_id"]]
                check["claim"] = (
                    f"{atom['claim']} The architecture preserves this constraint."
                )
                check["failure_condition"] = (
                    f"{atom['claim']} would fail if any line contradicted it."
                )
        self._refresh_derivations(model)
        self._validate(model)

        missing = copy.deepcopy(model)
        next(
            item for item in missing["cross_line_consistency"]
            if item["dimension"] == "causality"
        )["source_claim_atom_ids"] = []
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_SOURCE_COVERAGE_MISMATCH"
        ):
            self._validate(missing)

        wrong_dimension = copy.deepcopy(model)
        time_check = next(
            item for item in wrong_dimension["cross_line_consistency"]
            if item["dimension"] == "time"
        )
        time_check["source_claim_atom_ids"] = [atom["id"]]
        time_check["source_control_ids"] = [atom["control_id"]]
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_SOURCE_COVERAGE_MISMATCH"
        ):
            self._validate(wrong_dimension)

        semantic_gap = copy.deepcopy(model)
        next(
            item for item in semantic_gap["cross_line_consistency"]
            if item["dimension"] == "causality"
        )["failure_condition"] = "A different failure with no source claim."
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_SOURCE_SEMANTICS_MISSING"
        ):
            self._validate(semantic_gap)

        generic_witness = copy.deepcopy(model)
        next(
            item for item in generic_witness["cross_line_consistency"]
            if item["dimension"] == "causality"
        )["witness_ids"].append(atom["id"])
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_SOURCE_IN_GENERIC_WITNESS"
        ):
            self._validate(generic_witness)

    def test_line_order_is_presentation_only_for_legal_state_return(self) -> None:
        model = copy.deepcopy(self.proposal)
        lines = {item["id"]: item for item in model["storylines"]}
        main = lines["SL-MAIN"]
        supporting = next(
            item for item in model["storylines"] if item["type"] == "supporting"
        )
        return_connection = next(
            item
            for item in model["connections"]
            if item["from_storyline_id"] == supporting["id"]
            and item["to_storyline_id"] == "SL-MAIN"
            and item["relation"] == "causal"
        )
        self.assertGreater(return_connection["to_state_index"], 0)
        outbound = {
            "id": "SLC-STATE-RETURN",
            "type": "collision",
            "relation": "causal",
            "from_storyline_id": "SL-MAIN",
            "to_storyline_id": supporting["id"],
            "from_state": main["start_state"],
            "from_state_index": 0,
            "to_state": supporting["start_state"],
            "to_state_index": 0,
        }
        model["connections"].append(outbound)
        main["connection_ids"].append(outbound["id"])
        supporting["connection_ids"].append(outbound["id"])
        model["temporal_architecture"]["milestones"][0][
            "connection_ids"
        ].append(outbound["id"])
        model["architecture"]["line_order"] = list(
            reversed(model["architecture"]["line_order"])
        )
        self._refresh_derivations(model)
        self._validate(model)

        model["architecture"]["line_order"] = sorted(lines)
        self._refresh_derivations(model)
        self._validate(model)

    def test_line_order_still_requires_exact_storyline_coverage(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["architecture"]["line_order"].pop()
        self._refresh_derivations(model)
        with self.assertRaisesRegex(s1.S1Error, "S1_LINE_ORDER_INVALID"):
            self._validate(model)

    def test_connection_incidence_is_reciprocal_exact(self) -> None:
        model = copy.deepcopy(self.proposal)
        optional = next(
            item
            for item in model["storylines"]
            if item["type"] == "optional_melody"
        )
        optional["connection_ids"] = []
        self._refresh_derivations(model)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONNECTION_RECIPROCAL_MISMATCH"
        ):
            self._validate(model)

    def test_structural_line_needs_causal_path_to_main(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["connections"][0]["relation"] = "associative"
        with self.assertRaisesRegex(
            s1.S1Error, "S1_STRUCTURAL_CAUSAL_CLOSURE_MISSING"
        ):
            self._validate(model)

    def test_milestone_rejects_line_state_regression(self) -> None:
        model = copy.deepcopy(self.proposal)
        main = next(item for item in model["storylines"] if item["type"] == "main")
        milestones = model["temporal_architecture"]["milestones"]
        open_ref = next(
            item for item in milestones[0]["state_refs"] if item["storyline_id"] == main["id"]
        )
        probe_ref = next(
            item for item in milestones[1]["state_refs"] if item["storyline_id"] == main["id"]
        )
        open_ref.update({"state_index": 1, "state": main["state_changes"][0]})
        probe_ref.update({"state_index": 0, "state": main["start_state"]})
        self._refresh_derivations(model)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_MILESTONE_LINE_STATE_REGRESSION"
        ):
            self._validate(model)

    def test_optional_line_accepts_association_without_ordering_weight(
        self,
    ) -> None:
        model = copy.deepcopy(self.proposal)
        model["storylines"][1]["type"] = "optional_melody"
        model["storylines"][1]["closure_mode"] = None
        model["storylines"][1]["terminal_source_anchor"] = None
        model["storylines"][1]["terminal_entry_connection_id"] = None
        model["connections"][0]["relation"] = "associative"
        self._refresh_derivations(model)
        self._validate(model)
        causality = next(
            item
            for item in model["cross_line_consistency"]
            if item["dimension"] == "causality"
        )
        causality["witness_ids"].append(
            model["connections"][0]["id"]
        )
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_WITNESS_INVALID"
        ):
            self._validate(model)

        missing_dimension = copy.deepcopy(self.proposal)
        missing_dimension["cross_line_consistency"] = [
            item
            for item in missing_dimension["cross_line_consistency"]
            if item["dimension"] != "causality"
        ]
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_DIMENSIONS_MISMATCH"
        ):
            self._validate(missing_dimension)

        missing_line = copy.deepcopy(self.proposal)
        missing_line["cross_line_consistency"][0]["witness_ids"].remove(
            missing_line["storylines"][0]["id"]
        )
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_LINE_COVERAGE_MISSING"
        ):
            self._validate(missing_line)

        unknown = copy.deepcopy(self.proposal)
        unknown["cross_line_consistency"][0][
            "witness_ids"
        ].append("UNKNOWN-WITNESS")
        with self.assertRaisesRegex(
            s1.S1Error, "S1_CONSISTENCY_WITNESS_INVALID"
        ):
            self._validate(unknown)

        for field in ("claim", "failure_condition"):
            with self.subTest(placeholder_field=field):
                placeholder = copy.deepcopy(self.proposal)
                placeholder["cross_line_consistency"][0][field] = (
                    "TBD placeholder consistency statement."
                )
                with self.assertRaisesRegex(
                    s1.S1Error, "S1_CONSISTENCY_PLACEHOLDER"
                ):
                    self._validate(placeholder)

    def test_optional_line_rejects_causal_connection(self) -> None:
        model = copy.deepcopy(self.proposal)
        model["storylines"][1]["type"] = "optional_melody"
        model["storylines"][1]["closure_mode"] = None
        model["storylines"][1]["terminal_source_anchor"] = None
        model["storylines"][1]["terminal_entry_connection_id"] = None
        self._refresh_derivations(model)
        with self.assertRaisesRegex(
            s1.S1Error, "S1_OPTIONAL_CAUSAL_LINK_FORBIDDEN"
        ):
            self._validate(model)

    def test_topology_phase_rejects_optional_causal_connection(self) -> None:
        demand_payload = {
            field: copy.deepcopy(self.proposal[field])
            for field in s1.PHASE_FIELDS["demand-scan"]
        }
        line_payload = {
            field: copy.deepcopy(self.proposal[field])
            for field in s1.PHASE_FIELDS["line-design"]
        }
        topology_payload = {
            field: copy.deepcopy(self.proposal[field])
            for field in s1.PHASE_FIELDS["topology-and-consistency"]
        }
        optional_ids = {
            item["id"]
            for item in line_payload["storylines"]
            if item["type"] == "optional_melody"
        }
        connection = next(
            item
            for item in topology_payload["connections"]
            if item["from_storyline_id"] in optional_ids
            or item["to_storyline_id"] in optional_ids
        )
        connection["relation"] = "causal"
        baseline = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(encoding="utf-8")
        )
        with self.assertRaisesRegex(
            s1.S1Error, "S1_TOPOLOGY_PHASE_SEMANTIC_INVALID"
        ):
            s1._validate_topology_phase_semantics(
                demand_payload,
                line_payload,
                topology_payload,
                s1._controls(self.b0, baseline),
            )

    def test_structural_lines_may_reach_main_through_causal_path(self) -> None:
        model = copy.deepcopy(self.proposal)
        lines = {item["id"]: item for item in model["storylines"]}
        connection = model["connections"][1]
        connection["to_storyline_id"] = "SL-002"
        connection["to_state"] = lines["SL-002"]["end_state"]
        connection["to_state_index"] = len(lines["SL-002"]["state_changes"]) + 1
        lines["SL-MAIN"]["connection_ids"].remove(connection["id"])
        lines["SL-002"]["connection_ids"].append(connection["id"])
        convergence = next(
            item
            for item in model["temporal_architecture"]["milestones"]
            if connection["id"] in item["connection_ids"]
        )
        convergence["state_refs"].sort(
            key=lambda item: (
                0
                if item["storyline_id"] == connection["from_storyline_id"]
                else 2
                if item["storyline_id"] == "SL-MAIN"
                else 1
            )
        )
        model["architecture"]["line_order"] = list(
            reversed(model["architecture"]["line_order"])
        )
        self._refresh_derivations(model)
        self._validate(model)

    def test_generic_baseline_builds_closed_storyline_package(self) -> None:
        receipt = self.run_s1()
        model = receipt.model

        self.assertEqual("ready", model["status"])
        self.assertEqual(1, sum(x["type"] == "main" for x in model["storylines"]))
        self.assertGreaterEqual(len(model["storylines"]), 3)
        self.assertEqual(
            {x["id"] for x in model["storyline_demands"]},
            {x["source_ids"][0] for x in model["coverage_ledger"]},
        )
        main_id = next(x["id"] for x in model["storylines"] if x["type"] == "main")
        connected = {x["from_storyline_id"] for x in model["connections"]}
        self.assertEqual(
            {x["id"] for x in model["storylines"] if x["id"] != main_id},
            connected,
        )
        self.assertTrue(
            all(x["to_storyline_id"] == main_id for x in model["connections"])
        )
        for field, stage in (
            ("world_requirements", "W1"),
            ("environment_requirements", "E1"),
            ("event_requirements", "T1"),
            ("character_requirements", "C1"),
        ):
            self.assertTrue(model[field])
            self.assertTrue(
                all(
                    x["target_stage"] == stage
                    and x["responsibility"]
                    and x["constraints"]
                    and x["acceptance_checks"]
                    for x in model[field]
                )
            )
        self.assertNotIn("断线", json.dumps(model, ensure_ascii=False))
        self.assertEqual("S1", receipt.completion.data["stage"])
        self.assertEqual(2, receipt.transition.snapshot["revision"])
        self.assertEqual(
            receipt.completion.reference,
            receipt.transition.snapshot["current_stage_completions"]["S1"],
        )
        self.assertEqual(
            {"author_open"},
            {item["status"] for item in model["open_items"]},
        )
        self.assertEqual(
            "ready", s1.validate_s1_package(self.package)["verdict"]
        )

    @unittest.skipUnless(os.name == "nt", "Windows path-length regression")
    def test_long_final_path_with_hash_review_directories_publishes(self) -> None:
        relative_paths = [
            Path("sources") / "B0" / path.relative_to(self.b0)
            for path in self.b0.rglob("*")
            if path.is_file()
        ]
        relative_paths.extend(
            path.relative_to(self.workspace)
            for path in self.workspace.rglob("*")
            if path.is_file()
        )
        relative_paths.extend(
            Path("implementation") / identity
            for identity in s1._implementation_paths()
        )
        relative_paths.extend(
            Path(name)
            for name in (
                "storyline-architecture.json",
                "generation-evidence-index.json",
                "execution-record.json",
                "storyline-preview.md",
                "package-manifest.json",
                "validation.json",
                "stage-completion.json",
            )
        )
        longest_relative = max(len(os.fspath(path)) for path in relative_paths)
        base = self.work / "long-package-root"
        # The final tree remains below MAX_PATH. The old
        # .<destination>.<random>/package staging shape would not.
        padding = 246 - len(os.fspath(base)) - 10 - longest_relative
        self.assertGreaterEqual(padding, 8)
        self.assertLessEqual(padding, 240)
        destination = base / ("x" * padding) / "package"
        parent_length = len(os.fspath(destination.parent))
        old_deepest = (
            parent_length
            + 1
            + len(".package.")
            + 8
            + 1
            + len("package")
            + 1
            + longest_relative
        )
        new_deepest = (
            parent_length
            + 1
            + len(".s1-")
            + 8
            + 1
            + longest_relative
        )
        self.assertGreater(old_deepest, 259)
        self.assertLess(new_deepest, 260)

        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-s1"}, clear=False
        ):
            receipt = s1.run_s1(
                destination,
                baseline_package=self.b0,
                coordinator=self.coordinator,
                input_gate=self.gate,
                controlled_workspace=self.workspace,
                logical_package_path="S1/long-path",
                next_state_path="state/revision-002.json",
            )

        self.assertEqual(destination.resolve(), receipt.package_root)
        self.assertEqual("ready", s1.validate_s1_package(destination)["verdict"])
        self.assertEqual([], list(destination.parent.glob(".s1-*")))

    def test_staging_copy_failure_cleans_short_atomic_directory(self) -> None:
        with mock.patch.object(
            s1.shutil, "copytree", side_effect=OSError("injected copy failure")
        ):
            with self.assertRaises(OSError):
                self.run_s1()

        self.assertFalse(self.package.exists())
        self.assertEqual([], list(self.package.parent.glob(".s1-*")))
        self.assertEqual(1, self.coordinator.state["revision"])

    def test_late_output_conflict_is_preserved_and_staging_is_cleaned(self) -> None:
        marker = self.package / "owner.txt"

        def create_conflict(**_: object) -> object:
            self.package.mkdir(parents=True)
            marker.write_text("preexisting owner", encoding="utf-8")
            return mock.sentinel.transition

        with mock.patch.object(
            self.coordinator,
            "accept_stage_completion",
            side_effect=create_conflict,
        ):
            with self.assertRaises(s1.S1Error) as caught:
                self.run_s1()

        self.assertEqual("S1_OUTPUT_EXISTS", caught.exception.code)
        self.assertEqual("preexisting owner", marker.read_text(encoding="utf-8"))
        self.assertEqual([], list(self.package.parent.glob(".s1-*")))
        self.assertEqual(1, self.coordinator.state["revision"])

    def test_invalid_b0_is_rejected_before_candidate_package(self) -> None:
        copied = next(
            p for p in (self.b0 / "sources").rglob("design.md") if "I0" in p.parts
        )
        copied.write_text("tampered", encoding="utf-8")
        with self.assertRaises(s1.S1Error) as caught:
            self.run_s1()
        self.assertEqual("S1_B0_INVALID", caught.exception.code)
        self.assertFalse(self.package.exists())
        self.assertEqual(1, self.coordinator.state["revision"])

    def test_missing_controlled_thread_is_blocked_without_output(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(s1.S1Error) as caught:
                s1.run_s1(
                    self.package,
                    baseline_package=self.b0,
                    coordinator=self.coordinator,
                    input_gate=self.gate,
                    controlled_workspace=self.workspace,
                    logical_package_path="S1",
                    next_state_path="state/revision-002.json",
                )
        self.assertEqual("S1_THREAD_REQUIRED", caught.exception.code)
        self.assertFalse(self.package.exists())

    def test_tamper_and_resealed_semantic_gap_fail_read_only_validation(self) -> None:
        self.run_s1()
        model_path = self.package / "storyline-architecture.json"
        model = json.loads(model_path.read_text(encoding="utf-8"))
        model["storylines"][0]["state_changes"] = []
        model_path.write_text(runtime.canonical_json(model), encoding="utf-8")
        with self.assertRaises(s1.S1Error) as caught:
            s1.validate_s1_package(self.package)
        self.assertIn(
            caught.exception.code,
            {"S1_MANIFEST_INVALID", "S1_MODEL_SCHEMA_INVALID"},
        )

    def test_gate_from_another_baseline_is_rejected(self) -> None:
        bad = copy.deepcopy(self.gate.data)
        bad["baseline_completion"]["sha256"] = "0" * 64
        bad_gate = runtime.SealedDocument(
            data=bad,
            reference={
                "path": "S1/input-gate.json",
                "sha256": runtime.canonical_sha256(bad),
            },
        )
        with mock.patch.dict(
            os.environ, {"CODEX_THREAD_ID": "thread-generic-s1"}, clear=False
        ):
            with self.assertRaises(s1.S1Error) as caught:
                s1.run_s1(
                    self.package,
                    baseline_package=self.b0,
                    coordinator=self.coordinator,
                    input_gate=bad_gate,
                    controlled_workspace=self.workspace,
                    logical_package_path="S1",
                    next_state_path="state/revision-002.json",
                )
        self.assertIn(
            caught.exception.code,
            {"S1_GATE_INVALID", "S1_SESSION_INVALID"},
        )
        self.assertFalse(self.package.exists())

    def test_resealed_requirement_deletion_is_rejected(self) -> None:
        self.run_s1()
        model_path = self.package / "storyline-architecture.json"
        model = json.loads(model_path.read_text(encoding="utf-8"))
        removed = model["world_requirements"].pop()
        model["authority_partition"]["downstream_freedom"].remove(removed["id"])
        self._reseal_model(model)

        with self.assertRaises(s1.S1Error) as caught:
            s1.validate_s1_package(self.package)

        self.assertEqual("S1_REQUIREMENT_COVERAGE_MISMATCH", caught.exception.code)

    def test_forged_model_gate_is_rejected_after_reseal(self) -> None:
        self.run_s1()
        model_path = self.package / "storyline-architecture.json"
        model = json.loads(model_path.read_text(encoding="utf-8"))
        model["input_gate"]["sha256"] = "0" * 64
        self._reseal_model(model, input_gate=model["input_gate"])

        with self.assertRaises(s1.S1Error) as caught:
            s1.validate_s1_package(self.package)

        self.assertEqual("S1_GATE_REFERENCE_MISMATCH", caught.exception.code)

    def test_missing_completion_is_not_a_ready_package(self) -> None:
        self.run_s1()
        (self.package / "stage-completion.json").unlink()

        with self.assertRaises(s1.S1Error) as caught:
            s1.validate_s1_package(self.package)

        self.assertEqual("S1_COMPLETION_MISSING", caught.exception.code)

    def test_opposite_source_values_change_all_agent_phase_payloads(self) -> None:
        baseline_model = json.loads(
            (self.b0 / "author-control-baseline.json").read_text(encoding="utf-8")
        )
        controls = s1._controls(self.b0, baseline_model)
        positive = copy.deepcopy(controls)
        negative = copy.deepcopy(controls)
        positive[0]["value"] = "The protected person must stay."
        negative[0]["value"] = "The protected person must leave."
        sources = copy.deepcopy(self.proposal["source_artifacts"])
        left = agent_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            controls=positive,
        )
        right = agent_proposal(
            run_id=self.sources.run_id,
            gate_reference=self.gate.reference,
            source_artifacts=sources,
            controls=negative,
        )

        for phase in s1.PHASES:
            left_payload = (
                {"model": left}
                if phase == "final-storyline-model"
                else {field: left[field] for field in s1.PHASE_FIELDS[phase]}
            )
            right_payload = (
                {"model": right}
                if phase == "final-storyline-model"
                else {field: right[field] for field in s1.PHASE_FIELDS[phase]}
            )
            self.assertNotEqual(
                runtime.canonical_sha256(left_payload),
                runtime.canonical_sha256(right_payload),
                phase,
            )

    def test_multiline_control_participates_without_json_substring_artifact(self) -> None:
        control = "first locked line\nsecond locked line"
        artifact = {
            "responsibility": f"Carry the author control exactly:\n{control}",
            "state_changes": ["unrelated state"],
        }

        # JSON serialization escapes the newline, which is why the former raw
        # serialized-substring check produced a false negative.
        self.assertNotIn(control, runtime.canonical_json(artifact))
        self.assertTrue(s1._value_participates(control, artifact))
        self.assertFalse(
            s1._value_participates(
                "first locked line\na different second line", artifact
            )
        )

    def _reseal_model(
        self,
        model: dict[str, object],
        *,
        input_gate: dict[str, str] | None = None,
    ) -> None:
        model_path = self.package / "storyline-architecture.json"
        model_path.write_text(runtime.canonical_json(model), encoding="utf-8")
        execution_path = self.package / "execution-record.json"
        execution = json.loads(execution_path.read_text(encoding="utf-8"))
        execution["output_sha256"] = runtime.canonical_sha256(model)
        if input_gate is not None:
            execution["input_gate"] = copy.deepcopy(input_gate)
        execution_path.write_text(
            runtime.canonical_json(execution), encoding="utf-8"
        )
        manifest_path = self.package / "package-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        replacements = {
            "storyline-architecture.json": runtime.artifact_reference(
                model_path, root=self.package
            ),
            "execution-record.json": runtime.artifact_reference(
                execution_path, root=self.package
            ),
        }
        manifest["files"] = [
            replacements.get(item["path"], item) for item in manifest["files"]
        ]
        manifest["artifact_roles"]["canonical"] = replacements[
            "storyline-architecture.json"
        ]
        manifest["artifact_roles"]["execution_record"] = replacements[
            "execution-record.json"
        ]
        manifest_path.write_text(runtime.canonical_json(manifest), encoding="utf-8")
        completion_path = self.package / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["manifest"]["sha256"] = runtime.sha256_file(manifest_path)
        if input_gate is not None:
            completion["input_gate"] = copy.deepcopy(input_gate)
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )


if __name__ == "__main__":
    unittest.main()
