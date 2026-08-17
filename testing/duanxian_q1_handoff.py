from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ID = os.environ["DUANXIAN_CONCEPTION_RUN_ID"]
RUN_ROOT = ROOT / "projects" / "duanxian" / "conception-runs" / RUN_ID
Q1_CONTROLLER = RUN_ROOT / "workspaces" / "Q1-controller-01"
Q1_HANDOFF = RUN_ROOT / "workspaces" / "Q1-handoff-01"


def load_q1_runtime():
    path = ROOT / "skills" / "novel-conception-reviewer" / "scripts" / "run_v2.py"
    spec = importlib.util.spec_from_file_location("duanxian_q1_handoff_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Q1 runtime: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def start() -> dict[str, object]:
    runtime = load_q1_runtime()
    session = runtime.start_handoff_review(
        Q1_CONTROLLER,
        Q1_HANDOFF,
        baseline_package=RUN_ROOT / "B0",
        storyline_package=RUN_ROOT / "S1",
        world_package=RUN_ROOT / "W1",
        environment_package=RUN_ROOT / "E1",
        event_package=RUN_ROOT / "T1",
        character_package=RUN_ROOT / "C1",
    )
    return {
        "status": "handoff_running",
        "workspace": str(Q1_HANDOFF),
        "session_id": session["session_id"],
        "allowlist": session["allowlist"],
    }


def payload() -> dict[str, object]:
    canonical_names = {
        "B0": "author-control-baseline.json",
        "S1": "storyline-architecture.json",
        "W1": "world-model.json",
        "E1": "environment-system.json",
        "T1": "event-timeline.json",
        "C1": "character-system.json",
    }

    def canonical_sha256(value: object) -> str:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def find_object(value: object, identifier: str) -> dict[str, object] | None:
        if isinstance(value, dict):
            if value.get("id") == identifier:
                return value
            for child in value.values():
                found = find_object(child, identifier)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = find_object(child, identifier)
                if found is not None:
                    return found
        return None

    def pointer(value: object, path: str) -> object:
        current = value
        for token in path.split("/")[1:]:
            token = token.replace("~1", "/").replace("~0", "~")
            if isinstance(current, dict):
                current = current[token]
            elif isinstance(current, list):
                current = current[int(token)]
            else:
                raise KeyError(path)
        return current

    def object_kind(stage: str, identifier: str) -> str:
        prefixes = {
            "S1": (("SLD-", "storyline-demand"), ("SLC-", "storyline-connection"), ("SL-", "storyline")),
            "W1": (("WR-", "world-requirement"), ("WF-", "world-fact"), ("WS-", "world-system")),
            "E1": (("END-", "environment-demand"), ("ENV-", "environment"), ("ZONE-", "environment-zone")),
            "T1": (("EVD-", "event-demand"), ("EV-", "event")),
            "C1": (("CHD-", "character-demand"), ("SLOT-", "character-slot"), ("CHR-", "character"), ("REL-", "relationship"), ("DEV-", "development-freedom")),
        }
        if stage == "B0":
            return "author-control"
        for prefix, kind in prefixes[stage]:
            if identifier.startswith(prefix):
                return kind
        return "governance"

    models = {
        stage: json.loads(
            (Q1_HANDOFF / "inputs" / stage / name).read_text(encoding="utf-8")
        )
        for stage, name in canonical_names.items()
    }

    def evidence_object(stage: str, identifier: str, paths: list[str]) -> dict[str, object]:
        value = find_object(models[stage], identifier)
        if value is None:
            raise KeyError(f"{stage}:{identifier}")
        return {
            "id": identifier,
            "stage": stage,
            "kind": object_kind(stage, identifier),
            "value_sha256": canonical_sha256(value),
            "projections": [
                {
                    "path": path,
                    "value_sha256": canonical_sha256(pointer(value, path)),
                }
                for path in paths
            ],
        }

    specifications = [
        {
            "id": "CHK-HANDOFF-STORY-SUBJECT",
            "scope": "story_subject",
            "checked_contract": "独立开发者只凭冻结 canonical 包能够复述小说主体、核心困境与闭环。",
            "conclusion": "主体可被无歧义复述：R-07 的目标是“让继承顾衡记忆的新生命形成自己的价值观、阻止伤害并自主离开。”；它从“R-07 尚未启动，顾衡记忆只是无法直接提取的数据。”出发，在无感官、无身体、无自主行动和退出能力的压力下形成独立价值，终局是袭击被阻止、沈逾关停当前实例，而未来重载仍开放。",
            "objects": [
                evidence_object("S1", "SL-R07-MAIN", ["/goal", "/start_state", "/pressure", "/end_state"]),
            ],
            "predicate": "story-subject",
            "subject_id": "SL-R07-MAIN",
            "target_id": None,
            "operator": "reconstruct-subject",
        },
        {
            "id": "CHK-HANDOFF-STORYLINE-TRACE",
            "scope": "storyline_trace",
            "checked_contract": "独立开发者能够从故事线状态追到按时间排序的实现事件与终态。",
            "conclusion": "SL-R07-MAIN 可从“R-07 尚未启动，顾衡记忆只是无法直接提取的数据。”沿 SEQ-R07-MAIN 的 EV-R07-MAIN-01 至 EV-R07-MAIN-06 顺序追踪：启动与认识处境、形成独立选择、争取沈逾协助，最终到达“袭击被阻止，沈逾按下按钮，当前 R-07 实例终止且未来是否重载保持开放。”，完整闭合 S1 的起止状态。",
            "objects": [
                evidence_object("S1", "SL-R07-MAIN", ["/start_state", "/state_changes", "/end_state"]),
                evidence_object("T1", "SEQ-R07-MAIN", ["/storyline_id", "/entry_state", "/event_ids", "/exit_state"]),
            ],
            "predicate": "storyline-event-trace",
            "subject_id": "SEQ-R07-MAIN",
            "target_id": "SL-R07-MAIN",
            "operator": "trace-development",
        },
        {
            "id": "CHK-HANDOFF-EVENT-CONDITIONS",
            "scope": "event_conditions",
            "checked_contract": "独立开发者能够定位事件的世界规则、场所、前序状态、准入与直接结果。",
            "conclusion": "EV-R07-MAIN-06 的条件可定位：它发生在 ENV-R07-CORE-LAB；必须承接 EV-R07-MAIN-05，实验环境保持隔离运行且经授权可用，WF/WS-R07-LIFECYCLE 仍有效，并遵守“无视觉、听觉、肢体与现实感知”“不能自我关停”的生命周期限制。事件落实的结果是“袭击被阻止后，沈逾执行授权操作，当前R-07实例及启动后的连续经验不可逆终止。”，不是普通休眠或已有副本续存。",
            "objects": [
                evidence_object("T1", "EV-R07-MAIN-06", ["/environment_id", "/predecessor_event_ids", "/preconditions", "/before_state", "/direct_result", "/complication"]),
                evidence_object("E1", "ENV-R07-CORE-LAB", ["/scope", "/access_rules", "/allowed_actions", "/blockers", "/hazards"]),
                evidence_object("W1", "WS-R07-LIFECYCLE", ["/limits", "/authorities", "/state_changes"]),
            ],
            "predicate": "event-condition",
            "subject_id": "EV-R07-MAIN-06",
            "target_id": "ENV-R07-CORE-LAB",
            "operator": "locate-preconditions",
        },
        {
            "id": "CHK-HANDOFF-CHARACTER-CHOICES",
            "scope": "character_choices",
            "checked_contract": "独立开发者能够用人物动机、权限、信息、事件位置与代价解释核心选择。",
            "conclusion": "沈逾在 EV-R07-MAIN-06 的选择可解释：她从把 R-07 当作有生命的机器走向承认其新主体性，价值上拒绝用制度模糊逃避责任；“是否相信 R-07 的承诺并按下关停按钮，不能由导师、项目领导或机器替代。” AGY-C1-012 将 EV-R07-MAIN-06 明确列入她必须亲自承担的事件选择，而该事件的不可逆终止与身份、伦理、关系后果构成真实代价。",
            "objects": [
                evidence_object("C1", "AGY-C1-012", ["/character_id", "/event_ids", "/available_choices", "/chosen_action", "/cost"]),
                evidence_object("C1", "CHR-SHEN-YU", ["/arc_direction", "/values", "/non_delegable_choices", "/pressure_behavior"]),
                evidence_object("T1", "EV-R07-MAIN-06", ["/initiator_slot_id", "/before_state", "/direct_result", "/complication", "/next_pressure"]),
            ],
            "predicate": "character-choice",
            "subject_id": "AGY-C1-012",
            "target_id": "EV-R07-MAIN-06",
            "operator": "explain-choice",
        },
        {
            "id": "CHK-HANDOFF-DEVELOPMENT-FREEDOMS",
            "scope": "development_freedoms",
            "checked_contract": "独立开发者能够区分终端实现自由与不可改变的权威人物、事件和关系控制。",
            "conclusion": "DEV-C1-014 给沈逾的开发自由是“在不改变角色控制信息的前提下开发具体场景表达。” 开发者可变化动作、对白节奏、感官细节、局部社交习惯和显性程度；不得改变目标、价值、盲点、硬边界、权限、信息限制、不可委托选择、关系变化或冻结事件结果，并须让行为可追溯到 profile、事件角色和关系杠杆。",
            "objects": [
                evidence_object("C1", "DEV-C1-014", ["/scope", "/source_ids", "/allowed_variations", "/forbidden_changes", "/acceptance_checks"]),
            ],
            "predicate": "development-boundary",
            "subject_id": "DEV-C1-014",
            "target_id": None,
            "operator": "locate-freedom",
        },
    ]

    checks: list[dict[str, object]] = []
    bindings: list[dict[str, object]] = []
    for specification in specifications:
        evidence_ids = [item["id"] for item in specification["objects"]]
        assertion = {
            "predicate": specification["predicate"],
            "subject_id": specification["subject_id"],
            "target_id": specification["target_id"],
            "challenge_operator": specification["operator"],
            "result": "pass",
        }
        unsigned_binding = {
            "check_id": specification["id"],
            "scope": specification["scope"],
            "evidence_objects": specification["objects"],
            "assertion": assertion,
        }
        assertion_sha256 = canonical_sha256(unsigned_binding)
        bindings.append({**unsigned_binding, "assertion_sha256": assertion_sha256})
        checks.append(
            {
                "id": specification["id"],
                "scope": specification["scope"],
                "checked_contract": specification["checked_contract"],
                "method": f"story-assertion:{assertion_sha256}",
                "evidence_ids": evidence_ids,
                "conclusion": specification["conclusion"],
                "result": "pass",
            }
        )

    all_evidence_ids: list[str] = []
    for check in checks:
        for identifier in check["evidence_ids"]:
            if identifier not in all_evidence_ids:
                all_evidence_ids.append(identifier)

    read_set = [
        f"inputs/{stage}/{name}"
        for stage, name in canonical_names.items()
        for name in (name, "package-manifest.json")
    ]
    return {
        "development_usability_test": {
            "id": "HANDOFF-DUANXIAN-DEVELOPMENT-USABILITY",
            "tested_tasks": [
                "story_subject",
                "storyline_trace",
                "event_conditions",
                "character_choices",
                "development_freedoms",
            ],
            "evidence_ids": all_evidence_ids,
            "conclusion": "冻结的《断线》B0/S1-W1-E1-T1-C1 canonical 包足以让独立开发者复述 R-07 主体故事，追踪主线至关停，定位关停条件，解释沈逾承担按钮选择的原因与代价，并按 DEV-C1-014 保留场景表达自由而不改写权威控制。",
            "result": "pass",
        },
        "read_set": read_set,
        "responses": {
            "story_subject": "近未来 C、M 两国危机中，顾衡牺牲后其记忆被加载进实验性数字生命 R-07。R-07 不是顾衡复活，而是在仅有意识中文字、无感官无身体且不能自行退出的处境中，经由沈逾的现实关心形成新意识与价值；它帮助阻止气象袭击并自主选择结束当前存在，沈逾承担关停，重载与身份连续性保持开放。",
            "storyline_trace": "SL-R07-MAIN 从未启动状态进入 R-07 启动与记忆触发，经处境认识和崩溃、温和交流恢复、独立减害决定、争取沈逾协助，按 SEQ-R07-MAIN 的六个事件到达袭击被阻止与当前实例不可逆终止。",
            "event_conditions": "EV-R07-MAIN-06 位于 ENV-R07-CORE-LAB，承接 EV-R07-MAIN-05；核心实验环境须隔离且授权可用，R-07 生命周期规则须维持无现实感知、不能自关停和无可证实活动备份，袭击先由现实团队阻止后才进入授权告别操作。",
            "character_choices": "沈逾按下按钮不是替 R-07 决定价值，而是回应 R-07 已自主形成的离开诉求；她具有执行经授权关停的现实位置，却无法把是否相信承诺、是否亲自结束其痛苦的责任委托给导师、机构或机器，并承担不可逆生命、伦理、关系和秘密后果。",
            "development_freedoms": "DEV-C1-014 允许开发者调整沈逾场景中的动作、对白节奏、感官细节、局部社交习惯与显性程度；目标、价值、盲点、权限、信息限制、不可委托选择、关系变化和冻结事件结果不可变，新增表达必须可追溯到 profile、事件角色与关系杠杆。",
        },
        "handoff_checks": checks,
        "assertion_bindings": bindings,
    }


def seal() -> dict[str, object]:
    runtime = load_q1_runtime()
    reference = runtime.seal_handoff_review(
        Q1_CONTROLLER,
        Q1_HANDOFF,
        payload=payload(),
    )
    return {"status": "handoff_sealed", "evidence": reference}


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "start"
    result = start() if action == "start" else seal() if action == "seal" else None
    if result is None:
        raise SystemExit(f"unknown action: {action}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
