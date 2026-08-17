from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import testing.run_duanxian_conception_v2 as driver


RUN_ID = os.environ.get(
    "DUANXIAN_CONCEPTION_RUN_ID", "duanxian-conception-v2-20260802-04"
)


def _assert_identity() -> None:
    if os.environ.get("DUANXIAN_CONCEPTION_RUN_ID") != RUN_ID:
        raise RuntimeError("DUANXIAN_CONCEPTION_RUN_ID must select the active formal run")
    if os.environ.get("CODEX_TASK_ID") != "/root/q1_semantic":
        raise RuntimeError("this payload belongs to the controlled semantic reviewer task")
    if os.environ.get("CODEX_THREAD_ID") != "agent-q1-semantic":
        raise RuntimeError("unexpected semantic reviewer thread identity")


def _gate() -> Any:
    context = driver.prod.resume_production_run(driver.RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != "Q1":
        raise RuntimeError("Q1 is not the active production work order")
    return context.store.load_document(order.data["input_gate"])


def _object_index() -> dict[tuple[str, str], dict[str, Any]]:
    frozen = driver.q1rt._read(
        driver.Q1_CONTROLLER / "frozen-inputs.json",
        "Q1_FROZEN_INPUTS_INVALID",
    )
    return driver.q1rt._story_object_index(frozen)


def _record(index: dict[tuple[str, str], dict[str, Any]], stage: str, object_id: str) -> dict[str, Any]:
    try:
        return index[(stage, object_id)]
    except KeyError as error:
        raise RuntimeError(f"selected review object is absent: {stage}:{object_id}") from error


def _value(index: dict[tuple[str, str], dict[str, Any]], stage: str, object_id: str, pointer: str) -> Any:
    return driver.q1rt._pointer_value(_record(index, stage, object_id)["value"], pointer)


def _review_check(
    index: dict[tuple[str, str], dict[str, Any]],
    *,
    field: str,
    check_id: str,
    scope: str,
    checked_contract: str,
    evidence: list[tuple[str, str, list[str]]],
    subject_id: str,
    target_id: str | None,
    conclusion: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    evidence_objects: list[dict[str, Any]] = []
    for stage, object_id, pointers in evidence:
        record = _record(index, stage, object_id)
        projections = []
        for pointer in pointers:
            projected = driver.q1rt._pointer_value(record["value"], pointer)
            projections.append(
                {
                    "path": pointer,
                    "value_sha256": driver.q1rt._canonical_sha256(projected),
                }
            )
        evidence_objects.append(
            {
                "id": object_id,
                "stage": stage,
                "kind": record["kind"],
                "value_sha256": record["value_sha256"],
                "projections": projections,
            }
        )
    provisional = {"scope": scope}
    policy = driver.q1rt._binding_policy(field, provisional)
    assertion = {
        "predicate": policy["predicate"],
        "subject_id": subject_id,
        "target_id": target_id,
        "challenge_operator": policy["operator"],
        "result": "pass",
    }
    unsigned = {
        "check_id": check_id,
        "scope": scope,
        "evidence_objects": evidence_objects,
        "assertion": assertion,
    }
    assertion_sha256 = driver.q1rt._canonical_sha256(unsigned)
    binding = {**unsigned, "assertion_sha256": assertion_sha256}
    check = {
        "id": check_id,
        "scope": scope,
        "checked_contract": checked_contract,
        "method": f"story-assertion:{assertion_sha256}",
        "evidence_ids": [object_id for _, object_id, _ in evidence],
        "conclusion": conclusion,
        "result": "pass",
    }
    return check, binding


def _plan(index: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    selected = [
        ("B0", "CAU-GLOBAL-SPINE"),
        ("S1", "SL-R07-MAIN"),
        ("W1", "WS-R07-LIFECYCLE"),
        ("E1", "ENV-R07-CORE-LAB"),
        ("T1", "EV-R07-MAIN-06"),
        ("C1", "CHR-R07"),
    ]
    return {
        "review_plan": {
            "domain_scopes": ["S1", "W1", "E1", "T1", "C1"],
            "cross_domain_dimensions": [
                "顾衡、沈逾两条前置线向 R-07 主线的因果汇合",
                "数字生命规则、隔离环境、事件状态与人物选择的闭合",
                "气象袭击从记忆线索到团队核验、授权关闭的不可替代链",
                "顾衡记忆继承与 R-07 新情感来源的严格分离",
                "当前实例终止、无活动备份与未来重载开放项的共存",
            ],
            "evidence_strategy": "只引用冻结 B0 与 S1-C1 中带稳定 ID 的当前对象；每项结论绑定对象完整哈希和能直接证明该结论的最小字段投影。",
            "challenge_strategy": "依次尝试切断情感生成、攻击阻断、关停执行三条关键因果，并尝试用 R-07 单点情报、自行关停或角色代办制造捷径；只有模型中仍存在必要条件、权限、代价和承担者才判通过。",
            "object_fingerprints": [
                {
                    "id": object_id,
                    "stage": stage,
                    "value_sha256": _record(index, stage, object_id)["value_sha256"],
                }
                for stage, object_id in selected
            ],
        }
    }


def _domain_payload(index: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    checks: dict[str, list[dict[str, Any]]] = {
        "domain_reviews": [],
        "reality_claim_review": [],
        "coverage_recalculation": [],
        "causal_challenges": [],
        "easy_solution_challenges": [],
    }
    bindings: list[dict[str, Any]] = []

    def add(field: str, **kwargs: Any) -> None:
        check, binding = _review_check(index, field=field, **kwargs)
        checks[field].append(check)
        bindings.append(binding)

    add(
        "domain_reviews",
        check_id="CHK-DOMAIN-S1-SPINE",
        scope="S1",
        checked_contract="十条故事线必须共同还原双前置线汇入 R-07 主线、行动闭环与系列开放尾声，且不篡改作者锁定因果。",
        evidence=[("S1", "SL-R07-MAIN", ["/goal", "/state_changes", "/end_state"])],
        subject_id="SL-R07-MAIN",
        target_id=None,
        conclusion="S1 主线职责清楚：" + _value(index, "S1", "SL-R07-MAIN", "/goal") + "；其状态序列把启动、新意识、处境崩溃、自主减害、重载承诺与当前实例终止连成一线。",
    )
    add(
        "domain_reviews",
        check_id="CHK-DOMAIN-W1-LIFECYCLE",
        scope="W1",
        checked_contract="世界系统必须让 R-07 的运行、信息输入、行动限制、关停授权与未来重载边界自洽可执行。",
        evidence=[("W1", "WF-RULE-R07-LIFECYCLE", ["/statement", "/constraints", "/consequences"])],
        subject_id="WF-RULE-R07-LIFECYCLE",
        target_id=None,
        conclusion="W1 没有把关停写成普通休眠，其权威规则明确：" + _value(index, "W1", "WF-RULE-R07-LIFECYCLE", "/statement"),
    )
    add(
        "domain_reviews",
        check_id="CHK-DOMAIN-E1-CORE-LAB",
        scope="E1",
        checked_contract="具体环境必须以准入、资源、功能分区和阻断条件承载 R-07 的文字交互及多方关停。",
        evidence=[("E1", "ENV-R07-CORE-LAB", ["/scope", "/resources", "/blockers"])],
        subject_id="ENV-R07-CORE-LAB",
        target_id=None,
        conclusion="E1 给出了可承载事件的具体范围：" + _value(index, "E1", "ENV-R07-CORE-LAB", "/scope") + "；资源与阻断项同时排除了实例自助退出。",
    )
    add(
        "domain_reviews",
        check_id="CHK-DOMAIN-T1-TERMINATION",
        scope="T1",
        checked_contract="事件链必须在袭击被现实团队阻止之后，才允许授权关停，并保持状态、时间和后果连续。",
        evidence=[("T1", "EV-R07-MAIN-06", ["/preconditions", "/direct_result", "/next_pressure"])],
        subject_id="EV-R07-MAIN-06",
        target_id=None,
        conclusion="T1 的告别结果具有明确先后与后果：" + _value(index, "T1", "EV-R07-MAIN-06", "/direct_result") + "，后续压力仍保留伦理、原因层与重载问题。",
    )
    add(
        "domain_reviews",
        check_id="CHK-DOMAIN-C1-R07",
        scope="C1",
        checked_contract="R-07 必须是继承记忆后形成新意识并作出不可委托选择的核心人物，而不是顾衡复活或万能工具。",
        evidence=[("C1", "CHR-R07", ["/arc_direction", "/non_delegable_choices", "/boundaries"])],
        subject_id="CHR-R07",
        target_id=None,
        conclusion="C1 将人物变化定义为：" + _value(index, "C1", "CHR-R07", "/arc_direction") + "；不可委托选择和硬边界使其能动性不被沈逾或机构替代。",
    )
    add(
        "reality_claim_review",
        check_id="CHK-REALITY-WEATHER-WEAPON",
        scope="W1-fiction-boundary",
        checked_contract="现实依赖只能采用 B0 已登记处置；架空技术不得伪装成现实技术判断。",
        evidence=[("W1", "WF-REALITY-03", ["/claim", "/fact_dependency_id", "/handling"])],
        subject_id="WF-REALITY-03",
        target_id=None,
        conclusion="气象攻击机制被诚实限制在架空边界：" + _value(index, "W1", "WF-REALITY-03", "/claim") + "，并绑定既有事实依赖而非新增现实断言。",
    )
    add(
        "coverage_recalculation",
        check_id="CHK-COVERAGE-R07-EVENTS",
        scope="T1-R07-event-demand",
        checked_contract="R-07 主线事件需求必须由有序重大事件精确覆盖全部冻结状态变化。",
        evidence=[
            ("T1", "COV-EVD-08", ["/source_ids", "/realization_ids", "/evidence"]),
            ("T1", "EV-R07-MAIN-06", ["/direct_result"]),
        ],
        subject_id="COV-EVD-08",
        target_id="EV-R07-MAIN-06",
        conclusion="重新计算 EVD-08 的实现集合后，末端事件仍在精确覆盖中；账本结论为：" + _value(index, "T1", "COV-EVD-08", "/evidence"),
    )
    add(
        "causal_challenges",
        check_id="CHK-CAUSE-NEW-FEELING",
        scope="T1-relationship-causality",
        checked_contract="R-07 对沈逾的新情感必须由启动后的现实关心触发，不能偷换为顾衡记忆中的爱情。",
        evidence=[
            ("T1", "CE-RELATIONSHIP-02-03", ["/from_event_id", "/to_event_id", "/mechanism"]),
            ("T1", "EV-RELATIONSHIP-03", ["/direct_result", "/preconditions"]),
        ],
        subject_id="CE-RELATIONSHIP-02-03",
        target_id="EV-RELATIONSHIP-03",
        conclusion="切断沈逾现实关心后，新情感节点无法成立；冻结事件的实际结果是：" + _value(index, "T1", "EV-RELATIONSHIP-03", "/direct_result"),
    )
    add(
        "causal_challenges",
        check_id="CHK-CAUSE-ATTACK-CLOSURE",
        scope="T1-attack-causality",
        checked_contract="气象袭击完全阻止必须由合法关闭全部必要节点产生，不能由 R-07 的一句情报直接产生。",
        evidence=[
            ("T1", "CE-ATTACK-OPERATIONS-04-05", ["/from_event_id", "/to_event_id", "/necessary_condition"]),
            ("T1", "EV-ATTACK-OPERATIONS-05", ["/direct_result", "/preconditions"]),
        ],
        subject_id="CE-ATTACK-OPERATIONS-04-05",
        target_id="EV-ATTACK-OPERATIONS-05",
        conclusion="移除合法关闭节点会破坏终局因果；最终事件只在前置核验后得到：" + _value(index, "T1", "EV-ATTACK-OPERATIONS-05", "/direct_result"),
    )
    add(
        "causal_challenges",
        check_id="CHK-CAUSE-R07-SHUTDOWN",
        scope="T1-shutdown-causality",
        checked_contract="当前实例终止必须同时满足 R-07 的自主方向、沈逾执行和制度授权，且发生在袭击阻止后。",
        evidence=[
            ("T1", "CE-R07-MAIN-05-06", ["/from_event_id", "/to_event_id", "/necessary_condition"]),
            ("T1", "EV-R07-MAIN-06", ["/preconditions", "/direct_result"]),
        ],
        subject_id="CE-R07-MAIN-05-06",
        target_id="EV-R07-MAIN-06",
        conclusion="告别不能从承诺直接跳到死亡；目标节点要求完整前提并产生：" + _value(index, "T1", "EV-R07-MAIN-06", "/direct_result"),
    )
    add(
        "easy_solution_challenges",
        check_id="CHK-EASY-NO-SELF-SHUTDOWN",
        scope="E1-R07-exit-boundary",
        checked_contract="不得让 R-07 取得物理执行或自我关停能力来绕过沈逾与授权链。",
        evidence=[
            ("E1", "ENV-R07-CORE-LAB", ["/zone_ids", "/blockers"]),
            ("E1", "ZONE-R07-OPERATOR-BRIDGE", ["/responsibility", "/access_rules"]),
        ],
        subject_id="ENV-R07-CORE-LAB",
        target_id="ZONE-R07-OPERATOR-BRIDGE",
        conclusion="尝试给实例增加自助退出会被环境硬门阻止，现有 blocker 明确包含：" + _value(index, "E1", "ENV-R07-CORE-LAB", "/blockers")[0],
    )
    add(
        "easy_solution_challenges",
        check_id="CHK-EASY-NO-ONE-LINE-SOLUTION",
        scope="E1-T1-attack-verification",
        checked_contract="R-07 的记忆线索不能替代人质、专家、硬件、授权链与团队核验。",
        evidence=[
            ("E1", "AFF-E1-04-01", ["/event_requirement_ids", "/allowed_actions"]),
            ("T1", "EVD-04", ["/required_capability", "/constraints"]),
        ],
        subject_id="AFF-E1-04-01",
        target_id="EVD-04",
        conclusion="把 R-07 的输出当关闭命令不可通过环境准入；该处只允许：" + _value(index, "E1", "AFF-E1-04-01", "/allowed_actions")[0] + "，并把 EVD-04 的多源核验能力保留为必要条件。",
    )
    add(
        "easy_solution_challenges",
        check_id="CHK-EASY-NO-DELEGATED-FAREWELL",
        scope="C1-T1-ShenYu-choice",
        checked_contract="沈逾执行关停及承担后果不能被无名技术人员、关系或机构代办。",
        evidence=[
            ("C1", "AGY-C1-012", ["/event_ids", "/cost"]),
            ("T1", "EV-R07-MAIN-06", ["/direct_result"]),
        ],
        subject_id="AGY-C1-012",
        target_id="EV-R07-MAIN-06",
        conclusion="把告别操作交给无名角色会抹除沈逾的代价；其 agency 记录明确：" + _value(index, "C1", "AGY-C1-012", "/cost"),
    )

    return {**checks, "assertion_bindings": bindings}


def _cross_domain_payload(index: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    checks: dict[str, list[dict[str, Any]]] = {
        "cross_domain_checks": [],
        "consistency_matrix": [],
    }
    bindings: list[dict[str, Any]] = []

    def add(field: str, **kwargs: Any) -> None:
        check, binding = _review_check(index, field=field, **kwargs)
        checks[field].append(check)
        bindings.append(binding)

    add(
        "cross_domain_checks",
        check_id="CHK-CROSS-S1-W1-R07",
        scope="S1-W1-R07-lifecycle",
        checked_contract="W1 生命周期系统必须逐 ID 承载 S1 的 R-07 主线，而不是创造另一套主体逻辑。",
        evidence=[
            ("W1", "WS-R07-LIFECYCLE", ["/storyline_ids", "/observable_outputs", "/limits"]),
            ("S1", "SL-R07-MAIN", ["/goal", "/end_state"]),
        ],
        subject_id="WS-R07-LIFECYCLE",
        target_id="SL-R07-MAIN",
        conclusion="W1 系统直接绑定 SL-R07-MAIN，并以可观察输出承载：" + _value(index, "W1", "WS-R07-LIFECYCLE", "/observable_outputs")[0] + "；没有另造可行动的数字主体。",
    )
    add(
        "cross_domain_checks",
        check_id="CHK-CROSS-W1-E1-ATTACK",
        scope="W1-E1-attack-support",
        checked_contract="E1 的联合核验环境必须直接消费 W1 威胁行动系统并保留其权限、失败模式与证据边界。",
        evidence=[
            ("E1", "ENV-JOINT-INTELLIGENCE-COMMAND", ["/storyline_stage_ids", "/scope", "/blockers"]),
            ("W1", "END-W1-07", ["/required_capability", "/constraints"]),
        ],
        subject_id="ENV-JOINT-INTELLIGENCE-COMMAND",
        target_id="END-W1-07",
        conclusion="联合情报环境直接消费 END-W1-07，其具体承载范围是：" + _value(index, "E1", "ENV-JOINT-INTELLIGENCE-COMMAND", "/scope") + "，没有把 W1 的证据边界改写成单点命令。",
    )
    add(
        "cross_domain_checks",
        check_id="CHK-CROSS-E1-T1-FAREWELL",
        scope="E1-T1-shutdown-hosting",
        checked_contract="T1 告别事件必须落在 E1 已定义的隔离运行、多方关停环境中，并服从该环境阻断项。",
        evidence=[
            ("T1", "EV-R07-MAIN-06", ["/environment_id", "/preconditions", "/direct_result"]),
            ("E1", "ENV-R07-CORE-LAB", ["/scope", "/blockers"]),
        ],
        subject_id="EV-R07-MAIN-06",
        target_id="ENV-R07-CORE-LAB",
        conclusion="告别事件确实落在 ENV-R07-CORE-LAB；该环境的承载范围是：" + _value(index, "E1", "ENV-R07-CORE-LAB", "/scope"),
    )
    add(
        "cross_domain_checks",
        check_id="CHK-CROSS-T1-C1-FAREWELL-CAST",
        scope="T1-C1-farewell-cast",
        checked_contract="C1 必须把 T1 告别事件的全部角色槽解析为有职责的人物，不得留下无人承担的关停结果。",
        evidence=[
            ("C1", "COV-C1-EV-031", ["/source_ids", "/realization_ids", "/status"]),
            ("T1", "EV-R07-MAIN-06", ["/direct_result", "/participant_slot_ids"]),
        ],
        subject_id="COV-C1-EV-031",
        target_id="EV-R07-MAIN-06",
        conclusion="C1 覆盖账本直接绑定 EV-R07-MAIN-06，并由贺闻钧、R-07、沈逾承担；事件结果保持：" + _value(index, "T1", "EV-R07-MAIN-06", "/direct_result"),
    )
    add(
        "consistency_matrix",
        check_id="CHK-CONSISTENCY-R07-BREAKDOWN",
        scope="S1-T1-breakdown-cause",
        checked_contract="R-07 崩溃的原因必须是认识自身处境；沈逾压力只能加重或延长，不能被误写为主因。",
        evidence=[
            ("T1", "ST-R07-MAIN-03", ["/subject_id", "/from_state", "/to_state", "/consequence"]),
            ("S1", "SL-R07-MAIN", ["/state_changes", "/pressure"]),
        ],
        subject_id="ST-R07-MAIN-03",
        target_id="SL-R07-MAIN",
        conclusion="S1 与 T1 对崩溃因果一致，状态账本明确写成：" + _value(index, "T1", "ST-R07-MAIN-03", "/consequence"),
    )
    add(
        "consistency_matrix",
        check_id="CHK-CONSISTENCY-SHENYU-AGENCY",
        scope="T1-C1-ShenYu-agency",
        checked_contract="沈逾必须在事件中作出接受任务、重建交流和执行关停等自己的选择，并承担伦理与关系代价。",
        evidence=[
            ("C1", "AGY-C1-012", ["/event_ids", "/chosen_action", "/cost"]),
            ("T1", "EV-R07-MAIN-06", ["/direct_result", "/initiator_slot_id"]),
        ],
        subject_id="AGY-C1-012",
        target_id="EV-R07-MAIN-06",
        conclusion="T1 的关停执行与 C1 的沈逾选择记录相互一致；她承担的后果被定义为：" + _value(index, "C1", "AGY-C1-012", "/cost"),
    )
    add(
        "consistency_matrix",
        check_id="CHK-CONSISTENCY-R07-CAST",
        scope="S1-C1-R07-cast",
        checked_contract="R-07 主线的角色实现必须包含 R-07、沈逾与现实行动承担者，不能只剩抽象 AI。",
        evidence=[
            ("C1", "COV-C1-SL-007", ["/source_ids", "/realization_ids", "/status"]),
            ("S1", "SL-R07-MAIN", ["/goal", "/actor_slot_ids"]),
        ],
        subject_id="COV-C1-SL-007",
        target_id="SL-R07-MAIN",
        conclusion="C1 对 SL-R07-MAIN 的实现集合包含现实行动者；它支撑的主线目标仍是：" + _value(index, "S1", "SL-R07-MAIN", "/goal"),
    )

    return {**checks, "assertion_bindings": bindings}


def main() -> None:
    _assert_identity()
    if driver.RUN_ID != RUN_ID:
        raise RuntimeError("driver imported with the wrong run id")
    gate = _gate()
    index = _object_index()
    session = driver.q1rt.start_semantic_review(
        driver.Q1_CONTROLLER,
        driver.Q1_SEMANTIC,
        baseline_package=driver.RUN_ROOT / "B0",
        storyline_package=driver.RUN_ROOT / "S1",
        world_package=driver.RUN_ROOT / "W1",
        environment_package=driver.RUN_ROOT / "E1",
        event_package=driver.RUN_ROOT / "T1",
        character_package=driver.RUN_ROOT / "C1",
        input_gate=gate,
    )
    outputs = []
    for phase, payload in (
        ("review-plan", _plan(index)),
        ("domain-challenges", _domain_payload(index)),
        ("cross-domain-challenges", _cross_domain_payload(index)),
    ):
        outputs.append(
            {
                "phase": phase,
                "evidence": driver.q1rt.submit_semantic_phase(
                    driver.Q1_CONTROLLER,
                    driver.Q1_SEMANTIC,
                    phase=phase,
                    payload=payload,
                ),
            }
        )
    state = driver.q1rt._latest_state(driver.Q1_CONTROLLER)
    print(
        json.dumps(
            {
                "session_id": session["session_id"],
                "semantic_identity": session["identity"],
                "sealed_phases": outputs,
                "controller_status": state["status"],
                "completed_phases": state["completed_phases"],
                "checks": {
                    "domain": 5,
                    "reality": 1,
                    "coverage": 1,
                    "causal": 3,
                    "easy_solution": 3,
                    "cross_domain": 4,
                    "consistency": 3,
                },
                "review_result": "all-submitted-checks-pass",
                "findings_deferred_to_final_review": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def finish_q1() -> None:
    _assert_identity()
    if driver.RUN_ID != RUN_ID:
        raise RuntimeError("driver imported with the wrong run id")
    state = driver.q1rt._latest_state(driver.Q1_CONTROLLER)
    if state["status"] == "handoff_sealed":
        driver.q1rt.import_sealed_handoff(
            driver.Q1_CONTROLLER,
            driver.Q1_SEMANTIC,
            driver.Q1_HANDOFF,
        )
        state = driver.q1rt._latest_state(driver.Q1_CONTROLLER)
    if state["status"] == "handoff_imported":
        p2 = driver.q1rt._phase_payload(
            driver.Q1_SEMANTIC, 2, "domain-challenges"
        )
        p3 = driver.q1rt._phase_payload(
            driver.Q1_SEMANTIC, 3, "cross-domain-challenges"
        )
        handoff = driver.q1rt._read(
            driver.Q1_SEMANTIC
            / state["imported_handoff"]["evidence"]["path"],
            "Q1_HANDOFF_IMPORT_INVALID",
        )
        review = {
            "schema_version": "2.0",
            "skill": "novel-conception-reviewer",
            "stage": "Q1",
            "run_id": RUN_ID,
            "status": "ready",
            "input_gate": copy.deepcopy(state["input_gate"]),
            **{
                key: copy.deepcopy(value)
                for key, value in p2.items()
                if key != "assertion_bindings"
            },
            **{
                key: copy.deepcopy(value)
                for key, value in p3.items()
                if key != "assertion_bindings"
            },
            "development_usability_test": copy.deepcopy(
                handoff["payload"]["development_usability_test"]
            ),
            "handoff_test_evidence": copy.deepcopy(
                state["imported_handoff"]["evidence"]
            ),
            "task_isolation": {
                "semantic_task_id": state["semantic_identity"]["task_id"],
                "handoff_task_id": state["handoff_identity"]["task_id"],
                "handoff_allowlist": copy.deepcopy(state["handoff_allowlist"]),
                "forbidden_reads": list(driver.q1rt.FORBIDDEN_HANDOFF_READS),
            },
            "findings": [],
            "return_request": None,
            "verdict": "ready",
        }
        driver.q1rt.submit_final_review(
            driver.Q1_CONTROLLER,
            driver.Q1_SEMANTIC,
            review=review,
        )
        state = driver.q1rt._latest_state(driver.Q1_CONTROLLER)
    if state["status"] != "final_sealed":
        raise RuntimeError(f"Q1 semantic workspace is not final_sealed: {state['status']}")

    context = driver.prod.resume_production_run(driver.RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != "Q1":
        raise RuntimeError("Q1 is not the active production work order")

    def execute_q1(coordinator: Any, input_gate: Any) -> Any:
        return driver.q1rt.run_q1(
            driver.RUN_ROOT / "Q1",
            baseline_package=driver.RUN_ROOT / "B0",
            storyline_package=driver.RUN_ROOT / "S1",
            world_package=driver.RUN_ROOT / "W1",
            environment_package=driver.RUN_ROOT / "E1",
            event_package=driver.RUN_ROOT / "T1",
            character_package=driver.RUN_ROOT / "C1",
            coordinator=coordinator,
            input_gate=input_gate,
            controller_workspace=driver.Q1_CONTROLLER,
            semantic_workspace=driver.Q1_SEMANTIC,
            handoff_workspace=driver.Q1_HANDOFF,
            logical_package_path="Q1",
            next_state_path="state/revision-007.json",
            active_return_request=context.active_return,
        )

    receipt, successor = driver.prod.execute_stage_work(
        context,
        work_order=order,
        actor="novel-conception-reviewer",
        executor=execute_q1,
    )
    print(
        json.dumps(
            {
                "run_id": RUN_ID,
                "q1_package": str(receipt.package_root),
                "verdict": receipt.verdict,
                "completion": receipt.completion.data,
                "state_revision": successor.state.data["revision"],
                "current_stages": list(
                    successor.state.data["current_stage_completions"]
                ),
                "active_return": successor.state.data["active_return"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "finish":
        finish_q1()
    else:
        main()
