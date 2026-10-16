"""SQLite persistence: tasks, plans, execution logs. Uses parameterized queries only."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path("data") / "frictionai.db"

# Allowed task statuses
PLANNED = "PLANNED"
AWAITING_APPROVAL = "AWAITING_APPROVAL"
APPROVED = "APPROVED"
RUNNING = "RUNNING"
COMPLETED = "COMPLETED"
FAILED = "FAILED"
REJECTED = "REJECTED"
VALID_STATUSES = {PLANNED, AWAITING_APPROVAL, APPROVED, RUNNING, COMPLETED, FAILED, REJECTED}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def _connect(db_path=DEFAULT_DB_PATH):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path=DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                task_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                user_request  TEXT NOT NULL,
                selected_tool TEXT,
                status        TEXT NOT NULL,
                created_at    TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_plans (
                plan_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id    INTEGER NOT NULL REFERENCES tasks(task_id),
                plan_json  TEXT NOT NULL,
                approved   INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS execution_logs (
                log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id     INTEGER NOT NULL REFERENCES tasks(task_id),
                action      TEXT NOT NULL,
                status      TEXT NOT NULL,
                details     TEXT,
                executed_at TEXT NOT NULL
            );
            """
        )


def create_task(user_request: str, selected_tool: str | None = None,
                status: str = PLANNED, db_path=DEFAULT_DB_PATH) -> int:
    if not user_request or not user_request.strip():
        raise ValueError("user_request cannot be empty")
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO tasks (user_request, selected_tool, status, created_at) VALUES (?, ?, ?, ?)",
            (user_request.strip(), selected_tool, status, _now()),
        )
        return cur.lastrowid


def update_task_status(task_id: int, status: str, db_path=DEFAULT_DB_PATH) -> None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    with _connect(db_path) as conn:
        conn.execute("UPDATE tasks SET status = ? WHERE task_id = ?", (status, task_id))


def save_plan(task_id: int, plan: dict, db_path=DEFAULT_DB_PATH) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO task_plans (task_id, plan_json, approved) VALUES (?, ?, 0)",
            (task_id, json.dumps(plan)),
        )
        return cur.lastrowid


def get_plan(plan_id: int, db_path=DEFAULT_DB_PATH) -> dict | None:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM task_plans WHERE plan_id = ?", (plan_id,)).fetchone()
    if row is None:
        return None
    return {"plan_id": row["plan_id"], "task_id": row["task_id"],
            "plan": json.loads(row["plan_json"]), "approved": bool(row["approved"])}


def approve_plan(plan_id: int, db_path=DEFAULT_DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute("UPDATE task_plans SET approved = 1 WHERE plan_id = ?", (plan_id,))


def is_plan_approved(plan_id: int, db_path=DEFAULT_DB_PATH) -> bool:
    plan = get_plan(plan_id, db_path)
    return bool(plan and plan["approved"])


def log_execution(task_id: int, action: str, status: str, details: str = "",
                  db_path=DEFAULT_DB_PATH) -> int:
    with _connect(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO execution_logs (task_id, action, status, details, executed_at) VALUES (?, ?, ?, ?, ?)",
            (task_id, action, status, details, _now()),
        )
        return cur.lastrowid


def get_history(limit: int = 50, db_path=DEFAULT_DB_PATH) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY task_id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_task_logs(task_id: int, db_path=DEFAULT_DB_PATH) -> list[dict]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM execution_logs WHERE task_id = ? ORDER BY log_id", (task_id,)
        ).fetchall()
    return [dict(r) for r in rows]