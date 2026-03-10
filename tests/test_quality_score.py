import pandas as pd

from services.analytics import calculate_data_quality_score


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
