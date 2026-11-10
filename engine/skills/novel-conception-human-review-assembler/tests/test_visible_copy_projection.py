from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))
import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve()
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_ENGINE = _ENGINE.parent
_sys.path.insert(0, str(_ENGINE))

import copy
import importlib
import unittest


h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)
h1c = importlib.import_module(
    "skills.novel-conception-review-html-generator.scripts.run_v2"
)


def _control(item_id: str, title: str, definition: str) -> dict:
    return {
        "id": item_id,
        "title": title,
        "definition": definition,
        "responsibility": "让人物的选择在这里付出代价。",
        "must_hold": ["人物知道什么与能做什么必须分开。"],
        "must_not_imply": ["情感不能替代人物自己的决定。"],
        "source_ids": ["MACHINE-SOURCE-01"],
    }


def _visual(
    visual_id: str,
    role: str,
    section_id: str,
    kind: str,
    *,
    timeline: bool = False,
) -> dict:
    groups = []
    group_id = None
    temporal_label = None
    node_kind = "人物"
    if timeline:
        group_id = f"{visual_id}-GROUP"
        temporal_label = "第一幕"
        node_kind = "setup"
        groups = [{
            "id": group_id,
            "order": 1,
            "label": "相遇之前",
            "summary": "两个人各自走向同一场危机。",
            "kind": "故事线",
            "lane": "前置线",
            "tier": None,
            "temporal_label": None,
            "source_ids": ["MACHINE-SOURCE-01"],
        }]
    return {
        "id": visual_id,
        "semantic_role": role,
        "section_id": section_id,
        "visual_kind": kind,
        "title": "人物与危机怎样靠近",
        "review_purpose": "看清每一步变化如何把人物推向下一次选择。",
        "groups": groups,
        "nodes": [{
            "id": f"{visual_id}-NODE",
            "order": 1,
            "group_id": group_id,
            "label": "雨夜里的来电",
            "summary": "一通被截断的电话改变了所有人的方向。",
            "kind": node_kind,
            "lane": "前置线" if timeline else None,
            "tier": None,
            "temporal_label": temporal_label,
            "source_ids": ["MACHINE-SOURCE-01"],
        }],
        "edges": [],
        "text_equivalents": [{
            "id": f"{visual_id}-TEXT",
            "order": 1,
            "element_ids": [f"{visual_id}-NODE"],
            "text": "一通来电让秘密实验与现实危机开始相撞。",
            "source_ids": ["MACHINE-SOURCE-01"],
        }],
        "source_ids": ["MACHINE-SOURCE-01"],
        "text_equivalent_module_id": "MOD-HIDDEN-TEXT",
    }


