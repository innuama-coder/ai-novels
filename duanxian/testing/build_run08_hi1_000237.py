from __future__ import annotations

import json
import sys
from pathlib import Path


ENGINE = Path(__file__).resolve().parents[2] / "engine"
NOVEL = ENGINE.parent / "duanxian"
RUN = NOVEL / "development" / "hld-run-08"
WORK_ORDER = RUN / "work-order-000237-HI1.json"
DRAFT = RUN / "draft-000237-HI1-fresh"
HARNESS = ENGINE / "harnesses" / "novel-hld-autonomous"
sys.path.insert(0, str(HARNESS))

from runtime.canonical import canonical_sha256, write_json  # noqa: E402


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


work = read(WORK_ORDER)
gate = read(RUN / work["input_gate_ref"]["path"])
baseline = read(RUN / "HB0-r0000-HB0-package" / "hld-control-baseline.json")
ha1 = read(RUN / "HA1-r0103-HA1-package" / "package" / "narrative-architecture.json")
hs1 = read(RUN / "HS1-r0104-HS1-package" / "package" / "storyline-choreography.json")
hc1 = read(RUN / "HC1-r0120-HC1-attempt-000235-package" / "package" / "character-arc-placement.json")

# This is a fresh semantic read of the sealed lineage. No prior HI1 package is read.
source_documents = {item["role"]: read(RUN / item["path"]) for item in gate["source_lineage_refs"]}
assert len(source_documents) == len(gate["source_lineage_refs"])

controls = {item["source_id"]: item for item in baseline["control_registry"]}


def auth(source_id: str) -> dict:
    item = controls[source_id]
    return {
        "source_id": source_id,
        "classification": item["classification"],
        "open_item": item["open_item"],
        "authority_class": item["authority_class"],
        "value_sha256": item["source_value_sha256"],
    }


def trace(source_ids: list[str], ownership: str = "source_projection") -> dict:
    return {
        "source_refs": source_ids,
        "source_authority_refs": [auth(source_id) for source_id in source_ids],
        "ownership_class": ownership,
        "resolution_ref": None,
    }


units = ha1["narrative_units"]
shells = ha1["chapter_shells"]
agencies = hc1["chapter_agency_contracts"]
unit_ids = [item["id"] for item in units]
shell_ids = [item["id"] for item in shells]
agency_by_chapter = {item["chapter_id"]: item for item in agencies}

# Controlled check 1: current sealed upstream identity and the author-locked POV allocation.
assert len(units) == 8
assert len(shells) == len(agencies) == 24
assert shell_ids == [item["chapter_id"] for item in agencies]

focal_by_chapter = {
    **{shell_ids[0]: "CHR-GUHENG", shell_ids[1]: "CHR-LIANG-CE", shell_ids[2]: "CHR-LIANG-CE"},
    **{chapter_id: "CHR-SHEN-YU" for chapter_id in shell_ids[3:]},
}


def focalization(character_id: str, chapter_id: str) -> str:
    if character_id == "CHR-GUHENG":
        return "顾衡限制第三人称；只到他在栖港失去意识前，此后不再进入他的感知、记忆或选择。"
    if character_id == "CHR-LIANG-CE":
        return "梁策限制第三人称；只呈现接收记录、书面材料和他人通报造成的知识变化，不把未在场事件写成现场经历。"
    return "沈逾限制第三人称现实主线；只呈现她获准接触的材料、文字交流、正式通报和界面结果，不进入他人未表达的内心。"


chapter_assignments = []
for index, shell in enumerate(shells, 1):
    chapter_id = shell["id"]
    focal = focal_by_chapter[chapter_id]
    agency = agency_by_chapter[chapter_id]
    assert focal in agency["focal_character_ids"]
    paths = [item for item in agency["information_paths"] if item["character_id"] == focal]
    assert len(paths) == 1
    path = paths[0]
    chapter_assignments.append(
        {
            "id": f"HPV-CHAPTER-{index:02d}",
            **trace(["NAR-POV-ARCHITECTURE", focal]),
            "chapter_id": chapter_id,
            "parent_unit_id": shell["parent_unit_id"],
            "hc1_agency_contract_id": agency["id"],
            "pov_character_id": focal,
            "focalization_mode": focalization(focal, chapter_id),
            "knowledge_acquisition_modes": path["acquisition_modes"],
            "perception_limits": [path["limit"]],
        }
    )

unit_limits = {
    unit_ids[0]: "首章只到顾衡失去意识前；同单元后两章改由梁策凭记录和通报承接，不能恢复顾衡焦点。",
    unit_ids[1]: "只跟随沈逾看到的授权、医疗材料、设备输出和文字交流；顾衡仍昏迷垂危且尚未脑死亡。",
    unit_ids[2]: "沈逾承担现实主线；错序记忆只是受限插入材料，不把顾衡过去的感官变成R-07的现实感官。",
    unit_ids[3]: "沈逾承担可观察的现实交流；R-07的片段只说明记忆联想和正在形成的判断，不形成独立现实视角。",
    unit_ids[4]: "沈逾承担现实压力和交流变化；R-07只能从文字、继承片段与告知中重解信息。",
    unit_ids[5]: "沈逾凭四城核验摘要、通报和系统状态了解行动准备；记忆不能代替证据、授权或现场执行。",
    unit_ids[6]: "沈逾承担可观察的询问、答复和留痕；R-07的内部片段不泄露未表达的最终结论。",
    unit_ids[7]: "沈逾承担现实阻断结果、获授权关停和余波；R-07没有现实感官或控制权，关停后不再有活动焦点。",
}

