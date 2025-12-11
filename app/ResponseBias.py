import streamlit as st
import pandas as pd
import numpy as np

from core.bias import apply_all_biases
from app.branding import render_app_header, render_app_footer


# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="DataSmartPLS4.0 – Response Bias Simulation",
    layout="wide",
)

# Branding header
render_app_header("Response Behaviour & Bias Simulation")

# ------------------------------------------------
# INTRO
# ------------------------------------------------
st.markdown(
    """
This module applies **realistic response behaviours** to an existing dataset, including:

- **Careless responding:** random noise  
- **Straight-lining:** same score across items  
- **Random responding:** full random patterns  
- **Midpoint bias:** pull toward center  
- **Extremity bias:** push toward ends  
- **Acquiescence bias:** tendency to agree  
- **Missingness (MCAR):** random item-level missing data  

### Workflow
1. Upload dataset (CSV)  
2. Select Likert-type columns  
3. Configure bias settings  
4. Apply biases → download modified dataset  
"""
)


# ------------------------------------------------
# 1. DATA UPLOAD
# ------------------------------------------------
st.subheader("1. Upload dataset")

uploaded_file = st.file_uploader(
    "Upload a CSV file (item-level survey data).",
    type=["csv"],
)

if uploaded_file is None:
    st.info("Please upload a CSV file to continue.")
    render_app_footer()
    st.stop()

# Load data
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read the CSV file. Error: {e}")
    render_app_footer()
    st.stop()

st.success(f"Dataset loaded: **{df.shape[0]} rows × {df.shape[1]} columns**")
st.dataframe(df.head(10), use_container_width=True)


# ------------------------------------------------
# 2. SELECT ITEM COLUMNS
# ------------------------------------------------
st.subheader("2. Select Likert-type item columns")

numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

if not numeric_cols:
    st.error("No numeric columns detected — Likert items must be numeric.")
    render_app_footer()
    st.stop()

selected_items = st.multiselect(
    "Select Likert-scale item columns:",
    options=numeric_cols,
    default=numeric_cols,
)

if not selected_items:
    st.error("Select at least one Likert item column.")
    render_app_footer()
    st.stop()

items_df = df[selected_items].copy()

# Auto-detect Likert range
data_min = int(np.nanmin(items_df.values))
data_max = int(np.nanmax(items_df.values))

col_a, col_b = st.columns(2)
with col_a:
    likert_min = st.number_input(
        "Likert minimum",
        min_value=1,
        max_value=10,
        value=max(1, data_min),
        step=1,
    )
with col_b:
    likert_max = st.number_input(
        "Likert maximum",
        min_value=2,
        max_value=10,
        value=min(7, max(likert_min + 1, data_max)),
        step=1,
    )

if likert_max <= likert_min:
    st.error("Likert maximum must be greater than minimum.")
    render_app_footer()
    st.stop()


# ------------------------------------------------
# 3. BIAS SETTINGS
# ------------------------------------------------
st.subheader("3. Configure response behaviours")

st.markdown("All values represent **proportions (0–1)** or **strength levels (0–1)**.")

col1, col2 = st.columns(2)

with col1:
    careless_rate = st.slider(
        "Careless responding (cell randomization rate)",
        0.0, 0.5, 0.0, 0.01
    )
    straightlining_rate = st.slider(
        "Straight-lining (fraction of respondents)",
        0.0, 0.5, 0.0, 0.01
    )
    random_response_rate = st.slider(
        "Random responding (fraction of respondents)",
        0.0, 0.5, 0.0, 0.01
    )

with col2:
    midpoint_bias_level = st.slider(
        "Midpoint bias strength",
        0.0, 1.0, 0.0, 0.05
    )
    extreme_bias_level = st.slider(
        "Extremity bias strength",
        0.0, 1.0, 0.0, 0.05
    )
    acquiescence_level = st.slider(
        "Acquiescence (positive = upwards shift, negative = downwards)",
        -1.0, 1.0, 0.0, 0.1
    )

missing_rate = st.slider(
    "Missingness rate (MCAR)",
    0.0, 0.5, 0.0, 0.01
)


# ------------------------------------------------
# 4. APPLY BIASES
# ------------------------------------------------
st.subheader("4. Apply biases and generate modified dataset")

if st.button("Apply biases to the dataset", type="primary"):

    with st.spinner("Applying response behaviour models..."):

        biased_items = apply_all_biases(
            df=items_df,
            likert_min=int(likert_min),
            likert_max=int(likert_max),
            careless_rate=float(careless_rate),
            straightlining_rate=float(straightlining_rate),
            random_response_rate=float(random_response_rate),
            midpoint_bias_level=float(midpoint_bias_level),
            extreme_bias_level=float(extreme_bias_level),
            acquiescence_level=float(acquiescence_level),
            missing_rate=float(missing_rate),
        )

        non_item_cols = [c for c in df.columns if c not in selected_items]

        biased_df = pd.concat(
            [df[non_item_cols].reset_index(drop=True),
             biased_items.reset_index(drop=True)],
            axis=1
        )

    st.success("Bias transformation applied successfully.")

    st.markdown("### Preview of Biased Dataset (Top 10 Rows)")
    st.dataframe(biased_df.head(10), use_container_width=True)

    st.markdown("### Comparison of Means (Original vs Biased)")
    compare_df = pd.concat(
        [items_df.mean().rename("Original"), biased_items.mean().rename("Biased")],
        axis=1
    )
    st.dataframe(compare_df.T, use_container_width=True)

    # Download button
    st.download_button(
        "📥 Download Biased Dataset (CSV)",
        biased_df.to_csv(index=False).encode("utf-8"),
        file_name="DataSmartPLS4_biased_dataset.csv",
        mime="text/csv",
    )

else:
    st.caption("Set behaviour parameters, then click **Apply biases**.")


# ------------------------------------------------
# FOOTER
# ------------------------------------------------
render_app_footer()
