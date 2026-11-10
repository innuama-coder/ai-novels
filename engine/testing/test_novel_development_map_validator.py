"""Regression tests for the generic D1 development-map contract."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "novel-development-map-designer" / "scripts"
D1_MANAGER = SCRIPTS / "manage_generation.py"
D1_EXECUTOR = SCRIPTS / "execute_autonomous.py"
sys.path.insert(0, str(SCRIPTS))

import render_development_map as renderer  # noqa: E402
import validate_development_map as validator  # noqa: E402
import execution_record as d1_execution_record  # noqa: E402
import d1_generation_session  # noqa: E402


def load_harness_validator():
    path = (
        ROOT
        / "harnesses"
        / "novel-conception-interview"
        / "validators"
        / "validate_stage_completion.py"
    )
    spec = importlib.util.spec_from_file_location("d1_harness_validator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


HARNESS_VALIDATOR = load_harness_validator()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_text(value: str) -> str:
    return digest_bytes(value.encode("utf-8"))


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def write_json(path: Path, data: dict) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def reference(path: Path) -> dict[str, str]:
    return {"path": path.name, "sha256": digest_file(path)}


def make_derivation_claims(data: dict) -> list[dict]:
    claims = []
    for (subject_type, subject_id, field), spec in (
        validator.derived_subject_specs(data).items()
    ):
        sources = sorted(
            validator.allowed_derivation_sources(
                subject_type,
                subject_id,
                spec["record"],
            )
        )
        claims.append(
            {
                "id": (
                    f"DRV-{subject_type}-{subject_id}-{field}"
                    .upper()
                    .replace("_", "-")
                ),
                "subject_type": subject_type,
                "subject_id": subject_id,
                "field": field,
                "value_sha256": validator.canonical_value_sha256(spec["value"]),
                "source_controls": sources,
                "source_decisions": (
                    sorted(
                        validator.allowed_derivation_decisions(
                            subject_type, spec["record"]
                        )
                    )
                    if subject_type == "major_event"
                    else (
                        ["DEC-001"]
                        if subject_type == "unit"
                        and field
                        in {
                            "opposition",
                            "choice_options",
                            "choice_cost",
                            "consequence",
                            "next_pressure",
                        }
                        else []
                    )
                ),
                "rationale": (
                    "This bounded interpretation converts the cited controls "
                    "into a downstream development responsibility."
                ),
            }
        )
    return claims


def make_semantic_assertion(check_id: str, unit: dict) -> dict:
    required_fields = sorted(
        validator.SEMANTIC_REQUIRED_UNIT_FIELDS[check_id]
    )
    bound_text = json.dumps(
        {field: unit[field] for field in required_fields},
        ensure_ascii=False,
        sort_keys=True,
    )
    return {
        "id": (
            f"ASSERT-{check_id.upper().replace('_', '-')}-{unit['id']}"
        ),
        "subject_id": unit["id"],
        "result": "pass",
        "failure_found": False,
        "test": (
            f"Inspect the current {unit['id']} values {bound_text} against "
            f"the {check_id} failure condition."
        ),
        "failure_condition": (
            f"The {check_id} check fails if the bound {unit['id']} values "
            f"{bound_text} cannot support the declared transition."
        ),
        "counterexample": (
            f"A contrary implementation would remove or reverse the "
            f"story-specific values {bound_text}."
        ),
        "conclusion": (
            f"The bound {unit['id']} values {bound_text} preserve the "
            f"required {check_id} development logic."
        ),
        "field_evidence": [
            {
                "field": field,
                "value_sha256": validator.canonical_value_sha256(unit[field]),
            }
            for field in required_fields
        ],
    }


class GenericPackage:
    AREAS = [
        ("intent", "I0", "Intent"),
        ("subject", "I1", "Subject"),
        ("world", "I2", "World"),
        ("character", "I3", "Character"),
        ("causality", "I4", "Causality"),
        ("narrative", "I5", "Narrative"),
    ]

    def __init__(self, root: Path) -> None:
        self.root = root
        self.packets: dict[str, tuple[Path, dict]] = {}
        self.data = self._make_data()
        self.write_model_and_documents()

    def _make_data(self) -> dict:
        artifacts = []
        controls = []
        control_ids = []
        area_evidence = {
            "intent": (
                "Mara must relight Greyhaven's storm beacon without sacrificing "
                "the stranded ferry crew."
            ),
            "subject": (
                "Mara alone chooses whether to expose her father's sabotage and "
                "accept command of the failing lighthouse."
            ),
            "world": (
                "Greyhaven's tidal gate opens only when the lighthouse lens and "
                "harbor bell transmit matching coded signals."
            ),
            "character": (
                "Mara hides uncertainty behind procedural discipline until the "
                "ferry captain challenges her inherited loyalty."
            ),
            "causality": (
                "The stolen lens disables the beacon, which traps the ferry and "
                "forces Mara to confront the sabotage before the storm lands."
            ),
            "narrative": (
                "The account remains with Mara, so the saboteur's actions appear "
                "only through damaged machinery, signal logs, and testimony."
            ),
        }
        for index, (area, stage, heading) in enumerate(self.AREAS, 1):
            evidence = area_evidence[area]
            artifact_path = self.root / f"{stage.lower()}-{area}.md"
            artifact_path.write_text(
                f"# Generic design\n\n## {heading}\n\n{evidence}\n",
                encoding="utf-8",
            )
            artifact_id = f"SRC-{stage}"
            artifact = {
                "id": artifact_id,
                "area": area,
                "stage": stage,
                "path": artifact_path.name,
                "sha256": digest_file(artifact_path),
            }
            artifacts.append(artifact)
            packet_path = self.root / f"{stage.lower()}-completion.json"
            packet = {
                "design_artifact": artifact_path.name,
                "design_artifact_sha256": artifact["sha256"],
            }
            self.packets[stage] = (packet_path, packet)
            control_id = f"CTL-{index:03d}"
            control_ids.append(control_id)
            controls.append(
                {
                    "id": control_id,
                    "area": area,
                    "kind": "constraint",
                    "text": evidence,
                    "hardness": "hard",
                    "owner_stage": stage,
                    "sources": [
                        {
                            "artifact_id": artifact_id,
                            "section": heading,
                            "evidence": evidence,
                            "evidence_sha256": digest_text(evidence),
                        }
                    ],
                }
            )

        gap = {
            "id": "GAP-001",
            "domain": "cross",
            "kind": "causal_bridge",
            "question": (
                "What bounded mechanism turns the confirmed pressure into a "
                "costly protagonist decision?"
            ),
            "why_needed": (
                "Without this bridge, downstream development would have to "
                "invent the main opposition, options, and consequences."
            ),
            "source_controls": control_ids,
            "resolution": "autonomous_decision",
            "decision_ids": ["DEC-001"],
            "downstream_reservation": None,
        }
        decision = {
            "id": "DEC-001",
            "domain": "cross",
            "kind": "causal_bridge",
            "statement": (
                "Mara restores Greyhaven's coded lighthouse signal only by "
                "exposing her father's sabotage and taking command before the storm."
            ),
            "function": (
                "Link the stolen beacon lens, trapped ferry, tidal gate, and "
                "Mara's inherited loyalty to one costly act of command."
            ),
            "gap_ids": ["GAP-001"],
            "source_controls": control_ids,
            "novelty": "concretization",
            "authority_basis": (
                "This specifies how existing controls operate without changing "
                "their facts, owners, or promised outcome."
            ),
            "necessity": (
                "The map otherwise repeats the interview controls without "
                "giving downstream developers executable causal logic."
            ),
            "compatibility": (
                "The mechanism preserves every hard control and leaves scenes, "
                "dialogue, and concrete implementation open."
            ),
            "alternatives": [
                {
                    "id": "ALT-001",
                    "proposal": "Use progressive constraint and active commitment.",
                    "benefit": "Preserves agency and creates causal momentum.",
                    "cost": "Requires the protagonist to accept an irreversible loss.",
                    "status": "selected",
                },
                {
                    "id": "ALT-002",
                    "proposal": "Let an external coincidence resolve the pressure.",
                    "benefit": "Reaches the outcome with fewer development units.",
                    "cost": "Removes agency and leaves the central conflict unearned.",
                    "status": "rejected",
                },
            ],
            "impact": "structural",
            "reversibility": "whole_design",
            "projected_subjects": ["WORLD-001", "STORY-001", "CHAR-001", "U01"],
            "downstream_freedom": [
                "Choose scene form, setting details, dialogue, and exact action."
            ],
        }
        unit = {
            "id": "U01",
            "title": "Necessary transformation",
            "purpose": "Convert all confirmed controls into one testable change.",
            "source_controls": control_ids,
            "causal_nodes": ["CTL-005"],
            "pov": "CTL-006",
            "preconditions": ["The initiating pressure already exists."],
            "objective": "The protagonist seeks a defensible outcome.",
            "obstacle": "The confirmed constraints prevent an effortless result.",
            "opposition": {
                "force": "The confirmed external and internal constraints.",
                "goal": "Keep the protagonist from obtaining a cost-free resolution.",
                "tactic": "Remove easy routes as the protagonist tries them.",
                "leverage": "Control over the resources required for success.",
                "adaptation": "Escalate the cost when avoidance continues.",
            },
            "choice": "The protagonist chooses the costly permitted course.",
            "choice_options": [
                {
                    "id": "OPT-001",
                    "option": "Accept the costly permitted course.",
                    "attraction": "Creates a defensible outcome.",
                    "cost": "Makes the protagonist responsible for the consequence.",
                    "status": "selected",
                },
                {
                    "id": "OPT-002",
                    "option": "Continue avoiding commitment.",
                    "attraction": "Preserves short-term safety and deniability.",
                    "cost": "Leaves the initiating pressure unresolved.",
                    "status": "rejected",
                },
            ],
            "choice_cost": (
                "The protagonist gives up safety and accepts responsibility."
            ),
            "consequence": (
                "Commitment makes the confirmed outcome causally available."
            ),
            "next_pressure": (
                "The terminal design closes the immediate pressure while "
                "preserving downstream implementation choices."
            ),
            "development_decisions": ["DEC-001"],
            "value_shift": {
                "axis": "agency",
                "before": "avoidance",
                "after": "commitment",
                "turning_cause": "The protagonist accepts the consequence.",
            },
            "information": {
                "establish": [],
                "hint": [],
                "withhold": [],
                "payoff": [],
            },
            "world_constraints": [control_ids[2]],
            "exit_state": "The confirmed outcome is now causally available.",
            "depends_on": [],
            "creative_freedom": [
                "Choose concrete scene implementation without changing controls."
            ],
            "prohibitions": [control_ids[3]],
            "scale": "unspecified",
        }
        semantic_checks = {}
        for check_id in validator.SEMANTIC_CHECKS:
            required_fields = sorted(
                validator.SEMANTIC_REQUIRED_UNIT_FIELDS[check_id]
            )
            bound_text = json.dumps(
                {field: unit[field] for field in required_fields},
                ensure_ascii=False,
                sort_keys=True,
            )
            semantic_checks[check_id] = {
                "status": "pass",
                "reviewer_id": "designer-01",
                "reviewer_role": "map_designer",
                "method": (
                    "Review every cited control, unit transition, and dependency "
                    "against the declared contract."
                ),
                "subject_ids": ["U01"],
                "assertions": [
                    {
                        "id": f"ASSERT-{check_id.upper().replace('_', '-')}-U01",
                        "subject_id": "U01",
                        "result": "pass",
                        "failure_found": False,
                        "test": (
                            f"Inspect the current U01 values {bound_text} against "
                            f"the {check_id} failure condition."
                        ),
                        "failure_condition": (
                            f"The {check_id} check fails if the bound U01 values "
                            f"{bound_text} cannot support the declared transition."
                        ),
                        "counterexample": (
                            f"A contrary implementation would remove or reverse "
                            f"the story-specific values {bound_text}."
                        ),
                        "conclusion": (
                            f"The bound U01 values {bound_text} preserve the "
                            f"required {check_id} development logic."
                        ),
                        "field_evidence": [
                            {
                                "field": field,
                                "value_sha256": validator.canonical_value_sha256(
                                    unit[field]
                                ),
                            }
                            for field in required_fields
                        ],
                    }
                ],
            }
        handoff_responses = {
            "promise": (
                "Mara must relight Greyhaven's beacon without sacrificing the "
                "ferry crew, while accepting the cost of truthful command."
            ),
            "autonomous_value": (
                "The map adds the coded-signal repair, split authority, active "
                "opposition, and paid command choice that interviews did not specify."
            ),
            "causal_chain": (
                "The stolen lens disables the beacon, traps the ferry, closes "
                "easy routes, and forces Mara to disclose the sabotage before repair."
            ),
            "unit_contract": (
                "U01 enters with the ferry trapped, pursues a matched signal, "
                "meets resource limits, chooses disclosure, and exits with command."
            ),
            "freedom_boundary": (
                "The lighthouse, tidal gate, costly disclosure, and Mara's agency "
                "are fixed; scene order, dialogue, weather detail, and prose remain open."
            ),
            "drift_detection": (
                "A draft drifts if coincidence opens the gate, another actor makes "
                "Mara's choice, or the father-sabotage cost disappears."
            ),
            "easy_solution": (
                "A private rescue or unexplained spare lens is rejected because it "
                "bypasses the matched-signal rule and erases Mara's public responsibility."
            ),
            "scene_plan": (
                "A developer can stage damaged machinery, disputed signal logs, "
                "the captain's challenge, Mara's disclosure, and the changed gate state."
            ),
        }
        handoff_self_test = {
            "status": "pass",
            "reviewer_id": "designer-01",
            "reviewer_role": "map_designer",
            "assurance": "self_test",
            "method": (
                "Use the current D1 package as the sole evidence source and "
                "execute all eight downstream development comprehension tasks."
            ),
            "evidence_scope": "d1_package_only",
            "subject_ids": ["U01"],
            "evidence": [
                {
                    "claim": (
                        "U01 carries the Greyhaven rescue through a costly "
                        "disclosure and a verified state change."
                    ),
                    "control_ids": control_ids,
                    "unit_ids": ["U01"],
                }
            ],
            "tasks": [
            {
                "id": task_id,
                "status": "pass",
                "response": handoff_responses[task_id],
                "evidence_ids": ["U01", control_ids[0]],
            }
                for task_id in sorted(validator.HANDOFF_TASKS)
            ],
        }
        facet_details = {
            "ontology_and_nature": (
                "Greyhaven's mechanical beacon and tidal gate require a physical "
                "lens plus matching harbor-bell code.",
                "The material signal rule prevents Mara from solving the storm by declaration.",
            ),
            "time_and_history": (
                "Mara inherited the lighthouse after her father concealed the prior sabotage.",
                "The inherited failure turns the approaching storm into a family reckoning.",
            ),
            "space_and_geography": (
                "Greyhaven lighthouse, tidal gate, and stranded ferry occupy separated harbor nodes.",
                "Distance forces Mara to coordinate signal repair before the ferry reaches the reef.",
            ),
            "society_and_culture": (
                "Greyhaven trusts lighthouse keepers as public witnesses during coastal disasters.",
                "That trust makes disclosure of Mara's father socially costly and operationally necessary.",
            ),
            "institutions_and_power": (
                "Harbor command controls the tidal gate while Mara controls the lighthouse lens.",
                "Split authority requires cooperation instead of a private rescue shortcut.",
            ),
            "economy_and_resources": (
                "Greyhaven has one replacement lens and one storm-ready repair crew.",
                "Resource scarcity makes every failed repair attempt endanger the ferry.",
            ),
            "law_ethics_and_norms": (
                "Signal logs and keeper testimony determine responsibility for opening the tidal gate.",
                "Mara must choose truthful evidence over protecting her father's reputation.",
            ),
            "daily_life": (
                "Keepers maintain lenses and coded bells through disciplined nightly inspections.",
                "Mara's procedural habits reveal both competence and her avoidance of inherited guilt.",
            ),
        }
        world_facets = [
            {
                "id": f"FACET-{index:02d}",
                "domain": domain,
                "status": "defined",
                "definition": facet_details[domain][0],
                "story_relevance": facet_details[domain][1],
                "source_controls": [control_ids[2]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Concrete names, places, customs, and surface expression "
                    "remain open to downstream development."
                ),
            }
            for index, domain in enumerate(
                sorted(validator.WORLD_FACET_DOMAINS), start=1
            )
        ]
        world_systems = [
            {
                "id": "SYSTEM-001",
                "name": "Constraint and consequence system",
                "domain": "institutional",
                "definition": (
                    "The minimal operating system that turns confirmed world "
                    "rules into permissions, costs, limits, and consequences."
                ),
                "input_conditions": [
                    "A verified signal, an authorized actor, and an unresolved hazard are present."
                ],
                "transformation_rule": (
                    "The system checks evidence and authority, applies the bounded "
                    "intervention, and records both its cost and consequence."
                ),
                "observable_outputs": [
                    "A permitted or refused action and an auditable state change."
                ],
                "environment_ids": ["ENV-001"],
                "major_event_ids": [
                    "EVENT-TRIGGER",
                    "EVENT-CLIMAX",
                    "EVENT-CLOSE",
                ],
                "actors": ["The protagonist and the relevant governing actors."],
                "resources": ["Only resources authorized by confirmed controls."],
                "rules": ["Actions must follow the confirmed causal rules."],
                "permissions": [
                    "Actors may take only actions permitted by their authority."
                ],
                "costs": ["Every decisive use creates a meaningful loss."],
                "limits": ["No capability may bypass a hard control."],
                "failure_modes": [
                    "A missing permission or resource prevents the desired result."
                ],
                "story_effects": [
                    "The system forces the protagonist to choose under constraint."
                ],
                "state_changes": [
                    "The system moves from unresolved pressure to a paid consequence."
                ],
                "source_controls": [control_ids[2]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Downstream work may choose labels and scene implementation."
                ),
            }
        ]
        world_environments = [
            {
                "id": "ENV-001",
                "name": "Primary constrained environment",
                "environment_type": "hybrid",
                "definition": (
                    "The principal environment in which the confirmed pressure, "
                    "permissions, resources, and character choices become concrete."
                ),
                "scope": (
                    "It covers the full development unit without prescribing "
                    "chapter-level locations or scene blocking."
                ),
                "distinctive_features": [
                    "Access is limited and every consequential action leaves evidence."
                ],
                "basic_elements": [
                    "A decision area, an information channel, and a constrained exit."
                ],
                "sensory_conditions": [
                    "Observable conditions reinforce pressure without fixing prose."
                ],
                "occupants_and_access": [
                    "Only the protagonist and authorized functional actors may enter."
                ],
                "resources_and_infrastructure": [
                    "The environment contains only resources authorized by controls."
                ],
                "rules_and_affordances": [
                    "Actors may investigate, negotiate, choose, and act within authority."
                ],
                "hazards_and_pressures": [
                    "Delay, failed access, or resource loss raises the decision cost."
                ],
                "story_functions": [
                    "Make the central choice spatially and operationally possible."
                ],
                "state_changes": [
                    "The environment changes from unresolved pressure to paid consequence."
                ],
                "topology": {
                    "boundaries": [
                        "The operational boundary separates authorized action from the uncontrolled harbor."
                    ],
                    "zones": [
                        {
                            "id": "ZONE-DECISION",
                            "name": "Signal decision station",
                            "function": (
                                "Holds the evidence, authority, and controls needed "
                                "for the protagonist's consequential choice."
                            ),
                            "state": (
                                "The station begins with an unverified signal and "
                                "a closing intervention window."
                            ),
                            "occupant_ids": [
                                "CHAR-001",
                                "CHAR-002",
                                "CHAR-003",
                                "CHAR-004",
                            ],
                            "resources": [
                                "A damaged signal record and the bounded control interface."
                            ],
                        }
                    ],
                    "connections": [],
                },
                "event_hosting": [
                    {
                        "unit_id": "U01",
                        "zone_ids": ["ZONE-DECISION"],
                        "active_character_ids": [
                            "CHAR-001",
                            "CHAR-002",
                            "CHAR-003",
                            "CHAR-004",
                        ],
                        "event_function": (
                            "Concentrate the evidence, authority limit, and "
                            "irreversible choice in one usable setting."
                        ),
                        "entry_state": (
                            "The protagonist has evidence but has not accepted "
                            "the cost of acting."
                        ),
                        "available_actions": [
                            "Verify the signal record and commit the permitted intervention."
                        ],
                        "blocked_actions": [
                            "Bypass authorization or resolve the danger without paying the confirmed cost."
                        ],
                        "pressure": (
                            "The ferry margin closes while every failed check "
                            "reduces the remaining options."
                        ),
                        "exit_state": (
                            "The protagonist has acted, the cost is paid, and "
                            "the environment preserves the consequence."
                        ),
                    }
                ],
                "storyline_ids": [
                    "LINE-MAIN",
                    "LINE-SUBPLOT",
                    "LINE-BACKGROUND",
                ],
                "unit_ids": ["U01"],
                "source_controls": [control_ids[2]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Names, layout, décor, weather, and scene-specific movement remain open."
                ),
            }
        ]
        storylines = [
            {
                "id": f"LINE-{line_type.upper()}",
                "type": line_type,
                "title": f"Harbor signal {line_type} line",
                "function": (
                    "Carry a distinct causal, relational, or contextual function "
                    "and intersect the central transformation."
                ),
                "protagonists": ["CHAR-001"],
                "central_question": (
                    "How does this line change the protagonist's available choice?"
                ),
                "start_state": "The relevant pressure is present but unresolved.",
                "driver": "The confirmed conflict forces this line to develop.",
                "escalation": [
                    "Avoidance narrows the available options and raises the cost."
                ],
                "major_event_ids": ["EVENT-TRIGGER", "EVENT-CLIMAX", "EVENT-CLOSE"],
                "end_state": "The line has changed the terminal choice or context.",
                "resolution": (
                    "Its book-level function closes without deciding reserved details."
                ),
                "unit_ids": ["U01"],
                "source_controls": [control_ids[4]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Downstream work may choose chapter placement and scene form."
                ),
            }
            for line_type in ("main", "subplot", "background")
        ]
        storyline_details = {
            "main": {
                "function": (
                    "Carry Mara's operational effort to relight the beacon and "
                    "save the ferry through a costly public command decision."
                ),
                "central_question": (
                    "Will Mara expose her father's sabotage in time to restore "
                    "the matched lighthouse and harbor-bell signal?"
                ),
                "driver": (
                    "The stolen lens, incoming storm, and trapped ferry remove "
                    "Mara's ability to postpone command."
                ),
                "escalation": [
                    "Failed repair attempts consume the only storm-ready crew.",
                    "The ferry nears the reef while the tidal gate remains locked.",
                ],
                "turning_points": [
                    "Signal logs connect the missing lens to Mara's father.",
                    "Mara discloses the sabotage and accepts lighthouse command.",
                ],
                "intersections": [
                    "U01 makes the captain's challenge and harbor authority "
                    "conditional on Mara's disclosure."
                ],
                "end_state": (
                    "The beacon and gate can coordinate because Mara has taken "
                    "responsibility for the truthful signal."
                ),
                "resolution": (
                    "The ferry rescue and Mara's command choice close together."
                ),
            },
            "subplot": {
                "function": (
                    "Test whether Mara and the ferry captain can replace inherited "
                    "distrust with operational reliance during the rescue."
                ),
                "central_question": (
                    "Can the captain trust Mara's signal after challenging the "
                    "loyalty that kept her father's sabotage hidden?"
                ),
                "driver": (
                    "Each missed signal forces the captain to choose between "
                    "Mara's instructions and an increasingly dangerous independent route."
                ),
                "escalation": [
                    "The captain questions Mara's incomplete account of the lens.",
                    "Trust becomes necessary when the ferry has one safe turn remaining.",
                ],
                "turning_points": [
                    "The captain refuses an unsupported command.",
                    "Mara's full disclosure makes a final coordinated turn possible.",
                ],
                "intersections": [
                    "U01 ties relational trust to the same verified code that opens the gate."
                ],
                "end_state": (
                    "The captain follows Mara's verified signal without erasing "
                    "their disagreement over her earlier secrecy."
                ),
                "resolution": (
                    "Operational trust is earned for the rescue; personal reconciliation stays open."
                ),
            },
            "background": {
                "function": (
                    "Track Greyhaven's public signal rules and split harbor authority "
                    "as the institutional context that makes private repair insufficient."
                ),
                "central_question": (
                    "Will harbor command accept evidence strong enough to open "
                    "the tidal gate without abandoning its public-safety rule?"
                ),
                "driver": (
                    "Damaged machinery, coded logs, and keeper testimony create "
                    "an escalating institutional proof burden."
                ),
                "escalation": [
                    "Harbor command rejects an unmatched lighthouse signal.",
                    "The storm compresses the time available for formal verification.",
                ],
                "turning_points": [
                    "The logs establish the source of signal failure.",
                    "Mara's testimony completes the authority chain for opening the gate.",
                ],
                "intersections": [
                    "U01 converts the family secret into admissible operational evidence."
                ],
                "end_state": (
                    "The gate opens under a verified exception while the public "
                    "record preserves responsibility for the sabotage."
                ),
                "resolution": (
                    "The immediate authorization closes; Greyhaven's judgment of "
                    "the keeper family remains downstream material."
                ),
            },
        }
        for storyline in storylines:
            storyline.update(storyline_details[storyline["type"]])
            storyline.pop("turning_points", None)
            storyline.pop("intersections", None)
        major_events = [
            {
                "id": "EVENT-TRIGGER",
                "title": "The stolen lens disables the beacon and makes delay impossible",
                "event_role": "trigger",
                "definition": (
                    "The ferry loses its trusted signal while the storm closes "
                    "the harbor margin, forcing Mara to enter the evidence chain."
                ),
                "storyline_ids": [
                    "LINE-MAIN",
                    "LINE-SUBPLOT",
                    "LINE-BACKGROUND",
                ],
                "unit_ids": ["U01"],
                "environment_ids": ["ENV-001"],
                "participant_ids": ["CHAR-001", "CHAR-004"],
                "initiator_ids": ["CHAR-001"],
                "opposition_actor_ids": ["CHAR-004"],
                "preconditions": [
                    "The damaged beacon and concealed keeper record already constrain command."
                ],
                "initiating_action": (
                    "Mara opens the signal record and accepts responsibility "
                    "for proving what failed."
                ),
                "opposition_or_complication": (
                    "Nera Holt refuses an unmatched signal while the remaining "
                    "evidence implicates Mara's father."
                ),
                "decisive_change": (
                    "Private avoidance becomes an active public-safety obligation."
                ),
                "immediate_outcome": (
                    "Mara must choose whether to disclose the family record."
                ),
                "state_before": (
                    "The pressure exists but Mara can still avoid command."
                ),
                "state_after": (
                    "The failed signal makes Mara the accountable evidence holder."
                ),
                "next_pressure": (
                    "The ferry approaches the reef before the record is verified."
                ),
                "information_effects": [
                    "The failure is established as a signal-chain problem."
                ],
                "causal_predecessor_ids": [],
                "source_controls": [control_ids[4]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Scene placement, dialogue, and physical choreography remain open."
                ),
            },
            {
                "id": "EVENT-CLIMAX",
                "title": "Mara discloses the sabotage and commits the rescue signal",
                "event_role": "climax",
                "definition": (
                    "Mara names her father's sabotage, completes the proof chain, "
                    "and issues the only verified signal the ferry can follow."
                ),
                "storyline_ids": [
                    "LINE-MAIN",
                    "LINE-SUBPLOT",
                    "LINE-BACKGROUND",
                ],
                "unit_ids": ["U01"],
                "environment_ids": ["ENV-001"],
                "participant_ids": ["CHAR-001"],
                "initiator_ids": ["CHAR-001"],
                "opposition_actor_ids": [],
                "preconditions": [
                    "The signal record is available but unusable without Mara's testimony."
                ],
                "initiating_action": (
                    "Mara releases the concealed maintenance history to harbor command."
                ),
                "opposition_or_complication": (
                    "Disclosure destroys the family protection she used to avoid command."
                ),
                "decisive_change": (
                    "Her testimony converts private guilt into admissible operational evidence."
                ),
                "immediate_outcome": (
                    "The matched signal and gate exception become available for the rescue."
                ),
                "state_before": (
                    "Evidence, trust, and authority remain separated."
                ),
                "state_after": (
                    "One accountable disclosure joins evidence, trust, and authority."
                ),
                "next_pressure": (
                    "The rescue must still be executed and recorded without erasing its cost."
                ),
                "information_effects": [
                    "The source of the beacon failure becomes verified public evidence."
                ],
                "causal_predecessor_ids": ["EVENT-TRIGGER"],
                "source_controls": [control_ids[4]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "The exact testimony, timing, and reaction beats remain open."
                ),
            },
            {
                "id": "EVENT-CLOSE",
                "title": "The ferry turns under a recorded emergency exception",
                "event_role": "resolution",
                "definition": (
                    "The verified signal enables the final turn and the harbor "
                    "record preserves responsibility for the sabotage and exception."
                ),
                "storyline_ids": [
                    "LINE-MAIN",
                    "LINE-SUBPLOT",
                    "LINE-BACKGROUND",
                ],
                "unit_ids": ["U01"],
                "environment_ids": ["ENV-001"],
                "participant_ids": ["CHAR-001"],
                "initiator_ids": ["CHAR-001"],
                "opposition_actor_ids": [],
                "preconditions": [
                    "Mara's disclosure has completed the matched-signal authorization."
                ],
                "initiating_action": (
                    "Mara commits the verified rescue instruction and retains the record."
                ),
                "opposition_or_complication": (
                    "The safe outcome cannot restore the family reputation or erase distrust."
                ),
                "decisive_change": (
                    "The immediate danger closes while accountability remains active."
                ),
                "immediate_outcome": (
                    "The ferry survives and the emergency exception enters public review."
                ),
                "state_before": (
                    "The rescue is possible but has not produced a defensible outcome."
                ),
                "state_after": (
                    "The rescue is complete and its institutional cost is preserved."
                ),
                "next_pressure": (
                    "Greyhaven must live with the exposed history after the rescue."
                ),
                "information_effects": [
                    "The final record distinguishes rescue success from moral exoneration."
                ],
                "causal_predecessor_ids": ["EVENT-CLIMAX"],
                "source_controls": [control_ids[4]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Aftermath scenes and public response remain downstream choices."
                ),
            },
        ]
        storyline_demands = [
            {
                "id": f"LINE-DEMAND-{index:02d}",
                "need": need,
                "story_function": function,
                "omission_consequence": omission,
                "disposition": "dedicated_line",
                "storyline_ids": [line_id],
                "rationale": (
                    "The obligation changes a distinct choice, information "
                    "burden, or consequence and therefore merits explicit "
                    "storyline ownership."
                ),
                "source_controls": [control_ids[4]],
                "development_decisions": ["DEC-001"],
            }
            for index, (need, function, omission, line_id) in enumerate(
                [
                    (
                        "Rescue objective and accountable command",
                        "Carry the book-level promise through Mara's irreversible choice.",
                        "The rescue would become an unowned sequence of actions.",
                        "LINE-MAIN",
                    ),
                    (
                        "Operational trust under incomplete disclosure",
                        "Make the captain's trust alter the feasibility and cost of rescue.",
                        "The relationship would decorate rather than change the climax.",
                        "LINE-SUBPLOT",
                    ),
                    (
                        "Public authorization and inherited sabotage history",
                        "Turn prior wrongdoing and harbor rules into present pressure.",
                        "The gate could open through unexplained institutional convenience.",
                        "LINE-BACKGROUND",
                    ),
                ],
                1,
            )
        ]
        storyline_architecture = {
            "id": "STORY-ARCH-001",
            "entry_storyline_ids": ["LINE-SUBPLOT", "LINE-BACKGROUND"],
            "main_storyline_id": "LINE-MAIN",
            "terminal_storyline_ids": ["LINE-MAIN"],
            "coverage_rationale": (
                "The relationship and institutional histories enter as distinct "
                "pressures, merge into Mara's accountable rescue decision, and "
                "remain traceable through the shared event inventory."
            ),
            "connection_points": [
                {
                    "id": "LINE-CONNECTION-001",
                    "connection_type": "merge",
                    "event_id": "EVENT-TRIGGER",
                    "incoming_storyline_ids": [
                        "LINE-SUBPLOT",
                        "LINE-BACKGROUND",
                    ],
                    "outgoing_storyline_ids": ["LINE-MAIN"],
                    "preconditions": (
                        "The captain distrusts the signal while harbor authority "
                        "requires evidence the family record can supply."
                    ),
                    "transferred_obligations": (
                        "Relational trust and institutional proof become conditions "
                        "of Mara's central rescue objective."
                    ),
                    "resulting_state": (
                        "One main action now carries rescue, disclosure, trust, "
                        "and authorization without erasing their separate origins."
                    ),
                    "source_controls": [control_ids[4]],
                    "development_decisions": ["DEC-001"],
                }
            ],
            "source_controls": [control_ids[4]],
            "development_decisions": ["DEC-001"],
        }
        event_environment_requirements = [
            {
                "id": f"ENV-REQ-{index:02d}",
                "major_event_id": event["id"],
                "primary_environment_id": "ENV-001",
                "secondary_environment_ids": [],
                "required_capabilities": [
                    "Bring evidence, authority, and the irreversible signal decision into one bounded operating context."
                ],
                "required_zone_ids": ["ZONE-DECISION"],
                "required_resources": [
                    "The damaged signal record and bounded control interface."
                ],
                "required_permissions": [
                    "Only the accountable keeper and harbor authority may validate the intervention."
                ],
                "required_information_channels": [
                    "The signal log and verified harbor communication channel."
                ],
                "hazards_and_constraints": [
                    "The intervention window closes while failed verification consumes rescue margin."
                ],
                "transition_requirements": [],
                "adequacy_rationale": (
                    "ENV-001 provides the declared zone, evidence, authority, "
                    "resource constraint, and observable state change required "
                    f"for {event['id']}."
                ),
                "source_controls": [control_ids[2], control_ids[4]],
                "development_decisions": ["DEC-001"],
            }
            for index, event in enumerate(major_events, 1)
        ]
        supporting_profiles = [
            {
                "id": "CHAR-002",
                "name": "Elias Venn",
                "naming_status": "confirmed",
                "importance": "supporting",
                "role": "Mara's father and former lighthouse keeper",
                "story_function": "Make inherited loyalty obstruct truthful command.",
                "start_state": "His concealed sabotage governs Mara through a damaged legacy.",
                "surface_goal": "Preserve the keeper family's public reputation.",
                "deeper_need": "Have his failure named truthfully rather than inherited as duty.",
                "fear_or_avoidance": "Avoids exposure of the sabotage attached to his name.",
                "values_and_boundaries": ["Values family continuity but cannot alter present evidence."],
                "information_limits": ["Exists through records and Mara's knowledge, not present action."],
                "pressure_behavior": ["His record intensifies Mara's shame when the ferry nears the reef."],
                "agency_choices": ["The historical concealment remains the choice that others must answer."],
                "arc_stages": [],
                "end_state": "His legacy becomes acknowledged history rather than Mara's command.",
                "invariants": ["Cannot return to make Mara's present decision for her."],
                "storyline_ids": ["LINE-MAIN", "LINE-SUBPLOT"],
                "unit_ids": ["U01"],
                "demand_ids": [
                    "DEMAND-EXPERTISE",
                    "DEMAND-RELATIONSHIP",
                ],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": "Concrete records, remembered gestures, and wording remain open.",
            },
            {
                "id": "CHAR-003",
                "name": "Ilya Sorn",
                "naming_status": "autonomous",
                "importance": "supporting",
                "role": "Captain responsible for the trapped ferry",
                "story_function": "Convert Mara's truth into an operational trust decision.",
                "start_state": "Trusts certified signals but cannot verify the damaged beacon.",
                "surface_goal": "Turn the ferry away from the reef without gambling on false guidance.",
                "deeper_need": "Accept accountable cooperation when procedure alone is insufficient.",
                "fear_or_avoidance": "Refuses an unverified signal that could kill the passengers.",
                "values_and_boundaries": ["Passenger survival outranks personal reassurance."],
                "information_limits": ["Knows the ferry margin but not the keeper family's sabotage."],
                "pressure_behavior": ["Demands stronger evidence as the remaining turn radius collapses."],
                "agency_choices": ["Chooses whether Mara's disclosure earns the final turn."],
                "arc_stages": [],
                "end_state": "Makes the rescue turn on verified testimony rather than blind trust.",
                "invariants": ["Retains independent command of the ferry."],
                "storyline_ids": ["LINE-SUBPLOT", "LINE-BACKGROUND"],
                "unit_ids": ["U01"],
                "demand_ids": [
                    "DEMAND-INFORMATION",
                    "DEMAND-OPERATION",
                ],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": "Dialogue cadence and deck actions remain open.",
            },
            {
                "id": "CHAR-004",
                "name": "Nera Holt",
                "naming_status": "autonomous",
                "importance": "supporting",
                "role": "Officer personally accountable for the tidal-gate exception",
                "story_function": "Embodies public authorization without turning an institution into a person.",
                "start_state": "Requires a matched signal before opening the gate.",
                "surface_goal": "Protect the harbor while granting only defensible exceptions.",
                "deeper_need": "Recognize when accountable evidence justifies departing from routine.",
                "fear_or_avoidance": "Avoids signing an exception that cannot survive public review.",
                "values_and_boundaries": ["Will not open the gate on anonymous or unmatched claims."],
                "information_limits": ["Sees logs and captain testimony but not Mara's private memory."],
                "pressure_behavior": ["Compresses the authorization test as the storm closes the harbor."],
                "agency_choices": ["Signs or refuses the exception after the captain verifies the chain."],
                "arc_stages": [],
                "end_state": "Documents the exception and preserves responsibility for the sabotage.",
                "invariants": ["Cannot waive the public record requirement."],
                "storyline_ids": ["LINE-BACKGROUND"],
                "unit_ids": ["U01"],
                "demand_ids": [
                    "DEMAND-OPPOSITION",
                    "DEMAND-AFTERMATH",
                ],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": "Office detail and surface manner remain open.",
            },
        ]
        character_demands = [
            {
                "id": "DEMAND-AUTHORITY",
                "category": "decision_authority",
                "criticality": "structural",
                "trigger": (
                    "Mara must accept lighthouse command and publicly authorize "
                    "a costly truthful signal under storm pressure."
                ),
                "story_function": (
                    "Place the irreversible central decision in a concrete, "
                    "accountable character rather than an abstract institution."
                ),
                "omission_consequence": (
                    "Without a named decision owner, the climax would occur by "
                    "procedure and Mara's agency could not carry the story promise."
                ),
                "resolution": "profile",
                "profile_id": "CHAR-001",
                "naming_requirement": "named",
                "source_subject_ids": ["U01", "LINE-MAIN"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "The exact command language and physical action remain open."
                ),
            },
            {
                "id": "DEMAND-INFORMATION",
                "category": "information_transfer",
                "criticality": "supporting",
                "trigger": (
                    "The ferry's remaining turn margin must reach the lighthouse "
                    "and authorization chain as verified operational testimony."
                ),
                "story_function": (
                    "Give time-critical field information a named source whose "
                    "credibility and interests can be tested."
                ),
                "omission_consequence": (
                    "An anonymous report would make the rescue evidence frictionless "
                    "and erase the trust decision carried by the subplot."
                ),
                "resolution": "profile",
                "profile_id": "CHAR-003",
                "naming_requirement": "named",
                "source_subject_ids": ["U01", "LINE-SUBPLOT"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Transmission medium and exact report phrasing remain open."
                ),
            },
            {
                "id": "DEMAND-EXPERTISE",
                "category": "expertise_formation",
                "criticality": "supporting",
                "trigger": (
                    "Mara's ability to read the damaged lighthouse and inherited "
                    "maintenance record requires a concrete formative relationship."
                ),
                "story_function": (
                    "Explain where decisive expertise and its emotional bias came "
                    "from, tying competence to the legacy she must overcome."
                ),
                "omission_consequence": (
                    "If competence appears without a source, Mara becomes a convenient "
                    "solver and the father's legacy loses causal force."
                ),
                "resolution": "profile",
                "profile_id": "CHAR-002",
                "naming_requirement": "named",
                "source_subject_ids": ["U01", "LINE-MAIN"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Training memories and technical lesson details remain open."
                ),
            },
            {
                "id": "DEMAND-OPPOSITION",
                "category": "opposition_execution",
                "criticality": "supporting",
                "trigger": (
                    "The matched-signal safeguard must actively resist Mara's "
                    "emergency request before a documented exception is earned."
                ),
                "story_function": (
                    "Personify legitimate institutional resistance through an "
                    "accountable actor with the power to refuse the gate."
                ),
                "omission_consequence": (
                    "Leaving resistance as policy alone would prevent negotiation, "
                    "remove leverage, and turn the obstacle into exposition."
                ),
                "resolution": "profile",
                "profile_id": "CHAR-004",
                "naming_requirement": "named",
                "source_subject_ids": ["U01", "LINE-BACKGROUND"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Nera's procedural tactics and surface manner remain open."
                ),
            },
            {
                "id": "DEMAND-RELATIONSHIP",
                "category": "relationship_pressure",
                "criticality": "structural",
                "trigger": (
                    "Mara's family loyalty must obstruct disclosure strongly enough "
                    "to make truth a costly choice rather than an obvious answer."
                ),
                "story_function": (
                    "Anchor the protagonist's internal resistance in a specific "
                    "relationship with history, love, shame, and leverage."
                ),
                "omission_consequence": (
                    "Without Elias, the moral cost loses its personal source and Mara has no "
                    "personal relationship capable of changing through the climax."
                ),
                "resolution": "profile",
                "profile_id": "CHAR-002",
                "naming_requirement": "named",
                "source_subject_ids": ["U01", "LINE-MAIN"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "The order and sensory form of remembered pressure remain open."
                ),
            },
            {
                "id": "DEMAND-OPERATION",
                "category": "operational_execution",
                "criticality": "structural",
                "trigger": (
                    "A final ferry turn must translate the verified signal into "
                    "physical rescue action under an independent command."
                ),
                "story_function": (
                    "Ensure that information alone cannot solve the crisis and that "
                    "another capable person must execute the risky action."
                ),
                "omission_consequence": (
                    "Without Ilya, Mara's disclosure would automatically save the "
                    "ferry and collapse the action chain into a single speech."
                ),
                "resolution": "profile",
                "profile_id": "CHAR-003",
                "naming_requirement": "named",
                "source_subject_ids": ["U01", "LINE-SUBPLOT"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Deck choreography and maneuver sequence remain open."
                ),
            },
            {
                "id": "DEMAND-AFTERMATH",
                "category": "aftermath_responsibility",
                "criticality": "supporting",
                "trigger": (
                    "The emergency exception and exposed sabotage must remain in "
                    "a public record after the ferry survives."
                ),
                "story_function": (
                    "Assign the consequence to a continuing accountable person so "
                    "victory cannot erase institutional and reputational cost."
                ),
                "omission_consequence": (
                    "If nobody owns the aftermath, the story can end at rescue and "
                    "evade the promised cost of Mara's disclosure."
                ),
                "resolution": "profile",
                "profile_id": "CHAR-004",
                "naming_requirement": "named",
                "source_subject_ids": ["U01", "LINE-BACKGROUND"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "The hearing, report form, and later public response remain open."
                ),
            },
        ]
        character_relationships = [
            {
                "id": "REL-001",
                "source_id": "CHAR-001",
                "target_id": "CHAR-002",
                "relationship_type": "Daughter answering a father's damaged legacy",
                "shared_history": "Mara inherited lighthouse duty and concealed sabotage from Elias.",
                "alignment": "Both identities depend on the keeper duty being taken seriously.",
                "conflict": "Family reputation blocks the disclosure required to save the ferry.",
                "leverage": "Elias's hidden record controls Mara's shame and the repair evidence.",
                "information_asymmetry": "Mara recognizes his maintenance pattern before anyone else.",
                "change": "Inherited loyalty becomes acknowledged history rather than command.",
                "storyline_ids": ["LINE-MAIN"],
                "unit_ids": ["U01"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": "Memory order and exact emotional expression remain open.",
            },
            {
                "id": "REL-002",
                "source_id": "CHAR-002",
                "target_id": "CHAR-003",
                "relationship_type": "Historical keeper record tested by present ferry command",
                "shared_history": "The captain trusted keeper certification before the failed beacon.",
                "alignment": "Both positions require a reliable signal chain.",
                "conflict": "A concealed family record prevents operational verification.",
                "leverage": "The captain controls the ferry turn while the record controls repair evidence.",
                "information_asymmetry": "The record contains lens history; the captain knows remaining margin.",
                "change": "Inherited certification becomes evidence that must be independently tested.",
                "storyline_ids": ["LINE-SUBPLOT"],
                "unit_ids": ["U01"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": "The concrete evidence handoff remains a scene-level choice.",
            },
            {
                "id": "REL-003",
                "source_id": "CHAR-003",
                "target_id": "CHAR-004",
                "relationship_type": "Operational testimony entering a public authorization chain",
                "shared_history": "The officer has long relied on verified captain reports.",
                "alignment": "Both are responsible for passenger and harbor safety.",
                "conflict": "Emergency speed strains the matched-signal safeguard.",
                "leverage": "The captain owns testimony; the officer owns gate authorization.",
                "information_asymmetry": "The officer sees logs but depends on the captain for ferry conditions.",
                "change": "Routine certification becomes documented emergency accountability.",
                "storyline_ids": ["LINE-BACKGROUND"],
                "unit_ids": ["U01"],
                "source_controls": [control_ids[3]],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": "Authorization dialogue and procedural surface detail remain open.",
            },
        ]
        decision["projected_subjects"].extend(
            [item["id"] for item in world_facets]
            + [item["id"] for item in world_systems]
            + [item["id"] for item in world_environments]
            + [item["id"] for item in event_environment_requirements]
            + [item["id"] for item in major_events]
            + [item["id"] for item in storylines]
            + [item["id"] for item in storyline_demands]
            + [storyline_architecture["id"]]
            + [
                item["id"]
                for item in storyline_architecture["connection_points"]
            ]
            + [item["id"] for item in character_demands]
            + [item["id"] for item in supporting_profiles]
            + [item["id"] for item in character_relationships]
        )
        data = {
            "schema_version": "4.0",
            "harness": validator.HARNESS,
            "run_id": "generic-regression-run",
            "status": "ready",
            "input_gate": {},
            "source_artifacts": artifacts,
            "allowed_povs": ["CTL-006"],
            "control_points": controls,
            "authority_partition": {
                "author_locked": list(control_ids),
                "delegated": [],
                "open": [],
                "autonomous_mandate": (
                    "Develop necessary causal, opposition, choice, and "
                    "consequence logic inside confirmed boundaries."
                ),
                "downstream_reserved": (
                    "Reserve chapters, scenes, dialogue, prose, imagery, and "
                    "non-structural implementation for later development."
                ),
                "prohibitions": (
                    "Do not change locked controls, decide author-open questions, "
                    "or present autonomous additions as interview facts."
                ),
            },
            "development_gaps": [gap],
            "design_decisions": [decision],
            "units": [unit],
            "conception": {
                "world": {
                    "id": "WORLD-001",
                    "definition": (
                        "A bounded story environment governed by the confirmed "
                        "world rules and their practical consequences."
                    ),
                    "story_function": (
                        "Make the protagonist's costly choice necessary and "
                        "prevent an effortless resolution."
                    ),
                    "time_space_scope": (
                        "Only the places and duration needed by the main "
                        "transformation are developed."
                    ),
                    "operating_logic": [
                        "Actions succeed only through the confirmed causal rules."
                    ],
                    "power_and_resources": [
                        "Relevant actors have only the authority and resources "
                        "explicitly carried by the controls."
                    ],
                    "action_permissions": [
                        "Concrete implementation may vary while control facts remain fixed."
                    ],
                    "hard_constraints": [
                        "No downstream invention may bypass a hard control."
                    ],
                    "pressure_sources": [
                        "The environment makes delay and avoidance increasingly costly."
                    ],
                    "costs_and_consequences": [
                        "Every decisive action changes the available outcome."
                    ],
                    "end_state": (
                        "The world remains coherent after the confirmed "
                        "transformation has occurred."
                    ),
                    "scope_exclusions": [
                        "Unneeded history, geography and systems remain undesigned."
                    ],
                    "source_controls": [control_ids[2]],
                    "facets": world_facets,
                    "systems": world_systems,
                    "environments": world_environments,
                    "event_environment_requirements": (
                        event_environment_requirements
                    ),
                },
                "story": {
                    "id": "STORY-001",
                    "core_promise": (
                        "A constrained protagonist must choose a costly permitted "
                        "course and create a defensible outcome."
                    ),
                    "whose_story": (
                        "The protagonist whose agency changes from avoidance to commitment."
                    ),
                    "central_conflict": (
                        "The desired outcome conflicts with the confirmed limits "
                        "that rule out an effortless solution."
                    ),
                    "dramatic_question": (
                        "Will the protagonist accept the cost required to act?"
                    ),
                    "stakes": [
                        "Failure leaves the initiating pressure unresolved.",
                        "Success requires an irreversible commitment.",
                    ],
                    "start_state": (
                        "The initiating pressure exists while the protagonist still avoids commitment."
                    ),
                    "inciting_incident": (
                        "The pressure becomes impossible to ignore within the confirmed scope."
                    ),
                    "escalation_logic": [
                        "Each attempted avoidance narrows the remaining permitted options."
                    ],
                    "climax": (
                        "The protagonist chooses the costly permitted course."
                    ),
                    "resolution": (
                        "The choice produces the confirmed terminal state without "
                        "resolving anything reserved to the author."
                    ),
                    "open_threads": [
                        "Any author-owned decision remains visibly open."
                    ],
                    "scope_exclusions": [
                        "No chapter sequence, scene plan, dialogue or prose is specified."
                    ],
                    "source_controls": [control_ids[0], control_ids[4]],
                    "event_span": {
                        "earliest_causal_change": (
                            "The stolen lens disables the beacon before Mara "
                            "can continue avoiding command."
                        ),
                        "latest_consequence": (
                            "The ferry survives while the public record retains "
                            "the emergency exception and sabotage responsibility."
                        ),
                        "opening_event_ids": ["EVENT-TRIGGER"],
                        "main_action_entry_event_id": "EVENT-TRIGGER",
                        "aftermath_event_ids": ["EVENT-CLOSE"],
                        "coverage_rationale": (
                            "The event chain begins with the first confirmed "
                            "signal failure and ends only after rescue and "
                            "accountability have both changed state."
                        ),
                    },
                    "event_source_coverage": [
                        {
                            "id": "EVENT-SOURCE-CAUSAL-TRIGGER",
                            "source_artifact_id": artifacts[4]["id"],
                            "source_section": self.AREAS[4][2],
                            "source_excerpt": (
                                "The stolen lens disables the beacon"
                            ),
                            "candidate_type": "causal_transition",
                            "disposition": "enacted",
                            "major_event_ids": ["EVENT-TRIGGER"],
                            "rationale": (
                                "The opening event enacts the physical signal "
                                "failure instead of treating it as prior context."
                            ),
                        },
                        {
                            "id": "EVENT-SOURCE-CAUSAL-CLIMAX",
                            "source_artifact_id": artifacts[4]["id"],
                            "source_section": self.AREAS[4][2],
                            "source_excerpt": (
                                "forces Mara to confront the sabotage"
                            ),
                            "candidate_type": "causal_transition",
                            "disposition": "enacted",
                            "major_event_ids": ["EVENT-CLIMAX"],
                            "rationale": (
                                "The climax event enacts Mara's accountable "
                                "confrontation and disclosure."
                            ),
                        },
                        {
                            "id": "EVENT-SOURCE-CAUSAL-CLOSE",
                            "source_artifact_id": artifacts[4]["id"],
                            "source_section": self.AREAS[4][2],
                            "source_excerpt": "traps the ferry",
                            "candidate_type": "causal_antecedent",
                            "disposition": "enacted",
                            "major_event_ids": ["EVENT-CLOSE"],
                            "rationale": (
                                "The resolution changes the trapped ferry's "
                                "state rather than merely reporting evidence."
                            ),
                        },
                        {
                            "id": "EVENT-SOURCE-NARRATIVE",
                            "source_artifact_id": artifacts[5]["id"],
                            "source_section": self.AREAS[5][2],
                            "source_excerpt": area_evidence["narrative"],
                            "candidate_type": "static_context",
                            "disposition": "context_only",
                            "major_event_ids": [],
                            "rationale": (
                                "This source constrains viewpoint and evidence "
                                "presentation but does not add a story-world event."
                            ),
                        },
                    ],
                    "phases": [
                        {
                            "id": "PHASE-001",
                            "title": "Pressure becomes commitment",
                            "function": (
                                "Carry the complete causal transformation from "
                                "its entry condition to the terminal choice."
                            ),
                            "entry_state": (
                                "The initiating pressure exists and commitment is absent."
                            ),
                            "driving_goal": (
                                "Reach a defensible outcome within the confirmed constraints."
                            ),
                            "pressure": (
                                "The obstacle removes every cost-free route."
                            ),
                            "decisive_change": (
                                "The protagonist accepts the consequence and acts."
                            ),
                            "exit_state": (
                                "Commitment makes the confirmed outcome causally available."
                            ),
                            "unit_ids": ["U01"],
                            "source_controls": [control_ids[4]],
                        }
                    ],
                    "major_events": major_events,
                    "storylines": storylines,
                    "storyline_demands": storyline_demands,
                    "storyline_architecture": storyline_architecture,
                    "melody_lines": [],
                },
                "characters": {
                    "profiles": [
                    {
                        "id": "CHAR-001",
                        "name": "Mara Venn",
                        "naming_status": "confirmed",
                        "importance": "core",
                        "role": "central decision-maker",
                        "story_function": (
                            "Turn the governing conflict into an active, costly choice."
                        ),
                        "start_state": (
                            "Aware of the pressure but still oriented toward avoidance."
                        ),
                        "surface_goal": "Obtain a defensible outcome.",
                        "deeper_need": (
                            "Accept responsibility for choosing under constraint."
                        ),
                        "fear_or_avoidance": (
                            "Avoid the irreversible cost attached to commitment."
                        ),
                        "values_and_boundaries": [
                            "Will not bypass the confirmed moral and practical limits."
                        ],
                        "information_limits": [
                            "Knows only information established by the development units."
                        ],
                        "pressure_behavior": [
                            "Initially avoids, then makes the costly permitted choice."
                        ],
                        "agency_choices": [
                            "Chooses commitment after the obstacle removes easy alternatives."
                        ],
                        "arc_stages": [
                            {
                                "label": "Avoidance to commitment",
                                "state": "The protagonist begins without commitment.",
                                "pressure": "The confirmed obstacle makes avoidance untenable.",
                                "choice": "The protagonist accepts the required consequence.",
                                "change": "Agency shifts from avoidance to commitment.",
                                "unit_ids": ["U01"],
                            }
                        ],
                        "end_state": (
                            "Committed to the costly choice and responsible for its result."
                        ),
                        "invariants": [
                            "The character never gains authority or knowledge absent from controls."
                        ],
                        "storyline_ids": [
                            "LINE-MAIN",
                            "LINE-SUBPLOT",
                            "LINE-BACKGROUND",
                        ],
                        "unit_ids": ["U01"],
                        "demand_ids": ["DEMAND-AUTHORITY"],
                        "source_controls": [control_ids[1], control_ids[3]],
                        "development_decisions": [],
                        "downstream_freedom": (
                            "Dialogue, gesture, scene tactics, and prose remain open."
                        ),
                    }
                    ] + supporting_profiles,
                    "demand_register": character_demands,
                    "relationships": character_relationships,
                },
            },
            "information_obligations": [],
            "derivation_claims": [],
            "terminal_threads": [
                {
                    "id": "THREAD-MAIN",
                    "label": "Main",
                    "role": "main",
                    "terminal_unit": "U01",
                    "source_controls": [control_ids[0]],
                }
            ],
            "coverage": [
                {
                    "control_id": control_id,
                    "unit_ids": ["U01"],
                    "status": "covered",
                    "evidence": (
                        "U01 carries this control into its objective, choice, "
                        "boundary, and exit state."
                    ),
                }
                for control_id in control_ids
            ],
            "open_items": [],
            "semantic_checks": semantic_checks,
            "handoff_self_test": handoff_self_test,
            "declared_blockers": [],
        }
        data["derivation_claims"] = make_derivation_claims(data)
        return data

    def write_model_and_documents(self) -> None:
        conception = (
            self.data.get("conception")
            if isinstance(self.data.get("conception"), dict)
            else {}
        )
        (self.root / "map-data.json").write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        workspace = self.root / ".test-d1-generation"
        if workspace.exists():
            shutil.rmtree(workspace)
        d1_generation_session.begin_session(
            workspace,
            run_id=self.data["run_id"],
            executor_id="synthetic-autonomous-designer-01",
            method=(
                "Read only the six hash-bound authoritative design artifacts, "
                "synthesize the complete conception and development map, then "
                "submit every derived field to deterministic hard acceptance."
            ),
            input_gate=self.data["input_gate"],
        )
        phase_values = (
            {
                "run_id": self.data["run_id"],
                "control_points": self.data["control_points"],
                "authority_partition": self.data["authority_partition"],
            },
            {
                "run_id": self.data["run_id"],
                "development_gaps": self.data["development_gaps"],
                "design_decisions": self.data["design_decisions"],
            },
            {
                "run_id": self.data["run_id"],
                "conception": {
                    "story": conception.get("story"),
                },
                "units": self.data.get("units", []),
            },
            {
                "run_id": self.data["run_id"],
                "conception": {
                    "story": conception.get("story"),
                    "world": conception.get("world"),
                },
                "units": self.data.get("units", []),
            },
            {
                "run_id": self.data["run_id"],
                "conception": {
                    "story": conception.get("story"),
                    "world": conception.get("world"),
                    "characters": conception.get("characters"),
                },
                "units": self.data.get("units", []),
            },
            self.data,
        )
        phase_source = self.root / ".test-d1-phase.json"
        for phase, value in zip(d1_generation_session.PHASES, phase_values):
            write_json(phase_source, value)
            d1_generation_session.submit_phase(
                workspace,
                phase=phase,
                artifact=phase_source,
                summary=(
                    f"Synthetic regression execution completed {phase} with "
                    "story-specific evidence and a model-bound phase artifact."
                ),
            )
        phase_source.unlink()
        d1_generation_session.seal_into_package(workspace, self.root)
        shutil.rmtree(workspace)
        d1_execution_record.write_record(self.root, self.data)
        for filename, text in renderer.render_content_documents(self.data).items():
            (self.root / filename).write_text(
                text.rstrip() + "\n", encoding="utf-8"
            )

    def review(self):
        review = validator.Review(self.root)

        def accept_gate(_data):
            review.stage_packets.update(self.packets)
            review.evidence["input_gate"] = {"test_fixture": "accepted"}

        review.validate_input_gate = accept_gate
        return review, review.run(write_map_check=True)


class DevelopmentMapValidatorTests(unittest.TestCase):
    def make_package(self, directory: str) -> GenericPackage:
        return GenericPackage(Path(directory))

    def configure_valid_information_lifecycle(
        self, package: GenericPackage
    ) -> None:
        first = package.data["units"][0]
        second = copy.deepcopy(first)
        second.update(
            {
                "id": "U02",
                "title": "Information payoff",
                "depends_on": ["U01"],
            }
        )
        first["information"]["establish"] = ["INFO-001"]
        first["information"]["payoff"] = []
        second["information"]["establish"] = []
        second["information"]["payoff"] = ["INFO-001"]
        package.data["units"].append(second)
        package.data["design_decisions"][0]["projected_subjects"].append("U02")
        package.data["information_obligations"] = [
            {
                "id": "INFO-001",
                "statement": (
                    "A consequential truth is established for the reader and "
                    "the cited story character, then resolved in the later unit."
                ),
                "source_controls": ["CTL-004", "CTL-006"],
                "audience": "mixed",
                "knowledge_holder_controls": ["CTL-004"],
                "resolution": "within_book",
                "series_interface": None,
            }
        ]
        package.data["terminal_threads"][0]["terminal_unit"] = "U02"
        for record in package.data["coverage"]:
            record["unit_ids"] = ["U01", "U02"]
        for check_id, check in package.data["semantic_checks"].items():
            check["subject_ids"] = ["U01", "U02"]
            check["assertions"] = [
                make_semantic_assertion(check_id, first),
                make_semantic_assertion(check_id, second),
            ]
        package.data["handoff_self_test"]["subject_ids"] = ["U01", "U02"]
        package.data["handoff_self_test"]["evidence"][0]["unit_ids"] = [
            "U01",
            "U02",
        ]
        package.data["conception"]["story"]["phases"][0]["unit_ids"] = [
            "U01",
            "U02",
        ]
        for storyline in package.data["conception"]["story"]["storylines"]:
            storyline["unit_ids"] = ["U01", "U02"]
        for environment in package.data["conception"]["world"]["environments"]:
            environment["unit_ids"] = ["U01", "U02"]
            payoff_event = copy.deepcopy(environment["event_hosting"][0])
            payoff_event.update(
                {
                    "unit_id": "U02",
                    "active_character_ids": ["CHAR-001"],
                    "event_function": (
                        "Return the planted truth to the same bounded station "
                        "so verification changes the terminal choice."
                    ),
                    "entry_state": (
                        "The planted record is available but its consequence "
                        "has not been accepted."
                    ),
                    "available_actions": [
                        "Compare the planted record with the later evidence and disclose the result."
                    ],
                    "blocked_actions": [
                        "Treat the planted information as resolved before the later evidence arrives."
                    ],
                    "pressure": (
                        "The terminal decision cannot proceed while the two "
                        "information states conflict."
                    ),
                    "exit_state": (
                        "The information duty is paid off and changes the "
                        "terminal decision state."
                    ),
                }
            )
            environment["event_hosting"].append(payoff_event)
        character = package.data["conception"]["characters"]["profiles"][0]
        character["unit_ids"] = ["U01", "U02"]
        character["arc_stages"][0]["unit_ids"] = ["U01", "U02"]
        package.data["conception"]["story"]["major_events"][-1][
            "unit_ids"
        ] = ["U01", "U02"]
        package.data["derivation_claims"] = make_derivation_claims(package.data)

    def make_valid_handoff(self, package: GenericPackage) -> Path:
        root = package.root
        run_id = package.data["run_id"]
        current: dict[str, dict[str, str]] = {}
        completions: dict[str, Path] = {}
        for stage, _area, _heading in [
            (stage, area, heading)
            for area, stage, heading in package.AREAS
        ]:
            state_path = root / f"run-state-{stage.lower()}.json"
            write_json(
                state_path,
                {
                    "harness": validator.HARNESS,
                    "run_id": run_id,
                    "active_return": None,
                    "current_interview_completions": copy.deepcopy(current),
                    "resolved_returns": [],
                },
            )
            report_path = root / f"{stage.lower()}-report.md"
            report_path.write_text(f"# {stage} report\n", encoding="utf-8")
            validation_path = root / f"{stage.lower()}-validation.json"
            write_json(validation_path, {"run_id": run_id, "verdict": "ready"})
            artifact_path = root / package.packets[stage][1]["design_artifact"]
            completion_path = root / f"{stage.lower()}-completion.json"
            write_json(
                completion_path,
                {
                    "harness": validator.HARNESS,
                    "run_id": run_id,
                    "stage": stage,
                    "session_id": f"generic-{stage.lower()}",
                    "status": "ready",
                    "design_artifact": artifact_path.name,
                    "design_artifact_sha256": digest_file(artifact_path),
                    "report": reference(report_path),
                    "validation": {
                        **reference(validation_path),
                        "verdict": "ready",
                    },
                    "input_completions": [
                        reference(completions[prior])
                        for prior in validator.INTERVIEW_STAGES
                        if prior in completions
                    ],
                    "run_state": reference(state_path),
                },
            )
            completions[stage] = completion_path
            current[stage] = reference(completion_path)

        final_state = root / "run-state-final.json"
        write_json(
            final_state,
            {
                "harness": validator.HARNESS,
                "run_id": run_id,
                "active_return": None,
                "current_interview_completions": current,
                "resolved_returns": [],
            },
        )
        semantic_path = root / "v1-semantic-review.json"
        write_json(
            semantic_path,
            {
                "harness": validator.HARNESS,
                "run_id": run_id,
                "stage": "V1",
                "verdict": "pass",
                "reviewer_role": "integrity_auditor",
                "return_package": None,
                "evidence": [
                    {
                        "control_area": area,
                        "owner_stage": stage,
                        "artifact": package.packets[stage][1]["design_artifact"],
                        "finding": f"{area} is covered by the current artifact.",
                    }
                    for area, stage, _heading in package.AREAS
                ],
            },
        )
        v1_artifact = root / "integrity-report.md"
        v1_artifact.write_text("# Integrity\n", encoding="utf-8")
        v1_validation = root / "v1-validation.json"
        write_json(v1_validation, {"run_id": run_id, "verdict": "ready"})
        v1_path = root / "v1-completion.json"
        write_json(
            v1_path,
            {
                "harness": validator.HARNESS,
                "run_id": run_id,
                "stage": "V1",
                "session_id": "generic-v1",
                "status": "ready",
                "design_artifact": v1_artifact.name,
                "design_artifact_sha256": digest_file(v1_artifact),
                "validation": {**reference(v1_validation), "verdict": "ready"},
                "semantic_review": reference(semantic_path),
                "input_completions": [
                    reference(completions[stage])
                    for stage in validator.INTERVIEW_STAGES
                ],
                "run_state": reference(final_state),
            },
        )
        brief_path = root / "review-brief.html"
        brief_path.write_text("<!doctype html><title>Approved</title>", encoding="utf-8")
        v2_validation = root / "v2-validation.json"
        write_json(v2_validation, {"run_id": run_id, "verdict": "ready"})
        v2_path = root / "v2-completion.json"
        write_json(
            v2_path,
            {
                "harness": validator.HARNESS,
                "run_id": run_id,
                "stage": "V2",
                "session_id": "generic-v2",
                "status": "ready",
                "design_artifact": brief_path.name,
                "design_artifact_sha256": digest_file(brief_path),
                "validation": {**reference(v2_validation), "verdict": "ready"},
                "input_completions": [reference(v1_path)],
                "run_state": reference(final_state),
            },
        )
        approval_path = root / "author-approval.json"
        write_json(
            approval_path,
            {
                "harness": validator.HARNESS,
                "run_id": run_id,
                "approval_scope": "V2",
                "decision": "approved",
                "record_assurance": "self_recorded",
                "review_brief": reference(brief_path),
                "approval_record": {
                    "event_seq": 1,
                    "text": "The author explicitly approves this review brief.",
                },
            },
        )
        package.data["input_gate"] = {
            "run_state": reference(final_state),
            "interview_completions": [
                {"stage": stage, **reference(completions[stage])}
                for stage in validator.INTERVIEW_STAGES
            ],
            "v1_completion": reference(v1_path),
            "v2_completion": reference(v2_path),
            "author_approval": reference(approval_path),
        }
        package.write_model_and_documents()
        process = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_development_map.py"),
                str(root),
                "--write-validation",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        d1_path = root / "d1-stage-completion.json"
        completion_process = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "write_d1_completion.py"),
                str(root),
                "--session-id",
                "generic-d1",
                "--output",
                d1_path.name,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(
            completion_process.returncode,
            0,
            completion_process.stdout + completion_process.stderr,
        )
        return d1_path

    def test_specific_synthetic_ready_package_allows_empty_optional_arrays(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            _review, result = package.review()
            self.assertEqual(result["verdict"], "ready", result)

    def test_official_staged_entry_executes_and_seals_ready_package(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            self.make_valid_handoff(package)
            input_gate = package.root / ".official-input-gate.json"
            write_json(input_gate, package.data["input_gate"])
            workspace = package.root / ".official-d1-workspace"
            commands = [
                [
                    sys.executable,
                    str(D1_MANAGER),
                    "begin",
                    str(input_gate),
                    str(workspace),
                    "--run-id",
                    package.data["run_id"],
                    "--executor-id",
                    "official-synthetic-designer",
                    "--method",
                    (
                        "Build controls, compare genuine gap options, complete "
                        "the three-domain conception, and seal the final map."
                    ),
                ]
            ]
            phase_values = (
                {
                    "run_id": package.data["run_id"],
                    "control_points": package.data["control_points"],
                    "authority_partition": package.data["authority_partition"],
                },
                {
                    "run_id": package.data["run_id"],
                    "development_gaps": package.data["development_gaps"],
                    "design_decisions": package.data["design_decisions"],
                },
                {
                    "run_id": package.data["run_id"],
                    "conception": {
                        "story": package.data["conception"]["story"],
                    },
                    "units": package.data["units"],
                },
                {
                    "run_id": package.data["run_id"],
                    "conception": {
                        "story": package.data["conception"]["story"],
                        "world": package.data["conception"]["world"],
                    },
                    "units": package.data["units"],
                },
                {
                    "run_id": package.data["run_id"],
                    "conception": package.data["conception"],
                    "units": package.data["units"],
                },
                package.data,
            )
            phase_source = package.root / ".official-phase.json"
            for phase, value in zip(d1_generation_session.PHASES, phase_values):
                write_json(phase_source, value)
                commands.append(
                    [
                        sys.executable,
                        str(D1_MANAGER),
                        "submit",
                        str(workspace),
                        phase,
                        str(phase_source),
                        "--summary",
                        (
                            f"Official synthetic run completed {phase} with "
                            "model-specific evidence and a committed phase result."
                        ),
                    ]
                )
            for command in commands:
                process = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=120,
                )
                self.assertEqual(
                    process.returncode,
                    0,
                    process.stdout + process.stderr,
                )
            process = subprocess.run(
                [
                    sys.executable,
                    str(D1_EXECUTOR),
                    str(workspace),
                    str(package.root),
                    "--session-id",
                    "official-staged-d1",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=180,
            )
            self.assertEqual(
                process.returncode,
                0,
                process.stdout + process.stderr,
            )
            self.assertIn('"verdict": "ready"', process.stdout)

    def test_ready_package_requires_complete_conception_model(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            del package.data["conception"]
            with self.assertRaisesRegex(
                RuntimeError,
                "does not project",
            ):
                package.write_model_and_documents()

    def test_world_facets_must_cover_all_eight_information_domains(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["world"]["facets"].pop()
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "facets must exactly cover all eight" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_world_requires_at_least_one_major_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["world"]["environments"] = []
            package.data["design_decisions"][0]["projected_subjects"] = [
                item
                for item in package.data["design_decisions"][0][
                    "projected_subjects"
                ]
                if item != "ENV-001"
            ]
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "world.environments must be non-empty" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_world_system_requires_executable_mechanism_and_full_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            system = package.data["conception"]["world"]["systems"][0]
            del system["transformation_rule"]
            system["major_event_ids"] = ["EVENT-TRIGGER"]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("transformation_rule" in item for item in result["errors"]),
                result,
            )
            self.assertTrue(
                any(
                    "systems must collectively cover every major event" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_major_environment_requires_features_and_basic_elements(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            environment["distinctive_features"] = []
            environment["basic_elements"] = []
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "distinctive_features must be a string array" in item
                    or "basic_elements must be a string array" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_environment_requires_event_bearing_topology(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            environment.pop("topology")
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    ".topology must be an object" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_environment_event_hosting_must_exactly_cover_declared_units(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            environment["event_hosting"] = []
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "event_hosting must exactly cover" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_environment_event_rejects_unknown_zone_and_character(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            event = package.data["conception"]["world"][
                "environments"
            ][0]["event_hosting"][0]
            event["zone_ids"] = ["ZONE-MISSING"]
            event["active_character_ids"] = ["CHAR-MISSING"]
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "contains unknown zones" in item
                    for item in result["errors"]
                ),
                result,
            )
            self.assertTrue(
                any(
                    "unknown canonical character" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_environment_event_character_must_carry_hosted_unit(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            environment["topology"]["zones"][0]["occupant_ids"] = [
                "CHAR-002"
            ]
            environment["event_hosting"][0]["active_character_ids"] = [
                "CHAR-002"
            ]
            package.data["conception"]["characters"]["profiles"][1][
                "unit_ids"
            ] = []
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "does not carry hosted unit" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_environment_event_requires_observable_state_change(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            event = package.data["conception"]["world"][
                "environments"
            ][0]["event_hosting"][0]
            event["exit_state"] = event["entry_state"]
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "entry_state and exit_state must differ" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_environment_rejects_cross_field_copying(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            environment["sensory_conditions"] = list(
                environment["distinctive_features"]
            )
            environment["resources_and_infrastructure"] = list(
                environment["basic_elements"]
            )
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "must perform different environment-design jobs" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_multi_zone_environment_must_be_connected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            second_zone = copy.deepcopy(
                environment["topology"]["zones"][0]
            )
            second_zone["id"] = "ZONE-ISOLATED"
            second_zone["name"] = "Isolated evidence station"
            second_zone["function"] = (
                "Hold a separate authorization consequence that cannot affect "
                "the occupied station without a declared connection."
            )
            second_zone["state"] = (
                "The isolated station retains a pending authorization while "
                "the main decision area lacks access to it."
            )
            second_zone["resources"] = [
                "A distinct authorization token and its unresolved audit trail."
            ]
            environment["topology"]["zones"].append(second_zone)
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "must connect multi-zone environments" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_environment_allows_unoccupied_non_event_zone(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            environment["topology"]["zones"].append(
                {
                    "id": "ZONE-SEALED",
                    "name": "Sealed equipment threshold",
                    "function": (
                        "Hold an inaccessible environmental dependency without "
                        "inventing a character who must stand beside it."
                    ),
                    "state": (
                        "The threshold remains sealed while its status constrains "
                        "the occupied decision station."
                    ),
                    "occupant_ids": [],
                    "resources": [
                        "A sealed dependency indicator and its failure record."
                    ],
                }
            )
            environment["topology"]["connections"].append(
                {
                    "from_zone": "ZONE-DECISION",
                    "to_zone": "ZONE-SEALED",
                    "channel": "Read-only dependency status link",
                    "access_condition": (
                        "The occupied station may read status but cannot enter."
                    ),
                    "blockage_effect": (
                        "Loss of status prevents the protagonist from proving "
                        "the dependency is safe."
                    ),
                }
            )
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "ready", result)

    def test_environment_events_reject_repeated_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            template = environment["event_hosting"][0]
            environment["unit_ids"] = ["U01", "U02", "U03"]
            environment["event_hosting"] = []
            for unit_id in environment["unit_ids"]:
                event = copy.deepcopy(template)
                event["unit_id"] = unit_id
                environment["event_hosting"].append(event)
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            with self.assertRaisesRegex(
                ValueError,
                "world.environment_events",
            ):
                package.write_model_and_documents()

    def test_multiline_story_requires_explicit_connection_topology(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["story"]["storyline_architecture"][
                "connection_points"
            ] = []
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "requires explicit connection points" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_storyline_demands_must_justify_every_line(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["story"]["storyline_demands"] = (
                package.data["conception"]["story"]["storyline_demands"][:1]
            )
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "must justify every designed storyline" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_storyline_protagonists_must_reference_canonical_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["story"]["storylines"][0][
                "protagonists"
            ] = ["the accountable harbor team"]
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "protagonists must reference canonical character profiles"
                    in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_storyline_requires_environment_realization(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            environment = package.data["conception"]["world"][
                "environments"
            ][0]
            environment["storyline_ids"].remove("LINE-SUBPLOT")
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "storyline LINE-SUBPLOT has no major environment carrier"
                    in item
                    for item in result["errors"]
                ),
                result,
            )
            self.assertTrue(
                any(
                    "has no listed environment that carries storyline "
                    "LINE-SUBPLOT"
                    in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_event_storyline_requires_a_participating_line_carrier(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            for profile in package.data["conception"]["characters"][
                "profiles"
            ]:
                if profile["id"] in {"CHAR-001", "CHAR-004"}:
                    profile["storyline_ids"].remove("LINE-BACKGROUND")
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "major event EVENT-CLIMAX has no participating "
                    "character who carries storyline LINE-BACKGROUND"
                    in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_storyline_protagonists_require_connected_line_relationships(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            subplot = next(
                item
                for item in package.data["conception"]["story"]["storylines"]
                if item["id"] == "LINE-SUBPLOT"
            )
            subplot["protagonists"] = ["CHAR-001", "CHAR-004"]
            profile = next(
                item
                for item in package.data["conception"]["characters"][
                    "profiles"
                ]
                if item["id"] == "CHAR-004"
            )
            if "LINE-SUBPLOT" not in profile["storyline_ids"]:
                profile["storyline_ids"].append("LINE-SUBPLOT")
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "protagonists must form a connected relationship subgraph"
                    in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_optional_melody_line_can_anchor_existing_events(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            events = package.data["conception"]["story"]["major_events"]
            melody = {
                "id": "MELODY-001",
                "title": "Signal language changes with trust",
                "function": (
                    "Modulate how the same rescue signal feels as trust, "
                    "authority, and accountability change."
                ),
                "anchor_event_ids": [item["id"] for item in events[:3]],
                "variation_pattern": [
                    "The signal first appears as an untrusted family trace.",
                    "It returns as a negotiated operational instruction.",
                    "It ends as an accountable public record rather than absolution.",
                ],
                "expansion_options": [
                    "Use a repeated phrase in dialogue or records.",
                    "Compress the recurrence to one sentence at each anchor.",
                ],
                "omission_effect": (
                    "Removing the entire modulation leaves rescue causality, "
                    "authorization, climax, and ending intact."
                ),
                "boundaries": [
                    "Do not add a viewpoint or a new source of rescue evidence.",
                    "Do not let the repeated phrase authorize the harbor gate.",
                ],
                "series_potential": (
                    "A later book may recall the public wording without making "
                    "this recurrence a prerequisite."
                ),
                "required_for_causality": False,
                "required_for_resolution": False,
                "new_pov_allowed": False,
                "carries_decisive_information": False,
                "source_controls": package.data["conception"]["story"][
                    "source_controls"
                ],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Chapter development may expand, compress, or omit every "
                    "recurrence while preserving the structural story."
                ),
            }
            package.data["conception"]["story"]["melody_lines"] = [melody]
            package.data["design_decisions"][0]["projected_subjects"].append(
                melody["id"]
            )
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "ready", result)

    def test_melody_line_cannot_carry_structural_causality(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            events = package.data["conception"]["story"]["major_events"]
            melody = {
                "id": "MELODY-001",
                "title": "Optional recurring harbor signal",
                "function": (
                    "Vary the emotional meaning of one signal without changing "
                    "the rescue action."
                ),
                "anchor_event_ids": [item["id"] for item in events[:3]],
                "variation_pattern": [
                    "The signal is initially distrusted.",
                    "The signal becomes a negotiated reminder.",
                    "The signal remains in the public record.",
                ],
                "expansion_options": [
                    "Repeat it in dialogue.",
                    "Leave it only in records.",
                ],
                "omission_effect": (
                    "The rescue and its accountable resolution remain complete "
                    "if the recurrence is removed."
                ),
                "boundaries": [
                    "No new evidence source.",
                    "No independent viewpoint.",
                ],
                "series_potential": (
                    "The wording may return later as optional historical texture."
                ),
                "required_for_causality": True,
                "required_for_resolution": False,
                "new_pov_allowed": False,
                "carries_decisive_information": False,
                "source_controls": package.data["conception"]["story"][
                    "source_controls"
                ],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "The recurrence may be expanded or omitted in chapter work."
                ),
            }
            package.data["conception"]["story"]["melody_lines"] = [melody]
            package.data["design_decisions"][0]["projected_subjects"].append(
                melody["id"]
            )
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "required_for_causality must be false" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_every_major_event_requires_environment_demand_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["world"][
                "event_environment_requirements"
            ].pop()
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "must exactly cover every major event" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_story_requires_structured_major_events(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            del package.data["conception"]["story"]["major_events"]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("major_events must be non-empty" in item for item in result["errors"]),
                result,
            )

    def test_story_requires_complete_event_span_and_source_coverage(self):
        for field, expected in (
            ("event_span", "event_span is missing"),
            (
                "event_source_coverage",
                "event_source_coverage must be non-empty",
            ),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                package = self.make_package(directory)
                del package.data["conception"]["story"][field]
                package.write_model_and_documents()
                _review, result = package.review()
                self.assertEqual(result["verdict"], "revise")
                self.assertTrue(
                    any(expected in item for item in result["errors"]),
                    result,
                )

    def test_event_source_cannot_be_covered_only_as_a_later_precondition(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            coverage = package.data["conception"]["story"][
                "event_source_coverage"
            ][0]
            coverage["source_excerpt"] = (
                "The stolen lens disables the beacon"
            )
            coverage["major_event_ids"] = ["EVENT-CLOSE"]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "a precondition mention is not event coverage" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_major_event_requires_same_line_causal_predecessor(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            events = package.data["conception"]["story"]["major_events"]
            events[1]["causal_predecessor_ids"] = []
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "must cite an earlier event from the same storyline" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_major_event_requires_event_bearing_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            event = package.data["conception"]["story"]["major_events"][0]
            event["environment_ids"] = ["ENV-MISSING"]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "contains unknown environments" in item
                    or "is not hosted by any listed environment" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_major_event_requires_canonical_active_participant(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            event = package.data["conception"]["story"]["major_events"][0]
            environment = package.data["conception"]["world"]["environments"][0]
            environment["event_hosting"][0]["active_character_ids"].remove(
                "CHAR-001"
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "is not active in a listed event environment" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_major_event_rejects_declared_initiator_missing_from_action(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            event = package.data["conception"]["story"]["major_events"][0]
            event["initiating_action"] = (
                "An unnamed operator opens the record and assumes responsibility."
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "initiator CHAR-001 must be named" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_opposition_demand_requires_enacted_event_counteraction(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            for event in package.data["conception"]["story"]["major_events"]:
                event["opposition_actor_ids"] = []
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "opposition profile" in item
                    and "must enact at least one" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_character_demand_register_requires_every_responsibility_category(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            demands = package.data["conception"]["characters"]["demand_register"]
            demands[:] = [
                item
                for item in demands
                if item["category"] != "information_transfer"
            ]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "character demand register must cover every responsibility category"
                    in item
                    and "information_transfer" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_supporting_character_cannot_remain_a_functional_role_label(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            profile = package.data["conception"]["characters"]["profiles"][2]
            profile["name"] = "Ferry captain"
            profile["naming_status"] = "functional"
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "core and supporting characters must be explicitly named"
                    in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_named_character_cannot_disguise_a_functional_role_as_a_name(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            profile = package.data["conception"]["characters"]["profiles"][3]
            profile["name"] = "Harbor authorization officer"
            profile["naming_status"] = "autonomous"
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "only a functional role label" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_structural_character_demand_cannot_be_marked_not_applicable(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            demand = package.data["conception"]["characters"]["demand_register"][0]
            demand["resolution"] = "not_applicable"
            demand["profile_id"] = None
            demand["naming_requirement"] = "not_applicable"
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "structural or supporting demand cannot be not_applicable"
                    in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_core_character_requires_three_graph_depths(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            model = package.data["conception"]["characters"]
            model["profiles"] = [
                item for item in model["profiles"] if item["id"] != "CHAR-004"
            ]
            model["relationships"] = [
                item for item in model["relationships"] if item["id"] != "REL-003"
            ]
            decision = package.data["design_decisions"][0]
            decision["projected_subjects"] = [
                item
                for item in decision["projected_subjects"]
                if item not in {"CHAR-004", "REL-003"}
            ]
            package.data["derivation_claims"] = make_derivation_claims(package.data)
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "must reach at least shortest-path depth 3" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_global_graph_rejects_shortcut_disguised_as_three_layers(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            shortcut = copy.deepcopy(
                package.data["conception"]["characters"]["relationships"][2]
            )
            shortcut.update(
                {
                    "id": "REL-SHORTCUT",
                    "source_id": "CHAR-001",
                    "target_id": "CHAR-004",
                    "relationship_type": "A direct shortcut that collapses graph depth",
                }
            )
            package.data["conception"]["characters"]["relationships"].append(
                shortcut
            )
            package.data["design_decisions"][0]["projected_subjects"].append(
                shortcut["id"]
            )
            package.data["derivation_claims"] = make_derivation_claims(package.data)
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "must reach at least shortest-path depth 3" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_relationship_edges_require_canonical_person_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            relation = package.data["conception"]["characters"][
                "relationships"
            ][2]
            relation["target_id"] = "HARBOR-INSTITUTION"
            package.data["derivation_claims"] = make_derivation_claims(package.data)
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "canonical character profiles" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_character_graph_requires_complete_extended_character_definition(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            profile = package.data["conception"]["characters"]["profiles"][2]
            profile.pop("surface_goal")
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "surface_goal is too small" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_relationship_network_may_extend_beyond_three_depths(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            model = package.data["conception"]["characters"]
            profile = copy.deepcopy(model["profiles"][3])
            profile["id"] = "CHAR-005"
            profile["name"] = "Public inquiry chair"
            profile["role"] = "Chair who receives the officer's signed incident record"
            profile["story_function"] = "Carry accountability beyond the immediate gate decision."
            profile["surface_goal"] = "Preserve an independently reviewable public record."
            profile["demand_ids"] = ["DEMAND-INQUIRY"]
            model["profiles"].append(profile)
            demand = copy.deepcopy(model["demand_register"][-1])
            demand.update(
                {
                    "id": "DEMAND-INQUIRY",
                    "category": "aftermath_responsibility",
                    "criticality": "supporting",
                    "trigger": (
                        "The signed emergency record must enter an independent "
                        "public inquiry after the harbor rescue."
                    ),
                    "story_function": (
                        "Carry accountability beyond the officer who authorized "
                        "the immediate tidal-gate exception."
                    ),
                    "omission_consequence": (
                        "Without a named inquiry owner, the incident record would "
                        "exist without anyone responsible for reviewing it."
                    ),
                    "profile_id": "CHAR-005",
                    "naming_requirement": "named",
                }
            )
            model["demand_register"].append(demand)
            relation = copy.deepcopy(model["relationships"][2])
            relation.update(
                {
                    "id": "REL-004",
                    "source_id": "CHAR-004",
                    "target_id": "CHAR-005",
                    "relationship_type": "Authorization record entering public review",
                }
            )
            model["relationships"].append(relation)
            package.data["design_decisions"][0]["projected_subjects"].extend(
                [profile["id"], demand["id"], relation["id"]]
            )
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "ready", result)

    def test_story_phases_must_cover_every_development_unit(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["story"]["phases"][0]["unit_ids"] = []
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "story phases must exactly cover" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_conception_rejects_chapter_and_scene_level_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["story"]["chapters"] = [
                {"title": "Out of scope"}
            ]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "unsupported fields: chapters" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_ready_package_requires_current_autonomous_execution_record(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            path = package.root / "execution-record.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["skill_name"] = "handwritten-package"
            write_json(path, record)
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "execution-record.json.skill_name" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_ready_rejects_placeholder_conception_language(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["characters"]["profiles"][0]["name"] = (
                "Generic placeholder protagonist"
            )
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("content-specificity" in item for item in result["errors"]),
                result,
            )

    def test_ready_rejects_structurally_complete_but_ungrounded_design(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["design_decisions"][0]["statement"] = (
                "The applicable constraints progressively remove easy routes "
                "until the central actor accepts a consequential course."
            )
            package.data["design_decisions"][0]["function"] = (
                "Convert static pressure into a bounded transition with options."
            )
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "subject lacks story-grounded terms" in item
                    for item in result["errors"]
                ),
                result,
            )

    def test_same_field_templates_are_rejected_before_d1_sealing(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            copied = (
                "Every line carries the same generic function and changes only its label."
            )
            for storyline in package.data["conception"]["story"]["storylines"]:
                storyline["function"] = copied
            with self.assertRaisesRegex(
                ValueError,
                r"same-field.*story\.storylines",
            ):
                package.write_model_and_documents()

    def test_character_agency_field_comparison_retains_english_prose(self):
        copied = [
            {
                "agency_choices": [
                    "Chooses whether to reveal the harbor signal evidence."
                ]
            },
            {
                "agency_choices": [
                    "Chooses whether to reveal the harbor signal evidence."
                ]
            },
        ]
        distinct = [
            copied[0],
            {
                "agency_choices": [
                    "Authorizes the tidal gate only after the bell code matches."
                ]
            },
        ]
        self.assertEqual(
            validator.repeated_field_templates(
                copied,
                ("agency_choices",),
            ),
            {"agency_choices": 1},
        )
        self.assertEqual(
            validator.repeated_field_templates(
                distinct,
                ("agency_choices",),
            ),
            {},
        )

    def test_generation_phase_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            phase = (
                package.root
                / "generation-evidence"
                / "02-gap-and-options.json"
            )
            phase.write_text("{}\n", encoding="utf-8")
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("artifact hash is invalid" in item for item in result["errors"]),
                result,
            )

    def test_generation_session_is_required_for_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            (package.root / "generation-session.json").unlink()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("generation-session.json" in item for item in result["errors"]),
                result,
            )

    def test_ready_requires_real_autonomous_design_decisions(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["design_decisions"][0]["statement"] = package.data[
                "control_points"
            ][0]["text"]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("merely repeats an upstream control" in item for item in result["errors"]),
                result,
            )

    def test_autonomous_decision_must_project_into_model_and_units(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["design_decisions"][0]["projected_subjects"] = ["U01"]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("must project into the conception" in item for item in result["errors"]),
                result,
            )

    def test_choice_options_must_contain_a_real_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["units"][0]["choice_options"] = package.data["units"][0][
                "choice_options"
            ][:1]
            package.data["derivation_claims"] = make_derivation_claims(package.data)
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("choice_options must contain at least two" in item for item in result["errors"]),
                result,
            )

    def test_multiple_terminal_threads_are_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            root_unit = package.data["units"][0]
            terminals = []
            for unit_id, title in (("U02", "Main resolution"), ("U03", "Subplot resolution")):
                unit = copy.deepcopy(root_unit)
                unit.update(
                    {
                        "id": unit_id,
                        "title": title,
                        "purpose": f"Complete the distinct {title.lower()} responsibility.",
                        "preconditions": ["U01 has made both resolutions possible."],
                        "exit_state": f"The {title.lower()} responsibility is complete.",
                        "depends_on": ["U01"],
                    }
                )
                terminals.append(unit)
            package.data["units"].extend(terminals)
            package.data["design_decisions"][0]["projected_subjects"].extend(
                ["U02", "U03"]
            )
            all_unit_ids = ["U01", "U02", "U03"]
            for record in package.data["coverage"]:
                record["unit_ids"] = all_unit_ids
            unit_index = {
                unit["id"]: unit for unit in package.data["units"]
            }
            for check_id, check in package.data["semantic_checks"].items():
                check["subject_ids"] = all_unit_ids
                check["assertions"].extend(
                    make_semantic_assertion(check_id, unit_index[unit_id])
                    for unit_id in ("U02", "U03")
                )
            package.data["handoff_self_test"]["subject_ids"] = all_unit_ids
            package.data["handoff_self_test"]["evidence"][0]["unit_ids"] = all_unit_ids
            package.data["conception"]["story"]["phases"][0][
                "unit_ids"
            ] = all_unit_ids
            for storyline in package.data["conception"]["story"]["storylines"]:
                storyline["unit_ids"] = all_unit_ids
            for environment in package.data["conception"]["world"][
                "environments"
            ]:
                environment["unit_ids"] = all_unit_ids
                for unit_id, title in (
                    ("U02", "main consequence"),
                    ("U03", "subplot consequence"),
                ):
                    terminal_event = copy.deepcopy(
                        environment["event_hosting"][0]
                    )
                    terminal_event.update(
                        {
                            "unit_id": unit_id,
                            "active_character_ids": ["CHAR-001"],
                            "event_function": (
                                f"Host the distinct {title} after the shared "
                                "choice has made it possible."
                            ),
                            "entry_state": (
                                f"The {title} remains unresolved when the "
                                "terminal action begins."
                            ),
                            "available_actions": [
                                f"Complete and document the permitted {title}."
                            ],
                            "blocked_actions": [
                                f"Merge the {title} into the other terminal responsibility."
                            ],
                            "pressure": (
                                f"Failure to complete the {title} leaves a "
                                "separate story obligation open."
                            ),
                            "exit_state": (
                                f"The {title} is independently completed and "
                                "its consequence remains visible."
                            ),
                        }
                    )
                    environment["event_hosting"].append(terminal_event)
            character = package.data["conception"]["characters"]["profiles"][0]
            character["unit_ids"] = all_unit_ids
            character["arc_stages"][0]["unit_ids"] = all_unit_ids
            # The storyline contract requires its final major event to carry
            # the final referenced unit. This test extends the fixture graph,
            # so extend the canonical closing event with the new terminal
            # units instead of leaving the event layer stale.
            closing_event = package.data["conception"]["story"][
                "major_events"
            ][-1]
            closing_event["unit_ids"] = ["U01", "U02", "U03"]
            package.data["terminal_threads"] = [
                {
                    "id": "THREAD-MAIN",
                    "label": "Main",
                    "role": "main",
                    "terminal_unit": "U02",
                    "source_controls": ["CTL-001"],
                },
                {
                    "id": "THREAD-SUB",
                    "label": "Subplot",
                    "role": "subplot",
                    "terminal_unit": "U03",
                    "source_controls": ["CTL-001"],
                },
            ]
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "ready", result)
            self.assertEqual(
                result["evidence"]["terminal_threads"]["graph_terminals"],
                ["U02", "U03"],
            )

    def test_source_must_match_completion_bound_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["source_artifacts"][0]["sha256"] = "0" * 64
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("hash mismatch" in message for message in result["errors"]),
                result,
            )

    def test_control_text_cannot_invent_a_claim_absent_from_source(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["control_points"][0]["text"] = (
                "The protagonist must become the monarch of Mars."
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "text must exactly equal a valid source statement" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_free_control_or_terminal_meaning_is_rejected(self):
        mutations = {
            "control": lambda data: data["control_points"][0].update(
                {
                    "development_effect": (
                        "An unconstrained interpretation must not become a "
                        "development fact."
                    )
                }
            ),
            "terminal": lambda data: data["terminal_threads"][0].update(
                {
                    "development_meaning": (
                        "An unconstrained terminal interpretation must not pass."
                    )
                }
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                package = self.make_package(directory)
                mutate(package.data)
                package.write_model_and_documents()
                _review, result = package.review()
                self.assertEqual(result["verdict"], "revise")
                self.assertTrue(
                    any("is not allowed" in message for message in result["errors"]),
                    result,
                )

    def test_untraceable_pov_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["allowed_povs"] = ["OMNISCIENT"]
            package.data["units"][0]["pov"] = "OMNISCIENT"
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "allowed_povs contains unknown control" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_unplanted_payoff_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["information_obligations"] = [
                {
                    "id": "INFO-001",
                    "statement": "A consequential truth must be planted and resolved.",
                    "source_controls": ["CTL-006"],
                    "audience": "reader",
                    "knowledge_holder_controls": [],
                    "resolution": "within_book",
                    "series_interface": None,
                }
            ]
            package.data["units"][0]["information"]["payoff"] = ["INFO-001"]
            package.data["derivation_claims"] = make_derivation_claims(
                package.data
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "has no establish or hint" in message
                    or "payoff must occur after" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_valid_information_lifecycle_and_statement_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            self.configure_valid_information_lifecycle(package)
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "ready", result)

            package.data["information_obligations"][0]["statement"] = (
                "The protagonist is secretly the monarch of Mars."
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "value_sha256 does not bind "
                    "information_obligation.INFO-001.statement" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_valid_open_item_and_boundary_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["control_points"][0]["hardness"] = "open"
            package.data["authority_partition"]["author_locked"].remove("CTL-001")
            package.data["authority_partition"]["open"].append("CTL-001")
            package.data["open_items"] = [
                {
                    "id": "OPEN-001",
                    "source_control": "CTL-001",
                    "owner_stage": "I0",
                    "allowed_handling": (
                        "Keep the cited intent question open during development."
                    ),
                    "forbidden_resolution": (
                        "Do not convert the open intent question into a fixed answer."
                    ),
                }
            ]
            package.data["derivation_claims"] = make_derivation_claims(package.data)
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "ready", result)

            package.data["open_items"][0]["allowed_handling"] = (
                "The protagonist may secretly become monarch of Mars."
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "value_sha256 does not bind "
                    "open_item.OPEN-001.allowed_handling" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_control_classification_is_hash_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["control_points"][0]["hardness"] = "open"
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "value_sha256 does not bind "
                    "control_point.CTL-001.hardness" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_malformed_reference_arrays_return_revise_instead_of_crashing(self):
        for field in ("depends_on", "source_controls"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                package = self.make_package(directory)
                package.data["units"][0][field] = [{}]
                package.write_model_and_documents()
                _review, result = package.review()
                self.assertEqual(result["verdict"], "revise", result)
                self.assertTrue(
                    any(field in message for message in result["errors"]),
                    result,
                )

    def test_malformed_derivation_identity_returns_revise(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["derivation_claims"][0]["subject_type"] = {}
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise", result)
            self.assertTrue(
                any(
                    "derived subject identity is invalid" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_derived_value_change_requires_a_new_bound_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["units"][0]["objective"] = (
                "The protagonist pursues an invented objective with no new claim."
            )
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "value_sha256 does not bind unit.U01.objective" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_duplicate_terminal_registration_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            duplicate = copy.deepcopy(package.data["terminal_threads"][0])
            duplicate["id"] = "THREAD-DUPLICATE"
            duplicate["role"] = "subplot"
            package.data["terminal_threads"].append(duplicate)
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "duplicate terminal_unit registration" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_map_check_reports_canonical_verdict_not_candidate_status(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["semantic_checks"].pop("minimality")
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            report = (Path(directory) / "map-check.md").read_text(encoding="utf-8")
            self.assertIn("semantic check is missing: minimality", report)
            self.assertTrue(report.rstrip().endswith("verdict: revise"))

    def test_weak_semantic_pass_string_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["semantic_checks"]["forward_causality"]["assertions"] = "pass"
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "assertions must be non-empty" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_semantic_pass_cannot_hide_a_detected_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            assertion = package.data["semantic_checks"]["forward_causality"][
                "assertions"
            ][0]
            assertion["failure_found"] = True
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "failure_found must be false" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_semantic_assertion_must_bind_current_field_value(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            evidence = package.data["semantic_checks"]["forward_causality"][
                "assertions"
            ][0]["field_evidence"][0]
            evidence["value_sha256"] = "0" * 64
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "does not bind the current unit field" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_semantic_assertion_must_discuss_bound_story_values(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            assertion = package.data["semantic_checks"]["forward_causality"][
                "assertions"
            ][0]
            weather = (
                "Cloud bands move over a distant mountain while rain cools the road."
            )
            for field in (
                "test",
                "failure_condition",
                "counterexample",
                "conclusion",
            ):
                assertion[field] = weather
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "semantic assertion is not grounded in its bound field values"
                    in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_legacy_duplicate_character_summary_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["characters"]["profiles"][0][
                "relationships"
            ] = ["Mara acts entirely alone and has no relationship network."]
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "unsupported fields" in message and "relationships" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_legacy_duplicate_relationship_goal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.data["conception"]["characters"]["relationships"][0][
                "counterpart_goal"
            ] = "Destroy the ferry despite the canonical profile goal."
            package.write_model_and_documents()
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "unsupported fields" in message
                    and "counterpart_goal" in message
                    for message in result["errors"]
                ),
                result,
            )

    def test_hand_edited_render_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            path = Path(directory) / "development-map.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "manual edit\n",
                encoding="utf-8",
            )
            _review, result = package.review()
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any("deterministic renderer" in message for message in result["errors"]),
                result,
            )

    def test_declared_gate_failure_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gate = {
                "schema_version": "1.0",
                "harness": validator.HARNESS,
                "run_id": "generic-regression-run",
                "status": "blocked",
                "input_gate": {},
                "declared_failures": [
                    {
                        "id": "GATE-001",
                        "problem": "The current approval evidence is unavailable.",
                        "evidence": "The required hash-bound record is missing.",
                        "owner": "AUTHOR",
                        "required_action": "Record approval for the current brief.",
                    }
                ],
            }
            (root / "gate-data.json").write_text(
                json.dumps(gate, indent=2), encoding="utf-8"
            )
            review = validator.Review(root)
            review.validate_input_gate = lambda _data: None
            result = review.run()
            self.assertEqual(result["verdict"], "blocked")
            report = validator.render_blocked_report(gate, result)
            self.assertIn("verdict: blocked", report)
            self.assertIn("AUTHOR", report)

    def test_manifest_detects_post_validation_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            _review, result = package.review()
            self.assertEqual(result["verdict"], "ready", result)
            root = Path(directory)
            validation_path = root / "validation.json"
            validation_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest_path = validator.write_package_manifest(
                root, package.data, validation_path
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            error = HARNESS_VALIDATOR.validate_d1_package_manifest(
                manifest_path,
                manifest,
                package.data["run_id"],
                validation_path,
                digest_file(validation_path),
            )
            self.assertIsNone(error)
            coverage = root / "coverage-matrix.md"
            coverage.write_text(
                coverage.read_text(encoding="utf-8") + "tampered\n",
                encoding="utf-8",
            )
            error = HARNESS_VALIDATOR.validate_d1_package_manifest(
                manifest_path,
                manifest,
                package.data["run_id"],
                validation_path,
                digest_file(validation_path),
            )
            self.assertIn("has changed", error)

    def test_main_harness_revalidates_a_valid_d1_package(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            d1_path = self.make_valid_handoff(package)
            process = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "harnesses"
                        / "novel-conception-interview"
                        / "validators"
                        / "validate_stage_completion.py"
                    ),
                    str(d1_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_self_signed_fabricated_ready_validation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            d1_path = self.make_valid_handoff(package)
            root = Path(directory)
            package.data["control_points"][0]["text"] = (
                "The protagonist must become the monarch of Mars."
            )
            package.write_model_and_documents()
            fabricated = {
                "schema_version": "1.0",
                "harness": validator.HARNESS,
                "run_id": package.data["run_id"],
                "stage": "D1",
                "mode": "map",
                "verdict": "ready",
                "errors": [],
                "blockers": [],
                "warnings": [],
                "evidence": {"fabricated": True},
            }
            (root / "map-check.md").write_text(
                renderer.render_map_check(package.data, fabricated).rstrip() + "\n",
                encoding="utf-8",
            )
            validation_path = root / "validation.json"
            write_json(validation_path, fabricated)
            manifest_path = validator.write_package_manifest(
                root, package.data, validation_path
            )
            completion = json.loads(d1_path.read_text(encoding="utf-8"))
            completion["design_artifact_sha256"] = digest_file(manifest_path)
            completion["validation"] = {
                **reference(validation_path),
                "verdict": "ready",
            }
            write_json(d1_path, completion)
            process = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "harnesses"
                        / "novel-conception-interview"
                        / "validators"
                        / "validate_stage_completion.py"
                    ),
                    str(d1_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("canonical D1 validation did not pass", process.stdout)

    def test_complete_d1_package_remains_valid_after_directory_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / "source"
            copied = base / "copied"
            source.mkdir()
            package = self.make_package(str(source))
            self.make_valid_handoff(package)
            shutil.copytree(source, copied)
            process = subprocess.run(
                [
                    sys.executable,
                    str(
                        ROOT
                        / "harnesses"
                        / "novel-conception-interview"
                        / "validators"
                        / "validate_stage_completion.py"
                    ),
                    str(copied / "d1-stage-completion.json"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)

    def test_r1_handoff_requires_real_ids_and_identified_reviewer(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            d1_path = self.make_valid_handoff(package)
            d1_completion = json.loads(d1_path.read_text(encoding="utf-8"))
            derivation_reviews = [
                {
                    "derivation_id": claim["id"],
                    "status": "pass",
                    "finding": (
                        "The derived value remains bounded by the cited source "
                        "controls and does not add a story fact."
                    ),
                    "source_control_ids": claim["source_controls"],
                    "source_decision_ids": claim.get("source_decisions", []),
                }
                for claim in package.data["derivation_claims"]
            ]
            world = package.data["conception"]["world"]
            world_model_reviews = [
                {
                    "subject_id": item["id"],
                    "subject_type": subject_type,
                    "status": "pass",
                    "finding": (
                        "The independent review confirms this world subject has "
                        "causal use, operational limits, and sufficient downstream freedom."
                    ),
                    "decision_ids": item["development_decisions"],
                }
                for subject_type, records in (
                    ("facet", world["facets"]),
                    ("system", world["systems"]),
                    ("environment", world["environments"]),
                    (
                        "event_environment_requirement",
                        world["event_environment_requirements"],
                    ),
                )
                for item in records
            ]
            storylines = package.data["conception"]["story"]["storylines"]
            storyline_reviews = [
                {
                    "storyline_id": item["id"],
                    "type": item["type"],
                    "status": "pass",
                    "finding": (
                        "The independent review confirms the line has a causal "
                        "driver, progressive turns, intersections, and a usable resolution."
                    ),
                    "unit_ids": item["unit_ids"],
                    "decision_ids": item["development_decisions"],
                }
                for item in storylines
            ]
            event_source_ids = {
                event["id"]: [
                    coverage["id"]
                    for coverage in package.data["conception"]["story"][
                        "event_source_coverage"
                    ]
                    if event["id"] in coverage["major_event_ids"]
                ]
                for event in package.data["conception"]["story"]["major_events"]
            }
            major_event_reviews = [
                {
                    "event_id": item["id"],
                    "status": "pass",
                    "finding": (
                        "The independent review confirms this event has a concrete "
                        "action, complication, state change, causal predecessor, "
                        "canonical participants, and event-bearing environments."
                    ),
                    "storyline_ids": item["storyline_ids"],
                    "unit_ids": item["unit_ids"],
                    "environment_ids": item["environment_ids"],
                    "participant_ids": item["participant_ids"],
                    "source_coverage_ids": event_source_ids[item["id"]],
                    "decision_ids": item["development_decisions"],
                }
                for item in package.data["conception"]["story"]["major_events"]
            ]
            character_model = package.data["conception"]["characters"]
            demands = character_model["demand_register"]
            profiles = character_model["profiles"]
            relationships = character_model["relationships"]
            character_demand_reviews = [
                {
                    "demand_id": demand["id"],
                    "category": demand["category"],
                    "status": "pass",
                    "finding": (
                        "The independent review confirms the responsibility trigger, "
                        "story function, omission consequence, named-profile disposition, "
                        "source subjects, and downstream boundary are coherent."
                    ),
                    "resolution": demand["resolution"],
                    "profile_id": demand["profile_id"],
                    "decision_ids": demand["development_decisions"],
                }
                for demand in demands
            ]
            character_profile_reviews = [
                {
                    "character_id": character["id"],
                    "importance": character["importance"],
                    "status": "pass",
                    "finding": (
                        "The independent review confirms this canonical profile "
                        "defines role, goal, boundary, agency, arc, and story duties."
                    ),
                    "decision_ids": character["development_decisions"],
                }
                for character in profiles
            ]
            relationship_edge_reviews = [
                {
                    "relationship_id": edge["id"],
                    "source_id": edge["source_id"],
                    "target_id": edge["target_id"],
                    "status": "pass",
                    "finding": (
                        "The independent review confirms this canonical edge "
                        "defines history, conflict, leverage, information, and change."
                    ),
                    "decision_ids": edge["development_decisions"],
                }
                for edge in relationships
            ]
            adjacency = {character["id"]: [] for character in profiles}
            for edge in relationships:
                adjacency[edge["source_id"]].append(edge["target_id"])
                adjacency[edge["target_id"]].append(edge["source_id"])
            relationship_network_reviews = []
            for character in [
                item for item in profiles if item["importance"] == "core"
            ]:
                distances = {character["id"]: 0}
                queue = [character["id"]]
                for current in queue:
                    for neighbor in sorted(adjacency[current]):
                        if neighbor in distances:
                            continue
                        distances[neighbor] = distances[current] + 1
                        queue.append(neighbor)
                layers = {}
                for node_id, distance in distances.items():
                    if distance:
                        layers.setdefault(str(distance), []).append(node_id)
                layers = {
                    level: sorted(node_ids)
                    for level, node_ids in sorted(
                        layers.items(), key=lambda item: int(item[0])
                    )
                }
                component_ids = set(distances)
                relationship_network_reviews.append(
                    {
                        "character_id": character["id"],
                        "status": "pass",
                        "finding": (
                            "The independent review recomputes a continuous "
                            "three-depth person graph from canonical profiles and edges."
                        ),
                        "max_depth": max(distances.values()),
                        "layer_character_ids": layers,
                        "profiled_character_ids": [
                            node_id
                            for level in sorted(layers, key=int)
                            for node_id in layers[level]
                        ],
                        "relationship_ids": [
                            edge["id"]
                            for edge in relationships
                            if edge["source_id"] in component_ids
                            and edge["target_id"] in component_ids
                        ],
                    }
                )
            handoff = {
                "schema_version": "1.0",
                "harness": validator.HARNESS,
                "run_id": package.data["run_id"],
                "stage": "R1",
                "verdict": "pass",
                "reviewer_id": "independent-developer-01",
                "reviewer_role": "independent_developer",
                "assurance": "role_separated_execution",
                "evidence_scope": "d1_package_only",
                "method": (
                    "Independently execute the eight handoff tasks and review every "
                    "derived field against its cited controls."
                ),
                "d1_package": reference(Path(directory) / "package-manifest.json"),
                "subject_ids": ["U01"],
                "development_gap_reviews": [
                    {
                        "gap_id": "GAP-001",
                        "status": "pass",
                        "finding": (
                            "The gap is necessary before chapter development and "
                            "is assigned to the correct autonomous authority."
                        ),
                        "resolution": "autonomous_decision",
                    }
                ],
                "design_decision_reviews": [
                    {
                        "decision_id": "DEC-001",
                        "status": "pass",
                        "finding": (
                            "The decision is necessary, compatible, concrete, "
                            "causally useful, author-bounded, and leaves "
                            "implementation freedom for downstream development."
                        ),
                        "gap_ids": ["GAP-001"],
                        "source_control_ids": [
                            f"CTL-{index:03d}" for index in range(1, 7)
                        ],
                        "dimensions": {
                            "necessity": "pass",
                            "compatibility": "pass",
                            "causal_utility": "pass",
                            "specificity": "pass",
                            "author_boundary": "pass",
                            "downstream_freedom": "pass",
                        },
                    }
                ],
                "derivation_reviews": derivation_reviews,
                "world_model_reviews": world_model_reviews,
                "major_event_reviews": major_event_reviews,
                "storyline_reviews": storyline_reviews,
                "character_demand_reviews": character_demand_reviews,
                "character_profile_reviews": character_profile_reviews,
                "relationship_edge_reviews": relationship_edge_reviews,
                "relationship_network_reviews": relationship_network_reviews,
                "tasks": [
                    {
                        "id": task_id,
                        "status": "pass",
                        "response": (
                            f"The independent response for {task_id} demonstrates "
                            "the relevant promise, boundary, change, and evidence."
                        ),
                        "evidence_ids": ["U01", "CTL-001"],
                    }
                    for task_id in sorted(validator.HANDOFF_TASKS)
                ],
            }
            handoff_path = Path(directory) / "independent-handoff.json"
            error = HARNESS_VALIDATOR.validate_independent_handoff(
                handoff,
                package.data["run_id"],
                handoff_path,
                d1_path,
                d1_completion,
            )
            self.assertIsNone(error)
            handoff["tasks"][0]["evidence_ids"] = ["NONEXISTENT-ID"]
            error = HARNESS_VALIDATOR.validate_independent_handoff(
                handoff,
                package.data["run_id"],
                handoff_path,
                d1_path,
                d1_completion,
            )
            self.assertIn("unknown evidence", error)
            handoff["reviewer_id"] = ""
            error = HARNESS_VALIDATOR.validate_independent_handoff(
                handoff,
                package.data["run_id"],
                handoff_path,
                d1_path,
                d1_completion,
            )
            self.assertIn("lacks reviewer_id", error)


if __name__ == "__main__":
    unittest.main()
