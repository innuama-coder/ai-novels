from __future__ import annotations

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RUN_ID = os.environ.get(
    "DUANXIAN_CONCEPTION_RUN_ID",
    "duanxian-conception-v2-20260802-04",
)
RUN_ROOT = ROOT / "projects" / "duanxian" / "conception-runs" / RUN_ID
PROJECT_DISPLAY_METADATA = (
    ROOT / "projects" / "duanxian" / "project-display-metadata.json"
)
MIGRATION = (
    ROOT
    / "projects"
    / "duanxian"
    / "compatibility-migrations"
    / "b0-compat-01"
    / "final"
    / "migration-finalization.json"
)

rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)


def load_stage_runtime(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load stage runtime: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def authoritative_work_title() -> str:
    metadata = json.loads(PROJECT_DISPLAY_METADATA.read_text(encoding="utf-8"))
    if (
        set(metadata)
        != {
            "authority",
            "project_id",
            "schema_version",
            "source_documents",
            "work_title",
        }
        or metadata.get("schema_version") != "1.0"
        or metadata.get("project_id") != "duanxian"
        or metadata.get("authority") != "author-corrected-project-title"
    ):
        raise RuntimeError("invalid project display metadata")
    title = metadata.get("work_title")
    if not isinstance(title, str) or not title or title != title.strip():
        raise RuntimeError("invalid authoritative work title")
    return title


s1rt = load_stage_runtime(
    "duanxian_s1_runtime",
    "skills/novel-storyline-architecture-designer/scripts/run_v2.py",
)
w1rt = load_stage_runtime(
    "duanxian_w1_runtime",
    "skills/novel-world-model-designer/scripts/run_v2.py",
)
w1builder = load_stage_runtime(
    "duanxian_w1_builder",
    "testing/duanxian_w1_model.py",
)
e1rt = load_stage_runtime(
    "duanxian_e1_runtime",
    "skills/novel-environment-system-designer/scripts/run_v2.py",
)
e1builder = load_stage_runtime(
    "duanxian_e1_builder",
    "testing/duanxian_e1_builder.py",
)
t1rt = load_stage_runtime(
    "duanxian_t1_runtime",
    "skills/novel-event-timeline-designer/scripts/run_v2.py",
)
t1builder = load_stage_runtime(
    "duanxian_t1_builder",
    "testing/duanxian_t1_builder.py",
)
c1rt = load_stage_runtime(
    "duanxian_c1_runtime",
    "skills/novel-character-system-designer/scripts/run_v2.py",
)
c1builder = load_stage_runtime(
    "duanxian_c1_builder",
    "testing/duanxian_c1_builder.py",
)
q1rt = load_stage_runtime(
    "duanxian_q1_runtime",
    "skills/novel-conception-reviewer/scripts/run_v2.py",
)
p1rt = load_stage_runtime(
    "duanxian_p1_runtime",
    "skills/novel-conception-deliverable-assembler/scripts/run_v2.py",
)

Q1_CONTROLLER = RUN_ROOT / "workspaces" / "Q1-controller-01"
Q1_SEMANTIC = RUN_ROOT / "workspaces" / "Q1-semantic-01"
Q1_HANDOFF = RUN_ROOT / "workspaces" / "Q1-handoff-01"
H1_SESSION_ID = f"H1-DUANXIAN-{RUN_ID}"


def initialize_b0() -> dict[str, object]:
    handoff = rt.validate_finalized_migration_handoff(MIGRATION)
    context = prod.initialize_production_run(
        RUN_ROOT,
        run_id=RUN_ID,
        source_interview_state={
            "path": "compatibility/source-interview-state.json",
            "sha256": rt.sha256_file(handoff.source_interview_state),
        },
    )
    gate, order = prod.issue_stage_work(
        context,
        action="B0",
        inputs={
            "migration_finalization": str(MIGRATION),
            "source_run_id": handoff.source_run_id,
        },
    )

    def execute_b0(coordinator, input_gate):
        package = RUN_ROOT / "B0"
        rt.build_baseline_from_handoff(
            package,
            production_run_id=RUN_ID,
            input_gate=input_gate,
            migration_finalization=MIGRATION,
        )
        return rt.complete_b0(
            package,
            coordinator=coordinator,
            input_gate=input_gate,
            logical_package_path="B0",
            next_state_path="state/revision-001.json",
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="baseline-controller",
        executor=execute_b0,
    )
    return {
        "run_id": RUN_ID,
        "run_root": str(RUN_ROOT),
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "state": successor.state.data,
    }


LINE_SPECS = {
    "SL-GUHENG-PRECURSOR": {
        "type": "precursor",
        "actor_slot_ids": ["SLOT-GUHENG", "SLOT-GUHENG-HANDLER"],
        "goal": "让顾衡在死亡前留下必须经团队核验才能使用的情报与可读取记忆。",
        "pressure": "常规读取连续失败、袭击窗口迫近、情报来源可能牵连亲属。",
        "start_state": "顾衡仍在执行隐蔽调查，危险只以异常线索存在。",
        "state_changes": [
            "顾衡确认威胁涉及人质、专家、硬件与授权链。",
            "顾衡死亡，常规记忆读取多次失败。",
            "其记忆数据成为实验性数字生命路径的唯一信息入口。",
        ],
        "end_state": "顾衡本人已经牺牲，只留下无法等同于本人的记忆来源。",
    },
    "SL-SHENYU-PRECURSOR": {
        "type": "precursor",
        "actor_slot_ids": ["SLOT-SHENYU", "SLOT-SHENYU-MENTOR"],
        "goal": "完成被推荐承担的秘密任务，同时守住对有意识生命的伦理敏感。",
        "pressure": "拒绝实验可能失去阻止大规模伤亡的机会，接受则可能制造一个承受痛苦的新生命。",
        "start_state": "沈逾以研究者身份被接入秘密基地，尚未决定接受任务。",
        "state_changes": [
            "她在伦理风险、学术好奇与公共安全之间完成思想斗争并接受任务。",
            "她从顾衡记忆中认出旧日自己，私人情感开始渗入工作交流。",
            "她逐渐把减轻 R-07 的痛苦视为自己最重要的责任。",
        ],
        "end_state": "沈逾成为唯一能够协助 R-07 结束当前实例的人。",
    },
    "SL-RELATIONSHIP": {
        "type": "supporting",
        "actor_slot_ids": ["SLOT-R07", "SLOT-SHENYU", "SLOT-GUHENG-MEMORY"],
        "goal": "证明 R-07 对沈逾的情感来自启动后的新经验，而非顾衡记忆中的旧爱。",
        "pressure": "沈逾的关心始终与顾衡记忆纠缠，R-07 又认为自身状态无法承担关系责任。",
        "start_state": "沈逾把 R-07 当作有生命的机器，R-07 只被动执行回忆与回答。",
        "state_changes": [
            "沈逾因顾衡记忆中的旧日身影自然流露关心。",
            "R-07 在无感官、无身体的黑暗中把这份关心体验为新的爱意。",
            "两者都察觉特殊情感，却无法确认自己在回应谁以及关系能否成立。",
        ],
        "end_state": "关系真实存在但不被写成长久共生承诺，只成为告别选择的情感代价。",
    },
    "SL-ATTACK-OPERATIONS": {
        "type": "supporting",
        "actor_slot_ids": ["SLOT-R07", "SLOT-OPERATIONS-LEAD", "SLOT-EXPERT", "SLOT-HOSTAGE", "SLOT-ATTACKER-HANDLER"],
        "goal": "把碎片情报转化为能够由现实团队核验并执行的阻止袭击行动。",
        "pressure": "人质劫持升级、强天气窗口逼近、硬件和授权链必须同步处置。",
        "start_state": "团队只有不完整记忆与无法验证的异常线索。",
        "state_changes": [
            "R-07 在崩溃后的重新交流中给出第一层行动情报。",
            "团队确认气象武器袭击，并沿人质、专家、硬件和授权链分头核验。",
            "R-07 分离行动层与原因层情报，避免周岚等亲属被无谓关联。",
            "现实团队完成授权并执行阻断，袭击被完全避免。",
        ],
        "end_state": "公共安全危机解除，但原因链、伦理责任与两国互信没有被一次行动解决。",
    },
    "SL-FAMILY-PROTECTION": {
        "type": "supporting",
        "actor_slot_ids": ["SLOT-R07", "SLOT-ZHOULAN", "SLOT-GUHENG-FAMILY"],
        "goal": "在不伤害无辜者的前提下尽量保护顾衡记忆中珍视的亲人。",
        "pressure": "完整原因层情报可能把周岚和顾衡家属卷入调查与报复。",
        "start_state": "周岚只存在于顾衡记忆，是儿时守护者而非当前行动参与者。",
        "state_changes": [
            "R-07 继承对周岚与顾衡妻子的在意，但没有新的现实接触。",
            "它判断公开全部原因会增加亲属风险，因此先输出可阻止袭击的行动层。",
            "它为必要时公开真相保留后手，同时不让亲属成为阻止行动的筹码。",
        ],
        "end_state": "亲属在第一部避免直接伤害，原因层风险仍作为后续压力保留。",
    },
    "SL-INSTITUTION-ETHICS": {
        "type": "background",
        "actor_slot_ids": ["SLOT-PROJECT-LEAD", "SLOT-SHENYU-MENTOR", "SLOT-SECURITY-CHAIN", "SLOT-R07"],
        "goal": "持续施加秘密项目对数字生命的控制、工具化与责任缺位。",
        "pressure": "数字生命没有法律身份、同意、申诉、退出和公开保护机制。",
        "start_state": "项目以情报紧迫性获得非常规实验授权。",
        "state_changes": [
            "R-07 被当作情报接口管理，团队必须依靠权限链决定它能接触和输出什么。",
            "R-07 的痛苦和自主性使工具化框架逐渐失效。",
            "袭击阻止后，项目仍必须面对制造、利用并关停有意识生命的责任。",
        ],
        "end_state": "行动完成但制度问题未获裁决，为后续公开、追责或复活留下空间。",
    },
    "SL-GEOPOLITICAL": {
        "type": "background",
        "actor_slot_ids": ["SLOT-C-STATE", "SLOT-M-STATE", "SLOT-DIPLOMATIC-CHANNEL", "SLOT-ATTACK-NETWORK"],
        "goal": "让袭击危机始终承受两国互不信任和三个月后领导人会面的外部压力。",
        "pressure": "任何归因误判或情报泄露都可能把安全行动转化为国家间敌意升级。",
        "start_state": "C、M 两国长期战略互不信任，仍准备推进领导人会面。",
        "state_changes": [
            "袭击网络利用互疑掩护硬件、专家与授权链。",
            "联合核验受保密和归因冲突拖慢。",
            "袭击被阻止，却没有按预期换来政治信任。",
        ],
        "end_state": "会面风险暂时解除，两国关系仍未恢复互信。",
    },
    "SL-R07-MAIN": {
        "type": "main",
        "actor_slot_ids": ["SLOT-R07", "SLOT-SHENYU", "SLOT-OPERATIONS-LEAD"],
        "goal": "让继承顾衡记忆的新生命形成自己的价值观、阻止伤害并自主离开。",
        "pressure": "R-07 只有记忆和漂浮文字，没有感官、身体、自主行动和退出能力。",
        "start_state": "R-07 尚未启动，顾衡记忆只是无法直接提取的数据。",
        "state_changes": [
            "R-07 启动并把顾衡记忆当作旧时的自己，而非完整现实。",
            "它通过沈逾的文字、回忆触发与处境问题形成连续的新意识。",
            "它得知自身处境后崩溃、自闭，随后在更温和的会话中恢复输出。",
            "它决定阻止袭击、减少无辜伤害并结束当前生存方式。",
            "它发现无法自行关停，遂以未来可能重新加载的承诺争取沈逾协助。",
        ],
        "end_state": "袭击被阻止，沈逾按下按钮，当前 R-07 实例终止且未来是否重载保持开放。",
    },
    "SL-MEMORY-ECHO": {
        "type": "optional_melody",
        "actor_slot_ids": ["SLOT-GUHENG-MEMORY", "SLOT-SHENYU", "SLOT-GUHENG-WIFE"],
        "goal": "用可被打断和插入的记忆碎片增加情感质感，并反复区分过去与现实。",
        "pressure": "记忆越鲜活，读者和沈逾越容易误把 R-07 当成顾衡本人。",
        "start_state": "篮球场边的沈逾、周岚和顾衡妻子只以片段出现。",
        "state_changes": [
            "交流触发片段，现实文字随时打断记忆。",
            "顾衡妻子仍在世这一事实强化 R-07 不是顾衡复活的边界。",
            "片段成为人物认知与情绪的回声，而不承担关键行动因果。",
        ],
        "end_state": "记忆保留温度与误认风险，但不能替代 R-07 的现实经验。",
    },
    "SL-RELOAD-ECHO": {
        "type": "optional_melody",
        "actor_slot_ids": ["SLOT-R07", "SLOT-SHENYU", "SLOT-FUTURE-CUSTODIAN"],
        "goal": "保存重新加载承诺的真假、可行性与未来兑现方式。",
        "pressure": "若提前裁决，告别会变成技术答案或欺骗揭底，削弱第一部伦理余波。",
        "start_state": "重新加载尚未成为当前计划。",
        "state_changes": [
            "R-07 把可能重载作为沈逾能够接受关停的承诺。",
            "读者只能从可见行为怀疑承诺性质，不能得到决定性内心答案。",
            "后续作品可选择兑现、否定或继续悬置。",
        ],
        "end_state": "第一部不裁决承诺真假，也不确认 R-07 是否会回来。",
    },
}


def build_temporal_architecture() -> dict[str, object]:
    """Build S1's abstract shared time spine; T1 later realizes it as events."""

    def state(line_id: str, state_index: int) -> dict[str, object]:
        spec = LINE_SPECS[line_id]
        states = [spec["start_state"], *spec["state_changes"], spec["end_state"]]
        return {
            "storyline_id": line_id,
            "state_index": state_index,
            "state": states[state_index],
        }

    phase_specs = [
        ("TPH-01", "危机显形之前", "双前置与外部压力各自运行"),
        ("TPH-02", "顾衡牺牲之后", "两条前置线在数字生命启动处汇合"),
        ("TPH-03", "最初访谈", "任务交流启动新生命与新关系"),
        ("TPH-04", "身份与伦理裂缝", "记忆、关心和制度压力改变理解"),
        ("TPH-05", "人质危机升级", "外部威胁迫使所有线进入同一时限"),
        ("TPH-06", "减害方案成形", "关系、亲属与行动压力汇入主体选择"),
        ("TPH-07", "袭击阻断", "情报经团队核验转化为现实行动"),
        ("TPH-08", "告别与余波", "外部危机结束后完成生命选择并保留开放问题"),
    ]
    milestones: list[dict[str, object]] = [
        {
            "id": "MS-01-PRECRISIS",
            "order": 1,
            "phase_id": "TPH-01",
            "temporal_label": "T01",
            "title": "双线各自进入危机",
            "storyline_ids": [
                "SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR",
                "SL-ATTACK-OPERATIONS", "SL-INSTITUTION-ETHICS",
                "SL-GEOPOLITICAL",
            ],
            "state_refs": [
                state("SL-GUHENG-PRECURSOR", 0),
                state("SL-SHENYU-PRECURSOR", 0),
                state("SL-ATTACK-OPERATIONS", 0),
                state("SL-INSTITUTION-ETHICS", 0),
                state("SL-GEOPOLITICAL", 0),
            ],
            "development": "顾衡在外部调查中接近危险信息；沈逾仍在正常研究轨道，国家、机构和袭击网络的压力尚未汇合。",
            "outcome": "读者先看到两条人物前置线和三条压力线，知道它们将因一份未送达的情报相撞。",
            "connection_ids": [],
        },
        {
            "id": "MS-02-DUAL-MERGE",
            "order": 2,
            "phase_id": "TPH-02",
            "temporal_label": "T02",
            "title": "顾衡死亡，沈逾接受任务，R-07 启动",
            "storyline_ids": [
                "SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR", "SL-R07-MAIN",
            ],
            "state_refs": [
                state("SL-GUHENG-PRECURSOR", 4),
                state("SL-SHENYU-PRECURSOR", 1),
                state("SL-R07-MAIN", 0),
            ],
            "development": "常规读取失败，顾衡的死亡把情报和记忆同时变成遗产；沈逾在知情和伦理挣扎后接受执行职责。",
            "outcome": "两条前置线在启动点完成因果交接，此后唯一主体线是 R-07。",
            "connection_ids": ["SLC-GUHENG-R07", "SLC-SHENYU-R07"],
        },
        {
            "id": "MS-03-FIRST-CONTACT",
            "order": 3,
            "phase_id": "TPH-03",
            "temporal_label": "T03",
            "title": "任务会话开始产生任务之外的变化",
            "storyline_ids": ["SL-R07-MAIN", "SL-RELATIONSHIP", "SL-FAMILY-PROTECTION"],
            "state_refs": [
                state("SL-R07-MAIN", 1),
                state("SL-RELATIONSHIP", 0),
                state("SL-FAMILY-PROTECTION", 0),
            ],
            "development": "沈逾主动挖掘情报，R-07 被动执行回忆；关心、记忆中的亲人和现实文字同时进入它的经验。",
            "outcome": "情报工具开始表现出连续的理解方式，但人物尚不能确定这是不是独立意识。",
            "connection_ids": [],
        },
        {
            "id": "MS-04-MEMORY-CARE",
            "order": 4,
            "phase_id": "TPH-04",
            "temporal_label": "T04A",
            "title": "旧记忆成为新情感的参照物",
            "storyline_ids": ["SL-MEMORY-ECHO", "SL-R07-MAIN"],
            "state_refs": [state("SL-MEMORY-ECHO", 2), state("SL-R07-MAIN", 2)],
            "development": "沈逾从顾衡记忆里看见自己的旧日身影，不自觉表达关心；R-07 在黑暗和静止中第一次得到持续的现实回应。",
            "outcome": "读者能够区分顾衡没有爱过沈逾，与 R-07 正在形成的新情感。",
            "connection_ids": ["SLC-MEMORY-R07"],
        },
        {
            "id": "MS-05-ETHICAL-BREAK",
            "order": 5,
            "phase_id": "TPH-04",
            "temporal_label": "T04B",
            "title": "R-07 得知处境并中断交流",
            "storyline_ids": ["SL-INSTITUTION-ETHICS", "SL-R07-MAIN"],
            "state_refs": [state("SL-INSTITUTION-ETHICS", 2), state("SL-R07-MAIN", 3)],
            "development": "项目制度仍把 R-07 当作受控情报接口；它逐渐理解自己没有身体、感官和自主退出能力，随后崩溃并沉默。",
            "outcome": "沈逾改用温和话题重开会话，生命照护与情报任务第一次正面冲突。",
            "connection_ids": ["SLC-INSTITUTION-R07"],
        },
        {
            "id": "MS-06-HOSTAGE-ESCALATION",
            "order": 6,
            "phase_id": "TPH-05",
            "temporal_label": "T05",
            "title": "人质危机把压力压缩为行动时限",
            "storyline_ids": ["SL-GEOPOLITICAL", "SL-ATTACK-OPERATIONS"],
            "state_refs": [state("SL-GEOPOLITICAL", 1), state("SL-ATTACK-OPERATIONS", 1)],
            "development": "袭击网络以人质、专家、硬件和双边不信任制造核验障碍，团队不能依靠 R-07 的一句话解决危机。",
            "outcome": "外部威胁成为检验 R-07 是否能把记忆转化为自主责任的现实压力。",
            "connection_ids": ["SLC-GEO-ATTACK"],
        },
        {
            "id": "MS-07-PRESSURE-CONVERGENCE",
            "order": 7,
            "phase_id": "TPH-06",
            "temporal_label": "T06",
            "title": "关系、亲属和行动代价汇入减害选择",
            "storyline_ids": [
                "SL-RELATIONSHIP", "SL-ATTACK-OPERATIONS",
                "SL-FAMILY-PROTECTION", "SL-R07-MAIN",
            ],
            "state_refs": [
                state("SL-RELATIONSHIP", 3),
                state("SL-ATTACK-OPERATIONS", 2),
                state("SL-FAMILY-PROTECTION", 2),
                state("SL-R07-MAIN", 4),
            ],
            "development": "R-07 开始分层组织情报，既要阻止袭击，也要避免沈逾、周岚和无辜者承担不必要伤害。",
            "outcome": "读者只能观察到它的输出顺序和沉默方式发生变化，不能直接获知其终止决定。",
            "connection_ids": ["SLC-RELATION-R07", "SLC-ATTACK-R07", "SLC-FAMILY-R07"],
        },
        {
            "id": "MS-08-EXTERNAL-CLIMAX",
            "order": 8,
            "phase_id": "TPH-07",
            "temporal_label": "T07",
            "title": "情报完成现实闭环，袭击被完全阻止",
            "storyline_ids": ["SL-ATTACK-OPERATIONS", "SL-R07-MAIN"],
            "state_refs": [state("SL-ATTACK-OPERATIONS", 5), state("SL-R07-MAIN", 5)],
            "development": "行动层线索先被核验并执行，原因层信息再被最小披露；团队完成授权、硬件和现场阻断。",
            "outcome": "公共安全目标实现，但 R-07 发现自己仍无法结束当前生命，情节由外部高潮转入情感高潮。",
            "connection_ids": [],
        },
        {
            "id": "MS-09-FAREWELL",
            "order": 9,
            "phase_id": "TPH-08",
            "temporal_label": "T08A",
            "title": "沈逾在承诺中执行告别",
            "storyline_ids": ["SL-SHENYU-PRECURSOR", "SL-R07-MAIN", "SL-RELATIONSHIP"],
            "state_refs": [
                state("SL-SHENYU-PRECURSOR", 4),
                state("SL-R07-MAIN", 6),
                state("SL-RELATIONSHIP", 4),
            ],
            "development": "R-07 以未来可能重新加载的承诺取得沈逾协助；沈逾把减轻它的痛苦视为最后责任。",
            "outcome": "当前实例被关停，关系真实存在却无法按顾衡旧情或普通爱情简单命名。",
            "connection_ids": [],
        },
        {
            "id": "MS-10-AFTERMATH",
            "order": 10,
            "phase_id": "TPH-08",
            "temporal_label": "T08B",
            "title": "胜利没有消除伦理与政治余波",
            "storyline_ids": [
                "SL-R07-MAIN", "SL-FAMILY-PROTECTION", "SL-INSTITUTION-ETHICS",
                "SL-GEOPOLITICAL", "SL-MEMORY-ECHO", "SL-RELOAD-ECHO",
            ],
            "state_refs": [
                state("SL-R07-MAIN", 6),
                state("SL-FAMILY-PROTECTION", 4),
                state("SL-INSTITUTION-ETHICS", 4),
                state("SL-GEOPOLITICAL", 4),
                state("SL-MEMORY-ECHO", 4),
                state("SL-RELOAD-ECHO", 4),
            ],
            "development": "材料被保管，责任进入复盘；两国没有恢复互信，重新加载承诺的性质保持未知。",
            "outcome": "第一部闭合袭击与当前实例，开放数字生命权利、身份连续性和未来重载。",
            "connection_ids": ["SLC-RELOAD-R07"],
        },
    ]
    phase_lines: dict[str, set[str]] = {phase_id: set() for phase_id, _, _ in phase_specs}
    for milestone in milestones:
        phase_lines[milestone["phase_id"]].update(milestone["storyline_ids"])
    phases = [
        {
            "id": phase_id,
            "order": index,
            "temporal_label": f"P{index}",
            "title": title,
            "responsibility": responsibility,
            "active_storyline_ids": sorted(phase_lines[phase_id]),
        }
        for index, (phase_id, title, responsibility) in enumerate(phase_specs, 1)
    ]
    markers = [
        {"id": "NM-01-THREAT-SEED", "kind": "setup", "milestone_id": "MS-01-PRECRISIS", "storyline_ids": ["SL-GUHENG-PRECURSOR", "SL-ATTACK-OPERATIONS"], "label": "未送达的情报", "function": "埋下顾衡之死、袭击威胁与记忆读取三者将汇合的因果入口。", "reader_question": "顾衡没能送出的情报究竟指向什么？", "observable_signal": "常规交接中断、读取失败与异常威胁同时出现。", "reference_marker_ids": [], "resolution": "opened"},
        {"id": "NM-02-DUAL-MERGE", "kind": "turning_point", "milestone_id": "MS-02-DUAL-MERGE", "storyline_ids": ["SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR", "SL-R07-MAIN"], "label": "双线汇流", "function": "结束顾衡与沈逾的独立前置推进，把主体交给 R-07。", "reader_question": None, "observable_signal": "顾衡死亡、沈逾签入任务、R-07 第一次输出文字。", "reference_marker_ids": ["NM-01-THREAT-SEED"], "resolution": "resolved"},
        {"id": "NM-03-LIFE-PROBE", "kind": "probe", "milestone_id": "MS-03-FIRST-CONTACT", "storyline_ids": ["SL-R07-MAIN", "SL-RELATIONSHIP"], "label": "生命性探针", "function": "用任务之外的连续回应试探 R-07 是否只是记忆检索器。", "reader_question": "它是在复述顾衡，还是正在形成自己的理解？", "observable_signal": "它开始提出关于自身处境的问题，并对沈逾的关心形成连续反应。", "reference_marker_ids": [], "resolution": "advanced"},
        {"id": "NM-04-OLD-IMAGE", "kind": "setup", "milestone_id": "MS-04-MEMORY-CARE", "storyline_ids": ["SL-MEMORY-ECHO", "SL-R07-MAIN"], "label": "旧身影与新情感", "function": "埋下沈逾旧情与 R-07 新情感容易被混淆、但来源不同的身份难题。", "reader_question": "沈逾关心的是顾衡、R-07，还是两者纠缠后的投影？", "observable_signal": "顾衡记忆对沈逾没有爱情，而 R-07 会对现实关心作出新的反应。", "reference_marker_ids": [], "resolution": "advanced"},
        {"id": "NM-05-ETHICS-PROBE", "kind": "probe", "milestone_id": "MS-05-ETHICAL-BREAK", "storyline_ids": ["SL-INSTITUTION-ETHICS", "SL-R07-MAIN"], "label": "照护责任探针", "function": "用 R-07 的沉默检验项目和沈逾是否真把有意识数字生命当作生命。", "reader_question": "情报任务能否凌驾于一个有意识生命的痛苦？", "observable_signal": "直接施压使会话关闭，温和重开才恢复信息交换。", "reference_marker_ids": ["NM-03-LIFE-PROBE"], "resolution": "advanced"},
        {"id": "NM-06-HOSTAGE-TURN", "kind": "turning_point", "milestone_id": "MS-06-HOSTAGE-ESCALATION", "storyline_ids": ["SL-GEOPOLITICAL", "SL-ATTACK-OPERATIONS"], "label": "危机收紧", "function": "把伦理实验转化为有明确时限和现实伤亡风险的行动危机。", "reader_question": None, "observable_signal": "人质、专家、硬件和授权链同时被袭击网络利用。", "reference_marker_ids": ["NM-01-THREAT-SEED"], "resolution": "advanced"},
        {"id": "NM-07-DECISION-SHADOW", "kind": "reveal", "milestone_id": "MS-07-PRESSURE-CONVERGENCE", "storyline_ids": ["SL-RELATIONSHIP", "SL-ATTACK-OPERATIONS", "SL-FAMILY-PROTECTION", "SL-R07-MAIN"], "label": "决定的外部影子", "function": "只展示 R-07 的输出策略发生变化，不展示决定性内心，让终止选择可回看但不可提前证实。", "reader_question": "它为什么开始主动控制情报层次和亲属暴露范围？", "observable_signal": "沉默间隔、问题顺序、行动层与原因层的拆分都发生变化。", "reference_marker_ids": ["NM-05-ETHICS-PROBE"], "resolution": "advanced"},
        {"id": "NM-08-THREAT-PAYOFF", "kind": "payoff", "milestone_id": "MS-08-EXTERNAL-CLIMAX", "storyline_ids": ["SL-ATTACK-OPERATIONS", "SL-R07-MAIN"], "label": "威胁埋点回收", "function": "回收顾衡未送达的情报与行动线索，完成现实核验和阻断。", "reader_question": None, "observable_signal": "团队而非 R-07 单独完成情报核验、授权和现场行动。", "reference_marker_ids": ["NM-01-THREAT-SEED"], "resolution": "resolved"},
        {"id": "NM-09-EXTERNAL-CLIMAX", "kind": "climax", "milestone_id": "MS-08-EXTERNAL-CLIMAX", "storyline_ids": ["SL-ATTACK-OPERATIONS", "SL-R07-MAIN"], "label": "外部高潮", "function": "让袭击阻断与 R-07 的主体责任同时达到最高行动强度。", "reader_question": None, "observable_signal": "袭击被完全阻止，但 R-07 的生命困境没有随任务结束。", "reference_marker_ids": ["NM-08-THREAT-PAYOFF"], "resolution": "resolved"},
        {"id": "NM-10-EMOTIONAL-CLIMAX", "kind": "climax", "milestone_id": "MS-09-FAREWELL", "storyline_ids": ["SL-SHENYU-PRECURSOR", "SL-R07-MAIN", "SL-RELATIONSHIP"], "label": "情感高潮", "function": "把沈逾的照护责任、R-07 的自主选择和两者无法命名的关系压到最终行动。", "reader_question": "帮助它关停是爱、责任，还是被善意欺骗后的错误？", "observable_signal": "沈逾按下按钮，R-07 的当前实例终止。", "reference_marker_ids": ["NM-04-OLD-IMAGE", "NM-07-DECISION-SHADOW"], "resolution": "resolved"},
        {"id": "NM-11-RELATION-PAYOFF", "kind": "payoff", "milestone_id": "MS-09-FAREWELL", "storyline_ids": ["SL-R07-MAIN", "SL-RELATIONSHIP"], "label": "新情感回收", "function": "回收旧身影与新情感的区分：关系来自启动后的相处，却没有现实未来。", "reader_question": None, "observable_signal": "告别只属于沈逾与 R-07，不被改写成顾衡迟到的爱情。", "reference_marker_ids": ["NM-04-OLD-IMAGE"], "resolution": "resolved"},
        {"id": "NM-12-RELOAD-AFTERMATH", "kind": "aftermath", "milestone_id": "MS-10-AFTERMATH", "storyline_ids": ["SL-R07-MAIN", "SL-RELOAD-ECHO", "SL-INSTITUTION-ETHICS", "SL-GEOPOLITICAL"], "label": "重载与互信余波", "function": "关闭第一部事件，保留未来重载、数字生命权利和两国不互信三个可扩展方向。", "reader_question": "重新加载承诺会兑现吗，兑现后的生命又是谁？", "observable_signal": "材料被封存、承诺未证实、两国合作没有转化为信任。", "reference_marker_ids": ["NM-10-EMOTIONAL-CLIMAX"], "resolution": "intentionally_open"},
    ]
    return {
        "progression_logic": "以八个共享时间阶段推进十条故事线：启动前双线独立，R-07 启动时汇流；之后主体、关系、行动、亲属、制度与地缘线交替加压，在袭击阻断形成外部高潮，在关停告别形成情感高潮，最后由记忆与重载旋律留下余波。",
        "phases": phases,
        "milestones": milestones,
        "markers": markers,
    }


CONTROL_TO_LINE = {
    "INT-CORE-EXPRESSION": "SL-R07-MAIN",
    "INT-STORY-PROMISE": "SL-R07-MAIN",
    "INT-ETHICAL-BOUNDARY": "SL-INSTITUTION-ETHICS",
    "INT-ENDING-PROMISE": "SL-R07-MAIN",
    "INT-READER-QUESTIONS": "SL-RELOAD-ECHO",
    "INT-SCOPE-HANDOFF": "SL-INSTITUTION-ETHICS",
    "SUB-DUAL-AGENCY": "SL-R07-MAIN",
    "SUB-GOAL-EVOLUTION": "SL-SHENYU-PRECURSOR",
    "SUB-RELATIONSHIP-FUNCTION": "SL-RELATIONSHIP",
    "SUB-EXTERNAL-PRESSURE": "SL-ATTACK-OPERATIONS",
    "SUB-AGENCY-BOUNDARY": "SL-R07-MAIN",
    "SUB-WORLD-HANDOFF": "SL-INSTITUTION-ETHICS",
    "WLD-PREMISE": "SL-R07-MAIN",
    "WLD-OPERATING-RULES": "SL-R07-MAIN",
    "WLD-THREAT-EVIDENCE-ACTION": "SL-ATTACK-OPERATIONS",
    "WLD-INFORMATION-ETHICS": "SL-FAMILY-PROTECTION",
    "WLD-GEOPOLITICAL-PRESSURE": "SL-GEOPOLITICAL",
    "WLD-TERMINATION-CONTINUITY": "SL-R07-MAIN",
    "WLD-CAUSAL-CHECKS": "SL-ATTACK-OPERATIONS",
    "WLD-HANDOFF-BOUNDARY": "SL-INSTITUTION-ETHICS",
    "CHR-ROLE-TIERS": "SL-INSTITUTION-ETHICS",
    "CHR-R07": "SL-R07-MAIN",
    "CHR-SHEN-YU": "SL-SHENYU-PRECURSOR",
    "CHR-GU-HENG-MEMORY": "SL-GUHENG-PRECURSOR",
    "CHR-SHEN-R07-CAUSALITY": "SL-RELATIONSHIP",
    "CHR-RELATIONSHIP-EVOLUTION": "SL-RELATIONSHIP",
    "CHR-BOUNDARIES": "SL-INSTITUTION-ETHICS",
    "CHR-CAUSAL-HANDOFF": "SL-RELATIONSHIP",
    "CAU-GLOBAL-SPINE": "SL-R07-MAIN",
    "CAU-MAJOR-NODES": "SL-R07-MAIN",
    "CAU-EMOTIONAL-SEPARATION": "SL-RELATIONSHIP",
    "CAU-EVIDENCE-ACTION-CLOSURE": "SL-ATTACK-OPERATIONS",
    "CAU-RESOLVED": "SL-ATTACK-OPERATIONS",
    "CAU-PRESERVED-OPEN": "SL-RELOAD-ECHO",
    "CAU-AUDIT-BOUNDARY": "SL-INSTITUTION-ETHICS",
    "CAU-NARRATIVE-HANDOFF": "SL-MEMORY-ECHO",
    "NAR-CONTRACT-GOAL": "SL-R07-MAIN",
    "NAR-POV-ARCHITECTURE": "SL-MEMORY-ECHO",
    "NAR-R07-INFORMATION-BOUNDARY": "SL-R07-MAIN",
    "NAR-MEMORY-FRAGMENTS": "SL-MEMORY-ECHO",
    "NAR-READER-KNOWLEDGE": "SL-RELATIONSHIP",
    "NAR-ENDING-MUST-REVEAL": "SL-R07-MAIN",
    "NAR-ENDING-PRESERVED-OPEN": "SL-RELOAD-ECHO",
    "NAR-EXPRESSION": "SL-MEMORY-ECHO",
    "NAR-FAIRNESS": "SL-INSTITUTION-ETHICS",
    "NAR-DOWNSTREAM-RULES": "SL-INSTITUTION-ETHICS",
}


DECISIONS = [
    {
        "id": "DEC-S1-DUAL-PRECURSOR",
        "gap": "R-07 启动前的顾衡行动与沈逾选择必须同时成立且在启动点汇流。",
        "options": ["单线倒叙概括前史", "顾衡行动线与沈逾选择线双前置并行"],
        "selection": "顾衡行动线与沈逾选择线双前置并行",
        "owner": "S1",
        "authority_basis": "访谈明确要求 R-07 诞生前顾衡、沈逾双线推进，诞生后合并为主体线。",
        "compatibility": "不新增顾衡对沈逾的爱情，也保留沈逾自主接受任务的思想斗争。",
        "impact_ids": ["SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR", "SL-R07-MAIN"],
        "cost": "开篇必须控制两条前置线的篇幅并清晰标记时间关系。",
        "reversibility": "locked_by_downstream",
        "downstream_freedom": "后续可调整交替频率，不得取消双前置汇流结构。",
        "projection_ids": ["SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR"],
    },
    {
        "id": "DEC-S1-MAIN-CONVERGENCE",
        "gap": "数字生命自主性、袭击阻止和自主离开需要一条能够闭合的主体线。",
        "options": ["把危机行动作为主线", "把 R-07 从启动到自主离开作为主线"],
        "selection": "把 R-07 从启动到自主离开作为唯一主线",
        "owner": "S1",
        "authority_basis": "核心表达要求记忆继承后的新意识通过现实选择成为自己。",
        "compatibility": "危机行动仍提供不可回避的现实选择与代价，但不能取代生命主题。",
        "impact_ids": ["SL-R07-MAIN", "SL-ATTACK-OPERATIONS"],
        "cost": "所有外部行动都必须回到 R-07 的价值形成和选择，不能单独抢走主体。",
        "reversibility": "locked_by_downstream",
        "downstream_freedom": "可调整外部行动篇幅，不得改变主线主体。",
        "projection_ids": ["SL-R07-MAIN"],
    },
    {
        "id": "DEC-S1-PRESSURE-SYSTEM",
        "gap": "袭击、亲属保护、项目伦理与地缘政治若混成一线会失去各自职责。",
        "options": ["并入单一危机副线", "拆为行动、亲属、制度、地缘四条压力线"],
        "selection": "拆为行动、亲属、制度、地缘四条压力线",
        "owner": "S1",
        "authority_basis": "访谈分别锁定行动闭环、周岚代价、数字生命伦理和两国不互信。",
        "compatibility": "四线共享同一危机但分别改变信息、责任、权限与后果。",
        "impact_ids": ["SL-ATTACK-OPERATIONS", "SL-FAMILY-PROTECTION", "SL-INSTITUTION-ETHICS", "SL-GEOPOLITICAL"],
        "cost": "后续必须给每条压力线明确事件承载，避免只作背景说明。",
        "reversibility": "costly",
        "downstream_freedom": "可合并局部场景，不得删除其独立控制职责。",
        "projection_ids": ["SL-ATTACK-OPERATIONS", "SL-FAMILY-PROTECTION", "SL-INSTITUTION-ETHICS", "SL-GEOPOLITICAL"],
    },
    {
        "id": "DEC-S1-RELATION-INDEPENDENCE",
        "gap": "沈逾—R-07 情感必须证明为新经验所生，又不能改写成顾衡旧爱。",
        "options": ["作为主线中的情绪点", "建立独立关系支持线并在选择前汇入主线"],
        "selection": "建立独立关系支持线并在选择前汇入主线",
        "owner": "S1",
        "authority_basis": "角色访谈明确分离顾衡记忆、沈逾旧情与 R-07 新情感。",
        "compatibility": "关系线只增加选择代价，不替代袭击因果或关停能力限制。",
        "impact_ids": ["SL-RELATIONSHIP", "SL-R07-MAIN"],
        "cost": "必须通过连续互动而非宣言建立感情。",
        "reversibility": "locked_by_downstream",
        "downstream_freedom": "可调整互动载体，不得改变感情来源。",
        "projection_ids": ["SL-RELATIONSHIP"],
    },
    {
        "id": "DEC-S1-OPTIONAL-ECHOES",
        "gap": "记忆质感与重载悬念需要提升可读性，但不能承担主体因果。",
        "options": ["完全删除", "设为两条只做关联的可选旋律线"],
        "selection": "设为记忆回声与重载回声两条可选旋律线",
        "owner": "S1",
        "authority_basis": "叙述契约要求片段记忆可被打断，并把重载承诺保持开放。",
        "compatibility": "两线均只使用 associative 连接，删除后危机闭环和关停结局仍成立。",
        "impact_ids": ["SL-MEMORY-ECHO", "SL-RELOAD-ECHO"],
        "cost": "后续不得让旋律线提前泄露决定性内心或提供关键行动答案。",
        "reversibility": "reversible",
        "downstream_freedom": "开发阶段可缩减或不展开，但不得用其裁决开放项。",
        "projection_ids": ["SL-MEMORY-ECHO", "SL-RELOAD-ECHO"],
    },
]


def build_s1_model(session: dict[str, object], gate) -> tuple[dict[str, object], dict[str, object]]:
    baseline_path = RUN_ROOT / "B0" / "author-control-baseline.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    controls = []
    for entry in baseline["design_artifacts"]:
        authority = rt.verify_artifact_reference(entry["artifact"], root=RUN_ROOT / "B0")
        controls.extend(rt.extract_controls(authority, entry["domain"]))
    controls.sort(key=lambda item: item["id"])
    if set(CONTROL_TO_LINE) != {item["id"] for item in controls}:
        missing = sorted({item["id"] for item in controls} - set(CONTROL_TO_LINE))
        extra = sorted(set(CONTROL_TO_LINE) - {item["id"] for item in controls})
        raise RuntimeError(f"S1 control mapping mismatch missing={missing} extra={extra}")

    demands = []
    demands_by_line = {line_id: [] for line_id in LINE_SPECS}
    controls_by_line = {line_id: [] for line_id in LINE_SPECS}
    for index, control in enumerate(controls, 1):
        line_id = CONTROL_TO_LINE[control["id"]]
        demand_id = f"SLD-{index:03d}"
        line_type = LINE_SPECS[line_id]["type"]
        disposition = (
            "optional_melody"
            if line_type == "optional_melody"
            else "background_pressure"
            if line_type == "background"
            else "independent_line"
        )
        demand = {
            "id": demand_id,
            "source_ids": [control["id"]],
            "obligation": f"{control['heading']}\n{control['value']}\n该控制由 {line_id} 承担，不得改写其事实、边界或开放状态。",
            "disposition": disposition,
        }
        demands.append(demand)
        demands_by_line[line_id].append(demand_id)
        controls_by_line[line_id].append(control)

    decision_for_line = {}
    for decision in DECISIONS:
        for line_id in decision["projection_ids"]:
            decision_for_line.setdefault(line_id, []).append(decision["id"])
    decision_for_line.setdefault("SL-R07-MAIN", []).extend(
        ["DEC-S1-DUAL-PRECURSOR", "DEC-S1-PRESSURE-SYSTEM", "DEC-S1-RELATION-INDEPENDENCE"]
    )
    decision_for_line.setdefault("SL-ATTACK-OPERATIONS", []).append(
        "DEC-S1-MAIN-CONVERGENCE"
    )

    connections = [
        {"id": "SLC-GUHENG-R07", "type": "merge", "relation": "causal", "from_storyline_id": "SL-GUHENG-PRECURSOR", "to_storyline_id": "SL-R07-MAIN", "from_state": LINE_SPECS["SL-GUHENG-PRECURSOR"]["end_state"], "from_state_index": 4, "to_state": LINE_SPECS["SL-R07-MAIN"]["start_state"], "to_state_index": 0},
        {"id": "SLC-SHENYU-R07", "type": "handoff", "relation": "causal", "from_storyline_id": "SL-SHENYU-PRECURSOR", "to_storyline_id": "SL-R07-MAIN", "from_state": LINE_SPECS["SL-SHENYU-PRECURSOR"]["state_changes"][0], "from_state_index": 1, "to_state": LINE_SPECS["SL-R07-MAIN"]["start_state"], "to_state_index": 0},
        {"id": "SLC-RELATION-R07", "type": "collision", "relation": "causal", "from_storyline_id": "SL-RELATIONSHIP", "to_storyline_id": "SL-R07-MAIN", "from_state": LINE_SPECS["SL-RELATIONSHIP"]["state_changes"][2], "from_state_index": 3, "to_state": LINE_SPECS["SL-R07-MAIN"]["state_changes"][3], "to_state_index": 4},
        {"id": "SLC-ATTACK-R07", "type": "collision", "relation": "causal", "from_storyline_id": "SL-ATTACK-OPERATIONS", "to_storyline_id": "SL-R07-MAIN", "from_state": LINE_SPECS["SL-ATTACK-OPERATIONS"]["state_changes"][1], "from_state_index": 2, "to_state": LINE_SPECS["SL-R07-MAIN"]["state_changes"][3], "to_state_index": 4},
        {"id": "SLC-FAMILY-R07", "type": "handoff", "relation": "causal", "from_storyline_id": "SL-FAMILY-PROTECTION", "to_storyline_id": "SL-R07-MAIN", "from_state": LINE_SPECS["SL-FAMILY-PROTECTION"]["state_changes"][1], "from_state_index": 2, "to_state": LINE_SPECS["SL-R07-MAIN"]["state_changes"][3], "to_state_index": 4},
        {"id": "SLC-INSTITUTION-R07", "type": "collision", "relation": "causal", "from_storyline_id": "SL-INSTITUTION-ETHICS", "to_storyline_id": "SL-R07-MAIN", "from_state": LINE_SPECS["SL-INSTITUTION-ETHICS"]["state_changes"][1], "from_state_index": 2, "to_state": LINE_SPECS["SL-R07-MAIN"]["state_changes"][2], "to_state_index": 3},
        {"id": "SLC-GEO-ATTACK", "type": "synchronization", "relation": "causal", "from_storyline_id": "SL-GEOPOLITICAL", "to_storyline_id": "SL-ATTACK-OPERATIONS", "from_state": LINE_SPECS["SL-GEOPOLITICAL"]["state_changes"][0], "from_state_index": 1, "to_state": LINE_SPECS["SL-ATTACK-OPERATIONS"]["state_changes"][0], "to_state_index": 1},
        {"id": "SLC-MEMORY-R07", "type": "reveal", "relation": "associative", "from_storyline_id": "SL-MEMORY-ECHO", "to_storyline_id": "SL-R07-MAIN", "from_state": LINE_SPECS["SL-MEMORY-ECHO"]["state_changes"][1], "from_state_index": 2, "to_state": LINE_SPECS["SL-R07-MAIN"]["state_changes"][1], "to_state_index": 2},
        {"id": "SLC-RELOAD-R07", "type": "reveal", "relation": "associative", "from_storyline_id": "SL-RELOAD-ECHO", "to_storyline_id": "SL-R07-MAIN", "from_state": LINE_SPECS["SL-RELOAD-ECHO"]["end_state"], "from_state_index": 4, "to_state": LINE_SPECS["SL-R07-MAIN"]["end_state"], "to_state_index": 6},
    ]
    incident = {line_id: [] for line_id in LINE_SPECS}
    for connection in connections:
        incident[connection["from_storyline_id"]].append(connection["id"])
        incident[connection["to_storyline_id"]].append(connection["id"])

    storylines = []
    for line_id, spec in LINE_SPECS.items():
        control_text = "\n\n".join(
            item["value"]
            if isinstance(item["value"], str)
            else rt.canonical_json(item["value"])
            for item in controls_by_line[line_id]
        )
        storylines.append(
            {
                "id": line_id,
                "type": spec["type"],
                "responsibility": f"{spec['goal']}\n\n必须无损承担以下作者控制：\n{control_text}",
                "actor_slot_ids": spec["actor_slot_ids"],
                "goal": spec["goal"],
                "pressure": spec["pressure"],
                "start_state": spec["start_state"],
                "state_changes": spec["state_changes"],
                "end_state": spec["end_state"],
                "connection_ids": sorted(incident[line_id]),
                "source_decision_ids": sorted(set(decision_for_line.get(line_id, []))),
                "downstream_freedom": "后续阶段可设计具体规则、环境、事件和人物实现，但不得改变本线职责、状态方向、连接关系和来源控制原文。",
            }
        )

    architecture = {
        "subject": "一个继承他人记忆的新生命，如何在没有身体与现实感知的囚笼中，通过关系、危机和自主选择成为自己。",
        "opening_condition": "顾衡调查袭击并死亡；沈逾被推荐进入秘密基地，在伦理斗争后接受实验任务。",
        "development_logic": "双前置线在 R-07 启动时汇入主线；关系、行动、亲属、制度和地缘压力分别改变它能知道、能做和愿意承担的代价。",
        "turning_logic": "R-07 得知自身处境后崩溃；人质危机迫使交流重启，它由被动记忆接口转为主动设计情报与减少伤害。",
        "resolution_condition": "团队依靠核验、硬件和授权链完全阻止袭击；R-07 取得沈逾协助并终止当前实例，但重载、伦理责任和两国互信保持开放。",
        "theme_test": "若删除 R-07 启动后的新经验与自主选择，故事就只剩顾衡记忆的工具化续命，因此每个关键转折必须由新意识的连续价值形成解释。",
        "line_order": [
            "SL-GUHENG-PRECURSOR", "SL-SHENYU-PRECURSOR", "SL-RELATIONSHIP",
            "SL-FAMILY-PROTECTION", "SL-INSTITUTION-ETHICS", "SL-GEOPOLITICAL",
            "SL-ATTACK-OPERATIONS", "SL-R07-MAIN", "SL-MEMORY-ECHO", "SL-RELOAD-ECHO",
        ],
    }

    line_ids = list(LINE_SPECS)
    connection_ids = [item["id"] for item in connections]
    causal_ids = [item["id"] for item in connections if item["relation"] == "causal"]
    demand_ids = [item["id"] for item in demands]
    decision_ids = [item["id"] for item in DECISIONS]
    temporal = build_temporal_architecture()
    temporal_phase_ids = [item["id"] for item in temporal["phases"]]
    milestone_ids = [item["id"] for item in temporal["milestones"]]
    marker_ids = [item["id"] for item in temporal["markers"]]
    consistency = [
        {"id": "SLCHECK-TIME", "dimension": "time", "witness_ids": [*line_ids, *connection_ids, *temporal_phase_ids, *milestone_ids], "claim": "两条前置线只在 R-07 启动前独立存在，启动后所有压力线与主线并行推进，告别发生在袭击完全阻止之后。", "failure_condition": "任一连接要求 R-07 在启动前行动，或要求沈逾在袭击阻止前执行关停。"},
        {"id": "SLCHECK-CAUSALITY", "dimension": "causality", "witness_ids": [*line_ids, *causal_ids], "claim": "每条结构线都通过纯 causal 路径改变 R-07 主线的选择条件，可选旋律线不承担因果闭包。", "failure_condition": "存在结构线不能到达主线，或重载与记忆回声成为阻止袭击所必需的原因。"},
        {"id": "SLCHECK-INFORMATION", "dimension": "information", "witness_ids": [*line_ids, *connection_ids, *demand_ids, *milestone_ids, *marker_ids], "claim": "顾衡记忆、行动层情报、原因层情报和 R-07 的决定性内心按不同权限与时点释放；埋点、探针与回收只通过可观察信号推进。", "failure_condition": "团队在核验前即拥有完整行动答案，或读者在告别前直接获知 R-07 已决定终止。"},
        {"id": "SLCHECK-AUTHORITY", "dimension": "authority", "witness_ids": [*line_ids, *decision_ids, *demand_ids], "claim": "S1 只决定故事线职责与连接；世界规则、具体环境、事件记录和人物档案均交给唯一后续 owner。", "failure_condition": "任何故事线对象直接规定具体设备参数、场所拓扑、事件时间戳或完整人物履历。"},
        {"id": "SLCHECK-STATE", "dimension": "state", "witness_ids": [*line_ids, *connection_ids, *milestone_ids], "claim": "每条线从起点经有序变化抵达终点，时间里程碑与连接索引共同约束交汇。", "failure_condition": "任一里程碑引用不存在的状态，或结果状态在原因状态之前成立。"},
        {"id": "SLCHECK-THEME", "dimension": "theme", "witness_ids": [*line_ids, *connection_ids, *demand_ids, *decision_ids, *marker_ids], "claim": "所有结构线及其关键标记都把 R-07 从记忆载体推向能承担选择的新生命，开放旋律只保留余波。", "failure_condition": "结局可被解释为程序故障、顾衡遗愿机械执行或他人强迫，而不需要 R-07 的新经验。"},
    ]

    stage_specs = {
        "W1": ("WR", "定义支撑本线的世界规则、系统、机构、资源、权限与信息边界。", "世界层可选择制度名称和系统组织形式，但不能改变本线因果职责。"),
        "E1": ("END", "定义能够具体承载本线全部状态与连接的环境、功能区、准入和资源。", "环境层可选择地点组合与空间风格，但必须承载全部状态变化。"),
        "T1": ("EVD", "定义能够把本线状态变化和跨线连接落实为完整时间事件链的事件能力。", "事件层可选择节拍与并行窗口，但不得跳过原因、行动、核验、代价和后果。"),
        "C1": ("CHD", "把本线角色槽解析为具有目标、能力、权限、信息和关系连续性的规范人物。", "角色层可补足姓名与履历，但不得改变已锁定人物事实和职责边界。"),
    }
    requirements = {"W1": [], "E1": [], "T1": [], "C1": []}
    for stage, (prefix, responsibility, freedom) in stage_specs.items():
        for index, line_id in enumerate(LINE_SPECS, 1):
            demand_refs = demands_by_line[line_id]
            line_milestones = [
                item["id"] for item in temporal["milestones"]
                if line_id in item["storyline_ids"]
            ]
            line_markers = [
                item["id"] for item in temporal["markers"]
                if line_id in item["storyline_ids"]
            ]
            source_values = "\n\n".join(
                item["value"]
                if isinstance(item["value"], str)
                else rt.canonical_json(item["value"])
                for item in controls_by_line[line_id]
            )
            requirements[stage].append(
                {
                    "id": f"{prefix}-{index:02d}",
                    "target_stage": stage,
                    "responsibility": f"{responsibility} 对象：{line_id}。",
                    "source_ids": [line_id, *demand_refs],
                    "required_capability": f"必须解释并承载 {LINE_SPECS[line_id]['goal']}",
                    "constraints": [
                        f"必须无损遵守以下来源控制原文：\n{source_values}",
                        f"不得越权改变 {line_id} 的起点、状态方向、终点和连接。",
                        f"不得改变共享时间主轴中的里程碑 {', '.join(line_milestones)} 及其标记功能。",
                    ],
                    "acceptance_checks": [
                        f"逐项覆盖 {', '.join(demand_refs)}。",
                        f"交付结果能够验证 {line_id} 的全部状态变化和关联。",
                        f"能够追溯并实现叙事标记 {', '.join(line_markers)}。",
                    ],
                    "downstream_freedom": freedom,
                }
            )

    coverage = [
        {
            "id": f"COV-{index:03d}",
            "source_ids": [demand["id"]],
            "realization_ids": [CONTROL_TO_LINE[demand["source_ids"][0]]],
            "status": "covered",
            "evidence": f"{demand['id']} 仅由 {CONTROL_TO_LINE[demand['source_ids'][0]]} 承担，并由四类下游需求继续展开。",
        }
        for index, demand in enumerate(demands, 1)
    ]
    locked = [item["id"] for item in controls if item["hardness"] == "author_locked"]
    author_open = [item["id"] for item in controls if item["hardness"] == "author_open"]
    downstream_ids = [
        item["id"] for stage in ("W1", "E1", "T1", "C1") for item in requirements[stage]
    ]

    model = {
        "schema_version": "2.0",
        "skill": "novel-storyline-architecture-designer",
        "stage": "S1",
        "run_id": RUN_ID,
        "status": "ready",
        "input_gate": gate.reference,
        "source_artifacts": session["source_artifacts"],
        "authority_partition": {
            "author_locked": locked,
            "autonomous_owned": [
                *decision_ids, *line_ids, *temporal_phase_ids,
                *milestone_ids, *marker_ids,
            ],
            "downstream_freedom": downstream_ids,
            "author_open": author_open,
        },
        "design_decisions": DECISIONS,
        "derivation_claims": [],
        "storyline_demands": demands,
        "storylines": storylines,
        "connections": connections,
        "architecture": architecture,
        "temporal_architecture": temporal,
        "cross_line_consistency": consistency,
        "world_requirements": requirements["W1"],
        "environment_requirements": requirements["E1"],
        "event_requirements": requirements["T1"],
        "character_requirements": requirements["C1"],
        "coverage_ledger": coverage,
        "open_items": [
            {"id": "OPEN-READER-QUESTIONS", "question": "R-07 与顾衡究竟是什么关系，沈逾在回应谁？", "source_ids": ["INT-READER-QUESTIONS"], "status": "author_open"},
            {"id": "OPEN-FIRST-BOOK", "question": "原因链、数字生命伦理与后续责任如何在未来继续展开？", "source_ids": ["CAU-PRESERVED-OPEN"], "status": "author_open"},
            {"id": "OPEN-RELOAD", "question": "重新加载承诺是真实可能、善意欺骗还是未来会被兑现？", "source_ids": ["NAR-ENDING-PRESERVED-OPEN"], "status": "author_open"},
        ],
    }
    derivations = []
    line_by_id = {item["id"]: item for item in storylines}
    for index, line_id in enumerate(line_ids, 1):
        control_ids = [item["id"] for item in controls_by_line[line_id]]
        derivations.append(
            {
                "id": f"DRV-LINE-{index:02d}",
                "value_sha256": rt.canonical_sha256(line_by_id[line_id]),
                "source_ids": control_ids,
                "decision_ids": line_by_id[line_id]["source_decision_ids"],
                "projection_ids": [line_id],
            }
        )
    derivations.append(
        {
            "id": "DRV-ARCHITECTURE",
            "value_sha256": rt.canonical_sha256(architecture),
            "source_ids": ["INT-CORE-EXPRESSION", "CAU-GLOBAL-SPINE", "NAR-CONTRACT-GOAL"],
            "decision_ids": decision_ids,
            "projection_ids": line_ids,
        }
    )
    derivations.append(
        {
            "id": "DRV-TEMPORAL-ARCHITECTURE",
            "value_sha256": rt.canonical_sha256(temporal),
            "source_ids": [
                "CAU-GLOBAL-SPINE", "CAU-MAJOR-NODES", "NAR-FAIRNESS",
            ],
            "decision_ids": decision_ids,
            "projection_ids": [
                *temporal_phase_ids, *milestone_ids, *marker_ids,
            ],
        }
    )
    model["derivation_claims"] = derivations
    phases = {
        "demand-scan": {"storyline_demands": demands},
        "line-design": {"design_decisions": DECISIONS, "storylines": storylines},
        "topology-and-consistency": {
            "connections": connections,
            "architecture": architecture,
            "temporal_architecture": temporal,
            "cross_line_consistency": consistency,
        },
        "downstream-requirements": {
            "world_requirements": requirements["W1"],
            "environment_requirements": requirements["E1"],
            "event_requirements": requirements["T1"],
            "character_requirements": requirements["C1"],
            "coverage_ledger": coverage,
            "authority_partition": model["authority_partition"],
            "derivation_claims": derivations,
            "open_items": model["open_items"],
        },
        "final-storyline-model": {"model": model},
    }
    return model, phases


def run_s1() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None:
        gate, order = prod.issue_stage_work(
            context,
            action="S1",
            inputs={"baseline_package": str(RUN_ROOT / "B0")},
        )
    else:
        if order.data.get("action") != "S1":
            raise RuntimeError(
                f"cannot resume S1 while {order.data.get('action')} is pending"
            )
        gate = context.store.load_document(order.data["input_gate"])

    def execute_s1(coordinator, input_gate):
        # Failed attempts are preserved as immutable validation evidence.  The
        # corrected gate/package lineage and semantic-containment validators are
        # exercised in attempt 04.
        workspace = RUN_ROOT / "workspaces" / "S1-attempt-04"
        session = s1rt.start_s1_session(
            workspace,
            baseline_package=RUN_ROOT / "B0",
            input_gate=input_gate,
        )
        _, phases = build_s1_model(session, input_gate)
        for phase in s1rt.PHASES:
            s1rt.submit_s1_phase(
                workspace,
                baseline_package=RUN_ROOT / "B0",
                input_gate=input_gate,
                phase=phase,
                payload=phases[phase],
            )
        return s1rt.run_s1(
            RUN_ROOT / "S1",
            baseline_package=RUN_ROOT / "B0",
            coordinator=coordinator,
            input_gate=input_gate,
            controlled_workspace=workspace,
            logical_package_path="S1",
            next_state_path="state/revision-002.json",
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-storyline-architecture-designer",
        executor=execute_s1,
    )
    return {
        "run_id": RUN_ID,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "storylines": len(receipt.model["storylines"]),
        "connections": len(receipt.model["connections"]),
        "state_revision": successor.state.data["revision"],
    }


def _next_attempt_workspace(stage: str) -> Path:
    """Return a new workspace path without overwriting failed evidence."""

    root = RUN_ROOT / "workspaces"
    index = 1
    while True:
        candidate = root / f"{stage}-attempt-{index:02d}"
        if not candidate.exists():
            return candidate
        index += 1


def _build_w1(session: dict[str, object], input_gate) -> tuple[dict[str, object], dict[str, object]]:
    baseline = json.loads(
        (RUN_ROOT / "B0" / "author-control-baseline.json").read_text(
            encoding="utf-8"
        )
    )
    storyline = json.loads(
        (RUN_ROOT / "S1" / "storyline-architecture.json").read_text(
            encoding="utf-8"
        )
    )
    return w1builder.build_w1_model(
        run_id=RUN_ID,
        gate_reference=input_gate.reference,
        source_artifacts=session["source_artifacts"],
        baseline=baseline,
        storyline=storyline,
        canonical_sha256=rt.canonical_sha256,
    )


def validate_w1_draft() -> dict[str, object]:
    """Validate W1 semantics without issuing a work order or writing a package."""

    b0_root = RUN_ROOT / "B0"
    s1_root = RUN_ROOT / "S1"
    baseline = json.loads(
        (b0_root / "author-control-baseline.json").read_text(encoding="utf-8")
    )
    storyline = json.loads(
        (s1_root / "storyline-architecture.json").read_text(encoding="utf-8")
    )
    gate_reference = {
        "path": "orchestration/input-gates/draft-W1/input-gate.json",
        "sha256": "0" * 64,
    }
    source_artifacts = w1rt._source_artifacts(b0_root, s1_root)
    model, phases = w1builder.build_w1_model(
        run_id=RUN_ID,
        gate_reference=gate_reference,
        source_artifacts=source_artifacts,
        baseline=baseline,
        storyline=storyline,
        canonical_sha256=rt.canonical_sha256,
    )
    w1rt._validate_model(
        model,
        baseline,
        storyline,
        w1rt._controls(b0_root, baseline),
        rt.ContractRuntime(),
        expected_gate=gate_reference,
        expected_sources=source_artifacts,
    )
    if tuple(phases) != tuple(w1rt.PHASES):
        raise RuntimeError("W1 phase payloads do not match the runtime contract")
    return {
        "stage": "W1",
        "status": "draft-valid",
        "requirements": len(model["storyline_requirements"]),
        "rules": len(model["world_facts"]),
        "systems": len(model["systems"]),
        "environment_demands": len(model["environment_demands"]),
    }


def run_w1() -> dict[str, object]:
    """Run W1 through the production orchestrator, resuming a pending order."""

    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="W1",
            inputs={
                "baseline_package": str(RUN_ROOT / "B0"),
                "storyline_package": str(RUN_ROOT / "S1"),
            },
        )
    elif order.data.get("action") != "W1":
        raise RuntimeError(
            f"cannot resume W1 while {order.data.get('action')} is pending"
        )

    def execute_w1(coordinator, input_gate):
        workspace = _next_attempt_workspace("W1")
        session = w1rt.start_w1_session(
            workspace,
            baseline_package=RUN_ROOT / "B0",
            storyline_package=RUN_ROOT / "S1",
            input_gate=input_gate,
        )
        model, phases = _build_w1(session, input_gate)
        for phase in w1rt.PHASES:
            w1rt.submit_w1_phase(
                workspace,
                baseline_package=RUN_ROOT / "B0",
                storyline_package=RUN_ROOT / "S1",
                input_gate=input_gate,
                phase=phase,
                payload=phases[phase],
            )
        return w1rt.run_w1(
            RUN_ROOT / "W1",
            baseline_package=RUN_ROOT / "B0",
            storyline_package=RUN_ROOT / "S1",
            coordinator=coordinator,
            input_gate=input_gate,
            controlled_workspace=workspace,
            logical_package_path="W1",
            next_state_path="state/revision-003.json",
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-world-model-designer",
        executor=execute_w1,
    )
    return {
        "run_id": RUN_ID,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "rules": len(receipt.model["world_facts"]),
        "systems": len(receipt.model["systems"]),
        "environment_demands": len(receipt.model["environment_demands"]),
        "state_revision": successor.state.data["revision"],
    }


