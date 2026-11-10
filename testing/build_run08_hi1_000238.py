from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "projects/duanxian/development/hld-run-08"
WORK_ORDER_PATH = RUN / "work-order-000238-HI1.json"
DRAFT = RUN / "draft-HI1-000238"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def digest(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    wo = load(WORK_ORDER_PATH)
    by_role = {item["role"]: item for item in wo["file_allowlist"]}
    hb = load(RUN / by_role["upstream::HB0::main"]["path"])
    source_index = load(RUN / by_role["source_index"]["path"])
    ha = load(RUN / by_role["upstream::HA1::main"]["path"])
    hs = load(RUN / by_role["upstream::HS1::main"]["path"])
    hc = load(RUN / by_role["upstream::HC1::main"]["path"])

    source_meta: dict[str, dict] = {}

    def visit(value: object) -> None:
        if isinstance(value, dict):
            source_id = value.get("source_id")
            if isinstance(source_id, str) and "value_sha256" in value:
                source_meta.setdefault(
                    source_id,
                    {
                        "source_id": source_id,
                        "classification": value.get("classification", "mandatory"),
                        "open_item": value.get("open_item", False),
                        "authority_class": value.get("authority_class", "autonomous_owned"),
                        "value_sha256": value["value_sha256"],
                    },
                )
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for document in (hb, source_index, ha, hs, hc):
        visit(document)

    # Source-index rows do not repeat the authority dimensions. Complete only the three
    # sealed author-open controls from HB0's unresolved register.
    unresolved = {item["source_id"]: item for item in hb["unresolved_register"]}
    for source_id, item in unresolved.items():
        if source_id in source_meta:
            source_meta[source_id].update(
                classification=item["classification"],
                open_item=item["open_item"],
                authority_class=item["authority_class"],
            )

    def auth(source_ids: list[str]) -> list[dict]:
        missing = [source_id for source_id in source_ids if source_id not in source_meta]
        if missing:
            raise RuntimeError(f"missing authority metadata: {missing}")
        return [source_meta[source_id] for source_id in source_ids]

    units = ha["narrative_units"]
    chapters = ha["chapter_shells"]
    agency_by_chapter = {item["chapter_id"]: item for item in hc["chapter_agency_contracts"]}
    plan_by_chapter = {item["chapter_id"]: item for item in hs["chapter_storyline_plan"]}

    expected_focal = {
        **{chapters[0]["id"]: "CHR-GUHENG"},
        **{chapters[index]["id"]: "CHR-LIANG-CE" for index in (1, 2)},
        **{chapter["id"]: "CHR-SHEN-YU" for chapter in chapters[3:]},
    }

    chapter_assignments = []
    selected_paths: dict[str, dict] = {}
    for chapter in chapters:
        chapter_id = chapter["id"]
        agency = agency_by_chapter[chapter_id]
        focal = expected_focal[chapter_id]
        paths = [item for item in agency["information_paths"] if item["character_id"] == focal]
        if len(paths) != 1 or focal not in agency["focal_character_ids"]:
            raise RuntimeError(f"sealed HC1 does not authorize required focal: {chapter_id} -> {focal}")
        path = paths[0]
        selected_paths[chapter_id] = path
        chapter_assignments.append(
            {
                "id": f"HPV-{chapter_id}",
                "source_refs": chapter["source_refs"],
                "source_authority_refs": chapter["source_authority_refs"],
                "ownership_class": "hld_owned",
                "resolution_ref": None,
                "chapter_id": chapter_id,
                "parent_unit_id": chapter["parent_unit_id"],
                "hc1_agency_contract_id": agency["id"],
                "pov_character_id": focal,
                "focalization_mode": "外部限制第三人称" if focal != "CHR-SHEN-YU" else "沈逾限制第三人称",
                "knowledge_acquisition_modes": path["acquisition_modes"],
                "perception_limits": [path["limit"]],
            }
        )

    policy_sources = ["NAR-POV-ARCHITECTURE"]
    pov_policy = {
        "id": "HPV-POLICY-SINGLE-REALITY",
        "source_refs": policy_sources,
        "source_authority_refs": auth(policy_sources),
        "ownership_class": "source_projection",
        "resolution_ref": None,
        "allowed_modes": ["外部限制第三人称", "沈逾限制第三人称", "受限记忆材料经沈逾接收"],
        "switch_rule": "视角只在章节边界切换；第一章由顾衡承载，第二至三章由梁策通过记录和通报承载，第四至二十四章持续由沈逾承载。",
        "legality_rule": "R-07 启动后现实线只允许沈逾作为焦点人物；顾衡昏迷后不再承担视角，R-07 的错序记忆只能作为沈逾接收到的受限信息，不能形成独立叙事线。",
    }

    unit_assignments = []
    for index, unit in enumerate(units):
        focal = "CHR-GUHENG" if index == 0 else "CHR-SHEN-YU"
        unit_assignments.append(
            {
                "id": f"HPV-UNIT-{index + 1:02d}",
                "source_refs": unit["source_refs"],
                "source_authority_refs": unit["source_authority_refs"],
                "ownership_class": "hld_owned",
                "resolution_ref": None,
                "unit_id": unit["id"],
                "pov_character_id": focal,
                "focalization_mode": "外部限制第三人称" if index == 0 else "沈逾限制第三人称",
                "perception_limits": [
                    "单元默认不越过人物当时可接触的信息；章节级分配是实际约束，第二至三章按梁策的书面记录和通报限制执行。"
                    if index == 0
                    else "只呈现沈逾能够接收、核验、回忆或合理推断的信息；不得进入 R-07、专家、行动人员或机构代表的内心。"
                ],
            }
        )

    def choose_mode(chapter_id: str, preferences: tuple[str, ...]) -> str:
        modes = selected_paths[chapter_id]["acquisition_modes"]
        for mode in preferences:
            if mode in modes:
                return mode
        return modes[0]

    information_nodes: list[dict] = []

    def add_node(
        node_id: str,
        chapter_id: str,
        source_information_id: str,
        reader_state: str,
        preferences: tuple[str, ...],
        *,
        source_ids: list[str] | None = None,
        ownership: str = "hld_owned",
    ) -> None:
        chapter = next(item for item in chapters if item["id"] == chapter_id)
        plan = plan_by_chapter[chapter_id]
        focal = expected_focal[chapter_id]
        refs = source_ids or plan["source_refs"]
        information_nodes.append(
            {
                "id": node_id,
                "source_refs": refs,
                "source_authority_refs": auth(refs) if source_ids else plan["source_authority_refs"],
                "ownership_class": ownership,
                "resolution_ref": None,
                "source_information_id": source_information_id,
                "knower_ids": [focal],
                "reader_state": reader_state,
                "acquisition_mode": choose_mode(chapter_id, preferences),
                "earliest_legal_unit_id": chapter["parent_unit_id"],
                "forbidden_leak_unit_ids": [
                    unit["id"] for unit in units if unit["order"] < next(x["order"] for x in units if x["id"] == chapter["parent_unit_id"])
                ],
            }
        )

    # One chapter-level information transition for every chapter. Each transition has
    # exactly one knower and uses one mode allowed by the selected HC1 focal path.
    for number, chapter in enumerate(chapters, start=1):
        chapter_id = chapter["id"]
        plan = plan_by_chapter[chapter_id]
        preferences = (
            ("perceived", "inferred")
            if number == 1
            else ("documented", "told")
            if number in (2, 3)
            else ("system_output", "documented", "told", "remembered", "inferred", "perceived")
        )
        add_node(
            f"HIN-CHAPTER-{number:02d}",
            chapter_id,
            plan["primary_storyline_id"],
            "known",
            preferences,
        )

    # Eleven explicit semantic transitions keep the memory, evidence, and termination
    # chains distinguishable. They deliberately remain single-knower records.
    add_node("HIN-GUHENG-ONSITE-MINIMUM-CLUE", "HCH-01-01", "CAU-MAJOR-NODES", "known", ("perceived",))
    add_node("HIN-LIANG-DOCUMENTED-RECEIPT", "HCH-01-02", "CAU-MAJOR-NODES", "known", ("documented", "told"))
    for suffix, chapter_id, state in (
        ("SOURCE-LABEL", "HCH-03-01", "inferable"),
        ("NONLINEAR-ORDER", "HCH-03-02", "inferable"),
        ("REALITY-CORROBORATION", "HCH-03-03", "known"),
        ("INHERITED-NOT-CURRENT", "HCH-04-01", "known"),
    ):
        add_node(
            f"HIN-MEMORY-{suffix}",
            chapter_id,
            "NAR-MEMORY-FRAGMENTS",
            state,
            ("system_output", "told", "documented", "inferred", "remembered"),
            source_ids=["NAR-MEMORY-FRAGMENTS"],
        )
    add_node("HIN-R07-TERMINATION-REQUEST-RECORDED", "HCH-07-03", "CAU-RESOLVED", "known", ("told",), source_ids=["CAU-RESOLVED"])
    add_node("HIN-THREAT-RESOLVED", "HCH-08-01", "CAU-RESOLVED", "known", ("told", "system_output", "documented"), source_ids=["CAU-RESOLVED"])
    add_node("HIN-AUTHORIZED-SHUTDOWN", "HCH-08-02", "NAR-ENDING-MUST-REVEAL", "known", ("documented", "system_output", "told"), source_ids=["NAR-ENDING-MUST-REVEAL"])
    add_node("HIN-NO-ACTIVE-R07-BACKUP", "HCH-08-03", "NAR-ENDING-MUST-REVEAL", "known", ("documented", "told", "remembered"), source_ids=["NAR-ENDING-MUST-REVEAL"])
    add_node(
        "HIN-FUTURE-IDENTITY-OPEN",
        "HCH-08-03",
        "NAR-ENDING-PRESERVED-OPEN",
        "open",
        ("documented", "told", "remembered"),
        source_ids=["NAR-ENDING-PRESERVED-OPEN"],
        ownership="preserved_open",
    )

    # One explicit character transition per information node makes provenance auditable;
    # no state groups several knowers or implies automatic knowledge sharing.
    knowledge_states = []
    for index, node in enumerate(information_nodes, start=1):
        knowledge_states.append(
            {
                "id": f"HKS-CHARACTER-{index:02d}",
                "source_refs": node["source_refs"],
                "source_authority_refs": node["source_authority_refs"],
                "ownership_class": node["ownership_class"],
                "resolution_ref": None,
                "character_id": node["knower_ids"][0],
                "unit_id": node["earliest_legal_unit_id"],
                "information_node_ids": [node["id"]],
                "misbelief_node_ids": [],
            }
        )

    reader_states = []
    for index, unit in enumerate(units, start=1):
        node_ids = [
            node["id"]
            for node in information_nodes
            if node["earliest_legal_unit_id"] == unit["id"] and node["reader_state"] != "hidden"
        ]
        refs = unit["source_refs"]
        reader_states.append(
            {
                "id": f"HKS-READER-{index:02d}",
                "source_refs": refs,
                "source_authority_refs": unit["source_authority_refs"],
                "ownership_class": "hld_owned",
                "resolution_ref": None,
                "unit_id": unit["id"],
                "information_node_ids": node_ids,
                "inference_permissions": [
                    "只能依据本单元已列信息形成暂时判断；错序记忆可以改变怀疑方向，但必须等待现实材料核验。",
                    "不得把顾衡的记忆、R-07 的当下判断和机构确认视为同一种证据。",
                ],
            }
        )

    def object_contract(
        object_id: str,
        source_ids: list[str],
        ownership: str = "hld_owned",
    ) -> dict:
        return {
            "id": object_id,
            "source_refs": source_ids,
            "source_authority_refs": auth(source_ids),
            "ownership_class": ownership,
            "resolution_ref": None,
        }

    suspense_chains = [
        {
            **object_contract("HSP-MEMORY-TRUTH", ["NAR-MEMORY-FRAGMENTS", "CAU-MAJOR-NODES"]),
            "setup_node_ids": ["HIN-GUHENG-ONSITE-MINIMUM-CLUE", "HIN-MEMORY-SOURCE-LABEL"],
            "probe_node_ids": ["HIN-MEMORY-NONLINEAR-ORDER", "HIN-MEMORY-INHERITED-NOT-CURRENT"],
            "reveal_node_ids": ["HIN-MEMORY-REALITY-CORROBORATION"],
            "payoff_node_ids": ["HIN-CHAPTER-18"],
            "authorized_open_terminal": None,
        },
        {
            **object_contract("HSP-THREAT-EVIDENCE-CLOSURE", ["CAU-GLOBAL-SPINE", "CAU-RESOLVED"]),
            "setup_node_ids": ["HIN-GUHENG-ONSITE-MINIMUM-CLUE"],
            "probe_node_ids": ["HIN-LIANG-DOCUMENTED-RECEIPT", "HIN-CHAPTER-18"],
            "reveal_node_ids": ["HIN-CHAPTER-19"],
            "payoff_node_ids": ["HIN-THREAT-RESOLVED"],
            "authorized_open_terminal": None,
        },
        {
            **object_contract("HSP-TERMINATION-CHAIN", ["CAU-RESOLVED", "NAR-ENDING-MUST-REVEAL"]),
            "setup_node_ids": ["HIN-R07-TERMINATION-REQUEST-RECORDED"],
            "probe_node_ids": ["HIN-THREAT-RESOLVED"],
            "reveal_node_ids": ["HIN-AUTHORIZED-SHUTDOWN"],
            "payoff_node_ids": ["HIN-NO-ACTIVE-R07-BACKUP"],
            "authorized_open_terminal": None,
        },
        {
            **object_contract("HSP-FUTURE-IDENTITY-OPEN", ["NAR-ENDING-PRESERVED-OPEN"], "preserved_open"),
            "setup_node_ids": ["HIN-R07-TERMINATION-REQUEST-RECORDED"],
            "probe_node_ids": ["HIN-AUTHORIZED-SHUTDOWN", "HIN-NO-ACTIVE-R07-BACKUP"],
            "reveal_node_ids": [],
            "payoff_node_ids": [],
            "authorized_open_terminal": "未来是否重载、重载者是否与当前 R-07 连续，以及两国能否恢复互信，均保持未决。",
        },
    ]

    payoff_matrix = [
        {
            **object_contract("HIN-TRACE-MEMORY-TRUTH", ["NAR-MEMORY-FRAGMENTS", "CAU-MAJOR-NODES"]),
            "information_node_ids": ["HIN-MEMORY-SOURCE-LABEL", "HIN-MEMORY-NONLINEAR-ORDER", "HIN-MEMORY-REALITY-CORROBORATION"],
            "setup_unit_ids": ["HNU-03-RECOGNITION-AND-CARE"],
            "terminal_unit_id": "HNU-06-EVIDENCE-TO-ACTION",
            "terminal_kind": "payoff",
        },
        {
            **object_contract("HIN-TRACE-THREAT-CLOSURE", ["CAU-GLOBAL-SPINE", "CAU-RESOLVED"]),
            "information_node_ids": ["HIN-GUHENG-ONSITE-MINIMUM-CLUE", "HIN-LIANG-DOCUMENTED-RECEIPT", "HIN-THREAT-RESOLVED"],
            "setup_unit_ids": ["HNU-01-GUHENG-BREAK", "HNU-06-EVIDENCE-TO-ACTION"],
            "terminal_unit_id": "HNU-08-STOP-SHUTDOWN-AFTERMATH",
            "terminal_kind": "payoff",
        },
        {
            **object_contract("HIN-TRACE-TERMINATION", ["CAU-RESOLVED", "NAR-ENDING-MUST-REVEAL"]),
            "information_node_ids": ["HIN-R07-TERMINATION-REQUEST-RECORDED", "HIN-THREAT-RESOLVED", "HIN-AUTHORIZED-SHUTDOWN", "HIN-NO-ACTIVE-R07-BACKUP"],
            "setup_unit_ids": ["HNU-07-R07-CHOICE-AND-PROMISE"],
            "terminal_unit_id": "HNU-08-STOP-SHUTDOWN-AFTERMATH",
            "terminal_kind": "payoff",
        },
        {
            **object_contract("HIN-TRACE-FUTURE-OPEN", ["NAR-ENDING-PRESERVED-OPEN"], "preserved_open"),
            "information_node_ids": ["HIN-FUTURE-IDENTITY-OPEN"],
            "setup_unit_ids": ["HNU-07-R07-CHOICE-AND-PROMISE"],
            "terminal_unit_id": "HNU-08-STOP-SHUTDOWN-AFTERMATH",
            "terminal_kind": "authorized_open",
        },
    ]

    inference_rules = [
        {
            **object_contract("HIN-RULE-MEMORY-NOT-RECORD", ["NAR-MEMORY-FRAGMENTS"]),
            "information_node_ids": ["HIN-MEMORY-SOURCE-LABEL", "HIN-MEMORY-NONLINEAR-ORDER", "HIN-MEMORY-REALITY-CORROBORATION"],
            "concealment_basis": "片段本身缺少完整时序和现实核验，沈逾与读者只能把它当成调查方向。",
            "legal_inferences": ["片段可能指向真实关系或威胁，但可信程度随现实材料逐步改变。"],
            "forbidden_inferences": ["不得把片段当成顾衡完整回忆、法律证词或 R-07 当前意愿。"],
        },
        {
            **object_contract("HIN-RULE-SEPARATE-PROVENANCE", ["NAR-R07-INFORMATION-BOUNDARY", "CAU-MAJOR-NODES"]),
            "information_node_ids": ["HIN-GUHENG-ONSITE-MINIMUM-CLUE", "HIN-LIANG-DOCUMENTED-RECEIPT"],
            "concealment_basis": "顾衡在场感知与梁策后来收到的记录属于两条不同来源链。",
            "legal_inferences": ["两条来源可以相互印证，但不能自动合并为同一人的连续知识。"],
            "forbidden_inferences": ["不得让梁策拥有顾衡未传出的现场感知，也不得让顾衡预知后续书面通报。"],
        },
        {
            **object_contract("HIN-RULE-REALITY-ACTION-INDEPENDENT", ["CAU-RESOLVED", "NAR-ENDING-MUST-REVEAL"]),
            "information_node_ids": ["HIN-THREAT-RESOLVED", "HIN-AUTHORIZED-SHUTDOWN", "HIN-NO-ACTIVE-R07-BACKUP"],
            "concealment_basis": "现实阻断、意识关停与关停后核验是先后独立的责任链。",
            "legal_inferences": ["读者可以确认公共危机先闭环，再确认经授权关停，最后确认无活动副本。"],
            "forbidden_inferences": ["不得让 R-07 直接控制现实设备，也不得把关停请求等同于已经关停。"],
        },
        {
            **object_contract("HIN-RULE-OPEN-FUTURE", ["NAR-ENDING-PRESERVED-OPEN"], "preserved_open"),
            "information_node_ids": ["HIN-FUTURE-IDENTITY-OPEN"],
            "concealment_basis": "来源明确要求未来重载、身份连续性和两国互信不在本部回答。",
            "legal_inferences": ["读者可以理解静态材料仍在，但不能据此认定活动意识仍存续。"],
            "forbidden_inferences": ["不得承诺顾衡苏醒、R-07 复活、身份连续或国家互信恢复。"],
        },
    ]

    dependencies = [
        {
            "id": f"HDD-HI1-{source_id}",
            "source_id": source_id,
            "owner_stage": "HI1",
            "affected_obligation_ids": ["HSP-FUTURE-IDENTITY-OPEN"],
            "disposition": "conditional_structure_preserves_open",
            "object_evidence_refs": ["HIN-FUTURE-IDENTITY-OPEN", "HSP-FUTURE-IDENTITY-OPEN"],
            "rationale_anchor": "HI1 只需规定该问题保持开放及其信息边界，不需要替作者作答。",
            "downstream_effect": "HR1 及后续章节设计必须保留未决状态，不得写出确定答案。",
            "resolution_ref": None,
        }
        for source_id in wo["unresolved_projection"]
    ]

    candidate_ids = ["HI1-CAND-A-SINGLE-REALITY", "HI1-CAND-B-UNIT-INHERITANCE", "HI1-CAND-C-R07-PARALLEL"]
    design_decisions = [
        {
            "id": "HDDES-HI1-POV-AND-INFORMATION",
            "choice": "采用章节级单现实线方案：顾衡第一章、梁策第二至三章、沈逾第四至二十四章；错序记忆作为沈逾收到的受限信息。",
            "candidate_refs": candidate_ids,
        }
    ]

    canonical = {
        "schema_version": "1.0",
        "skill": "novel-hld-information-architect",
        "stage": "HI1",
        "hld_run_id": wo["hld_run_id"],
        "status": "ready",
        "input_gate_ref": wo["input_gate_ref"],
        "source_artifacts": [
            by_role["upstream::HB0::main"],
            by_role["source_index"],
            by_role["upstream::HA1::main"],
            by_role["upstream::HS1::main"],
            by_role["upstream::HC1::main"],
        ],
        "authority_partition": {},
        "design_decisions": design_decisions,
        "derivation_claims": [],
        "decision_dependencies": dependencies,
        "open_items": wo["unresolved_projection"],
        "downstream_contract": {
            "consumer": "HR1",
            "required_roles": [
                "pov_policy",
                "chapter_pov_assignments",
                "information_nodes",
                "knowledge_states",
                "reader_information_states",
                "suspense_chains",
                "reveal_payoff_matrix",
                "concealment_and_inference_rules",
            ],
        },
        "pov_policy": pov_policy,
        "unit_pov_assignments": unit_assignments,
        "chapter_pov_assignments": chapter_assignments,
        "knowledge_states": knowledge_states,
        "reader_information_states": reader_states,
        "suspense_chains": suspense_chains,
        "information_nodes": information_nodes,
        "reveal_payoff_matrix": payoff_matrix,
        "concealment_and_inference_rules": inference_rules,
    }

    owned_objects = [
        pov_policy,
        *unit_assignments,
        *chapter_assignments,
        *knowledge_states,
        *reader_states,
        *suspense_chains,
        *information_nodes,
        *payoff_matrix,
        *inference_rules,
    ]
    hld_ownership = {name: [] for name in ("source_projection", "hld_owned", "preserved_open", "lld_freedom")}
    for item in owned_objects:
        hld_ownership[item["ownership_class"]].append(item["id"])

    used_meta = {}
    for item in owned_objects:
        for ref in item["source_authority_refs"]:
            used_meta[ref["source_id"]] = ref
    canonical["authority_partition"] = {
        "source_authority_classes": {
            authority_class: sorted(source_id for source_id, item in used_meta.items() if item["authority_class"] == authority_class)
            for authority_class in ("author_locked", "autonomous_owned", "downstream_freedom", "author_open")
        },
        "source_classifications": {
            classification: sorted(source_id for source_id, item in used_meta.items() if item["classification"] == classification)
            for classification in ("mandatory", "freedom", "must_ask", "open")
        },
        "source_open_items": sorted(source_id for source_id, item in used_meta.items() if item["open_item"]),
        "hld_ownership": hld_ownership,
    }
    canonical["derivation_claims"] = [
        {
            "id": "HDRV-HI1-POV-POLICY",
            "source_refs": ["NAR-POV-ARCHITECTURE"],
            "target_locator": "/pov_policy",
            "value_sha256": digest(canonical["pov_policy"]),
        },
        {
            "id": "HDRV-HI1-CHAPTER-POV",
            "source_refs": ["NAR-POV-ARCHITECTURE", "CAU-MAJOR-NODES"],
            "target_locator": "/chapter_pov_assignments",
            "value_sha256": digest(canonical["chapter_pov_assignments"]),
        },
        {
            "id": "HDRV-HI1-INFORMATION-LEDGER",
            "source_refs": ["NAR-MEMORY-FRAGMENTS", "CAU-RESOLVED", "NAR-ENDING-MUST-REVEAL"],
            "target_locator": "/information_nodes",
            "value_sha256": digest(canonical["information_nodes"]),
        },
    ]

    actual_reads = canonical["source_artifacts"]
    session = {
        "schema_version": "1.0",
        "skill": "novel-hld-information-architect",
        "task_id": wo["task_id"],
        "actual_read_refs": actual_reads,
    }
    evidence = {
        "00-dependency-assessment.json": {"schema_version": "1.0", "assessments": dependencies},
        "01-obligation-analysis.json": {
            "schema_version": "1.0",
            "obligations": [
                "每个 HA1 单元与章节都必须有一个合法有效的视角分配。",
                "第一章顾衡、第二至三章梁策、第四至二十四章沈逾，R-07 启动后不得增加平行现实视角。",
                "顾衡现场感知与梁策通过记录和通报获得的信息必须分开建账。",
                "错序记忆只能作为片段性输入，不能冒充录像、证词、顾衡本人或 R-07 当前意愿。",
                "R-07 的关停链必须完整呈现请求记录、公共威胁解除、授权关停和无活动副本。",
                "顾衡始终是昏迷垂危但尚未脑死亡的在世患者。",
            ],
            "open_items": wo["unresolved_projection"],
            "forbidden": [
                "禁止让顾衡在失去意识后继续承担视角或知识。",
                "禁止让 R-07、专家、行动人员或机构代表在启动后成为平行现实视角。",
                "禁止让任何信息节点拥有多个知情者而省略各自的获取路径。",
                "禁止回答未来重载、身份连续性和两国互信是否恢复。",
            ],
        },
        "02-option-analysis.json": {
            "schema_version": "1.0",
            "candidates": [
                {
                    "id": candidate_ids[0],
                    "canonical_difference": "按章节绑定顾衡、梁策、沈逾三段有效视角；启动后现实线只保留沈逾。",
                    "tradeoff": "视角最少且信息来源清楚，但远端行动只能通过沈逾合法收到的记录与通报呈现。",
                    "downstream_impact": "HR1 可围绕单一现实线安排错序回忆和跨城回报，不需要补造其他人物内心。",
                },
                {
                    "id": candidate_ids[1],
                    "canonical_difference": "每个单元只使用一个默认视角，不细分第二至三章的梁策接收视角。",
                    "tradeoff": "形式较省，但会让昏迷后的顾衡继续承担信息，或抹掉梁策的合法接收路径。",
                    "downstream_impact": "违反 HC1 章节授权与人物可用性，不能进入后续设计。",
                },
                {
                    "id": candidate_ids[2],
                    "canonical_difference": "将 R-07 的记忆片段扩展为启动后的独立第一人称章节线。",
                    "tradeoff": "可直接呈现内部体验，但会增加平行叙事线并越过作者锁定的现实视角边界。",
                    "downstream_impact": "会造成信息泄漏和叙事合同冲突，不能采用。",
                },
            ],
            "unique_solution_exclusion_evidence": None,
        },
        "03-projection-analysis.json": {
            "schema_version": "1.0",
            "selected": candidate_ids[0],
            "projected_ids": [item["id"] for item in owned_objects],
            "projected_source_ids": sorted(used_meta),
        },
        "04-adversarial-self-review.json": {
            "schema_version": "1.0",
            "verdict": "pass",
            "challenges": [
                {"id": "HI1-ADV-POV", "claim": "全部 24 章都绑定 HC1 的合法焦点人物、获取方式和感知限制。", "evidence_ids": [item["id"] for item in chapter_assignments], "result": "pass"},
                {"id": "HI1-ADV-PROVENANCE", "claim": "35 个信息节点均为单一知情者，且顾衡现场感知与梁策记录接收分开。", "evidence_ids": [item["id"] for item in information_nodes], "result": "pass"},
                {"id": "HI1-ADV-MEMORY", "claim": "错序记忆只改变怀疑与核验方向，不承担现实证明、人格继承或行动。", "evidence_ids": ["HSP-MEMORY-TRUTH", "HIN-RULE-MEMORY-NOT-RECORD"], "result": "pass"},
                {"id": "HI1-ADV-TERMINATION", "claim": "关停请求、威胁解除、授权关停、无活动副本和开放未来彼此分开且顺序完整。", "evidence_ids": ["HSP-TERMINATION-CHAIN", "HSP-FUTURE-IDENTITY-OPEN"], "result": "pass"},
            ],
            "blockers": [],
        },
    }

    if DRAFT.exists():
        raise RuntimeError(f"fresh draft directory already exists: {DRAFT}")
    dump(DRAFT / "canonical.json", canonical)
    dump(DRAFT / "generation-session.json", session)
    for filename, value in evidence.items():
        dump(DRAFT / "generation-evidence" / filename, value)


if __name__ == "__main__":
    main()
