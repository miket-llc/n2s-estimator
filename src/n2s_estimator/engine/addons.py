"""Add-on packages calculation engine for Integrations and Reports."""


from .datatypes import (
    AddOnPackage,
    ConfigurationData,
    EstimationInputs,
    RoleHours,
    StageHours,
)
from .pricing import PricingEngine


class AddOnEngine:
    """Handles add-on package calculations for Integrations and Reports."""

    def __init__(self, config: ConfigurationData, pricing_engine: PricingEngine) -> None:
        """Initialize add-on engine with configuration and pricing engine."""
        self.config = config
        self.pricing_engine = pricing_engine
        self._package_cache: dict[str, AddOnPackage] = {}
        self._build_cache()

    def _build_cache(self) -> None:
        """Build package lookup cache."""
        for package in self.config.addon_packages:
            self._package_cache[package.name] = package

    def calculate_integrations(self, inputs: EstimationInputs) -> tuple[StageHours, list[RoleHours]]:
        """
        Calculate Integrations add-on package.
        
        Pipeline:
        1. Compute hours: count * sum(tier_mix[tier] * unit_hours[tier])
        2. Explode to roles via tier's role % (sum 1.0)
        3. Apply same delivery mix & rates as base package
        """
        if not inputs.include_integrations or inputs.integrations_count <= 0:
            return self._empty_stage_hours(), []

        package = self._package_cache.get('Integrations')
        if not package:
            return self._empty_stage_hours(), []

        # Calculate total hours by tier
        tier_hours = {}
        tier_mixes = {
            'Simple': inputs.integrations_simple_pct,
            'Standard': inputs.integrations_standard_pct,
            'Complex': inputs.integrations_complex_pct
        }

        total_hours = 0.0
        role_hours_dict: dict[str, float] = {}

        for tier in package.tiers:
            tier_mix = tier_mixes.get(tier.name, 0.0)
            tier_total_hours = inputs.integrations_count * tier_mix * tier.unit_hours
            tier_hours[tier.name] = tier_total_hours
            total_hours += tier_total_hours

            # Distribute tier hours to roles
            for role, role_pct in tier.role_distribution.items():
                tier_role_hours = tier_total_hours * role_pct
                role_hours_dict[role] = role_hours_dict.get(role, 0.0) + tier_role_hours

        # Create StageHours (treat as single "Integrations" stage)
        stage_hours = StageHours(
            stage_hours={'Integrations': total_hours},
            presales_hours={'Integrations': 0.0},  # Add-ons are all delivery
            delivery_hours={'Integrations': total_hours}
        )

        # Convert to RoleHours with pricing
        role_hours_list = self._create_role_hours(
            role_hours_dict,
            'Integrations',
            inputs
        )

        return stage_hours, role_hours_list

    def calculate_reports(self, inputs: EstimationInputs) -> tuple[StageHours, list[RoleHours]]:
        """
        Calculate Reports add-on package.
        
        Same pipeline as integrations but for Reports package.
        """
        if not inputs.include_reports or inputs.reports_count <= 0:
            return self._empty_stage_hours(), []

        package = self._package_cache.get('Reports')
        if not package:
            return self._empty_stage_hours(), []

        # Calculate total hours by tier
        tier_hours = {}
        tier_mixes = {
            'Simple': inputs.reports_simple_pct,
            'Standard': inputs.reports_standard_pct,
            'Complex': inputs.reports_complex_pct
        }

        total_hours = 0.0
        role_hours_dict: dict[str, float] = {}

        for tier in package.tiers:
            tier_mix = tier_mixes.get(tier.name, 0.0)
            tier_total_hours = inputs.reports_count * tier_mix * tier.unit_hours
            tier_hours[tier.name] = tier_total_hours
            total_hours += tier_total_hours

            # Distribute tier hours to roles
            for role, role_pct in tier.role_distribution.items():
                tier_role_hours = tier_total_hours * role_pct
                role_hours_dict[role] = role_hours_dict.get(role, 0.0) + tier_role_hours

        # Create StageHours (treat as single "Reports" stage)
        stage_hours = StageHours(
            stage_hours={'Reports': total_hours},
            presales_hours={'Reports': 0.0},  # Add-ons are all delivery
            delivery_hours={'Reports': total_hours}
        )

        # Convert to RoleHours with pricing
        role_hours_list = self._create_role_hours(
            role_hours_dict,
            'Reports',
            inputs
        )

        return stage_hours, role_hours_list

    def _create_role_hours(
        self,
        role_hours_dict: dict[str, float],
        stage: str,
        inputs: EstimationInputs
    ) -> list[RoleHours]:
        """Convert role hours dictionary to RoleHours objects with pricing."""
        role_hours_list = []

        # Get enabled roles for the product
        enabled_roles = self.pricing_engine._get_enabled_roles(inputs.product)

        for role, hours in role_hours_dict.items():
            if role not in enabled_roles or hours <= 0:
                continue

            # Apply product multiplier
            product_multiplier = self.pricing_engine._get_product_multiplier(inputs.product, role)
            total_hours = hours * product_multiplier

            if total_hours <= 0:
                continue

            # Apply delivery split
            delivery_split = self.pricing_engine._get_delivery_split(role)

            onshore_hours = total_hours * delivery_split.onshore_pct
            offshore_hours = total_hours * delivery_split.offshore_pct
            partner_hours = total_hours * delivery_split.partner_pct

            # Get rates
            rates = self.pricing_engine._get_rates(role, inputs.locale)

            # Calculate costs
            onshore_cost = onshore_hours * rates.onshore
            offshore_cost = offshore_hours * rates.offshore
            partner_cost = partner_hours * rates.partner
            total_cost = onshore_cost + offshore_cost + partner_cost

            # Calculate blended rate
            blended_rate = total_cost / total_hours if total_hours > 0 else 0.0

            role_hours_list.append(RoleHours(
                role=role,
                stage=stage,
                total_hours=total_hours,
                onshore_hours=onshore_hours,
                offshore_hours=offshore_hours,
                partner_hours=partner_hours,
                onshore_cost=onshore_cost,
                offshore_cost=offshore_cost,
                partner_cost=partner_cost,
                total_cost=total_cost,
                blended_rate=blended_rate
            ))

        return sorted(role_hours_list, key=lambda x: x.total_cost, reverse=True)

    def _empty_stage_hours(self) -> StageHours:
        """Return empty StageHours for disabled add-ons."""
        return StageHours(
            stage_hours={},
            presales_hours={},
            delivery_hours={}
        )

    def get_tier_breakdown(
        self,
        package_name: str,
        inputs: EstimationInputs
    ) -> dict[str, dict[str, float]]:
        """Get detailed tier breakdown for a package."""
        package = self._package_cache.get(package_name)
        if not package:
            return {}

        if package_name == 'Integrations':
            count = inputs.integrations_count
            tier_mixes = {
                'Simple': inputs.integrations_simple_pct,
                'Standard': inputs.integrations_standard_pct,
                'Complex': inputs.integrations_complex_pct
            }
            enabled = inputs.include_integrations
        elif package_name == 'Reports':
            count = inputs.reports_count
            tier_mixes = {
                'Simple': inputs.reports_simple_pct,
                'Standard': inputs.reports_standard_pct,
                'Complex': inputs.reports_complex_pct
            }
            enabled = inputs.include_reports
        else:
            return {}

        if not enabled or count <= 0:
            return {}

        breakdown = {}
        for tier in package.tiers:
            tier_mix = tier_mixes.get(tier.name, 0.0)
            tier_count = count * tier_mix
            tier_total_hours = tier_count * tier.unit_hours

            breakdown[tier.name] = {
                'count': tier_count,
                'unit_hours': tier.unit_hours,
                'total_hours': tier_total_hours,
                'mix_percentage': tier_mix
            }

        return breakdown

    def validate_expected_addon_totals(self, inputs: EstimationInputs) -> dict[str, float]:
        """
        Validate add-on calculations against expected totals.
        
        Expected with defaults:
        - Integrations (30; 60/30/10; 80/160/320): 3,840 hours
        - Reports (40; 50/35/15; 24/72/160): 2,448 hours
        """
        results = {}

        # Integrations expected calculation:
        # 30 * (0.6 * 80 + 0.3 * 160 + 0.1 * 320) = 30 * (48 + 48 + 32) = 30 * 128 = 3,840
        integrations_expected = (
            inputs.integrations_count * (
                inputs.integrations_simple_pct * 80 +
                inputs.integrations_standard_pct * 160 +
                inputs.integrations_complex_pct * 320
            )
        )
        results['integrations_expected'] = integrations_expected

        # Reports expected calculation:
        # 40 * (0.5 * 24 + 0.35 * 72 + 0.15 * 160) = 40 * (12 + 25.2 + 24) = 40 * 61.2 = 2,448
        reports_expected = (
            inputs.reports_count * (
                inputs.reports_simple_pct * 24 +
                inputs.reports_standard_pct * 72 +
                inputs.reports_complex_pct * 160
            )
        )
        results['reports_expected'] = reports_expected

        return results

