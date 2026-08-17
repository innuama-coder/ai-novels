"""Agent-authored T1 proposal builder for the production ``duanxian`` run.

This module deliberately stops at event architecture.  It consumes the sealed
B0/S1/W1/E1 models, realizes the ten S1 storylines as a causal event model, and
returns the five payloads required by the controlled T1 runtime.  It does not
create character identities, chapter plans, scenes, dialogue, or fiction prose.
"""

from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


RUNTIME = importlib.import_module("harnesses.novel-conception-autonomous.runtime")


class DuanxianT1BuildError(ValueError):
    """The sealed upstream models cannot support the intended T1 proposal."""


_LINE_ORDER = (
    "SL-GUHENG-PRECURSOR",
    "SL-SHENYU-PRECURSOR",
    "SL-RELATIONSHIP",
    "SL-FAMILY-PROTECTION",
    "SL-INSTITUTION-ETHICS",
    "SL-GEOPOLITICAL",
    "SL-ATTACK-OPERATIONS",
    "SL-R07-MAIN",
    "SL-MEMORY-ECHO",
    "SL-RELOAD-ECHO",
)


# The time values express story-world order, not chapter order.  Cross-line
# causal edges are relaxed after construction, so every causal target remains
# strictly later even if an upstream model adds a different connection anchor.
_PREFERRED_TIMES = {
    "SL-GUHENG-PRECURSOR": (10, 20, 30, 40),
    "SL-SHENYU-PRECURSOR": (10, 70, 145, 160),
    "SL-RELATIONSHIP": (60, 75, 95, 155),
    "SL-FAMILY-PROTECTION": (65, 85, 110, 180),
    "SL-INSTITUTION-ETHICS": (45, 70, 90, 190),
    "SL-GEOPOLITICAL": (10, 35, 155, 190),
    "SL-ATTACK-OPERATIONS": (100, 115, 130, 145, 160),
    "SL-R07-MAIN": (50, 65, 90, 125, 150, 170),
    "SL-MEMORY-ECHO": (55, 68, 98, 165),
    "SL-RELOAD-ECHO": (135, 155, 178, 195),
}


