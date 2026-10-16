"""Maps tool names to explicitly implemented functions. No eval/exec, ever."""
from pathlib import Path

from tools.csv_cleaner import clean_csv_file
from tools.pdf_extractor import extract_pdfs


def _run_clean_csv(plan, input_path: str, output_path: str) -> dict:
    ops = [a.operation for a in plan.actions]
    return clean_csv_file(input_path, output_path, ops)


def _run_extract_pdf(plan, input_path: str, output_path: str) -> dict:
    p = Path(input_path)
    pdfs = [f for f in sorted(p.iterdir()) if f.suffix.lower() == ".pdf"] if p.is_dir() else [p]
    ops = [a.operation for a in plan.actions]
    return extract_pdfs(pdfs, output_path, ops)


TOOLS = {
    "clean_csv": _run_clean_csv,
    "extract_pdf": _run_extract_pdf,
}


def get_tool(name: str):
    if name not in TOOLS:
        raise KeyError(f"Tool '{name}' is not registered")
    return TOOLS[name]
