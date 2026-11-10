from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
ASSEMBLER_DIR = SKILL_DIR.parent / "novel-conception-human-review-assembler"
ASSEMBLER_TESTS = ASSEMBLER_DIR / "tests"
sys.path.insert(0, str(SCRIPTS))

from common import ContractError, STYLE_CONTRACT, load_json, sha256_file, sha256_text, write_json  # noqa: E402
from manage_writing import (  # noqa: E402
    validate_drafts,
    validate_revision,
    validate_scene_contracts,
)
from validate_fragments import validate_package  # noqa: E402

_assembler_spec = importlib.util.spec_from_file_location(
    "assembler_test_helpers",
    ASSEMBLER_TESTS / "test_workflow.py",
)
assert _assembler_spec and _assembler_spec.loader
_assembler_helpers = importlib.util.module_from_spec(_assembler_spec)
_fragment_common = sys.modules.pop("common")
sys.path.insert(0, str(ASSEMBLER_DIR / "scripts"))
try:
    _assembler_spec.loader.exec_module(_assembler_helpers)
finally:
    sys.path.remove(str(ASSEMBLER_DIR / "scripts"))
    sys.modules["common"] = _fragment_common
make_plan_package = _assembler_helpers.make_plan_package
make_upstream = _assembler_helpers.make_upstream


FINAL_TEXTS = {
    "HR-FRAG-01": (
        "许可灯在林澈指下熄灭。隔着门，周遥把证件贴上结霜的玻璃。"
        "“再核一次。”她说。\n\n"
        "备用电源只剩一格。林澈没有抬闸，而是把核验结果推到她能看见的位置。"
        "广播随即中断，门内的倒计时亮了起来。"
    ),
    "HR-FRAG-02": (
        "周遥把纸面证据推过窄台。林澈没有接，只让她念出最后一行。"
        "她读到编号时停了一下。\n\n"
        "警报逼近第二遍。周遥把纸留在台上，转身去扶被困的人。"
        "林澈这才调出自己的核验记录，两份时间戳第一次对上。"
    ),
    "HR-FRAG-03": (
        "闸门只剩最后十秒。林澈的手停在越权键上，系统仍要求第二份许可。"
        "周遥站在门外，没有催他。\n\n"
        "他按下去，把自己的工号留在记录顶端。闸门升起半米，被困者依次爬过。"
        "屏幕随后收走了他的权限，空白处只剩责任人的名字。"
    ),
}


def scene_contracts(briefs: dict) -> dict:
    fragments = []
    for slot in briefs["slots"]:
        fragments.append(
            {
                "id": slot["id"],
                "style_contract_id": STYLE_CONTRACT["id"],
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
                "information_limit": "只呈现指定 POV 当下可以获得的信息。",
                "allowed_sensory_channels": ["视觉", "听觉"],
                "forbidden_sensory_channels": [],
                "creative_choices": [
                    {
                        "choice": "以许可灯和窄台承载局部动作。",
                        "authorization_basis": slot["allowed_creative_freedom"][0],
                    }
                ],
                "source_ids": slot["required_source_ids"],
                "control_ids": slot["control_ids"],
                "unit_ids": slot["unit_ids"],
            }
        )
    return {
        "schema_version": "1.0",
        "phase": "scene-contracts",
        "style_contract": STYLE_CONTRACT,
        "fragments": fragments,
    }


def drafts(briefs: dict, contracts: dict) -> dict:
    contract_by_id = {item["id"]: item for item in contracts["fragments"]}
    fragments = []
    for slot in briefs["slots"]:
        final = FINAL_TEXTS[slot["id"]]
        draft = final.replace("。", "，", 1)
        fragments.append(
            {
                "id": slot["id"],
                "title": slot["title"],
                "text": draft,
                "source_ids": slot["required_source_ids"],
                "control_ids": slot["control_ids"],
                "unit_ids": slot["unit_ids"],
                "creative_choices": contract_by_id[slot["id"]]["creative_choices"],
                "introduced_authoritative_facts": [],
            }
        )
    return {
        "schema_version": "1.0",
        "phase": "drafts",
        "style_contract": STYLE_CONTRACT,
        "fragments": fragments,
    }


