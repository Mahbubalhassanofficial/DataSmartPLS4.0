import streamlit as st
import pandas as pd

from core.config import PathConfig, StructuralConfig
from app.branding import render_app_header, render_app_footer


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="DataSmartPLS4.0 – Structural Model",
    layout="wide",
)

# Branding header
render_app_header("Structural Model Configuration (PLS-SEM Style)")

st.markdown(
    """
Configure your **structural model** for synthetic PLS-SEM simulation:

- Unlimited number of paths (e.g., PE → BI, EE → BI)  
- Parallel, chain, or hierarchical models  
- Multiple endogenous constructs allowed  
- Optional R² targets for finer control  

When saved, this configuration will be used on the **Home** page to generate
latent variables consistent with your structural design.
"""
)

# ---------------------------------------------------------
# 1. LOAD CONSTRUCTS FROM HOME PAGE
# ---------------------------------------------------------
st.subheader("1. Available Constructs")

construct_names = []

if "construct_editor" in st.session_state:
    try:
        df_constructs = st.session_state["construct_editor"]
        # Sometimes data_editor returns a DataFrame directly,
        # sometimes a structure; this assumes DataFrame as used in Home.
        if isinstance(df_constructs, pd.DataFrame) and "name" in df_constructs.columns:
            construct_names = (
                df_constructs["name"]
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .unique()
                .tolist()
            )
    except Exception:
        construct_names = []

# If none detected, allow manual input
if construct_names:
    st.success(
        f"Detected {len(construct_names)} constructs from Home: "
        + ", ".join(construct_names)
    )
else:
    st.warning(
        "No constructs detected from the Home page. "
        "You can manually specify constructs below."
    )
    manual = st.text_input(
        "Enter constructs (comma-separated), e.g., PE, EE, SI, BI",
        value="",
    )
    if manual.strip():
        construct_names = [c.strip() for c in manual.split(",") if c.strip()]

if not construct_names:
    st.info("Define constructs on the Home page or manually above to continue.")
    render_app_footer()
    st.stop()


# ---------------------------------------------------------
# 2. STRUCTURAL PATHS TABLE
# ---------------------------------------------------------
st.subheader("2. Structural Paths (β Relations)")

st.markdown(
    """
Each row defines a PLS-SEM structural relation:  
**source → target** with coefficient **β**.
"""
)

# Initialize paths DF in session_state if missing
if "structural_paths_df" not in st.session_state:
    st.session_state["structural_paths_df"] = pd.DataFrame(
        {"source": [], "target": [], "beta": []}
    )

paths_df = st.session_state["structural_paths_df"]

# Editable table
edited_df = st.data_editor(
    paths_df,
    num_rows="dynamic",
    use_container_width=True,
    key="paths_editor",
    column_config={
        "source": st.column_config.SelectboxColumn(
            "Source", options=construct_names, required=True
        ),
        "target": st.column_config.SelectboxColumn(
            "Target", options=construct_names, required=True
        ),
        "beta": st.column_config.NumberColumn(
            "Beta coefficient", format="%.3f", step=0.05
        ),
    },
)

# Persist edited table
st.session_state["structural_paths_df"] = edited_df

st.markdown("---")

# ---------------------------------------------------------
# 2A. QUICK-ADD PATH HELPER
# ---------------------------------------------------------
st.markdown("#### Quick Add Structural Path")

col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1])

with col1:
    new_source = st.selectbox("Source", options=construct_names, key="new_src")

with col2:
    new_target = st.selectbox("Target", options=construct_names, key="new_tgt")

with col3:
    new_beta = st.number_input(
        "β coefficient",
        min_value=-3.0,
        max_value=3.0,
        value=0.30,
        step=0.05,
        key="new_beta",
    )

with col4:
    add_clicked = st.button("Add", type="secondary")

if add_clicked:
    if new_source == new_target:
        st.error("Source and target cannot be the same.")
    else:
        new_row = pd.DataFrame(
            [{"source": new_source, "target": new_target, "beta": float(new_beta)}]
        )
        # Append and drop duplicates to avoid identical duplicate paths
        st.session_state["structural_paths_df"] = (
            pd.concat(
                [st.session_state["structural_paths_df"], new_row],
                ignore_index=True,
            )
            .drop_duplicates(subset=["source", "target"], keep="last")
            .reset_index(drop=True)
        )
        st.success(f"Added: {new_source} → {new_target} (β = {new_beta:.2f})")


# ---------------------------------------------------------
# 3. R² TARGETS
# ---------------------------------------------------------
st.subheader("3. Optional R² Targets")

# Endogenous constructs = all unique targets
if "structural_paths_df" in st.session_state:
    df_paths = st.session_state["structural_paths_df"]
    if "target" in df_paths.columns:
        endogenous = sorted(set(df_paths["target"].dropna().tolist()))
    else:
        endogenous = []
else:
    endogenous = []

if endogenous:
    # Initialize or update R² targets dict in session_state
    if "r2_targets" not in st.session_state:
        st.session_state["r2_targets"] = {e: None for e in endogenous}
    else:
        # Keep existing values for previous constructs, add new ones if needed
        for e in endogenous:
            st.session_state["r2_targets"].setdefault(e, None)

    r2_cols = st.columns(len(endogenous))

    for col, cons in zip(r2_cols, endogenous):
        with col:
            current_val = st.session_state["r2_targets"].get(cons)
            new_val = st.number_input(
                f"R² for {cons}",
                min_value=0.0,
                max_value=0.95,
                value=float(current_val) if current_val else 0.0,
                step=0.01,
            )
            st.session_state["r2_targets"][cons] = new_val
else:
    st.info(
        "No endogenous constructs detected yet (no targets). "
        "Add at least one structural path."
    )


# ---------------------------------------------------------
# 4. SAVE STRUCTURAL MODEL
# ---------------------------------------------------------
st.subheader("4. Save Structural Configuration")

if st.button("Save structural configuration", type="primary"):

    # Convert table to list of PathConfig
    paths_cfg = []
    for _, row in st.session_state["structural_paths_df"].iterrows():
        if pd.isna(row["source"]) or pd.isna(row["target"]):
            continue

        # Safe β: if NaN, default to 0.30
        try:
            beta_val = float(row["beta"])
        except Exception:
            beta_val = 0.30

        paths_cfg.append(
            PathConfig(
                source=str(row["source"]).strip(),
                target=str(row["target"]).strip(),
                beta=beta_val,
            )
        )

    # Clean R² dictionary: keep only positive values
    r2_targets = {}
    if "r2_targets" in st.session_state:
        for k, v in st.session_state["r2_targets"].items():
            try:
                v = float(v)
                if v > 0:
                    r2_targets[str(k)] = v
            except Exception:
                continue

    # Store serializable version in session_state for Home page
    st.session_state["structural_config_raw"] = {
        "paths": [
            {"source": p.source, "target": p.target, "beta": p.beta}
            for p in paths_cfg
        ],
        "r2_targets": r2_targets,
    }

    # Also build a StructuralConfig object in case core modules want to use it directly
    st.session_state["structural_config"] = StructuralConfig(
        paths=paths_cfg,
        r2_targets=r2_targets,
    )

    st.success("Structural model saved. Home page will now use this configuration.")
    st.json(st.session_state["structural_config_raw"])

else:
    st.caption(
        "After defining paths and (optionally) R² values, "
        "click **Save structural configuration** to activate the model."
    )

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
render_app_footer()
