from __future__ import annotations

import importlib
import unittest


q1 = importlib.import_module("skills.novel-conception-reviewer.scripts.run_v2")


def object_index():
    return {
        ("S1", "SL-R07"): {
            "kind": "storyline",
            "value": {"id": "SL-R07"},
        },
        ("E1", "CF-STARTUP-PERMIT"): {
            "kind": "governance",
            "value": {"id": "CF-STARTUP-PERMIT"},
        },
        ("T1", "LFS-R07"): {
            "kind": "lifecycle-scope",
            "value": {
                "id": "LFS-R07",
                "source_ids": ["SL-R07", "CF-STARTUP-PERMIT"],
            },
        },
        ("T1", "LFC-R07"): {
            "kind": "lifecycle-contract",
            "value": {
                "id": "LFC-R07",
                "source_ids": ["SL-R07", "CF-STARTUP-PERMIT"],
            },
        },
    }


def evidence_objects():
    return [
        {"stage": stage, "id": identifier}
        for stage, identifier in sorted(object_index())
    ]


class T1LifecycleCrossModelTests(unittest.TestCase):
    def test_review_plan_requires_lifecycle_dimension(self) -> None:
        body = {"review_plan": {"cross_domain_dimensions": ["causality"]}}
        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_T1_LIFECYCLE_REVIEW_MISSING"
        ):
            q1._validate_t1_lifecycle_review_coverage(
                body, object_index=object_index(), phase="review-plan"
            )
        body["review_plan"]["cross_domain_dimensions"].append(
            q1.T1_LIFECYCLE_CLOSURE_SCOPE
        )
        q1._validate_t1_lifecycle_review_coverage(
            body, object_index=object_index(), phase="review-plan"
        )

    def test_t1_domain_review_binds_25_contract(self) -> None:
        reviews = [
            {"scope": stage, "checked_contract": "ordinary"}
            for stage in q1.UPSTREAM_STAGES
        ]
        body = {"domain_reviews": reviews}
        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_T1_LIFECYCLE_REVIEW_MISSING"
        ):
            q1._validate_t1_lifecycle_review_coverage(
                body, object_index=object_index(), phase="domain-challenges"
            )
        next(item for item in reviews if item["scope"] == "T1")[
            "checked_contract"
        ] = q1.T1_LIFECYCLE_REVIEW_CONTRACT
        q1._validate_t1_lifecycle_review_coverage(
            body, object_index=object_index(), phase="domain-challenges"
        )

    def test_cross_domain_check_covers_sources_and_contracts(self) -> None:
        check = {"id": "CHK-LIFECYCLE", "scope": q1.T1_LIFECYCLE_CLOSURE_SCOPE}
        body = {
            "cross_domain_checks": [check],
            "assertion_bindings": [
                {"check_id": check["id"], "evidence_objects": evidence_objects()}
            ],
        }
        q1._validate_t1_lifecycle_review_coverage(
            body,
            object_index=object_index(),
            phase="cross-domain-challenges",
        )
        body["assertion_bindings"][0]["evidence_objects"].pop()
        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_T1_LIFECYCLE_REVIEW_INCOMPLETE"
        ):
            q1._validate_t1_lifecycle_review_coverage(
                body,
                object_index=object_index(),
                phase="cross-domain-challenges",
            )

    def test_handoff_chronology_and_causality_each_cover_lifecycle(self) -> None:
        checks = [
            {"id": "CHK-CHRONOLOGY", "scope": "chronology_reconstruction"},
            {"id": "CHK-CAUSAL", "scope": "causal_precondition_trace"},
        ]
        payload = {
            "handoff_checks": checks,
            "assertion_bindings": [
                {"check_id": item["id"], "evidence_objects": evidence_objects()}
                for item in checks
            ],
        }
        q1._validate_t1_lifecycle_handoff_coverage(
            payload, object_index=object_index()
        )
        payload["assertion_bindings"][1]["evidence_objects"].pop()
        with self.assertRaisesRegex(
            q1.Q1Error, "Q1_T1_LIFECYCLE_HANDOFF_INCOMPLETE"
        ):
            q1._validate_t1_lifecycle_handoff_coverage(
                payload, object_index=object_index()
            )

    def test_handoff_lifecycle_trace_policies_admit_e1_sources(self) -> None:
        for scope in (
            "chronology_reconstruction",
            "causal_precondition_trace",
        ):
            policy = q1._binding_policy(
                "handoff_checks", {"scope": scope}
            )
            self.assertEqual(policy["stages"], {"S1", "E1", "T1"})
            self.assertNotIn("W1", policy["stages"])
            self.assertNotIn("C1", policy["stages"])


if __name__ == "__main__":
    unittest.main()
