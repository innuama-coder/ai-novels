from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_ENGINE = _Path(__file__).resolve().parents[2] / "engine"
_sys.path.insert(0, str(_ENGINE))

import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path


ENGINE = Path(__file__).resolve().parents[2] / "engine"
NOVEL = ENGINE.parent / "duanxian"
sys.path.insert(0, str(ENGINE))
RUN_ID = os.environ.get(
    "DUANXIAN_CONCEPTION_RUN_ID", "duanxian-conception-v2-20260802-04"
)
RUN_ROOT = NOVEL / "conception-runs" / RUN_ID
H1_ROOT = RUN_ROOT / "H1"
PLAN_ROOT = H1_ROOT / "plan"
FRAGMENT_ROOT = H1_ROOT / "fragments"
ASSEMBLY_ROOT = H1_ROOT / "assembly"
SESSION_ROOT = H1_ROOT / f"H1-DUANXIAN-{RUN_ID}"
FIDELITY_REVIEW_PATH = Path(
    os.environ.get(
        "DUANXIAN_H1_FIDELITY_REVIEW",
        str(H1_ROOT / "presentation-fidelity-review.candidate.json"),
    )
)

rt = importlib.import_module("harnesses.novel-conception-autonomous.runtime")
prod = importlib.import_module(
    "harnesses.novel-conception-autonomous.runtime.production_orchestrator"
)


def _load_runtime(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ENGINE / relative_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime: {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


h1a = _load_runtime(
    "duanxian_h1a_assemble_runtime",
    "engine/skills/novel-conception-human-review-assembler/scripts/run_v2.py",
)


def main() -> dict[str, object]:
    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if order is None or order.data.get("action") != "H1-A-assemble":
        raise RuntimeError(
            "expected pending H1-A-assemble, got "
            f"{None if order is None else order.data.get('action')}"
        )
    current_workspace = context.store.latest_workspace()
    if current_workspace.data.get("state") != "fragments_ready":
        raise RuntimeError(
            f"expected fragments_ready, got {current_workspace.data.get('state')}"
        )
    initialized_path = SESSION_ROOT / "workspace-initialized.json"
    initialized_workspace = context.store.load_document(
        {
            "path": initialized_path.relative_to(RUN_ROOT).as_posix(),
            "sha256": rt.sha256_file(initialized_path),
        }
    )
    planned_path = SESSION_ROOT / "workspace-planned.json"
    planned_workspace = context.store.load_document(
        {
            "path": planned_path.relative_to(RUN_ROOT).as_posix(),
            "sha256": rt.sha256_file(planned_path),
        }
    )
    plan = json.loads(
        (PLAN_ROOT / "review-plan.json").read_text(encoding="utf-8")
    )
    if plan["work_identity"]["report_title"] != "《断线》小说构思人审报告":
        raise RuntimeError("sealed report title drift")
    if [step["kind"] for step in plan["review_path"]] != [
        "world",
        "storylines",
        "characters",
        "fragments",
        "decision",
    ]:
        raise RuntimeError("sealed four-dimension review path drift")
    plan_gate = context.store.load_document(
        plan["work_identity"]["input_gate"]
    )
    if not FIDELITY_REVIEW_PATH.is_file():
        raise RuntimeError(
            "missing independent presentation fidelity review: "
            f"{FIDELITY_REVIEW_PATH}"
        )
    fidelity_review = json.loads(
        FIDELITY_REVIEW_PATH.read_text(encoding="utf-8")
    )

    def execute(coordinator, _assembly_gate):
        return h1a.run_assemble(
            ASSEMBLY_ROOT,
            p1_package=RUN_ROOT / "P1",
            plan_package=PLAN_ROOT,
            plan_input_gate=plan_gate,
            plan_workspace_state=initialized_workspace,
            fragment_package=FRAGMENT_ROOT,
            fragment_workspace_state=planned_workspace,
            workspace_state=current_workspace,
            coordinator=coordinator,
            logical_package_path="H1/assembly",
            plan_logical_package_path="H1/plan",
            fragment_logical_package_path="H1/fragments",
            fidelity_review=fidelity_review,
            runtime=rt.ContractRuntime(),
        )

    receipt, workspace = prod.commit_h1_workspace(
        context,
        work_order=order,
        actor="novel-conception-human-review-assembler",
        executor=execute,
    )
    report = json.loads(
        (ASSEMBLY_ROOT / "human-review-report.json").read_text(
            encoding="utf-8"
        )
    )
    validation = json.loads(
        (ASSEMBLY_ROOT / "validation.json").read_text(encoding="utf-8")
    )
    return {
        "run_id": RUN_ID,
        "status": "assembled",
        "title": report["title"],
        "review_path": [step["kind"] for step in report["review_path"]],
        "report_json": str(ASSEMBLY_ROOT / "human-review-report.json"),
        "report_markdown": str(ASSEMBLY_ROOT / "human-review-report.md"),
        "validation": str(ASSEMBLY_ROOT / "validation.json"),
        "manifest": workspace.data["artifacts"]["assembly_manifest"],
        "workspace": workspace.reference,
        "workspace_state": workspace.data["state"],
        "verdict": validation["verdict"],
    }


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=2))