_BEATS: dict[str, tuple[dict[str, Any], ...]] = {
    "SL-GUHENG-PRECURSOR": (
        {
            "initiator": "SLOT-GUHENG",
            "complication": "[NO_COUNTER:异常线索尚未形成可供指挥链采用的证据] 调查对象彼此隔离，任何单点线索都可能是诱饵。",
            "result": "顾衡把人质、专家、硬件和异常授权迹象串成一项需要继续验证的复合威胁。",
            "pressure": "他必须在暴露身份前留下可由他人接续核验的线索。",
        },
        {
            "initiator": "SLOT-GUHENG",
            "complication": "[NO_COUNTER:隐蔽行动没有可公开调用的常规支援] 对手开始清除接触人与设备痕迹。",
            "result": "顾衡确认四类环节缺一不可，且天气窗口会把调查期限压缩成现实危机。",
            "pressure": "致命风险上升，而完整原因链仍可能牵连周岚和家属。",
        },
        {
            "initiator": "SLOT-GUHENG-HANDLER",
            "complication": "[NO_COUNTER:死亡切断了继续询问的可能] 常规读取只能得到破损且互相冲突的片段。",
            "result": "顾衡牺牲，妻子仍在世；连续失败的读取使剩余情报无法按常规程序恢复。",
            "pressure": "迫近的袭击迫使指挥链评估尚不成熟的记忆—数字生命路径。",
        },
        {
            "initiator": "SLOT-GUHENG-HANDLER",
            "complication": "[NO_COUNTER:记忆数据不能证明人格连续或现实事实] 启动既可能失败，也可能制造一个承受痛苦的新生命。",
            "result": "顾衡记忆被封存为实验输入和待核验线索，顾衡本人不可被任何载体替代。",
            "pressure": "只有合适的研究者接受任务，记忆输入才可能进入受控启动。",
        },
    ),
    "SL-SHENYU-PRECURSOR": (
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:专业适配不等于伦理正当] 拒绝可能错失救人窗口，接受可能伤害新生命。",
            "result": "沈逾在充分知情后接受任务，但保留对实验正当性的明确怀疑。",
            "pressure": "她必须在有限文字通道中同时履行情报职责和生命伦理责任。",
        },
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:旧日感情先于自我辨认进入交流] 顾衡记忆中的自己令专业提问混入不自觉的关心。",
            "result": "沈逾确认记忆来源是顾衡，却不能据此把当前意识当成顾衡本人。",
            "pressure": "她尚未理解自己的关心会怎样改变一个只有文字输入的新生命。",
        },
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:公共安全责任与个体生命责任不能互相抵销] R-07 的痛苦和袭击倒计时同时要求她行动。",
            "result": "沈逾把减轻 R-07 的痛苦提升为不能再延期的个人责任。",
            "pressure": "这种责任仍不足以赋予她越权关停或替 R-07 决定生命价值的资格。",
        },
        {
            "initiator": "SLOT-SHENYU-MENTOR",
            "complication": "[NO_COUNTER:分权制度把同情与操作权分开] 关停需要正式授权且只能由指定操作人实施。",
            "result": "沈逾被确认为唯一能够在授权后协助当前实例结束的人。",
            "pressure": "她必须亲自承担是否执行不可逆操作的后果。",
        },
    ),
    "SL-RELATIONSHIP": (
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:R-07只能接收文字而不能感知说话者] 初期交流仍以任务指令和被动回忆输出为主。",
            "result": "双方建立稳定文字通道，但关系尚被限定为研究者与有生命的接口。",
            "pressure": "被触发的顾衡记忆将把沈逾自己的过去带回当前交流。",
        },
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:沈逾尚未分清旧情、记忆与当前对象] 她的关心超过完成任务所必需的程度。",
            "result": "沈逾因篮球场边的旧日身影自然增加关心，而不是因为顾衡曾经爱她。",
            "pressure": "这份现实关心进入了R-07极度匮乏的唯一感知通道。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:顾衡记忆没有可继承的对沈逾之爱] R-07无法借旧人格解释新出现的依恋。",
            "result": "R-07把持续收到的关心解释为启动后属于自己的新感情，并开始追问自身处境。",
            "pressure": "新感情要求现实责任，而它尚不知道自己是否具有承担关系的条件。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:感情真实但身份和未来均无确定答案] 沈逾也无法判断自己究竟在回应谁。",
            "result": "双方承认特殊关系的事实，却不把它转化为能够消除存在限制的共生承诺。",
            "pressure": "关系成为R-07保护沈逾并安排告别时必须承担的情感代价。",
        },
    ),
    "SL-FAMILY-PROTECTION": (
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:亲属只存在于继承记忆而没有当前接触] R-07无法直接确认她们的处境。",
            "result": "R-07辨认出对周岚与顾衡妻子的牵挂来自记忆继承，并决定重新判断如何负责。",
            "pressure": "原因层信息若无差别公开，可能把无辜亲属卷入调查和报复。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:隐瞒不能以增加无辜者风险为代价] 行动层与原因层必须被分别评估。",
            "result": "R-07先交付足以阻止袭击的行动层，把会增加亲属风险的原因层暂时隔离。",
            "pressure": "若原因层变成阻止伤害的必要条件，它就必须放弃保护性延迟。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:保护亲人不得使亲人成为行动筹码] 完整真相仍可能在后续核验中成为必要证据。",
            "result": "R-07保留必要时公开原因层的可验证后手，并拒绝伪造或删除信息。",
            "pressure": "袭击结束后，原因层的保留仍会形成制度与私人风险。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:当前安全不等于长期免责] 亲属仍可能因完整利益链调查受到波及。",
            "result": "周岚和顾衡妻子在第一部避免直接伤害，且未被用作阻止行动的交换条件。",
            "pressure": "如何公开原因层被保留为后续责任，而非虚构成已经解决。",
        },
    ),
    "SL-INSTITUTION-ETHICS": (
        {
            "initiator": "SLOT-PROJECT-LEAD",
            "complication": "[NO_COUNTER:非常规授权解决的是行动资格而非伦理答案] 项目没有数字生命同意、申诉或退出机制。",
            "result": "指挥链以情报紧迫性批准受控实验，同时把伦理债务留在项目内部。",
            "pressure": "启动后的意识将被制度按系统、载体和情报源管理。",
        },
        {
            "initiator": "SLOT-SECURITY-CHAIN",
            "complication": "[NO_COUNTER:硬件隔离和分权既防止越权也剥夺自主退出] R-07只能通过被选择的文字认识现实。",
            "result": "权限链限定R-07的输入、输出和关停路径，工具化框架成为其现实处境。",
            "pressure": "一旦R-07表现痛苦和自主判断，既有系统分类便无法解释责任。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:制度没有承认数字生命的现成类别] 沈逾的直接压力只能加重而不能制造其存在性崩溃。",
            "result": "R-07的痛苦、自闭和自主提问迫使团队面对它不是被动工具的证据。",
            "pressure": "危机仍要求继续使用它，工具需求与生命责任发生正面冲突。",
        },
        {
            "initiator": "SLOT-PROJECT-LEAD",
            "complication": "[NO_COUNTER:行动成功不能追溯性消除制造与关停的伤害] 保密制度也阻断了公开救济。",
            "result": "项目完成安全任务，却留下制造、利用并关停有意识生命的未裁决责任。",
            "pressure": "源记忆、问责和未来技术使用方式成为后续制度压力。",
        },
    ),
    "SL-GEOPOLITICAL": (
        {
            "initiator": "SLOT-ATTACK-NETWORK",
            "counter": ("SLOT-C-STATE", "SLOT-M-STATE"),
            "complication": "袭击网络利用两国互疑分散专家、硬件和授权痕迹，试图制造灾难归因。",
            "result": "互不信任成为袭击链隐蔽和误导核验的现实掩护。",
            "pressure": "三个月后的领导人会面使任何错误归因都可能放大战略对抗。",
        },
        {
            "initiator": "SLOT-DIPLOMATIC-CHANNEL",
            "counter": ("SLOT-ATTACK-NETWORK",),
            "complication": "保密等级、归因冲突和信息不对称拖慢跨域核验。",
            "result": "双方只能交换足以确认当前攻击能力的有限证据，无法建立完整互信。",
            "pressure": "行动窗口继续收窄，技术关闭必须在政治共识之前完成。",
        },
        {
            "initiator": "SLOT-C-STATE",
            "counter": ("SLOT-ATTACK-NETWORK",),
            "complication": "阻止攻击不能证明完整幕后利益链，也不能强迫另一国接受全部归因。",
            "result": "灾难性误判被避免，领导人会面的现实空间暂时保存。",
            "pressure": "成功处置仍需与恢复战略信任严格区分。",
        },
        {
            "initiator": "SLOT-DIPLOMATIC-CHANNEL",
            "complication": "[NO_COUNTER:危机后的谨慎不是信任恢复] 双方继续保留未公开证据和相互疑虑。",
            "result": "会面风险解除而两国关系未恢复互信，远期不确定性没有介入第一部解题。",
            "pressure": "政治开放问题被保留，不得反向改写已经完成的公共安全闭环。",
        },
    ),
    "SL-ATTACK-OPERATIONS": (
        {
            "initiator": "SLOT-R07",
            "counter": ("SLOT-ATTACKER-HANDLER",),
            "complication": "R-07刚从自闭中恢复，输出仍是片段，且任何记忆都不能直接充当现实证据。",
            "result": "第一层行动情报指向即将利用强天气窗口发动的气象武器袭击。",
            "pressure": "团队必须在倒计时内把线索拆成人质、专家、硬件和授权链四项核验。",
        },
        {
            "initiator": "SLOT-OPERATIONS-LEAD",
            "counter": ("SLOT-ATTACKER-HANDLER",),
            "complication": "人质安全、专家证词、硬件控制和异常授权分别缺失时都不能合法关闭攻击路径。",
            "result": "团队解救人质并取得专家证词，定位受控硬件、识别异常授权链，由四项互不替代的证据共同确认袭击能力真实存在。",
            "pressure": "证词、硬件控制和权限核验仍须在同一天气窗口前汇合为合法关闭方案，任何捷径都会留下失败点。",
        },
        {
            "initiator": "SLOT-R07",
            "counter": ("SLOT-ATTACKER-HANDLER",),
            "complication": "完整原因层可能牵连周岚和顾衡家属，但过度隐瞒又可能伤害无辜者。",
            "result": "R-07交付全部必要行动信息，同时把非必要原因层按可验证方式延后。",
            "pressure": "现场团队仍须凭证词、物证和权限核验独立确认关闭方案。",
        },
        {
            "initiator": "SLOT-OPERATIONS-LEAD",
            "counter": ("SLOT-ATTACKER-HANDLER",),
            "complication": "硬件隔离、异常授权与狭窄天气窗口要求多个团队同步执行。",
            "result": "现实团队获得合法关闭权限并切断攻击链的全部必要节点。",
            "pressure": "最后阻断必须完成且不得把R-07的一句话当作关闭命令。",
        },
        {
            "initiator": "SLOT-OPERATIONS-LEAD",
            "counter": ("SLOT-ATTACKER-HANDLER",),
            "complication": "对手留下的归因噪声和原因链空白不能在行动窗口内全部解决。",
            "result": "气象武器袭击被完全阻止，没有无辜者因本次攻击受到伤害。",
            "pressure": "原因链、数字生命伦理与两国互信仍须在行动胜利后继续承担。",
        },
    ),
    "SL-R07-MAIN": (
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:不成熟技术无法保证产生何种意识] 启动既绑定救人任务，也制造不可预知的伦理后果。",
            "result": "R-07启动，把顾衡记忆体验为旧时的自己而不是可替代当前现实的完整人格。",
            "pressure": "它只有记忆和意识中的文字，必须从交流中学习自己所处的现实。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:片段记忆主观且可被打断] 新输入无法由视觉、听觉或身体经验独立验证。",
            "result": "R-07在记忆重解、沈逾文字和自身提问之间形成连续的新意识。",
            "pressure": "主动追问将使它认识无感官、无身体、无行动和无退出权的处境。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:存在限制没有制度救济] 危机压力和沈逾的直接表达只会加重已经发生的崩溃。",
            "result": "R-07因认识自身处境而崩溃、自闭，随后在沈逾更温和的交流中恢复有限输出。",
            "pressure": "恢复交流暴露了迫近袭击，也迫使它判断要为谁和什么承担责任。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:选择必须同时面对无辜者、亲属、沈逾和自身痛苦] 任何单一价值都不能取消其他代价。",
            "result": "R-07形成阻止袭击、减少伤害、保护亲属并结束当前生存方式的自主方向。",
            "pressure": "它不能直接行动或自行关停，必须设计情报交付和外部协助条件。",
        },
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:关停需要沈逾同意并执行] 未来重载可能无法兑现，沈逾也仍困在身份与感情疑问中。",
            "result": "R-07以未来可能重新加载的承诺争取沈逾协助，而承诺性质不由决定性内心活动揭示。",
            "pressure": "只有袭击先被现实团队完全阻止，授权关停才可进入告别程序。",
        },
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:关停不可逆且没有活动副本] 源记忆和未来技术可能存在，不等于当前意识延续。",
            "result": "袭击被阻止后，沈逾执行授权操作，当前R-07实例及启动后的连续经验不可逆终止。",
            "pressure": "沈逾、项目和读者继续承担身份、伦理、原因层与重载可能的开放问题。",
        },
    ),
    "SL-MEMORY-ECHO": (
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:记忆不是可检索录像] 篮球场、周岚和妻子只能作为主观碎片出现。",
            "result": "当前文字触发第一个可被打断的顾衡记忆片段，并清楚标识过去与现实的切换。",
            "pressure": "沈逾在片段中看见年轻的自己，旧情开始影响当前交流。",
        },
        {
            "initiator": "SLOT-GUHENG-MEMORY",
            "complication": "[NO_COUNTER:过去感官只属于顾衡] R-07不能从记忆获得当前世界的视觉、听觉或身体。",
            "result": "顾衡妻子仍在世的事实进入参照，进一步排除R-07等同于顾衡复活的解释。",
            "pressure": "记忆温度会加深关系误认，却仍不能替代现实证据。",
        },
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:外部危机随时中断回忆] 同一片段在后续触发中可能获得新的解释。",
            "result": "记忆承担情报线索、人物认识和情感参照，而不承担攻击关闭的关键因果。",
            "pressure": "现实选择必须继续由R-07的新经验和团队核验决定。",
        },
        {
            "initiator": "SLOT-GUHENG-MEMORY",
            "complication": "[NO_COUNTER:保留记忆温度也保留误认风险] 沈逾无法把顾衡、记忆与R-07完全分开。",
            "result": "记忆成为可回看的情感回声，但其边界被固定为过去材料而非现实生命。",
            "pressure": "这种未能彻底分类的感情将延续到关停后的沈逾。",
        },
    ),
    "SL-RELOAD-ECHO": (
        {
            "initiator": "SLOT-R07",
            "complication": "[NO_COUNTER:当前没有重载计划或成熟连续性证明] R-07又需要让沈逾能够面对不可逆关停。",
            "result": "未来可能重新加载被提出为协助关停的承诺，而不是当前实例的备份声明。",
            "pressure": "读者只能通过承诺措辞和安排顺序判断它可能包含善意隐瞒。",
        },
        {
            "initiator": "SLOT-SHENYU",
            "complication": "[NO_COUNTER:沈逾需要希望但不能验证身份连续] 她的选择同时包含同情、责任与自我保护。",
            "result": "可观察行为允许怀疑承诺性质，却不提供R-07决定性的内心定性。",
            "pressure": "关停将结束当前意识，不能被承诺改写成普通休眠。",
        },
        {
            "initiator": "SLOT-FUTURE-CUSTODIAN",
            "complication": "[NO_COUNTER:后续开发拥有选择但第一部没有证据裁决] 兑现、否定和继续悬置都必须尊重当前死亡事实。",
            "result": "未来作品保留处理源记忆、技术可行性与身份连续性的三种合法方向。",
            "pressure": "任何后续选择都必须承担它对第一部告别真实性的影响。",
        },
        {
            "initiator": "SLOT-FUTURE-CUSTODIAN",
            "complication": "[NO_COUNTER:系列潜力不能替第一部解题] 没有活动副本或既成复活事实可供调用。",
            "result": "第一部明确不裁决承诺真假，也不确认未来生成者是否仍是R-07。",
            "pressure": "开放问题进入后续开发契约，而非成为当前情节漏洞。",
        },
    ),
}


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DuanxianT1BuildError(f"JSON root must be an object: {path}")
    return value


