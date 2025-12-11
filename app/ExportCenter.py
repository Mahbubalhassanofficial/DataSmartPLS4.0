import streamlit as st
import pandas as pd

from utils.export import (
    generate_codebook,
    export_csv,
    export_excel_full,
    export_excel_smartpls,
    export_spss,
    export_stata,
    export_rds,
    export_metadata_json,
    export_codebook_pdf,
    export_codebook_html,
    pdf_available,
)

from app.branding import render_app_header, render_app_footer


# --------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------
st.set_page_config(
    page_title="DataSmartPLS4.0 – Export & Codebook Center",
    layout="wide",
)

# Header with branding
render_app_header("Export & Codebook Center")


st.markdown(
    """
Use this center to export your synthetic dataset and metadata in multiple
research-ready formats:

### Available Outputs
- **SmartPLS-ready Excel (items only)**
- **Full dataset CSV / Excel**
- **SPSS (.sav), Stata (.dta), R (.rds)**
- **Codebook (CSV, PDF, HTML)**
- **Full metadata JSON**

⚠️ Data must first be generated from the **Home page**.
"""
)


# --------------------------------------------------------
# 1. Retrieve generated data from session_state
# --------------------------------------------------------
full_df = st.session_state.get("last_full_df")
items_df = st.session_state.get("last_items_df")
model_cfg = st.session_state.get("last_model_cfg")

if full_df is None or items_df is None or model_cfg is None:
    st.error("No dataset available. Please generate data on the **Home** page first.")
    render_app_footer()
    st.stop()

# --------------------------------------------------------
# 2. Dataset Summary & Preview
# --------------------------------------------------------
st.subheader("1. Dataset Summary")

st.write(
    f"""
- **Rows (respondents):** {full_df.shape[0]}  
- **Columns (full dataset):** {full_df.shape[1]}  
- **Indicators (items_df):** {items_df.shape[1]}  
"""
)

st.markdown("### Preview (first 10 rows)")
st.dataframe(full_df.head(10), use_container_width=True)


# --------------------------------------------------------
# 3. Generate Codebook
# --------------------------------------------------------
st.subheader("2. Codebook & Model Metadata")

codebook_df = generate_codebook(model_cfg, items_df, full_df)

st.markdown("### Codebook Preview (first 20 rows)")
st.dataframe(codebook_df.head(20), use_container_width=True)


# --------------------------------------------------------
# Prepare export bytes
# --------------------------------------------------------
csv_bytes = export_csv(full_df)
excel_full_bytes = export_excel_full(full_df)
excel_spls_bytes = export_excel_smartpls(items_df)
codebook_csv_bytes = codebook_df.to_csv(index=False).encode("utf-8")
codebook_html_bytes = export_codebook_html(codebook_df)
metadata_bytes = export_metadata_json(model_cfg, codebook_df)

# PDF (optional)
pdf_ok = False
if pdf_available:
    try:
        pdf_bytes = export_codebook_pdf(codebook_df)
        pdf_ok = True
    except Exception as e:
        st.warning(f"PDF export failed: {e}")
else:
    pdf_ok = False

# SPSS / Stata / R optional formats
try:
    spss_bytes = export_spss(full_df)
    spss_ok = True
except:
    spss_ok = False

try:
    stata_bytes = export_stata(full_df)
    stata_ok = True
except:
    stata_ok = False

try:
    rds_bytes = export_rds(full_df)
    rds_ok = True
except:
    rds_ok = False


# --------------------------------------------------------
# 4. Download Buttons
# --------------------------------------------------------
st.subheader("3. Download Files")

colA, colB, colC = st.columns(3)


# -------------------------------
# Column A – General Formats
# -------------------------------
with colA:
    st.markdown("### General Formats")

    st.download_button(
        "📄 CSV (Full Dataset)",
        data=csv_bytes,
        file_name="DataSmartPLS4_full_dataset.csv",
        mime="text/csv",
    )

    st.download_button(
        "📊 Excel (Full Dataset)",
        data=excel_full_bytes,
        file_name="DataSmartPLS4_full_dataset.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# -------------------------------
# Column B – SmartPLS + Codebooks
# -------------------------------
with colB:
    st.markdown("### SmartPLS + Codebooks")

    st.download_button(
        "📊 SmartPLS Excel (Items Only)",
        data=excel_spls_bytes,
        file_name="DataSmartPLS4_items_only_SmartPLS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.download_button(
        "📘 Codebook (CSV)",
        data=codebook_csv_bytes,
        file_name="DataSmartPLS4_codebook.csv",
        mime="text/csv",
    )

    st.download_button(
        "🌐 Codebook (HTML)",
        data=codebook_html_bytes,
        file_name="DataSmartPLS4_codebook.html",
        mime="text/html",
    )

    if pdf_ok:
        st.download_button(
            "📕 Codebook (PDF)",
            data=pdf_bytes,
            file_name="DataSmartPLS4_codebook.pdf",
            mime="application/pdf",
        )
    else:
        st.caption("PDF unavailable – install **reportlab** to enable this feature.")

    st.download_button(
        "🧩 Metadata JSON",
        data=metadata_bytes,
        file_name="DataSmartPLS4_metadata.json",
        mime="application/json",
    )


# -------------------------------
# Column C – SPSS / Stata / R
# -------------------------------
with colC:
    st.markdown("### Statistical Software")

    if spss_ok:
        st.download_button(
            "📁 SPSS (.sav)",
            data=spss_bytes,
            file_name="DataSmartPLS4.sav",
            mime="application/octet-stream",
        )
    else:
        st.caption("SPSS export unavailable (pyreadstat not installed).")

    if stata_ok:
        st.download_button(
            "📁 Stata (.dta)",
            data=stata_bytes,
            file_name="DataSmartPLS4.dta",
            mime="application/octet-stream",
        )
    else:
        st.caption("Stata export unavailable (pyreadstat not installed).")

    if rds_ok:
        st.download_button(
            "📁 R (.rds)",
            data=rds_bytes,
            file_name="DataSmartPLS4.rds",
            mime="application/octet-stream",
        )
    else:
        st.caption("R export unavailable (pyreadr not installed).")


# --------------------------------------------------------
# FOOTER
# --------------------------------------------------------
render_app_footer()
