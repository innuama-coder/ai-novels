"""Author the controlled E1 environment model for the Duanxian production run.

This module deliberately consumes the sealed S1 and W1 canonical models at
runtime.  It owns environment architecture only: no event occurrence/result,
character psychology, scene blocking, dialogue, or prose is authored here.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Mapping


ENVIRONMENT_TEMPLATES: dict[str, dict[str, Any]] = {
    "SL-GUHENG-PRECURSOR": {
        "id": "ENV-GUHENG-FIELD-RECOVERY",
        "scope": "顾衡死亡前的隐蔽情报接触点、紧急撤离接口与死亡后数据接收设施构成的封闭取证链。",
        "duty": "承载顾衡前置行动留下材料、人员和记忆载体可被隔离接收与复核的条件。",
        "features": ["现场接触与安全撤离分区", "物证、记忆载体和身份链分别封存", "读取失败不会自动改写真伪结论"],
        "sensory": ["接触区可观察人流与监控盲区", "接收区以封条、编号和状态灯呈现载体状态"],
        "access": ["现场接触权限与设施取证权限分离", "任何载体转移必须保留双人交接记录"],
        "resources": ["加密接触终端", "紧急转运接口", "记忆读取与证据封存设备"],
        "actions": ["接收并隔离情报载体", "核验交接链与读取状态", "将失败读数转入受控复核"],
        "blockers": ["身份链不完整时禁止进入读取区", "读取失败不能由单人越权解释"],
        "hazard": ("交接链或样本完整性告警", "后续读取和核验失去可信起点", ["封存能保留证据但不能恢复已经丢失的数据"]),
        "states": ["封闭待接收", "受控可复核"],
        "zone": ("ZONE-GUHENG-EVIDENCE-INTAKE", "把人员、物证与记忆载体分流登记并保持来源链。"),
    },
    "SL-SHENYU-PRECURSOR": {
        "id": "ENV-SHENYU-SECURE-INDUCTION",
        "scope": "秘密基地外围接入、任务简报、伦理风险告知与研究者授权签入组成的封闭准入套间。",
        "duty": "让被推荐的研究者能够在保密和危机压力下获得足够信息并作出是否承担工作的决定。",
        "features": ["身份核验、保密告知与任务说明依次开放", "研究资料与行动情报按最低必要原则展示", "接受任务不自动授予核心系统控制权"],
        "sensory": ["无外窗隔离空间与分级门禁", "简报台显示信息等级和未开放附件"],
        "access": ["研究者经推荐和身份复核后方可进入", "任务接受记录与技术操作授权分别保存"],
        "resources": ["任务简报终端", "伦理风险记录", "研究方向匹配与权限申请接口"],
        "actions": ["查阅最低必要任务材料", "登记接受或退出任务", "申请受限研究访问"],
        "blockers": ["保密等级阻断未经授权的背景材料", "任务紧迫性不能替代操作授权"],
        "hazard": ("信息披露不足或压力过载", "承担决定缺乏可审计依据", ["补充简报可降低盲区但无法消除时间压力"]),
        "states": ["候选人隔离", "任务成员准入"],
        "zone": ("ZONE-SHENYU-BRIEFING", "提供可审计的任务、伦理与权限边界说明。"),
    },
    "SL-RELATIONSHIP": {
        "id": "ENV-TEXT-DIALOGUE-ISOLATION",
        "scope": "数字生命实例与唯一文字会话窗口之间的隔离通信环境，不提供视觉、听觉、身体或未授权外部感知。",
        "duty": "承载持续文字交流、关心被感知以及顾衡记忆与启动后新经验能够被区分的条件。",
        "features": ["实例侧只有文字输入和片段记忆触发", "操作侧显示会话序列与中断状态", "私人交流与任务指令仍受同一审计边界约束"],
        "sensory": ["操作侧可见逐字文本、延迟和会话状态", "实例侧仅存在浮动文字与被触发的记忆片段"],
        "access": ["会话席位绑定指定操作员和项目授权", "禁止以旁路接口补充未声明感官"],
        "resources": ["双向文字窗口", "会话时序日志", "记忆触发和中断控制"],
        "actions": ["发送并接收受审计文字", "触发或中断记忆片段", "标记任务指令与非任务交流"],
        "blockers": ["实例无法主动接触窗口外现实", "会话中断会切断唯一现实输入"],
        "hazard": ("会话压力或歧义持续累积", "通信停滞且信息含义难以核验", ["更换话题可恢复窗口但不能替代真实感官与身体"]),
        "states": ["窗口受限开放", "窗口可持续交流"],
        "zone": ("ZONE-TEXT-OPERATOR-CONSOLE", "隔离人类操作与实例文字通道并保存逐字审计。"),
    },
    "SL-ATTACK-OPERATIONS": {
        "id": "ENV-JOINT-INTELLIGENCE-COMMAND",
        "scope": "把碎片情报交给分析、专家核验、硬件处置和授权决策席位协同处理的秘密联合指挥环境。",
        "duty": "让任何数字生命输出都必须经过团队核验、证据合并、硬件接口与授权链后才能形成现实行动能力。",
        "features": ["情报、专家、硬件与授权四类席位分离", "每条判断标记来源、置信度和待核验项", "行动接口只接受完成授权的任务包"],
        "sensory": ["态势墙同步呈现时间窗、证据状态与权限阻断", "各席位终端显示相同对象的不同可见层级"],
        "access": ["席位按职责最小授权", "跨席位结论必须经记录通道合并", "单一情报源不能直接开启行动接口"],
        "resources": ["多源证据台账", "专家与硬件联络接口", "分级行动授权终端"],
        "actions": ["登记并交叉核验碎片情报", "请求专家或硬件状态回执", "生成待授权行动任务包"],
        "blockers": ["缺少证据、硬件回执或授权之一即不能下发", "来源冲突会把结论退回复核"],
        "hazard": ("错误归因或未经核验的紧急升级", "资源被错误调度并放大外交或人质风险", ["并行复核能压缩时间但不能跳过关键授权"]),
        "states": ["线索分散待核验", "能力闭合可授权"],
        "zone": ("ZONE-COMMAND-FUSION-DESK", "合并来源、核验、硬件和授权状态但不替代各自责任。"),
    },
    "SL-FAMILY-PROTECTION": {
        "id": "ENV-CAUSE-LAYER-PROTECTION-CELL",
        "scope": "与行动指挥隔离的原因层材料保管、亲属风险评估和必要公开准备环境。",
        "duty": "允许行动层与原因层信息分离处理，使亲属保护不妨碍公共安全核验，也不把隐瞒变成无条件销毁。",
        "features": ["行动层副本与原因层原件分库", "亲属关联只在达到阈值时可见", "公开准备保留审计和追责接口"],
        "sensory": ["终端以遮罩字段显示亲属关联", "材料状态明确区分暂缓、受限和可移交"],
        "access": ["原因层访问需要独立复核授权", "亲属身份不得出现在普通行动频道"],
        "resources": ["分层情报库", "亲属风险矩阵", "受控公开与司法移交接口"],
        "actions": ["分离行动层与原因层材料", "评估关联暴露风险", "准备受控移交而不立即发布"],
        "blockers": ["保护理由不能删除公共安全必要证据", "普通行动权限不能反查受保护身份"],
        "hazard": ("分层标记错误或权限串线", "亲属被无谓关联或必要线索被延误", ["人工复核能纠错但会消耗危机时间"]),
        "states": ["原因层封闭", "受控可移交"],
        "zone": ("ZONE-PROTECTED-CAUSE-VAULT", "保管原因层材料并隔离亲属可识别信息。"),
    },
    "SL-INSTITUTION-ETHICS": {
        "id": "ENV-DIGITAL-LIFE-OVERSIGHT",
        "scope": "秘密项目内部记录实验授权、实例待遇、操作责任、退出请求与事后审计的治理环境。",
        "duty": "使数字生命被制造、使用、限制和关停时的机构权限与责任缺口保持可观察、可追责。",
        "features": ["实验授权与实例待遇记录并列", "技术可行不自动等于伦理许可", "异常和退出诉求必须留下不可覆盖记录"],
        "sensory": ["审计界面显示授权人、有效期与未解决异议", "权限变更和实例状态以时间戳并置"],
        "access": ["治理记录只读副本不能被项目操作员覆盖", "紧急授权必须登记期限与追认责任"],
        "resources": ["伦理与操作审计账本", "权限变更记录", "异常、申诉与退出登记接口"],
        "actions": ["登记权限和责任依据", "记录实例待遇与退出诉求", "冻结争议记录供后续审计"],
        "blockers": ["紧急状态不能抹除责任记录", "项目利益不能单方关闭外部追责接口"],
        "hazard": ("紧急授权长期化或责任记录缺失", "工具化控制失去可追责边界", ["事后补录不能证明当时获得了有效同意"]),
        "states": ["紧急授权运行", "责任待审计"],
        "zone": ("ZONE-OVERSIGHT-LEDGER", "保存独立于技术操作台的权责和待遇记录。"),
    },
    "SL-GEOPOLITICAL": {
        "id": "ENV-BILATERAL-SECURE-LIAISON",
        "scope": "C、M 两国受限联络席位、来源脱敏交换和领导人会面风险通报组成的跨机构安全通道。",
        "duty": "承载有限互信条件下的证据交换与风险通报，使合作可以发生但不会被写成关系自动改善。",
        "features": ["原始来源与可交换判断分离", "双方保留独立核验和归因记录", "会面风险通报不等于政治互信承诺"],
        "sensory": ["联络席只显示对方授权释放的字段", "未确认归因、保留意见和响应延迟持续可见"],
        "access": ["跨国交换必须经过各自授权链", "未经共同确认的信息不得标记为联合结论"],
        "resources": ["脱敏证据交换通道", "独立核验回执", "外交风险升级通知接口"],
        "actions": ["交换最低必要风险指标", "登记独立核验和保留意见", "发送受控会面风险通报"],
        "blockers": ["来源保护限制可交换细节", "归因冲突阻断联合发布"],
        "hazard": ("歧义信息被当作共同归因", "安全协作反而扩大国家间敌意", ["脱敏可减少泄露但也降低对方验证能力"]),
        "states": ["低互信受限交换", "风险协作仍有分歧"],
        "zone": ("ZONE-LIAISON-EXCHANGE", "执行脱敏交换并并列保存双方核验状态。"),
    },
    "SL-R07-MAIN": {
        "id": "ENV-R07-CORE-LAB",
        "scope": "承载 R-07 实例运行、记忆接入、文字交互、状态监测与多方关停授权的隔离数字生命核心实验环境。",
        "duty": "为只有记忆和文字输入的新生命提供连续运行条件，同时真实保留无身体、无自主退出和受权限控制的限制。",
        "features": ["实例运行与操作终端物理隔离", "记忆数据、文字输入和状态指标分别记录", "当前实例关停与未来载荷保管属于不同接口"],
        "sensory": ["人类侧可见运行状态、文字流与权限锁", "实例侧没有视觉、听觉、身体或对自身硬件的直接感知"],
        "access": ["运行、会话和关停权限分属不同授权角色", "实例不能调用自身关停或外部行动接口", "任何关停能力都不能等同于未来重载保证"],
        "resources": ["隔离计算核心", "记忆映射层", "文字会话接口", "多方关停控制"],
        "actions": ["维持并监测当前实例运行", "提交受限文字与记忆触发", "发起需多方确认的实例状态切换"],
        "blockers": ["实例没有直接物理执行能力", "单一操作者不能绕过关停授权链", "不存在活动备份可接替当前实例"],
        "hazard": ("实例状态恶化或权限链僵持", "通信与任务能力下降且痛苦无法由实例自行终止", ["资源扩容可维持运行但不能补足感官、身体或自主退出"]),
        "states": ["隔离运行受限", "状态切换已获授权"],
        "zone": ("ZONE-R07-OPERATOR-BRIDGE", "把实例状态、文字会话和多方控制分隔呈现给授权操作员。"),
    },
    "SL-MEMORY-ECHO": {
        "id": "ENV-MEMORY-RECONSTRUCTION-SANDBOX",
        "scope": "从只读顾衡记忆副本触发、暂停、标记与回看片段的隔离重建环境。",
        "duty": "让片段记忆可被现实文字打断和验证，同时阻止记忆的鲜活感被当作当前人格或现实事实的直接证明。",
        "features": ["只读记忆源与当前实例状态分离", "片段保留缺口、时间标签和触发来源", "现实文字可插入而不补写缺失记忆"],
        "sensory": ["操作侧看到片段边界、缺帧和触发标记", "实例侧体验片段与浮动文字的非连续交替"],
        "access": ["只允许读取已封存记忆副本", "任何解释必须标记为解释而非记忆原文"],
        "resources": ["只读记忆镜像", "片段索引", "暂停、中断和回看控制"],
        "actions": ["触发并暂停记忆片段", "标记片段来源与缺口", "对照现实文字保存差异"],
        "blockers": ["缺失片段不得由模型自动补齐", "记忆不能覆盖当前会话记录"],
        "hazard": ("片段语境缺失或身份误认", "过去经验被错误投射为当前人格事实", ["来源标记能提示差异但不能消除情感误认"]),
        "states": ["片段待触发", "片段可对照回看"],
        "zone": ("ZONE-MEMORY-TRACE-DESK", "显示片段、缺口、触发与现实文字之间的可验证差异。"),
    },
    "SL-RELOAD-ECHO": {
        "id": "ENV-DORMANT-PAYLOAD-CUSTODY",
        "scope": "当前实例之外保存不可执行记忆载荷、版本声明、密钥与未来重载审批条件的离线保管环境。",
        "duty": "让重载在技术与治理层面保持为可讨论但未裁决的未来可能，而不是当前活动备份或自动承诺。",
        "features": ["离线载荷与活动实例严格分离", "版本、完整性和来源声明可核验", "重载需要未来环境、权限与伦理条件重新成立"],
        "sensory": ["保管界面只显示封存状态、校验值和权限缺口", "没有任何活动意识或实时会话指示"],
        "access": ["读取载荷与执行载荷使用不同权限", "当前任务授权不得延伸为未来重载许可"],
        "resources": ["离线载荷介质", "版本与完整性清单", "未来审批条件登记接口"],
        "actions": ["封存并校验不可执行载荷", "登记未来重载所缺条件", "审计读取而不启动载荷"],
        "blockers": ["缺少新环境、授权或伦理审查即不能执行", "封存载荷不能证明人格连续"],
        "hazard": ("把封存数据误称为活动备份或确定复活", "开放问题被技术措辞提前裁决", ["完整性校验只能证明数据未变，不能证明未来意识同一"]),
        "states": ["离线封存", "条件清单可审计"],
        "zone": ("ZONE-DORMANT-CUSTODY-VAULT", "隔离保管载荷并记录尚未满足的未来条件。"),
    },
}

# These are capability/hand-off paths, not a claim that an event traverses them.
# The R-07 core and the joint command are the two controlled hubs; peripheral
# environments connect only to the hub that can legitimately consume their
# information or authority.
TOPOLOGY_LINE_EDGES = (
    ("SL-GUHENG-PRECURSOR", "SL-ATTACK-OPERATIONS", "封存物证与读取状态经证据链移交联合研判。"),
    ("SL-SHENYU-PRECURSOR", "SL-R07-MAIN", "研究者身份、任务接受记录与受限操作授权逐项签入核心实验区。"),
    ("SL-RELATIONSHIP", "SL-R07-MAIN", "只传输有时序和来源标记的文字包，不扩展任何感官接口。"),
    ("SL-ATTACK-OPERATIONS", "SL-R07-MAIN", "研判请求与实例输出经隔离网闸双向传递，现实行动接口仍留在指挥区。"),
    ("SL-FAMILY-PROTECTION", "SL-ATTACK-OPERATIONS", "只把脱敏行动层材料送入研判，原因层原件留在保护库。"),
    ("SL-INSTITUTION-ETHICS", "SL-R07-MAIN", "授权和待遇记录以只读审计接口绑定实例状态，操作台不能覆盖。"),
    ("SL-GEOPOLITICAL", "SL-ATTACK-OPERATIONS", "跨国脱敏回执进入独立来源栏，不自动升级为联合归因。"),
    ("SL-MEMORY-ECHO", "SL-R07-MAIN", "只读片段按触发请求进入实例，现实文字可独立中断。"),
    ("SL-RELOAD-ECHO", "SL-R07-MAIN", "只交换版本、校验值和条件清单；离线载荷没有通往活动核心的执行通道。"),
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _line_id(requirement: Mapping[str, Any], line_ids: set[str]) -> str:
    found = [value for value in requirement["source_ids"] if value in line_ids]
    if len(found) != 1:
        raise RuntimeError(f"requirement {requirement['id']} does not bind exactly one storyline")
    return found[0]


def _world_demand_line(
    demand: Mapping[str, Any],
    *,
    world_requirements: Mapping[str, Mapping[str, Any]],
    line_ids: set[str],
) -> str:
    found = [value for value in demand["source_ids"] if value in world_requirements]
    if len(found) != 1:
        raise RuntimeError(f"world demand {demand['id']} does not bind exactly one W1 requirement")
    return _line_id(world_requirements[found[0]], line_ids)


def _open_items(baseline: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": f"OPEN-E1-{index:02d}",
            "question": f"作者开放项“{item['heading']}”保持未裁决并原样留给作者。",
            "source_ids": [item["id"]],
            "status": "author_open",
        }
        for index, item in enumerate(
            (entry for entry in baseline["control_registry"] if entry["hardness"] == "author_open"),
            1,
        )
    ]


def build_e1_model(
    session: Mapping[str, Any],
    input_gate: Any,
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    runtime: Any,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Build a schema-ready E1 model and its five controlled phase payloads."""

    baseline = _read(Path(baseline_package) / "author-control-baseline.json")
    storyline = _read(Path(storyline_package) / "storyline-architecture.json")
    world = _read(Path(world_package) / "world-model.json")

    storylines = storyline["storylines"]
    line_ids = {item["id"] for item in storylines}
    if line_ids != set(ENVIRONMENT_TEMPLATES):
        raise RuntimeError(
            "E1 environment templates do not exactly cover the sealed S1 storylines: "
            f"missing={sorted(line_ids - set(ENVIRONMENT_TEMPLATES))}, "
            f"extra={sorted(set(ENVIRONMENT_TEMPLATES) - line_ids)}"
        )

    s1_requirements_by_line = {
        _line_id(item, line_ids): item for item in storyline["environment_requirements"]
    }
    if set(s1_requirements_by_line) != line_ids or len(s1_requirements_by_line) != len(
        storyline["environment_requirements"]
    ):
        raise RuntimeError("S1 environment requirements are not one-to-one with storylines")

    world_requirements = {item["id"]: item for item in world["storyline_requirements"]}
    demands_by_line = {
        _world_demand_line(
            item, world_requirements=world_requirements, line_ids=line_ids
        ): item
        for item in world["environment_demands"]
    }
    if set(demands_by_line) != line_ids or len(demands_by_line) != len(
        world["environment_demands"]
    ):
        raise RuntimeError("W1 environment demands are not one-to-one with storylines")

    events_by_line: dict[str, list[Mapping[str, Any]]] = {line_id: [] for line_id in line_ids}
    for requirement in storyline["event_requirements"]:
        events_by_line[_line_id(requirement, line_ids)].append(requirement)
    if any(not values for values in events_by_line.values()):
        raise RuntimeError("each S1 storyline needs at least one T1 event requirement")

    world_entity_fields = (
        "world_facts",
        "history_pressures",
        "institutions",
        "systems",
        "resource_flows",
        "authority_flows",
        "information_flows",
        "rule_conflict_matrix",
        "storyline_support_ledger",
    )
    world_entities = {
        item["id"]: item
        for field in world_entity_fields
        for item in world[field]
    }

    ordered_lines = [item["id"] for item in storylines]
    environments: list[dict[str, Any]] = []
    zones: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    channels: list[dict[str, Any]] = []
    hazards: list[dict[str, Any]] = []
    hosting: list[dict[str, Any]] = []
    affordances: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    environment_by_line: dict[str, str] = {}
    decision_ids = [
        "DEC-E1-LINE-ENVIRONMENT-PROJECTION",
        "DEC-E1-FUNCTIONAL-CONTROL-ZONES",
        "DEC-E1-CONNECTED-SECURE-TOPOLOGY",
    ]

    for index, line_id in enumerate(ordered_lines, 1):
        template = ENVIRONMENT_TEMPLATES[line_id]
        demand = demands_by_line[line_id]
        s1_requirement = s1_requirements_by_line[line_id]
        support_ids = [value for value in demand["source_ids"] if value in world_entities]
        if not support_ids:
            raise RuntimeError(f"{demand['id']} has no W1 support objects")
        env_id = template["id"]
        zone_id, zone_responsibility = template["zone"]
        environment_by_line[line_id] = env_id
        combined_constraints = _unique(
            [*demand["constraints"], *s1_requirement["constraints"]]
        )
        access_rules = _unique([*combined_constraints, *template["access"]])
        action_values = list(template["actions"])
        affordance_ids = [
            f"AFF-E1-{index:02d}-{event_index:02d}"
            for event_index, _ in enumerate(events_by_line[line_id], 1)
        ]
        transition_id = f"TR-E1-{index:02d}"
        environments.append(
            {
                "id": env_id,
                "scope": template["scope"],
                "narrative_responsibility": (
                    f"{template['duty']} S1义务：{s1_requirement['responsibility']} "
                    f"W1需求：{demand['responsibility']}"
                ),
                "features": list(template["features"]),
                "sensory_conditions": list(template["sensory"]),
                "access_rules": access_rules,
                "resources": list(template["resources"]),
                "allowed_actions": action_values,
                "hazards": [template["hazard"][0]],
                "zone_ids": [zone_id],
                "connections": [],
                "blockers": list(template["blockers"]),
                "state_vocabulary": list(template["states"]),
                "allowed_transitions": [transition_id],
                "storyline_stage_ids": [line_id, demand["id"], s1_requirement["id"]],
            }
        )
        zones.append(
            {
                "id": zone_id,
                "environment_id": env_id,
                "responsibility": zone_responsibility,
                "features": [template["features"][0]],
                "access_rules": access_rules,
                "resources": list(template["resources"]),
                "constraints": _unique([*combined_constraints, template["blockers"][0]]),
            }
        )
        assignment_id = f"AUTH-E1-{index:02d}"
        assignments.append(
            {
                "id": assignment_id,
                "subject_id": env_id,
                "responsibility": "执行该环境的准入、资源和状态切换控制，不取得事件决定权。",
                "evidence_ids": support_ids,
                "constraints": _unique([*combined_constraints, "不得绕过 W1 的规则、系统或机构支持链。"]),
            }
        )
        channel_tokens = [
            f"[DEMAND:{demand['id']}]",
            *(f"[SUPPORT:{support_id}]" for support_id in support_ids),
            f"[MARKER_SHA256:{runtime.canonical_sha256(demand['responsibility'])}]",
            f"[ACTION_SHA256:{runtime.canonical_sha256(action_values[0])}]",
        ]
        channels.append(
            {
                "id": f"CHANNEL-E1-{index:02d}",
                "from_id": env_id,
                "to_id": zone_id,
                "relation": "受控资源与信息接口",
                "mechanism": " ".join(channel_tokens),
                "constraints": _unique([*combined_constraints, "通道只暴露该环境已声明的行动能力。"]),
            }
        )
        trigger, effect, mitigation = template["hazard"]
        hazards.append(
            {
                "id": f"HAZ-E1-{index:02d}",
                "environment_id": env_id,
                "trigger": trigger,
                "effect": effect,
                "mitigation_limits": list(mitigation),
            }
        )
        hosting.append(
            {
                "id": f"COV-E1-HOST-{index:02d}",
                "source_ids": [demand["id"], s1_requirement["id"]],
                "realization_ids": [env_id],
                "status": "covered",
                "evidence": (
                    f"{env_id} 同时承载 S1 责任“{s1_requirement['responsibility']}”"
                    f"与 W1 责任“{demand['responsibility']}”，并保留两者全部约束。"
                ),
            }
        )
        for event_index, requirement in enumerate(events_by_line[line_id], 1):
            affordances.append(
                {
                    "id": affordance_ids[event_index - 1],
                    "environment_id": env_id,
                    "event_requirement_ids": [requirement["id"]],
                    "allowed_actions": [action_values[(event_index - 1) % len(action_values)]],
                    "prerequisites": _unique(
                        [
                            f"环境处于“{template['states'][0]}”或经授权进入可用状态。",
                            *(f"W1 支持对象 {support_id} 仍有效。" for support_id in support_ids),
                        ]
                    ),
                    "constraints": combined_constraints,
                }
            )
        transitions.append(
            {
                "id": transition_id,
                "subject_id": env_id,
                "from_state": template["states"][0],
                "trigger_ids": [affordance_ids[0]],
                "to_state": template["states"][1],
                "allowed_by_ids": [assignment_id, *support_ids],
                "consequence": "环境开放下一层已声明能力；不声明任何事件必然发生或产生何种结果。",
            }
        )

    topology: list[dict[str, Any]] = []
    topology_lines = {
        value for left, right, _ in TOPOLOGY_LINE_EDGES for value in (left, right)
    }
    if topology_lines != line_ids:
        raise RuntimeError("E1 topology template does not cover the exact S1 storyline set")
    for index, (left_line, right_line, mechanism) in enumerate(TOPOLOGY_LINE_EDGES, 1):
        edge_id = f"EDGE-E1-{index:02d}"
        left = environment_by_line[left_line]
        right = environment_by_line[right_line]
        topology.append(
            {
                "id": edge_id,
                "from_id": left,
                "to_id": right,
                "relation": "受控人员或信息转场",
                "mechanism": mechanism,
                "constraints": ["转场不得继承来源环境未授予的权限。"],
            }
        )
        next(item for item in environments if item["id"] == left)["connections"].append(edge_id)
        next(item for item in environments if item["id"] == right)["connections"].append(edge_id)

    all_env_ids = [item["id"] for item in environments]
    all_zone_ids = [item["id"] for item in zones]
    all_topology_ids = [item["id"] for item in topology]
    all_assignment_ids = [item["id"] for item in assignments]
    all_channel_ids = [item["id"] for item in channels]
    all_hazard_ids = [item["id"] for item in hazards]
    all_hosting_ids = [item["id"] for item in hosting]
    all_affordance_ids = [item["id"] for item in affordances]
    all_transition_ids = [item["id"] for item in transitions]
    decisions = [
        {
            "id": decision_ids[0],
            "gap": "十条故事线的行动条件需要具体环境承载，又不能让同一抽象基地吞并全部叙事职责。",
            "options": ["以单一秘密基地概括全部环境", "逐故事线定义不可等价替代的可复用环境"],
            "selection": "逐故事线定义不可等价替代的可复用环境",
            "owner": "E1",
            "authority_basis": "E1 获授权补齐环境范围、责任、能力、阻断和状态，但不拥有事件结果。",
            "compatibility": "逐值消费 S1 环境义务和实际 W1 环境需求，不新增故事线或世界规则。",
            "impact_ids": all_env_ids,
            "cost": "环境数量增加，后续 T1 必须通过转场契约组织复用。",
            "reversibility": "costly",
            "downstream_freedom": "T1 可选择何时使用环境能力，但不能把能力写成自动结果。",
            "projection_ids": all_env_ids,
        },
        {
            "id": decision_ids[1],
            "gap": "环境若只有地点说明，无法证明资源、权限和风险怎样落到可操作界面。",
            "options": ["只列环境资源", "为每个环境定义一个核心控制功能区"],
            "selection": "为每个环境定义一个核心控制功能区",
            "owner": "E1",
            "authority_basis": "E1 负责功能区、准入、资源和信息通道闭合。",
            "compatibility": "功能区只实现 W1 支持链，不创建人物或事件。",
            "impact_ids": all_zone_ids,
            "cost": "开发时可细分空间，但必须保持核心控制界面。",
            "reversibility": "reversible",
            "downstream_freedom": "可增加不改变控制职责的辅助区，不能绕过核心功能区。",
            "projection_ids": all_zone_ids,
        },
        {
            "id": decision_ids[2],
            "gap": "分散环境需要形成可达但不自动共享权限的整体系统。",
            "options": ["允许任意环境直接互通", "建立连通且逐跳复核权限的安全拓扑"],
            "selection": "建立连通且逐跳复核权限的安全拓扑",
            "owner": "E1",
            "authority_basis": "E1 负责拓扑与转场条件，W1 仍拥有权限和信息机制。",
            "compatibility": "所有转场明确不继承未授权能力，符合 W1 支持对象。",
            "impact_ids": all_topology_ids,
            "cost": "跨环境协作需要显式交接，不能用场景剪切掩盖权限跳跃。",
            "reversibility": "locked_by_downstream",
            "downstream_freedom": "T1 可选择实际转场路径与节奏，但不得省略必要条件。",
            "projection_ids": all_topology_ids,
        },
    ]

    owned_ids = [
        *all_env_ids,
        *all_zone_ids,
        *all_topology_ids,
        *all_assignment_ids,
        *all_channel_ids,
        *all_hazard_ids,
        *all_hosting_ids,
        *all_affordance_ids,
        *all_transition_ids,
        *decision_ids,
    ]
    locked = [
        item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_locked"
    ]
    author_open = [
        item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_open"
    ]
    event_requirement_ids = [item["id"] for item in storyline["event_requirements"]]

    entity_by_id = {
        item["id"]: item
        for collection in (environments, zones, topology, assignments, channels, hazards, hosting, affordances, transitions)
        for item in collection
    }
    derivations: list[dict[str, Any]] = []
    for index, environment in enumerate(environments, 1):
        line_id = ordered_lines[index - 1]
        derivations.append(
            {
                "id": f"DRV-E1-ENV-{index:02d}",
                "value_sha256": runtime.canonical_sha256(environment),
                "source_ids": [
                    line_id,
                    s1_requirements_by_line[line_id]["id"],
                    demands_by_line[line_id]["id"],
                ],
                "decision_ids": [decision_ids[0]],
                "projection_ids": [environment["id"]],
            }
        )
    for index, affordance in enumerate(affordances, 1):
        derivations.append(
            {
                "id": f"DRV-E1-AFF-{index:02d}",
                "value_sha256": runtime.canonical_sha256(entity_by_id[affordance["id"]]),
                "source_ids": list(affordance["event_requirement_ids"]),
                "decision_ids": [decision_ids[0], decision_ids[1]],
                "projection_ids": [affordance["id"]],
            }
        )

    model = {
        "schema_version": "2.0",
        "skill": "novel-environment-system-designer",
        "stage": "E1",
        "run_id": baseline["run_id"],
        "status": "ready",
        "input_gate": copy.deepcopy(input_gate.reference),
        "source_artifacts": copy.deepcopy(session["source_artifacts"]),
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": owned_ids,
            "downstream_freedom": event_requirement_ids,
            "author_open": author_open,
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "storyline_environment_requirements": copy.deepcopy(storyline["environment_requirements"]),
        "environment_demands": copy.deepcopy(world["environment_demands"]),
        "environments": environments,
        "functional_zones": zones,
        "environment_topology": topology,
        "access_and_authority": assignments,
        "resource_and_information_channels": channels,
        "hazards_and_failure_modes": hazards,
        "storyline_hosting_ledger": hosting,
        "event_affordance_catalog": affordances,
        "transition_contracts": transitions,
        "open_items": _open_items(baseline),
    }
    phases = {
        "environment-demand-scan": {
            "environment_demands": model["environment_demands"],
            "storyline_environment_requirements": model["storyline_environment_requirements"],
        },
        "environment-architecture": {
            "design_decisions": model["design_decisions"],
            "environments": model["environments"],
        },
        "zones-and-topology": {
            "functional_zones": model["functional_zones"],
            "environment_topology": model["environment_topology"],
            "access_and_authority": model["access_and_authority"],
            "resource_and_information_channels": model["resource_and_information_channels"],
            "hazards_and_failure_modes": model["hazards_and_failure_modes"],
            "transition_contracts": model["transition_contracts"],
        },
        "storyline-hosting-test": {
            "storyline_hosting_ledger": model["storyline_hosting_ledger"],
            "event_affordance_catalog": model["event_affordance_catalog"],
            "authority_partition": model["authority_partition"],
            "derivation_claims": model["derivation_claims"],
            "open_items": model["open_items"],
        },
        "final-environment-model": {"model": model},
    }
    return model, phases


