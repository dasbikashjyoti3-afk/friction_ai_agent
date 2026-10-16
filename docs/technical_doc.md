@'
# FrictionAI: Technical Document

## 1. Problem and users
Students and office workers repeatedly rename, clean and copy data between files. Each repetition requires recognising the task, finding a method, running it and checking the result. FrictionAI lets the user describe the task in English and handles planning, execution and verification.

## 2. Why automation helps
It removes manual copy-paste work, reduces human error, and leaves an auditable record of what was done.

## 3. Architecture
Streamlit UI -> Controller -> AI Planner -> Plan Validator -> User Approval -> Tool Registry -> Tools (CSV cleaner, PDF extractor) -> Verification -> SQLite.

The controller coordinates modules. The planner only proposes. The validator and registry decide what may run. Tools are deterministic Python.

## 4. Technology choices
- **Python 3.12**: application logic. Python 3.14 free-threaded builds broke NumPy during development.
- **Streamlit**: fast browser UI, no separate frontend.
- **pandas**: CSV cleaning.
- **PyMuPDF**: PDF text extraction.
- **Pydantic**: plan schema validation.
- **SQLite**: single-user persistence, parameterized queries only.
- **Gemini API**: planning and field extraction, with JSON output. Chosen for its free tier. Model name is configurable through `GEMINI_MODEL`.
- **pytest**: automated tests.

No RAG, vector database, fine-tuning or multi-agent design was used, because the workflows do not need them.

## 5. How the agent plans and executes
1. The planner sends the request, file type and the list of allowed tools to Gemini and asks for JSON.
2. The validator checks structure, tool name, operations, file extensions and workspace paths.
3. The user reviews operations and approves or rejects.
4. The controller re-validates, sets status APPROVED then RUNNING, and calls the registered function.
5. The tool output is reloaded and checked. Only then is the task marked COMPLETED. Failures are logged and marked FAILED.

Task statuses: PLANNED, AWAITING_APPROVAL, APPROVED, RUNNING, COMPLETED, FAILED, REJECTED.

## 6. Security and approval
- Model output is untrusted. Unknown tools or operations are rejected.
- `requires_approval` is forced to true regardless of model output.
- Workspace boundary enforced with resolved paths.
- No `exec` or `eval`. Tools come from a fixed registry.
- Extracted PDF text is passed to the model as data, with an instruction to ignore embedded instructions. This reduces but does not eliminate prompt-injection risk; outputs are also validated and user-reviewed.
- Unreadable or incomplete fields are left blank and flagged `needs_review`, never guessed.

## 7. Reliability
- Gemini calls retry on transient errors (503/500/429, network).
- If the API stays unavailable, a rule-based planner and extractor take over.
- During development the Gemini API returned repeated 503 "high demand" errors. The app continued working through the fallback.

## 8. Testing
Automated tests (pytest) cover: duplicate removal, column standardisation, missing-value reporting, unknown operations, original data not modified, database CRUD and SQL-injection safety, plan validation, unknown tools, approval enforcement, path traversal, wrong file types, PDF extraction, no-text PDFs, date normalisation and the planner fallback.

Result of the last full run: **<FILL IN: e.g. 37 passed>**.

Manual end-to-end tests: CSV cleaning (15 rows to 10), multi-PDF extraction (4 files, 1 flagged), plan rejection, history view. '<cleaned_14_trial_student.csv>'.

## 9. Known limitations
- Scanned (image-only) PDFs need OCR, which is not implemented. They are flagged `no_text`.
- Rule-based extraction expects labelled fields such as "Deadline:". Free-form layouts need the AI path.
- Dates in ambiguous formats may parse differently from what the author intended.
- Single user, local only. No authentication.
- The AI path sends document text (first 6,000 characters) to a third-party API.
- The file organizer tool from the original blueprint was not built.
- Model names change over time; `GEMINI_MODEL` may need updating.
- Test count reflects the tests I wrote. It does not cover the Streamlit UI or live API calls.
'@ | Set-Content -Path docs\technical_document.md -Encoding utf8