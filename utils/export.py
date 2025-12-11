"""
utils/export.py
----------------
Handles all exporting functions for DataSmartPLS4.0:

- CSV, Excel (full and SmartPLS-format)
- SPSS (.sav)
- Stata (.dta)
- R (.rds)
- JSON metadata
- Codebook generation

This module enables complete academic-quality export functionality.
"""

import json
import pandas as pd
import numpy as np

# Optional libraries
try:
    import pyreadstat       # SPSS + Stata
except ImportError:
    pyreadstat = None

try:
    import pyreadr          # R export
except ImportError:
    pyreadr = None



# =====================================================================
# CODEBOOK GENERATION
# =====================================================================

def generate_codebook(model_cfg, items_df, full_df):
    """
    Create a metadata table for constructs, items, demographics,
    and structural paths.

    Returned as a pandas DataFrame.
    """
    rows = []

    # Measurement constructs
    for cons in model_cfg.constructs:
        for i in range(1, cons.n_items + 1):
            col = f"{cons.name}_{i:02d}"

            if col in full_df.columns:
                col_min = full_df[col].min()
                col_max = full_df[col].max()
            else:
                col_min, col_max = np.nan, np.nan

            rows.append(
                {
                    "variable": col,
                    "construct": cons.name,
                    "item_label": f"Item {i}",
                    "distribution": cons.distribution,
                    "latent_mean": cons.latent_mean,
                    "latent_sd": cons.latent_sd,
                    "skew": cons.skew,
                    "loading_target_mean": cons.target_loading_mean,
                    "scale_min": model_cfg.sample.likert_min,
                    "scale_max": model_cfg.sample.likert_max,
                    "type": "Likert item",
                }
            )

    # Demographics
    if model_cfg.demographics.add_demographics:
        for col in ["gender", "age_group", "income_band", "study_level"]:
            if col in full_df.columns:
                rows.append(
                    {
                        "variable": col,
                        "construct": "demographic",
                        "item_label": col,
                        "distribution": "categorical",
                        "latent_mean": None,
                        "latent_sd": None,
                        "skew": None,
                        "loading_target_mean": None,
                        "scale_min": None,
                        "scale_max": None,
                        "type": "category",
                    }
                )

    # Structural appendix
    if model_cfg.structural and model_cfg.structural.paths:
        for p in model_cfg.structural.paths:
            rows.append(
                {
                    "variable": f"{p.source} → {p.target}",
                    "construct": "structural_path",
                    "item_label": f"β = {p.beta:.3f}",
                    "distribution": None,
                    "latent_mean": None,
                    "latent_sd": None,
                    "skew": None,
                    "loading_target_mean": None,
                    "scale_min": None,
                    "scale_max": None,
                    "type": "structural_relation",
                }
            )

    return pd.DataFrame(rows)



# =====================================================================
# BASIC EXPORTS
# =====================================================================

def export_csv(full_df):
    """Export full dataset as CSV."""
    return full_df.to_csv(index=False).encode("utf-8")



# =====================================================================
# EXCEL EXPORTS
# =====================================================================

def export_excel_full(full_df):
    """
    Export the *full* dataset as Excel:
    demographic + items + additional variables.
    """
    from io import BytesIO
    buf = BytesIO()
    full_df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def export_excel_smartpls(items_df):
    """
    Export ONLY item indicators as Excel.
    This is the official SmartPLS-compatible format.
    
    No demographics, no strings — only pure numeric indicator columns.
    """
    from io import BytesIO
    buf = BytesIO()
    items_df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()



# =====================================================================
# SPSS + STATA EXPORTS
# =====================================================================

def export_spss(full_df):
    """Export full dataset to SPSS .sav."""
    if pyreadstat is None:
        raise ImportError("pyreadstat is required for SPSS export.")

    from io import BytesIO
    buf = BytesIO()
    pyreadstat.write_sav(full_df, buf)
    return buf.getvalue()


def export_stata(full_df):
    """Export full dataset to Stata .dta."""
    if pyreadstat is None:
        raise ImportError("pyreadstat is required for Stata export.")

    from io import BytesIO
    buf = BytesIO()
    pyreadstat.write_dta(full_df, buf)
    return buf.getvalue()



# =====================================================================
# R EXPORT (.rds)
# =====================================================================

def export_rds(full_df):
    """Export full dataset as a .rds file for R."""
    if pyreadr is None:
        raise ImportError("pyreadr is required for R export.")

    from io import BytesIO
    buf = BytesIO()
    pyreadr.write_rds(buf, full_df)
    return buf.getvalue()



# =====================================================================
# METADATA JSON EXPORT
# =====================================================================

def export_metadata_json(model_cfg, codebook_df):
    """
    Create a complete JSON metadata file containing:
    - project info
    - construct definitions
    - structural paths
    - R² targets
    - codebook
    """
    meta = {
        "project": model_cfg.project_name,
        "researcher": model_cfg.researcher_name,
        "n_respondents": model_cfg.sample.n_respondents,
        "likert_min": model_cfg.sample.likert_min,
        "likert_max": model_cfg.sample.likert_max,
        "constructs": [
            {
                "name": c.name,
                "items": c.n_items,
                "distribution": c.distribution,
                "latent_mean": c.latent_mean,
                "latent_sd": c.latent_sd,
                "skew": c.skew,
                "target_loading_mean": c.target_loading_mean,
            }
            for c in model_cfg.constructs
        ],
        "structural_paths": [
            {"source": p.source, "target": p.target, "beta": p.beta}
            for p in (model_cfg.structural.paths if model_cfg.structural else [])
        ],
        "r2_targets": (
            model_cfg.structural.r2_targets
            if model_cfg.structural else {}
        ),
        "codebook": codebook_df.to_dict(orient="records"),
    }

    return json.dumps(meta, indent=4).encode("utf-8")
