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
import unittest


contract_25 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.contract_25"
)


def _event(
    event_id: str,
    time: int,
    *,
    subject: str | None = None,
    before: str = "idle",
    after: str = "done",
) -> dict:
    return {
        "id": event_id,
        "world_time_slot": f"[WT:{time:06d}]",
        "changed_subject": {
            "subject_id": subject or f"PSS-{event_id}",
            "before": before,
            "after": after,
            "subject_kind": "t1_process_record",
        },
        "requires_proposition_ids": [],
        "produces_proposition_ids": [f"PROP-{event_id}"],
        "discloses_proposition_ids": [],
        "requires_token_instance_ids": [],
        "consumes_token_instance_ids": [],
        "produces_token_instance_ids": [],
        "lifecycle_effects": [],
    }


def lifecycle_case(*, same_time: bool = False, multi_hop: bool = False):
    lifecycle_id = "LFC-R07"
    subject_id = "PSS-R07"
    token_id = "ATI-STARTUP"
    acceptance = _event("EV-ACCEPT", 1)
    acceptance["produces_proposition_ids"].append("PROP-ACCEPTED")
    producer = _event("EV-PERMIT", 1 if same_time else 2)
    producer["requires_proposition_ids"] = ["PROP-ACCEPTED"]
    producer["produces_token_instance_ids"] = [token_id]
    startup = _event(
        "EV-STARTUP",
        1 if same_time else 3,
        subject=subject_id,
        before="NOT_STARTED",
        after="ACTIVE",
    )
    startup["requires_token_instance_ids"] = [token_id]
    startup["consumes_token_instance_ids"] = [token_id]
    startup["lifecycle_effects"] = [
        {
            "lifecycle_contract_id": lifecycle_id,
            "transition_kind": "startup",
            "from_state": "NOT_STARTED",
            "to_state": "ACTIVE",
        }
    ]
    shutdown = _event(
        "EV-SHUTDOWN",
        5,
        subject=subject_id,
        before="ACTIVE",
        after="SHUTDOWN",
    )
    shutdown["lifecycle_effects"] = [
        {
            "lifecycle_contract_id": lifecycle_id,
            "transition_kind": "shutdown",
            "from_state": "ACTIVE",
            "to_state": "SHUTDOWN",
        }
    ]
    memory = _event("EV-LATE-MEMORY", 4)
    memory["discloses_proposition_ids"] = ["PROP-NOT-STARTED-MEMORY"]

    events = [acceptance, producer, startup, memory, shutdown]
    pairs = [
        ("EV-ACCEPT", "EV-PERMIT", "narrative_causal"),
        ("EV-PERMIT", "EV-STARTUP", "token_dependency"),
        ("EV-STARTUP", "EV-LATE-MEMORY", "sequencing"),
        ("EV-LATE-MEMORY", "EV-SHUTDOWN", "narrative_causal"),
    ]
    if multi_hop:
        accept_bridge = _event("EV-ACCEPT-BRIDGE", 1 if same_time else 2)
        permit_bridge = _event("EV-PERMIT-BRIDGE", 1 if same_time else 3)
        events.extend([accept_bridge, permit_bridge])
        pairs = [
            ("EV-ACCEPT", "EV-ACCEPT-BRIDGE", "capability_dependency"),
            ("EV-ACCEPT-BRIDGE", "EV-PERMIT", "narrative_causal"),
            ("EV-PERMIT", "EV-PERMIT-BRIDGE", "token_dependency"),
            ("EV-PERMIT-BRIDGE", "EV-STARTUP", "narrative_causal"),
            ("EV-STARTUP", "EV-LATE-MEMORY", "sequencing"),
            ("EV-LATE-MEMORY", "EV-SHUTDOWN", "narrative_causal"),
        ]
    edges = [
        {
            "id": f"CE-{index}",
            "from_event_id": left,
            "to_event_id": right,
            "edge_kind": kind,
        }
        for index, (left, right, kind) in enumerate(pairs, 1)
    ]
    plan = {
        "lifecycle_scope": {
            "id": "LFS-ONE",
            "applicability": "applicable",
            "source_ids": ["SL-R07"],
            "lifecycle_contract_ids": [lifecycle_id],
            "semantic_review_claim_id": "CLAIM-LFS",
        },
        "lifecycle_contract_registry": [
            {
                "id": lifecycle_id,
                "subject_id": subject_id,
                "initial_state": "NOT_STARTED",
                "active_state": "ACTIVE",
                "terminal_state": "SHUTDOWN",
                "acceptance_event_id": "EV-ACCEPT",
                "acceptance_proposition_id": "PROP-ACCEPTED",
                "permit_producer_event_id": "EV-PERMIT",
                "permit_token_instance_id": token_id,
                "startup_event_id": "EV-STARTUP",
                "shutdown_event_id": "EV-SHUTDOWN",
                "source_ids": ["SL-R07"],
                "semantic_review_claim_id": "CLAIM-LFC",
            }
        ],
        "planned_event_registry": events,
        "planned_causal_edges": edges,
        "planned_proposition_registry": [
            {
                "id": "PROP-ACCEPTED",
                "initially_true": False,
                "producer_event_ids": ["EV-ACCEPT"],
            }
        ],
        "process_state_subject_registry": [
            {
                "id": subject_id,
                "state_vocabulary": ["NOT_STARTED", "ACTIVE", "SHUTDOWN"],
                "allowed_transitions": [
                    {"from": "NOT_STARTED", "to": "ACTIVE"},
                    {"from": "ACTIVE", "to": "SHUTDOWN"},
                ],
            }
        ],
        "authority_token_instance_ledger": [
            {
                "token_instance_id": token_id,
                "token_fact_id": "CF-STARTUP-PERMIT",
                "consumption_policy": "single_use",
                "origin": {
                    "kind": "t1_produced",
                    "producer_event_id": "EV-PERMIT",
                },
                "consumer_occurrences": [
                    {"event_id": "EV-STARTUP", "occurrence_id": "CSO-START"}
                ],
            }
        ],
    }
    environment = {
        "capability_fact_registry": [
            {
                "id": "CF-STARTUP-PERMIT",
                "kind": "authority_token",
                "consumption_policy": "single_use",
            }
        ]
    }
    return plan, environment


