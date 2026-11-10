from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS))

from common import build_source_inventory, sha256_file, write_json  # noqa: E402
from validate_human_review import (  # noqa: E402
    ContractError,
    _validate_fragment_package,
    validate_plan_package,
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_manifest(directory: Path, names: list[str], **extra: object) -> dict:
    manifest = {
        "schema_version": "1.0",
        "files": [
            {"path": name, "sha256": sha256_file(directory / name)} for name in names
        ],
        **extra,
    }
    write_json(directory / "package-manifest.json", manifest)
    return manifest


def make_upstream(root: Path) -> tuple[Path, Path]:
    d1 = root / "D1"
    r1 = root / "R1"
    d1.mkdir(parents=True)
    r1.mkdir(parents=True)
    map_data = {
        "schema_version": "3.2",
        "status": "ready",
        "control_points": [{"id": "K1", "summary": "控制"}],
        "conception": {
            "world": {
                "id": "W0",
                "definition": "有限资源世界",
                "facets": [{"id": "WF1", "name": "公共秩序"}],
                "systems": [{"id": "WS1", "name": "许可系统"}],
                "environments": [{"id": "WE1", "name": "封闭港站"}],
            },
            "story": {
                "id": "S0",
                "core_promise": "主人公必须选择",
                "phases": [
                    {"id": "SP1", "title": "进入"},
                    {"id": "SP2", "title": "受压"},
                    {"id": "SP3", "title": "选择"},
                ],
                "storylines": [{"id": "SL1", "title": "主线"}],
            },
            "characters": [
                {
                    "id": "C1",
                    "name": "林澈",
                    "relationship_layers": [
                        {"id": "R1", "name": "亲密层"},
                        {"id": "R2", "name": "职责层"},
                        {"id": "R3", "name": "制度层"},
                    ],
                },
                {"id": "C2", "name": "周遥"},
            ],
        },
        "units": [
            {"id": "U1", "title": "进入"},
            {"id": "U2", "title": "受压"},
            {"id": "U3", "title": "选择"},
        ],
        "open_items": [{"id": "O1", "title": "未来接口"}],
    }
    write_json(d1 / "map-data.json", map_data)
    make_manifest(d1, ["map-data.json"], stage="D1", verdict="ready")
    d1_hash = sha256_file(d1 / "package-manifest.json")

    write_json(
        r1 / "review-data.json",
        {
            "schema_version": "1.0",
            "stage": "R1",
            "run_id": "generic-run",
            "status": "ready",
            "findings": [],
        },
    )
    write_json(
        r1 / "validation.json",
        {"verdict": "ready", "errors": [], "blockers": []},
    )
    write_json(
        r1 / "independent-handoff.json",
        {
            "verdict": "pass",
            "d1_package": {
                "path": "../D1/package-manifest.json",
                "sha256": d1_hash,
            },
        },
    )
    write_text(r1 / "novel-design-brief.md", "# 通用构思\n")
    make_manifest(
        r1,
        [
            "review-data.json",
            "validation.json",
            "independent-handoff.json",
            "novel-design-brief.md",
        ],
        stage="R1",
        verdict="ready",
    )
    return r1, d1


def item(item_id: str, text: str, sources: list[str]) -> dict:
    return {"id": item_id, "text": text, "source_ids": sources}


def make_plan(inventory: dict) -> dict:
    bp = {
        "orientation": {
            "story_identity": item("HR-O-01", "一名守门人在危机中选择承担代价。", ["S0", "C1"]),
            "this_is": [item("HR-O-02", "关于选择与责任的故事。", ["S0"])],
            "this_is_not": [item("HR-O-03", "不是无代价的胜利幻想。", ["S0"])],
            "review_instruction": item("HR-O-04", "请判断世界、故事、人物和片段。", ["S0"]),
        },
        "world": {
            "definition": item("HR-W-00", "资源和行动都受许可约束。", ["W0"]),
            "systems": [
                {
                    "id": "HR-W-01",
                    "name": "许可系统",
                    "rule": "行动必须获得许可。",
                    "permissions": "守门人只能核验。",
                    "resources": "许可有时效。",
                    "cost_or_failure": "越权会触发封锁。",
                    "source_ids": ["WS1"],
                }
            ],
            "environments": [
                {
                    "id": "HR-W-02",
                    "name": "封闭港站",
                    "signature": "狭窄且持续广播。",
                    "elements": "闸门、广播、备用电源。",
                    "access_and_hazard": "凭许可进入，停电会封闭。",
                    "story_function": "迫使人物共同决策。",
                    "state_change": "由中转站变成困局。",
                    "source_ids": ["WE1"],
                }
            ],
            "boundaries": [
                {
                    "id": "HR-W-03",
                    "name": "秩序边界",
                    "commitment": "不能绕过公共安全核验。",
                    "source_ids": ["WF1"],
                }
            ],
            "open_interfaces": [
                {
                    "id": "HR-W-04",
                    "title": "未来接口",
                    "text": "危机后的制度走向保持开放。",
                    "source_ids": ["O1"],
                }
            ],
            "visual_model": {
                "type": "world-system-map",
                "nodes": [
                    {
                        "id": "HR-WV-01",
                        "name": "许可连接港站",
                        "source_ids": ["WS1", "WE1"],
                    }
                ],
                "edges": [],
            },
            "review_question": "这些规则和环境是否足以迫使人物付出代价？",
        },
        "story": {
            "definition": {
                "id": "HR-S-00",
                "promise": "主人公在秩序与救人之间选择。",
                "dramatic_question": "他会不会越过自己的边界？",
                "start": "按规核验",
                "end": "承担选择后果",
                "stakes": "个体生命与公共秩序",
                "source_ids": ["S0"],
            },
            "lines": [
                {
                    "id": "HR-SL-01",
                    "name": "守门主线",
                    "kind": "main",
                    "function": "推动选择",
                    "driver": "林澈",
                    "intersections": "危机时与制度压力交汇",
                    "end": "主动承担后果",
                    "source_ids": ["SL1"],
                }
            ],
            "timeline": [
                {
                    "id": "HR-T-01",
                    "label": "进入",
                    "pressure": "陌生人请求通行",
                    "choice": "坚持核验",
                    "consequence": "时间流失",
                    "cost": "关系紧张",
                    "new_state": "危机逼近",
                    "unit_ids": ["U1"],
                    "line_ids": ["HR-SL-01"],
                    "source_ids": ["SP1", "U1"],
                },
                {
                    "id": "HR-T-02",
                    "label": "受压",
                    "pressure": "电力中断",
                    "choice": "共享权限信息",
                    "consequence": "得到合作",
                    "cost": "暴露职责弱点",
                    "new_state": "可以行动",
                    "unit_ids": ["U2"],
                    "line_ids": ["HR-SL-01"],
                    "source_ids": ["SP2", "U2"],
                },
                {
                    "id": "HR-T-03",
                    "label": "选择",
                    "pressure": "闸门即将锁死",
                    "choice": "承担越权责任",
                    "consequence": "救下被困者",
                    "cost": "失去职位",
                    "new_state": "制度问题开放",
                    "unit_ids": ["U3"],
                    "line_ids": ["HR-SL-01"],
                    "source_ids": ["SP3", "U3"],
                },
            ],
            "narrative_constraints": [
                item("HR-N-01", "只展示人物当下可知信息。", ["K1"])
            ],
            "open_interfaces": [
                item("HR-S-OPEN", "制度余波留到后续开发。", ["O1"])
            ],
            "visual_model": {
                "type": "multi-line-timeline",
                "nodes": [
                    {
                        "id": "HR-SV-01",
                        "label": "三阶段推进",
                        "source_ids": ["SP1", "SP2", "SP3"],
                    }
                ],
                "edges": [],
            },
            "review_question": "压力、选择和代价是否构成可信推进？",
        },
        "characters": {
            "definition": item("HR-C-00", "人物靠主动选择改变局面。", ["C1", "C2"]),
            "profiles": [
                {
                    "id": "HR-C-01",
                    "character_source_id": "C1",
                    "name": "林澈",
                    "role": "守门人",
                    "story_function": "承担核心选择。",
                    "surface_goal": "维持秩序",
                    "deeper_need": "确认责任属于自己",
                    "fear": "越权伤人",
                    "values_and_boundaries": "不牺牲无辜者",
                    "information_limits": "不知道停电原因",
                    "pressure_behavior": "先核验再行动",
                    "agency_choice": "自愿承担越权后果",
                    "arc": "从守规到负责",
                    "end_state": "失去职位但保有判断",
                    "invariants": "不能漠视生命",
                    "source_ids": ["C1"],
                },
                {
                    "id": "HR-C-02",
                    "character_source_id": "C2",
                    "name": "周遥",
                    "role": "求助者",
                    "story_function": "提供另一种责任视角。",
                    "surface_goal": "通过闸门",
                    "deeper_need": "得到平等信任",
                    "fear": "再次被制度拒绝",
                    "values_and_boundaries": "不以谎言换通行",
                    "information_limits": "不知道守门权限",
                    "pressure_behavior": "直接提出证据",
                    "agency_choice": "留下协助救人",
                    "arc": "从求助到协作",
                    "end_state": "成为证人",
                    "invariants": "不伪造证据",
                    "source_ids": ["C2"],
                },
            ],
            "relationship_layers": [
                {
                    "id": "HR-R-01",
                    "layer": "1",
                    "from_character_source_id": "C1",
                    "to_character_source_id": "C2",
                    "function": "互信",
                    "start_state": "彼此怀疑",
                    "pressure": "时间减少",
                    "change": "共享证据",
                    "end_state": "有限信任",
                    "source_ids": ["R1", "C1", "C2"],
                },
                {
                    "id": "HR-R-02",
                    "layer": "2",
                    "from_character_source_id": "C1",
                    "to_character_source_id": "C2",
                    "function": "职责",
                    "start_state": "核验与被核验",
                    "pressure": "系统失效",
                    "change": "共同判断",
                    "end_state": "责任见证",
                    "source_ids": ["R2", "C1", "C2"],
                },
                {
                    "id": "HR-R-03",
                    "layer": "3",
                    "from_character_source_id": "C1",
                    "to_character_source_id": "C2",
                    "function": "制度",
                    "start_state": "规则隔开两人",
                    "pressure": "规则不能救人",
                    "change": "以代价暴露缺口",
                    "end_state": "制度问题公开",
                    "source_ids": ["R3", "C1", "C2"],
                },
            ],
            "visual_model": {
                "type": "layered-relationship-map",
                "nodes": [
                    {"id": "HR-CV-01", "name": "林澈—周遥", "source_ids": ["C1", "C2"]}
                ],
                "edges": [],
            },
            "review_question": "人物是否在边界内主动改变了局面？",
        },
        "fragments": {
            "sample_authority": "以下内容只是评审样本，不是最终定稿或新设定权威。",
            "slots": [
                {
                    "id": "HR-FRAG-01",
                    "title": "第一次核验",
                    "purpose": "验证世界规则进入行动。",
                    "review_question": "规则是否自然形成压力？",
                    "pov": "C1",
                    "before_state": "例行值守",
                    "after_state": "危机逼近",
                    "required_facts": ["必须核验"],
                    "prohibited_facts": ["不能提前知道停电原因"],
                    "required_source_ids": ["U1", "WS1"],
                    "allowed_source_ids": ["U1", "WS1", "WE1", "C1", "K1"],
                    "control_ids": ["K1"],
                    "unit_ids": ["U1"],
                    "narrative_constraints": ["限知"],
                    "allowed_creative_freedom": ["局部动作"],
                    "coverage_targets": ["world_in_action", "narrative_contract"],
                    "max_cjk_chars": 120,
                    "max_latin_words": 0,
                    "source_ids": ["U1", "WS1"],
                },
                {
                    "id": "HR-FRAG-02",
                    "title": "共同判断",
                    "purpose": "验证关系和能动性。",
                    "review_question": "关系变化是否来自行动？",
                    "pov": "C2",
                    "before_state": "互不信任",
                    "after_state": "有限协作",
                    "required_facts": ["共享证据"],
                    "prohibited_facts": ["不能无条件信任"],
                    "required_source_ids": ["U2", "C1", "C2"],
                    "allowed_source_ids": ["U2", "C1", "C2", "R1", "R2", "K1"],
                    "control_ids": ["K1"],
                    "unit_ids": ["U2"],
                    "narrative_constraints": ["限知"],
                    "allowed_creative_freedom": ["对话节奏"],
                    "coverage_targets": ["character_agency", "relationship_change"],
                    "max_cjk_chars": 120,
                    "max_latin_words": 0,
                    "source_ids": ["U2", "C1", "C2"],
                },
                {
                    "id": "HR-FRAG-03",
                    "title": "闸门之后",
                    "purpose": "验证选择、代价和结局。",
                    "review_question": "结局是否支付了承诺的代价？",
                    "pov": "C1",
                    "before_state": "闸门将锁",
                    "after_state": "失去职位",
                    "required_facts": ["主动承担"],
                    "prohibited_facts": ["不能取消代价"],
                    "required_source_ids": ["U3", "C1"],
                    "allowed_source_ids": ["U3", "C1", "C2", "O1", "K1"],
                    "control_ids": ["K1"],
                    "unit_ids": ["U3"],
                    "narrative_constraints": ["不提前裁决制度"],
                    "allowed_creative_freedom": ["余波意象"],
                    "coverage_targets": ["story_causality", "ending_nature"],
                    "max_cjk_chars": 120,
                    "max_latin_words": 0,
                    "source_ids": ["U3", "C1"],
                },
            ],
            "review_question": "这些片段是否证明构思能转化为目标体验？",
        },
        "decision": {
            "questions": {
                "world": "这是你想要的世界吗？",
                "story": "故事应该这样发展吗？",
                "characters": "人物应该这样选择吗？",
                "fragments": "阅读体验接近目标吗？",
            },
            "options": ["approve", "revise"],
            "open_items": [item("HR-D-01", "制度后续仍然开放。", ["O1"])],
            "instruction": "请按四个板块判断是否进入开发。",
        },
    }
    bp["orientation"]["logic_spine"] = [
        {
            "id": f"HR-LOGIC-{index:02d}",
            "layer": layer,
            "title": title,
            "claim": claim,
            "therefore": therefore,
            "controls": controls,
            "must_hold": must_hold,
            "boundary": boundary,
            "source_ids": sources,
        }
        for index, (layer, title, claim, therefore, controls, must_hold, boundary, sources)
        in enumerate(
            [
                ("worldview", "世界观命题", "责任必须由能够选择的人承担。", "制度不能替人物完成伦理判断。", "人物选择与主题检验。", "救人和守序都必须支付代价。", "不得写成规则自动给出答案。", ["W0", "S0"]),
                ("world_rules", "世界运行规则", "行动受到许可和资源时效限制。", "危机必然把核验转化为时间压力。", "系统权限、失败与行动边界。", "任何越权都留下可追责后果。", "不得用万能权限解除困局。", ["WS1", "WF1"]),
                ("event_space", "事件承载环境", "封闭港站把规则变成可见阻碍。", "停电与锁门迫使人物共同判断。", "环境可发生与不可发生的动作。", "关键选择必须发生在受限现场。", "不得把环境写成装饰背景。", ["WE1", "U1"]),
                ("story_architecture", "故事线架构", "三阶段因果持续抬高选择代价。", "主线从核验推进到主动负责。", "阶段连接、交汇与终点。", "每一阶段都改变下一阶段前提。", "不得用偶然跳过因果节点。", ["SL1", "SP1", "SP2", "SP3"]),
                ("character_agency", "人物能动选择", "林澈和周遥都以行动改变局面。", "关系变化必须来自共享风险。", "责任、权限与不可委托选择。", "双方选择都受信息边界限制。", "不得把人物写成情节工具。", ["C1", "C2"]),
                ("terminal_contract", "终局契约", "救人成功但越权代价仍然生效。", "结局兑现责任主题并保留制度余波。", "结局事实与后续开放接口。", "胜利不能抹去职位与制度后果。", "不得在构思阶段裁决制度未来。", ["U3", "O1"]),
            ],
            start=1,
        )
    ]
    for system in bp["world"]["systems"]:
        system.update(
            {
                "definition": "规定谁能核验、授权和执行港站通行。",
                "controls": "控制危机中的行动顺序与责任归属。",
                "must_not": "不得提供无需核验或无需追责的万能通行。",
                "control_summary": "许可先于行动；越权能救人，但必须留下可追责后果。",
            }
        )
    for environment in bp["world"]["environments"]:
        environment.update(
            {
                "affordances": "允许核验、广播、封锁与协作救援。",
                "prohibitions": "不能绕过闸门、停电与现场权限限制。",
                "hosted_event_source_ids": ["U1", "U2", "U3"],
                "controls": "承载全部关键选择并让制度压力可见。",
                "must_hold": "环境状态变化必须改变下一事件的可行动作。",
                "control_summary": "封闭港站把许可变成物理阻碍；停电后，只能以协作和担责推进。",
            }
        )
    for line in bp["story"]["lines"]:
        line.update(
            {
                "start": "例行核验被求助打断",
                "objective": "在公共秩序与救人之间形成可承担的选择",
                "connection_points": "进入、受压、选择三个阶段连续接力",
                "exit_condition": "人物完成选择并承担制度后果",
                "must_hold": "结果必须由人物选择而非系统自动裁决",
                "optional_scope": "局部救援动作可开发，因果节点不可省略",
                "control_summary": "求助打断核验→停电迫使协作→林澈越权救人并承担后果。",
            }
        )
    for stage in bp["story"]["timeline"]:
        stage["logic_summary"] = (
            f"{stage['pressure']}→{stage['choice']}→{stage['consequence']}；"
            f"并把局面推进为{stage['new_state']}。"
        )
    bp["story"]["event_controls"] = [
        {
            "id": f"HR-E-{index:02d}",
            "event_source_id": unit_id,
            "name": name,
            "role": role,
            "logic": logic,
            "controls": controls,
            "line_ids": ["HR-SL-01"],
            "environment_source_ids": ["WE1"],
            "character_source_ids": ["C1", "C2"],
            "source_ids": [unit_id, "WE1", "C1", "C2"],
        }
        for index, (unit_id, name, role, logic, controls) in enumerate(
            [
                ("U1", "求助进入核验", "建立规则压力", "陌生求助进入→林澈坚持核验→可用时间减少。", "锁定许可规则必须进入人物行动。"),
                ("U2", "停电迫使协作", "改变关系与能力", "系统失效→双方共享证据→获得有限行动能力。", "锁定互信必须由共同风险产生。"),
                ("U3", "越权救人与担责", "兑现主题和代价", "闸门将锁→林澈主动越权→救人且失去职位。", "锁定胜利不能取消选择代价。"),
            ],
            start=1,
        )
    ]
    for profile in bp["characters"]["profiles"]:
        profile.update(
            {
                "responsibility": "对自己的判断及其造成的他人后果负责",
                "authority": "只能使用角色已知信息与既有职责权限",
                "nondelegable_choice": "是否承担风险与后果必须由本人决定",
                "controls": "控制角色在危机中的行动边界和结局位置",
                "must_not": "不得获得越过信息限制或免除代价的便利",
                "control_summary": f"{profile['name']}必须在有限信息下主动选择；选择改变局面，也固定其终局责任。",
            }
        )
    for relation in bp["characters"]["relationship_layers"]:
        relation.update(
            {
                "trigger": "共同风险使原有关系状态无法维持",
                "controls": "控制双方合作程度与责任互认方式",
                "must_hold": "关系变化必须由可见行动触发而非突然亲近",
                "control_summary": f"{relation['start_state']}→共同受压后{relation['change']}→{relation['end_state']}；变化必须由行动证明。",
            }
        )
    element_sources: dict[str, set[str]] = {}

    def collect_elements(value: object) -> None:
        if isinstance(value, dict):
            item_id = value.get("id")
            if isinstance(item_id, str) and item_id.startswith("HR-"):
                element_sources[item_id] = set(value.get("source_ids", []))
            for child in value.values():
                collect_elements(child)
        elif isinstance(value, list):
            for child in value:
                collect_elements(child)

    collect_elements(bp)
    coverage = []
    for subject in inventory["review_subjects"]:
        source_id = subject["source_id"]
        element = next(
            element_id
            for element_id, source_ids in element_sources.items()
            if source_id in source_ids
        )
        coverage.append(
            {
                "source_id": source_id,
                "domain": subject["domain"],
                "visible_element_ids": [element],
                "role": "支持作者判断该对象在构思中的作用。",
            }
        )
    tasks = []
    task_specs = [
        ("story_identity", "这是什么故事？", "HR-O-01", ["S0"]),
        ("world_logic", "世界规则如何改变行动？", "HR-W-01", ["WS1"]),
        ("story_causality", "故事为何走到结局？", "HR-T-03", ["U3"]),
        ("thread_structure", "各故事线如何作用？", "HR-SL-01", ["SL1"]),
        ("character_agency", "人物主动做了什么？", "HR-C-01", ["C1"]),
        ("relationship_logic", "关系怎样改变？", "HR-R-01", ["R1"]),
        ("narrative_experience", "片段体验是否合适？", "HR-FRAG-01", ["U1"]),
        ("ending_and_open_interfaces", "结局和开放项是什么？", "HR-D-01", ["O1"]),
    ]
    for task_id, question, visible, sources in task_specs:
        tasks.append(
            {
                "id": task_id,
                "question": question,
                "visible_element_ids": [visible],
                "source_ids": sources,
            }
        )
    return {
        "schema_version": "1.0",
        "skill": "novel-conception-human-review-assembler",
        "run_id": inventory["run_id"],
        "status": "ready",
        "source_inventory_sha256": "",
        "review_contract": {
            "work_title": "雾港守门人",
            "audience": "作者与构思决策人",
            "decision": "判断是否进入小说开发",
            "target_minutes": 10,
            "main_sections": ["world", "story", "characters", "fragments"],
            "out_of_scope": [
                "machine_package_replacement",
                "final_novel_prose",
                "html_generation",
                "self_approval",
            ],
        },
        "reading_budget": {
            "profile": {
                "id": "review-reading-baseline-v1",
                "cjk_chars_per_minute": 400,
                "latin_words_per_minute": 200,
                "assumption": "用于内部预算，可经真实测试校准。",
            },
            "navigation_minutes": 0.5,
            "sections": [
                {"id": "orientation", "minutes": 1.0},
                {"id": "world", "minutes": 1.5},
                {"id": "story", "minutes": 2.5},
                {"id": "characters", "minutes": 2.0},
                {"id": "fragments", "minutes": 2.0},
                {"id": "decision", "minutes": 0.5},
            ],
        },
        "report_blueprint": bp,
        "coverage_ledger": coverage,
        "review_tasks": tasks,
    }


def make_plan_package(root: Path, r1: Path) -> Path:
    package = root / "plan"
    package.mkdir()
    inventory = build_source_inventory(r1)
    write_json(package / "source-inventory.json", inventory)
    plan = make_plan(inventory)
    plan["source_inventory_sha256"] = sha256_file(package / "source-inventory.json")
    write_json(package / "review-plan.json", plan)
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "export_fragment_briefs.py"),
            str(package / "review-plan.json"),
            str(package / "fragment-briefs.json"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "write_execution_record.py"),
            "plan",
            str(package),
            "--executor-id",
            "generic-executor",
            "--task-id",
            "generic-task",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return package


