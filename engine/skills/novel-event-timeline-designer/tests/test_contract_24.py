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


v22_test = importlib.import_module(
    "skills.novel-event-timeline-designer.tests.test_contract_22"
)
v23_test = importlib.import_module(
    "skills.novel-event-timeline-designer.tests.test_contract_23"
)
contract_24 = importlib.import_module(
    "skills.novel-event-timeline-designer.scripts.contract_24"
)
runtime = importlib.import_module("harnesses.novel-conception-autonomous.runtime")


def typed_span_case(kind: str = "proposition_dependency"):
    storyline, environment, plan = v23_test.span_case()
    edge = plan["planned_causal_edges"][0]
    edge["edge_kind"] = kind
    edge["payload_ids"] = (
        ["PROP-DISCLOSED"] if kind == "proposition_dependency" else []
    )
    return storyline, environment, plan


class Contract24TypedEdgeTests(unittest.TestCase):
    def test_schema_separates_legacy_and_current_edges(self) -> None:
        validator = runtime.ContractRuntime()
        legacy = {
            "id": "CE-A",
            "from_event_id": "EV-A",
            "to_event_id": "EV-B",
            "mechanism": "bound result",
            "necessary_condition": "bound precondition",
        }
        current = {
            **legacy,
            "edge_kind": "capability_dependency",
            "payload_ids": ["CF-A"],
        }
        validator.validate_definition(
            legacy, "event-timeline.schema.json", "causalEdgeLegacy"
        )
        validator.validate_definition(
            current, "event-timeline.schema.json", "causalEdge24"
        )
        with self.assertRaises(runtime.ContractValidationError):
            validator.validate_definition(
                current, "event-timeline.schema.json", "causalEdgeLegacy"
            )
        with self.assertRaises(runtime.ContractValidationError):
            validator.validate_definition(
                legacy, "event-timeline.schema.json", "causalEdge24"
            )

    def test_proposition_dependency_preserves_ancestry(self) -> None:
        storyline, environment, plan = typed_span_case()
        contract_24.validate_p2_plan(
            plan, storyline, environment, v22_test.digest
        )

    def test_dependency_payload_is_exact_endpoint_intersection(self) -> None:
        storyline, environment, plan = typed_span_case()
        plan["planned_causal_edges"][0]["payload_ids"] = ["PROP-AFTER"]
        with self.assertRaisesRegex(
            contract_24.Contract24Error,
            "T1_EDGE_DEPENDENCY_PAYLOAD_MISMATCH",
        ):
            contract_24.validate_p2_plan(
                plan, storyline, environment, v22_test.digest
            )

    def test_sequencing_cannot_claim_dependency_payload(self) -> None:
        storyline, environment, plan = typed_span_case("sequencing")
        plan["planned_event_registry"][1]["requires_proposition_ids"] = [
            "PROP-INITIAL"
        ]
        contract_24.validate_p2_plan(
            plan, storyline, environment, v22_test.digest
        )
        plan["planned_causal_edges"][0]["payload_ids"] = ["PROP-DISCLOSED"]
        with self.assertRaisesRegex(
            contract_24.Contract24Error,
            "T1_EDGE_DEPENDENCY_PAYLOAD_MISMATCH",
        ):
            contract_24.validate_p2_plan(
                plan, storyline, environment, v22_test.digest
            )

    def test_different_dependency_kinds_may_share_endpoints(self) -> None:
        storyline, environment, plan = typed_span_case()
        source, target = plan["planned_event_registry"]
        environment["capability_fact_registry"] = [
            {"id": "CF-A", "root_policy": "producer_required"}
        ]
        steps = {
            item["id"]: item for item in environment["capability_step_registry"]
        }
        steps["CSTEP-D"]["produces_fact_ids"] = ["CF-A"]
        steps["CSTEP-A"]["requires_fact_ids"] = ["CF-A"]
        source["produces_capability_fact_ids"] = ["CF-A"]
        target["requires_capability_fact_ids"] = ["CF-A"]
        fact_edge = copy.deepcopy(plan["planned_causal_edges"][0])
        fact_edge.update(
            {
                "id": "CE-FACT",
                "edge_kind": "capability_dependency",
                "payload_ids": ["CF-A"],
            }
        )
        plan["planned_causal_edges"].append(fact_edge)
        contract_24.validate_p2_plan(
            plan, storyline, environment, v22_test.digest
        )


if __name__ == "__main__":
    unittest.main()
