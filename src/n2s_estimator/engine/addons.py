"""Add-on packages calculation engine for Integrations and Reports."""


from typing import Dict, List, Optional, Tuple

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
        self._package_cache: Dict[str, AddOnPackage] = {}
        self._build_cache()

    def _build_cache(self) -> None:
        """Build package lookup cache."""
        for package in self.config.addon_packages:
            self._package_cache[package.name] = package

    def _calculate_package(
        self,
        package_name: str,
        count: int,
        tier_mix: Optional[Dict[str, float]],
        inputs: EstimationInputs,
    ) -> Tuple[StageHours, List[RoleHours]]:
        """
        Generic add-on package calculation.
        
        Args:
            package_name: Name of the package to calculate
            count: Number of items
            tier_mix: Mix percentages by tier name (None for single tier)
            inputs: Estimation inputs for size scaling
            
        Returns:
            Tuple of (StageHours, List[RoleHours])
        """
        if count <= 0:
            return self._empty_stage_hours(), []

        package = self._package_cache.get(package_name)
        if not package:
            return self._empty_stage_hours(), []

        # Calculate total hours by tier
        tier_hours = {}
        
        for tier in package.tiers:
            if tier_mix:
                mix = tier_mix.get(tier.name, 0.0)
            else:
                mix = 1.0  # Single tier case
            
            hours = count * mix * tier.unit_hours
            
            # Apply size scaling if enabled for this specific tier
            if tier.scale_by_size:
                size_multiplier = self.config.size_multipliers.get(inputs.size_band, 1.0)
                hours *= size_multiplier
                
            tier_hours[tier.name] = hours

        # Distribute hours to roles
        role_hours_dict = {}
        for tier in package.tiers:
            if tier_hours.get(tier.name, 0) > 0:
                for role, role_pct in tier.role_distribution.items():
                    role_hours = tier_hours[tier.name] * role_pct
                    if role in role_hours_dict:
                        role_hours_dict[role] += role_hours
                    else:
                        role_hours_dict[role] = role_hours

        # Create stage hours (all delivery, no presales for add-ons)
        total_hours = sum(role_hours_dict.values())
        stage_hours = StageHours(
            stage_hours={package_name: total_hours},
            presales_hours={package_name: 0.0},
            delivery_hours={package_name: total_hours}
        )

        # Convert to RoleHours via pricing engine
        role_hours_list = self._create_role_hours(
            role_hours_dict,
            package_name,
            inputs
        )

        return stage_hours, role_hours_list

    def calculate_integrations(self, inputs: EstimationInputs) -> Tuple[StageHours, List[RoleHours]]:
        """Calculate Integrations add-on package."""
        if not inputs.include_integrations:
            return self._empty_stage_hours(), []

        tier_mix = {
            'Simple': inputs.integrations_simple_pct,
            'Standard': inputs.integrations_standard_pct,
            'Complex': inputs.integrations_complex_pct
        }

        return self._calculate_package(
            package_name='Integrations',
            count=inputs.integrations_count,
            tier_mix=tier_mix,
            inputs=inputs
        )

    def calculate_reports(self, inputs: EstimationInputs) -> Tuple[StageHours, List[RoleHours]]:
        """Calculate Reports add-on package."""
        if not inputs.include_reports:
            return self._empty_stage_hours(), []

        tier_mix = {
            'Simple': inputs.reports_simple_pct,
            'Standard': inputs.reports_standard_pct,
            'Complex': inputs.reports_complex_pct
        }

        return self._calculate_package(
            package_name='Reports',
            count=inputs.reports_count,
            tier_mix=tier_mix,
            inputs=inputs
        )

    def calculate_degreeworks(self, inputs: EstimationInputs) -> Tuple[StageHours, List[RoleHours]]:
        """
        Calculate Degree Works as sum of:
        - Setup (size-scaled if the 'Setup' tier has scale_by_size=True)
        - PVEs by complexity tiers using calculator or direct PVE count.
        
        Returns StageHours with two entries:
        'Degree Works – Setup' and 'Degree Works – PVEs'
        and combined RoleHours list for the DW package.
        """
        if not inputs.include_degreeworks:
            return self._empty_stage_hours(), []

        package = self._package_cache.get('Degree Works')
        if not package:
            return self._empty_stage_hours(), []

        # Calculate PVE count using calculator or direct input
        if inputs.degreeworks_use_pve_calculator:
            pve_count = (
                inputs.degreeworks_majors + 
                0.5 * (inputs.degreeworks_minors + inputs.degreeworks_certificates + inputs.degreeworks_concentrations)
            ) * inputs.degreeworks_catalog_years
        else:
            pve_count = inputs.degreeworks_pve_count

        # Separate Setup and PVE calculations
        setup_hours_dict = {}
        pve_hours_dict = {}
        stage_hours_dict = {}

        for tier in package.tiers:
            if tier.name.lower() == 'setup':
                if inputs.degreeworks_include_setup:
                    setup_hours = 1 * tier.unit_hours  # Setup is always count=1
                    
                    # Apply size scaling if enabled for Setup tier
                    if tier.scale_by_size:
                        size_multiplier = self.config.size_multipliers.get(inputs.size_band, 1.0)
                        setup_hours *= size_multiplier
                    
                    # Distribute to roles
                    for role, role_pct in tier.role_distribution.items():
                        role_hours = setup_hours * role_pct
                        if role in setup_hours_dict:
                            setup_hours_dict[role] += role_hours
                        else:
                            setup_hours_dict[role] = role_hours
                    
                    stage_hours_dict['Degree Works – Setup'] = setup_hours

            elif tier.name.lower().startswith('pve'):
                if pve_count > 0:
                    # Determine mix from inputs based on tier name
                    if 'simple' in tier.name.lower():
                        mix = inputs.degreeworks_simple_pct
                    elif 'standard' in tier.name.lower():
                        mix = inputs.degreeworks_standard_pct
                    elif 'complex' in tier.name.lower():
                        mix = inputs.degreeworks_complex_pct
                    else:
                        mix = 0.0  # Unknown tier

                    tier_total_hours = pve_count * mix * tier.unit_hours
                    # Note: PVE tiers are NOT size-scaled per requirements
                    
                    # Distribute to roles
                    for role, role_pct in tier.role_distribution.items():
                        role_hours = tier_total_hours * role_pct
                        if role in pve_hours_dict:
                            pve_hours_dict[role] += role_hours
                        else:
                            pve_hours_dict[role] = role_hours

        # Calculate total PVE hours
        total_pve_hours = sum(pve_hours_dict.values())
        if total_pve_hours > 0:
            stage_hours_dict['Degree Works – PVEs'] = total_pve_hours

        # Apply Degree Works cap if enabled
        total_setup_hours = stage_hours_dict.get('Degree Works – Setup', 0.0)
        cap_map = self.config.addon_caps.get("Degree Works", {})
        size_cap = cap_map.get(inputs.size_band, None)

        # Allow UI override if provided
        cap_enabled = getattr(inputs, "degreeworks_cap_enabled", True)
        cap_value = getattr(inputs, "degreeworks_cap_hours", None) or size_cap

        if cap_enabled and cap_value:
            allowance_for_pve = max(cap_value - total_setup_hours, 0.0)
            if total_pve_hours > allowance_for_pve:
                ratio = (allowance_for_pve / total_pve_hours) if total_pve_hours > 0 else 0.0
                # scale down each PVE role
                for role in list(pve_hours_dict.keys()):
                    pve_hours_dict[role] *= ratio
                # replace PVEs stage hours
                total_pve_hours = sum(pve_hours_dict.values())
                stage_hours_dict['Degree Works – PVEs'] = total_pve_hours

        # Combine role hours from Setup and PVEs
        combined_role_hours_dict = {}
        for role, hours in setup_hours_dict.items():
            combined_role_hours_dict[role] = combined_role_hours_dict.get(role, 0.0) + hours
        for role, hours in pve_hours_dict.items():
            combined_role_hours_dict[role] = combined_role_hours_dict.get(role, 0.0) + hours

        # Create StageHours with both Setup and PVEs
        total_setup_hours = stage_hours_dict.get('Degree Works – Setup', 0.0)
        total_pve_hours = stage_hours_dict.get('Degree Works – PVEs', 0.0)
        
        stage_hours = StageHours(
            stage_hours=stage_hours_dict,
            presales_hours={
                'Degree Works – Setup': 0.0,
                'Degree Works – PVEs': 0.0
            },
            delivery_hours={
                'Degree Works – Setup': total_setup_hours,
                'Degree Works – PVEs': total_pve_hours
            }
        )

        # Convert combined role hours to RoleHours objects
        role_hours_list = []
        for role, hours in combined_role_hours_dict.items():
            if hours > 0:
                # Use 'Degree Works' as stage name for pricing
                role_hour = self._create_role_hours(
                    {role: hours}, 
                    'Degree Works', 
                    inputs
                )[0] if self._create_role_hours({role: hours}, 'Degree Works', inputs) else None
                if role_hour:
                    role_hours_list.append(role_hour)

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
        elif package_name == 'Degree Works':
            # Calculate PVE count
            if inputs.degreeworks_use_pve_calculator:
                pve_count = (
                    inputs.degreeworks_majors + 
                    0.5 * (inputs.degreeworks_minors + inputs.degreeworks_certificates + inputs.degreeworks_concentrations)
                ) * inputs.degreeworks_catalog_years
            else:
                pve_count = inputs.degreeworks_pve_count
            
            # Setup tier mix
            tier_mixes = {}
            if inputs.degreeworks_include_setup:
                tier_mixes['Setup'] = 1.0  # Always 100% when included
            
            # PVE tier mixes
            if pve_count > 0:
                tier_mixes['PVE Simple'] = inputs.degreeworks_simple_pct
                tier_mixes['PVE Standard'] = inputs.degreeworks_standard_pct
                tier_mixes['PVE Complex'] = inputs.degreeworks_complex_pct
            
            enabled = inputs.include_degreeworks
        else:
            return {}

        if not enabled:
            return {}

        # Special handling for Degree Works vs other packages
        if package_name == 'Degree Works':
            if not (inputs.degreeworks_include_setup or pve_count > 0):
                return {}
        elif count <= 0:
            return {}

        breakdown = {}
        for tier in package.tiers:
            tier_mix = tier_mixes.get(tier.name, 0.0)
            
            if package_name == 'Degree Works':
                # Special logic for Degree Works tiers
                if tier.name.lower() == 'setup':
                    tier_count = 1 if inputs.degreeworks_include_setup else 0
                    tier_total_hours = tier_count * tier.unit_hours
                elif tier.name.lower().startswith('pve'):
                    tier_count = pve_count * tier_mix
                    tier_total_hours = tier_count * tier.unit_hours
                else:
                    tier_count = 0
                    tier_total_hours = 0
            else:
                # Regular package logic
                tier_count = count * tier_mix
                tier_total_hours = tier_count * tier.unit_hours
            
            # Apply per-tier size scaling
            if tier.scale_by_size:
                size_multiplier = self.config.size_multipliers.get(inputs.size_band, 1.0)
                tier_total_hours *= size_multiplier

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