def audit_entries(fragment_id: str, text: str, targets: list[str]) -> dict:
    quotes = {
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
            "屏幕随后收走了他的权限",
            "周遥站在门外，没有催他",
        ],
    }[fragment_id]
    keys = [
        "orientation",
        "pressure_or_goal",
        "turning_choice",
        "consequence_or_state_change",
        "pov_and_information",
    ]
    target_keys = {
        "world_in_action": "world_in_action",
        "story_causality": "causal_progression",
        "character_agency": "character_agency",
        "relationship_change": "relationship_change",
        "narrative_contract": "narrative_contract",
        "ending_nature": "ending_nature",
    }
    result = {}
    for index, key in enumerate(keys):
        result[key] = {
            "finding": f"文本以页面证据完成{key}。",
            "evidence_quote": quotes[index],
        }
    for index, target in enumerate(targets):
        key = target_keys[target]
        result[key] = {
            "finding": f"片段直接验证{target}。",
            "evidence_quote": quotes[(index + 1) % len(quotes)],
        }
    return result


def revision_audit(briefs: dict, draft_data: dict) -> dict:
    draft_by_id = {item["id"]: item for item in draft_data["fragments"]}
    fragments = []
    for slot in briefs["slots"]:
        draft = draft_by_id[slot["id"]]
        text = FINAL_TEXTS[slot["id"]]
        scene_audit = audit_entries(slot["id"], text, slot["coverage_targets"])
        orientation_quote = scene_audit["orientation"]["evidence_quote"]
        consequence_quote = scene_audit["consequence_or_state_change"][
            "evidence_quote"
        ]
        choice_quote = scene_audit["turning_choice"]["evidence_quote"]
        fragments.append(
            {
                "id": slot["id"],
                "title": slot["title"],
                "draft_sha256": sha256_text(draft["text"]),
                "final_text": text,
                "source_ids": draft["source_ids"],
                "control_ids": draft["control_ids"],
                "unit_ids": draft["unit_ids"],
                "creative_choices": draft["creative_choices"],
                "introduced_authoritative_facts": [],
                "contract_checks": {
                    "source_grounding": True,
                    "narrative_contract": True,
                    "no_new_authority": True,
                    "review_question_fit": True,
                },
                "scene_audit": scene_audit,
                "brief_compliance": {
                    "final_text_sha256": sha256_text(text),
                    "before_state": {
                        "value": slot["before_state"],
                        "evidence_quote": orientation_quote,
                    },
                    "after_state": {
                        "value": slot["after_state"],
                        "evidence_quote": consequence_quote,
                    },
                    "required_facts": [
                        {
                            "fact": fact,
                            "finding": "该事实通过人物选择或现场反馈进入正文。",
                            "evidence_quote": choice_quote,
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
                        "change": "强化选择后立即出现的权限或关系变化。",
                        "reason": "让片段的前后状态可以直接检查。",
                    }
                ],
            }
        )
    return {
        "schema_version": "1.0",
        "phase": "revision-audit",
        "style_contract": STYLE_CONTRACT,
        "fragments": fragments,
    }


class FragmentWriterWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.r1, _ = make_upstream(self.root)
        self.plan = make_plan_package(self.root, self.r1)
        self.briefs = load_json(self.plan / "fragment-briefs.json")
        self.contracts = scene_contracts(self.briefs)
        self.draft_data = drafts(self.briefs, self.contracts)
        self.audit_data = revision_audit(self.briefs, self.draft_data)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_command(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [sys.executable, *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def make_workspace(self) -> Path:
        workspace = self.root / "writing"
        self.run_command(
            str(SCRIPTS / "manage_writing.py"),
            "begin",
            str(self.plan),
            str(self.r1),
            str(workspace),
            "--executor-id",
            "fragment-executor",
            "--task-id",
            "fragment-task",
        )
        for phase, data in (
            ("scene-contracts", self.contracts),
            ("drafts", self.draft_data),
            ("revision-audit", self.audit_data),
        ):
            payload = self.root / f"{phase}.json"
            write_json(payload, data)
            self.run_command(
                str(SCRIPTS / "manage_writing.py"),
                "submit",
                str(workspace),
                phase,
                str(payload),
            )
        return workspace

    def make_package(self) -> Path:
        workspace = self.make_workspace()
        output = self.root / "fragment-package"
        self.run_command(
            str(SCRIPTS / "finalize_fragments.py"),
            str(workspace),
            str(output),
        )
        return output

    def test_full_workflow_and_assembler_handoff(self) -> None:
        output = self.make_package()
        evidence = validate_package(output, self.plan, self.r1)
        self.assertEqual(len(evidence["fragments"]), 3)
        self.assertEqual(
            evidence["fixed_style_contract"], "restrained-concrete-scene-v1"
        )
        assembly = self.root / "assembly"
        self.run_command(
            str(ASSEMBLER_DIR / "scripts" / "assemble_human_review.py"),
            str(self.plan),
            str(output),
            str(assembly),
            "--r1",
            str(self.r1),
        )
        result = load_json(assembly / "validation.json")
        self.assertEqual(result["verdict"], "ready")

    def test_style_contract_is_not_overridable(self) -> None:
        data = copy.deepcopy(self.contracts)
        data["style_contract"]["name"] = "华丽抒情"
        with self.assertRaisesRegex(ContractError, "style contract was changed"):
            validate_scene_contracts(data, {item["id"]: item for item in self.briefs["slots"]})

    def test_pov_mismatch_is_blocked(self) -> None:
        data = copy.deepcopy(self.contracts)
        data["fragments"][0]["pov"] = "OTHER"
        with self.assertRaisesRegex(ContractError, "POV mismatch"):
            validate_scene_contracts(data, {item["id"]: item for item in self.briefs["slots"]})

    def test_state_contract_must_match_brief(self) -> None:
        data = copy.deepcopy(self.contracts)
        data["fragments"][0]["start_value"] = "另一个前状态"
        with self.assertRaisesRegex(ContractError, "start value does not match brief"):
            validate_scene_contracts(
                data,
                {item["id"]: item for item in self.briefs["slots"]},
            )

    def test_creative_choice_requires_authorization(self) -> None:
        data = copy.deepcopy(self.contracts)
        data["fragments"][0]["creative_choices"][0]["authorization_basis"] = "新增世界事实"
        with self.assertRaisesRegex(ContractError, "no brief authorization"):
            validate_scene_contracts(data, {item["id"]: item for item in self.briefs["slots"]})

    def test_phase_order_is_hard(self) -> None:
        workspace = self.root / "order-workspace"
        self.run_command(
            str(SCRIPTS / "manage_writing.py"),
            "begin",
            str(self.plan),
            str(self.r1),
            str(workspace),
            "--executor-id",
            "fragment-executor",
            "--task-id",
            "fragment-task",
        )
        payload = self.root / "drafts-early.json"
        write_json(payload, self.draft_data)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "manage_writing.py"),
                "submit",
                str(workspace),
                "drafts",
                str(payload),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("next phase must be scene-contracts", result.stderr)

    def test_new_authoritative_fact_is_blocked(self) -> None:
        data = copy.deepcopy(self.audit_data)
        data["fragments"][0]["introduced_authoritative_facts"] = ["新增机构"]
        with self.assertRaisesRegex(ContractError, "introduces authoritative facts"):
            validate_revision(
                data,
                {item["id"]: item for item in self.briefs["slots"]},
                self.draft_data,
            )

    def test_stale_draft_hash_is_blocked(self) -> None:
        data = copy.deepcopy(self.audit_data)
        data["fragments"][0]["draft_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "draft hash mismatch"):
            validate_revision(
                data,
                {item["id"]: item for item in self.briefs["slots"]},
                self.draft_data,
            )

    def test_missing_target_audit_is_blocked(self) -> None:
        data = copy.deepcopy(self.audit_data)
        del data["fragments"][0]["scene_audit"]["world_in_action"]
        with self.assertRaisesRegex(ContractError, "missing audit keys"):
            validate_revision(
                data,
                {item["id"]: item for item in self.briefs["slots"]},
                self.draft_data,
            )

    def test_fake_audit_quote_is_blocked(self) -> None:
        data = copy.deepcopy(self.audit_data)
        data["fragments"][0]["scene_audit"]["orientation"][
            "evidence_quote"
        ] = "正文里不存在的句子"
        with self.assertRaisesRegex(ContractError, "quote not found"):
            validate_revision(
                data,
                {item["id"]: item for item in self.briefs["slots"]},
                self.draft_data,
            )

    def test_prohibited_fact_in_final_text_is_blocked(self) -> None:
        data = copy.deepcopy(self.audit_data)
        fragment = data["fragments"][0]
        prohibited = self.briefs["slots"][0]["prohibited_facts"][0]
        fragment["final_text"] += f"\n\n{prohibited}。"
        fragment["brief_compliance"]["final_text_sha256"] = sha256_text(
            fragment["final_text"]
        )
        with self.assertRaisesRegex(ContractError, "contains prohibited fact"):
            validate_revision(
                data,
                {item["id"]: item for item in self.briefs["slots"]},
                self.draft_data,
            )

    def test_required_fact_audit_must_match_brief(self) -> None:
        data = copy.deepcopy(self.audit_data)
        data["fragments"][0]["brief_compliance"]["required_facts"] = []
        with self.assertRaisesRegex(ContractError, "required fact audit does not match brief"):
            validate_revision(
                data,
                {item["id"]: item for item in self.briefs["slots"]},
                self.draft_data,
            )

    def test_markdown_in_prose_is_blocked(self) -> None:
        output = self.make_package()
        package_path = output / "fragment-package.json"
        package = load_json(package_path)
        package["fragments"][0]["text"] = "## 场景\n\n" + package["fragments"][0]["text"]
        write_json(package_path, package)
        with self.assertRaisesRegex(ContractError, "not derived"):
            validate_package(output, self.plan, self.r1)

    def test_cliche_is_blocked_before_finalization(self) -> None:
        data = copy.deepcopy(self.audit_data)
        text = data["fragments"][0]["final_text"].replace(
            "门内的倒计时亮了起来", "空气仿佛凝固，门内的倒计时亮了起来"
        )
        data["fragments"][0]["final_text"] = text
        data["fragments"][0]["brief_compliance"][
            "final_text_sha256"
        ] = sha256_text(text)
        data["fragments"][0]["scene_audit"]["consequence_or_state_change"][
            "evidence_quote"
        ] = "门内的倒计时亮了起来"
        validate_revision(
            data,
            {item["id"]: item for item in self.briefs["slots"]},
            self.draft_data,
        )
        workspace = self.root / "cliche-workspace"
        workspace.mkdir()
        with self.assertRaisesRegex(ContractError, "mechanical clichés"):
            from common import validate_style_text

            validate_style_text(
                text,
                self.briefs["slots"][0],
                "HR-FRAG-01",
            )

    def test_too_short_prose_is_blocked(self) -> None:
        from common import validate_style_text

        with self.assertRaises(ContractError):
            validate_style_text(
                "灯灭了。门开了。\n\n他走了。人散了。",
                self.briefs["slots"][0],
                "short",
            )

    def test_disallowed_source_is_blocked(self) -> None:
        data = copy.deepcopy(self.draft_data)
        data["fragments"][0]["source_ids"].append("O1")
        with self.assertRaisesRegex(ContractError, "disallowed sources"):
            validate_drafts(
                data,
                {item["id"]: item for item in self.briefs["slots"]},
                self.contracts,
            )

    def test_execution_tampering_is_blocked(self) -> None:
        output = self.make_package()
        path = output / "execution-record.json"
        record = load_json(path)
        record["task_id"] = "forged-task"
        write_json(path, record)
        with self.assertRaisesRegex(ContractError, "task mismatch"):
            validate_package(output, self.plan, self.r1)

    def test_final_package_is_deterministic_from_audit(self) -> None:
        output = self.make_package()
        path = output / "fragment-package.json"
        package = load_json(path)
        package["fragments"][1]["title"] = "擅自改题"
        write_json(path, package)
        with self.assertRaisesRegex(ContractError, "not derived"):
            validate_package(output, self.plan, self.r1)


if __name__ == "__main__":
    unittest.main()
