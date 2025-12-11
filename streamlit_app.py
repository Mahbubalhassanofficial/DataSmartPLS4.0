import streamlit as st

# ============================================================
#  GLOBAL APP CONFIG
# ============================================================
st.set_page_config(
    page_title="DataSmartPLS4.0 – Synthetic PLS-SEM Studio",
    layout="wide",
)

# ============================================================
#  SAFE SESSION STATE INITIALIZATION
# ============================================================
# Streamlit Cloud sometimes resets session_state on reload.
# These lines ensure your structural model is always persistent.
if "structural_config_raw" not in st.session_state:
    st.session_state["structural_config_raw"] = {"paths": [], "r2_targets": {}}

if "structural_config" not in st.session_state:
    st.session_state["structural_config"] = None

# Reserve dataset for ExportCenter
if "last_full_df" not in st.session_state:
    st.session_state["last_full_df"] = None
if "last_items_df" not in st.session_state:
    st.session_state["last_items_df"] = None
if "last_model_cfg" not in st.session_state:
    st.session_state["last_model_cfg"] = None


# ============================================================
#  IMPORT PAGE MODULES
# ============================================================
from app.Home import run as home
from app.StructuralModel import run as structural
from app.MeasurementModel import run as measurement
from app.ResponseBias import run as bias
from app.Diagnostics import run as diagnostics
from app.ExportCenter import run as export_center


# ============================================================
#  SIDEBAR NAVIGATION
# ============================================================
st.sidebar.markdown(
    """
    <div style="font-size:1.2rem; font-weight:700; color:#7b2cbf;">
        DataSmartPLS4.0
    </div>
    <div style="font-size:0.85rem; color:#666; margin-bottom:12px;">
        Synthetic SEM · SmartPLS · fsQCA Data Studio
    </div>
    """,
    unsafe_allow_html=True,
)

PAGE = st.sidebar.selectbox(
    "Navigation",
    [
        "Home",
        "Structural Model",
        "Measurement Model",
        "Bias Simulation",
        "Diagnostics",
        "Export Center",
    ]
)

# ============================================================
#  PAGE ROUTER
# ============================================================
if PAGE == "Home":
    home()

elif PAGE == "Structural Model":
    structural()

elif PAGE == "Measurement Model":
    measurement()

elif PAGE == "Bias Simulation":
    bias()

elif PAGE == "Diagnostics":
    diagnostics()

elif PAGE == "Export Center":
    export_center()
