"""Reusable schema-valid HD1 fixture for public integration tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
SUPPORT_PATH = REPO / "skills" / "novel-hld-narrative-architect" / "tests" / "test_skill.py"
spec = importlib.util.spec_from_file_location("hld_public_fixture_hd1_base", SUPPORT_PATH)
assert spec and spec.loader
BASE = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = BASE
spec.loader.exec_module(BASE)

from runtime.canonical import canonical_sha256  # type: ignore[import-not-found]  # noqa:E402


CONTRACT = json.loads((SKILL / "references" / "runtime-contract.json").read_text(encoding="utf-8"))


def _authority() -> dict:
    return {
        "source_id": BASE.FREE_ID,
        "classification": "freedom",
        "open_item": False,
        "authority_class": "downstream_freedom",
        "value_sha256": BASE.VALUE_HASH,
    }


def _owned(identifier: str, **extra) -> dict:
    value = {
        "id": identifier,
        "source_refs": [BASE.FREE_ID],
        "source_authority_refs": [_authority()],
        "ownership_class": "hld_owned",
        "resolution_ref": None,
    }
    value.update(extra)
    return value


def stage_model(stage: str, input_gate_ref: dict, actual_reads: list[dict]) -> dict:
    if stage != "HD1":
        raise AssertionError(f"HD1 fixture cannot build {stage}")
    previous = BASE.CONTRACT
    BASE.CONTRACT = CONTRACT
    try:
        model = BASE.common_model(stage, input_gate_ref, actual_reads)
    finally:
        BASE.CONTRACT = previous

    before = {
        "story_state": "线索尚未进入人物可以行动的范围",
        "character_state": "人物仍相信自己可以安全退出",
        "knowledge_state": "人物只知道异常存在却不知道来源",
        "pressure_state": "对手正在收紧调查窗口",
        "available_actions": ["继续核验线索", "保留安全退路"],
    }
    after = {
        "story_state": "线索已成为对手能够追踪的行动事实",
        "character_state": "人物决定承担暴露风险并失去安全退路",
        "knowledge_state": "人物确认异常来自可追查的设备记录",
        "pressure_state": "对手已改变追查方式并逼近人物",
        "available_actions": ["带着有限证据继续追查", "处理暴露造成的后果"],
    }
    chapter = _owned(
        "HDF-001",
        chapter_id="HCH-001",
        chapter_number=1,
        working_title="第一章：迫近的选择",
        parent_unit_id="HNU-001",
        narrative_necessity="迫使人物用失去安全退路的代价，把模糊异常变成下一章必须追查的事实",
        entry_state=before,
        time_scope="一个持续收紧的夜晚",
        place_scope=["ENV-001"],
        storyline_roles={
            "primary_storyline_id": "SL-MAIN-001",
            "supporting_storyline_ids": [],
            "background_storyline_ids": [],
            "preserved_open_storyline_ids": [],
        },
        pov_contract={
            "hi1_assignment_id": "HPV-CHAPTER-001",
            "focal_character_id": "CHR-001",
            "pov_mode": "第三人称限知",
            "may_know": ["人物亲自核验过的设备异常"],
            "must_not_know": ["对手尚未暴露的完整计划"],
            "reader_knows_before": ["人物正在追查一项异常"],
            "reader_knows_after": ["异常能够被设备记录独立核验"],
        },
        dramatic_contract={
            "choice_actor_ids": ["CHR-001"],
            "institutional_choice_actors": [],
            "cost_bearer_ids": ["CHR-001"],
            "immediate_goal": "在调查窗口关闭前取得一份能够被独立核验的设备记录",
            "active_opposition": "对手切断访问权限并沿着查询痕迹追查人物",
            "pressure_escalation": "可用时间缩短，同时继续查询会暴露人物所在位置",
            "consequential_choice": "人物放弃安全退出，留下最少但可复核的线索",
            "choice_cost": "人物失去原有退路，并把自己置于对手追查范围内",
            "immediate_consequence": "对手改变追查方式，人物只能依靠有限证据继续行动",
            "irreversible_change": "人物的调查已经留下痕迹，原先不被注意的状态无法恢复",
        },
        story_development={
            "required_developments": ["把异常从猜测推进为可复核的设备事实"],
            "information_revealed": ["设备记录与公开状态存在明确矛盾"],
            "information_withheld": ["谁修改了设备记录以及最终目的是什么"],
            "fair_clues": ["访问时间与设备编号能够在后续章节再次核验"],
            "relationship_changes": ["人物开始依赖另一名角色接收有限而危险的证据"],
        },
        memory_design=None,
        exit_state=after,
        chapter_end_hook="对手沿着刚刚留下的访问痕迹逼近人物",
        unresolved_question="设备记录究竟由谁修改，修改命令来自哪里",
        next_chapter_necessity="下一章必须处理人物暴露后的追查，并验证已经交出的有限线索",
        references={
            "character_ids": ["CHR-001"],
            "environment_ids": ["ENV-001"],
            "event_ids": ["EV-001"],
            "key_function_ids": ["HKF-001"],
        },
        lld_handoff={
            "scene_design_must_solve": ["用具体行动呈现核验、受阻、选择和代价的连续因果"],
            "freedoms": ["可以设计场景数量、动作细节与自然对话"],
            "prohibitions": ["不得让巧合替人物取得线索", "不得提前揭露对手完整计划"],
            "acceptance_criteria": ["章节结束时线索可复核且人物确实失去安全退路"],
        },
    )
    model.update({
        "chapter_definitions": [chapter],
        "chapter_chain": [],
        "coverage_summary": {
            "chapter_shell_ids": ["HCH-001"],
            "chapter_definition_ids": ["HDF-001"],
            "storyline_ids": ["SL-MAIN-001"],
            "character_ids": ["CHR-001"],
            "environment_ids": ["ENV-001"],
            "event_ids": ["EV-001"],
            "key_function_ids": ["HKF-001"],
        },
    })
    model["authority_partition"]["hld_ownership"]["hld_owned"] = ["HDF-001"]
    model["derivation_claims"] = [{
        "id": "DRV-HD1-001",
        "source_refs": [BASE.FREE_ID],
        "target_locator": "/chapter_definitions/0/narrative_necessity",
        "value_sha256": canonical_sha256(chapter["narrative_necessity"]),
    }]
    return model
