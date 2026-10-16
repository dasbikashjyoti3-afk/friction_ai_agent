"""Validates AI-proposed plans. The model proposes; this module decides what is allowed."""
from pathlib import Path
from pydantic import BaseModel, ValidationError, field_validator

from tools.csv_cleaner import ALLOWED_OPERATIONS as CSV_OPS
from tools.pdf_extractor import ALLOWED_OPERATIONS as PDF_OPS

# Tool name -> operations that tool permits
TOOL_OPERATIONS = {
    "clean_csv": set(CSV_OPS),
    "extract_pdf": set(PDF_OPS),
}

WORKSPACE = Path("workspace").resolve()
ALLOWED_EXTENSIONS = {"clean_csv": {".csv"}, "extract_pdf": {".pdf"}}


class PlanAction(BaseModel):
    operation: str


class Plan(BaseModel):
    tool: str
    goal: str = ""
    actions: list[PlanAction]
    requires_approval: bool = True

    @field_validator("actions")
    @classmethod
    def not_empty(cls, v):
        if not v:
            raise ValueError("plan has no actions")
        return v


class PlanRejected(Exception):
    """Raised when a plan fails validation. The message is safe to show to the user."""


def is_inside_workspace(path, workspace: Path = WORKSPACE) -> bool:
    """Resolve symlinks and '..' first, then check the path is really inside the workspace."""
    try:
        resolved = Path(path).resolve()
        resolved.relative_to(Path(workspace).resolve())
        return True
    except (ValueError, OSError):
        return False


def _input_files(path) -> list[Path]:
    p = Path(path)
    if p.is_dir():
        return [f for f in sorted(p.iterdir()) if f.is_file()]
    return [p]


def validate_plan(raw_plan: dict, input_path=None, workspace: Path = WORKSPACE) -> Plan:
    try:
        plan = Plan.model_validate(raw_plan)
    except ValidationError as e:
        raise PlanRejected(f"Invalid plan structure: {e.error_count()} problem(s) found.") from e

    if plan.tool not in TOOL_OPERATIONS:
        raise PlanRejected(f"Unknown tool: '{plan.tool}'")

    allowed = TOOL_OPERATIONS[plan.tool]
    bad = [a.operation for a in plan.actions if a.operation not in allowed]
    if bad:
        raise PlanRejected(f"Unsupported operations for {plan.tool}: {bad}")

    if input_path is not None:
        if not is_inside_workspace(input_path, workspace):
            raise PlanRejected("Input file is outside the permitted workspace.")
        files = _input_files(input_path)
        if not files:
            raise PlanRejected("No files were found in the input folder.")
        allowed_ext = ALLOWED_EXTENSIONS.get(plan.tool, set())
        for f in files:
            if not is_inside_workspace(f, workspace):
                raise PlanRejected("Input file is outside the permitted workspace.")
            ext = f.suffix.lower()
            if ext not in allowed_ext:
                raise PlanRejected(f"File type '{ext}' is not supported by {plan.tool}.")

    # Safety rule: we always require approval, whatever the model says.
    plan.requires_approval = True
    return plan
