import pandas as pd

from validation_config import ValidationRules
from validation import validate_dataset


def test_validate_dataset_roles():
    df = pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "constant": ["x", "x", "x", "x", "x"],
            "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"],
            "category": ["a", "b", "c", "d", "e"],
            "small_num": [1, 1, 2, 2, 1],
        }
    )

    result = validate_dataset(df)

    id_cols = {c["column"] for c in result["id_columns"]}
    assert "id" in id_cols

    constant_cols = {c["column"] for c in result["constant_columns"]}
    assert "constant" in constant_cols

    dt_cols = {c["column"] for c in result["datetime_columns"]}
    assert "date" in dt_cols

    high_card = {c["column"] for c in result["high_cardinality"]}
    assert "category" in high_card

    numeric_cat = {c["column"] for c in result["numeric_as_categorical"]}
    assert "small_num" in numeric_cat

    summary = result["schema_summary"]
    assert summary["total_rows"] == 5
    assert summary["total_columns"] == 5


def test_validation_avoids_common_false_positives():
    df = pd.read_csv("sample_datasets/customer_profiles.csv")

    result = validate_dataset(df)

    id_cols = {c["column"] for c in result["id_columns"]}
    dt_cols = {c["column"] for c in result["datetime_columns"]}

    assert "customer_id" in id_cols
    assert "age" not in id_cols
    assert "salary" not in id_cols

    assert "signup_date" in dt_cols
    assert "age" not in dt_cols
    assert "salary" not in dt_cols


def test_validation_detects_epoch_timestamp_by_name():
    df = pd.DataFrame(
        {
            "event_timestamp": [1704067200, 1704153600, 1704240000, 1704326400],
            "amount": [10.5, 20.0, 15.5, 19.0],
        }
    )

    result = validate_dataset(df)

    dt_cols = {c["column"] for c in result["datetime_columns"]}
    assert "event_timestamp" in dt_cols
    assert "amount" not in dt_cols


def test_validation_rules_are_configurable():
    df = pd.DataFrame(
        {
            "customer_code": ["A1", "B2", "C3", "D4", "E5"],
            "segment": ["Retail", "Retail", "SMB", "Retail", "SMB"],
        }
    )

    default_result = validate_dataset(df)
    strict_result = validate_dataset(
        df,
        ValidationRules(
            high_cardinality_unique_min=2,
            high_cardinality_ratio_threshold=0.3,
        ),
    )

    default_high_card = {c["column"] for c in default_result["high_cardinality"]}
    strict_high_card = {c["column"] for c in strict_result["high_cardinality"]}

    assert "customer_code" in default_high_card
    assert "segment" not in default_high_card
    assert "segment" in strict_high_card
