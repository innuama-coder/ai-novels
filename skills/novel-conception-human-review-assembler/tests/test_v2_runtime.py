import importlib
import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


h1a = importlib.import_module(
    "skills.novel-conception-human-review-assembler.scripts.run_v2"
)


class _Coordinator:
    def __init__(self):
        self.calls = []

    def accept_h1_workspace_transition(self, **kwargs):
        self.calls.append(kwargs)
        return {"state": kwargs["expected_next_state"]}


class H1APlanSkeletonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.runtime = h1a.rt.ContractRuntime()
        self.p1_completion = {
            "stage": "P1",
            "path": "P1/stage-completion.json",
            "sha256": "1" * 64,
        }
        self.workspace_data = {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "stage": "H1",
            "session_id": "H1-SESSION-1",
            "state": "initialized",
            "p1_completion": self.p1_completion,
            "previous_state_sha256": None,
            "artifacts": {},
        }
        self.workspace = h1a.rt.SealedDocument(
            data=self.workspace_data,
            reference={
                "path": "H1/h1-workspace-state.json",
                "sha256": h1a.rt.canonical_sha256(self.workspace_data),
            },
        )

    def tearDown(self):
        self.temporary.cleanup()

    def test_plan_requires_exact_initialized_workspace(self):
        result = h1a.validate_plan_workspace(
            self.workspace,
            p1_completion=self.p1_completion,
            runtime=self.runtime,
        )
        self.assertEqual(result["state"], "initialized")

    def test_plan_rejects_planned_workspace(self):
        data = dict(self.workspace_data, state="planned")
        workspace = h1a.rt.SealedDocument(
            data=data,
            reference={
                "path": "H1/h1-workspace-state.json",
                "sha256": h1a.rt.canonical_sha256(data),
            },
        )
        with self.assertRaisesRegex(h1a.H1AError, "H1A_WORKSPACE_INVALID"):
            h1a.validate_plan_workspace(
                workspace,
                p1_completion=self.p1_completion,
                runtime=self.runtime,
            )

    def test_controlled_identity_cannot_be_caller_forged(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                h1a.H1AError, "H1A_CONTROLLED_CONTEXT_REQUIRED"
            ):
                h1a._identity()
        with mock.patch.dict(
            os.environ,
            {"CODEX_TASK_ID": "task-1", "CODEX_THREAD_ID": "thread-1"},
            clear=True,
        ):
            self.assertEqual(
                h1a._identity(),
                {"task_id": "task-1", "thread_id": "thread-1"},
            )

    def test_plan_requires_exact_five_phase_order(self):
        phases = [
            {"phase": phase, "phase_index": index, "payload": {"ok": True}}
            for index, phase in enumerate(h1a.PLAN_PHASES, 1)
        ]
        self.assertEqual(len(h1a.validate_plan_phases(phases)), 5)
        phases[1]["phase"], phases[2]["phase"] = (
            phases[2]["phase"],
            phases[1]["phase"],
        )
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_PLAN_PHASE_ORDER_INVALID"
        ):
            h1a.validate_plan_phases(phases)

    def test_source_inventory_is_deterministic_and_story_only(self):
        p1 = self.root / "P1"
        baseline = {
            "run_id": "RUN-1",
            "control_registry": [{"id": "INT-1", "value": "locked"}],
        }
        model = {"run_id": "RUN-1", "objects": [{"id": "SL-1"}]}
        self._write(p1 / "author-control-baseline.json", baseline)
        refs = {}
        for stage in ("S1", "W1", "E1", "T1", "C1"):
            path = p1 / f"{stage}.json"
            self._write(path, dict(model, stage=stage))
            refs[stage] = h1a.rt.artifact_reference(path, root=p1)
        self._write(
            p1 / "novel-conception-package.json",
            {
                "run_id": "RUN-1",
                "author_control_baseline": h1a.rt.artifact_reference(
                    p1 / "author-control-baseline.json", root=p1
                ),
                "canonical_models": refs,
            },
        )
        first = h1a.build_source_inventory(
            p1, p1_completion=self.p1_completion
        )
        second = h1a.build_source_inventory(
            p1, p1_completion=self.p1_completion
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first["anchors"]), 6)
        self.assertNotIn(
            "RUN-1", {item["source_id"] for item in first["anchors"]}
        )

    def _write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            h1a.rt.canonical_json(value), encoding="utf-8", newline=""
        )

    def _formal_inputs(self):
        p1 = self.root / "formal-P1"
        models = {
            "S1": {"objects": [{"id": "SLC-1"}]},
            "W1": {"objects": [{"id": "WR-1"}]},
            "E1": {"objects": [{"id": "ENV-1"}]},
            "T1": {"objects": [{"id": "EV-1"}]},
            "C1": {"objects": [{"id": "CHR-1"}]},
        }
        baseline = {"control_registry": [{"id": "INT-1"}]}
        self._write(p1 / "author-control-baseline.json", baseline)
        model_refs = {}
        for stage, model in models.items():
            self._write(p1 / f"{stage}.json", model)
            model_refs[stage] = h1a.rt.artifact_reference(
                p1 / f"{stage}.json", root=p1
            )
        self._write(
            p1 / "novel-conception-package.json",
            {
                "run_id": "RUN-1",
                "author_control_baseline": h1a.rt.artifact_reference(
                    p1 / "author-control-baseline.json", root=p1
                ),
                "canonical_models": model_refs,
            },
        )
        self._write(
            p1 / "stage-completion.json",
            {
                "run_id": "RUN-1",
                "stage": "P1",
                "status": "ready",
            },
        )
        p1_ref = {
            "stage": "P1",
            "path": "P1/stage-completion.json",
            "sha256": h1a.rt.sha256_file(
                p1 / "stage-completion.json"
            ),
        }
        workspace_data = {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "stage": "H1",
            "session_id": "H1-SESSION-1",
            "state": "initialized",
            "p1_completion": p1_ref,
            "previous_state_sha256": None,
            "artifacts": {},
        }
        workspace = h1a.rt.SealedDocument(
            data=workspace_data,
            reference={
                "path": "H1/h1-workspace-state.json",
                "sha256": h1a.rt.canonical_sha256(workspace_data),
            },
        )
        gate_data = {
            "schema_version": "2.0",
            "run_id": "RUN-1",
            "target_stage": "H1",
            "entry_mode": "forward",
            "run_state": {
                "path": "state/revision-009.json",
                "sha256": "9" * 64,
            },
            "baseline_completion": {
                "stage": "B0",
                "path": "B0/stage-completion.json",
                "sha256": "0" * 64,
            },
            "upstream_completions": [p1_ref],
            "active_return": None,
            "return_binding": None,
        }
        gate = h1a.rt.SealedDocument(
            data=gate_data,
            reference={
                "path": "H1/input-gate.json",
                "sha256": h1a.rt.canonical_sha256(gate_data),
            },
        )
        inventory = h1a.build_source_inventory(
            p1,
            p1_completion={
                "path": p1_ref["path"],
                "sha256": p1_ref["sha256"],
            },
        )
        plan = self._plan(inventory, p1_ref, gate.reference)
        phases = [
            {
                "phase": h1a.PLAN_PHASES[0],
                "phase_index": 1,
                "payload": {
                    "review_requirements": plan["review_requirements"],
                    "risk_register": plan["risk_register"],
                },
            },
            {
                "phase": h1a.PLAN_PHASES[1],
                "phase_index": 2,
                "payload": {
                    "review_path": plan["review_path"],
                    "sections": plan["sections"],
                    "review_scope_contract": plan[
                        "review_scope_contract"
                    ],
                    "decision_controls": plan["decision_controls"],
                    "reduction_ledger": plan["reduction_ledger"],
                    "drilldown_index": plan["drilldown_index"],
                },
            },
            {
                "phase": h1a.PLAN_PHASES[2],
                "phase_index": 3,
                "payload": {
                    "visual_models": plan["visual_models"],
                    "fragment_briefs": plan["fragment_briefs"],
                    "decision_prompts": plan["decision_prompts"],
                    "assembly_projection": plan["assembly_projection"],
                    "presentation_bindings": plan[
                        "presentation_bindings"
                    ],
                },
            },
            {
                "phase": h1a.PLAN_PHASES[3],
                "phase_index": 4,
                "payload": {
                    "reading_profile": plan["reading_profile"],
                    "budget_items": plan["budget_items"],
                    "budget_total_seconds": sum(
                        item["estimated_seconds"]
                        for item in plan["budget_items"]
                    ),
                },
            },
            {
                "phase": h1a.PLAN_PHASES[4],
                "phase_index": 5,
                "payload": {
                    "review_plan": plan,
                    "final_checks": {
                        "three_boards": True,
                        "all_source_anchors_covered": True,
                        "budget_within_600": True,
                        "fragments_non_authoritative": True,
                        "decision_unselected": True,
                    },
                },
            },
        ]
        return p1, workspace, gate, phases

    def _plan(self, inventory, p1_ref, input_gate_ref):
        anchor_ids = [item["id"] for item in inventory["anchors"]]
        sections = []
        for kind in h1a.SECTION_KINDS:
            modules = [
                {
                    "id": f"MOD-{kind.upper()}-{index}",
                    "title": f"{kind} {index}",
                    "display_kind": "cards",
                    "definition": f"{kind} definition {index}",
                    "responsibility": f"说明 {kind} {index} 在故事中的作用",
                    "must_hold": ["P1 values remain exact"],
                    "must_not_imply": ["No new authority"],
                    "source_anchor_ids": anchor_ids,
                    "default_visible": True,
                }
                for index in range(1, 4)
            ]
            if kind == "world":
                modules[1]["definition"] = (
                    "这个主要环境有明确地点与叙事作用；可见特征、可用物件、"
                    "进入限制和风险共同推动故事，让人物每次进入都面对清楚的选择压力与代价。"
                )
            sections.append(
                {
                    "id": f"SEC-{kind.upper()}",
                    "kind": kind,
                    "title": kind,
                    "review_goal": f"judge {kind}",
                    "modules": modules,
                }
            )
        path_kinds = h1a.REVIEW_PATH_KINDS
        visible = [
            [
                "MOD-WORLD-1",
                "MOD-WORLD-2",
                "MOD-WORLD-3",
                "VIS-1",
            ],
            [
                "MOD-STORYLINES-1",
                "MOD-STORYLINES-2",
                "MOD-STORYLINES-3",
                "VIS-2",
                "VIS-3",
                "VIS-4",
            ],
            [
                "MOD-CHARACTERS-1",
                "MOD-CHARACTERS-2",
                "MOD-CHARACTERS-3",
                "VIS-5",
            ],
            ["FRAG-1", "FRAG-2", "FRAG-3"],
            ["PROMPT-1"],
        ]
        path_seconds = [80, 80, 80, 220, 80]
        review_path = [
            {
                "id": f"PATH-{index}",
                "order": index,
                "kind": kind,
                "title": kind,
                "review_question": f"Does {kind} match?",
                "estimated_seconds": seconds,
                "visible_element_ids": element,
            }
            for index, (kind, element, seconds) in enumerate(
                zip(path_kinds, visible, path_seconds), 1
            )
        ]
        section_by_kind = {section["kind"]: section for section in sections}

        def graph_element(
            element_id,
            order,
            *,
            label,
            kind,
            group_id=None,
            lane=None,
            temporal_label=None,
        ):
            return {
                "id": element_id,
                "order": order,
                "group_id": group_id,
                "label": label,
                "summary": f"{label} summary",
                "kind": kind,
                "lane": lane,
                "tier": None,
                "temporal_label": temporal_label,
                "source_anchor_ids": anchor_ids,
            }

        def visual(
            index,
            semantic_role,
            section_kind,
            visual_kind,
            *,
            node_count=1,
            with_edge=False,
            timeline=False,
        ):
            prefix = str(index)
            groups = []
            group_id = None
            lane = None
            if timeline:
                group_id = f"GRP-{prefix}-1"
                lane = "primary"
                groups = [
                    {
                        "id": group_id,
                        "order": 1,
                        "label": "Primary lane",
                        "summary": "Primary event lane",
                        "kind": "event-lane",
                        "lane": lane,
                        "tier": None,
                        "temporal_label": "ordered",
                        "source_anchor_ids": anchor_ids,
                    }
                ]
            nodes = [
                graph_element(
                    f"NODE-{prefix}-{node_index}",
                    node_index,
                    label=f"{semantic_role} node {node_index}",
                    kind="control-node",
                    group_id=group_id,
                    lane=lane,
                    temporal_label=(
                        f"T{node_index}" if timeline else None
                    ),
                )
                for node_index in range(1, node_count + 1)
            ]
            edges = []
            if with_edge:
                edges = [
                    {
                        "id": f"EDGE-{prefix}-1",
                        "order": 1,
                        "group_id": group_id,
                        "from_node_id": nodes[0]["id"],
                        "to_node_id": nodes[1]["id"],
                        "direction": "directed",
                        "relation_label": "leads to",
                        "summary": "The first control leads to the second",
                        "kind": "causal-link",
                        "lane": lane,
                        "tier": None,
                        "temporal_label": (
                            "T1-T2" if timeline else None
                        ),
                        "source_anchor_ids": anchor_ids,
                    }
                ]
            elements = [*groups, *nodes, *edges]
            section = section_by_kind[section_kind]
            return {
                "id": f"VIS-{index}",
                "semantic_role": semantic_role,
                "section_id": section["id"],
                "visual_kind": visual_kind,
                "title": f"{semantic_role} visual",
                "review_purpose": f"Review {semantic_role}",
                "groups": groups,
                "nodes": nodes,
                "edges": edges,
                "text_equivalents": [
                    {
                        "id": f"TXT-{prefix}-1",
                        "order": 1,
                        "element_ids": [
                            element["id"] for element in elements
                        ],
                        "text": f"{semantic_role} text equivalent",
                        "source_anchor_ids": anchor_ids,
                    }
                ],
                "source_anchor_ids": anchor_ids,
                "text_equivalent_module_id": section["modules"][0]["id"],
            }

        visuals = [
            visual(
                1,
                "world_environment_map",
                "world",
                "map",
            ),
            visual(
                2,
                "control_logic_chain",
                "storylines",
                "flow",
                node_count=2,
                with_edge=True,
            ),
            visual(
                3,
                "storyline_architecture",
                "storylines",
                "flow",
            ),
            visual(
                4,
                "major_event_timeline",
                "storylines",
                "timeline",
                node_count=2,
                with_edge=True,
                timeline=True,
            ),
            visual(
                5,
                "character_relationship_network",
                "characters",
                "network",
            ),
        ]
        briefs = [
            {
                "id": f"BRIEF-{index}",
                "slot_id": f"FRAG-{index}",
                "title": f"fragment {index}",
                "review_purpose": "test reading experience",
                "pov_character_id": "CHR-1",
                "language_contract_id": "zh-Hans-review-v1",
                "style_contract_id": "restrained-concrete-scene-v1",
                "depth_contract_id": "character-grounded-scene-v1",
                "pov_mode": "third_person_limited",
                "information_limits": {
                    "may_present": [
                        "POV可感知、回忆、推断或误解的信息"
                    ],
                    "must_not_present_as_known": [
                        "未向POV角色开放的信息"
                    ],
                },
                "allowed_perception_channels": ["视觉", "听觉"],
                "scene_contract": {
                    "before_state": "选择尚未发生",
                    "immediate_goal": "处理眼前压力",
                    "pressure": "时间与责任同时收紧",
                    "obstacle": "行动受到现实条件限制",
                    "required_choice": "POV角色必须主动选择",
                    "direct_consequence": "选择在片段内产生后果",
                    "after_state": "责任或关系已经改变",
                },
                "decisive_interiority_policy": (
                    "process-only-no-unresolved-decision-disclosure"
                ),
                "surface_detail_policy": (
                    "fragment-local-non-authoritative-v1"
                ),
                "decision_control_ids": ["DCTRL-FRAGMENTS"],
                "source_anchor_ids": anchor_ids,
                "required_demonstrations": ["Show bounded P1 behavior"],
                "forbidden_additions": ["No new facts"],
                "target_words_min": 320,
                "target_words_max": 480,
            }
            for index in range(1, 4)
        ]
        artifact_ref = {"path": p1_ref["path"], "sha256": p1_ref["sha256"]}
        plan = {
            "schema_version": "2.0",
            "skill": "novel-conception-human-review-assembler",
            "run_id": "RUN-1",
            "h1_session_id": "H1-SESSION-1",
            "p1_completion": artifact_ref,
            "work_identity": h1a._work_identity(
                "测试作品", input_gate_ref
            ),
            "reading_budget_minutes": 10,
            "reading_profile": "review-reading-baseline-v1",
            "review_requirements": [
                "judge world",
                "judge storylines",
                "judge characters",
                "judge fragments",
                "record decision",
            ],
            "review_scope_contract": {
                "contract_id": "bounded-decision-controls-v1",
                "default_path_scope": "complete-decision-control-surface",
                "full_evidence_mode": "expandable-lossless-p1",
                "semantic_disclaimer": (
                    "Source binding proves provenance, not semantic equivalence."
                ),
            },
            "decision_controls": [
                {
                    "id": "DCTRL-WORLD",
                    "domain": "world",
                    "priority": "critical",
                    "statement": "The world controls the available choices.",
                    "must_hold": ["World constraints remain reviewable."],
                    "must_not_imply": ["Every P1 detail is visible by default."],
                    "default_element_ids": ["MOD-WORLD-1"],
                },
                {
                    "id": "DCTRL-STORYLINES",
                    "domain": "storylines",
                    "priority": "critical",
                    "statement": "Story causality remains reviewable.",
                    "must_hold": ["Connections and consequences remain explicit."],
                    "must_not_imply": ["Evidence is replaced by this control."],
                    "default_element_ids": ["MOD-STORYLINES-1"],
                },
                {
                    "id": "DCTRL-CHARACTERS",
                    "domain": "characters",
                    "priority": "critical",
                    "statement": "Character agency remains reviewable.",
                    "must_hold": ["Relationships and choices remain explicit."],
                    "must_not_imply": ["Supporting detail was discarded."],
                    "default_element_ids": ["MOD-CHARACTERS-1"],
                },
                {
                    "id": "DCTRL-FRAGMENTS",
                    "domain": "fragments",
                    "priority": "structural",
                    "statement": "Fragments test the intended reading experience.",
                    "must_hold": ["Fragments remain non-authoritative evidence."],
                    "must_not_imply": ["Fragments add conception facts."],
                    "default_element_ids": ["FRAG-1"],
                },
            ],
            "risk_register": [
                {
                    "id": "RISK-1",
                    "risk": "compression drift",
                    "mitigation": "bind P1 anchors",
                    "source_anchor_ids": anchor_ids,
                }
            ],
            "review_path": review_path,
            "sections": sections,
            "visual_models": visuals,
            "fragment_briefs": briefs,
            "assembly_projection": {
                "world": {
                    "definition_module_id": "MOD-WORLD-1",
                    "operating_logic_module_id": "MOD-WORLD-2",
                    "system_module_ids": ["MOD-WORLD-1"],
                    "environment_module_ids": ["MOD-WORLD-2"],
                    "event_condition_module_ids": ["MOD-WORLD-3"],
                    "constraint_module_ids": ["MOD-WORLD-1"],
                    "boundary_module_ids": ["MOD-WORLD-3"],
                },
                "storylines": {
                    "story_subject_module_id": "MOD-STORYLINES-1",
                    "line_module_ids": ["MOD-STORYLINES-1"],
                    "connection_module_ids": ["MOD-STORYLINES-2"],
                    "major_event_module_ids": ["MOD-STORYLINES-3"],
                    "suspense_conflict_rhythm_module_id": "MOD-STORYLINES-2",
                    "constraint_module_ids": ["MOD-STORYLINES-1"],
                },
                "characters": {
                    "core_character_module_ids": ["MOD-CHARACTERS-1"],
                    "supporting_character_module_ids": [],
                    "relationship_network_module_ids": [
                        "MOD-CHARACTERS-2"
                    ],
                    "role_coverage_module_ids": ["MOD-CHARACTERS-3"],
                    "constraint_module_ids": ["MOD-CHARACTERS-1"],
                },
            },
            "decision_prompts": [
                {
                    "id": "PROMPT-1",
                    "question": "Is this the intended conception?",
                    "affected_source_anchor_ids": anchor_ids,
                    "allowed_decisions": [
                        "approved",
                        "revise",
                        "rejected",
                    ],
                    "preselected": False,
                }
            ],
            "budget_items": [
                {
                    "element_id": f"PATH-{index}",
                    "estimated_seconds": seconds,
                }
                for index, seconds in enumerate(path_seconds, 1)
            ],
            "control_coverage": [
                {
                    "source_anchor_id": anchor,
                    "visible_element_ids": [
                        (
                            [
                                "MOD-WORLD-1",
                                "MOD-STORYLINES-1",
                                "MOD-CHARACTERS-1",
                                "FRAG-1",
                            ][index]
                            if index < 4
                            else f"EVID-{index + 1}"
                        )
                    ],
                }
                for index, anchor in enumerate(anchor_ids)
            ],
            "reduction_ledger": [
                {
                    "source_anchor_id": anchor,
                    "decision_control_ids": [[
                        "DCTRL-WORLD",
                        "DCTRL-STORYLINES",
                        "DCTRL-CHARACTERS",
                        "DCTRL-FRAGMENTS",
                    ][index % 4]],
                    "relation": "supports",
                    "review_priority": "critical" if index < 4 else "supporting",
                    "exposure": (
                        "default-and-drilldown" if index < 4 else "drilldown-only"
                    ),
                    "rationale": "Preserves the source distinction in the evidence layer.",
                }
                for index, anchor in enumerate(anchor_ids)
            ],
            "drilldown_index": [
                {
                    "id": f"EVID-{index + 1}",
                    "source_anchor_id": anchor["id"],
                    "stage": anchor["stage"],
                    "source_id": anchor["source_id"],
                    "json_pointer": anchor["json_pointer"],
                    "value_sha256": anchor["value_sha256"],
                    "label": f"Evidence for {anchor['source_id']}",
                }
                for index, anchor in enumerate(inventory["anchors"])
            ],
        }
        source_hashes = {
            item["id"]: item["value_sha256"]
            for item in inventory["anchors"]
        }
        elements = [
            (module, "source_anchor_ids")
            for section in plan["sections"]
            for module in section["modules"]
        ]
        elements.extend(
            (item, "source_anchor_ids")
            for item in plan["visual_models"]
        )
        elements.extend(
            (item, "source_anchor_ids")
            for item in plan["fragment_briefs"]
        )
        elements.extend(
            (item, "affected_source_anchor_ids")
            for item in plan["decision_prompts"]
        )
        plan["presentation_bindings"] = [
            {
                "element_id": element["id"],
                "content_sha256": h1a.rt.canonical_sha256(element),
                "source_values": [
                    {
                        "source_anchor_id": anchor_id,
                        "value_sha256": source_hashes[anchor_id],
                    }
                    for anchor_id in element[source_field]
                ],
                "must_not_imply": (
                    element["must_not_imply"]
                    if element["id"].startswith("MOD-")
                    else ["Must not imply facts beyond bound P1 values"]
                ),
                "challenge_result": "passed",
                "challenge_notes": "Checked against frozen P1 values.",
            }
            for element, source_field in elements
        ]
        return plan

    def _run_plan(self, p1, workspace, gate, phases):
        coordinator = _Coordinator()
        with mock.patch.object(
            h1a.p1_runtime,
            "validate_p1_package",
            return_value={"verdict": "ready"},
        ), mock.patch.dict(
            os.environ,
            {
                "CODEX_TASK_ID": "task-plan",
                "CODEX_THREAD_ID": "thread-plan",
            },
            clear=True,
        ):
            receipt = h1a.run_plan(
                self.root / "plan-package",
                p1_package=p1,
                input_gate=gate,
                workspace_state=workspace,
                work_title="测试作品",
                phase_submissions=phases,
                coordinator=coordinator,
                runtime=self.runtime,
            )
        return receipt, coordinator

    def _refresh_presentation_binding(self, plan, element):
        binding = next(
            item
            for item in plan["presentation_bindings"]
            if item["element_id"] == element["id"]
        )
        binding["content_sha256"] = h1a.rt.canonical_sha256(element)

    def _assembly_inputs(self):
        p1, plan_workspace, gate, phases = self._formal_inputs()
        plan_receipt, _ = self._run_plan(
            p1, plan_workspace, gate, phases
        )
        plan_root = plan_receipt.package_root
        plan = json.loads(
            (plan_root / "review-plan.json").read_text(encoding="utf-8")
        )
        inventory = json.loads(
            (plan_root / "source-inventory.json").read_text(
                encoding="utf-8"
            )
        )
        source_by_anchor = {
            item["id"]: item["source_id"]
            for item in inventory["anchors"]
        }
        plan_manifest = {
            "path": "H1/plan/package-manifest.json",
            "sha256": h1a.rt.sha256_file(
                plan_root / "package-manifest.json"
            ),
        }
        fragment_root = self.root / "fragment-package"
        fragments = [
            {
                "id": brief["slot_id"],
                "title": brief["title"],
                "review_purpose": brief["review_purpose"],
                "text": f"Exact sealed fragment text {index}.",
                "source_ids": sorted(
                    {
                        source_by_anchor[anchor_id]
                        for anchor_id in brief["source_anchor_ids"]
                    }
                ),
                "decision_control_ids": brief[
                    "decision_control_ids"
                ],
            }
            for index, brief in enumerate(plan["fragment_briefs"], 1)
        ]
        self._write(
            fragment_root / "fragment-package.json",
            {
                "schema_version": "2.0",
                "run_id": plan["run_id"],
                "h1_session_id": plan["h1_session_id"],
                "p1_completion": plan["p1_completion"],
                "plan_manifest": plan_manifest,
                "fragments": fragments,
                "authority_status": "non_authoritative_sample",
            },
        )
        self._write(
            fragment_root / "generation-session.json",
            {
                "identity": {
                    "task_id": "task-fragment",
                    "thread_id": "thread-fragment",
                }
            },
        )
        (fragment_root / "fragments.md").write_text(
            "\n\n".join(item["text"] for item in fragments),
            encoding="utf-8",
            newline="",
        )
        self._write(
            fragment_root / "package-manifest.json",
            {"formal_h1b_mock": "TASK-011"},
        )
        fragment_manifest = {
            "path": "H1/fragments/package-manifest.json",
            "sha256": h1a.rt.sha256_file(
                fragment_root / "package-manifest.json"
            ),
        }
        fragment_workspace_data = {
            "schema_version": "2.0",
            "run_id": plan["run_id"],
            "stage": "H1",
            "session_id": plan["h1_session_id"],
            "state": "planned",
            "p1_completion": plan_workspace.data["p1_completion"],
            "previous_state_sha256": plan_workspace.reference["sha256"],
            "artifacts": {"plan_manifest": plan_manifest},
        }
        fragment_workspace = h1a.rt.SealedDocument(
            data=fragment_workspace_data,
            reference={
                "path": "H1/planned-workspace-state.json",
                "sha256": h1a.rt.canonical_sha256(
                    fragment_workspace_data
                ),
            },
        )
        ready_data = {
            "schema_version": "2.0",
            "run_id": plan["run_id"],
            "stage": "H1",
            "session_id": plan["h1_session_id"],
            "state": "fragments_ready",
            "p1_completion": plan_workspace.data["p1_completion"],
            "previous_state_sha256": fragment_workspace.reference[
                "sha256"
            ],
            "artifacts": {
                "plan_manifest": plan_manifest,
                "fragment_manifest": fragment_manifest,
            },
        }
        ready_workspace = h1a.rt.SealedDocument(
            data=ready_data,
            reference={
                "path": "H1/h1-workspace-state.json",
                "sha256": h1a.rt.canonical_sha256(ready_data),
            },
        )
        return {
            "p1": p1,
            "plan_workspace": plan_workspace,
            "gate": gate,
            "plan_root": plan_root,
            "fragment_root": fragment_root,
            "fragment_workspace": fragment_workspace,
            "ready_workspace": ready_workspace,
        }

    def _make_fidelity_review(
        self,
        *,
        p1_completion,
        plan_root,
        fragment_root,
    ):
        plan = json.loads(
            (plan_root / "review-plan.json").read_text(encoding="utf-8")
        )
        inventory = json.loads(
            (plan_root / "source-inventory.json").read_text(encoding="utf-8")
        )
        plan_manifest = {
            "path": "H1/plan/package-manifest.json",
            "sha256": h1a.rt.sha256_file(plan_root / "package-manifest.json"),
        }
        fragment_manifest = {
            "path": "H1/fragments/package-manifest.json",
            "sha256": h1a.rt.sha256_file(fragment_root / "package-manifest.json"),
        }
        fragments = h1a._validated_fragment_records(
            fragment_root,
            plan=plan,
            source_inventory=inventory,
            plan_manifest=plan_manifest,
            fragment_manifest=fragment_manifest,
            p1_completion=p1_completion,
            runtime=self.runtime,
        )
        report = h1a._assemble_report(plan, inventory, fragments)
        contracts = h1a._fidelity_element_contract(plan, report)
        element_ids = [item["element_id"] for item in contracts]
        return {
            "schema_version": "2.0",
            "skill": "novel-conception-presentation-fidelity-reviewer",
            "run_id": plan["run_id"],
            "h1_session_id": plan["h1_session_id"],
            "reviewer": {
                "task_id": "/root/presentation_fidelity_reviewer",
                "thread_id": "thread-presentation-fidelity-reviewer",
                "independence_basis": "separate-task-no-producer-context",
            },
            "inputs": {
                "p1_completion": p1_completion,
                "plan_manifest": plan_manifest,
                "fragment_manifest": fragment_manifest,
                "report_sha256": h1a.rt.canonical_sha256(report),
            },
            "dimensions": [
                {
                    "id": dimension,
                    "verdict": "pass",
                    "evidence_element_ids": element_ids,
                    "finding": "逐项核对候选呈现与绑定来源，未发现实质矛盾、关键遗漏或权威升级。",
                }
                for dimension in h1a.FIDELITY_DIMENSIONS
            ],
            "element_reviews": [
                {
                    "element_id": item["element_id"],
                    "content_sha256": item["content_sha256"],
                    "source_anchor_ids": item["source_anchor_ids"],
                    "verdict": item["expected_verdict"],
                    "semantic_assertion": "该元素保持来源中的条件、关系和边界，没有把压缩表达改写成新的构思结论。",
                    "evidence_quotes": [
                        next(
                            value
                            for value in h1a._string_leaves(item["_content"])
                            if len(value.strip()) >= 4
                        )
                    ],
                    "no_material_omission": True,
                    "no_contradiction": True,
                    "no_authority_escalation": True,
                }
                for item in contracts
            ],
            "blockers": [],
            "verdict": "pass",
        }

    def _run_assemble(
        self,
        inputs,
        *,
        h1b_result=None,
        fidelity_mutator=None,
        fidelity_review_present=True,
    ):
        coordinator = _Coordinator()
        validator = mock.Mock(
            return_value=h1b_result or {"verdict": "ready"}
        )
        fake_h1b = mock.Mock()
        fake_h1b.validate_fragment_package = validator
        plan = json.loads(
            (inputs["plan_root"] / "review-plan.json").read_text(encoding="utf-8")
        )
        inventory = json.loads(
            (inputs["plan_root"] / "source-inventory.json").read_text(encoding="utf-8")
        )
        plan_manifest = {
            "path": "H1/plan/package-manifest.json",
            "sha256": h1a.rt.sha256_file(inputs["plan_root"] / "package-manifest.json"),
        }
        fragment_manifest = {
            "path": "H1/fragments/package-manifest.json",
            "sha256": h1a.rt.sha256_file(inputs["fragment_root"] / "package-manifest.json"),
        }
        fragments = h1a._validated_fragment_records(
            inputs["fragment_root"],
            plan=plan,
            source_inventory=inventory,
            plan_manifest=plan_manifest,
            fragment_manifest=fragment_manifest,
            p1_completion={
                "path": inputs["plan_workspace"].data["p1_completion"]["path"],
                "sha256": inputs["plan_workspace"].data["p1_completion"]["sha256"],
            },
            runtime=self.runtime,
        )
        report = h1a._assemble_report(plan, inventory, fragments)
        contracts = h1a._fidelity_element_contract(plan, report)
        element_ids = [item["element_id"] for item in contracts]
        fidelity_review = {
            "schema_version": "2.0",
            "skill": "novel-conception-presentation-fidelity-reviewer",
            "run_id": plan["run_id"],
            "h1_session_id": plan["h1_session_id"],
            "reviewer": {
                "task_id": "/root/presentation_fidelity_reviewer",
                "thread_id": "thread-presentation-fidelity-reviewer",
                "independence_basis": "separate-task-no-producer-context",
            },
            "inputs": {
                "p1_completion": {
                    "path": inputs["plan_workspace"].data["p1_completion"]["path"],
                    "sha256": inputs["plan_workspace"].data["p1_completion"]["sha256"],
                },
                "plan_manifest": plan_manifest,
                "fragment_manifest": fragment_manifest,
                "report_sha256": h1a.rt.canonical_sha256(report),
            },
            "dimensions": [
                {
                    "id": dimension,
                    "verdict": "pass",
                    "evidence_element_ids": element_ids,
                    "finding": "逐项核对候选呈现与绑定来源，未发现实质矛盾、关键遗漏或权威升级。",
                }
                for dimension in h1a.FIDELITY_DIMENSIONS
            ],
            "element_reviews": [
                {
                    "element_id": item["element_id"],
                    "content_sha256": item["content_sha256"],
                    "source_anchor_ids": item["source_anchor_ids"],
                    "verdict": item["expected_verdict"],
                    "semantic_assertion": "该元素保持来源中的条件、关系和边界，没有把压缩表达改写成新的构思结论。",
                    "evidence_quotes": [
                        next(
                            value
                            for value in h1a._string_leaves(item["_content"])
                            if len(value.strip()) >= 4
                        )
                    ],
                    "no_material_omission": True,
                    "no_contradiction": True,
                    "no_authority_escalation": True,
                }
                for item in contracts
            ],
            "blockers": [],
            "verdict": "pass",
        }
        if fidelity_mutator is not None:
            fidelity_mutator(fidelity_review)
        assemble_kwargs = {}
        if fidelity_review_present:
            assemble_kwargs["fidelity_review"] = fidelity_review
        with mock.patch.object(
            h1a.p1_runtime,
            "validate_p1_package",
            return_value={"verdict": "ready"},
        ), mock.patch.object(
            h1a.importlib, "import_module", return_value=fake_h1b
        ):
            receipt = h1a.run_assemble(
                self.root / "assembly-package",
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                fragment_package=inputs["fragment_root"],
                fragment_workspace_state=inputs["fragment_workspace"],
                workspace_state=inputs["ready_workspace"],
                coordinator=coordinator,
                runtime=self.runtime,
                **assemble_kwargs,
            )
        return receipt, coordinator, validator

    def _validate_assembly(self, inputs, package_root):
        fake_h1b = mock.Mock()
        fake_h1b.validate_fragment_package = mock.Mock(
            return_value={"verdict": "ready"}
        )
        with mock.patch.object(
            h1a.p1_runtime,
            "validate_p1_package",
            return_value={"verdict": "ready"},
        ), mock.patch.object(
            h1a.importlib, "import_module", return_value=fake_h1b
        ):
            return h1a.validate_assembly_package(
                package_root,
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                fragment_package=inputs["fragment_root"],
                fragment_workspace_state=inputs["fragment_workspace"],
                workspace_state=inputs["ready_workspace"],
                runtime=self.runtime,
            )

    def test_run_assemble_deterministically_merges_sealed_inputs(self):
        inputs = self._assembly_inputs()
        receipt, coordinator, validator = self._run_assemble(inputs)
        report = json.loads(
            (
                receipt.package_root / "human-review-report.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(report["title"], "《测试作品》构思人审报告")
        self.assertEqual(len(report["visual_models"]), 5)
        self.assertEqual(
            report["fragments"][0]["text"],
            "Exact sealed fragment text 1.",
        )
        self.assertTrue(
            (receipt.package_root / "assembly-execution.json").is_file()
        )
        self.assertEqual(
            coordinator.calls[0]["expected_next_state"], "assembled"
        )
        self.assertGreaterEqual(validator.call_count, 3)
        call = validator.call_args_list[0]
        self.assertEqual(call.args, (inputs["fragment_root"].resolve(),))
        self.assertEqual(
            set(call.kwargs),
            {
                "p1_package",
                "plan_package",
                "plan_input_gate",
                "plan_workspace_state",
                "workspace_state",
                "plan_active_return_request",
                "runtime",
            },
        )
        self.assertIs(
            call.kwargs["plan_input_gate"], inputs["gate"]
        )
        self.assertIsNone(call.kwargs["plan_active_return_request"])
        self.assertIs(
            call.kwargs["workspace_state"],
            inputs["fragment_workspace"],
        )

    def test_run_assemble_requires_independent_fidelity_review(self):
        inputs = self._assembly_inputs()
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_FIDELITY_REVIEW_REQUIRED"
        ):
            self._run_assemble(inputs, fidelity_review_present=False)

    def test_run_assemble_rejects_producer_as_fidelity_reviewer(self):
        inputs = self._assembly_inputs()

        def reuse_plan_identity(review):
            review["reviewer"]["task_id"] = "task-plan"

        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_FIDELITY_REVIEW_NOT_INDEPENDENT"
        ):
            self._run_assemble(inputs, fidelity_mutator=reuse_plan_identity)

    def test_run_assemble_rejects_fidelity_element_hash_drift(self):
        inputs = self._assembly_inputs()

        def drift_hash(review):
            review["element_reviews"][0]["content_sha256"] = "0" * 64

        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_FIDELITY_REVIEW_INVALID"
        ):
            self._run_assemble(inputs, fidelity_mutator=drift_hash)

    def test_run_assemble_rejects_incomplete_fidelity_coverage(self):
        inputs = self._assembly_inputs()

        def omit_element(review):
            review["element_reviews"].pop()

        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_FIDELITY_REVIEW_INVALID"
        ):
            self._run_assemble(inputs, fidelity_mutator=omit_element)

    def test_run_assemble_rejects_wrong_workspace_state(self):
        inputs = self._assembly_inputs()
        data = copy.deepcopy(inputs["ready_workspace"].data)
        data["state"] = "planned"
        inputs["ready_workspace"] = h1a.rt.SealedDocument(
            data=data,
            reference={
                "path": "H1/h1-workspace-state.json",
                "sha256": h1a.rt.canonical_sha256(data),
            },
        )
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_ASSEMBLY_WORKSPACE_INVALID"
        ):
            self._run_assemble(inputs)

    def test_run_assemble_rejects_fragment_package_projection_drift(self):
        inputs = self._assembly_inputs()
        package_path = (
            inputs["fragment_root"] / "fragment-package.json"
        )
        package = json.loads(package_path.read_text(encoding="utf-8"))
        package["fragments"][0]["title"] = "Drifted title."
        self._write(package_path, package)
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_FRAGMENT_PACKAGE_INVALID"
        ):
            self._run_assemble(inputs)

    def test_run_assemble_rejects_non_ready_h1b_validator(self):
        inputs = self._assembly_inputs()
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_H1B_VALIDATION_FAILED"
        ):
            self._run_assemble(
                inputs, h1b_result={"verdict": "blocked"}
            )

    def test_run_assemble_rejects_wrong_fragment_workspace(self):
        inputs = self._assembly_inputs()
        data = copy.deepcopy(inputs["fragment_workspace"].data)
        data["state"] = "initialized"
        inputs["fragment_workspace"] = h1a.rt.SealedDocument(
            data=data,
            reference={
                "path": "H1/planned-workspace-state.json",
                "sha256": h1a.rt.canonical_sha256(data),
            },
        )
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_FRAGMENT_WORKSPACE_INVALID"
        ):
            self._run_assemble(inputs)

    def test_run_plan_builds_unique_review_plan_and_advances_after_publish(self):
        p1, workspace, gate, phases = self._formal_inputs()
        receipt, coordinator = self._run_plan(
            p1, workspace, gate, phases
        )
        self.assertTrue(
            (receipt.package_root / "review-plan.json").is_file()
        )
        self.assertFalse(
            (receipt.package_root / "h1-review-plan.json").exists()
        )
        self.assertEqual(len(coordinator.calls), 1)
        self.assertEqual(
            coordinator.calls[0]["expected_next_state"], "planned"
        )

    def test_run_plan_rejects_wrong_h1_gate(self):
        p1, workspace, gate, phases = self._formal_inputs()
        gate.data["target_stage"] = "P1"
        gate.reference["sha256"] = h1a.rt.canonical_sha256(gate.data)
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_INPUT_GATE_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_phase_to_final_binding_drift(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[1]["payload"]["sections"] = copy.deepcopy(
            phases[1]["payload"]["sections"]
        )
        phases[1]["payload"]["sections"][0]["title"] = "drift"
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_PLAN_PHASE_BINDING_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_missing_or_duplicate_visual_role(self):
        for mutation in ("missing", "duplicate"):
            with self.subTest(mutation=mutation):
                p1, workspace, gate, phases = self._formal_inputs()
                visuals = phases[4]["payload"]["review_plan"][
                    "visual_models"
                ]
                if mutation == "missing":
                    visuals.pop()
                else:
                    visuals[-1]["semantic_role"] = visuals[0][
                        "semantic_role"
                    ]
                with self.assertRaisesRegex(
                    h1a.H1AError,
                    (
                        "H1A_REVIEW_PLAN_SCHEMA_INVALID"
                        if mutation == "missing"
                        else "H1A_VISUAL_ROLE_INVALID"
                    ),
                ):
                    self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_visual_wrong_section_or_kind(self):
        for field, value in (
            ("section_id", "SEC-CHARACTERS"),
            ("visual_kind", "timeline"),
        ):
            with self.subTest(field=field):
                p1, workspace, gate, phases = self._formal_inputs()
                phases[4]["payload"]["review_plan"][
                    "visual_models"
                ][0][field] = value
                with self.assertRaisesRegex(
                    h1a.H1AError, "H1A_VISUAL_ROLE_INVALID"
                ):
                    self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_visual_dangling_edge(self):
        p1, workspace, gate, phases = self._formal_inputs()
        control = phases[4]["payload"]["review_plan"][
            "visual_models"
        ][1]
        control["edges"][0]["to_node_id"] = "NODE-GHOST-1"
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_VISUAL_GRAPH_EDGE_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_noncontinuous_visual_orders(self):
        for collection in ("groups", "nodes", "edges", "text_equivalents"):
            with self.subTest(collection=collection):
                p1, workspace, gate, phases = self._formal_inputs()
                plan = phases[4]["payload"]["review_plan"]
                visual = (
                    plan["visual_models"][3]
                    if collection == "groups"
                    else plan["visual_models"][1]
                )
                visual[collection][0]["order"] = 2
                with self.assertRaisesRegex(
                    h1a.H1AError, "H1A_VISUAL_GRAPH_ORDER_INVALID"
                ):
                    self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_timeline_lane_temporal_and_order_drift(self):
        mutations = (
            ("missing lane", "group_lane"),
            ("missing temporal", "node_temporal"),
            ("same lane duplicate order", "node_order"),
        )
        for label, mutation in mutations:
            with self.subTest(mutation=label):
                p1, workspace, gate, phases = self._formal_inputs()
                timeline = phases[4]["payload"]["review_plan"][
                    "visual_models"
                ][3]
                if mutation == "group_lane":
                    timeline["groups"][0]["lane"] = None
                elif mutation == "node_temporal":
                    timeline["nodes"][0]["temporal_label"] = None
                else:
                    timeline["nodes"][1]["order"] = 1
                expected = (
                    "H1A_VISUAL_GRAPH_ORDER_INVALID"
                    if mutation == "node_order"
                    else "H1A_VISUAL_TIMELINE_INVALID"
                )
                with self.assertRaisesRegex(h1a.H1AError, expected):
                    self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_accepts_non_timeline_single_node_without_edges(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        world_map = plan["visual_models"][0]
        character_network = plan["visual_models"][4]
        self.assertEqual(len(world_map["nodes"]), 1)
        self.assertEqual(world_map["edges"], [])
        self.assertEqual(len(character_network["nodes"]), 1)
        self.assertEqual(character_network["edges"], [])
        receipt, _ = self._run_plan(p1, workspace, gate, phases)
        self.assertTrue((receipt.package_root / "review-plan.json").is_file())

    def test_run_plan_rejects_visual_source_or_text_equivalent_drift(self):
        for mutation in ("visual source", "text equivalent source"):
            with self.subTest(mutation=mutation):
                p1, workspace, gate, phases = self._formal_inputs()
                visual = phases[4]["payload"]["review_plan"][
                    "visual_models"
                ][0]
                if mutation == "visual source":
                    visual["source_anchor_ids"] = visual[
                        "source_anchor_ids"
                    ][:-1]
                    expected = "H1A_VISUAL_GRAPH_SOURCE_INVALID"
                else:
                    visual["text_equivalents"][0][
                        "source_anchor_ids"
                    ] = visual["text_equivalents"][0][
                        "source_anchor_ids"
                    ][:-1]
                    expected = "H1A_VISUAL_TEXT_EQUIVALENT_INVALID"
                with self.assertRaisesRegex(h1a.H1AError, expected):
                    self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_work_identity_title_drift(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        plan["work_identity"]["work_title"] = "另一个作品"
        plan["work_identity"]["report_title"] = (
            "《另一个作品》构思人审报告"
        )
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_REVIEW_PLAN_LINEAGE_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_visual_text_budget_bypass(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        visual = plan["visual_models"][0]
        visual["nodes"][0]["summary"] = "扩" * 3000
        self._refresh_presentation_binding(plan, visual)
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_READING_BUDGET_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_assembly_validation_rejects_visual_or_title_projection_drift(self):
        inputs = self._assembly_inputs()
        receipt, _, _ = self._run_assemble(inputs)
        report_path = receipt.package_root / "human-review-report.json"
        original = json.loads(report_path.read_text(encoding="utf-8"))
        mutations = {
            "dropped visual": lambda report: report["visual_models"].pop(),
            "changed visual text": lambda report: report["visual_models"][0][
                "text_equivalents"
            ][0].__setitem__("text", "Drifted visual text"),
            "changed title": lambda report: report.__setitem__(
                "title", "《漂移作品》构思人审报告"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                report = copy.deepcopy(original)
                mutate(report)
                self._write(report_path, report)
                with self.assertRaisesRegex(
                    h1a.H1AError, "H1A_ASSEMBLY_REPORT_INVALID"
                ):
                    self._validate_assembly(inputs, receipt.package_root)
        self._write(report_path, original)

    def test_run_plan_rejects_fabricated_content_with_old_value_binding(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[1]["payload"]["sections"][0]["modules"][0][
            "definition"
        ] = "Fabricated content with a real source anchor."
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_PRESENTATION_BINDING_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_prompt_injected_only_in_final_phase(self):
        p1, workspace, gate, phases = self._formal_inputs()
        final_plan = phases[4]["payload"]["review_plan"]
        final_plan["decision_prompts"] = copy.deepcopy(
            final_plan["decision_prompts"]
        )
        injected = copy.deepcopy(final_plan["decision_prompts"][0])
        injected["id"] = "PROMPT-INJECTED"
        final_plan["decision_prompts"].append(injected)
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_PLAN_PHASE_BINDING_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_legacy_fragment_brief_without_v2_contract(self):
        p1, workspace, gate, phases = self._formal_inputs()
        del phases[4]["payload"]["review_plan"]["fragment_briefs"][0][
            "language_contract_id"
        ]
        with self.assertRaisesRegex(
            h1a.H1AError,
            "H1A_(?:FRAGMENT_BRIEF_INVALID|REVIEW_PLAN_SCHEMA_INVALID)",
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_fragment_brief_fixed_contract_drift(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[4]["payload"]["review_plan"]["fragment_briefs"][0][
            "pov_mode"
        ] = "omniscient"
        with self.assertRaisesRegex(
            h1a.H1AError,
            "H1A_(?:FRAGMENT_BRIEF_INVALID|REVIEW_PLAN_SCHEMA_INVALID)",
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_budget_above_ten_minutes(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        plan["review_path"][0]["estimated_seconds"] = 141
        plan["budget_items"][0]["estimated_seconds"] = 141
        phases[3]["payload"]["budget_items"] = plan["budget_items"]
        phases[3]["payload"]["budget_total_seconds"] = 601
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_READING_BUDGET_EXCEEDED"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_accepts_budget_exactly_ten_minutes(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        plan["review_path"][0]["estimated_seconds"] = 140
        plan["budget_items"][0]["estimated_seconds"] = 140
        phases[3]["payload"]["budget_items"] = plan["budget_items"]
        phases[3]["payload"]["budget_total_seconds"] = 600
        receipt, _ = self._run_plan(p1, workspace, gate, phases)
        self.assertTrue((receipt.package_root / "review-plan.json").is_file())

    def test_run_plan_rejects_critical_anchor_only_in_drilldown(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        critical = next(
            item
            for item in plan["reduction_ledger"]
            if item["review_priority"] == "critical"
        )
        critical["exposure"] = "drilldown-only"
        coverage = next(
            item
            for item in plan["control_coverage"]
            if item["source_anchor_id"] == critical["source_anchor_id"]
        )
        coverage["visible_element_ids"] = ["EVID-1"]
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_CRITICAL_EVIDENCE_NOT_DEFAULT_VISIBLE"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_orphan_anchor_in_reduction_ledger(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[4]["payload"]["review_plan"]["reduction_ledger"].pop()
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_REDUCTION_LEDGER_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_reading_baseline_accepts_measured_happy_budget(self):
        _, _, _, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        minimums = h1a._minimum_reading_seconds(plan)
        for step in plan["review_path"]:
            self.assertGreaterEqual(
                step["estimated_seconds"], minimums[step["kind"]]
            )

    def test_run_plan_rejects_all_path_steps_at_one_second(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        for step, budget in zip(
            plan["review_path"], plan["budget_items"]
        ):
            step["estimated_seconds"] = 1
            budget["estimated_seconds"] = 1
        phases[3]["payload"]["budget_total_seconds"] = 5
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_READING_BUDGET_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_caller_supplied_reading_profile(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[4]["payload"]["review_plan"][
            "reading_profile"
        ] = "caller-fast-reading-profile"
        phases[3]["payload"][
            "reading_profile"
        ] = "caller-fast-reading-profile"
        with self.assertRaisesRegex(
            h1a.H1AError,
            "H1A_(?:READING_PROFILE_INVALID|REVIEW_PLAN_SCHEMA_INVALID)",
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_ghost_default_path_element(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[4]["payload"]["review_plan"]["review_path"][0][
            "visible_element_ids"
        ][0] = "GHOST-1"
        with self.assertRaisesRegex(
            h1a.H1AError,
            "H1A_(?:REVIEW_PATH_INVALID|REVIEW_PLAN_SCHEMA_INVALID)",
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_cross_kind_default_path_element(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[4]["payload"]["review_plan"]["review_path"][0][
            "visible_element_ids"
        ][0] = "MOD-STORYLINES-1"
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_REVIEW_PATH_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_missing_default_visible_element(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[4]["payload"]["review_plan"]["review_path"][0][
            "visible_element_ids"
        ].remove("VIS-1")
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_REVIEW_PATH_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_wrong_anchor_coverage(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        brief = plan["fragment_briefs"][0]
        retained_anchors = brief["source_anchor_ids"][:-1]
        wrong_anchor = brief["source_anchor_ids"][-1]
        brief["source_anchor_ids"] = retained_anchors
        binding = next(
            item
            for item in plan["presentation_bindings"]
            if item["element_id"] == brief["id"]
        )
        binding["content_sha256"] = h1a.rt.canonical_sha256(brief)
        binding["source_values"] = [
            item
            for item in binding["source_values"]
            if item["source_anchor_id"] in retained_anchors
        ]
        coverage = next(
            item
            for item in plan["control_coverage"]
            if item["source_anchor_id"] == wrong_anchor
        )
        coverage["visible_element_ids"] = ["FRAG-1"]
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_SOURCE_COVERAGE_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_ghost_budget_item(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[4]["payload"]["review_plan"]["budget_items"][0][
            "element_id"
        ] = "GHOST-PATH"
        with self.assertRaisesRegex(
            h1a.H1AError,
            "H1A_(?:READING_BUDGET_INVALID|REVIEW_PLAN_SCHEMA_INVALID)",
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_missing_budget_item(self):
        p1, workspace, gate, phases = self._formal_inputs()
        plan = phases[4]["payload"]["review_plan"]
        plan["budget_items"].pop()
        phases[3]["payload"]["budget_total_seconds"] = 460
        with self.assertRaisesRegex(
            h1a.H1AError,
            "H1A_(?:READING_BUDGET_INVALID|REVIEW_PLAN_SCHEMA_INVALID)",
        ):
            self._run_plan(p1, workspace, gate, phases)

    def test_run_plan_rejects_missing_source_coverage(self):
        p1, workspace, gate, phases = self._formal_inputs()
        phases[4]["payload"]["review_plan"]["control_coverage"].pop()
        with self.assertRaisesRegex(
            h1a.H1AError, "H1A_SOURCE_COVERAGE_INVALID"
        ):
            self._run_plan(p1, workspace, gate, phases)


if __name__ == "__main__":
    unittest.main()