def validate_e1_draft() -> dict[str, object]:
    """Validate the E1 candidate without issuing work or changing run state."""

    return e1builder.validate_e1_draft(
        run_root=RUN_ROOT,
        e1_runtime=e1rt,
        contract_runtime=rt,
    )


def run_e1() -> dict[str, object]:
    """Run E1 through the production orchestrator after W1 is current-ready."""

    return e1builder.run_e1_production(
        run_root=RUN_ROOT,
        production_runtime=prod,
        e1_runtime=e1rt,
        contract_runtime=rt,
    )


def validate_t1_draft() -> dict[str, object]:
    """Validate the T1 proposal against the actual sealed B0/S1/W1/E1."""

    b0_root = RUN_ROOT / "B0"
    s1_root = RUN_ROOT / "S1"
    w1_root = RUN_ROOT / "W1"
    e1_root = RUN_ROOT / "E1"
    baseline = json.loads(
        (b0_root / "author-control-baseline.json").read_text(encoding="utf-8")
    )
    storyline = json.loads(
        (s1_root / "storyline-architecture.json").read_text(encoding="utf-8")
    )
    world = json.loads(
        (w1_root / "world-model.json").read_text(encoding="utf-8")
    )
    environment = json.loads(
        (e1_root / "environment-system.json").read_text(encoding="utf-8")
    )
    gate_reference = {
        "path": "orchestration/input-gates/draft-T1/input-gate.json",
        "sha256": "0" * 64,
    }
    source_artifacts = t1rt._source_artifacts(
        b0_root, s1_root, w1_root, e1_root
    )
    model, phases = t1builder.build_t1_model(
        run_id=RUN_ID,
        gate_reference=gate_reference,
        source_artifacts=source_artifacts,
        baseline=baseline,
        storyline=storyline,
        world=world,
        environment=environment,
        runtime=rt.ContractRuntime(),
    )
    t1rt._validate_model(
        model,
        baseline,
        storyline,
        world,
        environment,
        t1rt._controls(b0_root, baseline),
        rt.ContractRuntime(),
        expected_gate=gate_reference,
        expected_sources=source_artifacts,
    )
    if tuple(phases) != tuple(t1rt.PHASES):
        raise RuntimeError("T1 phase payloads do not match the runtime contract")
    return {
        "stage": "T1",
        "status": "draft-valid",
        "events": len(model["major_events"]),
        "causal_edges": len(model["causal_edges"]),
        "connections": len(model["connection_realization"]),
        "state_transitions": len(model["state_ledger"]),
        "information_changes": len(model["information_changes"]),
    }


