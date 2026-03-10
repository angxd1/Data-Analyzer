import re
import warnings
import numpy as np
import pandas as pd
from validation_config import DEFAULT_VALIDATION_RULES, ValidationRules
from validation_models import SchemaSummary, ValidationFinding, ValidationResult

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


def _tokenize_name(name: str) -> set[str]:
    return {token for token in re.split(r"[^a-zA-Z0-9]+", name.lower()) if token}


def _has_name_token(name: str, tokens: set[str]) -> bool:
    name_tokens = _tokenize_name(name)
    if name_tokens & tokens:
        return True
    lowered = name.lower()
    return any(token in lowered for token in tokens)


def _datetime_inference(
    series: pd.Series, column_name: str, rules: ValidationRules
) -> dict:
    result = {
        "success": False,
        "method": None,
        "inferred_format": None,
        "parsed_ratio": 0.0,
    }

    if series.dropna().empty:
        return result

    if pd.api.types.is_datetime64_any_dtype(series):
        result.update(
            {
                "success": True,
                "method": "native_datetime",
                "parsed_ratio": 1.0,
                "inferred_format": "datetime",
            }
        )
        return result

    looks_temporal_by_name = _has_name_token(column_name, rules.datetime_name_tokens)
    is_numeric_dtype = pd.api.types.is_numeric_dtype(series)
    if is_numeric_dtype and not looks_temporal_by_name:
        return result

    # Regex-based hint for text columns.
    sample = series.dropna().astype(str).head(200)
    regex_ratio = 0.0
    if not sample.empty:
        pattern_hits = 0
        for val in sample:
            if any(p.search(val) for p in _DATE_PATTERNS):
                pattern_hits += 1
        regex_ratio = pattern_hits / len(sample)
        if regex_ratio >= rules.datetime_regex_threshold:
            result["method"] = "regex"

    # Pandas inference for non-numeric / mixed values.
    if not is_numeric_dtype and (
        looks_temporal_by_name or regex_ratio >= rules.datetime_regex_threshold
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            parsed = pd.to_datetime(series, errors="coerce")
        parsed_ratio = parsed.notna().mean()
        if parsed_ratio >= rules.datetime_parse_threshold:
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
    if looks_temporal_by_name and numeric.between(
        rules.epoch_seconds_min, rules.epoch_seconds_max
    ).mean() >= rules.datetime_parse_threshold:
        result.update(
            {
                "success": True,
                "method": "epoch_seconds",
                "parsed_ratio": round(float(numeric.notna().mean()), 2),
                "inferred_format": "epoch_seconds",
            }
        )
    elif looks_temporal_by_name and numeric.between(
        rules.epoch_millis_min, rules.epoch_millis_max
    ).mean() >= rules.datetime_parse_threshold:
        result.update(
            {
                "success": True,
                "method": "epoch_millis",
                "parsed_ratio": round(float(numeric.notna().mean()), 2),
                "inferred_format": "epoch_millis",
            }
        )

    return result


def _empty_result(df: pd.DataFrame | None) -> ValidationResult:
    total_rows = int(len(df)) if df is not None else 0
    return ValidationResult(
        schema_summary=SchemaSummary(
            total_rows=total_rows,
            total_columns=0,
            numeric_count=0,
            categorical_count=0,
            datetime_count=0,
            missing_pct=0.0,
            duplicate_rows_pct=0.0,
        )
    )


def validate_dataset_typed(
    df: pd.DataFrame, rules: ValidationRules = DEFAULT_VALIDATION_RULES
) -> ValidationResult:
    """
    Validate dataset structure and return diagnostics.

    Returns a structured dictionary with detected column roles and warnings.
    """
    if df is None or df.empty or df.columns.empty:
        return _empty_result(df)

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
        has_id_name = _has_name_token(col, rules.id_name_tokens)
        if (
            unique_ratio > rules.id_uniqueness_threshold
            and unique_count == len(non_null)
            and integer_like
            and (has_id_name or monotonic in {"increasing", "decreasing"})
        ):
            id_columns.append(
                ValidationFinding(
                    column=col,
                    uniqueness_ratio=round(float(unique_ratio), 2),
                    monotonic=monotonic,
                    integer_like=integer_like,
                    warning="This column likely represents an identifier and should not be treated as a feature.",
                )
            )

        # 2) CONSTANT & NEAR-CONSTANT
        value_counts = series.value_counts(dropna=False)
        if not value_counts.empty:
            dominant_ratio = value_counts.iloc[0] / max(total_rows, 1)
            if unique_count <= 1 or dominant_ratio > rules.constant_dominant_ratio:
                constant_columns.append(
                    ValidationFinding(
                        column=col,
                        dominant_value_pct=round(float(dominant_ratio * 100), 2),
                        unique_values=int(unique_count),
                        warning="This column provides little or no analytical value.",
                    )
                )

        # 3) DATETIME INFERENCE
        dt_info = _datetime_inference(series, col, rules)
        if dt_info["success"]:
            datetime_columns.append(
                ValidationFinding(
                    column=col,
                    method=dt_info["method"],
                    parsed_ratio=dt_info["parsed_ratio"],
                    inferred_format=dt_info["inferred_format"],
                    warning="This column appears to represent temporal information.",
                )
            )

        # 4) HIGH-CARDINALITY CATEGORICALS
        if (
            col in categorical_cols
            and unique_count >= rules.high_cardinality_unique_min
            and (
                unique_ratio >= rules.high_cardinality_ratio_threshold
                or unique_count >= rules.high_cardinality_count_threshold
            )
        ):
            high_cardinality.append(
                ValidationFinding(
                    column=col,
                    unique_count=int(unique_count),
                    ratio=round(float(unique_ratio), 2),
                    warning="This column may behave like an identifier or require encoding.",
                )
            )

        # 5) NUMERIC COLUMNS THAT ARE PROBABLY CATEGORICAL
        if col in numeric_cols:
            if unique_count < rules.numeric_as_categorical_unique_max and integer_like:
                value_range = float(non_null.max() - non_null.min()) if not non_null.empty else 0.0
                if value_range <= rules.numeric_as_categorical_range_max:
                    numeric_as_categorical.append(
                        ValidationFinding(
                            column=col,
                            unique_values=int(unique_count),
                            range=round(value_range, 2),
                            warning="This numeric column likely represents categorical data.",
                        )
                    )

        # 6) DISTRIBUTION & STATISTICAL WARNINGS (numeric only)
        if col in numeric_cols and not non_null.empty:
            series_num = pd.to_numeric(series, errors="coerce").dropna()
            if len(series_num) > 1:
                std = float(series_num.std())
                if std <= rules.near_zero_std_threshold:
                    distribution_warnings.append(
                        ValidationFinding(
                            column=col,
                            metric="near_zero_variance",
                            severity=3,
                            warning="This column may distort analytics and modeling.",
                        )
                    )
                skew = float(series_num.skew())
                if abs(skew) >= rules.skew_threshold:
                    distribution_warnings.append(
                        ValidationFinding(
                            column=col,
                            metric="extreme_skew",
                            severity=2,
                            warning="This column may distort analytics and modeling.",
                        )
                    )

                q1 = series_num.quantile(0.25)
                q3 = series_num.quantile(0.75)
                iqr = q3 - q1
                if iqr > 0:
                    lower = q1 - 1.5 * iqr
                    upper = q3 + 1.5 * iqr
                    outlier_ratio = ((series_num < lower) | (series_num > upper)).mean()
                    if outlier_ratio >= rules.outlier_ratio_threshold:
                        distribution_warnings.append(
                            ValidationFinding(
                                column=col,
                                metric="heavy_outliers",
                                severity=2,
                                warning="This column may distort analytics and modeling.",
                            )
                        )

                mode_ratio = series_num.value_counts(normalize=True).iloc[0]
                if mode_ratio >= rules.dominant_numeric_mode_threshold:
                    distribution_warnings.append(
                        ValidationFinding(
                            column=col,
                            metric="dominant_value",
                            severity=2,
                            warning="This column may distort analytics and modeling.",
                        )
                    )

    return ValidationResult(
        id_columns=id_columns,
        constant_columns=constant_columns,
        datetime_columns=datetime_columns,
        high_cardinality=high_cardinality,
        numeric_as_categorical=numeric_as_categorical,
        distribution_warnings=distribution_warnings,
        schema_summary=SchemaSummary(
            total_rows=int(total_rows),
            total_columns=int(total_cols),
            numeric_count=int(len(numeric_cols)),
            categorical_count=int(len(categorical_cols)),
            datetime_count=int(len(datetime_columns)),
            missing_pct=round(float(missing_pct), 2),
            duplicate_rows_pct=round(float(duplicate_rows_pct), 2),
        ),
    )


def validate_dataset(
    df: pd.DataFrame, rules: ValidationRules = DEFAULT_VALIDATION_RULES
) -> dict:
    return validate_dataset_typed(df, rules).to_dict()
