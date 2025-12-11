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


# ================================================================
# SIDEBAR: GLOBAL SETTINGS
# ================================================================
with st.sidebar:
    st.header("Global Settings")

    project_name = st.text_input("Project name", value="Demo SmartPLS Study")
    researcher_name = st.text_input("Researcher name", value="Prof. Mahbub")

    n_respondents = st.number_input(
        "Number of respondents (N)",
        min_value=30,
        max_value=200_000,
        value=500,
        step=10,
    )

    likert_min = st.number_input(
        "Likert minimum", min_value=1, max_value=3, value=1, step=1
    )
    likert_max = st.number_input(
        "Likert maximum", min_value=3, max_value=10, value=5, step=1
    )

    random_seed = st.number_input(
        "Random seed", min_value=0, max_value=999_999, value=123, step=1
    )

    add_demographics = st.checkbox(
        "Include synthetic demographics", value=True
    )

    if likert_max <= likert_min:
        st.error("Likert maximum must be greater than minimum.")


# ================================================================
# 1. CONSTRUCT CONFIGURATION
# ================================================================
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

# ---- Clean & enforce types -------------------------------------
# Strip names and drop fully empty rows
construct_df["name"] = (
    construct_df["name"]
    .astype(str)
    .str.strip()
)

# numeric columns
numeric_cols_int = ["n_items"]
numeric_cols_float = [
    "latent_mean",
    "latent_sd",
    "skew",
    "kurtosis",
    "target_loading_mean",
    "target_loading_min",
    "target_loading_max",
]

for col in numeric_cols_int:
    construct_df[col] = pd.to_numeric(
        construct_df[col], errors="coerce"
    ).fillna(0).astype(int)

for col in numeric_cols_float:
    construct_df[col] = pd.to_numeric(
        construct_df[col], errors="coerce"
    )

construct_df["distribution"] = (
    construct_df["distribution"].astype(str).str.lower().replace({"": "normal"})
)

# Drop constructs with no name or no items
construct_df = construct_df[
    (construct_df["name"] != "") & (construct_df["n_items"] > 0)
].reset_index(drop=True)


# ================================================================
# 2. STRUCTURAL MODEL STATUS
# ================================================================
st.subheader("2. Structural Model Status")

structural_cfg = StructuralConfig(paths=[], r2_targets={})

if "structural_config_raw" in st.session_state:
    raw = st.session_state["structural_config_raw"]

    # rebuild path configs safely
    paths = []
    for p in raw.get("paths", []):
        try:
            src = str(p.get("source", "")).strip()
            tgt = str(p.get("target", "")).strip()
            beta_val = float(p.get("beta", 0.0))
            if src and tgt:
                paths.append(PathConfig(source=src, target=tgt, beta=beta_val))
        except Exception:
            # silently skip problematic rows
            continue

    r2_dict = {}
    for k, v in raw.get("r2_targets", {}).items():
        try:
            val = float(v)
            if val > 0:
                r2_dict[str(k)] = val
        except Exception:
            continue

    structural_cfg = StructuralConfig(paths=paths, r2_targets=r2_dict)

    st.success(
        f"Structural model detected: {len(paths)} paths · "
        f"R² for {len(r2_dict)} constructs."
    )
    st.json(raw)
else:
    st.info(
        "No structural model found. "
        "Data will be generated without structural relations."
    )


# ================================================================
# 3. GENERATE DATA
# ================================================================
st.subheader("3. Generate Synthetic Survey Data")

generate_clicked = st.button("Generate synthetic data", type="primary")

if generate_clicked:

    # Basic checks
    if likert_max <= likert_min:
        st.error("Fix Likert scale: maximum must be greater than minimum.")

    elif construct_df.empty or construct_df["n_items"].sum() <= 0:
        st.error("Define at least one construct with at least one item.")

    else:
        with st.spinner(
            "Generating dataset using structural + measurement engine..."
        ):
            # Build construct list for ModelConfig
            constructs = []
            for _, row in construct_df.iterrows():
                # Safe defaults for any missing numeric fields
                latent_mean = float(row["latent_mean"]) if pd.notna(row["latent_mean"]) else 0.0
                latent_sd = float(row["latent_sd"]) if pd.notna(row["latent_sd"]) else 1.0
                skew = float(row["skew"]) if pd.notna(row["skew"]) else 0.0
                kurt = float(row["kurtosis"]) if pd.notna(row["kurtosis"]) else 3.0
                t_mean = float(row["target_loading_mean"]) if pd.notna(row["target_loading_mean"]) else 0.75
                t_min = float(row["target_loading_min"]) if pd.notna(row["target_loading_min"]) else 0.60
                t_max = float(row["target_loading_max"]) if pd.notna(row["target_loading_max"]) else 0.90

                constructs.append(
                    ConstructConfig(
                        name=row["name"],
                        n_items=int(row["n_items"]),
                        latent_mean=latent_mean,
                        latent_sd=latent_sd,
                        distribution=row["distribution"],
                        skew=skew,
                        kurtosis=kurt,
                        target_loading_mean=t_mean,
                        target_loading_min=t_min,
                        target_loading_max=t_max,
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

            # Core engine
            full_df, items_df = generate_dataset(model_cfg)

        # Store in session state for other pages (e.g., ExportCenter)
        st.session_state["last_full_df"] = full_df
        st.session_state["last_items_df"] = items_df
        st.session_state["last_model_cfg"] = model_cfg

        st.success(
            f"Generated dataset: {full_df.shape[0]} rows × {full_df.shape[1]} columns."
        )

        st.markdown(
            f"**Project:** {project_name}  \n"
            f"**Researcher:** {researcher_name}"
        )

        st.markdown("### Preview (first 10 rows)")
        st.dataframe(full_df.head(10), use_container_width=True)

        st.markdown("### Descriptive statistics")
        st.dataframe(full_df.describe(), use_container_width=True)

else:
    st.caption(
        "Adjust constructs and settings, then click **Generate synthetic data**."
    )


# ------------------------------------------------
# FOOTER
# ------------------------------------------------
render_app_footer()
