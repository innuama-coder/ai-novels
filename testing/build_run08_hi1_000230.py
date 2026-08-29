from __future__ import annotations

import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RUN = REPO / "projects" / "duanxian" / "development" / "hld-run-08"
WORK_ORDER = RUN / "work-order-000230-HI1.json"
DRAFT = RUN / "draft-000230-HI1-fresh"
HARNESS = REPO / "harnesses" / "novel-hld-autonomous"
sys.path.insert(0, str(HARNESS))

from runtime.canonical import canonical_sha256, write_json  # noqa: E402


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


work = read(WORK_ORDER)
gate = read(RUN / work["input_gate_ref"]["path"])
baseline = read(RUN / "HB0-r0000-HB0-package" / "hld-control-baseline.json")
ha1 = read(RUN / "HA1-r0103-HA1-package" / "package" / "narrative-architecture.json")
hs1 = read(RUN / "HS1-r0104-HS1-package" / "package" / "storyline-choreography.json")
hc1 = read(RUN / "HC1-r0118-HC1-attempt-000229-package" / "package" / "character-arc-placement.json")

# Fresh semantic identity reads every sealed source-lineage document and no prior HI1 package.
source_documents = {
    item["role"]: read(RUN / item["path"])
    for item in gate["source_lineage_refs"]
}
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


def chapter_distance(character_id: str, chapter_id: str) -> str:
    if chapter_id == "HCH-01-01":
        return "限制第三人称近距；只贴近顾衡在栖港当下可感知的现场与即时推断，并在失去意识前结束，不进入其后状态。"
    if character_id == "CHR-LIANG-CE":
        return "限制第三人称中距的文档聚焦；只呈现接收记录、警方书面通知与急救/机构通报造成的知识变化，不把未在场事件还原为现场感知。"
    if character_id == "CHR-SHEN-YU":
        return "沈逾限制第三人称近距；只呈现她获得的授权材料、文字会话、正式通报及可见接口结果，不进入R-07未输出的内部结论。"
    if character_id == "CHR-R07":
        return "短暂受限第一人称内部窗口；仅容纳文字输入、继承片段与非结论性的过程心理；记忆感官不等于现实感官，且不产生任何现实设备控制。"
    return "沈逾现实主线内的受限外部文档聚焦；仅以该角色被授权的记录、通报和系统结果承担现实节点，不进入其内心，也不扩展为独立视角线。"


focal_by_chapter = {
    "HCH-01-01": "CHR-GUHENG",
    "HCH-01-02": "CHR-LIANG-CE",
    "HCH-01-03": "CHR-LIANG-CE",
    "HCH-02-01": "CHR-SHEN-YU",
    "HCH-02-02": "CHR-SHEN-YU",
    "HCH-02-03": "CHR-SHEN-YU",
    "HCH-03-01": "CHR-R07",
    "HCH-03-02": "CHR-SHEN-YU",
    "HCH-03-03": "CHR-SHEN-YU",
    "HCH-04-01": "CHR-SHEN-YU",
    "HCH-04-02": "CHR-SHEN-YU",
    "HCH-04-03": "CHR-R07",
    "HCH-05-01": "CHR-SHEN-YU",
    "HCH-05-02": "CHR-R07",
    "HCH-05-03": "CHR-SHEN-YU",
    "HCH-06-01": "CHR-SHEN-YU",
    "HCH-06-02": "CHR-SHEN-YU",
    "HCH-06-03": "CHR-HE-WENJUN",
    "HCH-07-01": "CHR-SHEN-YU",
    "HCH-07-02": "CHR-SHEN-YU",
    "HCH-07-03": "CHR-SHEN-YU",
    "HCH-08-01": "CHR-TANG-LI",
    "HCH-08-02": "CHR-SHEN-YU",
    "HCH-08-03": "CHR-SHEN-YU",
}

shells = ha1["chapter_shells"]
agencies = hc1["chapter_agency_contracts"]
assert len(shells) == len(agencies) == 24
assert [item["id"] for item in shells] == [item["chapter_id"] for item in agencies]

agency_by_chapter = {item["chapter_id"]: item for item in agencies}
chapter_assignments = []
for index, shell in enumerate(shells, 1):
    chapter_id = shell["id"]
    agency = agency_by_chapter[chapter_id]
    focal = focal_by_chapter[chapter_id]
    assert focal in agency["focal_character_ids"]
    path = [item for item in agency["information_paths"] if item["character_id"] == focal]
    assert len(path) == 1
    path = path[0]
    chapter_assignments.append(
        {
            "id": f"HPV-CHAPTER-{index:02d}",
            **trace(["NAR-POV-ARCHITECTURE", focal]),
            "chapter_id": chapter_id,
            "parent_unit_id": shell["parent_unit_id"],
            "hc1_agency_contract_id": agency["id"],
            "pov_character_id": focal,
            "focalization_mode": chapter_distance(focal, chapter_id),
            "knowledge_acquisition_modes": path["acquisition_modes"],
            "perception_limits": [path["limit"]],
        }
    )

