import streamlit as st

# ============================================================
#  GLOBAL APP CONFIG (WITH FAVICON + THEME OVERRIDES)
# ============================================================
st.set_page_config(
    page_title="DataSmartPLS4.0 – Synthetic PLS-SEM Studio",
    page_icon="📊",        # Favicon (emoji-based, works everywhere)
    layout="wide",
)

# ---- GLOBAL THEME OVERRIDE (BRANDING CONSISTENCY) ----
st.markdown("""
    <style>
        /* PRIMARY BRAND COLORS */
        :root {
            --primary-color: #7b2cbf;
            --primaryColor: #7b2cbf !important;
            --text-color: #444444;
        }

        /* Improve sidebar text visibility */
        section[data-testid="stSidebar"] .stMarkdown, 
        section[data-testid="stSidebar"] label {
            color: #333333 !important;
        }

        /* Remove Streamlit top padding for cleaner layout */
        .block-container {
            padding-top: 1.2rem;
        }
    </style>
""", unsafe_allow_html=True)


# ============================================================
#  IMPORT PAGE MODULES (each must have run())
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
    <div style="font-size:1.4rem; font-weight:800; color:#7b2cbf;">
        DataSmartPLS <span style="font-size:1.1rem;">4.0</span>
    </div>
    <div style="font-size:0.85rem; color:#666; margin-top:-6px; margin-bottom:14px;">
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