def _report() -> dict:
    world = _control("MOD-WORLD-01", "近未来的秘密实验", "两个国家在危机中有限合作。")
    logic = _control("MOD-WORLD-02", "不能越过的规则", "记忆不是人格，关心也不能替代同意。")
    story = _control(
        "MOD-STORY-01",
        "一个生命想决定自己的去留",
        "一段不该被复活的记忆，唤醒了一个想要自己决定去留的生命。",
    )
    connection = _control(
        "MOD-STORY-02",
        "两条前线在此汇合",
        "顾衡的失踪把沈逾带进秘密基地。",
    )
    rhythm = _control(
        "MOD-STORY-03",
        "危机越急，人物越要诚实",
        "外部危机越来越急，人物却必须慢下来承认彼此。",
    )
    character = _control("MOD-CHAR-01", "沈逾", "她接受任务，却不愿把服从说成赞同。")
    visuals = [
        _visual("VIS-WORLD", "world_environment_map", "SEC-WORLD", "map"),
        _visual("VIS-LOGIC", "control_logic_chain", "SEC-STORY", "flow"),
        _visual("VIS-ARCH", "storyline_architecture", "SEC-STORY", "flow"),
        _visual(
            "VIS-TIME", "major_event_timeline", "SEC-STORY", "timeline",
            timeline=True,
        ),
        _visual("VIS-CHAR", "character_relationship_network", "SEC-CHAR", "network"),
    ]
    return {
        "title": "《断线》构思人审报告",
        "review_scope_contract": {
            "semantic_disclaimer": "这份短报告只帮助你判断故事方向；细节可以随后展开。"
        },
        "review_path": [
            {"id": "PATH-WORLD", "order": 1, "kind": "world", "title": "这是什么故事", "review_question": "你愿意跟随这场相遇吗？", "estimated_seconds": 30, "visible_element_ids": ["MOD-WORLD-01"]},
            {"id": "PATH-STORY", "order": 2, "kind": "storylines", "title": "故事怎样发展", "review_question": "危机是否逼出了真正的选择？", "estimated_seconds": 30, "visible_element_ids": ["MOD-STORY-01"]},
            {"id": "PATH-CHAR", "order": 3, "kind": "characters", "title": "人物害怕什么", "review_question": "他们的愿望和代价是否可信？", "estimated_seconds": 30, "visible_element_ids": ["MOD-CHAR-01"]},
            {"id": "PATH-FRAG", "order": 4, "kind": "fragments", "title": "三个试读场景", "review_question": "声音、距离和温度是否属于这部小说？", "estimated_seconds": 30, "visible_element_ids": ["FRAG-HIDDEN-01"]},
            {"id": "PATH-DECISION", "order": 5, "kind": "decision", "title": "需要你判断的问题", "review_question": "这是不是你想写的故事？", "estimated_seconds": 15, "visible_element_ids": ["PROMPT-HIDDEN-01"]},
        ],
        "visual_models": visuals,
        "world": {
            "definition": world["definition"],
            "operating_logic": logic["definition"],
            "systems": [world, logic],
            "environments": [],
            "event_conditions": [],
            "constraints": [],
            "boundaries": [],
            "source_ids": ["MACHINE-SOURCE-01"],
        },
        "storylines": {
            "story_subject": "一段不该被复活的记忆，唤醒了一个想要自己决定去留的生命。",
            "lines": [story],
            "connections": [connection],
            "major_events": [rhythm],
            "suspense_conflict_rhythm": "外部危机越来越急，人物却必须慢下来承认彼此。",
            "constraints": [],
            "source_ids": ["MACHINE-SOURCE-01"],
        },
        "characters": {
            "core_characters": [character],
            "supporting_characters": [],
            "relationship_networks": [character],
            "role_coverage": [character],
            "constraints": [],
            "source_ids": ["MACHINE-SOURCE-01"],
        },
        "fragments": [{
            "id": "FRAG-HIDDEN-01",
            "title": "雨声里的来电",
            "review_purpose": "顾衡试着留下最后一句完整的话。",
            "text": "雨点砸在铁皮屋顶上，她听见电话那头忽然没了呼吸。",
            "source_ids": ["MACHINE-SOURCE-01"],
            "decision_control_ids": ["DCTRL-HIDDEN-01"],
        }],
        "decision_prompts": [{
            "id": "PROMPT-HIDDEN-01",
            "question": "你愿意让这段关系走到这样的告别吗？",
            "affected_source_ids": ["MACHINE-SOURCE-01"],
            "allowed_decisions": ["approved", "revise", "rejected"],
        }],
    }