unit_limits = {
    "HNU-01-GUHENG-BREAK": "现实主线默认由梁策的接收记录与机构通报承接；仅首章例外进入顾衡意识丧失前的限知，后两章不得恢复顾衡焦点。",
    "HNU-02-FAILED-READ-AND-START": "只跟随沈逾获得的授权、医疗通报、设备输出与文字会话；顾衡昏迷垂危且未脑死亡，不可充当感知者或选择者。",
    "HNU-03-RECOGNITION-AND-CARE": "沈逾承担现实主线；R-07仅在记忆重解所必需的短暂窗口内出现，过去顾衡的感官不得转化为R-07的现实感官。",
    "HNU-04-NEW-FEELING-AND-INQUIRY": "沈逾承担可观察交流；R-07窗口只显示文字输入、记忆联想和形成中的判断，不把顾衡旧关系直接等同于当下选择。",
    "HNU-05-COLLAPSE-AND-RECONNECTION": "沈逾承担现实压力与交流变化；R-07窗口只呈现受限文字通道中的混乱与重解，不显示未输出的决定。",
    "HNU-06-EVIDENCE-TO-ACTION": "沈逾现实主线只凭文档、通报和系统输出获知跨城验证；必需现实节点采用外部文档聚焦，记忆不能替代证据或授权。",
    "HNU-07-R07-CHOICE-AND-PROMISE": "沈逾承担可观察的告知与回应；R-07终止方向只能由信息释放顺序、提问与可见状态推断，不进入决定性结论。",
    "HNU-08-STOP-SHUTDOWN-AFTERMATH": "沈逾承担告别与余波；北岬阻断仅以受授权的外部记录承接，R-07不感知或控制现实设备，关停后不再有R-07焦点。",
}
unit_assignments = []
for index, unit in enumerate(ha1["narrative_units"], 1):
    focal = "CHR-LIANG-CE" if index == 1 else "CHR-SHEN-YU"
    unit_assignments.append(
        {
            "id": f"HPV-UNIT-{index:02d}",
            **trace(["NAR-POV-ARCHITECTURE", focal]),
            "unit_id": unit["id"],
            "pov_character_id": focal,
            "focalization_mode": "限制第三人称中距文档聚焦" if index == 1 else "沈逾限制第三人称近距现实主线",
            "perception_limits": [unit_limits[unit["id"]]],
        }
    )


def info(
    identifier: str,
    source_ids: list[str],
    source_information_id: str,
    knower_ids: list[str],
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
        "knower_ids": knower_ids,
        "reader_state": reader_state,
        "acquisition_mode": acquisition_mode,
        "earliest_legal_unit_id": earliest,
        "forbidden_leak_unit_ids": forbidden,
    }


