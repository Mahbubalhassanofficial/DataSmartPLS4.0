"""
core/bias.py
------------
Applies response behaviours and biases to synthetic datasets.

Included in this foundational version:
- careless responding
- straight-lining
- random responding
- midpoint bias
- extremity bias
- acquiescence bias
- missingness injection (MCAR)

These functions receive a pandas DataFrame and return a modified DataFrame.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


# --------------------------------------------------------------
# 1. CARELESS RESPONSE (random noise replacing real values)
# --------------------------------------------------------------
def apply_careless(df: pd.DataFrame, rate: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if rate <= 0:
        return df

    out = df.copy()
    n, k = df.shape

    rng = np.random.default_rng()

    total = n * k
    n_affect = int(total * rate)

    # pick random cells
    rows = rng.integers(0, n, size=n_affect)
    cols = rng.integers(0, k, size=n_affect)

    for r, c in zip(rows, cols):
        out.iat[r, c] = rng.integers(likert_min, likert_max + 1)

    return out


# --------------------------------------------------------------
# 2. STRAIGHT-LINING (same answer across all items)
# --------------------------------------------------------------
def apply_straightlining(df: pd.DataFrame, rate: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if rate <= 0:
        return df

    out = df.copy()
    n = df.shape[0]

    rng = np.random.default_rng()
    n_people = int(n * rate)

    rows = rng.choice(n, size=n_people, replace=False)
    for r in rows:
        value = rng.integers(likert_min, likert_max + 1)
        out.iloc[r, :] = value

    return out


# --------------------------------------------------------------
# 3. RANDOM RESPONDING (fully random for selected rows)
# --------------------------------------------------------------
def apply_random_responding(df: pd.DataFrame, rate: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if rate <= 0:
        return df

    out = df.copy()
    n = df.shape[0]

    rng = np.random.default_rng()
    n_people = int(n * rate)

    rows = rng.choice(n, size=n_people, replace=False)
    for r in rows:
        out.iloc[r, :] = rng.integers(likert_min, likert_max + 1, size=df.shape[1])

    return out


# --------------------------------------------------------------
# 4. MIDPOINT BIAS (shift values toward midpoint)
# --------------------------------------------------------------
def apply_midpoint_bias(df: pd.DataFrame, level: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if level <= 0:
        return df

    out = df.copy()
    midpoint = (likert_min + likert_max) / 2
    midpoint = int(round(midpoint))

    # pull values toward midpoint
    for col in out.columns:
        out[col] = out[col].apply(
            lambda x: int(round(x + level * (midpoint - x)))
        )

        # ensure bounds
        out[col] = out[col].clip(likert_min, likert_max)

    return out


# --------------------------------------------------------------
# 5. EXTREMITY BIAS (move values toward ends of scale)
# --------------------------------------------------------------
def apply_extremity_bias(df: pd.DataFrame, level: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if level <= 0:
        return df

    out = df.copy()
    midpoint = (likert_min + likert_max) / 2

    def push_extreme(x):
        if x >= midpoint:
            target = likert_max
        else:
            target = likert_min
        return int(round(x + level * (target - x)))

    for col in out.columns:
        out[col] = out[col].apply(push_extreme).clip(likert_min, likert_max)

    return out


# --------------------------------------------------------------
# 6. ACQUIESCENCE (shift values upward)
# --------------------------------------------------------------
def apply_acquiescence(df: pd.DataFrame, level: float, likert_min: int, likert_max: int) -> pd.DataFrame:
    if level == 0:
        return df

    out = df.copy()

    shift = int(round(level * 1))  # small shift
    out = out + shift
    return out.clip(likert_min, likert_max)


# --------------------------------------------------------------
# 7. MISSINGNESS (MCAR)
# --------------------------------------------------------------
def apply_missingness(df: pd.DataFrame, rate: float) -> pd.DataFrame:
    if rate <= 0:
        return df

    out = df.copy()
    n, k = out.shape
    rng = np.random.default_rng()

    total = n * k
    n_nan = int(total * rate)

    rows = rng.integers(0, n, size=n_nan)
    cols = rng.integers(0, k, size=n_nan)

    for r, c in zip(rows, cols):
        out.iat[r, c] = np.nan

    return out


# --------------------------------------------------------------
# 8. MASTER FUNCTION — APPLY ALL BIASES
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

    out = df.copy()

    out = apply_careless(out, careless_rate, likert_min, likert_max)
    out = apply_straightlining(out, straightlining_rate, likert_min, likert_max)
    out = apply_random_responding(out, random_response_rate, likert_min, likert_max)
    out = apply_midpoint_bias(out, midpoint_bias_level, likert_min, likert_max)
    out = apply_extremity_bias(out, extreme_bias_level, likert_min, likert_max)
    out = apply_acquiescence(out, acquiescence_level, likert_min, likert_max)
    out = apply_missingness(out, missing_rate)

    return out
