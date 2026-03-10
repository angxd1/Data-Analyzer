import pandas as pd

from services.cleaning import clean_dataset


def test_clean_dataset_basic():
    df_raw = pd.DataFrame(
        {
            "num": [1, 2, None, 2],
            "cat": [" a ", None, "b", "b"],
        }
    )
    options = {
        "drop_duplicates": True,
        "fill_numeric": True,
        "fill_categorical": True,
        "trim_strings": True,
        "convert_numeric": True,
    }

    cleaned, summary = clean_dataset(df_raw, options)

    assert summary["duplicates_removed"] == 1
    assert summary["numeric_filled"] == 1
    assert summary["categorical_filled"] == 1
    assert summary["strings_trimmed"] is True
    assert summary["numeric_converted"] is False

    assert cleaned["num"].isna().sum() == 0
    assert cleaned["cat"].isna().sum() == 0
    assert cleaned.loc[0, "cat"] == "a"
