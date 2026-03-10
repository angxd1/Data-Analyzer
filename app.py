import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import io

from services.cleaning import clean_dataset
from services.analytics import (
    compute_missing_df,
    compute_numeric_stats,
    compute_categorical_counts,
    compute_insights,
    calculate_data_quality_score,
)
from services.reporting import build_report
from validation import validate_dataset
from storage import (
    init_db,
    save_dataset,
    save_cleaned_data,
    save_report,
    get_datasets,
    get_reports,
    get_cleaned_data,
)
from ui.sidebar import render_cleaning_options, render_show_raw_toggle
from ui.sections import (
    render_previews,
    render_cleaning_summary,
    render_core_analytics,
    render_visualizations,
    render_insights,
    render_exports,
)

st.set_page_config(page_title="Data Health Console", layout="wide")

with open("app/theme.css", "r", encoding="utf-8") as theme_file:
    GLOBAL_CSS = f"<style>{theme_file.read()}</style>"

SAMPLE_CSV = """id,age,city,salary,signup_date,plan,active
1,23,New York,72000,2023-01-14,Pro,True
2,41,Chicago,98000,2022-11-03,Basic,True
3,35,San Francisco,132000,2021-05-19,Pro,True
4,29,Austin,88000,2023-07-22,Basic,False
5,52,Seattle,150000,2020-02-08,Enterprise,True
6,46,Boston,115000,2019-09-14,Pro,True
7,31,Miami,79000,2023-03-11,Basic,False
8,27,Denver,83000,2022-06-30,Basic,True
9,39,Atlanta,97000,2021-08-04,Pro,True
10,33,Los Angeles,102000,2022-12-12,Pro,True
"""

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

