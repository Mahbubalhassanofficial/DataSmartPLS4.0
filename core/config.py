"""
core/config.py
--------------
Central configuration dataclasses for DataSmartPLS 4.0.

This module defines all model-level objects used by:
- structural latent generator
- measurement/item generator
- bias engine
- demographic generator
- export/diagnostics modules

Designed for high extensibility and strict type validation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict


# ============================================================
# BASIC TYPE DEFINITIONS
# ============================================================

# Supported latent distribution families
DistributionType = Literal[
    "normal",
    "skewed",
    "uniform",
    "lognormal",
    "beta",
]

LikertScaleType = Literal[
    "discrete_likert"
]


# ============================================================
# STRUCTURAL MODEL CONFIGURATION
# ============================================================

@dataclass
class PathConfig:
    """
    Represents a single structural path:
        target = β * source + error
    """
    source: str
    target: str
    beta: float

    def __post_init__(self):
        self.source = str(self.source).strip()
        self.target = str(self.target).strip()
        if self.source == "" or self.target == "":
            raise ValueError("Structural path cannot have empty source/target.")
        if self.source == self.target:
            raise ValueError(f"Invalid path: {self.source} → {self.target} (same construct).")


@dataclass
class StructuralConfig:
    """
    Container for structural model:
        - list of PathConfig objects
        - optional R² targets for endogenous constructs
    """
    paths: List[PathConfig] = field(default_factory=list)
    r2_targets: Dict[str, float] = field(default_factory=dict)

    def validate(self):
        # Check for duplicate paths
        seen = set()
        for p in self.paths:
            key = (p.source, p.target)
            if key in seen:
                raise ValueError(f"Duplicate structural path detected: {p.source} → {p.target}")
            seen.add(key)


# ============================================================
# MEASUREMENT MODEL CONFIGURATION
# ============================================================

@dataclass
class ConstructConfig:
    """
    Defines a reflective latent construct and its item-generation rules.
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

    def __post_init__(self):
        self.name = str(self.name).strip()
        if self.name == "":
            raise ValueError("Construct name cannot be empty.")
        if self.n_items <= 0:
            raise ValueError(f"Construct '{self.name}' must have at least one item.")

        if self.distribution not in {"normal", "skewed", "uniform", "lognormal", "beta"}:
            raise ValueError(f"Unsupported distribution type: {self.distribution}")

        # Ensure loading bounds are logical
        if not (0 < self.target_loading_min <= self.target_loading_mean <= self.target_loading_max < 1):
            raise ValueError(
                f"Invalid loading bounds for '{self.name}'. "
                "Require: 0 < min ≤ mean ≤ max < 1."
            )


# ============================================================
# SAMPLING CONFIGURATION
# ============================================================

@dataclass
class SampleConfig:
    """
    Controls sampling properties for the dataset.
    """
    n_respondents: int = 500
    likert_min: int = 1
    likert_max: int = 5
    scale_type: LikertScaleType = "discrete_likert"
    random_seed: Optional[int] = 123

    def __post_init__(self):
        if self.likert_max <= self.likert_min:
            raise ValueError("Likert max must be greater than min.")
        if self.n_respondents <= 0:
            raise ValueError("Sample size must be positive.")


# ============================================================
# DEMOGRAPHIC CONFIGURATION
# ============================================================

@dataclass
class DemographicConfig:
    add_demographics: bool = True


# ============================================================
# RESPONSE BIAS CONFIGURATION
# ============================================================

@dataclass
class BiasConfig:
    careless_rate: float = 0.0
    straightlining_rate: float = 0.0
    random_response_rate: float = 0.0
    acquiescence_level: float = 0.0
    midpoint_bias_level: float = 0.0
    extreme_bias_level: float = 0.0

    def validate(self):
        for name, val in self.__dict__.items():
            if not isinstance(val, (int, float)):
                raise ValueError(f"Bias parameter '{name}' must be numeric.")
            if abs(val) > 5:
                raise ValueError(f"Bias parameter '{name}' has unrealistic magnitude: {val}")


# ============================================================
# GLOBAL MODEL CONFIGURATION
# ============================================================

@dataclass
class ModelConfig:
    """
    High-level configuration object controlling the entire data-generation pipeline.
    """
    project_name: str
    researcher_name: str

    constructs: List[ConstructConfig]

    sample: SampleConfig = field(default_factory=SampleConfig)
    demographics: DemographicConfig = field(default_factory=DemographicConfig)
    bias: BiasConfig = field(default_factory=BiasConfig)

    structural: StructuralConfig = field(
        default_factory=lambda: StructuralConfig(paths=[], r2_targets={})
    )

    metadata: Dict[str, str] = field(default_factory=dict)

    def validate(self):
        """
        Validates all subcomponents for safe dataset generation.
        """
        # Validate constructs
        names = set()
        for c in self.constructs:
            if c.name in names:
                raise ValueError(f"Duplicate construct name detected: '{c.name}'")
            names.add(c.name)

        # Validate structural model
        self.structural.validate()

        # Validate bias parameters
        self.bias.validate()

        # Sample validation already done in SampleConfig


    def describe(self) -> Dict[str, object]:
        """
        Returns a clean serializable summary for debugging or export.
        """
        return {
            "project_name": self.project_name,
            "researcher": self.researcher_name,
            "n_constructs": len(self.constructs),
            "construct_names": [c.name for c in self.constructs],
            "n_respondents": self.sample.n_respondents,
            "likert_range": (self.sample.likert_min, self.sample.likert_max),
            "structural_paths": [(p.source, p.target, p.beta) for p in self.structural.paths],
            "r2_targets": self.structural.r2_targets,
            "has_demographics": self.demographics.add_demographics,
            "bias_settings": self.bias.__dict__,
            "metadata": self.metadata,
        }
