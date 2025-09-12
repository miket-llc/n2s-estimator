"""Validation utilities for N2S Estimator configuration and calculations."""

from .datatypes import ConfigurationData


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class MethodologyWarning(Exception):
    """Custom exception for methodology drift warnings."""
    pass


class ConfigurationValidator:
    """Validates configuration data and detects methodology drift."""

    def __init__(self, config: ConfigurationData) -> None:
        """Initialize validator with configuration data."""
        self.config = config
        self._baseline_role_mix = self._get_baseline_role_mix()

    def validate_all(self) -> list[str]:
        """Run all validations and return list of warnings/errors."""
        warnings = []

        try:
            self.validate_stage_weights()
        except ValidationError as e:
            warnings.append(f"Stage Weights Error: {e}")

        try:
            self.validate_role_mix()
        except ValidationError as e:
            warnings.append(f"Role Mix Error: {e}")

        try:
            self.validate_delivery_mix()
        except ValidationError as e:
            warnings.append(f"Delivery Mix Error: {e}")

        try:
            self.validate_addon_tiers()
        except ValidationError as e:
            warnings.append(f"Add-on Tiers Error: {e}")

        # Role coverage warnings (non-fatal)
        role_warnings = self.check_role_coverage()
        warnings.extend(role_warnings)

        # Check for methodology drift
        drift_warnings = self.check_methodology_drift()
        warnings.extend(drift_warnings)

        return warnings

    def validate_stage_weights(self) -> None:
        """Validate that stage weights sum to 1.0."""
        total_weight = sum(sw.weight for sw in self.config.stage_weights)
        if abs(total_weight - 1.0) > 0.001:
            raise ValidationError(f"Stage weights must sum to 1.0, got {total_weight}")

    def validate_role_mix(self) -> None:
        """Validate that each stage's role mix sums to 1.0."""
        stages = set(rm.stage for rm in self.config.role_mix)

        for stage in stages:
            stage_roles = [rm for rm in self.config.role_mix if rm.stage == stage]
            total_pct = sum(rm.pct for rm in stage_roles)

            # Hard error if very far off
            if abs(total_pct - 1.0) > 0.05:
                raise ValidationError(
                    f"Stage '{stage}' role mix sums to {total_pct:.3f}, should be 1.0"
                )
            # Warning will be handled in check_role_coverage for smaller deviations

    def validate_delivery_mix(self) -> None:
        """Validate that delivery mix percentages sum to 1.0."""
        for dm in self.config.delivery_mix:
            total_pct = dm.onshore_pct + dm.offshore_pct + dm.partner_pct
            if abs(total_pct - 1.0) > 0.001:
                role_desc = f"role '{dm.role}'" if dm.role else "global"
                raise ValidationError(
                    f"Delivery mix for {role_desc} sums to {total_pct:.3f}, should be 1.0"
                )

    def validate_addon_tiers(self) -> None:
        """Validate that add-on tier role distributions sum to 1.0, including Degree Works."""
        for package in self.config.addon_packages:
            for tier in package.tiers:
                total_pct = sum(tier.role_distribution.values())
                if abs(total_pct - 1.0) > 0.01:
                    raise ValidationError(
                        f"Add-on '{package.name}' tier '{tier.name}' role distribution "
                        f"sums to {total_pct:.3f}, should be 1.0"
                    )
                
                # Special validation for Degree Works
                if package.name == 'Degree Works':
                    expected_tiers = {'Setup', 'PVE Simple', 'PVE Standard', 'PVE Complex'}
                    if tier.name not in expected_tiers:
                        raise ValidationError(
                            f"Degree Works tier '{tier.name}' not in expected tiers: {expected_tiers}"
                        )
                    
                    # Check that DegreeWorks Scribe is present and has significant allocation
                    if 'DegreeWorks Scribe' not in tier.role_distribution:
                        raise ValidationError(
                            f"Degree Works '{tier.name}' tier must include 'DegreeWorks Scribe' role"
                        )
                    
                    dw_scribe_pct = tier.role_distribution['DegreeWorks Scribe']
                    if dw_scribe_pct < 0.4:  # Should be at least 40% (Complex tier is 50%)
                        raise ValidationError(
                            f"DegreeWorks Scribe should have significant allocation in '{tier.name}', "
                            f"found {dw_scribe_pct:.1%}"
                        )


    def check_role_coverage(self) -> list[str]:
        """Check role coverage across configuration sheets and return warnings."""
        warnings = []
        
        # Collect all roles referenced in the system
        all_roles = set()
        
        # Roles from Role Mix
        role_mix_roles = {rm.role for rm in self.config.role_mix}
        all_roles.update(role_mix_roles)
        
        # Roles from Add-on packages
        addon_roles = set()
        for package in self.config.addon_packages:
            for tier in package.tiers:
                addon_roles.update(tier.role_distribution.keys())
        all_roles.update(addon_roles)
        
        # Roles from Rates
        rates_roles = {rt.role for rt in self.config.rates}
        
        # Roles from Product Role Map
        product_roles = {prm.role for prm in self.config.product_role_map}
        
        # Check for roles missing from Rates (configuration integrity)
        missing_from_rates = all_roles - rates_roles
        if missing_from_rates:
            warnings.append(
                f"Configuration warning: Roles missing from Rates sheet: {', '.join(sorted(missing_from_rates))}"
            )
        
        # Check for roles missing from Product Role Map (configuration integrity)
        missing_from_product_map = all_roles - product_roles
        if missing_from_product_map:
            warnings.append(
                f"Configuration warning: Roles missing from Product Role Map: {', '.join(sorted(missing_from_product_map))}"
            )
        
        # Check stage role mix sums for minor deviations (configuration validation)
        stages = set(rm.stage for rm in self.config.role_mix)
        for stage in stages:
            stage_roles = [rm for rm in self.config.role_mix if rm.stage == stage]
            total_pct = sum(rm.pct for rm in stage_roles)
            
            if abs(total_pct - 1.0) > 0.01:  # Warn for smaller deviations
                warnings.append(
                    f"Configuration warning: Stage '{stage}' role mix sums to {total_pct:.3f}, should be 1.0 (will be auto-normalized)"
                )
        
        return warnings

    def check_methodology_drift(self, threshold: float = 0.10) -> list[str]:
        """Check for methodology drift in role mix distributions."""
        warnings = []

        current_role_mix = self._get_current_role_mix()

        for stage, baseline_mix in self._baseline_role_mix.items():
            current_mix = current_role_mix.get(stage, {})

            for role, baseline_pct in baseline_mix.items():
                current_pct = current_mix.get(role, 0.0)
                drift = abs(current_pct - baseline_pct)

                if drift > threshold:
                    warnings.append(
                        f"Methodology drift warning: Stage '{stage}', Role '{role}' "
                        f"changed from {baseline_pct:.1%} to {current_pct:.1%} "
                        f"(drift: {drift:.1%}). You're changing the method, not just the estimate."
                    )

        return warnings

    def _get_baseline_role_mix(self) -> dict[str, dict[str, float]]:
        """Get baseline role mix from configuration (used as reference)."""
        # For now, use the current configuration as baseline
        # In a real implementation, this might come from a separate baseline file
        return self._get_current_role_mix()

    def _get_current_role_mix(self) -> dict[str, dict[str, float]]:
        """Get current role mix organized by stage and role."""
        role_mix_dict: dict[str, dict[str, float]] = {}

        for rm in self.config.role_mix:
            if rm.stage not in role_mix_dict:
                role_mix_dict[rm.stage] = {}
            role_mix_dict[rm.stage][rm.role] = rm.pct

        return role_mix_dict


