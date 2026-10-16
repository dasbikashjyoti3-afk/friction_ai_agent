import pandas as pd
import pymupdf
import pytest

from core import planner
from core.validator import validate_plan, PlanRejected
from tools import pdf_extractor as px

ALL = sorted(px.ALLOWED_OPERATIONS)
TEXT = "Subject: Data Structures\nAssignment Number: 3\nDeadline: 2026-10-20\nInstructor: Dr. Rao"


def make_pdf(path, text):
    doc = pymupdf.open()
    page = doc.new_page()
    if text:
        page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()


@pytest.fixture(autouse=True)
def no_ai(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_rules_extract_fields(tmp_path):
    pdf = tmp_path / "a.pdf"
    make_pdf(pdf, TEXT)
    out = tmp_path / "out.csv"
    report = px.extract_pdfs([pdf], out, ALL)
    df = pd.read_csv(out)
    assert report["verified"] is True
    assert df.loc[0, "subject"] == "Data Structures"
    assert df.loc[0, "assignment_number"] == 3
    assert df.loc[0, "deadline"] == "2026-10-20"
    assert df.loc[0, "instructor"] == "Dr. Rao"
    assert df.loc[0, "status"] == "ok"


def test_no_text_pdf_flagged(tmp_path):
    pdf = tmp_path / "blank.pdf"
    make_pdf(pdf, "")
    report = px.extract_pdfs([pdf], tmp_path / "o.csv", ALL)
    assert report["files_failed"] == 1
    assert pd.read_csv(tmp_path / "o.csv").loc[0, "status"] == "no_text"


def test_missing_field_needs_review(tmp_path):
    pdf = tmp_path / "a.pdf"
    make_pdf(pdf, "Subject: Networks\nAssignment Number: 2\nInstructor: Dr. Khan")
    report = px.extract_pdfs([pdf], tmp_path / "o.csv", ALL)
    assert report["needs_review"] == 1


def test_deadline_normalized():
    assert px._normalize({"deadline": "20 October 2026"})["deadline"] == "2026-10-20"
    assert px._normalize({"deadline": "not a date"})["deadline"] is None


def test_bad_assignment_number_becomes_none():
    assert px._normalize({"assignment_number": "three"})["assignment_number"] is None


def test_validator_accepts_pdf_folder(tmp_path):
    folder = tmp_path / "batch"
    folder.mkdir()
    make_pdf(folder / "a.pdf", TEXT)
    make_pdf(folder / "b.pdf", TEXT)
    plan = validate_plan({"tool": "extract_pdf", "actions": [{"operation": "extract_deadline"}]},
                         input_path=folder, workspace=tmp_path)
    assert plan.tool == "extract_pdf"


def test_validator_rejects_wrong_file_in_folder(tmp_path):
    folder = tmp_path / "batch"
    folder.mkdir()
    make_pdf(folder / "a.pdf", TEXT)
    (folder / "virus.exe").write_text("x")
    with pytest.raises(PlanRejected):
        validate_plan({"tool": "extract_pdf", "actions": [{"operation": "extract_deadline"}]},
                      input_path=folder, workspace=tmp_path)


def test_csv_operation_rejected_for_pdf_tool():
    with pytest.raises(PlanRejected):
        validate_plan({"tool": "extract_pdf", "actions": [{"operation": "remove_duplicates"}]})


def test_unknown_pdf_operation_rejected():
    with pytest.raises(PlanRejected):
        validate_plan({"tool": "extract_pdf", "actions": [{"operation": "extract_passwords"}]})


def test_planner_pdf_fallback():
    plan = planner._rule_based_plan("get the deadline and the instructor", "pdf")
    ops = [a["operation"] for a in plan["actions"]]
    assert plan["tool"] == "extract_pdf"
    assert "extract_deadline" in ops and "extract_instructor" in ops
    assert validate_plan(plan).tool == "extract_pdf"
