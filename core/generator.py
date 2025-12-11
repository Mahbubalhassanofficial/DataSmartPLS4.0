"""
core/generator.py
-----------------
The foundational measurement engine for DataSmartPLS4.0.

This module generates:
- latent variables
- item-level reflective indicators
- Likert-scale outputs
- basic demographics

Later extensions will add:
- bias simulation
- structural model generation
- multi-group data
- diagnostics
- exports
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (
    ModelConfig,
    ConstructConfig,
    SampleConfig,
    DemographicConfig,
)


# ============================================================
# LATENT VARIABLE GENERATION
# ============================================================

def _generate_latent(construct: ConstructConfig, sample: SampleConfig) -> np.ndarray:
    """
    Generate latent variable scores for one construct.
    Provides several distribution options:
    - normal
    - skewed
    - uniform
    - lognormal
    - beta
    """
    n = sample.n_respondents
    rng = np.random.default_rng(sample.random_seed)

    mean = construct.latent_mean
    sd = construct.latent_sd

    dist = construct.distribution

    if dist == "normal":
        latent = rng.normal(loc=mean, scale=sd, size=n)

    elif dist == "uniform":
        low = mean - np.sqrt(3) * sd
        high = mean + np.sqrt(3) * sd
        latent = rng.uniform(low=low, high=high, size=n)

    elif dist == "lognormal":
        latent = rng.lognormal(mean=mean, sigma=abs(sd), size=n)

    elif dist == "skewed":
        base = rng.normal(loc=0.0, scale=1.0, size=n)
        skew_factor = np.clip(construct.skew, -2.0, 2.0)

        if skew_factor >= 0:
            latent = np.exp(skew_factor * base)
        else:
            latent = -np.exp(-skew_factor * base)

        # standardize + scale back
        latent = (latent - latent.mean()) / (latent.std() + 1e-8)
        latent = mean + sd * latent

    elif dist == "beta":
        a, b = 2.0, 2.0
        x = rng.beta(a, b, size=n)
        latent = (x - x.mean()) / (x.std() + 1e-8)
        latent = mean + sd * latent

    else:
        latent = rng.normal(loc=mean, scale=sd, size=n)

    return latent


# ============================================================
# ITEM GENERATION
# ============================================================

def _sample_loadings(construct: ConstructConfig, rng) -> np.ndarray:
    """
    Sample item loadings in allowed range.
    Center around target mean for realism.
    """
    low = max(0.1, min(construct.target_loading_min, construct.target_loading_max))
    high = min(0.99, max(construct.target_loading_min, construct.target_loading_max))

    loadings = rng.uniform(low=low, high=high, size=construct.n_items)

    # shift toward target mean
    shift = construct.target_loading_mean - loadings.mean()
    loadings = np.clip(loadings + shift, 0.1, 0.99)

    return loadings


def _generate_items_for_construct(construct: ConstructConfig, sample: SampleConfig) -> pd.DataFrame:
    """
    Generate Likert-scale items for a reflective construct.
    """
    rng = np.random.default_rng(sample.random_seed)

    latent = _generate_latent(construct, sample)
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
        raw = lam * latent + eps  # continuous score

        # convert to Likert categories
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
# DEMOGRAPHIC GENERATION (basic version)
# ============================================================

def _generate_demographics(demo_cfg: DemographicConfig, sample: SampleConfig) -> pd.DataFrame:
    """
    Basic demographic profiles.
    Later versions will allow custom distributions.
    """
    if not demo_cfg.add_demographics:
        return pd.DataFrame(index=range(sample.n_respondents))

    seed = (sample.random_seed or 0) + 999
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
# MAIN API
# ============================================================

def generate_dataset(model_cfg: ModelConfig):
    """
    Generate a complete synthetic dataset:
    - demographics (optional)
    - items for each construct
    """
    sample = model_cfg.sample
    constructs = model_cfg.constructs

    frames = []
    for c in constructs:
        if c.n_items <= 0:
            continue
        df = _generate_items_for_construct(c, sample)
        frames.append(df)

    if not frames:
        raise ValueError("No constructs with n_items > 0.")

    items_df = pd.concat(frames, axis=1)
    demo_df = _generate_demographics(model_cfg.demographics, sample)

    if demo_df.empty:
        full_df = items_df.reset_index(drop=True)
    else:
        full_df = pd.concat([demo_df.reset_index(drop=True),
                             items_df.reset_index(drop=True)], axis=1)

    return full_df, items_df
