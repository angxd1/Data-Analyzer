import streamlit as st


def render_cleaning_options():
    with st.expander("Cleaning Options", expanded=False):
        return {
            "drop_duplicates": st.checkbox("Drop duplicate rows", key="opt_drop_duplicates"),
            "fill_numeric": st.checkbox(
                "Fill missing numeric values (median)", key="opt_fill_numeric"
            ),
            "fill_categorical": st.checkbox(
                "Fill missing categorical values ('Unknown')", key="opt_fill_categorical"
            ),
            "trim_strings": st.checkbox(
                "Trim whitespace from text columns", key="opt_trim_strings"
            ),
            "convert_numeric": st.checkbox(
                "Auto-convert numeric columns", key="opt_convert_numeric"
            ),
        }


def render_show_raw_toggle():
    return st.checkbox("Show original dataset", key="opt_show_raw")
