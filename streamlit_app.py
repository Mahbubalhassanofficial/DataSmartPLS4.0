import streamlit as st
from app.Home import run as home
from app.Structural import run as structural
from app.Measurement import run as measurement
from app.Bias import run as bias
from app.Diagnostics import run as diagnostics

PAGE = st.sidebar.selectbox(
    "Navigation",
    ["Home", "Structural Model", "Measurement Model", "Bias Simulation", "Diagnostics"]
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
