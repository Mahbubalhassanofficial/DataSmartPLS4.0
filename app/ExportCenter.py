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
)


st.set_page_config(
    page_title="DataSmartPLS4.0 – Export & Codebook Center",
    layout="wide",
)

st.title("Export & Codebook Center")

st.markdown(
    """
This center lets you **export your most recently generated dataset** in multiple
research-ready formats, including:

- SmartPLS-compatible Excel (items only)  
- Full dataset Excel & CSV  
- SPSS (.sav), Stata (.dta), R (.rds)  
- JSON metadata (model + codebook)  
- Codebook CSV for appendices and replication packages  

⚠️ Data shown here comes from the **last dataset you generated on the Home page**
in this session.
"""
)

# --------------------------------------------------------
# 1. Retrieve last generated data + model config
# --------------------------------------------------------
full_df = st.session_state.get("last_full_df", None)
items_df = st.session_state.get("last_items_df", None)
model_cfg = st.session_state.get("last_model_cfg", None)

if full_df is None or items_df is None or model_cfg is None:
    st.error(
        "No generated dataset found in the current session.\n\n"
        "Please go to the **Home** page, configure your constructs and structural model, "
        "generate a dataset, and then return here."
    )
    st.stop()

if not isinstance(full_df, pd.DataFrame) or not isinstance(items_df, pd.DataFrame):
    st.error("Internal data format error: stored objects are not DataFrames.")
    st.stop()

# --------------------------------------------------------
# 2. Basic summary
# --------------------------------------------------------
st.subheader("1. Dataset Summary")

st.write(
    f"- **Total rows (respondents):** {full_df.shape[0]}  \n"
    f"- **Total columns (full dataset):** {full_df.shape[1]}  \n"
    f"- **Measurement indicators (items_df):** {items_df.shape[1]}"
)

st.markdown("### Preview of full dataset (first 10 rows)")
st.dataframe(full_df.head(10), use_container_width=True)

# --------------------------------------------------------
# 3. Generate codebook
# --------------------------------------------------------
st.subheader("2. Codebook & Model Metadata")

codebook_df = generate_codebook(model_cfg, items_df, full_df)

st.markdown("### Codebook preview (first 20 rows)")
st.dataframe(codebook_df.head(20), use_container_width=True)

st.caption(
    "The codebook includes measurement items, demographics (if present), "
    "and structural relations as an appendix."
)

# --------------------------------------------------------
# 4. Prepare all export bytes
# --------------------------------------------------------
st.subheader("3. Download Exports")

# Always safe:
csv_bytes = export_csv(full_df)
excel_full_bytes = export_excel_full(full_df)
excel_spls_bytes = export_excel_smartpls(items_df)
codebook_csv_bytes = codebook_df.to_csv(index=False).encode("utf-8")
metadata_bytes = export_metadata_json(model_cfg, codebook_df)

# Optional: SPSS / Stata / R
spss_bytes = None
stata_bytes = None
rds_bytes = None
spss_ok = False
stata_ok = False
rds_ok = False

try:
    spss_bytes = export_spss(full_df)
    spss_ok = True
except ImportError:
    spss_ok = False
except Exception as e:
    st.warning(f"SPSS export error: {e}")

try:
    stata_bytes = export_stata(full_df)
    stata_ok = True
except ImportError:
    stata_ok = False
except Exception as e:
    st.warning(f"Stata export error: {e}")

try:
    rds_bytes = export_rds(full_df)
    rds_ok = True
except ImportError:
    rds_ok = False
except Exception as e:
    st.warning(f"R export error: {e}")

# --------------------------------------------------------
# 5. Layout download buttons
# --------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### General formats")
    st.download_button(
        label="📄 Download CSV (full dataset)",
        data=csv_bytes,
        file_name="DataSmartPLS4_full_dataset.csv",
        mime="text/csv",
    )
    st.download_button(
        label="📊 Download Excel (full dataset)",
        data=excel_full_bytes,
        file_name="DataSmartPLS4_full_dataset.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with col2:
    st.markdown("#### SmartPLS & Codebook")
    st.download_button(
        label="📊 Download SmartPLS Excel (items only)",
        data=excel_spls_bytes,
        file_name="DataSmartPLS4_items_only_for_SmartPLS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.download_button(
        label="📘 Download Codebook (CSV)",
        data=codebook_csv_bytes,
        file_name="DataSmartPLS4_codebook.csv",
        mime="text/csv",
    )
    st.download_button(
        label="🧩 Download Metadata JSON (model + codebook)",
        data=metadata_bytes,
        file_name="DataSmartPLS4_metadata.json",
        mime="application/json",
    )

with col3:
    st.markdown("#### SPSS / Stata / R")

    if spss_ok and spss_bytes is not None:
        st.download_button(
            label="📁 Download SPSS (.sav)",
            data=spss_bytes,
            file_name="DataSmartPLS4_full_dataset.sav",
            mime="application/octet-stream",
        )
    else:
        st.caption("SPSS export unavailable (pyreadstat not installed).")

    if stata_ok and stata_bytes is not None:
        st.download_button(
            label="📁 Download Stata (.dta)",
            data=stata_bytes,
            file_name="DataSmartPLS4_full_dataset.dta",
            mime="application/octet-stream",
        )
    else:
        st.caption("Stata export unavailable (pyreadstat not installed).")

    if rds_ok and rds_bytes is not None:
        st.download_button(
            label="📁 Download R (.rds)",
            data=rds_bytes,
            file_name="DataSmartPLS4_full_dataset.rds",
            mime="application/octet-stream",
        )
    else:
        st.caption("R export unavailable (pyreadr not installed).")

# --------------------------------------------------------
# 6. Footer
# --------------------------------------------------------
st.markdown("---")
st.markdown(
    """
**DataSmartPLS4.0 – Export & Codebook Center**  
Designed for SmartPLS 4, SEM, fsQCA, and cross-platform statistical workflows.
"""
)
