from __future__ import annotations
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));import public_fixture as fx  # noqa:E402
C=fx.C;publisher=fx.ab.publisher
from runtime.package_envelope import validate_completion_bindings,validate_manifest,validate_ready_profile,validate_result_envelope  # noqa:E402
from runtime.canonical import read_json  # noqa:E402
from render_validation import validate_render_model  # noqa:E402

def write(path,value):fx.ab.write_json(path,value)
def tree(root):return {p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob("*") if p.is_file()}
def rewrite_allow(work_path,gate_path,allow,workspace):
    work=read_json(work_path);gate=read_json(gate_path);work["file_allowlist"]=allow;gate["file_allowlist"]=allow;write(gate_path,gate);work["input_gate_ref"]=fx.ab.fref(gate_path,workspace,"input_gate");write(work_path,work);return work
class HH1CRuntimeTests(unittest.TestCase):
    def build(self):self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);return fx.build_c(Path(self.temp.name))
    def test_ready_profile_accessible_chinese_and_envelope(self):
        fixture,work,order,_,_,_=self.build();code,result=C.execute(work);package=fixture.workspace/order["output_directory"]
        self.assertEqual((code,result["result"],result["result_scope"]),(0,"ready","composite_internal"));validate_ready_profile(package,"HH1.C");validate_manifest(package,read_json(package/"package-manifest.json"));validate_result_envelope(result,order)
        self.assertFalse((package/"stage-completion.json").exists());html=(package/"hld-human-review-report.html").read_text(encoding="utf-8");self.assertIn("《小说》故事方案",html);self.assertIn("几条故事怎样碰到一起",html);self.assertNotIn("评审问题：",html);self.assertNotIn("图形文字说明：",html);self.assertNotIn("依据与定位",html);self.assertNotIn("<code>",html);self.assertNotIn(chr(0xfffd),html)
        report=read_json(fixture.workspace/"internal/HH1-A/package/hld-human-review-report.json");registry=read_json(package/"render-target-registry.json");self.assertEqual(validate_render_model(html,report,registry),[]);self.assertEqual(len(registry["targets"]),1+sum(len(report[name]) for name,_ in C.SECTIONS)+len(report["visual_models"]))
    def test_deterministic_across_independent_workspaces(self):
        values=[]
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temp:
                fixture,work,order,_,_,_=fx.build_c(Path(temp));self.assertEqual(C.execute(work)[0],0);values.append(tree(fixture.workspace/order["output_directory"]))
        self.assertEqual(values[0],values[1])
    def test_machine_contract_and_public_cli(self):
        fixture,work,order,_,_,_=self.build();contract=json.loads((C.SKILL_ROOT/"references/runtime-contract.json").read_text(encoding="utf-8"));self.assertEqual(contract["required_roles"],list(C.REQUIRED_ROLES));self.assertEqual(contract["public_entrypoint"]["path"],"skills/novel-hld-html-renderer/scripts/run_skill.py");self.assertEqual(len(C.impl_hash()),64)
        done=subprocess.run([sys.executable,str(C.SKILL_ROOT/"scripts/run_skill.py"),str(work)],capture_output=True,text=True,timeout=60);self.assertEqual((done.returncode,done.stderr),(0,""));self.assertTrue((fixture.workspace/order["output_directory"]/C.SPEC.canonical_name).is_file())
    def test_full_real_a_b_c_publisher_integration_and_byte_copy(self):
        fixture,c_path,c_order,_,a_path,b_path=self.build();self.assertEqual(C.execute(c_path)[0],0);ws=fixture.workspace;(ws/"stage-result.json").unlink(missing_ok=True);tasks=fx.ready_tasks(fixture,a_path,b_path,c_path);publish_order=fixture.publish_order("HH1",tasks);code,result=publisher.execute(publish_order);package=ws/"HH1-package"
        self.assertEqual((code,result["result"]),(0,"ready"));validate_ready_profile(package,"HH1");manifest=read_json(package/"package-manifest.json");completion=read_json(package/"stage-completion.json");validate_manifest(package,manifest);validate_completion_bindings(ws,package,completion)
        for source,target in ((ws/"internal/HH1-A/package/hld-human-review-report.json",package/"hld-human-review-report.json"),(ws/"internal/HH1-B/package/presentation-fidelity-review.json",package/"presentation-fidelity-review.json"),(ws/"internal/HH1-C/package/hld-human-review-report.html",package/"hld-human-review-report.html"),(ws/"internal/HH1-C/package/render-target-registry.json",package/"render-target-registry.json")):self.assertEqual(source.read_bytes(),target.read_bytes())
    def test_extra_missing_and_reordered_reads_fail_hard(self):
        for mode in ("extra","missing","reordered"):
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as temp:
                    fixture,work,order,gate,_,_=fx.build_c(Path(temp));allow=copy.deepcopy(order["file_allowlist"])
                    if mode=="extra":extra=fixture.workspace/"sample-chapter.md";extra.write_text("正文",encoding="utf-8");allow.append(fx.ab.fref(extra,fixture.workspace,"sample_chapter"))
                    elif mode=="missing":allow.pop()
                    else:allow[0],allow[1]=allow[1],allow[0]
                    rewrite_allow(work,gate,allow,fixture.workspace)
                    with self.assertRaises(C.InternalCondition):C.execute(work)
                    self.assertFalse((fixture.workspace/order["output_directory"]).exists())
    def test_report_tamper_with_updated_allow_is_blocked_by_a_manifest(self):
        fixture,work,order,gate,_,_=self.build();report=fixture.workspace/"internal/HH1-A/package/hld-human-review-report.json";value=read_json(report);value["title_and_decision_scope"][0]["conclusion"]="篡改";write(report,value);allow=copy.deepcopy(order["file_allowlist"])
        for item in allow:
            if item["role"]=="human_review_report":item["sha256"]=publisher.sha256(report)
        rewrite_allow(work,gate,allow,fixture.workspace);code,result=C.execute(work);package=fixture.workspace/order["output_directory"]
        self.assertEqual((code,result["result"],result["blocker_class"]),(2,"blocked","upstream_defect"));self.assertFalse((package/C.SPEC.canonical_name).exists())
    def test_duplicate_dom_id_becomes_durable_local_revise(self):
        fixture,work,order,_,_,_=self.build();original=C.render_document
        def duplicate(report,review):document,targets=original(report,review);return document.replace("</body>",'<div id="overall_narrative_architecture"></div></body>'),targets
        with patch.object(C,"render_document",side_effect=duplicate):code,result=C.execute(work)
        package=fixture.workspace/order["output_directory"];self.assertEqual((code,result["result"]),(2,"revise"));self.assertFalse((package/C.SPEC.canonical_name).exists())
    def test_dangling_svg_edge_is_durable_blocked(self):
        fixture,work,order,_,_,_=self.build();original=C.admit
        def inject(context):value=original(context);value=copy.deepcopy(value);value["report"]["visual_models"][0]["edges"][0]["to"]="MISSING";return value
        with patch.object(C,"admit",side_effect=inject):code,result=C.execute(work)
        package=fixture.workspace/order["output_directory"];self.assertEqual((code,result["result"]),(2,"blocked"));self.assertFalse((package/C.SPEC.canonical_name).exists())
    def test_script_and_external_url_content_is_escaped_not_executed(self):
        fixture,work,_,_,_,_=self.build();context=C.load_context(work,C.SPEC,C.impl_hash(),C._catalog());admitted=C.admit(context);report=copy.deepcopy(admitted["report"]);report["overall_narrative_architecture"][0]["conclusion"]='<script src="https://evil.invalid/x.js">alert(1)</script>';report["visual_models"][0]["nodes"][0]["label"]='https://evil.invalid is text';document,targets=C.render_document(report,admitted["review"]);registry={"targets":targets}
        self.assertIn("&lt;script",document);self.assertNotIn('<script src=',document);self.assertNotIn('src="https://',document);self.assertEqual(validate_render_model(document,report,registry),[])
    def test_work_title_story_first_and_natural_visual_type(self):
        fixture,work,_,_,_,_=self.build();context=C.load_context(work,C.SPEC,C.impl_hash(),C._catalog());admitted=C.admit(context);report=copy.deepcopy(admitted["report"]);report["title_and_decision_scope"][0]["conclusion"]="《断线》请作者判断这版高层设计。";story=report["overall_narrative_architecture"][0];story["conclusion"]="顾衡死亡留下材料，R-07 在文字交流中成为自己；现实团队先阻断袭击，沈逾随后完成告别。";document,targets=C.render_document(report,admitted["review"])
        self.assertIn("《断线》故事方案",document);self.assertNotIn("断弦",document);self.assertLess(document.index(story["conclusion"]),document.index("<nav"));self.assertEqual(document.count(story["conclusion"]),1);self.assertNotIn(">architecture ·",document);self.assertNotIn("评审问题：",document);self.assertNotIn("依据与定位",document);self.assertEqual(len(targets),1+sum(len(report[name]) for name,_ in C.SECTIONS)+len(report["visual_models"]));self.assertEqual(validate_render_model(document,report,{"targets":targets}),[])
    def test_character_and_environment_definitions_are_explicit_human_cards(self):
        fixture,work,_,_,_,_=self.build();context=C.load_context(work,C.SPEC,C.impl_hash(),C._catalog());admitted=C.admit(context);report=admitted["report"];document,targets=C.render_document(report,admitted["review"])
        world=report["world_environment_definitions"][0];character=report["character_definitions"][0];environment=report["environment_definitions"][0]
        for text in ("故事发生在怎样的世界",world["name"],world["definition"],"这些人是谁",character["name"],character["story_position"],"这些地方是什么样",environment["name"],environment["story_function"]):
            self.assertIn(text,document)
        for machine_label in ("最显著的特征","当地人怎样生活","仍由作者决定的细节","在故事中的位置","能做什么，不能做什么","它在故事中的作用","谁能进入，什么不能发生"):
            self.assertNotIn(machine_label,document)
        for source_id in world["source_ids"]+character["source_ids"]+environment["source_ids"]:
            self.assertNotIn(source_id,document)
        self.assertIn(C.natural_sentence_list(world["defining_features"]),document)
        self.assertIn(C.natural_sentence_list(world["author_open_details"]),document)
        self.assertNotIn("。；",document)
        self.assertEqual(validate_render_model(document,report,{"targets":targets}),[])

    def test_city_season_and_ordinary_people_are_explicit_reader_sections(self):
        fixture,work,_,_,_,_=self.build();context=C.load_context(work,C.SPEC,C.impl_hash(),C._catalog());admitted=C.admit(context);report=admitted["report"];document,targets=C.render_document(report,admitted["review"])
        city=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="city_and_region");people=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="local_people_and_daily_life");climate=next(item for item in report["world_environment_definitions"] if item["environment_scope"]=="climate_and_physical_environment")
        network=city["city_network"]
        for text in ("四座城市",city["city_stories"][0]["city_name"],city["city_stories"][0]["story"],"人和消息怎样在城市之间移动",city["route_stories"][0]["story"],"生活在四座城市里的人",people["ordinary_people_stories"][0]["city"],people["ordinary_people_stories"][0]["portrait_name"],people["ordinary_people_stories"][0]["story"],"六周里的天气",climate["season_story"]):self.assertIn(text,document)
        self.assertNotIn(network["intercity_links"][0]["information_route"],document)
        self.assertEqual(validate_render_model(document,report,{"targets":targets}),[])

    def test_chapter_design_is_a_human_readable_storyline_card(self):
        fixture,work,_,_,_,_=self.build();context=C.load_context(work,C.SPEC,C.impl_hash(),C._catalog());admitted=C.admit(context);report=admitted["report"];document,targets=C.render_document(report,admitted["review"])
        chapter=next(item for item in report["storyline_choreography"] if item["element_kind"]=="chapter_design")
        for text in (chapter["visual_role"],"这一章要讲清什么",chapter["core_content"],"这一章推进哪些故事","本章结束时发生的变化",chapter["chapter_end_change"]):
            self.assertIn(text,document)
        role_labels={"primary":"主要推进","supporting":"同时推进","background":"形成背景压力","preserved_open":"继续悬而未决"}
        for storyline in chapter["storylines"]:
            self.assertIn(role_labels[storyline["role"]],document);self.assertIn(storyline["name"],document)
        for source_id in chapter["source_ids"]:
            self.assertNotIn(source_id,document)
        self.assertNotIn("chapter_storyline_plan",document);self.assertNotIn("章节壳",document);self.assertEqual(validate_render_model(document,report,{"targets":targets}),[])

    def test_visible_language_gate_rejects_split_machine_phrase_and_duplicates(self):
        fixture,work,_,_,_,_=self.build();context=C.load_context(work,C.SPEC,C.impl_hash(),C._catalog());admitted=C.admit(context);report=admitted["report"];document,targets=C.render_document(report,admitted["review"]);registry={"targets":targets}
        split=document.replace("</main>","<p>顾衡线负责留下证据<em>入口</em>。</p></main>")
        self.assertTrue(any("machine/process" in error for error in validate_render_model(split,report,registry)))
        repeated="沈逾必须亲自决定是否继续与眼前这个生命交谈。"
        duplicate=document.replace("</main>",f"<p>{repeated}</p><p>{repeated}</p></main>")
        self.assertTrue(any("repeats substantive" in error for error in validate_render_model(duplicate,report,registry)))
        ai_memo=document.replace("</main>","<p>把人物关系投影到叙事链路，并与后续工作流对齐。</p></main>")
        self.assertTrue(any("machine/process" in error for error in validate_render_model(ai_memo,report,registry)))
    def test_sealed_earlier_hp1_hq2_revisions_are_valid_consumer_inputs(self):
        fixture,work,_,_,_,_=self.build();context=C.load_context(work,C.SPEC,C.impl_hash(),C._catalog());report=read_json(context.roles["human_review_report"]);review=read_json(context.roles["presentation_fidelity_review"]);hp1=read_json(context.roles["novel_hld_package"]);hp1_completion=read_json(context.roles["hp1_completion"]);hq2=read_json(context.roles["lld_handoff_acceptance"]);hq2_completion=read_json(context.roles["hq2_completion"])
        earlier=copy.deepcopy(hq2);earlier["revision"]=context.work_order["revision"]-7;C._validate_identity(context,report,review,hp1,hp1_completion,earlier,hq2_completion)
        stale_report=copy.deepcopy(report);stale_report["revision"]-=1
        with self.assertRaises(C.InternalCondition):C._validate_identity(context,stale_report,review,hp1,hp1_completion,earlier,hq2_completion)
    def test_b_nonready_prefix_publishes_without_c_issue(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture,b_path,b_order,_,b_draft,_=fx.ab.build_b(Path(temp),"fail");self.assertEqual(fx.ab.B.execute(b_path,b_draft)[0],2);ws=fixture.workspace;a_path=ws/next(item["path"] for item in b_order["file_allowlist"] if item["role"]=="hh1_a_work_order");a=fx.task_fixture("HH1-A",ws,a_path,("hld-human-review-report.json",));b_work=read_json(b_path);b_pkg=ws/b_work["output_directory"];b=fx.ab.PUBTEST.TaskFixture("HH1-B",b_path,b_work,b_pkg.parent/"stage-result.json",b_pkg/"result-manifest.json",());(ws/"stage-result.json").unlink(missing_ok=True);publish=fixture.publish_order("HH1",[a,b]);code,result=publisher.execute(publish)
            self.assertEqual((code,result["result"]),(2,"blocked"));self.assertFalse((ws/"internal/HH1-C").exists());self.assertFalse((ws/"HH1-package/hld-human-review-report.html").exists())
    def test_c_nonready_prefix_publishes_without_canonical(self):
        fixture,c_path,_,_,a_path,b_path=self.build();original=C.render_document
        def duplicate(report,review):document,targets=original(report,review);return document.replace("</body>",'<div id="overall_narrative_architecture"></div></body>'),targets
        with patch.object(C,"render_document",side_effect=duplicate):self.assertEqual(C.execute(c_path)[0],2)
        ws=fixture.workspace;c_work=read_json(c_path);c_pkg=ws/c_work["output_directory"];tasks=fx.ready_tasks(fixture,a_path,b_path,c_path)[:2]+[fx.ab.PUBTEST.TaskFixture("HH1-C",c_path,c_work,c_pkg.parent/"stage-result.json",c_pkg/"result-manifest.json",())];(ws/"stage-result.json").unlink(missing_ok=True);publish=fixture.publish_order("HH1",tasks);code,result=publisher.execute(publish)
        self.assertEqual((code,result["result"]),(2,"revise"));self.assertFalse((ws/"HH1-package/hld-human-review-report.html").exists())

if __name__=="__main__":unittest.main()
