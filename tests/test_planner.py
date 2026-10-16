import pytest
from core import planner
from core.validator import validate_plan


def test_rule_based_picks_duplicates_and_columns():
    plan = planner._rule_based_plan("remove duplicates and standardize column names")
    ops = [a["operation"] for a in plan["actions"]]
    assert "remove_duplicates" in ops
    assert "standardize_column_names" in ops


def test_rule_based_plan_passes_validator():
    plan = planner._rule_based_plan("clean this")
    assert validate_plan(plan).tool == "clean_csv"


def test_empty_request_rejected():
    with pytest.raises(ValueError):
        planner.generate_plan("   ")


def test_no_key_falls_back_to_rules(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    plan, source = planner.generate_plan("remove duplicates")
    assert source == "rules"
    validate_plan(plan)


def test_parse_json_handles_code_fences():
    assert planner._parse_json('```json\n{"a": 1}\n```') == {"a": 1}
