import numpy as np
import pandas as pd
import pytest

from core.config import (
    ConstructConfig,
    SampleConfig,
    ModelConfig,
    DemographicConfig,
    BiasConfig,
    StructuralConfig,
    PathConfig,
)
from core.generator import generate_dataset


def mk_construct(name, items=4):
    return ConstructConfig(
        name=name,
        n_items=items,
        latent_mean=0,
        latent_sd=1,
        distribution="normal",
        target_loading_mean=0.75,
        target_loading_min=0.60,
        target_loading_max=0.90,
    )


# ----------------------------------------------------------
# 1. Full pipeline test
# ----------------------------------------------------------
def test_full_pipeline():
    constructs = [
        mk_construct("PE", 4),
        mk_construct("EE", 4),
        mk_construct("BI", 3)
    ]

    sample = SampleConfig(n_respondents=500, likert_min=1, likert_max=5, random_seed=123)

    structural = StructuralConfig(
        paths=[
            PathConfig("PE", "BI", 0.5),
            PathConfig("EE", "BI", 0.4),
        ],
        r2_targets={"BI": 0.50},
    )

    model = ModelConfig(
        project_name="Pipeline",
        researcher_name="Tester",
        constructs=constructs,
        sample=sample,
        demographics=DemographicConfig(add_demographics=True),
        bias=BiasConfig(),
        structural=structural,
    )

    full_df, items_df = generate_dataset(model)

    # Basic checks
    assert full_df.shape[0] == 500
    assert items_df.shape[1] == 11  # 4+4+3 items

    # Likert correctness
    assert full_df.filter(like="PE_").min().min() >= 1
    assert full_df.filter(like="PE_").max().max() <= 5

    # Demographics exist
    assert "gender" in full_df.columns


# ----------------------------------------------------------
# 2. Likert distribution test
# ----------------------------------------------------------
def test_likert_balanced_distribution():
    constructs = [mk_construct("PE", 5)]

    model = ModelConfig(
        project_name="LikertTest",
        researcher_name="Tester",
        constructs=constructs,
        sample=SampleConfig(n_respondents=2000, likert_min=1, likert_max=5),
    )

    full_df, items_df = generate_dataset(model)

    # distribution approx uniform
    for col in items_df.columns:
        counts = items_df[col].value_counts(normalize=True)
        assert abs(counts.mean() - 0.20) < 0.05  # tolerance


# ----------------------------------------------------------
# 3. Reverse-coded item test
# ----------------------------------------------------------
def test_reverse_coded_items():
    c = ConstructConfig(
        name="SAT",
        n_items=4,
        latent_mean=0,
        latent_sd=1,
        distribution="normal",
        reverse_items=2,
        target_loading_mean=0.75,
        target_loading_min=0.60,
        target_loading_max=0.90,
    )

    model = ModelConfig(
        project_name="RC",
        researcher_name="Tester",
        constructs=[c],
        sample=SampleConfig(n_respondents=500, likert_min=1, likert_max=7),
    )

    full_df, items_df = generate_dataset(model)

    # Last two items must be reversed
    assert items_df.iloc[:, -1].max() <= 7
    assert items_df.iloc[:, -1].min() >= 1

    # Reverse relationship: high latent -> low observed
    corr = items_df.iloc[:, -1].corr(items_df.iloc[:, 0])
    assert corr < 0  # must be negative
