from __future__ import annotations

import copy
import importlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


runtime = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
c1 = importlib.import_module("skills.novel-character-system-designer.scripts.run_v2")
t1_test = importlib.import_module(
    "skills.novel-event-timeline-designer.tests.test_v2_runtime"
)
_SHARED_FIXTURE = None


def agent_character_proposal(
    *,
    run_id,
    gate_reference,
    source_artifacts,
    baseline,
    storyline,
    world,
    environment,
    timeline,
):
    """Test-only Agent authors character semantics; production Python never does."""
    maps = c1._c1_maps(storyline, world, environment, timeline)
    slots = sorted(maps["required_slots"])
    slot_to_char = {slot: f"CHR-{index:03d}" for index, slot in enumerate(slots, 1)}
    resolutions = [
        {
            "slot_id": slot,
            "character_id": slot_to_char[slot],
            "demand_ids": sorted(maps["slot_demands"][slot]),
            "event_ids": sorted(maps["slot_events"][slot]),
            "rationale": (
                "".join(
                    f"[DEMAND:{demand_id}:"
                    f"{c1._c1_demand_digest(maps['demands'][demand_id])}]"
                    f"{maps['demands'][demand_id]['responsibility']}[/DEMAND]"
                    for demand_id in sorted(maps["slot_demands"][slot])
                )
                + f" {slot} remains distinct because these duties are compatible."
            ),
        }
        for slot in slots
    ]
    first_event = timeline["major_events"][0]["id"]
    core = slot_to_char[timeline["major_events"][0]["initiator_slot_id"]]
    extras = ["CHR-NET-1", "CHR-NET-2", "CHR-NET-3"]
    all_chars = [*slot_to_char.values(), *extras]
    relations = [
        {
            "id": f"REL-{index}",
            "from_character_id": left,
            "to_character_id": right,
            "function": f"[FUNCTION:{kind}] Maintains a distinct pressure path.",
            "start_state": f"{left} cannot yet rely on {right}.",
            "change_event_ids": [first_event],
            "end_state": f"{left} must account for {right}.",
            "boundaries": ["The relationship cannot erase either party's agency."],
        }
        for index, (left, right, kind) in enumerate(
            (
                (core, extras[0], "direct"),
                (extras[0], extras[1], "institutional"),
                (extras[1], extras[2], "contextual"),
            ),
            1,
        )
    ]
    incident = {character_id: [] for character_id in all_chars}
    for relation in relations:
        for endpoint in ("from_character_id", "to_character_id"):
            character_id = relation[endpoint]
            incident[character_id].append(
                f"[REL:{relation['id']}] The relationship changes available support."
            )
    initiated = {character_id: [] for character_id in all_chars}
    participated = {character_id: [] for character_id in all_chars}
    providers = {character_id: set() for character_id in all_chars}
    capabilities = {character_id: set() for character_id in all_chars}
    for event in timeline["major_events"]:
        event_id = event["id"]
        initiator = slot_to_char[event["initiator_slot_id"]]
        initiated[initiator].append(event_id)
        providers[initiator].update(maps["ledger_providers"].get(event_id, set()))
        capabilities[initiator].add(
            f"[ACTION_SHA256:{runtime.canonical_sha256(event['initiating_action'])}] "
            f"Can initiate {event_id} without changing its result."
        )
        for slot in event["participant_slot_ids"]:
            character_id = slot_to_char[slot]
            participated[character_id].append(event_id)
            capabilities[character_id].add(
                f"[ENV_ACCESS:{event['environment_id']}] Can function in {event['environment_id']}."
            )
        for slot in event["counter_slot_ids"]:
            capabilities[slot_to_char[slot]].add(
                f"[COUNTER_EVENT:{event_id}] Can execute the recorded counter-pressure."
            )
    info_change = timeline["information_changes"][0]
    visible_char = slot_to_char[info_change["visibility_ids"][0]]
    info_event = info_change["event_ids"][0]
    known = (
        f"[KNOWN_AFTER:{info_change['id']}:{info_event}]"
        f"[BEFORE_SHA256:{runtime.canonical_sha256(info_change['before'])}]"
        f"[AFTER_SHA256:{runtime.canonical_sha256(info_change['after'])}] "
        f"After {info_event}, the character knows the recorded change."
    )
    unknown = (
        f"[UNKNOWN_BEFORE:{info_change['id']}:{info_event}]"
        f"[BEFORE_SHA256:{runtime.canonical_sha256(info_change['before'])}]"
        f"[AFTER_SHA256:{runtime.canonical_sha256(info_change['after'])}] "
        f"Before {info_event}, the character does not know the recorded change."
    )
    profiles = []
    for index, character_id in enumerate(all_chars, 1):
        is_core = character_id == core
        character_slots = {
            slot for slot, resolved in slot_to_char.items()
            if resolved == character_id
        }
        character_demands = sorted(
            {
                demand_id
                for slot in character_slots
                for demand_id in maps["slot_demands"][slot]
            }
        )
        demand_blocks = "".join(
            f"[DEMAND:{demand_id}:"
            f"{c1._c1_demand_digest(maps['demands'][demand_id])}]"
            f"{maps['demands'][demand_id]['responsibility']}[/DEMAND]"
            for demand_id in character_demands
        )
        demand_goals = [
            f"[DEMAND_EFFECT:{demand_id}:"
            f"{c1._c1_demand_digest(maps['demands'][demand_id])}:goal] "
            f"Fulfil {maps['demands'][demand_id]['responsibility']} through owned choices."
            for demand_id in character_demands
        ]
        demand_boundaries = [
            f"[TYPE:hard-boundary] [DEMAND_EFFECT:{demand_id}:"
            f"{c1._c1_demand_digest(maps['demands'][demand_id])}:boundary] "
            f"Will not violate the constraints of {maps['demands'][demand_id]['responsibility']}."
            for demand_id in character_demands
        ]
        profile_unknown = unknown if character_id == visible_char else (
            f"[UNKNOWN_BEFORE:{info_change['id']}:{info_event}]"
            f"[BEFORE_SHA256:{runtime.canonical_sha256(info_change['before'])}]"
            f"[AFTER_SHA256:{runtime.canonical_sha256(info_change['after'])}] "
            "This character is outside the visibility change."
        )
        profile_event_ids = sorted(
            {
                event_id
                for slot in character_slots
                for event_id in maps["slot_events"][slot]
            }
        )
        profile_storyline_ids = sorted(
            {
                storyline_id
                for event_id in profile_event_ids
                for storyline_id in maps["events"][event_id]["storyline_ids"]
            }
        )
        profile_environment_ids = sorted(
            {
                maps["events"][event_id]["environment_id"]
                for event_id in profile_event_ids
            }
        )
        profiles.append(
            {
                "id": character_id,
                "name": f"[CLASS:{'core' if is_core else 'support'}] Test Person {index}",
                "story_position": {
                    "narrative_level": "core" if is_core else "support",
                    "entry_function": "Enters when the frozen story first needs this person.",
                    "ongoing_function": "Carries a distinct responsibility through the middle.",
                    "ending_function": "Owns a visible consequence at the end.",
                },
                "activity_participation": {
                    "storyline_ids": profile_storyline_ids,
                    "event_ids": profile_event_ids,
                    "environment_ids": profile_environment_ids,
                    "activity_summary": "Performs the activities assigned by frozen events and relationships.",
                    "causal_contribution": "Changes available information, choices, or consequences.",
                },
                "individual_definition": {
                    "appearance": "Has one stable, recognizable physical or interface presentation.",
                    "personality": "Responds consistently to pressure while retaining a contradiction.",
                    "life_background": "Has a prior life that explains current values without replacing agency.",
                    "occupation_and_daily_life": "Has a concrete occupation and ordinary routine outside plot utility.",
                    "social_circle": "Belongs to a defined private and professional relationship circle.",
                    "embodied_or_interface_constraints": "Can perceive and act only through explicitly defined channels.",
                },
                "story_responsibility": (
                    demand_blocks + " Carries the exact event and relationship duties."
                    if character_id in slot_to_char.values()
                    else "Extends the core network through an irreplaceable relationship function."
                ),
                "goals": (
                    demand_goals
                    if demand_goals
                    else [f"Preserve the consequence assigned to {character_id}."]
                ),
                "values": ["Choices must remain accountable to affected people."],
                "boundaries": [
                    "[TYPE:blind-spot] Under pressure, misses one indirect consequence.",
                    *(
                        demand_boundaries
                        if demand_boundaries
                        else ["[TYPE:hard-boundary] Will not erase another person's agency."]
                    ),
                ],
                "capabilities": sorted(capabilities[character_id]),
                "authorities": sorted(providers[character_id]),
                "information_limits": [profile_unknown],
                "pressure_behavior": "Narrows options, then makes an owned choice.",
                "agency_choices": ["Act now.", "Delay and absorb a larger cost."],
                "non_delegable_choices": ["Accept the consequence of the final decision."],
                "relationship_levers": incident[character_id],
                "arc_direction": "Pressure clarifies the value the character will protect.",
                "forbidden_portrayals": ["Do not replace motive with plot convenience."],
            }
        )
    profile_by_id = {item["id"]: item for item in profiles}
    obligations = c1._c1_obligations(maps, timeline)
    responsibilities = []
    ordered_obligations = sorted(
        obligations.items(), key=c1._c1_obligation_sort_key
    )
    for index, (_, obligation) in enumerate(ordered_obligations, 1):
        character_id = slot_to_char[obligation["slot_id"]]
        evidence = [
            item
            for item in (
                obligation.get("event_id"),
                obligation.get("storyline_id"),
                obligation.get("information_id"),
            )
            if item
        ]
        constraints = [
            f"[DEMAND_SHA256:{demand_id}:"
            f"{c1._c1_demand_digest(maps['demands'][demand_id])}]"
            for demand_id in sorted(
                maps["slot_demands"][obligation["slot_id"]]
            )
        ]
        constraints.append("Must preserve all frozen upstream outcomes.")
        if obligation["kind"] == "decision":
            constraints.extend(
                [
                f"[GOAL_SHA256:{runtime.canonical_sha256(profile_by_id[character_id]['goals'])}]",
                f"[VALUE_SHA256:{runtime.canonical_sha256(profile_by_id[character_id]['values'])}]",
                ]
            )
        responsibilities.append(
            {
                "id": f"ASG-C1-{index:03d}",
                "subject_id": character_id,
                "responsibility": (
                    f"[KIND:{obligation['kind']}][SLOT:{obligation['slot_id']}] "
                    "Own this structural duty without changing the event."
                ),
                "evidence_ids": evidence,
                "constraints": constraints,
            }
        )
    agencies = []
    for index, (character_id, event_ids) in enumerate(
        ((key, value) for key, value in initiated.items() if value), 1
    ):
        duty_digest = runtime.canonical_sha256(
            profile_by_id[character_id]["story_responsibility"]
        )
        chosen = (
            "".join(
                f"[INIT_ACTION:{event_id}:"
                f"{runtime.canonical_sha256(maps['events'][event_id]['initiating_action'])}]"
                for event_id in event_ids
            )
            + f"[DUTY_SHA256:{duty_digest}] "
            + f"Execute the recorded initiating actions for {','.join(event_ids)}."
        )
        agencies.append(
            {
                "id": f"AGY-C1-{index:03d}",
                "character_id": character_id,
                "event_ids": event_ids,
                "available_choices": [chosen, "Refuse and accept the explicit downstream cost."],
                "chosen_action": chosen,
                "cost": (
                    f"[DUTY_SHA256:{duty_digest}] The choice creates an "
                    "accountable personal and relational cost."
                ),
            }
        )
    information = [
        {
            "id": "INFO-C1-001",
            "character_id": visible_char,
            "knows": [known],
            "does_not_know": [unknown],
            "misreads": [],
            "change_event_ids": list(info_change["event_ids"]),
        }
    ]
    profile_by_id[visible_char]["information_limits"] = [unknown]
    arcs = [
        {
            "id": f"ARC-C1-{index:03d}",
            "character_id": agency["character_id"],
            "start_state": "The cost of choosing is not yet personally owned.",
            "pressure_event_ids": list(agency["event_ids"]),
            "choice_event_ids": list(agency["event_ids"]),
            "end_state": "The character owns the consequence without losing the core value.",
            "theme_effect": (
                f"[DUTY_SHA256:{runtime.canonical_sha256(profile_by_id[agency['character_id']]['story_responsibility'])}] "
                "Agency is proved by accountable choice under constraint."
            ),
        }
        for index, agency in enumerate(agencies, 1)
    ]
    storyline_coverage = [
        {
            "id": f"COV-C1-SL-{index:03d}",
            "source_ids": [line_id],
            "realization_ids": sorted(slot_to_char[slot] for slot in maps["line_slots"][line_id]),
            "status": "covered",
            "evidence": (
                "".join(
                    f"[CHAIN:{demand_id}:"
                    f"{c1._c1_demand_digest(maps['demands'][demand_id])}:"
                    f"{slot}:{slot_to_char[slot]}:{line_id}]"
                    for slot in sorted(maps["line_slots"][line_id])
                    for demand_id in sorted(maps["slot_demands"][slot])
                )
                + " Every storyline demand, slot and character is closed."
            ),
        }
        for index, line_id in enumerate(maps["lines"], 1)
    ]
    event_coverage = [
        {
            "id": f"COV-C1-EV-{index:03d}",
            "source_ids": [event_id],
            "realization_ids": sorted(slot_to_char[slot] for slot in maps["event_slots"][event_id]),
            "status": "covered",
            "evidence": (
                "".join(
                    f"[CHAIN:{demand_id}:"
                    f"{c1._c1_demand_digest(maps['demands'][demand_id])}:"
                    f"{slot}:{slot_to_char[slot]}:{event_id}]"
                    for slot in sorted(maps["event_slots"][event_id])
                    for demand_id in sorted(maps["slot_demands"][slot])
                )
                + " Every event demand, slot and character is closed."
            ),
        }
        for index, event_id in enumerate(maps["events"], 1)
    ]
    terminal = {
        item["event_ids"][-1] for item in timeline["storyline_event_sequences"]
    }
    aftermath = [
        {
            "id": f"ASG-C1-AF-{index:03d}",
            "subject_id": slot_to_char[maps["events"][event_id]["initiator_slot_id"]],
            "responsibility": "[KIND:aftermath] Own the terminal consequence.",
            "evidence_ids": [event_id],
            "constraints": ["Do not erase the recorded aftermath."],
        }
        for index, event_id in enumerate(sorted(terminal), 1)
    ]
    core_digest = runtime.canonical_sha256([core])
    decisions = [
        {
            "id": "DEC-C1-CORE",
            "gap": "Select the smallest core set that carries the main-line choices.",
            "options": [
                f"[CORE_EVIDENCE_SHA256:{core_digest}] Select {core}.",
                "Select every participant as core.",
            ],
            "selection": f"[CORE_EVIDENCE_SHA256:{core_digest}] Select {core}.",
            "owner": "C1",
            "authority_basis": "C1 owns character centrality and network design.",
            "compatibility": "The selected character initiates a true main-line event.",
            "impact_ids": [core],
            "cost": "Supporting characters remain non-core while keeping agency.",
            "reversibility": "costly",
            "downstream_freedom": "Scene emphasis remains open.",
            "projection_ids": [core],
        }
    ]
    generated = [
        *[item["id"] for item in decisions],
        *[item["id"] for item in profiles],
        *[item["id"] for item in responsibilities],
        *[item["id"] for item in agencies],
        *[item["id"] for item in information],
        *[item["id"] for item in arcs],
        *[item["id"] for item in relations],
        *[item["id"] for item in storyline_coverage],
        *[item["id"] for item in event_coverage],
        *[item["id"] for item in aftermath],
    ]
    development_freedoms = [
        {
            "id": f"DEV-C1-{index:03d}",
            "subject_ids": [profile["id"]],
            "scope": (
                "Scene-level expression of the character without changing "
                "the canonical responsibility, choice logic, arc, or relationships."
            ),
            "allowed_variations": [
                "Vary concrete gestures, dialogue cadence, and sensory emphasis."
            ],
            "forbidden_changes": [
                "Do not change canonical goals, values, boundaries, choices, or outcomes."
            ],
            "acceptance_checks": [
                "The developed scene remains consistent with the bound character profile."
            ],
            "source_ids": [profile["id"]],
        }
        for index, profile in enumerate(profiles, 1)
    ]
    derivations = [
        {
            "id": f"DRV-C1-{index:03d}",
            "value_sha256": runtime.canonical_sha256(item),
            "source_ids": (
                sorted(
                    {
                        demand_id
                        for slot, resolved in slot_to_char.items()
                        if resolved == item["id"]
                        for demand_id in maps["slot_demands"][slot]
                    }
                )
                if item["id"] in profile_by_id
                and item["id"] in slot_to_char.values()
                else [first_event]
            ),
            "decision_ids": ["DEC-C1-CORE"],
            "projection_ids": [item["id"]],
        }
        for index, item in enumerate([*profiles, *arcs, *relations], 1)
    ]
    locked = [item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_locked"]
    opened = [item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_open"]
    return {
        "schema_version": "2.0",
        "skill": "novel-character-system-designer",
        "stage": "C1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(gate_reference),
        "source_artifacts": copy.deepcopy(source_artifacts),
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": [
                identifier
                for identifier in generated
                if identifier not in set(locked) | set(opened)
            ],
            "downstream_freedom": [
                item["id"] for item in development_freedoms
            ],
            "author_open": opened,
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "character_demands": copy.deepcopy(storyline["character_requirements"]),
        "slot_resolution": resolutions,
        "profiles": profiles,
        "responsibility_matrix": responsibilities,
        "agency_matrix": agencies,
        "information_matrix": information,
        "character_arcs": arcs,
        "relationships": relations,
        "three_layer_networks": [
            {
                "core_character_id": core,
                "layer_1_direct": [extras[0]],
                "layer_2_institutional": [extras[1]],
                "layer_3_contextual": [extras[2]],
                "relationship_ids": [item["id"] for item in relations],
                "story_function": "Extends direct pressure into institutional and contextual consequences.",
            }
        ],
        "storyline_cast_coverage": storyline_coverage,
        "event_cast_coverage": event_coverage,
        "aftermath_responsibility": aftermath,
        "development_freedoms": development_freedoms,
        "open_items": [
            {
                "id": f"OPEN-C1-{index:03d}",
                "question": f"Preserve author-open control {control_id}.",
                "source_ids": [control_id],
                "status": "author_open",
            }
            for index, control_id in enumerate(opened, 1)
        ],
    }


class C1DevelopmentFreedomContractTests(unittest.TestCase):
    def _freedoms(self):
        return [
            {
                "id": "DEV-C1-001",
                "subject_ids": ["CHR-001"],
                "scope": "Scene-level expression under the frozen profile.",
                "allowed_variations": ["Vary gesture and dialogue cadence."],
                "forbidden_changes": ["Do not change goals or outcomes."],
                "acceptance_checks": ["The scene remains profile-consistent."],
                "source_ids": ["CHR-001"],
            },
            {
                "id": "DEV-C1-002",
                "subject_ids": ["CHR-002"],
                "scope": "Scene-level expression under the frozen profile.",
                "allowed_variations": ["Vary gesture and dialogue cadence."],
                "forbidden_changes": ["Do not change goals or outcomes."],
                "acceptance_checks": ["The scene remains profile-consistent."],
                "source_ids": ["CHR-002"],
            },
        ]

    def test_development_freedoms_are_a_phase4_contract(self):
        self.assertIn(
            "development_freedoms",
            c1.PHASE_FIELDS["cross-model-cast-test"],
        )

    def test_development_freedom_validator_accepts_closed_profile_cover(self):
        values = self._freedoms()
        actual = c1._validate_development_freedoms(
            values,
            profile_ids={"CHR-001", "CHR-002"},
            defined_source_ids={"CHR-001", "CHR-002"},
        )
        self.assertEqual(set(actual), {"DEV-C1-001", "DEV-C1-002"})

    def test_development_freedom_validator_rejects_duplicate_id(self):
        values = self._freedoms()
        values[1]["id"] = values[0]["id"]
        with self.assertRaisesRegex(c1.C1Error, "C1_DEV_ID_DUPLICATE"):
            c1._validate_development_freedoms(
                values,
                profile_ids={"CHR-001", "CHR-002"},
                defined_source_ids={"CHR-001", "CHR-002"},
            )

    def test_development_freedom_validator_rejects_missing_profile(self):
        with self.assertRaisesRegex(
            c1.C1Error,
            "C1_DEV_PROFILE_COVERAGE_MISMATCH",
        ):
            c1._validate_development_freedoms(
                self._freedoms()[:1],
                profile_ids={"CHR-001", "CHR-002"},
                defined_source_ids={"CHR-001", "CHR-002"},
            )

    def test_development_freedom_validator_rejects_dangling_source(self):
        values = self._freedoms()
        values[0]["source_ids"] = ["CHR-UNKNOWN"]
        with self.assertRaisesRegex(c1.C1Error, "C1_DEV_SOURCE_DANGLING"):
            c1._validate_development_freedoms(
                values,
                profile_ids={"CHR-001", "CHR-002"},
                defined_source_ids={"CHR-001", "CHR-002"},
            )

    def test_development_freedom_validator_rejects_placeholder(self):
        values = self._freedoms()
        values[0]["scope"] = "TBD"
        with self.assertRaisesRegex(c1.C1Error, "C1_DEV_PLACEHOLDER"):
            c1._validate_development_freedoms(
                values,
                profile_ids={"CHR-001", "CHR-002"},
                defined_source_ids={"CHR-001", "CHR-002"},
            )

    def test_authority_validator_rejects_any_overlap(self):
        with self.assertRaisesRegex(c1.C1Error, "C1_AUTHORITY_CONFLICT"):
            c1._validate_authority_disjoint(
                {
                    "author_locked": ["INT-001"],
                    "autonomous_owned": ["INT-001"],
                    "downstream_freedom": ["DEV-C1-001"],
                    "author_open": [],
                }
            )


class C1SealedUpstreamLogicalPathTests(unittest.TestCase):
    class _SchemaRuntime:
        @staticmethod
        def validate(value, schema_name):
            return None

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.run_id = "run-c1-sealed-upstream"
        self.schema_runtime = self._SchemaRuntime()

    def tearDown(self):
        self.temporary.cleanup()

    def _package(self, stage, logical_root, previous):
        root = self.root / f"physical-{stage}"
        root.mkdir()
        (root / "package-manifest.json").write_text(
            runtime.canonical_json({"stage": stage}), encoding="utf-8"
        )
        (root / "validation.json").write_text(
            runtime.canonical_json({"stage": stage, "verdict": "ready"}),
            encoding="utf-8",
        )
        completion = {
            "schema_version": "2.0",
            "run_id": self.run_id,
            "stage": stage,
            "status": "ready",
            "manifest": {
                "path": f"{logical_root}/package-manifest.json",
                "sha256": runtime.sha256_file(root / "package-manifest.json"),
            },
            "validation": {
                "path": f"{logical_root}/validation.json",
                "sha256": runtime.sha256_file(root / "validation.json"),
            },
            "previous_stage_completions": copy.deepcopy(previous),
        }
        (root / "stage-completion.json").write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )
        return root, {
            "stage": stage,
            "path": f"{logical_root}/stage-completion.json",
            "sha256": runtime.sha256_file(root / "stage-completion.json"),
        }

    def _files(self):
        return {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

    def test_attempt_qualified_extended_and_flat_legacy_paths_are_exact(self):
        b0_root, b0_ref = self._package("B0", "B0", [])
        s1_root, s1_ref = self._package(
            "S1", "workspaces/S1-attempt-03/package", []
        )
        w1_root, w1_ref = self._package(
            "W1", "workspaces/W1-attempt-04/package", [s1_ref]
        )
        before = self._files()
        cases = (
            (b0_root, b0_ref, "B0", []),
            (s1_root, s1_ref, "S1", []),
            (w1_root, w1_ref, "W1", [s1_ref]),
        )
        for package_root, reference, stage, previous in cases:
            physical_root = package_root
            if os.name == "nt" and stage == "W1":
                physical_root = Path("\\\\?\\" + str(package_root.resolve()))
            with self.subTest(stage=stage):
                self.assertEqual(
                    reference,
                    c1._sealed_upstream_reference(
                        physical_root,
                        reference,
                        stage=stage,
                        run_id=self.run_id,
                        previous_stage_completions=previous,
                        runtime=self.schema_runtime,
                    ),
                )
        self.assertEqual(before, self._files())

    def test_wrong_path_stage_hash_parent_escape_and_backslash_fail_before_write(self):
        root, reference = self._package(
            "T1", "workspaces/T1-attempt-15/package", []
        )
        before = self._files()
        mutations = {
            "wrong-path": {**reference, "path": "foreign/T1/stage-completion.json"},
            "wrong-stage": {**reference, "stage": "E1"},
            "wrong-hash": {**reference, "sha256": "0" * 64},
            "escape": {**reference, "path": "../T1/stage-completion.json"},
            "backslash": {**reference, "path": "T1\\stage-completion.json"},
        }
        for name, mutated in mutations.items():
            with self.subTest(name=name), self.assertRaises(c1.C1Error):
                c1._sealed_upstream_reference(
                    root,
                    mutated,
                    stage="T1",
                    run_id=self.run_id,
                    previous_stage_completions=[],
                    runtime=self.schema_runtime,
                )
        completion_path = root / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion["manifest"]["path"] = "foreign/package-manifest.json"
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )
        wrong_parent = {
            **reference,
            "sha256": runtime.sha256_file(completion_path),
        }
        with self.assertRaises(c1.C1Error):
            c1._sealed_upstream_reference(
                root,
                wrong_parent,
                stage="T1",
                run_id=self.run_id,
                previous_stage_completions=[],
                runtime=self.schema_runtime,
            )
        # Only this test's deliberate fixture mutation may differ.
        after = self._files()
        self.assertEqual(
            {key: value for key, value in before.items() if not key.endswith("stage-completion.json")},
            {key: value for key, value in after.items() if not key.endswith("stage-completion.json")},
        )

    def test_raw_canonical_and_nested_body_mutations_fail_closed(self):
        root, reference = self._package("S1", "S1/attempt-03", [])
        completion_path = root / "stage-completion.json"
        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        completion_path.write_text(json.dumps(completion, indent=2), encoding="utf-8")
        noncanonical = {**reference, "sha256": runtime.sha256_file(completion_path)}
        with self.assertRaises(c1.C1Error):
            c1._sealed_upstream_reference(
                root,
                noncanonical,
                stage="S1",
                run_id=self.run_id,
                previous_stage_completions=[],
                runtime=self.schema_runtime,
            )
        completion_path.write_text(
            runtime.canonical_json(completion), encoding="utf-8"
        )
        reference["sha256"] = runtime.sha256_file(completion_path)
        nested = self.root / "copied" / "sources" / "S1" / "stage-completion.json"
        nested.parent.mkdir(parents=True)
        nested.write_bytes(completion_path.read_bytes())
        c1._require_embedded_completion(
            nested, reference, code="C1_UPSTREAM_LINEAGE_MISMATCH"
        )
        nested_body = json.loads(nested.read_text(encoding="utf-8"))
        nested_body["run_id"] = "mutated"
        nested.write_text(runtime.canonical_json(nested_body), encoding="utf-8")
        with self.assertRaisesRegex(c1.C1Error, "C1_UPSTREAM_LINEAGE_MISMATCH"):
            c1._require_embedded_completion(
                nested, reference, code="C1_UPSTREAM_LINEAGE_MISMATCH"
            )

    def test_session_and_public_replay_share_exact_gate_selected_lineage(self):
        roots = {}
        references = {}
        previous = {
            "B0": [],
            "S1": [],
            "W1": ["S1"],
            "E1": ["S1", "W1"],
            "T1": ["S1", "W1", "E1"],
        }
        for stage, attempt in (
            ("B0", "01"),
            ("S1", "03"),
            ("W1", "04"),
            ("E1", "13"),
            ("T1", "15"),
        ):
            roots[stage], references[stage] = self._package(
                stage,
                f"{stage}/attempt-{attempt}",
                [references[item] for item in previous[stage]],
            )
        ancestors = {
            "S1": ("B0",),
            "W1": ("B0", "S1"),
            "E1": ("B0", "S1", "W1"),
            "T1": ("B0", "S1", "W1", "E1"),
        }
        for owner, stages in ancestors.items():
            for stage in stages:
                target = roots[owner] / "sources" / stage / "stage-completion.json"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(roots[stage] / "stage-completion.json", target)
        gate = {
            "baseline_completion": references["B0"],
            "upstream_completions": [
                references[stage] for stage in ("S1", "W1", "E1", "T1")
            ],
        }
        expected = tuple(references[stage] for stage in ("B0", "S1", "W1", "E1", "T1"))
        before = self._files()
        self.assertEqual(
            expected,
            c1._gate_selected_upstream_references(
                roots, gate, run_id=self.run_id, runtime=self.schema_runtime
            ),
        )
        public = self.root / "public" / "sources"
        public_roots = {}
        for stage, source in roots.items():
            public_roots[stage] = public / stage
            shutil.copytree(source, public_roots[stage])
        self.assertEqual(
            expected,
            c1._gate_selected_upstream_references(
                public_roots,
                gate,
                run_id=self.run_id,
                runtime=self.schema_runtime,
            ),
        )
        # Verifiers are read-only; only the explicit public fixture copy differs.
        after = self._files()
        self.assertEqual(
            before,
            {key: value for key, value in after.items() if not key.startswith("public/")},
        )


