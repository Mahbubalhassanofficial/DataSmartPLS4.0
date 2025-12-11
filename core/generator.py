"""
core/generator.py
-----------------
Integrated structural + measurement engine for DataSmartPLS4.0.

Supports:
- Full structural latent generation (any number of paths)
- Reflective measurement generation
- Likert scaling
- Demographics
- Backward compatibility when no structural paths exist
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    ModelConfig,
    ConstructConfig,
    SampleConfig,
    StructuralConfig,
)
from .structural import simulate_structural_latents


# ============================================================
#  ITEM LOADING GENERATOR
# ============================================================

def _sample_loadings(construct: ConstructConfig, rng) -> np.ndarray:
    """
    Generate item loadings inside the user-defined range
    and center them around the target mean.
    """
    low = max(0.10, min(construct.target_loading_min, construct.target_loading_max))
    high = min(0.99, max(construct.target_loading_min, construct.target_loading_max))

    loadings = rng.uniform(low, high, size=construct.n_items)

    # Shift mean to target mean
    shift = construct.target_loading_mean - loadings.mean()
    loadings = np.clip(loadings + shift, 0.10, 0.99)

    return loadings


# ============================================================
#  INDICATOR GENERATION (REFLECTIVE)
# ============================================================

def _generate_items_for_construct(
    construct: ConstructConfig,
    latent: np.ndarray,
    sample: SampleConfig,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Converts latent scores into Likert-scale indicator items.
    """
    loadings = _sample_loadings(construct, rng)

    n = sample.n_respondents
    lik_min = sample.likert_min
    lik_max = sample.likert_max
    n_cat = lik_max - lik_min + 1

    data = {}

    for idx, lam in enumerate(loadings, start=1):
        lam = float(np.clip(lam, 0.10, 0.95))
        error_var = max(1e-6, 1.0 - lam**2)
        error_sd = np.sqrt(error_var)

        eps = rng.normal(0, error_sd, size=n)
        raw = lam * latent + eps

        # Likert binning via quantiles
        try:
            cats = pd.qcut(raw, n_cat, labels=False, duplicates="drop")
        except ValueError:
            # fallback when raw values have low variance
            ranks = pd.Series(raw).rank(method="average")
            u = (ranks - 0.5) / len(ranks)
            cats = np.floor(u * n_cat).astype(int)
            cats = np.clip(cats, 0, n_cat - 1)

        lik = cats + lik_min

        col = f"{construct.name}_{idx:02d}"
        data[col] = lik.astype(int)

    return pd.DataFrame(data)


# ============================================================
#  DEMOGRAPHIC GENERATOR
# ============================================================

def _generate_demographics(model_cfg: ModelConfig) -> pd.DataFrame:
    if not model_cfg.demographics.add_demographics:
        return pd.DataFrame(index=range(model_cfg.sample.n_respondents))

    sample = model_cfg.sample
    rng = np.random.default_rng((sample.random_seed or 0) + 777)

    n = sample.n_respondents

    return pd.DataFrame({
        "gender": rng.choice(["Male", "Female", "Other"], n, p=[0.55, 0.43, 0.02]),
        "age_group": rng.choice(["18–20", "21–23", "24–26", "27+"], n, p=[0.35, 0.40, 0.20, 0.05]),
        "income_band": rng.choice(["<15k", "15-30k", "30-50k", ">50k"], n, p=[0.40, 0.30, 0.20, 0.10]),
        "study_level": rng.choice(["1st year", "2nd year", "3rd year", "4th year", "Postgrad"],
                                  n, p=[0.20, 0.25, 0.25, 0.20, 0.10]),
    })


# ============================================================
#  MAIN PIPELINE: STRUCTURAL → MEASUREMENT
# ============================================================

def generate_dataset(model_cfg: ModelConfig):
    """
    Full simulation pipeline:
        1. Generate latent variables (structural or independent)
        2. Generate reflective indicators
        3. Generate demographics
    """
    sample = model_cfg.sample
    constructs = model_cfg.constructs
    rng = np.random.default_rng(sample.random_seed)

    # ========================================================
    # 1. LATENT VARIABLE GENERATION
    # ========================================================
    latent_df = simulate_structural_latents(model_cfg)

    if set(latent_df.columns) != set(c.name for c in constructs):
        missing = set(c.name for c in constructs) - set(latent_df.columns)
        raise ValueError(f"Structural latent generator missing constructs: {missing}")

    latent_scores = {col: latent_df[col].values for col in latent_df.columns}

    # ========================================================
    # 2. INDICATOR GENERATION
    # ========================================================
    frames = []

    for cons in constructs:
        if cons.n_items <= 0:
            continue

        df_items = _generate_items_for_construct(
            construct=cons,
            latent=latent_scores[cons.name],
            sample=sample,
            rng=rng,
        )
        frames.append(df_items)

    if not frames:
        raise ValueError("No constructs with items > 0.")

    items_df = pd.concat(frames, axis=1)

    # ========================================================
    # 3. DEMOGRAPHICS
    # ========================================================
    demo_df = _generate_demographics(model_cfg)

    if demo_df.empty:
        full_df = items_df.reset_index(drop=True)
    else:
        full_df = pd.concat(
            [demo_df.reset_index(drop=True), items_df.reset_index(drop=True)],
            axis=1,
        )

    return full_df, items_df
