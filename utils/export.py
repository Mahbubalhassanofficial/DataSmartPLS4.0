"""
utils/export.py
----------------
Full export system for DataSmartPLS4.0 including:

- CSV
- Excel (full dataset)
- Excel SmartPLS (items only)
- SPSS (.sav)
- Stata (.dta)
- R (.rds)
- JSON metadata
- Codebook CSV
- Codebook PDF (journal-ready)
- Codebook HTML

This module is used by the Export Center.
"""

from __future__ import annotations

import json
import pandas as pd
import numpy as np

# Optional libs for SPSS / STATA / R
try:
    import pyreadstat
except ImportError:
    pyreadstat = None

try:
    import pyreadr
except ImportError:
    pyreadr = None

# Optional lib for PDF generation
try:
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    pdf_available = True
except ImportError:
    pdf_available = False

from io import BytesIO
from typing import Dict, List

# =====================================================================
# CODEBOOK GENERATION
# =====================================================================

def generate_codebook(model_cfg, items_df, full_df):
    """
    Create a comprehensive metadata table for:
    - measurement model items
    - demographics
    - structural paths

    Handles both list-based and dict-based construct configurations.
    """
    rows = []

    # Constructs may be a dict or list (generator converts to dict internally)
    if isinstance(model_cfg.constructs, dict):
        constructs_list = list(model_cfg.constructs.values())
    else:
        constructs_list = list(model_cfg.constructs)

    # ---------------------------
    # Measurement Items
    # ---------------------------
    for cons in constructs_list:
        for i in range(1, cons.n_items + 1):
            col = f"{cons.name}_{i:02d}"
            rows.append({
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
            })

    # ---------------------------
    # Demographics
    # ---------------------------
    if model_cfg.demographics.add_demographics:
        demographic_fields = [
            "gender", "age_group", "income_band", "study_level"
        ]
        for col in demographic_fields:
            if col in full_df.columns:
                rows.append({
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
                })

    # ---------------------------
    # Structural paths (appendix section)
    # ---------------------------
    if model_cfg.structural and model_cfg.structural.paths:
        for p in model_cfg.structural.paths:
            rows.append({
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
            })

    return pd.DataFrame(rows)


# =====================================================================
# BASIC EXPORTS
# =====================================================================

def export_csv(full_df: pd.DataFrame) -> bytes:
    """Export dataset to CSV (UTF-8)."""
    return full_df.to_csv(index=False).encode("utf-8")


# =====================================================================
# EXCEL EXPORTS
# =====================================================================

def export_excel_full(full_df: pd.DataFrame) -> bytes:
    """Full dataset (demographics + items) in Excel."""
    buf = BytesIO()
    full_df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


def export_excel_smartpls(items_df: pd.DataFrame) -> bytes:
    """SmartPLS expected format: indicators only, numeric Excel."""
    buf = BytesIO()
    items_df.to_excel(buf, index=False, engine="openpyxl")
    return buf.getvalue()


# =====================================================================
# SPSS, STATA, R
# =====================================================================

def export_spss(full_df: pd.DataFrame) -> bytes:
    """SPSS .sav export using pyreadstat."""
    if pyreadstat is None:
        raise ImportError("pyreadstat not installed (SPSS export unavailable).")
    buf = BytesIO()
    pyreadstat.write_sav(full_df, buf)
    return buf.getvalue()


def export_stata(full_df: pd.DataFrame) -> bytes:
    """STATA .dta export."""
    if pyreadstat is None:
        raise ImportError("pyreadstat not installed (STATA export unavailable).")
    buf = BytesIO()
    pyreadstat.write_dta(full_df, buf)
    return buf.getvalue()


def export_rds(full_df: pd.DataFrame) -> bytes:
    """R .rds export (pyreadr)."""
    if pyreadr is None:
        raise ImportError("pyreadr not installed (R export unavailable).")
    buf = BytesIO()
    pyreadr.write_rds(buf, full_df)
    return buf.getvalue()


# =====================================================================
# JSON METADATA EXPORT
# =====================================================================

def export_metadata_json(model_cfg, codebook_df: pd.DataFrame) -> bytes:
    """Export full project metadata + codebook as JSON."""
    # Construct dictionary
    if isinstance(model_cfg.constructs, dict):
        constructs_list = list(model_cfg.constructs.values())
    else:
        constructs_list = list(model_cfg.constructs)

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
            for c in constructs_list
        ],
        "structural_paths": [
            {"source": p.source, "target": p.target, "beta": p.beta}
            for p in (model_cfg.structural.paths if model_cfg.structural else [])
        ],
        "r2_targets": model_cfg.structural.r2_targets if model_cfg.structural else {},
        "codebook": codebook_df.to_dict(orient="records"),
    }

    return json.dumps(meta, indent=4).encode("utf-8")


# =====================================================================
# CODEBOOK PDF EXPORT
# =====================================================================

def export_codebook_pdf(codebook_df: pd.DataFrame, title="DataSmartPLS4.0 Codebook") -> bytes:
    """Generate a professional PDF codebook."""
    if not pdf_available:
        raise ImportError("reportlab not installed — PDF export unavailable.")

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()

    # Title
    story = [
        Paragraph(title, styles["Title"]),
        Paragraph("Generated using DataSmartPLS4.0", styles["Normal"])
    ]

    # Table
    data = [list(codebook_df.columns)] + codebook_df.astype(str).values.tolist()

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ]))

    story.append(table)
    doc.build(story)

    return buf.getvalue()


# =====================================================================
# HTML CODEBOOK EXPORT
# =====================================================================

def export_codebook_html(codebook_df: pd.DataFrame) -> bytes:
    """Export the codebook as a readable HTML table."""
    html = codebook_df.to_html(index=False, border=1, classes="datasmartpls-table")
    return html.encode("utf-8")