U = [item["id"] for item in ha1["narrative_units"]]
information_nodes = [
    info("HIN-THREAT-SUSPECTED", ["CAU-GLOBAL-SPINE"], "HNU-01-GUHENG-BREAK", ["CHR-GUHENG"], "inferable", "inferred", U[0], []),
    info("HIN-MINIMAL-CLUE-RECEIVED", ["CAU-EVIDENCE-ACTION-CLOSURE"], "HCH-01-02", ["CHR-LIANG-CE"], "known", "documented", U[0], []),
    info("HIN-GUHENG-ALIVE-NONCOMMUNICATIVE", ["NAR-POV-ARCHITECTURE"], "HNU-02-FAILED-READ-AND-START", ["CHR-LIANG-CE", "CHR-SHEN-YU", "CHR-CHENG-YUAN"], "known", "told", U[0], []),
    info("HIN-R07-DISTINCT-SUBJECT", ["CHR-R07"], "HCH-02-03", ["CHR-R07", "CHR-SHEN-YU"], "known", "told", U[1], [U[0]]),
    info("HIN-MEMORY-FRAGMENTS-UNRELIABLE", ["NAR-MEMORY-FRAGMENTS"], "HNU-03-RECOGNITION-AND-CARE", ["CHR-R07", "CHR-SHEN-YU"], "known", "documented", U[2], [U[0], U[1]]),
    info("HIN-MEMORY-CONTINUITY-MISBELIEF", ["NAR-READER-KNOWLEDGE"], "HCH-03-01", ["CHR-R07", "CHR-SHEN-YU"], "misbelieved", "inferred", U[2], [U[0], U[1]]),
    info("HIN-MEMORY-NOT-REAL-SENSORY", ["NAR-MEMORY-FRAGMENTS", "NAR-R07-INFORMATION-BOUNDARY"], "HCH-03-02", ["CHR-R07", "CHR-SHEN-YU"], "known", "inferred", U[2], [U[0], U[1]]),
    info("HIN-R07-NEW-AFFECTION", ["CHR-GU-HENG-MEMORY", "NAR-READER-KNOWLEDGE"], "HNU-04-NEW-FEELING-AND-INQUIRY", ["CHR-R07", "CHR-SHEN-YU"], "inferable", "inferred", U[3], [U[0], U[1], U[2]]),
    info("HIN-R07-NO-REALITY-ACCESS", ["CHR-R07", "NAR-R07-INFORMATION-BOUNDARY"], "HCH-04-03", ["CHR-R07", "CHR-SHEN-YU"], "known", "told", U[3], [U[0], U[1], U[2]]),
    info("HIN-MISREAD-CORRECTED", ["NAR-FAIRNESS"], "HCH-05-02", ["CHR-R07", "CHR-SHEN-YU"], "known", "documented", U[4], [U[0], U[1], U[2], U[3]]),
    info("HIN-ATTACK-DIRECTION", ["CAU-EVIDENCE-ACTION-CLOSURE"], "HCH-05-03", ["CHR-R07", "CHR-SHEN-YU", "CHR-LIANG-CE"], "known", "told", U[4], [U[0], U[1], U[2], U[3]]),
    info("HIN-INDEPENDENT-EVIDENCE-CLOSURE", ["CAU-EVIDENCE-ACTION-CLOSURE", "WLD-THREAT-EVIDENCE-ACTION"], "HNU-06-EVIDENCE-TO-ACTION", ["CHR-SHEN-YU", "CHR-LIANG-CE", "CHR-HE-WENJUN", "CHR-TANG-LI", "CHR-QIN-ZHENG"], "known", "documented", U[5], [U[0], U[1], U[2], U[3], U[4]]),
    info("HIN-REALITY-ACTION-READY", ["WLD-THREAT-EVIDENCE-ACTION"], "HCH-06-03", ["CHR-HE-WENJUN", "CHR-TANG-LI", "CHR-QIN-ZHENG"], "known", "documented", U[5], [U[0], U[1], U[2], U[3], U[4]]),
    info("HIN-R07-TERMINATION-DIRECTION-INFERABLE", ["NAR-R07-INFORMATION-BOUNDARY", "NAR-READER-KNOWLEDGE"], "HNU-07-R07-CHOICE-AND-PROMISE", ["CHR-R07", "CHR-SHEN-YU"], "inferable", "inferred", U[6], [U[0], U[1], U[2], U[3], U[4], U[5]]),
    info("HIN-ATTACK-STOPPED", ["NAR-ENDING-MUST-REVEAL"], "HCH-08-01", ["CHR-SHEN-YU", "CHR-TANG-LI", "CHR-HE-WENJUN", "CHR-QIN-ZHENG"], "known", "system_output", U[7], U[:7]),
    info("HIN-R07-CURRENT-CONSCIOUSNESS-ENDED", ["NAR-ENDING-MUST-REVEAL"], "HCH-08-02", ["CHR-SHEN-YU", "CHR-TANG-LI"], "known", "system_output", U[7], U[:7]),
    info("HIN-NO-ACTIVE-R07-COPY", ["NAR-ENDING-MUST-REVEAL"], "HCH-08-03", ["CHR-SHEN-YU", "CHR-TANG-LI", "CHR-FUTURE-CUSTODIAN"], "known", "documented", U[7], U[:7]),
    info("HIN-OPEN-CAUSAL-AND-TRUST", ["CAU-PRESERVED-OPEN"], "CAU-PRESERVED-OPEN", ["CHR-SHEN-YU", "CHR-C-STATE-REP", "CHR-M-STATE-REP"], "open", "authorized_open", U[7], U[:7], "preserved_open"),
    info("HIN-OPEN-READER-IDENTITY-AND-FEELING", ["INT-READER-QUESTIONS"], "INT-READER-QUESTIONS", ["CHR-SHEN-YU", "CHR-FUTURE-CUSTODIAN"], "open", "authorized_open", U[7], U[:7], "preserved_open"),
    info("HIN-OPEN-RELOAD-CONTINUITY", ["NAR-ENDING-PRESERVED-OPEN"], "NAR-ENDING-PRESERVED-OPEN", ["CHR-SHEN-YU", "CHR-FUTURE-CUSTODIAN"], "open", "authorized_open", U[7], U[:7], "preserved_open"),
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
    knowledge("HKS-CHAR-01-LIANG", "CHR-LIANG-CE", U[0], ["HIN-MINIMAL-CLUE-RECEIVED", "HIN-GUHENG-ALIVE-NONCOMMUNICATIVE"]),
    knowledge("HKS-CHAR-02-SHEN", "CHR-SHEN-YU", U[1], ["HIN-GUHENG-ALIVE-NONCOMMUNICATIVE", "HIN-R07-DISTINCT-SUBJECT"]),
    knowledge("HKS-CHAR-03-R07", "CHR-R07", U[2], ["HIN-R07-DISTINCT-SUBJECT", "HIN-MEMORY-FRAGMENTS-UNRELIABLE", "HIN-MEMORY-NOT-REAL-SENSORY"], ["HIN-MEMORY-CONTINUITY-MISBELIEF"]),
    knowledge("HKS-CHAR-04-R07", "CHR-R07", U[3], ["HIN-R07-DISTINCT-SUBJECT", "HIN-R07-NEW-AFFECTION", "HIN-R07-NO-REALITY-ACCESS"], ["HIN-MEMORY-CONTINUITY-MISBELIEF"]),
    knowledge("HKS-CHAR-05-SHEN", "CHR-SHEN-YU", U[4], ["HIN-MISREAD-CORRECTED", "HIN-ATTACK-DIRECTION"]),
    knowledge("HKS-CHAR-06-SHEN", "CHR-SHEN-YU", U[5], ["HIN-INDEPENDENT-EVIDENCE-CLOSURE", "HIN-REALITY-ACTION-READY"]),
    knowledge("HKS-CHAR-07-R07", "CHR-R07", U[6], ["HIN-REALITY-ACTION-READY", "HIN-R07-TERMINATION-DIRECTION-INFERABLE"]),
    knowledge("HKS-CHAR-08-SHEN", "CHR-SHEN-YU", U[7], ["HIN-ATTACK-STOPPED", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED", "HIN-NO-ACTIVE-R07-COPY", "HIN-OPEN-READER-IDENTITY-AND-FEELING", "HIN-OPEN-RELOAD-CONTINUITY"]),
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
    reader("HKS-READER-01", U[0], ["HIN-THREAT-SUSPECTED", "HIN-MINIMAL-CLUE-RECEIVED", "HIN-GUHENG-ALIVE-NONCOMMUNICATIVE"], ["可判断顾衡发出最小线索后失去意识；不可进入其后主观状态。"]),
    reader("HKS-READER-02", U[1], ["HIN-GUHENG-ALIVE-NONCOMMUNICATIVE", "HIN-R07-DISTINCT-SUBJECT"], ["可知顾衡仍昏迷垂危且R-07为另一个主体；不可把神经材料当作证词。"]),
    reader("HKS-READER-03", U[2], ["HIN-MEMORY-FRAGMENTS-UNRELIABLE", "HIN-MEMORY-CONTINUITY-MISBELIEF", "HIN-MEMORY-NOT-REAL-SENSORY"], ["可怀疑片段时序与因果；不可把过去感官当作R-07现实感官。"]),
    reader("HKS-READER-04", U[3], ["HIN-R07-NEW-AFFECTION", "HIN-R07-NO-REALITY-ACCESS"], ["可推断新情感来自现实交流；不可推断为顾衡旧爱延续或R-07具备现实设备访问。"]),
    reader("HKS-READER-05", U[4], ["HIN-MISREAD-CORRECTED", "HIN-ATTACK-DIRECTION"], ["可知第一层行动方向需要现实核验；不可把片段直接当作关闭权限。"]),
    reader("HKS-READER-06", U[5], ["HIN-INDEPENDENT-EVIDENCE-CLOSURE", "HIN-REALITY-ACTION-READY"], ["可知阻断已不依赖R-07继续输出；不可推断R-07控制了任何硬件。"]),
    reader("HKS-READER-07", U[6], ["HIN-R07-TERMINATION-DIRECTION-INFERABLE", "HIN-REALITY-ACTION-READY"], ["可由可观察迹象怀疑终止方向；不可获得R-07决定性内在结论或承诺真伪。"]),
    reader("HKS-READER-08", U[7], ["HIN-ATTACK-STOPPED", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED", "HIN-NO-ACTIVE-R07-COPY", "HIN-OPEN-CAUSAL-AND-TRUST", "HIN-OPEN-READER-IDENTITY-AND-FEELING", "HIN-OPEN-RELOAD-CONTINUITY"], ["必须确认现实危机与当前意识终止；必须保留幕后链、感情分类、重载与身份连续性为开放。"]),
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
    suspense("HSP-ATTACK-EVIDENCE", ["CAU-EVIDENCE-ACTION-CLOSURE"], ["HIN-THREAT-SUSPECTED", "HIN-MINIMAL-CLUE-RECEIVED"], ["HIN-ATTACK-DIRECTION"], ["HIN-INDEPENDENT-EVIDENCE-CLOSURE", "HIN-REALITY-ACTION-READY"], ["HIN-ATTACK-STOPPED"], None),
    suspense("HSP-R07-DISTINCT-LIFE", ["NAR-READER-KNOWLEDGE"], ["HIN-R07-DISTINCT-SUBJECT"], ["HIN-MEMORY-FRAGMENTS-UNRELIABLE", "HIN-R07-NEW-AFFECTION"], ["HIN-MISREAD-CORRECTED"], ["HIN-R07-CURRENT-CONSCIOUSNESS-ENDED"], None),
    suspense("HSP-R07-TERMINATION", ["NAR-R07-INFORMATION-BOUNDARY"], ["HIN-R07-NO-REALITY-ACCESS"], ["HIN-R07-TERMINATION-DIRECTION-INFERABLE"], [], ["HIN-R07-CURRENT-CONSCIOUSNESS-ENDED"], None),
    suspense("HSP-OPEN-CAUSAL-TRUST", ["CAU-PRESERVED-OPEN"], ["HIN-INDEPENDENT-EVIDENCE-CLOSURE"], ["HIN-ATTACK-STOPPED"], [], [], "HDD-HI1-CAU-PRESERVED-OPEN", "preserved_open"),
    suspense("HSP-OPEN-READER-QUESTIONS", ["INT-READER-QUESTIONS"], ["HIN-R07-DISTINCT-SUBJECT", "HIN-R07-NEW-AFFECTION"], ["HIN-R07-TERMINATION-DIRECTION-INFERABLE"], [], [], "HDD-HI1-INT-READER-QUESTIONS", "preserved_open"),
    suspense("HSP-OPEN-RELOAD", ["NAR-ENDING-PRESERVED-OPEN"], ["HIN-NO-ACTIVE-R07-COPY"], ["HIN-OPEN-RELOAD-CONTINUITY"], [], [], "HDD-HI1-NAR-ENDING-PRESERVED-OPEN", "preserved_open"),
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
    payoff("HIN-MATRIX-ATTACK", ["CAU-EVIDENCE-ACTION-CLOSURE"], ["HIN-THREAT-SUSPECTED", "HIN-ATTACK-DIRECTION", "HIN-INDEPENDENT-EVIDENCE-CLOSURE", "HIN-ATTACK-STOPPED"], [U[0], U[4], U[5]], U[7], "payoff"),
    payoff("HIN-MATRIX-R07-IDENTITY", ["NAR-READER-KNOWLEDGE"], ["HIN-R07-DISTINCT-SUBJECT", "HIN-MEMORY-FRAGMENTS-UNRELIABLE", "HIN-R07-NEW-AFFECTION", "HIN-MISREAD-CORRECTED"], [U[1], U[2], U[3]], U[4], "reveal"),
    payoff("HIN-MATRIX-TERMINATION", ["NAR-R07-INFORMATION-BOUNDARY"], ["HIN-R07-NO-REALITY-ACCESS", "HIN-R07-TERMINATION-DIRECTION-INFERABLE", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED"], [U[3], U[6]], U[7], "payoff"),
    payoff("HIN-MATRIX-OPEN-CAUSAL", ["CAU-PRESERVED-OPEN"], ["HIN-OPEN-CAUSAL-AND-TRUST"], [U[7]], U[7], "authorized_open", "preserved_open"),
    payoff("HIN-MATRIX-OPEN-READER", ["INT-READER-QUESTIONS"], ["HIN-OPEN-READER-IDENTITY-AND-FEELING"], [U[7]], U[7], "authorized_open", "preserved_open"),
    payoff("HIN-MATRIX-OPEN-RELOAD", ["NAR-ENDING-PRESERVED-OPEN"], ["HIN-OPEN-RELOAD-CONTINUITY"], [U[7]], U[7], "authorized_open", "preserved_open"),
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
    rule("HIN-RULE-GUHENG-POV-CUTOFF", ["NAR-POV-ARCHITECTURE"], ["HIN-GUHENG-ALIVE-NONCOMMUNICATIVE"], "顾衡只在首章意识丧失前承担限知；此后昏迷垂危且未脑死亡，信息只能由记录与告知转移。", ["读者可从医疗和机构通报知道顾衡仍活着但无法交流。"], ["不得进入顾衡第2章及之后的感知、记忆、选择或内在状态。"]),
    rule("HIN-RULE-LIANG-DOCUMENT-ONLY", ["NAR-POV-ARCHITECTURE"], ["HIN-MINIMAL-CLUE-RECEIVED", "HIN-GUHENG-ALIVE-NONCOMMUNICATIVE"], "第二章及其后同单元交接由梁策通过记录与机构告知承接。", ["梁策可依据documented与told形成判断。"], ["不得把梁策未在场的受伤、抢救或顾衡主观状态写成perceived。"]),
    rule("HIN-RULE-R07-NO-REALITY-SENSE", ["NAR-MEMORY-FRAGMENTS", "NAR-R07-INFORMATION-BOUNDARY"], ["HIN-MEMORY-NOT-REAL-SENSORY", "HIN-R07-NO-REALITY-ACCESS"], "R-07只有文字输入、继承片段和过程性心理；过去顾衡的感官归属过去，现实设备状态只能由他人告知或系统输出转述。", ["R-07可对文字、停顿、片段与告知作联想和推断。"], ["不得赋予R-07现实视觉、听觉、身体感、网络访问、设备控制或行动权限。"]),
    rule("HIN-RULE-TERMINATION-CONCLUSION-HIDDEN", ["NAR-R07-INFORMATION-BOUNDARY", "NAR-FAIRNESS"], ["HIN-R07-TERMINATION-DIRECTION-INFERABLE", "HIN-R07-CURRENT-CONSCIOUSNESS-ENDED"], "终止选择形成后收紧可见范围，以可观察迹象维持公平推断而不展示决定性结论。", ["读者可由沉默、信息次序、关停问题与告别准备怀疑终止方向。"], ["不得出现决定性内心独白、终止计划完整步骤或对未来重载承诺真伪的内在定性。"]),
    rule("HIN-RULE-EVIDENCE-LADDER", ["CAU-EVIDENCE-ACTION-CLOSURE", "WLD-THREAT-EVIDENCE-ACTION"], ["HIN-ATTACK-DIRECTION", "HIN-INDEPENDENT-EVIDENCE-CLOSURE", "HIN-REALITY-ACTION-READY", "HIN-ATTACK-STOPPED"], "记忆只给方向，证词、硬件、授权与属地行动分别承担不可替代的现实闭环。", ["读者可在多源材料闭合后判断行动已准备完成。"], ["不得让R-07一句话、单一记忆或单一系统输出直接阻止袭击。"]),
    rule("HIN-RULE-OPEN-CAUSAL", ["CAU-PRESERVED-OPEN"], ["HIN-OPEN-CAUSAL-AND-TRUST"], "完整幕后利益链、原因层公开程度和两国互信被作者明确保留。", ["读者可判断一次合作完成了当前阻断。"], ["不得推断两国恢复互信、完整利益链已查清或原因层已公开。"], "preserved_open"),
    rule("HIN-RULE-OPEN-READER", ["INT-READER-QUESTIONS"], ["HIN-OPEN-READER-IDENTITY-AND-FEELING"], "沈逾的感情分类与R-07/顾衡关系保持为持续问题。", ["读者可确认R-07的新感情不来自顾衡旧爱。"], ["不得替沈逾裁定她最终回应顾衡、R-07或两者纠缠中的哪一方。"], "preserved_open"),
    rule("HIN-RULE-OPEN-RELOAD", ["NAR-ENDING-PRESERVED-OPEN"], ["HIN-NO-ACTIVE-R07-COPY", "HIN-OPEN-RELOAD-CONTINUITY"], "当前意识结束且无活动副本，但未来技术与身份连续性未裁决。", ["读者可确认当前这一个R-07已经不可逆终止。"], ["不得把未来重载写成已保证可行，也不得预先认定重载者就是或不是R-07。"], "preserved_open"),
]

dependencies = [
    {
        "id": "HDD-HI1-CAU-PRESERVED-OPEN",
        "source_id": "CAU-PRESERVED-OPEN",
        "owner_stage": "HI1",
        "affected_obligation_ids": ["HSP-OPEN-CAUSAL-TRUST", "HIN-OPEN-CAUSAL-AND-TRUST"],
        "disposition": "conditional_structure_preserves_open",
        "object_evidence_refs": ["HIN-RULE-OPEN-CAUSAL", "HIN-MATRIX-OPEN-CAUSAL"],
        "rationale_anchor": "HI1只需保留幕后链、原因层披露、感情分类与重载可能的未知状态，不需要替作者选择答案。",
        "downstream_effect": "HD1/LLD必须以未裁决边界书写余波，不得把当前危机闭环扩大为系列级答案。",
        "resolution_ref": None,
    },
    {
        "id": "HDD-HI1-INT-READER-QUESTIONS",
        "source_id": "INT-READER-QUESTIONS",
        "owner_stage": "HI1",
        "affected_obligation_ids": ["HSP-OPEN-READER-QUESTIONS", "HIN-OPEN-READER-IDENTITY-AND-FEELING"],
        "disposition": "conditional_structure_preserves_open",
        "object_evidence_refs": ["HIN-RULE-OPEN-READER", "HIN-MATRIX-OPEN-READER"],
        "rationale_anchor": "读者需要持续面对而不是在本部得到三项身份与感情答案；信息架构可通过开放终端稳定保留。",
        "downstream_effect": "HD1/LLD必须给出足够证据形成问题，同时禁止叙述者或人物替作者最终分类。",
        "resolution_ref": None,
    },
    {
        "id": "HDD-HI1-NAR-ENDING-PRESERVED-OPEN",
        "source_id": "NAR-ENDING-PRESERVED-OPEN",
        "owner_stage": "HI1",
        "affected_obligation_ids": ["HSP-OPEN-RELOAD", "HIN-OPEN-RELOAD-CONTINUITY"],
        "disposition": "conditional_structure_preserves_open",
        "object_evidence_refs": ["HIN-RULE-OPEN-RELOAD", "HIN-MATRIX-OPEN-RELOAD"],
        "rationale_anchor": "结尾必须确认当前意识终止和无活动副本，但承诺真伪、未来重载与身份连续性均可保持未裁决。",
        "downstream_effect": "HD1/LLD必须把事实性终止与未来可能分开，禁止以暗示偷渡身份连续性答案。",
        "resolution_ref": None,
    },
]

policy = {
    "id": "HPV-POLICY-SHEN-MAINLINE",
    **trace(["NAR-POV-ARCHITECTURE"]),
    "allowed_modes": [
        "顾衡首章意识丧失前的限制第三人称",
        "沈逾限制第三人称现实主线",
        "R-07短暂受限第一人称内部窗口",
        "沈逾主线内不进入他人内心的外部文档聚焦",
    ],
    "switch_rule": "每章最多一个有效焦点，只能在HA1章壳边界切换；R-07窗口仅用于沈逾不可替代的意识形成、记忆重解与存在困境，形成终止选择后不得展示结论。",
    "legality_rule": "焦点人物必须由对应HC1 agency contract授权并逐字复制其acquisition_modes与limit；顾衡仅HCH-01-01可限知，第2章起不可焦点或选择；梁策HCH-01-02/03仅documented+told；R-07无现实感官、网络或设备控制。",
}

actual_reads = list(gate["source_lineage_refs"])
allow_by_role = {item["role"]: item for item in work["file_allowlist"]}
actual_reads.extend(allow_by_role[f"upstream::{stage}::main"] for stage in ("HB0", "HA1", "HS1", "HC1"))

model = {
    "schema_version": "1.0",
    "skill": "novel-hld-information-architect",
    "stage": "HI1",
    "hld_run_id": work["hld_run_id"],
    "status": "ready",
    "input_gate_ref": work["input_gate_ref"],
    "source_artifacts": actual_reads,
    "authority_partition": baseline["authority_partition"],
    "design_decisions": [
        {"id": "HDDES-HI1-POV-ALLOCATION", "choice": "沈逾现实主线、三处R-07短暂内部窗口及两处外部文档节点", "candidate_refs": ["HI1-OPT-SHEN-MAIN", "HI1-OPT-BROADER-MULTI"]},
        {"id": "HDDES-HI1-KNOWLEDGE-LEDGER", "choice": "按八个单元分离人物与读者知识，并为每次获得设置合法路径和泄漏禁区", "candidate_refs": ["HI1-OPT-SHEN-MAIN", "HI1-OPT-BROADER-MULTI"]},
        {"id": "HDDES-HI1-SUSPENSE-CLOSURE", "choice": "以袭击证据、R-07主体性、终止方向和三项开放终端组成闭合链", "candidate_refs": ["HI1-OPT-SHEN-MAIN", "HI1-OPT-BROADER-MULTI"]},
    ],
    "derivation_claims": [],
    "decision_dependencies": dependencies,
    "open_items": work["unresolved_projection"],
    "downstream_contract": {
        "consumer": "HR1",
        "required_roles": ["legal_pov_assignments", "character_reader_knowledge_separation", "fair_suspense_and_payoff_control"],
    },
    "pov_policy": policy,
    "unit_pov_assignments": unit_assignments,
    "chapter_pov_assignments": chapter_assignments,
    "knowledge_states": knowledge_states,
    "reader_information_states": reader_states,
    "suspense_chains": suspense_chains,
    "information_nodes": information_nodes,
    "reveal_payoff_matrix": reveal_payoff,
    "concealment_and_inference_rules": inference_rules,
}

ownership = {name: [] for name in ("source_projection", "hld_owned", "preserved_open", "lld_freedom")}
for array_name in (
    "unit_pov_assignments",
    "chapter_pov_assignments",
    "knowledge_states",
    "reader_information_states",
    "suspense_chains",
    "information_nodes",
    "reveal_payoff_matrix",
    "concealment_and_inference_rules",
):
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
    target = model[pointer[1:]]
    model["derivation_claims"].append(
        {"id": identifier, "source_refs": source_refs, "target_locator": pointer, "value_sha256": canonical_sha256(target)}
    )

session = {
    "schema_version": "1.0",
    "skill": "novel-hld-information-architect",
    "task_id": work["task_id"],
    "actual_read_refs": actual_reads,
}

evidence = {
    "00-dependency-assessment.json": {"schema_version": "1.0", "assessments": dependencies},
    "01-obligation-analysis.json": {
        "schema_version": "1.0",
        "obligations": [
            "24个HA1章壳按原顺序一一绑定24个HC1 agency contract，并逐字复制所选焦点的信息获得模式和限制。",
            "顾衡仅HCH-01-01可限知；HCH-01-02起持续昏迷垂危且未脑死亡，不得成为焦点、感知者或选择者。",
            "HCH-01-02与HCH-01-03梁策只通过documented和told获得信息，不得现场perceived。",
            "R-07所有信息来自文字输入、继承片段与他人告知；过去记忆感官不等于现实感官，且无网络、设备或现实行动控制。",
            "沈逾现实主线保持近距限知；R-07只在意识形成、关系新判断和存在崩溃三处出现短暂受限内部窗口。",
            "行动线索必须经证词、硬件、授权与属地行动独立闭合，R-07不能直接解决现实危机。",
            "终止方向在第7单元只允许公平推断，第8单元才以关停事实和系统记录确认。",
            "当前意识终止、无活动副本、袭击停止必须揭示；幕后链、感情分类、重载及身份连续性必须保持开放。",
        ],
        "open_items": work["unresolved_projection"],
        "forbidden": [
            "顾衡第2章及之后的任何主观感知、选择或内在焦点",
            "梁策对未在场伤害和抢救的现场感知",
            "R-07现实感官、网络访问、设备控制或由记忆替代现实证据",
            "R-07终止决定的决定性内心独白、完整计划或重载承诺真伪",
            "叙述者替作者回答系列级开放问题",
            "对白、线索措辞、动作编排、感官细节或段落级场景设计",
        ],
    },
    "02-option-analysis.json": {
        "schema_version": "1.0",
        "candidates": [
            {
                "id": "HI1-OPT-SHEN-MAIN",
                "canonical_difference": "现实持续由沈逾限制第三人称承载，仅在三处不可替代节点短暂进入R-07；HC1无沈逾焦点的现实节点采用不进入内心的外部文档聚焦。",
                "tradeoff": "最大化主线连续性和终止悬念公平性，但HD1需要明确标出文档交接与短暂窗口的边界。",
                "downstream_impact": "HD1可据24章合同直接分配叙述距离；LLD不得把外部文档节点扩展为新人物内心线。",
            },
            {
                "id": "HI1-OPT-BROADER-MULTI",
                "canonical_difference": "在更多HC1允许章节采用梁策、唐黎、何文军和R-07的近距内部焦点，形成更广的多角色信息分发。",
                "tradeoff": "现实证据节点更直接，但会增加视角切换、缩短读者与沈逾的信息差，并违反不增加独立人物视角线的上游约束。",
                "downstream_impact": "HD1/LLD会需要额外主观知识账本并更容易泄漏R-07决定或让证据线先于沈逾主线完成。",
            },
        ],
        "unique_solution_exclusion_evidence": None,
    },
    "03-projection-analysis.json": {
        "schema_version": "1.0",
        "selected": "HI1-OPT-SHEN-MAIN",
        "projected_ids": [item["id"] for item in model["design_decisions"]],
        "projected_source_ids": work["unresolved_projection"],
    },
    "04-adversarial-self-review.json": {
        "schema_version": "1.0",
        "verdict": "pass",
        "challenges": [
            {"id": "HI1-ADV-GUHENG", "claim": "顾衡是否在失去意识后仍被用作感知者或选择者", "evidence_ids": ["HPV-CHAPTER-01", "HIN-RULE-GUHENG-POV-CUTOFF"], "result": "pass"},
            {"id": "HI1-ADV-LIANG", "claim": "第二章梁策是否偷渡现场感知", "evidence_ids": ["HPV-CHAPTER-02", "HIN-RULE-LIANG-DOCUMENT-ONLY"], "result": "pass"},
            {"id": "HI1-ADV-R07-SENSE", "claim": "R-07记忆感官是否被误写为现实感官或设备控制", "evidence_ids": ["HIN-MEMORY-NOT-REAL-SENSORY", "HIN-RULE-R07-NO-REALITY-SENSE"], "result": "pass"},
            {"id": "HI1-ADV-R07-DECISION", "claim": "终止方向是否通过决定性内心结论泄漏", "evidence_ids": ["HIN-R07-TERMINATION-DIRECTION-INFERABLE", "HIN-RULE-TERMINATION-CONCLUSION-HIDDEN"], "result": "pass"},
            {"id": "HI1-ADV-EVIDENCE", "claim": "记忆线索是否非法替代现实证据、硬件与授权链", "evidence_ids": ["HSP-ATTACK-EVIDENCE", "HIN-RULE-EVIDENCE-LADDER"], "result": "pass"},
            {"id": "HI1-ADV-POV", "claim": "R-07窗口和外部节点是否扩展为独立人物视角线", "evidence_ids": ["HPV-POLICY-SHEN-MAINLINE", "HPV-UNIT-06"], "result": "pass"},
            {"id": "HI1-ADV-OPEN", "claim": "结尾开放问题是否被静默回答", "evidence_ids": ["HSP-OPEN-RELOAD", "HIN-RULE-OPEN-READER"], "result": "pass"},
            {"id": "HI1-ADV-LLD", "claim": "是否泄漏对白、动作、线索措辞、感官细节或段落级安排", "evidence_ids": ["HDDES-HI1-POV-ALLOCATION", "HDDES-HI1-KNOWLEDGE-LEDGER"], "result": "pass"},
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
    "draft": str(DRAFT),
    "chapters": len(chapter_assignments),
    "information_nodes": len(information_nodes),
    "actual_reads": len(actual_reads),
}, ensure_ascii=False))
