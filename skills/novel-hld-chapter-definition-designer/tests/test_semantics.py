from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("hd1_run",ROOT/"scripts/run_skill.py")
assert SPEC and SPEC.loader
HD1=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(HD1)


def ref(stage:str)->dict[str,str]:return {"role":f"upstream::{stage}::main","path":f"{stage}.json","sha256":"0"*64}


def chapter(number:int,chapter_id:str,title:str,parent:str,character:str,environment:str,event:str,key_function:str)->dict:
    before={"story_state":f"第{number}章开始前的故事状态","character_state":f"第{number}章开始前的人物状态","knowledge_state":f"第{number}章开始前的认知状态","pressure_state":f"第{number}章开始前的压力状态","available_actions":["继续调查"]}
    after={"story_state":f"第{number}章结束后的故事状态","character_state":f"第{number}章结束后的人物状态","knowledge_state":f"第{number}章结束后的认知状态","pressure_state":f"第{number}章结束后的压力状态","available_actions":["承担后果"]}
    return {
        "id":f"HDF-{number:02d}","chapter_id":chapter_id,"chapter_number":number,"working_title":title,"parent_unit_id":parent,
        "source_refs":[f"SRC-CH-{number:02d}"],
        "narrative_necessity":f"迫使人物在第{number}次压力中作出无法撤回的选择", "entry_state":before,"time_scope":f"第{number}个连续行动时段","place_scope":[environment],"exit_state":after,
        "storyline_roles":{"primary_storyline_id":"STORY-A","supporting_storyline_ids":[],"background_storyline_ids":[],"preserved_open_storyline_ids":[]},
        "pov_contract":{"hi1_assignment_id":f"HPV-CH-{number:02d}","focal_character_id":character,"pov_mode":"第三人称限知","may_know":[f"人物亲历的第{number}项事实"],"must_not_know":[f"对手隐藏的第{number}项计划"],"reader_knows_before":[f"第{number}章前的有限事实"],"reader_knows_after":[f"第{number}章后新增的事实"]},
        "dramatic_contract":{"choice_actor_ids":[character],"institutional_choice_actors":[],"cost_bearer_ids":[character],"immediate_goal":f"第{number}章人物必须取得关键线索","active_opposition":f"第{number}章对手封锁线索来源","pressure_escalation":f"第{number}章时间与安全压力同步上升","consequential_choice":f"第{number}章人物决定承担暴露风险","choice_cost":f"第{number}章人物失去安全退路","immediate_consequence":f"第{number}章对手立刻改变追查方式","irreversible_change":f"第{number}章留下不可撤回的具体后果"},
        "story_development":{"required_developments":["完成本章具体发展"],"information_revealed":[f"揭示第{number}条事实"],"information_withheld":[f"保留第{number}个疑问"],"fair_clues":[f"留下第{number}个公平线索"],"relationship_changes":[f"第{number}组关系发生具体变化"]},
        "memory_design":None,
        "chapter_end_hook":f"第{number}章结尾出现新的迫近危险","unresolved_question":f"第{number}章仍未查清幕后来源","next_chapter_necessity":f"第{number+1}章必须处理上一章留下的后果",
        "references":{"character_ids":[character],"environment_ids":[environment],"event_ids":[event],"key_function_ids":[key_function]},
        "lld_handoff":{"scene_design_must_solve":[f"呈现第{number}章选择与代价的因果"],"freedoms":[f"第{number}章可以设计自然对白"],"prohibitions":[f"第{number}章不得改变既定结果"],"acceptance_criteria":[f"第{number}章结束状态必须成立"]},
    }


