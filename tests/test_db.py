import pytest
from database import db


@pytest.fixture
def path(tmp_path):
    p = tmp_path / "test.db"
    db.init_db(p)
    return p


def test_create_and_history(path):
    tid = db.create_task("clean my csv", "clean_csv", db_path=path)
    history = db.get_history(db_path=path)
    assert len(history) == 1
    assert history[0]["task_id"] == tid
    assert history[0]["status"] == db.PLANNED


def test_empty_request_rejected(path):
    with pytest.raises(ValueError):
        db.create_task("   ", db_path=path)


def test_invalid_status_rejected(path):
    tid = db.create_task("x", db_path=path)
    with pytest.raises(ValueError):
        db.update_task_status(tid, "DONE_MAYBE", db_path=path)


def test_plan_starts_unapproved_then_approved(path):
    tid = db.create_task("x", "clean_csv", db_path=path)
    pid = db.save_plan(tid, {"tool": "clean_csv", "actions": []}, db_path=path)
    assert db.is_plan_approved(pid, db_path=path) is False
    db.approve_plan(pid, db_path=path)
    assert db.is_plan_approved(pid, db_path=path) is True
    assert db.get_plan(pid, db_path=path)["plan"]["tool"] == "clean_csv"


def test_logs_and_status_update(path):
    tid = db.create_task("x", db_path=path)
    db.log_execution(tid, "remove_duplicates", "SUCCESS", "2 removed", db_path=path)
    db.update_task_status(tid, db.COMPLETED, db_path=path)
    logs = db.get_task_logs(tid, db_path=path)
    assert logs[0]["action"] == "remove_duplicates"
    assert db.get_history(db_path=path)[0]["status"] == db.COMPLETED


def test_sql_injection_is_stored_as_plain_text(path):
    nasty = "x'); DROP TABLE tasks;--"
    db.create_task(nasty, db_path=path)
    assert db.get_history(db_path=path)[0]["user_request"] == nasty