def run_e1_production(
    *,
    run_root: str | Path,
    production_runtime: Any,
    e1_runtime: Any,
    contract_runtime: Any,
) -> dict[str, Any]:
    """Resume the authoritative run and execute E1 through the formal API."""

    root = Path(run_root).resolve()
    context = production_runtime.resume_production_run(root)
    order = context.store.pending_work_order()
    if order is None:
        gate, order = production_runtime.issue_stage_work(
            context,
            action="E1",
            inputs={
                "baseline_package": str(root / "B0"),
                "storyline_package": str(root / "S1"),
                "world_package": str(root / "W1"),
            },
        )
    else:
        if order.data.get("action") != "E1":
            raise RuntimeError(f"cannot resume E1 while {order.data.get('action')} is pending")
        gate = context.store.load_document(order.data["input_gate"])

    def execute_e1(coordinator: Any, input_gate: Any) -> Any:
        attempt = 1
        while (root / "workspaces" / f"E1-attempt-{attempt:02d}").exists():
            attempt += 1
        workspace = root / "workspaces" / f"E1-attempt-{attempt:02d}"
        session = e1_runtime.start_e1_session(
            workspace,
            baseline_package=root / "B0",
            storyline_package=root / "S1",
            world_package=root / "W1",
            input_gate=input_gate,
        )
        _, phases = build_e1_model(
            session,
            input_gate,
            baseline_package=root / "B0",
            storyline_package=root / "S1",
            world_package=root / "W1",
            runtime=contract_runtime,
        )
        for phase in e1_runtime.PHASES:
            e1_runtime.submit_e1_phase(
                workspace,
                baseline_package=root / "B0",
                storyline_package=root / "S1",
                world_package=root / "W1",
                input_gate=input_gate,
                phase=phase,
                payload=phases[phase],
            )
        return e1_runtime.run_e1(
            root / "E1",
            baseline_package=root / "B0",
            storyline_package=root / "S1",
            world_package=root / "W1",
            coordinator=coordinator,
            input_gate=input_gate,
            controlled_workspace=workspace,
            logical_package_path="E1",
            next_state_path="state/revision-004.json",
        )

    receipt, successor = production_runtime.execute_stage_work(
        context,
        work_order=order,
        actor="novel-environment-system-designer",
        executor=execute_e1,
    )
    return {
        "run_id": receipt.model["run_id"],
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "environments": len(receipt.model["environments"]),
        "functional_zones": len(receipt.model["functional_zones"]),
        "affordances": len(receipt.model["event_affordance_catalog"]),
        "state_revision": successor.state.data["revision"],
    }