class ChapterDefinitionSemanticsTests(unittest.TestCase):
    def setUp(self)->None:
        self.temp=tempfile.TemporaryDirectory();self.workspace=Path(self.temp.name);HD1._WORKSPACE=self.workspace
        shells=[{"id":"HCH-01","parent_unit_id":"HNU-01","source_refs":["SRC-CH-01"]},{"id":"HCH-02","parent_unit_id":"HNU-02","source_refs":["SRC-CH-02"]}]
        plans=[{"chapter_id":"HCH-01","chapter_number":1,"working_title":"第一章","parent_unit_id":"HNU-01","primary_storyline_id":"STORY-A","supporting_storyline_ids":[],"background_storyline_ids":[],"preserved_open_storyline_ids":[],"source_refs":["SRC-CH-01"]},{"chapter_id":"HCH-02","chapter_number":2,"working_title":"第二章","parent_unit_id":"HNU-02","primary_storyline_id":"STORY-A","supporting_storyline_ids":[],"background_storyline_ids":[],"preserved_open_storyline_ids":[],"source_refs":["SRC-CH-02"]}]
        values={"HA1":{"chapter_shells":shells,"environment":"ENV-01","event":"EV-01"},"HS1":{"chapter_storyline_plan":plans,"event":"EV-01"},"HC1":{"character_participation_register":[{"id":"HAS-PART-01","character_id":"CHAR-01"}],"chapter_agency_contracts":[{"id":"HAS-AGENCY-01","chapter_id":"HCH-01","parent_unit_id":"HNU-01","focal_character_ids":["CHAR-01"],"choice_actor_ids":["CHAR-01"],"institutional_choice_actors":[],"cost_bearer_ids":["CHAR-01"],"information_paths":[{"character_id":"CHAR-01","acquisition_modes":["perceived"],"limit":"限于人物可知"}]},{"id":"HAS-AGENCY-02","chapter_id":"HCH-02","parent_unit_id":"HNU-02","focal_character_ids":["CHAR-01"],"choice_actor_ids":["CHAR-01"],"institutional_choice_actors":[],"cost_bearer_ids":["CHAR-01"],"information_paths":[{"character_id":"CHAR-01","acquisition_modes":["perceived"],"limit":"限于人物可知"}]}],"event":"EV-01"},"HI1":{"chapter_pov_assignments":[{"id":"HPV-CH-01","chapter_id":"HCH-01","parent_unit_id":"HNU-01","hc1_agency_contract_id":"HAS-AGENCY-01","pov_character_id":"CHAR-01","focalization_mode":"第三人称限知","knowledge_acquisition_modes":["perceived"],"perception_limits":["限于人物可知"]},{"id":"HPV-CH-02","chapter_id":"HCH-02","parent_unit_id":"HNU-02","hc1_agency_contract_id":"HAS-AGENCY-02","pov_character_id":"CHAR-01","focalization_mode":"第三人称限知","knowledge_acquisition_modes":["perceived"],"perception_limits":["限于人物可知"]}]},"HR1":{"environment":"ENV-01","event":"EV-01"},"HK1":{"key_scene_functions":[{"id":"HKF-01"}],"environment":"ENV-01","event":"EV-01"}}
        for stage,value in values.items():(self.workspace/f"{stage}.json").write_text(json.dumps(value),encoding="utf-8")
        definitions=[chapter(1,"HCH-01","第一章","HNU-01","CHAR-01","ENV-01","EV-01","HKF-01"),chapter(2,"HCH-02","第二章","HNU-02","CHAR-01","ENV-01","EV-01","HKF-01")]
        first,second=definitions
        link={"id":"HDC-01","from_chapter_id":"HCH-01","to_chapter_id":"HCH-02","inherited_change":first["dramatic_contract"]["irreversible_change"],"unresolved_pressure":first["exit_state"]["pressure_state"],"continuity_requirement":second["entry_state"]["story_state"],"why_next_cannot_be_skipped":first["next_chapter_necessity"]}
        self.model={"source_artifacts":[ref(stage) for stage in values],"derivation_claims":[],"chapter_definitions":definitions,"chapter_chain":[link],"coverage_summary":{"chapter_shell_ids":["HCH-01","HCH-02"],"chapter_definition_ids":["HDF-01","HDF-02"],"storyline_ids":["STORY-A"],"character_ids":["CHAR-01"],"environment_ids":["ENV-01"],"event_ids":["EV-01"],"key_function_ids":["HKF-01"]}}

    def tearDown(self)->None:self.temp.cleanup()

    def test_complete_chain_passes(self)->None:HD1.validate_stage_model(self.model,{})

    def test_shell_identity_drift_fails(self)->None:
        self.model["chapter_definitions"][0]["working_title"]="错误标题"
        with self.assertRaisesRegex(HD1.CandidateError,"HS1 chapter plan"):HD1.validate_stage_model(self.model,{})

    def test_generic_or_duplicate_chapter_job_fails(self)->None:
        self.model["chapter_definitions"][0]["narrative_necessity"]="推进剧情"
        with self.assertRaisesRegex(HD1.CandidateError,"generic chapter definition"):HD1.validate_stage_model(self.model,{})

    def test_unknown_downstream_reference_fails(self)->None:
        self.model["chapter_definitions"][0]["references"]["environment_ids"]=["ENV-MISSING"]
        self.model["chapter_definitions"][0]["place_scope"]=["ENV-MISSING"]
        self.model["coverage_summary"]["environment_ids"]=["ENV-MISSING","ENV-01"]
        with self.assertRaisesRegex(HD1.CandidateError,"unknown environment_ids"):HD1.validate_stage_model(self.model,{})

    def test_chain_must_bind_exact_adjacent_state(self)->None:
        self.model["chapter_chain"][0]["inherited_change"]="笼统地承接上一章"
        with self.assertRaisesRegex(HD1.CandidateError,"inherited_change does not exactly bind"):HD1.validate_stage_model(self.model,{})

    def test_unrelated_chapter_authority_fails(self)->None:
        self.model["chapter_definitions"][0]["source_refs"]=["DEV-UNRELATED"]
        with self.assertRaisesRegex(HD1.CandidateError,"HA1/HS1 authority"):HD1.validate_stage_model(self.model,{})

    def test_derivation_claim_must_bind_target_chapter_authority(self)->None:
        self.model["chapter_definitions"][0]["source_refs"].append("DEV-UNRELATED")
        self.model["derivation_claims"]=[{"id":"CLM-01","source_refs":["DEV-UNRELATED"],"target_locator":"/chapter_definitions/0/dramatic_contract/irreversible_change","value_sha256":"0"*64}]
        with self.assertRaisesRegex(HD1.CandidateError,"derivation sources do not cite"):HD1.validate_stage_model(self.model,{})

    def test_chapter_pov_must_exactly_bind_hi1(self)->None:
        self.model["chapter_definitions"][0]["pov_contract"]["focal_character_id"]="CHAR-OTHER"
        self.model["chapter_definitions"][0]["references"]["character_ids"]=["CHAR-OTHER"]
        with self.assertRaisesRegex(HD1.CandidateError,"exactly bind HI1"):HD1.validate_stage_model(self.model,{})

    def test_choice_actor_and_cost_bearer_must_be_explicit(self)->None:
        self.model["chapter_definitions"][0]["dramatic_contract"]["choice_actor_ids"]=["CHAR-OTHER"]
        with self.assertRaisesRegex(HD1.CandidateError,"explicit chapter character references"):HD1.validate_stage_model(self.model,{})

    def test_choice_actor_must_be_authorized_by_hc1(self)->None:
        hc1=json.loads((self.workspace/"HC1.json").read_text(encoding="utf-8"))
        hc1["character_participation_register"].append({"id":"HAS-PART-02","character_id":"CHAR-OTHER"})
        (self.workspace/"HC1.json").write_text(json.dumps(hc1),encoding="utf-8")
        definition=self.model["chapter_definitions"][0]
        definition["dramatic_contract"]["choice_actor_ids"]=["CHAR-OTHER"]
        definition["references"]["character_ids"].append("CHAR-OTHER")
        self.model["coverage_summary"]["character_ids"].append("CHAR-OTHER")
        with self.assertRaisesRegex(HD1.CandidateError,"HC1-unauthorized actor"):
            HD1.validate_stage_model(self.model,{})

    def test_institutional_choice_actor_must_exactly_bind_hc1(self)->None:
        actor={"actor_role":"第三国急救人员","source_refs":["SRC-CH-01"],"responsibility":"维持伤员循环并确认尚未脑死亡","authority_limit":"只负责现场急救，不决定证据归属"}
        hc1=json.loads((self.workspace/"HC1.json").read_text(encoding="utf-8"))
        hc1["chapter_agency_contracts"][0]["choice_actor_ids"]=[]
        hc1["chapter_agency_contracts"][0]["institutional_choice_actors"]=[actor]
        (self.workspace/"HC1.json").write_text(json.dumps(hc1),encoding="utf-8")
        dramatic=self.model["chapter_definitions"][0]["dramatic_contract"]
        dramatic["choice_actor_ids"]=[]
        dramatic["institutional_choice_actors"]=[actor]
        HD1.validate_stage_model(self.model,{})
        dramatic["institutional_choice_actors"][0]["authority_limit"]="越权决定证据归属"
        with self.assertRaisesRegex(HD1.CandidateError,"institutional choice actors"):
            HD1.validate_stage_model(self.model,{})

    def test_choice_requires_named_or_institutional_actor(self)->None:
        dramatic=self.model["chapter_definitions"][0]["dramatic_contract"]
        dramatic["choice_actor_ids"]=[]
        dramatic["institutional_choice_actors"]=[]
        with self.assertRaisesRegex(HD1.CandidateError,"named or institutional actor"):
            HD1.validate_stage_model(self.model,{})


if __name__=="__main__":unittest.main()
