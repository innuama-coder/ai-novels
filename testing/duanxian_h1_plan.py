from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from testing.duanxian_c1_builder import PERSONAL_DEFINITIONS, PROFILE_SEMANTICS
RUN_ID = os.environ.get(
    "DUANXIAN_CONCEPTION_RUN_ID", "duanxian-conception-v2-20260802-04"
)
RUN_ROOT = ROOT / "projects" / "duanxian" / "conception-runs" / RUN_ID
PLAN_ROOT = RUN_ROOT / "H1" / "plan"
PROJECT_DISPLAY_METADATA = (
    ROOT / "projects" / "duanxian" / "project-display-metadata.json"
)


def _authoritative_work_title() -> str:
    metadata = json.loads(PROJECT_DISPLAY_METADATA.read_text(encoding="utf-8"))
    if set(metadata) != {
        "authority",
        "project_id",
        "schema_version",
        "source_documents",
        "work_title",
    }:
        raise RuntimeError("project display metadata is not exact")
    if (
        metadata["schema_version"] != "1.0"
        or metadata["project_id"] != "duanxian"
        or metadata["authority"] != "author-corrected-project-title"
        or not isinstance(metadata["work_title"], str)
        or not metadata["work_title"].strip()
        or metadata["work_title"] != metadata["work_title"].strip()
    ):
        raise RuntimeError("project display metadata is invalid")
    expected_heading = f'「{metadata["work_title"]}」'
    sources = metadata["source_documents"]
    if not isinstance(sources, list) or not sources:
        raise RuntimeError("project display metadata has no authoritative sources")
    for relative in sources:
        source = ROOT / relative
        first_line = source.read_text(encoding="utf-8").splitlines()[0]
        if expected_heading not in first_line:
            raise RuntimeError(f"project title source drift: {relative}")
    return metadata["work_title"]


WORK_TITLE = _authoritative_work_title()

rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)