def run_t1() -> dict[str, object]:
    """Run T1 through the production orchestrator, resuming pending work."""

    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="T1",
            inputs={
                "baseline_package": str(RUN_ROOT / "B0"),
                "storyline_package": str(RUN_ROOT / "S1"),
                "world_package": str(RUN_ROOT / "W1"),
                "environment_package": str(RUN_ROOT / "E1"),
            },
        )
    elif order.data.get("action") != "T1":
        raise RuntimeError(
            f"cannot resume T1 while {order.data.get('action')} is pending"
        )

    def execute_t1(coordinator, input_gate):
        workspace = _next_attempt_workspace("T1")
        session = t1rt.start_t1_session(
            workspace,
            baseline_package=RUN_ROOT / "B0",
            storyline_package=RUN_ROOT / "S1",
            world_package=RUN_ROOT / "W1",
            environment_package=RUN_ROOT / "E1",
            input_gate=input_gate,
        )
        model, phases = t1builder.build_t1_from_packages(
            baseline_package=RUN_ROOT / "B0",
            storyline_package=RUN_ROOT / "S1",
            world_package=RUN_ROOT / "W1",
            environment_package=RUN_ROOT / "E1",
            session=session,
            runtime=rt.ContractRuntime(),
        )
        for phase in t1rt.PHASES:
            t1rt.submit_t1_phase(
                workspace,
                baseline_package=RUN_ROOT / "B0",
                storyline_package=RUN_ROOT / "S1",
                world_package=RUN_ROOT / "W1",
                environment_package=RUN_ROOT / "E1",
                input_gate=input_gate,
                phase=phase,
                payload=phases[phase],
            )
        return t1rt.run_t1(
            RUN_ROOT / "T1",
            baseline_package=RUN_ROOT / "B0",
            storyline_package=RUN_ROOT / "S1",
            world_package=RUN_ROOT / "W1",
            environment_package=RUN_ROOT / "E1",
            coordinator=coordinator,
            input_gate=input_gate,
            controlled_workspace=workspace,
            logical_package_path="T1",
            next_state_path="state/revision-005.json",
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-event-timeline-designer",
        executor=execute_t1,
    )
    return {
        "run_id": RUN_ID,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "events": len(receipt.model["major_events"]),
        "causal_edges": len(receipt.model["causal_edges"]),
        "connections": len(receipt.model["connection_realization"]),
        "state_revision": successor.state.data["revision"],
    }


