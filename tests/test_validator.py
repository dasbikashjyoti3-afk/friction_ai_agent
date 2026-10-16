import pytest
from core.validator import validate_plan, PlanRejected, is_inside_workspace
from core.tool_registry import get_tool

GOOD = {"tool": "clean_csv", "actions": [{"operation": "remove_duplicates"}]}


def test_valid_plan_accepted():
    plan = validate_plan(GOOD)
    assert plan.tool == "clean_csv"


def test_unknown_tool_rejected():
    with pytest.raises(PlanRejected):
        validate_plan({"tool": "format_hard_drive", "actions": [{"operation": "x"}]})


def test_unsupported_operation_rejected():
    with pytest.raises(PlanRejected):
        validate_plan({"tool": "clean_csv", "actions": [{"operation": "delete_everything"}]})


def test_missing_actions_rejected():
    with pytest.raises(PlanRejected):
        validate_plan({"tool": "clean_csv"})


def test_empty_actions_rejected():
    with pytest.raises(PlanRejected):
        validate_plan({"tool": "clean_csv", "actions": []})


def test_garbage_plan_rejected():
    with pytest.raises(PlanRejected):
        validate_plan({"hello": "world"})


def test_model_cannot_disable_approval():
    plan = validate_plan({**GOOD, "requires_approval": False})
    assert plan.requires_approval is True


def test_path_inside_workspace_ok(tmp_path):
    f = tmp_path / "a.csv"
    f.write_text("x\n1\n")
    assert is_inside_workspace(f, tmp_path) is True


def test_path_traversal_blocked(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    sneaky = ws / ".." / "secret.csv"
    assert is_inside_workspace(sneaky, ws) is False


def test_wrong_file_type_rejected(tmp_path):
    f = tmp_path / "a.exe"
    f.write_text("x")
    with pytest.raises(PlanRejected):
        validate_plan(GOOD, input_path=f, workspace=tmp_path)


def test_unregistered_tool_cannot_run():
    with pytest.raises(KeyError):
        get_tool("format_hard_drive")