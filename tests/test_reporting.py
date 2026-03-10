import pandas as pd

from services.cleaning import clean_dataset
from services.analytics import compute_insights, compute_missing_df
from services.reporting import build_report
from validation import validate_dataset


def test_report_includes_fixture_diagnostics():
    df_raw = pd.read_csv("sample_datasets/messy_orders.csv")
    options = {
        "drop_duplicates": True,
        "fill_numeric": True,
        "fill_categorical": True,
        "trim_strings": True,
        "convert_numeric": True,
    }

    df, clean_summary = clean_dataset(df_raw, options)
    numeric_cols = df.select_dtypes(include="number").columns
    categorical_cols = df.select_dtypes(exclude="number").columns
    missing_df = compute_missing_df(df)
    validation = validate_dataset(df)
    insights = compute_insights(
        df, numeric_cols, categorical_cols, missing_df, clean_summary, validation
    )

    report = build_report(df, clean_summary, insights, validation)

    assert "SMART DATA ANALYZER REPORT" in report
    assert "Cleaning Summary:" in report
    assert "Dataset Diagnostics & Validation:" in report
    assert "order_id" in report or "order_date" in report