def _load_c1_inputs():
    roots = {stage: RUN_ROOT / stage for stage in ("B0", "S1", "W1", "E1", "T1")}
    return roots, (
        json.loads((roots["B0"] / "author-control-baseline.json").read_text(encoding="utf-8")),
        json.loads((roots["S1"] / "storyline-architecture.json").read_text(encoding="utf-8")),
        json.loads((roots["W1"] / "world-model.json").read_text(encoding="utf-8")),
        json.loads((roots["E1"] / "environment-system.json").read_text(encoding="utf-8")),
        json.loads((roots["T1"] / "event-timeline.json").read_text(encoding="utf-8")),
    )


def _build_c1(session, models):
    baseline, storyline, world, environment, timeline = models
    return c1builder.build_c1_model(
        run_id=RUN_ID,
        gate_reference=session["input_gate"],
        source_artifacts=session["source_artifacts"],
        baseline=baseline,
        storyline=storyline,
        world=world,
        environment=environment,
        timeline=timeline,
        c1_runtime=c1rt,
        canonical_sha256=rt.canonical_sha256,
    )


def validate_c1_draft() -> dict[str, object]:
    roots, models = _load_c1_inputs()
    baseline, storyline, world, environment, timeline = models
    gate_reference = {"path": "orchestration/input-gates/draft-C1/input-gate.json", "sha256": "0" * 64}
    session = {
        "input_gate": gate_reference,
        "source_artifacts": c1rt._source_artifacts(
            roots["B0"], roots["S1"], roots["W1"], roots["E1"], roots["T1"]
        ),
    }
    model, phases = _build_c1(session, models)
    c1rt._validate_model(
        model,
        baseline,
        storyline,
        world,
        environment,
        timeline,
        c1rt._controls(roots["B0"], baseline),
        rt.ContractRuntime(),
        expected_gate=gate_reference,
        expected_sources=session["source_artifacts"],
    )
    if tuple(phases) != tuple(c1rt.PHASES):
        raise RuntimeError("C1 phase payloads do not match the runtime contract")
    return {
        "stage": "C1",
        "status": "draft-valid",
        "profiles": len(model["profiles"]),
        "relationships": len(model["relationships"]),
        "core_networks": len(model["three_layer_networks"]),
        "resolved_slots": len(model["slot_resolution"]),
    }