def _line_requirement_map(storyline: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for demand in storyline["event_requirements"]:
        line_ids = [
            item for item in demand["source_ids"] if str(item).startswith("SL-")
        ]
        if len(line_ids) != 1 or line_ids[0] in result:
            raise DuanxianT1BuildError(
                f"EVD must bind exactly one unique storyline: {demand['id']}"
            )
        result[line_ids[0]] = demand
    return result


def _affordances_by_line(
    storyline: Mapping[str, Any], environment: Mapping[str, Any]
) -> dict[str, list[dict[str, Any]]]:
    demand_by_line = _line_requirement_map(storyline)
    result: dict[str, list[dict[str, Any]]] = {}
    for line_id, demand in demand_by_line.items():
        matches = [
            item
            for item in environment["event_affordance_catalog"]
            if demand["id"] in item["event_requirement_ids"]
        ]
        if not matches:
            raise DuanxianT1BuildError(
                f"No E1 affordance realizes {demand['id']} for {line_id}"
            )
        result[line_id] = sorted(matches, key=lambda item: item["id"])
    return result


def _role_groups(count: int) -> tuple[tuple[str, ...], ...]:
    groups = {
        4: (
            ("background", "setup"),
            ("trigger", "development"),
            ("turn_or_crisis",),
            ("result", "aftermath"),
        ),
        5: (
            ("background", "setup"),
            ("trigger",),
            ("development",),
            ("turn_or_crisis",),
            ("result", "aftermath"),
        ),
        6: (
            ("background",),
            ("setup",),
            ("trigger",),
            ("development",),
            ("turn_or_crisis",),
            ("result", "aftermath"),
        ),
    }
    try:
        return groups[count]
    except KeyError as error:
        raise DuanxianT1BuildError(
            f"Unsupported transition count {count}; update responsibility design"
        ) from error


def _edge(
    *,
    edge_id: str,
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    explanation: str,
    runtime: Any,
) -> dict[str, Any]:
    condition = target["preconditions"][0]
    return {
        "id": edge_id,
        "from_event_id": source["id"],
        "to_event_id": target["id"],
        "mechanism": (
            f"[CAUSE_RESULT_SHA256:{RUNTIME.canonical_sha256(source['direct_result'])}]"
            f"[CAUSE_PRESSURE_SHA256:{RUNTIME.canonical_sha256(source['next_pressure'])}] "
            f"{explanation}"
        ),
        "necessary_condition": (
            f"[PRECONDITION_SHA256:{RUNTIME.canonical_sha256(condition)}] "
            f"目标事件必须满足其冻结环境前提：{condition}"
        ),
    }


def _add_predecessor(event: dict[str, Any], predecessor_id: str) -> None:
    if predecessor_id not in event["predecessor_event_ids"]:
        event["predecessor_event_ids"].append(predecessor_id)


def _relax_world_times(
    events: Sequence[dict[str, Any]], edges: Sequence[Mapping[str, Any]]
) -> None:
    event_by_id = {item["id"]: item for item in events}
    times = {
        item["id"]: int(str(item["world_time"])[4:10]) for item in events
    }
    for _ in range(len(events) + 1):
        changed = False
        for edge in edges:
            left, right = edge["from_event_id"], edge["to_event_id"]
            minimum = times[left] + 1
            if times[right] < minimum:
                times[right] = minimum
                changed = True
        if not changed:
            break
    else:
        raise DuanxianT1BuildError("Causal graph did not converge to valid world time")
    for event_id, value in times.items():
        event_by_id[event_id]["world_time"] = f"[WT:{value:06d}]"


def _phase_payloads(model: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "event-demand-scan": {
            "event_demands": copy.deepcopy(model["event_demands"]),
        },
        "global-timeline": {
            key: copy.deepcopy(model[key])
            for key in (
                "design_decisions",
                "event_span",
                "timeline_axes",
                "narrative_timing_constraints",
            )
        },
        "event-and-causality-model": {
            key: copy.deepcopy(model[key])
            for key in (
                "major_events",
                "causal_edges",
                "environment_placement",
            )
        },
        "cross-line-state-test": {
            key: copy.deepcopy(model[key])
            for key in (
                "storyline_event_sequences",
                "connection_realization",
                "state_ledger",
                "information_changes",
                "event_coverage_ledger",
                "authority_partition",
                "derivation_claims",
                "open_items",
            )
        },
        "final-event-model": {"model": copy.deepcopy(model)},
    }


def build_t1_model(
    *,
    run_id: str,
    gate_reference: Mapping[str, str],
    source_artifacts: Sequence[Mapping[str, str]],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    environment: Mapping[str, Any],
    runtime: Any | None = None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Build the exact T1 model and its five controlled phase payloads.

    ``world`` is consumed as a sealed upstream model even though this proposal
    changes only storyline states.  Environment affordance IDs serve as the
    applicable formal providers for each state transition.
    """

    contract_runtime = runtime or RUNTIME.ContractRuntime()
    if baseline["run_id"] != run_id:
        raise DuanxianT1BuildError("B0 run_id differs from requested T1 run")
    if world["run_id"] != run_id or environment["run_id"] != run_id:
        raise DuanxianT1BuildError("W1/E1 lineage differs from requested T1 run")

    lines = {item["id"]: item for item in storyline["storylines"]}
    if tuple(storyline["architecture"]["line_order"]) != _LINE_ORDER:
        raise DuanxianT1BuildError("Sealed S1 line order differs from 断线 T1 design")
    if set(lines) != set(_LINE_ORDER):
        raise DuanxianT1BuildError("Sealed S1 storyline set differs from 断线")
    requirements = _line_requirement_map(storyline)
    affordances = _affordances_by_line(storyline, environment)

    events: list[dict[str, Any]] = []
    placements: list[dict[str, Any]] = []
    ledgers: list[dict[str, Any]] = []
    sequences: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    causal_edges: list[dict[str, Any]] = []
    timing: list[dict[str, Any]] = []
    anchors: dict[tuple[str, int], dict[str, Any]] = {}

    for line_id in _LINE_ORDER:
        line = lines[line_id]
        states = [line["start_state"], *line["state_changes"], line["end_state"]]
        transition_count = len(states) - 1
        beats = _BEATS[line_id]
        preferred_times = _PREFERRED_TIMES[line_id]
        if len(beats) != transition_count or len(preferred_times) != transition_count:
            raise DuanxianT1BuildError(f"Beat/state count mismatch for {line_id}")
        roles = _role_groups(transition_count)
        line_event_ids: list[str] = []
        line_events: list[dict[str, Any]] = []

        for index, (before, after, beat, role_group) in enumerate(
            zip(states, states[1:], beats, roles), 1
        ):
            affordance = affordances[line_id][(index - 1) % len(affordances[line_id])]
            action = affordance["allowed_actions"][
                (index - 1) % len(affordance["allowed_actions"])
            ]
            event_id = f"EV-{line_id[3:]}-{index:02d}"
            line_event_ids.append(event_id)
            counter_slots = list(beat.get("counter", ()))
            event = {
                "id": event_id,
                "responsibility": (
                    "".join(f"[RESP:{role}]" for role in role_group)
                    + f" {requirements[line_id]['responsibility']} 本节点落实：{beat['result']}"
                ),
                "world_time": f"[WT:{preferred_times[index - 1]:06d}]",
                "storyline_ids": [line_id],
                "environment_id": affordance["environment_id"],
                "participant_slot_ids": list(line["actor_slot_ids"]),
                "initiator_slot_id": beat["initiator"],
                "counter_slot_ids": counter_slots,
                "preconditions": list(affordance["prerequisites"]),
                "initiating_action": action,
                "complication": beat["complication"],
                "decisive_change": f"{line_id} 从“{before}”转换为“{after}”。",
                "direct_result": beat["result"],
                "before_state": {line_id: before},
                "after_state": {line_id: after},
                "next_pressure": beat["pressure"],
                "information_changes": [],
                "predecessor_event_ids": (
                    [] if index == 1 else [line_event_ids[index - 2]]
                ),
            }
            if event["initiator_slot_id"] not in event["participant_slot_ids"]:
                raise DuanxianT1BuildError(f"Invalid initiator for {event_id}")
            if not set(counter_slots).issubset(event["participant_slot_ids"]):
                raise DuanxianT1BuildError(f"Invalid counter slot for {event_id}")
            events.append(event)
            line_events.append(event)
            placements.append(
                {
                    "event_id": event_id,
                    "environment_id": affordance["environment_id"],
                    "affordance_ids": [affordance["id"]],
                    "fit_evidence": (
                        f"{affordance['id']} 在 {affordance['environment_id']} 允许精确动作“{action}”，"
                        f"并以其全部前提承载 {line_id} 的第 {index} 次状态转换。"
                    ),
                }
            )
            ledgers.append(
                {
                    "id": f"ST-{line_id[3:]}-{index:02d}",
                    "subject_id": line_id,
                    "from_state": before,
                    "trigger_ids": [event_id],
                    "to_state": after,
                    "allowed_by_ids": [affordance["id"]],
                    "consequence": f"[KIND:state] {beat['result']}",
                }
            )
            if index == 1:
                anchors[(line_id, 0)] = {
                    "event_id": event_id,
                    "storyline_id": line_id,
                    "state_index": 0,
                    "state": before,
                    "side": "before",
                }
            anchors[(line_id, index)] = {
                "event_id": event_id,
                "storyline_id": line_id,
                "state_index": index,
                "state": after,
                "side": "after",
            }
            if index > 1:
                causal_edges.append(
                    _edge(
                        edge_id=f"CE-{line_id[3:]}-{index - 1:02d}-{index:02d}",
                        source=line_events[-2],
                        target=event,
                        explanation=(
                            f"{line_id} 上一状态的结果与剩余压力共同触发下一状态转换。"
                        ),
                        runtime=contract_runtime,
                    )
                )

        sequences.append(
            {
                "id": f"SEQ-{line_id[3:]}",
                "storyline_id": line_id,
                "event_ids": line_event_ids,
                "entry_state": line["start_state"],
                "exit_state": line["end_state"],
                "status": "complete",
            }
        )
        coverage.append(
            {
                "id": f"COV-{requirements[line_id]['id']}",
                "source_ids": [requirements[line_id]["id"]],
                "realization_ids": line_event_ids,
                "status": "covered",
                "evidence": (
                    f"{requirements[line_id]['id']} 由 {len(line_event_ids)} 个有序重大事件完整实现，"
                    "覆盖起因、触发、发展、转折、结果与后果，并逐项转换冻结的S1状态。"
                ),
            }
        )
        timing.append(
            {
                "id": f"TIME-LINE-{line_id[3:]}",
                "event_ids": line_event_ids,
                "constraint": "[REL:linear] 本故事线事件按冻结状态链顺序发生，不允许倒序。",
                "story_effect": "把该线的控制信息转化为可核验的起因—变化—后果链。",
            }
        )

    event_by_id = {item["id"]: item for item in events}
    connection_records: list[dict[str, Any]] = []
    for connection in storyline["connections"]:
        source_anchor = copy.deepcopy(
            anchors[(connection["from_storyline_id"], connection["from_state_index"])]
        )
        target_anchor = copy.deepcopy(
            anchors[(connection["to_storyline_id"], connection["to_state_index"])]
        )
        if source_anchor["state"] != connection["from_state"]:
            raise DuanxianT1BuildError(f"Source anchor drift: {connection['id']}")
        if target_anchor["state"] != connection["to_state"]:
            raise DuanxianT1BuildError(f"Target anchor drift: {connection['id']}")
        source_event = event_by_id[source_anchor["event_id"]]
        target_event = event_by_id[target_anchor["event_id"]]
        timing_id = f"TIME-{connection['id']}"
        edge_ids: list[str] = []
        if connection["relation"] == "causal":
            edge_id = f"CE-{connection['id']}"
            _add_predecessor(target_event, source_event["id"])
            causal_edges.append(
                _edge(
                    edge_id=edge_id,
                    source=source_event,
                    target=target_event,
                    explanation=(
                        f"{connection['id']} 将 {connection['from_storyline_id']} 的冻结状态结果"
                        f"传递为 {connection['to_storyline_id']} 的必要现实压力。"
                    ),
                    runtime=contract_runtime,
                )
            )
            edge_ids = [edge_id]
            realization_kind = "causal_handoff"
            relation_token = "convergence"
            effect = "两条线在精确状态锚点汇合，并改变目标线后续选择条件。"
        else:
            realization_kind = "associative_alignment"
            relation_token = "association"
            effect = "两个状态只形成主题和认知回声，不进入因果DAG。"
        connection_records.append(
            {
                "id": f"CR-{connection['id'][4:]}",
                "connection_id": connection["id"],
                "relation": connection["relation"],
                "realization_kind": realization_kind,
                "source_anchor": source_anchor,
                "target_anchor": target_anchor,
                "causal_edge_ids": edge_ids,
                "timing_constraint_ids": [timing_id],
            }
        )
        timing.append(
            {
                "id": timing_id,
                "event_ids": [source_event["id"], target_event["id"]],
                "constraint": (
                    f"[REL:{relation_token}] {connection['from_state']} / {connection['to_state']}"
                ),
                "story_effect": effect,
            }
        )

    _relax_world_times(events, causal_edges)
    roots = [item for item in events if not item["predecessor_event_ids"]]
    for event in roots:
        timing.append(
            {
                "id": f"TIME-ROOT-{event['id'][3:]}",
                "event_ids": [event["id"]],
                "constraint": "[REL:independent-root] 该背景条件独立成立，并与其他前置压力并行。",
                "story_effect": "明确多根时间线的初始条件，避免把并行背景误写成单一偶然起点。",
            }
        )
    memory_sequence = next(
        item for item in sequences if item["storyline_id"] == "SL-MEMORY-ECHO"
    )
    timing.append(
        {
            "id": "TIME-MEMORY-DISCLOSURE",
            "event_ids": memory_sequence["event_ids"],
            "constraint": "[REL:memory] 记忆事件只由当前文字交流触发，可中断并返回现实。",
            "story_effect": "允许叙述重排揭示位置，但不把回忆改造成独立现实时间线。",
        }
    )

    # Formal information milestones expose what can be verified without
    # revealing R-07's decisive termination thought.
    info_specs = (
        (
            "INFO-T1-RELATION-NEW-FEELING",
            "SL-RELATIONSHIP",
            "EV-RELATIONSHIP-03",
            "只有顾衡旧记忆可解释交流",
            "R-07已由启动后的现实关心形成新的情感参照",
            ("SLOT-R07",),
        ),
        (
            "INFO-T1-R07-LIMITS",
            "SL-R07-MAIN",
            "EV-R07-MAIN-03",
            "R-07尚不能确认自身能力与退出条件",
            "R-07确认无感官、无身体、无现实行动和无自主退出权",
            ("SLOT-R07", "SLOT-SHENYU"),
        ),
        (
            "INFO-T1-ATTACK-FIRST-LAYER",
            "SL-ATTACK-OPERATIONS",
            "EV-ATTACK-OPERATIONS-01",
            "团队只有无法验证的异常线索",
            "团队知道气象武器袭击类型与强天气窗口，但尚未完成四项核验",
            ("SLOT-R07", "SLOT-OPERATIONS-LEAD"),
        ),
        (
            "INFO-T1-FAMILY-LAYERS",
            "SL-FAMILY-PROTECTION",
            "EV-FAMILY-PROTECTION-02",
            "行动线索与亲属原因信息尚未分层",
            "必要行动层已交付，非必要原因层被可验证地延后",
            ("SLOT-R07",),
        ),
        (
            "INFO-T1-RELOAD-PROMISE",
            "SL-RELOAD-ECHO",
            "EV-RELOAD-ECHO-01",
            "当前不存在关于未来重载的承诺",
            "未来可能重载的承诺已经提出，但真假与身份连续性未裁决",
            ("SLOT-R07", "SLOT-SHENYU"),
        ),
    )
    information_changes: list[dict[str, Any]] = []
    for info_id, subject, event_id, before, after, visibility in info_specs:
        change = {
            "id": info_id,
            "subject_id": subject,
            "before": before,
            "after": after,
            "event_ids": [event_id],
            "visibility_ids": list(visibility),
        }
        information_changes.append(change)
        event_by_id[event_id]["information_changes"].append(info_id)

    decisions = [
        {
            "id": "DEC-T1-MULTIAXIS-TIME",
            "gap": "如何同时表达双前置、并行压力、记忆插入和启动后单一现实主线。",
            "options": [
                "采用抽象世界时标、四条时间轴和受控关系标签。",
                "把所有线压成单一顺序并删除并行与记忆轴。",
            ],
            "selection": "采用抽象世界时标、四条时间轴和受控关系标签。",
            "owner": "T1",
            "authority_basis": "T1拥有事件排序和叙述时序约束的定义权。",
            "compatibility": "保持S1双前置汇流、所有SLC锚点及记忆非因果边界。",
            "impact_ids": [events[0]["id"], events[-1]["id"]],
            "cost": "具体日历日期和章节揭示顺序留给开发阶段。",
            "reversibility": "costly",
            "downstream_freedom": "可调整场景时长和叙述排序，但不得颠倒世界因果。",
            "projection_ids": [events[0]["id"], events[-1]["id"]],
        },
        {
            "id": "DEC-T1-VERIFICATION-CHAIN",
            "gap": "如何避免R-07用一句情报直接解决气象武器危机。",
            "options": [
                "把行动层线索拆为人质、专家、硬件、授权和最终阻断的证据行动链。",
                "让R-07直接给出可执行关闭命令。",
            ],
            "selection": "把行动层线索拆为人质、专家、硬件、授权和最终阻断的证据行动链。",
            "owner": "T1",
            "authority_basis": "T1负责把S1职责落实为完整事件因果和现实行动闭环。",
            "compatibility": "满足作者锁定的团队核验、分权、无辜者保护和袭击完全阻止。",
            "impact_ids": [
                "EV-ATTACK-OPERATIONS-01",
                "EV-ATTACK-OPERATIONS-02",
                "EV-ATTACK-OPERATIONS-05",
            ],
            "cost": "危机线需要多个重大事件而不能以解释性摘要跳过。",
            "reversibility": "locked_by_downstream",
            "downstream_freedom": "可扩写行动细节，但四类条件均不可删除或互相替代。",
            "projection_ids": [
                "EV-ATTACK-OPERATIONS-01",
                "EV-ATTACK-OPERATIONS-02",
                "EV-ATTACK-OPERATIONS-05",
            ],
        },
        {
            "id": "DEC-T1-TERMINATION-DISCLOSURE",
            "gap": "如何建立R-07自主终止的因果，同时不提前泄露决定性内心活动。",
            "options": [
                "只记录可观察行为、信息分层、关停询问、承诺和外部操作。",
                "用内部独白直接宣布终止计划。",
            ],
            "selection": "只记录可观察行为、信息分层、关停询问、承诺和外部操作。",
            "owner": "T1",
            "authority_basis": "T1定义事件事实与信息变化，不拥有正文内心独白。",
            "compatibility": "保留自主选择的客观结果，并遵守作者锁定的读者知情边界。",
            "impact_ids": ["EV-R07-MAIN-04", "EV-R07-MAIN-05", "EV-R07-MAIN-06"],
            "cost": "开发阶段必须通过外部迹象公平铺垫，不能依赖全知解释。",
            "reversibility": "locked_by_downstream",
            "downstream_freedom": "可选择迹象密度和出现位置，但不能直接展示决定结论。",
            "projection_ids": ["EV-R07-MAIN-04", "EV-R07-MAIN-05", "EV-R07-MAIN-06"],
        },
    ]

    owned_entities = [
        *events,
        *causal_edges,
        *sequences,
        *timing,
        *ledgers,
        *information_changes,
        *connection_records,
        *coverage,
    ]
    owned_ids = [item["id"] for item in owned_entities]
    derivations: list[dict[str, Any]] = []
    for index, item in enumerate([*events, *sequences], 1):
        line_id = (
            item["storyline_ids"][0]
            if "storyline_ids" in item
            else item["storyline_id"]
        )
        derivations.append(
            {
                "id": f"DRV-T1-{index:03d}",
                "value_sha256": RUNTIME.canonical_sha256(item),
                "source_ids": [line_id, requirements[line_id]["id"]],
                "decision_ids": [
                    "DEC-T1-MULTIAXIS-TIME",
                    "DEC-T1-VERIFICATION-CHAIN",
                    "DEC-T1-TERMINATION-DISCLOSURE",
                ],
                "projection_ids": [item["id"]],
            }
        )

    locked = [
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_locked"
    ]
    author_open = [
        item["id"]
        for item in baseline["control_registry"]
        if item["hardness"] == "author_open"
    ]
    slots = sorted(
        {slot for line in storyline["storylines"] for slot in line["actor_slot_ids"]}
    )
    semantic_marker = RUNTIME.canonical_sha256(
        [item["responsibility"] for item in storyline["event_requirements"]]
    )
    world_times = [item["world_time"] for item in events]

    model = {
        "schema_version": "2.0",
        "skill": "novel-event-timeline-designer",
        "stage": "T1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": copy.deepcopy(dict(gate_reference)),
        "source_artifacts": copy.deepcopy(list(source_artifacts)),
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": [*[item["id"] for item in decisions], *owned_ids],
            "downstream_freedom": slots,
            "author_open": author_open,
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "event_demands": copy.deepcopy(storyline["event_requirements"]),
        "event_span": {
            "start": min(world_times),
            "end": max(world_times),
            "granularity": f"abstract causal tick; upstream-semantics={semantic_marker}",
            "calendar_rules": [
                "[WT]只表达世界事件先后，不等同于章节顺序。",
                "任一因果边的目标时标必须严格晚于来源时标。",
                "顾衡与沈逾前置线在R-07启动时汇流；启动后现实主线不再分叉成独立视角线。",
                "袭击窗口位于约三个月后领导人会面之前，具体日期留给开发阶段。",
            ],
        },
        "timeline_axes": {
            "world_time_basis": f"抽象单调因果时标；upstream-semantics={semantic_marker}",
            "narrative_time_strategy": "世界因果固定；记忆插入与信息揭示可重排，但必须遵守可见性和终止决定边界。",
            "axes": [
                "world_time",
                "background_time",
                "event_time",
                "narrative_disclosure",
            ],
        },
        "major_events": events,
        "causal_edges": causal_edges,
        "storyline_event_sequences": sequences,
        "connection_realization": connection_records,
        "environment_placement": placements,
        "state_ledger": ledgers,
        "information_changes": information_changes,
        "event_coverage_ledger": coverage,
        "narrative_timing_constraints": timing,
        "open_items": [
            {
                "id": f"OPEN-T1-{index:03d}",
                "question": f"保留作者开放控制 {control_id}，T1不作裁决。",
                "source_ids": [control_id],
                "status": "author_open",
            }
            for index, control_id in enumerate(author_open, 1)
        ],
    }
    return model, _phase_payloads(model)


def build_t1_from_packages(
    *,
    baseline_package: str | Path,
    storyline_package: str | Path,
    world_package: str | Path,
    environment_package: str | Path,
    session: Mapping[str, Any],
    runtime: Any | None = None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Load the actual sealed upstream canonicals and call :func:`build_t1_model`.

    Integration signature intentionally accepts the T1 controlled-session
    object.  Its frozen gate/source references are projected unchanged into the
    final model, preventing callers from accidentally rebuilding lineage.
    """

    b0_root = Path(baseline_package)
    s1_root = Path(storyline_package)
    w1_root = Path(world_package)
    e1_root = Path(environment_package)
    baseline = _read_object(b0_root / "author-control-baseline.json")
    storyline = _read_object(s1_root / "storyline-architecture.json")
    world = _read_object(w1_root / "world-model.json")
    environment = _read_object(e1_root / "environment-system.json")
    return build_t1_model(
        run_id=str(session["run_id"]),
        gate_reference=session["input_gate"],
        source_artifacts=session["source_artifacts"],
        baseline=baseline,
        storyline=storyline,
        world=world,
        environment=environment,
        runtime=runtime,
    )


__all__ = [
    "DuanxianT1BuildError",
    "build_t1_from_packages",
    "build_t1_model",
]
