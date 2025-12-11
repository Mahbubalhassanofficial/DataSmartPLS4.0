"""
core/structural.py
------------------
Structural latent-variable simulation for DataSmartPLS4.0.

This engine:
- Reads structural paths from StructuralConfig (PathConfig list).
- Detects exogenous vs endogenous constructs.
- Performs a topological sort of constructs.
- Simulates exogenous constructs using their distribution settings.
- Simulates endogenous constructs as linear combinations of their parents + error.
- Can optionally use R² targets (if provided).

This module works at the **latent level** only.
Measurement (indicator generation) is handled in core.generator.
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd

from .config import (
    ModelConfig,
    ConstructConfig,
    SampleConfig,
    StructuralConfig,
    PathConfig,
)


# ============================================================
# LATENT DISTRIBUTION (copied from generator logic, simplified)
# ============================================================

def _generate_exogenous_latent(
    construct: ConstructConfig,
    sample: SampleConfig,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate latent scores for an exogenous construct using its
    specified distribution.
    """
    n = sample.n_respondents
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
# GRAPH / TOPOLOGICAL SORT UTILITIES
# ============================================================

def _build_graph(structural: StructuralConfig) -> Tuple[Set[str], Dict[str, List[str]], Dict[str, List[str]]]:
    """
    Build adjacency structures for the structural model.

    Returns:
        nodes: set of all construct names referenced in paths
        parents: target -> list of sources
        children: source -> list of targets
    """
    parents: Dict[str, List[str]] = {}
    children: Dict[str, List[str]] = {}
    nodes: Set[str] = set()

    for p in structural.paths:
        nodes.add(p.source)
        nodes.add(p.target)

        parents.setdefault(p.target, []).append(p.source)
        children.setdefault(p.source, []).append(p.target)

    return nodes, parents, children


def _topological_sort(
    nodes: Set[str],
    parents: Dict[str, List[str]],
) -> List[str]:
    """
    Perform a topological sort of the constructs.
    Raises ValueError if a cycle is detected.
    """
    # In-degree = number of parents
    in_deg: Dict[str, int] = {node: 0 for node in nodes}
    for tgt, srcs in parents.items():
        in_deg.setdefault(tgt, 0)
        in_deg[tgt] += len(srcs)
        for s in srcs:
            in_deg.setdefault(s, 0)

    # queue: nodes with in-degree 0 (exogenous in the structural sense)
    queue = [n for n, d in in_deg.items() if d == 0]
    order: List[str] = []

    while queue:
        node = queue.pop(0)
        order.append(node)

        # any children of this node?
        for tgt, srcs in parents.items():
            if node in srcs:
                in_deg[tgt] -= 1
                if in_deg[tgt] == 0:
                    queue.append(tgt)

    if len(order) != len(in_deg):
        raise ValueError("Structural model contains a cycle (not allowed in PLS-SEM).")

    return order


# ============================================================
# STRUCTURAL LATENT SIMULATION
# ============================================================