def run_c1() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="C1",
            inputs={
                "baseline_package": str(RUN_ROOT / "B0"),
                "storyline_package": str(RUN_ROOT / "S1"),
                "world_package": str(RUN_ROOT / "W1"),
                "environment_package": str(RUN_ROOT / "E1"),
                "event_package": str(RUN_ROOT / "T1"),
            },
        )
    elif order.data.get("action") != "C1":
        raise RuntimeError(f"cannot resume C1 while {order.data.get('action')} is pending")

    def execute_c1(coordinator, input_gate):
        roots, models = _load_c1_inputs()
        workspace = _next_attempt_workspace("C1")
        session = c1rt.start_c1_session(
            workspace,
            baseline_package=roots["B0"],
            storyline_package=roots["S1"],
            world_package=roots["W1"],
            environment_package=roots["E1"],
            event_package=roots["T1"],
            input_gate=input_gate,
        )
        _, phases = _build_c1(session, models)
        for phase in c1rt.PHASES:
            c1rt.submit_c1_phase(
                workspace,
                baseline_package=roots["B0"],
                storyline_package=roots["S1"],
                world_package=roots["W1"],
                environment_package=roots["E1"],
                event_package=roots["T1"],
                input_gate=input_gate,
                phase=phase,
                payload=phases[phase],
            )
        return c1rt.run_c1(
            RUN_ROOT / "C1",
            baseline_package=roots["B0"],
            storyline_package=roots["S1"],
            world_package=roots["W1"],
            environment_package=roots["E1"],
            event_package=roots["T1"],
            coordinator=coordinator,
            input_gate=input_gate,
            controlled_workspace=workspace,
            logical_package_path="C1",
            next_state_path="state/revision-006.json",
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-character-system-designer",
        executor=execute_c1,
    )
    return {
        "run_id": RUN_ID,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "profiles": len(receipt.model["profiles"]),
        "relationships": len(receipt.model["relationships"]),
        "state_revision": successor.state.data["revision"],
    }


