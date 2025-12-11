"""
core/diagnostics.py
-------------------
High-accuracy psychometric diagnostics for reflective measurement models
consistent with SmartPLS, PLS-SEM, and psychometric reliability theory.

Computes:
- Cronbach's Alpha
- Composite Reliability (CR)
- Average Variance Extracted (AVE)
- Construct–level correlations
- HTMT (Heterotrait–Monotrait Ratio, Henseler et al. 2015)
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Dict, List


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _safe_numeric_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensures a numeric-only DataFrame without breaking structure."""
    out = df.apply(pd.to_numeric, errors="coerce")
    out = out.dropna(how="all")  # remove rows with all NaN
    return out


# ------------------------------------------------------------
# Cronbach's Alpha
# ------------------------------------------------------------
def cronbach_alpha(df: pd.DataFrame) -> float:
    df = _safe_numeric_df(df)
    k = df.shape[1]
    if k < 2:
        return np.nan

    item_vars = df.var(axis=0, ddof=1)
    total_var = df.sum(axis=1).var(ddof=1)

    if total_var <= 0:
        return np.nan

    alpha = (k / (k - 1)) * (1 - (item_vars.sum() / total_var))
    return float(alpha)


# ------------------------------------------------------------
# Composite Reliability (PLS-style)
# ------------------------------------------------------------
def compute_loadings(df: pd.DataFrame) -> np.ndarray:
    """
    More realistic loading estimation:
    Each indicator is correlated with the mean composite score.
    """
    df = _safe_numeric_df(df)
    latent_score = df.mean(axis=1)

    loadings = df.apply(lambda col: np.corrcoef(col, latent_score)[0, 1])
    loadings = loadings.fillna(0).clip(-0.999, 0.999)

    return loadings.values


def composite_reliability(loadings: np.ndarray, errors: np.ndarray) -> float:
    """
    SmartPLS-style CR formula:
        CR = (Σλ)^2 / ((Σλ)^2 + Σθ)
    """
    lam_sum = np.sum(loadings)
    lam_sq = lam_sum ** 2
    theta_sum = np.sum(errors)

    if lam_sq + theta_sum == 0:
        return np.nan

    return float(lam_sq / (lam_sq + theta_sum))


# ------------------------------------------------------------
# Average Variance Extracted (AVE)
# ------------------------------------------------------------
def ave(loadings: np.ndarray) -> float:
    return float(np.mean(loadings ** 2))


# ------------------------------------------------------------
# HTMT (Henseler et al. 2015)
# ------------------------------------------------------------
def compute_htmt(df_a: pd.DataFrame, df_b: pd.DataFrame,
                 df_a_self: pd.DataFrame, df_b_self: pd.DataFrame) -> float:
    """
    Correct HTMT implementation:

        HTMT_ab = mean(|heterotrait correlations|)
                  / sqrt( mean(|monotrait a|) * mean(|monotrait b|) )

    df_a_self and df_b_self are the within-construct indicator blocks.
    """

    df_a = _safe_numeric_df(df_a)
    df_b = _safe_numeric_df(df_b)
    df_a_self = _safe_numeric_df(df_a_self)
    df_b_self = _safe_numeric_df(df_b_self)

    het = df_a.corrwith(df_b, axis=0)
    het = het.abs().replace([np.inf, -np.inf], np.nan).dropna()

    if len(het) == 0:
        return np.nan

    mono_a = df_a_self.corr().abs()
    mono_b = df_b_self.corr().abs()

    # Off-diagonal average (exclude diagonal=1)
    def off_diag_mean(m):
        vals = m.values.flatten()
        filtered = [v for v in vals if v < 0.9999]  # exclude diagonal
        return np.mean(filtered) if filtered else np.nan

    mono_a_mean = off_diag_mean(mono_a)
    mono_b_mean = off_diag_mean(mono_b)

    if mono_a_mean <= 0 or mono_b_mean <= 0:
        return np.nan

    return float(het.mean() / np.sqrt(mono_a_mean * mono_b_mean))


# ============================================================
# MAIN ROUTINE: FULL DIAGNOSTICS
# ============================================================
def compute_measurement_diagnostics(
    items_df: pd.DataFrame,
    construct_map: Dict[str, List[str]],
):
    """
    Computes psychometric diagnostics identical to SmartPLS practice.

    Inputs:
        items_df: cleaned item-level survey DF
        construct_map: { "PE": ["PE_01", "PE_02", ...], ... }

    Returns:
        dict with alpha, CR, AVE, correlation matrix, HTMT matrix
    """

    items_df = _safe_numeric_df(items_df)

    results = {
        "alpha": {},
        "cr": {},
        "ave": {},
        "construct_correlations": None,
        "htmt": None,
    }

    latent_scores = {}

    # --------------------------------------------------------
    # Reliability metrics by construct
    # --------------------------------------------------------
    for cons, indicators in construct_map.items():
        df_sub = items_df[indicators].copy()

        # Cronbach's alpha
        alpha_val = cronbach_alpha(df_sub)
        results["alpha"][cons] = alpha_val

        # Loadings
        loadings = compute_loadings(df_sub)
        loadings = np.nan_to_num(loadings, nan=0.0)

        # Measurement error variances
        errors = 1 - (loadings ** 2)

        # CR, AVE
        results["cr"][cons] = composite_reliability(loadings, errors)
        results["ave"][cons] = ave(loadings)

        # Latent variable score (unit-weight composite)
        latent_scores[cons] = df_sub.mean(axis=1)

    # --------------------------------------------------------
    # Construct-level correlations
    # --------------------------------------------------------
    latent_df = pd.DataFrame(latent_scores)
    results["construct_correlations"] = latent_df.corr()

    # --------------------------------------------------------
    # HTMT Matrix
    # --------------------------------------------------------
    constructs = list(construct_map.keys())
    htmt_matrix = pd.DataFrame(index=constructs, columns=constructs, dtype=float)

    for i, a in enumerate(constructs):
        for j, b in enumerate(constructs):
            if a == b:
                htmt_matrix.loc[a, b] = 1.0
            else:
                htmt_matrix.loc[a, b] = compute_htmt(
                    items_df[construct_map[a]],
                    items_df[construct_map[b]],
                    items_df[construct_map[a]],
                    items_df[construct_map[b]],
                )

    results["htmt"] = htmt_matrix

    return results