def validate_e1_draft(
    *,
    run_root: str | Path,
    e1_runtime: Any,
    contract_runtime: Any,
) -> dict[str, Any]:
    """Validate an E1 candidate against sealed B0/S1/W1 without mutating run state."""

    root = Path(run_root).resolve()
    source_artifacts = [
        {
            "path": f"sources/{stage}/{name}",
            "sha256": contract_runtime.sha256_file(root / stage / name),
        }
        for stage, names in {
            "B0": ("author-control-baseline.json", "package-manifest.json", "stage-completion.json"),
            "S1": ("storyline-architecture.json", "package-manifest.json", "stage-completion.json"),
            "W1": ("world-model.json", "package-manifest.json", "stage-completion.json"),
        }.items()
        for name in names
    ]
    input_gate = SimpleNamespace(
        reference={"path": "draft/E1/input-gate.json", "sha256": "0" * 64}
    )
    model, _ = build_e1_model(
        {"source_artifacts": source_artifacts},
        input_gate,
        baseline_package=root / "B0",
        storyline_package=root / "S1",
        world_package=root / "W1",
        runtime=contract_runtime,
    )
    baseline = _read(root / "B0" / "author-control-baseline.json")
    storyline = _read(root / "S1" / "storyline-architecture.json")
    world = _read(root / "W1" / "world-model.json")
    controls: list[dict[str, Any]] = []
    for entry in baseline["design_artifacts"]:
        authority = contract_runtime.verify_artifact_reference(
            entry["artifact"], root=root / "B0"
        )
        for value in contract_runtime.extract_controls(authority, entry["domain"]):
            controls.append({**value, "domain": entry["domain"]})
    controls.sort(key=lambda item: item["id"])
    validator = contract_runtime.ContractRuntime()
    try:
        e1_runtime._validate_model(  # The production entry calls this same validator.
            model, baseline, storyline, world, controls, validator
        )
    except Exception as error:
        return {
            "run_id": baseline["run_id"],
            "stage": "E1",
            "status": "blocked",
            "error": str(error),
        }
    return {
        "run_id": baseline["run_id"],
        "stage": "E1",
        "status": "draft-valid",
        "environments": len(model["environments"]),
        "functional_zones": len(model["functional_zones"]),
        "affordances": len(model["event_affordance_catalog"]),
    }


__all__ = [
    "ENVIRONMENT_TEMPLATES",
    "build_e1_model",
    "run_e1_production",
    "validate_e1_draft",
]