def start_q1_controller_only() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None:
        gate, order = prod.issue_stage_work(
            context,
            action="Q1",
            inputs={
                "baseline_package": str(RUN_ROOT / "B0"),
                "storyline_package": str(RUN_ROOT / "S1"),
                "world_package": str(RUN_ROOT / "W1"),
                "environment_package": str(RUN_ROOT / "E1"),
                "event_package": str(RUN_ROOT / "T1"),
                "character_package": str(RUN_ROOT / "C1"),
            },
        )
    elif order.data.get("action") == "Q1":
        gate = context.store.load_document(order.data["input_gate"])
    else:
        raise RuntimeError(
            f"cannot start Q1 while {order.data.get('action')} is pending"
        )
    frozen = q1rt.start_q1_controller(
        Q1_CONTROLLER,
        baseline_package=RUN_ROOT / "B0",
        storyline_package=RUN_ROOT / "S1",
        world_package=RUN_ROOT / "W1",
        environment_package=RUN_ROOT / "E1",
        event_package=RUN_ROOT / "T1",
        character_package=RUN_ROOT / "C1",
        input_gate=gate,
    )
    return {
        "run_id": RUN_ID,
        "stage": "Q1",
        "status": "inputs_frozen",
        "controller_workspace": str(Q1_CONTROLLER),
        "semantic_workspace": str(Q1_SEMANTIC),
        "handoff_workspace": str(Q1_HANDOFF),
        "frozen_sources": len(frozen["source_inventory"]),
    }


