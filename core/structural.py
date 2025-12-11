"""
core/structural.py (DataSmartPLS 4.0 — Final Stable Version)
------------------------------------------------------------
Fully corrected structural latent generator supporting:
- Unlimited DAG-style structural paths
- Exact or heuristic R² control
- Arbitrary distributions of exogenous constructs
- Deterministic ordering and integration with generator.py
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
# EXOGENOUS LATENT GENERATOR
# ============================================================

def _generate_exogenous_latent(
    construct: ConstructConfig,
    sample: SampleConfig,
    rng: np.random.Generator,
) -> np.ndarray:

    n = sample.n_respondents
    mean, sd = construct.latent_mean, construct.latent_sd
    dist = construct.distribution

    if dist == "normal":
        latent = rng.normal(mean, sd, n)

    elif dist == "uniform":
        span = np.sqrt(3) * sd
        latent = rng.uniform(mean - span, mean + span, n)

    elif dist == "lognormal":
        latent = rng.lognormal(mean, max(sd, 1e-6), n)

    elif dist == "skewed":
        base = rng.normal(0, 1, n)
        skew = np.clip(construct.skew, -2, 2)

        if skew >= 0:
            z = np.exp(skew * base)
        else:
            z = -np.exp(-skew * base)

        z = (z - z.mean()) / (z.std() + 1e-8)
        latent = mean + sd * z

    elif dist == "beta":
        x = rng.beta(2, 2, n)
        z = (x - x.mean()) / (x.std() + 1e-8)
        latent = mean + sd * z

    else:
        latent = rng.normal(mean, sd, n)

    return latent



# ============================================================
# GRAPH UTILITIES — CLEAN DAG HANDLING
# ============================================================

def _build_graph(paths: List[PathConfig]):
    parents = {}
    children = {}
    nodes = set()

    for p in paths:
        nodes.add(p.source)
        nodes.add(p.target)
        parents.setdefault(p.target, []).append(p.source)
        children.setdefault(p.source, []).append(p.target)

    return nodes, parents, children


def _topological_sort(nodes: Set[str], parents: Dict[str, List[str]]):
    """
    Classical Kahn's algorithm for cycle-safe topological sorting.
    """
    in_deg = {n: 0 for n in nodes}

    # compute in-degrees
    for tgt, srcs in parents.items():
        for s in srcs:
            in_deg[tgt] += 1

    # queue of exogenous constructs
    queue = [n for n, d in in_deg.items() if d == 0]
    order = []

    while queue:
        node = queue.pop(0)
        order.append(node)

        # reduce in-degree of children
        for tgt, srcs in parents.items():
            if node in srcs:
                in_deg[tgt] -= 1
                if in_deg[tgt] == 0:
                    queue.append(tgt)

    if len(order) != len(nodes):
        raise ValueError("Cycle detected in structural model — PLS-SEM requires a DAG.")

    return order



# ============================================================
# STRUCTURAL LATENT SIMULATION
# ============================================================

def simulate_structural_latents(model_cfg: ModelConfig) -> pd.DataFrame:
    """
    Main structural latent generator.
    Produces a DataFrame of latent variable scores for each construct.
    """

    sample = model_cfg.sample
    structural = model_cfg.structural
    rng = np.random.default_rng(sample.random_seed)

    # ALWAYS treat constructs as a list (generator enforces this)
    constructs: List[ConstructConfig] = model_cfg.constructs
    cons_map = {c.name: c for c in constructs}
    construct_order = [c.name for c in constructs]

    if not constructs:
        raise ValueError("No constructs defined in ModelConfig.")

    # ============================================================
    # CASE 1 — NO STRUCTURAL RELATIONS
    # ============================================================
    if not structural.paths:
        return pd.DataFrame({
            c.name: _generate_exogenous_latent(c, sample, rng)
            for c in constructs
        })[construct_order]

    # ============================================================
    # CASE 2 — STRUCTURAL MODEL DEFINED
    # ============================================================
    nodes, parents, children = _build_graph(structural.paths)

    # Validate constructs referenced in structural model
    for node in nodes:
        if node not in cons_map:
            raise ValueError(
                f"Construct '{node}' is referenced in structural paths "
                f"but is not defined in ModelConfig."
            )

    # include constructs not referenced at all (pure exogenous)
    for c in construct_order:
        nodes.add(c)

    order = _topological_sort(nodes, parents)

    latent_scores = {}

    # ============================================================
    # 1. EXOGENOUS GENERATION
    # ============================================================
    for name in order:
        if name not in parents or len(parents.get(name, [])) == 0:
            latent_scores[name] = _generate_exogenous_latent(cons_map[name], sample, rng)

    # ============================================================
    # 2. ENDOGENOUS GENERATION
    # ============================================================
    for name in order:

        if name in latent_scores:
            continue

        if name not in parents:
            # treat as exogenous
            latent_scores[name] = _generate_exogenous_latent(cons_map[name], sample, rng)
            continue

        parent_list = parents[name]

        # Get betas
        betas = [(p.source, p.beta)
                 for p in structural.paths
                 if p.target == name and p.source in parent_list]

        if not betas:
            latent_scores[name] = _generate_exogenous_latent(cons_map[name], sample, rng)
            continue

        X = []
        B = []

        # build predictors
        for src, beta in betas:
            parent = latent_scores[src]
            z = (parent - parent.mean()) / (parent.std() + 1e-8)
            X.append(z)
            B.append(beta)

        X = np.vstack(X)
        B = np.array(B).reshape(-1, 1)

        # linear predictor (standardized)
        lin = np.dot(B.T, X).flatten()
        lin = (lin - lin.mean()) / (lin.std() + 1e-8)

        # R² configuration
        r2_targets = structural.r2_targets or {}
        r2 = float(r2_targets.get(name, 0.0))

        if r2 <= 0:
            # improved heuristic R²
            beta_vec = np.array([b for _, b in betas])
            beta_norm = np.sqrt(np.sum(beta_vec ** 2))
            r2 = float(np.clip(beta_norm / (1 + beta_norm), 0.10, 0.70))

        # error
        eps = rng.normal(0, 1, sample.n_respondents)

        y_std = np.sqrt(r2) * lin + np.sqrt(1 - r2) * eps

        # rescale to construct latent parameters
        cfg = cons_map[name]
        y_std = (y_std - y_std.mean()) / (y_std.std() + 1e-8)
        y = cfg.latent_mean + cfg.latent_sd * y_std

        latent_scores[name] = y

    # ============================================================
    # FINAL LATENT DATAFRAME
    # ============================================================
    df_latent = pd.DataFrame(latent_scores)
    df_latent = df_latent[construct_order]   # enforce strict order

    return df_latent
