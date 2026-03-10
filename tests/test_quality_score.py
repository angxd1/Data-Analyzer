import pandas as pd

from services.cleaning import clean_dataset
from services.analytics import calculate_data_quality_score
from validation import validate_dataset


def test_quality_score_range_and_breakdown():
    df_raw = pd.DataFrame(
        {
            "a": [1, 2, 2, None],
            "b": ["x", "x", "x", "x"],
        }
    )
    df = df_raw.copy()

    score, label, breakdown = calculate_data_quality_score(df, df_raw)

    assert 0 <= score <= 100
    assert label in {"Excellent", "Good", "Fair", "Poor"}
    assert "penalty_missing" in breakdown
    assert "penalty_duplicates" in breakdown


def test_quality_score_penalizes_messy_data_more_than_clean_fixture():
    clean_df = pd.read_csv("sample_datasets/customer_profiles.csv")
    messy_df = pd.read_csv("sample_datasets/messy_orders.csv")

    clean_score, _, _ = calculate_data_quality_score(
        clean_df, clean_df, validate_dataset(clean_df)
    )
    messy_score, _, breakdown = calculate_data_quality_score(
        messy_df, messy_df, validate_dataset(messy_df)
    )

    assert clean_score > messy_score
    assert breakdown["penalty_missing"] > 0
    assert breakdown["penalty_duplicates"] > 0


def test_cleaning_improves_missingness_penalty_on_messy_fixture():
    messy_df = pd.read_csv("sample_datasets/messy_orders.csv")
    options = {
        "drop_duplicates": True,
        "fill_numeric": True,
        "fill_categorical": True,
        "trim_strings": True,
        "convert_numeric": True,
    }

    cleaned_df, _ = clean_dataset(messy_df, options)

    _, _, raw_breakdown = calculate_data_quality_score(
        messy_df, messy_df, validate_dataset(messy_df)
    )
    _, _, cleaned_breakdown = calculate_data_quality_score(
        cleaned_df, messy_df, validate_dataset(cleaned_df)
    )

    assert cleaned_breakdown["penalty_missing"] < raw_breakdown["penalty_missing"]