def run_p1() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="P1",
            inputs={
                "baseline_package": str(RUN_ROOT / "B0"),
                "storyline_package": str(RUN_ROOT / "S1"),
                "world_package": str(RUN_ROOT / "W1"),
                "environment_package": str(RUN_ROOT / "E1"),
                "event_package": str(RUN_ROOT / "T1"),
                "character_package": str(RUN_ROOT / "C1"),
                "review_package": str(RUN_ROOT / "Q1"),
            },
        )
    elif order.data.get("action") != "P1":
        raise RuntimeError(
            f"cannot resume P1 while {order.data.get('action')} is pending"
        )

    def execute_p1(coordinator, input_gate):
        return p1rt.run_p1(
            RUN_ROOT / "P1",
            baseline_package=RUN_ROOT / "B0",
            storyline_package=RUN_ROOT / "S1",
            world_package=RUN_ROOT / "W1",
            environment_package=RUN_ROOT / "E1",
            event_package=RUN_ROOT / "T1",
            character_package=RUN_ROOT / "C1",
            review_package=RUN_ROOT / "Q1",
            coordinator=coordinator,
            input_gate=input_gate,
            logical_package_path="P1",
            next_state_path="state/revision-008.json",
        )

    receipt, successor = prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-conception-deliverable-assembler",
        executor=execute_p1,
    )
    return {
        "run_id": RUN_ID,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "state_revision": successor.state.data["revision"],
        "replayed": receipt.replayed,
        "machine_spec": str(RUN_ROOT / "P1" / "novel-conception-spec.md"),
    }