unit_assignments = []
for index, unit in enumerate(units, 1):
    focal = "CHR-LIANG-CE" if index == 1 else "CHR-SHEN-YU"
    unit_assignments.append(
        {
            "id": f"HPV-UNIT-{index:02d}",
            **trace(["NAR-POV-ARCHITECTURE", focal]),
            "unit_id": unit["id"],
            "pov_character_id": focal,
            "focalization_mode": "梁策文档限知承接" if index == 1 else "沈逾限制第三人称现实主线",
            "perception_limits": [unit_limits[unit["id"]]],
        }
    )


def info(
    identifier: str,
    source_ids: list[str],
    knower_id: str,
    reader_state: str,
    acquisition_mode: str,
    earliest: str,
    forbidden: list[str],
    ownership: str = "source_projection",
) -> dict:
    return {
        "id": identifier,
        **trace(source_ids, ownership),
        "source_information_id": source_ids[0],
        "knower_ids": [knower_id],
        "reader_state": reader_state,
        "acquisition_mode": acquisition_mode,
        "earliest_legal_unit_id": earliest,
        "forbidden_leak_unit_ids": forbidden,
    }


U = unit_ids
information_nodes = [
    info("HIN-THREAT-SUSPECTED-GUHENG", ["CAU-GLOBAL-SPINE"], "CHR-GUHENG", "inferable", "inferred", U[0], []),
    info("HIN-MINIMAL-CLUE-ONSITE-GUHENG", ["CAU-EVIDENCE-ACTION-CLOSURE"], "CHR-GUHENG", "hidden", "perceived", U[0], []),
    info("HIN-MINIMAL-CLUE-RECEIPT-LIANG", ["CAU-EVIDENCE-ACTION-CLOSURE"], "CHR-LIANG-CE", "known", "documented", U[0], []),
    info("HIN-GUHENG-ALIVE-LIANG", ["NAR-POV-ARCHITECTURE"], "CHR-LIANG-CE", "known", "told", U[0], []),
    info("HIN-GUHENG-ALIVE-SHEN", ["NAR-POV-ARCHITECTURE"], "CHR-SHEN-YU", "known", "documented", U[1], [U[0]]),
    info("HIN-R07-DISTINCT-R07", ["CHR-R07"], "CHR-R07", "hidden", "told", U[1], [U[0]]),
    info("HIN-R07-DISTINCT-SHEN", ["CHR-R07"], "CHR-SHEN-YU", "known", "system_output", U[1], [U[0]]),
    info("HIN-MEMORY-UNRELIABLE-R07", ["NAR-MEMORY-FRAGMENTS"], "CHR-R07", "inferable", "inferred", U[2], U[:2]),
    info("HIN-MEMORY-UNRELIABLE-SHEN", ["NAR-MEMORY-FRAGMENTS"], "CHR-SHEN-YU", "known", "documented", U[2], U[:2]),
    info("HIN-MEMORY-CONTINUITY-MISBELIEF-R07", ["NAR-READER-KNOWLEDGE"], "CHR-R07", "misbelieved", "inferred", U[2], U[:2]),
    info("HIN-MEMORY-NOT-REAL-SENSE-R07", ["NAR-MEMORY-FRAGMENTS", "NAR-R07-INFORMATION-BOUNDARY"], "CHR-R07", "known", "inferred", U[2], U[:2]),
    info("HIN-MEMORY-NOT-REAL-SENSE-SHEN", ["NAR-MEMORY-FRAGMENTS", "NAR-R07-INFORMATION-BOUNDARY"], "CHR-SHEN-YU", "known", "documented", U[2], U[:2]),
    info("HIN-R07-NEW-AFFECTION-R07", ["CHR-GU-HENG-MEMORY", "NAR-READER-KNOWLEDGE"], "CHR-R07", "inferable", "inferred", U[3], U[:3]),
    info("HIN-R07-NEW-AFFECTION-SHEN", ["CHR-GU-HENG-MEMORY", "NAR-READER-KNOWLEDGE"], "CHR-SHEN-YU", "inferable", "inferred", U[3], U[:3]),
    info("HIN-R07-NO-REALITY-ACCESS-R07", ["CHR-R07", "NAR-R07-INFORMATION-BOUNDARY"], "CHR-R07", "known", "system_output", U[3], U[:3]),
    info("HIN-R07-NO-REALITY-ACCESS-SHEN", ["CHR-R07", "NAR-R07-INFORMATION-BOUNDARY"], "CHR-SHEN-YU", "known", "documented", U[3], U[:3]),
    info("HIN-MISREAD-CORRECTED-R07", ["NAR-FAIRNESS"], "CHR-R07", "hidden", "told", U[4], U[:4]),
    info("HIN-MISREAD-CORRECTED-SHEN", ["NAR-FAIRNESS"], "CHR-SHEN-YU", "known", "documented", U[4], U[:4]),
    info("HIN-ATTACK-DIRECTION-R07", ["CAU-EVIDENCE-ACTION-CLOSURE"], "CHR-R07", "hidden", "remembered", U[4], U[:4]),
    info("HIN-ATTACK-DIRECTION-SHEN", ["CAU-EVIDENCE-ACTION-CLOSURE"], "CHR-SHEN-YU", "known", "told", U[4], U[:4]),
    info("HIN-INDEPENDENT-EVIDENCE-CLOSURE-SHEN", ["CAU-EVIDENCE-ACTION-CLOSURE", "WLD-THREAT-EVIDENCE-ACTION"], "CHR-SHEN-YU", "known", "documented", U[5], U[:5]),
    info("HIN-REALITY-ACTION-READY-SHEN", ["WLD-THREAT-EVIDENCE-ACTION"], "CHR-SHEN-YU", "known", "system_output", U[5], U[:5]),
    info("HIN-TERMINATION-CHOICE-FORMING-R07", ["NAR-R07-INFORMATION-BOUNDARY"], "CHR-R07", "inferable", "inferred", U[6], U[:6]),
    info("HIN-R07-TERMINATION-REQUEST-SHEN", ["CAU-GLOBAL-SPINE", "NAR-R07-INFORMATION-BOUNDARY"], "CHR-SHEN-YU", "known", "told", U[6], U[:6]),
    info("HIN-R07-TERMINATION-REQUEST-RECORDED-SHEN", ["CAU-GLOBAL-SPINE", "NAR-R07-INFORMATION-BOUNDARY"], "CHR-SHEN-YU", "known", "documented", U[6], U[:6]),
    info("HIN-ATTACK-STOPPED-SHEN", ["NAR-ENDING-MUST-REVEAL"], "CHR-SHEN-YU", "known", "system_output", U[7], U[:7]),
    info("HIN-SHUTDOWN-AUTHORIZED-SHEN", ["NAR-ENDING-MUST-REVEAL"], "CHR-SHEN-YU", "known", "documented", U[7], U[:7]),
    info("HIN-R07-CURRENT-CONSCIOUSNESS-ENDED-SHEN", ["NAR-ENDING-MUST-REVEAL"], "CHR-SHEN-YU", "known", "system_output", U[7], U[:7]),
    info("HIN-NO-ACTIVE-R07-COPY-SHEN", ["NAR-ENDING-MUST-REVEAL"], "CHR-SHEN-YU", "known", "documented", U[7], U[:7]),
    info("HIN-GUHENG-STILL-CRITICAL-SHEN", ["CAU-GLOBAL-SPINE", "NAR-POV-ARCHITECTURE"], "CHR-SHEN-YU", "known", "documented", U[7], U[:7]),
    info("HIN-OPEN-CAUSAL-TRUST-SHEN", ["CAU-PRESERVED-OPEN"], "CHR-SHEN-YU", "open", "authorized_open", U[7], U[:7], "preserved_open"),
    info("HIN-OPEN-IDENTITY-FEELING-SHEN", ["INT-READER-QUESTIONS"], "CHR-SHEN-YU", "open", "authorized_open", U[7], U[:7], "preserved_open"),
    info("HIN-OPEN-RELOAD-CONTINUITY-CUSTODIAN", ["NAR-ENDING-PRESERVED-OPEN"], "CHR-FUTURE-CUSTODIAN", "open", "authorized_open", U[7], U[:7], "preserved_open"),
]