class Contract25LifecycleTests(unittest.TestCase):
    def assert_invalid(self, plan, environment, code: str) -> None:
        with self.assertRaisesRegex(contract_25.Contract25Error, code):
            contract_25.validate_lifecycle_closure(plan, environment)

    def test_distinct_world_times_pass(self) -> None:
        plan, environment = lifecycle_case()
        contract_25.validate_lifecycle_closure(plan, environment)

    def test_same_world_time_uses_dag_tie_break(self) -> None:
        plan, environment = lifecycle_case(same_time=True)
        contract_25.validate_lifecycle_closure(plan, environment)

    def test_multihop_typed_paths_pass(self) -> None:
        plan, environment = lifecycle_case(same_time=True, multi_hop=True)
        contract_25.validate_lifecycle_closure(plan, environment)

    def test_late_analeptic_not_started_disclosure_is_independent(self) -> None:
        plan, environment = lifecycle_case()
        memory = next(
            item
            for item in plan["planned_event_registry"]
            if item["id"] == "EV-LATE-MEMORY"
        )
        self.assertEqual(
            ["PROP-NOT-STARTED-MEMORY"], memory["discloses_proposition_ids"]
        )
        contract_25.validate_lifecycle_closure(plan, environment)

    def test_missing_startup_fails(self) -> None:
        plan, environment = lifecycle_case()
        plan["planned_event_registry"] = [
            item
            for item in plan["planned_event_registry"]
            if item["id"] != "EV-STARTUP"
        ]
        self.assert_invalid(plan, environment, "T1_LIFECYCLE_EVENT_BINDING_INVALID")

    def test_double_startup_fails(self) -> None:
        plan, environment = lifecycle_case()
        duplicate = _event(
            "EV-STARTUP-2",
            4,
            subject="PSS-R07",
            before="NOT_STARTED",
            after="ACTIVE",
        )
        duplicate["lifecycle_effects"] = copy.deepcopy(
            next(
                item
                for item in plan["planned_event_registry"]
                if item["id"] == "EV-STARTUP"
            )["lifecycle_effects"]
        )
        plan["planned_event_registry"].append(duplicate)
        self.assert_invalid(
            plan, environment, "T1_LIFECYCLE_EFFECT_COVERAGE_MISMATCH"
        )

    def test_post_startup_state_rollback_fails(self) -> None:
        plan, environment = lifecycle_case()
        rollback = _event(
            "EV-ROLLBACK",
            4,
            subject="PSS-R07",
            before="ACTIVE",
            after="NOT_STARTED",
        )
        plan["planned_event_registry"].append(rollback)
        self.assert_invalid(
            plan, environment, "T1_LIFECYCLE_STATE_ROLLBACK"
        )

    def test_acceptance_after_startup_fails(self) -> None:
        plan, environment = lifecycle_case()
        next(
            item
            for item in plan["planned_event_registry"]
            if item["id"] == "EV-ACCEPT"
        )["world_time_slot"] = "[WT:000004]"
        self.assert_invalid(
            plan, environment, "T1_LIFECYCLE_ACCEPTANCE_AFTER_STARTUP"
        )

    def test_missing_typed_path_fails(self) -> None:
        plan, environment = lifecycle_case()
        next(
            item
            for item in plan["planned_causal_edges"]
            if item["from_event_id"] == "EV-ACCEPT"
        )["edge_kind"] = "sequencing"
        self.assert_invalid(
            plan, environment, "T1_LIFECYCLE_ACCEPTANCE_CAUSAL_PATH_MISSING"
        )

    def test_single_use_requires_explicit_consume(self) -> None:
        plan, environment = lifecycle_case()
        next(
            item
            for item in plan["planned_event_registry"]
            if item["id"] == "EV-STARTUP"
        )["consumes_token_instance_ids"] = []
        self.assert_invalid(plan, environment, "T1_LIFECYCLE_PERMIT_BINDING_INVALID")

    def test_single_use_double_consume_fails(self) -> None:
        plan, environment = lifecycle_case()
        memory = next(
            item
            for item in plan["planned_event_registry"]
            if item["id"] == "EV-LATE-MEMORY"
        )
        memory["requires_token_instance_ids"] = ["ATI-STARTUP"]
        memory["consumes_token_instance_ids"] = ["ATI-STARTUP"]
        plan["authority_token_instance_ledger"][0]["consumer_occurrences"].append(
            {"event_id": "EV-LATE-MEMORY", "occurrence_id": "CSO-MEMORY"}
        )
        self.assert_invalid(plan, environment, "T1_LIFECYCLE_PERMIT_BINDING_INVALID")


if __name__ == "__main__":
    unittest.main()
