import streamlit as st
import pandas as pd

from core.config import (
    ModelConfig,
    ConstructConfig,
    SampleConfig,
    DemographicConfig,
    BiasConfig,
    StructuralConfig,
    PathConfig,
)
from core.generator import generate_dataset
from app.branding import render_app_header, render_app_footer


# ------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="DataSmartPLS4.0 – Synthetic Survey Data Generator",
    layout="wide",
)

# Unified branding header
render_app_header("Home · Data Generator")

st.markdown(
    """
This interface supports **full PLS-SEM synthetic data generation**, including:

- Reflective measurement model  
- Structural model (unlimited relations, endogenous constructs, R² targets)  
- Realistic Likert-scale indicators  
- Optional demographics  

Tip: configure your **Structural Model** page if you want relations, then generate data here.
"""
)


# ------------------------------------------------
# SIDEBAR SETTINGS
# ------------------------------------------------
st.sidebar.header("Global Settings")

project_name = st.sidebar.text_input("Project name", value="Demo SmartPLS Study")
researcher_name = st.sidebar.text_input("Researcher name", value="Prof. Mahbub")

n_respondents = st.sidebar.number_input(
    "Number of respondents (N)", min_value=30, max_value=200000, value=500, step=10
)

likert_min = st.sidebar.number_input("Likert minimum", min_value=1, max_value=3, value=1)
likert_max = st.sidebar.number_input("Likert maximum", min_value=3, max_value=10, value=5)

random_seed = st.sidebar.number_input("Random seed", min_value=0, max_value=999999, value=123)

add_demographics = st.sidebar.checkbox("Include synthetic demographics", value=True)

if likert_max <= likert_min:
    st.sidebar.error("Likert maximum must be greater than minimum.")


# ------------------------------------------------
# CONSTRUCT CONFIGURATION
# ------------------------------------------------
st.subheader("1. Define Measurement Constructs")

st.markdown("Each row defines **one reflective latent construct**.")

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
construct_df["name"] = construct_df["name"].astype(str).str.strip()   # FIXED
construct_df["n_items"] = pd.to_numeric(construct_df["n_items"], errors="coerce").fillna(0).astype(int)

for col in [
    "latent_mean", "latent_sd", "skew", "kurtosis",
    "target_loading_mean", "target_loading_min", "target_loading_max",
]:
    construct_df[col] = pd.to_numeric(construct_df[col], errors="coerce")

construct_df["distribution"] = construct_df["distribution"].astype(str)


# ------------------------------------------------
# LOAD STRUCTURAL MODEL (if exists)
# ------------------------------------------------
st.subheader("2. Structural Model Status")

structural_cfg = StructuralConfig(paths=[], r2_targets={})

if "structural_config_raw" in st.session_state:
    raw = st.session_state["structural_config_raw"]

    # rebuild path configs
    paths = []
    for p in raw.get("paths", []):
        try:
            paths.append(PathConfig(source=str(p["source"]), target=str(p["target"]), beta=float(p["beta"])))
        except:
            pass

    r2_dict = {k: float(v) for k, v in raw.get("r2_targets", {}).items() if v is not None and v > 0}

    structural_cfg = StructuralConfig(paths=paths, r2_targets=r2_dict)

    st.success(f"Structural model detected: {len(paths)} paths · R² for {len(r2_dict)} constructs.")
    st.json(raw)
else:
    st.info("No structural model found. Data will be generated without structural relations.")


# ------------------------------------------------
# GENERATE DATA
# ------------------------------------------------
st.subheader("3. Generate Synthetic Survey Data")

if st.button("Generate synthetic data", type="primary"):

    if likert_max <= likert_min:
        st.error("Fix Likert scale: maximum must be greater than minimum.")

    elif construct_df["n_items"].sum() <= 0:
        st.error("Define at least one construct with items.")

    else:
        with st.spinner("Generating dataset using structural + measurement engine..."):

            # Build construct list
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
            bias_cfg = BiasConfig()

            model_cfg = ModelConfig(
                project_name=project_name,
                researcher_name=researcher_name,
                constructs=constructs,
                sample=sample_cfg,
                demographics=demo_cfg,
                bias=bias_cfg,
                structural=structural_cfg,
            )

            full_df, items_df = generate_dataset(model_cfg)

        # Save for ExportCenter
        st.session_state["last_full_df"] = full_df
        st.session_state["last_items_df"] = items_df
        st.session_state["last_model_cfg"] = model_cfg

        st.success(f"Generated dataset: {full_df.shape[0]} rows × {full_df.shape[1]} columns.")

        st.markdown(f"**Project:** {project_name}  \n**Researcher:** {researcher_name}")

        st.markdown("### Preview (first 10 rows)")
        st.dataframe(full_df.head(10), use_container_width=True)

        st.markdown("### Descriptive statistics")
        st.dataframe(full_df.describe(), use_container_width=True)

else:
    st.caption("Adjust constructs and settings, then click **Generate synthetic data**.")


# ------------------------------------------------
# FOOTER
# ------------------------------------------------
render_app_footer()
