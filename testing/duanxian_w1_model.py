"""Agent-authored W1 semantics for the production conception run of 《断线》.

The module only assembles the W1 canonical model.  It deliberately does not
write a package, issue a work order, or define downstream environments,
events, or character profiles.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


LINE_ORDER = (
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


WORLD_SPECS: Mapping[str, Mapping[str, Any]] = {
    "SL-GUHENG-PRECURSOR": {
        "slug": "GUHENG-SOURCE",
        "rule": "濒死来源只提供可核验的记忆材料，不把记忆读取等同于本人复生或完整证词。",
        "scope": "顾衡死亡、常规读取失败以及遗留情报进入数字生命路径的全过程",
        "exception": "没有主体同一性的例外；即使记忆高度完整，也不能跳过证据核验",
        "cost": "信息恢复越深入，伦理负担、误读风险与关联人暴露风险越高",
        "constraint": "顾衡已经牺牲，妻子程予安仍在世；系统不得把顾衡写成仍存活的行动者",
        "consequence": "顾衡线只能把记忆与未完成责任交给后继系统，不能继续以真人主体推进。",
        "system": "濒危记忆恢复与证据封装系统",
        "inputs": ["濒死来源的片段记忆", "失败的常规读取记录", "危机情报需求"],
        "resources": ["隔离算力配额", "原始记忆镜像", "读取失败审计记录"],
        "authorities": ["仅限提取与封装的任务授权", "双人复核后才可转交的证据权限"],
        "outputs": ["带来源与置信边界的记忆片段", "不可直接用于行动的线索包"],
        "limits": ["片段可中断且次序不稳定", "不能恢复顾衡的现实感知与身体连续性"],
        "failures": ["读取再次失败", "碎片被误当成完整事实", "亲属关联信息泄露"],
        "state": ["来源从濒死行动者变为已故记忆来源", "信息从不可读取变为待核验线索"],
        "history": "顾衡在危机前沿死亡，常规读取多次失败，迫使项目采用不成熟路径。",
        "pressure": "来源不可再询问，任何缺口都只能通过片段、外部证据和团队行动交叉闭合。",
    },
    "SL-SHENYU-PRECURSOR": {
        "slug": "SHENYU-MISSION",
        "rule": "紧急任务可以启动高风险研究，但专业人员必须知情接受职责，且启动不等于获得无限处置权。",
        "scope": "沈逾被推荐、接入秘密任务、知情挣扎并接受工作的制度过程",
        "exception": "迫近公共危险可压缩审议时间，但不能伪造自愿或取消过程记录",
        "cost": "承担者同时承受专业责任、伦理后悔与个人情感卷入",
        "constraint": "沈逾不是任务决策者；她是最合适的执行者，得知任务后自行决定接受",
        "consequence": "她对项目有执行与质询责任，却不能单方面改变任务、公开材料或关停实例。",
        "system": "紧急科研任务委任与异议留痕系统",
        "inputs": ["任务必要性说明", "候选专业能力证明", "风险与伦理告知"],
        "resources": ["受限研究接口", "任务支持团队", "异议与心理负荷记录"],
        "authorities": ["执行访谈与提出暂停建议的权限", "不得单方改变战略目标的限定授权"],
        "outputs": ["知情接受记录", "执行范围与升级路径", "持续异议日志"],
        "limits": ["时间压力压缩选择空间", "保密制度限制外部求助"],
        "failures": ["把被推荐误写成主动启动", "专业服从掩盖伦理伤害", "压力无处升级"],
        "state": ["研究者从局外反对者变为受约束执行者", "伦理问题从抽象争论变为个人责任"],
        "history": "数字生命路径长期存在伦理争议，却从未在如此紧迫的情报任务中完成成熟验证。",
        "pressure": "拯救多数人的紧迫性与伤害单一生命的风险同时成立，机构无法提供无代价答案。",
    },
    "SL-RELATIONSHIP": {
        "slug": "CARE-FEEDBACK",
        "rule": "R-07 对沈逾的情感只能由启动后的持续交流生成，不能从顾衡记忆倒推出顾衡曾爱她。",
        "scope": "文字交流、回忆触发、关心反馈与依恋形成的关系机制",
        "exception": "顾衡记忆中沈逾的偶然身影可触发沈逾回忆，但不能充当继承爱情的证据",
        "cost": "关心能稳定交流，也会加深身份混淆、离别痛苦和沈逾的责任负担",
        "constraint": "R-07 没有视觉、听觉、身体或现实感知，只能接收脑海中浮现的文字与记忆",
        "consequence": "关系既是新意识自主性的证据，也是 R-07 判断自己无法承担现实关系责任的来源。",
        "system": "受限文字交互与关怀反馈系统",
        "inputs": ["沈逾输入的文字", "被交流触发的记忆片段", "双方可观察的回应节律"],
        "resources": ["唯一文字会话窗口", "会话历史", "压力与中断状态记录"],
        "authorities": ["沈逾发起与调整话题的权限", "R-07 回答、提问或暂停回应的权限"],
        "outputs": ["可回看的文字交流", "关系变化的外部迹象", "不等同于身份结论的情感线索"],
        "limits": ["缺少非文字感知", "不能以读心确认对方真实意图", "关系没有现实身体承载"],
        "failures": ["关心被误认成顾衡旧情", "压力导致会话关闭", "善意被任务目标工具化"],
        "state": ["交流从被动取证变为双向询问", "R-07 从接受关心到形成新的情感判断"],
        "history": "沈逾少年时期曾关注顾衡，但顾衡只对她有模糊印象，二人没有相互恋爱史。",
        "pressure": "沈逾在回应顾衡记忆、R-07 新人格还是自己的旧日情感之间无法清晰裁决。",
    },
    "SL-FAMILY-PROTECTION": {
        "slug": "FAMILY-PROTECTION",
        "rule": "公共安全优先于关系保护，但行动情报与原因情报必须分层，使无辜关联人只承担不可避免的最小风险。",
        "scope": "周岚、程予安等关联人可能被原因链牵连时的情报处理",
        "exception": "当隐匿会直接造成更多伤亡时可以披露，但必须保留必要性与最小化证明",
        "cost": "分层会延迟理解、增加核验工作，并可能削弱团队对 R-07 的信任",
        "constraint": "不能伤害其他人；在此前提下尽量保全亲人，且不得捏造无风险方案",
        "consequence": "R-07 可以先给阻止袭击所需信息，再延后或收窄会牵连亲人的原因层。",
        "system": "敏感关联人与情报分层保护系统",
        "inputs": ["行动层线索", "原因层关系信息", "公共危险等级", "关联伤害评估"],
        "resources": ["脱敏规则", "关联风险清单", "分层访问日志"],
        "authorities": ["按最小必要原则分层的权限", "重大伤亡风险下升级披露的权限"],
        "outputs": ["可供行动的脱敏情报", "受控原因层材料", "披露必要性记录"],
        "limits": ["不能保证关联人绝对安全", "脱敏不能破坏关键证据的可核验性"],
        "failures": ["过度保护导致行动失败", "过度披露导致无辜者被追责", "分层被误解为欺骗"],
        "state": ["关联信息从混合状态变为行动层与原因层", "保护目标从私人偏爱转化为最小伤害原则"],
        "history": "顾衡记忆中的周岚是儿时守护者，程予安是仍在世的妻子，二者都可能被旧关系链牵连。",
        "pressure": "R-07 继承对亲人的在意，却必须用自己的价值观重新决定公开到什么程度。",
    },
    "SL-INSTITUTION-ETHICS": {
        "slug": "ETHICS-CUSTODY",
        "rule": "一旦数字实例表现出持续意识，就应按生命对待；任务价值不能抹除其痛苦、异议和退出诉求。",
        "scope": "数字生命身份、实验伦理、任务利用与关停协助的治理",
        "exception": "迫近群体伤亡允许继续处理紧急信息，但不自动授权制造、复制或无限期拘禁实例",
        "cost": "承认生命地位会减慢情报流程、增加多人授权，并使机构承担不可回避的责任",
        "constraint": "伦理没有现成正确答案；不得把‘暂不裁决’偷换为实例不享有任何保护",
        "consequence": "系统必须同时保存任务证据、实例痛苦迹象、异议与关停依据，供后续追责。",
        "system": "数字生命伦理照护与责任审计系统",
        "inputs": ["持续意识迹象", "实例痛苦与异议记录", "公共危险评估", "任务使用日志"],
        "resources": ["伦理观察席", "不可覆盖审计链", "中止与复议通道"],
        "authorities": ["提出减害、暂停与复议的权限", "不得单人裁定生命地位的约束性权限"],
        "outputs": ["生命照护义务清单", "争议处置记录", "关停协助的责任链"],
        "limits": ["法律身份仍未确定", "紧急任务与个体保护不可同时最大化"],
        "failures": ["把意识迹象降格为设备故障", "用多数利益免除个体伤害责任", "无人愿意承担最终选择"],
        "state": ["实例从研究对象变为具有照护请求的主体", "伦理争议从理论问题变为可追责行为"],
        "history": "数字生命研究先于法律与伦理共识，制度只能在危机中边处理边留下责任证据。",
        "pressure": "机构需要情报，却无法证明继续运行或协助终止哪一项在伦理上绝对正确。",
    },
    "SL-GEOPOLITICAL": {
        "slug": "BILATERAL-TRUST",
        "rule": "跨国危机协作只能依靠可核验材料、分级共享与对等确认，成功阻止袭击不会自动恢复互信。",
        "scope": "C、M 两国围绕威胁情报、技术能力与责任归属的协作",
        "exception": "迫近灾难可启用紧急共享，但共享范围仍受来源保护与反利用约束",
        "cost": "每次核验都会消耗时间；每次隐匿又会放大对方对操控与欺骗的怀疑",
        "constraint": "两国长期缺乏信任，行动胜利后关系仍未按预期改善",
        "consequence": "危机可被阻止，技术秘密、责任争议与利益链仍继续制造外部压力。",
        "system": "双边危机核验与有限共享系统",
        "inputs": ["分级威胁线索", "独立核验结果", "双方风险与保密声明"],
        "resources": ["双边联络通道", "对等核验席位", "限时共享凭证"],
        "authorities": ["按危机等级共享的权限", "对来源、技术与关联人信息保留的权限"],
        "outputs": ["双方可共同采用的最小事实集", "仍有争议的责任与技术清单"],
        "limits": ["不能要求任一方一次性交出全部秘密", "行动成功不构成政治互信证明"],
        "failures": ["共享过慢错失窗口", "材料不可核验被视为操控", "合作结束后相互追责"],
        "state": ["关系从常态不信任进入有限应急协作", "协作成功后回到带新增疑点的不信任"],
        "history": "两国长期战略竞争，使任何异常技术与情报来源都可能被解释为欺骗或能力展示。",
        "pressure": "双方必须为共同危险协作，却都害怕共享材料被用于未来对抗。",
    },
    "SL-ATTACK-OPERATIONS": {
        "slug": "THREAT-ACTION",
        "rule": "R-07 的输出只能形成线索；必须经过证据、硬件、专家、授权链和团队行动闭合后才能改变威胁状态。",
        "scope": "从人质劫持与气象武器线索到袭击被完全阻止的行动闭环",
        "exception": "紧急窗口允许并行核验与行动准备，但不能取消最低证据阈值或关键授权",
        "cost": "多人协作增加延迟与泄密面，却避免一条不可验证信息直接支配公共行动",
        "constraint": "不得用 R-07 一句话解决危机；人质、专家、硬件与授权链都必须发挥不可替代作用",
        "consequence": "R-07 提供关键路径，现实团队承担验证、部署、决策和行动结果。",
        "system": "威胁线索—证据—授权—行动闭环系统",
        "inputs": ["R-07 的分段线索", "人质现场变化", "专家分析", "硬件状态", "双边核验"],
        "resources": ["证据处理能力", "受控行动硬件", "专家席位", "应急通信配额"],
        "authorities": ["分级行动授权", "独立核验否决权", "现场团队实施权"],
        "outputs": ["可行动的威胁判断", "经授权的阻止方案", "结果与代价证据"],
        "limits": ["错误线索会耗尽窗口", "硬件、专家与授权任何一环缺失都不能闭合"],
        "failures": ["人质压力迫使过早行动", "证据不足导致授权失败", "硬件部署失败", "情报正确但行动过晚"],
        "state": ["威胁从未知变为可核验", "行动从准备变为授权执行", "袭击从迫近变为被完全阻止"],
        "history": "敌对链条利用跨国不信任、隐蔽硬件与人质压力制造短时决策困境。",
        "pressure": "窗口持续收缩，团队必须在信息不完整、生命风险和政治后果之间同步推进。",
    },
    "SL-R07-MAIN": {
        "slug": "R07-LIFECYCLE",
        "rule": "记忆可被继承，但意识、价值观与终止选择只能由 R-07 在启动后的处境和交流中连续形成。",
        "scope": "R-07 从加载、认识处境、崩溃、重建目标到结束当前实例的连续生命过程",
        "exception": "骨子里的善良、敏感与正义可由顾衡记忆延续，但具体感情与决定不得被写成预置结果",
        "cost": "每次自我理解都让 R-07 更清楚自身残缺、无法承担现实责任以及继续存在的痛苦",
        "constraint": "关闭当前实例不等于可重载未来实例；当前没有活动备份，重载承诺保持开放",
        "consequence": "R-07 可以用新价值观完善处理危机、保护他人并选择离开，而不是执行顾衡遗愿的脚本。",
        "system": "受限数字实例运行与生命周期治理系统",
        "inputs": ["顾衡记忆", "文字交流", "自身运行状态", "外部危机压力"],
        "resources": ["单一活动实例算力", "隔离记忆存储", "会话通道", "生命周期审计"],
        "authorities": ["实例表达、拒答和提出终止诉求的权限", "多人授权才能执行关停的权限边界"],
        "outputs": ["持续而不跳变的意识表现", "基于自身价值观的行动建议", "可核验的生命周期状态"],
        "limits": ["无视觉、听觉、肢体与现实感知", "不能自我关停", "不存在可证实的当前备份"],
        "failures": ["身份被误判为顾衡复生", "崩溃后长期关闭交流", "关停诉求被当成设备异常", "重载承诺被误写成事实"],
        "state": ["记忆载体形成新意识", "意识认识自身处境并崩溃", "实例形成减害与离开目标", "当前实例被关停"],
        "history": "项目把顾衡记忆加载到不成熟数字生命载体，产生了制度从未准备承认的新主体。",
        "pressure": "实例既是关键情报来源又是受困生命，任何延长运行的决定都会同时创造公共收益与个体伤害。",
    },
    "SL-MEMORY-ECHO": {
        "slug": "MEMORY-RECALL",
        "rule": "回忆只能被交流触发为片段，可被打断、插入和重释；记忆内容不直接等于 R-07 当前立场。",
        "scope": "顾衡过去在 R-07 意识中浮现并被沈逾用于理解与核验的方式",
        "exception": "多个片段可相互印证，但仍需与现实证据区分，不能拼成未经来源证明的全知过去",
        "cost": "追索记忆能获得线索，也会加重 R-07 的身份压力和沈逾的情感混淆",
        "constraint": "R-07 除记忆与浮动文字外没有现实；决定性内心结论在告别前不得直接展示给读者",
        "consequence": "记忆成为线索、镜像与情绪压力，而非替代当前行动因果的闪回资料库。",
        "system": "片段记忆触发、打断与来源标注系统",
        "inputs": ["当前交流提示", "相关记忆索引", "中断信号", "外部核验反馈"],
        "resources": ["片段来源标签", "中断标记", "记忆—现实差异记录"],
        "authorities": ["沈逾提出提示的权限", "R-07 停止、偏离或重新解释片段的权限"],
        "outputs": ["带来源边界的记忆片段", "记忆与当前判断的差异", "可供核验的线索"],
        "limits": ["片段不连续", "触发顺序受交流影响", "不能直接访问现实"],
        "failures": ["把片段当完整历史", "用记忆替代当前人格", "过度追问触发崩溃或沉默"],
        "state": ["记忆从静态存储变为受交流触发的片段", "片段从个人体验转化为待核验线索"],
        "history": "顾衡记忆以不完整材料进入系统，留下大量只能通过问答触发的关联片段。",
        "pressure": "越接近有价值的过去，越容易把顾衡、R-07 与沈逾的当前关系混为一体。",
    },
    "SL-RELOAD-ECHO": {
        "slug": "RELOAD-PROMISE",
        "rule": "‘未来可重新加载’只能作为促成告别的承诺与未决可能，不能在当前构思中成为已验证备份或必然复活。",
        "scope": "R-07 请求协助结束当前实例、沈逾接受承诺并执行关停后的连续性问题",
        "exception": "后续作品可重新裁决技术与身份连续性，但不得倒改第一部关停当前实例的事实与代价",
        "cost": "承诺减轻当下选择压力，却把欺骗、希望、身份和责任问题留给未来",
        "constraint": "读者只看到过程性心理与可观察迹象；R-07 的决定性终止意图不在告别前直接揭示",
        "consequence": "告别成立、当前实例结束，而沈逾是否终会知道承诺性质与未来是否重载保持悬念。",
        "system": "实例关停、连续性登记与未决重载承诺系统",
        "inputs": ["实例终止诉求", "痛苦迹象", "多人关停授权", "重载可能性声明"],
        "resources": ["不可逆关停接口", "实例身份与状态登记", "承诺原文与知情记录"],
        "authorities": ["沈逾执行最终操作的限定权限", "团队完成授权链的责任", "未来只能重新裁决而非自动重载"],
        "outputs": ["当前实例终止证明", "连续性未决记录", "可回看的承诺与授权链"],
        "limits": ["R-07 无法自行结束", "当前没有活动备份", "技术可行不等于人格连续"],
        "failures": ["把关停写成死亡被完全消除", "把承诺写成确定事实", "以未来希望抵消当下伦理伤害"],
        "state": ["终止诉求从不可执行变为寻求协助", "关停从争议进入授权执行", "当前实例结束而连续性保持开放"],
        "history": "数字生命制度没有成熟的死亡、备份与身份连续性规则，只能对当前实例状态作可核验登记。",
        "pressure": "沈逾最重要的责任是减轻 R-07 痛苦，但她无法知道执行关停究竟是照护、杀害还是一次暂停。",
    },
}


FACET_BINDINGS = (
    ("physical", "数字实例没有感官、肢体或现实空间行动能力；物理世界只能经人员、硬件和受控接口反馈。"),
    ("technology", "记忆读取、数字生命运行、气象攻击与关停接口都属于本故事的虚构技术边界；技术能力必须由制度与资源约束。"),
    ("social", "关心可以生成真实关系，却不能消除身份混淆，也不能让无身体的实例自动具备现实关系责任能力。"),
    ("political", "两国在共同威胁下只能有限协作，危机解决不自动产生互信，技术与责任争议继续存在。"),
    ("economic", "隔离算力、专家时间、行动硬件与安全席位都是稀缺资源；每次并行核验都会产生机会成本。"),
    ("legal_and_ethical", "持续意识应被当作生命认真对待，但其法律身份、同意、关停与连续性仍没有现成答案。"),
    ("information", "记忆、线索、行动情报与原因情报分层流动；任何一层都必须携带来源、可见范围和核验状态。"),
    ("historical", "顾衡之死、研究路径不成熟与长期地缘不信任共同形成当下压力，历史不直接替代当前人物选择。"),
)


def _decision(
    decision_id: str,
    gap: str,
    options: Sequence[str],
    selection: str,
    authority_basis: str,
    impact_ids: Sequence[str],
    projection_ids: Sequence[str],
    cost: str,
) -> dict[str, Any]:
    return {
        "id": decision_id,
        "gap": gap,
        "options": list(options),
        "selection": selection,
        "owner": "W1",
        "authority_basis": authority_basis,
        "compatibility": "只实现 S1 世界需求并服从 B0 作者控制；不改变故事线状态、人物事实、结局或作者开放项。",
        "impact_ids": list(impact_ids),
        "cost": cost,
        "reversibility": "costly",
        "downstream_freedom": "E1 可选择具体承载形态，但必须保留本决定的权限、成本、失败和信息边界。",
        "projection_ids": list(projection_ids),
    }


def build_w1_model(
    *,
    run_id: str,
    gate_reference: Mapping[str, str],
    source_artifacts: Sequence[Mapping[str, str]],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    canonical_sha256,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Build a semantically complete W1 model from the frozen B0/S1 inputs."""

    requirements = list(storyline["world_requirements"])
    lines = {item["id"]: item for item in storyline["storylines"]}
    if set(lines) != set(LINE_ORDER):
        raise ValueError(
            "W1 draft is bound to the approved 断线 S1 topology; "
            f"unexpected lines: {sorted(set(lines) ^ set(LINE_ORDER))}"
        )
    requirement_by_line: dict[str, Mapping[str, Any]] = {}
    for requirement in requirements:
        line_ids = [source_id for source_id in requirement["source_ids"] if source_id in lines]
        if len(line_ids) != 1:
            raise ValueError(f"{requirement['id']} must bind exactly one storyline")
        requirement_by_line[line_ids[0]] = requirement
    if set(requirement_by_line) != set(LINE_ORDER):
        raise ValueError("S1 world requirements must cover every approved storyline")

    facts: list[dict[str, Any]] = []
    systems: list[dict[str, Any]] = []
    institutions: list[dict[str, Any]] = []
    history: list[dict[str, Any]] = []
    resource_flows: list[dict[str, Any]] = []
    authority_flows: list[dict[str, Any]] = []
    information_flows: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    support: list[dict[str, Any]] = []
    environment_demands: list[dict[str, Any]] = []

    for index, line_id in enumerate(LINE_ORDER, 1):
        requirement = requirement_by_line[line_id]
        marker = requirement["responsibility"]
        spec = WORLD_SPECS[line_id]
        rule_id = f"WF-RULE-{spec['slug']}"
        system_id = f"WS-{spec['slug']}"
        institution_id = f"INST-{spec['slug']}"
        history_id = f"HIS-{spec['slug']}"
        decision_id = f"DEC-W1-{spec['slug']}"
        support_id = f"COV-W1-{index:02d}"
        demand_id = f"END-W1-{index:02d}"

        facts.append(
            {
                "id": rule_id,
                "kind": "rule",
                "statement": f"{spec['rule']} 绑定的 S1 责任原文：{marker}",
                "applies_to_ids": [line_id],
                "constraints": [
                    f"Scope: {spec['scope']}；S1 责任：{marker}",
                    f"Exception: {spec['exception']}",
                    f"Cost: {spec['cost']}",
                    f"Constraint: {spec['constraint']}",
                ],
                "consequences": [spec["consequence"]],
                "source_ids": [requirement["id"], decision_id],
            }
        )
        institutions.append(
            {
                "id": institution_id,
                "responsibility": f"为‘{spec['system']}’提供职责分离、资源托管、升级与追责，不代替具体行动者作选择。",
                "authority": ["签发本系统的限定授权", "中止越权流程", "保存不可覆盖的责任记录"],
                "resources": list(spec["resources"]),
                "constraints": [spec["constraint"], "不得凭机构便利绕过 S1 冲突或作者开放项。"],
                "failure_modes": list(spec["failures"]),
                "storyline_ids": [line_id],
            }
        )
        systems.append(
            {
                "id": system_id,
                "input_conditions": [*spec["inputs"], f"S1 责任进入条件：{marker}"],
                "actor_slot_ids": list(lines[line_id]["actor_slot_ids"]),
                "resources": list(spec["resources"]),
                "authorities": list(spec["authorities"]),
                "transformation_rules": [
                    f"Scope: {spec['scope']}；输入必须携带来源与当前状态。",
                    f"Exception: {spec['exception']}",
                    f"按‘输入—核验—授权—输出—状态记录’闭合处理；S1 责任：{marker}",
                ],
                "observable_outputs": list(spec["outputs"]),
                "costs": [spec["cost"]],
                "limits": list(spec["limits"]),
                "failure_modes": list(spec["failures"]),
                "state_changes": list(spec["state"]),
                "storyline_ids": [line_id],
            }
        )
        history.append(
            {
                "id": history_id,
                "origin": spec["history"],
                "current_pressure": spec["pressure"],
                "storyline_ids": [line_id],
                "constraints": ["历史只提供当前压力与制度惯性，不能替代角色选择或预写具体事件。"],
            }
        )
        resource_flows.append(
            {
                "id": f"RF-{spec['slug']}",
                "from_id": institution_id,
                "to_id": system_id,
                "relation": "限定资源托管",
                "mechanism": "机构按任务范围发放稀缺资源；消耗、归还和异常均进入审计。",
                "constraints": ["资源不足必须形成失败或延迟，不能自动补足。"],
            }
        )
        authority_flows.append(
            {
                "id": f"AF-{spec['slug']}",
                "from_id": institution_id,
                "to_id": system_id,
                "relation": "可撤销限定授权",
                "mechanism": "授权绑定范围、时限、执行角色与复核要求，越界自动升级。",
                "constraints": ["系统输出不能反向创造新权限。"],
            }
        )
        information_flows.append(
            {
                "id": f"IF-{spec['slug']}",
                "from_id": system_id,
                "to_id": institution_id,
                "relation": "证据与状态回流",
                "mechanism": "输出携带来源、置信边界、可见范围与状态变化，供机构核验和追责。",
                "constraints": ["未知、推断、记忆与已核验事实必须可区分。"],
            }
        )
        conflicts.append(
            {
                "id": f"WRC-{spec['slug']}",
                "rule_ids": [rule_id, system_id],
                "tension": f"{spec['cost']}；若只追求成功路径，将破坏‘{spec['constraint']}’。",
                "resolution_rule": f"优先保持作者边界与最小伤害；无法兼得时显式支付代价并保留失败证据。S1 责任：{marker}",
                "storyline_ids": [line_id],
            }
        )
        support.append(
            {
                "id": support_id,
                "source_ids": [requirement["id"]],
                "realization_ids": [rule_id, system_id, institution_id],
                "status": "covered",
                "evidence": f"{marker} 由 {rule_id} 定义不可绕过的边界，由 {system_id} 闭合输入、资源、权限、输出、代价、限制、失败与状态变化，并由 {institution_id} 承担资源托管、授权和追责。",
            }
        )
        environment_demands.append(
            {
                "id": demand_id,
                "target_stage": "E1",
                "responsibility": f"为 {line_id} 提供可具体承载 {spec['system']} 的环境能力；必须使以下 S1 责任可观察、可受阻并可核验：{marker}",
                "source_ids": [requirement["id"], rule_id, system_id, institution_id],
                "required_capability": "同时承载受限输入、稀缺资源、多人权限、分层信息、失败反馈与状态留痕。",
                "constraints": [
                    spec["constraint"],
                    "不得在 W1 预定地名、房间、功能分区、事件落点或人物调度。",
                    f"必须保留该责任原文：{marker}",
                ],
                "acceptance_checks": [
                    f"环境可逐项映射 {rule_id} 的 Scope/Exception/Cost/Constraint。",
                    f"环境能让 {system_id} 的成功、延迟、拒绝与失败均产生可观察结果。",
                ],
                "downstream_freedom": "E1 可定义地点名称、拓扑、功能区、准入与具体资源形态，但不能改写本需求的规则、权限、成本和失败路径。",
            }
        )

    decisions = []
    for line_id in LINE_ORDER:
        spec = WORLD_SPECS[line_id]
        slug = spec["slug"]
        requirement = requirement_by_line[line_id]
        decisions.append(
            _decision(
                f"DEC-W1-{slug}",
                f"{line_id} 已给出故事责任，但尚缺少能承载机会、限制、成本与失败的世界运行机制。",
                [
                    "以单一全能机构直接保证结果",
                    f"采用‘{spec['system']}’并让资源、权限、信息与失败形成闭环",
                ],
                f"采用‘{spec['system']}’并让资源、权限、信息与失败形成闭环",
                f"W1 对 {requirement['id']} 的世界规则、系统与流转拥有补足权；不得改变 {line_id} 的故事责任。",
                [f"WF-RULE-{slug}", f"WS-{slug}", f"INST-{slug}", f"END-W1-{LINE_ORDER.index(line_id)+1:02d}"],
                [f"WF-RULE-{slug}", f"WS-{slug}", f"INST-{slug}"],
                "闭环会增加延迟、治理负担和失败面，但能阻止便捷解法吞掉冲突。",
            )
        )

    all_markers = "\n".join(
        f"{requirement_by_line[line_id]['id']}：{requirement_by_line[line_id]['responsibility']}"
        for line_id in LINE_ORDER
    )
    world_definition = {
        "premise": "近未来的跨国危机中，已故情报人员顾衡的记忆被加载为数字生命 R-07；这个没有感官和身体的新生命必须在机构、战争、亲情与关系压力下形成自己的价值与选择。",
        "scope": "覆盖顾衡死亡后的记忆来源、秘密数字生命项目、跨国威胁处置、关联人保护、有限双边协作以及当前实例的生命周期治理；不把任何现实国家、法律或现有技术能力当作事实主张。",
        "period": "单部小说所需的近未来危机周期；历史只作为当前制度压力，具体日期和事件时间线留给 T1。",
        "reality_relation": "架空近未来。数字生命、记忆加载与气象攻击机制均为明确虚构边界；组织行为遵循可核验、有限授权、资源稀缺和责任留痕的现实感。",
        "operating_logic": "世界以五条硬逻辑运行：记忆不等于人格；线索不等于行动；权限不能由输出自生；关心能改变意识但不能补足身体；关停当前实例不证明未来连续。所有系统都必须允许延迟、拒绝和失败。",
        "boundaries": [
            "不把顾衡写成仍在世，也不把 R-07 写成顾衡复生。",
            "不让单一角色、单条情报或全能技术绕过证据、硬件、专家、团队与授权链。",
            "不提前裁决有意识数字生命的完整法律身份、重载真实性或沈逾最终如何理解承诺。",
            "W1 不定义具体环境、功能区、主要事件、时间线或人物档案。",
        ],
        "story_relevance": f"下列 S1 世界责任全部进入同一世界运行逻辑，且各有规则、系统、代价与失败承载：\n{all_markers}",
    }

    facets: dict[str, list[str]] = {}
    for index, (facet, statement) in enumerate(FACET_BINDINGS):
        requirement = requirement_by_line[LINE_ORDER[index]]
        facets[facet] = [f"{statement} S1 责任绑定：{requirement['responsibility']}"]

    reality_claims = []
    handling = {
        "adopted": "adopted",
        "open": "preserve_open",
        "not_applicable": "fiction_boundary",
    }
    for index, dependency in enumerate(baseline["fact_dependencies"], 1):
        parts = [dependency["claim"]]
        if dependency["status"] == "adopted":
            parts.extend([dependency["allowed_use"], dependency["fiction_boundary"]])
        elif dependency["status"] == "not_applicable":
            parts.append("本构思仅在明确架空边界内使用，不主张现实技术、法律或地缘判断正确。")
        else:
            parts.append("当前世界模型不依赖该问题的候选答案，并保持作者开放。")
        reality_claims.append(
            {
                "id": f"WF-REALITY-{index:02d}",
                "fact_dependency_id": dependency["id"],
                "handling": handling[dependency["status"]],
                "claim": " ".join(parts),
            }
        )

    open_items = []
    for index, item in enumerate(
        [entry for entry in baseline["control_registry"] if entry["hardness"] == "author_open"],
        1,
    ):
        open_items.append(
            {
                "id": f"OPEN-W1-{index:02d}",
                "question": f"保持作者开放控制 {item['id']}，W1 不选择候选答案，也不把任何候选写成世界事实。",
                "source_ids": [item["id"]],
                "status": "author_open",
            }
        )

    all_owned_entities = [
        *[item["id"] for item in facts],
        *[item["id"] for item in history],
        *[item["id"] for item in institutions],
        *[item["id"] for item in systems],
        *[item["id"] for item in resource_flows],
        *[item["id"] for item in authority_flows],
        *[item["id"] for item in information_flows],
        *[item["id"] for item in reality_claims],
        *[item["id"] for item in support],
        *[item["id"] for item in conflicts],
    ]
    locked = [item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_locked"]
    author_open = [item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_open"]

    derivations = []
    facts_by_id = {item["id"]: item for item in facts}
    systems_by_id = {item["id"]: item for item in systems}
    for index, line_id in enumerate(LINE_ORDER, 1):
        requirement = requirement_by_line[line_id]
        slug = WORLD_SPECS[line_id]["slug"]
        decision_id = f"DEC-W1-{slug}"
        for kind, object_id, value in (
            ("RULE", f"WF-RULE-{slug}", facts_by_id[f"WF-RULE-{slug}"]),
            ("SYSTEM", f"WS-{slug}", systems_by_id[f"WS-{slug}"]),
        ):
            derivations.append(
                {
                    "id": f"DRV-W1-{kind}-{index:02d}",
                    "value_sha256": canonical_sha256(value),
                    "source_ids": [requirement["id"]],
                    "decision_ids": [decision_id],
                    "projection_ids": [object_id],
                }
            )

    model = {
        "schema_version": "2.0",
        "skill": "novel-world-model-designer",
        "stage": "W1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": dict(gate_reference),
        "source_artifacts": [dict(item) for item in source_artifacts],
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": [*[item["id"] for item in decisions], *all_owned_entities],
            "downstream_freedom": [item["id"] for item in environment_demands],
            "author_open": author_open,
        },
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "storyline_requirements": requirements,
        "world_definition": world_definition,
        "world_facts": facts,
        "reality_claims": reality_claims,
        "world_facets": facets,
        "history_pressures": history,
        "institutions": institutions,
        "systems": systems,
        "resource_flows": resource_flows,
        "authority_flows": authority_flows,
        "information_flows": information_flows,
        "rule_conflict_matrix": conflicts,
        "storyline_support_ledger": support,
        "environment_demands": environment_demands,
        "open_items": open_items,
    }
    phases = {
        "requirement-projection": {"storyline_requirements": requirements},
        "world-rules-and-history": {
            "design_decisions": decisions,
            "world_definition": world_definition,
            "world_facts": facts,
            "reality_claims": reality_claims,
            "world_facets": facets,
            "history_pressures": history,
        },
        "systems-and-flows": {
            "institutions": institutions,
            "systems": systems,
            "resource_flows": resource_flows,
            "authority_flows": authority_flows,
            "information_flows": information_flows,
        },
        "cross-line-world-test": {
            "rule_conflict_matrix": conflicts,
            "storyline_support_ledger": support,
            "environment_demands": environment_demands,
            "authority_partition": model["authority_partition"],
            "derivation_claims": derivations,
            "open_items": open_items,
        },
        "final-world-model": {"model": model},
    }
    return model, phases