class C1RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        t1_test.T1RuntimeTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        global _SHARED_FIXTURE
        if _SHARED_FIXTURE is not None:
            _SHARED_FIXTURE["upstream"].tearDown()
            _SHARED_FIXTURE = None
        t1_test.T1RuntimeTests.tearDownClass()

    def setUp(self):
        global _SHARED_FIXTURE
        if _SHARED_FIXTURE is not None:
            for name in (
                "upstream", "b0", "s1", "w1", "e1", "t1", "gate",
                "workspace", "package", "inputs", "baseline", "storyline",
                "world", "environment",
            ):
                setattr(self, name, _SHARED_FIXTURE[name])
            self.coordinator = runtime.AutonomousCoordinator.from_snapshot(
                _SHARED_FIXTURE["coordinator_state"],
                _SHARED_FIXTURE["coordinator_reference"],
            )
            self.timeline = copy.deepcopy(_SHARED_FIXTURE["timeline"])
            self.model = copy.deepcopy(_SHARED_FIXTURE["model"])
            return
        self.upstream = t1_test.T1RuntimeTests("test_happy_path_and_exact_package")
        self.upstream.setUp()
        proposal = self.upstream.proposal
        event = proposal["major_events"][0]
        slot = event["participant_slot_ids"][0]
        change = {
            "id": "INFO-T1-C1",
            "subject_id": event["storyline_ids"][0],
            "before": "The character lacks the event result.",
            "after": "The character knows the event result.",
            "event_ids": [event["id"]],
            "visibility_ids": [slot],
        }
        proposal["information_changes"] = [change]
        event["information_changes"] = [change["id"]]
        proposal["authority_partition"]["autonomous_owned"].append(change["id"])
        event_claim = next(
            item
            for item in proposal["derivation_claims"]
            if item["projection_ids"] == [event["id"]]
        )
        event_claim["value_sha256"] = runtime.canonical_sha256(event)
        self.upstream._run_package()
        self.b0 = self.upstream.input_roots["B0"]
        self.s1 = self.upstream.input_roots["S1"]
        self.w1 = self.upstream.input_roots["W1"]
        self.e1 = self.upstream.input_roots["E1"]
        self.t1 = self.upstream.package
        self.coordinator = self.upstream.coordinator
        self.gate = self.coordinator.build_input_gate("C1", "C1/input-gate.json")
        self.workspace = self.upstream.work / "workspace" / "C1"
        self.package = self.upstream.work / "run" / "C1"
        self.inputs = {
            "baseline_package": self.b0,
            "storyline_package": self.s1,
            "world_package": self.w1,
            "environment_package": self.e1,
            "event_package": self.t1,
        }
        self.baseline = self.upstream._read(self.b0 / "author-control-baseline.json")
        self.storyline = self.upstream._read(self.s1 / "storyline-architecture.json")
        self.world = self.upstream._read(self.w1 / "world-model.json")
        self.environment = self.upstream._read(self.e1 / "environment-system.json")
        self.timeline = self.upstream._read(self.t1 / "event-timeline.json")
        self.model = agent_character_proposal(
            run_id=self.baseline["run_id"],
            gate_reference=self.gate.reference,
            source_artifacts=c1._source_artifacts(self.b0, self.s1, self.w1, self.e1, self.t1),
            baseline=self.baseline,
            storyline=self.storyline,
            world=self.world,
            environment=self.environment,
            timeline=self.timeline,
        )
        _SHARED_FIXTURE = {
            name: getattr(self, name)
            for name in (
                "upstream", "b0", "s1", "w1", "e1", "t1", "gate",
                "workspace", "package", "inputs", "baseline", "storyline",
                "world", "environment",
            )
        }
        _SHARED_FIXTURE.update(
            {
                "coordinator_state": self.coordinator.state,
                "coordinator_reference": self.coordinator.state_reference,
                "timeline": copy.deepcopy(self.timeline),
                "model": copy.deepcopy(self.model),
            }
        )

    def tearDown(self):
        pass

    def _seal(self):
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": "thread-c1-runtime"}, clear=False):
            c1.start_c1_session(self.workspace, **self.inputs, input_gate=self.gate)
            for phase in c1.PHASES:
                payload = (
                    {"model": self.model}
                    if phase == c1.PHASES[-1]
                    else {field: self.model[field] for field in c1.PHASE_FIELDS[phase]}
                )
                c1.submit_c1_phase(
                    self.workspace,
                    **self.inputs,
                    input_gate=self.gate,
                    phase=phase,
                    payload=payload,
                )

    def _run(self):
        self._seal()
        with mock.patch.dict(os.environ, {"CODEX_THREAD_ID": "thread-c1-runtime"}, clear=False):
            c1.run_c1(
                self.package,
                **self.inputs,
                coordinator=self.coordinator,
                input_gate=self.gate,
                controlled_workspace=self.workspace,
                logical_package_path="C1",
                next_state_path="state/revision-006.json",
            )

    def test_happy_path_and_exact_package(self):
        self._run()
        self.assertEqual(c1.validate_c1_package(self.package)["verdict"], "ready")
        self.assertEqual(
            set(path.name for path in (self.package / "generation-evidence").iterdir()),
            {f"{index:02d}-{phase}.json" for index, phase in enumerate(c1.PHASES, 1)},
        )

    def test_explicit_development_freedoms_are_valid(self):
        self._validate_bad(copy.deepcopy(self.model))

    def test_development_freedom_ids_are_unique(self):
        bad = copy.deepcopy(self.model)
        bad["development_freedoms"][1]["id"] = bad["development_freedoms"][0]["id"]
        # Keep the authority list structurally valid so this test isolates the
        # duplicate terminal object ID instead of being intercepted by the
        # schema's uniqueItems check on downstream_freedom.
        bad["authority_partition"]["downstream_freedom"] = sorted(
            {item["id"] for item in bad["development_freedoms"]}
        )
        with self.assertRaisesRegex(c1.C1Error, "C1_DEV_ID_DUPLICATE"):
            self._validate_bad(bad)

    def test_development_freedoms_cover_every_profile(self):
        bad = copy.deepcopy(self.model)
        removed = bad["development_freedoms"].pop()
        bad["authority_partition"]["downstream_freedom"].remove(removed["id"])
        with self.assertRaisesRegex(
            c1.C1Error,
            "C1_DEV_PROFILE_COVERAGE_MISMATCH",
        ):
            self._validate_bad(bad)

    def test_development_freedom_sources_must_close(self):
        bad = copy.deepcopy(self.model)
        bad["development_freedoms"][0]["source_ids"] = ["CHR-NOT-DEFINED"]
        with self.assertRaisesRegex(c1.C1Error, "C1_DEV_SOURCE_DANGLING"):
            self._validate_bad(bad)

    def test_development_freedom_text_cannot_be_placeholder(self):
        bad = copy.deepcopy(self.model)
        bad["development_freedoms"][0]["scope"] = "TBD"
        with self.assertRaisesRegex(c1.C1Error, "C1_DEV_PLACEHOLDER"):
            self._validate_bad(bad)

    def test_development_freedom_cannot_enter_autonomous_owned(self):
        bad = copy.deepcopy(self.model)
        bad["authority_partition"]["autonomous_owned"].append(
            bad["development_freedoms"][0]["id"]
        )
        with self.assertRaisesRegex(c1.C1Error, "C1_AUTHORITY_CONFLICT"):
            self._validate_bad(bad)

    def test_authority_partition_is_locally_disjoint(self):
        bad = copy.deepcopy(self.model)
        bad["authority_partition"]["autonomous_owned"].append(
            bad["authority_partition"]["author_locked"][0]
        )
        with self.assertRaisesRegex(c1.C1Error, "C1_AUTHORITY_CONFLICT"):
            self._validate_bad(bad)

    def test_old_character_model_without_development_freedoms_fails(self):
        bad = copy.deepcopy(self.model)
        bad.pop("development_freedoms")
        with self.assertRaisesRegex(c1.C1Error, "C1_MODEL_SCHEMA_INVALID"):
            self._validate_bad(bad)

    def test_empty_t1_information_fails(self):
        self.timeline["information_changes"] = []
        with self.assertRaisesRegex(c1.C1Error, "C1_INFORMATION_INPUT_EMPTY"):
            c1._validate_model(
                self.model,
                self.baseline,
                self.storyline,
                self.world,
                self.environment,
                self.timeline,
                c1._controls(self.b0, self.baseline),
                runtime.ContractRuntime(),
                expected_gate=self.gate.reference,
                expected_sources=c1._source_artifacts(self.b0, self.s1, self.w1, self.e1, self.t1),
            )

    def test_three_layer_distance_tamper_fails(self):
        bad = copy.deepcopy(self.model)
        bad["three_layer_networks"][0]["layer_1_direct"], bad["three_layer_networks"][0]["layer_2_institutional"] = (
            bad["three_layer_networks"][0]["layer_2_institutional"],
            bad["three_layer_networks"][0]["layer_1_direct"],
        )
        with self.assertRaisesRegex(c1.C1Error, "C1_NETWORK_DISTANCE_MISMATCH"):
            c1._validate_model(
                bad,
                self.baseline,
                self.storyline,
                self.world,
                self.environment,
                self.timeline,
                c1._controls(self.b0, self.baseline),
                runtime.ContractRuntime(),
                expected_gate=self.gate.reference,
                expected_sources=c1._source_artifacts(self.b0, self.s1, self.w1, self.e1, self.t1),
            )

    def test_agency_action_must_bind_exact_t1_roles(self):
        bad = copy.deepcopy(self.model)
        bad["agency_matrix"][0]["chosen_action"] = "Execute a plausible but unbound action."
        bad["agency_matrix"][0]["available_choices"][0] = bad["agency_matrix"][0]["chosen_action"]
        with self.assertRaisesRegex(c1.C1Error, "C1_AGENCY_ACTION_BINDING_MISMATCH"):
            self._validate_bad(bad)

    def test_information_token_cannot_name_fake_change(self):
        bad = copy.deepcopy(self.model)
        state = bad["information_matrix"][0]
        state["knows"] = [
            value.replace("INFO-T1-C1", "INFO-FAKE") for value in state["knows"]
        ]
        with self.assertRaisesRegex(c1.C1Error, "C1_INFORMATION_KNOWN_BINDING_MISMATCH"):
            self._validate_bad(bad)

    def test_arc_pressure_event_must_be_relevant_and_real(self):
        bad = copy.deepcopy(self.model)
        bad["character_arcs"][0]["pressure_event_ids"] = ["EV-FAKE"]
        with self.assertRaisesRegex(c1.C1Error, "C1_ARC_PRESSURE_MISMATCH"):
            self._validate_bad(bad)

    def test_three_layer_cannot_omit_real_distance_one_neighbor(self):
        bad = copy.deepcopy(self.model)
        network = bad["three_layer_networks"][0]
        core = network["core_character_id"]
        candidate = next(
            item["id"]
            for item in bad["profiles"]
            if item["id"] != core
            and item["id"] not in set().union(
                network["layer_1_direct"],
                network["layer_2_institutional"],
                network["layer_3_contextual"],
            )
        )
        relation = {
            "id": "REL-OMITTED-L1",
            "from_character_id": core,
            "to_character_id": candidate,
            "function": "[FUNCTION:direct] Creates a second real direct neighbor.",
            "start_state": "The direct pressure is not yet active.",
            "change_event_ids": [self.timeline["major_events"][0]["id"]],
            "end_state": "The direct pressure now constrains both characters.",
            "boundaries": ["Neither character loses independent agency."],
        }
        bad["relationships"].append(relation)
        network["relationship_ids"].append(relation["id"])
        for profile in bad["profiles"]:
            if profile["id"] in {core, candidate}:
                profile["relationship_levers"].append(
                    f"[REL:{relation['id']}] This direct pressure changes support."
                )
        with self.assertRaisesRegex(c1.C1Error, "C1_NETWORK_DISTANCE_MISMATCH"):
            self._validate_bad(bad)

    def test_opposite_character_demand_propagates_through_all_phases(self):
        changed_storyline = copy.deepcopy(self.storyline)
        demand = changed_storyline["character_requirements"][0]
        demand["responsibility"] = (
            "Require the opposite character responsibility while preserving "
            "the same demand identity."
        )
        regenerated = agent_character_proposal(
            run_id=self.baseline["run_id"],
            gate_reference=self.gate.reference,
            source_artifacts=c1._source_artifacts(
                self.b0, self.s1, self.w1, self.e1, self.t1
            ),
            baseline=self.baseline,
            storyline=changed_storyline,
            world=self.world,
            environment=self.environment,
            timeline=self.timeline,
        )
        for phase in c1.PHASES:
            old_payload = (
                {"model": self.model}
                if phase == c1.PHASES[-1]
                else {
                    field: self.model[field]
                    for field in c1.PHASE_FIELDS[phase]
                }
            )
            new_payload = (
                {"model": regenerated}
                if phase == c1.PHASES[-1]
                else {
                    field: regenerated[field]
                    for field in c1.PHASE_FIELDS[phase]
                }
            )
            self.assertNotEqual(
                runtime.canonical_sha256(old_payload),
                runtime.canonical_sha256(new_payload),
                phase,
            )
        stale_later_phases = copy.deepcopy(self.model)
        stale_later_phases["character_demands"] = copy.deepcopy(
            changed_storyline["character_requirements"]
        )
        with self.assertRaisesRegex(
            c1.C1Error, "C1_SLOT_RATIONALE_MISSING"
        ):
            c1._validate_model(
                stale_later_phases,
                self.baseline,
                changed_storyline,
                self.world,
                self.environment,
                self.timeline,
                c1._controls(self.b0, self.baseline),
                runtime.ContractRuntime(),
                expected_gate=self.gate.reference,
                expected_sources=c1._source_artifacts(
                    self.b0, self.s1, self.w1, self.e1, self.t1
                ),
            )

    def _validate_bad(self, model):
        c1._validate_model(
            model,
            self.baseline,
            self.storyline,
            self.world,
            self.environment,
            self.timeline,
            c1._controls(self.b0, self.baseline),
            runtime.ContractRuntime(),
            expected_gate=self.gate.reference,
            expected_sources=c1._source_artifacts(
                self.b0, self.s1, self.w1, self.e1, self.t1
            ),
        )

    def test_finalizer_does_not_accept_external_model(self):
        self.assertNotIn("model", c1.run_c1.__annotations__)


if __name__ == "__main__":
    unittest.main()
