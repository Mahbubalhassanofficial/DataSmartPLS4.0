import streamlit as st
import pandas as pd
import numpy as np

from core.bias import apply_all_biases


st.set_page_config(
    page_title="DataSmartPLS4.0 – Response Bias Simulation",
    layout="wide",
)


st.title("Response Behaviour & Bias Simulation")

st.markdown(
    """
This module applies **realistic response behaviours** to an existing dataset, including:

- Careless responding (random noise in some cells)  
- Straight-lining (same answer across all items for some respondents)  
- Fully random responding for some respondents  
- Midpoint bias (pulling responses toward the central category)  
- Extremity bias (pushing responses toward the ends)  
- Acquiescence (general tendency to agree / upward drift)  
- Missingness (MCAR-style item non-response)  

You can:
1. Upload a CSV file (e.g., generated from **DataSmartPLS4.0** or from your own survey).
2. Select which columns are Likert-type items.
3. Set bias levels.
4. Apply all biases and download the modified dataset.
"""
)

# ------------------------------------------------
# 1. DATA INPUT
# ------------------------------------------------
st.subheader("1. Upload dataset")

uploaded_file = st.file_uploader(
    "Upload a CSV file (item-level data). Non-item columns can be excluded in the next step.",
    type=["csv"],
)

if uploaded_file is None:
    st.info("Please upload a CSV file to configure and apply bias.")
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read CSV file. Error: {e}")
    st.stop()

st.success(f"Dataset loaded: {df.shape[0]} rows × {df.shape[1]} columns.")
st.markdown("### Preview (first 10 rows)")
st.dataframe(df.head(10), use_container_width=True)


# ------------------------------------------------
# 2. SELECT ITEM COLUMNS & LIKERT RANGE
# ------------------------------------------------
st.subheader("2. Select Likert-type item columns")

numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

if not numeric_cols:
    st.error("No numeric columns detected. Likert items must be numeric.")
    st.stop()

selected_items = st.multiselect(
    "Select columns that represent Likert-scale items:",
    options=numeric_cols,
    default=numeric_cols,
)

if not selected_items:
    st.error("Please select at least one Likert item column.")
    st.stop()

items_df = df[selected_items].copy()

# Guess Likert range from data
data_min = int(np.nanmin(items_df.values))
data_max = int(np.nanmax(items_df.values))

st.markdown("#### Likert Scale Range")

col1, col2 = st.columns(2)
with col1:
    likert_min = st.number_input(
        "Likert minimum",
        min_value=1,
        max_value=10,
        value=max(1, data_min),
        step=1,
    )
with col2:
    likert_max = st.number_input(
        "Likert maximum",
        min_value=2,
        max_value=10,
        value=min(7, max(likert_min + 1, data_max)),
        step=1,
    )

if likert_max <= likert_min:
    st.error("Likert maximum must be greater than minimum.")
    st.stop()


# ------------------------------------------------
# 3. SET BIAS LEVELS
# ------------------------------------------------
st.subheader("3. Configure response behaviours & bias levels")

st.markdown("All rates/levels are **proportions** between 0 and 1.")

col_c1, col_c2 = st.columns(2)

with col_c1:
    careless_rate = st.slider(
        "Careless responding (fraction of individual cells randomized)",
        min_value=0.0,
        max_value=0.5,
        value=0.0,
        step=0.01,
    )
    straightlining_rate = st.slider(
        "Straight-lining (fraction of respondents with same answer across all items)",
        min_value=0.0,
        max_value=0.5,
        value=0.0,
        step=0.01,
    )
    random_response_rate = st.slider(
        "Random responding (fraction of respondents answering randomly)",
        min_value=0.0,
        max_value=0.5,
        value=0.0,
        step=0.01,
    )

with col_c2:
    midpoint_bias_level = st.slider(
        "Midpoint bias level (0 = none, 1 = strong pull to middle)",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
    )
    extreme_bias_level = st.slider(
        "Extremity bias level (0 = none, 1 = strong push to scale ends)",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
    )
    acquiescence_level = st.slider(
        "Acquiescence (tendency to agree / shift upward; negative = downward)",
        min_value=-1.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
    )

missing_rate = st.slider(
    "Missingness rate (MCAR; fraction of item cells set to NaN)",
    min_value=0.0,
    max_value=0.5,
    value=0.0,
    step=0.01,
)


# ------------------------------------------------
# 4. APPLY BIAS
# ------------------------------------------------
st.subheader("4. Apply biases and generate biased dataset")

if st.button("Apply selected biases to item data", type="primary"):
    with st.spinner("Applying bias transformations..."):
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

        # merge back with non-item columns
        non_item_cols = [c for c in df.columns if c not in selected_items]
        biased_df = pd.concat([df[non_item_cols].reset_index(drop=True),
                               biased_items.reset_index(drop=True)], axis=1)

    st.success("Bias applied. See preview below.")

    st.markdown("### Preview of biased dataset (first 10 rows)")
    st.dataframe(biased_df.head(10), use_container_width=True)

    st.markdown("### Quick comparison of means (original vs biased items)")
    orig_means = items_df.mean().rename("Original mean")
    biased_means = biased_items.mean().rename("Biased mean")
    compare_df = pd.concat([orig_means, biased_means], axis=1)
    st.dataframe(compare_df.T, use_container_width=True)

    csv_bytes = biased_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download biased dataset as CSV",
        data=csv_bytes,
        file_name="DataSmartPLS4_biased_dataset.csv",
        mime="text/csv",
    )

    st.info(
        "You can now feed this **biased synthetic dataset** into SmartPLS, SEM, or fsQCA "
        "to study robustness, detection of bias, and effectiveness of diagnostics."
    )
else:
    st.caption("Set the bias parameters and click **Apply selected biases to item data**.")
