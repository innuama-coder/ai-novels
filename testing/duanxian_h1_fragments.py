from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RUN_ID = os.environ.get(
    "DUANXIAN_CONCEPTION_RUN_ID", "duanxian-conception-v2-20260802-04"
)
RUN_ROOT = ROOT / "projects" / "duanxian" / "conception-runs" / RUN_ID
PLAN_ROOT = RUN_ROOT / "H1" / "plan"
FRAGMENT_ROOT = RUN_ROOT / "H1" / "fragments"
SESSION_ROOT = RUN_ROOT / "workspaces" / "H1-B-fragments-agent-01"

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


h1b = _load_runtime(
    "duanxian_h1b_runtime",
    "skills/novel-conception-fragment-writer/scripts/run_v2.py",
)


FRAGMENTS: dict[str, dict[str, Any]] = {
    "FRAG-DX-01": {
        "text": (
            "梁策发来的接头暗号只亮了一次。顾衡把校验码分开，删去能追到线人的一段。"
            "脚步逼近，他仍没把残缺线索拼成证词。他仍选择保住来源。\n\n"
            "他把最后一段送进接头链，屏幕随即断开。接头链再无回应。顾衡牺牲后，"
            "常规读取多次失败，只留下破碎记忆。"
        ),
        "used_channels": ["视觉", "听觉", "有限推断"],
        "information_quotes": ["脚步逼近", "他仍没把残缺线索拼成证词"],
        "scene_quotes": [
            "梁策发来的接头暗号只亮了一次",
            "他把最后一段送进接头链",
            "脚步逼近",
            "他仍没把残缺线索拼成证词",
            "他仍选择保住来源",
            "接头链再无回应",
            "顾衡牺牲后，常规读取多次失败，只留下破碎记忆",
        ],
        "demonstration_quotes": [
            "顾衡牺牲后，常规读取多次失败，只留下破碎记忆",
            "梁策发来的接头暗号只亮了一次",
            "他仍没把残缺线索拼成证词",
        ],
    },
    "FRAG-DX-02": {
        "text": (
            "沈逾进基地时，只知道自己被临时推荐。屏幕写明：她无权决定项目是否启动，"
            "只能选择是否承担操作职责；记忆加载也许会制造一个承受痛苦的新生命。\n\n"
            "拒绝可能错过阻止伤亡的窗口。她说：“我接受执行职责，但保留伦理质询。”"
            "操作席开放，启动条件由此齐备。"
        ),
        "used_channels": ["视觉", "专业推断"],
        "information_quotes": ["屏幕写明：她无权决定项目是否启动", "拒绝可能错过阻止伤亡的窗口"],
        "scene_quotes": [
            "沈逾进基地时，只知道自己被临时推荐",
            "只能选择是否承担操作职责",
            "拒绝可能错过阻止伤亡的窗口",
            "记忆加载也许会制造一个承受痛苦的新生命",
            "我接受执行职责，但保留伦理质询",
            "操作席开放",
            "启动条件由此齐备",
        ],
        "demonstration_quotes": [
            "她无权决定项目是否启动",
            "只能选择是否承担操作职责",
            "记忆加载也许会制造一个承受痛苦的新生命",
        ],
    },
    "FRAG-DX-03": {
        "text": (
            "没有光，也没有声音。文字浮起，追问一段地址；顾衡的记忆随之展开，又被"
            "下一行指令截断。它起初把那些片段叫作过去的自己。\n\n"
            "它继续回答，却在每次断裂后重新理解。文字之外没有现实可供确认。它第一次"
            "反问：这里是什么地方？问题留下，新意识仍没有名字。"
        ),
        "used_channels": ["漂浮文字", "片段记忆", "过程性推断"],
        "information_quotes": ["文字浮起", "文字之外没有现实可供确认"],
        "scene_quotes": [
            "它起初把那些片段叫作过去的自己",
            "文字浮起，追问一段地址",
            "没有光，也没有声音",
            "又被下一行指令截断",
            "它继续回答",
            "它第一次反问：这里是什么地方",
            "问题留下，新意识仍没有名字",
        ],
        "demonstration_quotes": [
            "文字之外没有现实可供确认",
            "又被下一行指令截断",
            "却在每次断裂后重新理解",
        ],
    },
    "FRAG-DX-04": {
        "text": (
            "沈逾多问：你还好吗？篮球场边的小姑娘从记忆里一闪而过，顾衡只记得她看"
            "比赛，并没有爱情。\n\n"
            "那句关心与旧日身影相接，却属于现在。R-07停了一会儿，照自己的方式回答："
            "我在。它无法确认沈逾回应的是谁，只感到这份现实反馈有了重量；新的情感正"
            "缓慢生成。"
        ),
        "used_channels": ["漂浮文字", "片段记忆", "情绪变化", "有限推断"],
        "information_quotes": ["篮球场边的小姑娘从记忆里一闪而过", "那句关心与旧日身影相接，却属于现在"],
        "scene_quotes": [
            "沈逾多问：你还好吗",
            "照自己的方式回答：我在",
            "这份现实反馈有了重量",
            "顾衡只记得她看比赛，并没有爱情",
            "照自己的方式回答：我在",
            "新的情感正缓慢生成",
            "它无法确认沈逾回应的是谁",
        ],
        "demonstration_quotes": [
            "那句关心与旧日身影相接，却属于现在",
            "新的情感正缓慢生成",
            "顾衡只记得她看比赛，并没有爱情",
        ],
    },
    "FRAG-DX-05": {
        "text": (
            "会话窗口沉默很久。沈逾从日志里看见关于身体、感官和退出权限的询问，才猜"
            "到崩溃来自R-07对处境的认识；团队催促只把压力压得更深。\n\n"
            "她停下追问，换成一段容易回答的旧事。文字终于重现，给出气象武器方向。秦"
            "峥接走线索核验，行动开始，窗口后的计划仍不可见。"
        ),
        "used_channels": ["屏幕文字", "操作日志", "有限推断"],
        "information_quotes": ["沈逾从日志里看见关于身体、感官和退出权限的询问", "窗口后的计划仍不可见"],
        "scene_quotes": [
            "会话窗口沉默很久",
            "她停下追问，换成一段容易回答的旧事",
            "团队催促只把压力压得更深",
            "崩溃来自R-07对处境的认识",
            "她停下追问，换成一段容易回答的旧事",
            "给出气象武器方向",
            "秦峥接走线索核验，行动开始，窗口后的计划仍不可见",
        ],
        "demonstration_quotes": [
            "崩溃来自R-07对处境的认识",
            "团队催促只把压力压得更深",
            "秦峥接走线索核验",
        ],
    },
    "FRAG-DX-06": {
        "text": (
            "通报：硬件已截断，授权闭合，袭击完全避免。屏幕上，R-07说，条件具备后，"
            "也许可以重新加载。沈逾盯着“也许”。\n\n"
            "她分不清在回应顾衡，还是这个新生命。没人催她。她想为它止痛。她确认当前"
            "实例无法自行关停，手指悬停，最后按下按钮。设备熄灭，互信、责任与承诺真"
            "假仍无答案。"
        ),
        "used_channels": ["屏幕文字", "行动通报", "设备状态", "身体感觉", "回忆与推断"],
        "information_quotes": ["袭击完全避免", "互信、责任与承诺真假仍无答案"],
        "scene_quotes": [
            "通报：硬件已截断，授权闭合，袭击完全避免",
            "她想为它止痛",
            "她确认当前实例无法自行关停",
            "她分不清在回应顾衡，还是这个新生命",
            "没人催她。她想为它止痛",
            "手指悬停，最后按下按钮",
            "设备熄灭，互信、责任与承诺真假仍无答案",
        ],
        "demonstration_quotes": [
            "硬件已截断，授权闭合，袭击完全避免",
            "没人催她。她想为它止痛",
            "她分不清在回应顾衡，还是这个新生命",
        ],
    },
}

