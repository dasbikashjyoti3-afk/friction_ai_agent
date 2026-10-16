import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from core import controller
from core.validator import PlanRejected
from database import db

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="FrictionAI", page_icon="⚙️", layout="wide")
db.init_db()

st.title("FrictionAI")
st.caption("Describe it. Automate it. Verify it.")

tab_new, tab_hist = st.tabs(["New Automation", "History"])


def clear_state():
    st.session_state.pop("result", None)
    st.session_state.pop("pending", None)


def read_csv_safe(path):
    try:
        return pd.read_csv(path)
    except (pd.errors.EmptyDataError, FileNotFoundError):
        st.error("The output file is empty or missing. Check the History tab and the terminal logs.")
        return pd.DataFrame()


with tab_new:
    st.subheader("1. Describe")
    request = st.text_area(
        "What repetitive task do you want to automate?",
        placeholder="Clean this spreadsheet, remove duplicates and report missing values\n"
                    "or: Extract subject, assignment number, deadline and instructor from these PDFs",
    )
    uploaded = st.file_uploader(
        "Upload one CSV file, or one or more PDF files",
        type=["csv", "pdf"],
        accept_multiple_files=True,
    )

    if st.button("Generate plan", type="primary"):
        clear_state()
        if not request.strip():
            st.error("Please describe the task first.")
        elif not uploaded:
            st.error("Please upload a file.")
        else:
            kinds = {Path(f.name).suffix.lower() for f in uploaded}
            if len(kinds) > 1:
                st.error("Please upload only one type of file at a time (CSV or PDF).")
            elif kinds == {".csv"} and len(uploaded) > 1:
                st.error("Please upload only one CSV file at a time.")
            else:
                try:
                    path = controller.save_uploads([(f.name, f.getvalue()) for f in uploaded])
                    st.session_state["pending"] = controller.create_plan(request, path)
                except PlanRejected as e:
                    st.error(f"Plan rejected: {e}")
                except Exception:
                    st.error("Could not create a plan. Check the logs and try again.")

    pending = st.session_state.get("pending")
    if pending:
        st.subheader("2. Review")
        st.write(f"**Goal:** {pending['plan']['goal']}")
        st.write(f"**Tool:** `{pending['plan']['tool']}`  |  **Planned by:** {pending['source']}")
        in_path = Path(pending["input_path"])
        if in_path.is_dir():
            pdfs = sorted(p.name for p in in_path.iterdir())
            st.write(f"**Input files ({len(pdfs)}):** " + ", ".join(f"`{n}`" for n in pdfs))
        else:
            st.write(f"**Input file:** `{in_path.name}`")
        st.table(pd.DataFrame(
            [{"Operation": a["operation"], "Status": "Awaiting approval"}
             for a in pending["plan"]["actions"]]
        ))
        if pending["plan"]["tool"] == "clean_csv":
            st.write("**Preview of input (first 5 rows):**")
            st.dataframe(pd.read_csv(in_path).head())

        c1, c2 = st.columns(2)
        if c1.button("Approve & run"):
            try:
                with st.spinner("Running..."):
                    report = controller.approve_and_run(
                        pending["task_id"], pending["plan_id"], pending["input_path"])
                st.session_state["result"] = {"report": report, "pending": pending}
                st.session_state.pop("pending")
                st.rerun()
            except Exception:
                st.error("Execution failed. See History for details.")
        if c2.button("Reject"):
            controller.reject(pending["task_id"])
            st.session_state.pop("pending")
            st.rerun()

    result = st.session_state.get("result")
    if result:
        st.subheader("3. Results")
        report = result["report"]
        tool = result["pending"]["plan"]["tool"]
        out = Path(report["output_path"])
        st.success("Completed and verified.")

        if tool == "clean_csv":
            m1, m2, m3 = st.columns(3)
            m1.metric("Rows before", report["rows_before"])
            m2.metric("Rows after", report["rows_after"])
            m3.metric("Duplicates removed", report.get("duplicates_removed", 0))
            left, right = st.columns(2)
            left.write("**Before**")
            left.dataframe(pd.read_csv(result["pending"]["input_path"]))
            right.write("**After**")
            right.dataframe(read_csv_safe(out))
        else:
            m1, m2, m3 = st.columns(3)
            m1.metric("Files processed", report["files_processed"])
            m2.metric("Needs review", report["needs_review"])
            m3.metric("Failed", report["files_failed"])
            st.caption(f"Extraction by: {report['extraction_source']}")
            st.write("**Extracted data**")
            st.dataframe(read_csv_safe(out), use_container_width=True)
            if report["needs_review"]:
                st.warning("Some files have missing fields (status: needs_review). "
                           "Missing values are left blank, never guessed.")

        st.download_button("Download CSV", out.read_bytes(),
                           file_name=out.name, mime="text/csv")
        with st.expander("Full report"):
            st.json(report)

with tab_hist:
    history = db.get_history()
    if not history:
        st.info("No tasks yet.")
    else:
        st.dataframe(pd.DataFrame(history), use_container_width=True)
        ids = [h["task_id"] for h in history]
        chosen = st.selectbox("Show logs for task", ids)
        logs = db.get_task_logs(chosen)
        st.dataframe(pd.DataFrame(logs)) if logs else st.write("No logs for this task.")

