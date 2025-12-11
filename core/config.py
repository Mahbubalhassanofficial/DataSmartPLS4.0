from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict


# Distribution types for latent variables
DistributionType = Literal[
    "normal",
    "skewed",
    "uniform",
    "lognormal",
    "beta"
]

# Scale type (later: binary, VAS, etc.)
LikertScaleType = Literal["discrete_likert"]


@dataclass
class ConstructConfig:
    """
    Configuration for one reflective latent construct.
    Future versions will expand to formative, higher-order, and structural relations.
    """
    name: str
    n_items: int

    latent_mean: float = 0.0
    latent_sd: float = 1.0

    distribution: DistributionType = "normal"
    skew: float = 0.0
    kurtosis: float = 3.0

    target_loading_mean: float = 0.75
    target_loading_min: float = 0.60
    target_loading_max: float = 0.90

    reverse_items: int = 0
    allow_cross_loadings: bool = False


@dataclass
class SampleConfig:
    """
    Sample-level configuration settings.
    """
    n_respondents: int = 500
    likert_min: int = 1
    likert_max: int = 5
    scale_type: LikertScaleType = "discrete_likert"
    random_seed: Optional[int] = 123


@dataclass
class DemographicConfig:
    """
    Demographic simulation settings.
    """
    add_demographics: bool = True


@dataclass
class BiasConfig:
    """
    Response style behaviours — to be applied in later steps.
    """
    careless_rate: float = 0.0
    straightlining_rate: float = 0.0
    random_response_rate: float = 0.0
    acquiescence_level: float = 0.0
    midpoint_bias_level: float = 0.0
    extreme_bias_level: float = 0.0


@dataclass
class ModelConfig:
    """
    High-level configuration object that holds everything needed
    to generate one synthetic dataset.
    """
    project_name: str
    researcher_name: str

    constructs: List[ConstructConfig]
    sample: SampleConfig = field(default_factory=SampleConfig)
    demographics: DemographicConfig = field(default_factory=DemographicConfig)
    bias: BiasConfig = field(default_factory=BiasConfig)

    metadata: Dict[str, str] = field(default_factory=dict)

# ============================================================
# STRUCTURAL MODEL CONFIGURATION
# ============================================================

@dataclass
class PathConfig:
    """
    Defines a single structural path between constructs.

    Example:
        PathConfig(source="PE", target="BI", beta=0.35)

    Meaning:
        BI = 0.35 * PE + error
    """
    source: str   # predictor construct name
    target: str   # outcome construct name
    beta: float   # path coefficient


@dataclass
class StructuralConfig:
    """
    Holds all structural paths and (optionally) R² targets.

    - paths: list of PathConfig objects
    - r2_targets: optional mapping from construct → desired R²

    R² matching will be implemented in a later structural step.
    For now, paths control how latent variables influence each other.
    """
    paths: List[PathConfig] = field(default_factory=list)
    r2_targets: Dict[str, float] = field(default_factory=dict)

