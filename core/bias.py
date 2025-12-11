"""
core/bias.py
------------
High-performance bias & response-behaviour simulation engine
for DataSmartPLS 4.0.

Includes:
- careless responding
- straight-lining
- random responding
- midpoint bias
- extremity bias
- acquiescence bias
- missingness (MCAR)

All functions are vectorized as much as possible for speed.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


# --------------------------------------------------------------
# 1. CARELESS RESPONSE (cell-level random noise)
# --------------------------------------------------------------
def apply_careless(df: pd.DataFrame, rate: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if rate <= 0:
        return df.copy()

    out = df.copy()
    n, k = out.shape
    total = n * k
    n_affect = int(total * rate)

    rng = np.random.default_rng()

    # Random cell coordinates
    rows = rng.integers(0, n, size=n_affect)
    cols = rng.integers(0, k, size=n_affect)

    # Generate random values in one vectorized step
    random_values = rng.integers(likert_min, likert_max + 1, size=n_affect)
    out.values[rows, cols] = random_values

    return out


# --------------------------------------------------------------
# 2. STRAIGHT-LINING (row-level constant responses)
# --------------------------------------------------------------
def apply_straightlining(df: pd.DataFrame, rate: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if rate <= 0:
        return df.copy()

    out = df.copy()
    n = out.shape[0]

    rng = np.random.default_rng()
    n_people = int(n * rate)

    rows = rng.choice(n, size=n_people, replace=False)
    constant_values = rng.integers(likert_min, likert_max + 1, size=n_people)

    # Fill entire row with its constant value
    for i, r in enumerate(rows):
        out.iloc[r, :] = constant_values[i]

    return out


# --------------------------------------------------------------
# 3. RANDOM RESPONDING (full random rows)
# --------------------------------------------------------------
def apply_random_responding(df: pd.DataFrame, rate: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if rate <= 0:
        return df.copy()

    out = df.copy()
    n, k = out.shape

    rng = np.random.default_rng()
    n_people = int(n * rate)

    rows = rng.choice(n, size=n_people, replace=False)
    random_matrix = rng.integers(likert_min, likert_max + 1, size=(n_people, k))

    out.values[rows, :] = random_matrix

    return out


# --------------------------------------------------------------
# 4. MIDPOINT BIAS (pull values toward central Likert point)
# --------------------------------------------------------------
def apply_midpoint_bias(df: pd.DataFrame, level: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if level <= 0:
        return df.copy()

    out = df.copy()
    midpoint = (likert_min + likert_max) / 2

    # Vectorized midpoint transformation
    out = out + level * (midpoint - out)
    out = out.round().clip(likert_min, likert_max)

    return out


# --------------------------------------------------------------
# 5. EXTREMITY BIAS (push values to nearest extreme)
# --------------------------------------------------------------
def apply_extremity_bias(df: pd.DataFrame, level: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if level <= 0:
        return df.copy()

    out = df.copy().astype(float)
    midpoint = (likert_min + likert_max) / 2

    # Create masks
    upper_mask = out >= midpoint
    lower_mask = out < midpoint

    # Move values toward nearest extreme
    out[upper_mask] = out[upper_mask] + level * (likert_max - out[upper_mask])
    out[lower_mask] = out[lower_mask] + level * (likert_min - out[lower_mask])

    out = out.round().clip(likert_min, likert_max)

    return out


# --------------------------------------------------------------
# 6. ACQUIESCENCE (systematic upward/downward drift)
# --------------------------------------------------------------
def apply_acquiescence(df: pd.DataFrame, level: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if level == 0:
        return df.copy()

    out = df.copy()

    # More realistic: level range [-1, 1] shifts values by up to ±1 point
    shift_amount = np.clip(level, -1, 1)

    out = out + shift_amount
    out = out.round().clip(likert_min, likert_max)

    return out


# --------------------------------------------------------------
# 7. MISSINGNESS (MCAR)
# --------------------------------------------------------------
def apply_missingness(df: pd.DataFrame, rate: float) -> pd.DataFrame:
    if rate <= 0:
        return df.copy()

    out = df.copy()
    n, k = out.shape

    rng = np.random.default_rng()
    total = n * k
    n_nan = int(total * rate)

    rows = rng.integers(0, n, size=n_nan)
    cols = rng.integers(0, k, size=n_nan)

    out.values[rows, cols] = np.nan

    return out


# --------------------------------------------------------------
# 8. MASTER PIPELINE — APPLY ALL BIASES
# --------------------------------------------------------------
def apply_all_biases(
    df: pd.DataFrame,
    likert_min: int,
    likert_max: int,
    careless_rate: float = 0.0,
    straightlining_rate: float = 0.0,
    random_response_rate: float = 0.0,
    midpoint_bias_level: float = 0.0,
    extreme_bias_level: float = 0.0,
    acquiescence_level: float = 0.0,
    missing_rate: float = 0.0,
) -> pd.DataFrame:
    """
    Applies all response behaviours in a fixed, interpretable sequence.
    """
    out = df.copy()

    # Order matters
    out = apply_careless(out, careless_rate, likert_min, likert_max)
    out = apply_straightlining(out, straightlining_rate, likert_min, likert_max)
    out = apply_random_responding(out, random_response_rate, likert_min, likert_max)
    out = apply_midpoint_bias(out, midpoint_bias_level, likert_min, likert_max)
    out = apply_extremity_bias(out, extreme_bias_level, likert_min, likert_max)
    out = apply_acquiescence(out, acquiescence_level, likert_min, likert_max)
    out = apply_missingness(out, missing_rate)

    return out
