from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("hc1_run", ROOT / "scripts/run_skill.py")
assert SPEC and SPEC.loader
HC1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HC1)


class ChapterAgencySemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        HC1._WORKSPACE = self.workspace
        HC1._WORK_ORDER = None
        (self.workspace / "HA1.json").write_text(json.dumps({
            "chapter_shells": [
                {"id": "HCH-01", "parent_unit_id": "HNU-01", "source_refs": ["SRC-CH-01"]},
                {"id": "HCH-02", "parent_unit_id": "HNU-01", "source_refs": ["SRC-CH-02"]},
            ],
        }), encoding="utf-8")
        (self.workspace / "HS1.json").write_text(json.dumps({
            "chapter_storyline_plan": [
                {"chapter_id": "HCH-01", "source_refs": ["SRC-CH-01"]},
                {"chapter_id": "HCH-02", "source_refs": ["SRC-CH-02"]},
            ],
        }), encoding="utf-8")
        self.model = {
            "source_artifacts": [
                {"role": "upstream::HA1::main", "path": "HA1.json"},
                {"role": "upstream::HS1::main", "path": "HS1.json"},
            ],
            "authority_partition": {"source_projection": ["HAS-ARC-A-START"]},
            "derivation_claims": [
                {"id": "HDC-PART", "target_locator": "/character_participation_register"},
                {"id": "HDC-AGENCY", "target_locator": "/chapter_agency_contracts"},
            ],
            "character_participation_register": [
                {"id": "HAS-PART-A", "character_id": "CHR-A", "importance": "core", "responsibilities": ["负责核验关键线索"]},
                {"id": "HAS-PART-B", "character_id": "CHR-B", "importance": "support", "responsibilities": ["负责接收正式记录"]},
            ],
            "arc_state_models": [{"character_id": "CHR-A"}],
            "arc_steps": [
                {"id": "HAS-ARC-A-START" if role == "start" else f"HAS-STEP-{role}", "character_id": "CHR-A", "role": role,
                 "pressure": "p", "choice": "c", "cost": "k", "consequence": "r",
                 "unit_id": "HNU-01", "event_id": "EV-01", "storyline_segment_id": "HTS-01"}
                for role in ("start", "pressure", "choice", "cost", "result")
            ],
            "relationship_steps": [],
            "chapter_agency_contracts": [
                self.agency("01", "HCH-01", "CHR-A", unavailable=[]),
                self.agency("02", "HCH-02", "CHR-B", unavailable=["CHR-A"]),
            ],
        }

    @staticmethod
    def agency(number: str, chapter: str, focal: str, unavailable: list[str]) -> dict:
        return {
            "id": f"HAS-AGENCY-{number}", "chapter_id": chapter, "parent_unit_id": "HNU-01",
            "source_refs": [f"SRC-CH-{number}"],
            "focal_character_ids": [focal], "choice_actor_ids": [focal], "institutional_choice_actors": [],
            "cost_bearer_ids": ["CHR-A"], "unavailable_character_ids": unavailable,
            "information_paths": [{
                "character_id": focal, "acquisition_modes": ["perceived"],
                "limit": "只允许角色当时能够感知的事实",
            }],
        }

    def tearDown(self) -> None:
        HC1._WORK_ORDER = None
        self.temp.cleanup()

    def bind_return_resolution(self, affected_ids: list[str] | None = None) -> None:
        affected_ids = affected_ids or ["HAS-PARTICIPATION-A", "HAS-PARTICIPATION-B"]
        binding = {
            "affected_ids": affected_ids,
            "completion_condition": "参与角色精确覆盖",
            "exact_owner": "HC1",
            "group_id": "HRG-TEST",
        }
        raw = json.dumps(binding, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        (self.workspace / "return-binding.json").write_bytes(raw)
        HC1._WORK_ORDER = {
            "mode": "return_resolution",
            "return_binding": {
                "path": "return-binding.json",
                "role": "return_binding",
                "sha256": hashlib.sha256(raw).hexdigest(),
            },
        }
        if all(item.startswith("HAS-PARTICIPATION-") for item in affected_ids):
            self.model["character_participation_register"][0]["id"] = "HAS-PARTICIPATION-A"
            self.model["character_participation_register"][1]["id"] = "HAS-PARTICIPATION-B"
        base = deepcopy(self.model)
        main_raw = json.dumps(base, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        (self.workspace / "return-base.json").write_bytes(main_raw)
        manifest = {"status": "ready"}
        manifest_raw = json.dumps(manifest, separators=(",", ":")).encode("utf-8")
        (self.workspace / "return-base-manifest.json").write_bytes(manifest_raw)
        main_ref = {"path": "return-base.json", "role": "character_arc_placement", "sha256": hashlib.sha256(main_raw).hexdigest()}
        manifest_ref = {"path": "return-base-manifest.json", "role": "package_manifest", "sha256": hashlib.sha256(manifest_raw).hexdigest()}
        completion = {"stage": "HC1", "status": "ready", "canonical_artifacts": [main_ref], "manifest_ref": manifest_ref}
        completion_raw = json.dumps(completion, separators=(",", ":")).encode("utf-8")
        (self.workspace / "return-base-completion.json").write_bytes(completion_raw)
        HC1._WORK_ORDER["file_allowlist"] = [
            {**main_ref, "role": "return_base::HC1::main"},
            {**manifest_ref, "role": "return_base::HC1::manifest"},
            {"path": "return-base-completion.json", "role": "return_base::HC1::completion", "sha256": hashlib.sha256(completion_raw).hexdigest()},
        ]

    def test_return_binding_requires_exact_participation_ids_and_character_mapping(self) -> None:
        self.bind_return_resolution()
        HC1.validate_stage_model(deepcopy(self.model), {})

        for mutation in ("missing", "renamed", "reordered", "wrong_character"):
            with self.subTest(mutation=mutation):
                mutant = deepcopy(self.model)
                if mutation == "missing":
                    mutant["character_participation_register"].pop()
                elif mutation == "renamed":
                    mutant["character_participation_register"][0]["id"] = "HAS-PART-A"
                elif mutation == "reordered":
                    mutant["character_participation_register"].reverse()
                else:
                    mutant["character_participation_register"][0]["character_id"] = "CHR-B"
                with self.assertRaises(HC1.CandidateError):
                    HC1.validate_stage_model(mutant, {})

    def test_return_binding_hash_drift_fails(self) -> None:
        self.bind_return_resolution()
        HC1._WORK_ORDER["return_binding"]["sha256"] = "f" * 64
        with self.assertRaisesRegex(HC1.CandidateError, "hash mismatch"):
            HC1.validate_stage_model(deepcopy(self.model), {})

    def test_return_binding_role_drift_fails(self) -> None:
        self.bind_return_resolution()
        HC1._WORK_ORDER["return_binding"]["role"] = "wrong_return_binding"
        with self.assertRaisesRegex(HC1.CandidateError, "exact return binding"):
            HC1.validate_stage_model(deepcopy(self.model), {})

    def test_return_binding_accepts_exact_chapter_agency_targets_in_model_order(self) -> None:
        self.bind_return_resolution(["HAS-AGENCY-01", "HAS-AGENCY-02"])
        HC1.validate_stage_model(deepcopy(self.model), {})

        for affected_ids in (
            ["HAS-AGENCY-02", "HAS-AGENCY-01"],
            ["HAS-AGENCY-01", "HAS-AGENCY-MISSING"],
            ["HAS-AGENCY-01", "HAS-PARTICIPATION-A"],
        ):
            with self.subTest(affected_ids=affected_ids):
                self.bind_return_resolution(affected_ids)
                with self.assertRaises(HC1.CandidateError):
                    HC1.validate_stage_model(deepcopy(self.model), {})

    def test_return_binding_rejects_unaffected_chapter_agency_drift(self) -> None:
        self.bind_return_resolution(["HAS-AGENCY-02"])
        mutant = deepcopy(self.model)
        mutant["chapter_agency_contracts"][0]["constraints"] = ["未经授权的返工漂移"]
        with self.assertRaisesRegex(HC1.CandidateError, "unaffected chapter agency"):
            HC1.validate_stage_model(mutant, {})

    def test_return_binding_rejects_partial_prior_hc1_base(self) -> None:
        self.bind_return_resolution(["HAS-AGENCY-01"])
        HC1._WORK_ORDER["file_allowlist"].pop()
        with self.assertRaisesRegex(HC1.CandidateError, "partial prior HC1 base"):
            HC1.validate_stage_model(deepcopy(self.model), {})

    def test_return_binding_accepts_exact_agency_plus_arc_targets(self) -> None:
        affected = ["HAS-AGENCY-02", "HAS-ARC-A-START"]
        self.bind_return_resolution(affected)
        mutant = deepcopy(self.model)
        mutant["chapter_agency_contracts"][1]["constraints"] = ["只修正目标章节的信息权限"]
        mutant["arc_steps"][0]["event_id"] = "EV-02"
        HC1.validate_stage_model(mutant, {})

    def test_combined_return_rejects_wrong_target_order_or_unknown_target(self) -> None:
        for affected in (
            ["HAS-ARC-A-START", "HAS-AGENCY-02"],
            ["HAS-AGENCY-02", "HAS-ARC-MISSING"],
            ["HAS-AGENCY-02", "HAS-PARTICIPATION-A", "HAS-ARC-A-START"],
        ):
            with self.subTest(affected=affected):
                self.bind_return_resolution(affected)
                with self.assertRaises(HC1.CandidateError):
                    HC1.validate_stage_model(deepcopy(self.model), {})

    def test_combined_return_rejects_unaffected_agency_or_arc_drift(self) -> None:
        affected = ["HAS-AGENCY-02", "HAS-ARC-A-START"]
        self.bind_return_resolution(affected)
        for field, index in (("chapter_agency_contracts", 0), ("arc_steps", 1)):
            with self.subTest(field=field):
                mutant = deepcopy(self.model)
                mutant[field][index]["unexpected_drift"] = True
                with self.assertRaisesRegex(HC1.CandidateError, "unaffected"):
                    HC1.validate_stage_model(mutant, {})

    def test_combined_return_rejects_unrelated_semantic_drift(self) -> None:
        self.bind_return_resolution(["HAS-AGENCY-02", "HAS-ARC-A-START"])
        mutant = deepcopy(self.model)
        mutant["relationship_steps"] = [{"id": "HRS-DRIFT"}]
        with self.assertRaisesRegex(HC1.CandidateError, "unaffected semantic field"):
            HC1.validate_stage_model(mutant, {})

        mutant = deepcopy(self.model)
        mutant["derivation_claims"][0]["target_locator"] = "/arc_state_models"
        with self.assertRaisesRegex(HC1.CandidateError, "derivation claim"):
            HC1.validate_stage_model(mutant, {})

    def test_combined_return_allows_only_target_derivation_claim_refresh(self) -> None:
        self.bind_return_resolution(["HAS-AGENCY-02", "HAS-ARC-A-START"])
        mutant = deepcopy(self.model)
        mutant["derivation_claims"][1]["value_sha256"] = "a" * 64
        HC1.validate_stage_model(mutant, {})

        mutant = deepcopy(self.model)
        mutant["derivation_claims"][1]["target_locator"] = "/relationship_steps"
        with self.assertRaisesRegex(HC1.CandidateError, "derivation claim target changed"):
            HC1.validate_stage_model(mutant, {})

    def test_combined_return_requires_complete_prior_base(self) -> None:
        self.bind_return_resolution(["HAS-AGENCY-02", "HAS-ARC-A-START"])
        HC1._WORK_ORDER["file_allowlist"] = []
        with self.assertRaisesRegex(HC1.CandidateError, "require an exact prior HC1 base"):
            HC1.validate_stage_model(deepcopy(self.model), {})

    def test_exact_chapter_agency_coverage_passes(self) -> None:
        HC1.validate_stage_model(deepcopy(self.model), {})

    def test_missing_or_reordered_chapter_contract_fails(self) -> None:
        mutant = deepcopy(self.model)
        mutant["chapter_agency_contracts"].reverse()
        with self.assertRaisesRegex(HC1.CandidateError, "one ordered chapter agency"):
            HC1.validate_stage_model(mutant, {})

    def test_unavailable_character_cannot_focalize_or_choose(self) -> None:
        mutant = deepcopy(self.model)
        mutant["chapter_agency_contracts"][1]["focal_character_ids"] = ["CHR-A"]
        mutant["chapter_agency_contracts"][1]["choice_actor_ids"] = ["CHR-A"]
        mutant["chapter_agency_contracts"][1]["information_paths"][0]["character_id"] = "CHR-A"
        with self.assertRaisesRegex(HC1.CandidateError, "unavailable character"):
            HC1.validate_stage_model(mutant, {})

    def test_information_paths_must_exactly_cover_focal_characters(self) -> None:
        mutant = deepcopy(self.model)
        mutant["chapter_agency_contracts"][1]["information_paths"][0]["character_id"] = "CHR-A"
        with self.assertRaisesRegex(HC1.CandidateError, "exactly cover focal"):
            HC1.validate_stage_model(mutant, {})

    def test_source_bound_institutional_actor_can_make_the_choice(self) -> None:
        contract = self.model["chapter_agency_contracts"][1]
        contract["choice_actor_ids"] = []
        contract["institutional_choice_actors"] = [{
            "actor_role": "第三国急救人员",
            "source_refs": ["SRC-CH-02"],
            "responsibility": "维持伤员循环并确认尚未脑死亡",
            "authority_limit": "只负责现场急救，不决定证据归属或后续记忆使用",
        }]
        HC1.validate_stage_model(deepcopy(self.model), {})

    def test_choice_cannot_have_no_named_or_institutional_actor(self) -> None:
        contract = self.model["chapter_agency_contracts"][1]
        contract["choice_actor_ids"] = []
        contract["institutional_choice_actors"] = []
        with self.assertRaisesRegex(HC1.CandidateError, "named or institutional actor"):
            HC1.validate_stage_model(deepcopy(self.model), {})

    def test_institutional_actor_requires_chapter_local_authority(self) -> None:
        contract = self.model["chapter_agency_contracts"][1]
        contract["source_refs"].append("SRC-OTHER")
        contract["choice_actor_ids"] = []
        contract["institutional_choice_actors"] = [{
            "actor_role": "第三国警方",
            "source_refs": ["SRC-OTHER"],
            "responsibility": "依法封存现场和原始设备",
            "authority_limit": "只负责现场保全，不解释记忆内容",
        }]
        with self.assertRaisesRegex(HC1.CandidateError, "lacks this chapter's HA1/HS1 authority"):
            HC1.validate_stage_model(deepcopy(self.model), {})

    def test_participation_responsibility_cannot_reintroduce_lifecycle_state(self) -> None:
        claims = [
            "角色死亡后由其他人接手任务", "角色牺牲前保留决定权", "角色尚未脑死亡",
            "角色仍然活着", "角色处于昏迷状态", "角色后来苏醒", "角色恢复意识",
            "角色死了以后由别人接手任务",
            "负责记录角色 survival 状态", "角色 was sacrificed", "角色 is brain-dead",
            "角色 remains unconscious", "角色 recovery 未定", "角色 resurrection 未定",
            "角色 is deceased",
        ]
        for claim in claims:
            with self.subTest(claim=claim):
                mutant = deepcopy(self.model)
                mutant["character_participation_register"][0]["responsibilities"].append(claim)
                with self.assertRaisesRegex(HC1.CandidateError, "natural Chinese duty sentence"):
                    HC1.validate_stage_model(mutant, {})

    def test_participation_responsibility_rejects_unexplained_english_prose(self) -> None:
        for claim in ("负责取得 consent", "负责记录 pending 状态", "负责 downstream review"):
            with self.subTest(claim=claim):
                mutant = deepcopy(self.model)
                mutant["character_participation_register"][0]["responsibilities"].append(claim)
                with self.assertRaisesRegex(HC1.CandidateError, "natural Chinese duty sentence"):
                    HC1.validate_stage_model(mutant, {})

    def test_participation_responsibility_requires_explicit_duty_form(self) -> None:
        for claim in ("核验关键线索", "角色死了以后由别人接手任务", "国家层面的责任不能由项目组宣布"):
            with self.subTest(claim=claim):
                mutant = deepcopy(self.model)
                mutant["character_participation_register"][0]["responsibilities"] = [claim]
                with self.assertRaisesRegex(HC1.CandidateError, "beginning with '负责'"):
                    HC1.validate_stage_model(mutant, {})

    def test_participation_responsibility_rejects_out_of_world_design_jargon(self) -> None:
        claims = [
            "负责维持现实失败路径", "负责推动剧情并制造悬念", "负责承担叙事功能",
            "负责回收伏笔并形成高潮", "负责让读者理解故事线",
        ]
        for claim in claims:
            with self.subTest(claim=claim):
                mutant = deepcopy(self.model)
                mutant["character_participation_register"][0]["responsibilities"] = [claim]
                with self.assertRaisesRegex(HC1.CandidateError, "describing an in-world duty"):
                    HC1.validate_stage_model(mutant, {})

    def test_antagonist_in_world_duty_remains_legal(self) -> None:
        duties = [
            "负责保护备用节点、清理痕迹，并阻止两国团队取得完整证据",
            "负责推进跨境证据核验",
            "负责回收已封存的故障设备",
        ]
        for duty in duties:
            with self.subTest(duty=duty):
                mutant = deepcopy(self.model)
                mutant["character_participation_register"][0]["responsibilities"] = [duty]
                HC1.validate_stage_model(mutant, {})

    def test_story_native_single_letter_names_remain_legal(self) -> None:
        mutant = deepcopy(self.model)
        mutant["character_participation_register"][0]["responsibilities"] = [
            "负责核验 R-07 提供的线索，并向 C 国和 M 国通报可确认的事实"
        ]
        HC1.validate_stage_model(mutant, {})

    def test_lifecycle_limits_remain_legal_in_chapter_agency(self) -> None:
        contract = self.model["chapter_agency_contracts"][1]
        contract["constraints"] = ["角色仍在昏迷且尚未脑死亡，只能作为代价承担者"]
        contract["information_paths"][0]["limit"] = "只能通过记录得知角色仍然活着，不能假定其苏醒"
        HC1.validate_stage_model(deepcopy(self.model), {})


if __name__ == "__main__":
    unittest.main()
