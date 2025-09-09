"""Data models for N2S Estimator configuration and calculations."""

from typing import Optional, Union, List, Dict
from pydantic import BaseModel, Field, validator


class StageWeight(BaseModel):
    """Stage weight configuration."""
    phase: str
    stage: str
    weight: float = Field(ge=0.0, le=1.0)


class StagePresales(BaseModel):
    """Stage default presales percentage."""
    stage: str
    default_pct: float = Field(ge=0.0, le=1.0)


class ActivityDef(BaseModel):
    """Activity definition within a stage."""
    stage: str
    activity: str
    weight: float = Field(gt=0.0)
    is_presales: bool


class RoleMix(BaseModel):
    """Role mix percentage for a stage."""
    stage: str
    role: str
    pct: float = Field(ge=0.0, le=1.0)


class RateCard(BaseModel):
    """Rate card for a role and locale."""
    role: str
    locale: str
    onshore: float = Field(gt=0.0)
    offshore: float = Field(gt=0.0)
    partner: float = Field(gt=0.0)


class DeliveryMix(BaseModel):
    """Delivery mix percentages (global or per-role override)."""
    role: Optional[str] = None  # None = global
    onshore_pct: float = Field(ge=0.0, le=1.0)
    offshore_pct: float = Field(ge=0.0, le=1.0)
    partner_pct: float = Field(ge=0.0, le=1.0)

    @validator('partner_pct')
    def validate_percentages_sum_to_one(cls, v: float, values: dict) -> float:
        """Validate that the three percentages sum to 1.0."""
        onshore = values.get('onshore_pct', 0.0)
        offshore = values.get('offshore_pct', 0.0)
        total = onshore + offshore + v
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Delivery mix percentages must sum to 1.0, got {total}")
        return v