st.markdown(
    """
<div class="hero">
  <div class="hero-kicker">Portfolio product case study</div>
  <div class="hero-title">Data Health Console</div>
  <div class="hero-sub">Upload a CSV and get instant cleaning, diagnostics, and executive-ready insights.</div>
  <div class="hero-badges">
    <span class="badge">Cleaner</span>
    <span class="badge">Diagnostics</span>
    <span class="badge">Insights</span>
    <span class="badge">Export</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@st.cache_data(show_spinner=False)
def read_csv_from_bytes(file_bytes):
    return pd.read_csv(io.BytesIO(file_bytes))


@st.cache_data(show_spinner=False)
def cached_missing_df(df):
    return compute_missing_df(df)


@st.cache_data(show_spinner=False)
def cached_numeric_stats(df, numeric_cols):
    return compute_numeric_stats(df, numeric_cols)


@st.cache_data(show_spinner=False)
def cached_categorical_counts(df, column):
    return compute_categorical_counts(df, column)


@st.cache_data(show_spinner=False)
def cached_validation(df):
    return validate_dataset(df)


init_db()

st.sidebar.header("Quick Actions")
if st.sidebar.button("Reset session"):
    st.session_state.clear()
    st.rerun()
st.sidebar.markdown(
    "<div class='sidebar-caption'>Upload a CSV or load the sample dataset.</div>",
    unsafe_allow_html=True,
)

st.write("")

upload_col, sample_col = st.columns([2, 1], vertical_alignment="center")
with upload_col:
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    st.caption("Max file size: 50MB")
with sample_col:
    st.markdown("**No file handy?**")
    if st.button("Load sample dataset"):
        st.session_state["use_sample"] = True

use_sample = st.session_state.get("use_sample", False)

if uploaded_file:
    st.session_state["use_sample"] = False
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name
elif use_sample:
    file_bytes = SAMPLE_CSV.encode("utf-8")
    filename = "sample_dataset.csv"
else:
    st.info("Upload a CSV to begin, or load the sample dataset to explore the UI.")
    st.stop()

if not file_bytes:
    st.error("Uploaded file is empty.")
    st.stop()
if len(file_bytes) > MAX_UPLOAD_BYTES:
    st.error("File too large. Max supported size is 50MB.")
    st.stop()

dataset_hash = hashlib.md5(file_bytes).hexdigest()
try:
    df_raw = read_csv_from_bytes(file_bytes)
except Exception as exc:
    st.error(f"Failed to read CSV: {exc}")
    st.stop()

dataset_token = f"{filename}:{dataset_hash}"
if st.session_state.get("dataset_token") != dataset_token:
    dataset_id = save_dataset(filename)
    st.session_state["dataset_id"] = dataset_id
    st.session_state["dataset_token"] = dataset_token

st.write("")
options = render_cleaning_options()
show_raw = render_show_raw_toggle()

df, clean_summary = clean_dataset(df_raw, options)
if st.session_state.get("cleaned_saved_token") != (dataset_token, str(options)):
    save_cleaned_data(st.session_state["dataset_id"], df)
    st.session_state["cleaned_saved_token"] = (dataset_token, str(options))

numeric_cols = df.select_dtypes(include=np.number).columns
categorical_cols = df.select_dtypes(exclude=np.number).columns

missing_df = cached_missing_df(df)
validation = cached_validation(df)

insights = compute_insights(
    df, numeric_cols, categorical_cols, missing_df, clean_summary, validation
)
report = build_report(df, clean_summary, insights, validation)


tab_overview, tab_quality, tab_insights, tab_visuals, tab_report, tab_history = st.tabs(
    ["Overview", "Data Quality", "Insights", "Visuals", "Report", "History"]
)

with tab_overview:
    st.subheader("Executive Snapshot")
    st.markdown(
        "<div class='card section-note'>Fast signal before deep dive. Highlight the health and scope of the dataset.</div>",
        unsafe_allow_html=True,
    )
    kpi_cols = st.columns(4)
    kpi_cols[0].metric("Rows", f"{df.shape[0]:,}")
    kpi_cols[1].metric("Columns", f"{df.shape[1]:,}")
    kpi_cols[2].metric("Missing %", f"{missing_df['Missing %'].mean():.2f}")
    duplicate_pct = (clean_summary.get("duplicates_removed", 0) / max(len(df_raw), 1)) * 100
    kpi_cols[3].metric("Duplicates %", f"{duplicate_pct:.2f}")

    st.divider()

    render_previews(df_raw, df, show_raw)
    render_cleaning_summary(df, clean_summary, missing_df)

    st.divider()

    cat_counts = None
    if len(categorical_cols) > 0:
        selected_cat = st.selectbox("Select categorical column", categorical_cols)
        cat_counts = cached_categorical_counts(df, selected_cat)

    numeric_stats = None
    if len(numeric_cols) > 0:
        numeric_stats = cached_numeric_stats(df, tuple(numeric_cols))

    render_core_analytics(df, numeric_cols, categorical_cols, numeric_stats, cat_counts)

with tab_quality:
    st.subheader("Dataset Diagnostics & Validation")

    if validation["id_columns"]:
        st.markdown("**Identifiers**")
        for item in validation["id_columns"]:
            st.write(
                f"• {item['column']} — uniqueness {item['uniqueness_ratio']} "
                f"(monotonic: {item['monotonic']})"
            )
            st.caption(item["warning"])
    else:
        st.info("No identifier-like columns detected.")

    if validation["constant_columns"]:
        st.markdown("**Low-Information Columns**")
        for item in validation["constant_columns"]:
            st.write(
                f"• {item['column']} — dominant {item['dominant_value_pct']}% "
                f"(unique: {item['unique_values']})"
            )
            st.caption(item["warning"])
    else:
        st.info("No low-information columns detected.")

    if validation["datetime_columns"]:
        st.markdown("**Temporal Columns**")
        for item in validation["datetime_columns"]:
            st.write(
                f"• {item['column']} — method {item['method']} "
                f"(parsed: {item['parsed_ratio']})"
            )
            st.caption(item["warning"])
    else:
        st.info("No datetime-like columns detected.")

    if validation["high_cardinality"]:
        st.markdown("**High-Cardinality Columns**")
        for item in validation["high_cardinality"]:
            st.write(
                f"• {item['column']} — unique {item['unique_count']} "
                f"(ratio: {item['ratio']})"
            )
            st.caption(item["warning"])
    else:
        st.info("No high-cardinality columns detected.")

    if validation["numeric_as_categorical"] or validation["distribution_warnings"]:
        st.markdown("**Feature Warnings**")
        for item in validation["numeric_as_categorical"]:
            st.write(
                f"• {item['column']} — unique {item['unique_values']} "
                f"(range: {item['range']})"
            )
            st.caption(item["warning"])
        for item in validation["distribution_warnings"]:
            st.write(
                f"• {item['column']} — {item['metric']} (severity: {item['severity']})"
            )
            st.caption(item["warning"])
    else:
        st.info("No feature warnings detected.")

    st.markdown("**Schema Summary**")
    summary = validation["schema_summary"]
    st.write(
        f"Rows: {summary['total_rows']} | Columns: {summary['total_columns']} | "
        f"Numeric: {summary['numeric_count']} | Categorical: {summary['categorical_count']} | "
        f"Datetime: {summary['datetime_count']}"
    )
    st.write(
        f"Missing %: {summary['missing_pct']} | Duplicate rows %: {summary['duplicate_rows_pct']}"
    )

    st.markdown("**Data Quality Score**")
    score, label, breakdown = calculate_data_quality_score(df, df_raw, validation)
    st.metric("Quality Score", score)
    st.write(f"Quality Label: **{label}**")
    st.write("Penalties / Reasons:")
    st.write(
        f"• Missing values penalty: -{breakdown['penalty_missing']} "
        f"(missing {breakdown['missing_pct']}%)"
    )
    st.write(
        f"• Duplicate rows penalty: -{breakdown['penalty_duplicates']} "
        f"(duplicates {breakdown['duplicates']})"
    )
    st.write(
        f"• Constant columns penalty: -{breakdown['penalty_constant']} "
        f"(constant {breakdown['constant_cols']})"
    )
    st.write(
        f"• Outliers penalty: -{breakdown['penalty_outliers']} "
        f"(outlier {breakdown['outlier_pct']}%)"
    )
    st.write(
        f"• Non-convertible columns penalty: -{breakdown['penalty_nonconvertible']} "
        f"(count {breakdown['nonconvertible_cols']})"
    )
    st.write(
        f"• Schema warnings penalty: -{breakdown['penalty_schema']}"
    )

with tab_insights:
    st.subheader("Insight Brief")
    if insights:
        render_insights(insights)
    else:
        st.info("No insights generated yet.")

with tab_visuals:
    st.subheader("Exploratory Visuals")
    render_visualizations(df, numeric_cols, categorical_cols)

with tab_report:
    st.subheader("Executive Report")
    if st.button("Save Report to Database"):
        if "dataset_id" in st.session_state:
            save_report(st.session_state["dataset_id"], report)
            st.success("Report saved.")
            st.rerun()
        else:
            st.error("No dataset ID found to save the report.")
    render_exports(df, report)

with tab_history:
    st.subheader("Saved Analysis History")
    datasets = get_datasets()
    if datasets:
        dataset_labels = [
            f"{d['name']} ({d['upload_time']})" for d in datasets
        ]
        selected_index = st.selectbox(
            "Select a dataset", range(len(datasets)), format_func=lambda i: dataset_labels[i]
        )
        selected_dataset_id = datasets[selected_index]["id"]
        cleaned_snapshot = get_cleaned_data(selected_dataset_id)
        if cleaned_snapshot:
            st.download_button(
                "Download Cleaned CSV",
                cleaned_snapshot["csv_data"],
                file_name="cleaned_dataset.csv",
                mime="text/csv",
            )
        else:
            st.info("No cleaned data saved for this dataset yet.")
        reports = get_reports(selected_dataset_id)
        if reports:
            for rep in reports:
                with st.expander(f"Report {rep['id']} • {rep['created_at']}"):
                    st.write(rep["report_text"][:2000])
        else:
            st.info("No reports saved for this dataset yet.")
    else:
        st.info("No datasets saved yet.")
