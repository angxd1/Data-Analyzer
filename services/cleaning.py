import pandas as pd
import numpy as np


def clean_dataset(df_raw, options):
    df = df_raw.copy()
    summary = {
        "duplicates_removed": 0,
        "numeric_filled": 0,
        "categorical_filled": 0,
        "strings_trimmed": False,
        "numeric_converted": False,
    }

    if options["convert_numeric"]:
        for col in df.columns:
            before_type = df[col].dtype
            try:
                converted = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                continue
            df[col] = converted
            if df[col].dtype != before_type:
                summary["numeric_converted"] = True

    numeric_cols = df.select_dtypes(include=np.number).columns
    categorical_cols = df.select_dtypes(exclude=np.number).columns

    if options["trim_strings"]:
        for col in categorical_cols:
            non_null_mask = df[col].notna()
            df.loc[non_null_mask, col] = df.loc[non_null_mask, col].astype(str).str.strip()
        summary["strings_trimmed"] = True

    if options["fill_numeric"]:
        for col in numeric_cols:
            missing = df[col].isna().sum()
            summary["numeric_filled"] += missing
            df[col] = df[col].fillna(df[col].median())

    if options["fill_categorical"]:
        for col in categorical_cols:
            missing = df[col].isna().sum()
            summary["categorical_filled"] += missing
            df[col] = df[col].fillna("Unknown")

    if options["drop_duplicates"]:
        summary["duplicates_removed"] = df.duplicated().sum()
        df = df.drop_duplicates()

    return df, summary