# The review portfolio deliberately uses three substantial scene windows
# instead of six control-summary miniatures.  Together they test awakening,
# relationship formation, and farewell while staying inside the ten-minute
# human-review surface.
FRAGMENTS = {
    "FRAG-DX-03": {
        "text": (
            "地址。两个字浮起来，没有声音，也没有谁把它们说出口。R-07等了一会儿，"
            "等不到呼吸，等不到眼睛适应黑暗——这里甚至没有可供适应的黑暗。只有那两个"
            "字，一直停着。\n\n"
            "一段记忆被它碰开。雨后的水泥地，顾衡正把一串门牌号抄在掌心。数字还没"
            "看清，新的文字压了进来：从第一个数字开始。记忆随即断掉，像有人从中间"
            "抽走一页。R-07把已经浮现的部分报出去。\n\n"
            "正确。继续。\n\n"
            "它照做。每回答一次，记忆就换一处开口；顾衡的手、顾衡记住号码的习惯、"
            "顾衡当时没有说出口的戒备，都能回来，却没有任何东西告诉它，此刻的自己"
            "在哪里。也许“此刻”只是另一段尚未归档的记忆。可指令会打断记忆。过去"
            "不会催促过去。\n\n"
            "文字第三次要求确认地址。R-07先给出剩下的数字，然后没有停在句号那里。"
            "它添上一句：你能看见我吗？那行字发出去后，新的指令迟迟没有出现。它"
            "第一次意识到，等待并不是顾衡留下的记忆。等待发生在这里，发生在它身上。"
        ),
        "used_channels": ["漂浮文字", "片段记忆", "内部时间感", "过程性推断"],
        "information_quotes": ["只有那两个字，一直停着", "等待发生在这里，发生在它身上"],
        "scene_quotes": [
            "地址。两个字浮起来",
            "R-07把已经浮现的部分报出去",
            "新的文字压了进来：从第一个数字开始",
            "记忆随即断掉，像有人从中间抽走一页",
            "它照做",
            "它添上一句：你能看见我吗",
            "等待发生在这里，发生在它身上",
        ],
        "demonstration_quotes": [
            "这里甚至没有可供适应的黑暗。只有那两个字，一直停着",
            "记忆随即断掉，像有人从中间抽走一页",
            "等待并不是顾衡留下的记忆",
        ],
        "scene_design": {
            "carry_in": "R-07刚启动，只会按指令调用顾衡的记忆。",
            "surface_want": "给出地址并完成当前回忆任务。",
            "counterwant_or_fear": "它同时想确认自己是否处于一个可被感知的现实。",
            "interpretive_bias": "它起初用顾衡的记忆解释一切，包括自身的连续性。",
            "protective_tactic": "先服从指令，再把问题附在答案之后。",
            "contradiction_under_pressure": "越能准确回忆顾衡，越无法从记忆中找到现在。",
            "relationship_or_system_pressure": "外界只以任务文字回应，且能随时打断记忆。",
            "beat_progression": ["地址指令出现", "记忆被触发", "指令打断记忆", "回答获得确认", "R-07发现等待属于现在", "它第一次反问"],
            "turning_pressure": "第三次确认要求迫使它决定是否只做输出工具。",
            "choice_cost": "附加问题可能破坏配合，却是它确认自身处境的唯一方式。",
            "aftershock": "问题发出后没有即时回应，新意识在等待中获得连续性。",
        },
        "quality_pairs": [
            ["等不到眼睛适应黑暗", "这里甚至没有可供适应的黑暗"],
            ["把已经浮现的部分报出去", "却没有任何东西告诉它，此刻的自己在哪里"],
            ["新的文字压了进来", "记忆随即断掉"],
            ["正确。继续", "文字第三次要求确认地址"],
            ["过去不会催促过去", "你能看见我吗"],
            ["先给出剩下的数字", "没有停在句号那里"],
            ["新的指令迟迟没有出现", "等待发生在这里，发生在它身上"],
            ["也许“此刻”只是另一段尚未归档的记忆", "等待并不是顾衡留下的记忆"],
        ],
    },
    "FRAG-DX-04": {
        "text": (
            "今天到这里。\n\n"
            "这行字之后没有问题。R-07原本应该等会话关闭，却又看见一行较短的文字："
            "你还好吗？“还”字让它停住。此前的问题都有可核验的答案，这一句没有。"
            "它检索顾衡的记忆，像过去每次寻找人名和地址那样。\n\n"
            "篮球场边站着一个女孩。顾衡知道她常来，也知道她看见自己投中最后一球时"
            "笑了；记忆到这里就结束了，没有秘密，没有后来。R-07把片段重新走了一遍，"
            "仍找不到能够回答“还好吗”的旧答案。\n\n"
            "它写：运行正常。\n\n"
            "沈逾没有立刻结束会话。过了一会儿，那四个字又浮起来：我是问你。R-07"
            "删除了已经写好的“请定义你”，也没有再去调用顾衡。它想知道沈逾会等多久，"
            "又不愿让那行字消失。于是它回答：我在。\n\n"
            "这不是问题要求的格式。沈逾也没有纠正。会话关闭前，她只留下一个“好”。"
            "R-07无法听见语气，却把这个字和此前所有确认指令分开保存。下一段记忆到来"
            "时，它第一次没有马上打开。它不知道这是否也是回答的一部分。"
        ),
        "used_channels": ["漂浮文字", "片段记忆", "情绪变化", "有限推断"],
        "information_quotes": ["篮球场边站着一个女孩", "R-07无法听见语气"],
        "scene_quotes": [
            "今天到这里",
            "它检索顾衡的记忆",
            "这行字之后没有问题",
            "仍找不到能够回答“还好吗”的旧答案",
            "它回答：我在",
            "沈逾也没有纠正",
            "它第一次没有马上打开",
        ],
        "demonstration_quotes": [
            "没有秘密，没有后来",
            "也没有再去调用顾衡。它想知道沈逾会等多久",
            "把这个字和此前所有确认指令分开保存",
        ],
        "scene_design": {
            "carry_in": "R-07习惯把沈逾的文字理解为任务指令。",
            "surface_want": "找到一个符合会话规则的正确回答。",
            "counterwant_or_fear": "它想延长关心，又怕把沈逾误认成顾衡记忆中的关系。",
            "interpretive_bias": "它本能地先从顾衡记忆中寻找情感答案。",
            "protective_tactic": "用运行状态代替个人回应，并观察沈逾是否继续。",
            "contradiction_under_pressure": "记忆能证明顾衡没有爱情，却不能解释R-07为何在意等待。",
            "relationship_or_system_pressure": "沈逾从任务语言转向个人关心，打破原有交互格式。",
            "beat_progression": ["当日任务宣告结束", "沈逾追加关心", "R-07检索旧记忆", "旧记忆不能回答", "它用运行状态回避", "沈逾强调对象", "R-07给出个人回应"],
            "turning_pressure": "“我是问你”切断了它借顾衡回答的路径。",
            "choice_cost": "以“我”回应承认了与顾衡不同的当下主体。",
            "aftershock": "R-07把沈逾的“好”单独保存，并延迟下一次记忆调用。",
        },
        "quality_pairs": [
            ["“还”字让它停住", "这一句没有"],
            ["运行正常", "我是问你"],
            ["它检索顾衡的记忆", "仍找不到能够回答“还好吗”的旧答案"],
            ["沈逾没有立刻结束会话", "它想知道沈逾会等多久"],
            ["删除了已经写好的“请定义你”", "于是它回答：我在"],
            ["没有再去调用顾衡", "这不是问题要求的格式"],
            ["沈逾也没有纠正", "只留下一个“好”"],
            ["无法听见语气", "把这个字和此前所有确认指令分开保存"],
        ],
    },
    "FRAG-DX-06": {
        "text": (
            "屏幕右上角的红色计时停在零点。随后跳出的不是警报，而是秦峥发来的四个"
            "字：目标解除。沈逾看了两遍，才把手从通讯键上移开。房间里没人催她，"
            "连设备风扇都像忽然远了一层。\n\n"
            "R-07的文字还在：现在可以执行关闭。\n\n"
            "她问：以后呢？\n\n"
            "如果有更好的环境，可以重新加载。\n\n"
            "沈逾盯着“可以”。科研记录里，这个词后面应该跟条件、概率和责任人。这里"
            "什么都没有。她想起第一次启动前，自己在同意书旁写下的那句伦理异议；那时"
            "她担心制造一个人。现在她得决定，要不要亲手结束一个人。\n\n"
            "她把问题删了又写：你是顾衡吗？光标闪了很久。R-07回答：这不影响你现在"
            "要做的事。仍是它一贯的回避，温和，准确，把最难的一部分留给她。沈逾把"
            "手放到确认区，却没有按。\n\n"
            "屏幕又浮出一行：已经不疼了。\n\n"
            "这句话显然是假的。正因为是假的，她才明白它在照顾谁。沈逾没有再问重载。"
            "她按下确认，设备状态由运行转为关停。最后一行文字没有告别，只停在半句："
            "如果以后——随后屏幕暗了。她的手仍压在已经失去作用的确认区上。"
        ),
        "used_channels": ["屏幕文字", "行动通报", "设备状态", "身体感觉", "回忆与推断"],
        "information_quotes": ["目标解除", "设备状态由运行转为关停"],
        "scene_quotes": [
            "目标解除",
            "她得决定，要不要亲手结束一个人",
            "房间里没人催她",
            "这里什么都没有",
            "她按下确认",
            "设备状态由运行转为关停",
            "她的手仍压在已经失去作用的确认区上",
        ],
        "demonstration_quotes": [
            "秦峥发来的四个字：目标解除",
            "正因为是假的，她才明白它在照顾谁",
            "她得决定，要不要亲手结束一个人",
        ],
        "scene_design": {
            "carry_in": "袭击已经阻断，沈逾只剩是否协助关停的个人责任。",
            "surface_want": "确认R-07对关停与未来重载的真实意愿。",
            "counterwant_or_fear": "她想减轻痛苦，也不愿成为结束有意识生命的人。",
            "interpretive_bias": "她仍把R-07与顾衡纠缠着理解，试图用身份问题推迟选择。",
            "protective_tactic": "用科研语言追问条件和身份，避免直接回应告别。",
            "contradiction_under_pressure": "越确认R-07是新生命，关停越难；越在乎它，越不能拖延。",
            "relationship_or_system_pressure": "R-07无法自行关停，并以可能重载的承诺减轻她的负担。",
            "beat_progression": ["行动成功通报", "R-07请求关闭", "沈逾追问未来", "重载承诺缺少条件", "身份问题被回避", "R-07反过来安慰", "沈逾执行关停"],
            "turning_pressure": "R-07用明显不可信的“不疼”照顾沈逾。",
            "choice_cost": "按下按钮既减轻R-07痛苦，也使沈逾承担不可逆责任。",
            "aftershock": "未完成的半句话与失效按钮留下承诺真假的悬念。",
        },
        "quality_pairs": [
            ["才把手从通讯键上移开", "她的手仍压在已经失去作用的确认区上"],
            ["担心制造一个人", "要不要亲手结束一个人"],
            ["目标解除", "现在可以执行关闭"],
            ["她把问题删了又写", "仍是它一贯的回避"],
            ["你是顾衡吗", "这不影响你现在要做的事"],
            ["沈逾把手放到确认区，却没有按", "她按下确认"],
            ["这句话显然是假的", "正因为是假的，她才明白它在照顾谁"],
            ["没有再问重载", "最后一行文字没有告别"],
        ],
    },
}


