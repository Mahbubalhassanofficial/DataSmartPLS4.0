import streamlit as st

from app.Home import run as home
from app.StructuralModel import run as structural
from app.MeasurementModel import run as measurement
from app.ResponseBias import run as bias
from app.Diagnostics import run as diagnostics
from app.ExportCenter import run as export_center  # optional

st.set_page_config(page_title="DataSmartPLS4.0", layout="wide")

PAGE = st.sidebar.selectbox(
    "Navigation",
    [
        "Home",
        "Structural Model",
        "Measurement Model",
        "Bias Simulation",
        "Diagnostics",
        "Export Center"
    ]
)

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
