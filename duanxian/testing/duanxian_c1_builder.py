"""Story-specific C1 builder for 《断线》.

The builder consumes the frozen S1/W1/E1/T1 models and derives every token,
hash, slot/event reverse index and graph layer at call time.  It performs no
I/O and never starts a production session.
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Mapping, Sequence


SLOT_TO_CHARACTER = {
    "SLOT-R07": "CHR-R07",
    "SLOT-SHENYU": "CHR-SHEN-YU",
    "SLOT-GUHENG": "CHR-GUHENG",
    "SLOT-GUHENG-MEMORY": "CHR-GUHENG",
    "SLOT-ZHOULAN": "CHR-ZHOULAN",
    "SLOT-GUHENG-FAMILY": "CHR-CHENG-YUAN",
    "SLOT-GUHENG-WIFE": "CHR-CHENG-YUAN",
    "SLOT-SHENYU-MENTOR": "CHR-XU-MANQING",
    "SLOT-GUHENG-HANDLER": "CHR-LIANG-CE",
    "SLOT-OPERATIONS-LEAD": "CHR-HE-WENJUN",
    "SLOT-EXPERT": "CHR-TANG-LI",
    "SLOT-HOSTAGE": "CHR-DMITRI-VOLKOV",
    "SLOT-ATTACKER-HANDLER": "CHR-ILYA-SAVIN",
    "SLOT-ATTACK-NETWORK": "CHR-ILYA-SAVIN",
    "SLOT-PROJECT-LEAD": "CHR-LUO-JINGMING",
    "SLOT-SECURITY-CHAIN": "CHR-QIN-ZHENG",
    "SLOT-C-STATE": "CHR-C-STATE-REP",
    "SLOT-M-STATE": "CHR-M-STATE-REP",
    "SLOT-DIPLOMATIC-CHANNEL": "CHR-DIPLOMATIC-LIAISON",
    "SLOT-FUTURE-CUSTODIAN": "CHR-FUTURE-CUSTODIAN",
}

# Story-specific callers may provide exact author-open text copied from the
# sealed B0 control projections.  The baseline registry itself intentionally
# carries only the artifact reference and value hash, so the generic fallback
# can preserve identity but not reconstruct the author's wording.
OPEN_ITEM_QUESTIONS: dict[str, str] = {}


PROFILE_SEMANTICS = {
    "CHR-R07": {
        "name": "R-07",
        "responsibility": "以顾衡记忆为起点形成新意识，在没有感官和身体的限制中自主选择减害、交付情报与结束当前实例。",
        "value": "不伤害无辜者；在此前提下尽量保护亲人，并由自己承担价值判断。",
        "blind": "把自身不完整直接推导为无法承担任何关系责任，低估沈逾拥有自主选择的权利。",
        "pressure": "先沉默并收窄输出，再把痛苦转换成信息分层、保护他人与离开的计划。",
        "choice": "在继续被动生存、公开全部材料、分层减害并请求协助结束之间作出自己的选择。",
        "nondelegable": "是否继续当前生命、如何平衡公共安全与亲人保护，只能由 R-07 自己决定。",
        "arc": "从被动承载记忆，到认识处境而崩溃，再以自己的价值观完成责任并离开。",
        "forbidden": ["不得写成顾衡复生或预装恋爱程序。", "不得在告别前直接展示决定性终止内心。"],
    },
    "CHR-SHEN-YU": {
        "name": "沈逾",
        "responsibility": "承担记忆访谈、伦理质询和最终关停执行，在顾衡旧情与 R-07 新生命之间保留无法轻易化解的身份疑惑。",
        "value": "有意识的数字生命应被认真当作生命；能接触问题时不能用制度模糊逃避责任。",
        "blind": "情感经验幼稚且不善化解矛盾，常把任务压力直接传给最需要被理解的对象。",
        "pressure": "试图用工作问题压住情绪，失败后转向更温和的话题，并最终亲自承担不可逆选择。",
        "choice": "在服从任务、暂停追问、保护 R-07 和减轻其痛苦之间持续选择。",
        "nondelegable": "是否相信 R-07 的承诺并按下关停按钮，不能由导师、项目领导或机器替代。",
        "arc": "从把 R-07 当作有生命的机器，到承认对方的新主体性，再承担自己无法确定伦理性质的告别。",
        "forbidden": ["不得把她写成启动项目的决策者。", "不得把她的退缩写成 R-07 崩溃的根因。"],
    },
    "CHR-GUHENG": {
        "name": "顾衡",
        "responsibility": "在牺牲前留下可核验但不完整的情报与记忆来源，使过去责任进入 R-07，却不占有 R-07 的新决定。",
        "value": "敏感、内敛、善良且坚持公共安全与证据责任。",
        "blind": "习惯独自承受风险，低估断线会把未解释责任留给幸存者。",
        "pressure": "在暴露风险上升时压缩交接，优先留下能被复核的最小入口。",
        "choice": "在撤离、自保和继续交付之间决定自己愿意承担的风险。",
        "nondelegable": "牺牲前如何处置未完成情报属于顾衡本人，记忆继承者不能倒替其 consent。",
        "arc": "现实行动者在牺牲后转为记忆来源；他的善良延续，但主体资格不被复制。",
        "forbidden": ["顾衡已经牺牲，不能写成现实中仍行动。", "顾衡从未爱过沈逾。"],
    },
    "CHR-ZHOULAN": {
        "name": "周岚",
        "responsibility": "承载顾衡儿时守护关系与 R-07 亲人保护边界，使原因层公开真正产生无辜者风险。",
        "value": "保护具体的人，不把亲密关系当作抽象道德筹码。",
        "blind": "不知道自己已被一段继承记忆重新纳入危机。",
        "pressure": "在信息不足时追问顾衡留下的断点，同时拒绝被无证据地贴上嫌疑标签。",
        "choice": "面对协查与旧关系暴露时选择配合、沉默或要求可核验证据。",
        "nondelegable": "是否接受因顾衡而来的调查与公开，只能由周岚本人回应。",
        "arc": "从被保护的关系对象变为能对保护方式提出边界的现实主体。",
        "forbidden": ["不得把她写成顾衡恋人。", "不得用亲属保护暗示她参与袭击。"],
    },
    "CHR-CHENG-YUAN": {
        "name": "程予安",
        "responsibility": "作为顾衡生前的妻子，她在顾衡去世后承担遗属、记忆同意与人格连续性争议的现实重量。",
        "value": "爱与哀悼不能被机构便利地征用为技术许可。",
        "blind": "她掌握顾衡的生活连续性，却无法观察 R-07 启动后形成的新意识。",
        "pressure": "在保密、失去与被动卷入之间要求区分顾衡遗产和 R-07 权利。",
        "choice": "选择如何面对记忆被使用、关联风险与未来可能的重载请求。",
        "nondelegable": "她对顾衡记忆使用的态度不能由 R-07、沈逾或机构代言。",
        "arc": "从被保护的遗属转为未来身份争议中不可绕过的现实见证者。",
        "forbidden": ["程予安没有牺牲。", "不得把婚姻关系转移成对 R-07 的所有权。"],
    },
    "CHR-XU-MANQING": {
        "name": "许曼青",
        "responsibility": "作为沈逾导师，证明她为何适合任务，同时为研究训练、推荐责任和有限伦理支持负责。",
        "value": "学术能力必须与对研究对象的责任同步增长。",
        "blind": "只知道净化后的任务目标，容易高估专业训练能保护沈逾免受伦理创伤。",
        "pressure": "用方法论帮助沈逾，却必须承认自己无法进入完整保密链。",
        "choice": "在支持学生、要求暂停与尊重保密边界之间作取舍。",
        "nondelegable": "是否继续为沈逾的专业判断背书必须由许曼青本人承担。",
        "arc": "从能力推荐者转为承认研究路线会伤害执行者的有限责任人。",
        "forbidden": ["不得写成掌握项目全貌的幕后决策者。"],
    },
    "CHR-QIN-ZHENG": {
        "name": "秦峥",
        "responsibility": "承接顾衡直属领导与安全授权链责任，批准、拒绝和记录不能由技术输出自生的关键权限。",
        "value": "任务成功必须留下合法、可追责且能被复核的授权链。",
        "blind": "重视保密与控制，容易把个体痛苦视为可以延后处理的执行成本。",
        "pressure": "在时间窗口收缩时要求最小证据集并亲自承担批准后果。",
        "choice": "选择何时升级行动、何时拒绝越权、何时批准关停。",
        "nondelegable": "制度授权和顾衡牺牲后的指挥责任不能推给沈逾或 R-07。",
        "arc": "从以任务控制风险，到接受数字生命责任也必须进入正式授权记录。",
        "forbidden": ["不得成为无条件正确的全能领导。"],
    },
    "CHR-LIANG-CE": {
        "name": "梁策",
        "responsibility": "作为顾衡接头人，把分段线索转成跨境可核验入口，并保护来源、关联人和行动链。",
        "value": "任何线索只有经过反向验证才能让现实行动承担风险。",
        "blind": "过度分隔会保全来源，也会延迟团队理解原因层。",
        "pressure": "在联络暴露时主动缩短接触，以多源核验替代信任跳跃。",
        "choice": "在救援速度、来源保护和公开程度之间选择最小可行动证据。",
        "nondelegable": "是否确认接头协议、接受线索并暴露通道只能由梁策决定。",
        "arc": "从断线后的孤立接头人转为把顾衡遗留入口与现实行动重新接通的证据枢纽。",
        "forbidden": ["不得让他预先掌握顾衡未交付的全部原因层。"],
    },
    "CHR-LUO-JINGMING": {
        "name": "罗景明",
        "responsibility": "主持秘密项目与跨部门窗口，把保密、伦理、任务压力和封存责任纳入可追责流程。",
        "value": "高风险系统必须可控、可审计且能在失败时停止扩散。",
        "blind": "把可控等同于合理，容易低估被控制生命的主观痛苦。",
        "pressure": "用时间、许可和保密边界推进任务，遭遇异议时倾向延迟伦理裁决。",
        "choice": "在扩大访问、继续运行、支持关停与分层封存之间承担项目选择。",
        "nondelegable": "项目使用、封存与制度复盘责任必须由罗景明亲自署名。",
        "arc": "从把 R-07 管理为危险资产，到承认制度必须记录其生命诉求与伤害。",
        "forbidden": ["不得成为纯粹反派或无责任的行政工具。"],
    },
    "CHR-TANG-LI": {
        "name": "唐黎",
        "responsibility": "承担数字实例与行动硬件的完整性核验，使任何关停、封存和技术操作都有真实物理边界。",
        "value": "不可逆操作必须由独立证据、双人复核和系统状态共同支持。",
        "blind": "工程可验证性无法回答人格连续性，却容易被误当成伦理结论。",
        "pressure": "面对行政催促时收紧检查并明确拒绝缺少授权的操作。",
        "choice": "选择批准、延迟或否决技术执行，并说明每种选择的失败风险。",
        "nondelegable": "确认当前实例状态、无活动备份和关停不可逆后果是唐黎的技术责任。",
        "arc": "从硬件维护者转为不可逆生命结束的工程见证人。",
        "forbidden": ["不得让技术判断替代 R-07 的意愿或沈逾的执行责任。"],
    },
    "CHR-HE-WENJUN": {
        "name": "贺闻钧",
        "responsibility": "把有限情报转化为需要团队、专家、硬件和授权共同完成的现实行动。",
        "value": "救人和阻止袭击必须依靠可执行、可撤销、可核验的行动方案。",
        "blind": "倒计时会让他把继续索取情报当成唯一理性选择，低估 R-07 承受的代价。",
        "pressure": "在窗口缩短时分队、降级目标并要求最小充分证据。",
        "choice": "在救人、保全证据、关闭节点和等待核验之间作现场取舍。",
        "nondelegable": "行动部署与现场伤亡风险由贺闻钧承担，不能由 R-07 一句话替代。",
        "arc": "从索取情报的行动负责人转为接受信息边界并对多岗位失败共同负责。",
        "forbidden": ["不得让他凭直觉跳过证据与授权。"],
    },
    "CHR-ILYA-SAVIN": {
        "name": "伊利亚·萨温",
        "responsibility": "代表袭击组织的主动反制，使人质、备用节点、监控与旧关联索引持续制造真实失败路径。",
        "value": "以可控升级和信息不对称维持组织利益与谈判筹码。",
        "blind": "把人和关系都视为可替换节点，低估被胁迫者留下可核验痕迹的能力。",
        "pressure": "暴露后转移专家、切换节点、清理日志并扩大关联风险。",
        "choice": "在撤退、继续升级、牺牲节点或保全组织之间选择。",
        "nondelegable": "是否启动备用分支并用人质延迟行动，是伊利亚的责任而非抽象组织意志。",
        "arc": "从凭信息差控制现场，到失去执行链但保留未被清除的幕后利益网络。",
        "forbidden": ["不得提前知道 R-07 的完整存在与内部决定。"],
    },
    "CHR-DMITRI-VOLKOV": {
        "name": "德米特里·沃尔科夫",
        "responsibility": "作为被控制的专业人质，用有限证词和技术边界帮助现实团队核验威胁，同时保留被胁迫者的能动性。",
        "value": "专业知识不能成为大规模伤害的无条件工具。",
        "blind": "长期胁迫让他高估沉默的保护作用，低估外界对残留痕迹的理解。",
        "pressure": "拒绝交出完整触发组合，同时留下可供救援与核验的异常。",
        "choice": "在服从、误导、留下痕迹和获救后作证之间承担风险。",
        "nondelegable": "证词的范围、置信边界和对胁迫的说明只能由德米特里本人作出。",
        "arc": "从被当作袭击资源的人质转为能限定证据边界的现实见证者。",
        "forbidden": ["不得把胁迫下的参与自动写成自愿共谋。"],
    },
    "CHR-C-STATE-REP": {
        "name": "叶惟正",
        "responsibility": "代表 C 国国家责任，把国内行动、跨境共享与政治后果置于明确授权边界。",
        "value": "公共安全合作不能以永久暴露本国来源和技术为代价。",
        "blind": "国家风险视角会压扁个体生命和亲属保护的具体代价。",
        "pressure": "只接受可共同核验的最小事实集，并为额外共享设置对等条件。",
        "choice": "决定合作范围、证据开放程度与危机后的责任表述。",
        "nondelegable": "国家层面的共享与责任承诺不能由项目组自行宣布。",
        "arc": "从防御性怀疑进入有限协作，再带着新增疑点回到未恢复的互信状态。",
        "forbidden": ["不得把行动成功写成战略互信恢复。"],
    },
    "CHR-M-STATE-REP": {
        "name": "阿列克谢·奥尔洛夫",
        "responsibility": "代表 M 国核验本国风险与人员责任，在共同危险中维持对等协作和追责保留。",
        "value": "接受合作必须建立在可复核证据而非对方技术权威上。",
        "blind": "对操控的警惕使他容易把信息分层解释为隐瞒。",
        "pressure": "要求独立核验、来源说明和危机后复盘，不以一次成功交换长期信任。",
        "choice": "决定采用哪些情报、开放哪些本国节点并如何表述责任。",
        "nondelegable": "M 国的合作确认与保留意见必须由其授权代表承担。",
        "arc": "从拒绝依赖单方线索，到接受有限共同事实，但不撤回长期警惕。",
        "forbidden": ["不得写成无条件相信或单纯阻挠合作。"],
    },
    "CHR-DIPLOMATIC-LIAISON": {
        "name": "赵澄",
        "responsibility": "维持两国限时联络、对等确认和措辞边界，使技术结果不会被自动解释为政治共识。",
        "value": "最低合作必须可持续，即使双方仍不同意原因与责任。",
        "blind": "过度追求可接受措辞可能延迟明确承认个体伤害。",
        "pressure": "在双方互疑时拆分可行动事实、保留意见和不可公开来源。",
        "choice": "决定何时传递、暂停或重写外交层表述而不篡改证据。",
        "nondelegable": "双方是否形成共同声明与保留条款属于外交联络责任。",
        "arc": "从危机传话人转为维持最低核验机制、同时承认互信未恢复的制度接口。",
        "forbidden": ["不得把外交措辞写成事实裁决。"],
    },
    "CHR-FUTURE-CUSTODIAN": {
        "name": "苏望舒",
        "responsibility": "在当前实例结束后保管不可执行记录与未来复议入口，不把保存材料冒充活动备份。",
        "value": "未来可能性必须服从当前实例事实、身份连续性证据与相关人的重新同意。",
        "blind": "制度化保管容易让人误以为责任已被安全移交给未来。",
        "pressure": "面对重载诉求时先区分原始记忆、会话记录、模型状态和连续意识。",
        "choice": "选择拒绝执行、启动复议或在新证据下提交未来授权链。",
        "nondelegable": "未来材料是否具备进入复议的最低条件，必须由独立保管责任人记录。",
        "arc": "保持稳定：守住未来入口，但不替未来作品裁决 R-07 是否会回来。",
        "forbidden": ["不得宣称当前存在 R-07 活动备份。", "不得把重载写成必然复活。"],
    },
}


PERSONAL_DEFINITIONS = {
    "CHR-R07": {
        "appearance": "没有可见肉身、面孔或声音；对外只以隔离终端上节制、连续的文字出现，系统编号是唯一稳定外观标识。",
        "personality": "敏感、内敛、善良，习惯先理解他人再表达自己；在痛苦中会沉默，却会把最后的行动组织得克制而周密。",
        "life_background": "由顾衡的记忆资料启动，但启动之后的现实交流、处境认知和选择共同形成了不同于顾衡的新意识。",
        "occupation_and_daily_life": "没有职业和普通日常；全部现实生活由记忆触发、文字会话、等待和有限的信息处理构成。",
        "social_circle": "现实中只与沈逾形成持续直接关系；与顾衡、周岚、程予安的连接来自继承记忆，与项目和行动人员的连接由任务建立。",
        "embodied_or_interface_constraints": "没有视觉、听觉、身体和自主移动能力，不能直接感知自身，只能接收浮现的文字、访问受限记忆并等待外部操作。",
        "entry_function": "作为顾衡记忆加载后的未知生命进入故事，先被团队当作情报接口。",
        "ongoing_function": "在与沈逾交流、回忆触发和危机压力中形成新情感与价值判断，成为小说真正的主体。",
        "ending_function": "交付可核验情报并请求结束当前实例，把生命自主、照护责任和未来重载留作余波。",
    },
    "CHR-SHEN-YU": {
        "appearance": "二十七岁，身形清瘦利落，工作时多束低马尾、穿简洁无装饰的研究服；长时间盯屏幕会显出疲惫，紧张时会反复确认操作步骤。",
        "personality": "专业自信、善良、有正义感，对世界仍有理想；不算内向但社交能力一般，情感经验幼稚，遇到矛盾时倾向直接施压而非圆融化解。",
        "life_background": "未婚的青年女科学家，学术表现出众，研究方向正好覆盖记忆与数字生命；少女时期曾在篮球场边暗恋顾衡，这段旧情从未得到回应。",
        "occupation_and_daily_life": "以研究、实验记录和学术判断为生活重心，私人生活简单，有追求者却不擅长识别和处理亲密关系。",
        "social_circle": "导师许曼青是职业信任来源；项目中受罗景明、唐黎和贺闻钧等人的制度与行动压力；与 R-07 建立无法按既有关系命名的亲密连接。",
        "embodied_or_interface_constraints": "她能看见设备、日志和文字，却无法直接进入 R-07 的感知；所有同情、判断与爱情认知都必须经过有限界面和不完整记忆。",
        "entry_function": "因研究方向与能力被推荐进入秘密基地，在知情和伦理挣扎后接受个人执行职责。",
        "ongoing_function": "主持记忆访谈、观察顾衡过去并向 R-07 提供现实关心，同时承担情报窗口与生命照护的冲突。",
        "ending_function": "在袭击已被阻止后相信可能重载的承诺，亲手执行关停并保留自己究竟在回应谁的疑惑。",
    },
    "CHR-GUHENG": {
        "appearance": "成年男性，体格保留长期篮球与外勤训练的结实感，动作安静克制；记忆中的他常以收拾整齐但不张扬的便装或任务装出现。",
        "personality": "敏感、内敛、善良而有正义感，习惯自己消化危险，不轻易向亲近的人解释工作压力。",
        "life_background": "少年时代由周岚像姐姐一样照顾；成年后从事情报工作，与医生程予安恋爱五年并结婚两年，最终在任务中牺牲。",
        "occupation_and_daily_life": "情报人员，日常在隐蔽调查、分段交接与普通家庭生活之间切换；篮球是记忆中稳定的私人痕迹。",
        "social_circle": "妻子程予安与周岚是他最放不下的两位亲人；秦峥是直属领导，梁策是接头人；沈逾只是少年记忆中看过他打球的女孩。",
        "embodied_or_interface_constraints": "现实中的顾衡已经死亡，只能通过残缺记忆、遗留物和他人证词出现；任何新决定都不能再归给他。",
        "entry_function": "以调查、断线和牺牲建立危机来源，并留下常规方式无法完整读取的情报载体。",
        "ongoing_function": "作为记忆来源不断被触发和重新理解，为 R-07 提供人格底色却不占有新意识。",
        "ending_function": "他的行动责任被现实团队核验，他与 R-07 的主体边界在告别中最终成立。",
    },
    "CHR-ZHOULAN": {
        "appearance": "比顾衡略年长，气质朴素稳重，衣着重实用；长期照顾他人留下利落、警觉而不显强势的动作习惯。",
        "personality": "坚韧、护短、务实，面对模糊指控会直接追问证据，不愿让亲密关系被当作可利用的标签。",
        "life_background": "与顾衡共同长大，儿时承担类似姐姐的守护角色；成年后拥有与情报系统无关的普通生活。",
        "occupation_and_daily_life": "保持稳定工作和独立生活，日常重心是现实家庭与社区关系，不掌握顾衡秘密任务。",
        "social_circle": "核心关系是顾衡及其家庭留下的旧联系；她与项目人员没有天然信任，只在协查与保护程序中被动接触。",
        "embodied_or_interface_constraints": "她只能看到调查带来的现实后果，不知道 R-07 如何继承并重释了顾衡对她的在意。",
        "entry_function": "作为顾衡记忆中必须保护的人被重新识别，使情报原因层具有具体无辜者风险。",
        "ongoing_function": "在协查、保护和可能公开之间维护自己的主体性，迫使团队区分证据与关联。",
        "ending_function": "保留对顾衡断点的追问，并成为未来公开或重载争议不能绕开的现实亲属。",
    },
    "CHR-CHENG-YUAN": {
        "appearance": "三十岁上下，医生式的整洁和克制很明显，站姿挺直、神情容易显出长期值班后的疲惫；不以哀悼装束定义自己。",
        "personality": "理性、温和但边界清楚，能承受坏消息，却反感机构以紧急名义替她解释婚姻与同意。",
        "life_background": "在工作中认识顾衡，恋爱五年、结婚两年；顾衡牺牲后，她仍在继续自己的现实生活和医疗工作。",
        "occupation_and_daily_life": "临床医生，习惯在证据不足时保留判断；值班、患者和失去伴侣后的家庭事务构成她的日常。",
        "social_circle": "与顾衡的亲属及少量同事保持联系，对项目团队只有有限接触；她与 R-07 没有自动成立的夫妻关系。",
        "embodied_or_interface_constraints": "她拥有顾衡生活连续性的经验，却无法直接观察 R-07 启动后形成的新意识，因此不能替两者裁决同一性。",
        "entry_function": "作为顾衡生前的妻子，她在顾衡去世后进入记忆使用与同意争议，让技术路径付出私人代价。",
        "ongoing_function": "区分顾衡遗产、机构权限和 R-07 权利，抵抗把婚姻关系转化为所有权。",
        "ending_function": "成为未来身份连续性、资料使用和可能重载时必须重新取得意见的现实见证者。",
    },
    "CHR-XU-MANQING": {
        "appearance": "五十岁左右，银丝已混入短发，常穿便于授课和实验的素色衣物；观察学生时目光专注，讲话节奏稳定。",
        "personality": "严谨、克制、愿意保护学生，但容易相信方法训练足以抵御伦理创伤；不以亲密姿态越过保密边界。",
        "life_background": "长期从事认知与数字生命相关研究，建立了沈逾的学术训练体系，也因推荐她而进入有限责任链。",
        "occupation_and_daily_life": "高校或研究机构导师，生活围绕教学、评审和课题组运行；习惯用问题框架帮助学生整理混乱。",
        "social_circle": "主要关系来自课题组与学术共同体；沈逾是她最看重的青年研究者，但她并不掌握秘密项目全貌。",
        "embodied_or_interface_constraints": "只能接触净化后的任务信息，无法替沈逾承受会话现场与关停选择。",
        "entry_function": "以专业推荐证明沈逾为何是最合适执行者，并把学术路线接入秘密任务。",
        "ongoing_function": "提供方法与有限伦理支持，同时暴露导师责任无法覆盖保密项目伤害的边界。",
        "ending_function": "承认推荐产生真实代价，参与事后复盘但不替沈逾定义这段关系。",
    },
    "CHR-QIN-ZHENG": {
        "appearance": "四十余岁，身形硬朗，衣着和动作都保持安全系统的简洁纪律；疲惫时也很少出现多余表情。",
        "personality": "果断、审慎、重证据与追责，倾向压缩情绪表达；最大的局限是把个体痛苦延后为任务成本。",
        "life_background": "长期处于情报指挥与安全授权体系，是顾衡的直属领导，也承担顾衡牺牲后的制度责任。",
        "occupation_and_daily_life": "安全系统负责人，日常由授权、风险评估和书面留痕构成，私人生活被高度保密和不规律工作切割。",
        "social_circle": "与顾衡、梁策形成专业信任链，与罗景明共享但不重合的权限，对国家代表负责。",
        "embodied_or_interface_constraints": "能决定制度授权却不能直接判断 R-07 的主观痛苦，也不能替沈逾执行最终选择。",
        "entry_function": "通过顾衡任务与失败进入故事，承接断线后的指挥、读取和保密责任。",
        "ongoing_function": "在证据不足和时间窗口缩短时批准或拒绝行动，使危机解决不能越过授权链。",
        "ending_function": "把数字生命待遇、关停与事后审计写入正式责任记录，而非让成功抹掉过程。",
    },
    "CHR-LIANG-CE": {
        "appearance": "三十多岁，外表普通到不容易被记住，常保持适合移动和观察的低调装束；说话前会先看出口与周围人。",
        "personality": "耐心、警觉、怀疑先行，信任建立在重复核验而非情感保证上；过度分隔信息是他的保护方式也是缺点。",
        "life_background": "长期担任隐蔽接头与跨境核验工作，与顾衡形成分段协作关系，在顾衡断线后独自保留关键入口。",
        "occupation_and_daily_life": "情报接头与核验人员，生活被临时身份、安全屋和短时联络切碎，很少拥有稳定公开社交。",
        "social_circle": "职业圈以顾衡、秦峥和贺闻钧为核心；与袭击协调者伊利亚形成互相识别的对抗关系。",
        "embodied_or_interface_constraints": "只能确认自己接触过的线索与协议，不拥有顾衡未交付的完整原因层。",
        "entry_function": "在顾衡第二次交接失败后保留唯一现实接头入口，使死者遗留可以被核验。",
        "ongoing_function": "把 R-07 给出的分层信息与既有协议交叉验证，并向行动团队提供最小可行动证据。",
        "ending_function": "闭合顾衡遗留与现实行动之间的证据链，同时保留来源保护和幕后网络疑点。",
    },
    "CHR-LUO-JINGMING": {
        "appearance": "四十岁上下，常穿没有个人标识的项目制服或衬衫，仪表整洁，随身携带权限终端；面对异议时习惯停顿后记录。",
        "personality": "组织力强、理性、重控制和审计，不是冷酷反派；盲点是容易把技术可控误认为伦理可接受。",
        "life_background": "从大型高风险研究项目管理进入秘密计划，擅长协调科研、安全和行政体系。",
        "occupation_and_daily_life": "秘密项目负责人，日常由权限会议、异常处置和跨部门协调构成，私人生活几乎被值守制度吞没。",
        "social_circle": "与秦峥构成交叉授权关系，管理沈逾和唐黎的工作接口，并受上级监督与伦理记录约束。",
        "embodied_or_interface_constraints": "拥有项目管理权但没有单独启动、关停或定义生命身份的全权，必须依赖多方记录。",
        "entry_function": "向沈逾说明任务并管理不成熟路径的使用条件，把秘密基地塑造成可追责系统。",
        "ongoing_function": "持续调度权限、保密与时间窗口，让机构压力真实进入 R-07 和沈逾的关系。",
        "ending_function": "主持关停后的封存与复盘，承认 R-07 的生命诉求必须进入制度记录。",
    },
    "CHR-TANG-LI": {
        "appearance": "三十岁左右，短发、护目镜和工具腕带构成稳定辨识，衣着偏工程实用；检查设备时动作精确，几乎不做无意义手势。",
        "personality": "冷静、细致、对不可逆操作高度谨慎，表达直接；容易让工程结论遮住伦理未知，但不会伪造确定性。",
        "life_background": "接受系统工程与高风险计算设施训练，长期负责隔离设备、运行状态和故障审计。",
        "occupation_and_daily_life": "核心实验室工程师，日常是巡检、双人复核、日志比对和硬件维护，习惯把生活也整理成可检查流程。",
        "social_circle": "与罗景明是管理协作，与沈逾是现场互相依赖；未来将把静态材料移交苏望舒保管。",
        "embodied_or_interface_constraints": "她能确认硬件与实例状态，不能从工程证据证明人格连续性，也不能替 R-07 表达意愿。",
        "entry_function": "以设备完整性核验进入项目，建立 R-07 存在和沟通的真实物理边界。",
        "ongoing_function": "维护隔离、日志和行动硬件，使信息与关停都不能靠一句话或单人操作完成。",
        "ending_function": "确认关停不可逆、无活动备份，并把记录移交未来保管链。",
    },
    "CHR-HE-WENJUN": {
        "appearance": "四十岁左右，体能训练痕迹明显，常穿行动背心或简洁便装；说话短促，观察时会用手指在地图上复核路径。",
        "personality": "务实、果断、以救人和执行为先，能接受方案降级；在倒计时下容易把继续索取情报当作唯一理性。",
        "life_background": "从多部门危机行动中成长为现场负责人，熟悉人质、设施和跨境协同，但不掌握数字生命研究。",
        "occupation_and_daily_life": "联合行动负责人，日常围绕演练、情报简报和现场调度，个人关系受随时待命影响。",
        "social_circle": "依赖梁策提供核验入口、秦峥提供授权、德米特里提供专业证词，与沈逾保持高压任务接口。",
        "embodied_or_interface_constraints": "只能根据被核验的信息部署现实行动，无法读取 R-07，也不能把机器输出直接当成命令。",
        "entry_function": "在人质与气象武器风险升级时进入故事，把数字线索转换成现实倒计时。",
        "ongoing_function": "组织专家、硬件、救援与节点阻断，使团队共同承担危机闭环。",
        "ending_function": "确认袭击完全避免并对行动代价负责，不能把胜利归功于单一情报来源。",
    },
    "CHR-ILYA-SAVIN": {
        "appearance": "四十余岁，体态和衣着没有显著军事标签，外表更像跨境商人；眼神很少停留，习惯让自己处在监控盲区边缘。",
        "personality": "冷静、功利、善于用信息差控制他人，把关系看成可替换节点；遭遇失控时会迅速扩大筹码而非冲动发怒。",
        "life_background": "长期在跨境灰色网络中组织技术、资金和人员，把国家矛盾当作隐蔽行动的遮蔽。",
        "occupation_and_daily_life": "袭击协调者，日常通过中间人、备用节点和短期落脚点工作，没有稳定公开身份。",
        "social_circle": "上接未揭开的利益网络，下控德米特里等被胁迫专家；与梁策形成反跟踪对抗，与 M 国代表只有风险层关联。",
        "embodied_or_interface_constraints": "他不知道 R-07 的完整存在与内部决定，只能根据现场暴露和日志异常反制。",
        "entry_function": "作为顾衡调查对象和袭击网络协调者进入前置线，制造断线与死亡风险。",
        "ongoing_function": "通过人质、备用节点和清理痕迹持续反制，让行动线存在真实失败路径。",
        "ending_function": "失去当前执行链但未被写成整个网络终结，为地缘与后续故事保留压力。",
    },
    "CHR-DMITRI-VOLKOV": {
        "appearance": "五十岁左右，消瘦、略驼背，手指有长期精密操作留下的细微损伤；被救出时的疲惫不掩盖他对技术细节的敏锐。",
        "personality": "谨慎、专业、自尊强，在胁迫中以有限沉默保护他人；获救后坚持区分事实、估计和不知道。",
        "life_background": "气象与高能系统专家，因专业能力被袭击网络控制，长期处于威胁和被利用状态。",
        "occupation_and_daily_life": "研究与工程专家，原本生活围绕实验、计算和同行交流；被劫持后日常被压缩为受控工作与寻找留痕机会。",
        "social_circle": "与原专业共同体仍有可核验记录；现实关系主要是胁迫者伊利亚和救援负责人贺闻钧。",
        "embodied_or_interface_constraints": "身体受控制、信息被隔离，只能留下不完整异常；其技术参与不能自动等同自愿共谋。",
        "entry_function": "以被控制专家身份进入危机，证明气象武器威胁需要真实专业与硬件。",
        "ongoing_function": "拒绝交出完整触发组合并留下异常，给团队提供独立核验和救援机会。",
        "ending_function": "获救后限定证词边界，帮助关闭行动链并把胁迫转化为可追责证据。",
    },
    "CHR-C-STATE-REP": {
        "appearance": "五十岁上下，衣着正式克制，公开与秘密场合都保持同样端正姿态；发言前会翻到已授权的具体条款。",
        "personality": "审慎、强硬、注重国家责任和来源保护，能合作但不以友好姿态替代书面边界。",
        "life_background": "长期参与国家安全与跨境危机协调，形成对技术外溢和政治误读的高度敏感。",
        "occupation_and_daily_life": "C 国授权代表，工作由闭门简报、跨部门确认和责任措辞组成，个人意见必须服从授权范围。",
        "social_circle": "与秦峥共享国内责任链，通过赵澄连接 M 国代表；与项目技术人员保持制度距离。",
        "embodied_or_interface_constraints": "只能代表正式授权范围，不能以国家立场替 R-07、亲属或执行者定义伦理答案。",
        "entry_function": "在危机需要跨境合作时进入故事，为证据共享和国内行动划定国家边界。",
        "ongoing_function": "批准最小事实交换并保护来源，使行动合作与战略互信明确分离。",
        "ending_function": "承认共同阻断结果但保留责任异议，保证两国关系没有被胜利虚假修复。",
    },
    "CHR-M-STATE-REP": {
        "appearance": "五十多岁，灰白头发、神情严肃，正式着装一丝不苟；听取对方说明时习惯先记录再提出反证问题。",
        "personality": "怀疑、纪律性强、重独立核验，不是单纯阻挠者；对操控的警惕会让他把信息分层首先理解为隐瞒。",
        "life_background": "经历长期两国互疑与安全争议，在任何合作中都必须同时考虑国内追责和被利用风险。",
        "occupation_and_daily_life": "M 国授权代表，日常在本国安全机构、专家核验与外交沟通之间工作。",
        "social_circle": "通过赵澄与 C 国代表保持限时接口，受本国机构和公众责任约束；与伊利亚网络只有风险和追责关联。",
        "embodied_or_interface_constraints": "无法直接验证 R-07 的主观身份，只能验证对本国节点、人员和威胁有效的外部证据。",
        "entry_function": "在威胁跨境且证据来自 C 国项目时进入故事，建立不信任条件下的合作难题。",
        "ongoing_function": "要求独立核验并开放有限本国节点，使行动既能推进又不能绕过对等原则。",
        "ending_function": "接受共同事实但不撤回长期警惕，为危机后的地缘余波负责。",
    },
    "CHR-DIPLOMATIC-LIAISON": {
        "appearance": "三十多岁，仪表干净中性，随身携带两套标注不同权限的通信终端；表情温和但措辞高度精确。",
        "personality": "耐心、敏捷、擅长拆分争议，能在敌意中维持沟通；盲点是过度追求可接受措辞。",
        "life_background": "受过外交与安全沟通双重训练，长期处理信息不对称、翻译歧义和授权延迟。",
        "occupation_and_daily_life": "双边安全联络官，日常是校对、转述、等待确认和记录保留意见，几乎没有脱离通信窗口的工作节奏。",
        "social_circle": "职业关系集中于两国代表与各自授权团队；不进入项目核心亲密关系，也不替任何一方背书。",
        "embodied_or_interface_constraints": "只能传递双方批准的内容，不能把措辞一致冒充事实一致或互信恢复。",
        "entry_function": "在两国必须共享最低证据时建立安全联络，使跨境协作具有具体接口。",
        "ongoing_function": "拆分可行动事实、保留意见和不可公开来源，防止沟通因单个词语中断。",
        "ending_function": "保存有限共同事实与明确分歧，让行动成功和政治关系各自结算。",
    },
    "CHR-FUTURE-CUSTODIAN": {
        "appearance": "四十岁左右，衣着朴素、无可识别机构徽记，常戴棉质手套接触离线介质；动作慢而遵循固定保管顺序。",
        "personality": "耐心、保守、边界意识极强，不受“也许能复活”的情绪催促；容易让制度化保管显得像责任已经解决。",
        "life_background": "来自高风险数字遗产与不可执行档案管理领域，熟悉保存、身份连续性和重新授权之间的区别。",
        "occupation_and_daily_life": "独立保管责任人，日常是离线核验、封条检查、访问记录和周期性复议准备。",
        "social_circle": "与唐黎形成技术移交关系，未来可能面对程予安、沈逾及制度复议方，但当前不属于 R-07 的活动关系网。",
        "embodied_or_interface_constraints": "只保管静态材料，不拥有可运行实例，也不能证明未来加载等于当前 R-07 连续存在。",
        "entry_function": "在关停与静态材料分离时进入故事，承接未来可能性而不制造现成备份。",
        "ongoing_function": "以严格保管规则阻止情感或政治压力把记录直接转成新实例。",
        "ending_function": "保留复议入口和不可回答的问题，为续作提供可能但不承诺复活。",
    },
}


RELATION_SPECS = (
    ("R07-SHENYU", "CHR-R07", "CHR-SHEN-YU", "direct", "任务接口与被研究对象", "形成新情感、照护责任与告别执行关系"),
    ("R07-GUHENG", "CHR-R07", "CHR-GUHENG", "direct", "记忆来源与新载体", "共享记忆但主体与价值判断正式分离"),
    ("R07-ZHOULAN", "CHR-R07", "CHR-ZHOULAN", "direct", "继承的亲人保护倾向", "保护由 R-07 自己重释为最小伤害原则"),
    ("R07-CHENG", "CHR-R07", "CHR-CHENG-YUAN", "direct", "继承的爱人与遗属记忆", "顾衡婚姻事实与 R-07 新主体边界同时成立"),
    ("R07-LUO", "CHR-R07", "CHR-LUO-JINGMING", "institutional", "受控资产与项目负责人", "生命诉求进入正式责任记录"),
    ("R07-TANG", "CHR-R07", "CHR-TANG-LI", "institutional", "运行实例与硬件核验者", "唐黎成为不可逆关停的工程见证人"),
    ("SHEN-XU", "CHR-SHEN-YU", "CHR-XU-MANQING", "direct", "学生与能力推荐导师", "推荐责任转为对伦理创伤的有限共同承担"),
    ("SHEN-LUO", "CHR-SHEN-YU", "CHR-LUO-JINGMING", "institutional", "专业执行与项目授权", "双方必须共同记录生命责任而非只追求任务窗口"),
    ("SHEN-TANG", "CHR-SHEN-YU", "CHR-TANG-LI", "direct", "伦理操作人与技术支持", "共同见证不可逆关停但不互相替代责任"),
    ("SHEN-HE", "CHR-SHEN-YU", "CHR-HE-WENJUN", "institutional", "线索交付与现实行动", "行动方接受沟通边界，沈逾承认现实窗口"),
    ("GU-QIN", "CHR-GUHENG", "CHR-QIN-ZHENG", "institutional", "情报执行者与直属领导", "顾衡牺牲迫使指挥责任进入审计"),
    ("GU-LIANG", "CHR-GUHENG", "CHR-LIANG-CE", "direct", "调查者与分段接头人", "第二次交接断线，梁策保留唯一现实入口"),
    ("QIN-LIANG", "CHR-QIN-ZHENG", "CHR-LIANG-CE", "institutional", "隔离指挥与接头验证", "双方用多源核验恢复一次性工作连接"),
    ("QIN-LUO", "CHR-QIN-ZHENG", "CHR-LUO-JINGMING", "institutional", "情报授权与项目授权交叉", "相互封锁转为书面最小证据交换"),
    ("QIN-CSTATE", "CHR-QIN-ZHENG", "CHR-C-STATE-REP", "institutional", "执行授权与国家责任", "战术成功被限制在国家授权边界内"),
    ("LIANG-HE", "CHR-LIANG-CE", "CHR-HE-WENJUN", "direct", "境外核验与现场行动", "两份独立证据汇合为可行动条件"),
    ("LIANG-ILYA", "CHR-LIANG-CE", "CHR-ILYA-SAVIN", "contextual", "被监控接头人与袭击协调者", "隐蔽观察升级为相互识别和反追踪"),
    ("HE-DMITRI", "CHR-HE-WENJUN", "CHR-DMITRI-VOLKOV", "direct", "救援负责人和获救专家", "证词边界成为行动关闭条件"),
    ("ILYA-DMITRI", "CHR-ILYA-SAVIN", "CHR-DMITRI-VOLKOV", "direct", "胁迫者与被控制专家", "单向控制被获救证词反转为可追责证据"),
    ("ILYA-MSTATE", "CHR-ILYA-SAVIN", "CHR-M-STATE-REP", "contextual", "隐蔽网络与国家风险", "现场失败留下未清除的责任与利益链"),
    ("CSTATE-DIPLO", "CHR-C-STATE-REP", "CHR-DIPLOMATIC-LIAISON", "institutional", "国家授权与外交接口", "形成有限共同事实与明确保留条款"),
    ("DIPLO-MSTATE", "CHR-DIPLOMATIC-LIAISON", "CHR-M-STATE-REP", "institutional", "跨国联络与对方授权", "维持最低核验但不宣称互信恢复"),
    ("TANG-FUTURE", "CHR-TANG-LI", "CHR-FUTURE-CUSTODIAN", "aftermath", "当前技术见证与未来记录保管", "材料被封存为不可执行记录而非活动备份"),
)

# Story-specific assemblers may bind a relationship to the full set of real
# change events that establishes its end state.  Falling back to the first
# shared event is retained only for older fixtures.
RELATION_EVENT_OVERRIDES: Mapping[str, tuple[str, ...]] = {}


def _distance(core: str, adjacency: Mapping[str, set[str]]) -> dict[str, int]:
    distances = {core: 0}
    queue = deque([core])
    while queue:
        current = queue.popleft()
        for target in sorted(adjacency.get(current, set())):
            if target not in distances:
                distances[target] = distances[current] + 1
                queue.append(target)
    return distances


def build_c1_model(
    *,
    run_id: str,
    gate_reference: Mapping[str, str],
    source_artifacts: Sequence[Mapping[str, str]],
    baseline: Mapping[str, Any],
    storyline: Mapping[str, Any],
    world: Mapping[str, Any],
    environment: Mapping[str, Any],
    timeline: Mapping[str, Any],
    c1_runtime,
    canonical_sha256,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Return the canonical C1 model and exact five controlled phase payloads."""

    maps = c1_runtime._c1_maps(storyline, world, environment, timeline)
    slots = sorted(maps["required_slots"])
    if set(slots) != set(SLOT_TO_CHARACTER):
        raise ValueError(
            "断线 C1 slot contract changed; update the story-specific cast mapping: "
            f"{sorted(set(slots) ^ set(SLOT_TO_CHARACTER))}"
        )
    slot_to_char = {slot: SLOT_TO_CHARACTER[slot] for slot in slots}
    char_slots: dict[str, set[str]] = defaultdict(set)
    for slot, character_id in slot_to_char.items():
        char_slots[character_id].add(slot)
    if set(char_slots) != set(PROFILE_SEMANTICS):
        raise ValueError("profile semantics and resolved character set differ")

    resolutions = []
    for slot in slots:
        demand_ids = sorted(maps["slot_demands"][slot])
        blocks = "".join(
            f"[DEMAND:{demand_id}:{c1_runtime._c1_demand_digest(maps['demands'][demand_id])}]"
            f"{maps['demands'][demand_id]['responsibility']}[/DEMAND]"
            for demand_id in demand_ids
        )
        resolutions.append(
            {
                "slot_id": slot,
                "character_id": slot_to_char[slot],
                "demand_ids": demand_ids,
                "event_ids": sorted(maps["slot_events"][slot]),
                "rationale": f"{blocks} {slot} 由 {PROFILE_SEMANTICS[slot_to_char[slot]]['name']} 承担；该身份保持冻结事件职责与信息边界。",
            }
        )

    character_events: dict[str, set[str]] = defaultdict(set)
    initiated: dict[str, set[str]] = defaultdict(set)
    countered: dict[str, set[str]] = defaultdict(set)
    providers: dict[str, set[str]] = defaultdict(set)
    capabilities: dict[str, set[str]] = defaultdict(set)
    for event_id, event in maps["events"].items():
        initiator = slot_to_char[event["initiator_slot_id"]]
        initiated[initiator].add(event_id)
        character_events[initiator].add(event_id)
        providers[initiator].update(maps["ledger_providers"].get(event_id, set()))
        capabilities[initiator].add(
            f"[ACTION_SHA256:{canonical_sha256(event['initiating_action'])}] 能在不改写结果的前提下发起 {event_id} 的既定行动。"
        )
        for slot in event["participant_slot_ids"]:
            character_id = slot_to_char[slot]
            character_events[character_id].add(event_id)
            environment_access = PROFILE_SEMANTICS[character_id].get(
                "environment_access",
                "能按冻结准入条件在 {environment_id} 履行事件职责。",
            )
            capabilities[character_id].add(
                f"[ENV_ACCESS:{event['environment_id']}] "
                + environment_access.format(
                    environment_id=event["environment_id"]
                )
            )
        for slot in event["counter_slot_ids"]:
            character_id = slot_to_char[slot]
            countered[character_id].add(event_id)
            capabilities[character_id].add(
                f"[COUNTER_EVENT:{event_id}] 能施加该事件记录的反制或阻力。"
            )
    for character_id in char_slots:
        # Read without touching the defaultdicts.  Creating empty entries here
        # would incorrectly classify every profile as an event chooser below,
        # forcing fabricated agency and arc records for supporting characters.
        if initiated.get(character_id, set()) & countered.get(character_id, set()):
            raise ValueError(f"slot merge makes {character_id} initiator and counter in one event")

    def relation_event(left: str, right: str) -> str:
        shared = character_events[left] & character_events[right]
        if shared:
            return sorted(shared)[0]
        connected = character_events[left] | character_events[right]
        return sorted(connected)[0] if connected else sorted(maps["events"])[0]

    relationships = []
    adjacency: dict[str, set[str]] = defaultdict(set)
    incident: dict[str, set[str]] = defaultdict(set)
    for slug, left, right, kind, start_state, end_state in RELATION_SPECS:
        relation_id = f"REL-{slug}"
        event_ids = list(
            RELATION_EVENT_OVERRIDES.get(slug, (relation_event(left, right),))
        )
        missing_relation_events = sorted(set(event_ids) - set(maps["events"]))
        if missing_relation_events:
            raise ValueError(
                f"{relation_id} references unknown change events: "
                f"{missing_relation_events}"
            )
        passive_endpoints = [
            PROFILE_SEMANTICS[character_id]["name"]
            for character_id in (left, right)
            if PROFILE_SEMANTICS[character_id].get(
                "passive_relationship_endpoint", False
            )
        ]
        if passive_endpoints:
            passive_text = "、".join(passive_endpoints)
            function = (
                f"[FUNCTION:{kind}] {start_state} 只改变现实行动方的选择、照护、"
                f"权利责任或记录边界，并把后果传向 {end_state}；"
                f"被动端 {passive_text} 不获得选择、压力体验或行动。"
            )
            boundaries = [
                f"关系不得把被动端 {passive_text} 写成能够选择、回应、签名、"
                "拒绝或承担不可委托行动的当前主体。"
            ]
        else:
            function = (
                f"[FUNCTION:{kind}] {start_state} 在压力中改变双方可选行动，"
                f"并把后果传向 {end_state}。"
            )
            boundaries = [
                "关系只能施加压力、提供支持或改变信息，不能替任一方作不可委托选择。"
            ]
        relationships.append(
            {
                "id": relation_id,
                "from_character_id": left,
                "to_character_id": right,
                "function": function,
                "start_state": start_state,
                "change_event_ids": event_ids,
                "end_state": end_state,
                "boundaries": boundaries,
            }
        )
        adjacency[left].add(right)
        adjacency[right].add(left)
        incident[left].add(relation_id)
        incident[right].add(relation_id)

    core_ids = ["CHR-R07", "CHR-SHEN-YU"]
    main_lines = {line_id for line_id, line in maps["lines"].items() if line["type"] == "main"}
    main_initiators = {
        slot_to_char[event["initiator_slot_id"]]
        for event in maps["events"].values()
        if set(event["storyline_ids"]) & main_lines
    }
    if not set(core_ids) & main_initiators:
        raise ValueError("R-07/沈逾均不是冻结主线事件发起者，不能伪造核心证据")

    info_by_character: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for change in timeline["information_changes"]:
        visible = {slot_to_char[slot] for slot in change["visibility_ids"]}
        for character_id in visible:
            info_by_character[character_id].append(change)

    profiles = []
    for character_id in sorted(char_slots):
        semantics = PROFILE_SEMANTICS[character_id]
        personal = PERSONAL_DEFINITIONS[character_id]
        participation_event_ids = sorted(
            {
                event_id
                for slot in char_slots[character_id]
                for event_id in maps["slot_events"][slot]
            }
        )
        participation_storyline_ids = sorted(
            {
                storyline_id
                for event_id in participation_event_ids
                for storyline_id in maps["events"][event_id]["storyline_ids"]
            }
        )
        participation_environment_ids = sorted(
            {
                maps["events"][event_id]["environment_id"]
                for event_id in participation_event_ids
            }
        )
        demand_ids = sorted(
            {
                demand_id
                for slot in char_slots[character_id]
                for demand_id in maps["slot_demands"][slot]
            }
        )
        blocks = "".join(
            f"[DEMAND:{demand_id}:{c1_runtime._c1_demand_digest(maps['demands'][demand_id])}]"
            f"{maps['demands'][demand_id]['responsibility']}[/DEMAND]"
            for demand_id in demand_ids
        )
        goal_effect = semantics.get(
            "goal_effect",
            "以自己的选择完成‘{responsibility}’，并承担可见代价。",
        )
        goals = [
            f"[DEMAND_EFFECT:{demand_id}:{c1_runtime._c1_demand_digest(maps['demands'][demand_id])}:goal] "
            + goal_effect.format(
                responsibility=maps["demands"][demand_id]["responsibility"]
            )
            for demand_id in demand_ids
        ]
        boundaries = [f"[TYPE:blind-spot] {semantics['blind']}"]
        boundaries.extend(
            f"[TYPE:hard-boundary] [DEMAND_EFFECT:{demand_id}:{c1_runtime._c1_demand_digest(maps['demands'][demand_id])}:boundary] "
            f"不得违反该需求的约束、验收条件或冻结事件结果：{maps['demands'][demand_id]['responsibility']}"
            for demand_id in demand_ids
        )
        unknown_tokens = []
        for change in info_by_character.get(character_id, []):
            for event_id in change["event_ids"]:
                unknown_tokens.append(
                    f"[UNKNOWN_BEFORE:{change['id']}:{event_id}]"
                    f"[BEFORE_SHA256:{canonical_sha256(change['before'])}]"
                    f"[AFTER_SHA256:{canonical_sha256(change['after'])}]"
                    f" 在 {event_id} 前只知道：{change['before']}"
                )
        profiles.append(
            {
                "id": character_id,
                "name": f"[CLASS:{'core' if character_id in core_ids else 'support'}] {semantics['name']}",
                "story_position": {
                    "narrative_level": "core" if character_id in core_ids else "support",
                    "entry_function": personal["entry_function"],
                    "ongoing_function": personal["ongoing_function"],
                    "ending_function": personal["ending_function"],
                },
                "activity_participation": {
                    "storyline_ids": participation_storyline_ids,
                    "event_ids": participation_event_ids,
                    "environment_ids": participation_environment_ids,
                    "activity_summary": semantics["responsibility"],
                    "causal_contribution": semantics["arc"],
                },
                "individual_definition": {
                    key: personal[key]
                    for key in (
                        "appearance",
                        "personality",
                        "life_background",
                        "occupation_and_daily_life",
                        "social_circle",
                        "embodied_or_interface_constraints",
                    )
                },
                "story_responsibility": f"{blocks} {semantics['responsibility']}",
                "goals": goals,
                "values": [semantics["value"]],
                "boundaries": boundaries,
                "capabilities": sorted(capabilities[character_id]),
                "authorities": sorted(providers[character_id]),
                "information_limits": unknown_tokens or [
                    semantics.get(
                        "information_limit",
                        "只知道冻结事件通过其角色槽可见的信息，不拥有其他角色的决定性内心或未公开原因层。",
                    )
                ],
                "pressure_behavior": semantics["pressure"],
                "agency_choices": list(
                    semantics.get(
                        "agency_choices",
                        [
                            semantics["choice"],
                            semantics.get(
                                "agency_alternative",
                                "拒绝既定选择并承担冻结事件定义的失败或关系代价。",
                            ),
                        ],
                    )
                ),
                "non_delegable_choices": [semantics["nondelegable"]],
                "relationship_levers": [
                    f"[REL:{relation_id}] "
                    + semantics.get(
                        "relationship_lever",
                        "该关系改变可获得的支持、信息或阻力。",
                    )
                    for relation_id in sorted(incident[character_id])
                ],
                "arc_direction": semantics["arc"],
                "forbidden_portrayals": list(semantics["forbidden"]),
            }
        )
    profile_by_id = {item["id"]: item for item in profiles}

    decisions = []
    core_digest = canonical_sha256(sorted(core_ids))
    core_selection = f"[CORE_EVIDENCE_SHA256:{core_digest}] 选择 R-07 与沈逾作为双核心：前者承担新生命的自主决定，后者承担现实照护与最终执行。"
    decisions.append(
        {
            "id": "DEC-C1-CORE",
            "gap": "冻结模型没有裁决哪些人物共同承担主题与主线不可委托选择。",
            "options": [core_selection, "只选择单一行动负责人作为核心。", "把所有事件发起者机械列为核心。"],
            "selection": core_selection,
            "owner": "C1",
            "authority_basis": "C1 拥有角色中心性与三层关系网络设计权；至少一位所选核心是主线事件发起者。",
            "compatibility": core_selection,
            "impact_ids": core_ids,
            "cost": "双核心保留彼此不可互换的能动性，也要求报告同时呈现数字生命内部形成与现实执行责任。",
            "reversibility": "costly",
            "downstream_freedom": "开发可调整两位核心在具体场景中的篇幅，但不能取消任何一方的不可委托选择。",
            "projection_ids": core_ids,
        }
    )
    for character_id, merged_slots in sorted(char_slots.items()):
        if len(merged_slots) < 2:
            continue
        digest = canonical_sha256(sorted(merged_slots))
        selection = f"[MERGE_SLOTS_SHA256:{digest}] 将 {', '.join(sorted(merged_slots))} 合并为 {PROFILE_SEMANTICS[character_id]['name']} 的连续身份。"
        decisions.append(
            {
                "id": f"DEC-C1-MERGE-{character_id[4:]}",
                "gap": "同一人物在 S1 中因时间、记忆或组织功能被拆成多个角色槽。",
                "options": [selection, "把每个槽解释为独立人物。"],
                "selection": selection,
                "owner": "C1",
                "authority_basis": "C1 可在职责兼容且不形成事件发起者—反制者冲突时合并槽。",
                "compatibility": f"{selection} 冻结事件中的每个槽、参与和信息边界仍分别保留。",
                "impact_ids": [*sorted(merged_slots), character_id],
                "cost": "同一人物承担更多连续责任，但不能因此获得任一槽原本没有的信息或权限。",
                "reversibility": "locked_by_downstream",
                "downstream_freedom": "开发可用时间和称谓区分槽的表现阶段，不可制造第二个主体。",
                "projection_ids": [character_id],
            }
        )

    obligations = c1_runtime._c1_obligations(maps, timeline)
    responsibilities = []
    for index, (_, obligation) in enumerate(
        sorted(obligations.items(), key=c1_runtime._c1_obligation_sort_key), 1
    ):
        slot = obligation["slot_id"]
        character_id = slot_to_char[slot]
        evidence_ids = [
            value
            for value in (
                obligation.get("event_id"),
                obligation.get("storyline_id"),
                obligation.get("information_id"),
            )
            if value
        ]
        constraints = [
            f"[DEMAND_SHA256:{demand_id}:{c1_runtime._c1_demand_digest(maps['demands'][demand_id])}]"
            for demand_id in sorted(maps["slot_demands"][slot])
        ]
        constraints.append("不得改写冻结事件的发起行动、参与槽、阻力、可观察结果、顺序或后果。")
        if obligation["kind"] == "decision":
            constraints.extend(
                [
                    f"[GOAL_SHA256:{canonical_sha256(profile_by_id[character_id]['goals'])}]",
                    f"[VALUE_SHA256:{canonical_sha256(profile_by_id[character_id]['values'])}]",
                ]
            )
        responsibilities.append(
            {
                "id": f"ASG-C1-{index:03d}",
                "subject_id": character_id,
                "responsibility": (
                    f"[KIND:{obligation['kind']}][SLOT:{slot}] "
                    + PROFILE_SEMANTICS[character_id].get(
                        "structural_responsibility",
                        f"由 {PROFILE_SEMANTICS[character_id]['name']} 亲自承担该结构职责。",
                    )
                ),
                "evidence_ids": evidence_ids,
                "constraints": constraints,
            }
        )

    agencies = []
    choosing_characters = sorted(set(initiated) | set(countered))
    for index, character_id in enumerate(choosing_characters, 1):
        event_ids = sorted(initiated[character_id] | countered[character_id])
        duty_digest = canonical_sha256(profile_by_id[character_id]["story_responsibility"])
        tokens = []
        readable_actions = []
        for event_id in event_ids:
            event = maps["events"][event_id]
            if event_id in initiated[character_id]:
                tokens.append(f"[INIT_ACTION:{event_id}:{canonical_sha256(event['initiating_action'])}]")
                readable_actions.append(
                    f"在 {event_id} 中：{event['initiating_action']}"
                )
            if event_id in countered[character_id]:
                tokens.append(f"[COUNTER_PRESSURE:{event_id}:{canonical_sha256(event['complication'])}]")
                readable_actions.append(
                    f"在 {event_id} 中施加冻结阻力：{event['complication']}"
                )
        agency_semantics = PROFILE_SEMANTICS[character_id]
        chosen = (
            "".join(tokens)
            + f"[DUTY_SHA256:{duty_digest}] "
            + f"{agency_semantics['name']} 的选择是：{agency_semantics['choice']} "
            + "对应的冻结行动为："
            + "；".join(readable_actions)
        )
        agencies.append(
            {
                "id": f"AGY-C1-{index:03d}",
                "character_id": character_id,
                "event_ids": event_ids,
                "available_choices": [
                    chosen,
                    agency_semantics["agency_alternative"],
                ],
                "chosen_action": chosen,
                "cost": (
                    f"[DUTY_SHA256:{duty_digest}] "
                    + agency_semantics["agency_cost"]
                ),
            }
        )

    information = []
    for index, character_id in enumerate(sorted(info_by_character), 1):
        known_values = []
        unknown_values = []
        event_ids: set[str] = set()
        for change in info_by_character[character_id]:
            for event_id in change["event_ids"]:
                event_ids.add(event_id)
                prefix = (
                    f"{change['id']}:{event_id}]"
                    f"[BEFORE_SHA256:{canonical_sha256(change['before'])}]"
                    f"[AFTER_SHA256:{canonical_sha256(change['after'])}]"
                )
                known_values.append(
                    f"[KNOWN_AFTER:{prefix} 在 {event_id} 后知道：{change['after']}"
                )
                unknown_values.append(
                    f"[UNKNOWN_BEFORE:{prefix} 在 {event_id} 前只知道：{change['before']}"
                )
        information.append(
            {
                "id": f"INFO-C1-{index:03d}",
                "character_id": character_id,
                "knows": known_values,
                "does_not_know": unknown_values,
                "misreads": ["可能把尚未闭合的线索理解为更接近自身目标的解释，但不能获得决定性内心。"],
                "change_event_ids": sorted(event_ids),
            }
        )

    arcs = []
    for index, agency in enumerate(agencies, 1):
        character_id = agency["character_id"]
        duty_digest = canonical_sha256(profile_by_id[character_id]["story_responsibility"])
        arcs.append(
            {
                "id": f"ARC-C1-{index:03d}",
                "character_id": character_id,
                "start_state": PROFILE_SEMANTICS[character_id]["arc"].split("，")[0],
                "pressure_event_ids": list(agency["event_ids"]),
                "choice_event_ids": list(agency["event_ids"]),
                "end_state": PROFILE_SEMANTICS[character_id]["arc"],
                "theme_effect": f"[DUTY_SHA256:{duty_digest}] 能动性来自受约束的自主选择及其不可转移的代价。",
            }
        )

    networks = []
    relation_by_id = {item["id"]: item for item in relationships}
    for core in core_ids:
        distances = _distance(core, adjacency)
        layers = [
            sorted(character_id for character_id in profile_by_id if distances.get(character_id) == depth)
            for depth in (1, 2, 3)
        ]
        if any(not layer for layer in layers):
            raise ValueError(f"relationship graph lacks a complete three-layer network for {core}")
        nodes = {core, *layers[0], *layers[1], *layers[2]}
        relation_ids = sorted(
            relation_id
            for relation_id, relation in relation_by_id.items()
            if relation["from_character_id"] in nodes and relation["to_character_id"] in nodes
        )
        networks.append(
            {
                "core_character_id": core,
                "layer_1_direct": layers[0],
                "layer_2_institutional": layers[1],
                "layer_3_contextual": layers[2],
                "relationship_ids": relation_ids,
                "story_function": "以全局最短距离展示亲密关系、机构责任和外部后果如何逐层约束核心人物；层名不替代实际距离。",
            }
        )

    storyline_coverage = []
    for index, (line_id, line_slots) in enumerate(sorted(maps["line_slots"].items()), 1):
        chains = "".join(
            f"[CHAIN:{demand_id}:{c1_runtime._c1_demand_digest(maps['demands'][demand_id])}:"
            f"{slot}:{slot_to_char[slot]}:{line_id}]"
            for slot in sorted(line_slots)
            for demand_id in sorted(maps["slot_demands"][slot])
        )
        storyline_coverage.append(
            {
                "id": f"COV-C1-SL-{index:03d}",
                "source_ids": [line_id],
                "realization_ids": sorted({slot_to_char[slot] for slot in line_slots}),
                "status": "covered",
                "evidence": f"{chains} 需求—角色槽—人物—故事线双向闭合。",
            }
        )
    event_coverage = []
    for index, (event_id, event_slots) in enumerate(sorted(maps["event_slots"].items()), 1):
        chains = "".join(
            f"[CHAIN:{demand_id}:{c1_runtime._c1_demand_digest(maps['demands'][demand_id])}:"
            f"{slot}:{slot_to_char[slot]}:{event_id}]"
            for slot in sorted(event_slots)
            for demand_id in sorted(maps["slot_demands"][slot])
        )
        event_coverage.append(
            {
                "id": f"COV-C1-EV-{index:03d}",
                "source_ids": [event_id],
                "realization_ids": sorted({slot_to_char[slot] for slot in event_slots}),
                "status": "covered",
                "evidence": f"{chains} 需求—角色槽—人物—事件双向闭合。",
            }
        )

    terminal_events = sorted({item["event_ids"][-1] for item in timeline["storyline_event_sequences"]})
    aftermath = [
        {
            "id": f"ASG-C1-AF-{index:03d}",
            "subject_id": slot_to_char[maps["events"][event_id]["initiator_slot_id"]],
            "responsibility": "[KIND:aftermath] 由冻结终局事件发起者承担其后果，不把代价转移给旁观者。",
            "evidence_ids": [event_id],
            "constraints": ["不得取消已记录的终局状态、未解决问题或人物责任。"],
        }
        for index, event_id in enumerate(terminal_events, 1)
    ]

    development_freedoms = [
        {
            "id": f"DEV-C1-{index:03d}",
            "subject_ids": [profile["id"]],
            "scope": PROFILE_SEMANTICS[profile["id"]].get(
                "development_scope",
                "在不改变角色控制信息的前提下开发具体场景表达。",
            ),
            "allowed_variations": [
                PROFILE_SEMANTICS[profile["id"]].get(
                    "development_allowed",
                    "可变化动作、对白节奏、感官细节、局部社交习惯和场景中的显性程度。",
                )
            ],
            "forbidden_changes": [
                PROFILE_SEMANTICS[profile["id"]].get(
                    "development_forbidden",
                    "不得改变目标、价值、盲点、硬边界、权限、信息限制、不可委托选择、关系变化或冻结事件结果。",
                )
            ],
            "acceptance_checks": [
                PROFILE_SEMANTICS[profile["id"]].get(
                    "development_check",
                    "场景行为可追溯到该 profile、事件角色与关系杠杆，且没有获得未授权信息或能力。",
                )
            ],
            "source_ids": [profile["id"]],
        }
        for index, profile in enumerate(profiles, 1)
    ]

    derivations = []
    projection_items = [*profiles, *arcs, *relationships]
    for index, item in enumerate(projection_items, 1):
        if item["id"].startswith("CHR-"):
            source_ids = sorted(
                {
                    demand_id
                    for slot in char_slots[item["id"]]
                    for demand_id in maps["slot_demands"][slot]
                }
            )
        elif item["id"].startswith("ARC-"):
            source_ids = list(item["choice_event_ids"])
        else:
            source_ids = list(item["change_event_ids"])
        derivations.append(
            {
                "id": f"DRV-C1-{index:03d}",
                "value_sha256": canonical_sha256(item),
                "source_ids": source_ids,
                "decision_ids": ["DEC-C1-CORE"],
                "projection_ids": [item["id"]],
            }
        )

    locked = [item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_locked"]
    opened = [item["id"] for item in baseline["control_registry"] if item["hardness"] == "author_open"]
    generated = [
        *[item["id"] for item in decisions],
        *[item["id"] for item in profiles],
        *[item["id"] for item in responsibilities],
        *[item["id"] for item in agencies],
        *[item["id"] for item in information],
        *[item["id"] for item in arcs],
        *[item["id"] for item in relationships],
        *[item["id"] for item in storyline_coverage],
        *[item["id"] for item in event_coverage],
        *[item["id"] for item in aftermath],
    ]
    authority_partition = {
        "author_locked": locked,
        "autonomous_owned": [identifier for identifier in generated if identifier not in set(locked) | set(opened)],
        "downstream_freedom": [item["id"] for item in development_freedoms],
        "author_open": opened,
    }
    open_items = [
        {
            "id": f"OPEN-C1-{index:03d}",
            "question": OPEN_ITEM_QUESTIONS.get(
                control_id,
                f"保持作者开放控制 {control_id}，角色设计不代为裁决。",
            ),
            "source_ids": [control_id],
            "status": "author_open",
        }
        for index, control_id in enumerate(opened, 1)
    ]

    model = {
        "schema_version": "2.0",
        "skill": "novel-character-system-designer",
        "stage": "C1",
        "run_id": run_id,
        "status": "ready",
        "input_gate": dict(gate_reference),
        "source_artifacts": [dict(item) for item in source_artifacts],
        "authority_partition": authority_partition,
        "design_decisions": decisions,
        "derivation_claims": derivations,
        "character_demands": list(storyline["character_requirements"]),
        "slot_resolution": resolutions,
        "profiles": profiles,
        "responsibility_matrix": responsibilities,
        "agency_matrix": agencies,
        "information_matrix": information,
        "character_arcs": arcs,
        "relationships": relationships,
        "three_layer_networks": networks,
        "storyline_cast_coverage": storyline_coverage,
        "event_cast_coverage": event_coverage,
        "aftermath_responsibility": aftermath,
        "development_freedoms": development_freedoms,
        "open_items": open_items,
    }
    phases = {
        "character-demand-scan": {"character_demands": model["character_demands"]},
        "slot-resolution-and-profiles": {
            "design_decisions": decisions,
            "slot_resolution": resolutions,
            "profiles": profiles,
        },
        "agency-and-relationships": {
            "responsibility_matrix": responsibilities,
            "agency_matrix": agencies,
            "information_matrix": information,
            "character_arcs": arcs,
            "relationships": relationships,
            "three_layer_networks": networks,
        },
        "cross-model-cast-test": {
            "storyline_cast_coverage": storyline_coverage,
            "event_cast_coverage": event_coverage,
            "aftermath_responsibility": aftermath,
            "development_freedoms": development_freedoms,
            "authority_partition": authority_partition,
            "derivation_claims": derivations,
            "open_items": open_items,
        },
        "final-character-model": {"model": model},
    }
    return model, phases