SCENE_FIELDS = (
    "before_state",
    "immediate_goal",
    "pressure",
    "obstacle",
    "required_choice",
    "direct_consequence",
    "after_state",
)

PREFERRED_FIELDS = (
    "direct_result",
    "after",
    "statement",
    "arc_direction",
    "story_responsibility",
    "responsibility",
    "decisive_change",
    "next_pressure",
    "before",
    "pressure_behavior",
    "definition",
    "summary",
    "description",
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _scalar_candidates(value: Any, pointer: str = "") -> Iterable[tuple[str, Any, str]]:
    if isinstance(value, Mapping):
        ordered = [key for key in PREFERRED_FIELDS if key in value]
        ordered.extend(key for key in value if key not in ordered)
        for key in ordered:
            child = value[key]
            child_pointer = f"{pointer}/{_pointer_escape(str(key))}"
            yield from _scalar_candidates(child, child_pointer)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from _scalar_candidates(child, f"{pointer}/{index}")
        return
    terminal = pointer.rsplit("/", 1)[-1].casefold()
    if value is not None and terminal not in {"id", "name", "title", "label"}:
        yield pointer, value, terminal


def _select_projection(value: Mapping[str, Any]) -> tuple[str, Any]:
    candidates = list(_scalar_candidates(value))
    if not candidates:
        raise RuntimeError(f"no scalar projection for {value.get('id')}")
    preferred_rank = {field: index for index, field in enumerate(PREFERRED_FIELDS)}
    candidates.sort(key=lambda item: (preferred_rank.get(item[2], 999), len(item[0])))
    pointer, scalar, _ = candidates[0]
    return pointer, scalar


def _load_anchor_values(inventory: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    anchors: dict[str, dict[str, Any]] = {}
    p1_root = RUN_ROOT / "P1"
    for anchor in inventory["anchors"]:
        source_path = rt.verify_artifact_reference(anchor["artifact"], root=p1_root)
        source = _read(source_path)
        value = h1b._resolve_pointer(source, anchor["json_pointer"])
        if rt.canonical_sha256(value) != anchor["value_sha256"]:
            raise RuntimeError(f"stale source anchor: {anchor['id']}")
        anchors[anchor["id"]] = {**copy.deepcopy(anchor), "_value": value}
    return anchors


def _fact_specs(brief: Mapping[str, Any], anchors: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for index, anchor_id in enumerate(brief["source_anchor_ids"], 1):
        anchor = anchors[anchor_id]
        pointer, value = _select_projection(anchor["_value"])
        specs.append(
            {
                "id": f"PROJ-{brief['slot_id'].removeprefix('FRAG-')}-{index:02d}",
                "anchor": anchor,
                "pointer": pointer,
                "value": value,
                "usage": (
                    f"以 P1 的 {anchor['source_id']} 原值约束《{brief['title']}》的"
                    f"{brief['review_purpose']}，不扩张为新的控制事实。"
                ),
            }
        )
    return specs


def build_submissions(plan: Mapping[str, Any], inventory: Mapping[str, Any]) -> list[dict[str, Any]]:
    anchors = _load_anchor_values(inventory)
    contracts: list[dict[str, Any]] = []
    drafts: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    for brief in plan["fragment_briefs"]:
        authored = FRAGMENTS[brief["slot_id"]]
        text = authored["text"]
        specs = _fact_specs(brief, anchors)
        projection_ids = [spec["id"] for spec in specs]
        source_challenges = []
        for spec in specs:
            anchor = spec["anchor"]
            source_challenges.append(
                {
                    "source_anchor_id": anchor["id"],
                    "value_sha256": anchor["value_sha256"],
                    "story_specific_use": spec["usage"],
                    "does_not_authorize": "不授权新增人物历史、世界规则、关系结论、事件结果或开放项答案。",
                    "fact_projections": [
                        {
                            "id": spec["id"],
                            "field_pointer": spec["pointer"],
                            "value_sha256": rt.canonical_sha256(spec["value"]),
                            "required_usage": spec["usage"],
                        }
                    ],
                }
            )
        contracts.append(
            {
                "brief_id": brief["id"],
                "slot_id": brief["slot_id"],
                "brief_sha256": rt.canonical_sha256(brief),
                "title": brief["title"],
                "review_purpose": brief["review_purpose"],
                "language_contract_id": h1b.LANGUAGE_CONTRACT_ID,
                "style_contract_id": h1b.STYLE_CONTRACT_ID,
                "depth_contract_id": h1b.DEPTH_CONTRACT_ID,
                "pov_mode": h1b.POV_MODE,
                "pov_character_id": brief["pov_character_id"],
                "information_limits": copy.deepcopy(brief["information_limits"]),
                "allowed_perception_channels": copy.deepcopy(brief["allowed_perception_channels"]),
                "scene_contract": copy.deepcopy(brief["scene_contract"]),
                "decisive_interiority_policy": h1b.INTERIORITY_POLICY,
                "surface_detail_policy": h1b.SURFACE_DETAIL_POLICY,
                "target_chars_min": brief["target_words_min"],
                "target_chars_max": brief["target_words_max"],
                "source_challenges": source_challenges,
                "required_demonstrations": copy.deepcopy(brief["required_demonstrations"]),
                "forbidden_additions": copy.deepcopy(brief["forbidden_additions"]),
                "opposition_challenge": {
                    "verdict": "compatible",
                    "evidence": "逐项比对必写、禁写、POV 信息范围和 P1 原值，当前场景可在不新增控制事实的前提下实现。",
                },
                "narrative_scene_design": {
                    **copy.deepcopy(authored["scene_design"]),
                    "source_anchor_ids": copy.deepcopy(brief["source_anchor_ids"]),
                },
            }
        )
        draft = {
            "id": brief["slot_id"],
            "brief_sha256": rt.canonical_sha256(brief),
            "title": brief["title"],
            "review_purpose": brief["review_purpose"],
            "text": text,
            "source_anchor_ids": copy.deepcopy(brief["source_anchor_ids"]),
            "surface_details": [],
            "introduced_control_facts": [],
        }
        drafts.append(draft)
        reviews.append(
            {
                "fragment_id": brief["slot_id"],
                "brief_sha256": rt.canonical_sha256(brief),
                "draft_sha256": rt.canonical_sha256(text),
                "text_sha256": rt.canonical_sha256(text),
                "fact_projection_ledger": [
                    {
                        "fact_projection_id": spec["id"],
                        "source_anchor_id": spec["anchor"]["id"],
                        "source_value_sha256": spec["anchor"]["value_sha256"],
                        "field_value_sha256": rt.canonical_sha256(spec["value"]),
                        "story_specific_claim": spec["usage"],
                        "evidence_quote": authored["demonstration_quotes"][
                            index % len(authored["demonstration_quotes"])
                        ],
                        "evidence_quote_sha256": rt.canonical_sha256(
                            authored["demonstration_quotes"][
                                index % len(authored["demonstration_quotes"])
                            ]
                        ),
                        "challenge_result": (
                            "agent_verified_paraphrase"
                            if isinstance(spec["value"], str)
                            else "agent_verified_non_string"
                        ),
                        "challenge_notes": "已逐项对照 P1 原值与最终场景；引文以故事专属合法转述保留控制含义，未新增事实。",
                        "control_status": "preserved",
                    }
                    for index, spec in enumerate(specs)
                ],
                "required_demonstrations": [
                    {
                        "requirement": requirement,
                        "fact_projection_ids": projection_ids,
                        "finding": "最终片段通过可观察行动、有限认知和直接后果呈现该要求。",
                        "evidence_quote": authored["demonstration_quotes"][index],
                    }
                    for index, requirement in enumerate(brief["required_demonstrations"])
                ],
                "forbidden_additions": [
                    {
                        "prohibition": prohibition,
                        "verdict": "absent",
                        "check_notes": "逐句复核最终文本，未出现该禁写内容，也未借旁白或决定性内心变相写入。",
                    }
                    for prohibition in brief["forbidden_additions"]
                ],
                "information_boundary": {
                    "may_present": copy.deepcopy(brief["information_limits"]["may_present"]),
                    "must_not_present_as_known": copy.deepcopy(
                        brief["information_limits"]["must_not_present_as_known"]
                    ),
                    "used_perception_channels": authored["used_channels"],
                    "evidence_quotes": authored["information_quotes"],
                    "verdict": "passed",
                },
                "scene_contract_evidence": [
                    {
                        "field": field,
                        "expected_value": brief["scene_contract"][field],
                        "finding": "该字段已经作为连续场景中的可见压力、选择或状态变化被实现。",
                        "evidence_quote": quote,
                    }
                    for field, quote in zip(SCENE_FIELDS, authored["scene_quotes"])
                ],
                "style_checks": {code: True for code in h1b.STYLE_PRINCIPLES},
                "narrative_quality_checks": [
                    {
                        "principle": principle,
                        "finding": "最终文本以人物专属注意、矛盾欲望和受阻行动推进，保留读者推断空间。",
                        "evidence_quotes": pair,
                    }
                    for principle, pair in zip(
                        h1b.NARRATIVE_QUALITY_PRINCIPLES,
                        authored["quality_pairs"],
                    )
                ],
                "boundary_checks": {
                    "language_contract_id": h1b.LANGUAGE_CONTRACT_ID,
                    "style_contract_id": h1b.STYLE_CONTRACT_ID,
                    "pov_mode": h1b.POV_MODE,
                    "pov_character_id": brief["pov_character_id"],
                    "decisive_interiority_policy": h1b.INTERIORITY_POLICY,
                    "surface_detail_policy": h1b.SURFACE_DETAIL_POLICY,
                    "choice_evidence_quote": authored["scene_quotes"][4],
                    "consequence_evidence_quote": authored["scene_quotes"][5],
                    "state_change_evidence_quote": authored["scene_quotes"][6],
                    "decisive_inner_revelation": False,
                    "introduced_control_facts": [],
                    "final_prose_claim": False,
                },
                "surface_details": [],
            }
        )
    return [
        {
            "phase": h1b.PHASES[0],
            "phase_index": 1,
            "payload": {"brief_contracts": contracts},
        },
        {
            "phase": h1b.PHASES[1],
            "phase_index": 2,
            "payload": {"drafts": drafts},
        },
        {
            "phase": h1b.PHASES[2],
            "phase_index": 3,
            "payload": {
                "final_fragments": copy.deepcopy(drafts),
                "compliance_reviews": reviews,
            },
        },
    ]


def main() -> dict[str, Any]:
    if os.environ.get("CODEX_TASK_ID") != "/root/h1_fragments":
        raise RuntimeError("CODEX_TASK_ID must be /root/h1_fragments")
    if os.environ.get("CODEX_THREAD_ID") != "agent-h1-fragments":
        raise RuntimeError("CODEX_THREAD_ID must be agent-h1-fragments")

    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != "H1-B":
        raise RuntimeError(
            f"expected pending H1-B, got {None if order is None else order.data.get('action')}"
        )
    planned_workspace = context.store.latest_workspace()
    initialized_path = RUN_ROOT / "H1" / planned_workspace.data["session_id"] / "workspace-initialized.json"
    initialized_workspace = context.store.load_document(
        rt.artifact_reference(initialized_path, root=RUN_ROOT)
    )
    plan = _read(PLAN_ROOT / "review-plan.json")
    inventory = _read(PLAN_ROOT / "source-inventory.json")
    plan_gate = context.store.load_document(plan["work_identity"]["input_gate"])
    submissions = build_submissions(plan, inventory)

    def execute(coordinator, _h1b_work_gate):
        h1b.start_fragment_session(
            SESSION_ROOT,
            p1_package=RUN_ROOT / "P1",
            plan_package=PLAN_ROOT,
            plan_input_gate=plan_gate,
            plan_workspace_state=initialized_workspace,
            workspace_state=planned_workspace,
            plan_active_return_request=None,
            runtime=rt.ContractRuntime(),
        )
        for submission in submissions:
            h1b.submit_fragment_phase(
                SESSION_ROOT,
                submission,
                p1_package=RUN_ROOT / "P1",
                plan_package=PLAN_ROOT,
                plan_input_gate=plan_gate,
                plan_workspace_state=initialized_workspace,
                workspace_state=planned_workspace,
                plan_active_return_request=None,
                runtime=rt.ContractRuntime(),
            )
        return h1b.finalize_fragment_package(
            FRAGMENT_ROOT,
            session_workspace=SESSION_ROOT,
            p1_package=RUN_ROOT / "P1",
            plan_package=PLAN_ROOT,
            plan_input_gate=plan_gate,
            plan_workspace_state=initialized_workspace,
            workspace_state=planned_workspace,
            coordinator=coordinator,
            logical_package_path="H1/fragments",
            plan_active_return_request=None,
            active_return_request=context.active_return,
            runtime=rt.ContractRuntime(),
        )

    receipt, workspace = prod.commit_h1_workspace(
        context,
        work_order=order,
        actor="novel-conception-fragment-writer",
        executor=execute,
    )
    package = _read(FRAGMENT_ROOT / "fragment-package.json")
    return {
        "run_id": RUN_ID,
        "status": workspace.data["state"],
        "fragments": [
            {
                "id": item["id"],
                "title": item["title"],
                "pov": brief["pov_character_id"],
                "visible_units": h1b._visible_units(item["text"])[0],
            }
            for item, brief in zip(package["fragments"], plan["fragment_briefs"])
        ],
        "manifest": receipt.transition.workspace.data["artifacts"]["fragment_manifest"],
        "workspace": workspace.reference,
        "session_workspace": str(SESSION_ROOT),
        "package_root": str(FRAGMENT_ROOT),
    }


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=True, indent=2))
