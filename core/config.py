from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict


# ============================================================
# BASIC TYPES
# ============================================================

DistributionType = Literal["normal", "skewed", "uniform", "lognormal", "beta"]
LikertScaleType = Literal["discrete_likert"]


# ============================================================
# STRUCTURAL MODEL CONFIGURATION  (MOVED TO TOP)
# ============================================================

@dataclass
class PathConfig:
    """
    Defines a single structural path:
        BI = beta * PE + error
    """
    source: str
    target: str
    beta: float


@dataclass
class StructuralConfig:
    """
    Holds structural paths and optional R² targets.
    """
    paths: List[PathConfig] = field(default_factory=list)
    r2_targets: Dict[str, float] = field(default_factory=dict)


# ============================================================
# MEASUREMENT MODEL CONFIGURATION
# ============================================================

@dataclass
class ConstructConfig:
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
    n_respondents: int = 500
    likert_min: int = 1
    likert_max: int = 5
    scale_type: LikertScaleType = "discrete_likert"
    random_seed: Optional[int] = 123


@dataclass
class DemographicConfig:
    add_demographics: bool = True


@dataclass
class BiasConfig:
    careless_rate: float = 0.0
    straightlining_rate: float = 0.0
    random_response_rate: float = 0.0
    acquiescence_level: float = 0.0
    midpoint_bias_level: float = 0.0
    extreme_bias_level: float = 0.0


# ============================================================
# MODEL CONFIG  (NOW StructuralConfig is defined above)
# ============================================================

@dataclass
class ModelConfig:
    """
    High-level configuration object that controls dataset generation.
    """
    project_name: str
    researcher_name: str

    constructs: List[ConstructConfig]

    sample: SampleConfig = field(default_factory=SampleConfig)
    demographics: DemographicConfig = field(default_factory=DemographicConfig)
    bias: BiasConfig = field(default_factory=BiasConfig)

    # FIX: use lambda to avoid class-order issues
    structural: StructuralConfig = field(
        default_factory=lambda: StructuralConfig(paths=[], r2_targets={})
    )

    metadata: Dict[str, str] = field(default_factory=dict)
