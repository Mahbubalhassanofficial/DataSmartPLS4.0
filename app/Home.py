import streamlit as st
import pandas as pd

from core.config import (
    ModelConfig,
    ConstructConfig,
    SampleConfig,
    DemographicConfig,
    BiasConfig,
)
from core.generator import generate_dataset


# ------------------------------------------------
# BASIC PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="DataSmartPLS4.0 – Synthetic Survey Data Generator",
    layout="wide",
)

st.title("DataSmartPLS4.0 – Synthetic Survey Data Generator (Foundation UI)")

st.markdown(
    """
This interface uses the **core latent-variable engine** of DataSmartPLS4.0 to generate
realistic Likert-scale survey data based on reflective constructs.

We will later add:
- response biases,
- structural models,
- diagnostics,
- multi-group simulation,
- and advanced export options.

For now, this page focuses on **measurement model data generation**.
"""
)

# ------------------------------------------------
# SIDEBAR: GLOBAL SAMPLE SETTINGS
# ------------------------------------------------
st.sidebar.header("Global Settings")

project_name = st.sidebar.text_input("Project name", value="Demo SmartPLS Study")
researcher_name = st.sidebar.text_input("Researcher name", value="Prof. Mahbub")

n_respondents = st.sidebar.number_input(
    "Number of respondents (N)", min_value=30, max_value=200000, value=500, step=10
)

likert_min = st.sidebar.number_input(
    "Likert minimum", min_value=1, max_value=3, value=1, step=1
)
likert_max = st.sidebar.number_input(
    "Likert maximum", min_value=3, max_value=10, value=5, step=1
)

random_seed = st.sidebar.number_input(
    "Random seed", min_value=0, max_value=999999, value=123, step=1
)

add_demographics = st.sidebar.checkbox("Include synthetic demographics", value=True)

if likert_max <= likert_min:
    st.sidebar.error("Likert maximum must be greater than minimum.")


# ------------------------------------------------
# MAIN: CONSTRUCT CONFIGURATION
# ------------------------------------------------
st.subheader("1. Define Measurement Constructs")

st.markdown(
    """
Each row below corresponds to **one latent construct**.

You can configure:
- number of items (indicators),
- latent mean and standard deviation,
- distribution shape,
- average loading and its range.

Later we will link these constructs with a structural model (paths, mediation, moderation).
"""
)

default_constructs = pd.DataFrame(
    [
        {
            "name": "PE",
            "n_items": 4,
            "latent_mean": 0.0,
            "latent_sd": 1.0,
            "distribution": "normal",
            "skew": 0.0,
            "kurtosis": 3.0,
            "target_loading_mean": 0.75,
            "target_loading_min": 0.60,
            "target_loading_max": 0.90,
        },
        {
            "name": "EE",
            "n_items": 4,
            "latent_mean": 0.1,
            "latent_sd": 1.0,
            "distribution": "normal",
            "skew": 0.0,
            "kurtosis": 3.0,
            "target_loading_mean": 0.72,
            "target_loading_min": 0.60,
            "target_loading_max": 0.90,
        },
        {
            "name": "BI",
            "n_items": 3,
            "latent_mean": 0.3,
            "latent_sd": 1.0,
            "distribution": "skewed",
            "skew": 0.8,
            "kurtosis": 3.0,
            "target_loading_mean": 0.80,
            "target_loading_min": 0.70,
            "target_loading_max": 0.95,
        },
    ]
)

construct_df = st.data_editor(
    default_constructs,
    num_rows="dynamic",
    use_container_width=True,
    key="construct_editor",
)

# enforce types
construct_df["name"] = construct_df["name"].astype(str).str.strip()
construct_df["n_items"] = pd.to_numeric(construct_df["n_items"], errors="coerce").fillna(0).astype(int)

for col in [
    "latent_mean",
    "latent_sd",
    "skew",
    "kurtosis",
    "target_loading_mean",
    "target_loading_min",
    "target_loading_max",
]:
    construct_df[col] = pd.to_numeric(construct_df[col], errors="coerce")

construct_df["distribution"] = construct_df["distribution"].astype(str)


# ------------------------------------------------
# GENERATE DATA
# ------------------------------------------------
st.subheader("2. Generate Synthetic Survey Data")

if st.button("Generate synthetic data", type="primary"):
    if likert_max <= likert_min:
        st.error("Fix Likert scale: maximum must be greater than minimum.")
    elif construct_df["n_items"].sum() <= 0:
        st.error("Please define at least one construct with n_items > 0.")
    else:
        with st.spinner("Generating dataset using latent-variable model..."):
            # Build construct configuration objects
            constructs = []
            for _, row in construct_df.iterrows():
                if not row["name"] or row["n_items"] <= 0:
                    continue

                constructs.append(
                    ConstructConfig(
                        name=row["name"],
                        n_items=int(row["n_items"]),
                        latent_mean=float(row["latent_mean"]),
                        latent_sd=float(row["latent_sd"]),
                        distribution=row["distribution"],
                        skew=float(row["skew"]),
                        kurtosis=float(row["kurtosis"]),
                        target_loading_mean=float(row["target_loading_mean"]),
                        target_loading_min=float(row["target_loading_min"]),
                        target_loading_max=float(row["target_loading_max"]),
                    )
                )

            sample_cfg = SampleConfig(
                n_respondents=int(n_respondents),
                likert_min=int(likert_min),
                likert_max=int(likert_max),
                random_seed=int(random_seed),
            )

            demo_cfg = DemographicConfig(add_demographics=add_demographics)
            bias_cfg = BiasConfig()  # not applied yet; will be used in later steps

            model_cfg = ModelConfig(
                project_name=project_name,
                researcher_name=researcher_name,
                constructs=constructs,
                sample=sample_cfg,
                demographics=demo_cfg,
                bias=bias_cfg,
            )

            full_df, items_df = generate_dataset(model_cfg)

        st.success(
            f"Generated dataset with shape: {full_df.shape[0]} rows × {full_df.shape[1]} columns."
        )

        st.markdown(f"**Project:** {project_name}  \n**Researcher:** {researcher_name}")

        st.markdown("### Preview (first 10 rows)")
        st.dataframe(full_df.head(10), use_container_width=True)

        st.markdown("### Descriptive statistics (numeric columns)")
        st.dataframe(full_df.describe(), use_container_width=True)

        csv_bytes = full_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download full dataset (CSV)",
            data=csv_bytes,
            file_name="DataSmartPLS4_synthetic_data.csv",
            mime="text/csv",
        )

        st.info(
            "This dataset is fully synthetic and intended for **methodological testing, teaching, and pipeline validation** "
            "(e.g., SmartPLS, SEM, fsQCA). Real empirical conclusions must always be based on real data."
        )
else:
    st.caption("Adjust constructs and global settings, then click **Generate synthetic data**.")


# ------------------------------------------------
# FOOTER / BRANDING
# ------------------------------------------------
st.markdown("---")
st.markdown(
    """
**DataSmartPLS4.0** · B’Deshi Emerging Research Lab  
Synthetic survey data generator for research design, education, and methodological simulation.
"""
)
