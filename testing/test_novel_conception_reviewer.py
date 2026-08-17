"""Regression tests for the generic R1 conception-review contract."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from testing import test_novel_development_map_validator as d1_test_helpers
from testing.test_novel_development_map_validator import (
    GenericPackage,
    digest_file,
    make_derivation_claims,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
R1_SCRIPTS = ROOT / "skills" / "novel-conception-reviewer" / "scripts"
sys.path.insert(0, str(R1_SCRIPTS))
import r1_generation_session  # noqa: E402

R1_VALIDATOR = R1_SCRIPTS / "validate_conception_review.py"
R1_RENDERER = R1_SCRIPTS / "render_conception_review.py"
R1_COMPLETION_WRITER = R1_SCRIPTS / "write_r1_completion.py"
R1_MANAGER = R1_SCRIPTS / "manage_generation.py"
R1_EXECUTOR = R1_SCRIPTS / "execute_autonomous.py"
HARNESS_VALIDATOR = (
    ROOT
    / "harnesses"
    / "novel-conception-interview"
    / "validators"
    / "validate_stage_completion.py"
)


def load_r1_execution_record():
    path = R1_SCRIPTS / "execution_record.py"
    spec = importlib.util.spec_from_file_location("r1_execution_record", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R1_EXECUTION_RECORD = load_r1_execution_record()


def relative_reference(base: Path, target: Path) -> dict[str, str]:
    return {
        "path": Path(os.path.relpath(target, base)).as_posix(),
        "sha256": digest_file(target),
    }


def canonical_value_sha256(value) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class GenericR1Package:
    def __init__(
        self,
        root: Path,
        *,
        with_open_item: bool = False,
        with_melody_line: bool = False,
    ) -> None:
        self.root = root
        self.d1 = GenericPackage(root)
        if with_melody_line:
            events = self.d1.data["conception"]["story"]["major_events"]
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
                    "Removing the modulation leaves rescue causality, "
                    "authorization, climax, and ending intact."
                ),
                "boundaries": [
                    "Do not add a viewpoint or a new source of rescue evidence.",
                    "Do not let the repeated phrase authorize the harbor gate.",
                ],
                "series_potential": (
                    "A later book may recall the wording without making this "
                    "recurrence a prerequisite."
                ),
                "required_for_causality": False,
                "required_for_resolution": False,
                "new_pov_allowed": False,
                "carries_decisive_information": False,
                "source_controls": self.d1.data["conception"]["story"][
                    "source_controls"
                ],
                "development_decisions": ["DEC-001"],
                "downstream_freedom": (
                    "Development may expand, compress, or omit every recurrence "
                    "while preserving the structural story."
                ),
            }
            self.d1.data["conception"]["story"]["melody_lines"] = [melody]
            self.d1.data["design_decisions"][0]["projected_subjects"].append(
                melody["id"]
            )
            self.d1.data["derivation_claims"] = make_derivation_claims(
                self.d1.data
            )
            self.d1.write_model_and_documents()
        if with_open_item:
            control = self.d1.data["control_points"][0]
            control["hardness"] = "open"
            self.d1.data["authority_partition"]["author_locked"].remove(
                control["id"]
            )
            self.d1.data["authority_partition"]["open"].append(control["id"])
            self.d1.data["open_items"] = [
                {
                    "id": "OPEN-001",
                    "source_control": control["id"],
                    "owner_stage": control["owner_stage"],
                    "allowed_handling": (
                        "Keep the decision visibly unresolved while developing "
                        "only consequences already allowed by the source."
                    ),
                    "forbidden_resolution": (
                        "Do not decide the author-owned answer during development."
                    ),
                }
            ]
            self.d1.data["derivation_claims"] = make_derivation_claims(
                self.d1.data
            )
            self.d1.write_model_and_documents()
        helper = d1_test_helpers.DevelopmentMapValidatorTests()
        self.d1_completion = helper.make_valid_handoff(self.d1)
        self.package_dir = root / "r1"
        self.package_dir.mkdir()
        self.review_data = self._make_review_data()
        self.write_review_data()

    def _make_review_data(self) -> dict:
        map_data = self.d1.data
        controls = {
            item["id"]: item for item in map_data["control_points"]
        }
        units = [item["id"] for item in map_data["units"]]
        first_control = next(iter(controls))
        first_unit = units[0]
        first_unit_record = map_data["units"][0]
        area_reviews = []
        for area, stage, _heading in self.d1.AREAS:
            area_ids = [
                item["id"]
                for item in map_data["control_points"]
                if item["area"] == area
            ]
            area_reviews.append(
                {
                    "area": area,
                    "owner_stage": stage,
                    "status": "pass",
                    "finding": (
                        f"The {area} controls are internally usable and are "
                        "carried into the validated development map; the bound "
                        f"story evidence is: {controls[area_ids[0]]['text']}"
                    ),
                    "control_ids": area_ids,
                }
            )
        cross_findings = {
            "autonomous_value": (
                "DEC-001 adds the matched-signal repair, split authority, and "
                "paid command choice beyond the interview controls."
            ),
            "gap_closure": (
                "GAP-001 is closed by making Mara expose the sabotage before "
                "the lighthouse and harbor bell can coordinate."
            ),
            "promise_scope": (
                "The ferry rescue, truthful command, and inherited loyalty remain "
                "inside the Greyhaven promise without adding a second premise."
            ),
            "world_causality": (
                "The lighthouse lens, harbor bell, coded signal, and tidal gate "
                "create permissions and failure consequences for U01."
            ),
            "character_agency": (
                "Mara alone chooses disclosure and command; the ferry captain and "
                "harbor authority retain their separate operational choices."
            ),
            "opposition_response": (
                "Each failed repair removes resources, brings the ferry nearer the "
                "reef, and makes continued avoidance harder in U01."
            ),
            "choice_costs": (
                "Mara saves the ferry only by surrendering family deniability and "
                "accepting public responsibility for the sabotage."
            ),
            "easy_solution": (
                "An unexplained spare lens or private gate opening would bypass the "
                "matched-signal constraint and is therefore unavailable."
            ),
            "causal_closure": (
                "Verified disclosure enables repair, repair enables the coded beacon, "
                "and the matched signal enables the terminal gate state."
            ),
            "narrative_information": (
                "Damaged machinery, signal logs, and testimony expose the sabotage "
                "through Mara's permitted viewpoint rather than omniscient disclosure."
            ),
            "thematic_testing": (
                "Mara's inherited loyalty is tested by a rescue that requires truth "
                "and responsibility rather than abstract reflection."
            ),
            "open_boundaries": (
                "Dialogue, scene order, surface weather, and later public judgment "
                "remain open while the causal mechanism stays fixed."
            ),
            "development_usability": (
                "U01 supplies a trapped-ferry entry, matched-signal objective, "
                "resource opposition, disclosure choice, cost, and changed gate exit."
            ),
        }
        cross_checks = {}
        for check_id, finding in cross_findings.items():
            objective = first_unit_record["objective"]
            cross_checks[check_id] = {
                "status": "pass",
                "finding": finding,
                "control_ids": [first_control],
                "unit_ids": [first_unit],
                "assertions": [
                    {
                        "id": f"R1-{check_id}-A01",
                        "result": "pass",
                        "failure_found": False,
                        "test": (
                            f"Challenge the current unit objective '{objective}' "
                            "against this review dimension and trace its effects."
                        ),
                        "failure_condition": (
                            f"The objective '{objective}' would fail if it could "
                            "not sustain the claimed causal or agency requirement."
                        ),
                        "counterexample": (
                            f"A bypass that removes '{objective}' was tested and "
                            "does not preserve the bound development contract."
                        ),
                        "conclusion": (
                            f"The current objective '{objective}' survives this "
                            "specific challenge without a detected contradiction."
                        ),
                        "field_evidence": [
                            {
                                "subject_id": first_unit,
                                "field": "objective",
                                "value_sha256": canonical_value_sha256(
                                    objective
                                ),
                            }
                        ],
                    }
                ],
            }
        derivation_reviews = [
            {
                "derivation_id": claim["id"],
                "status": "pass",
                "finding": (
                    "The current value remains a bounded development "
                    "interpretation of the cited controls and adds no new fact."
                ),
                "source_control_ids": copy.deepcopy(
                    claim["source_controls"]
                ),
                "source_decision_ids": copy.deepcopy(
                    claim.get("source_decisions", [])
                ),
            }
            for claim in map_data["derivation_claims"]
        ]
        gap_reviews = [
            {
                "gap_id": gap["id"],
                "status": "pass",
                "finding": (
                    f"{gap['question']} This is a real pre-chapter development "
                    "gap, and its "
                    "declared resolution assigns it to the correct authority."
                ),
                "resolution": gap["resolution"],
            }
            for gap in map_data["development_gaps"]
        ]
        decision_reviews = [
            {
                "decision_id": decision["id"],
                "status": "pass",
                "finding": (
                    "The selected addition is necessary, concrete, causally "
                    "useful, compatible with author controls, and still leaves "
                    "scene-level implementation freedom downstream."
                ),
                "gap_ids": copy.deepcopy(decision["gap_ids"]),
                "source_control_ids": copy.deepcopy(
                    decision["source_controls"]
                ),
                "dimensions": {
                    "necessity": "pass",
                    "compatibility": "pass",
                    "causal_utility": "pass",
                    "specificity": "pass",
                    "author_boundary": "pass",
                    "downstream_freedom": "pass",
                },
            }
            for decision in map_data["design_decisions"]
        ]
        task_responses = {
            "promise": (
                "The package identifies the governing promise, its hard scope "
                "and the terminal responsibility that development must pay."
            ),
            "autonomous_value": (
                "The package identifies the development gap and the new "
                "bounded design decision that adds opposition, options, cost, "
                "consequence, and causal momentum beyond the interview summary."
            ),
            "causal_chain": (
                "The package supports a dependency-ordered chain in which "
                "pressure produces an active choice and a changed exit state."
            ),
            "unit_contract": (
                "Every listed unit provides preconditions, objective, obstacle, "
                "choice, value change, information duty and an exit state."
            ),
            "freedom_boundary": (
                "The package distinguishes implementation freedom from cited "
                "controls, prohibitions and author-owned open decisions."
            ),
            "drift_detection": (
                "A downstream change drifts when it contradicts a cited "
                "control, invents authority or silently resolves an open item."
            ),
            "easy_solution": (
                "The most convenient external rescue is rejected because it "
                "would bypass the established constraints, erase the costly "
                "choice, and leave the promised transformation unearned."
            ),
            "scene_plan": (
                "A developer can plan a scene from the unit objective, obstacle, "
                "choice, value shift and exit state without inventing a premise."
            ),
        }
        open_reviews = [
            {
                "open_item_id": item["id"],
                "status": "preserved",
                "finding": (
                    "The package permits only the declared handling and keeps "
                    "the forbidden author-owned resolution outside development."
                ),
            }
            for item in map_data["open_items"]
        ]
        conception = map_data["conception"]
        world_subject_ids = [
            conception["world"]["id"],
            *[item["id"] for item in conception["world"]["facets"]],
            *[item["id"] for item in conception["world"]["systems"]],
            *[item["id"] for item in conception["world"]["environments"]],
        ]
        story_subject_ids = [
            conception["story"]["id"],
            *[item["id"] for item in conception["story"]["phases"]],
            *[item["id"] for item in conception["story"]["major_events"]],
            *[item["id"] for item in conception["story"]["storylines"]],
        ]
        character_model = conception["characters"]
        demands = character_model["demand_register"]
        profiles = character_model["profiles"]
        relationships = character_model["relationships"]
        character_subject_ids = [
            *[item["id"] for item in demands],
            *[item["id"] for item in profiles],
            *[item["id"] for item in relationships],
        ]
        conception_reviews = [
            {
                "area": "world",
                "status": "pass",
                "finding": (
                    "The world model defines the operating environment, "
                    "permissions, constraints, pressures, consequences and end "
                    "state at the depth needed for story development."
                ),
                "subject_ids": world_subject_ids,
                "control_ids": copy.deepcopy(
                    conception["world"]["source_controls"]
                ),
            },
            {
                "area": "story",
                "status": "pass",
                "finding": (
                    "The story model states the promise, conflict, stakes, "
                    "escalation, climax and resolution, while its phases cover "
                    "every development unit in causal order."
                ),
                "subject_ids": story_subject_ids,
                "control_ids": copy.deepcopy(
                    conception["story"]["source_controls"]
                ),
            },
            {
                "area": "characters",
                "status": "pass",
                "finding": (
                    "The character model gives each central actor a role, goal, "
                    "need, boundary, information limit, agency and staged arc "
                    "without inventing scene-level behavior."
                ),
                "subject_ids": character_subject_ids,
                "control_ids": sorted(
                    set().union(
                        *[
                            set(item["source_controls"])
                            for item in profiles
                        ]
                    )
                ),
            },
        ]
        world_model_reviews = [
            {
                "subject_id": item["id"],
                "subject_type": subject_type,
                "status": "pass",
                "finding": (
                    f"{item.get('definition', item.get('adequacy_rationale', ''))} "
                    f"{item.get('story_relevance', item.get('story_effects', item.get('story_functions', item.get('required_capabilities', ''))))} "
                    "This world subject defines "
                    "story-relevant facts, permissions, "
                    "limits, costs, failure behavior and downstream freedom without "
                    "expanding into unused encyclopedia detail."
                ),
                "decision_ids": copy.deepcopy(
                    item["development_decisions"]
                ),
            }
            for collection, subject_type in (
                ("facets", "facet"),
                ("systems", "system"),
                ("environments", "environment"),
                (
                    "event_environment_requirements",
                    "event_environment_requirement",
                ),
            )
            for item in conception["world"][collection]
        ]
        storyline_reviews = [
            {
                "storyline_id": item["id"],
                "type": item["type"],
                "status": "pass",
                "finding": (
                    f"{item['function']} {item['central_question']} Its driver, "
                    "major-event progression, intersections, and resolution are distinct "
                    "from the other two lines."
                ),
                "unit_ids": copy.deepcopy(item["unit_ids"]),
                "decision_ids": copy.deepcopy(
                    item["development_decisions"]
                ),
            }
            for item in conception["story"]["storylines"]
        ]
        storyline_demand_reviews = [
            {
                "demand_id": item["id"],
                "status": "pass",
                "finding": (
                    f"{item['need']} {item['story_function']} The disposition "
                    "is justified by its omission consequence and maps to "
                    "explicit lines without creating decorative duplication."
                ),
                "disposition": item["disposition"],
                "storyline_ids": copy.deepcopy(item["storyline_ids"]),
                "decision_ids": copy.deepcopy(
                    item["development_decisions"]
                ),
            }
            for item in conception["story"]["storyline_demands"]
        ]
        architecture = conception["story"]["storyline_architecture"]
        storyline_architecture_review = {
            "subject_id": architecture["id"],
            "status": "pass",
            "finding": (
                f"{architecture['coverage_rationale']} The entry, main, "
                "terminal and connection declarations form a reviewable "
                "storyline topology rather than a flat list."
            ),
            "entry_storyline_ids": copy.deepcopy(
                architecture["entry_storyline_ids"]
            ),
            "main_storyline_id": architecture["main_storyline_id"],
            "terminal_storyline_ids": copy.deepcopy(
                architecture["terminal_storyline_ids"]
            ),
            "decision_ids": copy.deepcopy(
                architecture["development_decisions"]
            ),
        }
        storyline_connection_reviews = [
            {
                "connection_id": item["id"],
                "status": "pass",
                "finding": (
                    f"{item['transferred_obligations']} "
                    f"{item['resulting_state']} The declared event visibly "
                    "moves obligations between the participating lines."
                ),
                "connection_type": item["connection_type"],
                "event_id": item["event_id"],
                "incoming_storyline_ids": copy.deepcopy(
                    item["incoming_storyline_ids"]
                ),
                "outgoing_storyline_ids": copy.deepcopy(
                    item["outgoing_storyline_ids"]
                ),
                "decision_ids": copy.deepcopy(
                    item["development_decisions"]
                ),
            }
            for item in architecture["connection_points"]
        ]
        major_event_reviews = [
            {
                "event_id": item["id"],
                "status": "pass",
                "finding": (
                    f"{item['definition']} The linked action, complication, "
                    "decisive state change, participants, environments and causal "
                    "predecessors form an executable major event without fixing scenes."
                ),
                "storyline_ids": copy.deepcopy(item["storyline_ids"]),
                "unit_ids": copy.deepcopy(item["unit_ids"]),
                "environment_ids": copy.deepcopy(item["environment_ids"]),
                "participant_ids": copy.deepcopy(item["participant_ids"]),
                "source_coverage_ids": [
                    coverage["id"]
                    for coverage in conception["story"][
                        "event_source_coverage"
                    ]
                    if item["id"] in coverage["major_event_ids"]
                ],
                "decision_ids": copy.deepcopy(item["development_decisions"]),
            }
            for item in conception["story"]["major_events"]
        ]
        character_demand_reviews = [
            {
                "demand_id": item["id"],
                "category": item["category"],
                "status": "pass",
                "finding": (
                    f"{item['story_function']} {item['omission_consequence']} "
                    "The trigger, criticality, named-profile disposition, source "
                    "subjects and downstream boundary prove that this required "
                    "human responsibility was discovered before character design."
                ),
                "resolution": item["resolution"],
                "profile_id": item["profile_id"],
                "decision_ids": copy.deepcopy(
                    item["development_decisions"]
                ),
            }
            for item in demands
        ]
        character_profile_reviews = [
            {
                "character_id": item["id"],
                "importance": item["importance"],
                "status": "pass",
                "finding": (
                    f"{item['story_function']} {item['surface_goal']} "
                    "The profile binds role, pressure behavior, agency, arc, "
                    "storyline duties and downstream freedom in one canonical record."
                ),
                "decision_ids": copy.deepcopy(
                    item["development_decisions"]
                ),
            }
            for item in profiles
        ]
        relationship_edge_reviews = [
            {
                "relationship_id": item["id"],
                "source_id": item["source_id"],
                "target_id": item["target_id"],
                "status": "pass",
                "finding": (
                    f"{item['shared_history']} {item['conflict']} "
                    "This canonical edge carries alignment, leverage, information "
                    "asymmetry, change, storyline duties and unit evidence."
                ),
                "decision_ids": copy.deepcopy(
                    item["development_decisions"]
                ),
            }
            for item in relationships
        ]
        relationship_network_reviews = []
        adjacency = {item["id"]: [] for item in profiles}
        for edge in relationships:
            adjacency[edge["source_id"]].append(edge["target_id"])
            adjacency[edge["target_id"]].append(edge["source_id"])
        for character in [
            item for item in profiles if item["importance"] == "core"
        ]:
            distances = {character["id"]: 0}
            queue = [character["id"]]
            while queue:
                current = queue.pop(0)
                for neighbor in adjacency[current]:
                    if neighbor in distances:
                        continue
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)
            max_depth = max(distances.values())
            layer_character_ids = {
                str(depth): [
                    item["id"]
                    for item in profiles
                    if distances.get(item["id"]) == depth
                ]
                for depth in range(1, max_depth + 1)
            }
            component_ids = set(distances)
            relationship_network_reviews.append(
                {
                    "character_id": character["id"],
                    "status": "pass",
                    "finding": (
                        "The core character reaches three continuous person-to-person "
                        "graph depths; every extended person has an independent "
                        "definition, goal and choice, while every edge carries "
                        "conflict, leverage, information asymmetry and change."
                    ),
                    "max_depth": max_depth,
                    "layer_character_ids": layer_character_ids,
                    "profiled_character_ids": [
                        item["id"]
                        for item in profiles
                        if item["id"] != character["id"]
                        and item["id"] in component_ids
                    ],
                    "relationship_ids": [
                        edge["id"]
                        for edge in relationships
                        if edge["source_id"] in component_ids
                        and edge["target_id"] in component_ids
                    ],
                }
            )
        d1_packet = json.loads(
            self.d1_completion.read_text(encoding="utf-8")
        )
        run_state = (
            self.d1_completion.parent / d1_packet["run_state"]["path"]
        ).resolve()
        return {
            "schema_version": "1.0",
            "harness": "novel-conception-interview",
            "run_id": map_data["run_id"],
            "stage": "R1",
            "status": "ready",
            "input_gate": {
                "run_state": relative_reference(
                    self.package_dir, run_state
                ),
                "v1_completion": relative_reference(
                    self.package_dir, self.root / "v1-completion.json"
                ),
                "v2_completion": relative_reference(
                    self.package_dir, self.root / "v2-completion.json"
                ),
                "d1_completion": relative_reference(
                    self.package_dir, self.d1_completion
                ),
            },
            "reviewer": {
                "id": "independent-reviewer-01",
                "role": "independent_developer",
                "assurance": "role_separated_execution",
                "evidence_scope": "d1_package_only",
                "method": (
                    "Revalidate the package, inspect every derivation, then "
                    "perform all eight handoff tasks using only the D1 package."
                ),
            },
            "control_area_reviews": area_reviews,
            "conception_reviews": conception_reviews,
            "cross_domain_checks": cross_checks,
            "world_model_reviews": world_model_reviews,
            "major_event_reviews": major_event_reviews,
            "storyline_reviews": storyline_reviews,
            "storyline_demand_reviews": storyline_demand_reviews,
            "storyline_architecture_review": storyline_architecture_review,
            "storyline_connection_reviews": storyline_connection_reviews,
            "melody_line_reviews": [
                {
                    "melody_line_id": item["id"],
                    "status": "pass",
                    "finding": (
                        f"{item['title']} only modulates existing event anchors "
                        "and remains removable without changing rescue causality, "
                        "resolution, viewpoint authority, or decisive evidence."
                    ),
                    "anchor_event_ids": item["anchor_event_ids"],
                    "required_for_causality": item[
                        "required_for_causality"
                    ],
                    "required_for_resolution": item[
                        "required_for_resolution"
                    ],
                    "new_pov_allowed": item["new_pov_allowed"],
                    "carries_decisive_information": item[
                        "carries_decisive_information"
                    ],
                    "decision_ids": item["development_decisions"],
                }
                for item in map_data["conception"]["story"].get(
                    "melody_lines", []
                )
            ],
            "character_demand_reviews": character_demand_reviews,
            "character_profile_reviews": character_profile_reviews,
            "relationship_edge_reviews": relationship_edge_reviews,
            "relationship_network_reviews": relationship_network_reviews,
            "development_gap_reviews": gap_reviews,
            "design_decision_reviews": decision_reviews,
            "derivation_reviews": derivation_reviews,
            "subject_ids": units,
            "tasks": [
                {
                    "id": task_id,
                    "status": "pass",
                    "response": response,
                    "evidence_ids": [first_control, first_unit],
                }
                for task_id, response in task_responses.items()
            ],
            "open_item_reviews": open_reviews,
            "findings": [],
        }

    def write_review_data(self) -> None:
        write_json(self.package_dir / "review-data.json", self.review_data)
        reviewer = self.review_data.get("reviewer", {})
        workspace = self.package_dir / ".test-r1-generation"
        if workspace.exists():
            shutil.rmtree(workspace)
        original_thread = os.environ.get("CODEX_THREAD_ID")
        d1_thread = json.loads(
            (self.d1.root / "execution-record.json").read_text(encoding="utf-8")
        )["thread_id"]
        test_thread = (
            "00000000-0000-4000-8000-000000000002"
            if d1_thread != "00000000-0000-4000-8000-000000000002"
            else "00000000-0000-4000-8000-000000000003"
        )
        os.environ["CODEX_THREAD_ID"] = test_thread
        r1_generation_session.begin_session(
            workspace,
            run_id=self.review_data["run_id"],
            executor_id=reviewer.get("id", "independent-reviewer-01"),
            method=(
                "Revalidate the complete D1 execution package, independently "
                "review the world, story and character conception, inspect all "
                "derivations, and perform the eight handoff tasks from D1 only."
            ),
            input_gate=self.review_data["input_gate"],
            upstream_execution_record=self.d1.root / "execution-record.json",
        )
        phase_values = (
            {
                "run_id": self.review_data["run_id"],
                "control_area_reviews": self.review_data["control_area_reviews"],
                "conception_reviews": self.review_data["conception_reviews"],
                "world_model_reviews": self.review_data["world_model_reviews"],
                "major_event_reviews": self.review_data["major_event_reviews"],
                "storyline_reviews": self.review_data["storyline_reviews"],
                "storyline_demand_reviews": self.review_data[
                    "storyline_demand_reviews"
                ],
                "storyline_architecture_review": self.review_data[
                    "storyline_architecture_review"
                ],
                "storyline_connection_reviews": self.review_data[
                    "storyline_connection_reviews"
                ],
                "melody_line_reviews": self.review_data[
                    "melody_line_reviews"
                ],
            },
            {
                "run_id": self.review_data["run_id"],
                "cross_domain_checks": self.review_data["cross_domain_checks"],
                "design_decision_reviews": self.review_data[
                    "design_decision_reviews"
                ],
            },
            {
                "run_id": self.review_data["run_id"],
                "subject_ids": self.review_data["subject_ids"],
                "tasks": self.review_data["tasks"],
            },
            self.review_data,
        )
        phase_source = self.package_dir / ".test-r1-phase.json"
        for phase, value in zip(r1_generation_session.PHASES, phase_values):
            write_json(phase_source, value)
            r1_generation_session.submit_phase(
                workspace,
                phase=phase,
                artifact=phase_source,
                summary=(
                    f"Synthetic independent regression completed {phase} with "
                    "D1-only evidence and a review-model-bound phase artifact."
                ),
            )
        phase_source.unlink()
        r1_generation_session.seal_into_package(workspace, self.package_dir)
        shutil.rmtree(workspace)
        if original_thread is None:
            os.environ.pop("CODEX_THREAD_ID", None)
        else:
            os.environ["CODEX_THREAD_ID"] = original_thread
        R1_EXECUTION_RECORD.write_record(self.package_dir, self.review_data)

    def validate(self, *, write: bool = False) -> subprocess.CompletedProcess:
        command = [sys.executable, str(R1_VALIDATOR), str(self.package_dir)]
        if write:
            command.append("--write-validation")
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=120,
        )

    def write_approval(self) -> Path:
        approval = self.package_dir / "author-approval.json"
        review = self.package_dir / "conception-review.md"
        write_json(
            approval,
            {
                "harness": "novel-conception-interview",
                "run_id": self.review_data["run_id"],
                "approval_scope": "R1",
                "decision": "approved",
                "record_assurance": "self_recorded",
                "review_brief": relative_reference(
                    approval.parent, review
                ),
                "approval_record": {
                    "event_seq": 1,
                    "text": (
                        "The author explicitly approves this conception review "
                        "for entry into development."
                    ),
                },
                "unresolved_items": [],
            },
        )
        return approval


class ConceptionReviewerTests(unittest.TestCase):
    def make_package(
        self,
        directory: str,
        *,
        with_open_item: bool = False,
        with_melody_line: bool = False,
    ) -> GenericR1Package:
        return GenericR1Package(
            Path(directory),
            with_open_item=with_open_item,
            with_melody_line=with_melody_line,
        )

    def test_ready_review_package_is_deterministic_and_manifest_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            first = package.validate(write=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            expected = {
                name: (package.package_dir / name).read_bytes()
                for name in (
                    "novel-design-brief.md",
                    "conception-review.md",
                    "independent-handoff.json",
                )
            }
            second = package.validate(write=True)
            self.assertEqual(
                second.returncode, 0, second.stdout + second.stderr
            )
            self.assertEqual(
                expected,
                {
                    name: (package.package_dir / name).read_bytes()
                    for name in expected
                },
            )
            canonical = package.validate()
            self.assertEqual(
                canonical.returncode, 0, canonical.stdout + canonical.stderr
            )

    def test_official_independent_entry_executes_and_seals_ready_review(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            d1_record_path = package.d1.root / "execution-record.json"
            d1_record = json.loads(
                d1_record_path.read_text(encoding="utf-8")
            )
            r1_thread = (
                "00000000-0000-4000-8000-000000000012"
                if d1_record["thread_id"]
                != "00000000-0000-4000-8000-000000000012"
                else "00000000-0000-4000-8000-000000000013"
            )
            env = dict(os.environ)
            env["CODEX_THREAD_ID"] = r1_thread
            input_gate = package.package_dir / ".official-input-gate.json"
            write_json(input_gate, package.review_data["input_gate"])
            workspace = package.root / "official-r1-workspace"
            commands = [
                [
                    sys.executable,
                    str(R1_MANAGER),
                    "begin",
                    str(input_gate),
                    str(d1_record_path),
                    str(workspace),
                    "--run-id",
                    package.review_data["run_id"],
                    "--executor-id",
                    package.review_data["reviewer"]["id"],
                    "--method",
                    (
                        "Independently challenge the D1 world, story, character, "
                        "derivations, and handoff tasks using D1-only evidence."
                    ),
                ]
            ]
            phase_values = (
                {
                    "run_id": package.review_data["run_id"],
                    "control_area_reviews": package.review_data[
                        "control_area_reviews"
                    ],
                    "conception_reviews": package.review_data[
                        "conception_reviews"
                    ],
                    "world_model_reviews": package.review_data[
                        "world_model_reviews"
                    ],
                    "major_event_reviews": package.review_data[
                        "major_event_reviews"
                    ],
                    "storyline_reviews": package.review_data[
                        "storyline_reviews"
                    ],
                    "storyline_demand_reviews": package.review_data[
                        "storyline_demand_reviews"
                    ],
                    "storyline_architecture_review": package.review_data[
                        "storyline_architecture_review"
                    ],
                    "storyline_connection_reviews": package.review_data[
                        "storyline_connection_reviews"
                    ],
                    "melody_line_reviews": package.review_data[
                        "melody_line_reviews"
                    ],
                },
                {
                    "run_id": package.review_data["run_id"],
                    "cross_domain_checks": package.review_data[
                        "cross_domain_checks"
                    ],
                    "design_decision_reviews": package.review_data[
                        "design_decision_reviews"
                    ],
                },
                {
                    "run_id": package.review_data["run_id"],
                    "subject_ids": package.review_data["subject_ids"],
                    "tasks": package.review_data["tasks"],
                },
                package.review_data,
            )
            phase_source = package.package_dir / ".official-r1-phase.json"
            for phase, value in zip(r1_generation_session.PHASES, phase_values):
                write_json(phase_source, value)
                commands.append(
                    [
                        sys.executable,
                        str(R1_MANAGER),
                        "submit",
                        str(workspace),
                        phase,
                        str(phase_source),
                        "--summary",
                        (
                            f"Official independent run completed {phase} with "
                            "D1-grounded evidence and a committed review result."
                        ),
                    ]
                )
            for command in commands:
                process = subprocess.run(
                    command,
                    env=env,
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
                    str(R1_EXECUTOR),
                    str(workspace),
                    str(package.package_dir),
                ],
                env=env,
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

    def test_standalone_renderer_never_emits_authoritative_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            render = subprocess.run(
                [
                    sys.executable,
                    str(R1_RENDERER),
                    str(package.package_dir),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(render.returncode, 0, render.stdout + render.stderr)
            self.assertTrue(
                (package.package_dir / "novel-design-brief.md").is_file()
            )
            self.assertTrue(
                (package.package_dir / "conception-review.md").is_file()
            )
            for filename in (
                "independent-handoff.json",
                "return-package.json",
                "next-run-state.json",
            ):
                self.assertFalse((package.package_dir / filename).exists())
            validated = package.validate(write=True)
            self.assertEqual(
                validated.returncode,
                0,
                validated.stdout + validated.stderr,
            )
            self.assertTrue(
                (package.package_dir / "independent-handoff.json").is_file()
            )
            rerender = subprocess.run(
                [
                    sys.executable,
                    str(R1_RENDERER),
                    str(package.package_dir),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(
                rerender.returncode, 0, rerender.stdout + rerender.stderr
            )
            self.assertFalse(
                (package.package_dir / "independent-handoff.json").exists()
            )

    def test_ready_package_survives_complete_tree_relocation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir()
            package = self.make_package(str(source))
            self.assertEqual(package.validate(write=True).returncode, 0)
            relocated = root / "relocated"
            shutil.copytree(source, relocated)
            process = subprocess.run(
                [
                    sys.executable,
                    str(R1_VALIDATOR),
                    str(relocated / "r1"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=120,
            )
            self.assertEqual(
                process.returncode, 0, process.stdout + process.stderr
            )

    def test_hand_edited_ndb_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            self.assertEqual(package.validate(write=True).returncode, 0)
            path = package.package_dir / "novel-design-brief.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nInvented fact.\n",
                encoding="utf-8",
            )
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("stale or hand-edited", process.stdout)

    def test_ndb_exposes_complete_unit_development_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            process = package.validate(write=True)
            self.assertEqual(
                process.returncode, 0, process.stdout + process.stderr
            )
            ndb = (
                package.package_dir / "novel-design-brief.md"
            ).read_text(encoding="utf-8")
            unit = package.d1.data["units"][0]
            self.assertIn(unit["purpose"], ndb)
            self.assertIn(f"- POV：`{unit['pov']}`", ndb)
            self.assertIn("- 信息责任：", ndb)
            self.assertIn("- 世界约束：", ndb)
            self.assertIn("- 因果节点：", ndb)
            self.assertIn("- 规模：", ndb)
            self.assertIn("## 1. 小说世界设定", ndb)
            self.assertIn("## 2. 小说故事线设定", ndb)
            self.assertIn("### 故事发展阶段", ndb)
            self.assertIn("## 3. 小说人物设定", ndb)
            self.assertIn("- 信息限制：", ndb)
            self.assertNotIn("- 信息限制：—", ndb)

    def test_ready_review_requires_all_three_conception_reviews(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["conception_reviews"] = package.review_data[
                "conception_reviews"
            ][1:]
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "conception_reviews must exactly cover",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_world_facet_and_system(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["world_model_reviews"].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "exactly cover all world facets, systems, environments and "
                "event-environment requirements",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_storyline(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["storyline_reviews"].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "exactly cover all D1 storylines",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_storyline_demand(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["storyline_demand_reviews"].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "must exactly cover all D1 storyline demands",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_storyline_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["storyline_connection_reviews"].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "must exactly cover all D1 storyline connections",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_optional_melody_line(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(
                directory, with_melody_line=True
            )
            ready = package.validate(write=True)
            self.assertEqual(
                ready.returncode, 0, ready.stdout + ready.stderr
            )
            package.review_data["melody_line_reviews"].clear()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "melody_line_reviews must exactly cover",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_major_event(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["major_event_reviews"].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "exactly cover all D1 major events",
                process.stdout + process.stderr,
            )

    def test_major_event_review_must_reverse_check_event_source_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["major_event_reviews"][0][
                "source_coverage_ids"
            ] = []
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "source_coverage_ids do not match D1",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_character_demand(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["character_demand_reviews"].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "exactly cover the D1 demand register",
                process.stdout + process.stderr,
            )

    def test_ready_review_cannot_redirect_a_character_demand(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["character_demand_reviews"][0][
                "profile_id"
            ] = "CHAR-004"
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "reviewed profile_id does not match D1",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_character_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["character_profile_reviews"].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "exactly cover canonical profiles",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_relationship_edge(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["relationship_edge_reviews"].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "exactly cover canonical edges",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_each_three_depth_character_network(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["relationship_network_reviews"] = []
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "exactly cover core characters",
                process.stdout + process.stderr,
            )

    def test_ready_review_recomputes_character_graph_depth(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["relationship_network_reviews"][0][
                "layer_character_ids"
            ]["2"] = ["ROLE-L1"]
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "layer_character_ids do not match",
                process.stdout + process.stderr,
            )

    def test_ready_review_rejects_declared_max_depth_without_graph_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["relationship_network_reviews"][0][
                "max_depth"
            ] = 4
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "max_depth must match the recomputed",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_all_extended_character_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["relationship_network_reviews"][0][
                "profiled_character_ids"
            ].pop()
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "profiled_character_ids must exactly cover",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_every_autonomous_design_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["design_decision_reviews"] = []
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "design_decision_reviews must exactly cover",
                process.stdout + process.stderr,
            )

    def test_design_decision_review_requires_all_six_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["design_decision_reviews"][0]["dimensions"].pop(
                "author_boundary"
            )
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "dimensions must exactly cover",
                process.stdout + process.stderr,
            )

    def test_ready_review_requires_bound_autonomous_execution_record(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            path = package.package_dir / "execution-record.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["model"]["sha256"] = "0" * 64
            write_json(path, record)
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "does not bind the current review-data.json",
                process.stdout + process.stderr,
            )

    def test_ready_review_rejects_placeholder_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["world_model_reviews"][0]["finding"] = (
                "Generic placeholder finding that merely states the field exists "
                "without examining any story-specific consequence or boundary."
            )
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("content-specificity", process.stdout)

    def test_ready_review_rejects_ungrounded_template_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["world_model_reviews"][0]["finding"] = (
                "This subject defines relevant permissions, limits, costs, "
                "failure behavior, and downstream freedom at sufficient depth."
            )
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("lacks story-grounded terms", process.stdout)

    def test_cross_domain_challenge_must_use_its_target_d1_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["cross_domain_checks"]["character_agency"][
                "finding"
            ] = (
                "The indexed record passes a formal completeness inspection "
                "under the currently declared review procedure."
            )
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "semantic challenge is not grounded in its target D1 fields",
                process.stdout,
            )

    def test_cross_domain_pass_cannot_hide_detected_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            assertion = package.review_data["cross_domain_checks"][
                "world_causality"
            ]["assertions"][0]
            assertion["failure_found"] = True
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "failure_found must be false",
                process.stdout + process.stderr,
            )

    def test_cross_domain_pass_cannot_use_an_opposite_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["cross_domain_checks"]["world_causality"][
                "finding"
            ] = (
                "The lighthouse signal, harbor gate, and ferry sequence "
                "contradict each other and cannot support a coherent development."
            )
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "finding reports an unresolved failure but status is pass",
                process.stdout + process.stderr,
            )

    def test_cross_domain_assertion_must_bind_current_d1_field(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            evidence = package.review_data["cross_domain_checks"][
                "world_causality"
            ]["assertions"][0]["field_evidence"][0]
            evidence["value_sha256"] = "0" * 64
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "does not bind the current D1 field",
                process.stdout + process.stderr,
            )

    def test_cross_domain_assertion_must_discuss_bound_value(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            assertion = package.review_data["cross_domain_checks"][
                "world_causality"
            ]["assertions"][0]
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
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn(
                "assertion is not grounded in bound D1 values",
                process.stdout + process.stderr,
            )

    def test_repeated_handoff_responses_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            copied = (
                "The package is complete because every required field exists and "
                "the cited evidence is available for downstream development."
            )
            for task in package.review_data["tasks"]:
                task["response"] = copied
            package.write_review_data()
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("handoff task responses", process.stdout)

    def test_generation_phase_rejects_unknown_d1_evidence_ids(self):
        with self.assertRaisesRegex(
            ValueError,
            "outside the D1 evidence set",
        ):
            r1_generation_session.validate_phase_evidence_ids(
                {
                    "tasks": [
                        {
                            "id": "promise",
                            "evidence_ids": ["OPEN-ITEM-NOT-TASK-EVIDENCE"],
                        }
                    ]
                },
                phase="handoff-test",
                task_ids={"CTL-001", "U01"},
                finding_ids={"CTL-001", "U01", "OPEN-ITEM-NOT-TASK-EVIDENCE"},
            )

    def test_r1_session_rejects_same_codex_task_as_d1(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            d1_record = json.loads(
                (package.d1.root / "execution-record.json").read_text(
                    encoding="utf-8"
                )
            )
            original = os.environ.get("CODEX_THREAD_ID")
            os.environ["CODEX_THREAD_ID"] = d1_record["thread_id"]
            workspace = Path(directory) / "same-thread-r1"
            try:
                with self.assertRaisesRegex(RuntimeError, "different Codex task"):
                    r1_generation_session.begin_session(
                        workspace,
                        run_id=package.review_data["run_id"],
                        executor_id="same-thread-reviewer",
                        method=(
                            "Attempt a complete independent review while using "
                            "the same task identity as the upstream D1 execution."
                        ),
                        input_gate=package.review_data["input_gate"],
                        upstream_execution_record=(
                            package.d1.root / "execution-record.json"
                        ),
                    )
            finally:
                if original is None:
                    os.environ.pop("CODEX_THREAD_ID", None)
                else:
                    os.environ["CODEX_THREAD_ID"] = original

    def test_r1_generation_phase_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            phase = (
                package.package_dir
                / "generation-evidence"
                / "02-semantic-challenges.json"
            )
            phase.write_text("{}\n", encoding="utf-8")
            process = package.validate()
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("artifact hash is invalid", process.stdout)

    def test_absolute_input_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            reference = package.review_data["input_gate"]["d1_completion"]
            reference["path"] = str(
                (package.package_dir / reference["path"]).resolve()
            )
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("not a hash-bound reference", process.stdout)
            self.assertIn('"verdict": "blocked"', process.stdout)

    def test_revise_status_requires_a_revise_finding(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["status"] = "revise"
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("status must match", process.stdout)
            self.assertFalse(
                (package.package_dir / "independent-handoff.json").exists()
            )

    def test_revise_finding_produces_actionable_report_without_pass_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            control_id = package.d1.data["control_points"][0]["id"]
            package.review_data["status"] = "revise"
            package.review_data["findings"] = [
                {
                    "id": "FND-REV-001",
                    "severity": "revise",
                    "owner": "D1",
                    "problem": "The development-map projection omits a required local field.",
                    "evidence_ids": [control_id],
                    "required_action": "Repair the D1 projection and rerun R1.",
                }
            ]
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            result = json.loads(process.stdout)
            self.assertEqual(result["verdict"], "revise")
            report = (
                package.package_dir / "conception-review.md"
            ).read_text(encoding="utf-8")
            self.assertIn("FND-REV-001", report)
            self.assertFalse(
                (package.package_dir / "independent-handoff.json").exists()
            )
            self.assertFalse(
                (package.package_dir / "package-manifest.json").exists()
            )

    def test_upstream_control_owner_cannot_bypass_return_as_revise(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            control_id = package.d1.data["control_points"][0]["id"]
            package.review_data["status"] = "revise"
            package.review_data["findings"] = [
                {
                    "id": "FND-REV-UPSTREAM",
                    "severity": "revise",
                    "owner": "I4",
                    "problem": "A confirmed causal control requires a new decision.",
                    "evidence_ids": [control_id],
                    "required_action": "Return the decision to its control owner.",
                }
            ]
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            result = json.loads(process.stdout)
            self.assertEqual(result["verdict"], "revise")
            self.assertTrue(
                any(
                    "revise finding owner must be D1 or R1" in error
                    for error in result["errors"]
                )
            )
            self.assertFalse(
                (package.package_dir / "return-package.json").exists()
            )
            self.assertFalse(
                (package.package_dir / "independent-handoff.json").exists()
            )

    def test_blocked_finding_generates_structured_return_and_next_state(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            control_id = package.d1.data["control_points"][0]["id"]
            package.review_data["status"] = "blocked"
            package.review_data["findings"] = [
                {
                    "id": "FND-BLK-001",
                    "severity": "blocked",
                    "owner": "I4",
                    "problem": "Two confirmed causal controls require incompatible ordering.",
                    "evidence_ids": [control_id],
                    "required_action": "Return to I4 for one authoritative causal order.",
                }
            ]
            package.review_data["return_request"] = {
                "finding_ids": ["FND-BLK-001"],
                "target_stage": "I4",
                "requested_decision": (
                    "Choose the authoritative order for the conflicting causes."
                ),
                "affected_artifacts": ["causal-storyline.md"],
            }
            state_reference = package.review_data["input_gate"]["run_state"]
            current_state_path = (
                package.package_dir / state_reference["path"]
            ).resolve()
            current_state_before = current_state_path.read_bytes()
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            result = json.loads(process.stdout)
            self.assertEqual(result["verdict"], "blocked")
            return_path = package.package_dir / "return-package.json"
            state_path = package.package_dir / "next-run-state.json"
            self.assertTrue(return_path.is_file())
            self.assertTrue(state_path.is_file())
            return_data = json.loads(return_path.read_text(encoding="utf-8"))
            next_state = json.loads(state_path.read_text(encoding="utf-8"))
            current_state = json.loads(
                current_state_path.read_text(encoding="utf-8")
            )
            self.assertEqual(return_data["origin_stage"], "R1")
            self.assertEqual(return_data["target_stage"], "I4")
            self.assertEqual(
                next_state["active_return"],
                {
                    "path": "return-package.json",
                    "sha256": digest_file(return_path),
                },
            )
            self.assertEqual(current_state_path.read_bytes(), current_state_before)
            for stage, old_reference in current_state.get(
                "current_interview_completions", {}
            ).items():
                new_reference = next_state[
                    "current_interview_completions"
                ][stage]
                self.assertEqual(
                    (
                        current_state_path.parent / old_reference["path"]
                    ).resolve(),
                    (
                        state_path.parent / new_reference["path"]
                    ).resolve(),
                )
                self.assertEqual(
                    old_reference["sha256"], new_reference["sha256"]
                )
            self.assertFalse(
                (package.package_dir / "independent-handoff.json").exists()
            )
            self.assertFalse(
                (package.package_dir / "package-manifest.json").exists()
            )
            canonical = package.validate()
            self.assertNotEqual(canonical.returncode, 0)
            self.assertEqual(
                json.loads(canonical.stdout),
                json.loads(
                    (package.package_dir / "validation.json").read_text(
                        encoding="utf-8"
                    )
                ),
            )

    def test_blocked_return_must_name_target_canonical_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            control_id = package.d1.data["control_points"][0]["id"]
            package.review_data["status"] = "blocked"
            package.review_data["findings"] = [
                {
                    "id": "FND-BLK-ARTIFACT",
                    "severity": "blocked",
                    "owner": "I4",
                    "problem": "A confirmed causal control requires a new decision.",
                    "evidence_ids": [control_id],
                    "required_action": "Return to I4 for one causal decision.",
                }
            ]
            package.review_data["return_request"] = {
                "finding_ids": ["FND-BLK-ARTIFACT"],
                "target_stage": "I4",
                "requested_decision": (
                    "Choose the authoritative causal control before continuing."
                ),
                "affected_artifacts": ["unrelated-placeholder.txt"],
            }
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            result = json.loads(process.stdout)
            self.assertEqual(result["verdict"], "blocked")
            self.assertTrue(
                any(
                    "must include causal-storyline.md for I4" in error
                    for error in result["errors"]
                )
            )
            self.assertFalse(
                (package.package_dir / "return-package.json").exists()
            )
            self.assertFalse(
                (package.package_dir / "next-run-state.json").exists()
            )

    def test_local_owner_cannot_escalate_to_upstream_blocked_return(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            control_id = package.d1.data["control_points"][0]["id"]
            package.review_data["status"] = "blocked"
            package.review_data["findings"] = [
                {
                    "id": "FND-BLK-LOCAL",
                    "severity": "blocked",
                    "owner": "D1",
                    "problem": "A local development-map field requires repair.",
                    "evidence_ids": [control_id],
                    "required_action": "Repair the local D1 projection and revalidate.",
                }
            ]
            package.review_data["return_request"] = {
                "finding_ids": ["FND-BLK-LOCAL"],
                "target_stage": "I4",
                "requested_decision": (
                    "Repair the local development-map projection."
                ),
                "affected_artifacts": ["causal-storyline.md"],
            }
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            result = json.loads(process.stdout)
            self.assertEqual(result["verdict"], "blocked")
            self.assertTrue(
                any(
                    "blocked finding owner must be I0-I5" in error
                    for error in result["errors"]
                )
            )
            self.assertFalse(
                (package.package_dir / "return-package.json").exists()
            )
            self.assertFalse(
                (package.package_dir / "next-run-state.json").exists()
            )

    def test_reviewer_must_differ_from_d1_self_test_executor(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["reviewer"]["id"] = "designer-01"
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("must differ", process.stdout)

    def test_every_derivation_must_be_semantically_reviewed(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["derivation_reviews"].pop()
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("exactly cover all D1 claims", process.stdout)

    def test_every_open_item_must_remain_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory, with_open_item=True)
            package.review_data["open_item_reviews"] = []
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("exactly cover all D1 open items", process.stdout)

    def test_malformed_evidence_arrays_return_revise_not_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["tasks"][0]["evidence_ids"] = [{}]
            package.review_data["cross_domain_checks"]["promise_scope"][
                "unit_ids"
            ] = [{}]
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertNotIn("Traceback", process.stdout + process.stderr)
            self.assertIn('"verdict": "revise"', process.stdout)

    def test_unsupported_review_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            package.review_data["invented_story_answer"] = "not allowed"
            package.write_review_data()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn("unsupported fields", process.stdout)

    def test_gate_failure_emits_only_blocked_report(self):
        with tempfile.TemporaryDirectory() as directory:
            package_dir = Path(directory)
            write_json(
                package_dir / "gate-data.json",
                {
                    "schema_version": "1.0",
                    "harness": "novel-conception-interview",
                    "run_id": "blocked-run",
                    "stage": "R1",
                    "status": "blocked",
                    "input_gate": {},
                    "declared_failures": [
                        {
                            "id": "GATE-001",
                            "problem": "The D1 completion is unavailable.",
                            "evidence": "No current hash-bound D1 packet exists.",
                            "owner": "D1",
                            "required_action": (
                                "Produce and validate the current D1 completion."
                            ),
                        }
                    ],
                },
            )
            process = subprocess.run(
                [
                    sys.executable,
                    str(R1_VALIDATOR),
                    str(package_dir),
                    "--write-validation",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=120,
            )
            self.assertNotEqual(process.returncode, 0)
            self.assertIn('"verdict": "blocked"', process.stdout)
            self.assertTrue((package_dir / "blocked-review-report.md").is_file())
            self.assertFalse((package_dir / "package-manifest.json").exists())
            self.assertFalse((package_dir / "novel-design-brief.md").exists())

    def test_review_and_gate_roots_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            write_json(
                package.package_dir / "gate-data.json",
                {
                    "schema_version": "1.0",
                    "harness": "novel-conception-interview",
                    "run_id": package.review_data["run_id"],
                    "stage": "R1",
                    "status": "blocked",
                    "input_gate": package.review_data["input_gate"],
                    "declared_failures": [
                        {
                            "id": "GATE-DUAL-001",
                            "problem": (
                                "The current D1 completion is unusable."
                            ),
                            "evidence": (
                                "A current hard-gate check rejected the packet."
                            ),
                            "owner": "D1",
                            "required_action": (
                                "Restore and validate the current D1 completion."
                            ),
                        }
                    ],
                },
            )
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            result = json.loads(process.stdout)
            self.assertEqual(result["verdict"], "blocked")
            self.assertIn(
                "review-data.json and gate-data.json must not coexist",
                result["blockers"],
            )
            for filename in (
                "novel-design-brief.md",
                "conception-review.md",
                "independent-handoff.json",
                "return-package.json",
                "next-run-state.json",
                "package-manifest.json",
            ):
                self.assertFalse((package.package_dir / filename).exists())
            self.assertTrue(
                (package.package_dir / "blocked-review-report.md").is_file()
            )

    def test_missing_root_scrubs_stale_authoritative_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            ready = package.validate(write=True)
            self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)
            self.assertTrue(
                (package.package_dir / "independent-handoff.json").is_file()
            )
            (package.package_dir / "review-data.json").unlink()
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            result = json.loads(process.stdout)
            self.assertEqual(result["verdict"], "blocked")
            self.assertIn(
                (
                    "exactly one of review-data.json or gate-data.json "
                    "is required"
                ),
                result["blockers"],
            )
            for filename in (
                "novel-design-brief.md",
                "conception-review.md",
                "independent-handoff.json",
                "return-package.json",
                "next-run-state.json",
                "package-manifest.json",
            ):
                self.assertFalse((package.package_dir / filename).exists())
            self.assertTrue(
                (package.package_dir / "blocked-review-report.md").is_file()
            )

    def test_changed_d1_package_fails_hard_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            self.assertEqual(package.validate(write=True).returncode, 0)
            path = package.root / "development-map.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nTampered.\n",
                encoding="utf-8",
            )
            process = package.validate(write=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn('"verdict": "blocked"', process.stdout)
            self.assertFalse(
                (package.package_dir / "novel-design-brief.md").exists()
            )
            self.assertFalse(
                (package.package_dir / "independent-handoff.json").exists()
            )

    def test_final_approval_produces_consumable_manifest_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            ready = package.validate(write=True)
            self.assertEqual(ready.returncode, 0, ready.stdout + ready.stderr)
            approval = package.write_approval()
            writer = subprocess.run(
                [
                    sys.executable,
                    str(R1_COMPLETION_WRITER),
                    str(package.package_dir),
                    "--session-id",
                    "generic-r1",
                    "--final-approval",
                    str(approval),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=180,
            )
            self.assertEqual(writer.returncode, 0, writer.stdout + writer.stderr)
            completion = package.package_dir / "stage-completion.json"
            packet = json.loads(completion.read_text(encoding="utf-8"))
            self.assertEqual(packet["design_artifact"], "package-manifest.json")
            harness = subprocess.run(
                [sys.executable, str(HARNESS_VALIDATOR), str(completion)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=180,
            )
            self.assertEqual(
                harness.returncode, 0, harness.stdout + harness.stderr
            )

    def test_stale_author_approval_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            self.assertEqual(package.validate(write=True).returncode, 0)
            approval = package.write_approval()
            package.review_data["control_area_reviews"][0][
                "finding"
            ] += " This changes the current review."
            package.write_review_data()
            self.assertEqual(package.validate(write=True).returncode, 0)
            writer = subprocess.run(
                [
                    sys.executable,
                    str(R1_COMPLETION_WRITER),
                    str(package.package_dir),
                    "--session-id",
                    "stale-approval",
                    "--final-approval",
                    str(approval),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=180,
            )
            self.assertNotEqual(writer.returncode, 0)
            self.assertIn("not bound", writer.stdout)

    def test_post_completion_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.make_package(directory)
            self.assertEqual(package.validate(write=True).returncode, 0)
            approval = package.write_approval()
            writer = subprocess.run(
                [
                    sys.executable,
                    str(R1_COMPLETION_WRITER),
                    str(package.package_dir),
                    "--session-id",
                    "tamper-r1",
                    "--final-approval",
                    str(approval),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=180,
            )
            self.assertEqual(writer.returncode, 0, writer.stdout + writer.stderr)
            path = package.package_dir / "independent-handoff.json"
            path.write_text(
                path.read_text(encoding="utf-8") + "\n",
                encoding="utf-8",
            )
            harness = subprocess.run(
                [
                    sys.executable,
                    str(HARNESS_VALIDATOR),
                    str(package.package_dir / "stage-completion.json"),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=180,
            )
            self.assertNotEqual(harness.returncode, 0)
            self.assertIn("has changed", harness.stdout)


if __name__ == "__main__":
    unittest.main()
