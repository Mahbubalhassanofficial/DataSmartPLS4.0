import streamlit as st
import pandas as pd

from core.config import PathConfig, StructuralConfig


st.set_page_config(
    page_title="DataSmartPLS4.0 – Structural Model",
    layout="wide",
)

st.title("Structural Model Configuration (PLS-SEM Style)")

st.markdown(
    """
Configure the **structural model** for your simulation:

- Unlimited number of paths (e.g., PE → BI, EE → BI, SI → BI, etc.).
- Multiple endogenous constructs.
- Chains (PE → AT → BI → USE) and parallel predictors.
- Optional R² targets for endogenous constructs.

This configuration will later be used when generating synthetic data
so that **latent variables follow your structural model**.
"""
)

# ---------------------------------------------------------
# 1. Get construct names (from session or manual)
# ---------------------------------------------------------
st.subheader("1. Available constructs")

construct_names = []

# Try to read from the construct editor on Home.py
if "construct_editor" in st.session_state:
    try:
        cons_df = st.session_state["construct_editor"]
        if isinstance(cons_df, pd.DataFrame) and "name" in cons_df.columns:
            construct_names = (
                cons_df["name"]
                .astype(str)
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .unique()
                .tolist()
            )
    except Exception:
        construct_names = []

if construct_names:
    st.success(
        f"Detected {len(construct_names)} constructs from the Home page: "
        + ", ".join(construct_names)
    )
else:
    st.warning(
        "No constructs detected from the Home page. You can still manually enter construct names below."
    )
    manual = st.text_input(
        "Enter construct names (comma-separated), e.g., PE, EE, SI, BI, USE",
        value="",
    )
    if manual.strip():
        construct_names = [c.strip() for c in manual.split(",") if c.strip()]

if not construct_names:
    st.stop()

# ---------------------------------------------------------
# 2. Structural paths editing (table + helper controls)
# ---------------------------------------------------------
st.subheader("2. Structural paths (β relations)")

# Initialize session state container for structural paths
if "structural_paths_df" not in st.session_state:
    # Start with an empty DataFrame
    st.session_state["structural_paths_df"] = pd.DataFrame(
        columns=["source", "target", "beta"]
    )

paths_df = st.session_state["structural_paths_df"]

st.markdown(
    """
Each row is a path of the form:  
`source → target` with coefficient `beta`.

You can edit the table directly, or use the helper controls below to add new paths.
"""
)

# --- Table editor for existing paths ---
edited_paths_df = st.data_editor(
    paths_df,
    num_rows="dynamic",
    use_container_width=True,
    key="paths_editor",
    column_config={
        "source": st.column_config.SelectboxColumn(
            "Source construct",
            options=construct_names,
            required=True,
        ),
        "target": st.column_config.SelectboxColumn(
            "Target construct",
            options=construct_names,
            required=True,
        ),
        "beta": st.column_config.NumberColumn(
            "Beta (path coefficient)",
            format="%.3f",
            step=0.05,
        ),
    },
)

# Update session state with edited table
st.session_state["structural_paths_df"] = edited_paths_df

st.markdown("---")

# --- Helper controls to add a single path quickly ---
st.markdown("#### Quick add structural path")

col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1])

with col1:
    new_source = st.selectbox(
        "Source",
        options=construct_names,
        key="new_path_source",
    )
with col2:
    new_target = st.selectbox(
        "Target",
        options=construct_names,
        key="new_path_target",
    )
with col3:
    new_beta = st.number_input(
        "β coefficient",
        min_value=-3.0,
        max_value=3.0,
        value=0.30,
        step=0.05,
        key="new_path_beta",
    )
with col4:
    add_clicked = st.button("Add path", type="secondary")

if add_clicked:
    if new_source == new_target:
        st.error("Source and target must be different.")
    else:
        new_row = pd.DataFrame(
            [{"source": new_source, "target": new_target, "beta": float(new_beta)}]
        )
        st.session_state["structural_paths_df"] = pd.concat(
            [st.session_state["structural_paths_df"], new_row],
            ignore_index=True,
        )
        st.success(f"Added path: {new_source} → {new_target} (β = {new_beta:.2f})")


# ---------------------------------------------------------
# 3. R² targets for endogenous constructs
# ---------------------------------------------------------
st.subheader("3. Optional R² targets")

st.markdown(
    """
You can (optionally) specify **target R² values** for each endogenous construct.
If left blank, the structural engine will derive an approximate R² from path coefficients.

Typical R² guidelines:
- 0.19 (weak), 0.33 (moderate), 0.67 (substantial) – *Cohen / PLS convention*.
"""
)

# Determine which constructs are endogenous (appear as target)
endogenous = sorted(
    set(st.session_state["structural_paths_df"]["target"].dropna().unique().tolist())
)

if endogenous:
    # Initialize or retrieve R² dict in session state
    if "r2_targets" not in st.session_state:
        st.session_state["r2_targets"] = {e: None for e in endogenous}
    else:
        # Ensure all endogenous constructs exist in dict
        for e in endogenous:
            st.session_state["r2_targets"].setdefault(e, None)

    r2_cols = st.columns(len(endogenous))
    for col, cons in zip(r2_cols, endogenous):
        with col:
            current_val = st.session_state["r2_targets"].get(cons, None)
            r2_val = st.number_input(
                f"R² for {cons}",
                min_value=0.0,
                max_value=0.95,
                value=float(current_val) if current_val is not None else 0.0,
                step=0.01,
            )
            st.session_state["r2_targets"][cons] = r2_val
else:
    st.info("No endogenous constructs detected yet (no targets). Add paths above first.")


# ---------------------------------------------------------
# 4. Save structural configuration to session_state
# ---------------------------------------------------------
st.subheader("4. Save structural model for generation")

if st.button("Save structural configuration", type="primary"):
    # Build PathConfig list and StructuralConfig
    paths_cfg = []
    for _, row in st.session_state["structural_paths_df"].dropna(subset=["source", "target"]).iterrows():
        try:
            beta_val = float(row["beta"])
        except Exception:
            beta_val = 0.0
        paths_cfg.append(
            PathConfig(
                source=str(row["source"]),
                target=str(row["target"]),
                beta=beta_val,
            )
        )

    r2_targets = {
        k: float(v)
        for k, v in st.session_state.get("r2_targets", {}).items()
        if v is not None and v > 0
    }

    structural_cfg = StructuralConfig(
        paths=paths_cfg,
        r2_targets=r2_targets,
    )

    # Store a serializable version in session_state for Home.py to use
    st.session_state["structural_config_raw"] = {
        "paths": [
            {"source": p.source, "target": p.target, "beta": p.beta}
            for p in paths_cfg
        ],
        "r2_targets": r2_targets,
    }

    st.success(
        "Structural configuration saved to session. "
        "When generating data on the Home page, the model will use this structural setup."
    )

    st.json(st.session_state["structural_config_raw"])
else:
    st.caption(
        "After editing paths and R² values, click **Save structural configuration** so it can be used during data generation."
    )
