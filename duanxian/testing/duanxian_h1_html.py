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
from typing import Any


ENGINE = Path(__file__).resolve().parents[2] / "engine"
NOVEL = ENGINE.parent / "duanxian"
sys.path.insert(0, str(ENGINE))
RUN_ID = os.environ.get(
    "DUANXIAN_CONCEPTION_RUN_ID", "duanxian-conception-v2-20260811-18"
)
RUN_ROOT = NOVEL / "conception-runs" / RUN_ID
RUN_ROOT_EXTENDED = Path(
    r"\\?\C:\Users\54256213\Documents\github\ai-novels\projects"
    r"\duanxian\conception-runs\duanxian-conception-v2-20260811-18"
)
H1_ROOT = RUN_ROOT_EXTENDED / "H1"
PLAN_ROOT = H1_ROOT / "plan-attempt-03"
FRAGMENT_ROOT = H1_ROOT / "fragments-attempt-04"
ASSEMBLY_ROOT = H1_ROOT / "assembly-attempt-03"
HTML_ROOT = H1_ROOT / "html-attempt-02"
RESULT = Path(r"C:\tmp\run18-h1c-rev033-formal-result.json")
INITIALIZED = {
    "path": "H1/H1-IMPLEMENTATION-8c833df39b06486bd7e5/workspace-initialized.json",
    "sha256": "8796a4937185ce32f60653d7f7220f817056cff8a0778b5d8d29fe37d0471b39",
}
PLANNED = {
    "path": "H1/H1-IMPLEMENTATION-8c833df39b06486bd7e5/workspace-planned.json",
    "sha256": "21c3f4417b4a8e103781c098874bbda8c9e96e77e9c6a12d1721cab90108a68d",
}
FRAGMENTS_READY = {
    "path": (
        "H1/H1-IMPLEMENTATION-8c833df39b06486bd7e5/"
        "workspace-fragments_ready-7a39861db8c17885f7b10fcb.json"
    ),
    "sha256": "2460cacc09413d712804712c5e27bdee5f0e56ca2c2ef9ffb65fa499264103fd",
}
ASSEMBLED = {
    "path": "H1/H1-IMPLEMENTATION-8c833df39b06486bd7e5/workspace-assembled.json",
    "sha256": "adaf3b160b1f8b96e9aecc9f828dcf735fd3ab25987951a5280268a3e8a1999f",
}
EXPECTED_ORDER = {
    "path": "orchestration/work-orders/c8a4e983475e1054b40bb0f3.json",
    "sha256": "f1ea4a342953482c5aaaeeef7bbfd58dd6f5d8a666b5f945335fb783953f5bb7",
}

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


h1c = _load_runtime(
    "duanxian_h1c_html_runtime",
    "engine/skills/novel-conception-review-html-generator/scripts/run_v2.py",
)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _load_workspace(context: Any, session_root: Path, state: str):
    path = session_root / f"workspace-{state}.json"
    return context.store.load_document(
        rt.artifact_reference(path, root=RUN_ROOT)
    )


