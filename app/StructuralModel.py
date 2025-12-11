import streamlit as st
import pandas as pd

from core.config import PathConfig, StructuralConfig
from app.branding import render_app_header, render_app_footer


# ============================================================
#  PAGE FUNCTION (required for navigation)
# ============================================================
def run():

    # ---------------- HEADER ----------------
    render_app_header("Structural Model Configuration (PLS-SEM Style)")

    st.markdown(
        """
        Configure your **structural model** for synthetic PLS-SEM simulation:

        - Unlimited causal paths (e.g., PE → BI, EE → BI)  
        - Parallel or chain models  
        - Multiple endogenous constructs  
        - Optional R² targets for realism  

        Once saved, this model will be consumed by the **Home** page when generating
        latent variables and final synthetic datasets.
        """
    )

    # ============================================================
    # 1. LOAD CONSTRUCTS FROM HOME PAGE
    # ============================================================
    st.subheader("1. Available Constructs")

    construct_names = []

    # Retrieve constructs created from Home page
    if "construct_editor" in st.session_state:
        df_constructs = st.session_state["construct_editor"]

        if isinstance(df_constructs, pd.DataFrame) and "name" in df_constructs.columns:
            try:
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

    # Manual fallback
    if construct_names:
        st.success(f"Detected constructs from Home: {', '.join(construct_names)}")
    else:
        st.warning("No constructs detected. You may manually define construct names below.")

        manual = st.text_input(
            "Enter constructs (comma-separated), e.g., PE, EE, SI, BI",
            value=""
        )

        if manual.strip():
            construct_names = [c.strip() for c in manual.split(",") if c.strip()]

    # If still empty → stop
    if not construct_names:
        st.info("Define constructs on Home page or manually above to proceed.")
        render_app_footer()
        return

    # ============================================================
    # 2. STRUCTURAL PATHS
    # ============================================================
    st.subheader("2. Structural Paths (β Relations)")

    st.markdown(
        """
        Each row defines a structural relation:

        **source → target  (β coefficient)**  
        """
    )

    # Initialize table if missing
    if "structural_paths_df" not in st.session_state:
        st.session_state["structural_paths_df"] = pd.DataFrame(
            {"source": [], "target": [], "beta": []}
        )

    paths_df = st.session_state["structural_paths_df"]

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

    st.session_state["structural_paths_df"] = edited_df

    st.markdown("---")

    # ============================================================
    # QUICK ADD PATH
    # ============================================================
    st.markdown("#### Quick Add Structural Path")

    col1, col2, col3, col4 = st.columns([2, 2, 1.5, 1])

    with col1:
        new_source = st.selectbox("Source", construct_names, key="new_src")

    with col2:
        new_target = st.selectbox("Target", construct_names, key="new_tgt")

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

            st.session_state["structural_paths_df"] = (
                pd.concat([st.session_state["structural_paths_df"], new_row], ignore_index=True)
                .drop_duplicates(subset=["source", "target"], keep="last")
                .reset_index(drop=True)
            )

            st.success(f"Added structural path: {new_source} → {new_target} (β = {new_beta:.2f})")

    # ============================================================
    # 3. R² TARGETS
    # ============================================================
    st.subheader("3. Optional R² Targets")

    df_paths = st.session_state["structural_paths_df"]

    if not df_paths.empty:
        endogenous = sorted(set(df_paths["target"].dropna()))
    else:
        endogenous = []

    if endogenous:
        # Initialize if missing
        if "r2_targets" not in st.session_state:
            st.session_state["r2_targets"] = {e: None for e in endogenous}

        # Add new endogenous entries
        for e in endogenous:
            st.session_state["r2_targets"].setdefault(e, None)

        cols = st.columns(len(endogenous))

        for col, cons in zip(cols, endogenous):
            with col:
                current = st.session_state["r2_targets"].get(cons)
                val = st.number_input(
                    f"R²: {cons}",
                    min_value=0.0,
                    max_value=0.95,
                    value=float(current) if current else 0.0,
                    step=0.01
                )
                st.session_state["r2_targets"][cons] = val
    else:
        st.info("No endogenous constructs detected. Add structural paths first.")

    # ============================================================
    # 4. SAVE STRUCTURAL CONFIGURATION
    # ============================================================
    st.subheader("4. Save Structural Configuration")

    if st.button("Save structural configuration", type="primary"):

        paths_cfg = []

        for _, row in st.session_state["structural_paths_df"].iterrows():
            if pd.isna(row["source"]) or pd.isna(row["target"]):
                continue

            beta_val = float(row["beta"]) if pd.notna(row["beta"]) else 0.30

            paths_cfg.append(
                PathConfig(
                    source=str(row["source"]).strip(),
                    target=str(row["target"]).strip(),
                    beta=beta_val,
                )
            )

        # R² dictionary
        r2_targets = {}
        for key, val in st.session_state.get("r2_targets", {}).items():
            try:
                val = float(val)
                if val > 0:
                    r2_targets[str(key)] = val
            except:
                continue

        # Save a JSON-serializable version for Home.py
        st.session_state["structural_config_raw"] = {
            "paths": [{"source": p.source, "target": p.target, "beta": p.beta} for p in paths_cfg],
            "r2_targets": r2_targets,
        }

        # Save compiled config
        st.session_state["structural_config"] = StructuralConfig(
            paths=paths_cfg,
            r2_targets=r2_targets,
        )

        st.success("Structural model saved successfully.")
        st.json(st.session_state["structural_config_raw"])

    else:
        st.caption("Click **Save** to apply current settings to the Home page.")

    # Footer
    render_app_footer()
