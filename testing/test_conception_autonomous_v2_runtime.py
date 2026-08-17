from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from testing.autonomous_v2_schema_runtime import (
    ContractValidationError,
    SchemaRuntime,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "docs" / "ai-novel-workflow" / "contracts" / "autonomous-v2"
RUNTIME = SchemaRuntime(CONTRACT_DIR)
SHA = "a" * 64


def artifact(path: str) -> dict[str, str]:
    return {"path": path, "sha256": SHA}


def stage_ref(stage: str) -> dict[str, str]:
    return {"stage": stage, "path": f"{stage}/stage-completion.json", "sha256": SHA}


def return_binding(
    owner: str = "W1",
    resume_stage: str = "W1",
    resume_point: str = "W1",
    kind: str = "local_revision",
) -> dict:
    return {
        "return_id": "RET-001",
        "return_kind": kind,
        "return_request": artifact("returns/RET-001/return-request.json"),
        "calculated_owner": owner,
        "resume_stage": resume_stage,
        "resume_point": resume_point,
    }


def gate(stage: str, upstream: list[str], *, binding: dict | None = None) -> dict:
    return {
        "schema_version": "2.0",
        "run_id": "RUN-001",
        "target_stage": stage,
        "entry_mode": "return_resolution" if binding else "forward",
        "run_state": artifact("state/run-state.1.json"),
        "baseline_completion": None if stage == "B0" else stage_ref("B0"),
        "upstream_completions": [stage_ref(item) for item in upstream],
        "active_return": (
            artifact("returns/RET-001/return-request.json") if binding else None
        ),
        "return_binding": binding,
    }


class AutonomousV2RuntimeTests(unittest.TestCase):
    def test_runtime_executes_every_contract_keyword(self) -> None:
        schemas = sorted(CONTRACT_DIR.glob("*.schema.json"))
        self.assertGreaterEqual(len(schemas), 20)
        for schema in schemas:
            with self.subTest(schema=schema.name):
                RUNTIME.assert_schema_keywords_supported(schema.name)

    def test_exact_forward_topology_accepts_all_stages(self) -> None:
        topology = {
            "B0": [],
            "S1": [],
            "W1": ["S1"],
            "E1": ["S1", "W1"],
            "T1": ["S1", "W1", "E1"],
            "C1": ["S1", "W1", "E1", "T1"],
            "Q1": ["S1", "W1", "E1", "T1", "C1"],
            "P1": ["S1", "W1", "E1", "T1", "C1", "Q1"],
            "H1": ["P1"],
        }
        for stage, upstream in topology.items():
            with self.subTest(stage=stage):
                RUNTIME.assert_valid(gate(stage, upstream), "input-gate.schema.json")

    def test_wrong_or_missing_upstream_is_rejected(self) -> None:
        RUNTIME.assert_invalid(gate("W1", []), "input-gate.schema.json")
        RUNTIME.assert_invalid(gate("E1", ["W1", "S1"]), "input-gate.schema.json")
        RUNTIME.assert_invalid(gate("H1", ["Q1"]), "input-gate.schema.json")

    def test_forward_mode_cannot_smuggle_active_return(self) -> None:
        value = gate("W1", ["S1"])
        value["active_return"] = artifact("returns/RET-001/return-request.json")
        RUNTIME.assert_invalid(value, "input-gate.schema.json")

    def test_only_named_resume_stage_can_resolve_return(self) -> None:
        binding = return_binding()
        RUNTIME.assert_valid(
            gate("W1", ["S1"], binding=binding), "input-gate.schema.json"
        )
        RUNTIME.assert_invalid(
            gate("E1", ["S1", "W1"], binding=binding),
            "input-gate.schema.json",
        )

    def test_completion_requires_exact_predecessor_chain(self) -> None:
        completion = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "stage": "T1",
            "status": "ready",
            "manifest": artifact("T1/package-manifest.json"),
            "validation": artifact("T1/validation.json"),
            "input_gate": artifact("T1/input-gate.json"),
            "state_before": artifact("state/run-state.4.json"),
            "session_id": "SESSION-T1",
            "previous_stage_completions": [
                stage_ref("S1"),
                stage_ref("W1"),
                stage_ref("E1"),
            ],
            "return_binding": None,
        }
        RUNTIME.assert_valid(completion, "stage-completion.schema.json")
        RUNTIME.assert_completion_matches_gate(
            completion, gate("T1", ["S1", "W1", "E1"])
        )
        bad = deepcopy(completion)
        bad["previous_stage_completions"].pop()
        RUNTIME.assert_invalid(bad, "stage-completion.schema.json")

    def test_local_return_has_exact_invalidation_suffix(self) -> None:
        request = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "return_id": "RET-001",
            "return_kind": "local_revision",
            "origin_kind": "stage",
            "origin_stage": "Q1",
            "author_decision": None,
            "problem": "世界权限不足",
            "evidence_ids": ["WF-001"],
            "violated_contract": "W1 authority flow",
            "calculated_owner": "W1",
            "owner_basis": "world rule owner",
            "required_revision": "修正权限路径",
            "target_stage": "W1",
            "resume_stage": "W1",
            "resume_point": "W1",
            "invalidated_stages": ["W1", "E1", "T1", "C1", "Q1", "P1", "H1"],
            "invalidated_h1_artifacts": [
                "plan", "fragments", "assembly", "html", "completion"
            ],
            "invalidate_author_decision": False,
            "invalidate_conception_completion": False,
            "status": "active",
        }
        RUNTIME.assert_valid(request, "return-request.schema.json")
        RUNTIME.assert_return_routing(request)
        bad = deepcopy(request)
        bad["invalidated_stages"].remove("T1")
        RUNTIME.assert_invalid(bad, "return-request.schema.json")

    def test_new_structural_fact_returns_to_i2_and_resumes_b0(self) -> None:
        request = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "return_id": "RET-FACT-001",
            "return_kind": "upstream_reentry",
            "origin_kind": "stage",
            "origin_stage": "W1",
            "author_decision": None,
            "problem": "出现未登记的结构性现实事实依赖",
            "evidence_ids": ["WF-REALITY-001"],
            "violated_contract": "B0 fact dependency closure",
            "calculated_owner": "I2",
            "owner_basis": "world and research intake owner",
            "required_revision": "完成条件研究并重新批准访谈简报",
            "target_stage": "I2",
            "resume_stage": "B0",
            "resume_point": "B0",
            "invalidated_stages": [
                "B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"
            ],
            "invalidated_h1_artifacts": [
                "plan", "fragments", "assembly", "html", "completion"
            ],
            "invalidate_author_decision": True,
            "invalidate_conception_completion": True,
            "status": "active",
        }
        RUNTIME.assert_valid(request, "return-request.schema.json")
        RUNTIME.assert_return_routing(request)

    def test_html_only_author_revision_has_exact_h1_suffix(self) -> None:
        request = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "return_id": "RET-HTML-001",
            "return_kind": "author_revision",
            "origin_kind": "author",
            "origin_stage": None,
            "author_decision": artifact("approval/author-decision.json"),
            "problem": "图形过密",
            "evidence_ids": ["visible-world-map"],
            "violated_contract": "H1-C readability",
            "calculated_owner": "H1-C",
            "owner_basis": "HTML presentation owner",
            "required_revision": "降低图形密度",
            "target_stage": "H1",
            "resume_stage": "H1",
            "resume_point": "H1-C",
            "invalidated_stages": ["H1"],
            "invalidated_h1_artifacts": ["html", "completion"],
            "invalidate_author_decision": True,
            "invalidate_conception_completion": True,
            "status": "active",
        }
        RUNTIME.assert_valid(request, "return-request.schema.json")
        RUNTIME.assert_return_routing(request)
        bad = deepcopy(request)
        bad["invalidated_h1_artifacts"] = ["completion"]
        RUNTIME.assert_invalid(bad, "return-request.schema.json")

    def test_run_state_can_close_return_without_hash_cycle(self) -> None:
        state = {
            "schema_version": "2.0",
            "workflow": "novel-conception-autonomous-v2",
            "run_id": "RUN-001",
            "revision": 3,
            "status": "running",
            "source_interview_state": artifact("interview/run-state.json"),
            "current_stage_completions": {
                "B0": stage_ref("B0"),
                "S1": stage_ref("S1"),
                "W1": stage_ref("W1"),
            },
            "h1_workspace": None,
            "active_return": None,
            "resolved_returns": [
                {
                    "return_binding": return_binding(),
                    "resolving_completion": stage_ref("W1"),
                    "pre_resolution_state": artifact("state/run-state.2.json"),
                }
            ],
            "superseded_completions": [stage_ref("W1")],
            "author_decision": None,
            "development_status": "not_ready",
            "previous_state": artifact("state/run-state.2.json"),
        }
        RUNTIME.assert_valid(state, "autonomous-run-state.schema.json")
        RUNTIME.assert_run_state_semantics(state)

    def test_run_state_semantics_reject_non_prefix_current_versions(self) -> None:
        state = {
            "current_stage_completions": {
                "B0": stage_ref("B0"),
                "W1": stage_ref("W1"),
            },
            "status": "running",
            "active_return": None,
            "development_status": "not_ready",
        }
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_run_state_semantics(state)

    def test_q1_ready_rejects_blocking_finding_and_return(self) -> None:
        def check(check_id: str, scope: str) -> dict:
            return {
                "id": check_id,
                "scope": scope,
                "checked_contract": f"{scope} contract",
                "method": "逐对象重验",
                "evidence_ids": ["SL-001"],
                "conclusion": "通过",
                "result": "pass",
            }

        review = {
            "schema_version": "2.0",
            "skill": "novel-conception-reviewer",
            "stage": "Q1",
            "run_id": "RUN-001",
            "status": "ready",
            "input_gate": artifact("Q1/input-gate.json"),
            "domain_reviews": [
                check(f"CHK-DOMAIN-{stage}", stage)
                for stage in ["S1", "W1", "E1", "T1", "C1"]
            ],
            "cross_domain_checks": [check("CHK-CROSS-001", "cross-domain")],
            "reality_claim_review": [check("CHK-REALITY-001", "reality")],
            "coverage_recalculation": [check("CHK-COVERAGE-001", "coverage")],
            "consistency_matrix": [check("CHK-CONSISTENCY-001", "consistency")],
            "causal_challenges": [check("CHK-CAUSAL-001", "causality")],
            "easy_solution_challenges": [check("CHK-EASY-001", "easy-solution")],
            "development_usability_test": {
                "id": "HANDOFF-001",
                "tested_tasks": ["复述主体", "追踪故事线", "定位事件条件"],
                "evidence_ids": ["SL-001"],
                "conclusion": "独立开发者能够使用",
                "result": "pass",
            },
            "handoff_test_evidence": artifact("Q1/handoff-test-evidence.json"),
            "task_isolation": {
                "semantic_task_id": "TASK-Q1-SEM",
                "handoff_task_id": "TASK-Q1-HANDOFF",
                "handoff_allowlist": [
                    artifact(f"Q1/input-{index}.json") for index in range(6)
                ],
                "forbidden_reads": [
                    "chat",
                    "interview_reports",
                    "generation_evidence",
                    "semantic_findings",
                    "expected_answers",
                ],
            },
            "findings": [],
            "return_request": None,
            "verdict": "ready",
        }
        RUNTIME.assert_valid(review, "conception-review.schema.json")
        failed_check = deepcopy(review)
        failed_check["causal_challenges"][0]["result"] = "revise"
        RUNTIME.assert_invalid(failed_check, "conception-review.schema.json")
        bad = deepcopy(review)
        bad["findings"] = [
            {
                "id": "FND-BLOCK-001",
                "severity": "blocked",
                "problem": "存在不可继续的问题",
                "evidence_ids": ["WF-001"],
                "affected_ids": ["SL-001"],
                "violated_contract": "Q1 ready gate",
                "calculated_owner": "W1",
                "required_revision": "修正世界规则",
                "minimum_rerun": "W1",
            }
        ]
        bad["return_request"] = artifact("returns/RET-001/return-request.json")
        RUNTIME.assert_invalid(bad, "conception-review.schema.json")

    def test_local_return_kind_and_full_h1_invalidation_are_hard(self) -> None:
        request = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "return_id": "RET-001",
            "return_kind": "local_revision",
            "origin_kind": "stage",
            "origin_stage": "Q1",
            "author_decision": None,
            "problem": "世界权限不足",
            "evidence_ids": ["WF-001"],
            "violated_contract": "W1 authority flow",
            "calculated_owner": "W1",
            "owner_basis": "world rule owner",
            "required_revision": "修正权限路径",
            "target_stage": "W1",
            "resume_stage": "W1",
            "resume_point": "W1",
            "invalidated_stages": [
                "W1", "E1", "T1", "C1", "Q1", "P1", "H1"
            ],
            "invalidated_h1_artifacts": [
                "plan", "fragments", "assembly", "html", "completion"
            ],
            "invalidate_author_decision": False,
            "invalidate_conception_completion": False,
            "status": "active",
        }
        RUNTIME.assert_valid(request, "return-request.schema.json")
        RUNTIME.assert_return_routing(request)
        wrong_kind = deepcopy(request)
        wrong_kind["return_kind"] = "upstream_reentry"
        RUNTIME.assert_invalid(wrong_kind, "return-request.schema.json")
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_return_routing(wrong_kind)
        missing_h1 = deepcopy(request)
        missing_h1["invalidated_h1_artifacts"] = []
        RUNTIME.assert_invalid(missing_h1, "return-request.schema.json")

    def test_active_return_removes_invalidated_current_completions(self) -> None:
        request = {
            "target_stage": "W1",
            "invalidated_stages": [
                "W1", "E1", "T1", "C1", "Q1", "P1", "H1"
            ],
            "invalidated_h1_artifacts": [
                "plan", "fragments", "assembly", "html", "completion"
            ],
            "resume_stage": "W1",
        }
        reference = artifact("returns/RET-001/return-request.json")
        state = {
            "current_stage_completions": {
                "B0": stage_ref("B0"),
                "S1": stage_ref("S1"),
            },
            "status": "revise",
            "active_return": reference,
            "development_status": "not_ready",
            "h1_workspace": None,
            "resolved_returns": [],
            "superseded_completions": [],
        }
        RUNTIME.assert_run_state_semantics(
            state,
            active_request=request,
            active_request_reference=reference,
        )
        bad = deepcopy(state)
        bad["current_stage_completions"]["W1"] = stage_ref("W1")
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_run_state_semantics(
                bad,
                active_request=request,
                active_request_reference=reference,
            )
        h1_request = {
            "target_stage": "H1",
            "resume_stage": "H1",
            "invalidated_stages": ["H1"],
            "invalidated_h1_artifacts": [
                "plan", "fragments", "assembly", "html", "completion"
            ],
        }
        h1_state = {
            "current_stage_completions": {
                stage: stage_ref(stage)
                for stage in ["B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1"]
            },
            "status": "revise",
            "active_return": reference,
            "development_status": "not_ready",
            "h1_workspace": artifact("H1/h1-workspace-state.initialized.json"),
            "resolved_returns": [],
            "superseded_completions": [],
        }
        RUNTIME.assert_run_state_semantics(
            h1_state,
            active_request=h1_request,
            active_request_reference=reference,
        )

    def test_resolved_return_requires_resume_stage_completion(self) -> None:
        state = {
            "current_stage_completions": {
                "B0": stage_ref("B0"),
                "S1": stage_ref("S1"),
                "W1": stage_ref("W1"),
            },
            "status": "running",
            "active_return": None,
            "development_status": "not_ready",
            "resolved_returns": [
                {
                    "return_binding": return_binding(),
                    "resolving_completion": stage_ref("C1"),
                    "pre_resolution_state": artifact("state/run-state.2.json"),
                }
            ],
            "superseded_completions": [stage_ref("C1")],
        }
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_run_state_semantics(state)

    def test_baseline_registry_must_be_lossless(self) -> None:
        domains = ["I0", "I1", "I2", "I3", "I4", "I5"]
        sources = []
        registry = []
        for index, domain in enumerate(domains):
            control_id = f"INT-{domain}-001"
            source_artifact = artifact(f"interview/{domain}/design.json")
            sources.append(
                {
                    "domain": domain,
                    "completion": artifact(f"interview/{domain}/completion.json"),
                    "artifact": source_artifact,
                    "control_ids": [control_id],
                }
            )
            registry.append(
                {
                    "id": control_id,
                    "domain": domain,
                    "hardness": "author_locked",
                    "artifact": source_artifact,
                    "heading": f"{domain} control",
                    "value_sha256": SHA,
                }
            )
        baseline = {
            "schema_version": "2.0",
            "stage": "B0",
            "run_id": "RUN-001",
            "status": "ready",
            "run_state": artifact("state/interview-state.json"),
            "design_artifacts": sources,
            "v1_completion": artifact("V1/completion.json"),
            "v2_completion": artifact("V2/completion.json"),
            "v2_author_approval": artifact("V2/approval.json"),
            "fact_dependency_register": artifact("B0/facts.json"),
            "control_registry": registry,
            "fact_dependencies": [
                {
                    "id": "FACT-001",
                    "status": "not_applicable",
                    "claim": "完全虚构",
                    "rationale": "不主张现实正确性",
                }
            ],
            "open_items": [],
        }
        RUNTIME.assert_valid(baseline, "author-control-baseline.schema.json")
        extracted = {
            item["domain"]: set(item["control_ids"])
            for item in baseline["design_artifacts"]
        }
        RUNTIME.assert_baseline_semantics(
            baseline,
            extracted_controls_by_domain=extracted,
        )
        partial = deepcopy(baseline)
        partial["control_registry"] = partial["control_registry"][:1]
        RUNTIME.assert_invalid(partial, "author-control-baseline.schema.json")
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_baseline_semantics(
                partial,
                extracted_controls_by_domain=extracted,
            )
        incomplete_inventory = deepcopy(baseline)
        incomplete_inventory["design_artifacts"][0]["control_ids"] = ["INT-I0-WRONG"]
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_baseline_semantics(
                incomplete_inventory,
                extracted_controls_by_domain=extracted,
            )

    def test_cross_stage_requirement_rejects_id_only_payload(self) -> None:
        path, schema = RUNTIME.load("canonical-common.schema.json")
        errors = RUNTIME._validate(
            {"id": "WR-001"},
            schema["$defs"]["worldRequirement"],
            path,
            "$",
        )
        self.assertTrue(errors)
        valid = {
            "id": "WR-001",
            "target_stage": "W1",
            "responsibility": "限制行动成本",
            "source_ids": ["SL-001"],
            "required_capability": "定义权限与失败路径",
            "constraints": ["不得提供便捷解法"],
            "acceptance_checks": ["至少存在一种可执行失败方式"],
            "downstream_freedom": "可命名机构，不可改变权限边界",
        }
        self.assertFalse(
            RUNTIME._validate(
                valid,
                schema["$defs"]["worldRequirement"],
                path,
                "$",
            )
        )

    def test_single_option_decision_requires_exclusion_evidence(self) -> None:
        model = {
            "design_decisions": [
                {
                    "id": "DEC-001",
                    "options": ["唯一可行方案"],
                    "selection": "唯一可行方案",
                }
            ]
        }
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_design_decisions_semantics(model)
        model["design_decisions"][0][
            "single_option_exclusion_evidence"
        ] = "其余方案违反作者锁定边界"
        RUNTIME.assert_design_decisions_semantics(model)

    def test_h1_report_rejects_empty_shell(self) -> None:
        empty = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "h1_session_id": "H1-001",
            "p1_completion": artifact("P1/completion.json"),
            "title": "构思评审",
            "world": {},
            "storylines": {},
            "characters": {},
            "fragments": [None],
            "decision_prompts": [None],
            "source_coverage": [None],
        }
        RUNTIME.assert_invalid(empty, "human-review-report.schema.json")

    def test_approved_state_is_one_way_input_to_final_completion(self) -> None:
        stages = ["B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"]
        state = {
            "schema_version": "2.0",
            "workflow": "novel-conception-autonomous-v2",
            "run_id": "RUN-001",
            "revision": 12,
            "status": "approved",
            "source_interview_state": artifact("interview/run-state.json"),
            "current_stage_completions": {
                stage: stage_ref(stage) for stage in stages
            },
            "h1_workspace": artifact("H1/h1-workspace-state.json"),
            "active_return": None,
            "resolved_returns": [],
            "superseded_completions": [],
            "author_decision": artifact("approval/author-decision.json"),
            "development_status": "not_ready",
            "previous_state": artifact("state/run-state.11.json"),
        }
        RUNTIME.assert_valid(state, "autonomous-run-state.schema.json")
        RUNTIME.assert_run_state_semantics(state)
        self.assertNotIn("conception_completion", state)

    def test_router_rejects_self_declared_wrong_owner(self) -> None:
        request = {
            "target_stage": "W1",
            "resume_point": "W1",
            "calculated_owner": "C1",
        }
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_return_routing(request)

    def test_canonical_schemas_reject_missing_business_models(self) -> None:
        empty = {
            "schema_version": "2.0",
            "skill": "novel-storyline-architecture-designer",
            "stage": "S1",
            "run_id": "RUN-001",
            "status": "ready",
            "input_gate": artifact("S1/input-gate.json"),
        }
        RUNTIME.assert_invalid(empty, "storyline-architecture.schema.json")
        self.assertTrue((CONTRACT_DIR / "world-model.schema.json").is_file())
        self.assertTrue((CONTRACT_DIR / "human-review-report.schema.json").is_file())

    def test_package_profile_cannot_masquerade_as_another_stage(self) -> None:
        manifest = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "stage": "P1",
            "package_profile": "generated-model",
            "verdict": "ready",
            "files": [artifact("P1/novel-conception-package.json")],
            "artifact_roles": {
                "canonical": artifact("P1/novel-conception-package.json")
            },
            "validation": artifact("P1/validation.json"),
            "implementation": [artifact("skills/assembler/SKILL.md")],
        }
        RUNTIME.assert_invalid(manifest, "package-manifest.schema.json")

    def test_p1_handoff_binding_is_acyclic_and_directional(self) -> None:
        package = {
            "schema_version": "2.0",
            "skill": "novel-conception-deliverable-assembler",
            "stage": "P1",
            "run_id": "RUN-001",
            "status": "ready",
            "input_gate": artifact("P1/input-gate.json"),
            "author_control_baseline": artifact(
                "P1/author-control-baseline.json"
            ),
            "authoritative_design_artifacts": [
                artifact(f"P1/authoritative-design-artifacts/I{index}.md")
                for index in range(6)
            ],
            "canonical_models": {
                stage: artifact(f"P1/canonical-models/{stage}.json")
                for stage in ["S1", "W1", "E1", "T1", "C1"]
            },
            "review": artifact("P1/review/conception-review.json"),
            "cross_model_index": {},
            "authority_partition": {
                "author_locked": [],
                "autonomous_owned": [],
                "downstream_freedom": [],
                "author_open": [],
            },
            "open_items": [],
            "development_handoff": {"path": "development-handoff.json"},
        }
        RUNTIME.assert_valid(
            package, "novel-conception-package.schema.json"
        )
        package["development_handoff"] = artifact(
            "P1/development-handoff.json"
        )
        RUNTIME.assert_invalid(
            package, "novel-conception-package.schema.json"
        )

    def test_actual_author_decision_schema_rejects_branch_smuggling(self) -> None:
        decision = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "approval_scope": "conception",
            "decision": "approved",
            "machine_package": {
                "completion_path": "P1/stage-completion.json",
                "completion_sha256": SHA,
                "manifest_path": "P1/package-manifest.json",
                "manifest_sha256": SHA,
            },
            "human_review_package": {
                "completion_path": "H1/stage-completion.json",
                "completion_sha256": SHA,
                "manifest_path": "H1/package-manifest.json",
                "manifest_sha256": SHA,
                "html_path": "H1/human-review-report.html",
                "html_sha256": SHA,
            },
            "approval_record": {"event_seq": 10, "text": "批准"},
            "unresolved_items": [],
        }
        RUNTIME.assert_valid(decision, "author-decision.schema.json")
        decision["revision_targets"] = []
        RUNTIME.assert_invalid(decision, "author-decision.schema.json")

    def test_actual_final_completion_requires_every_stage(self) -> None:
        completion = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "status": "ready",
            "run_state": artifact("state/run-state.approved.json"),
            "stage_completions": {
                stage: stage_ref(stage)
                for stage in ["B0", "S1", "W1", "E1", "T1", "C1", "Q1", "P1", "H1"]
            },
            "p1_manifest": artifact("P1/package-manifest.json"),
            "h1_html_manifest": artifact("H1/html/package-manifest.json"),
            "author_decision": artifact("approval/author-decision.json"),
            "development_handoff": artifact("P1/development-handoff.json"),
            "validation": artifact("completion/validation.json"),
        }
        RUNTIME.assert_valid(completion, "conception-completion.schema.json")
        del completion["stage_completions"]["E1"]
        RUNTIME.assert_invalid(completion, "conception-completion.schema.json")

    def test_h1_mixed_sessions_fail_semantic_gate(self) -> None:
        workspace = {"session_id": "H1-SESSION-A"}
        manifests = [
            {"session_id": "H1-SESSION-A"},
            {"session_id": "H1-SESSION-B"},
        ]
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_h1_session_consistency(workspace, manifests)

    def test_q1_task_isolation_rejects_same_task_or_leaked_scope(self) -> None:
        review = {
            "task_isolation": {
                "semantic_task_id": "TASK-A",
                "handoff_task_id": "TASK-B",
                "forbidden_reads": [
                    "chat",
                    "interview_reports",
                    "generation_evidence",
                    "semantic_findings",
                    "expected_answers",
                ],
            }
        }
        RUNTIME.assert_q1_task_isolation(review)
        review["task_isolation"]["handoff_task_id"] = "TASK-A"
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_q1_task_isolation(review)

    def test_manifest_roles_must_be_bound_files(self) -> None:
        validation = artifact("P1/validation.json")
        manifest = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "stage": "P1",
            "package_profile": "conception-package",
            "verdict": "ready",
            "files": [
                artifact("P1/novel-conception-package.json"),
                artifact("P1/author-control-baseline.json"),
                artifact("P1/authoritative-design-index.json"),
                artifact("P1/novel-conception-spec.md"),
                artifact("P1/cross-model-index.json"),
                artifact("P1/traceability-matrix.md"),
                artifact("P1/development-handoff.json"),
                artifact("P1/assembly-execution.json"),
                validation,
            ],
            "artifact_roles": {
                "conception_package": artifact("P1/novel-conception-package.json"),
                "author_control_baseline": artifact("P1/author-control-baseline.json"),
                "authoritative_design_index": artifact("P1/authoritative-design-index.json"),
                "spec": artifact("P1/novel-conception-spec.md"),
                "cross_model_index": artifact("P1/cross-model-index.json"),
                "traceability": artifact("P1/traceability-matrix.md"),
                "development_handoff": artifact("P1/development-handoff.json"),
                "execution_record": artifact("P1/assembly-execution.json"),
            },
            "validation": validation,
            "implementation": [artifact("skills/assembler/SKILL.md")],
        }
        RUNTIME.assert_valid(manifest, "package-manifest.schema.json")
        RUNTIME.assert_manifest_semantics(manifest)
        manifest["artifact_roles"]["spec"] = artifact("P1/unbound.md")
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_manifest_semantics(manifest)

    def test_h1_report_has_real_content_and_exact_source_coverage(self) -> None:
        def control(item_id: str, source_id: str) -> dict:
            return {
                "id": item_id,
                "definition": "控制定义",
                "responsibility": "控制故事开发",
                "must_hold": ["必须成立"],
                "must_not_imply": ["不得错误推导"],
                "source_ids": [source_id],
            }

        def visual_model(
            index: int,
            semantic_role: str,
            section_id: str,
            visual_kind: str,
            source_ids: list[str],
        ) -> dict:
            suffix = f"{index:03d}"
            first_node_id = f"NODE-GENERIC-{suffix}-A"
            second_node_id = f"NODE-GENERIC-{suffix}-B"
            edge_id = f"EDGE-GENERIC-{suffix}"
            return {
                "id": f"VIS-GENERIC-{suffix}",
                "semantic_role": semantic_role,
                "section_id": section_id,
                "visual_kind": visual_kind,
                "title": f"Generic review model {index}",
                "review_purpose": "Review a source-bound conception relationship.",
                "groups": [],
                "nodes": [
                    {
                        "id": first_node_id,
                        "order": 1,
                        "group_id": None,
                        "label": "Upstream control",
                        "summary": "A generic source-bound control point.",
                        "kind": "control",
                        "lane": "source",
                        "tier": "primary",
                        "temporal_label": None,
                        "source_ids": source_ids,
                    },
                    {
                        "id": second_node_id,
                        "order": 2,
                        "group_id": None,
                        "label": "Downstream effect",
                        "summary": "A generic source-bound downstream point.",
                        "kind": "effect",
                        "lane": "result",
                        "tier": "secondary",
                        "temporal_label": None,
                        "source_ids": source_ids,
                    },
                ],
                "edges": [
                    {
                        "id": edge_id,
                        "order": 1,
                        "group_id": None,
                        "from_node_id": first_node_id,
                        "to_node_id": second_node_id,
                        "direction": "directed",
                        "relation_label": "constrains",
                        "summary": "The upstream control constrains the downstream effect.",
                        "kind": "constraint",
                        "lane": None,
                        "tier": None,
                        "temporal_label": None,
                        "source_ids": source_ids,
                    }
                ],
                "text_equivalents": [
                    {
                        "id": f"TXT-GENERIC-{suffix}",
                        "order": 1,
                        "element_ids": [first_node_id, edge_id, second_node_id],
                        "text": "Upstream control constrains downstream effect.",
                        "source_ids": source_ids,
                    }
                ],
                "source_ids": source_ids,
                "text_equivalent_module_id": f"MOD-GENERIC-{suffix}",
            }

        report = {
            "schema_version": "2.0",
            "run_id": "RUN-001",
            "h1_session_id": "H1-001",
            "p1_completion": artifact("P1/completion.json"),
            "title": "小说构思评审",
            "review_budget": {
                "target_minutes": 10,
                "estimated_minutes": 8,
                "reading_baseline": "review-reading-baseline-v1",
            },
            "review_path": [
                {
                    "id": "PATH-WORLD",
                    "order": 1,
                    "kind": "world",
                    "title": "Review world controls",
                    "review_question": "Are the world controls coherent?",
                    "estimated_seconds": 90,
                    "visible_element_ids": ["VIS-GENERIC-001"],
                },
                {
                    "id": "PATH-STORYLINES",
                    "order": 2,
                    "kind": "storylines",
                    "title": "Review storyline controls",
                    "review_question": "Do the storylines form a complete architecture?",
                    "estimated_seconds": 90,
                    "visible_element_ids": ["VIS-GENERIC-003", "VIS-GENERIC-004"],
                },
                {
                    "id": "PATH-CHARACTERS",
                    "order": 3,
                    "kind": "characters",
                    "title": "Review character controls",
                    "review_question": "Do the characters cover required story functions?",
                    "estimated_seconds": 90,
                    "visible_element_ids": ["VIS-GENERIC-005"],
                },
                {
                    "id": "PATH-FRAGMENTS",
                    "order": 4,
                    "kind": "fragments",
                    "title": "Review representative fragments",
                    "review_question": "Do the fragments demonstrate the conception?",
                    "estimated_seconds": 90,
                    "visible_element_ids": ["FRAG-001"],
                },
                {
                    "id": "PATH-DECISION",
                    "order": 5,
                    "kind": "decision",
                    "title": "Record the review decision",
                    "review_question": "Should this conception be approved, revised, or rejected?",
                    "estimated_seconds": 90,
                    "visible_element_ids": ["PROMPT-001"],
                },
            ],
            "visual_models": [
                visual_model(
                    1,
                    "control_logic_chain",
                    "SEC-WORLD",
                    "flow",
                    ["WS-001", "EV-001"],
                ),
                visual_model(
                    2,
                    "world_environment_map",
                    "SEC-WORLD",
                    "map",
                    ["ENV-001", "EV-001"],
                ),
                visual_model(
                    3,
                    "storyline_architecture",
                    "SEC-STORYLINES",
                    "network",
                    ["SL-001", "EV-002"],
                ),
                visual_model(
                    4,
                    "major_event_timeline",
                    "SEC-STORYLINES",
                    "timeline",
                    ["EV-001", "EV-002"],
                ),
                visual_model(
                    5,
                    "character_relationship_network",
                    "SEC-CHARACTERS",
                    "network",
                    ["CHR-001", "REL-001"],
                ),
            ],
            "world": {
                "definition": "世界定义",
                "operating_logic": "运行逻辑",
                "systems": [control("VIS-WS-001", "WS-001")],
                "environments": [control("VIS-ENV-001", "ENV-001")],
                "event_conditions": [control("VIS-EV-001", "EV-001")],
                "constraints": ["世界约束"],
                "boundaries": ["世界边界"],
                "source_ids": ["WS-001", "ENV-001", "EV-001"],
            },
            "storylines": {
                "story_subject": "故事主体",
                "lines": [control("VIS-SL-001", "SL-001")],
                "connections": [],
                "major_events": [control("VIS-EV-002", "EV-002")],
                "suspense_conflict_rhythm": "悬念、冲突与起伏",
                "constraints": ["故事约束"],
                "source_ids": ["SL-001", "EV-002"],
            },
            "characters": {
                "core_characters": [control("VIS-CHR-001", "CHR-001")],
                "supporting_characters": [],
                "relationship_networks": [control("VIS-REL-001", "REL-001")],
                "role_coverage": [control("VIS-SLOT-001", "SLOT-001")],
                "constraints": ["人物边界"],
                "source_ids": ["CHR-001", "REL-001", "SLOT-001"],
            },
            "fragments": [
                {
                    "id": "FRAG-001",
                    "title": "评审片段",
                    "review_purpose": "验证人物选择",
                    "text": "人物作出了选择，后果随即发生。",
                    "source_ids": ["EV-002", "CHR-001"],
                }
            ],
            "decision_prompts": [
                {
                    "id": "PROMPT-001",
                    "question": "这是否是你想要的小说？",
                    "affected_source_ids": ["SL-001"],
                    "allowed_decisions": ["approved", "revise", "rejected"],
                }
            ],
            "source_coverage": [
                {"source_id": "WS-001", "visible_element_ids": ["VIS-WS-001"]},
                {"source_id": "ENV-001", "visible_element_ids": ["VIS-ENV-001"]},
                {"source_id": "EV-001", "visible_element_ids": ["VIS-EV-001"]},
                {"source_id": "SL-001", "visible_element_ids": ["VIS-SL-001"]},
                {"source_id": "EV-002", "visible_element_ids": ["VIS-EV-002", "FRAG-001"]},
                {"source_id": "CHR-001", "visible_element_ids": ["VIS-CHR-001", "FRAG-001"]},
                {"source_id": "REL-001", "visible_element_ids": ["VIS-REL-001"]},
                {"source_id": "SLOT-001", "visible_element_ids": ["VIS-SLOT-001"]},
            ],
        }
        RUNTIME.assert_valid(report, "human-review-report.schema.json")
        source_ids = {item["source_id"] for item in report["source_coverage"]}
        RUNTIME.assert_human_review_semantics(
            report,
            authoritative_source_ids=source_ids,
        )
        bad = deepcopy(report)
        bad["source_coverage"][0]["visible_element_ids"] = ["VIS-ENV-001"]
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_human_review_semantics(
                bad,
                authoritative_source_ids=source_ids,
            )

    def test_cross_model_semantics_closes_stage_handoffs(self) -> None:
        s1 = {
            "world_requirements": [{"id": "WR-001"}],
            "environment_requirements": [{"id": "END-S1-001"}],
            "event_requirements": [{"id": "EVD-001"}],
            "character_requirements": [{"id": "CHD-001"}],
            "storylines": [{"id": "SL-001"}],
        }
        w1 = {
            "storyline_requirements": [{"id": "WR-001"}],
            "environment_demands": [
                {"id": "END-S1-001"},
                {"id": "END-W1-001"},
            ],
        }
        e1 = {
            "environment_demands": [
                {"id": "END-S1-001"},
                {"id": "END-W1-001"},
            ],
            "environments": [{"id": "ENV-001"}],
        }
        t1 = {
            "event_demands": [{"id": "EVD-001"}],
            "major_events": [
                {
                    "id": "EV-001",
                    "storyline_ids": ["SL-001"],
                    "environment_id": "ENV-001",
                    "participant_slot_ids": ["SLOT-001"],
                }
            ],
        }
        c1 = {
            "character_demands": [{"id": "CHD-001"}],
            "profiles": [{"id": "CHR-001"}],
            "slot_resolution": [
                {
                    "slot_id": "SLOT-001",
                    "character_id": "CHR-001",
                    "event_ids": ["EV-001"],
                }
            ],
        }
        RUNTIME.assert_cross_model_semantics(s1, w1, e1, t1, c1)
        bad = deepcopy(e1)
        bad["environment_demands"][0]["id"] = "END-WRONG"
        with self.assertRaises(ContractValidationError):
            RUNTIME.assert_cross_model_semantics(s1, w1, bad, t1, c1)


if __name__ == "__main__":
    unittest.main()