class AddOnTier(BaseModel):
    """Add-on tier definition with role distribution."""
    name: str
    unit_hours: float = Field(gt=0.0)
    role_distribution: Dict[str, float] = Field(...)
    scale_by_size: bool = Field(default=False)

    @validator('role_distribution')
    def validate_role_distribution_sum(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate that role percentages sum to 1.0."""
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Role distribution must sum to 1.0, got {total}")
        return v


class AddOnPackage(BaseModel):
    """Add-on package with multiple tiers."""
    name: str
    tiers: List[AddOnTier]
    scale_by_size: bool = Field(default=False)


class RoleAlias(BaseModel):
    """Role alias mapping for canonicalization."""
    alias: str
    canonical_role: str


class ProductRoleToggle(BaseModel):
    """Product-specific role enablement and multipliers."""
    role: str
    banner_enabled: bool
    colleague_enabled: bool
    multiplier: float = Field(default=1.0, ge=0.0)


class EstimationInputs(BaseModel):
    """User inputs for estimation."""
    product: str = Field(default="Banner")
    delivery_type: str = Field(default="Net New")
    size_band: str = Field(default="Medium")
    locale: str = Field(default="US")
    maturity_factor: float = Field(default=1.0, ge=0.5, le=2.0)
    integrations_count: int = Field(default=30, ge=0)
    integrations_simple_pct: float = Field(default=0.60, ge=0.0, le=1.0)
    integrations_standard_pct: float = Field(default=0.30, ge=0.0, le=1.0)
    integrations_complex_pct: float = Field(default=0.10, ge=0.0, le=1.0)
    reports_count: int = Field(default=40, ge=0)
    reports_simple_pct: float = Field(default=0.50, ge=0.0, le=1.0)
    reports_standard_pct: float = Field(default=0.35, ge=0.0, le=1.0)
    reports_complex_pct: float = Field(default=0.15, ge=0.0, le=1.0)
    include_integrations: bool = Field(default=False)
    include_reports: bool = Field(default=False)
    include_degreeworks: bool = Field(default=False)
    degreeworks_include_setup: bool = Field(default=True)
    degreeworks_use_pve_calculator: bool = Field(default=True)
    # Calculator inputs
    degreeworks_majors: int = Field(default=0, ge=0)
    degreeworks_minors: int = Field(default=0, ge=0)
    degreeworks_certificates: int = Field(default=0, ge=0)
    degreeworks_concentrations: int = Field(default=0, ge=0)
    degreeworks_catalog_years: int = Field(default=1, ge=1)
    # Direct override when calculator off
    degreeworks_pve_count: int = Field(default=0, ge=0)
    # Tier mix for PVEs
    degreeworks_simple_pct: float = Field(default=0.50, ge=0.0, le=1.0)
    degreeworks_standard_pct: float = Field(default=0.35, ge=0.0, le=1.0)
    degreeworks_complex_pct: float = Field(default=0.15, ge=0.0, le=1.0)

    @validator('integrations_complex_pct')
    def validate_integrations_mix(cls, v: float, values: dict) -> float:
        """Validate integration tier mix sums to 1.0."""
        simple = values.get('integrations_simple_pct', 0.0)
        standard = values.get('integrations_standard_pct', 0.0)
        total = simple + standard + v
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Integration tier mix must sum to 1.0, got {total}")
        return v

    @validator('reports_complex_pct')
    def validate_reports_mix(cls, v: float, values: dict) -> float:
        """Validate reports tier mix sums to 1.0."""
        simple = values.get('reports_simple_pct', 0.0)
        standard = values.get('reports_standard_pct', 0.0)
        total = simple + standard + v
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Reports tier mix must sum to 1.0, got {total}")
        return v

    @validator('degreeworks_complex_pct')
    def validate_degreeworks_mix(cls, v: float, values: dict) -> float:
        """Validate Degree Works PVE tier mix sums to 1.0."""
        simple = values.get('degreeworks_simple_pct', 0.0)
        standard = values.get('degreeworks_standard_pct', 0.0)
        total = simple + standard + v
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Degree Works PVE tier mix must sum to 1.0, got {total}")
        return v


class StageHours(BaseModel):
    """Hours breakdown by stage."""
    stage_hours: Dict[str, float]
    presales_hours: Dict[str, float]
    delivery_hours: Dict[str, float]


class RoleHours(BaseModel):
    """Hours breakdown by role and delivery split."""
    role: str
    stage: str
    total_hours: float
    onshore_hours: float
    offshore_hours: float
    partner_hours: float
    onshore_cost: float
    offshore_cost: float
    partner_cost: float
    total_cost: float
    blended_rate: float


class EstimationResults(BaseModel):
    """Complete estimation results."""
    inputs: EstimationInputs
    base_n2s: StageHours
    base_role_hours: List[RoleHours]
    integrations_hours: Optional[StageHours] = None
    integrations_role_hours: Optional[List[RoleHours]] = None
    reports_hours: Optional[StageHours] = None
    reports_role_hours: Optional[List[RoleHours]] = None
    degreeworks_hours: Optional[StageHours] = None
    degreeworks_role_hours: Optional[List[RoleHours]] = None
    total_presales_hours: float
    total_delivery_hours: float
    total_presales_cost: float
    total_delivery_cost: float
    total_hours: float
    total_cost: float


class ConfigurationData(BaseModel):
    """Complete configuration data loaded from workbook."""
    baseline_hours: float
    stage_weights: List[StageWeight]
    stages_presales: List[StagePresales]
    activities: List[ActivityDef]
    role_mix: List[RoleMix]
    rates: List[RateCard]
    delivery_mix: List[DeliveryMix]
    addon_packages: List[AddOnPackage]
    product_role_map: List[ProductRoleToggle]
    role_aliases: List[RoleAlias] = Field(default_factory=list)
    size_multipliers: Dict[str, float] = Field(default={
        "Small": 0.85,
        "Medium": 1.00,
        "Large": 1.25,
        "Very Large": 1.50
    })
    delivery_type_multipliers: Dict[str, float] = Field(default={
        "Modernization": 0.90,
        "Net New": 1.00
    })
