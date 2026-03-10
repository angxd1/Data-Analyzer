import matplotlib.pyplot as plt
import streamlit as st



def render_previews(df_raw, df, show_raw):
    if show_raw:
        st.subheader("Original Dataset Preview")
        st.dataframe(df_raw.head(30))

    st.subheader("Cleaned Dataset Preview")
    st.dataframe(df.head(30))


def render_cleaning_summary(df, clean_summary, missing_df):
    st.subheader("Cleaning Summary")

    st.write(f"Duplicate rows removed: {clean_summary['duplicates_removed']}")
    st.write(f"Numeric values filled: {clean_summary['numeric_filled']}")
    st.write(f"Categorical values filled: {clean_summary['categorical_filled']}")
    st.write(f"Text columns trimmed: {clean_summary['strings_trimmed']}")
    st.write(f"Numeric auto-conversion applied: {clean_summary['numeric_converted']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", df.shape[0])
    col2.metric("Columns", df.shape[1])
    col3.metric("Missing Values", df.isna().sum().sum())

    st.dataframe(missing_df)


def render_core_analytics(df, numeric_cols, categorical_cols, numeric_stats, cat_counts):
    st.header("Core Analytics")

    if len(numeric_cols) > 0:
        st.subheader("Numeric Summary Statistics")
        st.dataframe(numeric_stats)

    if len(categorical_cols) > 0:
        st.subheader("Categorical Breakdown")
        st.dataframe(cat_counts)

    if len(numeric_cols) >= 2:
        st.subheader("Correlation Matrix")
        st.dataframe(df[numeric_cols].corr().style.background_gradient(cmap="coolwarm"))


def render_visualizations(df, numeric_cols, categorical_cols):
    st.header("Data Visualizations")

    if len(numeric_cols) > 0:
        num = st.selectbox("Numeric column", numeric_cols)
        colA, colB = st.columns(2)

        with colA:
            fig, ax = plt.subplots()
            ax.hist(df[num].dropna(), bins=30)
            ax.set_title(f"Distribution of {num}")
            st.pyplot(fig)

        with colB:
            fig, ax = plt.subplots()
            ax.boxplot(df[num].dropna(), vert=False)
            ax.set_title(f"Box Plot of {num}")
            st.pyplot(fig)

    if len(numeric_cols) >= 2:
        x = st.selectbox("X-axis", numeric_cols, index=0)
        y = st.selectbox("Y-axis", numeric_cols, index=1)
        fig, ax = plt.subplots()
        ax.scatter(df[x], df[y], alpha=0.6)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(f"{x} vs {y}")
        st.pyplot(fig)

    if len(categorical_cols) > 0:
        cat = st.selectbox("Categorical column", categorical_cols, key="barcat")
        top = df[cat].value_counts().head(10)
        fig, ax = plt.subplots()
        ax.bar(top.index.astype(str), top.values)
        plt.xticks(rotation=45)
        ax.set_title(f"Top categories in {cat}")
        st.pyplot(fig)


def render_insights(insights):
    st.header("Automated Insights")

    if insights:
        for item in insights:
            st.write(item)
    else:
        st.info("No major insights detected.")


def render_exports(df, report):
    st.header("Export & Reports")

    colE, colF = st.columns(2)

    with colE:
        st.download_button(
            "Download Cleaned Dataset (CSV)",
            df.to_csv(index=False),
            "cleaned_dataset.csv",
            "text/csv",
        )

    with colF:
        st.download_button(
            "Download Analysis Report",
            report,
            "analysis_report.txt",
            "text/plain",
        )

    st.subheader("Report Preview")
    st.code(report[:2000], language=None)
