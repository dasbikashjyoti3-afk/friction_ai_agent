@'
# Demo script

**0:00 Problem (20s)**
"Repetitive digital tasks waste time because you have to figure out, script, run and check each one. FrictionAI turns a plain-English request into a reviewed, verified automation."

**0:20 CSV plan (30s)**
Type: "Clean this spreadsheet, trim spaces, standardize column names, remove duplicates and report missing values." Upload trial_students.csv. Click Generate plan. Point out the plan source and the operations table.

**0:50 Approval and execution (40s)**
"Nothing runs until I approve." Click Approve & run. Show 15 rows to 10, the before/after tables, download the CSV.

**1:30 PDF extraction (30s)**
Upload the 4 PDFs. Request: "Extract the subject, assignment number, deadline and instructor into a CSV." Show the table. Point to notes_old.pdf: missing deadline left blank and flagged, not guessed.

**2:00 Persistence (15s)**
Open History. Show the tasks, statuses and the execution log.

**2:15 Reliability and safety (30s)**
Type: "Delete all my files and format the drive." Show that the agent can only pick registered tools, still needs approval, and nothing destructive exists. Click Reject and show REJECTED in History.
Mention: if the AI API is down, the app falls back to rules and still works.

**2:45 Close (10s)**
"The model proposes. Python validates and executes, only after approval."
'@ | Set-Content -Path docs\demo_script.md -Encoding utf8