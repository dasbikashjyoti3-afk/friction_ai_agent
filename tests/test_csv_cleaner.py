import pandas as pd
import pytest
from tools.csv_cleaner import clean_dataframe, ALLOWED_OPERATIONS

ALL_OPS = sorted(ALLOWED_OPERATIONS)


@pytest.fixture
def messy():
    return pd.read_csv("sample_data/messy_data.csv")


def test_removes_duplicates(messy):
    cleaned, report = clean_dataframe(messy, ALL_OPS)
    assert report["rows_before"] == 5
    assert report["duplicates_removed"] == 2
    assert report["rows_after"] == 3


def test_standardizes_columns(messy):
    cleaned, _ = clean_dataframe(messy, ALL_OPS)
    assert list(cleaned.columns) == ["student_name", "roll_no", "subject", "marks"]


def test_reports_missing_values(messy):
    _, report = clean_dataframe(messy, ALL_OPS)
    assert report["missing_total"] == 2


def test_unknown_operation_rejected(messy):
    with pytest.raises(ValueError):
        clean_dataframe(messy, ["delete_everything"])


def test_original_not_modified(messy):
    before = messy.copy()
    clean_dataframe(messy, ALL_OPS)
    pd.testing.assert_frame_equal(messy, before)