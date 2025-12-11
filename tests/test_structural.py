import numpy as np
import pandas as pd
import pytest

from core.config import (
    ConstructConfig,
    SampleConfig,
    ModelConfig,
    StructuralConfig,
    PathConfig,
)
from core.structural import simulate_structural_latents


# ----------------------------------------------------------
# Utility construct factory
# ----------------------------------------------------------
def mk_construct(name, dist="normal", mean=0.0, sd=1.0):
    return ConstructConfig(
        name=name,
        n_items=3,
        latent_mean=mean,
        latent_sd=sd,
        distribution=dist,
        skew=0.5,
        kurtosis=3.0,
        target_loading_mean=0.75,
        target_loading_min=0.60,
        target_loading_max=0.90,
    )


# ----------------------------------------------------------
# 1. Test independent latent generation
# ----------------------------------------------------------
def test_independent_latents():
    constructs = [mk_construct("PE"), mk_construct("EE"), mk_construct("BI")]
    sample = SampleConfig(n_respondents=1000, likert_min=1, likert_max=5, random_seed=123)

    model = ModelConfig(
        project_name="Test",
        researcher_name="Tester",
        constructs=constructs,
        sample=sample,
        structural=StructuralConfig(paths=[], r2_targets={}),
    )

    df = simulate_structural_latents(model)

    assert df.shape == (1000, 3)
    assert list(df.columns) == ["PE", "EE", "BI"]
    assert np.abs(df["PE"].mean()) < 0.05


# ----------------------------------------------------------
# 2. Simple structural relation PE → BI
# ----------------------------------------------------------
def test_single_path():
    constructs = [mk_construct("PE"), mk_construct("BI")]
    sample = SampleConfig(n_respondents=800, likert_min=1, likert_max=5, random_seed=222)

    paths = [PathConfig(source="PE", target="BI", beta=0.6)]

    model = ModelConfig(
        project_name="Test",
        researcher_name="Tester",
        constructs=constructs,
        sample=sample,
        structural=StructuralConfig(paths=paths, r2_targets={"BI": 0.45}),
    )

    df = simulate_structural_latents(model)

    # BI should correlate strongly with PE
    corr = df["PE"].corr(df["BI"])
    assert corr > 0.55


# ----------------------------------------------------------
# 3. Multi-parent structural model
# ----------------------------------------------------------
def test_multiple_parents():
    constructs = [mk_construct("PE"), mk_construct("EE"), mk_construct("BI")]
    sample = SampleConfig(n_respondents=1500, likert_min=1, likert_max=5, random_seed=77)

    paths = [
        PathConfig(source="PE", target="BI", beta=0.5),
        PathConfig(source="EE", target="BI", beta=0.4),
    ]

    model = ModelConfig(
        project_name="Test2",
        researcher_name="Tester",
        constructs=constructs,
        sample=sample,
        structural=StructuralConfig(paths=paths, r2_targets={"BI": 0.50}),
    )

    df = simulate_structural_latents(model)

    # Check correlations
    assert df["PE"].corr(df["BI"]) > 0.40
    assert df["EE"].corr(df["BI"]) > 0.30


# ----------------------------------------------------------
# 4. R² accuracy test
# ----------------------------------------------------------
def test_r2_accuracy():
    constructs = [mk_construct("PE"), mk_construct("BI")]
    sample = SampleConfig(n_respondents=2000, likert_min=1, likert_max=5, random_seed=999)

    paths = [PathConfig(source="PE", target="BI", beta=0.7)]

    target_r2 = 0.60

    model = ModelConfig(
        project_name="R2 Test",
        researcher_name="Tester",
        constructs=constructs,
        sample=sample,
        structural=StructuralConfig(paths=paths, r2_targets={"BI": target_r2}),
    )

    df = simulate_structural_latents(model)

    # Regression approximation of R²
    corr = df["PE"].corr(df["BI"])
    estimated_r2 = corr * corr

    # allow tolerance
    assert abs(estimated_r2 - target_r2) < 0.03


# ----------------------------------------------------------
# 5. Cycle detection
# ----------------------------------------------------------
def test_cycle_detection():
    constructs = [mk_construct("A"), mk_construct("B")]
    sample = SampleConfig(n_respondents=500)

    # Illegal: A → B and B → A
    paths = [
        PathConfig(source="A", target="B", beta=0.5),
        PathConfig(source="B", target="A", beta=0.4),
    ]

    model = ModelConfig(
        project_name="CycleTest",
        researcher_name="Tester",
        constructs=constructs,
        sample=sample,
        structural=StructuralConfig(paths=paths),
    )

    with pytest.raises(ValueError):
        simulate_structural_latents(model)


# ----------------------------------------------------------
# 6. Unreferenced constructs must be exogenous
# ----------------------------------------------------------
def test_unreferenced_constructs_are_generated():
    constructs = [mk_construct("PE"), mk_construct("EE"), mk_construct("BI")]

    paths = [PathConfig(source="PE", target="BI", beta=0.5)]

    model = ModelConfig(
        project_name="Test",
        researcher_name="Tester",
        constructs=constructs,
        sample=SampleConfig(n_respondents=300),
        structural=StructuralConfig(paths=paths),
    )

    df = simulate_structural_latents(model)

    assert "EE" in df.columns
    assert df["EE"].std() > 0.5  # must generate exogenously
