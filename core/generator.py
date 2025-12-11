"""
core/generator.py
-----------------
Integrated structural + measurement engine for DataSmartPLS4.0.

This module now supports:
- full structural latent generation (unlimited paths, multi-equation SEM)
- reflective measurement model generation
- Likert-scale output
- demographic generation
- backward compatibility (no structural model → independent latents)

Later extensions:
- bias simulation (already in core/bias)
- multi-group simulation
- exports
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    ModelConfig,
    ConstructConfig,
    SampleConfig,
)
from .structural import simulate_structural_latents


# ============================================================
# ITEM LOADINGS
# ============================================================

def _sample_loadings(construct: ConstructConfig, rng) -> np.ndarray:
    """
    Sample item loadings around target ranges for realism.
    """
    low = max(0.1, min(construct.target_loading_min, construct.target_loading_max))
    high = min(0.99, max(construct.target_loading_min, construct.target_loading_max))

    loadings = rng.uniform(low=low, high=high, size=construct.n_items)

    # shift distribution toward target mean
    shift = construct.target_loading_mean - loadings.mean()
    loadings = np.clip(loadings + shift, 0.10, 0.99)

    return loadings


# ============================================================
# INDICATOR GENERATION (for reflective constructs)
# ============================================================

def _generate_items_for_construct(
    construct: ConstructConfig,
    latent: np.ndarray,
    sample: SampleConfig,
    rng: np.random.Generator
) -> pd.DataFrame:
    """
    Generate Likert-scale indicators for one construct using its latent scores.
    """
    loadings = _sample_loadings(construct, rng)

    n = sample.n_respondents
    lik_min = sample.likert_min
    lik_max = sample.likert_max
    n_cat = lik_max - lik_min + 1

    data = {}

    for idx, lam in enumerate(loadings, start=1):
        lam = float(np.clip(lam, 0.1, 0.95))
        error_var = max(1e-6, 1.0 - lam**2)
        error_sd = np.sqrt(error_var)

        eps = rng.normal(loc=0.0, scale=error_sd, size=n)
        raw = lam * latent + eps  # continuous indicator value

        # convert to Likert categories via quantile binning
        try:
            categories = pd.qcut(raw, q=n_cat, labels=False, duplicates="drop")
        except ValueError:
            # fallback ranking method
            ranks = pd.Series(raw).rank(method="average")
            u = (ranks - 0.5) / len(ranks)
            categories = np.floor(u * n_cat).astype(int)
            categories = np.clip(categories, 0, n_cat - 1)

        likert_values = categories + lik_min
        col = f"{construct.name}_{idx:02d}"
        data[col] = likert_values.astype(int)

    return pd.DataFrame(data)


# ============================================================
# DEMOGRAPHIC GENERATION (basic)
# ============================================================

def _generate_demographics(model_cfg: ModelConfig) -> pd.DataFrame:
    demo_cfg = model_cfg.demographics
    sample = model_cfg.sample

    if not demo_cfg.add_demographics:
        return pd.DataFrame(index=range(sample.n_respondents))

    seed = (sample.random_seed or 0) + 12345
    rng = np.random.default_rng(seed)
    n = sample.n_respondents

    gender = rng.choice(["Male", "Female", "Other"], size=n, p=[0.55, 0.43, 0.02])
    age_group = rng.choice(["18–20", "21–23", "24–26", "27+"],
                           size=n, p=[0.35, 0.40, 0.20, 0.05])
    income = rng.choice(["< 15,000 BDT", "15,000–30,000", "30,001–50,000", "> 50,000"],
                        size=n, p=[0.40, 0.30, 0.20, 0.10])
    study = rng.choice(["1st year", "2nd year", "3rd year", "4th year", "Postgrad"],
                       size=n, p=[0.20, 0.25, 0.25, 0.20, 0.10])

    return pd.DataFrame({
        "gender": gender,
        "age_group": age_group,
        "income_band": income,
        "study_level": study
    })


# ============================================================
# MAIN PIPELINE (STRUCTURAL → MEASUREMENT)
# ============================================================

def generate_dataset(model_cfg: ModelConfig):
    """
    Master function that generates a complete synthetic dataset:

    1. Generate all latent variables:
       - If structural model exists → use structural simulation
       - Otherwise → fallback to independent latent generation

    2. Generate reflective indicators from latent variables.

    3. Generate demographics (optional).

    Returns:
        full_df: demographics + indicators
        items_df: indicator-only dataset
    """
    sample = model_cfg.sample
    constructs = model_cfg.constructs
    rng = np.random.default_rng(sample.random_seed)

    # ========================================================
    # 1. STRUCTURAL LATENT GENERATION
    # ========================================================
    latent_df = simulate_structural_latents(model_cfg)

    # convert to dict of arrays for measurement engine
    latent_scores = {c: latent_df[c].values for c in latent_df.columns}

    # ========================================================
    # 2. REFLECTIVE INDICATOR GENERATION
    # ========================================================
    item_frames = []

    for c in constructs:
        if c.n_items <= 0:
            continue

        latent_vector = latent_scores[c.name]
        df_items = _generate_items_for_construct(
            construct=c,
            latent=latent_vector,
            sample=sample,
            rng=rng
        )
        item_frames.append(df_items)

    if not item_frames:
        raise ValueError("No constructs with n_items > 0.")

    items_df = pd.concat(item_frames, axis=1)

    # ========================================================
    # 3. DEMOGRAPHICS
    # ========================================================
    demo_df = _generate_demographics(model_cfg)

    # merge and return
    if demo_df.empty:
        full_df = items_df.reset_index(drop=True)
    else:
        full_df = pd.concat([demo_df.reset_index(drop=True),
                             items_df.reset_index(drop=True)], axis=1)

    return full_df, items_df
