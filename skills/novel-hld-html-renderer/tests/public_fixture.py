from __future__ import annotations
import importlib,json,sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO))
ab=importlib.import_module("skills.novel-hld-review-report-assembler.tests.public_fixture")
C=__import__("skills.novel-hld-html-renderer.scripts.hh1c_runtime",fromlist=["*"])

def build_c(root:Path):
    fixture,b_path,b_order,_,b_draft,_=ab.build_b(root);code,_=ab.B.execute(b_path,b_draft)
    if code!=0:raise AssertionError("HH1-B fixture failed")
    ws=fixture.workspace;a_path=ws/next(item["path"] for item in b_order["file_allowlist"] if item["role"]=="hh1_a_work_order");hp1=ws/"HP1-package";hq2=ws/"HQ2-package";hb0=ws/"HB0-package";a=ws/"internal/HH1-A/package";b=ws/"internal/HH1-B/package"
    paths={"hb0_completion":hb0/"stage-completion.json","hp1_completion":hp1/"stage-completion.json","hp1_manifest":hp1/"package-manifest.json","novel_hld_package":hp1/"novel-hld-package.json","hq2_completion":hq2/"stage-completion.json","hq2_manifest":hq2/"package-manifest.json","lld_handoff_acceptance":hq2/"lld-handoff-acceptance.json","human_review_report":a/"hld-human-review-report.json","hh1_a_manifest":a/"package-manifest.json","hh1_a_generation_session":a/"generation-session.json","hh1_a_work_order":a_path,"presentation_fidelity_review":b/"presentation-fidelity-review.json","hh1_b_manifest":b/"package-manifest.json","hh1_b_review_session":b/"review-session.json","hh1_b_work_order":b_path}
    allow=[ab.fref(paths[role],ws,role) for role in C.REQUIRED_ROLES];path,order,gate=ab.work_order(ws,C.SKILL,C.VERSION,C.impl_hash(),allow,"internal/HH1-C/package","TASK-HH1-C",42)
    return fixture,path,order,gate,a_path,b_path

def task_fixture(kind:str,workspace:Path,work_path:Path,mains:tuple[str,...]):
    work=json.loads(work_path.read_text(encoding="utf-8"));package=workspace/work["output_directory"]
    return ab.PUBTEST.TaskFixture(kind,work_path,work,package.parent/"stage-result.json",package/"package-manifest.json",tuple(package/name for name in mains))

def ready_tasks(fixture,a_path:Path,b_path:Path,c_path:Path):
    ws=fixture.workspace
    return [task_fixture("HH1-A",ws,a_path,("hld-human-review-report.json",)),task_fixture("HH1-B",ws,b_path,("presentation-fidelity-review.json",)),task_fixture("HH1-C",ws,c_path,("hld-human-review-report.html","render-target-registry.json"))]
