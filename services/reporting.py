
def build_report(df, clean_summary, insights, validation=None):
    report = "SMART DATA ANALYZER REPORT\n\n"
    report += f"Rows: {df.shape[0]}, Columns: {df.shape[1]}\n\n"
    report += "Cleaning Summary:\n"
    for k, v in clean_summary.items():
        report += f"- {k}: {v}\n"

    report += "\nAutomated Insights:\n"
    for i in insights:
        report += f"- {i}\n"

    if validation:
        report += "\nDataset Diagnostics & Validation:\n"
        if validation.get("id_columns"):
            cols = ", ".join([c["column"] for c in validation["id_columns"]])
            report += f"- Identifier-like columns: {cols}\n"
        if validation.get("constant_columns"):
            cols = ", ".join([c["column"] for c in validation["constant_columns"]])
            report += f"- Low-information columns: {cols}\n"
        if validation.get("datetime_columns"):
            cols = ", ".join([c["column"] for c in validation["datetime_columns"]])
            report += f"- Temporal columns: {cols}\n"
        if validation.get("high_cardinality"):
            cols = ", ".join([c["column"] for c in validation["high_cardinality"]])
            report += f"- High-cardinality columns: {cols}\n"
        if validation.get("numeric_as_categorical"):
            cols = ", ".join([c["column"] for c in validation["numeric_as_categorical"]])
            report += f"- Numeric-as-categorical: {cols}\n"
        if validation.get("distribution_warnings"):
            cols = ", ".join(
                sorted({c["column"] for c in validation["distribution_warnings"]})
            )
            report += f"- Distribution warnings: {cols}\n"
        summary = validation.get("schema_summary", {})
        if summary:
            report += (
                "- Schema summary: "
                f"rows={summary.get('total_rows')}, "
                f"cols={summary.get('total_columns')}, "
                f"numeric={summary.get('numeric_count')}, "
                f"categorical={summary.get('categorical_count')}, "
                f"datetime={summary.get('datetime_count')}, "
                f"missing%={summary.get('missing_pct')}, "
                f"dup_rows%={summary.get('duplicate_rows_pct')}\n"
            )

    return report
