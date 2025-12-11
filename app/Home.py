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


# ------------------------------------------------
# BASIC PAGE CONFIG
# ------------------------------------------------
st.set_page_config(
    page_title="DataSmartPLS4.0 – Synthetic Survey Data Generator",
    layout="wide",
)

st.title("DataSmartPLS4.0 – Synthetic Survey Data Generator (Structural + Measurement)")


st.markdown(
    """
This interface now supports **full PLS-SEM simulation**, including:

- Reflective measurement model  
- Structural model (unlimited relations, endogenous constructs, R² targets)  
- Realistic Likert-scale indicators  
- Optional demographics  
- Latent-variable generation that respects your structural paths  

Use **Structural Model** page first if you want structural relations.
Then come here to generate the full dataset.
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
Each row defines **one reflective latent construct**.

Later, these constructs may serve as predictors or outcomes
in the **structural model** configured in the Structural Model page.
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
# LOAD STRUCTURAL MODEL FROM SESSION (if available)
# ------------------------------------------------
st.subheader("2. Structural Model Status")

structural_cfg = StructuralConfig(paths=[], r2_targets={})

if "structural_config_raw" in st.session_state:
    raw = st.session_state["structural_config_raw"]

    # Rebuild path configs
    paths = []
    for p in raw.get("paths", []):
        try:
            paths.append(
                PathConfig(
                    source=str(p["source"]),
                    target=str(p["target"]),
                    beta=float(p["beta"]),
                )
            )
        except Exception:
            pass

    r2_dict = {
        k: float(v)
        for k, v in raw.get("r2_targets", {}).items()
        if v is not None and v > 0
    }

    structural_cfg = StructuralConfig(paths=paths, r2_targets=r2_dict)

    st.success(
        f"Structural model detected: {len(paths)} paths · "
        f"R² specified for {len(r2_dict)} constructs."
    )
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
        st.error("Please define at least one construct with n_items > 0.")
    else:
        with st.spinner("Generating dataset using full structural + measurement engine..."):

            # Build construct configuration list
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

            # sample config
            sample_cfg = SampleConfig(
                n_respondents=int(n_respondents),
                likert_min=int(likert_min),
                likert_max=int(likert_max),
                random_seed=int(random_seed),
            )

            demo_cfg = DemographicConfig(add_demographics=add_demographics)
            bias_cfg = BiasConfig()  # will be used in later phases

            # full model config including structural model
            model_cfg = ModelConfig(
                project_name=project_name,
                researcher_name=researcher_name,
                constructs=constructs,
                sample=sample_cfg,
                demographics=demo_cfg,
                bias=bias_cfg,
                structural=structural_cfg,
            )

            # generate!
            full_df, items_df = generate_dataset(model_cfg)

        st.success(
            f"Generated dataset: {full_df.shape[0]} rows × {full_df.shape[1]} columns."
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
            "This dataset is fully synthetic and intended for **methodological research, teaching, and simulation** "
            "(e.g., SmartPLS, SEM, fsQCA)."
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
Advanced synthetic survey generator for research design, teaching, and simulation.
"""
)