def validate_estimation_inputs(inputs: 'EstimationInputs') -> list[str]:
    """Validate estimation inputs for consistency."""
    warnings = []

    # Check tier mixes sum to 1.0
    integrations_total = (
        inputs.integrations_simple_pct +
        inputs.integrations_standard_pct +
        inputs.integrations_complex_pct
    )
    if abs(integrations_total - 1.0) > 0.001:
        warnings.append(f"Integration tier mix sums to {integrations_total:.3f}, should be 1.0")

    reports_total = (
        inputs.reports_simple_pct +
        inputs.reports_standard_pct +
        inputs.reports_complex_pct
    )
    if abs(reports_total - 1.0) > 0.001:
        warnings.append(f"Reports tier mix sums to {reports_total:.3f}, should be 1.0")

    # Validate counts are reasonable
    if inputs.integrations_count > 1000:
        warnings.append(f"Integration count ({inputs.integrations_count}) seems very high")

    if inputs.reports_count > 1000:
        warnings.append(f"Reports count ({inputs.reports_count}) seems very high")

    # Check Degree Works inputs
    if inputs.include_degreeworks:
        degreeworks_total = (
            inputs.degreeworks_simple_pct +
            inputs.degreeworks_standard_pct +
            inputs.degreeworks_complex_pct
        )
        if abs(degreeworks_total - 1.0) > 0.001:
            warnings.append(f"Degree Works PVE tier mix sums to {degreeworks_total:.3f}, should be 1.0")

        # Validate PVE count logic
        if inputs.degreeworks_use_pve_calculator:
            computed_pves = (
                inputs.degreeworks_majors + 
                0.5 * (inputs.degreeworks_minors + inputs.degreeworks_certificates + inputs.degreeworks_concentrations)
            ) * inputs.degreeworks_catalog_years
            
            if computed_pves < 0:
                warnings.append("Degree Works computed PVE count cannot be negative")
            elif computed_pves == 0 and not inputs.degreeworks_include_setup:
                warnings.append("Degree Works has no Setup and 0 PVEs - nothing to calculate")
            elif computed_pves > 1000:
                warnings.append(f"Degree Works computed PVE count ({computed_pves:.1f}) seems very high")
        else:
            if inputs.degreeworks_pve_count < 0:
                warnings.append("Degree Works direct PVE count cannot be negative")
            elif inputs.degreeworks_pve_count == 0 and not inputs.degreeworks_include_setup:
                warnings.append("Degree Works has no Setup and 0 PVEs - nothing to calculate")
            elif inputs.degreeworks_pve_count > 1000:
                warnings.append(f"Degree Works direct PVE count ({inputs.degreeworks_pve_count}) seems very high")

        # Check Degree Works cap warnings
        if inputs.include_degreeworks and hasattr(inputs, 'degreeworks_cap_enabled') and inputs.degreeworks_cap_enabled:
            # This is a simplified check - in practice, we'd need access to the config to get the actual cap
            # and compute the actual setup/PVE hours to provide meaningful warnings
            cap_hours = getattr(inputs, 'degreeworks_cap_hours', None)
            if cap_hours is not None and cap_hours < 100:
                warnings.append(f"Degree Works cap ({cap_hours}h) seems very low")

    return warnings


