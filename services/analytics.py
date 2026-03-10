import numpy as np
import pandas as pd


def compute_missing_df(df):
    return pd.DataFrame({
        "Column": df.columns,
        "Missing Values": df.isna().sum().values,
        "Missing %": (df.isna().sum().values / len(df) * 100).round(2),
    })


def compute_numeric_stats(df, numeric_cols):
    cols = list(numeric_cols)
    stats = df[cols].describe().T
    stats["median"] = df[cols].median()
    return stats


def compute_categorical_counts(df, column):
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, "Count"]
    counts["Percent"] = (counts["Count"] / len(df) * 100).round(2)
    return counts


def compute_insights(
    df,
    numeric_cols,
    categorical_cols,
    missing_df,
    clean_summary,
    validation=None,
):
    insights = []

    high_missing = missing_df[missing_df["Missing %"] > 20]
    if not high_missing.empty:
        insights.append(
            f"⚠️ High missing values: {', '.join(high_missing['Column'])}"
        )

    if clean_summary["duplicates_removed"] > 0:
        insights.append(
            f"🧹 Removed {clean_summary['duplicates_removed']} duplicate rows."
        )

    if len(numeric_cols) > 0:
        stds = df[numeric_cols].std().sort_values(ascending=False)
        insights.append(
            f"📊 Highest variability: {stds.index[0]} (std = {stds.iloc[0]:.2f})"
        )

    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr().abs()
        upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
        top = upper.stack().sort_values(ascending=False)
        if not top.empty and top.iloc[0] > 0.75:
            pair = top.index[0]
            insights.append(
                f"🔗 Strong correlation: {pair[0]} & {pair[1]} (r={top.iloc[0]:.2f})"
            )

    if len(categorical_cols) > 0:
        cat0 = categorical_cols[0]
        top_val = df[cat0].value_counts(normalize=True).idxmax()
        pct = df[cat0].value_counts(normalize=True).max() * 100
        insights.append(f"📌 Most common in {cat0}: {top_val} ({pct:.1f}%)")

    if validation:
        id_cols = [c["column"] for c in validation.get("id_columns", [])]
        if id_cols:
            insights.append(
                f"🧭 Identifier-like columns detected: {', '.join(id_cols)}."
            )

        high_card = [c["column"] for c in validation.get("high_cardinality", [])]
        if high_card:
            insights.append(
                f"🧩 High-cardinality categoricals: {', '.join(high_card)}."
            )

        dist_warn = {w["column"] for w in validation.get("distribution_warnings", [])}
        if dist_warn:
            insights.append(
                f"⚠️ Distribution warnings for: {', '.join(sorted(dist_warn))}."
            )

    return insights


def calculate_data_quality_score(df, df_raw, validation=None):
    """
    Compute a 0–100 data quality score and penalty breakdown.

    Returns:
        score (int): final score bounded to [0, 100]
        label (str): Excellent / Good / Fair / Poor
        breakdown (dict): penalty details and component metrics
    """
    total_cells = max(len(df) * len(df.columns), 1)
    missing_cells = int(df.isna().sum().sum())
    missing_pct = (missing_cells / total_cells) * 100

    duplicates = int(df_raw.duplicated().sum())
    duplicate_pct = (duplicates / max(len(df_raw), 1)) * 100

    constant_cols = int((df.nunique(dropna=False) <= 1).sum())
    constant_pct = (constant_cols / max(len(df.columns), 1)) * 100

    numeric_cols = df.select_dtypes(include=np.number).columns
    outlier_cells = 0
    numeric_cells = 0
    for col in numeric_cols:
        series = df[col].dropna()
        numeric_cells += len(series)
        if len(series) < 4:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_cells += int(((series < lower) | (series > upper)).sum())
    outlier_pct = (outlier_cells / max(numeric_cells, 1)) * 100

    nonconvertible_cols = 0
    for col in df_raw.columns:
        if pd.api.types.is_numeric_dtype(df_raw[col]):
            continue
        series = df_raw[col]
        if series.notna().sum() == 0:
            continue
        converted = pd.to_numeric(series, errors="coerce")
        convertible_ratio = converted.notna().mean()
        # Only penalize columns that look numeric-like but fail conversion.
        if 0.2 <= convertible_ratio < 0.9:
            nonconvertible_cols += 1

    # Penalty design: missing values + duplicates are heavy, outliers are light.
    penalty_missing = min(50.0, missing_pct * 0.8)
    penalty_duplicates = min(25.0, duplicate_pct * 1.5)
    penalty_constant = min(15.0, constant_pct * 0.6)
    penalty_outliers = min(10.0, outlier_pct * 0.2)
    penalty_nonconvertible = min(15.0, nonconvertible_cols * 3.0)

    penalty_schema = 0.0
    if validation:
        penalty_schema += min(10.0, len(validation.get("id_columns", [])) * 2.0)
        penalty_schema += min(
            8.0, len(validation.get("high_cardinality", [])) * 1.5
        )
        penalty_schema += min(
            8.0, len(validation.get("distribution_warnings", [])) * 1.0
        )

    total_penalty = (
        penalty_missing
        + penalty_duplicates
        + penalty_constant
        + penalty_outliers
        + penalty_nonconvertible
        + penalty_schema
    )

    score = int(round(max(0.0, min(100.0, 100.0 - total_penalty))))

    if score >= 90:
        label = "Excellent"
    elif score >= 75:
        label = "Good"
    elif score >= 50:
        label = "Fair"
    else:
        label = "Poor"

    breakdown = {
        "missing_pct": round(missing_pct, 2),
        "duplicates": duplicates,
        "duplicate_pct": round(duplicate_pct, 2),
        "constant_cols": constant_cols,
        "outlier_pct": round(outlier_pct, 2),
        "nonconvertible_cols": nonconvertible_cols,
        "penalty_missing": round(penalty_missing, 2),
        "penalty_duplicates": round(penalty_duplicates, 2),
        "penalty_constant": round(penalty_constant, 2),
        "penalty_outliers": round(penalty_outliers, 2),
        "penalty_nonconvertible": round(penalty_nonconvertible, 2),
        "penalty_schema": round(penalty_schema, 2),
        "total_penalty": round(total_penalty, 2),
    }

    return score, label, breakdown
