import re
import warnings
from datetime import datetime
import numpy as np
import pandas as pd

# Date-like patterns to aid detection on object columns.
_DATE_PATTERNS = [
    re.compile(r"^\d{4}-\d{2}-\d{2}"),  # 2023-01-31
    re.compile(r"^\d{2}/\d{2}/\d{4}"),  # 01/31/2023
    re.compile(r"^\d{4}/\d{2}/\d{2}"),  # 2023/01/31
    re.compile(r"^\d{2}-\d{2}-\d{4}"),  # 31-01-2023
]


def _is_integer_like(series: pd.Series) -> bool:
    if series.empty:
        return False
    numeric = pd.to_numeric(series, errors="coerce")
    numeric = numeric.dropna()
    if numeric.empty:
        return False
    return bool(np.isclose(numeric % 1, 0).all())


def _monotonic_status(series: pd.Series) -> str:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty:
        return "unknown"
    if numeric.is_monotonic_increasing:
        return "increasing"
    if numeric.is_monotonic_decreasing:
        return "decreasing"
    return "not_monotonic"


def _datetime_inference(series: pd.Series) -> dict:
    result = {
        "success": False,
        "method": None,
        "inferred_format": None,
        "parsed_ratio": 0.0,
    }

    if series.dropna().empty:
        return result

    # Regex-based hint for text columns.
    sample = series.dropna().astype(str).head(200)
    if not sample.empty:
        pattern_hits = 0
        for val in sample:
            if any(p.search(val) for p in _DATE_PATTERNS):
                pattern_hits += 1
        if pattern_hits / len(sample) >= 0.6:
            result["method"] = "regex"

    # Pandas inference for non-numeric / mixed values.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(series, errors="coerce")
    parsed_ratio = parsed.notna().mean()
    if parsed_ratio >= 0.8:
        result.update(
            {
                "success": True,
                "method": result["method"] or "pandas",
                "parsed_ratio": round(float(parsed_ratio), 2),
                "inferred_format": "datetime",
            }
        )
        return result

    # Epoch timestamp heuristics for numeric-like columns.
    numeric = pd.to_numeric(series, errors="coerce")
    numeric = numeric.dropna()
    if numeric.empty:
        return result

    # Heuristic: seconds vs milliseconds since epoch.
    if numeric.between(1_000_000_000, 2_000_000_000).mean() >= 0.8:
        result.update(
            {
                "success": True,
                "method": "epoch_seconds",
                "parsed_ratio": round(float(numeric.notna().mean()), 2),
                "inferred_format": "epoch_seconds",
            }
        )
    elif numeric.between(1_000_000_000_000, 2_000_000_000_000).mean() >= 0.8:
        result.update(
            {
                "success": True,
                "method": "epoch_millis",
                "parsed_ratio": round(float(numeric.notna().mean()), 2),
                "inferred_format": "epoch_millis",
            }
        )

    return result


