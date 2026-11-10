#!/usr/bin/env python3
"""Validate the PRD workflow contract stays synchronized."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOVEL = ROOT.parent / "duanxian"


def resolve_recorded_path(relative: str) -> Path:
    """契约登记的运行产物路径：docs/superpowers/runs/* 现居 duanxian/design/runs/*。"""
    prefix = "docs/superpowers/runs/"
    text = str(relative)
    if text.startswith(prefix):
        return NOVEL / "design/runs" / text[len(prefix):]
    return ROOT / text


CONTRACT_PATH = ROOT / "docs/superpowers/specs/2026-07-06-novel-prd-contract.json"
HARNESS_DOC = ROOT / "docs/superpowers/specs/2026-07-05-novel-harness-workflows-and-skills-design.md"
CREATION_DOC = ROOT / "docs/superpowers/specs/2026-07-05-novel-creation-workflow-design.md"
WORKFLOW_SKILL = ROOT / "skills/novel-prd-workflow/SKILL.md"
CAUSALITY_CHECKER = ROOT / "skills/novel-prd-causality-checker/SKILL.md"
INTEGRATOR = ROOT / "skills/novel-prd-integrator/SKILL.md"
PRD_CONTRACT_TESTS = ROOT / "tests/test_validate_prd_contract.py"

REQUIRED_STATIC_CHECKS = {
    "proposal_claim_fact_trace_required",
    "core_check_failure_blocks_as_p0_p1_required",
    "prd_skill_verdict_required",
    "prd_artifact_source_closure_required",
    "prd_integration_verdict_required",
    "structured_source_reference_grammar_required",
    "prd_risk_checker_skill_verdict_required",
    "hld_entry_verdict_state_machine_required",
    "formal_prd_full_claim_map_validation_required",
    "contract_rule_coverage_matrix_required",
    "pre_extraction_causal_setup_required",
    "scene_execution_table_required",
    "story_logic_boundary_table_required",
    "story_logic_plausibility_anchors_required",
    "upstream_required_hld_entities_required",
    "hld_fact_atom_entity_registry_closure_required",
    "hld_information_obligation_coverage_required",
    "hld_expansion_requirement_final_package_integration_required",
    "hld_expansion_requirement_identity_and_scene_source_closure_required",
    "story_logic_hld_handoff_closure_required",
}

SKILL_VERDICT_FIELDS = [
    "Skill quality verdict",
    "Source closure",
    "Boundary obedience",
    "Downstream readiness",
    "Blocking issue",
    "Rerun target",
]

SKILL_QUALITY_VERDICTS = {"pass", "revise_own_output", "reopen_upstream"}
PASS_FAIL = {"pass", "fail"}
AGENT_QUALITY_VERDICTS = {"pass", "revise_skill_output", "reopen_proposal"}
HUMAN_REVIEW_VERDICTS = {"confirmed", "pending", "reopen_prd"}
HLD_ENTRY_VERDICTS = {"pass_to_hld", "blocked_pending_human_review", "blocked_revision_required"}
UPSTREAM_FACT_ID_PATTERN = re.compile(r"UPF-PRD-(S\d{2,})-\d{2,}")
HLD_REQUIREMENT_ID_PATTERN = re.compile(r"HLD-REQ-\d{2,}")
REQUIRED_HLD_ENTITY_TYPES = {
    "character",
    "group",
    "environment",
    "event",
    "rule",
    "information object",
    "time layer",
    "thread",
    "style/pov rule",
    "unresolved amendment",
}
UPSTREAM_FACT_SOURCE_FIELDS = {
    "Entry state": "entry_state",
    "Roles": "roles",
    "Environment": "environment",
    "Event": "event",
    "Causal output": "causal_output",
    "Scene content": "scene_content",
    "Previous dependency": "previous_dependency",
    "Next pressure": "next_pressure",
    "Indispensability proof": "indispensability_proof",
}
HLD_INFORMATION_BOUNDARY_COLUMNS = [
    "Information boundary id",
    "Story anchor scene id",
    "Narrative reveal scene id",
    "Narrative reveal order",
    "Disclosure tier",
    "Information object",
    "Reader access",
    "Known by entity refs",
    "Hidden from entity refs",
    "Reveal predecessor boundary refs",
    "Reveal condition type",
    "Freeze refs",
    "Source",
    "HLD obligation",
]


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


def load_contract() -> dict:
    return json.loads(read(CONTRACT_PATH))


def validate_required_static_checks(contract: dict, label: str) -> None:
    static_checks = contract.get("static_checks", [])
    if not isinstance(static_checks, list):
        raise ValueError(f"{label} static_checks must be a list")
    missing_checks = REQUIRED_STATIC_CHECKS - set(static_checks)
    if missing_checks:
        raise ValueError(f"{label} missing required static checks: {sorted(missing_checks)}")


def validate_contract_rule_coverage(contract: dict, label: str) -> None:
    rule_ids = {
        str(rule.get("id", "")).strip()
        for rule in contract.get("contract_rules", [])
        if str(rule.get("id", "")).strip()
    }
    coverage = contract.get("rule_coverage")
    if not isinstance(coverage, dict):
        raise ValueError(f"{label} missing rule_coverage")
    missing = rule_ids - set(coverage)
    if missing:
        raise ValueError(f"{label} missing rule coverage: {sorted(missing)}")
    extra = set(coverage) - rule_ids
    if extra:
        raise ValueError(f"{label} unknown rule coverage entries: {sorted(extra)}")
    for rule_id, entry in coverage.items():
        if not isinstance(entry, dict):
            raise ValueError(f"{label} rule coverage entry must be an object: {rule_id}")
        validators = entry.get("validators")
        tests = entry.get("tests")
        if not isinstance(validators, list) or not validators:
            raise ValueError(f"{label} rule coverage missing validators: {rule_id}")
        if not isinstance(tests, list) or not tests:
            raise ValueError(f"{label} rule coverage missing tests: {rule_id}")
        if not all(isinstance(item, str) and item.strip() for item in validators):
            raise ValueError(f"{label} rule coverage invalid validators: {rule_id}")
        if not all(isinstance(item, str) and item.strip() for item in tests):
            raise ValueError(f"{label} rule coverage invalid tests: {rule_id}")
        unknown_validators = [
            validator_name for validator_name in validators
            if not callable(globals().get(validator_name))
        ]
        if unknown_validators:
            raise ValueError(f"{label} unknown coverage validator for {rule_id}: {unknown_validators}")
        test_text = read(PRD_CONTRACT_TESTS)
        unknown_tests = [
            test_name for test_name in tests
            if f"def {test_name}(" not in test_text
        ]
        if unknown_tests:
            raise ValueError(f"{label} unknown coverage test for {rule_id}: {unknown_tests}")


def unquote_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def split_list_refs(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[,;，；]\s*", value.strip()) if part.strip() and part.strip() != "none"]


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
        if cells and not all(set(cell) <= {"-", ":"} for cell in cells):
            rows.append(cells)
    if len(rows) < 2:
        raise ValueError(f"{label} {heading} table must include header and at least one row")
    return rows


def markdown_section_text(text: str, heading: str, label: str) -> str:
    heading_match = re.search(rf"^##+\s+{re.escape(heading)}\s*$", text, re.M)
    if not heading_match:
        raise ValueError(f"{label} missing markdown section: {heading}")
    section = text[heading_match.start() :]
    next_heading = re.search(r"^##+\s+", section[1:], re.M)
    if next_heading:
        section = section[: next_heading.start() + 1]
    return section.strip()


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


def field_value_map(rows: list[list[str]], label: str) -> dict[str, str]:
    entries = row_dicts(rows, ["Field", "Value"], label)
    return {entry["Field"]: unquote_cell(entry["Value"]) for entry in entries}


def semantic_length(text: str) -> int:
    return len(re.sub(r"[\s`|，。；、：:,.!?！？“”\"'（）()\[\]《》-]", "", text))


def validate_skill_contract_text(skill_text: str, skill_name: str) -> None:
    for section in [
        "## Responsibility",
        "## Input",
        "## Output",
        "## Rules",
        "## Boundary",
        "## References",
        "## Traceability",
        "## Acceptance",
        "## Skill Verdict",
    ]:
        if section not in skill_text:
            raise ValueError(f"{skill_name} missing required independent-skill section: {section}")
    for field in SKILL_VERDICT_FIELDS:
        if field not in skill_text:
            raise ValueError(f"{skill_name} missing Skill Verdict field: {field}")


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
        deps = node.get("depends_on", [])
        if not isinstance(deps, list):
            raise ValueError(f"{label} node {node_id} depends_on must be a list")
        nodes[node_id] = {str(dep).strip() for dep in deps}
    for node_id, deps in nodes.items():
        missing = deps - set(nodes)
        if missing:
            raise ValueError(f"{label} node {node_id} depends on unknown artifacts: {sorted(missing)}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str, path: list[str]) -> None:
        if node_id in visiting:
            raise ValueError(f"{label} contains dependency cycle: {' -> '.join(path + [node_id])}")
        if node_id in visited:
            return
        visiting.add(node_id)
        for dep in sorted(nodes[node_id]):
            visit(dep, path + [node_id])
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(nodes):
        visit(node_id, [])


def expected_prd_artifact_dag() -> list[dict]:
    return [
        {"id": "01", "depends_on": []},
        {"id": "02", "depends_on": ["01"]},
        {"id": "03", "depends_on": ["01", "02"]},
        {"id": "04", "depends_on": ["03"]},
        {"id": "05", "depends_on": ["03", "04"]},
        {"id": "06", "depends_on": ["01", "02", "03", "04", "05"]},
        {"id": "07", "depends_on": ["01", "02", "03", "04", "05", "06"]},
        {"id": "08", "depends_on": ["01", "02", "03", "04", "05", "06", "07"]},
        {"id": "09", "depends_on": ["01", "02", "03", "04", "05", "06", "07", "08"]},
        {"id": "final-prd-package", "depends_on": ["08", "09"]},
    ]


def dependency_map(graph: list[dict]) -> dict[str, set[str]]:
    return {
        str(node["id"]).strip(): {str(dep).strip() for dep in node.get("depends_on", [])}
        for node in graph
    }


def validate_prd_artifact_topology(graph: list[dict], label: str) -> None:
    deps = dependency_map(graph)
    if "08" in deps and "09" in deps["08"]:
        raise ValueError(f"{label} artifact 08 must not depend on artifact 09")
    validate_artifact_dag(graph, label)
    expected = dependency_map(expected_prd_artifact_dag())
    missing = set(expected) - set(deps)
    if missing:
        raise ValueError(f"{label} missing required PRD artifact ids: {sorted(missing)}")
    for artifact_id, expected_deps in expected.items():
        actual = deps[artifact_id]
        if actual != expected_deps:
            raise ValueError(
                f"{label} artifact {artifact_id} must depend exactly on {sorted(expected_deps)}; "
                f"got {sorted(actual)}"
            )


def validate_upstream_proposal_entry_gate(proposal_risk_report: str, label: str) -> None:
    rows = parse_markdown_table_rows(proposal_risk_report, "Output", label)
    fields = field_value_map(rows, f"{label} Output")
    verdict = fields.get("PRD entry verdict")
    if verdict != "pass_to_prd":
        raise ValueError(f"{label} cannot start PRD unless PRD entry verdict is pass_to_prd; got {verdict}")


def proposal_prd_entry_verdict(proposal_risk_report: str, label: str) -> str:
    rows = parse_markdown_table_rows(proposal_risk_report, "Output", label)
    fields = field_value_map(rows, f"{label} Output")
    verdict = fields.get("PRD entry verdict")
    if not verdict:
        raise ValueError(f"{label} missing PRD entry verdict")
    return verdict


def validate_prd_runs_declared(contract: dict, label: str) -> None:
    artifact_runs = contract.get("artifact_runs", [])
    blocked_runs = contract.get("blocked_runs", [])
    if not artifact_runs and not blocked_runs:
        raise ValueError(f"{label} must declare artifact_runs or blocked_runs")
    if artifact_runs is not None and not isinstance(artifact_runs, list):
        raise ValueError(f"{label} artifact_runs must be a list")
    if blocked_runs is not None and not isinstance(blocked_runs, list):
        raise ValueError(f"{label} blocked_runs must be a list")


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


def convergence_log_entries(manifest_text: str, label: str) -> list[dict[str, str]]:
    rows = parse_markdown_table_rows(manifest_text, "Convergence log", label)
    return row_dicts(
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


def validate_manifest_required_terms(manifest_text: str, label: str, terms: list[str]) -> None:
    for term in terms:
        if term not in manifest_text:
            raise ValueError(f"{label} missing required term: {term}")
    validate_convergence_log(manifest_text, label)


def validate_blocked_run(blocked_run: dict, label: str) -> None:
    manifest_path = resolve_recorded_path(blocked_run["manifest"])
    manifest_text = read(manifest_path)
    validate_manifest_required_terms(
        manifest_text,
        label,
        [
            "PRD workflow artifact run",
            "Harness: `novel-prd-workflow`",
            "Execution status: blocked before PRD business dispatch",
            "Blocking verdict:",
            "## Convergence log",
        ],
    )
    upstream_path = resolve_recorded_path(blocked_run["upstream_proposal_risk_report"])
    verdict = proposal_prd_entry_verdict(read(upstream_path), f"{label} upstream proposal risk report")
    expected_verdict = blocked_run.get("blocking_verdict")
    if verdict != expected_verdict:
        raise ValueError(
            f"{label} blocking verdict mismatch: manifest expects {expected_verdict}, upstream has {verdict}"
        )
    if verdict == "pass_to_prd":
        raise ValueError(f"{label} blocked run cannot use upstream PRD entry verdict pass_to_prd")


def proposal_claims_from_risk_report(proposal_risk_report: str, label: str) -> dict[str, dict[str, str]]:
    rows = rows_as_dicts(
        proposal_risk_report,
        "Claim Source Map coverage",
        label,
        ["Claim ID", "Critical business claim", "Constraint role", "Coverage verdict", "Evidence"],
    )
    claims: dict[str, dict[str, str]] = {}
    for row in rows:
        claim_id = unquote_cell(row["Claim ID"])
        if not re.fullmatch(r"CLAIM-\d{2,}", claim_id):
            raise ValueError(f"{label} invalid Claim ID: {claim_id}")
        if claim_id in claims:
            raise ValueError(f"{label} duplicate Claim ID: {claim_id}")
        claim_text = unquote_cell(row["Critical business claim"])
        constraint_role = unquote_cell(row["Constraint role"])
        coverage_verdict = status_token(row["Coverage verdict"])
        if coverage_verdict != "pass":
            raise ValueError(
                f"{label} Claim Source Map coverage must pass for {claim_id}: "
                f"{row['Coverage verdict']}"
            )
        if semantic_length(claim_text) < 10:
            raise ValueError(f"{label} claim text too short: {claim_id}")
        if semantic_length(constraint_role) < 4:
            raise ValueError(f"{label} constraint role too short: {claim_id}")
        claims[claim_id] = {
            "claim": claim_text,
            "constraint_role": constraint_role,
        }
    if not claims:
        raise ValueError(f"{label} has no proposal claim ids")
    return claims


def proposal_claim_ids_from_risk_report(proposal_risk_report: str, label: str) -> set[str]:
    return set(proposal_claims_from_risk_report(proposal_risk_report, label))


def claim_id_set(proposal_claims: dict[str, dict[str, str]] | set[str] | None) -> set[str] | None:
    if proposal_claims is None:
        return None
    if isinstance(proposal_claims, set):
        return proposal_claims
    return set(proposal_claims)


def validate_proposal_trace_text(
    trace_text: str,
    proposal_claims: dict[str, dict[str, str]] | set[str] | None,
    label: str,
) -> None:
    proposal_claim_ids = claim_id_set(proposal_claims)
    if proposal_claim_ids is None:
        return
    trace_ids = set(re.findall(r"CLAIM-\d{2,}", trace_text))
    if not trace_ids:
        raise ValueError(f"{label} missing proposal trace claim id")
    unknown_ids = trace_ids - proposal_claim_ids
    if unknown_ids:
        raise ValueError(f"{label} unknown proposal trace claim: {sorted(unknown_ids)}")
    if isinstance(proposal_claims, dict):
        for claim_id in sorted(trace_ids):
            expected_role = proposal_claims[claim_id]["constraint_role"]
            expected_marker = f"role={expected_role}"
            if expected_marker not in trace_text:
                raise ValueError(
                    f"{label} constraint role drift for {claim_id}: "
                    f"expected {expected_role}"
                )


def normalized_fact_text(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", text)


def fact_bigrams(text: str) -> set[str]:
    normalized = normalized_fact_text(text)
    return {
        normalized[index : index + 2]
        for index in range(max(0, len(normalized) - 1))
    }


def validate_proposal_claim_support(
    content_text: str,
    trace_text: str,
    proposal_claims: dict[str, dict[str, str]] | set[str] | None,
    label: str,
) -> None:
    if proposal_claims is None or isinstance(proposal_claims, set):
        return
    trace_ids = set(re.findall(r"CLAIM-\d{2,}", trace_text))
    normalized_content = normalized_fact_text(content_text)
    for claim_id in trace_ids:
        claim = proposal_claims[claim_id]["claim"]
        normalized_claim = normalized_fact_text(claim)
        if not normalized_claim or not normalized_content:
            raise ValueError(f"{label} insufficient support for proposal claim: {claim_id}")
        if normalized_claim not in normalized_content:
            raise ValueError(
                f"{label} must preserve exact proposal claim fact for {claim_id}"
            )


def validate_skill_output_verdict(artifact_text: str, label: str) -> None:
    rows = parse_markdown_table_rows(artifact_text, "Skill Verdict", label)
    fields = field_value_map(rows, f"{label} Skill Verdict")
    missing = [field for field in SKILL_VERDICT_FIELDS if field not in fields]
    if missing:
        raise ValueError(f"{label} Skill Verdict missing fields: {missing}")
    quality = fields["Skill quality verdict"]
    source = fields["Source closure"]
    boundary = fields["Boundary obedience"]
    downstream = fields["Downstream readiness"]
    blocking = fields["Blocking issue"]
    rerun = fields["Rerun target"]
    if quality not in SKILL_QUALITY_VERDICTS:
        raise ValueError(f"{label} invalid Skill quality verdict: {quality}")
    for field, value in [
        ("Source closure", source),
        ("Boundary obedience", boundary),
        ("Downstream readiness", downstream),
    ]:
        if value not in PASS_FAIL:
            raise ValueError(f"{label} invalid {field}: {value}")
    if quality == "pass":
        failed_gates = [
            field
            for field, value in [
                ("Source closure", source),
                ("Boundary obedience", boundary),
                ("Downstream readiness", downstream),
            ]
            if value != "pass"
        ]
        if failed_gates:
            raise ValueError(f"{label} Skill quality verdict cannot pass with failed gates: {failed_gates}")
        if blocking != "none":
            raise ValueError(f"{label} passing Skill Verdict must use Blocking issue none")
        if rerun != "none":
            raise ValueError(f"{label} passing Skill Verdict must use Rerun target none")
    if quality != "pass" and blocking == "none":
        raise ValueError(f"{label} non-pass Skill Verdict must name Blocking issue")
    if quality != "pass" and rerun == "none":
        raise ValueError(f"{label} non-pass Skill Verdict must name Rerun target")


def referenced_scene_ids(text: str) -> set[str]:
    return set(re.findall(r"PRD-S\d{2,}", text))


def structured_source_refs(source_text: str) -> dict[str, set[str]]:
    refs = {"scene": set(), "claim": set()}
    for match in re.finditer(r"\b(scene):(PRD-S\d{2,})\b|\b(claim):(CLAIM-\d{2,})\b", source_text):
        if match.group(1) == "scene":
            refs["scene"].add(match.group(2))
        else:
            refs["claim"].add(match.group(4))
    return refs


def validate_source_references(
    source_text: str,
    canonical_scenes: dict[str, dict[str, str]],
    proposal_claims: dict[str, dict[str, str]] | set[str] | None,
    label: str,
) -> None:
    refs = structured_source_refs(source_text)
    if not refs["scene"] and not refs["claim"]:
        raise ValueError(f"{label} missing structured source reference")
    raw_scene_ids = referenced_scene_ids(source_text)
    if raw_scene_ids != refs["scene"]:
        missing = raw_scene_ids - refs["scene"]
        raise ValueError(f"{label} unstructured source scene reference: {sorted(missing)}")
    raw_claim_ids = set(re.findall(r"CLAIM-\d{2,}", source_text))
    if raw_claim_ids != refs["claim"]:
        missing = raw_claim_ids - refs["claim"]
        raise ValueError(f"{label} unstructured source claim reference: {sorted(missing)}")
    unknown_scenes = refs["scene"] - set(canonical_scenes)
    if unknown_scenes:
        raise ValueError(f"{label} scene ids: {sorted(unknown_scenes)}")
    if refs["claim"]:
        validate_proposal_trace_text(source_text, claim_id_set(proposal_claims), label)


def validate_trunk_scene_rows(
    rows: list[list[str]],
    label: str,
    proposal_claims: dict[str, dict[str, str]] | set[str] | None = None,
) -> dict[str, dict[str, str]]:
    required_headers = [
        "Scene id",
        "Order",
        "Entry state",
        "Roles",
        "Environment",
        "Event",
        "Causal output",
        "Proposal trace",
    ]
    if proposal_claims is not None:
        required_headers.extend(["Scene content", "Previous dependency", "Next pressure", "Indispensability proof"])
    scenes = row_dicts(
        rows,
        required_headers,
        label,
    )
    canonical: dict[str, dict[str, str]] = {}
    seen_orders: set[str] = set()
    for scene in scenes:
        scene_id = scene["Scene id"]
        order = scene["Order"]
        if not re.fullmatch(r"PRD-S\d{2,}", scene_id):
            raise ValueError(f"{label} invalid Scene id: {scene_id}")
        if scene_id in canonical:
            raise ValueError(f"{label} duplicate Scene id: {scene_id}")
        if not re.fullmatch(r"[1-9]\d*", order):
            raise ValueError(f"{label} invalid Order for {scene_id}: {order}")
        if order in seen_orders:
            raise ValueError(f"{label} duplicate Order: {order}")
        seen_orders.add(order)
        semantic_fields = ["Entry state", "Roles", "Environment", "Event", "Causal output", "Proposal trace"]
        if proposal_claims is not None:
            semantic_fields.extend(["Scene content", "Previous dependency", "Next pressure", "Indispensability proof"])
        for field in semantic_fields:
            if semantic_length(scene[field]) < 6:
                raise ValueError(f"{label} {scene_id} {field} too short")
        validate_proposal_trace_text(scene["Proposal trace"], proposal_claims, f"{label} {scene_id}")
        validate_proposal_claim_support(
            " ".join(
                [
                    scene["Entry state"],
                    scene["Roles"],
                    scene["Environment"],
                    scene["Event"],
                    scene.get("Scene content", ""),
                    scene["Causal output"],
                ]
            ),
            scene["Proposal trace"],
            proposal_claims,
            f"{label} {scene_id}",
        )
        canonical[scene_id] = {
            "order": order,
            "entry_state": scene["Entry state"],
            "roles": scene["Roles"],
            "environment": scene["Environment"],
            "event": scene["Event"],
            "causal_output": scene["Causal output"],
            "proposal_trace": scene["Proposal trace"],
            "scene_content": scene.get("Scene content", ""),
            "previous_dependency": scene.get("Previous dependency", ""),
            "next_pressure": scene.get("Next pressure", ""),
            "indispensability_proof": scene.get("Indispensability proof", ""),
        }
    return canonical


def validate_pre_extraction_causal_setup(
    canonical_scenes: dict[str, dict[str, str]],
    label: str,
) -> None:
    post_death_extraction_orders = []
    for scene in canonical_scenes.values():
        scene_text = "".join(
            [
                scene.get("entry_state", ""),
                scene.get("event", ""),
                scene.get("causal_output", ""),
                scene.get("scene_content", ""),
            ]
        )
        if all(term in scene_text for term in ["死亡后", "生命维持", "脑波分析"]):
            post_death_extraction_orders.append(int(scene["order"]))
    if not post_death_extraction_orders:
        return

    first_extraction_order = min(post_death_extraction_orders)
    setup_markers = ["交接", "传递", "上报", "线索", "未完成", "中断"]
    for scene in canonical_scenes.values():
        if int(scene["order"]) >= first_extraction_order:
            continue
        scene_text = "".join(
            [
                scene.get("entry_state", ""),
                scene.get("roles", ""),
                scene.get("environment", ""),
                scene.get("event", ""),
                scene.get("causal_output", ""),
                scene.get("scene_content", ""),
                scene.get("previous_dependency", ""),
                scene.get("next_pressure", ""),
                scene.get("indispensability_proof", ""),
            ]
        )
        has_key_intelligence = "关键情报" in scene_text
        has_death_context = "事故" in scene_text or "死亡" in scene_text
        has_handoff_loss = any(marker in scene_text for marker in setup_markers)
        if has_key_intelligence and has_death_context and has_handoff_loss:
            return

    raise ValueError(
        f"{label} missing pre-extraction causal setup before post-death memory reading"
    )


def validate_scene_execution_table(
    artifact_text: str,
    canonical_scenes: dict[str, dict[str, str]],
    proposal_claims: dict[str, dict[str, str]] | set[str] | None,
    label: str,
) -> None:
    rows = rows_as_dicts(
        artifact_text,
        "Scene execution table",
        label,
        [
            "Unit id",
            "Parent scene id",
            "Unit order",
            "Scene objective",
            "On-page action",
            "Conflict turn",
            "Exit state",
            "Proposal trace",
        ],
    )
    units_by_scene: dict[str, list[str]] = {scene_id: [] for scene_id in canonical_scenes}
    seen_units: set[str] = set()
    for row in rows:
        unit_id = row["Unit id"]
        parent_id = row["Parent scene id"]
        if not re.fullmatch(r"PRD-S\d{2,}-U\d{2,}", unit_id):
            raise ValueError(f"{label} invalid Unit id: {unit_id}")
        if unit_id in seen_units:
            raise ValueError(f"{label} duplicate Unit id: {unit_id}")
        seen_units.add(unit_id)
        if parent_id not in canonical_scenes:
            raise ValueError(f"{label} unknown Parent scene id: {parent_id}")
        if not unit_id.startswith(f"{parent_id}-U"):
            raise ValueError(f"{label} Unit id parent drift: {unit_id} -> {parent_id}")
        if not re.fullmatch(r"[1-9]\d*", row["Unit order"]):
            raise ValueError(f"{label} invalid Unit order for {unit_id}: {row['Unit order']}")
        for field in ["Scene objective", "On-page action", "Conflict turn", "Exit state", "Proposal trace"]:
            if semantic_length(row[field]) < 8:
                raise ValueError(f"{label} {unit_id} {field} too short")
        validate_proposal_trace_text(row["Proposal trace"], proposal_claims, f"{label} {unit_id}")
        units_by_scene[parent_id].append(unit_id)

    sparse_scenes = [
        scene_id for scene_id, unit_ids in units_by_scene.items()
        if len(unit_ids) < 2
    ]
    if sparse_scenes:
        raise ValueError(
            f"{label} Scene execution table requires at least two units per trunk scene: {sparse_scenes}"
        )


def story_logic_risk_text(canonical_scenes: dict[str, dict[str, str]]) -> str:
    return " ".join(
        " ".join(
            [
                scene.get("entry_state", ""),
                scene.get("roles", ""),
                scene.get("environment", ""),
                scene.get("event", ""),
                scene.get("causal_output", ""),
                scene.get("scene_content", ""),
                scene.get("previous_dependency", ""),
                scene.get("next_pressure", ""),
                scene.get("indispensability_proof", ""),
            ]
        )
        for scene in canonical_scenes.values()
    )


def requires_story_logic_boundary(canonical_scenes: dict[str, dict[str, str]]) -> bool:
    text = story_logic_risk_text(canonical_scenes)
    has_withheld_cause = all(term in text for term in ["可用情报", "完整原因", "被保护者"])
    has_terminal_deception = all(term in text for term in ["数字生命体", "终止"]) and any(
        term in text for term in ["系统提示", "权限", "误导", "设局"]
    )
    return has_withheld_cause or has_terminal_deception


def require_any_term(text: str, terms: list[str], label: str) -> None:
    if not any(term in text for term in terms):
        raise ValueError(f"{label} missing any required term from: {terms}")


def find_story_logic_row(
    rows: list[dict[str, str]],
    required_terms: list[str],
    label: str,
) -> dict[str, str]:
    for row in rows:
        searchable = " ".join([row["Logic concern"], row["Frozen answer"], row["HLD expansion room"]])
        if all(term in searchable for term in required_terms):
            return row
    raise ValueError(f"{label} Story logic boundary table missing concern: {required_terms}")


def story_logic_boundary_rows(
    artifact_text: str,
    canonical_scenes: dict[str, dict[str, str]],
    proposal_claims: dict[str, dict[str, str]] | set[str] | None,
    label: str,
) -> list[dict[str, str]]:
    if not requires_story_logic_boundary(canonical_scenes):
        return []

    return rows_as_dicts(
        artifact_text,
        "Story logic boundary table",
        label,
        [
            "Boundary id",
            "Logic concern",
            "Frozen answer",
            "HLD expansion room",
            "Required HLD entity refs",
            "Source",
        ],
    )


def validate_story_logic_boundary_table(
    artifact_text: str,
    canonical_scenes: dict[str, dict[str, str]],
    proposal_claims: dict[str, dict[str, str]] | set[str] | None,
    label: str,
) -> list[dict[str, str]]:
    rows = story_logic_boundary_rows(
        artifact_text,
        canonical_scenes,
        proposal_claims,
        label,
    )
    if not rows:
        return []
    seen_ids: set[str] = set()
    for row in rows:
        boundary_id = row["Boundary id"]
        if not re.fullmatch(r"PRD-LOGIC-\d{2,}", boundary_id):
            raise ValueError(f"{label} invalid Story logic Boundary id: {boundary_id}")
        if boundary_id in seen_ids:
            raise ValueError(f"{label} duplicate Story logic Boundary id: {boundary_id}")
        seen_ids.add(boundary_id)
        validate_semantic_fields(
            row,
            [
                "Logic concern",
                "Frozen answer",
                "HLD expansion room",
                "Required HLD entity refs",
                "Source",
            ],
            f"{label} {boundary_id}",
            min_length=8,
        )
        entity_refs = split_list_refs(row["Required HLD entity refs"])
        if not entity_refs:
            raise ValueError(f"{label} {boundary_id} missing Required HLD entity refs")
        for entity_ref in entity_refs:
            if not entity_ref.startswith("entity:") or not entity_ref.removeprefix("entity:").strip():
                raise ValueError(f"{label} {boundary_id} invalid Required HLD entity ref: {entity_ref}")
        validate_source_references(
            row["Source"],
            canonical_scenes,
            proposal_claims,
            f"{label} {boundary_id} source",
        )

    intelligence_row = find_story_logic_row(rows, ["可用情报", "完整原因"], label)
    intelligence_answer = intelligence_row["Frozen answer"]
    require_any_term(
        intelligence_answer,
        ["时间", "地点", "触发条件", "阻断方式", "行动方式"],
        f"{label} usable intelligence boundary",
    )
    require_any_term(
        intelligence_answer,
        ["行动窗口", "处置窗口", "执行窗口", "阻断窗口"],
        f"{label} usable intelligence plausibility anchor",
    )
    require_any_term(
        intelligence_answer,
        ["身份", "关系", "私人动机", "被保护者"],
        f"{label} complete-cause boundary",
    )

    protected_row = find_story_logic_row(rows, ["被保护者", "触发链"], label)
    protected_answer = protected_row["Frozen answer"]
    require_any_term(
        protected_answer,
        ["被胁迫", "被误导", "被利用", "触发链", "后果中心"],
        f"{label} protected-person causal boundary",
    )
    require_any_term(
        protected_answer,
        ["暴露", "处置", "审查", "重新卷入", "伤害"],
        f"{label} protected-person exposure consequence",
    )
    require_any_term(
        protected_answer,
        ["私人关系", "亏欠关系", "亲属关系", "承诺关系", "救命关系"],
        f"{label} protected-person plausibility anchor",
    )

    terminal_row = find_story_logic_row(rows, ["数字生命", "终止"], label)
    terminal_answer = terminal_row["Frozen answer"]
    require_any_term(
        terminal_answer,
        ["不能控制外部系统", "不能凭空伪造权限", "不能改写权限"],
        f"{label} digital-life capability limit",
    )
    require_any_term(
        terminal_answer,
        ["既有告警", "日志", "对话节奏", "研究员误判", "系统提示"],
        f"{label} digital-life deception mechanism",
    )
    require_any_term(
        terminal_answer,
        ["多重确认", "终止流程", "确认流程", "终止权限"],
        f"{label} digital-life terminal plausibility anchor",
    )

    organization_row = find_story_logic_row(rows, ["组织", "追问"], label)
    organization_answer = organization_row["Frozen answer"]
    require_any_term(
        organization_answer,
        ["结案审查", "情报缺口", "资产价值", "保存窗口"],
        f"{label} organization pressure plausibility anchor",
    )
    require_any_term(
        organization_answer,
        ["不能直接复制", "不能直接接管", "接管限制", "复制限制"],
        f"{label} organization boundary plausibility anchor",
    )
    return rows


def validate_semantic_fields(row: dict[str, str], fields: list[str], label: str, min_length: int = 6) -> None:
    for field in fields:
        if semantic_length(row[field]) < min_length:
            raise ValueError(f"{label} {field} too short")


def validate_scene_coverage(
    canonical_scenes: dict[str, dict[str, str]],
    rows: list[dict[str, str]],
    label: str,
    required_headers: list[str],
) -> None:
    seen_ids: set[str] = set()
    for row in rows:
        for header in required_headers:
            if header not in row:
                raise ValueError(f"{label} missing required row field: {header}")
        scene_id = row["Scene id"]
        if scene_id in seen_ids:
            raise ValueError(f"{label} duplicate scene id: {scene_id}")
        if scene_id not in canonical_scenes:
            raise ValueError(f"{label} contains extra scene id: {scene_id}")
        seen_ids.add(scene_id)
    missing_ids = set(canonical_scenes) - seen_ids
    if missing_ids:
        raise ValueError(f"{label} missing scene ids: {sorted(missing_ids)}")


def validate_scene_source_map_rows(
    canonical_scenes: dict[str, dict[str, str]],
    source_map_rows: list[dict[str, str]],
    label: str,
    proposal_claims: dict[str, dict[str, str]] | set[str] | None = None,
) -> None:
    validate_scene_coverage(
        canonical_scenes,
        source_map_rows,
        label,
        ["Scene id", "Order", "Event fact", "Causal output", "Proposal trace", "Source artifact"],
    )
    for row in source_map_rows:
        scene_id = row["Scene id"]
        canonical = canonical_scenes[scene_id]
        if row["Order"] != canonical["order"]:
            raise ValueError(
                f"{label} order drift for {scene_id}: expected {canonical['order']} got {row['Order']}"
            )
        if row["Event fact"] != canonical["event"]:
            raise ValueError(
                f"{label} event fact drift for {scene_id}: "
                f"expected {canonical['event']} got {row['Event fact']}"
            )
        if row["Causal output"] != canonical["causal_output"]:
            raise ValueError(
                f"{label} causal output drift for {scene_id}: "
                f"expected {canonical['causal_output']} got {row['Causal output']}"
            )
        if row["Proposal trace"] != canonical["proposal_trace"]:
            raise ValueError(
                f"{label} proposal trace drift for {scene_id}: "
                f"expected {canonical['proposal_trace']} got {row['Proposal trace']}"
            )
        validate_proposal_trace_text(row["Proposal trace"], proposal_claims, f"{label} {scene_id}")
        if "artifact 03" not in row["Source artifact"]:
            raise ValueError(f"{label} {scene_id} must cite artifact 03 trunk scene source")


def rows_as_dicts(text: str, heading: str, label: str, required_headers: list[str]) -> list[dict[str, str]]:
    rows = parse_markdown_table_rows(text, heading, label)
    return row_dicts(rows, required_headers, f"{label} {heading}")


PRD_CORE_RISK_CHECK_FIELDS = [
    "Proposal obedience",
    "Scope integrity",
    "Trunk causality",
    "Scene completeness",
    "Boundary control",
    "Freeze sufficiency",
    "HLD handoff",
]


def status_token(value: str) -> str:
    text = unquote_cell(value)
    match = re.match(r"`?(pass|fail|not_checked)`?\b", text)
    if not match:
        return ""
    return match.group(1)


def validate_scope_artifact(
    scope_text: str,
    proposal_claims: dict[str, dict[str, str]] | set[str] | None,
    label: str,
) -> None:
    rows = rows_as_dicts(
        scope_text,
        "Specified part scope table",
        label,
        [
            "Scope id",
            "Scope name",
            "Start boundary",
            "End boundary",
            "Excluded material",
            "Independence proof",
            "Proposal trace",
            "Verdict",
        ],
    )
    for row in rows:
        if unquote_cell(row["Verdict"]) != "pass":
            raise ValueError(f"{label} scope verdict must be pass")
        validate_semantic_fields(
            row,
            ["Scope id", "Scope name", "Start boundary", "End boundary", "Excluded material", "Independence proof"],
            f"{label} scope row",
        )
        validate_proposal_trace_text(row["Proposal trace"], proposal_claims, f"{label} scope row")
        validate_proposal_claim_support(
            " ".join(
                [
                    row["Scope name"],
                    row["Start boundary"],
                    row["End boundary"],
                    row["Independence proof"],
                ]
            ),
            row["Proposal trace"],
            proposal_claims,
            f"{label} scope row",
        )


def validate_part_goal_artifact(
    goal_text: str,
    proposal_claims: dict[str, dict[str, str]] | set[str] | None,
    label: str,
) -> None:
    rows = rows_as_dicts(
        goal_text,
        "Part goal table",
        label,
        [
            "Required story state at start",
            "Required story state at end",
            "Story function",
            "Required pressure",
            "Success criteria",
            "Proposal trace",
            "Verdict",
        ],
    )
    for row in rows:
        if unquote_cell(row["Verdict"]) != "pass":
            raise ValueError(f"{label} goal verdict must be pass")
        validate_semantic_fields(
            row,
            [
                "Required story state at start",
                "Required story state at end",
                "Story function",
                "Required pressure",
                "Success criteria",
            ],
            f"{label} goal row",
        )
        validate_proposal_trace_text(row["Proposal trace"], proposal_claims, f"{label} goal row")
        validate_proposal_claim_support(
            " ".join(
                [
                    row["Required story state at start"],
                    row["Required story state at end"],
                    row["Story function"],
                    row["Required pressure"],
                    row["Success criteria"],
                ]
            ),
            row["Proposal trace"],
            proposal_claims,
            f"{label} goal row",
        )


def validate_freeze_artifact(
    freeze_text: str,
    label: str,
    canonical_scenes: dict[str, dict[str, str]] | None = None,
    proposal_claims: dict[str, dict[str, str]] | set[str] | None = None,
) -> None:
    rows = rows_as_dicts(
        freeze_text,
        "Freeze boundary list",
        label,
        ["Freeze id", "Frozen item", "Source", "Downstream no-change rule", "Reopen condition"],
    )
    seen_ids: set[str] = set()
    for row in rows:
        freeze_id = row["Freeze id"]
        if not re.fullmatch(r"PRD-FREEZE-\d{2,}", freeze_id):
            raise ValueError(f"{label} invalid Freeze id: {freeze_id}")
        if freeze_id in seen_ids:
            raise ValueError(f"{label} duplicate Freeze id: {freeze_id}")
        seen_ids.add(freeze_id)
        validate_semantic_fields(
            row,
            ["Frozen item", "Source", "Downstream no-change rule", "Reopen condition"],
            f"{label} {freeze_id}",
        )
        if canonical_scenes is not None:
            validate_source_references(
                row["Source"],
                canonical_scenes,
                proposal_claims,
                f"{label} unknown freeze source",
            )


def validate_hld_information_boundary_table(
    information_text: str,
    freeze_text: str,
    canonical_scenes: dict[str, dict[str, str]],
    label: str,
) -> list[dict[str, str]]:
    rows = rows_as_dicts(information_text, "HLD information boundary table", label, HLD_INFORMATION_BOUNDARY_COLUMNS)
    freeze_rows = rows_as_dicts(
        freeze_text,
        "Freeze boundary list",
        label,
        ["Freeze id", "Frozen item", "Source", "Downstream no-change rule", "Reopen condition"],
    )
    freeze_ids = {row["Freeze id"] for row in freeze_rows}
    boundary_by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        boundary_id = row["Information boundary id"]
        if not re.fullmatch(r"PRD-INFO-\d{2,}", boundary_id) or boundary_id in boundary_by_id:
            raise ValueError(f"{label} invalid or duplicate Information boundary id: {boundary_id}")
        for scene_column in ["Story anchor scene id", "Narrative reveal scene id"]:
            if row[scene_column] not in canonical_scenes:
                raise ValueError(f"{label} unknown information boundary scene: {boundary_id} {scene_column}")
        if not row["Narrative reveal order"].isdigit() or int(row["Narrative reveal order"]) != int(canonical_scenes[row["Narrative reveal scene id"]]["order"]):
            raise ValueError(f"{label} information boundary reveal order mismatch: {boundary_id}")
        if row["Disclosure tier"] not in {"operational_intelligence", "partial_cause", "complete_cause", "protected_memory", "institutional_assessment", "private_motive"}:
            raise ValueError(f"{label} invalid information boundary disclosure tier: {boundary_id}")
        if row["Reader access"] not in {"visible", "concealed"}:
            raise ValueError(f"{label} invalid information boundary reader access: {boundary_id}")
        known_by = set(split_list_refs(row["Known by entity refs"]))
        hidden_from = set(split_list_refs(row["Hidden from entity refs"]))
        if not known_by and not hidden_from:
            raise ValueError(f"{label} empty information boundary knowledge state: {boundary_id}")
        if known_by & hidden_from:
            raise ValueError(f"{label} overlapping information boundary knowledge state: {boundary_id}")
        for knowledge_ref in known_by | hidden_from:
            if knowledge_ref != "reader" and not re.fullmatch(r"entity:[^,;，；]+", knowledge_ref):
                raise ValueError(f"{label} invalid information boundary knowledge ref: {boundary_id} {knowledge_ref}")
        if row["Reveal condition type"] not in {"action", "permission", "access", "evidence_change"}:
            raise ValueError(f"{label} invalid information boundary condition type: {boundary_id}")
        freeze_refs = [ref.strip() for ref in re.split(r"[,;，；]\s*", row["Freeze refs"]) if ref.strip()]
        if not freeze_refs or any(not ref.startswith("freeze:") or ref.removeprefix("freeze:") not in freeze_ids for ref in freeze_refs):
            raise ValueError(f"{label} invalid information boundary freeze refs: {boundary_id}")
        validate_source_references(row["Source"], canonical_scenes, None, f"{label} unknown information boundary source")
        validate_semantic_fields(row, ["Information object", "HLD obligation"], f"{label} {boundary_id}")
        boundary_by_id[boundary_id] = row
    for boundary_id, row in boundary_by_id.items():
        predecessors = [] if row["Reveal predecessor boundary refs"].strip().lower() == "none" else [ref.strip() for ref in re.split(r"[,;，；]\s*", row["Reveal predecessor boundary refs"]) if ref.strip()]
        if any(predecessor not in boundary_by_id for predecessor in predecessors):
            raise ValueError(f"{label} unresolved information boundary predecessor: {boundary_id}")
        if any(int(boundary_by_id[predecessor]["Narrative reveal order"]) >= int(row["Narrative reveal order"]) for predecessor in predecessors):
            raise ValueError(f"{label} information boundary predecessor order mismatch: {boundary_id}")
    return rows


def validate_hld_information_boundary_integration(
    artifact_05_text: str,
    artifact_08_text: str,
    final_package_text: str,
    label: str,
) -> None:
    canonical = markdown_section_text(artifact_05_text, "HLD information boundary table", f"{label} artifact 05")
    for artifact_label, artifact_text in [
        ("artifact 08", artifact_08_text),
        ("final-prd-package", final_package_text),
    ]:
        integrated = markdown_section_text(artifact_text, "HLD information boundary table", f"{label} {artifact_label}")
        if integrated != canonical:
            raise ValueError(f"{label} HLD information boundary table drift: {artifact_label}")


def validate_prd_integration_verdict(integrator_text: str, label: str) -> None:
    rows = parse_markdown_table_rows(integrator_text, "PRD Integration Verdict", label)
    fields = field_value_map(rows, f"{label} PRD Integration Verdict")
    required = [
        "Source completeness",
        "Scene fact preservation",
        "No new business content",
        "Package readiness",
    ]
    missing = [field for field in required if field not in fields]
    if missing:
        raise ValueError(f"{label} PRD Integration Verdict missing fields: {missing}")
    for field in required:
        status = status_token(fields[field])
        if status not in {"pass", "fail", "not_checked"}:
            raise ValueError(f"{label} invalid PRD Integration Verdict field {field}: {fields[field]}")
        if status != "pass":
            raise ValueError(f"{label} PRD Integration Verdict cannot pass packaging: {field}={status}")


def validate_final_prd_package(final_text: str, label: str) -> None:
    rows = rows_as_dicts(
        final_text,
        "Final PRD package index",
        label,
        ["Section", "Source"],
    )
    expected_sources = {
        "Proposal source and PRD entry proof": "harness input gate",
        "Specified part scope": "artifact 01",
        "Part goal and acceptance boundary": "artifact 02",
        "Linear trunk scene table": "artifact 03",
        "Conflict and value-shift table": "artifact 04",
        "Information-flow table": "artifact 05",
        "HLD information boundary table": "artifact 05",
        "PRD freeze boundaries": "artifact 06",
        "HLD expansion requirements": "artifact 07",
        "Upstream required HLD entities": "artifact 07",
        "PRD Integration Verdict": "artifact 08",
        "Scene Source Map": "artifact 08",
        "PRD risk report and HLD entry verdict": "artifact 09",
    }
    seen_sections: set[str] = set()
    section_sources: dict[str, str] = {}
    for row in rows:
        section = row["Section"]
        if section in seen_sections:
            raise ValueError(f"{label} duplicate final package section: {section}")
        seen_sections.add(section)
        section_sources[section] = unquote_cell(row["Source"])
    missing_sections = set(expected_sources) - set(section_sources)
    if missing_sections:
        raise ValueError(f"{label} missing final package sections: {sorted(missing_sections)}")
    extra_sections = set(section_sources) - set(expected_sources)
    if extra_sections:
        raise ValueError(f"{label} contains extra final package sections: {sorted(extra_sections)}")
    for section, expected_source in expected_sources.items():
        actual_source = section_sources[section]
        if actual_source != expected_source:
            raise ValueError(
                f"{label} final package source mismatch for {section}: "
                f"expected {expected_source} got {actual_source}"
            )


def validate_upstream_required_hld_entities(
    artifact_text: str,
    canonical_scenes: dict[str, dict[str, str]],
    proposal_claims: dict[str, dict[str, str]],
    label: str,
) -> list[dict[str, str]]:
    rows = rows_as_dicts(
        artifact_text,
        "Upstream required HLD entities",
        label,
        [
            "Upstream fact id",
            "Source fact field",
            "Upstream fact atom",
            "Required HLD entity",
            "Required entity type",
            "Source refs",
        ],
    )
    seen_keys: set[tuple[str, str, str, str]] = set()
    seen_fact_ids: set[str] = set()
    covered_scenes: set[str] = set()
    for row in rows:
        for field in [
            "Upstream fact id",
            "Source fact field",
            "Upstream fact atom",
            "Required HLD entity",
            "Required entity type",
            "Source refs",
        ]:
            if not row[field].strip():
                raise ValueError(f"{label} upstream required HLD entity row missing {field}")
        upstream_fact_id = row["Upstream fact id"]
        fact_id_match = UPSTREAM_FACT_ID_PATTERN.fullmatch(upstream_fact_id)
        if not fact_id_match:
            raise ValueError(f"{label} invalid upstream required HLD entity fact id: {upstream_fact_id}")
        if upstream_fact_id in seen_fact_ids:
            raise ValueError(f"{label} duplicate upstream required HLD entity fact id: {upstream_fact_id}")
        seen_fact_ids.add(upstream_fact_id)
        entity_type = row["Required entity type"]
        if entity_type not in REQUIRED_HLD_ENTITY_TYPES:
            raise ValueError(f"{label} invalid upstream required HLD entity type: {entity_type}")
        validate_source_references(
            row["Source refs"],
            canonical_scenes,
            proposal_claims,
            f"{label} upstream required HLD entity source",
        )
        source_refs = structured_source_refs(row["Source refs"])
        fact_id_scene = f"PRD-{fact_id_match.group(1)}"
        if fact_id_scene not in source_refs["scene"]:
            raise ValueError(
                f"{label} upstream fact id scene anchor missing from Source refs: {upstream_fact_id}"
            )
        source_field = row["Source fact field"]
        if source_field not in UPSTREAM_FACT_SOURCE_FIELDS:
            raise ValueError(f"{label} invalid Source fact field: {source_field}")
        source_fact = canonical_scenes[fact_id_scene][UPSTREAM_FACT_SOURCE_FIELDS[source_field]]
        if row["Upstream fact atom"] != source_fact:
            raise ValueError(
                f"{label} upstream fact atom does not exactly match Source fact field: {upstream_fact_id}"
            )
        if row["Required HLD entity"] not in row["Upstream fact atom"]:
            raise ValueError(
                f"{label} upstream fact atom does not bind Required HLD entity: {upstream_fact_id}"
            )
        covered_scenes.update(structured_source_refs(row["Source refs"])["scene"])
        key = (
            upstream_fact_id,
            row["Required HLD entity"].casefold(),
            entity_type,
            row["Source refs"],
        )
        if key in seen_keys:
            raise ValueError(f"{label} duplicate upstream required HLD entity: {upstream_fact_id}")
        seen_keys.add(key)
    missing_scene_entities = set(canonical_scenes) - covered_scenes
    if missing_scene_entities:
        raise ValueError(
            f"{label} Upstream required HLD entities missing scene ids: {sorted(missing_scene_entities)}"
        )
    return rows


def validate_information_boundary_knowledge_entity_closure(
    boundary_rows: list[dict[str, str]],
    entity_rows: list[dict[str, str]],
    label: str,
) -> None:
    registered_entities = {
        row["Required HLD entity"].strip()
        for row in entity_rows
        if row["Required entity type"] in {"character", "group"}
    }
    for boundary in boundary_rows:
        boundary_id = boundary["Information boundary id"]
        for field in ["Known by entity refs", "Hidden from entity refs"]:
            for ref in split_list_refs(boundary[field]):
                if ref == "reader":
                    continue
                entity_name = ref.removeprefix("entity:")
                if entity_name not in registered_entities:
                    raise ValueError(
                        f"{label} unknown knowledge entity: {boundary_id} {entity_name}"
                    )


def fact_anchor_scene(entity_row: dict[str, str]) -> str:
    fact_id_match = UPSTREAM_FACT_ID_PATTERN.fullmatch(entity_row.get("Upstream fact id", ""))
    if not fact_id_match:
        raise ValueError(
            f"invalid entity registration fact id: {entity_row.get('Upstream fact id', '<missing>')}"
        )
    return f"PRD-{fact_id_match.group(1)}"


def entity_fact_anchor_registry(entity_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    registry: dict[str, list[dict[str, str]]] = {}
    for entity_row in entity_rows:
        if entity_row["Required entity type"] not in {"character", "group"}:
            continue
        entity_name = entity_row["Required HLD entity"].strip()
        registry.setdefault(entity_name, []).append(entity_row)
    return registry


def validate_story_logic_entity_closure(
    story_logic_rows: list[dict[str, str]],
    entity_rows: list[dict[str, str]],
    label: str,
) -> None:
    registry = entity_fact_anchor_registry(entity_rows)
    for boundary in story_logic_rows:
        boundary_id = boundary["Boundary id"]
        boundary_scenes = structured_source_refs(boundary["Source"])["scene"]
        for entity_ref in split_list_refs(boundary["Required HLD entity refs"]):
            entity_name = entity_ref.removeprefix("entity:")
            candidates = registry.get(entity_name, [])
            if not candidates:
                raise ValueError(
                    f"{label} unknown Story logic entity: {boundary_id} {entity_name}"
                )
            if not any(fact_anchor_scene(candidate) in boundary_scenes for candidate in candidates):
                raise ValueError(
                    f"{label} Story logic entity source does not anchor: {boundary_id} {entity_name}"
                )


def validate_information_boundary_obligation_coverage(
    boundary_rows: list[dict[str, str]],
    requirement_rows: list[dict[str, str]],
    label: str,
) -> None:
    boundaries_by_id = {row["Information boundary id"]: row for row in boundary_rows}
    boundary_ids = set(boundaries_by_id)
    consumed: set[str] = set()
    for requirement in requirement_rows:
        requirement_id = requirement["Requirement id"]
        refs = split_list_refs(requirement["Information boundary refs"])
        if not refs:
            if requirement["Inherited HLD obligations"].strip().lower() != "none":
                raise ValueError(
                    f"{label} {requirement_id} has inherited HLD obligations without boundary refs"
                )
            continue
        unknown = set(refs) - boundary_ids
        if unknown:
            raise ValueError(
                f"{label} unknown HLD information boundary refs for {requirement_id}: {sorted(unknown)}"
            )
        if len(refs) != len(set(refs)):
            raise ValueError(f"{label} duplicate HLD information boundary refs for {requirement_id}")
        validate_semantic_fields(
            requirement,
            ["Required answer", "Boundary"],
            f"{label} {requirement_id} information boundary coverage",
        )
        supported_scenes = set(re.findall(r"PRD-S\d{2,}", requirement["Supports scene ids"]))
        source_scenes = structured_source_refs(requirement["Source"])["scene"]
        for boundary_id in refs:
            boundary = boundaries_by_id[boundary_id]
            boundary_scenes = {
                boundary["Story anchor scene id"],
                boundary["Narrative reveal scene id"],
            }
            if not supported_scenes & boundary_scenes:
                raise ValueError(
                    f"{label} {requirement_id} does not support information boundary scenes: {boundary_id}"
                )
            if not source_scenes & boundary_scenes:
                raise ValueError(
                    f"{label} {requirement_id} source does not anchor information boundary: {boundary_id}"
                )
            obligation = boundary["HLD obligation"]
            if obligation not in requirement["Inherited HLD obligations"]:
                raise ValueError(
                    f"{label} {requirement_id} does not preserve HLD obligation: {boundary_id}"
                )
        consumed.update(refs)
    missing = boundary_ids - consumed
    if missing:
        raise ValueError(
            f"{label} unmapped HLD information boundary obligation: {sorted(missing)}"
        )


def validate_story_logic_requirement_coverage(
    story_logic_rows: list[dict[str, str]],
    requirement_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    label: str,
) -> None:
    boundaries_by_id = {row["Boundary id"]: row for row in story_logic_rows}
    requirements_by_id = {row["Requirement id"]: row for row in requirement_rows}
    consumed: set[str] = set()
    for coverage in coverage_rows:
        boundary_id = coverage["Boundary id"]
        requirement_id = coverage["HLD requirement id"]
        if boundary_id not in boundaries_by_id:
            raise ValueError(f"{label} unknown Story logic boundary: {boundary_id}")
        if requirement_id not in requirements_by_id:
            raise ValueError(f"{label} unknown HLD requirement in Story logic coverage: {requirement_id}")
        if boundary_id in consumed:
            raise ValueError(f"{label} duplicate Story logic boundary coverage: {boundary_id}")
        boundary = boundaries_by_id[boundary_id]
        if coverage["Inherited frozen answer"] != boundary["Frozen answer"]:
            raise ValueError(f"{label} Story logic frozen answer drift: {boundary_id}")
        requirement = requirements_by_id[requirement_id]
        boundary_scenes = structured_source_refs(boundary["Source"])["scene"]
        support_scenes = set(re.findall(r"PRD-S\d{2,}", requirement["Supports scene ids"]))
        source_scenes = structured_source_refs(requirement["Source"])["scene"]
        if not support_scenes & boundary_scenes:
            raise ValueError(f"{label} {requirement_id} does not support Story logic boundary: {boundary_id}")
        if not source_scenes & boundary_scenes:
            raise ValueError(f"{label} {requirement_id} source does not anchor Story logic boundary: {boundary_id}")
        consumed.add(boundary_id)
    missing = set(boundaries_by_id) - consumed
    if missing:
        raise ValueError(f"{label} unmapped Story logic boundary: {sorted(missing)}")


def validate_hld_expansion_requirements(
    rows: list[dict[str, str]],
    canonical_scenes: dict[str, dict[str, str]],
    proposal_claims: dict[str, dict[str, str]],
    label: str,
) -> None:
    seen_requirement_ids: set[str] = set()
    for row in rows:
        requirement_id = row["Requirement id"]
        if not HLD_REQUIREMENT_ID_PATTERN.fullmatch(requirement_id):
            raise ValueError(f"{label} invalid HLD expansion requirement id: {requirement_id}")
        if requirement_id in seen_requirement_ids:
            raise ValueError(f"{label} duplicate HLD expansion requirement id: {requirement_id}")
        seen_requirement_ids.add(requirement_id)
        validate_semantic_fields(
            row,
            [
                "Requirement id",
                "Required expansion",
                "Supports scene ids",
                "Required answer",
                "Boundary",
                "Source",
            ],
            f"{label} {requirement_id}",
        )
        supported_scenes = set(re.findall(r"PRD-S\d{2,}", row["Supports scene ids"]))
        if not supported_scenes:
            raise ValueError(f"{label} {requirement_id} missing Supports scene ids")
        unknown_scenes = supported_scenes - set(canonical_scenes)
        if unknown_scenes:
            raise ValueError(
                f"{label} unknown HLD support scene ids: {sorted(unknown_scenes)}"
            )
        validate_source_references(
            row["Source"],
            canonical_scenes,
            proposal_claims,
            f"{label} unknown HLD source",
        )
        source_scenes = structured_source_refs(row["Source"])["scene"]
        if source_scenes != supported_scenes:
            raise ValueError(
                f"{label} {requirement_id} source scenes does not exactly match Supports scene ids"
            )


def validate_upstream_hld_entity_integration(
    artifact_07_text: str,
    final_package_text: str,
    label: str,
) -> None:
    canonical = markdown_section_text(
        artifact_07_text,
        "Upstream required HLD entities",
        f"{label} artifact 07",
    )
    integrated = markdown_section_text(
        final_package_text,
        "Upstream required HLD entities",
        f"{label} final-prd-package",
    )
    if integrated != canonical:
        raise ValueError(f"{label} Upstream required HLD entities drift: final-prd-package")


def validate_hld_expansion_requirement_integration(
    artifact_07_text: str,
    final_package_text: str,
    label: str,
) -> None:
    canonical = markdown_section_text(
        artifact_07_text,
        "HLD expansion requirement list",
        f"{label} artifact 07",
    )
    integrated = markdown_section_text(
        final_package_text,
        "HLD expansion requirement list",
        f"{label} final-prd-package",
    )
    if integrated != canonical:
        raise ValueError(f"{label} HLD expansion requirement list drift: final-prd-package")


def validate_story_logic_requirement_coverage_integration(
    artifact_07_text: str,
    final_package_text: str,
    label: str,
) -> None:
    canonical = markdown_section_text(
        artifact_07_text,
        "Story logic requirement coverage",
        f"{label} artifact 07",
    )
    integrated = markdown_section_text(
        final_package_text,
        "Story logic requirement coverage",
        f"{label} final-prd-package",
    )
    if integrated != canonical:
        raise ValueError(f"{label} Story logic requirement coverage drift: final-prd-package")


def sha256_digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def validate_prd_package_attestation(
    manifest_text: str,
    registered_paths: dict[str, str],
    run_id: str,
    label: str,
) -> None:
    fields = field_value_map(
        parse_markdown_table_rows(manifest_text, "PRD package attestation", label),
        f"{label} PRD package attestation",
    )
    required_fields = {"Run id", "Harness", "Package state"}
    missing_fields = required_fields - set(fields)
    if missing_fields:
        raise ValueError(f"{label} PRD package attestation missing fields: {sorted(missing_fields)}")
    if unquote_cell(fields["Run id"]) != run_id:
        raise ValueError(f"{label} PRD package attestation run id mismatch")
    if unquote_cell(fields["Harness"]) != "novel-prd-workflow":
        raise ValueError(f"{label} PRD package attestation harness mismatch")
    if unquote_cell(fields["Package state"]) not in {"packaged_for_human_review", "accepted"}:
        raise ValueError(f"{label} PRD package attestation invalid package state")
    rows = row_dicts(
        parse_markdown_table_rows(manifest_text, "Frozen artifact digest manifest", label),
        ["Artifact id", "Registered path", "SHA-256"],
        f"{label} Frozen artifact digest manifest",
    )
    attested = {row["Artifact id"]: row for row in rows}
    if set(attested) != set(registered_paths):
        raise ValueError(f"{label} PRD package attestation artifact set mismatch")
    for artifact_id, registered_path in registered_paths.items():
        row = attested[artifact_id]
        if unquote_cell(row["Registered path"]) != registered_path:
            raise ValueError(f"{label} PRD package attestation path mismatch: {artifact_id}")
        if unquote_cell(row["SHA-256"]) != sha256_digest(resolve_recorded_path(registered_path)):
            raise ValueError(f"{label} PRD package attestation digest mismatch: {artifact_id}")


def validate_formal_prd_artifact_texts(
    artifacts: dict[str, str],
    label: str,
    proposal_claim_ids: set[str] | None = None,
    proposal_claims: dict[str, dict[str, str]] | None = None,
) -> None:
    if proposal_claims is None or proposal_claim_ids is not None:
        raise ValueError(f"{label} requires full proposal claim map")
    proposal_trace_source: dict[str, dict[str, str]] = proposal_claims
    required_ids = {"01", "02", "03", "04", "05", "06", "07", "08", "09", "final-prd-package"}
    missing_ids = required_ids - set(artifacts)
    if missing_ids:
        raise ValueError(f"{label} missing required artifact texts: {sorted(missing_ids)}")

    validate_scope_artifact(artifacts["01"], proposal_trace_source, f"{label} artifact 01")
    validate_part_goal_artifact(artifacts["02"], proposal_trace_source, f"{label} artifact 02")
    validate_skill_output_verdict(artifacts["01"], f"{label} artifact 01")
    validate_skill_output_verdict(artifacts["02"], f"{label} artifact 02")

    trunk_rows = parse_markdown_table_rows(artifacts["03"], "Trunk scene table", f"{label} artifact 03")
    canonical_scenes = validate_trunk_scene_rows(
        trunk_rows,
        f"{label} artifact 03 Trunk scene table",
        proposal_trace_source,
    )
    for scene_id, scene in canonical_scenes.items():
        validate_proposal_trace_text(scene["proposal_trace"], proposal_trace_source, f"{label} artifact 03 {scene_id}")
    validate_skill_output_verdict(artifacts["03"], f"{label} artifact 03")

    conflict_rows = rows_as_dicts(
        artifacts["04"],
        "Conflict and value-shift table",
        f"{label} artifact 04",
        [
            "Scene id",
            "Conflict type",
            "Conflict pressure",
            "Start value",
            "End value",
            "Irreversibility",
            "Proposal trace",
        ],
    )
    validate_scene_coverage(
        canonical_scenes,
        conflict_rows,
        "conflict/value table",
        [
            "Scene id",
            "Conflict type",
            "Conflict pressure",
            "Start value",
            "End value",
            "Irreversibility",
            "Proposal trace",
        ],
    )
    for row in conflict_rows:
        validate_semantic_fields(
            row,
            ["Conflict pressure", "Start value", "End value", "Irreversibility", "Proposal trace"],
            f"{label} artifact 04 {row['Scene id']}",
        )
        validate_proposal_trace_text(row["Proposal trace"], proposal_trace_source, f"{label} artifact 04 {row['Scene id']}")
        validate_proposal_claim_support(
            " ".join(
                [
                    row["Conflict type"],
                    row["Conflict pressure"],
                    row["Start value"],
                    row["End value"],
                    row["Irreversibility"],
                ]
            ),
            row["Proposal trace"],
            proposal_trace_source,
            f"{label} artifact 04 {row['Scene id']}",
        )
    validate_skill_output_verdict(artifacts["04"], f"{label} artifact 04")

    information_rows = rows_as_dicts(
        artifacts["05"],
        "Information-flow table",
        f"{label} artifact 05",
        [
            "Scene id",
            "Reader learns",
            "Focal character learns",
            "Other actor information",
            "Misbelief or concealment",
            "Next-scene pressure",
            "HLD information need",
        ],
    )
    validate_scene_coverage(
        canonical_scenes,
        information_rows,
        "information-flow table",
        [
            "Scene id",
            "Reader learns",
            "Focal character learns",
            "Other actor information",
            "Misbelief or concealment",
            "Next-scene pressure",
            "HLD information need",
        ],
    )
    for row in information_rows:
        validate_semantic_fields(
            row,
            [
                "Reader learns",
                "Focal character learns",
                "Other actor information",
                "Misbelief or concealment",
                "Next-scene pressure",
                "HLD information need",
            ],
            f"{label} artifact 05 {row['Scene id']}",
        )
    boundary_rows = validate_hld_information_boundary_table(
        artifacts["05"],
        artifacts["06"],
        canonical_scenes,
        f"{label} artifact 05",
    )
    validate_skill_output_verdict(artifacts["05"], f"{label} artifact 05")

    scene_source_rows = rows_as_dicts(
        artifacts["08"],
        "Scene Source Map",
        f"{label} artifact 08",
        ["Scene id", "Order", "Event fact", "Causal output", "Proposal trace", "Source artifact"],
    )
    validate_prd_integration_verdict(artifacts["08"], f"{label} artifact 08")
    validate_skill_output_verdict(artifacts["08"], f"{label} artifact 08")
    validate_scene_source_map_rows(
        canonical_scenes,
        scene_source_rows,
        f"{label} Scene Source Map",
        proposal_claims=proposal_trace_source,
    )

    validate_prd_risk_verdict_consistency(artifacts["09"], f"{label} artifact 09")
    validate_skill_output_verdict(artifacts["09"], f"{label} artifact 09")

    validate_freeze_artifact(
        artifacts["06"],
        f"{label} artifact 06",
        canonical_scenes=canonical_scenes,
        proposal_claims=proposal_trace_source,
    )
    validate_skill_output_verdict(artifacts["06"], f"{label} artifact 06")
    story_logic_rows = validate_story_logic_boundary_table(
        artifacts["03"],
        canonical_scenes,
        proposal_trace_source,
        f"{label} artifact 03",
    )
    validate_final_prd_package(artifacts["final-prd-package"], f"{label} final-prd-package")
    validate_hld_information_boundary_integration(
        artifacts["05"],
        artifacts["08"],
        artifacts["final-prd-package"],
        label,
    )

    hld_rows = rows_as_dicts(
        artifacts["07"],
        "HLD expansion requirement list",
        f"{label} artifact 07",
        [
            "Requirement id",
            "Required expansion",
            "Supports scene ids",
            "Information boundary refs",
            "Inherited HLD obligations",
            "Required answer",
            "Boundary",
            "Source",
        ],
    )
    validate_hld_expansion_requirements(
        hld_rows,
        canonical_scenes,
        proposal_trace_source,
        f"{label} artifact 07",
    )
    story_logic_coverage_rows = rows_as_dicts(
        artifacts["07"],
        "Story logic requirement coverage",
        f"{label} artifact 07",
        ["Boundary id", "HLD requirement id", "Inherited frozen answer"],
    ) if story_logic_rows else []
    validate_story_logic_requirement_coverage(
        story_logic_rows,
        hld_rows,
        story_logic_coverage_rows,
        f"{label} artifact 07",
    )
    supported_scene_ids = {
        scene_id
        for row in hld_rows
        for scene_id in re.findall(r"PRD-S\d{2,}", row["Supports scene ids"])
    }
    missing_hld_support = set(canonical_scenes) - supported_scene_ids
    if missing_hld_support:
        raise ValueError(f"{label} HLD expansion requirements missing scene ids: {sorted(missing_hld_support)}")
    entity_rows = validate_upstream_required_hld_entities(
        artifacts["07"],
        canonical_scenes,
        proposal_trace_source,
        f"{label} artifact 07",
    )
    validate_information_boundary_knowledge_entity_closure(
        boundary_rows,
        entity_rows,
        f"{label} artifact 05",
    )
    validate_story_logic_entity_closure(
        story_logic_rows,
        entity_rows,
        f"{label} artifact 07",
    )
    validate_information_boundary_obligation_coverage(
        boundary_rows,
        hld_rows,
        f"{label} artifact 07",
    )
    validate_hld_expansion_requirement_integration(
        artifacts["07"],
        artifacts["final-prd-package"],
        label,
    )
    if story_logic_rows:
        validate_story_logic_requirement_coverage_integration(
            artifacts["07"],
            artifacts["final-prd-package"],
            label,
        )
    validate_upstream_required_hld_entities(
        artifacts["final-prd-package"],
        canonical_scenes,
        proposal_trace_source,
        f"{label} final-prd-package",
    )
    validate_upstream_hld_entity_integration(
        artifacts["07"],
        artifacts["final-prd-package"],
        label,
    )
    validate_skill_output_verdict(artifacts["07"], f"{label} artifact 07")
    validate_pre_extraction_causal_setup(canonical_scenes, label)
    validate_scene_execution_table(
        artifacts["03"],
        canonical_scenes,
        proposal_trace_source,
        f"{label} artifact 03",
    )


def validate_convergence_covers_blocking_risks(
    risk_report_text: str,
    manifest_text: str,
    label: str,
) -> None:
    risk_rows = parse_markdown_table_rows(risk_report_text, "Risks", label)
    risks = row_dicts(risk_rows, ["Risk", "Severity", "Handling"], f"{label} Risks")
    blocking_risks = [risk for risk in risks if unquote_cell(risk["Severity"]) in {"P0", "P1"}]
    if not blocking_risks:
        return
    entries = convergence_log_entries(manifest_text, label)
    searchable_rows = [
        " ".join(
            [
                entry["Stable issue id"],
                entry["Root cause"],
                entry["Fix hypothesis"],
                entry["Regression proof"],
            ]
        )
        for entry in entries
    ]
    for risk in blocking_risks:
        risk_name = risk["Risk"]
        if not any(risk_name in entry_text for entry_text in searchable_rows):
            raise ValueError(f"{label} missing convergence row for blocking risk: {risk_name}")


def validate_formal_prd_artifact_run(artifact_run: dict, contract: dict, label: str) -> None:
    upstream_report = artifact_run.get("upstream_proposal_risk_report")
    if not upstream_report:
        raise ValueError(f"{label} missing upstream_proposal_risk_report")
    upstream_text = read(resolve_recorded_path(upstream_report))
    validate_upstream_proposal_entry_gate(upstream_text, f"{label} upstream proposal risk report")
    proposal_claims = proposal_claims_from_risk_report(
        upstream_text,
        f"{label} upstream proposal risk report",
    )

    manifest_path = resolve_recorded_path(artifact_run["manifest"])
    manifest_text = read(manifest_path)
    validate_manifest_required_terms(
        manifest_text,
        label,
        [
            "PRD workflow artifact run",
            "Harness: `novel-prd-workflow`",
            "Final PRD package:",
            "PRD Integration Verdict artifact:",
            "PRD Risk Report artifact:",
            "## Convergence log",
        ],
    )
    skill_artifacts = artifact_run.get("skill_artifacts", {})
    missing_skill_entries = set(contract["skills"]) - set(skill_artifacts)
    if missing_skill_entries:
        raise ValueError(f"{label} missing skill_artifacts: {sorted(missing_skill_entries)}")
    for skill, entries in skill_artifacts.items():
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"{label} skill must map to non-empty list: {skill}")
    final_package_path = artifact_run.get("final_prd_package")
    if not final_package_path:
        raise ValueError(f"{label} missing final_prd_package")
    required_artifact_paths = {
        "upstream-proposal-risk-report": upstream_report,
        "01": skill_artifacts["novel-part-scope-selector"][0],
        "02": skill_artifacts["novel-part-goal-definer"][0],
        "03": skill_artifacts["novel-trunk-scene-designer"][0],
        "04": skill_artifacts["novel-scene-conflict-value-designer"][0],
        "05": skill_artifacts["novel-scene-information-flow-designer"][0],
        "06": skill_artifacts["novel-prd-freeze-boundary-writer"][0],
        "07": skill_artifacts["novel-hld-expansion-requirement-writer"][0],
        "08": skill_artifacts["novel-prd-integrator"][0],
        "09": skill_artifacts["novel-prd-causality-checker"][0],
        "final-prd-package": final_package_path,
    }
    validate_prd_package_attestation(
        manifest_text,
        required_artifact_paths,
        artifact_run["id"],
        label,
    )
    artifact_texts = {
        artifact_id: read(resolve_recorded_path(artifact_path))
        for artifact_id, artifact_path in required_artifact_paths.items()
    }
    validate_formal_prd_artifact_texts(artifact_texts, label, proposal_claims=proposal_claims)
    validate_convergence_covers_blocking_risks(artifact_texts["09"], manifest_text, label)


def validate_prd_risk_verdict_consistency(risk_report_text: str, label: str) -> None:
    output_rows = parse_markdown_table_rows(risk_report_text, "Output", label)
    output = field_value_map(output_rows, f"{label} Output")
    risk_rows = parse_markdown_table_rows(risk_report_text, "Risks", label)
    risks = row_dicts(risk_rows, ["Risk", "Severity", "Handling"], f"{label} Risks")
    blocking_risks = [risk for risk in risks if unquote_cell(risk["Severity"]) in {"P0", "P1"}]
    agent_verdict = output.get("Agent quality verdict")
    human_verdict = output.get("Human review verdict")
    hld_verdict = output.get("HLD entry verdict")
    if not agent_verdict:
        raise ValueError(f"{label} missing Agent quality verdict")
    if not human_verdict:
        raise ValueError(f"{label} missing Human review verdict")
    if not hld_verdict:
        raise ValueError(f"{label} missing HLD entry verdict")
    if agent_verdict not in AGENT_QUALITY_VERDICTS:
        raise ValueError(f"{label} invalid Agent quality verdict: {agent_verdict}")
    if human_verdict not in HUMAN_REVIEW_VERDICTS:
        raise ValueError(f"{label} invalid Human review verdict: {human_verdict}")
    if hld_verdict not in HLD_ENTRY_VERDICTS:
        raise ValueError(f"{label} invalid HLD entry verdict: {hld_verdict}")
    core_statuses: dict[str, str] = {}
    for field in PRD_CORE_RISK_CHECK_FIELDS:
        if field not in output:
            raise ValueError(f"{label} missing core risk check field: {field}")
        status = status_token(output[field])
        if status not in {"pass", "fail", "not_checked"}:
            raise ValueError(f"{label} invalid core risk check status for {field}: {output[field]}")
        core_statuses[field] = status
    non_pass_core_checks = [
        field for field, status in core_statuses.items()
        if status != "pass"
    ]
    if agent_verdict == "pass" and non_pass_core_checks:
        raise ValueError(
            f"{label} Agent quality verdict cannot pass with non-pass core checks: {non_pass_core_checks}"
        )
    if non_pass_core_checks and not blocking_risks:
        raise ValueError(
            f"{label} non-pass core checks require unresolved P0/P1 risks: {non_pass_core_checks}"
        )
    if agent_verdict != "pass" and not blocking_risks and not non_pass_core_checks:
        raise ValueError(f"{label} non-pass Agent quality verdict requires blocking evidence")
    if blocking_risks and agent_verdict == "pass":
        names = [risk["Risk"] for risk in blocking_risks]
        raise ValueError(f"{label} Agent quality verdict cannot pass with unresolved P0/P1 risks: {names}")
    revision_blocked = (
        bool(blocking_risks)
        or bool(non_pass_core_checks)
        or agent_verdict != "pass"
        or human_verdict == "reopen_prd"
    )
    if revision_blocked:
        expected_hld_verdict = "blocked_revision_required"
    elif human_verdict == "confirmed":
        expected_hld_verdict = "pass_to_hld"
    else:
        expected_hld_verdict = "blocked_pending_human_review"
    if hld_verdict != expected_hld_verdict:
        raise ValueError(
            f"{label} HLD entry verdict must be {expected_hld_verdict}; got {hld_verdict}"
        )


def require_terms(label: str, text: str, terms: list[str]) -> None:
    for term in terms:
        if term not in text:
            raise ValueError(f"{label} missing required term: {term}")


def main() -> None:
    contract = load_contract()
    if contract.get("node") != "prd":
        fail("contract node must be prd")
    if contract.get("harness") != "novel-prd-workflow":
        fail("contract harness must be novel-prd-workflow")
    if int(contract.get("prd_skill_count", 0)) != 9:
        fail("contract prd_skill_count must be 9")
    try:
        validate_required_static_checks(contract, "contract")
        validate_contract_rule_coverage(contract, "contract")
        validate_prd_runs_declared(contract, "contract")
    except ValueError as exc:
        fail(str(exc))

    for skill in contract["skills"]:
        skill_path = ROOT / "skills" / skill / "SKILL.md"
        if not skill_path.exists():
            fail(f"contract skill has no SKILL.md: {skill}")
        try:
            validate_skill_contract_text(read(skill_path), skill)
        except ValueError as exc:
            fail(str(exc))

    for gate in contract["hard_gates"]:
        if gate["owner_type"] != "independent_skill":
            fail(f"hard gate must be owned by an independent skill: {gate['id']}")
        owner_path = ROOT / "skills" / gate["owner"] / "SKILL.md"
        if not owner_path.exists():
            fail(f"gate owner has no SKILL.md: {gate['id']} -> {gate['owner']}")

    try:
        validate_prd_artifact_topology(contract["artifact_dag"], "contract artifact_dag")
    except ValueError as exc:
        fail(str(exc))

    for blocked_run in contract.get("blocked_runs", []):
        try:
            validate_blocked_run(blocked_run, f"blocked_run {blocked_run.get('id', '<missing id>')}")
        except ValueError as exc:
            fail(str(exc))

    for artifact_run in contract.get("artifact_runs", []):
        try:
            validate_formal_prd_artifact_run(
                artifact_run,
                contract,
                f"artifact_run {artifact_run.get('id', '<missing id>')}",
            )
        except ValueError as exc:
            fail(str(exc))

    workflow = read(WORKFLOW_SKILL)
    try:
        require_terms(
            "PRD workflow skill",
            workflow,
            [
                "proposal PRD entry verdict",
                "novel-prd-causality-checker",
                "final-prd-package",
                "## Convergence Protocol",
                "Claim trace is fact-level",
                "non-pass PRD core risk check",
                "It must not independently judge trunk-scene causality",
                "Story logic boundary table",
                "plausibility anchors",
            ],
        )
        require_terms(
            "PRD trunk scene designer skill",
            read(ROOT / "skills/novel-trunk-scene-designer/SKILL.md"),
            [
                "Story logic boundary table",
                "usable intelligence",
                "complete cause",
                "protected-person",
                "terminal-deception",
                "plausibility anchors",
            ],
        )
        require_terms(
            "PRD causality checker skill",
            read(CAUSALITY_CHECKER),
            [
                "## Output",
                "Field | Value",
                "## Risks",
                "Agent quality verdict",
                "HLD entry verdict",
                "blocking P0/P1 risk",
                "Story logic boundary table",
                "plausibility anchors",
            ],
        )
        require_terms(
            "PRD integrator skill",
            read(INTEGRATOR),
            [
                "Scene Source Map",
                "Scene id",
                "Order",
                "Event fact",
                "Causal output",
                "Proposal trace",
                "Source artifact",
            ],
        )
        require_terms(
            "harness design doc",
            read(HARNESS_DOC),
            [
                "proposal PRD entry verdict",
                "PRD harness 的调度状态机",
                "Convergence Protocol",
            ],
        )
        require_terms(
            "workflow creation doc",
            read(CREATION_DOC),
            [
                "主干场景表",
                "PRD rules",
                "PRD traceability",
            ],
        )
    except ValueError as exc:
        fail(str(exc))

    print("PRD contract valid")


if __name__ == "__main__":
    main()
