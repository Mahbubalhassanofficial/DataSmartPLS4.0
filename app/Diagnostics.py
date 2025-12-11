import streamlit as st
import pandas as pd

from core.diagnostics import compute_measurement_diagnostics


st.set_page_config(
    page_title="DataSmartPLS4.0 – Diagnostics",
    layout="wide",
)


st.title("Measurement Diagnostics – Reliability & Validity")

st.markdown(
    """
This page computes **psychometric diagnostics** for reflective measurement models, including:

- Cronbach's Alpha  
- Composite Reliability (CR)  
- Average Variance Extracted (AVE)  
- Construct-level correlation matrix  
- HTMT matrix  

You can upload:
- A CSV generated from **DataSmartPLS4.0**, or  
- Any survey dataset where item columns are named like `PE_01`, `PE_02`, `EE_01`, etc.

Constructs are automatically detected from the **prefix** before the underscore.
"""
)

# ------------------------------------------------
# 1. DATA INPUT
# ------------------------------------------------
st.subheader("1. Upload item-level dataset")

uploaded_file = st.file_uploader(
    "Upload a CSV file with item-level data (e.g., PE_01, EE_02, BI_03, ...). "
    "Demographic columns without '_' will be ignored automatically.",
    type=["csv"],
)

if uploaded_file is None:
    st.info("Please upload a CSV file to compute diagnostics.")
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
# 2. AUTO-DETECT CONSTRUCTS FROM COLUMN NAMES
# ------------------------------------------------
st.subheader("2. Auto-detected constructs")

construct_map = {}

for col in df.columns:
    if "_" not in col:
        # likely demographics or non-indicator columns
        continue
    prefix = col.split("_")[0].strip()
    if not prefix:
        continue
    construct_map.setdefault(prefix, []).append(col)

if not construct_map:
    st.error(
        "No item columns detected with pattern 'CONSTRUCT_XX'. "
        "Please ensure your item columns are named like 'PE_01', 'EE_02', etc."
    )
    st.stop()

# sort indicators per construct
for k in construct_map:
    construct_map[k] = sorted(construct_map[k])

construct_names = sorted(construct_map.keys())

st.write("The following constructs and their indicators were detected:")
for cons in construct_names:
    st.markdown(f"- **{cons}**: {', '.join(construct_map[cons])}")


# Let user optionally deselect constructs
st.markdown("You may deselect constructs if needed:")
selected_constructs = st.multiselect(
    "Select constructs to include in diagnostics:",
    options=construct_names,
    default=construct_names,
)

if not selected_constructs:
    st.error("Please select at least one construct.")
    st.stop()

# Filter construct_map to selected only
construct_map = {k: v for k, v in construct_map.items() if k in selected_constructs}

# Build item-only dataframe from selected constructs
indicator_cols = [c for cols in construct_map.values() for c in cols]
items_df = df[indicator_cols].copy()


# ------------------------------------------------
# 3. COMPUTE DIAGNOSTICS
# ------------------------------------------------
st.subheader("3. Compute diagnostics")

if st.button("Compute reliability and validity metrics", type="primary"):
    with st.spinner("Computing alpha, CR, AVE, correlations, and HTMT..."):
        diag = compute_measurement_diagnostics(items_df, construct_map)

    # Alpha, CR, AVE tables
    st.markdown("### Reliability & Convergent Validity")

    metrics_df = pd.DataFrame(
        {
            "Cronbach Alpha": diag["alpha"],
            "Composite Reliability (CR)": diag["cr"],
            "AVE": diag["ave"],
        }
    ).T  # constructs as columns
    st.dataframe(metrics_df, use_container_width=True)

    st.info(
        "Typical guidelines (not strict rules): "
        "Alpha ≥ 0.70, CR ≥ 0.70, AVE ≥ 0.50. "
        "Interpret values in context and with theoretical justification."
    )

    # Construct correlations
    st.markdown("### Construct-level correlation matrix")
    st.dataframe(diag["construct_correlations"], use_container_width=True)

    # HTMT
    st.markdown("### HTMT matrix")
    st.dataframe(diag["htmt"], use_container_width=True)

    st.info(
        "HTMT values below ~0.85 (or 0.90) are often used as evidence of discriminant validity. "
        "Higher values may suggest overlap between constructs."
    )

else:
    st.caption("Click **Compute reliability and validity metrics** to run diagnostics.")
