@'
# FrictionAI

**Describe it. Automate it. Verify it.**

FrictionAI is an AI agent that turns repetitive digital work into reviewed, verified automation. You describe a task in plain English and upload files. The agent proposes a structured plan, you approve it, and deterministic Python tools execute it.

## Features

| Tool | What it does |
|---|---|
| `clean_csv` | Trims whitespace, standardizes column names, removes duplicates, reports missing values |
| `extract_pdf` | Extracts subject, assignment number, deadline and instructor from one or more PDFs into a CSV |

Also included: SQLite task history, execution logs, a before/after view, and automatic fallback to rules when the AI API is unavailable.

## How it works

1. **Describe**: plain-English request plus file upload.
2. **Plan**: Gemini returns a JSON plan, choosing only from registered tools. Rule-based fallback if the API fails.
3. **Validate**: Pydantic checks the schema, tool name, operations, file types and workspace paths.
4. **Approve**: the user reviews the exact operations and approves or rejects.
5. **Execute**: the tool registry maps the tool name to an implemented Python function (no `exec` or `eval`).
6. **Verify**: the output file is reloaded and checked before the task is marked COMPLETED.
7. **Record**: task, plan and logs are stored in SQLite.

## Setup (Windows PowerShell)

Requires Python 3.12.

```powershell
git clone <your-repo-url>
cd FrictionAi
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
mkdir workspace, outputs
```

Create `.env` (optional; without a key the app uses the rule-based fallback):

GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash


Model availability changes. If you get a 404, list your models and update `GEMINI_MODEL`.

## Run

```powershell
python -m streamlit run app.py
```

Open http://localhost:8501.

## Try it

- Upload `sample_data/trial_students.csv` and ask: *Clean this spreadsheet, trim spaces, standardize column names, remove duplicates and report missing values.*
- Upload the PDFs in `sample_data/sample_assignments/` and ask: *Extract the subject, assignment number, deadline and instructor into a CSV.*

Regenerate the sample PDFs with `python scripts/make_sample_pdfs.py`.

## Tests

```powershell
python -m pytest tests -v
```

## Security design

- The model only proposes; it never executes. It cannot invent tools or operations.
- Every plan is validated, and approval is always required (the model cannot disable it).
- Plans are re-validated just before execution. Unapproved plans cannot run.
- File access is limited to the `workspace/` folder, with path traversal and symlinks resolved.
- Originals are never overwritten; results go to `outputs/`.
- Document text is treated as untrusted data in the extraction prompt.
- API keys live in `.env`, which is git-ignored.

## Project structure

app.py Streamlit UI
core/ planner, validator, controller, tool registry
tools/ csv_cleaner, pdf_extractor
database/ SQLite persistence
utils/ AI retry helper
tests/ pytest suite
sample_data/ sample CSV and PDFs (no private data)


## Known limitations

See `docs/technical_document.md`.
'@ | Set-Content -Path README.md -Encoding utf8
