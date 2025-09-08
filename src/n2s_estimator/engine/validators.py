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

            if abs(total_pct - 1.0) > 0.01:
                raise ValidationError(
                    f"Stage '{stage}' role mix sums to {total_pct:.3f}, should be 1.0"
                )

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
        """Validate that add-on tier role distributions sum to 1.0."""
        for package in self.config.addon_packages:
            for tier in package.tiers:
                total_pct = sum(tier.role_distribution.values())
                if abs(total_pct - 1.0) > 0.01:
                    raise ValidationError(
                        f"Add-on '{package.name}' tier '{tier.name}' role distribution "
                        f"sums to {total_pct:.3f}, should be 1.0"
                    )

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

    return warnings