def initialize_h1() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    workspace = prod.initialize_h1_workspace(
        context, session_id=H1_SESSION_ID
    )
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="H1-A-plan",
            inputs={
                "p1_package": str(RUN_ROOT / "P1"),
                "work_title": authoritative_work_title(),
            },
        )
    elif order.data.get("action") != "H1-A-plan":
        raise RuntimeError(
            f"cannot initialize H1 while {order.data.get('action')} is pending"
        )
    return {
        "run_id": RUN_ID,
        "stage": "H1",
        "status": workspace.data["state"],
        "session_id": workspace.data["session_id"],
        "workspace": workspace.reference,
        "pending_action": order.data["action"],
    }


def issue_h1_fragment_work() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    workspace = context.store.latest_workspace()
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="H1-B",
            inputs={
                "p1_package": str(RUN_ROOT / "P1"),
                "plan_package": str(RUN_ROOT / "H1" / "plan"),
            },
        )
    elif order.data.get("action") != "H1-B":
        raise RuntimeError(
            f"cannot issue H1-B while {order.data.get('action')} is pending"
        )
    return {
        "run_id": RUN_ID,
        "stage": "H1",
        "status": workspace.data["state"],
        "pending_action": order.data["action"],
    }


def issue_h1_assembly_work() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    workspace = context.store.latest_workspace()
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="H1-A-assemble",
            inputs={
                "p1_package": str(RUN_ROOT / "P1"),
                "plan_package": str(RUN_ROOT / "H1" / "plan"),
                "fragment_package": str(RUN_ROOT / "H1" / "fragments"),
            },
        )
    elif order.data.get("action") != "H1-A-assemble":
        raise RuntimeError(
            f"cannot issue H1-A-assemble while {order.data.get('action')} is pending"
        )
    return {
        "run_id": RUN_ID,
        "stage": "H1",
        "status": workspace.data["state"],
        "pending_action": order.data["action"],
    }


def issue_h1_html_work() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    workspace = context.store.latest_workspace()
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="H1-C",
            inputs={
                "p1_package": str(RUN_ROOT / "P1"),
                "plan_package": str(RUN_ROOT / "H1" / "plan"),
                "fragment_package": str(RUN_ROOT / "H1" / "fragments"),
                "assembly_package": str(RUN_ROOT / "H1" / "assembly"),
            },
        )
    elif order.data.get("action") != "H1-C":
        raise RuntimeError(
            f"cannot issue H1-C while {order.data.get('action')} is pending"
        )
    return {
        "run_id": RUN_ID,
        "stage": "H1",
        "status": workspace.data["state"],
        "pending_action": order.data["action"],
    }


def _h1_workspace(filename: str):
    path = RUN_ROOT / "H1" / H1_SESSION_ID / filename
    return rt.SealedDocument(
        data=json.loads(path.read_text(encoding="utf-8")),
        reference={
            "path": f"H1/{H1_SESSION_ID}/{filename}",
            "sha256": rt.sha256_file(path),
        },
    )


def run_h1_publish() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    rendered = _h1_workspace("workspace-rendered.json")
    order = context.store.pending_work_order()
    if order is None:
        _, order = prod.issue_stage_work(
            context,
            action="H1-publish",
            inputs={
                "p1_package": str(RUN_ROOT / "P1"),
                "plan_package": str(RUN_ROOT / "H1" / "plan"),
                "fragment_package": str(RUN_ROOT / "H1" / "fragments"),
                "assembly_package": str(RUN_ROOT / "H1" / "assembly"),
                "html_package": str(RUN_ROOT / "H1" / "html"),
            },
        )
    elif order.data.get("action") != "H1-publish":
        raise RuntimeError(
            f"cannot publish H1 while {order.data.get('action')} is pending"
        )
    plan_execution = json.loads(
        (RUN_ROOT / "H1" / "plan" / "execution-record.json").read_text(
            encoding="utf-8"
        )
    )
    plan_gate = context.store.load_document(plan_execution["input_gate"])
    receipt, successor = prod.publish_h1_transaction(
        context,
        RUN_ROOT / "H1" / "stage",
        work_order=order,
        p1_package=RUN_ROOT / "P1",
        plan_package=RUN_ROOT / "H1" / "plan",
        plan_input_gate=plan_gate,
        plan_workspace_state=_h1_workspace("workspace-initialized.json"),
        fragment_package=RUN_ROOT / "H1" / "fragments",
        fragment_workspace_state=_h1_workspace("workspace-planned.json"),
        assembly_package=RUN_ROOT / "H1" / "assembly",
        assembly_workspace_state=_h1_workspace("workspace-fragments_ready.json"),
        html_package=RUN_ROOT / "H1" / "html",
        rendered_workspace=rendered,
        logical_package_path="H1/stage",
    )
    return {
        "run_id": RUN_ID,
        "stage": receipt.completion.data["stage"],
        "status": receipt.completion.data["status"],
        "state_revision": successor.state.data["revision"],
        "workflow_status": successor.state.data["status"],
        "html": str(RUN_ROOT / "H1" / "html" / "human-review-report.html"),
    }


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "status"
    if action == "b0":
        result = initialize_b0()
    elif action == "s1":
        result = run_s1()
    elif action == "validate-w1-draft":
        result = validate_w1_draft()
    elif action == "w1":
        result = run_w1()
    elif action == "validate-e1-draft":
        result = validate_e1_draft()
    elif action == "e1":
        result = run_e1()
    elif action == "validate-t1-draft":
        result = validate_t1_draft()
    elif action == "t1":
        result = run_t1()
    elif action == "validate-c1-draft":
        result = validate_c1_draft()
    elif action == "c1":
        result = run_c1()
    elif action == "q1-controller":
        result = start_q1_controller_only()
    elif action == "p1":
        result = run_p1()
    elif action == "h1-init":
        result = initialize_h1()
    elif action == "h1-fragments-issue":
        result = issue_h1_fragment_work()
    elif action == "h1-assembly-issue":
        result = issue_h1_assembly_work()
    elif action == "h1-html-issue":
        result = issue_h1_html_work()
    elif action == "h1-publish":
        result = run_h1_publish()
    elif action == "status":
        context = prod.resume_production_run(RUN_ROOT)
        result = context.state.data
    else:
        raise SystemExit(f"unknown action: {action}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
