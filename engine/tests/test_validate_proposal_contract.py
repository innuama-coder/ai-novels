import unittest

from scripts import validate_proposal_contract as validator


class CriticalClaimValidationTests(unittest.TestCase):
    def test_rejects_short_phrase_claims(self):
        rows = [
            ["Claim ID", "Claim", "Constraint role", "Evidence quote", "Source within artifact"],
            ["CLAIM-01", "危机被解除", "terminal outcome", "危机被解除", "Complete story synopsis paragraph 5"],
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_critical_claim_rows(rows, "artifact 04")

        self.assertIn("too short", str(raised.exception))

    def test_accepts_semantic_claim_schema(self):
        rows = [
            ["Claim ID", "Claim", "Constraint role", "Evidence quote", "Source within artifact"],
            [
                "CLAIM-01",
                "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。",
                "opening pressure and technical failure",
                "组织不愿放弃，先把他的身体接入生命维持系统维持脑活动，再用脑波分析尝试读取记忆。",
                "Complete story synopsis paragraph 1",
            ],
        ]

        claims = validator.validate_critical_claim_rows(rows, "artifact 04")

        self.assertEqual(claims[0]["id"], "CLAIM-01")
        self.assertEqual(claims[0]["claim"], rows[1][1])

    def test_artifact_runs_supports_list_and_legacy_single_run(self):
        run = {"id": "run-1", "sample_proposal": "docs/sample.md"}

        self.assertEqual(validator.artifact_runs({"artifact_runs": [run]}), [run])
        self.assertEqual(validator.artifact_runs({"artifact_run": run}), [run])

    def test_rejects_claim_text_drift_for_same_claim_id(self):
        canonical_claims = {
            "CLAIM-01": {
                "claim": "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。",
                "constraint_role": "opening pressure and technical failure",
            }
        }
        downstream_rows = [
            {
                "Claim ID": "CLAIM-01",
                "Critical business claim": "组织直接读取了逝者完整记忆，并立即获得了全部情报。",
                "Constraint role": "opening pressure and technical failure",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_claim_trace_rows(
                canonical_claims,
                downstream_rows,
                "integration Claim Source Map",
                require_constraint_role=True,
            )

        self.assertIn("claim text drift", str(raised.exception))

    def test_rejects_constraint_role_drift_for_same_claim_id(self):
        canonical_claims = {
            "CLAIM-01": {
                "claim": "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。",
                "constraint_role": "opening pressure and technical failure",
            }
        }
        downstream_rows = [
            {
                "Claim ID": "CLAIM-01",
                "Critical business claim": "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。",
                "Constraint role": "terminal outcome",
            }
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_claim_trace_rows(
                canonical_claims,
                downstream_rows,
                "integration Claim Source Map",
                require_constraint_role=True,
            )

        self.assertIn("constraint role drift", str(raised.exception))

    def test_rejects_final_proposal_claim_source_map_drift(self):
        canonical_claims = {
            "CLAIM-01": {
                "claim": "组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。",
                "constraint_role": "opening pressure and technical failure",
            }
        }
        proposal = """
# Proposal

## Claim Source Map

| Claim ID | Critical business claim | Upstream source | Constraint role |
|---|---|---|---|
| CLAIM-01 | 组织在逝者死亡后以生命维持系统维持脑活动，并以脑波分析尝试读取记忆。 | artifact 04 | terminal outcome |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_final_proposal_claim_source_map(
                proposal,
                canonical_claims,
                "final proposal",
            )

        self.assertIn("constraint role drift", str(raised.exception))


class ArtifactDagValidationTests(unittest.TestCase):
    def test_rejects_artifact_dependency_cycle(self):
        graph = [
            {"id": "13", "depends_on": ["14"]},
            {"id": "14", "depends_on": ["13"]},
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_artifact_dag(graph, "artifact graph")

        self.assertIn("cycle", str(raised.exception))

    def test_rejects_artifact_reference_to_non_dependency(self):
        graph = [
            {"id": "13", "depends_on": ["01"]},
            {"id": "14", "depends_on": ["13"]},
        ]
        source_map_rows = [
            ["Proposal section", "Source artifact"],
            ["Risk report", "artifact 14"],
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_section_source_dependencies(
                source_map_rows,
                current_artifact_id="13",
                allowed_dependency_ids=validator.allowed_dependency_ids(graph, "13"),
                label="artifact 13 Section Source Map",
            )

        self.assertIn("non-dependency artifact", str(raised.exception))

    def test_rejects_missing_final_proposal_package_node(self):
        graph = [
            {"id": f"{index:02d}", "depends_on": []}
            for index in range(1, 15)
        ]

        with self.assertRaises(ValueError) as raised:
            validator.validate_proposal_artifact_topology(graph, "artifact graph")

        self.assertIn("final-proposal-package", str(raised.exception))

    def test_rejects_artifact_13_depending_on_risk_report(self):
        graph = [
            {"id": f"{index:02d}", "depends_on": []}
            for index in range(1, 15)
        ]
        graph[12]["depends_on"] = ["14"]
        graph.append({"id": "final-proposal-package", "depends_on": ["13", "14"]})

        with self.assertRaises(ValueError) as raised:
            validator.validate_proposal_artifact_topology(graph, "artifact graph")

        self.assertIn("artifact 13", str(raised.exception))

    def test_rejects_artifact_14_missing_required_upstream_gate_dependencies(self):
        graph = [
            {"id": f"{index:02d}", "depends_on": []}
            for index in range(1, 15)
        ]
        graph[12]["depends_on"] = [f"{index:02d}" for index in range(1, 13)]
        graph[13]["depends_on"] = ["13"]
        graph.append({"id": "final-proposal-package", "depends_on": ["13", "14"]})

        with self.assertRaises(ValueError) as raised:
            validator.validate_proposal_artifact_topology(graph, "artifact graph")

        self.assertIn("artifact 14", str(raised.exception))


class ProposalPackageTerminologyTests(unittest.TestCase):
    def test_rejects_legacy_integrated_proposal_risk_input_term(self):
        text = """
## Input

- Integrated proposal document
- Integration Verdict from `novel-proposal-integrator`
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_no_legacy_integrated_proposal_terms(text, "risk checker")

        self.assertIn("legacy integrated proposal term", str(raised.exception))


class RiskVerdictConsistencyTests(unittest.TestCase):
    def test_rejects_agent_pass_with_p1_risk(self):
        risk_report = """
# Risk Report

## Output

| Field | Value |
|---|---|
| Agent quality verdict | `pass` |
| Human/intake confirmation verdict | `pending` |
| PRD entry verdict | `blocked_pending_human_confirmation` |

## Risks

| Risk | Severity | Handling |
|---|---|---|
| Missing claim map coverage | P1 | Rerun integrator. |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_risk_verdict_consistency(risk_report, "risk report")

        self.assertIn("Agent quality verdict cannot pass", str(raised.exception))


class WorkflowConvergenceContractTests(unittest.TestCase):
    def test_workflow_declares_convergence_protocol(self):
        workflow = validator.read(validator.WORKFLOW_SKILL)

        for term in [
            "## Convergence Protocol",
            "Stable issue id",
            "Root cause",
            "Fix hypothesis",
            "Regression proof",
            "Versioned refactor trigger",
        ]:
            self.assertIn(term, workflow)

    def test_rejects_empty_convergence_log(self):
        manifest = """
# Proposal workflow artifact run

## Convergence log
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_convergence_log(manifest, "manifest")

        self.assertIn("must include header and at least one row", str(raised.exception))

    def test_manifest_required_terms_accept_structured_convergence_heading(self):
        terms = validator.manifest_required_terms()

        self.assertIn("## Convergence log", terms)
        self.assertNotIn("Convergence log:", terms)

    def test_requires_refactor_trigger_after_three_attempts(self):
        manifest = """
# Proposal workflow artifact run

## Convergence log

| Stable issue id | Root cause | Fix hypothesis | Regression proof | Attempt count | Versioned refactor trigger |
|---|---|---|---|---|---|
| P1-CLAIM | root cause exists | fix hypothesis exists | regression proof exists | 3 |  |
"""

        with self.assertRaises(ValueError) as raised:
            validator.validate_convergence_log(manifest, "manifest")

        self.assertIn("requires Versioned refactor trigger", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
