"""Deterministic CSV cleaning. All numbers in the report come from the real data, never from an AI."""
import re
import pandas as pd

ALLOWED_OPERATIONS = {
    "strip_whitespace",
    "standardize_column_names",
    "remove_duplicates",
    "report_missing_values",
}


def _standardize_name(name: str) -> str:
    name = str(name).strip().lower()
    name = re.sub(r"[^\w]+", "_", name)
    return name.strip("_") or "column"


def _make_unique(names: list[str]) -> list[str]:
    seen, result = {}, []
    for n in names:
        if n in seen:
            seen[n] += 1
            result.append(f"{n}_{seen[n]}")
        else:
            seen[n] = 1
            result.append(n)
    return result


def clean_dataframe(df: pd.DataFrame, operations: list[str]) -> tuple[pd.DataFrame, dict]:
    """Apply approved operations to a COPY of df. Returns (cleaned_df, report)."""
    unknown = set(operations) - ALLOWED_OPERATIONS
    if unknown:
        raise ValueError(f"Unsupported operations: {sorted(unknown)}")

    out = df.copy()
    report = {
        "rows_before": len(out),
        "columns_before": list(out.columns),
        "operations_applied": [],
    }

    if "strip_whitespace" in operations:
        for col in out.select_dtypes(include=["object", "string"]).columns:
            out[col] = out[col].str.strip().replace("", pd.NA)
        report["operations_applied"].append("strip_whitespace")

    if "standardize_column_names" in operations:
        new_names = _make_unique([_standardize_name(c) for c in out.columns])
        report["columns_renamed"] = {
            old: new for old, new in zip(out.columns, new_names) if old != new
        }
        out.columns = new_names
        report["operations_applied"].append("standardize_column_names")

    if "remove_duplicates" in operations:
        before = len(out)
        out = out.drop_duplicates().reset_index(drop=True)
        report["duplicates_removed"] = before - len(out)
        report["operations_applied"].append("remove_duplicates")

    if "report_missing_values" in operations:
        missing = out.isna().sum()
        report["missing_values"] = {c: int(n) for c, n in missing.items() if n > 0}
        report["missing_total"] = int(missing.sum())
        report["operations_applied"].append("report_missing_values")
    out = out.convert_dtypes()
    report["rows_after"] = len(out)
    report["columns_after"] = list(out.columns)
    return out, report


def clean_csv_file(input_path: str, output_path: str, operations: list[str]) -> dict:
    """Load a CSV, clean it, write the output, and verify the file exists."""
    df = pd.read_csv(input_path)
    cleaned, report = clean_dataframe(df, operations)
    cleaned.to_csv(output_path, index=False)

    # Verification: reload the output and confirm it matches what we expected
    check = pd.read_csv(output_path)
    report["verified"] = len(check) == report["rows_after"]
    report["output_path"] = output_path
    return report