def validate_dataset(df: pd.DataFrame) -> dict:
    """
    Validate dataset structure and return diagnostics.

    Returns a structured dictionary with detected column roles and warnings.
    """
    if df is None or df.empty or df.columns.empty:
        return {
            "id_columns": [],
            "constant_columns": [],
            "datetime_columns": [],
            "high_cardinality": [],
            "numeric_as_categorical": [],
            "distribution_warnings": [],
            "schema_summary": {
                "total_rows": int(len(df)) if df is not None else 0,
                "total_columns": 0,
                "numeric_count": 0,
                "categorical_count": 0,
                "datetime_count": 0,
                "missing_pct": 0.0,
                "duplicate_rows_pct": 0.0,
            },
        }

    total_rows = len(df)
    total_cols = len(df.columns)
    missing_pct = (df.isna().sum().sum() / max(total_rows * total_cols, 1)) * 100
    duplicate_rows_pct = (df.duplicated().sum() / max(total_rows, 1)) * 100

    id_columns = []
    constant_columns = []
    datetime_columns = []
    high_cardinality = []
    numeric_as_categorical = []
    distribution_warnings = []

    numeric_cols = df.select_dtypes(include=np.number).columns
    categorical_cols = df.select_dtypes(exclude=np.number).columns

    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        unique_count = non_null.nunique()
        unique_ratio = unique_count / max(len(non_null), 1)

        # 1) ID / INDEX DETECTION
        integer_like = _is_integer_like(series)
        monotonic = _monotonic_status(series)
        if unique_ratio > 0.95 and unique_count == len(non_null) and integer_like:
            id_columns.append(
                {
                    "column": col,
                    "uniqueness_ratio": round(float(unique_ratio), 2),
                    "monotonic": monotonic,
                    "integer_like": integer_like,
                    "warning": "This column likely represents an identifier and should not be treated as a feature.",
                }
            )

        # 2) CONSTANT & NEAR-CONSTANT
        value_counts = series.value_counts(dropna=False)
        if not value_counts.empty:
            dominant_ratio = value_counts.iloc[0] / max(total_rows, 1)
            if unique_count <= 1 or dominant_ratio > 0.95:
                constant_columns.append(
                    {
                        "column": col,
                        "dominant_value_pct": round(float(dominant_ratio * 100), 2),
                        "unique_values": int(unique_count),
                        "warning": "This column provides little or no analytical value.",
                    }
                )

        # 3) DATETIME INFERENCE
        dt_info = _datetime_inference(series)
        if dt_info["success"]:
            datetime_columns.append(
                {
                    "column": col,
                    "method": dt_info["method"],
                    "parsed_ratio": dt_info["parsed_ratio"],
                    "inferred_format": dt_info["inferred_format"],
                    "warning": "This column appears to represent temporal information.",
                }
            )

        # 4) HIGH-CARDINALITY CATEGORICALS
        if col in categorical_cols and unique_ratio > 0.2:
            high_cardinality.append(
                {
                    "column": col,
                    "unique_count": int(unique_count),
                    "ratio": round(float(unique_ratio), 2),
                    "warning": "This column may behave like an identifier or require encoding.",
                }
            )

        # 5) NUMERIC COLUMNS THAT ARE PROBABLY CATEGORICAL
        if col in numeric_cols:
            if unique_count < 15 and integer_like:
                value_range = float(non_null.max() - non_null.min()) if not non_null.empty else 0.0
                if value_range <= 50:
                    numeric_as_categorical.append(
                        {
                            "column": col,
                            "unique_values": int(unique_count),
                            "range": round(value_range, 2),
                            "warning": "This numeric column likely represents categorical data.",
                        }
                    )

        # 6) DISTRIBUTION & STATISTICAL WARNINGS (numeric only)
        if col in numeric_cols and not non_null.empty:
            series_num = pd.to_numeric(series, errors="coerce").dropna()
            if len(series_num) > 1:
                std = float(series_num.std())
                if std <= 1e-6:
                    distribution_warnings.append(
                        {
                            "column": col,
                            "metric": "near_zero_variance",
                            "severity": 3,
                            "warning": "This column may distort analytics and modeling.",
                        }
                    )
                skew = float(series_num.skew())
                if abs(skew) >= 2.0:
                    distribution_warnings.append(
                        {
                            "column": col,
                            "metric": "extreme_skew",
                            "severity": 2,
                            "warning": "This column may distort analytics and modeling.",
                        }
                    )

                q1 = series_num.quantile(0.25)
                q3 = series_num.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outlier_ratio = ((series_num < lower) | (series_num > upper)).mean()
                    if outlier_ratio >= 0.1:
                        distribution_warnings.append(
                            {
                                "column": col,
                                "metric": "heavy_outliers",
                                "severity": 2,
                                "warning": "This column may distort analytics and modeling.",
                            }
                        )

                mode_ratio = series_num.value_counts(normalize=True).iloc[0]
                if mode_ratio >= 0.5:
                    distribution_warnings.append(
                        {
                            "column": col,
                            "metric": "dominant_value",
                            "severity": 2,
                            "warning": "This column may distort analytics and modeling.",
                        }
                    )

    schema_summary = {
        "total_rows": int(total_rows),
        "total_columns": int(total_cols),
        "numeric_count": int(len(numeric_cols)),
        "categorical_count": int(len(categorical_cols)),
        "datetime_count": int(len(datetime_columns)),
        "missing_pct": round(float(missing_pct), 2),
        "duplicate_rows_pct": round(float(duplicate_rows_pct), 2),
    }

    return {
        "id_columns": id_columns,
        "constant_columns": constant_columns,
        "datetime_columns": datetime_columns,
        "high_cardinality": high_cardinality,
        "numeric_as_categorical": numeric_as_categorical,
        "distribution_warnings": distribution_warnings,
        "schema_summary": schema_summary,
    }
