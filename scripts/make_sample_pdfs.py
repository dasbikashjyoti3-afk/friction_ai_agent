from pathlib import Path
import pymupdf

OUT = Path("sample_data/sample_assignments")
OUT.mkdir(parents=True, exist_ok=True)

DOCS = {
    "scan_0381.pdf": "Subject: Data Structures\nAssignment Number: 3\nDeadline: 2026-10-20\nInstructor: Dr. Rao",
    "file_x22.pdf": "Subject: Operating Systems\nAssignment Number: 1\nDue Date: 2026-10-25\nInstructor: Prof. Mehta",
    "hw_final.pdf": "Subject: Databases\nAssignment Number: 5\nDeadline: 30 October 2026\nInstructor: Dr. Iyer",
    "notes_old.pdf": "Subject: Networks\nAssignment Number: 2\nInstructor: Dr. Khan",
}

for name, text in DOCS.items():
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=12)
    doc.save(str(OUT / name))
    doc.close()
print("Created", len(DOCS), "PDFs in", OUT)
