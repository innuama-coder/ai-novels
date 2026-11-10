#!/usr/bin/env python3
"""Validate the proposal workflow contract stays synchronized."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/superpowers/specs/2026-07-05-novel-proposal-contract.json"
HARNESS_DOC = ROOT / "docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md"
WORKFLOW_SKILL = ROOT / "skills/novel-proposal-workflow/SKILL.md"
RISK_CHECKER = ROOT / "skills/novel-proposal-risk-checker/SKILL.md"
INTEGRATOR = ROOT / "skills/novel-proposal-integrator/SKILL.md"
CREATION_DOC = ROOT / "docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing file: {rel(path)}")


def require_terms(label: str, text: str, terms: list[str]) -> None:
    for term in terms:
        if term not in text:
            fail(f"{label} missing required term: {term}")


def manifest_required_terms() -> list[str]:
    return [
        "Proposal workflow artifact run",
        "Harness: `novel-proposal-workflow`",
        "Producer:",
        "Skill version snapshot:",
        "Input digest:",
        "Execution status:",
        "Rerun log:",
        "## Convergence log",
        "Human/intake confirmation snapshot:",
        "Final proposal package:",
        "Integration Verdict artifact:",
        "Risk Report artifact:",
    ]


def require_absent(label: str, text: str, terms: list[str]) -> None:
    for term in terms:
        if term in text:
            fail(f"{label} contains forbidden term: {term}")


def require_section_before(path: Path, text: str, first: str, second: str) -> None:
    first_index = text.find(first)
    second_index = text.find(second)
    if first_index == -1:
        fail(f"{rel(path)} missing section: {first}")
    if second_index == -1:
        fail(f"{rel(path)} missing section: {second}")
    if first_index > second_index:
        fail(f"{rel(path)} must declare {first} before {second}")


def extract_markdown_table_rows(text: str, heading: str) -> list[list[str]]:
    heading_match = re.search(rf"^##+\s+{re.escape(heading)}\s*$", text, re.M)
    if not heading_match:
        fail(f"missing markdown table heading: {heading}")
    section = text[heading_match.end() :]
    next_heading = re.search(r"^##+\s+", section, re.M)
    if next_heading:
        section = section[: next_heading.start()]
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        fail(f"markdown table under {heading} must include header and at least one row")
    return rows


def parse_markdown_table_rows(text: str, heading: str, label: str) -> list[list[str]]:
    heading_match = re.search(rf"^##+\s+{re.escape(heading)}\s*$", text, re.M)
    if not heading_match:
        raise ValueError(f"{label} missing markdown table heading: {heading}")
    section = text[heading_match.end() :]
    next_heading = re.search(r"^##+\s+", section, re.M)
    if next_heading:
        section = section[: next_heading.start()]
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        raise ValueError(f"{label} {heading} table must include header and at least one row")
    return rows


def parse_markdown_table_rows_containing(text: str, heading_fragment: str, label: str) -> list[list[str]]:
    heading_match = re.search(rf"^##+\s+[^\n]*{re.escape(heading_fragment)}[^\n]*$", text, re.M)
    if not heading_match:
        raise ValueError(f"{label} missing markdown table heading containing: {heading_fragment}")
    section = text[heading_match.end() :]
    next_heading = re.search(r"^##+\s+", section, re.M)
    if next_heading:
        section = section[: next_heading.start()]
    rows: list[list[str]] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells or all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    if len(rows) < 2:
        raise ValueError(f"{label} {heading_fragment} table must include header and at least one row")
    return rows


def extract_section(text: str, heading_fragment: str) -> str:
    heading_match = re.search(rf"^##+\s+[^\n]*{re.escape(heading_fragment)}[^\n]*$", text, re.M)
    if not heading_match:
        fail(f"missing markdown section containing heading: {heading_fragment}")
    section = text[heading_match.end() :]
    next_heading = re.search(r"^##+\s+", section, re.M)
    if next_heading:
        section = section[: next_heading.start()]
    if not section.strip():
        fail(f"markdown section is empty: {heading_fragment}")
    return section


def artifact_runs(contract: dict) -> list[dict]:
    runs = contract.get("artifact_runs")
    if runs is not None:
        if not isinstance(runs, list) or not runs:
            raise ValueError("artifact_runs must be a non-empty list")
        return runs
    legacy_run = contract.get("artifact_run")
    if legacy_run:
        return [legacy_run]
    raise ValueError("contract missing artifact_runs")


def row_dicts(rows: list[list[str]], required_headers: list[str], label: str) -> list[dict[str, str]]:
    headers = rows[0]
    missing_headers = [header for header in required_headers if header not in headers]
    if missing_headers:
        raise ValueError(f"{label} missing required table headers: {missing_headers}")
    result: list[dict[str, str]] = []
    for index, row in enumerate(rows[1:], start=2):
        if len(row) != len(headers):
            raise ValueError(f"{label} row {index} has {len(row)} cells, expected {len(headers)}")
        result.append(dict(zip(headers, row)))
    return result


def semantic_length(text: str) -> int:
    return len(re.sub(r"[\s`|，。；、：:,.!?！？“”\"'（）()\[\]《》-]", "", text))


def validate_critical_claim_rows(rows: list[list[str]], label: str) -> list[dict[str, str]]:
    required_headers = [
        "Claim ID",
        "Claim",
        "Constraint role",
        "Evidence quote",
        "Source within artifact",
    ]
    claims = row_dicts(rows, required_headers, label)
    seen_ids: set[str] = set()
    seen_claims: set[str] = set()
    for claim in claims:
        claim_id = claim["Claim ID"]
        claim_text = claim["Claim"]
        constraint_role = claim["Constraint role"]
        evidence_quote = claim["Evidence quote"]
        source = claim["Source within artifact"]
        if not re.fullmatch(r"CLAIM-\d{2,}", claim_id):
            raise ValueError(f"{label} invalid claim id: {claim_id}")
        if claim_id in seen_ids:
            raise ValueError(f"{label} duplicate claim id: {claim_id}")
        if claim_text in seen_claims:
            raise ValueError(f"{label} duplicate claim text: {claim_text}")
        if semantic_length(claim_text) < 18:
            raise ValueError(f"{label} critical claim too short to preserve story logic: {claim_text}")
        if semantic_length(constraint_role) < 8:
            raise ValueError(f"{label} constraint role too short for {claim_id}")
        if semantic_length(evidence_quote) < 8:
            raise ValueError(f"{label} evidence quote too short for {claim_id}")
        if "Complete story synopsis paragraph" not in source:
            raise ValueError(f"{label} source must point into Complete story synopsis paragraphs: {claim_id}")
        seen_ids.add(claim_id)
        seen_claims.add(claim_text)
    return [
        {
            "id": claim["Claim ID"],
            "claim": claim["Claim"],
            "constraint_role": claim["Constraint role"],
            "evidence_quote": claim["Evidence quote"],
            "source": claim["Source within artifact"],
        }
        for claim in claims
    ]


def canonical_claim_map(claims: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {claim["id"]: claim for claim in claims}


def validate_artifact_dag(graph: list[dict], label: str) -> None:
    if not isinstance(graph, list) or not graph:
        raise ValueError(f"{label} must be a non-empty list")
    nodes: dict[str, set[str]] = {}
    for node in graph:
        node_id = str(node.get("id", "")).strip()
        if not node_id:
            raise ValueError(f"{label} node missing id")
        if node_id in nodes:
            raise ValueError(f"{label} duplicate node id: {node_id}")
        depends_on = node.get("depends_on", [])
        if not isinstance(depends_on, list):
            raise ValueError(f"{label} node {node_id} depends_on must be a list")
        nodes[node_id] = {str(dep).strip() for dep in depends_on}
    for node_id, deps in nodes.items():
        missing = deps - set(nodes)
        if missing:
            raise ValueError(f"{label} node {node_id} depends on unknown artifacts: {sorted(missing)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str, path: list[str]) -> None:
        if node_id in visiting:
            cycle = " -> ".join(path + [node_id])
            raise ValueError(f"{label} contains dependency cycle: {cycle}")
        if node_id in visited:
            return
        visiting.add(node_id)
        for dep in sorted(nodes[node_id]):
            visit(dep, path + [node_id])
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(nodes):
        visit(node_id, [])


def artifact_dependency_map(graph: list[dict]) -> dict[str, set[str]]:
    return {
        str(node.get("id", "")).strip(): {str(dep).strip() for dep in node.get("depends_on", [])}
        for node in graph
    }


def validate_proposal_artifact_topology(graph: list[dict], label: str) -> None:
    validate_artifact_dag(graph, label)
    deps = artifact_dependency_map(graph)
    required_ids = {f"{index:02d}" for index in range(1, 15)} | {"final-proposal-package"}
    missing_ids = required_ids - set(deps)
    if missing_ids:
        raise ValueError(f"{label} missing required proposal artifact ids: {sorted(missing_ids)}")

    expected_13 = {f"{index:02d}" for index in range(1, 13)}
    if deps["13"] != expected_13:
        raise ValueError(
            f"{label} artifact 13 must depend exactly on artifacts 01-12; got {sorted(deps['13'])}"
        )
    expected_14 = {"01", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"}
    if deps["14"] != expected_14:
        raise ValueError(
            f"{label} artifact 14 must depend exactly on risk-check inputs 01, 04-13; "
            f"got {sorted(deps['14'])}"
        )
    if "14" in deps["13"]:
        raise ValueError(f"{label} artifact 13 must not depend on artifact 14")
    if deps["final-proposal-package"] != {"13", "14"}:
        raise ValueError(
            f"{label} final-proposal-package must depend exactly on artifacts 13 and 14; "
            f"got {sorted(deps['final-proposal-package'])}"
        )


def allowed_dependency_ids(graph: list[dict], artifact_id: str) -> set[str]:
    by_id = {str(node.get("id", "")).strip(): node for node in graph}
    if artifact_id not in by_id:
        raise ValueError(f"artifact graph missing artifact id: {artifact_id}")
    return {str(dep).strip() for dep in by_id[artifact_id].get("depends_on", [])}


def validate_section_source_dependencies(
    rows: list[list[str]],
    *,
    current_artifact_id: str,
    allowed_dependency_ids: set[str],
    label: str,
) -> None:
    entries = row_dicts(rows, ["Proposal section", "Source artifact"], label)
    for entry in entries:
        source = entry["Source artifact"]
        for artifact_id in re.findall(r"artifact\s+(\d+)", source):
            if artifact_id == current_artifact_id:
                raise ValueError(f"{label} cannot cite itself as a source artifact: {artifact_id}")
            if artifact_id not in allowed_dependency_ids:
                raise ValueError(
                    f"{label} cites non-dependency artifact {artifact_id}; "
                    f"allowed dependencies are {sorted(allowed_dependency_ids)}"
                )


def validate_claim_trace_rows(
    canonical_claims: dict[str, dict[str, str]],
    downstream_rows: list[dict[str, str]],
    label: str,
    *,
    require_constraint_role: bool,
) -> None:
    seen_ids: set[str] = set()
    for row in downstream_rows:
        claim_id = row["Claim ID"]
        if claim_id in seen_ids:
            raise ValueError(f"{label} duplicate claim id: {claim_id}")
        seen_ids.add(claim_id)
        if claim_id not in canonical_claims:
            raise ValueError(f"{label} contains extra untraced claim id: {claim_id}")
        canonical = canonical_claims[claim_id]
        downstream_claim = row["Critical business claim"]
        if downstream_claim != canonical["claim"]:
            raise ValueError(
                f"{label} claim text drift for {claim_id}: "
                f"expected {canonical['claim']} got {downstream_claim}"
            )
        if require_constraint_role:
            downstream_role = row["Constraint role"]
            if downstream_role != canonical["constraint_role"]:
                raise ValueError(
                    f"{label} constraint role drift for {claim_id}: "
                    f"expected {canonical['constraint_role']} got {downstream_role}"
                )
    missing_ids = set(canonical_claims) - seen_ids
    if missing_ids:
        raise ValueError(f"{label} missing canonical claim ids: {sorted(missing_ids)}")


def validate_final_proposal_claim_source_map(
    proposal_text: str,
    canonical_claims: dict[str, dict[str, str]],
    label: str,
) -> None:
    rows = parse_markdown_table_rows_containing(proposal_text, "Claim Source Map", label)
    proposal_claims = row_dicts(
        rows,
        ["Claim ID", "Critical business claim", "Upstream source", "Constraint role"],
        f"{label} Claim Source Map",
    )
    validate_claim_trace_rows(
        canonical_claims,
        proposal_claims,
        f"{label} Claim Source Map",
        require_constraint_role=True,
    )
    for row in proposal_claims:
        if "artifact 04" not in row["Upstream source"]:
            raise ValueError(f"{label} Claim Source Map missing canonical artifact 04 source: {row['Claim ID']}")


def unquote_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def field_value_map(rows: list[list[str]], label: str) -> dict[str, str]:
    entries = row_dicts(rows, ["Field", "Value"], label)
    return {entry["Field"]: unquote_cell(entry["Value"]) for entry in entries}


def validate_risk_verdict_consistency(risk_report_text: str, label: str) -> None:
    output_rows = parse_markdown_table_rows(risk_report_text, "Output", label)
    output = field_value_map(output_rows, f"{label} Output")
    risk_rows = parse_markdown_table_rows(risk_report_text, "Risks", label)
    risks = row_dicts(risk_rows, ["Risk", "Severity", "Handling"], f"{label} Risks")
    blocking_risks = [risk for risk in risks if unquote_cell(risk["Severity"]) in {"P0", "P1"}]
    agent_verdict = output.get("Agent quality verdict")
    human_verdict = output.get("Human/intake confirmation verdict")
    prd_verdict = output.get("PRD entry verdict")
    if not agent_verdict:
        raise ValueError(f"{label} missing Agent quality verdict")
    if not human_verdict:
        raise ValueError(f"{label} missing Human/intake confirmation verdict")
    if not prd_verdict:
        raise ValueError(f"{label} missing PRD entry verdict")
    if blocking_risks and agent_verdict == "pass":
        names = [risk["Risk"] for risk in blocking_risks]
        raise ValueError(f"{label} Agent quality verdict cannot pass with unresolved P0/P1 risks: {names}")
    if blocking_risks and prd_verdict == "pass_to_prd":
        raise ValueError(f"{label} PRD entry verdict cannot pass with unresolved P0/P1 risks")
    if agent_verdict == "pass" and human_verdict == "pending" and prd_verdict != "blocked_pending_human_confirmation":
        raise ValueError(f"{label} pending human confirmation must block PRD entry")
    if agent_verdict != "pass" and prd_verdict == "pass_to_prd":
        raise ValueError(f"{label} PRD entry cannot pass unless Agent quality verdict passes")


def validate_no_legacy_integrated_proposal_terms(text: str, label: str) -> None:
    match = re.search(r"\bintegrated proposal\b", text, re.I)
    if match:
        raise ValueError(f"{label} contains legacy integrated proposal term: {match.group(0)}")


def validate_convergence_log(manifest_text: str, label: str) -> None:
    rows = parse_markdown_table_rows(manifest_text, "Convergence log", label)
    entries = row_dicts(
        rows,
        [
            "Stable issue id",
            "Root cause",
            "Fix hypothesis",
            "Regression proof",
            "Attempt count",
            "Versioned refactor trigger",
        ],
        f"{label} Convergence log",
    )
    for entry in entries:
        issue_id = entry["Stable issue id"]
        root_cause = entry["Root cause"]
        fix_hypothesis = entry["Fix hypothesis"]
        regression_proof = entry["Regression proof"]
        attempt_count_text = entry["Attempt count"]
        refactor_trigger = entry["Versioned refactor trigger"]
        if not issue_id:
            raise ValueError(f"{label} Convergence log row missing Stable issue id")
        if not root_cause:
            raise ValueError(f"{label} Convergence log row missing Root cause: {issue_id}")
        if not fix_hypothesis:
            raise ValueError(f"{label} Convergence log row missing Fix hypothesis: {issue_id}")
        if not regression_proof:
            raise ValueError(f"{label} Convergence log row missing Regression proof: {issue_id}")
        if not re.fullmatch(r"[1-9]\d*", attempt_count_text):
            raise ValueError(f"{label} Convergence log invalid Attempt count for {issue_id}: {attempt_count_text}")
        if int(attempt_count_text) >= 3 and not refactor_trigger:
            raise ValueError(f"{label} Convergence log {issue_id} requires Versioned refactor trigger")


def main() -> None:
    contract = json.loads(read(CONTRACT_PATH))
    expected_static_checks = {
        "proposal_skill_count_matches_design_doc",
        "all_hard_gate_owners_are_independent_skills",
        "all_proposal_skills_have_required_contract_sections",
        "harness_and_design_docs_do_not_own_business_gates",
        "harness_routing_gate_is_not_business_acceptance",
        "integrator_and_risk_checker_inputs_match_contract",
        "risk_checker_blocks_missing_evidence_and_consistency_report",
        "canonical_reference_evidence_term_only",
        "canonical_story_evidence_terms_absent",
        "all_proposal_skills_have_boundary_section",
        "storyline_terminal_agency_split_required",
        "integration_gate_has_independent_proof",
        "risk_checker_consumes_integration_verdict",
        "harness_packages_integration_verdict",
        "proposal_artifact_run_manifest_required",
        "all_proposal_skill_outputs_have_independent_artifacts",
        "proposal_artifact_schema_fields_required",
        "integration_verdict_has_section_source_map",
        "integration_claim_source_map_required",
        "storyline_critical_business_claims_required",
        "critical_business_claim_schema_required",
        "claim_trace_canonical_consistency_required",
        "artifact_runs_list_supported",
        "sample_critical_claims_trace_to_storyline_artifact",
        "risk_report_claim_source_map_coverage_required",
        "proposal_convergence_protocol_required",
        "convergence_log_schema_required",
        "convergence_log_refactor_trigger_required",
        "negative_contract_tests_required",
        "artifact_dag_required",
        "artifact_dag_acyclic_required",
        "proposal_artifact_topology_required",
        "artifact_source_dependency_required",
        "final_proposal_claim_source_map_required",
        "risk_verdict_consistency_required",
        "legacy_integrated_proposal_terms_absent",
        "risk_watch_item_count_matches_quality_report",
        "manifest_execution_metadata_required",
        "harness_dispatch_owner_points_to_business_skills",
        "terminal_agency_legacy_terms_absent",
        "sample_storyline_reference_evidence_has_multiple_dimensions",
        "sample_terminal_agency_map_required",
        "sample_proposal_contains_required_gate_proof",
    }
    actual_static_checks = set(contract.get("static_checks", []))
    missing_static_checks = expected_static_checks - actual_static_checks
    if missing_static_checks:
        fail(f"contract static_checks missing: {sorted(missing_static_checks)}")

    for skill in contract["skills"]:
        skill_path = ROOT / "skills" / skill / "SKILL.md"
        if not skill_path.exists():
            fail(f"contract skill has no SKILL.md: {skill}")
        skill_text = read(skill_path)
        for section in [
            "## Responsibility",
            "## Input",
            "## Output",
            "## Rules",
            "## Boundary",
            "## References",
            "## Traceability",
            "## Acceptance",
        ]:
            if section not in skill_text:
                fail(f"{skill} missing required independent-skill section: {section}")

    for gate in contract["hard_gates"]:
        if gate["owner_type"] != "independent_skill":
            fail(f"hard gate must be owned by an independent skill: {gate['id']}")
        owner_path = ROOT / "skills" / gate["owner"] / "SKILL.md"
        if not owner_path.exists():
            fail(f"gate owner has no SKILL.md: {gate['id']} -> {gate['owner']}")

    harness_doc = read(HARNESS_DOC)
    forbidden_harness_doc_patterns = [
        "生成边界账本、拆分构思任务",
        "与已验收故事线冲突或 consistency checker 不通过则定向重跑",
        "与已验收故事线、final reader promise 或 final core concept 冲突则定向重跑",
        "final promise/concept 冲突",
        "故事线缺少欲望",
        "提供故事证据",
        "harness 不自行判定业务质量。未解决 P0/P1",
    ]
    require_absent("harness design doc", harness_doc, forbidden_harness_doc_patterns)
    require_terms(
        "harness design doc",
        harness_doc,
        [
            "调度 boundary ledger 技能",
            "按独立技能 verdict 路由",
            "reference evidence",
        ],
    )
    count_pattern = re.compile(r"\|\s*proposal\s*\|\s*`novel-proposal-workflow`\s*\|\s*(\d+)\s*\|")
    count_match = count_pattern.search(harness_doc)
    if not count_match:
        fail("cannot find proposal skill count in harness design doc")
    if int(count_match.group(1)) != int(contract["proposal_skill_count"]):
        fail(
            "proposal skill count mismatch: "
            f"doc={count_match.group(1)} contract={contract['proposal_skill_count']}"
        )

    workflow = read(WORKFLOW_SKILL)
    forbidden_harness_patterns = [
        "Verify final reader promise and final core concept are mutually consistent | harness",
        "并校验二者互相一致",
        "pending harness verification",
        "| 3 | Dispatch pre-story reader promise and core concept hypotheses with the ledger attached | harness |",
        "| 5 | Dispatch final reader promise and final core concept using the accepted storyline | harness |",
        "| 7 | Dispatch macro, character, world, and ending skills using the accepted storyline plus final promise/concept | harness |",
        "Reject or rerun any skill output that violates upstream constraints",
        "Final reader promise, final concept, macro, character, world, or ending output contradicts",
        "Two or more business outputs contradict each other",
        "## Acceptance Gate",
        "Reject the proposal if:",
        "The proposal lacks a readable complete story synopsis",
        "The proposal lacks a main story chain",
        "The proposal lacks enough suspense and conflict layers",
        "The proposal explains key conflict",
        "The proposal uses abstract theme lines",
        "The proposal includes trunk scenes",
    ]
    require_absent("workflow", workflow, forbidden_harness_patterns)

    required_workflow_terms = [
        "novel-final-promise-concept-consistency-checker",
        "reference evidence",
        "Final promise/concept consistency report",
        "Integration Verdict",
        "## Routing Gate",
        "It must not independently judge story quality",
        "only when an independent output says so",
        "## Convergence Protocol",
        "Stable issue id",
        "Root cause",
        "Fix hypothesis",
        "Regression proof",
        "Versioned refactor trigger",
    ]
    require_terms("workflow", workflow, required_workflow_terms)

    storyline_designer = read(ROOT / "skills/novel-storyline-designer/SKILL.md")
    require_absent(
        "storyline designer",
        storyline_designer,
        [
            "The protagonist's decisive choice",
            "what the protagonist is trying to do",
            "final choice",
            "final choices",
        ],
    )
    require_terms(
        "storyline designer",
        storyline_designer,
        [
            "Critical business claims",
            "Terminal agency map",
            "focal character",
            "thematic subject",
            "information holder",
            "emotional carrier",
            "final decision owner",
            "final executor",
            "irreversible consequence bearer",
        ],
    )

    for skill in [
        "novel-storyline-quality-evaluator",
        "novel-final-promise-concept-consistency-checker",
        "novel-macro-structure-designer",
        "novel-ending-direction-designer",
        "novel-core-character-framer",
        "novel-world-premise-framer",
        "novel-proposal-integrator",
        "novel-proposal-risk-checker",
    ]:
        skill_text = read(ROOT / "skills" / skill / "SKILL.md")
        require_terms(skill, skill_text, ["Terminal agency map"])
    storyline_quality_evaluator = read(ROOT / "skills/novel-storyline-quality-evaluator/SKILL.md")
    require_terms(
        "storyline quality evaluator",
        storyline_quality_evaluator,
        [
            "Critical business claims",
            "Critical business claims assessment",
        ],
    )

    proposal_contract_paths = [
        HARNESS_DOC,
        WORKFLOW_SKILL,
    ] + [ROOT / "skills" / skill / "SKILL.md" for skill in contract["skills"]]
    legacy_agency_terms = [
        "protagonist",
        "final choice",
        "主角",
        "终局选择",
    ]
    for path in proposal_contract_paths:
        skill_text = read(path)
        require_absent(rel(path), skill_text, ["pending harness verification"])
        require_absent(rel(path), skill_text, legacy_agency_terms)

    reader_promise = read(ROOT / "skills/novel-reader-promise-designer/SKILL.md")
    core_concept = read(ROOT / "skills/novel-core-concept-designer/SKILL.md")
    require_absent(
        "finalization skills",
        reader_promise + core_concept,
        ["`pending_consistency_check` until the independent consistency checker passes"],
    )
    require_terms(
        "finalization skills",
        reader_promise + core_concept,
        ["draft_complete_pending_consistency"],
    )

    integrator = read(INTEGRATOR)
    require_section_before(INTEGRATOR, integrator, "## Input", "## Output")
    require_terms(
        rel(INTEGRATOR),
        integrator,
        [
            "Intake boundary ledger with readiness verdict",
            "Storyline quality report with reference evidence",
            "Final promise/concept consistency report",
            "All proposal expansion outputs",
        ],
    )

    risk_checker = read(RISK_CHECKER)
    require_section_before(RISK_CHECKER, risk_checker, "## Input", "## Output")
    require_terms(
        rel(RISK_CHECKER),
        risk_checker,
        [
            "Proposal assembly artifact",
            "Intake boundary ledger with readiness verdict",
            "Storyline quality report with reference evidence",
            "Final promise/concept consistency report",
        ],
    )
    required_risk_terms = [
        "evidence-free storyline quality report",
        "Missing or non-passing final promise/concept consistency report",
        "Final reader promise and final core concept contradict each other",
        "Integration Verdict",
    ]
    require_terms("risk checker", risk_checker, required_risk_terms)

    gate_inputs = {gate["id"]: set(gate["input"]) for gate in contract["hard_gates"]}
    gates_by_id = {gate["id"]: gate for gate in contract["hard_gates"]}
    integration_proof = gates_by_id["GATE-INTEGRATION"].get("sample_proof_required")
    if integration_proof != "Integration Verdict":
        fail("GATE-INTEGRATION must require independent Integration Verdict proof")
    expected_integration_inputs = {
        "all proposal skill outputs",
        "storyline quality report",
        "final promise/concept consistency report",
        "intake boundary ledger with readiness verdict",
        "accepted storyline",
        "all proposal expansion outputs",
    }
    if not expected_integration_inputs.issubset(gate_inputs["GATE-INTEGRATION"]):
        fail("GATE-INTEGRATION input does not match integrator contract")
    expected_final_risk_inputs = {
        "proposal assembly artifact",
        "intake boundary ledger with readiness verdict",
        "accepted storyline",
        "storyline quality report",
        "final promise/concept consistency report",
        "integration verdict",
        "all proposal expansion outputs",
        "human/intake confirmation status",
    }
    if not expected_final_risk_inputs.issubset(gate_inputs["GATE-FINAL-RISK"]):
        fail("GATE-FINAL-RISK input does not match risk checker contract")
    if "integration verdict" not in gate_inputs["GATE-FINAL-RISK"]:
        fail("GATE-FINAL-RISK must consume integration verdict as an explicit input")

    try:
        runs = artifact_runs(contract)
    except ValueError as exc:
        fail(str(exc))

    artifact_requirements = {
        "01-intake-boundary-ledger.md": [
            "Intake source",
            "Frozen constraints",
            "Conflict seeds",
            "Reference rules",
            "Open questions",
            "Non-frozen material",
            "Readiness verdict",
            "Gate result",
            "Readiness evidence",
            "Reopen triggers",
        ],
        "02-reader-promise-pre-story.md": [
            "Audience hypothesis",
            "Conflict promise",
            "Compatibility status",
            "Boundary trace",
        ],
        "03-core-concept-pre-story.md": [
            "Logline",
            "Core question",
            "Hook",
            "Human motive anchor",
            "Constraint trace",
        ],
        "04-storyline-design.md": [
            "Complete story synopsis",
            "Critical business claims",
            "Focal character and POV rule",
            "Terminal agency map",
            "Main story chain",
            "Story driver",
            "Suspense and conflict layers",
            "Human motive anchor",
            "Turning logic",
            "Terminal choice and outcome",
            "Auxiliary storyline list",
            "Constraint trace",
        ],
        "05-storyline-quality-report.md": [
            "Verdict",
            "Gate result",
            "Severity counts",
            "Pass conditions checked",
            "Reference assessment",
            "Reference Evidence",
            "Critical business claims assessment",
            "Terminal agency assessment",
            "Blocking issues",
            "Revision targets",
            "Strengths",
        ],
        "06-reader-promise-final.md": [
            "Audience hypothesis",
            "Conflict promise",
            "Compatibility status",
            "Compatibility note",
            "Boundary trace",
        ],
        "07-core-concept-final.md": [
            "Logline",
            "Core question",
            "Hook",
            "Human motive anchor",
            "Compatibility status",
            "Compatibility note",
            "Constraint trace",
        ],
        "08-final-promise-concept-consistency.md": [
            "Verdict",
            "Gate result",
            "Compatibility status",
            "Evidence",
            "Conflict findings",
            "Terminal agency findings",
            "Revision target",
        ],
        "09-macro-structure.md": [
            "Structure model",
            "Movement logic",
            "Conflict escalation",
            "PRD candidates",
            "Constraint trace",
        ],
        "10-core-character-frame.md": [
            "Core roles",
            "Relationship frame",
            "Motive pressure",
            "Terminal agency map",
            "Change direction",
            "Constraint trace",
        ],
        "11-world-premise.md": [
            "World premise",
            "Necessary rules",
            "Pressure function",
            "Unknowns",
            "Constraint trace",
        ],
        "12-ending-direction.md": [
            "Ending type",
            "Irreversible items",
            "Terminal agency map",
            "Thematic payoff",
            "Motive payoff",
            "Series hook",
            "Constraint trace",
        ],
        "13-proposal-integrator.md": [
            "Integration Verdict",
            "Section Source Map",
            "Claim Source Map",
            "Boundary ledger | artifact 01",
            "Complete story synopsis | artifact 04",
            "Reference Evidence | artifact 05",
            "Final promise/concept consistency report | artifact 08",
            "Macro structure | artifact 09",
            "Core character frame | artifact 10",
            "World premise | artifact 11",
            "Ending direction | artifact 12",
        ],
        "14-proposal-risk-checker.md": [
            "Constraint violations",
            "Conflict seed handling",
            "Open question handling",
            "Boundary risks",
            "Completeness risks",
            "PRD readiness",
            "Storyline quality",
            "Final promise/concept consistency",
            "Integration Verdict",
            "Claim Source Map coverage",
            "Agent quality verdict",
            "Human/intake confirmation verdict",
            "PRD entry verdict",
        ],
    }

    for artifact_run in runs:
        run_id = artifact_run.get("id", "<unknown>")
        manifest = artifact_run.get("manifest")
        if not manifest:
            fail(f"artifact_run {run_id} missing manifest")
        manifest_path = ROOT / manifest
        manifest_text = read(manifest_path)
        require_terms(
            manifest,
            manifest_text,
            manifest_required_terms(),
        )
        try:
            validate_convergence_log(manifest_text, manifest)
        except ValueError as exc:
            fail(str(exc))
        artifact_dag = artifact_run.get("artifact_dag")
        try:
            validate_proposal_artifact_topology(artifact_dag, f"artifact_run {run_id} artifact_dag")
        except ValueError as exc:
            fail(str(exc))
        skill_artifacts = artifact_run.get("skill_artifacts", {})
        missing_artifact_entries = set(contract["skills"]) - set(skill_artifacts)
        if missing_artifact_entries:
            fail(f"artifact_run {run_id} missing skill_artifacts: {sorted(missing_artifact_entries)}")
        for skill in contract["skills"]:
            entries = skill_artifacts.get(skill)
            if not isinstance(entries, list) or not entries:
                fail(f"artifact_run {run_id} skill must map to non-empty list: {skill}")
            for entry in entries:
                artifact_path = ROOT / entry
                artifact_text = read(artifact_path)
                require_terms(
                    entry,
                    artifact_text,
                    [
                        f"Skill: `{skill}`",
                        "Output artifact:",
                        "Source inputs:",
                        "Traceability:",
                        "Verdict:",
                    ],
                )
                require_terms(
                    entry,
                    artifact_text,
                    artifact_requirements.get(artifact_path.name, []),
                )

    creation_doc = read(CREATION_DOC)
    canonical_paths = [
        CREATION_DOC,
        HARNESS_DOC,
        WORKFLOW_SKILL,
        INTEGRATOR,
        RISK_CHECKER,
    ] + [ROOT / "skills" / skill / "SKILL.md" for skill in contract["skills"]]
    for path in canonical_paths:
        text = read(path)
        if "story evidence" in text or "故事证据" in text:
            fail(f"{rel(path)} must use 'reference evidence', not story-evidence wording")

    for artifact_run in runs:
        skill_artifacts = artifact_run["skill_artifacts"]
        sample_path = artifact_run.get("final_proposal_package") or artifact_run.get("integrated_proposal") or contract["sample_proposal"]
        sample = read(ROOT / sample_path)
        storyline_artifact = read(ROOT / skill_artifacts["novel-storyline-designer"][0])
        quality_report = read(ROOT / skill_artifacts["novel-storyline-quality-evaluator"][0])
        integration_artifact = read(ROOT / skill_artifacts["novel-proposal-integrator"][0])
        risk_report = read(ROOT / skill_artifacts["novel-proposal-risk-checker"][0])
        try:
            validate_no_legacy_integrated_proposal_terms(risk_checker + risk_report, "risk checker contract/artifact")
        except ValueError as exc:
            fail(str(exc))

        critical_claim_rows = extract_markdown_table_rows(storyline_artifact, "Critical business claims")
        try:
            critical_claims = validate_critical_claim_rows(
                critical_claim_rows,
                f"{artifact_run.get('id', '<unknown>')} Critical business claims",
            )
        except ValueError as exc:
            fail(str(exc))
        if not critical_claims:
            fail("storyline artifact Critical business claims table has no claims")

        storyline_synopsis = extract_section(storyline_artifact, "Complete story synopsis")
        sample_synopsis = extract_section(sample, "完整故事梗概")
        quality_claim_rows = extract_markdown_table_rows(quality_report, "Critical business claims assessment")
        integration_source_rows = extract_markdown_table_rows(integration_artifact, "Section Source Map")
        integration_claim_rows = extract_markdown_table_rows(integration_artifact, "Claim Source Map")
        risk_claim_rows = extract_markdown_table_rows(risk_report, "Claim Source Map coverage")
        try:
            artifact_dag = artifact_run["artifact_dag"]
            validate_section_source_dependencies(
                integration_source_rows,
                current_artifact_id="13",
                allowed_dependency_ids=allowed_dependency_ids(artifact_dag, "13"),
                label="integration Section Source Map",
            )
            canonical_claims = canonical_claim_map(critical_claims)
            quality_claims = row_dicts(
                quality_claim_rows,
                ["Claim ID", "Critical business claim", "Constraint role", "Synopsis support", "Judgment"],
                "storyline quality Critical business claims assessment",
            )
            integration_claims = row_dicts(
                integration_claim_rows,
                ["Claim ID", "Critical business claim", "Upstream source", "Constraint role"],
                "integration Claim Source Map",
            )
            risk_claims = row_dicts(
                risk_claim_rows,
                ["Claim ID", "Critical business claim", "Constraint role", "Coverage verdict", "Evidence"],
                "risk Claim Source Map coverage",
            )
            validate_claim_trace_rows(
                canonical_claims,
                quality_claims,
                "storyline quality Critical business claims assessment",
                require_constraint_role=True,
            )
            validate_claim_trace_rows(
                canonical_claims,
                integration_claims,
                "integration Claim Source Map",
                require_constraint_role=True,
            )
            validate_claim_trace_rows(
                canonical_claims,
                risk_claims,
                "risk Claim Source Map coverage",
                require_constraint_role=True,
            )
            validate_final_proposal_claim_source_map(
                sample,
                canonical_claims,
                sample_path,
            )
            validate_risk_verdict_consistency(risk_report, "risk report")
        except ValueError as exc:
            fail(str(exc))

        for claim in critical_claims:
            claim_id = claim["id"]
            claim_text = claim["claim"]
            evidence_quote = claim["evidence_quote"]
            if evidence_quote not in storyline_synopsis:
                fail(f"storyline synopsis missing evidence quote for {claim_id}: {evidence_quote}")
            if evidence_quote not in sample_synopsis:
                fail(f"sample proposal synopsis missing evidence quote for {claim_id}: {evidence_quote}")
            if claim_id not in sample or claim_text not in sample:
                fail(f"sample proposal Claim Source Map missing critical claim text: {claim_id}")
        if "Claim Source Map coverage" not in risk_report:
            fail("risk report must explicitly check Claim Source Map coverage")

        p2_match = re.search(r"P2=(\d+)", quality_report)
        if not p2_match:
            fail("storyline quality report missing P2 severity count")
        declared_p2 = int(p2_match.group(1))
        risk_p2_rows = len(re.findall(r"^\|[^|\n]+\|\s*P2\s*\|", risk_report, re.M))
        if declared_p2 != risk_p2_rows:
            fail(
                "risk report P2 watch item count mismatch: "
                f"quality_report={declared_p2} risk_report_rows={risk_p2_rows}"
            )
        for gate in contract["hard_gates"]:
            proof = gate["sample_proof_required"]
            if proof not in sample:
                fail(f"sample proposal missing gate proof: {gate['id']} -> {proof}")
        require_terms(
            sample_path,
            sample,
            [
                "Readiness verdict",
                "故事线质量 verdict：`pass`",
                "Reference Evidence",
                "Final promise/concept consistency verdict：`pass`",
                "| Agent quality verdict | `pass` |",
                "| PRD entry verdict | `blocked_pending_human_confirmation` |",
                "无未解决 P0/P1",
            ],
        )
        reference_section_match = re.search(
            r"^#{2,6}\s+[^\n]*Reference Evidence[^\n]*\n(?P<section>.*?)(?=^##\s|\Z)",
            sample,
            re.S | re.M,
        )
        if not reference_section_match:
            fail("sample proposal missing dedicated storyline Reference Evidence section")
        reference_section = reference_section_match.group("section")
        required_reference_dimensions = [
            "可连续阅读",
            "具体角色承压",
            "欲望、阻碍、升级、反转",
            "人性动机锚点",
            "视角控制",
            "终局因果",
        ]
        require_terms(
            "sample proposal Reference Evidence",
            reference_section,
            required_reference_dimensions,
        )
        require_terms(
            "sample proposal terminal agency map",
            sample,
            [
                "Terminal Agency Map",
                "主视角人物",
                "命题主体",
                "信息持有者",
                "情感承受者",
                "最终决策者",
                "最终执行者",
                "不可逆后果承担者",
            ],
        )

    print("proposal contract is valid")


if __name__ == "__main__":
    main()
