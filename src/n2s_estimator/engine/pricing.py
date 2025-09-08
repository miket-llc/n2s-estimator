"""Pricing and role expansion engine for N2S Delivery Estimator."""


from .datatypes import (
    ConfigurationData,
    DeliveryMix,
    EstimationInputs,
    RateCard,
    RoleHours,
    StageHours,
)


class PricingEngine:
    """Handles role expansion, delivery splits, and cost calculations."""

    def __init__(self, config: ConfigurationData) -> None:
        """Initialize pricing engine with configuration data."""
        self.config = config
        self._rate_cache: dict[tuple[str, str], RateCard] = {}
        self._delivery_mix_cache: dict[str | None, DeliveryMix] = {}
        self._build_caches()

    def _build_caches(self) -> None:
        """Build lookup caches for rates and delivery mix."""
        # Rate cache: (role, locale) -> RateCard
        for rate in self.config.rates:
            self._rate_cache[(rate.role, rate.locale)] = rate

        # Delivery mix cache: role -> DeliveryMix
        for dm in self.config.delivery_mix:
            self._delivery_mix_cache[dm.role] = dm

    def calculate_role_hours_and_costs(
        self,
        stage_hours: StageHours,
        inputs: EstimationInputs
    ) -> list[RoleHours]:
        """
        Calculate role hours and costs for delivery hours only.
        
        Pipeline:
        1. Explode delivery hours to roles via per-stage Role Mix
        2. Apply product role map (disable/multiply roles)
        3. Apply delivery splits (global or per-role overrides)
        4. Price each split with rate card for selected locale
        """
        role_hours_list = []

        # Get enabled roles for the selected product
        enabled_roles = self._get_enabled_roles(inputs.product)

        for stage, delivery_hours in stage_hours.delivery_hours.items():
            if delivery_hours <= 0:
                continue

            # Get roles for this stage
            stage_roles = self._get_stage_roles(stage)

            for role in stage_roles:
                if role not in enabled_roles:
                    continue  # Skip disabled roles

                # Get role percentage for this stage
                role_pct = self._get_role_percentage(stage, role)
                if role_pct <= 0:
                    continue

                # Apply product role multiplier
                product_multiplier = self._get_product_multiplier(inputs.product, role)

                # Calculate total hours for this role in this stage
                total_hours = delivery_hours * role_pct * product_multiplier

                if total_hours <= 0:
                    continue

                # Apply delivery split
                delivery_split = self._get_delivery_split(role)

                onshore_hours = total_hours * delivery_split.onshore_pct
                offshore_hours = total_hours * delivery_split.offshore_pct
                partner_hours = total_hours * delivery_split.partner_pct

                # Get rates for this role and locale
                rates = self._get_rates(role, inputs.locale)

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

        return role_hours_list

    def _get_enabled_roles(self, product: str) -> list[str]:
        """Get list of enabled roles for a product."""
        enabled_roles = []

        for role_toggle in self.config.product_role_map:
            if (product.lower() == "banner" and role_toggle.banner_enabled) or (product.lower() == "colleague" and role_toggle.colleague_enabled):
                enabled_roles.append(role_toggle.role)

        # If no product role map, return all roles
        if not enabled_roles:
            enabled_roles = list(set(rm.role for rm in self.config.role_mix))

        return enabled_roles

    def _get_stage_roles(self, stage: str) -> list[str]:
        """Get list of roles for a stage."""
        return [rm.role for rm in self.config.role_mix if rm.stage == stage]

    def _get_role_percentage(self, stage: str, role: str) -> float:
        """Get role percentage for a stage."""
        for rm in self.config.role_mix:
            if rm.stage == stage and rm.role == role:
                return rm.pct
        return 0.0

    def _get_product_multiplier(self, product: str, role: str) -> float:
        """Get product-specific multiplier for a role."""
        for role_toggle in self.config.product_role_map:
            if role_toggle.role == role:
                if (product.lower() == "banner" and role_toggle.banner_enabled) or (product.lower() == "colleague" and role_toggle.colleague_enabled):
                    return role_toggle.multiplier
                else:
                    return 0.0  # Role disabled

        return 1.0  # Default if no mapping

    def _get_delivery_split(self, role: str) -> DeliveryMix:
        """Get delivery split for a role (per-role override or global)."""
        # Check for per-role override
        if role in self._delivery_mix_cache:
            return self._delivery_mix_cache[role]

        # Use global split
        if None in self._delivery_mix_cache:
            return self._delivery_mix_cache[None]

        # Fallback default
        return DeliveryMix(
            role=None,
            onshore_pct=0.70,
            offshore_pct=0.20,
            partner_pct=0.10
        )

    def _get_rates(self, role: str, locale: str) -> RateCard:
        """Get rate card for a role and locale."""
        # Try exact match
        if (role, locale) in self._rate_cache:
            return self._rate_cache[(role, locale)]

        # Try fallback to US rates
        if (role, 'US') in self._rate_cache:
            return self._rate_cache[(role, 'US')]

        # Ultimate fallback
        return RateCard(
            role=role,
            locale=locale,
            onshore=100.0,
            offshore=50.0,
            partner=75.0
        )

    def summarize_by_role(self, role_hours_list: list[RoleHours]) -> list[RoleHours]:
        """Summarize role hours across all stages."""
        role_summaries: dict[str, dict[str, float]] = {}

        for rh in role_hours_list:
            if rh.role not in role_summaries:
                role_summaries[rh.role] = {
                    'total_hours': 0.0,
                    'onshore_hours': 0.0,
                    'offshore_hours': 0.0,
                    'partner_hours': 0.0,
                    'onshore_cost': 0.0,
                    'offshore_cost': 0.0,
                    'partner_cost': 0.0,
                    'total_cost': 0.0
                }

            role_summaries[rh.role]['total_hours'] += rh.total_hours
            role_summaries[rh.role]['onshore_hours'] += rh.onshore_hours
            role_summaries[rh.role]['offshore_hours'] += rh.offshore_hours
            role_summaries[rh.role]['partner_hours'] += rh.partner_hours
            role_summaries[rh.role]['onshore_cost'] += rh.onshore_cost
            role_summaries[rh.role]['offshore_cost'] += rh.offshore_cost
            role_summaries[rh.role]['partner_cost'] += rh.partner_cost
            role_summaries[rh.role]['total_cost'] += rh.total_cost

        summaries = []
        for role, totals in role_summaries.items():
            blended_rate = (
                totals['total_cost'] / totals['total_hours']
                if totals['total_hours'] > 0 else 0.0
            )

            summaries.append(RoleHours(
                role=role,
                stage="All Stages",
                total_hours=totals['total_hours'],
                onshore_hours=totals['onshore_hours'],
                offshore_hours=totals['offshore_hours'],
                partner_hours=totals['partner_hours'],
                onshore_cost=totals['onshore_cost'],
                offshore_cost=totals['offshore_cost'],
                partner_cost=totals['partner_cost'],
                total_cost=totals['total_cost'],
                blended_rate=blended_rate
            ))

        return sorted(summaries, key=lambda x: x.total_cost, reverse=True)

    def summarize_by_stage(self, role_hours_list: list[RoleHours]) -> list[RoleHours]:
        """Summarize role hours by stage."""
        stage_summaries: dict[str, dict[str, float]] = {}

        for rh in role_hours_list:
            if rh.stage not in stage_summaries:
                stage_summaries[rh.stage] = {
                    'total_hours': 0.0,
                    'onshore_hours': 0.0,
                    'offshore_hours': 0.0,
                    'partner_hours': 0.0,
                    'onshore_cost': 0.0,
                    'offshore_cost': 0.0,
                    'partner_cost': 0.0,
                    'total_cost': 0.0
                }

            stage_summaries[rh.stage]['total_hours'] += rh.total_hours
            stage_summaries[rh.stage]['onshore_hours'] += rh.onshore_hours
            stage_summaries[rh.stage]['offshore_hours'] += rh.offshore_hours
            stage_summaries[rh.stage]['partner_hours'] += rh.partner_hours
            stage_summaries[rh.stage]['onshore_cost'] += rh.onshore_cost
            stage_summaries[rh.stage]['offshore_cost'] += rh.offshore_cost
            stage_summaries[rh.stage]['partner_cost'] += rh.partner_cost
            stage_summaries[rh.stage]['total_cost'] += rh.total_cost

        summaries = []
        for stage, totals in stage_summaries.items():
            blended_rate = (
                totals['total_cost'] / totals['total_hours']
                if totals['total_hours'] > 0 else 0.0
            )

            summaries.append(RoleHours(
                role="All Roles",
                stage=stage,
                total_hours=totals['total_hours'],
                onshore_hours=totals['onshore_hours'],
                offshore_hours=totals['offshore_hours'],
                partner_hours=totals['partner_hours'],
                onshore_cost=totals['onshore_cost'],
                offshore_cost=totals['offshore_cost'],
                partner_cost=totals['partner_cost'],
                total_cost=totals['total_cost'],
                blended_rate=blended_rate
            ))

        return summaries

