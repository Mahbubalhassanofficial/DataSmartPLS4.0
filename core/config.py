"""
core/config.py
--------------
Central configuration dataclasses for DataSmartPLS 4.0.
Enhanced version with deeper validation and safeguards.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict


# ============================================================
# BASIC TYPE DEFINITIONS
# ============================================================

DistributionType = Literal[
    "normal",
    "skewed",
    "uniform",
    "lognormal",
    "beta",
]

LikertScaleType = Literal["discrete_likert"]


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

        if not self.source or not self.target:
            raise ValueError("Structural path cannot have empty source or target.")

        if self.source == self.target:
            raise ValueError(f"Invalid path: {self.source} → {self.target} (self-loop).")

        if not isinstance(self.beta, (int, float)):
            raise ValueError("Beta coefficient must be numeric.")


@dataclass
class StructuralConfig:
    """Container for structural model settings."""
    paths: List[PathConfig] = field(default_factory=list)
    r2_targets: Dict[str, float] = field(default_factory=dict)

    # ------------------------
    def validate(self, construct_names: List[str]):
        """Validate structural model integrity."""
        seen = set()

        # Duplicate path prevention
        for p in self.paths:
            key = (p.source, p.target)
            if key in seen:
                raise ValueError(f"Duplicate path: {p.source} → {p.target}")
            seen.add(key)

            # Construct existence check
            if p.source not in construct_names:
                raise ValueError(f"Structural path source '{p.source}' not defined as a construct.")
            if p.target not in construct_names:
                raise ValueError(f"Structural path target '{p.target}' not defined as a construct.")

        # R² validation
        for cons, val in self.r2_targets.items():
            if cons not in construct_names:
                raise ValueError(f"R² target set for unknown construct '{cons}'.")
            if not (0 <= val < 1):
                raise ValueError(f"R² for {cons} must be between 0 and 1.")

        # Detect circular loops
        self._check_cycles()

    # ------------------------
    def _check_cycles(self):
        """Detect circular dependencies (e.g., PE→EE→PE)."""
        graph = {}
        for p in self.paths:
            graph.setdefault(p.source, []).append(p.target)

        visited = set()
        stack = set()

        def dfs(node):
            if node in stack:
                raise ValueError(f"Circular dependency detected involving '{node}'.")
            if node in visited:
                return
            visited.add(node)
            stack.add(node)
            for nxt in graph.get(node, []):
                dfs(nxt)
            stack.remove(node)

        for node in graph:
            dfs(node)


# ============================================================
# MEASUREMENT MODEL CONFIGURATION
# ============================================================

@dataclass
class ConstructConfig:
    """Defines reflective construct + indicator generation rules."""
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
        if not self.name:
            raise ValueError("Construct name cannot be empty.")
        if self.n_items <= 0:
            raise ValueError(f"Construct '{self.name}' must have at least one item.")

        if self.distribution not in {"normal", "skewed", "uniform", "lognormal", "beta"}:
            raise ValueError(f"Unsupported distribution type: {self.distribution}")

        # Loading bounds
        if not (0 < self.target_loading_min <= self.target_loading_mean <= self.target_loading_max < 1):
            raise ValueError(f"Invalid loading bounds for '{self.name}'.")

        # Skew/kurtosis realism bounds
        if abs(self.skew) > 5:
            raise ValueError(f"Unrealistic skew for construct '{self.name}'.")
        if not (1 <= self.kurtosis <= 50):
            raise ValueError(f"Unrealistic kurtosis for construct '{self.name}'.")

        # Reverse-coded items limit
        if self.reverse_items > self.n_items:
            raise ValueError(f"Reverse items exceed total items in construct '{self.name}'.")


# ============================================================
# SAMPLING CONFIGURATION
# ============================================================

@dataclass
class SampleConfig:
    n_respondents: int = 500
    likert_min: int = 1
    likert_max: int = 5
    scale_type: LikertScaleType = "discrete_likert"
    random_seed: Optional[int] = 123

    def __post_init__(self):
        if self.n_respondents <= 0:
            raise ValueError("Sample size must be positive.")
        if self.likert_max <= self.likert_min:
            raise ValueError("Likert max must be greater than min.")


# ============================================================
# DEMOGRAPHIC CONFIG
# ============================================================

@dataclass
class DemographicConfig:
    add_demographics: bool = True


# ============================================================
# RESPONSE BIAS CONFIG
# ============================================================

@dataclass
class BiasConfig:
    careless_rate: float = 0.0
    straightlining_rate: float = 0.0
    random_response_rate: float = 0.0
    acquiescence_level: float = 0.0   # -1 to +1
    midpoint_bias_level: float = 0.0  # 0 to 1
    extreme_bias_level: float = 0.0   # 0 to 1
    missing_rate: float = 0.0         # 0 to 0.5

    def validate(self):
        if not (0 <= self.careless_rate <= 1):
            raise ValueError("Careless rate must be between 0 and 1.")
        if not (0 <= self.straightlining_rate <= 1):
            raise ValueError("Straightlining rate must be between 0 and 1.")
        if not (0 <= self.random_response_rate <= 1):
            raise ValueError("Random responding rate must be between 0 and 1.")
        if not (-1 <= self.acquiescence_level <= 1):
            raise ValueError("Acquiescence must be in [-1, 1].")
        if not (0 <= self.midpoint_bias_level <= 1):
            raise ValueError("Midpoint bias must be 0–1.")
        if not (0 <= self.extreme_bias_level <= 1):
            raise ValueError("Extreme bias must be 0–1.")
        if not (0 <= self.missing_rate <= 0.5):
            raise ValueError("Missing-rate must be 0–0.5.")


# ============================================================
# GLOBAL MODEL CONFIG
# ============================================================

@dataclass
class ModelConfig:
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
        # Construct name uniqueness
        names = set()
        for c in self.constructs:
            if c.name in names:
                raise ValueError(f"Duplicate construct: '{c.name}'")
            names.add(c.name)

        # Validate structural relative to constructs
        self.structural.validate(construct_names=list(names))

        # Validate bias settings
        self.bias.validate()

        return True

    def describe(self) -> Dict[str, object]:
        return {
            "project_name": self.project_name,
            "researcher": self.researcher_name,
            "constructs": [c.name for c in self.constructs],
            "n_constructs": len(self.constructs),
            "sample_size": self.sample.n_respondents,
            "likert_range": (self.sample.likert_min, self.sample.likert_max),
            "structural_paths": [(p.source, p.target, p.beta) for p in self.structural.paths],
            "r2_targets": self.structural.r2_targets,
            "demographics_enabled": self.demographics.add_demographics,
            "bias_settings": self.bias.__dict__,
        }