def simulate_structural_latents(model_cfg: ModelConfig) -> pd.DataFrame:
    """
    Simulate latent variables for all constructs in the model,
    respecting structural paths and optional R² targets.

    If no structural paths are defined, constructs are treated as independent
    and generated from their own distributions.

    Returns:
        pandas DataFrame with columns = construct names,
        rows = respondents.
    """
    constructs = model_cfg.constructs
    sample = model_cfg.sample
    structural = model_cfg.structural

    rng = np.random.default_rng(sample.random_seed)

    # Map construct name -> ConstructConfig
    cons_map: Dict[str, ConstructConfig] = {c.name: c for c in constructs}

    if not structural.paths:
        # No structural relations specified → generate each construct independently
        latent_scores = {}
        for c in constructs:
            latent_scores[c.name] = _generate_exogenous_latent(c, sample, rng)
        return pd.DataFrame(latent_scores)

    # Build graph from paths
    nodes, parents, _children = _build_graph(structural)

    # Ensure all constructs in paths exist in config
    for n in nodes:
        if n not in cons_map:
            raise ValueError(f"Construct '{n}' appears in structural paths but is not defined in constructs.")

    # Add constructs that are not referenced in any path (purely exogenous)
    for c in constructs:
        if c.name not in nodes:
            nodes.add(c.name)

    # Recompute topological order
    order = _topological_sort(nodes, parents)

    latent_scores: Dict[str, np.ndarray] = {}

    # First pass: generate exogenous constructs (no parents)
    for name in order:
        if name not in parents or len(parents.get(name, [])) == 0:
            c_cfg = cons_map[name]
            latent_scores[name] = _generate_exogenous_latent(c_cfg, sample, rng)

    # Second pass: generate endogenous constructs
    for name in order:
        if name in latent_scores and (name not in parents or len(parents.get(name, [])) == 0):
            # Already generated as exogenous
            continue

        if name not in parents or len(parents[name]) == 0:
            # No parents → treat as exogenous
            c_cfg = cons_map[name]
            latent_scores[name] = _generate_exogenous_latent(c_cfg, sample, rng)
            continue

        # endogenous construct: combine parents
        parent_names = parents[name]
        betas = []

        for p in structural.paths:
            if p.target == name and p.source in parent_names:
                betas.append((p.source, p.beta))

        if not betas:
            # no beta defined? treat as exogenous
            c_cfg = cons_map[name]
            latent_scores[name] = _generate_exogenous_latent(c_cfg, sample, rng)
            continue

        # build linear combination of standardized parent latents
        parent_matrix = []
        beta_vector = []

        for src_name, beta in betas:
            if src_name not in latent_scores:
                raise ValueError(
                    f"Parent construct '{src_name}' for '{name}' has not been generated yet. "
                    "Check structural paths for cycles or incorrect ordering."
                )
            vals = latent_scores[src_name]
            # standardize parent to mean=0, sd=1
            z = (vals - vals.mean()) / (vals.std() + 1e-8)
            parent_matrix.append(z)
            beta_vector.append(beta)

        parent_matrix = np.vstack(parent_matrix)  # shape: (n_parents, n_obs)
        beta_vector = np.array(beta_vector).reshape(-1, 1)

        # predicted component
        lin_comb = np.dot(beta_vector.T, parent_matrix).flatten()  # shape: (n_obs,)

        # standardize linear predictor
        lin_comb = (lin_comb - lin_comb.mean()) / (lin_comb.std() + 1e-8)

        # decide R² target if available
        r2_dict = structural.r2_targets or {}
        r2_target = float(r2_dict.get(name, 0.0))
        r2_target = float(np.clip(r2_target, 0.0, 0.95))

        if r2_target <= 0:
            # heuristic R² based on beta magnitudes
            heuristic = np.sum(np.square(beta_vector)) / (1.0 + np.sum(np.square(beta_vector)))
            r2 = float(np.clip(heuristic, 0.1, 0.7))
        else:
            r2 = r2_target

        # simulate structural disturbance
        eps = rng.normal(loc=0.0, scale=1.0, size=sample.n_respondents)

        # combine predictor and error to achieve approximated R²
        y_std = np.sqrt(r2) * lin_comb + np.sqrt(1.0 - r2) * eps

        # rescale to construct's mean and sd
        c_cfg = cons_map[name]
        y = (y_std - y_std.mean()) / (y_std.std() + 1e-8)
        y = c_cfg.latent_mean + c_cfg.latent_sd * y

        latent_scores[name] = y

    # ensure all constructs in model are represented in output
    for c in constructs:
        if c.name not in latent_scores:
            # fallback: generate as exogenous
            latent_scores[c.name] = _generate_exogenous_latent(c, sample, rng)

    # return as DataFrame
    df_latent = pd.DataFrame(latent_scores)

    # reorder columns to match the order of constructs in the config for consistency
    ordered_cols = [c.name for c in constructs]
    df_latent = df_latent[ordered_cols]

    return df_latent
