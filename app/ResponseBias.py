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
# INTRODUCTION
# ------------------------------------------------
st.markdown(
    """
This module applies **realistic human response behaviours** to an existing dataset.

### Supported Bias Models
- **Careless responding** (random item-wise noise)  
- **Straight-lining** (fixed response patterns)  
- **Random responding** (full respondent-level randomness)  
- **Midpoint bias** (pulling all scores toward center)  
- **Extremity bias** (inflating edges of the scale)  
- **Acquiescence** (agreement tendency: upward/downward shift)  
- **MCAR Missingness** (random missing values)

### Workflow
1. Upload an **item-level CSV dataset**  
2. Select Likert-type variables  
3. Configure behaviour parameters  
4. Apply transformations → Download enhanced dataset  
"""
)

# ------------------------------------------------
# 1. DATA UPLOAD
# ------------------------------------------------
st.subheader("1. Upload Dataset")

uploaded_file = st.file_uploader(
    "Upload a CSV file (item-level survey data)", type=["csv"]
)

if uploaded_file is None:
    st.info("Please upload a CSV file to begin.")
    render_app_footer()
    st.stop()

# Load data
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Unable to read CSV file. Error: {e}")
    render_app_footer()
    st.stop()

st.success(f"Dataset loaded successfully: **{df.shape[0]} rows × {df.shape[1]} columns**")
st.dataframe(df.head(10), use_container_width=True)


# ------------------------------------------------
# 2. SELECT LIKERT ITEM COLUMNS
# ------------------------------------------------
st.subheader("2. Select Likert-Type Item Columns")

numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

if not numeric_cols:
    st.error("No numeric columns found — Likert items must be numeric.")
    render_app_footer()
    st.stop()

selected_items = st.multiselect(
    "Select item columns to apply response behaviour models:",
    options=numeric_cols,
    default=numeric_cols,
)

if not selected_items:
    st.error("Select at least one item column.")
    render_app_footer()
    st.stop()

items_df = df[selected_items].copy()

# Auto-detect Likert range from data
data_min = int(np.nanmin(items_df.values))
data_max = int(np.nanmax(items_df.values))

col_a, col_b = st.columns(2)
with col_a:
    likert_min = st.number_input(
        "Likert Minimum",
        min_value=1,
        max_value=10,
        value=max(1, data_min),
        step=1
    )
with col_b:
    likert_max = st.number_input(
        "Likert Maximum",
        min_value=2,
        max_value=10,
        value=max(data_max, likert_min + 1),
        step=1
    )

if likert_max <= likert_min:
    st.error("Likert maximum must be greater than minimum.")
    render_app_footer()
    st.stop()


# ------------------------------------------------
# 3. CONFIGURE BIAS SETTINGS
# ------------------------------------------------
st.subheader("3. Configure Response Behaviours")

st.markdown("All sliders represent **proportions (0–1)** or **intensity levels**.")

col1, col2 = st.columns(2)

with col1:
    careless_rate = st.slider(
        "Careless Responding (cell-level noise probability)",
        0.0, 0.50, 0.00, step=0.01
    )
    straightlining_rate = st.slider(
        "Straight-Lining (fraction of respondents)",
        0.0, 0.50, 0.00, step=0.01
    )
    random_response_rate = st.slider(
        "Random Responding (fraction of respondents)",
        0.0, 0.50, 0.00, step=0.01
    )

with col2:
    midpoint_bias_level = st.slider(
        "Midpoint Bias Strength",
        0.0, 1.0, 0.00, step=0.05
    )
    extreme_bias_level = st.slider(
        "Extremity Bias Strength",
        0.0, 1.0, 0.00, step=0.05
    )
    acquiescence_level = st.slider(
        "Acquiescence (agreement tendency: +upwards / -downwards)",
        -1.0, 1.0, 0.00, step=0.10
    )

missing_rate = st.slider(
    "Missingness Rate (MCAR)",
    0.0, 0.50, 0.00, step=0.01
)


# ------------------------------------------------
# 4. APPLY RESPONSE BIASES
# ------------------------------------------------
st.subheader("4. Apply Biases and Generate Modified Dataset")

if st.button("Apply Bias Models", type="primary"):

    with st.spinner("Applying response behaviour transformations..."):

        try:
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
        except Exception as e:
            st.error(f"Bias application failed: {e}")
            render_app_footer()
            st.stop()

        # Recombine with non-item variables
        non_item_cols = [c for c in df.columns if c not in selected_items]
        biased_df = pd.concat(
            [
                df[non_item_cols].reset_index(drop=True),
                biased_items.reset_index(drop=True)
            ],
            axis=1
        )

    st.success("Bias transformation applied successfully.")

    st.markdown("### Preview of Modified Dataset (First 10 Rows)")
    st.dataframe(biased_df.head(10), use_container_width=True)

    # Means comparison
    st.markdown("### Comparison of Means (Original vs Biased)")
    compare_df = pd.DataFrame({
        "Original": items_df.mean(),
        "Biased": biased_items.mean()
    })
    st.dataframe(compare_df.T, use_container_width=True)

    # Download button
    st.download_button(
        label="📥 Download Biased Dataset (CSV)",
        data=biased_df.to_csv(index=False).encode("utf-8"),
        file_name="DataSmartPLS4_biased_dataset.csv",
        mime="text/csv",
    )

else:
    st.caption("Adjust behaviour parameters, then click **Apply Bias Models**.")

# ------------------------------------------------
# FOOTER
# ------------------------------------------------
render_app_footer()
