"""
core/generator.py
-----------------
Integrated structural + measurement engine for DataSmartPLS4.0.

This revised version:
- Fixes construct ordering issues
- Removes unsafe dict replacement
- Ensures structural + measurement RNG share the same seed stream
- Improves Likert binning robustness
- Adds validation for edge cases
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
#  ITEM LOADING GENERATOR
# ============================================================

def _sample_loadings(construct: ConstructConfig, rng: np.random.Generator) -> np.ndarray:
    """Generate loadings, centered around target mean, respecting user-defined bounds."""
    low = construct.target_loading_min
    high = construct.target_loading_max

    loadings = rng.uniform(low, high, size=construct.n_items)

    # Center toward target mean
    shift = construct.target_loading_mean - loadings.mean()
    loadings = np.clip(loadings + shift, 0.10, 0.99)

    return loadings


# ============================================================
#  REFLECTIVE INDICATOR GENERATION
# ============================================================

def _likert_discretize(raw, n_cat, lik_min, lik_max):
    """Safe & stable quantile → Likert binning."""
    try:
        # Full quantile binning
        bins = pd.qcut(raw, n_cat, labels=False, duplicates="drop")
        if bins.isnull().any():
            raise ValueError("qcut failed due to low variance.")
        cats = bins.values
    except Exception:
        # Fallback uniform rank transformation
        ranks = pd.Series(raw).rank(method="average")
        u = (ranks - 0.5) / len(ranks)
        cats = np.floor(u * n_cat).astype(int)
        cats = np.clip(cats, 0, n_cat - 1)

    return (cats + lik_min).clip(lik_min, lik_max)


def _generate_items_for_construct(
    construct: ConstructConfig,
    latent: np.ndarray,
    sample: SampleConfig,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """Generate reflective indicators for a construct."""
    n = sample.n_respondents
    lik_min = sample.likert_min
    lik_max = sample.likert_max
    n_cat = lik_max - lik_min + 1

    loadings = _sample_loadings(construct, rng)

    items = {}

    for idx, lam in enumerate(loadings, start=1):
        lam = float(np.clip(lam, 0.10, 0.95))

        error_var = max(1e-6, 1.0 - lam * lam)
        eps = rng.normal(0.0, np.sqrt(error_var), size=n)

        raw = lam * latent + eps

        lik = _likert_discretize(raw, n_cat, lik_min, lik_max)
        items[f"{construct.name}_{idx:02d}"] = lik.astype(int)

    df_items = pd.DataFrame(items)

    # Reverse coding (safer logic)
    if construct.reverse_items > 0:
        cols = df_items.columns[:construct.reverse_items]
        for c in cols:
            df_items[c] = lik_min + lik_max - df_items[c]

    return df_items


# ============================================================
#  DEMOGRAPHIC GENERATOR
# ============================================================

def _generate_demographics(model_cfg: ModelConfig) -> pd.DataFrame:
    """Synthetic categorical demographics."""
    if not model_cfg.demographics.add_demographics:
        return pd.DataFrame(index=range(model_cfg.sample.n_respondents))

    sample = model_cfg.sample
    rng = np.random.default_rng(sample.random_seed + 777)

    n = sample.n_respondents

    return pd.DataFrame({
        "gender": rng.choice(["Male", "Female", "Other"], n, p=[0.55, 0.43, 0.02]),
        "age_group": rng.choice(["18–20", "21–23", "24–26", "27+"], n, p=[0.35, 0.40, 0.20, 0.05]),
        "income_band": rng.choice(["<15k", "15–30k", "30–50k", ">50k"], n, p=[0.40, 0.30, 0.20, 0.10]),
        "study_level": rng.choice(
            ["1st year", "2nd year", "3rd year", "4th year", "Postgrad"],
            n, p=[0.20, 0.25, 0.25, 0.20, 0.10]
        ),
    })


# ============================================================
#  MAIN PIPELINE
# ============================================================

def generate_dataset(model_cfg: ModelConfig):
    """Full simulation pipeline: structural → reflective → demographics."""
    # Validate full model
    model_cfg.validate()

    sample = model_cfg.sample
    constructs = model_cfg.constructs

    if not constructs:
        raise ValueError("No constructs defined.")

    # ----------------------------
    # RNG for entire process
    # ----------------------------
    rng = np.random.default_rng(sample.random_seed)

    # ----------------------------
    # 1. STRUCTURAL LATENT GENERATION
    # ----------------------------
    latent_df = simulate_structural_latents(model_cfg)

    # Enforce ordering based on user-defined constructs
    expected = [c.name for c in constructs]
    missing = [c for c in expected if c not in latent_df.columns]

    if missing:
        raise ValueError(f"Missing latent variables in structural output: {missing}")

    latent_scores = {name: latent_df[name].values for name in expected}

    # ----------------------------
    # 2. INDICATOR GENERATION
    # ----------------------------
    item_frames = []

    for cons in constructs:
        df_items = _generate_items_for_construct(
            construct=cons,
            latent=latent_scores[cons.name],
            sample=sample,
            rng=rng,
        )
        item_frames.append(df_items)

    items_df = pd.concat(item_frames, axis=1)

    # ----------------------------
    # 3. DEMOGRAPHICS
    # ----------------------------
    demo_df = _generate_demographics(model_cfg)

    # ----------------------------
    # 4. FINAL ASSEMBLY
    # ----------------------------
    if demo_df.empty:
        full_df = items_df.reset_index(drop=True)
    else:
        full_df = pd.concat(
            [demo_df.reset_index(drop=True), items_df.reset_index(drop=True)],
            axis=1,
        )

    return full_df, items_df