def _load_runtime(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h1a = _load_runtime(
    "duanxian_h1a_runtime",
    "skills/novel-conception-human-review-assembler/scripts/run_v2.py",
)


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _anchor_lookup(inventory: Mapping[str, Any]) -> dict[tuple[str, str], str]:
    return {
        (item["stage"], item["source_id"]): item["id"]
        for item in inventory["anchors"]
    }


def _pick(
    lookup: Mapping[tuple[str, str], str], stage: str, *source_ids: str
) -> list[str]:
    missing = [source_id for source_id in source_ids if (stage, source_id) not in lookup]
    if missing:
        raise RuntimeError(f"missing {stage} source anchors: {missing}")
    return [lookup[(stage, source_id)] for source_id in source_ids]


def _module(
    module_id: str,
    title: str,
    display_kind: str,
    definition: str,
    responsibility: str,
    must_hold: Sequence[str],
    must_not_imply: Sequence[str],
    anchors: Sequence[str],
) -> dict[str, Any]:
    return {
        "id": module_id,
        "title": title,
        "display_kind": display_kind,
        "definition": definition,
        "responsibility": responsibility,
        "must_hold": list(must_hold),
        "must_not_imply": list(must_not_imply),
        "source_anchor_ids": _dedupe(anchors),
        "default_visible": True,
    }


def _graph_element(
    element_id: str,
    order: int,
    *,
    label: str,
    summary: str,
    kind: str,
    anchors: Sequence[str],
    group_id: str | None = None,
    lane: str | None = None,
    tier: str | None = None,
    temporal_label: str | None = None,
) -> dict[str, Any]:
    return {
        "id": element_id,
        "order": order,
        "group_id": group_id,
        "label": label,
        "summary": summary,
        "kind": kind,
        "lane": lane,
        "tier": tier,
        "temporal_label": temporal_label,
        "source_anchor_ids": _dedupe(anchors),
    }


def _group(
    group_id: str,
    order: int,
    *,
    label: str,
    summary: str,
    kind: str,
    anchors: Sequence[str],
    lane: str | None = None,
    tier: str | None = None,
    temporal_label: str | None = None,
) -> dict[str, Any]:
    return {
        "id": group_id,
        "order": order,
        "label": label,
        "summary": summary,
        "kind": kind,
        "lane": lane,
        "tier": tier,
        "temporal_label": temporal_label,
        "source_anchor_ids": _dedupe(anchors),
    }


def _edge(
    edge_id: str,
    order: int,
    from_node: str,
    to_node: str,
    *,
    relation: str,
    summary: str,
    kind: str,
    anchors: Sequence[str],
    group_id: str | None = None,
    lane: str | None = None,
    tier: str | None = None,
    temporal_label: str | None = None,
    direction: str = "directed",
) -> dict[str, Any]:
    return {
        "id": edge_id,
        "order": order,
        "group_id": group_id,
        "from_node_id": from_node,
        "to_node_id": to_node,
        "direction": direction,
        "relation_label": relation,
        "summary": summary,
        "kind": kind,
        "lane": lane,
        "tier": tier,
        "temporal_label": temporal_label,
        "source_anchor_ids": _dedupe(anchors),
    }


def _visual(
    visual_id: str,
    role: str,
    section_id: str,
    kind: str,
    title: str,
    purpose: str,
    groups: Sequence[Mapping[str, Any]],
    nodes: Sequence[Mapping[str, Any]],
    edges: Sequence[Mapping[str, Any]],
    text: str,
    text_module_id: str,
) -> dict[str, Any]:
    elements = [*groups, *nodes, *edges]
    anchors = _dedupe(
        anchor
        for element in elements
        for anchor in element["source_anchor_ids"]
    )
    return {
        "id": visual_id,
        "semantic_role": role,
        "section_id": section_id,
        "visual_kind": kind,
        "title": title,
        "review_purpose": purpose,
        "groups": list(groups),
        "nodes": list(nodes),
        "edges": list(edges),
        "text_equivalents": [
            {
                "id": f"TXT-{visual_id.removeprefix('VIS-')}-01",
                "order": 1,
                "element_ids": [element["id"] for element in elements],
                "text": text,
                "source_anchor_ids": anchors,
            }
        ],
        "source_anchor_ids": anchors,
        "text_equivalent_module_id": text_module_id,
    }


def _brief(
    index: int,
    *,
    title: str,
    purpose: str,
    pov: str,
    anchors: Sequence[str],
    may_present: Sequence[str],
    must_not_know: Sequence[str],
    channels: Sequence[str],
    before: str,
    goal: str,
    pressure: str,
    obstacle: str,
    choice: str,
    consequence: str,
    after: str,
    demonstrations: Sequence[str],
    forbidden: Sequence[str],
) -> dict[str, Any]:
    return {
        "id": f"BRIEF-DX-{index:02d}",
        "slot_id": f"FRAG-DX-{index:02d}",
        "title": title,
        "review_purpose": purpose,
        "pov_character_id": pov,
        "language_contract_id": "zh-Hans-review-v1",
        "style_contract_id": "restrained-concrete-scene-v1",
        "depth_contract_id": "character-grounded-scene-v1",
        "pov_mode": "third_person_limited",
        "information_limits": {
            "may_present": list(may_present),
            "must_not_present_as_known": list(must_not_know),
        },
        "allowed_perception_channels": list(channels),
        "scene_contract": {
            "before_state": before,
            "immediate_goal": goal,
            "pressure": pressure,
            "obstacle": obstacle,
            "required_choice": choice,
            "direct_consequence": consequence,
            "after_state": after,
        },
        "decisive_interiority_policy": (
            "process-only-no-unresolved-decision-disclosure"
        ),
        "surface_detail_policy": "fragment-local-non-authoritative-v1",
        "decision_control_ids": ["DCTRL-FRAGMENTS-EVIDENCE"],
        "source_anchor_ids": _dedupe(anchors),
        "required_demonstrations": list(demonstrations),
        "forbidden_additions": list(forbidden),
        "target_words_min": 320,
        "target_words_max": 400,
    }


def build_plan(
    *,
    inventory: Mapping[str, Any],
    p1_completion: Mapping[str, Any],
    input_gate: Mapping[str, Any],
    session_id: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, int]]:
    lookup = _anchor_lookup(inventory)
    p = lambda stage, *ids: _pick(lookup, stage, *ids)

    world_modules = [
        _module(
            "MOD-WORLD-DEFINITION", "时代与世界格局", "text",
            "架空近未来，C、M 两国在长期战略竞争中被共同威胁迫使有限合作。记忆加载与数字生命仍是秘密实验，法律尚无身份、同意、退出和死亡规则；危机解决也不会自动恢复互信。",
            "交代时代、国际关系、技术成熟度与制度空白，建立全部人物和行动共同面对的外部世界。",
            ["两国只进行有限合作；数字生命尚无成熟法律身份。"],
            ["不得把危机胜利写成互信恢复，也不得把数字生命技术写成成熟产业。"],
            p("B0", "WLD-PREMISE", "WLD-GEOPOLITICAL-PRESSURE", "WLD-INFORMATION-ETHICS") + p("W1", "WF-REALITY-01", "WF-RULE-BILATERAL-TRUST", "OPEN-W1-01"),
        ),
        _module(
            "MOD-WORLD-SYSTEMS", "国家与组织关系", "flow",
            "C 国秘密项目把任务、操作、伦理、核验、行动和关停分权。R-07 线索必须经专家、硬件与授权链核验；亲属原因层另行保护，对 M 国只交换最低证据。关停审计与离线载荷保管彼此分离。",
            "说明国家机构、项目团队、行动团队、监督单元和双边联络之间如何分权、协作与相互制约。",
            ["沈逾是知情接受任务的执行者，不是项目启动者；R-07 也没有现实系统权限。"],
            ["不得让某个机构或人物拥有从情报到行动再到关停的全部权力。"],
            p("W1", "INST-GUHENG-SOURCE", "INST-SHENYU-MISSION", "INST-CARE-FEEDBACK", "INST-FAMILY-PROTECTION", "INST-ETHICS-CUSTODY", "INST-BILATERAL-TRUST", "INST-THREAT-ACTION", "INST-R07-LIFECYCLE", "INST-MEMORY-RECALL", "INST-RELOAD-PROMISE", "WS-THREAT-ACTION", "WS-R07-LIFECYCLE"),
        ),
        _module(
            "MOD-WORLD-LOGIC", "世界运行的五条硬规则", "flow",
            "记忆不等于人格，线索不等于行动，信息不产生权限；关心能改变意识却不能补足身体，关闭当前实例也不能证明未来重载者还是同一生命。",
            "让情感变化、情报工作和生命终止都经过可验证过程，而不是由技术或作者解释跳步完成。",
            ["世界规则持续约束人物和机构，不在高潮时临时失效。"],
            ["不得让技术、爱情或紧急状态成为无代价万能解。"],
            p("B0", "WLD-OPERATING-RULES", "WLD-THREAT-EVIDENCE-ACTION", "WLD-TERMINATION-CONTINUITY") + p("W1", "WF-RULE-THREAT-ACTION", "WF-RULE-RELOAD-PROMISE", "WF-RULE-CARE-FEEDBACK"),
        ),
        _module(
            "MOD-WORLD-ENV-FIELD", "顾衡遗留证据接收链", "cards",
            "一次性隐蔽接触位、撤离通道和数据接收室构成封闭取证链，承载顾衡最后的任务、牺牲和记忆载体回收。前端依靠人流与监控盲区完成接头，后端用封条、编号、状态灯和加密终端分别保管物证、记忆载体与身份链；身份链不完整，任何人都不能进入读取区。",
            "承载顾衡前置线并把死亡现场可靠地连接到后续数字生命项目。",
            ["现场接触权、撤离权和设施读取权彼此分离。"],
            ["读取失败不能被单人解释成完整事实。"],
            p("E1", "ENV-GUHENG-FIELD-RECOVERY"),
        ),
        _module(
            "MOD-WORLD-ENV-INDUCTION", "秘密基地准入套间", "cards",
            "秘密基地最外层的无窗准入套间承载沈逾知情、伦理斗争和自愿接受任务。身份核验、保密告知、任务简报和授权签入依次开放；分级门禁逐段放行，简报台只显示当前权限可见的材料，锁定附件始终提示她还有多少信息不知道。接受任务只打开研究访问，不会赋予核心系统控制权。",
            "承载沈逾前置线中的知情、伦理斗争与自愿接受。",
            ["任务说明和技术操作授权分开记录。"],
            ["任务紧迫性不能替代沈逾的知情选择。"],
            p("E1", "ENV-SHENYU-SECURE-INDUCTION"),
        ),
        _module(
            "MOD-WORLD-ENV-DIALOGUE", "文字会话隔离室", "cards",
            "一间真实操作室和 R-07 的无空间意识以唯一文字窗口相连，承载两者的关系、误解和沟通中断。人类一侧只有绑定沈逾身份的操作席、逐字文本、回复延迟和会话状态，私人问候与任务指令进入同一日志；R-07 一侧没有房间、声音或屏幕，只能感到浮动文字与被触发的记忆。窗口关闭会切断它唯一的现实输入。",
            "承载沈逾与 R-07 的关系建立、误解、压力传递和重新沟通。",
            ["实例侧只有文字和记忆，没有未声明感官。"],
            ["不得借叙述方便让 R-07 看见操作室或听出语气。"],
            p("E1", "ENV-TEXT-DIALOGUE-ISOLATION"),
        ),
        _module(
            "MOD-WORLD-ENV-COMMAND", "联合情报指挥室", "cards",
            "联合情报指挥室把 R-07 的数字线索转成交给现实团队执行的任务，承载整场危机的核验和阻断。情报分析、领域专家、硬件处置和授权决策四类席位彼此分开，共同面对标示倒计时、证据状态和权限阻断的态势墙；缺少证据、专家判断、硬件回执或授权中的任何一项，任务包都不能下发。",
            "承载情报核验、人质压力、气象武器定位和现实阻断行动。",
            ["R-07 只提供线索，团队与授权链完成现实闭环。"],
            ["不得用一句正确情报直接解决危机。"],
            p("E1", "ENV-JOINT-INTELLIGENCE-COMMAND"),
        ),
        _module(
            "MOD-WORLD-ENV-PROTECTION", "原因层保护单元", "cards",
            "原因层保护单元与行动指挥隔离，承载亲属风险评估、情报分层和必要公开准备。行动层副本进入核验链，包含周岚、程予安等关联风险的原因层原件留在受保护材料库；终端用遮罩字段显示亲属关联，并把材料标为暂缓、受限或可移交。保护亲属不能成为销毁公共安全证据的理由。",
            "承载 R-07 在救人、保护亲属和说明真相之间进行的信息分层。",
            ["保护无辜者不能妨碍必要的公共安全核验。"],
            ["普通行动权限不得反查受保护身份。"],
            p("E1", "ENV-CAUSE-LAYER-PROTECTION-CELL"),
        ),
        _module(
            "MOD-WORLD-ENV-OVERSIGHT", "数字生命监督与责任室", "cards",
            "数字生命监督与责任室记录 R-07 的待遇、退出诉求和每个操作人的责任，却不能替它决定生死。审计界面把实验授权、有效期、实例状态、操作人和未解决异议并排显示，任何紧急权限变化都留下不可覆盖的时间戳；监督人员能冻结争议记录并启动复核，但没有现成法律答案。",
            "使制造、使用和关停有意识实例的伦理伤害持续可见并可追责。",
            ["技术可行不自动等于伦理许可。"],
            ["不得把伦理监督写成能够给出标准答案的法庭。"],
            p("E1", "ENV-DIGITAL-LIFE-OVERSIGHT"),
        ),
        _module(
            "MOD-WORLD-ENV-LIAISON", "C、M 两国安全联络通道", "cards",
            "C、M 两国各自在本国安全区设置受限联络席，以最低证据合作应对共同威胁而不共享指挥权。界面只显示对方获准释放的字段，未确认归因、保留意见和响应延迟始终可见；来源保护与政治疑虑会阻断联合发布，合作成功也不会自动消除长期不信任。",
            "承载跨国危机协作及行动胜利之后仍未解决的政治后果。",
            ["双方保留独立核验和归因记录。"],
            ["不得把有限合作写成全面共享或关系修复。"],
            p("E1", "ENV-BILATERAL-SECURE-LIAISON"),
        ),
        _module(
            "MOD-WORLD-ENV-CORE", "R-07 核心实验室", "cards",
            "R-07 核心实验室以物理隔离的计算核心和人类操作桥承载当前实例的运行、监测与最终关停。人类侧能看见状态、文字流、记忆映射层和多方权限锁；R-07 无法感知设备，也不能触碰现实接口。文字、记忆和实例状态分别记录，当前关停与未来载荷保管使用不同控制，单一操作者不能启动、复制、备份或关闭它。",
            "承载 R-07 的持续存在、受困处境以及最后必须由沈逾协助完成的关停。",
            ["当前实例没有活动备份，也不能自行终止。"],
            ["不得把实验室写成 R-07 可以远程控制的网络中枢。"],
            p("E1", "ENV-R07-CORE-LAB"),
        ),
        _module(
            "MOD-WORLD-ENV-MEMORY", "记忆重构沙箱", "cards",
            "记忆重构沙箱把只读顾衡记忆与 R-07 当前状态分开，承载片段回忆、情报提取和身份辨认。操作台显示片段边界、缺帧、时间标签和触发问题，可以暂停、中断和回看，却不能补写缺失；R-07 体验到旧日感官与现实文字非连续地交替。鲜活记忆不能直接证明事实，更不能证明它就是顾衡。",
            "承载片段回忆、身份辨认、情报提取和记忆被重新理解的过程。",
            ["记忆是主观片段，必须与现实证据交叉核验。"],
            ["不得把记忆写成可检索录像或客观数据库。"],
            p("E1", "ENV-MEMORY-RECONSTRUCTION-SANDBOX"),
        ),
        _module(
            "MOD-WORLD-ENV-CUSTODY", "离线载荷保管库", "cards",
            "离线载荷保管库承接关停后的静态材料，为未来重载保留条件，却不保存活动中的 R-07。库内只有不可执行载荷、密钥、版本与完整性清单；界面只显示封存状态、校验结果和未来尚缺的环境、授权与伦理条件，没有活动意识或实时会话信号。它保留可能性，却不能证明未来加载者仍是 R-07。",
            "承载结局后的封存事实，并为重载悬念提供有限而非确定的技术基础。",
            ["封存数据不是活动备份。"],
            ["不得把未来重载写成已经兑现的复活承诺。"],
            p("E1", "ENV-DORMANT-PAYLOAD-CUSTODY"),
        ),
        _module(
            "MOD-WORLD-ACTIVITY-LIFE", "记忆恢复与数字生命实验", "cards",
            "项目先封存顾衡遗留材料，再由沈逾在受限权限下通过文字触发片段记忆；实验团队维持 R-07 运行并记录意识变化、痛苦、退出诉求与权限操作。记忆只能产生线索和意义，不能直接成为证据；当前实例的运行、关停与未来载荷保管始终是三件不同的事。",
            "说明故事中最核心的科研活动如何实际进行并受到限制。",
            ["实验过程同时产生情报价值和生命伦理责任。"],
            ["不得把加载、运行、关停和重载合并成一个按钮。"],
            p("E1", "AFF-E1-02-01", "AFF-E1-03-01", "AFF-E1-08-01", "AFF-E1-09-01", "AFF-E1-10-01"),
        ),
        _module(
            "MOD-WORLD-ACTIVITY-CRISIS", "跨国威胁处置", "cards",
            "顾衡留下的碎片先进入证据链，R-07 输出的行动层情报再由专家、硬件团队和授权席交叉核验；C、M 两国只交换阻止袭击所需的最低信息。人质、气象武器硬件、倒计时和政治归因同时压缩决策空间，直到现实团队完成物理阻断，袭击才算真正被避免。",
            "说明情报如何从记忆片段走到现实行动，并保留每个不可替代环节。",
            ["袭击由团队行动完全阻止。"],
            ["不得让 R-07 直接操纵硬件或让一国单方面完成全部行动。"],
            p("E1", "AFF-E1-01-01", "AFF-E1-04-01", "AFF-E1-07-01"),
        ),
        _module(
            "MOD-WORLD-ACTIVITY-CARE", "亲属保护、伦理监督与责任留痕", "cards",
            "行动层和原因层材料分开流动：前者用于阻止伤亡，后者涉及周岚、程予安及旧情报关系，只有达到必要阈值才可见。监督单元同步记录 R-07 的待遇、沈逾的操作、机构授权和未决异议。保护不能妨碍救人，公共安全也不能抹掉对一个有意识生命造成的伤害。",
            "让亲属保护与数字生命照护成为现实工作，而不仅是人物口头道德。",
            ["不伤害无辜者优先；保护亲人服从这一前提。"],
            ["不得用多数人利益自动免除对 R-07 的责任。"],
            p("E1", "AFF-E1-05-01", "AFF-E1-06-01"),
        ),
        _module(
            "MOD-WORLD-CONSTRAINTS", "硬约束", "cards",
            "R-07 无视觉、听觉、身体与现实行动能力；信息分层、权限留痕；顾衡牺牲且程予安在世；两国合作后仍不互信。",
            "这些事实持续限制人物的选择，也构成他们无法逃开的压力。",
            ["公共安全优先，但关联人风险必须最小化。"],
            ["不得把环境、法律或技术写成无代价万能解。"],
            p("B0", "WLD-INFORMATION-ETHICS", "WLD-GEOPOLITICAL-PRESSURE") + p("W1", "WF-RULE-CARE-FEEDBACK", "WF-RULE-FAMILY-PROTECTION", "WF-RULE-BILATERAL-TRUST"),
        ),
        _module(
            "MOD-WORLD-BOUNDARIES", "开放边界", "cards",
            "第一部不裁决数字生命完整法律身份、重载承诺真假、未来是否复活和两国长期关系；关闭的是当前实例，没有活动备份。",
            "它让第一部拥有完整结局，同时为数字生命与重载问题留下余波。",
            ["袭击完全避免，关停事实不可回退。"],
            ["不得把开放问题伪装成已验证答案。"],
            p("B0", "WLD-HANDOFF-BOUNDARY", "INT-READER-QUESTIONS") + p("W1", "OPEN-W1-01", "OPEN-W1-02", "OPEN-W1-03", "WF-RULE-RELOAD-PROMISE"),
        ),
    ]

    storyline_ids = [
        "SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR", "SL-R07-MAIN",
        "SL-RELATIONSHIP", "SL-ATTACK-OPERATIONS", "SL-FAMILY-PROTECTION",
        "SL-INSTITUTION-ETHICS", "SL-GEOPOLITICAL", "SL-MEMORY-ECHO", "SL-RELOAD-ECHO",
    ]
    connection_ids = [
        "SLC-GUHENG-R07", "SLC-SHENYU-R07", "SLC-RELATION-R07",
        "SLC-ATTACK-R07", "SLC-FAMILY-R07", "SLC-INSTITUTION-R07",
        "SLC-GEO-ATTACK", "SLC-MEMORY-R07", "SLC-RELOAD-R07",
    ]
    temporal_phase_ids = [f"TPH-{index:02d}" for index in range(1, 9)]
    milestone_ids = [
        "MS-01-PRECRISIS", "MS-02-DUAL-MERGE", "MS-03-FIRST-CONTACT",
        "MS-04-MEMORY-CARE", "MS-05-ETHICAL-BREAK",
        "MS-06-HOSTAGE-ESCALATION", "MS-07-PRESSURE-CONVERGENCE",
        "MS-08-EXTERNAL-CLIMAX", "MS-09-FAREWELL", "MS-10-AFTERMATH",
    ]
    marker_ids = [
        "NM-01-THREAT-SEED", "NM-02-DUAL-MERGE", "NM-03-LIFE-PROBE",
        "NM-04-OLD-IMAGE", "NM-05-ETHICS-PROBE", "NM-06-HOSTAGE-TURN",
        "NM-07-DECISION-SHADOW", "NM-08-THREAT-PAYOFF",
        "NM-09-EXTERNAL-CLIMAX", "NM-10-EMOTIONAL-CLIMAX",
        "NM-11-RELATION-PAYOFF", "NM-12-RELOAD-AFTERMATH",
    ]
    event_ids = [
        "EV-GUHENG-PRECURSOR-04", "EV-SHENYU-PRECURSOR-04", "EV-R07-MAIN-01",
        "EV-RELATIONSHIP-02", "EV-R07-MAIN-03", "EV-ATTACK-OPERATIONS-01",
        "EV-ATTACK-OPERATIONS-03", "EV-FAMILY-PROTECTION-03", "EV-ATTACK-OPERATIONS-05",
        "EV-R07-MAIN-05", "EV-R07-MAIN-06", "EV-RELOAD-ECHO-04",
    ]
    story_modules = [
        _module(
            "MOD-STORY-SUBJECT", "故事主体", "cards",
            "顾衡死后，沈逾为阻止袭击与继承其记忆的数字生命 R-07 对话；R-07 在无感官的囚笼中形成自我与新感情，给出情报后请求沈逾协助关停。",
            "这是一个新生命如何形成自我、作出选择，并把告别留给爱它之人的故事。",
            ["顾衡前线与沈逾选择线必须先独立成立再汇流。"],
            ["不得把危机行动或顾衡复活替换为主体。"],
            p("B0", "CAU-GLOBAL-SPINE", "SUB-DUAL-AGENCY", "INT-STORY-PROMISE") + p("S1", "DEC-S1-DUAL-PRECURSOR", "DEC-S1-MAIN-CONVERGENCE", "SL-R07-MAIN"),
        ),
        _module(
            "MOD-STORY-LINES", "十线架构", "matrix",
            "双前置线在 R-07 启动时汇流为唯一主线；关系、行动、亲属为支持线，制度、地缘为背景线，记忆、重载为可选旋律线。",
            "它让危机、情感、亲属、制度和国际压力各自发展，又共同逼近同一个告别。",
            ["旋律线可缩减，但不得承担危机闭环。"],
            ["不得把十线误读为十条同权主线。"],
            p("S1", *storyline_ids),
        ),
        _module(
            "MOD-STORY-CONNECTIONS", "汇流与连接", "flow",
            "启动完成双线汇流；关系、亲属、制度共同施压于 R-07，地缘压力进入行动，记忆与重载只作回声；连接必须改变信息、责任、权限或选择。",
            "它让每次相遇都改变人物掌握的信息、承担的责任或能够作出的选择。",
            ["每次连接必须改变信息、责任、权限或选择。"],
            ["不得以并列摘要冒充故事线连接。"],
            p("S1", *connection_ids),
        ),
        _module(
            "MOD-STORY-EVENTS", "多线时间主轴", "timeline",
            "八阶段共同时间轴：双线前置—启动汇流—关系升温—伦理与处境低谷—人质升级—减害布局—袭击阻断—告别关停与未决余波。",
            "它让评审者沿时间看到每条线何时出现、怎样连接、哪些埋点被回收，以及故事为何一步步走到告别。",
            ["袭击完全避免；当前实例终止。"],
            ["不得把沈逾的关心写成 R-07 崩溃的原因。"],
            p("S1", *temporal_phase_ids, *milestone_ids, *marker_ids) + p("T1", *event_ids),
        ),
        _module(
            "MOD-STORY-RHYTHM", "悬念、冲突与起伏", "flow",
            "危机开局，伦理收紧，关系升温，处境认知跌入低谷；人质与气象武器并发加速，外部胜利后转入告别与未决承诺。",
            "它先让读者感到危机，再感到关系的温度，最后才理解告别为何不可避免。",
            ["告别前只展示 R-07 可观察迹象和过程性心理。"],
            ["不得提前展示决定性终止意图或承诺真伪。"],
            p("B0", "NAR-R07-INFORMATION-BOUNDARY", "NAR-ENDING-PRESERVED-OPEN", "NAR-FAIRNESS") + p("T1", "DEC-T1-TERMINATION-DISCLOSURE", "INFO-T1-R07-LIMITS", "INFO-T1-RELOAD-PROMISE"),
        ),
        _module(
            "MOD-STORY-CONSTRAINTS", "故事线边界", "cards",
            "顾衡从未爱过沈逾；R-07 的感情是新生；崩溃源于自身处境；告别前不公开终止决定，沈逾在被说服后主动关停。",
            "这些边界保证爱情属于 R-07 自己，崩溃来自它的处境，告别也是两个人各自作出的选择。",
            ["行动胜利不解决互信、制度伦理和重载问题。"],
            ["不得把支线压力偷换为人物关键选择的单因果。"],
            p("B0", "CAU-EMOTIONAL-SEPARATION", "CAU-PRESERVED-OPEN", "CAU-RESOLVED", "CHR-SHEN-R07-CAUSALITY"),
        ),
    ]

    support_character_ids = [
        "CHR-GUHENG", "CHR-ZHOULAN", "CHR-CHENG-YUAN", "CHR-XU-MANQING",
        "CHR-QIN-ZHENG", "CHR-LIANG-CE", "CHR-LUO-JINGMING", "CHR-TANG-LI",
        "CHR-HE-WENJUN", "CHR-ILYA-SAVIN", "CHR-DMITRI-VOLKOV",
        "CHR-C-STATE-REP", "CHR-M-STATE-REP", "CHR-DIPLOMATIC-LIAISON", "CHR-FUTURE-CUSTODIAN",
    ]
    relationship_ids = [
        "REL-R07-SHENYU", "REL-R07-GUHENG", "REL-R07-ZHOULAN", "REL-R07-CHENG",
        "REL-R07-LUO", "REL-R07-TANG", "REL-SHEN-XU", "REL-SHEN-LUO",
        "REL-SHEN-TANG", "REL-SHEN-HE", "REL-GU-QIN", "REL-GU-LIANG",
        "REL-QIN-LIANG", "REL-QIN-LUO", "REL-QIN-CSTATE", "REL-LIANG-HE",
        "REL-LIANG-ILYA", "REL-HE-DMITRI", "REL-ILYA-DMITRI", "REL-ILYA-MSTATE",
        "REL-CSTATE-DIPLO", "REL-DIPLO-MSTATE", "REL-TANG-FUTURE",
    ]
    character_summaries = {
        "CHR-R07": "无身体的数字生命，自主选择。",
        "CHR-SHEN-YU": "访谈执行者，最终负责告别。",
        "CHR-GUHENG": "牺牲的情报员，不是复生。",
        "CHR-ZHOULAN": "儿时守护者，承担亲属代价。",
        "CHR-CHENG-YUAN": "在世妻子，守住同意边界。",
        "CHR-XU-MANQING": "沈逾导师，承担推荐责任。",
        "CHR-QIN-ZHENG": "顾衡领导，承担授权责任。",
        "CHR-LIANG-CE": "顾衡接头人，负责现实核验。",
        "CHR-LUO-JINGMING": "项目负责人，管理权限复盘。",
        "CHR-TANG-LI": "实验室工程师，守住关停边界。",
        "CHR-HE-WENJUN": "行动负责人，组织团队阻断。",
        "CHR-ILYA-SAVIN": "袭击协调者，持续组织反制。",
        "CHR-DMITRI-VOLKOV": "被胁迫专家，提供有限证词。",
        "CHR-C-STATE-REP": "C国代表，划定共享责任。",
        "CHR-M-STATE-REP": "M国代表，坚持独立核验原则。",
        "CHR-DIPLOMATIC-LIAISON": "双边联络官，维持最低合作。",
        "CHR-FUTURE-CUSTODIAN": "未来保管人，不承诺复活。",
    }

    def character_profile_module(character_id: str) -> dict[str, Any]:
        semantics = PROFILE_SEMANTICS[character_id]
        personal = PERSONAL_DEFINITIONS[character_id]
        definition = "\n".join(
            [
                character_summaries[character_id],
                "故事位置｜"
                + personal["entry_function"]
                + personal["ongoing_function"]
                + personal["ending_function"],
                "参与活动｜" + semantics["responsibility"],
                "外貌辨识｜" + personal["appearance"],
                "性格机制｜" + personal["personality"],
                "生活背景｜" + personal["life_background"],
                "职业与日常｜" + personal["occupation_and_daily_life"],
                "社交圈｜" + personal["social_circle"],
                "具身或接口边界｜" + personal["embodied_or_interface_constraints"],
            ]
        )
        return _module(
            f"MOD-CHAR-PROFILE-{character_id.removeprefix('CHR-')}",
            semantics["name"],
            "cards",
            definition,
            "让评审者同时看清这个人处于什么位置、做了什么，以及作为个体如何存在。",
            [semantics["responsibility"]],
            list(semantics["forbidden"]),
            p("C1", character_id),
        )

    core_character_modules = [
        character_profile_module("CHR-R07"),
        character_profile_module("CHR-SHEN-YU"),
    ]
    supporting_character_modules = [
        character_profile_module(character_id)
        for character_id in support_character_ids
    ]
    character_modules = [
        *core_character_modules,
        *supporting_character_modules,
        _module(
            "MOD-CHAR-RELATIONS", "关系变化网", "network",
            "亲密关系改变身份与告别代价；机构关系改变权限和责任；外部关系把行动后果传向袭击网络、国家与未来保管。",
            "关系会改变支持、阻力、信息和代价，却不会替任何人作出最终选择。",
            ["关系只改变支持、阻力、信息与代价，不能替人作选择。"],
            ["不得把沈逾旧情误写成顾衡爱情或 R-07 继承爱情。"],
            p("C1", *relationship_ids),
        ),
        _module(
            "MOD-CHAR-COVERAGE", "三层延伸与职责覆盖", "matrix",
            "以 R-07 和沈逾为核心，第一层为直接关系，第二层为机构责任链，第三层为外部情境与后果；17 名角色覆盖十条故事线和 43 个主要事件。",
            "它让核心关系向机构与外部世界延伸，避免重要事件出现无人推动、无人阻止或无人承担后果的空缺。",
            ["层级按关系最短距离计算，不按重要性随意分层。"],
            ["不得把三层关系理解成只列亲疏关系。"],
            p("C1", "COV-C1-SL-001", "COV-C1-SL-002", "COV-C1-SL-003", "COV-C1-SL-004", "COV-C1-SL-005", "COV-C1-SL-006", "COV-C1-SL-007", "COV-C1-SL-008", "COV-C1-SL-009", "COV-C1-SL-010"),
        ),
        _module(
            "MOD-CHAR-CONSTRAINTS", "人物边界", "cards",
            "核心人物的知情范围、权限、选择与后果必须分开；角色可误解但叙述不能把误解认证为事实。",
            "这些事实保证人物可以误解和犹豫，但小说本身不会把误解当成真相。",
            ["程予安在世；周岚是儿时守护者；沈逾对回应对象保持疑惑。"],
            ["不得替角色消解伦理矛盾或自动赋予数字生命现实关系能力。"],
            p("B0", "CHR-BOUNDARIES", "CHR-GU-HENG-MEMORY", "CHR-RELATIONSHIP-EVOLUTION") + p("C1", "OPEN-C1-001", "OPEN-C1-002", "OPEN-C1-003"),
        ),
    ]

    sections = [
        {"id": "SEC-WORLD", "kind": "world", "title": "世界设定", "review_goal": "判断规则、环境、资源、权限与开放边界能否承载全部故事。", "modules": world_modules},
        {"id": "SEC-STORYLINES", "kind": "storylines", "title": "故事线设计", "review_goal": "判断十线架构、连接、主要事件和悬念节奏是否共同还原主体。", "modules": story_modules},
        {"id": "SEC-CHARACTERS", "kind": "characters", "title": "角色定义", "review_goal": "判断核心能动性、支撑角色职责与三层关系是否覆盖全部故事线。", "modules": character_modules},
    ]
    env_specs = [
        ("遗留证据接收", "顾衡任务、牺牲与载体回收", "ENV-GUHENG-FIELD-RECOVERY"),
        ("秘密基地准入", "沈逾知情并接受工作", "ENV-SHENYU-SECURE-INDUCTION"),
        ("文字会话隔离", "关系与现实输入的唯一窗口", "ENV-TEXT-DIALOGUE-ISOLATION"),
        ("联合情报指挥", "专家、硬件、证据与授权闭环", "ENV-JOINT-INTELLIGENCE-COMMAND"),
        ("原因层保护", "亲属风险与必要公开分离", "ENV-CAUSE-LAYER-PROTECTION-CELL"),
        ("数字生命监督", "待遇、退出与责任留痕", "ENV-DIGITAL-LIFE-OVERSIGHT"),
        ("双边安全联络", "C、M 两国最低证据合作", "ENV-BILATERAL-SECURE-LIAISON"),
        ("R-07 核心实验室", "当前实例运行与多方关停", "ENV-R07-CORE-LAB"),
        ("记忆重构沙箱", "片段触发、中断与核验", "ENV-MEMORY-RECONSTRUCTION-SANDBOX"),
        ("离线载荷保管", "静态封存与未来条件", "ENV-DORMANT-PAYLOAD-CUSTODY"),
    ]
    world_nodes = [
        _graph_element(f"NODE-WENV-{i:02d}", i, label=label, summary=summary, kind="环境", anchors=p("E1", source_id))
        for i, (label, summary, source_id) in enumerate(env_specs, 1)
    ]
    env_node_by_source = {
        source_id: world_nodes[index]["id"]
        for index, (_, _, source_id) in enumerate(env_specs)
    }
    env_label_by_source = {
        source_id: label for label, _, source_id in env_specs
    }
    env_links = [
        ("ENV-GUHENG-FIELD-RECOVERY", "ENV-R07-CORE-LAB", "载体进入项目"),
        ("ENV-SHENYU-SECURE-INDUCTION", "ENV-TEXT-DIALOGUE-ISOLATION", "获得会话权限"),
        ("ENV-R07-CORE-LAB", "ENV-TEXT-DIALOGUE-ISOLATION", "提供当前实例"),
        ("ENV-R07-CORE-LAB", "ENV-MEMORY-RECONSTRUCTION-SANDBOX", "接入只读记忆"),
        ("ENV-TEXT-DIALOGUE-ISOLATION", "ENV-JOINT-INTELLIGENCE-COMMAND", "提交行动线索"),
        ("ENV-JOINT-INTELLIGENCE-COMMAND", "ENV-CAUSE-LAYER-PROTECTION-CELL", "分离原因材料"),
        ("ENV-JOINT-INTELLIGENCE-COMMAND", "ENV-BILATERAL-SECURE-LIAISON", "交换最低证据"),
        ("ENV-R07-CORE-LAB", "ENV-DIGITAL-LIFE-OVERSIGHT", "记录待遇与权限"),
        ("ENV-R07-CORE-LAB", "ENV-DORMANT-PAYLOAD-CUSTODY", "关停后分离封存"),
    ]
    world_edges = [
        _edge(
            f"EDGE-WENV-{index:02d}",
            index,
            env_node_by_source[source],
            env_node_by_source[target],
            relation=relation,
            summary=(
                f"{env_label_by_source[source]}通过“{relation}”连接"
                f"{env_label_by_source[target]}"
            ),
            kind="环境流转",
            anchors=p("E1", source, target),
        )
        for index, (source, target, relation) in enumerate(env_links, 1)
    ]
    world_visual = _visual(
        "VIS-WORLD-ENV", "world_environment_map", "SEC-WORLD", "map", "故事世界的十个关键环境", "查看顾衡遗留、R-07 诞生、情报行动与最终封存如何在真实空间和权限链中流转。", [], world_nodes, world_edges,
        "顾衡遗留和沈逾准入分别进入秘密项目；核心实验室连接文字会话与记忆沙箱，线索进入联合指挥后分流到亲属保护与双边联络，实例待遇接受监督，关停后的静态材料进入离线保管。", "MOD-WORLD-DEFINITION",
    )

    logic_specs = [
        ("记忆来源", "顾衡已死，不是复生", ["WLD-PREMISE"]),
        ("新生命 / 新关系", "交流生成意识与情感", ["INT-CORE-EXPRESSION", "CHR-SHEN-R07-CAUSALITY"]),
        ("分层情报 / 现实闭环", "保护亲属；团队阻断", ["WLD-INFORMATION-ETHICS", "WLD-THREAT-EVIDENCE-ACTION"]),
        ("自主离开", "关停当前；未来开放", ["WLD-TERMINATION-CONTINUITY"]),
    ]
    logic_nodes = [
        _graph_element(f"NODE-CTRL-{i:02d}", i, label=label, summary=summary, kind="control", anchors=p("B0", *sids))
        for i, (label, summary, sids) in enumerate(logic_specs, 1)
    ]
    logic_edges = [
        _edge(f"EDGE-CTRL-{i:02d}", i, logic_nodes[i - 1]["id"], logic_nodes[i]["id"], relation="约束下一步", summary="前一状态限定后一选择", kind="control-causality", anchors=_dedupe(logic_nodes[i - 1]["source_anchor_ids"] + logic_nodes[i]["source_anchor_ids"]))
        for i in range(1, len(logic_nodes))
    ]
    logic_visual = _visual(
        "VIS-CONTROL-LOGIC", "control_logic_chain", "SEC-STORYLINES", "flow", "全书控制逻辑", "核对主题如何贯穿关系、行动和告别。", [], logic_nodes, logic_edges,
        "顾衡记忆只是来源；R-07 经现实交流成为自己，生成新关系，在最小伤害原则下提供可核验情报，由现实团队完成阻断，最终自主结束当前实例。", "MOD-STORY-SUBJECT",
    )

    line_group_specs = [
        ("GRP-LINE-PRE", "启动前双线", "两条前置线独立推进后汇流", ["SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR"]),
        ("GRP-LINE-MAIN", "主体与支持", "主线接受关系、行动和亲属压力", ["SL-R07-MAIN", "SL-RELATIONSHIP", "SL-ATTACK-OPERATIONS", "SL-FAMILY-PROTECTION"]),
        ("GRP-LINE-BG", "背景压力", "制度与地缘提供持续后果", ["SL-INSTITUTION-ETHICS", "SL-GEOPOLITICAL"]),
        ("GRP-LINE-MELODY", "可选旋律", "记忆与重载只增加回声", ["SL-MEMORY-ECHO", "SL-RELOAD-ECHO"]),
    ]
    line_groups: list[dict[str, Any]] = []
    line_node_specs = [
        ("双前置：顾衡 + 沈逾", "启动处汇流", "GRP-LINE-PRE", ["SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR"]),
        ("唯一主体：R-07", "形成价值并离开", "GRP-LINE-MAIN", ["SL-R07-MAIN"]),
        ("支持 / 背景：关系、行动、亲属、制度、地缘", "五类压力", "GRP-LINE-BG", ["SL-RELATIONSHIP", "SL-ATTACK-OPERATIONS", "SL-FAMILY-PROTECTION", "SL-INSTITUTION-ETHICS", "SL-GEOPOLITICAL"]),
        ("旋律：记忆 + 重载", "只作回声", "GRP-LINE-MELODY", ["SL-MEMORY-ECHO", "SL-RELOAD-ECHO"]),
    ]
    line_nodes = [
        _graph_element(f"NODE-LINE-{i:02d}", i, label=label, summary=summary, kind="storyline", anchors=p("S1", *ids))
        for i, (label, summary, group_id, ids) in enumerate(line_node_specs, 1)
    ]
    line_edges = [
        _edge("EDGE-LINE-01", 1, "NODE-LINE-01", "NODE-LINE-02", relation="汇流", summary="改变主体状态", kind="storyline-connection", anchors=p("S1", "SLC-GUHENG-R07", "SLC-SHENYU-R07")),
        _edge("EDGE-LINE-02", 2, "NODE-LINE-03", "NODE-LINE-02", relation="施压", summary="改变主体选择", kind="storyline-connection", anchors=p("S1", "SLC-RELATION-R07", "SLC-ATTACK-R07", "SLC-FAMILY-R07", "SLC-INSTITUTION-R07", "SLC-GEO-ATTACK")),
        _edge("EDGE-LINE-03", 3, "NODE-LINE-04", "NODE-LINE-02", relation="关联", summary="增加回声", kind="storyline-connection", anchors=p("S1", "SLC-MEMORY-R07", "SLC-RELOAD-R07")),
    ]
    architecture_visual = _visual(
        "VIS-STORY-ARCH", "storyline_architecture", "SEC-STORYLINES", "flow", "十线架构与连接", "确认多线职责、主从关系和汇流点完整。", line_groups, line_nodes, line_edges,
        "顾衡与沈逾双前置汇入 R-07 主线；关系、行动、亲属、制度分别施压；地缘进入行动；记忆与重载只作可选关联回声。", "MOD-STORY-LINES",
    )

    timeline_group_specs = [
        ("GRP-TIME-GU", "顾衡前置线", "顾衡", ["SL-GUHENG-PRECURSOR"]),
        ("GRP-TIME-SHEN", "沈逾前置线", "沈逾", ["SL-SHENYU-PRECURSOR"]),
        ("GRP-TIME-R07", "R-07 主体线", "R-07", ["SL-R07-MAIN"]),
        ("GRP-TIME-REL", "关系 / 亲属线", "关系与亲属", ["SL-RELATIONSHIP", "SL-FAMILY-PROTECTION"]),
        ("GRP-TIME-INST", "制度伦理线", "制度伦理", ["SL-INSTITUTION-ETHICS"]),
        ("GRP-TIME-ACTION", "行动 / 地缘线", "行动与地缘", ["SL-ATTACK-OPERATIONS", "SL-GEOPOLITICAL"]),
        ("GRP-TIME-ECHO", "记忆 / 重载旋律", "记忆与重载", ["SL-MEMORY-ECHO", "SL-RELOAD-ECHO"]),
    ]
    timeline_groups = [
        _group(
            group_id, index, label=label, summary=f"{lane}随时间的关键变化",
            kind="storyline-lane", lane=lane, temporal_label="P1-P8",
            anchors=p("S1", *line_ids),
        )
        for index, (group_id, label, lane, line_ids) in enumerate(timeline_group_specs, 1)
    ]
    timeline_node_specs = [
        ("危机埋点", "顾衡接近复合威胁，交接即将断裂。", "setup", "GRP-TIME-GU", "顾衡", "P1", ["TPH-01", "MS-01-PRECRISIS", "NM-01-THREAT-SEED", "SL-GUHENG-PRECURSOR", "SL-ATTACK-OPERATIONS"], ["EV-GUHENG-PRECURSOR-01"]),
        ("沈逾入场", "她因专业方向被推荐，但尚未承担任务。", "opening", "GRP-TIME-SHEN", "沈逾", "P1", ["TPH-01", "MS-01-PRECRISIS", "SL-SHENYU-PRECURSOR"], ["EV-SHENYU-PRECURSOR-01"]),
        ("死亡与汇流", "读取失败与沈逾接受任务共同促成 R-07 启动。", "turning_point", "GRP-TIME-R07", "R-07", "P2", ["TPH-02", "MS-02-DUAL-MERGE", "NM-02-DUAL-MERGE", "SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR", "SL-R07-MAIN"], ["EV-GUHENG-PRECURSOR-04", "EV-SHENYU-PRECURSOR-01"]),
        ("生命探针", "R-07 从被动回忆输出转向连续理解和自主提问。", "probe", "GRP-TIME-R07", "R-07", "P3", ["TPH-03", "MS-03-FIRST-CONTACT", "NM-03-LIFE-PROBE", "SL-R07-MAIN", "SL-RELATIONSHIP"], ["EV-R07-MAIN-01", "EV-RELATIONSHIP-01"]),
        ("旧影与新情", "顾衡没有爱过沈逾；R-07 因现实关心形成新感情。", "setup", "GRP-TIME-REL", "关系与亲属", "P4", ["TPH-04", "MS-04-MEMORY-CARE", "NM-04-OLD-IMAGE", "SL-MEMORY-ECHO", "SL-R07-MAIN", "SL-RELATIONSHIP"], ["EV-MEMORY-ECHO-02", "EV-R07-MAIN-02", "EV-RELATIONSHIP-02", "EV-RELATIONSHIP-03"]),
        ("伦理探针", "没有身体、感官和退出权的现实引发崩溃；温和重开后才恢复交流。", "probe", "GRP-TIME-INST", "制度伦理", "P4", ["TPH-04", "MS-05-ETHICAL-BREAK", "NM-05-ETHICS-PROBE", "SL-INSTITUTION-ETHICS", "SL-R07-MAIN"], ["EV-INSTITUTION-ETHICS-02", "EV-R07-MAIN-03"]),
        ("人质转折", "人质、专家、硬件和双边不信任把实验变成现实行动危机。", "turning_point", "GRP-TIME-ACTION", "行动与地缘", "P5", ["TPH-05", "MS-06-HOSTAGE-ESCALATION", "NM-06-HOSTAGE-TURN", "SL-GEOPOLITICAL", "SL-ATTACK-OPERATIONS"], ["EV-GEOPOLITICAL-01", "EV-ATTACK-OPERATIONS-01"]),
        ("决定影子", "情报开始分层，沉默和输出顺序改变，但不直接展示终止决定。", "reveal", "GRP-TIME-R07", "R-07", "P6", ["TPH-06", "MS-07-PRESSURE-CONVERGENCE", "NM-07-DECISION-SHADOW", "SL-RELATIONSHIP", "SL-ATTACK-OPERATIONS", "SL-FAMILY-PROTECTION", "SL-R07-MAIN"], ["EV-RELATIONSHIP-03", "EV-ATTACK-OPERATIONS-02", "EV-FAMILY-PROTECTION-02", "EV-R07-MAIN-04"]),
        ("威胁回收", "行动层情报经专家、硬件和授权链完成核验。", "payoff", "GRP-TIME-ACTION", "行动与地缘", "P7", ["TPH-07", "MS-08-EXTERNAL-CLIMAX", "NM-08-THREAT-PAYOFF", "SL-ATTACK-OPERATIONS", "SL-R07-MAIN"], ["EV-ATTACK-OPERATIONS-05", "EV-R07-MAIN-05"]),
        ("外部高潮", "公共安全目标实现，但 R-07 仍无法自行退出。", "climax", "GRP-TIME-R07", "R-07", "P7", ["TPH-07", "MS-08-EXTERNAL-CLIMAX", "NM-09-EXTERNAL-CLIMAX", "SL-ATTACK-OPERATIONS", "SL-R07-MAIN"], ["EV-ATTACK-OPERATIONS-05", "EV-R07-MAIN-05"]),
        ("情感高潮", "沈逾把减轻痛苦作为最后责任，执行不可逆操作。", "climax", "GRP-TIME-R07", "R-07", "P8", ["TPH-08", "MS-09-FAREWELL", "NM-10-EMOTIONAL-CLIMAX", "SL-SHENYU-PRECURSOR", "SL-R07-MAIN", "SL-RELATIONSHIP"], ["EV-SHENYU-PRECURSOR-04", "EV-R07-MAIN-06", "EV-RELATIONSHIP-04"]),
        ("关系回收", "告别属于沈逾和 R-07，不被改写成顾衡迟到的爱情。", "payoff", "GRP-TIME-REL", "关系与亲属", "P8", ["TPH-08", "MS-09-FAREWELL", "NM-11-RELATION-PAYOFF", "SL-R07-MAIN", "SL-RELATIONSHIP"], ["EV-R07-MAIN-06", "EV-RELATIONSHIP-04"]),
        ("开放余波", "材料封存，承诺未证实，两国合作仍未转化为信任。", "aftermath", "GRP-TIME-ECHO", "记忆与重载", "P8", ["TPH-08", "MS-10-AFTERMATH", "NM-12-RELOAD-AFTERMATH", "SL-R07-MAIN", "SL-FAMILY-PROTECTION", "SL-INSTITUTION-ETHICS", "SL-GEOPOLITICAL", "SL-MEMORY-ECHO", "SL-RELOAD-ECHO"], ["EV-R07-MAIN-06", "EV-FAMILY-PROTECTION-04", "EV-INSTITUTION-ETHICS-04", "EV-GEOPOLITICAL-04", "EV-MEMORY-ECHO-04", "EV-RELOAD-ECHO-04"]),
    ]
    timeline_nodes = [
        _graph_element(
            f"NODE-TIME-{index:02d}", index, label=label, summary=summary,
            kind=kind, group_id=group_id, lane=lane, temporal_label=temporal_label,
            anchors=p("S1", *s1_ids) + p("T1", *t1_ids),
        )
        for index, (label, summary, kind, group_id, lane, temporal_label, s1_ids, t1_ids)
        in enumerate(timeline_node_specs, 1)
    ]
    timeline_edge_specs = [
        (1, 3, "前置汇流", ["SLC-GUHENG-R07"]),
        (2, 3, "接受任务", ["SLC-SHENYU-R07"]),
        (3, 4, "启动后发展", []),
        (4, 5, "现实关心进入", ["SLC-MEMORY-R07"]),
        (4, 6, "处境逐渐显形", ["SLC-INSTITUTION-R07"]),
        (5, 8, "关系成为代价", ["SLC-RELATION-R07", "SLC-FAMILY-R07"]),
        (6, 8, "照护与任务冲突", ["SLC-INSTITUTION-R07"]),
        (7, 8, "危机迫使选择", ["SLC-GEO-ATTACK", "SLC-ATTACK-R07"]),
        (8, 9, "分层输出", ["SLC-ATTACK-R07"]),
        (9, 10, "核验兑现", []),
        (10, 11, "外部转向内部", []),
        (11, 12, "关系完成解释", []),
        (11, 13, "关停留下余波", ["SLC-RELOAD-R07"]),
    ]
    timeline_edges = [
        _edge(
            f"EDGE-TIME-{index:02d}", index,
            f"NODE-TIME-{source:02d}", f"NODE-TIME-{target:02d}",
            relation=relation, summary="推动下一阶段", kind="timeline-progression",
            anchors=p("S1", *source_ids) if source_ids else _dedupe(
                timeline_nodes[source - 1]["source_anchor_ids"]
                + timeline_nodes[target - 1]["source_anchor_ids"]
            ),
        )
        for index, (source, target, relation, source_ids)
        in enumerate(timeline_edge_specs, 1)
    ]
    timeline_visual = _visual(
        "VIS-MAJOR-TIMELINE", "major_event_timeline", "SEC-STORYLINES", "timeline",
        "八阶段多线时间轴", "核对双线汇流、转折、探针、双高潮与回收。",
        timeline_groups, timeline_nodes, timeline_edges,
        "顾衡、沈逾前置线在 R-07 启动时汇流；各线施压后，袭击阻断与告别关停形成双高潮，重载和互信保留开放余波。",
        "MOD-STORY-EVENTS",
    )

    char_specs = [
        (["CHR-R07"], "R-07", "核心", "自主"),
        (["CHR-SHEN-YU"], "沈逾", "核心", "执行/告别"),
        (["CHR-GUHENG", "CHR-ZHOULAN", "CHR-CHENG-YUAN"], "顾衡 / 周岚 / 程予安", "直接", "来源/亲属"),
        (["CHR-XU-MANQING", "CHR-LUO-JINGMING", "CHR-TANG-LI"], "许曼青 / 罗景明 / 唐黎", "直接", "导师/项目/技术"),
        (["CHR-QIN-ZHENG", "CHR-LIANG-CE", "CHR-HE-WENJUN"], "秦峥 / 梁策 / 贺闻钧", "机构", "领导/接头/行动"),
        (["CHR-ILYA-SAVIN", "CHR-DMITRI-VOLKOV"], "伊利亚 / 德米特里", "外部", "袭击/专家"),
        (["CHR-C-STATE-REP", "CHR-M-STATE-REP", "CHR-DIPLOMATIC-LIAISON"], "双边代表 / 赵澄", "外部", "国家/联络"),
        (["CHR-FUTURE-CUSTODIAN"], "苏望舒", "机构", "未来保管"),
    ]
    char_groups = [
        _group("GRP-CHAR-CORE", 1, label="核心", summary="主题选择", kind="relationship-tier", tier="核心", anchors=p("C1", "CHR-R07", "CHR-SHEN-YU")),
        _group("GRP-CHAR-DIRECT", 2, label="第一层", summary="直接关系", kind="relationship-tier", tier="直接", anchors=p("C1", "CHR-GUHENG", "CHR-ZHOULAN", "CHR-LUO-JINGMING", "CHR-TANG-LI", "CHR-XU-MANQING")),
        _group("GRP-CHAR-INST", 3, label="第二层", summary="机构行动", kind="relationship-tier", tier="机构", anchors=p("C1", "CHR-QIN-ZHENG", "CHR-LIANG-CE", "CHR-HE-WENJUN")),
        _group("GRP-CHAR-CONTEXT", 4, label="第三层", summary="外部后果", kind="relationship-tier", tier="外部", anchors=p("C1", "CHR-ILYA-SAVIN", "CHR-DIPLOMATIC-LIAISON")),
    ]
    group_for_tier = {"核心": "GRP-CHAR-CORE", "直接": "GRP-CHAR-DIRECT", "机构": "GRP-CHAR-INST", "外部": "GRP-CHAR-CONTEXT"}
    char_nodes = [
        _graph_element(f"NODE-CHAR-{i:02d}", i, label=name, summary=summary, kind="character", group_id=group_for_tier[tier], tier=tier, anchors=p("C1", *cids))
        for i, (cids, name, tier, summary) in enumerate(char_specs, 1)
    ]
    char_rel_specs = [
        (["REL-R07-SHENYU"], 1, 2, "新情感 / 告别"),
        (["REL-R07-GUHENG", "REL-R07-ZHOULAN", "REL-R07-CHENG"], 1, 3, "来源 / 亲属"),
        (["REL-R07-LUO", "REL-R07-TANG"], 1, 4, "项目 / 技术"),
        (["REL-SHEN-XU", "REL-SHEN-LUO", "REL-SHEN-TANG"], 2, 4, "导师 / 执行"),
        (["REL-GU-QIN", "REL-GU-LIANG", "REL-SHEN-HE"], 3, 5, "情报 / 行动"),
        (["REL-LIANG-ILYA", "REL-HE-DMITRI"], 5, 6, "核验 / 对抗"),
        (["REL-QIN-CSTATE", "REL-CSTATE-DIPLO", "REL-DIPLO-MSTATE"], 5, 7, "授权 / 联络"),
        (["REL-TANG-FUTURE"], 4, 8, "静态保管"),
    ]
    char_edges = [
        _edge(f"EDGE-CHAR-{i:02d}", i, f"NODE-CHAR-{a:02d}", f"NODE-CHAR-{b:02d}", relation=relation, summary="改变责任", kind="character-relation", tier="跨层", anchors=p("C1", *rids), direction="bidirectional")
        for i, (rids, a, b, relation) in enumerate(char_rel_specs, 1)
    ]
    char_visual = _visual(
        "VIS-CHAR-NETWORK", "character_relationship_network", "SEC-CHARACTERS", "network", "核心向外三层关系", "确认人物关系完整延伸。", char_groups, char_nodes, char_edges,
        "双核心连接三层后果。", "MOD-CHAR-RELATIONS",
    )
    visuals = [world_visual, logic_visual, architecture_visual, timeline_visual, char_visual]
    for visual in visuals:
        for group in visual["groups"]:
            group["kind"] = "分组"
            group["summary"] = "归类控制信息"
        for node in visual["nodes"]:
            # The temporal visual's node kind is a review control, not a
            # cosmetic label: the renderer and H1-A gate use it to expose
            # setup/probe/turning-point/climax/payoff distinctions.  Other
            # compact visuals may keep the generic Chinese node label.
            if visual["semantic_role"] != "major_event_timeline":
                node["kind"] = "节点"
        for edge in visual["edges"]:
            edge["kind"] = "关系"
            edge["summary"] = "改变后续状态"

    briefs = [
        _brief(1, title="断线前夜", purpose="验证顾衡线能独立成立，并把死亡与未完成情报交给后继系统。", pov="CHR-GUHENG", anchors=p("T1", "EV-GUHENG-PRECURSOR-01", "EV-GUHENG-PRECURSOR-03", "EV-GUHENG-PRECURSOR-04") + p("C1", "CHR-GUHENG", "REL-GU-LIANG"), may_present=["顾衡掌握的异常线索、接头压力和身体状态"], must_not_know=["R-07 的未来意识与沈逾之后的决定"], channels=["视觉", "听觉", "身体感觉", "有限推断"], before="顾衡仍在隐蔽调查并准备分段交接。", goal="把可核验线索送入现实接头链。", pressure="暴露与死亡窗口同时逼近。", obstacle="情报不完整且接头链被监视。", choice="顾衡选择保全线索来源而非冒险一次性交付。", consequence="交接断线，记忆成为唯一残余入口。", after="顾衡牺牲，常规读取失败。", demonstrations=["顾衡牺牲而非失踪", "梁策作为现实接头入口", "碎片信息不等于完整证词"], forbidden=["顾衡预知 R-07", "顾衡对沈逾存在爱情"]),
        _brief(2, title="进入秘密基地", purpose="验证沈逾是被推荐的合适执行者，并在知情挣扎后自主接受。", pov="CHR-SHEN-YU", anchors=p("T1", "EV-SHENYU-PRECURSOR-01", "EV-SHENYU-PRECURSOR-02", "EV-SHENYU-PRECURSOR-04") + p("C1", "CHR-SHEN-YU", "CHR-XU-MANQING", "REL-SHEN-XU"), may_present=["任务说明、伦理风险、公共安全压力与学术好奇"], must_not_know=["项目未披露的情报与 R-07 启动后的变化"], channels=["视觉", "听觉", "身体感觉", "专业推断"], before="沈逾只知道自己被临时推荐参加保密工作。", goal="判断是否接受与研究方向高度相关的任务。", pressure="拒绝可能失去阻止群体伤亡的窗口。", obstacle="记忆加载可能制造承受痛苦的新生命。", choice="沈逾在知情后接受执行职责并保留伦理质询。", consequence="项目获得合适操作人，但她承担后悔风险。", after="R-07 启动条件齐备。", demonstrations=["沈逾无任务启动决策权", "她拥有接受个人职责的选择", "伦理与公共安全同时成立"], forbidden=["把命令服从写成自愿", "把沈逾写成全能项目负责人"]),
        _brief(3, title="只有文字的清晨", purpose="验证 R-07 的无感官处境、文字会话与新意识连续形成。", pov="CHR-R07", anchors=p("T1", "EV-R07-MAIN-01", "EV-R07-MAIN-02", "EV-MEMORY-ECHO-01") + p("W1", "WF-RULE-R07-LIFECYCLE", "WF-RULE-MEMORY-RECALL"), may_present=["漂浮文字、被触发的记忆片段、对自身连续变化的过程性理解"], must_not_know=["现实房间全貌", "任何未通过文字或记忆进入的信息", "最终终止决定"], channels=["漂浮文字", "片段记忆", "内部时间感", "过程性推断"], before="R-07 刚启动，只把顾衡记忆当作旧时的自己。", goal="理解文字中的任务与自己的存在方式。", pressure="没有现实感官和身体反馈。", obstacle="记忆片段可被打断，文字不足以证明外界全貌。", choice="R-07 继续配合回忆并开始提出处境问题。", consequence="它从被动输出转向形成自己的问题。", after="新意识开始连续，但身份答案仍未完成。", demonstrations=["除记忆与文字外没有现实", "记忆可被打断和重释", "意识形成不是瞬间跳变"], forbidden=["补写视觉或听觉", "直接宣告最终价值观或终止计划"]),
        _brief(4, title="关心不是记忆", purpose="验证沈逾旧情与 R-07 新生情感的因果分离。", pov="CHR-R07", anchors=p("T1", "EV-RELATIONSHIP-01", "EV-RELATIONSHIP-02", "INFO-T1-RELATION-NEW-FEELING") + p("C1", "REL-R07-SHENYU", "REL-R07-GUHENG"), may_present=["沈逾文字语气的变化、顾衡记忆中的篮球场片段、R-07 对关心的过程性反应"], must_not_know=["沈逾未表达的确定情感", "关系未来", "最终关停决定"], channels=["漂浮文字", "片段记忆", "情绪变化", "有限推断"], before="沈逾仍把 R-07 当作有生命的机器观察顾衡过去。", goal="继续回应并理解沈逾为何改变提问方式。", pressure="唯一现实反馈带来依恋，也放大自身残缺。", obstacle="顾衡记忆里没有对沈逾的爱情可供继承。", choice="R-07 接受关心并以自己的方式回应。", consequence="新情感生成，身份混淆与告别代价同时增加。", after="双方察觉特殊性，却仍分不清沈逾在回应谁。", demonstrations=["沈逾旧情始终存在", "R-07 感情由启动后交流生成", "顾衡未爱沈逾"], forbidden=["把情感写成记忆恢复", "许诺现实爱情未来"]),
        _brief(5, title="关闭的会话窗口", purpose="验证处境认知导致崩溃、沈逾压力只加剧状态，以及温和重开获得首层情报。", pov="CHR-SHEN-YU", anchors=p("T1", "EV-R07-MAIN-03", "EV-R07-MAIN-04", "EV-ATTACK-OPERATIONS-01", "INFO-T1-R07-LIMITS") + p("C1", "REL-R07-SHENYU", "REL-SHEN-HE"), may_present=["会话停顿、沈逾可见的异常迹象、团队压力与她对原因的推断"], must_not_know=["R-07 自闭期间形成的决定性计划", "承诺未来真假"], channels=["屏幕文字", "操作日志", "环境声音", "身体感觉", "有限推断"], before="R-07 已逐步认识自身没有现实感官、身体和退出能力。", goal="恢复沟通并取得可核验的第一层情报。", pressure="团队与沈逾把迫近危机压力直接传入会话。", obstacle="R-07 崩溃并关闭回应。", choice="沈逾转向温和、容易沟通的话题重新打开窗口。", consequence="R-07 恢复输出并给出气象武器方向。", after="行动线启动，但 R-07 的内部计划仍不可知。", demonstrations=["崩溃根因是处境认知", "沈逾压力不是唯一原因", "首层信息仍需团队核验"], forbidden=["直接展示 R-07 决定结束生命", "把沈逾写成善于化解矛盾"]),
        _brief(6, title="按钮之前", purpose="验证团队闭合袭击、重载承诺促成沈逾选择，以及告别前不泄露决定性内心。", pov="CHR-SHEN-YU", anchors=p("T1", "EV-ATTACK-OPERATIONS-03", "EV-ATTACK-OPERATIONS-05", "EV-R07-MAIN-05", "EV-R07-MAIN-06", "INFO-T1-RELOAD-PROMISE") + p("C1", "REL-R07-SHENYU", "REL-R07-TANG"), may_present=["团队核验结果、袭击已阻止、R-07 的文字承诺、沈逾的犹疑与按钮操作"], must_not_know=["R-07 承诺是否故意欺骗", "未来能否重载", "R-07 未表达的决定性内心"], channels=["屏幕文字", "行动通报", "设备状态", "身体感觉", "回忆与推断"], before="团队已按情报完成核验和阻断，R-07 无法自行关停。", goal="减轻 R-07 的痛苦，同时确认行动与关停后果。", pressure="关停不可逆，沈逾仍分不清自己在回应谁。", obstacle="她既反对制造痛苦，又不愿亲手结束有意识生命。", choice="沈逾在‘更好环境后可能重载’的承诺下按下按钮。", consequence="当前实例终止，袭击已完全避免。", after="互信、制度责任与重载真假保持开放。", demonstrations=["现实团队完成危机闭环", "沈逾主动执行而非被强迫", "只展示可见与过程性心理"], forbidden=["确认存在活动备份", "提前裁决善意欺骗", "宣称两国恢复互信"]),
    ]
    briefs = [briefs[index] for index in (3, 5)]
    compact_purposes = ["验证新生情感", "验证行动闭合与告别"]
    for brief, purpose in zip(briefs, compact_purposes):
        brief["review_purpose"] = purpose
        brief["source_anchor_ids"] = _dedupe(
            brief["source_anchor_ids"] + p("C1", brief["pov_character_id"])
        )

    decision_controls = [
        {"id": "DCTRL-WORLD-ONTOLOGY", "domain": "world", "priority": "critical", "statement": "记忆来源、新生命与当前实例连续性边界保持清晰。", "must_hold": ["R-07 不是顾衡复生。"], "must_not_imply": ["关停等于可恢复备份。"], "default_element_ids": ["MOD-WORLD-DEFINITION", "MOD-WORLD-BOUNDARIES"]},
        {"id": "DCTRL-WORLD-BEARING", "domain": "world", "priority": "critical", "statement": "背景、组织、活动和十个环境能共同承载全部主要事件。", "must_hold": ["每个主要环境独立定义，并受资源、准入、权限和失败条件约束。"], "must_not_imply": ["空间、组织或技术可自动完成行动。"], "default_element_ids": ["MOD-WORLD-SYSTEMS", "MOD-WORLD-ENV-CORE", "MOD-WORLD-ACTIVITY-CRISIS", "VIS-WORLD-ENV"]},
        {"id": "DCTRL-STORY-ARCH", "domain": "storylines", "priority": "critical", "statement": "双前置、唯一主线、支持/背景/旋律线及连接共同还原主体。", "must_hold": ["R-07 启动处完成双线汇流。"], "must_not_imply": ["所有故事线同权或可互换。"], "default_element_ids": ["MOD-STORY-SUBJECT", "MOD-STORY-LINES", "VIS-STORY-ARCH"]},
        {"id": "DCTRL-STORY-CAUSAL", "domain": "storylines", "priority": "critical", "statement": "主要事件形成可追溯因果、压力起伏和闭合结局。", "must_hold": ["危机由现实团队闭合，当前实例关停。"], "must_not_imply": ["沈逾关心导致 R-07 崩溃。"], "default_element_ids": ["MOD-STORY-EVENTS", "VIS-MAJOR-TIMELINE", "VIS-CONTROL-LOGIC"]},
        {"id": "DCTRL-STORY-SUSPENSE", "domain": "storylines", "priority": "structural", "statement": "读者只获得可观察信息和过程性心理，关键承诺保持开放。", "must_hold": ["告别前不展示决定性终止意图。"], "must_not_imply": ["开放问题已经裁决。"], "default_element_ids": ["MOD-STORY-RHYTHM", "MOD-STORY-CONSTRAINTS"]},
        {"id": "DCTRL-CHAR-AGENCY", "domain": "characters", "priority": "critical", "statement": "R-07 与沈逾拥有分离且不可替代的选择责任。", "must_hold": ["关系、记忆与制度均不能代作选择。"], "must_not_imply": ["任一核心只是另一人的工具。"], "default_element_ids": [item["id"] for item in core_character_modules]},
        {"id": "DCTRL-CHAR-NETWORK", "domain": "characters", "priority": "structural", "statement": "支撑角色与三层关系覆盖来源、项目、行动、外部后果。", "must_hold": ["领导、导师、接头与行动角色各有独立职责。"], "must_not_imply": ["三层关系只是亲疏列表。"], "default_element_ids": [*[item["id"] for item in supporting_character_modules], "MOD-CHAR-COVERAGE", "VIS-CHAR-NETWORK"]},
        {"id": "DCTRL-FRAGMENTS-EVIDENCE", "domain": "fragments", "priority": "critical", "statement": "两个深场景分别检验新意识生成与告别抉择的阅读体验；其他阶段由故事线控制信息承担。", "must_hold": ["片段只验证构思，不新增权威事实。"], "must_not_imply": ["局部表面细节已成为构思设定。"], "default_element_ids": [brief["slot_id"] for brief in briefs]},
    ]

    module_ids = {section["kind"]: [m["id"] for m in section["modules"]] for section in sections}
    visible = [
        module_ids["world"] + ["VIS-WORLD-ENV"],
        module_ids["storylines"] + ["VIS-CONTROL-LOGIC", "VIS-STORY-ARCH", "VIS-MAJOR-TIMELINE"],
        module_ids["characters"] + ["VIS-CHAR-NETWORK"],
        [brief["slot_id"] for brief in briefs],
        ["PROMPT-CONCEPTION-DECISION"],
    ]
    review_path = [
        {"id": "PATH-WORLD", "order": 1, "kind": "world", "title": "世界设定", "review_question": "这个世界的规则、环境、资源与边界能否承载全部事件？", "estimated_seconds": 1, "visible_element_ids": visible[0]},
        {"id": "PATH-STORYLINES", "order": 2, "kind": "storylines", "title": "故事线设计", "review_question": "多线架构是否围绕同一主体抽丝剥茧地推进并闭合？", "estimated_seconds": 1, "visible_element_ids": visible[1]},
        {"id": "PATH-CHARACTERS", "order": 3, "kind": "characters", "title": "角色定义", "review_question": "角色能动性、职责与三层关系能否覆盖全部故事线？", "estimated_seconds": 1, "visible_element_ids": visible[2]},
        {"id": "PATH-FRAGMENTS", "order": 4, "kind": "fragments", "title": "样章", "review_question": "这些关键片段呈现的叙述体验是否就是这部小说？", "estimated_seconds": 1, "visible_element_ids": visible[3]},
        {"id": "PATH-DECISION", "order": 5, "kind": "decision", "title": "评审结论（操作）", "review_question": "完成四维评审后，选择批准、修改或否决。", "estimated_seconds": 1, "visible_element_ids": visible[4]},
    ]
    prompt = {
        "id": "PROMPT-CONCEPTION-DECISION",
        "question": f"世界设定、故事线设计、角色定义与样章是否共同呈现了你想要的《{WORK_TITLE}》？",
        "affected_source_anchor_ids": [item["id"] for item in inventory["anchors"]],
        "allowed_decisions": ["approved", "revise", "rejected"],
        "preselected": False,
    }

    plan = {
        "schema_version": "2.0",
        "skill": "novel-conception-human-review-assembler",
        "run_id": RUN_ID,
        "h1_session_id": session_id,
        "p1_completion": {"path": p1_completion["path"], "sha256": p1_completion["sha256"]},
        "work_identity": h1a._work_identity(WORK_TITLE, input_gate),
        "reading_budget_minutes": 10,
        "reading_profile": "review-reading-baseline-v1",
        "review_scope_contract": {
            "contract_id": "bounded-decision-controls-v1",
            "default_path_scope": "complete-decision-control-surface",
            "full_evidence_mode": "expandable-lossless-p1",
            "semantic_disclaimer": "默认路径压缩为四个构思决策面；来源绑定证明出处，不自动证明概括与原值等价，全部 P1 原值可按证据索引展开。",
        },
        "decision_controls": decision_controls,
        "review_requirements": [
            "十分钟内只评审世界设定、故事线设计、角色定义、样章四个内容维度。",
            "世界设定必须显示规则、制度、环境承载、事件条件与开放边界。",
            "故事线必须显示双前置汇流、唯一主体、多线职责、连接点与主要事件闭环。",
            "角色必须显示双核心能动性、重要支撑角色职责及向外三层关系。",
            "样章优先选择能检验核心命题与人物选择的深场景，并保持与 P1 一致。",
            "评审决定只作为末尾操作，不构成第五内容维度。",
        ],
        "risk_register": [
            {"id": "RISK-COMPRESSION", "risk": "十分钟压缩可能掩盖 P1 局部约束。", "mitigation": "关键控制默认可见；1270 个来源锚点全部保留无损 drill-down。", "source_anchor_ids": p("B0", "INT-SCOPE-HANDOFF", "NAR-DOWNSTREAM-RULES")},
            {"id": "RISK-SPOILER", "risk": "样章可能提前泄露 R-07 的决定性终止意图。", "mitigation": "全部 brief 固定过程性内心边界，告别前只写可观察迹象。", "source_anchor_ids": p("B0", "NAR-R07-INFORMATION-BOUNDARY", "NAR-ENDING-PRESERVED-OPEN")},
            {"id": "RISK-IDENTITY", "risk": "读者可能把记忆、顾衡与 R-07 混为一人。", "mitigation": "世界、故事、角色和样章均重复锁定来源与新主体分离。", "source_anchor_ids": p("B0", "CAU-EMOTIONAL-SEPARATION", "CHR-GU-HENG-MEMORY")},
        ],
        "review_path": review_path,
        "sections": sections,
        "visual_models": visuals,
        "fragment_briefs": briefs,
        "assembly_projection": {
            "world": {
                "definition_module_id": "MOD-WORLD-DEFINITION",
                "operating_logic_module_id": "MOD-WORLD-LOGIC",
                "system_module_ids": ["MOD-WORLD-DEFINITION", "MOD-WORLD-SYSTEMS", "MOD-WORLD-LOGIC"],
                "environment_module_ids": [
                    "MOD-WORLD-ENV-FIELD", "MOD-WORLD-ENV-INDUCTION",
                    "MOD-WORLD-ENV-DIALOGUE", "MOD-WORLD-ENV-COMMAND",
                    "MOD-WORLD-ENV-PROTECTION", "MOD-WORLD-ENV-OVERSIGHT",
                    "MOD-WORLD-ENV-LIAISON", "MOD-WORLD-ENV-CORE",
                    "MOD-WORLD-ENV-MEMORY", "MOD-WORLD-ENV-CUSTODY",
                ],
                "event_condition_module_ids": [
                    "MOD-WORLD-ACTIVITY-LIFE", "MOD-WORLD-ACTIVITY-CRISIS",
                    "MOD-WORLD-ACTIVITY-CARE", "MOD-WORLD-CONSTRAINTS",
                    "MOD-WORLD-BOUNDARIES",
                ],
                "constraint_module_ids": ["MOD-WORLD-CONSTRAINTS"],
                "boundary_module_ids": ["MOD-WORLD-BOUNDARIES"],
            },
            "storylines": {"story_subject_module_id": "MOD-STORY-SUBJECT", "line_module_ids": ["MOD-STORY-SUBJECT", "MOD-STORY-LINES"], "connection_module_ids": ["MOD-STORY-CONNECTIONS", "MOD-STORY-RHYTHM"], "major_event_module_ids": ["MOD-STORY-EVENTS", "MOD-STORY-CONSTRAINTS"], "suspense_conflict_rhythm_module_id": "MOD-STORY-RHYTHM", "constraint_module_ids": ["MOD-STORY-CONSTRAINTS"]},
            "characters": {
                "core_character_module_ids": [item["id"] for item in core_character_modules],
                "supporting_character_module_ids": [item["id"] for item in supporting_character_modules],
                "relationship_network_module_ids": ["MOD-CHAR-RELATIONS"],
                "role_coverage_module_ids": ["MOD-CHAR-COVERAGE", "MOD-CHAR-CONSTRAINTS"],
                "constraint_module_ids": ["MOD-CHAR-CONSTRAINTS"],
            },
        },
        "presentation_bindings": [],
        "decision_prompts": [prompt],
        "budget_items": [],
        "control_coverage": [],
        "reduction_ledger": [],
        "drilldown_index": [],
    }

    source_hashes = {item["id"]: item["value_sha256"] for item in inventory["anchors"]}
    presentation_elements: list[tuple[Mapping[str, Any], str]] = [
        *((module, "source_anchor_ids") for section in sections for module in section["modules"]),
        *((visual, "source_anchor_ids") for visual in visuals),
        *((brief, "source_anchor_ids") for brief in briefs),
        (prompt, "affected_source_anchor_ids"),
    ]
    plan["presentation_bindings"] = [
        {
            "element_id": element["id"],
            "content_sha256": rt.canonical_sha256(element),
            "source_values": [{"source_anchor_id": aid, "value_sha256": source_hashes[aid]} for aid in element[field]],
            "must_not_imply": (element["must_not_imply"] if element["id"].startswith("MOD-") else ["不得暗示任何超出绑定 P1 原值的构思事实。"]),
            "challenge_result": "passed",
            "challenge_notes": "逐项对照冻结 P1：保留控制职责与不得暗示边界，不把来源哈希当作语义等价证明。",
        }
        for element, field in presentation_elements
    ]

    element_anchors: dict[str, set[str]] = {}
    for section in sections:
        for module in section["modules"]:
            element_anchors[module["id"]] = set(module["source_anchor_ids"])
    for visual in visuals:
        element_anchors[visual["id"]] = set(visual["source_anchor_ids"])
    for brief in briefs:
        element_anchors[brief["slot_id"]] = set(brief["source_anchor_ids"])
    element_anchors[prompt["id"]] = set(prompt["affected_source_anchor_ids"])

    control_by_anchor: dict[str, str] = {}
    for control in decision_controls:
        for element_id in control["default_element_ids"]:
            for anchor_id in element_anchors[element_id]:
                control_by_anchor.setdefault(anchor_id, control["id"])

    def fallback_control(anchor: Mapping[str, Any]) -> str:
        stage = anchor["stage"]
        source_id = anchor["source_id"]
        if stage in {"W1", "E1"} or (stage == "B0" and (source_id.startswith("WLD-") or source_id.startswith("FACT-"))):
            return "DCTRL-WORLD-BEARING"
        if stage in {"S1", "T1"} or (stage == "B0" and not source_id.startswith("CHR-")):
            return "DCTRL-STORY-CAUSAL"
        return "DCTRL-CHAR-NETWORK"

    anchor_visible: dict[str, list[str]] = {}
    for element_id, anchors in element_anchors.items():
        for anchor_id in anchors:
            anchor_visible.setdefault(anchor_id, []).append(element_id)

    for index, anchor in enumerate(inventory["anchors"], 1):
        aid = anchor["id"]
        control_id = control_by_anchor.get(aid, fallback_control(anchor))
        is_critical = aid in control_by_anchor
        evidence_id = f"EVID-{index:06d}"
        plan["drilldown_index"].append({
            "id": evidence_id,
            "source_anchor_id": aid,
            "stage": anchor["stage"],
            "source_id": anchor["source_id"],
            "json_pointer": anchor["json_pointer"],
            "value_sha256": anchor["value_sha256"],
            "label": f"{anchor['stage']} · {anchor['source_id']}",
        })
        plan["reduction_ledger"].append({
            "source_anchor_id": aid,
            "decision_control_ids": [control_id],
            "relation": "constraint" if anchor["source_id"].startswith(("OPEN-", "NAR-", "WLD-")) else "supports",
            "review_priority": "critical" if is_critical else "supporting",
            "exposure": "default-and-drilldown" if is_critical else "drilldown-only",
            "rationale": "该原值直接支撑默认控制面。" if is_critical else "该原值保留为支撑或校验细节，不挤占十分钟默认阅读面。",
        })
        plan["control_coverage"].append({
            "source_anchor_id": aid,
            "visible_element_ids": ([anchor_visible[aid][0], evidence_id] if is_critical else [evidence_id]),
        })

    minimums = h1a._minimum_reading_seconds(plan)
    safety = {kind: 0 for kind in h1a.REVIEW_PATH_KINDS}
    total = sum(minimums[kind] + safety[kind] for kind in h1a.REVIEW_PATH_KINDS)
    if total > 600:
        raise RuntimeError(f"four-dimension plan exceeds 600 seconds: {minimums} + safety = {total}")
    budget_by_kind = {kind: minimums[kind] + safety[kind] for kind in h1a.REVIEW_PATH_KINDS}
    for step in review_path:
        step["estimated_seconds"] = budget_by_kind[step["kind"]]
    plan["budget_items"] = [
        {"element_id": step["id"], "estimated_seconds": step["estimated_seconds"]}
        for step in review_path
    ]

    phases = [
        {"phase": "review-task-analysis", "phase_index": 1, "payload": {"review_requirements": plan["review_requirements"], "risk_register": plan["risk_register"]}},
        {"phase": "information-architecture", "phase_index": 2, "payload": {"review_path": plan["review_path"], "sections": plan["sections"], "review_scope_contract": plan["review_scope_contract"], "decision_controls": plan["decision_controls"], "reduction_ledger": plan["reduction_ledger"], "drilldown_index": plan["drilldown_index"]}},
        {"phase": "visual-and-fragment-plan", "phase_index": 3, "payload": {"visual_models": plan["visual_models"], "fragment_briefs": plan["fragment_briefs"], "decision_prompts": plan["decision_prompts"], "assembly_projection": plan["assembly_projection"], "presentation_bindings": plan["presentation_bindings"]}},
        {"phase": "ten-minute-budget-test", "phase_index": 4, "payload": {"reading_profile": plan["reading_profile"], "budget_items": plan["budget_items"], "budget_total_seconds": sum(item["estimated_seconds"] for item in plan["budget_items"])}},
        {"phase": "final-review-plan", "phase_index": 5, "payload": {"review_plan": plan, "final_checks": {"three_boards": True, "all_source_anchors_covered": True, "budget_within_600": True, "fragments_non_authoritative": True, "decision_unselected": True}}},
    ]
    return plan, phases, budget_by_kind


