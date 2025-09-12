"""Core estimation engine for N2S Delivery Estimator."""

from .datatypes import ConfigurationData, EstimationInputs, StageHours


class EstimationEngine:
    """Core estimation engine implementing the deterministic math pipeline."""

    def __init__(self, config: ConfigurationData) -> None:
        """Initialize engine with configuration data."""
        self.config = config

    def estimate_base_n2s(self, inputs: EstimationInputs) -> StageHours:
        """
        Estimate Base N2S package hours following the deterministic pipeline:
        1. Apply size and delivery type multipliers to baseline hours
        2. Allocate to stages via stage weights
        3. Split each stage into presales vs delivery hours
        """
        # Step 1: Calculate adjusted base hours with product-specific multipliers
        size_multiplier = self.config.size_multipliers.get(inputs.size_band, 1.0)

        # Get product-specific delivery type multiplier, fall back to global
        product_mult = (
            self.config.product_delivery_type_multipliers
                .get(inputs.product, {})
                .get(inputs.delivery_type)
        )
        effective_delivery_mult = (
            product_mult if product_mult is not None
            else self.config.delivery_type_multipliers.get(inputs.delivery_type, 1.0)
        )

        adjusted_base = (
            self.config.baseline_hours *
            size_multiplier *
            effective_delivery_mult *
            inputs.maturity_factor
        )

        # Step 2: Build working weights dict and apply Sprint 0 uplift
        weights = {sw.stage: sw.weight for sw in self.config.stage_weights}

        # Apply Sprint 0 uplift (absolute % of total)
        uplift = inputs.sprint0_uplift_pct if hasattr(inputs, 'sprint0_uplift_pct') else 0.0
        if uplift > 0:
            donors = ['Plan', 'Configure']
            donor_total = sum(weights.get(d, 0.0) for d in donors)
            if donor_total > 0:
                # add uplift to Sprint 0
                weights['Sprint 0'] = weights.get('Sprint 0', 0.0) + uplift
                # subtract proportionally from donors
                for d in donors:
                    w = weights.get(d, 0.0)
                    delta = uplift * (w / donor_total)
                    weights[d] = max(w - delta, 0.0)
                # renormalize small float drift
                total = sum(weights.values())
                for k in weights:
                    weights[k] = weights[k] / total

        # Allocate to stages using adjusted weights
        stage_hours_dict = {}
        for stage, weight in weights.items():
            stage_hours_dict[stage] = adjusted_base * weight

        # Step 3: Split each stage into presales vs delivery
        presales_hours_dict = {}
        delivery_hours_dict = {}

        for stage, total_hours in stage_hours_dict.items():
            presales_pct = self._calculate_presales_percentage(stage)
            presales_hours = total_hours * presales_pct
            delivery_hours = total_hours - presales_hours

            presales_hours_dict[stage] = presales_hours
            delivery_hours_dict[stage] = delivery_hours

        return StageHours(
            stage_hours=stage_hours_dict,
            presales_hours=presales_hours_dict,
            delivery_hours=delivery_hours_dict
        )

    def get_size_multiplier(self, size_band: str) -> float:
        """Get size multiplier for the given size band."""
        return self.config.size_multipliers.get(size_band, 1.0)

    def _calculate_presales_percentage(self, stage: str) -> float:
        """
        Calculate presales percentage for a stage.

        If Activities sheet has multiple weighted activities with Is Presales flags for that stage,
        compute presales% = sum(weights of presales activities) / sum(all activity weights).
        Else fallback to Stages.Default Presales % for that stage.
        """
        # Get activities for this stage
        stage_activities = [a for a in self.config.activities if a.stage == stage]

        if len(stage_activities) > 0:
            # Use activity-based calculation
            total_weight = sum(a.weight for a in stage_activities)
            presales_weight = sum(a.weight for a in stage_activities if a.is_presales)

            if total_weight > 0:
                return presales_weight / total_weight

        # Fallback to stage default
        for stage_presales in self.config.stages_presales:
            if stage_presales.stage == stage:
                return stage_presales.default_pct

        # Ultimate fallback
        return 0.0

    def get_stage_list(self) -> list[str]:
        """Get ordered list of stages."""
        return [sw.stage for sw in self.config.stage_weights]

    def get_roles_for_stage(self, stage: str) -> list[str]:
        """Get list of roles for a specific stage."""
        return [rm.role for rm in self.config.role_mix if rm.stage == stage]

    def get_role_percentage(self, stage: str, role: str) -> float:
        """Get role percentage for a specific stage and role."""
        for rm in self.config.role_mix:
            if rm.stage == stage and rm.role == role:
                return rm.pct
        return 0.0

    def get_enabled_roles_for_product(self, product: str) -> list[str]:
        """Get list of enabled roles for a specific product."""
        enabled_roles = []

        for role_toggle in self.config.product_role_map:
            if (product.lower() == "banner" and role_toggle.banner_enabled) or (product.lower() == "colleague" and role_toggle.colleague_enabled):
                enabled_roles.append(role_toggle.role)

        # If no product role map, return all roles from role mix
        if not enabled_roles:
            enabled_roles = list({rm.role for rm in self.config.role_mix})

        return enabled_roles

    def get_product_role_multiplier(self, product: str, role: str) -> float:
        """Get product-specific multiplier for a role."""
        for role_toggle in self.config.product_role_map:
            if role_toggle.role == role:
                if (product.lower() == "banner" and role_toggle.banner_enabled) or (product.lower() == "colleague" and role_toggle.colleague_enabled):
                    return role_toggle.multiplier
                else:
                    return 0.0  # Role disabled for this product

        return 1.0  # Default multiplier if no mapping found

    def validate_expected_totals(self, stage_hours: StageHours) -> dict[str, float]:
        """
        Validate against expected totals for default scenario.
        Returns dict with expected vs actual values for testing.
        """
        expected_stage_hours = {
            'Start': 167.5,
            'Prepare': 167.5,
            'Sprint 0': 402.0,
            'Plan': 670.0,
            'Configure': 2278.0,
            'Test': 1340.0,
            'Deploy': 670.0,
            'Go-Live': 402.0,
            'Post Go-Live (Care)': 603.0
        }

        expected_presales = {
            'Start': 100.5,  # 167.5 * 0.6
            'Prepare': 50.25,  # 167.5 * 0.3
        }

        validation_results = {}

        # Check stage hours
        for stage, expected in expected_stage_hours.items():
            actual = stage_hours.stage_hours.get(stage, 0.0)
            validation_results[f"stage_hours_{stage}"] = {
                'expected': expected,
                'actual': actual,
                'diff': abs(actual - expected)
            }

        # Check presales hours
        for stage, expected in expected_presales.items():
            actual = stage_hours.presales_hours.get(stage, 0.0)
            validation_results[f"presales_hours_{stage}"] = {
                'expected': expected,
                'actual': actual,
                'diff': abs(actual - expected)
            }

        # Check totals
        total_hours = sum(stage_hours.stage_hours.values())
        total_presales = sum(stage_hours.presales_hours.values())
        total_delivery = sum(stage_hours.delivery_hours.values())

        validation_results['total_hours'] = {
            'expected': 6700.0,
            'actual': total_hours,
            'diff': abs(total_hours - 6700.0)
        }

        validation_results['total_presales'] = {
            'expected': 150.75,
            'actual': total_presales,
            'diff': abs(total_presales - 150.75)
        }

        validation_results['total_delivery'] = {
            'expected': 6549.25,
            'actual': total_delivery,
            'diff': abs(total_delivery - 6549.25)
        }

        return validation_results

