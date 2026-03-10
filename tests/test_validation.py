import pandas as pd

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
