"""Coordinates the workflow: plan -> validate -> save -> approve -> execute -> verify -> log."""
import logging
import re
import uuid
from pathlib import Path

from database import db
from core import planner
from core.validator import validate_plan, PlanRejected, WORKSPACE
from core.tool_registry import get_tool

log = logging.getLogger(__name__)
OUTPUTS = Path("outputs").resolve()


def save_upload(name: str, data: bytes, workspace: Path = WORKSPACE) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\-]", "_", Path(name).name)
    dest = workspace / safe
    dest.write_bytes(data)
    return dest


def save_uploads(files: list, workspace: Path = WORKSPACE) -> Path:
    """files = [(name, bytes), ...]. One file -> that file. Several -> a fresh batch folder."""
    if not files:
        raise ValueError("No files uploaded")
    if len(files) == 1:
        return save_upload(files[0][0], files[0][1], workspace)
    batch = workspace / f"batch_{uuid.uuid4().hex[:8]}"
    for name, data in files:
        save_upload(name, data, batch)
    return batch


def _file_kind(path) -> str:
    p = Path(path)
    if p.is_dir() or p.suffix.lower() == ".pdf":
        return "pdf"
    return "csv"


def create_plan(user_request: str, input_path) -> dict:
    db.init_db()
    task_id = db.create_task(user_request, None, db.PLANNED)
    try:
        raw, source = planner.generate_plan(user_request, _file_kind(input_path))
        plan = validate_plan(raw, input_path=input_path)
    except PlanRejected as e:
        db.update_task_status(task_id, db.FAILED)
        db.log_execution(task_id, "validate_plan", "REJECTED", str(e))
        raise
    except Exception as e:
        db.update_task_status(task_id, db.FAILED)
        db.log_execution(task_id, "plan", "FAILED", type(e).__name__)
        raise
    plan_id = db.save_plan(task_id, plan.model_dump())
    db.update_task_status(task_id, db.AWAITING_APPROVAL)
    return {"task_id": task_id, "plan_id": plan_id, "plan": plan.model_dump(),
            "source": source, "input_path": str(input_path)}


def reject(task_id: int) -> None:
    db.update_task_status(task_id, db.REJECTED)
    db.log_execution(task_id, "approval", "REJECTED", "User rejected the plan")


def approve_and_run(task_id: int, plan_id: int, input_path) -> dict:
    db.approve_plan(plan_id)
    return run_plan(task_id, plan_id, input_path)


def run_plan(task_id: int, plan_id: int, input_path) -> dict:
    if not db.is_plan_approved(plan_id):
        raise PermissionError("Plan has not been approved")
    stored = db.get_plan(plan_id)
    plan = validate_plan(stored["plan"], input_path=input_path)  # re-validate before running
    db.update_task_status(task_id, db.APPROVED)
    db.update_task_status(task_id, db.RUNNING)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    if plan.tool == "extract_pdf":
        output_path = OUTPUTS / f"extracted_{task_id}.csv"
    else:
        output_path = OUTPUTS / f"cleaned_{task_id}_{Path(input_path).name}"
    try:
        report = get_tool(plan.tool)(plan, str(input_path), str(output_path))
        if not report.get("verified"):
            raise RuntimeError("Output verification failed")
    except Exception as e:
        log.error("Execution failed: %s", type(e).__name__)
        db.log_execution(task_id, plan.tool, "FAILED", f"{type(e).__name__}: {e}")
        db.update_task_status(task_id, db.FAILED)
        raise
    for op in report["operations_applied"]:
        db.log_execution(task_id, op, "SUCCESS", "")
    db.log_execution(task_id, "verify_output", "SUCCESS", str(output_path))
    db.update_task_status(task_id, db.COMPLETED)
    return report
