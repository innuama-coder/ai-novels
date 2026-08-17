from __future__ import annotations

import copy
import importlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
c1 = importlib.import_module(
    "skills.novel-character-system-designer.scripts.run_v2"
)
proposal_adapter = importlib.import_module(
    "harnesses.novel-conception-autonomous.evals.proposal_adapter"
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _probe_inputs() -> dict[str, object]:
    line_ids = ("SL-Z", "SL-A", "SL-M", "SL-B", "SL-Y")
    slot_ids = ("SLOT-Z", "SLOT-A", "SLOT-M", "SLOT-B", "SLOT-Y")
    event_ids = ("EV-Z", "EV-A", "EV-M", "EV-B", "EV-Y")
    storylines = []
    demands = []
    events = []
    sequences = []
    for index, (line_id, slot_id, event_id) in enumerate(
        zip(line_ids, slot_ids, event_ids, strict=True), 1
    ):
        storylines.append(
            {
                "id": line_id,
                "actor_slot_ids": [slot_id],
            }
        )
        demands.append(
            {
                "id": f"CHD-{index:03d}",
                "responsibility": f"Carry {line_id}.",
                "source_ids": [slot_id, line_id],
                "required_capability": f"Act in {event_id}.",
                "constraints": ["Preserve the sealed event."],
                "acceptance_checks": ["The assigned character acts."],
                "downstream_freedom": ["Surface expression remains open."],
            }
        )
        events.append(
            {
                "id": event_id,
                "storyline_ids": [line_id],
                "environment_id": "ENV-001",
                "participant_slot_ids": [slot_id],
                "initiator_slot_id": slot_id,
                "counter_slot_ids": [],
                "initiating_action": f"Initiate {event_id}.",
            }
        )
        sequences.append(
            {
                "storyline_id": line_id,
                "event_ids": [event_id],
            }
        )
    return {
        "run_id": "RUN-C1-DETERMINISM",
        "gate_reference": {
            "path": "C1/input-gate.json",
            "sha256": "0" * 64,
        },
        "source_artifacts": [],
        "baseline": {
            "run_id": "RUN-C1-DETERMINISM",
            "control_registry": [],
        },
        "storyline": {
            "storylines": storylines,
            "character_requirements": demands,
        },
        "world": {
            "systems": [],
            "institutions": [],
            "authority_flows": [],
        },
        "environment": {
            "access_and_authority": [],
        },
        "timeline": {
            "major_events": events,
            "information_changes": [
                {
                    "id": "INFO-001",
                    "before": "The result is unknown.",
                    "after": "The result is known.",
                    "event_ids": ["EV-A"],
                    "visibility_ids": ["SLOT-Y", "SLOT-A"],
                }
            ],
            "storyline_event_sequences": sequences,
            "state_ledger": [],
        },
    }


def determinism_probe() -> dict[str, object]:
    proposal = proposal_adapter._character_proposal(**_probe_inputs())
    phase = "agency-and-relationships"
    phase_payload = {
        field: proposal[field] for field in c1.PHASE_FIELDS[phase]
    }
    return {
        "phase03_payload_sha256": rt.canonical_sha256(phase_payload),
        "responsibility_matrix": proposal["responsibility_matrix"],
        "canonical_proposal_sha256": rt.canonical_sha256(proposal),
    }


class C1DeterminismTests(unittest.TestCase):
    def test_production_obligations_have_stable_set_and_mapping_order(
        self,
    ) -> None:
        values = _probe_inputs()
        maps = c1._c1_maps(
            values["storyline"],
            values["world"],
            values["environment"],
            values["timeline"],
        )
        expected = c1._c1_obligations(maps, values["timeline"])
        reordered_maps = copy.deepcopy(maps)
        for field in ("events", "lines", "event_slots"):
            reordered_maps[field] = dict(
                reversed(list(reordered_maps[field].items()))
            )
        reordered_timeline = copy.deepcopy(values["timeline"])
        reordered_timeline["storyline_event_sequences"].reverse()
        actual = c1._c1_obligations(
            reordered_maps, reordered_timeline
        )

        self.assertEqual(list(expected.items()), list(actual.items()))
        first_event_kinds = [
            item["kind"]
            for item in expected.values()
            if item.get("event_id") == "EV-A"
            and item["kind"] not in {"information", "aftermath"}
        ]
        self.assertEqual(sorted(first_event_kinds), first_event_kinds)
        terminal_events = [
            item["event_id"]
            for item in expected.values()
            if item["kind"] == "aftermath"
        ]
        self.assertEqual(sorted(terminal_events), terminal_events)

    def test_mapping_insertion_order_preserves_responsibility_ids_and_proposal(
        self,
    ) -> None:
        values = _probe_inputs()
        expected = proposal_adapter._character_proposal(**values)
        maps = c1._c1_maps(
            values["storyline"],
            values["world"],
            values["environment"],
            values["timeline"],
        )
        reordered_maps = copy.deepcopy(maps)
        for field in (
            "lines",
            "demands",
            "events",
            "line_slots",
            "event_slots",
            "slot_events",
            "slot_demands",
            "ledger_providers",
        ):
            reordered_maps[field] = dict(
                reversed(list(reordered_maps[field].items()))
            )
        with mock.patch.object(
            proposal_adapter.c1,
            "_c1_maps",
            return_value=reordered_maps,
        ):
            actual = proposal_adapter._character_proposal(**values)

        self.assertEqual(
            expected["responsibility_matrix"],
            actual["responsibility_matrix"],
        )
        self.assertEqual(
            rt.canonical_json(expected),
            rt.canonical_json(actual),
        )

    def test_cross_process_python_hash_seeds_preserve_phase03_and_proposal(
        self,
    ) -> None:
        command = [
            sys.executable,
            "-c",
            (
                "import json;"
                "from testing.test_c1_determinism import determinism_probe;"
                "print(json.dumps(determinism_probe(),sort_keys=True,"
                "separators=(',',':')))"
            ),
        ]
        results = []
        for seed in ("1", "2", "random"):
            environment = dict(os.environ)
            environment["PYTHONHASHSEED"] = seed
            completed = subprocess.run(
                command,
                cwd=REPOSITORY_ROOT,
                env=environment,
                check=True,
                capture_output=True,
                text=True,
            )
            results.append(json.loads(completed.stdout))

        self.assertEqual(results[0], results[1])
        self.assertEqual(results[0], results[2])


if __name__ == "__main__":
    unittest.main()