def validate_pricing_overrides(rate_overrides: list[dict], global_mix_override: dict, role_mix_overrides: list[dict]) -> list[str]:
    """Validate pricing overrides for rates and delivery mixes."""
    warnings = []
    
    # Validate rate overrides
    for i, rate_override in enumerate(rate_overrides):
        if rate_override.get('onshore', 0) <= 0:
            warnings.append(f"Rate override {i+1}: Onshore rate must be > 0")
        if rate_override.get('offshore', 0) <= 0:
            warnings.append(f"Rate override {i+1}: Offshore rate must be > 0")
        if rate_override.get('partner', 0) <= 0:
            warnings.append(f"Rate override {i+1}: Partner rate must be > 0")
    
    # Validate global mix override
    if global_mix_override:
        onshore = global_mix_override.get('onshore_pct', 0)
        offshore = global_mix_override.get('offshore_pct', 0)
        partner = global_mix_override.get('partner_pct', 0)
        total = onshore + offshore + partner
        
        if abs(total - 1.0) > 0.001:
            warnings.append(f"Global delivery mix must sum to 1.0, got {total:.3f}")
        
        if onshore < 0 or offshore < 0 or partner < 0:
            warnings.append("Global delivery mix percentages must be >= 0")
    
    # Validate role mix overrides
    for i, role_override in enumerate(role_mix_overrides):
        onshore = role_override.get('onshore_pct', 0)
        offshore = role_override.get('offshore_pct', 0)
        partner = role_override.get('partner_pct', 0)
        total = onshore + offshore + partner
        
        if abs(total - 1.0) > 0.001:
            warnings.append(f"Role mix override {i+1} ({role_override.get('role', 'Unknown')}) must sum to 1.0, got {total:.3f}")
        
        if onshore < 0 or offshore < 0 or partner < 0:
            warnings.append(f"Role mix override {i+1} ({role_override.get('role', 'Unknown')}) percentages must be >= 0")
    
    return warnings
