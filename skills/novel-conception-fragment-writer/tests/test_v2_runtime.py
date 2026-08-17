import copy
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock


h1b = importlib.import_module(
    "skills.novel-conception-fragment-writer.scripts.run_v2"
)


class _Coordinator:
    def __init__(self):
        self.calls = []

    def accept_h1_workspace_transition(self, **kwargs):
        self.calls.append(kwargs)
        return {"state": kwargs["expected_next_state"]}


class _RejectingCoordinator:
    def __init__(self):
        self.calls = []

    def accept_h1_workspace_transition(self, **kwargs):
        self.calls.append(kwargs)
        raise RuntimeError("coordinator rejected transition")


class H1BRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.runtime = h1b.rt.ContractRuntime()
        self.run_index = 0
        self.input_index = 0

    def tearDown(self):
        self.temporary.cleanup()

    def _write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            h1b.rt.canonical_json(value), encoding="utf-8", newline=""
        )

    def _sealed(self, data, path):
        return h1b.rt.SealedDocument(
            data=data,
            reference={
                "path": path,
                "sha256": h1b.rt.canonical_sha256(data),
            },
        )

    def _brief(self, index):
        return {
            "id": f"BRIEF-{index}",
            "slot_id": f"FRAG-{index}",
            "title": f"选择样片 {index}",
            "review_purpose": "检验压力下的主动选择及直接后果",
            "pov_character_id": "CHR-1",
            "source_anchor_ids": ["SRC-000001", "SRC-000002"],
            "required_demonstrations": ["选择造成直接后果"],
            "forbidden_additions": ["新增世界规则"],
            "target_words_min": 320,
            "target_words_max": 480,
            "language_contract_id": h1b.LANGUAGE_CONTRACT_ID,
            "style_contract_id": h1b.STYLE_CONTRACT_ID,
            "depth_contract_id": h1b.DEPTH_CONTRACT_ID,
            "pov_mode": h1b.POV_MODE,
            "information_limits": {
                "may_present": ["终端文字、门锁反馈与林安的过程性判断"],
                "must_not_present_as_known": ["门外人员的真实意图"],
            },
            "allowed_perception_channels": ["视觉", "听觉", "终端文字"],
            "scene_contract": {
                "before_state": "未经核验的命令正在逼近执行",
                "immediate_goal": "阻止危险指令继续执行",
                "pressure": "对方要求立刻刷卡",
                "obstacle": "林安没有第二名核验者",
                "required_choice": "拒绝刷卡并触发复核",
                "direct_consequence": "门保持闭锁且命令暂停",
                "after_state": "现场无人离开，命令也无法继续",
            },
            "decisive_interiority_policy": h1b.INTERIORITY_POLICY,
            "surface_detail_policy": h1b.SURFACE_DETAIL_POLICY,
            "decision_control_ids": ["DCTRL-FRAGMENTS"],
        }

    def _inputs(self):
        self.input_index += 1
        p1 = self.root / f"P1-{self.input_index}"
        character_object = {
            "id": "CHR-1",
            "name": "林安",
            "decision_boundary": "未经双重核验不得执行危险指令",
            "information_limit": "只能依据终端文字和现场反馈判断",
        }
        environment_object = {
            "id": "ENV-1",
            "name": "封闭室",
            "access_rule": "封闭室门锁必须取得双人签名才能开启",
            "failure_consequence": "单人尝试会触发红灯并保持闭锁",
        }
        character = {"objects": [character_object]}
        environment = {"objects": [environment_object]}
        self._write(p1 / "C1.json", character)
        self._write(p1 / "E1.json", environment)
        self._write(
            p1 / "stage-completion.json",
            {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "stage": "P1",
                "status": "ready",
            },
        )
        p1_stage = {
            "stage": "P1",
            "path": "P1/stage-completion.json",
            "sha256": h1b.rt.sha256_file(p1 / "stage-completion.json"),
        }
        p1_artifact = {
            "path": p1_stage["path"],
            "sha256": p1_stage["sha256"],
        }
        anchors = [
            {
                "id": "SRC-000001",
                "stage": "C1",
                "source_id": "CHR-1",
                "artifact": h1b.rt.artifact_reference(
                    p1 / "C1.json", root=p1
                ),
                "json_pointer": "/objects/0",
                "value_sha256": h1b.rt.canonical_sha256(character_object),
            },
            {
                "id": "SRC-000002",
                "stage": "E1",
                "source_id": "ENV-1",
                "artifact": h1b.rt.artifact_reference(
                    p1 / "E1.json", root=p1
                ),
                "json_pointer": "/objects/0",
                "value_sha256": h1b.rt.canonical_sha256(environment_object),
            },
        ]
        plan_root = (
            self.root / f"input-{self.input_index}" / "H1" / "plan"
        )
        briefs = [self._brief(index) for index in range(1, 4)]
        plan = {
            "schema_version": "2.0",
            "skill": "novel-conception-human-review-assembler",
            "run_id": "RUN-1",
            "h1_session_id": "H1-SESSION-1",
            "p1_completion": p1_artifact,
            "fragment_briefs": briefs,
        }
        self._write(plan_root / "review-plan.json", plan)
        self._write(
            plan_root / "source-inventory.json",
            {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "p1_completion": p1_artifact,
                "anchors": anchors,
            },
        )
        plan_ref = h1b.rt.artifact_reference(
            plan_root / "review-plan.json", root=plan_root
        )
        self._write(
            plan_root / "fragment-briefs.json",
            {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "h1_session_id": "H1-SESSION-1",
                "p1_completion": p1_artifact,
                "review_plan": plan_ref,
                "briefs": briefs,
            },
        )
        initialized = self._sealed(
            {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "stage": "H1",
                "session_id": "H1-SESSION-1",
                "state": "initialized",
                "p1_completion": p1_stage,
                "previous_state_sha256": None,
                "artifacts": {},
            },
            "H1/initial-state.json",
        )
        auxiliary = {
            "generation-session.json": {"fixture": "session"},
            "generation-evidence-index.json": {"fixture": "evidence"},
            "execution-record.json": {"fixture": "execution"},
            "validation.json": {"fixture": "validation"},
            "implementation/run_v2.py": {"fixture": "implementation"},
        }
        for name, value in auxiliary.items():
            self._write(plan_root / name, value)
        plan_files = [
            h1b.rt.artifact_reference(path, root=plan_root)
            for path in sorted(
                plan_root.rglob("*"), key=lambda item: item.as_posix()
            )
            if path.is_file()
        ]
        by_path = {item["path"]: item for item in plan_files}
        self._write(
            plan_root / "package-manifest.json",
            {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "stage": "H1",
                "package_profile": "h1-plan",
                "verdict": "ready",
                "session_id": "H1-SESSION-1",
                "parent_state_sha256": initialized.reference["sha256"],
                "files": plan_files,
                "artifact_roles": {
                    "source_inventory": by_path["source-inventory.json"],
                    "review_plan": by_path["review-plan.json"],
                    "fragment_briefs": by_path["fragment-briefs.json"],
                    "generation_session": by_path[
                        "generation-session.json"
                    ],
                    "generation_evidence_index": by_path[
                        "generation-evidence-index.json"
                    ],
                    "execution_record": by_path["execution-record.json"],
                },
                "validation": by_path["validation.json"],
                "implementation": [
                    by_path["implementation/run_v2.py"]
                ],
            },
        )
        plan_manifest = {
            "path": "H1/plan/package-manifest.json",
            "sha256": h1b.rt.sha256_file(
                plan_root / "package-manifest.json"
            ),
        }
        planned = self._sealed(
            {
                "schema_version": "2.0",
                "run_id": "RUN-1",
                "stage": "H1",
                "session_id": "H1-SESSION-1",
                "state": "planned",
                "p1_completion": p1_stage,
                "previous_state_sha256": initialized.reference["sha256"],
                "artifacts": {"plan_manifest": plan_manifest},
            },
            "H1/h1-workspace-state.json",
        )
        gate = self._sealed(
            {"schema_version": "2.0", "fixture": "plan-gate"},
            "H1/input-gate.json",
        )
        phases = self._phases(
            briefs, anchors, character_object, environment_object
        )
        return {
            "p1": p1,
            "plan_root": plan_root,
            "plan_workspace": initialized,
            "planned_workspace": planned,
            "gate": gate,
            "phases": phases,
            "briefs": briefs,
            "anchors": anchors,
            "character": character_object,
            "environment": environment_object,
        }

    def _text(self):
        return (
            "林安站在封闭室的门边，终端上的字一行行浮出：未经双重核验不得执行危险"
            "指令。桌对面的人催他立刻刷卡，走廊里的脚步越来越近。他没有解释，只把"
            "临时通行卡推回桌面。\n\n"
            "那张卡擦过桌面时偏了一点，停在对方手边。林安认得这种催法：先说只是"
            "临时处置，再把签过字的人留在记录里。他想把门外的人放进来，也想让自己的"
            "名字别出现在一份无法解释的日志上。两件事不能同时做到。\n\n"
            "“第二个签名呢？”他问。对方没有看空着的签名框，只说时间来不及了。脚步"
            "在门外停住，有人敲了两下。林安的手已经碰到读卡区，又收了回来。若门外真"
            "有伤员，延误也会记在他名下；可越是这样，越不该替一个看不见的人补签。\n\n"
            "对方把卡推回来，这次压住了他的指尖。林安没抽手。他看着终端上的空框，"
            "等那只手先松开，然后转身按下墙边的复核键。警示灯由红转黄，系统把这次"
            "尝试锁进待核队列。\n\n"
            "封闭室门锁必须取得双人签名才能开启，屏幕上第二个签名框仍是空的。警示灯"
            "随即熄灭，门仍旧关着。林安听见对方吸了一口气，把文件慢慢合上。现在谁也"
            "不能离开，那份未经核验的命令也无法继续执行。门外又敲了一次，比刚才轻。"
            "林安没有去看对方。他把手留在复核键上，等第二个人来承担这个名字。"
        )

    def _projection_specs(self, anchors, character, environment):
        return [
            {
                "id": "PROJ-CHAR-BOUNDARY",
                "anchor": anchors[0],
                "pointer": "/decision_boundary",
                "value": character["decision_boundary"],
                "usage": "让林安以核验边界拒绝刷卡",
                "quote": "未经双重核验不得执行危险指令",
            },
            {
                "id": "PROJ-ENV-ACCESS",
                "anchor": anchors[1],
                "pointer": "/access_rule",
                "value": environment["access_rule"],
                "usage": "让双人签名门锁约束行动结果",
                "quote": "封闭室门锁必须取得双人签名才能开启",
            },
        ]

    def _phases(self, briefs, anchors, character, environment):
        specs = self._projection_specs(anchors, character, environment)
        contracts = []
        drafts = []
        reviews = []
        for brief in briefs:
            challenges = []
            for spec in specs:
                challenges.append(
                    {
                        "source_anchor_id": spec["anchor"]["id"],
                        "value_sha256": spec["anchor"]["value_sha256"],
                        "story_specific_use": spec["usage"],
                        "does_not_authorize": "不授权新增历史、关系或结果",
                        "fact_projections": [
                            {
                                "id": spec["id"],
                                "field_pointer": spec["pointer"],
                                "value_sha256": h1b.rt.canonical_sha256(
                                    spec["value"]
                                ),
                                "required_usage": spec["usage"],
                            }
                        ],
                    }
                )
            contract = {
                "brief_id": brief["id"],
                "slot_id": brief["slot_id"],
                "brief_sha256": h1b.rt.canonical_sha256(brief),
                "title": brief["title"],
                "review_purpose": brief["review_purpose"],
                "language_contract_id": h1b.LANGUAGE_CONTRACT_ID,
                "style_contract_id": h1b.STYLE_CONTRACT_ID,
                "depth_contract_id": h1b.DEPTH_CONTRACT_ID,
                "pov_mode": h1b.POV_MODE,
                "pov_character_id": brief["pov_character_id"],
                "information_limits": copy.deepcopy(
                    brief["information_limits"]
                ),
                "allowed_perception_channels": copy.deepcopy(
                    brief["allowed_perception_channels"]
                ),
                "scene_contract": copy.deepcopy(brief["scene_contract"]),
                "decisive_interiority_policy": h1b.INTERIORITY_POLICY,
                "surface_detail_policy": h1b.SURFACE_DETAIL_POLICY,
                "target_chars_min": brief["target_words_min"],
                "target_chars_max": brief["target_words_max"],
                "source_challenges": challenges,
                "required_demonstrations": copy.deepcopy(
                    brief["required_demonstrations"]
                ),
                "forbidden_additions": copy.deepcopy(
                    brief["forbidden_additions"]
                ),
                "opposition_challenge": {
                    "verdict": "compatible",
                    "evidence": "必写后果不要求建立新的世界规则。",
                },
                "narrative_scene_design": {
                    "carry_in": "林安已被命令压力推到门边，但尚未同意刷卡。",
                    "surface_want": "尽快判断门外情况并完成安全处置。",
                    "counterwant_or_fear": "不愿让自己的名字替未经核验的命令背书。",
                    "interpretive_bias": "他把催促理解为转移责任的惯用手法。",
                    "protective_tactic": "先追问第二签名，再用沉默拖慢对方。",
                    "contradiction_under_pressure": "既怕延误救援，也怕放行危险命令。",
                    "relationship_or_system_pressure": "对方的催促与门锁规则同时限制选择。",
                    "beat_progression": [
                        "命令催促刷卡，门外脚步逼近。",
                        "林安发现第二签名仍然空缺。",
                        "对方回避核验问题并把卡推回。",
                        "门外敲门使延误风险变得具体。",
                        "林安收回手并触发复核锁定。",
                    ],
                    "turning_pressure": "对方用手压住卡和林安的指尖。",
                    "choice_cost": "拒绝刷卡意味着承担延误处置的风险。",
                    "aftershock": "命令暂停，但门外需求与双方冲突没有消失。",
                    "source_anchor_ids": copy.deepcopy(brief["source_anchor_ids"]),
                },
            }
            text = self._text()
            draft = {
                "id": brief["slot_id"],
                "brief_sha256": h1b.rt.canonical_sha256(brief),
                "title": brief["title"],
                "review_purpose": brief["review_purpose"],
                "text": text,
                "source_anchor_ids": copy.deepcopy(
                    brief["source_anchor_ids"]
                ),
                "surface_details": [],
                "introduced_control_facts": [],
            }
            reviews.append(
                {
                    "fragment_id": brief["slot_id"],
                    "brief_sha256": h1b.rt.canonical_sha256(brief),
                    "draft_sha256": h1b.rt.canonical_sha256(text),
                    "text_sha256": h1b.rt.canonical_sha256(text),
                    "fact_projection_ledger": [
                        {
                            "fact_projection_id": spec["id"],
                            "source_anchor_id": spec["anchor"]["id"],
                            "source_value_sha256": spec["anchor"][
                                "value_sha256"
                            ],
                            "field_value_sha256": h1b.rt.canonical_sha256(
                                spec["value"]
                            ),
                            "story_specific_claim": spec["usage"],
                            "evidence_quote": spec["quote"],
                            "evidence_quote_sha256": h1b.rt.canonical_sha256(
                                spec["quote"]
                            ),
                            "challenge_result": "lexically_grounded",
                            "challenge_notes": (
                                "最终文本直接呈现该控制字段，并让它约束选择和后果。"
                            ),
                            "control_status": "preserved",
                        }
                        for spec in specs
                    ],
                    "required_demonstrations": [
                        {
                            "requirement": "选择造成直接后果",
                            "fact_projection_ids": [
                                spec["id"] for spec in specs
                            ],
                            "finding": "拒绝刷卡让门保持关闭并暂停命令。",
                            "evidence_quote": (
                                "那份未经核验的命令也无法继续执行"
                            ),
                        }
                    ],
                    "forbidden_additions": [
                        {
                            "prohibition": "新增世界规则",
                            "verdict": "absent",
                            "check_notes": "只使用两个已投影的 P1 控制字段。",
                        }
                    ],
                    "information_boundary": {
                        "may_present": copy.deepcopy(
                            brief["information_limits"]["may_present"]
                        ),
                        "must_not_present_as_known": copy.deepcopy(
                            brief["information_limits"][
                                "must_not_present_as_known"
                            ]
                        ),
                        "used_perception_channels": [
                            "视觉",
                            "听觉",
                            "终端文字",
                        ],
                        "evidence_quotes": [
                            "终端上的字一行行浮出",
                            "林安听见对方吸了一口气",
                        ],
                        "verdict": "passed",
                    },
                    "scene_contract_evidence": [
                        {
                            "field": field,
                            "expected_value": value,
                            "finding": "该场景字段已在连续行动中呈现。",
                            "evidence_quote": (
                                "那份未经核验的命令也无法继续执行"
                            ),
                        }
                        for field, value in brief["scene_contract"].items()
                    ],
                    "style_checks": {
                        code: True for code in h1b.STYLE_PRINCIPLES
                    },
                    "narrative_quality_checks": [
                        {
                            "principle": principle,
                            "finding": "人物的注意、矛盾和动作在现场相互推动，而不是由旁白概括结论。",
                            "evidence_quotes": pair,
                        }
                        for principle, pair in zip(
                            h1b.NARRATIVE_QUALITY_PRINCIPLES,
                            [
                                ["那张卡擦过桌面时偏了一点", "林安认得这种催法"],
                                ["两件事不能同时做到", "林安的手已经碰到读卡区，又收了回来"],
                                ["有人敲了两下", "越是这样，越不该替一个看不见的人补签"],
                                ["对方把卡推回来", "系统把这次尝试锁进待核队列"],
                                ["第二个签名呢", "对方没有看空着的签名框"],
                                ["等那只手先松开", "转身按下墙边的复核键"],
                                ["门外又敲了一次，比刚才轻", "他把手留在复核键上"],
                                ["对方吸了一口气，把文件慢慢合上", "等第二个人来承担这个名字"],
                            ],
                        )
                    ],
                    "boundary_checks": {
                        "language_contract_id": h1b.LANGUAGE_CONTRACT_ID,
                        "style_contract_id": h1b.STYLE_CONTRACT_ID,
                        "pov_mode": h1b.POV_MODE,
                        "pov_character_id": brief["pov_character_id"],
                        "decisive_interiority_policy": (
                            h1b.INTERIORITY_POLICY
                        ),
                        "surface_detail_policy": (
                            h1b.SURFACE_DETAIL_POLICY
                        ),
                        "choice_evidence_quote": (
                            "他没有解释，只把临时通行卡推回桌面"
                        ),
                        "consequence_evidence_quote": (
                            "警示灯随即熄灭，门仍旧关着"
                        ),
                        "state_change_evidence_quote": (
                            "那份未经核验的命令也无法继续执行"
                        ),
                        "decisive_inner_revelation": False,
                        "introduced_control_facts": [],
                        "final_prose_claim": False,
                    },
                    "surface_details": [],
                }
            )
            contracts.append(contract)
            drafts.append(draft)
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

    def _patches(self, inputs):
        return (
            mock.patch.object(
                h1b.h1a,
                "validate_plan_package",
                return_value={"verdict": "ready"},
            ),
            mock.patch.object(
                h1b.p1_runtime,
                "validate_p1_package",
                return_value={"verdict": "ready"},
            ),
        )

    def _relocate_plan(self, inputs, logical_manifest_path):
        logical = PurePosixPath(logical_manifest_path)
        target = self.root / f"relocated-{self.input_index}"
        target = target.joinpath(*logical.parts[:-1])
        target.parent.mkdir(parents=True, exist_ok=True)
        inputs["plan_root"].replace(target)
        inputs["plan_root"] = target
        data = copy.deepcopy(inputs["planned_workspace"].data)
        data["artifacts"]["plan_manifest"]["path"] = logical.as_posix()
        inputs["planned_workspace"] = self._sealed(
            data, "H1/h1-workspace-state.json"
        )
        return inputs

    def _run(self, inputs, coordinator=None):
        coordinator = coordinator or _Coordinator()
        self.run_index += 1
        session_root = self.root / f"fragment-session-{self.run_index}"
        output_root = self.root / f"fragment-output-{self.run_index}"
        self.last_session_root = session_root
        self.last_output_root = output_root
        plan_patch, p1_patch = (
            self._patches(inputs)
        )
        with plan_patch, p1_patch, mock.patch.dict(
            os.environ,
            {
                "CODEX_TASK_ID": "task-h1b",
                "CODEX_THREAD_ID": "thread-h1b",
            },
            clear=True,
        ):
            h1b.start_fragment_session(
                session_root,
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                workspace_state=inputs["planned_workspace"],
                runtime=self.runtime,
            )
            for submission in inputs["phases"]:
                h1b.submit_fragment_phase(
                    session_root,
                    submission,
                    p1_package=inputs["p1"],
                    plan_package=inputs["plan_root"],
                    plan_input_gate=inputs["gate"],
                    plan_workspace_state=inputs["plan_workspace"],
                    workspace_state=inputs["planned_workspace"],
                    runtime=self.runtime,
                )
            receipt = h1b.run(
                output_root,
                session_workspace=session_root,
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                workspace_state=inputs["planned_workspace"],
                coordinator=coordinator,
                runtime=self.runtime,
            )
        return receipt, coordinator

    def _start_only(self, inputs, *, task="task-h1b", thread="thread-h1b"):
        self.run_index += 1
        session_root = self.root / f"fragment-session-{self.run_index}"
        plan_patch, p1_patch = (
            self._patches(inputs)
        )
        with plan_patch, p1_patch, mock.patch.dict(
            os.environ,
            {"CODEX_TASK_ID": task, "CODEX_THREAD_ID": thread},
            clear=True,
        ):
            h1b.start_fragment_session(
                session_root,
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                workspace_state=inputs["planned_workspace"],
                runtime=self.runtime,
            )
        return session_root

    def _submit_one(
        self,
        inputs,
        session_root,
        submission,
        *,
        task="task-h1b",
        thread="thread-h1b",
    ):
        plan_patch, p1_patch = (
            self._patches(inputs)
        )
        with plan_patch, p1_patch, mock.patch.dict(
            os.environ,
            {"CODEX_TASK_ID": task, "CODEX_THREAD_ID": thread},
            clear=True,
        ):
            return h1b.submit_fragment_phase(
                session_root,
                submission,
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                workspace_state=inputs["planned_workspace"],
                runtime=self.runtime,
            )

    def _finalize_only(self, inputs, session_root):
        output = self.root / f"manual-output-{self.run_index}"
        plan_patch, p1_patch = (
            self._patches(inputs)
        )
        with plan_patch, p1_patch, mock.patch.dict(
            os.environ,
            {
                "CODEX_TASK_ID": "task-h1b",
                "CODEX_THREAD_ID": "thread-h1b",
            },
            clear=True,
        ):
            return h1b.run(
                output,
                session_workspace=session_root,
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                workspace_state=inputs["planned_workspace"],
                coordinator=_Coordinator(),
                runtime=self.runtime,
            )

    def _validate_published(self, inputs, package_root):
        plan_patch, p1_patch = (
            self._patches(inputs)
        )
        with plan_patch, p1_patch:
            return h1b.validate_fragment_package(
                package_root,
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                workspace_state=inputs["planned_workspace"],
                runtime=self.runtime,
            )

    def test_happy_path_publishes_complete_package_before_transition(self):
        inputs = self._inputs()
        receipt, coordinator = self._run(inputs)
        package = json.loads(
            (receipt.package_root / "fragment-package.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(package["fragments"]), 3)
        self.assertTrue((receipt.package_root / "fragments.md").is_file())
        self.assertEqual(
            coordinator.calls[0]["expected_next_state"],
            "fragments_ready",
        )

    def test_plan_manifest_paths_accept_legacy_attempt_and_nested(self):
        for logical in (
            "H1/plan/package-manifest.json",
            "H1/plan-attempt-02/package-manifest.json",
            "H1/plans/attempt-02/package-manifest.json",
        ):
            with self.subTest(logical=logical):
                inputs = self._inputs()
                if logical != "H1/plan/package-manifest.json":
                    self._relocate_plan(inputs, logical)
                session = self._start_only(inputs)
                stored = json.loads(
                    (session / "generation-session.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    stored["plan_manifest"],
                    inputs["planned_workspace"].data["artifacts"][
                        "plan_manifest"
                    ],
                )

    def test_attempt_plan_binding_survives_full_h1b_chain_and_public_replay(self):
        inputs = self._relocate_plan(
            self._inputs(), "H1/plan-attempt-02/package-manifest.json"
        )
        receipt, _ = self._run(inputs)
        expected = inputs["planned_workspace"].data["artifacts"][
            "plan_manifest"
        ]
        session = json.loads(
            (receipt.package_root / "generation-session.json").read_text(
                encoding="utf-8"
            )
        )
        execution = json.loads(
            (receipt.package_root / "execution-record.json").read_text(
                encoding="utf-8"
            )
        )
        package = json.loads(
            (receipt.package_root / "fragment-package.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(session["plan_manifest"], expected)
        self.assertEqual(execution["plan_manifest"], expected)
        self.assertEqual(package["plan_manifest"], expected)
        self.assertEqual(
            self._validate_published(inputs, receipt.package_root)["verdict"],
            "ready",
        )

    def test_plan_manifest_path_hash_and_parent_mutants_fail_before_session(self):
        mutations = (
            ("wrong-path", "H1/other/package-manifest.json", None),
            ("wrong-name", "H1/plan/manifest.json", None),
            ("backslash", "H1\\plan\\package-manifest.json", None),
            ("escape", "H1/../plan/package-manifest.json", None),
            ("foreign-stage", "P1/plan/package-manifest.json", None),
            ("wrong-hash", None, "0" * 64),
        )
        for name, path, digest in mutations:
            with self.subTest(name=name):
                inputs = self._inputs()
                data = copy.deepcopy(inputs["planned_workspace"].data)
                if path is not None:
                    data["artifacts"]["plan_manifest"]["path"] = path
                if digest is not None:
                    data["artifacts"]["plan_manifest"]["sha256"] = digest
                inputs["planned_workspace"] = self._sealed(
                    data, "H1/h1-workspace-state.json"
                )
                expected_session = self.root / (
                    f"fragment-session-{self.run_index + 1}"
                )
                with self.assertRaisesRegex(
                    h1b.H1BError,
                    "H1B_(?:PLAN_MANIFEST|WORKSPACE)_INVALID",
                ):
                    self._start_only(inputs)
                self.assertFalse(expected_session.exists())

    def test_foreign_physical_plan_parent_fails_before_session(self):
        inputs = self._inputs()
        foreign = self.root / "foreign" / "plan"
        foreign.parent.mkdir(parents=True, exist_ok=True)
        inputs["plan_root"].replace(foreign)
        inputs["plan_root"] = foreign
        expected_session = self.root / f"fragment-session-{self.run_index + 1}"
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_PLAN_MANIFEST_INVALID"
        ):
            self._start_only(inputs)
        self.assertFalse(expected_session.exists())

    def test_rejects_non_planned_workspace(self):
        inputs = self._inputs()
        data = copy.deepcopy(inputs["planned_workspace"].data)
        data["state"] = "fragments_ready"
        inputs["planned_workspace"] = self._sealed(
            data, "H1/h1-workspace-state.json"
        )
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_WORKSPACE_INVALID"
        ):
            self._run(inputs)

    def test_rejects_resealed_plan_when_formal_h1a_evidence_is_invalid(self):
        inputs = self._inputs()
        # The fixture has readable plan/brief/manifest projections, but the
        # formal H1-A validator is authoritative for five-phase evidence and
        # implementation snapshots.
        with mock.patch.object(
            h1b.h1a,
            "validate_plan_package",
            side_effect=ValueError("H1-A generation evidence invalid"),
        ), mock.patch.object(
            h1b.p1_runtime,
            "validate_p1_package",
            return_value={"verdict": "ready"},
        ), mock.patch.dict(
            os.environ,
            {
                "CODEX_TASK_ID": "task-h1b",
                "CODEX_THREAD_ID": "thread-h1b",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(
                h1b.H1BError, "H1B_PLAN_INVALID"
            ):
                h1b.start_fragment_session(
                    self.root / "fake-plan-session",
                    p1_package=inputs["p1"],
                    plan_package=inputs["plan_root"],
                    plan_input_gate=inputs["gate"],
                    plan_workspace_state=inputs["plan_workspace"],
                    workspace_state=inputs["planned_workspace"],
                    runtime=self.runtime,
                )

    def test_rejects_phase_order_drift(self):
        inputs = self._inputs()
        inputs["phases"][0], inputs["phases"][1] = (
            inputs["phases"][1],
            inputs["phases"][0],
        )
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_PHASE_ORDER_INVALID"
        ):
            self._run(inputs)

    def test_finalize_rejects_incomplete_session_and_payload_argument(self):
        inputs = self._inputs()
        session = self._start_only(inputs)
        self._submit_one(inputs, session, inputs["phases"][0])
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_SESSION_INCOMPLETE"
        ):
            self._finalize_only(inputs, session)
        with self.assertRaises(TypeError):
            h1b.run(
                self.root / "illegal-one-shot",
                session_workspace=session,
                p1_package=inputs["p1"],
                plan_package=inputs["plan_root"],
                plan_input_gate=inputs["gate"],
                plan_workspace_state=inputs["plan_workspace"],
                workspace_state=inputs["planned_workspace"],
                phase_submissions=inputs["phases"],
                coordinator=_Coordinator(),
                runtime=self.runtime,
            )

    def test_rejects_duplicate_phase_submit(self):
        inputs = self._inputs()
        session = self._start_only(inputs)
        self._submit_one(inputs, session, inputs["phases"][0])
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_PHASE_ORDER_INVALID"
        ):
            self._submit_one(inputs, session, inputs["phases"][0])

    def test_rejects_cross_identity_phase_submit(self):
        inputs = self._inputs()
        session = self._start_only(
            inputs, task="task-h1b", thread="thread-original"
        )
        with self.assertRaisesRegex(h1b.H1BError, "H1B_SESSION_INVALID"):
            self._submit_one(
                inputs,
                session,
                inputs["phases"][0],
                task="task-h1b",
                thread="thread-other",
            )

    def test_rejects_old_evidence_tamper_before_next_phase(self):
        inputs = self._inputs()
        session = self._start_only(inputs)
        self._submit_one(inputs, session, inputs["phases"][0])
        self._submit_one(inputs, session, inputs["phases"][1])
        evidence = (
            session
            / "generation-evidence"
            / f"01-{h1b.PHASES[0]}.json"
        )
        value = json.loads(evidence.read_text(encoding="utf-8"))
        value["payload_sha256"] = "f" * 64
        self._write(evidence, value)
        with self.assertRaisesRegex(h1b.H1BError, "H1B_EVIDENCE_INVALID"):
            self._submit_one(inputs, session, inputs["phases"][2])

    def test_rejects_input_change_between_phases(self):
        inputs = self._inputs()
        session = self._start_only(inputs)
        self._submit_one(inputs, session, inputs["phases"][0])
        plan_path = inputs["plan_root"] / "review-plan.json"
        with plan_path.open("a", encoding="utf-8") as stream:
            stream.write(" ")
        with self.assertRaisesRegex(h1b.H1BError, "H1B_INPUT_MUTATED"):
            self._submit_one(inputs, session, inputs["phases"][1])

    def test_rejects_out_of_session_evidence_backfill(self):
        inputs = self._inputs()
        session = self._start_only(inputs)
        backfill = (
            session
            / "generation-evidence"
            / f"03-{h1b.PHASES[2]}.json"
        )
        self._write(backfill, {"forged": True})
        with self.assertRaisesRegex(h1b.H1BError, "H1B_EVIDENCE_INVALID"):
            self._submit_one(inputs, session, inputs["phases"][0])

    def test_rejects_missing_controlled_identity(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(
                h1b.H1BError, "H1B_CONTROLLED_CONTEXT_REQUIRED"
            ):
                h1b._identity()

    def test_rejects_brief_contract_drift(self):
        inputs = self._inputs()
        inputs["phases"][0]["payload"]["brief_contracts"][0][
            "forbidden_additions"
        ] = [
            "选择造成直接后果"
        ]
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_BRIEF_CONTRACT_INVALID"
        ):
            self._run(inputs)

    def test_rejects_source_projection_hash_drift(self):
        inputs = self._inputs()
        ledger = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]["fact_projection_ledger"]
        ledger[0]["field_value_sha256"] = "f" * 64
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_SOURCE_GROUNDING_INVALID"
        ):
            self._run(inputs)

    def test_rejects_anchor_without_fact_projection(self):
        inputs = self._inputs()
        inputs["phases"][0]["payload"]["brief_contracts"][0][
            "source_challenges"
        ][0]["fact_projections"] = []
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_SOURCE_GROUNDING_INVALID"
        ):
            self._run(inputs)

    def test_rejects_pov_or_scene_contract_drift(self):
        inputs = self._inputs()
        contract = inputs["phases"][0]["payload"]["brief_contracts"][0]
        contract["pov_mode"] = "omniscient"
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_BRIEF_CONTRACT_INVALID"
        ):
            self._run(inputs)
        inputs = self._inputs()
        contract = inputs["phases"][0]["payload"]["brief_contracts"][0]
        contract["scene_contract"]["required_choice"] = "服从命令"
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_BRIEF_CONTRACT_INVALID"
        ):
            self._run(inputs)

    def test_rejects_generic_names_and_location_with_true_anchors(self):
        inputs = self._inputs()
        review = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]
        review["fact_projection_ledger"][0]["evidence_quote"] = (
            "林安站在封闭室的门边"
        )
        review["fact_projection_ledger"][0][
            "evidence_quote_sha256"
        ] = h1b.rt.canonical_sha256("林安站在封闭室的门边")
        review["fact_projection_ledger"][0][
            "challenge_result"
        ] = "agent_verified_paraphrase"
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_GENERIC_SOURCE_EVIDENCE"
        ):
            self._run(inputs)

    def test_accepts_agent_verified_legal_paraphrase(self):
        inputs = self._inputs()
        text = inputs["phases"][2]["payload"]["final_fragments"][0][
            "text"
        ].replace(
            "封闭室门锁必须取得双人签名才能开启",
            "第二个签名框空着，单凭一张卡打不开这扇门",
        )
        inputs["phases"][2]["payload"]["final_fragments"][0]["text"] = text
        review = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]
        review["text_sha256"] = h1b.rt.canonical_sha256(text)
        ledger = review["fact_projection_ledger"][1]
        ledger["evidence_quote"] = (
            "第二个签名框空着，单凭一张卡打不开这扇门"
        )
        ledger["evidence_quote_sha256"] = h1b.rt.canonical_sha256(
            ledger["evidence_quote"]
        )
        ledger["challenge_result"] = "agent_verified_paraphrase"
        ledger["challenge_notes"] = (
            "将“双人签名才能开启”转述为缺少第二签名且单卡不能开门。"
        )
        self._run(inputs)

    def test_accepts_process_interiority_without_decisive_answer(self):
        inputs = self._inputs()
        final = inputs["phases"][2]["payload"]["final_fragments"][0]
        final["text"] = final["text"].replace(
            "他没有解释",
            "他不能确定门外的人在等什么。他没有解释",
        )
        review = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]
        review["text_sha256"] = h1b.rt.canonical_sha256(final["text"])
        self._run(inputs)

    def test_rejects_decisive_inner_revelation_even_false_audit(self):
        inputs = self._inputs()
        final = inputs["phases"][2]["payload"]["final_fragments"][0]
        final["text"] += "\n\n林安早已决定牺牲自己。"
        review = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]
        review["text_sha256"] = h1b.rt.canonical_sha256(final["text"])
        self.assertFalse(
            review["boundary_checks"]["decisive_inner_revelation"]
        )
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_DECISIVE_INNER_REVELATION"
        ):
            self._run(inputs)

    def test_rejects_resealed_new_control_fact(self):
        inputs = self._inputs()
        final = inputs["phases"][2]["payload"]["final_fragments"][0]
        final["introduced_control_facts"] = ["门锁由军事法规设立"]
        with self.assertRaises(h1b.H1BError):
            self._run(inputs)

    def test_rejects_surface_detail_escalation(self):
        inputs = self._inputs()
        final = inputs["phases"][2]["payload"]["final_fragments"][0]
        review = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]
        detail = {
            "id": "SURF-1",
            "detail": "红灯代表永久封锁",
            "evidence_quote": "警示灯随即熄灭",
            "authority_status": "fragment_local_non_authoritative",
            "control_effect": "none",
            "scope": "fragment_only",
            "causal_role": "access_decision",
            "history_claim": False,
            "rule_claim": True,
            "relationship_claim": False,
            "reused_across_fragments": False,
        }
        final["surface_details"] = [detail]
        review["surface_details"] = copy.deepcopy(final["surface_details"])
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_SURFACE_DETAIL_INVALID"
        ):
            self._run(inputs)

    def test_rejects_surface_detail_reused_across_fragments(self):
        inputs = self._inputs()
        detail = {
            "id": "SURF-SHARED",
            "detail": "通行卡边缘有一道浅划痕",
            "evidence_quote": "临时通行卡",
            "authority_status": "fragment_local_non_authoritative",
            "control_effect": "none",
            "scope": "fragment_only",
            "causal_role": "none",
            "history_claim": False,
            "rule_claim": False,
            "relationship_claim": False,
            "reused_across_fragments": False,
        }
        for index in (0, 1):
            final = inputs["phases"][2]["payload"][
                "final_fragments"
            ][index]
            review = inputs["phases"][2]["payload"][
                "compliance_reviews"
            ][index]
            final["surface_details"] = [copy.deepcopy(detail)]
            review["surface_details"] = [copy.deepcopy(detail)]
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_SURFACE_DETAIL_REUSED"
        ):
            self._run(inputs)

    def test_opposite_p1_value_rejects_old_projection_and_evidence(self):
        inputs = self._inputs()
        c1_path = inputs["p1"] / "C1.json"
        c1 = json.loads(c1_path.read_text(encoding="utf-8"))
        c1["objects"][0][
            "decision_boundary"
        ] = "紧急状态允许单人直接执行危险指令"
        self._write(c1_path, c1)
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_SOURCE_INVENTORY_INVALID"
        ):
            self._run(inputs)

    def test_rejects_too_short_fragment(self):
        inputs = self._inputs()
        final = inputs["phases"][2]["payload"]["final_fragments"][0]
        final["text"] = "林安把卡放下。"
        review = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]
        review["text_sha256"] = h1b.rt.canonical_sha256(final["text"])
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_FRAGMENT_LENGTH_INVALID"
        ):
            self._run(inputs)

    def test_rejects_english_dominant_text_inside_combined_budget(self):
        brief = self._brief(1)
        brief["target_words_min"] = 100
        brief["target_words_max"] = 300
        text = (
            ("甲" * 25 + "。") * 2
            + "\n\n"
            + ("乙" * 25 + "。") * 2
            + " "
            + " ".join(f"token{index}" for index in range(60))
        )
        self.assertEqual(h1b._visible_units(text)[0], 160)
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_LANGUAGE_CONTRACT_INVALID"
        ):
            h1b._validate_text(text, brief)

    def test_rejects_long_latin_injection_by_combined_budget(self):
        inputs = self._inputs()
        final = inputs["phases"][2]["payload"]["final_fragments"][0]
        final["text"] += " " + " ".join(
            f"overflow{index}" for index in range(100)
        )
        review = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]
        review["text_sha256"] = h1b.rt.canonical_sha256(final["text"])
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_FRAGMENT_LENGTH_INVALID"
        ):
            self._run(inputs)

    def test_accepts_small_latin_term_in_chinese_scene(self):
        inputs = self._inputs()
        final = inputs["phases"][2]["payload"]["final_fragments"][0]
        final["text"] = final["text"].replace("终端上的字", "AI终端上的字")
        review = inputs["phases"][2]["payload"][
            "compliance_reviews"
        ][0]
        review["text_sha256"] = h1b.rt.canonical_sha256(final["text"])
        self._run(inputs)

    def test_combined_visible_unit_min_and_max_boundaries(self):
        brief = self._brief(1)
        minimum = "\n\n".join(["甲" * 64 + "。？"] * 5)
        self.assertEqual(h1b._visible_units(minimum), (320, 320, 0))
        self.assertEqual(h1b._validate_text(minimum, brief), minimum)
        maximum = "\n\n".join(["乙" * 96 + "。？"] * 5)
        self.assertEqual(h1b._visible_units(maximum), (480, 480, 0))
        self.assertEqual(h1b._validate_text(maximum, brief), maximum)

    def test_rejects_missing_brief_fragment(self):
        inputs = self._inputs()
        inputs["phases"][2]["payload"]["final_fragments"].pop()
        inputs["phases"][2]["payload"]["compliance_reviews"].pop()
        with self.assertRaisesRegex(
            h1b.H1BError, "H1B_FRAGMENT_COVERAGE_INVALID"
        ):
            self._run(inputs)

    def test_rejects_markdown_implementation_and_extra_file_tamper(self):
        for mutation, expected in (
            (
                lambda root: (root / "fragments.md").write_text(
                    "tampered", encoding="utf-8"
                ),
                "H1B_FRAGMENT_PACKAGE_INVALID",
            ),
            (
                lambda root: (
                    root / "implementation" / "skill" / "SKILL.md"
                ).write_text("tampered", encoding="utf-8"),
                "H1B_IMPLEMENTATION_STALE",
            ),
            (
                lambda root: (root / "unexpected.txt").write_text(
                    "extra", encoding="utf-8"
                ),
                "H1B_PACKAGE_BOUNDARY_INVALID",
            ),
        ):
            inputs = self._inputs()
            receipt, _ = self._run(inputs)
            mutation(receipt.package_root)
            with self.assertRaisesRegex(h1b.H1BError, expected):
                self._validate_published(inputs, receipt.package_root)

    def test_toctou_input_mutation_prevents_publish(self):
        inputs = self._inputs()
        original_copy = h1b._copy_exact
        changed = {"done": False}

        def mutate_after_snapshot(source, target):
            original_copy(source, target)
            if not changed["done"]:
                changed["done"] = True
                with (inputs["plan_root"] / "review-plan.json").open(
                    "a", encoding="utf-8"
                ) as stream:
                    stream.write(" ")

        with mock.patch.object(h1b, "_copy_exact", mutate_after_snapshot):
            with self.assertRaisesRegex(
                h1b.H1BError,
                "H1B_(?:PLAN_INVALID|PLAN_MANIFEST_INVALID|INPUT_MUTATED)",
            ):
                self._run(inputs)
        self.assertFalse(self.last_output_root.exists())

    def test_coordinator_rejection_preserves_valid_non_current_orphan(self):
        inputs = self._inputs()
        coordinator = _RejectingCoordinator()
        with self.assertRaisesRegex(
            RuntimeError, "coordinator rejected transition"
        ):
            self._run(inputs, coordinator=coordinator)
        orphan = self.last_output_root
        self.assertTrue(orphan.is_dir())
        self.assertEqual(len(coordinator.calls), 1)
        self.assertEqual(
            self._validate_published(inputs, orphan)["verdict"], "ready"
        )

    def test_fragment_projection_changes_only_with_semantic_payload(self):
        inputs = self._inputs()
        anchors = {
            item["id"]: {
                **item,
                "_value": (
                    inputs["character"]
                    if item["id"] == "SRC-000001"
                    else inputs["environment"]
                ),
            }
            for item in inputs["anchors"]
        }
        plan = json.loads(
            (inputs["plan_root"] / "review-plan.json").read_text(
                encoding="utf-8"
            )
        )
        final_fragments = inputs["phases"][2]["payload"][
            "final_fragments"
        ]
        first = h1b._fragment_package(
            plan=plan,
            p1_artifact={
                "path": "P1/stage-completion.json",
                "sha256": "a" * 64,
            },
            plan_manifest={
                "path": "H1/plan/package-manifest.json",
                "sha256": "b" * 64,
            },
            final_fragments=final_fragments,
            anchors=anchors,
        )
        unrelated = copy.deepcopy(anchors)
        unrelated["SRC-000001"]["_value"]["unused_note"] = "不参与片段"
        second = h1b._fragment_package(
            plan=plan,
            p1_artifact=first["p1_completion"],
            plan_manifest=first["plan_manifest"],
            final_fragments=final_fragments,
            anchors=unrelated,
        )
        self.assertEqual(first, second)
        changed_fragments = copy.deepcopy(final_fragments)
        changed_fragments[0]["text"] = changed_fragments[0][
            "text"
        ].replace("不得执行", "可以执行")
        third = h1b._fragment_package(
            plan=plan,
            p1_artifact=first["p1_completion"],
            plan_manifest=first["plan_manifest"],
            final_fragments=changed_fragments,
            anchors=anchors,
        )
        self.assertNotEqual(first, third)

    def test_real_h1a_plan_h1b_and_h1a_assembly_integration(self):
        h1a_tests = importlib.import_module(
            "skills.novel-conception-human-review-assembler.tests."
            "test_v2_runtime"
        )
        case = h1a_tests.H1APlanSkeletonTests(
            methodName="test_plan_requires_exact_initialized_workspace"
        )
        case.setUp()
        case.runtime = h1b.rt.ContractRuntime()
        try:
            p1, initialized, gate, _ = case._formal_inputs()
            control_values = {
                "author-control-baseline.json": "不得越权",
                "S1.json": "选择有果",
                "W1.json": "门禁双签",
                "E1.json": "单签闭锁",
                "T1.json": "核验即停",
                "C1.json": "不可伤人",
            }
            for filename, control in control_values.items():
                path = p1 / filename
                value = json.loads(path.read_text(encoding="utf-8"))
                collection = (
                    value["control_registry"]
                    if filename == "author-control-baseline.json"
                    else value["objects"]
                )
                collection[0]["control"] = control
                case._write(path, value)
            package = json.loads(
                (p1 / "novel-conception-package.json").read_text(
                    encoding="utf-8"
                )
            )
            package["author_control_baseline"] = (
                h1b.rt.artifact_reference(
                    p1 / "author-control-baseline.json", root=p1
                )
            )
            package["canonical_models"] = {
                stage: h1b.rt.artifact_reference(
                    p1 / f"{stage}.json", root=p1
                )
                for stage in ("S1", "W1", "E1", "T1", "C1")
            }
            case._write(p1 / "novel-conception-package.json", package)
            p1_ref = initialized.data["p1_completion"]
            inventory = h1b.h1a.build_source_inventory(
                p1,
                p1_completion={
                    "path": p1_ref["path"],
                    "sha256": p1_ref["sha256"],
                },
            )
            plan = case._plan(inventory, p1_ref, gate.reference)
            phases = [
                {
                    "phase": h1b.h1a.PLAN_PHASES[0],
                    "phase_index": 1,
                    "payload": {
                        "review_requirements": plan[
                            "review_requirements"
                        ],
                        "risk_register": plan["risk_register"],
                    },
                },
                {
                    "phase": h1b.h1a.PLAN_PHASES[1],
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
                    "phase": h1b.h1a.PLAN_PHASES[2],
                    "phase_index": 3,
                    "payload": {
                        key: plan[key]
                        for key in (
                            "visual_models",
                            "fragment_briefs",
                            "decision_prompts",
                            "assembly_projection",
                            "presentation_bindings",
                        )
                    },
                },
                {
                    "phase": h1b.h1a.PLAN_PHASES[3],
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
                    "phase": h1b.h1a.PLAN_PHASES[4],
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
            plan_receipt, _ = case._run_plan(
                p1, initialized, gate, phases
            )
            plan_root = plan_receipt.package_root
            qualified_plan_root = case.root / "H1" / "plan"
            qualified_plan_root.parent.mkdir(parents=True, exist_ok=True)
            plan_root.replace(qualified_plan_root)
            plan_root = qualified_plan_root
            formal_plan = json.loads(
                (plan_root / "review-plan.json").read_text(
                    encoding="utf-8"
                )
            )
            formal_inventory = json.loads(
                (plan_root / "source-inventory.json").read_text(
                    encoding="utf-8"
                )
            )
            plan_manifest = {
                "path": "H1/plan/package-manifest.json",
                "sha256": h1b.rt.sha256_file(
                    plan_root / "package-manifest.json"
                ),
            }
            planned_data = {
                "schema_version": "2.0",
                "run_id": formal_plan["run_id"],
                "stage": "H1",
                "session_id": formal_plan["h1_session_id"],
                "state": "planned",
                "p1_completion": initialized.data["p1_completion"],
                "previous_state_sha256": initialized.reference["sha256"],
                "artifacts": {"plan_manifest": plan_manifest},
            }
            planned = h1b.rt.SealedDocument(
                data=planned_data,
                reference={
                    "path": "H1/planned-workspace-state.json",
                    "sha256": h1b.rt.canonical_sha256(planned_data),
                },
            )
            text = (
                "终端依次亮出六条约束：不得越权、选择有果、门禁双签、单签闭锁、"
                "核验即停、不可伤人。林安没有逐条读完。门外有人催他刷卡，声音"
                "隔着门板发闷，第二签名框仍空着。\n\n"
                "他把卡压在桌上，没有贴近读卡区。对面的人说只是临时处置，出了"
                "问题以后再补手续。林安见过这种“以后”：记录里只会留下签名，"
                "不会留下催促的语气。\n\n"
                "门外又敲了两下。也许真有人等着进来，也许对方只是知道怎样让他"
                "害怕延误。林安的手移到卡边，又停住。他问第二个人在哪里。对面"
                "没有回答，只把卡往前推了一寸。\n\n"
                "他按下复核键。红灯亮起，系统把这次尝试锁进待核队列；门没有开。"
                "对方停止敲门，未核验的命令也停在屏幕上。谁都没有因此安全，"
                "只是没有人能继续假装这是一道无须负责的门。\n\n"
                "林安仍不知道门外的人真正想要什么。他把手留在复核键上，听见"
                "走廊里的脚步远了一点，又折回来。第二签名框依旧空着，门外无人回答。"
            )
            specs = []
            for anchor in formal_inventory["anchors"]:
                source_path = h1b.rt.verify_artifact_reference(
                    anchor["artifact"], root=p1
                )
                source = json.loads(
                    source_path.read_text(encoding="utf-8")
                )
                source_object = h1b._resolve_pointer(
                    source, anchor["json_pointer"]
                )
                specs.append(
                    {
                        "id": f"PROJ-{anchor['id']}",
                        "anchor": anchor,
                        "value": source_object["control"],
                    }
                )
            contracts = []
            drafts = []
            reviews = []
            for brief in formal_plan["fragment_briefs"]:
                contract = {
                    "brief_id": brief["id"],
                    "slot_id": brief["slot_id"],
                    "brief_sha256": h1b.rt.canonical_sha256(brief),
                    "title": brief["title"],
                    "review_purpose": brief["review_purpose"],
                    "language_contract_id": h1b.LANGUAGE_CONTRACT_ID,
                    "style_contract_id": h1b.STYLE_CONTRACT_ID,
                    "depth_contract_id": h1b.DEPTH_CONTRACT_ID,
                    "pov_mode": h1b.POV_MODE,
                    "pov_character_id": brief["pov_character_id"],
                    "information_limits": copy.deepcopy(
                        brief["information_limits"]
                    ),
                    "allowed_perception_channels": copy.deepcopy(
                        brief["allowed_perception_channels"]
                    ),
                    "scene_contract": copy.deepcopy(
                        brief["scene_contract"]
                    ),
                    "decisive_interiority_policy": h1b.INTERIORITY_POLICY,
                    "surface_detail_policy": h1b.SURFACE_DETAIL_POLICY,
                    "target_chars_min": brief["target_words_min"],
                    "target_chars_max": brief["target_words_max"],
                    "source_challenges": [
                        {
                            "source_anchor_id": spec["anchor"]["id"],
                            "value_sha256": spec["anchor"][
                                "value_sha256"
                            ],
                            "story_specific_use": (
                                f"让{spec['value']}进入当前选择"
                            ),
                            "does_not_authorize": "不授权新控制事实",
                            "fact_projections": [
                                {
                                    "id": spec["id"],
                                    "field_pointer": "/control",
                                    "value_sha256": (
                                        h1b.rt.canonical_sha256(
                                            spec["value"]
                                        )
                                    ),
                                    "required_usage": (
                                        f"呈现{spec['value']}"
                                    ),
                                }
                            ],
                        }
                        for spec in specs
                    ],
                    "required_demonstrations": copy.deepcopy(
                        brief["required_demonstrations"]
                    ),
                    "forbidden_additions": copy.deepcopy(
                        brief["forbidden_additions"]
                    ),
                    "opposition_challenge": {
                        "verdict": "compatible",
                        "evidence": "展示受控行为不要求新事实。",
                    },
                    "narrative_scene_design": {
                        "carry_in": "未核验的命令已经抵达执行门槛。",
                        "surface_want": "林安想让真正需要帮助的人进入。",
                        "counterwant_or_fear": "他不愿替不可见的命令承担签名责任。",
                        "interpretive_bias": "他把催促理解成转移责任的惯常手法。",
                        "protective_tactic": "通过追问第二签名和延迟刷卡争取核验时间。",
                        "contradiction_under_pressure": "救援速度与核验责任不能同时满足。",
                        "relationship_or_system_pressure": "门外催促和双签制度共同压迫他的选择。",
                        "beat_progression": [
                            "六条约束在终端集中出现。",
                            "门外催促使时间压力具体化。",
                            "第二签名空缺暴露责任问题。",
                            "林安拒绝刷卡并触发复核。",
                            "闭锁结果让双方停在原地。",
                        ],
                        "turning_pressure": "对方试图把通行卡重新推给林安。",
                        "choice_cost": "拒绝执行可能延误门外真正的需求。",
                        "aftershock": "命令暂停，但门外身份仍然未知。",
                        "source_anchor_ids": copy.deepcopy(
                            brief["source_anchor_ids"]
                        ),
                    },
                }
                draft = {
                    "id": brief["slot_id"],
                    "brief_sha256": h1b.rt.canonical_sha256(brief),
                    "title": brief["title"],
                    "review_purpose": brief["review_purpose"],
                    "text": text,
                    "source_anchor_ids": copy.deepcopy(
                        brief["source_anchor_ids"]
                    ),
                    "surface_details": [],
                    "introduced_control_facts": [],
                }
                review = {
                    "fragment_id": brief["slot_id"],
                    "brief_sha256": h1b.rt.canonical_sha256(brief),
                    "draft_sha256": h1b.rt.canonical_sha256(text),
                    "text_sha256": h1b.rt.canonical_sha256(text),
                    "fact_projection_ledger": [
                        {
                            "fact_projection_id": spec["id"],
                            "source_anchor_id": spec["anchor"]["id"],
                            "source_value_sha256": spec["anchor"][
                                "value_sha256"
                            ],
                            "field_value_sha256": (
                                h1b.rt.canonical_sha256(spec["value"])
                            ),
                            "story_specific_claim": (
                                f"{spec['value']}约束行动"
                            ),
                            "evidence_quote": text,
                            "evidence_quote_sha256": (
                                h1b.rt.canonical_sha256(text)
                            ),
                            "challenge_result": "lexically_grounded",
                            "challenge_notes": (
                                "最终场景原文包含该控制短语并据此改变行动。"
                            ),
                            "control_status": "preserved",
                        }
                        for spec in specs
                    ],
                    "required_demonstrations": [
                        {
                            "requirement": requirement,
                            "fact_projection_ids": [
                                spec["id"] for spec in specs
                            ],
                            "finding": "受控行为通过选择与后果呈现。",
                            "evidence_quote": text,
                        }
                        for requirement in brief[
                            "required_demonstrations"
                        ]
                    ],
                    "forbidden_additions": [
                        {
                            "prohibition": prohibition,
                            "verdict": "absent",
                            "check_notes": "只使用 formal P1 projections。",
                        }
                        for prohibition in brief["forbidden_additions"]
                    ],
                    "information_boundary": {
                        "may_present": copy.deepcopy(
                            brief["information_limits"]["may_present"]
                        ),
                        "must_not_present_as_known": copy.deepcopy(
                            brief["information_limits"][
                                "must_not_present_as_known"
                            ]
                        ),
                        "used_perception_channels": ["视觉", "听觉"],
                        "evidence_quotes": [text],
                        "verdict": "passed",
                    },
                    "scene_contract_evidence": [
                        {
                            "field": field,
                            "expected_value": brief["scene_contract"][field],
                            "finding": "场景行动呈现该字段。",
                            "evidence_quote": text,
                        }
                        for field in (
                            "before_state",
                            "immediate_goal",
                            "pressure",
                            "obstacle",
                            "required_choice",
                            "direct_consequence",
                            "after_state",
                        )
                    ],
                    "style_checks": {
                        code: True for code in h1b.STYLE_PRINCIPLES
                    },
                    "narrative_quality_checks": [
                        {
                            "principle": principle,
                            "finding": "现场压力通过人物注意、误判风险和动作选择连续推进。",
                            "evidence_quotes": pair,
                        }
                        for principle, pair in zip(
                            h1b.NARRATIVE_QUALITY_PRINCIPLES,
                            [
                                ["第二签名框仍空着", "不会留下催促的语气"],
                                ["也许真有人等着进来", "也许对方只是知道怎样让他害怕延误"],
                                ["林安见过这种“以后”", "林安的手移到卡边，又停住"],
                                ["只把卡往前推了一寸", "他按下复核键"],
                                ["对面的人说只是临时处置", "对面没有回答"],
                                ["门外又敲了两下", "走廊里的脚步远了一点，又折回来"],
                                ["谁都没有因此安全", "第二签名框依旧空着"],
                                ["没有人能继续假装", "林安仍不知道门外的人真正想要什么"],
                            ],
                        )
                    ],
                    "boundary_checks": {
                        "language_contract_id": h1b.LANGUAGE_CONTRACT_ID,
                        "style_contract_id": h1b.STYLE_CONTRACT_ID,
                        "pov_mode": h1b.POV_MODE,
                        "pov_character_id": brief["pov_character_id"],
                        "decisive_interiority_policy": (
                            h1b.INTERIORITY_POLICY
                        ),
                        "surface_detail_policy": (
                            h1b.SURFACE_DETAIL_POLICY
                        ),
                        "choice_evidence_quote": "他把卡压在桌上",
                        "consequence_evidence_quote": "门没有开",
                        "state_change_evidence_quote": (
                            "未核验的命令也停在屏幕上"
                        ),
                        "decisive_inner_revelation": False,
                        "introduced_control_facts": [],
                        "final_prose_claim": False,
                    },
                    "surface_details": [],
                }
                contracts.append(contract)
                drafts.append(draft)
                reviews.append(review)
            submissions = [
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
            fragment_coordinator = _Coordinator()
            fragment_root = case.root / "real-fragments"
            fragment_session = case.root / "real-fragment-session"
            with mock.patch.object(
                h1b.p1_runtime,
                "validate_p1_package",
                return_value={"verdict": "ready"},
            ), mock.patch.dict(
                os.environ,
                {
                    "CODEX_TASK_ID": "task-real-h1b",
                    "CODEX_THREAD_ID": "thread-real-h1b",
                },
                clear=True,
            ):
                h1b.start_fragment_session(
                    fragment_session,
                    p1_package=p1,
                    plan_package=plan_root,
                    plan_input_gate=gate,
                    plan_workspace_state=initialized,
                    workspace_state=planned,
                    runtime=case.runtime,
                )
                for submission in submissions:
                    h1b.submit_fragment_phase(
                        fragment_session,
                        submission,
                        p1_package=p1,
                        plan_package=plan_root,
                        plan_input_gate=gate,
                        plan_workspace_state=initialized,
                        workspace_state=planned,
                        runtime=case.runtime,
                    )
                fragment_receipt = h1b.run(
                    fragment_root,
                    session_workspace=fragment_session,
                    p1_package=p1,
                    plan_package=plan_root,
                    plan_input_gate=gate,
                    plan_workspace_state=initialized,
                    workspace_state=planned,
                    coordinator=fragment_coordinator,
                    runtime=case.runtime,
                )
            fragment_manifest = {
                "path": "H1/fragments/package-manifest.json",
                "sha256": h1b.rt.sha256_file(
                    fragment_receipt.package_root
                    / "package-manifest.json"
                ),
            }
            ready_data = {
                **copy.deepcopy(planned.data),
                "state": "fragments_ready",
                "previous_state_sha256": planned.reference["sha256"],
                "artifacts": {
                    "plan_manifest": plan_manifest,
                    "fragment_manifest": fragment_manifest,
                },
            }
            ready = h1b.rt.SealedDocument(
                data=ready_data,
                reference={
                    "path": "H1/fragments-ready-state.json",
                    "sha256": h1b.rt.canonical_sha256(ready_data),
                },
            )
            assembly_coordinator = _Coordinator()
            fidelity_review = case._make_fidelity_review(
                p1_completion={
                    "path": initialized.data["p1_completion"]["path"],
                    "sha256": initialized.data["p1_completion"]["sha256"],
                },
                plan_root=plan_root,
                fragment_root=fragment_receipt.package_root,
            )
            with mock.patch.object(
                h1b.h1a.p1_runtime,
                "validate_p1_package",
                return_value={"verdict": "ready"},
            ):
                assembly = h1b.h1a.run_assemble(
                    case.root / "real-assembly",
                    p1_package=p1,
                    plan_package=plan_root,
                    plan_input_gate=gate,
                    plan_workspace_state=initialized,
                    fragment_package=fragment_receipt.package_root,
                    fragment_workspace_state=planned,
                    workspace_state=ready,
                    coordinator=assembly_coordinator,
                    fidelity_review=fidelity_review,
                    runtime=case.runtime,
                )
            self.assertTrue(
                (assembly.package_root / "human-review-report.json").is_file()
            )
            self.assertEqual(
                assembly_coordinator.calls[0]["expected_next_state"],
                "assembled",
            )
        finally:
            case.tearDown()


if __name__ == "__main__":
    unittest.main()