def knowledge(identifier: str, character: str, unit: str, nodes: list[str], misbeliefs: list[str] | None = None) -> dict:
    return {
        "id": identifier,
        **trace(["NAR-READER-KNOWLEDGE"]),
        "character_id": character,
        "unit_id": unit,
        "information_node_ids": nodes,
        "misbelief_node_ids": misbeliefs or [],
    }


knowledge_states = [
    knowledge("HKS-CHAR-01-GUHENG", "CHR-GUHENG", U[0], ["HIN-THREAT-SUSPECTED-GUHENG", "HIN-MINIMAL-CLUE-ONSITE-GUHENG"]),
    knowledge("HKS-CHAR-01-LIANG", "CHR-LIANG-CE", U[0], ["HIN-MINIMAL-CLUE-RECEIPT-LIANG", "HIN-GUHENG-ALIVE-LIANG"]),
    knowledge("HKS-CHAR-02-SHEN", "CHR-SHEN-YU", U[1], ["HIN-GUHENG-ALIVE-SHEN", "HIN-R07-DISTINCT-SHEN"]),
    knowledge("HKS-CHAR-03-R07", "CHR-R07", U[2], ["HIN-R07-DISTINCT-R07", "HIN-MEMORY-UNRELIABLE-R07", "HIN-MEMORY-NOT-REAL-SENSE-R07"], ["HIN-MEMORY-CONTINUITY-MISBELIEF-R07"]),
    knowledge("HKS-CHAR-04-R07", "CHR-R07", U[3], ["HIN-R07-NEW-AFFECTION-R07", "HIN-R07-NO-REALITY-ACCESS-R07"], ["HIN-MEMORY-CONTINUITY-MISBELIEF-R07"]),
    knowledge("HKS-CHAR-05-SHEN", "CHR-SHEN-YU", U[4], ["HIN-MISREAD-CORRECTED-SHEN", "HIN-ATTACK-DIRECTION-SHEN"]),
    knowledge("HKS-CHAR-06-SHEN", "CHR-SHEN-YU", U[5], ["HIN-INDEPENDENT-EVIDENCE-CLOSURE-SHEN", "HIN-REALITY-ACTION-READY-SHEN"]),
    knowledge("HKS-CHAR-07-R07", "CHR-R07", U[6], ["HIN-TERMINATION-CHOICE-FORMING-R07", "HIN-R07-NO-REALITY-ACCESS-R07"]),
    knowledge("HKS-CHAR-07-SHEN", "CHR-SHEN-YU", U[6], ["HIN-REALITY-ACTION-READY-SHEN", "HIN-R07-TERMINATION-REQUEST-SHEN", "HIN-R07-TERMINATION-REQUEST-RECORDED-SHEN"]),
    knowledge("HKS-CHAR-08-SHEN", "CHR-SHEN-YU", U[7], ["HIN-ATTACK-STOPPED-SHEN", "HIN-SHUTDOWN-AUTHORIZED-SHEN", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED-SHEN", "HIN-NO-ACTIVE-R07-COPY-SHEN", "HIN-GUHENG-STILL-CRITICAL-SHEN", "HIN-OPEN-CAUSAL-TRUST-SHEN", "HIN-OPEN-IDENTITY-FEELING-SHEN"]),
]


def reader(identifier: str, unit: str, nodes: list[str], permissions: list[str]) -> dict:
    return {
        "id": identifier,
        **trace(["NAR-READER-KNOWLEDGE"]),
        "unit_id": unit,
        "information_node_ids": nodes,
        "inference_permissions": permissions,
    }


reader_states = [
    reader("HKS-READER-01", U[0], ["HIN-THREAT-SUSPECTED-GUHENG", "HIN-MINIMAL-CLUE-RECEIPT-LIANG", "HIN-GUHENG-ALIVE-LIANG"], ["可确认梁策收到最小线索并从通报得知顾衡仍活着；不可把梁策写成栖港现场见证者。"]),
    reader("HKS-READER-02", U[1], ["HIN-GUHENG-ALIVE-SHEN", "HIN-R07-DISTINCT-SHEN"], ["可知顾衡昏迷垂危但尚未脑死亡，且R-07是另一主体；不可把残缺神经材料当成证词。"]),
    reader("HKS-READER-03", U[2], ["HIN-MEMORY-UNRELIABLE-SHEN", "HIN-MEMORY-CONTINUITY-MISBELIEF-R07", "HIN-MEMORY-NOT-REAL-SENSE-SHEN"], ["可怀疑片段时序与因果；不可把顾衡过去的感官当成R-07现实感官。"]),
    reader("HKS-READER-04", U[3], ["HIN-R07-NEW-AFFECTION-SHEN", "HIN-R07-NO-REALITY-ACCESS-SHEN"], ["可推断新情感来自当下交流；不可推断为顾衡旧爱延续，也不可赋予R-07现实设备访问。"]),
    reader("HKS-READER-05", U[4], ["HIN-MISREAD-CORRECTED-SHEN", "HIN-ATTACK-DIRECTION-SHEN"], ["可知第一层方向仍需现实核验；不可把记忆片段直接当作行动权限。"]),
    reader("HKS-READER-06", U[5], ["HIN-INDEPENDENT-EVIDENCE-CLOSURE-SHEN", "HIN-REALITY-ACTION-READY-SHEN"], ["可知现实团队已经具备独立阻断条件；不可推断R-07控制了硬件。"]),
    reader("HKS-READER-07", U[6], ["HIN-R07-TERMINATION-REQUEST-SHEN", "HIN-R07-TERMINATION-REQUEST-RECORDED-SHEN", "HIN-REALITY-ACTION-READY-SHEN"], ["必须明确知道R-07提出结束当前存在的请求且请求已留痕；不可进入它未表达的内在推演。"]),
    reader("HKS-READER-08", U[7], ["HIN-ATTACK-STOPPED-SHEN", "HIN-SHUTDOWN-AUTHORIZED-SHEN", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED-SHEN", "HIN-NO-ACTIVE-R07-COPY-SHEN", "HIN-GUHENG-STILL-CRITICAL-SHEN", "HIN-OPEN-CAUSAL-TRUST-SHEN", "HIN-OPEN-IDENTITY-FEELING-SHEN", "HIN-OPEN-RELOAD-CONTINUITY-CUSTODIAN"], ["必须确认现实威胁已解除、关停经过授权、当前意识结束且无活动副本；未来重载、身份连续性、感情分类和两国互信仍开放。"]),
]


def suspense(identifier: str, source_ids: list[str], setup: list[str], probe: list[str], reveal: list[str], payoff: list[str], terminal: str | None, ownership: str = "source_projection") -> dict:
    return {
        "id": identifier,
        **trace(source_ids, ownership),
        "setup_node_ids": setup,
        "probe_node_ids": probe,
        "reveal_node_ids": reveal,
        "payoff_node_ids": payoff,
        "authorized_open_terminal": terminal,
    }


suspense_chains = [
    suspense("HSP-ATTACK-EVIDENCE", ["CAU-EVIDENCE-ACTION-CLOSURE"], ["HIN-MINIMAL-CLUE-RECEIPT-LIANG"], ["HIN-ATTACK-DIRECTION-SHEN"], ["HIN-INDEPENDENT-EVIDENCE-CLOSURE-SHEN", "HIN-REALITY-ACTION-READY-SHEN"], ["HIN-ATTACK-STOPPED-SHEN"], None),
    suspense("HSP-R07-DISTINCT-LIFE", ["NAR-READER-KNOWLEDGE"], ["HIN-R07-DISTINCT-SHEN"], ["HIN-MEMORY-UNRELIABLE-SHEN", "HIN-R07-NEW-AFFECTION-SHEN"], ["HIN-MISREAD-CORRECTED-SHEN"], ["HIN-R07-CURRENT-CONSCIOUSNESS-ENDED-SHEN"], None),
    suspense("HSP-R07-TERMINATION", ["NAR-R07-INFORMATION-BOUNDARY", "NAR-ENDING-MUST-REVEAL"], ["HIN-R07-NO-REALITY-ACCESS-SHEN"], ["HIN-TERMINATION-CHOICE-FORMING-R07"], ["HIN-R07-TERMINATION-REQUEST-SHEN", "HIN-R07-TERMINATION-REQUEST-RECORDED-SHEN"], ["HIN-SHUTDOWN-AUTHORIZED-SHEN", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED-SHEN"], None),
    suspense("HSP-OPEN-CAUSAL-TRUST", ["CAU-PRESERVED-OPEN"], ["HIN-INDEPENDENT-EVIDENCE-CLOSURE-SHEN"], ["HIN-ATTACK-STOPPED-SHEN"], [], [], "HDD-HI1-CAU-PRESERVED-OPEN", "preserved_open"),
    suspense("HSP-OPEN-READER-QUESTIONS", ["INT-READER-QUESTIONS"], ["HIN-R07-DISTINCT-SHEN"], ["HIN-R07-NEW-AFFECTION-SHEN", "HIN-R07-TERMINATION-REQUEST-SHEN"], [], [], "HDD-HI1-INT-READER-QUESTIONS", "preserved_open"),
    suspense("HSP-OPEN-RELOAD", ["NAR-ENDING-PRESERVED-OPEN"], ["HIN-NO-ACTIVE-R07-COPY-SHEN"], ["HIN-OPEN-RELOAD-CONTINUITY-CUSTODIAN"], [], [], "HDD-HI1-NAR-ENDING-PRESERVED-OPEN", "preserved_open"),
]


def payoff(identifier: str, source_ids: list[str], nodes: list[str], setup_units: list[str], terminal_unit: str, terminal_kind: str, ownership: str = "source_projection") -> dict:
    return {
        "id": identifier,
        **trace(source_ids, ownership),
        "information_node_ids": nodes,
        "setup_unit_ids": setup_units,
        "terminal_unit_id": terminal_unit,
        "terminal_kind": terminal_kind,
    }


reveal_payoff = [
    payoff("HIN-MATRIX-ATTACK", ["CAU-EVIDENCE-ACTION-CLOSURE"], ["HIN-MINIMAL-CLUE-RECEIPT-LIANG", "HIN-ATTACK-DIRECTION-SHEN", "HIN-INDEPENDENT-EVIDENCE-CLOSURE-SHEN", "HIN-ATTACK-STOPPED-SHEN"], [U[0], U[4], U[5]], U[7], "payoff"),
    payoff("HIN-MATRIX-R07-IDENTITY", ["NAR-READER-KNOWLEDGE"], ["HIN-R07-DISTINCT-SHEN", "HIN-MEMORY-UNRELIABLE-SHEN", "HIN-R07-NEW-AFFECTION-SHEN", "HIN-MISREAD-CORRECTED-SHEN"], [U[1], U[2], U[3]], U[4], "reveal"),
    payoff("HIN-MATRIX-TERMINATION", ["NAR-R07-INFORMATION-BOUNDARY", "NAR-ENDING-MUST-REVEAL"], ["HIN-R07-NO-REALITY-ACCESS-SHEN", "HIN-R07-TERMINATION-REQUEST-SHEN", "HIN-R07-TERMINATION-REQUEST-RECORDED-SHEN", "HIN-SHUTDOWN-AUTHORIZED-SHEN", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED-SHEN"], [U[3], U[6]], U[7], "payoff"),
    payoff("HIN-MATRIX-OPEN-CAUSAL", ["CAU-PRESERVED-OPEN"], ["HIN-OPEN-CAUSAL-TRUST-SHEN"], [U[7]], U[7], "authorized_open", "preserved_open"),
    payoff("HIN-MATRIX-OPEN-READER", ["INT-READER-QUESTIONS"], ["HIN-OPEN-IDENTITY-FEELING-SHEN"], [U[7]], U[7], "authorized_open", "preserved_open"),
    payoff("HIN-MATRIX-OPEN-RELOAD", ["NAR-ENDING-PRESERVED-OPEN"], ["HIN-OPEN-RELOAD-CONTINUITY-CUSTODIAN"], [U[7]], U[7], "authorized_open", "preserved_open"),
]


def rule(identifier: str, source_ids: list[str], nodes: list[str], basis: str, legal: list[str], forbidden: list[str], ownership: str = "source_projection") -> dict:
    return {
        "id": identifier,
        **trace(source_ids, ownership),
        "information_node_ids": nodes,
        "concealment_basis": basis,
        "legal_inferences": legal,
        "forbidden_inferences": forbidden,
    }


inference_rules = [
    rule("HIN-RULE-GUHENG-POV-CUTOFF", ["NAR-POV-ARCHITECTURE"], ["HIN-MINIMAL-CLUE-ONSITE-GUHENG", "HIN-GUHENG-ALIVE-LIANG", "HIN-GUHENG-ALIVE-SHEN"], "顾衡只在第一章失去意识前承担限知；此后他昏迷垂危且尚未脑死亡。", ["读者可从梁策的通报和沈逾的医疗材料知道顾衡仍活着。"], ["不得进入顾衡第二章及之后的感知、记忆、选择或内在状态。"]),
    rule("HIN-RULE-LIANG-RECEIPT-ONLY", ["NAR-POV-ARCHITECTURE", "CAU-EVIDENCE-ACTION-CLOSURE"], ["HIN-MINIMAL-CLUE-ONSITE-GUHENG", "HIN-MINIMAL-CLUE-RECEIPT-LIANG", "HIN-GUHENG-ALIVE-LIANG"], "顾衡在场时感知并送出线索；梁策只在第二章通过接收记录取得另一个知识节点。", ["梁策可依据documented与told形成判断，读者从接收节点进入后续证据链。"], ["不得把顾衡的现场感知直接授予梁策，也不得把梁策写成现场目击者。"]),
    rule("HIN-RULE-R07-NO-REALITY-SENSE", ["NAR-MEMORY-FRAGMENTS", "NAR-R07-INFORMATION-BOUNDARY"], ["HIN-MEMORY-NOT-REAL-SENSE-R07", "HIN-MEMORY-NOT-REAL-SENSE-SHEN", "HIN-R07-NO-REALITY-ACCESS-R07", "HIN-R07-NO-REALITY-ACCESS-SHEN"], "R-07只有文字输入、继承片段和由系统明确提供的状态；顾衡过去的感官仍属于过去。", ["R-07可对文字、片段和告知作有限联想或推断。"], ["不得赋予R-07现实视觉、听觉、身体感、网络访问、设备控制或行动权限。"]),
    rule("HIN-RULE-TERMINATION-REQUEST-VISIBLE", ["NAR-R07-INFORMATION-BOUNDARY", "NAR-ENDING-MUST-REVEAL"], ["HIN-TERMINATION-CHOICE-FORMING-R07", "HIN-R07-TERMINATION-REQUEST-SHEN", "HIN-R07-TERMINATION-REQUEST-RECORDED-SHEN", "HIN-SHUTDOWN-AUTHORIZED-SHEN"], "R-07形成决定的内部过程保持受限，但第七单元第三章必须明确呈现请求及其记录，第八单元再呈现授权和执行。", ["读者必须知道请求已提出并留痕，也可区分个人请求与现实行动条件。"], ["不得隐去请求事实，也不得展示未表达的完整内在推演或把请求当成未经授权即可执行的命令。"]),
    rule("HIN-RULE-EVIDENCE-LADDER", ["CAU-EVIDENCE-ACTION-CLOSURE", "WLD-THREAT-EVIDENCE-ACTION"], ["HIN-MINIMAL-CLUE-RECEIPT-LIANG", "HIN-ATTACK-DIRECTION-SHEN", "HIN-INDEPENDENT-EVIDENCE-CLOSURE-SHEN", "HIN-REALITY-ACTION-READY-SHEN", "HIN-ATTACK-STOPPED-SHEN"], "梁策的合法接收记录启动证据链；记忆只给方向，证词、硬件、授权和属地行动分别完成现实闭环。", ["读者可在多源材料闭合后判断行动已准备完成。"], ["不得让顾衡现场节点绕过接收链，也不得让R-07、单一记忆或单一系统输出直接阻止袭击。"]),
    rule("HIN-RULE-OPEN-CAUSAL", ["CAU-PRESERVED-OPEN"], ["HIN-OPEN-CAUSAL-TRUST-SHEN"], "完整幕后利益链、原因层公开程度和两国互信被作者明确保留。", ["读者可判断一次合作完成了当前阻断。"], ["不得推断两国恢复互信、完整利益链已查清或原因层已公开。"], "preserved_open"),
    rule("HIN-RULE-OPEN-READER", ["INT-READER-QUESTIONS"], ["HIN-OPEN-IDENTITY-FEELING-SHEN"], "沈逾的感情分类与R-07和顾衡的关系保持为持续问题。", ["读者可确认R-07的新感情不由顾衡旧爱直接决定。"], ["不得替沈逾裁定她最终回应哪一种关系。"], "preserved_open"),
    rule("HIN-RULE-OPEN-RELOAD", ["NAR-ENDING-PRESERVED-OPEN"], ["HIN-NO-ACTIVE-R07-COPY-SHEN", "HIN-OPEN-RELOAD-CONTINUITY-CUSTODIAN"], "当前R-07已关停且无活动副本，但未来技术与身份连续性未裁决。", ["读者可确认当前这一个R-07已经不可逆终止。"], ["不得把未来重载写成已保证可行，也不得预先认定重载者就是或不是R-07。"], "preserved_open"),
]

dependencies = [
    {
        "id": "HDD-HI1-CAU-PRESERVED-OPEN", "source_id": "CAU-PRESERVED-OPEN", "owner_stage": "HI1",
        "affected_obligation_ids": ["HSP-OPEN-CAUSAL-TRUST", "HIN-OPEN-CAUSAL-TRUST-SHEN"],
        "disposition": "conditional_structure_preserves_open",
        "object_evidence_refs": ["HIN-RULE-OPEN-CAUSAL", "HIN-MATRIX-OPEN-CAUSAL"],
        "rationale_anchor": "本阶段只需保留幕后链、原因公开程度和两国互信的未知状态，无需替作者作答。",
        "downstream_effect": "后续章节设计必须把当前危机闭环与长期答案分开。", "resolution_ref": None,
    },
    {
        "id": "HDD-HI1-INT-READER-QUESTIONS", "source_id": "INT-READER-QUESTIONS", "owner_stage": "HI1",
        "affected_obligation_ids": ["HSP-OPEN-READER-QUESTIONS", "HIN-OPEN-IDENTITY-FEELING-SHEN"],
        "disposition": "conditional_structure_preserves_open",
        "object_evidence_refs": ["HIN-RULE-OPEN-READER", "HIN-MATRIX-OPEN-READER"],
        "rationale_anchor": "读者需要持续面对身份与感情问题，本阶段可以用开放终点保留它们。",
        "downstream_effect": "后续必须给出形成问题的证据，但不能替作者最终分类。", "resolution_ref": None,
    },
    {
        "id": "HDD-HI1-NAR-ENDING-PRESERVED-OPEN", "source_id": "NAR-ENDING-PRESERVED-OPEN", "owner_stage": "HI1",
        "affected_obligation_ids": ["HSP-OPEN-RELOAD", "HIN-OPEN-RELOAD-CONTINUITY-CUSTODIAN"],
        "disposition": "conditional_structure_preserves_open",
        "object_evidence_refs": ["HIN-RULE-OPEN-RELOAD", "HIN-MATRIX-OPEN-RELOAD"],
        "rationale_anchor": "结尾确认当前意识终止和无活动副本，同时保留未来重载与身份连续性。",
        "downstream_effect": "后续必须把事实性终止与未来可能严格分开。", "resolution_ref": None,
    },
]

policy = {
    "id": "HPV-POLICY-SHEN-REALITY-MAINLINE",
    **trace(["NAR-POV-ARCHITECTURE"]),
    "allowed_modes": ["顾衡第一章失去意识前的限制第三人称", "梁策第二至第三章的记录与通报限知", "沈逾第四至第二十四章的限制第三人称现实主线", "不构成独立现实视角的R-07错序记忆片段"],
    "switch_rule": "每章只有一个有效焦点，只能在章边界切换；第四章起现实主线始终由沈逾承担，R-07记忆片段不能扩展成现实感知或独立行动线。",
    "legality_rule": "每章焦点必须由对应HC1 agency contract授权并原样绑定其获得方式与限制；第一章顾衡，第二至三章梁策且仅documented+told，第四至二十四章沈逾。",
}

actual_reads = list(gate["source_lineage_refs"])
allow_by_role = {item["role"]: item for item in work["file_allowlist"]}
actual_reads.extend(allow_by_role[f"upstream::{stage}::main"] for stage in ("HB0", "HA1", "HS1", "HC1"))

model = {
    "schema_version": "1.0", "skill": "novel-hld-information-architect", "stage": "HI1",
    "hld_run_id": work["hld_run_id"], "status": "ready", "input_gate_ref": work["input_gate_ref"],
    "source_artifacts": actual_reads, "authority_partition": baseline["authority_partition"],
    "design_decisions": [
        {"id": "HDDES-HI1-POV-ALLOCATION", "choice": "第一章顾衡、第二至三章梁策、第四至二十四章沈逾；R-07只保留受限错序记忆片段", "candidate_refs": ["HI1-OPT-SHEN-CONTINUOUS", "HI1-OPT-BROADER-MULTI"]},
        {"id": "HDDES-HI1-PROVENANCE", "choice": "每个人物按实际获得方式使用独立信息节点，顾衡现场线索与梁策接收记录严格分开", "candidate_refs": ["HI1-OPT-SINGLE-KNOWER", "HI1-OPT-SHARED-NODES"]},
        {"id": "HDDES-HI1-SUSPENSE-CLOSURE", "choice": "以合法接收、现实证据闭环、终止请求留痕、授权关停和开放余波构成完整链条", "candidate_refs": ["HI1-OPT-SHEN-CONTINUOUS", "HI1-OPT-BROADER-MULTI"]},
    ],
    "derivation_claims": [], "decision_dependencies": dependencies,
    "open_items": work["unresolved_projection"],
    "downstream_contract": {"consumer": "HR1", "required_roles": ["legal_pov_assignments", "character_reader_knowledge_separation", "fair_suspense_and_payoff_control"]},
    "pov_policy": policy, "unit_pov_assignments": unit_assignments, "chapter_pov_assignments": chapter_assignments,
    "knowledge_states": knowledge_states, "reader_information_states": reader_states,
    "suspense_chains": suspense_chains, "information_nodes": information_nodes,
    "reveal_payoff_matrix": reveal_payoff, "concealment_and_inference_rules": inference_rules,
}

ownership = {name: [] for name in ("source_projection", "hld_owned", "preserved_open", "lld_freedom")}
for array_name in ("unit_pov_assignments", "chapter_pov_assignments", "knowledge_states", "reader_information_states", "suspense_chains", "information_nodes", "reveal_payoff_matrix", "concealment_and_inference_rules"):
    for item in model[array_name]:
        ownership[item["ownership_class"]].append(item["id"])
ownership[policy["ownership_class"]].append(policy["id"])
model["authority_partition"] = json.loads(json.dumps(model["authority_partition"], ensure_ascii=False))
model["authority_partition"]["hld_ownership"] = ownership

for identifier, source_refs, pointer in (
    ("HDRV-HI1-POV", ["NAR-POV-ARCHITECTURE"], "/chapter_pov_assignments"),
    ("HDRV-HI1-INFORMATION", ["NAR-READER-KNOWLEDGE", "NAR-R07-INFORMATION-BOUNDARY"], "/information_nodes"),
    ("HDRV-HI1-SUSPENSE", ["CAU-EVIDENCE-ACTION-CLOSURE", "NAR-FAIRNESS"], "/suspense_chains"),
    ("HDRV-HI1-DEPENDENCIES", work["unresolved_projection"], "/decision_dependencies"),
):
    model["derivation_claims"].append({"id": identifier, "source_refs": source_refs, "target_locator": pointer, "value_sha256": canonical_sha256(model[pointer[1:]])})

# Controlled check 2: audit every information grant against a current HC1 path.
path_modes: dict[tuple[str, str], set[str]] = {}
for agency in agencies:
    unit_id = next(shell["parent_unit_id"] for shell in shells if shell["id"] == agency["chapter_id"])
    for path in agency["information_paths"]:
        path_modes.setdefault((unit_id, path["character_id"]), set()).update(path["acquisition_modes"])

mode_audit = []
for node in information_nodes:
    knower = node["knower_ids"][0]
    mode = node["acquisition_mode"]
    if mode != "authorized_open":
        legal = set().union(*(modes for (unit_id, character), modes in path_modes.items() if character == knower and U.index(unit_id) <= U.index(node["earliest_legal_unit_id"])), set())
        assert mode in legal, (node["id"], knower, mode, sorted(legal))
    mode_audit.append({"node_id": node["id"], "knower_id": knower, "acquisition_mode": mode, "result": "pass"})

assert all(len(node["knower_ids"]) == 1 for node in information_nodes)
assert knowledge_states[1]["information_node_ids"][0] == "HIN-MINIMAL-CLUE-RECEIPT-LIANG"
for container in reader_states + suspense_chains + reveal_payoff:
    values = set()
    for value in container.values():
        if isinstance(value, list):
            values.update(item for item in value if isinstance(item, str))
    assert "HIN-MINIMAL-CLUE-ONSITE-GUHENG" not in values

session = {"schema_version": "1.0", "skill": "novel-hld-information-architect", "task_id": work["task_id"], "actual_read_refs": actual_reads}
evidence = {
    "00-dependency-assessment.json": {"schema_version": "1.0", "assessments": dependencies},
    "01-obligation-analysis.json": {
        "schema_version": "1.0",
        "obligations": [
            "八个单元和二十四个章壳按上游顺序完整覆盖。",
            "第一章只由顾衡限知，第二至三章梁策只通过documented与told获知，第四至二十四章始终由沈逾承担现实焦点。",
            "顾衡现场感知的最小线索和梁策第二章收到的记录是两个不同节点；后续读者、悬念和揭示链只使用梁策合法接收节点。",
            "R-07的错序记忆只作为受限片段存在，不能获得现实感官、网络、设备控制或行动权限。",
            "第七单元第三章必须明确R-07提出结束当前存在的请求且请求已记录；第八单元依次确认现实威胁解除、授权关停、无活动副本与开放未来。",
            "顾衡到结尾仍昏迷垂危且尚未脑死亡，不能被写成已经死亡或在昏迷后继续选择。",
        ],
        "open_items": work["unresolved_projection"],
        "forbidden": ["梁策取得顾衡现场感知", "R-07取得现实感官或控制权", "第四章以后更换现实主线焦点", "隐去终止请求或请求留痕", "把无活动副本写成未来绝无重载可能", "对白、动作、感官细节和段落级写法"],
    },
    "02-option-analysis.json": {
        "schema_version": "1.0",
        "candidates": [
            {"id": "HI1-OPT-SHEN-CONTINUOUS", "canonical_difference": "第四章起由沈逾持续承担现实焦点，R-07只以错序片段和已输出信息进入。", "tradeoff": "主线连续且知识边界清楚，但后续章节必须区分沈逾所见界面与R-07未表达的内在过程。", "downstream_impact": "HR1与HD1可直接按单一现实焦点安排节奏和章节信息。"},
            {"id": "HI1-OPT-BROADER-MULTI", "canonical_difference": "在多章改用行动人员或R-07承担焦点。", "tradeoff": "现实节点更直接，却破坏作者锁定的沈逾主线并增加信息泄漏。", "downstream_impact": "后续需要额外视角账本且会削弱身份和终止悬念。"},
            {"id": "HI1-OPT-SINGLE-KNOWER", "canonical_difference": "每个节点只有一个知情者和一种获得方式，人物之间的转移另建节点。", "tradeoff": "节点数量增加，但每次获得都可独立审计。", "downstream_impact": "章节设计可明确知道谁在何时通过什么方式取得信息。"},
            {"id": "HI1-OPT-SHARED-NODES", "canonical_difference": "一个节点同时列出多名知情者并共用一种获得方式。", "tradeoff": "表面简短，却会把顾衡的perceived非法授予梁策等实际通过记录获知的人。", "downstream_impact": "会造成章节视角和知识来源矛盾，因此排除。"},
        ],
        "unique_solution_exclusion_evidence": None,
    },
    "03-projection-analysis.json": {"schema_version": "1.0", "selected": "HI1-OPT-SHEN-CONTINUOUS", "projected_ids": [item["id"] for item in model["design_decisions"]], "projected_source_ids": work["unresolved_projection"]},
    "04-adversarial-self-review.json": {
        "schema_version": "1.0", "verdict": "pass",
        "challenges": [
            {"id": "HI1-ADV-POV", "claim": "二十四章焦点是否符合顾衡1、梁策2至3、沈逾4至24", "evidence_ids": ["HPV-POLICY-SHEN-REALITY-MAINLINE", "HPV-CHAPTER-24"], "result": "pass"},
            {"id": "HI1-ADV-RECEIPT", "claim": "顾衡现场线索是否被误授给梁策", "evidence_ids": ["HIN-MINIMAL-CLUE-ONSITE-GUHENG", "HIN-MINIMAL-CLUE-RECEIPT-LIANG", "HIN-RULE-LIANG-RECEIPT-ONLY"], "result": "pass"},
            {"id": "HI1-ADV-MULTI-KNOWER", "claim": "是否存在一个获得方式覆盖多个实际路径", "evidence_ids": [item["node_id"] for item in mode_audit], "result": "pass"},
            {"id": "HI1-ADV-R07", "claim": "R-07是否取得现实感官或控制权", "evidence_ids": ["HIN-RULE-R07-NO-REALITY-SENSE"], "result": "pass"},
            {"id": "HI1-ADV-TERMINATION", "claim": "第七单元是否明确请求及留痕，第八单元是否经过授权关停", "evidence_ids": ["HIN-R07-TERMINATION-REQUEST-SHEN", "HIN-R07-TERMINATION-REQUEST-RECORDED-SHEN", "HIN-SHUTDOWN-AUTHORIZED-SHEN"], "result": "pass"},
            {"id": "HI1-ADV-ENDING", "claim": "现实威胁、当前意识、活动副本和未来开放是否彼此分开", "evidence_ids": ["HIN-ATTACK-STOPPED-SHEN", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED-SHEN", "HIN-NO-ACTIVE-R07-COPY-SHEN", "HIN-OPEN-RELOAD-CONTINUITY-CUSTODIAN"], "result": "pass"},
        ],
        "blockers": [],
    },
}

if DRAFT.exists():
    raise SystemExit(f"fresh draft path already exists: {DRAFT}")
(DRAFT / "generation-evidence").mkdir(parents=True)
write_json(DRAFT / "canonical.json", model)
write_json(DRAFT / "generation-session.json", session)
for name, value in evidence.items():
    write_json(DRAFT / "generation-evidence" / name, value)

print(json.dumps({
    "status": "draft_ready",
    "controlled_checks": 2,
    "units": len(unit_assignments),
    "chapters": len(chapter_assignments),
    "information_nodes": len(information_nodes),
    "multi_knower_nodes": sum(len(node["knower_ids"]) > 1 for node in information_nodes),
    "acquisition_grants_audited": len(mode_audit),
    "actual_reads": len(actual_reads),
}, ensure_ascii=False))
