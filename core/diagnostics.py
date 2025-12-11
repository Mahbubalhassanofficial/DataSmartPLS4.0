"""
core/diagnostics.py
-------------------
Psychometric diagnostics for reflective measurement models.

This module computes:
- Cronbach's Alpha
- Composite Reliability (CR)
- Average Variance Extracted (AVE)
- Item-item correlation matrices
- Construct correlation matrices
- HTMT (basic version)

These are necessary for SmartPLS-style reliability and validity assessment.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Dict, List


# -------------------------------------------------------------
# HELPER: Cronbach's Alpha
# -------------------------------------------------------------
def cronbach_alpha(df: pd.DataFrame) -> float:
    """
    Compute Cronbach's Alpha for a set of items.
    """
    if df.shape[1] < 2:
        return np.nan

    item_vars = df.var(axis=0, ddof=1)
    total_var = df.sum(axis=1).var(ddof=1)

    alpha = (df.shape[1] / (df.shape[1] - 1)) * (1 - (item_vars.sum() / total_var))
    return float(alpha)


# -------------------------------------------------------------
# HELPER: Composite Reliability (CR)
# -------------------------------------------------------------
def composite_reliability(loadings: List[float], errors: List[float]) -> float:
    """
    Compute Composite Reliability (CR) using standard PLS formula:
    CR = (Σλ)^2 / [(Σλ)^2 + Σθ]
    """
    lam_sum = np.sum(loadings)
    lam_sq_sum = lam_sum ** 2
    theta_sum = np.sum(errors)

    return float(lam_sq_sum / (lam_sq_sum + theta_sum))


# -------------------------------------------------------------
# HELPER: Average Variance Extracted (AVE)
# -------------------------------------------------------------
def ave(loadings: List[float]) -> float:
    """
    Compute AVE = mean of squared loadings.
    """
    return float(np.mean(np.square(loadings)))


# -------------------------------------------------------------
# HELPER: HTMT (basic version)
# -------------------------------------------------------------
def htmt(items_a: pd.DataFrame, items_b: pd.DataFrame) -> float:
    """
    HTMT ratio based on average heterotrait-monotrait correlations.
    """
    corr = items_a.corrwith(items_b, axis=0)
    return float(np.nanmean(np.abs(corr)))


# -------------------------------------------------------------
# MAIN ROUTINE: FULL DIAGNOSTICS
# -------------------------------------------------------------
def compute_measurement_diagnostics(items_df: pd.DataFrame,
                                    construct_map: Dict[str, List[str]]):
    """
    Compute:
    - Alpha
    - CR
    - AVE
    - Construct correlation matrix
    - HTMT matrix

    Inputs:
        items_df: full item-level dataset (only indicators)
        construct_map: dict { "PE": ["PE_01", "PE_02", ...], ... }

    Returns:
        dict with results
    """

    results = {
        "alpha": {},
        "cr": {},
        "ave": {},
        "construct_correlations": None,
        "htmt": None,
    }

    latent_scores = {}

    # Compute reliability metrics construct-by-construct
    for cons, indicators in construct_map.items():
        df = items_df[indicators]

        # alpha
        alpha_val = cronbach_alpha(df)
        results["alpha"][cons] = alpha_val

        # Estimate loadings directly from correlations
        corr = df.corr()
        loadings = np.sqrt(np.maximum(np.diag(corr.values), 1e-6))

        # Error variances
        errors = 1 - (loadings ** 2)

        # CR + AVE
        cr_val = composite_reliability(loadings, errors)
        ave_val = ave(loadings)

        results["cr"][cons] = cr_val
        results["ave"][cons] = ave_val

        # Score estimate (simple averaging)
        latent_scores[cons] = df.mean(axis=1)

    # Construct–level correlations
    latent_df = pd.DataFrame(latent_scores)
    results["construct_correlations"] = latent_df.corr()

    # HTMT
    constructs = list(construct_map.keys())
    htmt_matrix = pd.DataFrame(index=constructs, columns=constructs, dtype=float)

    for i in range(len(constructs)):
        for j in range(len(constructs)):
            if i == j:
                htmt_matrix.iloc[i, j] = 1.0
            else:
                ca = items_df[construct_map[constructs[i]]]
                cb = items_df[construct_map[constructs[j]]]
                htmt_matrix.iloc[i, j] = htmt(ca, cb)

    results["htmt"] = htmt_matrix

    return results