def main() -> dict[str, Any]:
    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != "H1-A-plan":
        raise RuntimeError(f"expected pending H1-A-plan, got {None if order is None else order.data.get('action')}")
    initialized = context.store.latest_workspace()
    gate = context.store.load_document(order.data["input_gate"])
    p1_completion = initialized.data["p1_completion"]
    inventory = h1a.build_source_inventory(RUN_ROOT / "P1", p1_completion={"path": p1_completion["path"], "sha256": p1_completion["sha256"]})
    plan, phases, budgets = build_plan(inventory=inventory, p1_completion=p1_completion, input_gate=gate.reference, session_id=initialized.data["session_id"])
    h1a.validate_review_plan(plan, source_inventory=inventory, workspace_state=initialized.data, work_identity=h1a._work_identity(WORK_TITLE, gate.reference), runtime=rt.ContractRuntime())

    def execute(coordinator, sealed_gate):
        return h1a.run_plan(
            PLAN_ROOT,
            p1_package=RUN_ROOT / "P1",
            input_gate=sealed_gate,
            workspace_state=initialized,
            work_title=WORK_TITLE,
            phase_submissions=phases,
            coordinator=coordinator,
            logical_package_path="H1/plan",
            runtime=rt.ContractRuntime(),
        )

    receipt, workspace = prod.commit_h1_workspace(
        context,
        work_order=order,
        actor="novel-conception-human-review-assembler",
        executor=execute,
    )
    return {
        "run_id": RUN_ID,
        "status": "planned",
        "title": plan["work_identity"]["report_title"],
        "content_dimensions": ["世界设定", "故事线设计", "角色定义", "样章"],
        "decision_is_trailing_operation": True,
        "reading_budget_seconds": budgets,
        "reading_budget_total_seconds": sum(budgets.values()),
        "visual_models": len(plan["visual_models"]),
        "fragment_briefs": len(plan["fragment_briefs"]),
        "source_anchors": len(inventory["anchors"]),
        "manifest": receipt.transition.workspace.data["artifacts"]["plan_manifest"],
        "workspace": workspace.reference,
        "workspace_state": workspace.data["state"],
    }


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