class VisibleCopyProjectionTests(unittest.TestCase):
    def _visible_blocks(self, document: str) -> tuple[list[str], list[str]]:
        inspector = h1c._Inspector()
        inspector.feed(document)
        inspector.close()
        return inspector.visible_text, inspector.hidden_text

    def test_markdown_uses_human_titles_without_mutating_machine_report(self) -> None:
        report = _report()
        frozen = copy.deepcopy(report)
        markdown = h1a._render_report_markdown(report)
        self.assertEqual(report, frozen)
        story_heading = markdown.index("## 这是一个怎样的故事")
        method_heading = markdown.index("## 先说在前面")
        reading_heading = markdown.index("## 阅读顺序")
        self.assertLess(story_heading, method_heading)
        self.assertLess(story_heading, reading_heading)
        self.assertNotIn(
            report["visual_models"][1]["text_equivalents"][0]["text"],
            markdown,
        )
        self.assertIn("故事开始时，", markdown)
        self.assertEqual(markdown.count(report["world"]["definition"]), 1)
        self.assertIn("### 近未来的秘密实验", markdown)
        self.assertEqual(markdown.count(report["world"]["definition"]), 1)
        self.assertEqual(markdown.count(report["world"]["operating_logic"]), 1)
        self.assertEqual(markdown.count(report["storylines"]["story_subject"]), 1)
        self.assertNotIn("MOD-WORLD-01", markdown)
        self.assertNotIn("Responsibility", markdown)
        h1a.validate_human_visible_copy(report)

    def test_markdown_renders_every_human_review_collection(self) -> None:
        report = _report()
        environment = _control(
            "MOD-WORLD-ENV-01",
            "隔离会话室",
            "这里承载当前会话，却不给其中的意识任何现实感官。",
        )
        event = _control(
            "MOD-WORLD-EVENT-01",
            "现实团队完成阻断",
            "只有现实中的行动完成，袭击才真正被阻止。",
        )
        supporting = _control(
            "MOD-CHAR-02",
            "许曼青",
            "她能提供任务信息，却不能替沈逾承担选择。",
        )
        relationship = _control(
            "MOD-CHAR-REL-01",
            "沈逾与 R-07",
            "两人只能通过文字靠近，也必须各自保留决定。",
        )
        coverage = _control(
            "MOD-CHAR-COVERAGE-01",
            "关停后的保管人",
            "她只在当前实例结束后接手静态材料。",
        )
        report["world"]["environments"] = [environment]
        report["world"]["event_conditions"] = [event]
        report["world"]["constraints"] = ["记忆不能自动成为人格。"]
        report["world"]["boundaries"] = ["重载是否连续，留给作者决定。"]
        report["characters"]["supporting_characters"] = [supporting]
        report["characters"]["relationship_networks"] = [relationship]
        report["characters"]["role_coverage"] = [coverage]
        report["characters"]["constraints"] = ["任何人都不能替别人同意。"]

        # A summary collection may carry the same sentence as an expanded
        # module. The author should see it once, in the richer module context.
        report["world"]["constraints"].append(environment["definition"])
        report["characters"]["constraints"].append(supporting["definition"])

        markdown = h1a._render_report_markdown(report)

        for item in (environment, event, supporting, relationship, coverage):
            self.assertIn(f"#### {item['title']}", markdown)
            self.assertIn(item["definition"], markdown)
            self.assertIn(item["responsibility"], markdown)
            self.assertNotIn(item["id"], markdown)
        for sentence in (
            "记忆不能自动成为人格。",
            "重载是否连续，留给作者决定。",
            "任何人都不能替别人同意。",
        ):
            self.assertIn(sentence, markdown)
        self.assertEqual(markdown.count(environment["definition"]), 1)
        self.assertEqual(markdown.count(supporting["definition"]), 1)

    def test_network_visual_expands_people_and_relationships(self) -> None:
        report = _report()
        network = report["visual_models"][-1]
        network["text_equivalents"][0]["text"] = "双核心连接三层后果。"
        network["groups"] = [
            {
                "id": "GROUP-CORE",
                "order": 1,
                "label": "故事核心",
                "summary": "R-07 与沈逾共同承担相遇和告别。",
                "kind": "分组",
                "lane": None,
                "tier": "核心",
                "temporal_label": None,
                "source_ids": ["MACHINE-SOURCE-01"],
            }
        ]
        network["nodes"] = [
            {
                **network["nodes"][0],
                "id": "NODE-R07",
                "label": "R-07",
                "group_id": "GROUP-CORE",
            },
            {
                **network["nodes"][0],
                "id": "NODE-SHEN",
                "label": "沈逾",
                "group_id": "GROUP-CORE",
                "order": 2,
            },
        ]
        network["edges"] = [
            {
                "id": "EDGE-R07-SHEN",
                "order": 1,
                "from_node_id": "NODE-R07",
                "to_node_id": "NODE-SHEN",
                "group_id": None,
                "direction": "bidirectional",
                "relation_label": "相遇与告别",
                "summary": "两人在文字交流中靠近，也各自保留最后的决定。",
                "kind": "关系",
                "lane": None,
                "tier": "核心",
                "temporal_label": None,
                "source_ids": ["MACHINE-SOURCE-01"],
            }
        ]

        markdown = h1a._render_report_markdown(report)

        self.assertNotIn("双核心连接三层后果。", markdown)
        self.assertIn("- 故事核心：R-07 与沈逾共同承担相遇和告别。", markdown)
        self.assertNotIn("- R-07：一通被截断的电话改变了所有人的方向。", markdown)
        self.assertIn(
            "- 两人在文字交流中靠近，也各自保留最后的决定。",
            markdown,
        )

    def test_flow_hides_covered_machine_nodes_and_keeps_complete_relation(self) -> None:
        report = _report()
        flow = report["visual_models"][1]
        flow["nodes"] = [
            {
                **flow["nodes"][0],
                "id": "FLOW-NODE-1",
                "order": 1,
                "label": "新生命 / 新关系",
                "summary": "交流生成意识与情感",
            },
            {
                **flow["nodes"][0],
                "id": "FLOW-NODE-2",
                "order": 2,
                "label": "现实闭环",
                "summary": "团队阻断",
            },
        ]
        flow["edges"] = [
            {
                "id": "FLOW-EDGE-1",
                "order": 1,
                "from_node_id": "FLOW-NODE-1",
                "to_node_id": "FLOW-NODE-2",
                "group_id": None,
                "direction": "directed",
                "relation_label": "选择进入行动",
                "summary": "R-07 在交流中形成新的判断，现实团队核验线索后完成阻断。",
                "kind": "流转",
                "lane": None,
                "tier": None,
                "temporal_label": None,
                "source_ids": ["MACHINE-SOURCE-01"],
            }
        ]

        markdown = h1a._render_report_markdown(report)

        self.assertNotIn("新生命 / 新关系", markdown)
        self.assertNotIn("现实闭环", markdown)
        self.assertIn(
            "- R-07 在交流中形成新的判断，现实团队核验线索后完成阻断。",
            markdown,
        )

    def test_map_visual_expands_every_place_and_connection(self) -> None:
        report = _report()
        visual = report["visual_models"][0]
        visual["text_equivalents"][0]["text"] = "几个地方彼此影响。"
        visual["nodes"].append(
            {
                **visual["nodes"][0],
                "id": "VIS-WORLD-NODE-2",
                "order": 2,
                "label": "现实硬件控制室",
                "summary": "人类团队在这里复核线索并操作硬件。",
            }
        )
        visual["edges"] = [
            {
                "id": "VIS-WORLD-EDGE-1",
                "order": 1,
                "from_node_id": "VIS-WORLD-NODE",
                "to_node_id": "VIS-WORLD-NODE-2",
                "group_id": None,
                "direction": "directed",
                "relation_label": "线索进入现实核验",
                "summary": "隔离会话只提供线索，现实团队仍须复核并操作硬件。",
                "kind": "流转",
                "lane": None,
                "tier": None,
                "temporal_label": None,
                "source_ids": ["MACHINE-SOURCE-01"],
            }
        ]

        markdown = h1a._render_report_markdown(report)

        self.assertNotIn("几个地方彼此影响。", markdown)
        self.assertIn(
            "- 现实硬件控制室：人类团队在这里复核线索并操作硬件。",
            markdown,
        )
        self.assertIn(
            "- 从“雨夜里的来电”到“现实硬件控制室”：隔离会话只提供线索，现实团队仍须复核并操作硬件。",
            markdown,
        )

    def test_timeline_preserves_parallel_phase_and_lane_without_machine_kind(self) -> None:
        report = _report()
        timeline = report["visual_models"][3]
        timeline["nodes"][0]["temporal_label"] = "P1"
        timeline["nodes"].append(
            {
                **timeline["nodes"][0],
                "id": "VIS-TIME-NODE-2",
                "order": 2,
                "label": "沈逾入场",
                "summary": "她被推荐进入任务，却还没有作出选择。",
                "kind": "probe",
                "lane": "沈逾",
            }
        )
        timeline["edges"] = [
            {
                "id": "VIS-TIME-EDGE-1",
                "order": 1,
                "from_node_id": "VIS-TIME-NODE",
                "to_node_id": "VIS-TIME-NODE-2",
                "group_id": None,
                "direction": "directed",
                "relation_label": "来电引出任务",
                "summary": "这通电话把沈逾带进了同一场危机。",
                "kind": "时间",
                "lane": None,
                "tier": None,
                "temporal_label": None,
                "source_ids": ["MACHINE-SOURCE-01"],
            }
        ]

        markdown = h1a._render_report_markdown(report)

        self.assertEqual(markdown.count("##### 第一阶段"), 1)
        self.assertIn(
            "- 推进｜雨夜里的来电：一通被截断的电话改变了所有人的方向。"
            "（这一步属于“前置线”。）",
            markdown,
        )
        self.assertIn(
            "- 铺垫｜沈逾进入任务：她被推荐进入任务，却还没有作出选择。"
            "（这一步属于“沈逾线”。）",
            markdown,
        )
        self.assertEqual(markdown.count("这通电话把沈逾带进了同一场危机。"), 1)
        self.assertNotIn("#### 转折怎样接上下一步", markdown)
        self.assertNotIn("沈逾线里", markdown)
        self.assertNotIn("｜铺垫｜", markdown)
        self.assertNotIn("｜探问｜", markdown)
        self.assertNotIn("turning_point", markdown)

    def test_html_keeps_machine_ids_only_in_data_attributes(self) -> None:
        report = _report()
        document = h1c.render_html(report)
        result = h1c.validate_html_document(document, report)
        self.assertEqual(result["verdict"], "ready")
        self.assertIn('data-element-id="MOD-STORY-01"', document)
        self.assertNotIn(">MOD-WORLD-01<", document)
        world_visual = h1c.render_visual(report["visual_models"][0])
        self.assertNotIn('class="small"', world_visual)
        self.assertNotIn("无 · 推进", world_visual)
        self.assertIn('data-kind="人物"', world_visual)

    def test_html_timeline_uses_natural_phase_and_translates_marker_copy(self) -> None:
        report = _report()
        timeline = report["visual_models"][3]
        timeline["nodes"][0].update(
            {
                "label": "危机埋点",
                "kind": "setup",
                "temporal_label": "第一阶段",
            }
        )
        timeline["nodes"].append(
            {
                **timeline["nodes"][0],
                "id": "VIS-TIME-NODE-2",
                "order": 2,
                "label": "生命探针",
                "kind": "probe",
            }
        )

        document = h1c.render_html(report)
        visible, hidden = self._visible_blocks(document)
        reader_copy = "\n".join(visible)

        self.assertEqual(hidden, [])
        self.assertIn("危机伏笔", reader_copy)
        self.assertIn("R-07 的新意识显现", reader_copy)
        self.assertIn("第一阶段 · 铺垫", reader_copy)
        self.assertIn("第一阶段 · 探问", reader_copy)
        self.assertNotIn("P1", reader_copy)
        self.assertNotIn("埋点", reader_copy)
        self.assertNotIn("探针", reader_copy)
        self.assertNotIn(">节点</li>", document)
        self.assertIn('data-kind="setup"', document)
        self.assertIn('data-kind="probe"', document)
        h1c.validate_html_document(document, report)

        legacy = copy.deepcopy(report)
        legacy["visual_models"][3]["nodes"][0]["kind"] = "节点"
        legacy["visual_models"][3]["nodes"][0]["label"] = "旧版节点"
        legacy_document = h1c.render_html(legacy)
        self.assertIn("第一阶段 · 推进", legacy_document)
        self.assertIn('class="node marker-control-node"', legacy_document)
        self.assertIn('data-kind="节点"', legacy_document)
        self.assertNotIn(">节点</li>", legacy_document)
        h1c.validate_html_document(legacy_document, legacy)

        leaked = document.replace(
            "第一阶段 · 铺垫", "P<em>1</em> · 探针", 1
        )
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_VISIBLE_COPY_INVALID"
        ):
            h1c.validate_html_document(leaked, report)

        timeline["nodes"][0]["kind"] = "unknown_kind"
        with self.assertRaisesRegex(
            h1c.H1CError, "unknown timeline marker kinds"
        ):
            h1c.render_html(report)

    def test_html_timeline_uses_accepted_story_role_over_stale_raw_kind(
        self,
    ) -> None:
        report = _report()
        timeline = report["visual_models"][3]
        base = timeline["nodes"][0]
        timeline["nodes"] = [
            {
                **base,
                "id": "VIS-TIME-NODE-PROBE",
                "order": 1,
                "label": "生命探针",
                "kind": "climax",
                "temporal_label": "P3",
            },
            {
                **base,
                "id": "VIS-TIME-NODE-OUTER-CLIMAX",
                "order": 2,
                "label": "外部高潮",
                "kind": "节点",
                "temporal_label": "P7",
            },
            {
                **base,
                "id": "VIS-TIME-NODE-EMOTIONAL-CLIMAX",
                "order": 3,
                "label": "情感高潮",
                "kind": "control-node",
                "temporal_label": "P8",
            },
        ]
        timeline["edges"] = []

        document = h1c.render_html(report)
        visible, hidden = self._visible_blocks(document)
        reader_copy = "\n".join(visible)

        self.assertEqual(hidden, [])
        self.assertIn("第三阶段 · 探问", reader_copy)
        self.assertIn("第七阶段 · 高潮", reader_copy)
        self.assertIn("第八阶段 · 高潮", reader_copy)
        self.assertNotIn("第三阶段 · 高潮", reader_copy)
        self.assertNotIn("第七阶段 · 推进", reader_copy)
        self.assertNotIn("第八阶段 · 推进", reader_copy)
        self.assertIn('class="node marker-probe"', document)
        self.assertEqual(document.count('class="node marker-climax"'), 2)
        self.assertIn('data-kind="climax"', document)
        self.assertIn('data-kind="节点"', document)
        self.assertIn('data-kind="control-node"', document)
        h1c.validate_html_document(document, report)

    def test_html_replaces_compressed_visual_memo_with_specific_prose(
        self,
    ) -> None:
        report = _report()
        network = report["visual_models"][-1]
        network["text_equivalents"][0]["text"] = "双核心连接三层后果。"
        network["groups"] = [
            {
                "id": "GROUP-CORE",
                "order": 1,
                "label": "故事核心",
                "summary": "R-07 与沈逾共同承担相遇和告别。",
                "kind": "分组",
                "lane": None,
                "tier": "核心",
                "temporal_label": None,
                "source_ids": ["MACHINE-SOURCE-01"],
            }
        ]
        network["nodes"][0]["group_id"] = "GROUP-CORE"
        network["edges"] = [
            {
                "id": "EDGE-CORE",
                "order": 1,
                "from_node_id": network["nodes"][0]["id"],
                "to_node_id": network["nodes"][0]["id"],
                "group_id": "GROUP-CORE",
                "direction": "bidirectional",
                "relation_label": "相遇与告别",
                "summary": "两人在文字交流中靠近，也各自保留最后的决定。",
                "kind": "关系",
                "lane": None,
                "tier": "核心",
                "temporal_label": None,
                "source_ids": ["MACHINE-SOURCE-01"],
            }
        ]

        document = h1c.render_html(report)

        self.assertNotIn("双核心连接三层后果。", document)
        self.assertIn("R-07 与沈逾共同承担相遇和告别。", document)
        self.assertIn("两人在文字交流中靠近，也各自保留最后的决定。", document)
        self.assertIn("不用看图，也可以这样理解", document)
        h1c.validate_html_document(document, report)

        caption = h1c._visual_prose_caption(network)
        slogan_caption = caption.replace(
            "两人在文字交流中靠近，也各自保留最后的决定。",
            "双核心连接三层后果。",
        )
        mutant = document.replace(caption, slogan_caption, 1)
        with self.assertRaisesRegex(
            h1c.H1CError, "natural prose fallback drift"
        ):
            h1c.validate_html_document(mutant, report)

    def test_bad_reader_copy_fails(self) -> None:
        for bad in (
            "MOD-WORLD-01",
            "DCTRL-STORY-01",
            "ENV-001",
            "SL-GUHENG-LIVING",
            "SLC-MAIN-THREAT",
            "SLOT-PERMIT-CUSTODIAN",
            "ACTOR-CONTRACT-H1",
            "TOKEN-STARTUP-01",
            "[DEMAND:CHD-001:" + "a" * 64 + "]职责[/DEMAND]",
            "NOT_STARTED",
            "UNCONSUMED",
            "a" * 64,
            "Review scope",
            "Responsibility",
            "Allowed",
            "《《断线》》",
            "这是一段评审用途说明",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(h1a.H1AError) as caught:
                    h1a.validate_human_visible_strings([bad])
                self.assertEqual(caught.exception.code, "H1A_VISIBLE_COPY_INVALID")

    def test_natural_chinese_and_story_name_are_not_false_positives(self) -> None:
        h1a.validate_human_visible_strings([
            "这份结论可核验，也保留来源材料供作者继续阅读。",
            "R-07 在沈逾面前提出了自己的请求。",
            "许可保管岗签发单次令牌，载体操作岗收到后才执行唯一启动。",
        ])

    def test_report_visible_fields_reject_internal_copy(self) -> None:
        mutations = (
            ("decision control", lambda report: report.__setitem__("decision_controls", [{"statement": "按 ENV-001 执行。", "must_hold": ["人物自己选择。"], "must_not_imply": ["不得替人物选择。"]}])),
            ("visual node", lambda report: report["visual_models"][0]["nodes"][0].__setitem__("label", "ENV-001")),
            ("visual group kind", lambda report: report["visual_models"][3]["groups"][0].__setitem__("kind", "ENV-001")),
            ("visual lane", lambda report: report["visual_models"][0]["nodes"][0].__setitem__("lane", "SL-MAIN")),
            ("character responsibility", lambda report: report["characters"]["core_characters"][0].__setitem__("responsibility", "[DEMAND:CHD-001:" + "b" * 64 + "]职责[/DEMAND]")),
            ("story definition", lambda report: report["storylines"]["lines"][0].__setitem__("definition", "状态从 NOT_STARTED 进入 ACTIVE。")),
            ("fragment purpose", lambda report: report["fragments"][0].__setitem__("review_purpose", "检查 SLOT-PERMIT-CUSTODIAN。")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                report = _report()
                mutate(report)
                with self.assertRaises(h1a.H1AError) as caught:
                    h1a.validate_human_visible_copy(report)
                self.assertEqual(caught.exception.code, "H1A_VISIBLE_COPY_INVALID")

    def test_plan_brief_and_visual_fields_use_the_same_lint(self) -> None:
        plan = {
            "review_scope_contract": {"semantic_disclaimer": "作者阅读正文。"},
            "decision_controls": [],
            "review_path": [],
            "sections": [],
            "visual_models": [{
                "title": "环境流转",
                "review_purpose": "查看人物如何移动。",
                "groups": [],
                "nodes": [{
                    "label": "ENV-001", "summary": "采样室。", "kind": "环境",
                    "lane": None, "tier": None, "temporal_label": None,
                }],
                "edges": [],
                "text_equivalents": [],
            }],
            "fragment_briefs": [{
                "title": "启动之前",
                "review_purpose": "确认选择边界。",
                "information_limits": {
                    "may_present": ["SLOT-PERMIT-CUSTODIAN"],
                    "must_not_present_as_known": ["未发生的决定"],
                },
                "allowed_perception_channels": ["监护屏"],
                "scene_contract": {
                    "before_state": "许可尚未生效。",
                    "immediate_goal": "确认授权。",
                    "pressure": "窗口收紧。",
                    "obstacle": "四栏必须分别成立。",
                    "required_choice": "只签自己的意见。",
                    "direct_consequence": "采样窗口打开。",
                    "after_state": "证据只读封存。",
                },
                "required_demonstrations": ["顾衡仍活着。"],
                "forbidden_additions": ["不得写成死亡。"],
            }],
            "decision_prompts": [],
        }
        with self.assertRaises(h1a.H1AError) as caught:
            h1a.validate_human_visible_strings(h1a._human_visible_plan_strings(plan))
        self.assertEqual(caught.exception.code, "H1A_VISIBLE_COPY_INVALID")

    def test_plan_title_and_visual_group_kind_are_visible_copy(self) -> None:
        base = {
            "work_identity": {
                "work_title": "断线",
                "report_title": "《断线》构思人审报告",
            },
            "review_scope_contract": {"semantic_disclaimer": "作者阅读正文。"},
            "decision_controls": [],
            "review_path": [],
            "sections": [],
            "visual_models": [{
                "title": "故事走向",
                "review_purpose": "查看变化。",
                "groups": [{
                    "label": "相遇之前",
                    "summary": "两个人走向同一场危机。",
                    "kind": "故事线",
                    "lane": None,
                    "tier": None,
                    "temporal_label": None,
                }],
                "nodes": [],
                "edges": [],
                "text_equivalents": [],
            }],
            "fragment_briefs": [],
            "decision_prompts": [],
        }
        mutations = (
            ("work title", lambda plan: plan["work_identity"].__setitem__("work_title", "ENV-001")),
            ("report title", lambda plan: plan["work_identity"].__setitem__("report_title", "《ENV-001》构思人审报告")),
            ("group kind", lambda plan: plan["visual_models"][0]["groups"][0].__setitem__("kind", "ENV-001")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                plan = copy.deepcopy(base)
                mutate(plan)
                values = h1a._human_visible_plan_strings(plan)
                self.assertTrue(any("ENV-001" in value for value in values))
                with self.assertRaises(h1a.H1AError) as caught:
                    h1a.validate_human_visible_strings(values)
                self.assertEqual(
                    caught.exception.code, "H1A_VISIBLE_COPY_INVALID"
                )

    def test_h1c_rejects_internal_visual_group_kind_before_dom_checks(self) -> None:
        report = _report()
        report["visual_models"][3]["groups"][0]["kind"] = "ENV-001"
        with self.assertRaises(h1a.H1AError) as caught:
            h1c.validate_html_document("", report)
        self.assertEqual(caught.exception.code, "H1A_VISIBLE_COPY_INVALID")

    def test_escaped_script_text_is_visible_prose_not_active_content(self) -> None:
        report = _report()
        report["fragments"][0]["text"] = (
            "她在纸上写下<script>只是字样</script>，纸面没有执行任何命令。"
        )
        document = h1c.render_html(report)
        self.assertIn("&lt;script&gt;", document)
        h1c.validate_html_document(document, report)

    def test_html_visible_flow_joins_inline_text_before_lint(self) -> None:
        mutations = (
            "Responsi<em>bility</em>",
            "Res<strong>pon<em>si</em></strong>bility",
            "Respons&#105;<span>bility</span>",
            "Re<span>sp</span><b>on</b><i>si</i>bility",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                visible, hidden = self._visible_blocks(
                    f"<body><p>{mutation}</p></body>"
                )
                self.assertEqual(hidden, [])
                with self.assertRaises(h1a.H1AError) as caught:
                    h1a.validate_human_visible_strings(visible)
                self.assertEqual(
                    caught.exception.code, "H1A_VISIBLE_COPY_INVALID"
                )

    def test_html_visible_flow_keeps_adjacent_blocks_separate(self) -> None:
        visible, hidden = self._visible_blocks(
            "<body><p>Responsi</p><p>bility</p></body>"
        )
        self.assertEqual(visible, ["Responsi", "bility"])
        self.assertEqual(hidden, [])
        h1a.validate_human_visible_strings(visible)

    def test_html_visibility_controls_fail_closed(self) -> None:
        report = _report()
        document = h1c.render_html(report)
        hidden_text = document.replace(
            '<span aria-hidden="true"></span>',
            '<span aria-hidden="true">Responsibility</span>',
            1,
        )
        with self.assertRaisesRegex(h1c.H1CError, "hidden content"):
            h1c.validate_html_document(hidden_text, report)
        hidden_attribute = document.replace(
            "</footer>", "<span hidden>Responsibility</span></footer>", 1
        )
        with self.assertRaisesRegex(h1c.H1CError, "hidden content"):
            h1c.validate_html_document(hidden_attribute, report)
        invalid_aria = document.replace(
            'aria-hidden="true"', 'aria-hidden="sometimes"', 1
        )
        with self.assertRaisesRegex(h1c.H1CError, "invalid aria-hidden"):
            h1c.validate_html_document(invalid_aria, report)

    def test_nonvisible_containers_cannot_extend_the_reader_surface(self) -> None:
        report = _report()
        document = h1c.render_html(report)
        for tag in ("template", "noscript"):
            with self.subTest(tag=tag):
                mutation = document.replace(
                    "</footer>",
                    f"<{tag}>Responsibility</{tag}></footer>",
                    1,
                )
                with self.assertRaisesRegex(h1c.H1CError, "forbidden active element"):
                    h1c.validate_html_document(mutation, report)

    def test_work_title_is_plain_and_author_title_is_explicit(self) -> None:
        gate = {"path": "gate.json", "sha256": "a" * 64}
        identity = h1a._work_identity("断线", gate)
        self.assertEqual(identity["report_title"], "《断线》构思人审报告")
        with self.assertRaises(h1a.H1AError):
            h1a._work_identity("《断线》构想人审包", gate)


if __name__ == "__main__":
    unittest.main()