def make_fragment_package(root: Path, plan_dir: Path) -> Path:
    plan = json.loads((plan_dir / "review-plan.json").read_text(encoding="utf-8"))
    briefs = json.loads((plan_dir / "fragment-briefs.json").read_text(encoding="utf-8"))
    fragment_skill = SKILL_DIR.parent / "novel-conception-fragment-writer"
    fragment_scripts = fragment_skill / "scripts"
    style_contract = {
        "id": "restrained-concrete-scene-v1",
        "purpose": "conception_review_sample",
        "name": "克制具象的场景驱动现代白描",
        "fixed_principles": [
            "single_limited_pov",
            "continuous_scene_now",
            "concrete_selective_detail",
            "pressure_choice_consequence",
            "subtextual_interaction",
            "restrained_emotion",
            "earned_state_change",
        ],
        "adaptive_axes": [
            "pov_person",
            "genre_lexicon",
            "character_diction",
            "emotional_temperature",
            "sentence_rhythm",
            "sensory_channels",
        ],
        "prohibitions": [
            "outline_or_screenplay",
            "author_explanation",
            "author_imitation",
            "pov_or_information_breach",
            "exposition_instead_of_choice",
            "unearned_state_change",
            "new_authoritative_fact",
            "final_prose_claim",
        ],
    }
    final_texts = {
        "HR-FRAG-01": (
            "许可灯在林澈指下熄灭。隔着门，周遥把证件贴上结霜的玻璃。"
            "“再核一次。”她说。\n\n备用电源只剩一格。林澈没有抬闸，"
            "而是把核验结果推到她能看见的位置。广播随即中断，门内的倒计时亮了起来。"
        ),
        "HR-FRAG-02": (
            "周遥把纸面证据推过窄台。林澈没有接，只让她念出最后一行。"
            "她读到编号时停了一下。\n\n警报逼近第二遍。周遥把纸留在台上，"
            "转身去扶被困的人。林澈调出核验记录，两份时间戳第一次对上。"
        ),
        "HR-FRAG-03": (
            "闸门只剩最后十秒。林澈的手停在越权键上，系统仍要求第二份许可。"
            "周遥站在门外，没有催他。\n\n他按下去，把工号留在记录顶端。"
            "闸门升起半米，被困者依次爬过。屏幕随后收走权限，只剩责任人的名字。"
        ),
    }
    evidence_quotes = {
        "HR-FRAG-01": [
            "许可灯在林澈指下熄灭",
            "备用电源只剩一格",
            "林澈没有抬闸",
            "门内的倒计时亮了起来",
            "周遥把证件贴上结霜的玻璃",
        ],
        "HR-FRAG-02": [
            "周遥把纸面证据推过窄台",
            "警报逼近第二遍",
            "转身去扶被困的人",
            "两份时间戳第一次对上",
            "她读到编号时停了一下",
        ],
        "HR-FRAG-03": [
            "闸门只剩最后十秒",
            "系统仍要求第二份许可",
            "他按下去",
            "屏幕随后收走权限",
            "周遥站在门外，没有催他",
        ],
    }
    target_keys = {
        "world_in_action": "world_in_action",
        "story_causality": "causal_progression",
        "character_agency": "character_agency",
        "relationship_change": "relationship_change",
        "narrative_contract": "narrative_contract",
        "ending_nature": "ending_nature",
    }
    contracts = []
    drafts = []
    audits = []
    for slot in briefs["slots"]:
        fragment_id = slot["id"]
        text = final_texts[fragment_id]
        quotes = evidence_quotes[fragment_id]
        creative_choices = [
            {
                "choice": "以许可灯和窄台承载局部动作。",
                "authorization_basis": slot["allowed_creative_freedom"][0],
            }
        ]
        contracts.append(
            {
                "id": fragment_id,
                "style_contract_id": style_contract["id"],
                "pov": slot["pov"],
                "start_value": slot["before_state"],
                "end_value": slot["after_state"],
                "immediate_intention": "在时限内完成眼前任务。",
                "active_pressure": "许可与剩余时间同时收紧。",
                "obstacle": "人物不能绕过既有核验边界。",
                "turning_choice": "人物主动承担信息或行动责任。",
                "direct_consequence": "行动改变关系、危险或责任状态。",
                "world_rule_in_action": "许可、资源和失败后果直接限制行动。",
                "relationship_change": "双方从拒绝转为有限协作或责任见证。",
                "information_limit": "只呈现指定视角当下可以获得的信息。",
                "allowed_sensory_channels": ["视觉", "听觉"],
                "forbidden_sensory_channels": [],
                "creative_choices": creative_choices,
                "source_ids": slot["required_source_ids"],
                "control_ids": slot["control_ids"],
                "unit_ids": slot["unit_ids"],
            }
        )
        draft_text = text.replace("。", "，", 1)
        drafts.append(
            {
                "id": fragment_id,
                "title": slot["title"],
                "text": draft_text,
                "source_ids": slot["required_source_ids"],
                "control_ids": slot["control_ids"],
                "unit_ids": slot["unit_ids"],
                "creative_choices": creative_choices,
                "introduced_authoritative_facts": [],
            }
        )
        audit_keys = [
            "orientation",
            "pressure_or_goal",
            "turning_choice",
            "consequence_or_state_change",
            "pov_and_information",
        ]
        scene_audit = {
            key: {
                "finding": f"文本以页面证据完成{key}。",
                "evidence_quote": quotes[index],
            }
            for index, key in enumerate(audit_keys)
        }
        for index, target in enumerate(slot["coverage_targets"]):
            scene_audit[target_keys[target]] = {
                "finding": f"片段直接验证{target}。",
                "evidence_quote": quotes[(index + 1) % len(quotes)],
            }
        audits.append(
            {
                "id": fragment_id,
                "title": slot["title"],
                "draft_sha256": hashlib.sha256(draft_text.encode("utf-8")).hexdigest(),
                "final_text": text,
                "source_ids": slot["required_source_ids"],
                "control_ids": slot["control_ids"],
                "unit_ids": slot["unit_ids"],
                "creative_choices": creative_choices,
                "introduced_authoritative_facts": [],
                "contract_checks": {
                    "source_grounding": True,
                    "narrative_contract": True,
                    "no_new_authority": True,
                    "review_question_fit": True,
                },
                "scene_audit": scene_audit,
                "brief_compliance": {
                    "final_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "before_state": {
                        "value": slot["before_state"],
                        "evidence_quote": quotes[0],
                    },
                    "after_state": {
                        "value": slot["after_state"],
                        "evidence_quote": quotes[3],
                    },
                    "required_facts": [
                        {
                            "fact": fact,
                            "finding": "该事实通过人物选择或现场反馈进入正文。",
                            "evidence_quote": quotes[2],
                        }
                        for fact in slot["required_facts"]
                    ],
                    "prohibited_facts": [
                        {
                            "fact": fact,
                            "verdict": "absent",
                            "rationale": "最终文本保留信息边界，没有写入该禁写事实。",
                        }
                        for fact in slot["prohibited_facts"]
                    ],
                },
                "revisions": [
                    {
                        "issue": "初稿转折后的后果不够明确。",
                        "change": "强化选择后的权限或关系变化。",
                        "reason": "让片段前后状态可以直接检查。",
                    }
                ],
            }
        )
    phase_payloads = {
        "scene-contracts": {
            "schema_version": "1.0",
            "phase": "scene-contracts",
            "style_contract": style_contract,
            "fragments": contracts,
        },
        "drafts": {
            "schema_version": "1.0",
            "phase": "drafts",
            "style_contract": style_contract,
            "fragments": drafts,
        },
        "revision-audit": {
            "schema_version": "1.0",
            "phase": "revision-audit",
            "style_contract": style_contract,
            "fragments": audits,
        },
    }
    r1_dir = Path(
        json.loads((plan_dir / "source-inventory.json").read_text(encoding="utf-8"))[
            "source_package"
        ]["r1_directory"]
    )
    workspace = root / "fragment-writing"
    subprocess.run(
        [
            sys.executable,
            str(fragment_scripts / "manage_writing.py"),
            "begin",
            str(plan_dir),
            str(r1_dir),
            str(workspace),
            "--executor-id",
            "fragment-executor",
            "--task-id",
            "fragment-task",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    for phase, payload in phase_payloads.items():
        payload_path = root / f"{phase}.json"
        write_json(payload_path, payload)
        subprocess.run(
            [
                sys.executable,
                str(fragment_scripts / "manage_writing.py"),
                "submit",
                str(workspace),
                phase,
                str(payload_path),
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    fragment_dir = root / "fragments"
    subprocess.run(
        [
            sys.executable,
            str(fragment_scripts / "finalize_fragments.py"),
            str(workspace),
            str(fragment_dir),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return fragment_dir


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.r1, self.d1 = make_upstream(self.root)
        self.plan_dir = make_plan_package(self.root, self.r1)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_plan_package_is_ready(self) -> None:
        evidence = validate_plan_package(self.plan_dir, self.r1)
        self.assertEqual(evidence["verdict"], "ready")
        self.assertEqual(evidence["coverage"]["required_subjects"], 18)
        self.assertLessEqual(evidence["reading_budget"]["measured_total_minutes"], 10)

    def test_r1_not_ready_is_blocked(self) -> None:
        review_path = self.r1 / "review-data.json"
        review = json.loads(review_path.read_text(encoding="utf-8"))
        review["status"] = "revise"
        write_json(review_path, review)
        make_manifest(
            self.r1,
            [
                "review-data.json",
                "validation.json",
                "independent-handoff.json",
                "novel-design-brief.md",
            ],
            stage="R1",
            verdict="ready",
        )
        with self.assertRaisesRegex(ContractError, "not ready"):
            build_source_inventory(self.r1)

    def test_manifest_tampering_is_blocked(self) -> None:
        write_text(self.r1 / "novel-design-brief.md", "tampered")
        with self.assertRaisesRegex(ContractError, "hash mismatch"):
            build_source_inventory(self.r1)

    def test_stale_inventory_is_blocked(self) -> None:
        inventory_path = self.plan_dir / "source-inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        inventory["known_source_ids"].append("FAKE")
        write_json(inventory_path, inventory)
        with self.assertRaisesRegex(ContractError, "stale or hand-edited"):
            validate_plan_package(self.plan_dir, self.r1)

    def _rewrite_plan(self, mutate) -> None:
        plan_path = self.plan_dir / "review-plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        mutate(plan)
        write_json(plan_path, plan)
        subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "export_fragment_briefs.py"),
                str(plan_path),
                str(self.plan_dir / "fragment-briefs.json"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "write_execution_record.py"),
                "plan",
                str(self.plan_dir),
                "--executor-id",
                "generic-executor",
                "--task-id",
                "generic-task",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_missing_coverage_is_blocked(self) -> None:
        self._rewrite_plan(lambda p: p["coverage_ledger"].pop())
        with self.assertRaisesRegex(ContractError, "coverage missing"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_coverage_must_be_supported_by_visible_element_sources(self) -> None:
        def mutate(plan: dict) -> None:
            entry = next(
                item for item in plan["coverage_ledger"] if item["source_id"] == "C1"
            )
            entry["visible_element_ids"] = ["HR-O-02"]

        self._rewrite_plan(mutate)
        with self.assertRaisesRegex(ContractError, "does not actually cite source"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_unknown_source_is_blocked(self) -> None:
        self._rewrite_plan(
            lambda p: p["report_blueprint"]["world"]["systems"][0]["source_ids"].append(
                "UNKNOWN"
            )
        )
        with self.assertRaisesRegex(ContractError, "unknown source"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_world_system_cannot_be_laundered_through_generic_source(self) -> None:
        self._rewrite_plan(
            lambda p: p["report_blueprint"]["world"]["systems"][0].update(
                {"source_ids": ["W0"]}
            )
        )
        with self.assertRaisesRegex(ContractError, "every D1 world system"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_timeline_unit_omission_is_blocked(self) -> None:
        self._rewrite_plan(
            lambda p: p["report_blueprint"]["story"]["timeline"][2].update(
                {"unit_ids": ["U2"], "source_ids": ["SP3", "U2"]}
            )
        )
        with self.assertRaisesRegex(ContractError, "every D1 unit"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_insufficient_relationship_layers_is_blocked(self) -> None:
        self._rewrite_plan(
            lambda p: p["report_blueprint"]["characters"].update(
                {"relationship_layers": p["report_blueprint"]["characters"]["relationship_layers"][:2]}
            )
        )
        with self.assertRaisesRegex(ContractError, "at least 3"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_reading_overflow_is_blocked(self) -> None:
        self._rewrite_plan(
            lambda p: p["report_blueprint"]["orientation"]["story_identity"].update(
                {"text": "非常" * 300}
            )
        )
        with self.assertRaisesRegex(ContractError, "exceeds"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_reading_rate_cannot_be_inflated(self) -> None:
        self._rewrite_plan(
            lambda p: p["reading_budget"]["profile"].update(
                {"cjk_chars_per_minute": 1_000_000}
            )
        )
        with self.assertRaisesRegex(ContractError, "versioned review baseline"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_story_line_schema_matches_html_consumer(self) -> None:
        self._rewrite_plan(
            lambda p: p["report_blueprint"]["story"]["lines"][0].pop("function")
        )
        with self.assertRaisesRegex(ContractError, "missing keys"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_fragment_target_omission_is_blocked(self) -> None:
        self._rewrite_plan(
            lambda p: p["report_blueprint"]["fragments"]["slots"][2].update(
                {"coverage_targets": ["story_causality"]}
            )
        )
        with self.assertRaisesRegex(ContractError, "miss required targets"):
            validate_plan_package(self.plan_dir, self.r1)

    def test_fragment_new_authority_is_blocked(self) -> None:
        fragments = make_fragment_package(self.root, self.plan_dir)
        path = fragments / "fragment-package.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["fragments"][0]["introduced_authoritative_facts"] = ["新增制度"]
        write_json(path, data)
        plan = json.loads((self.plan_dir / "review-plan.json").read_text(encoding="utf-8"))
        inventory = json.loads(
            (self.plan_dir / "source-inventory.json").read_text(encoding="utf-8")
        )
        with self.assertRaisesRegex(ContractError, "canonical fragment validation failed"):
            _validate_fragment_package(
                fragments,
                plan,
                self.plan_dir / "review-plan.json",
                set(inventory["known_source_ids"]),
                self.r1,
            )

    def test_fragment_plan_mismatch_is_blocked(self) -> None:
        fragments = make_fragment_package(self.root, self.plan_dir)
        path = fragments / "fragment-package.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["review_plan_sha256"] = "0" * 64
        write_json(path, data)
        plan = json.loads((self.plan_dir / "review-plan.json").read_text(encoding="utf-8"))
        inventory = json.loads(
            (self.plan_dir / "source-inventory.json").read_text(encoding="utf-8")
        )
        with self.assertRaisesRegex(ContractError, "plan hash mismatch"):
            _validate_fragment_package(
                fragments,
                plan,
                self.plan_dir / "review-plan.json",
                set(inventory["known_source_ids"]),
                self.r1,
            )

    def test_fragment_forged_execution_binding_is_blocked(self) -> None:
        fragments = make_fragment_package(self.root, self.plan_dir)
        path = fragments / "execution-record.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["fragment_package_sha256"] = "0" * 64
        write_json(path, data)
        plan = json.loads((self.plan_dir / "review-plan.json").read_text(encoding="utf-8"))
        inventory = json.loads(
            (self.plan_dir / "source-inventory.json").read_text(encoding="utf-8")
        )
        with self.assertRaisesRegex(ContractError, "execution fragment hash mismatch"):
            _validate_fragment_package(
                fragments,
                plan,
                self.plan_dir / "review-plan.json",
                set(inventory["known_source_ids"]),
                self.r1,
            )

    def test_incomplete_fragment_handoff_is_blocked(self) -> None:
        fragments = make_fragment_package(self.root, self.plan_dir)
        (fragments / "generation-session.json").unlink()
        plan = json.loads((self.plan_dir / "review-plan.json").read_text(encoding="utf-8"))
        inventory = json.loads(
            (self.plan_dir / "source-inventory.json").read_text(encoding="utf-8")
        )
        with self.assertRaisesRegex(ContractError, "canonical fragment validation failed"):
            _validate_fragment_package(
                fragments,
                plan,
                self.plan_dir / "review-plan.json",
                set(inventory["known_source_ids"]),
                self.r1,
            )

    def test_full_assembly_is_deterministic_and_ready(self) -> None:
        fragments = make_fragment_package(self.root, self.plan_dir)
        output = self.root / "assembly"
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "assemble_human_review.py"),
                str(self.plan_dir),
                str(fragments),
                str(output),
                "--r1",
                str(self.r1),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        validation = json.loads((output / "validation.json").read_text(encoding="utf-8"))
        self.assertEqual(validation["verdict"], "ready")
        report = json.loads(
            (output / "human-review-report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(report["report_blueprint"]["fragments"]["items"]), 3)
        self.assertNotIn("slots", report["report_blueprint"]["fragments"])
        self.assertIn(
            "# 小说构思人审报告",
            (output / "human-review-report.md").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