def main() -> dict[str, Any]:
    if os.environ.get("DUANXIAN_CONCEPTION_RUN_ID") != RUN_ID:
        raise RuntimeError(f"DUANXIAN_CONCEPTION_RUN_ID must be {RUN_ID}")
    if os.environ.get("CODEX_TASK_ID") != "/root/run18_t1_v24_attempt08_candidate":
        raise RuntimeError("controlled CODEX_TASK_ID drift")
    if os.environ.get("CODEX_THREAD_ID") != "019ffa15-31f8-7f71-865a-ec128bc822d1":
        raise RuntimeError("controlled CODEX_THREAD_ID drift")
    if RESULT.exists() or HTML_ROOT.exists():
        raise RuntimeError("fresh H1-C output required")

    context = prod.resume_production_run(RUN_ROOT)
    order = context.store.pending_work_order()
    if (
        order is None
        or order.reference != EXPECTED_ORDER
        or order.data.get("action") != "H1-C"
    ):
        raise RuntimeError(
            "expected pending H1-C, got "
            f"{None if order is None else order.data.get('action')}"
        )
    current_workspace = context.store.latest_workspace()
    if (
        current_workspace.reference != ASSEMBLED
        or current_workspace.data.get("state") != "assembled"
    ):
        raise RuntimeError(
            f"expected assembled, got {current_workspace.data.get('state')}"
        )

    initialized_workspace = context.store.load_document(INITIALIZED)
    planned_workspace = context.store.load_document(PLANNED)
    fragments_ready_workspace = context.store.load_document(FRAGMENTS_READY)

    plan = _read(PLAN_ROOT / "review-plan.json")
    report = _read(ASSEMBLY_ROOT / "human-review-report.json")
    expected_title = "《断线》构思人审报告"
    expected_path = [
        "world",
        "storylines",
        "characters",
        "fragments",
        "decision",
    ]
    if report.get("title") != expected_title:
        raise RuntimeError("sealed report title drift")
    if [item.get("kind") for item in report.get("review_path", [])] != expected_path:
        raise RuntimeError("sealed four-dimension review path drift")
    serialized_report = json.dumps(report, ensure_ascii=False)
    if "迁移评审" in serialized_report or "兼容" in serialized_report:
        raise RuntimeError("migration/compatibility content leaked into H1 report")
    roles = [item.get("semantic_role") for item in report["visual_models"]]
    if len(roles) != 5 or set(roles) != set(h1c.SEMANTIC_ROLES):
        raise RuntimeError(f"sealed visual role coverage drift: {roles}")

    plan_gate = context.store.load_document(
        plan["work_identity"]["input_gate"]
    )

    def execute(coordinator: Any, _html_gate: Any):
        return h1c.run(
            HTML_ROOT,
            p1_package=RUN_ROOT_EXTENDED / "P1",
            plan_package=PLAN_ROOT,
            plan_input_gate=plan_gate,
            plan_workspace_state=initialized_workspace,
            fragment_package=FRAGMENT_ROOT,
            fragment_workspace_state=planned_workspace,
            assembly_package=ASSEMBLY_ROOT,
            assembly_workspace_state=fragments_ready_workspace,
            workspace_state=current_workspace,
            coordinator=coordinator,
            logical_package_path="H1/html-attempt-02",
            plan_logical_package_path="H1/plan-attempt-03",
            fragment_logical_package_path="H1/fragments-attempt-04",
            assembly_logical_package_path="H1/assembly-attempt-03",
            plan_active_return_request=context.active_return,
            active_return_request=context.active_return,
            runtime=rt.ContractRuntime(),
        )

    receipt, rendered_workspace = prod.commit_h1_workspace(
        context,
        work_order=order,
        actor="novel-conception-review-html-generator",
        executor=execute,
    )

    independent_validation = h1c.validate_html_package(
        HTML_ROOT,
        p1_package=RUN_ROOT_EXTENDED / "P1",
        plan_package=PLAN_ROOT,
        plan_input_gate=plan_gate,
        plan_workspace_state=initialized_workspace,
        fragment_package=FRAGMENT_ROOT,
        fragment_workspace_state=planned_workspace,
        assembly_package=ASSEMBLY_ROOT,
        assembly_workspace_state=fragments_ready_workspace,
        workspace_state=current_workspace,
        plan_logical_package_path="H1/plan-attempt-03",
        fragment_logical_package_path="H1/fragments-attempt-04",
        assembly_logical_package_path="H1/assembly-attempt-03",
        plan_active_return_request=context.active_return,
        runtime=rt.ContractRuntime(),
    )
    document = (HTML_ROOT / "human-review-report.html").read_text(
        encoding="utf-8"
    )
    document_validation = h1c.validate_html_document(document, report)
    if document != h1c.render_html(report):
        raise RuntimeError("independent deterministic rerender mismatch")
    if "迁移评审" in document or "兼容" in document:
        raise RuntimeError("migration/compatibility content leaked into HTML")

    return {
        "run_id": RUN_ID,
        "status": rendered_workspace.data["state"],
        "title": report["title"],
        "content_dimensions": [
            "世界设定",
            "故事线设计",
            "角色定义",
            "样章",
        ],
        "decision_is_trailing_operation": True,
        "section_count": len(report["review_path"]),
        "content_dimension_count": 4,
        "visual_count": len(report["visual_models"]),
        "visual_roles": roles,
        "html": str(HTML_ROOT / "human-review-report.html"),
        "validation": independent_validation,
        "document_validation": document_validation,
        "deterministic": True,
        "security": "offline-no-active-content",
        "accessibility": "five-accessible-semantic-visuals",
        "manifest": receipt.transition.workspace.data["artifacts"][
            "html_manifest"
        ],
        "workspace": rendered_workspace.reference,
        "workspace_state": rendered_workspace.data["state"],
    }


if __name__ == "__main__":
    RESULT.write_text(
        json.dumps(main(), ensure_ascii=True, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
        newline="",
    )
