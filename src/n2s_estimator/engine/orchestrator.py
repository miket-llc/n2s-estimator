"""Main orchestration engine that coordinates all N2S estimation components."""

from pathlib import Path
from typing import Optional, List, Dict

from .addons import AddOnEngine
from .datatypes import ConfigurationData, EstimationInputs, EstimationResults, RoleHours, StageHours
from .estimator import EstimationEngine
from .loader import ConfigurationLoader
from .pricing import PricingEngine
from .validators import ConfigurationValidator, validate_estimation_inputs


class N2SEstimator:
    """Main orchestrator for N2S delivery estimation."""

    def __init__(self, workbook_path: Path) -> None:
        """Initialize estimator with workbook path."""
        self.workbook_path = workbook_path
        self.config: Optional[ConfigurationData] = None
        self.estimator: Optional[EstimationEngine] = None
        self.pricing: Optional[PricingEngine] = None
        self.addons: Optional[AddOnEngine] = None
        self.validator: Optional[ConfigurationValidator] = None

        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load and validate configuration from workbook."""
        loader = ConfigurationLoader(self.workbook_path)
        self.config = loader.load_configuration()

        # Initialize engines
        self.estimator = EstimationEngine(self.config)
        self.pricing = PricingEngine(self.config)
        self.addons = AddOnEngine(self.config, self.pricing)
        self.validator = ConfigurationValidator(self.config)

    def estimate(self, inputs: EstimationInputs) -> EstimationResults:
        """
        Perform complete N2S estimation.
        
        Returns EstimationResults with all calculations and breakdowns.
        """
        if not all([self.estimator, self.pricing, self.addons]):
            raise RuntimeError("Estimator not properly initialized")
        
        assert self.estimator is not None
        assert self.pricing is not None
        assert self.addons is not None

        # Validate inputs
        input_warnings = validate_estimation_inputs(inputs)
        if input_warnings:
            print("Input validation warnings:", input_warnings)

        # 1. Calculate Base N2S package
        base_stage_hours = self.estimator.estimate_base_n2s(inputs)
        base_role_hours = self.pricing.calculate_role_hours_and_costs(base_stage_hours, inputs)

        # 2. Calculate add-on packages if enabled
        integrations_stage_hours = None
        integrations_role_hours = None
        if inputs.include_integrations:
            integrations_stage_hours, integrations_role_hours = self.addons.calculate_integrations(inputs)

        reports_stage_hours = None
        reports_role_hours = None
        if inputs.include_reports:
            reports_stage_hours, reports_role_hours = self.addons.calculate_reports(inputs)

        degreeworks_stage_hours = None
        degreeworks_role_hours = None
        if inputs.include_degreeworks:
            degreeworks_stage_hours, degreeworks_role_hours = self.addons.calculate_degreeworks(inputs)

        # 3. Calculate totals
        totals = self._calculate_totals(
            base_stage_hours,
            base_role_hours,
            integrations_stage_hours,
            integrations_role_hours,
            reports_stage_hours,
            reports_role_hours,
            degreeworks_stage_hours,
            degreeworks_role_hours
        )

        return EstimationResults(
            inputs=inputs,
            base_n2s=base_stage_hours,
            base_role_hours=base_role_hours,
            integrations_hours=integrations_stage_hours,
            integrations_role_hours=integrations_role_hours,
            reports_hours=reports_stage_hours,
            reports_role_hours=reports_role_hours,
            degreeworks_hours=degreeworks_stage_hours,
            degreeworks_role_hours=degreeworks_role_hours,
            **totals
        )

    def _calculate_totals(
        self,
        base_stage_hours: StageHours,
        base_role_hours: List[RoleHours],
        integrations_stage_hours: Optional[StageHours],
        integrations_role_hours: Optional[List[RoleHours]],
        reports_stage_hours: Optional[StageHours],
        reports_role_hours: Optional[List[RoleHours]],
        degreeworks_stage_hours: Optional[StageHours],
        degreeworks_role_hours: Optional[List[RoleHours]]
    ) -> Dict:
        """Calculate total hours and costs across all packages."""
        # Base totals
        base_presales_hours = sum(base_stage_hours.presales_hours.values())
        base_delivery_hours = sum(base_stage_hours.delivery_hours.values())
        base_presales_cost = 0.0  # Presales not priced in this version
        base_delivery_cost = sum(rh.total_cost for rh in base_role_hours)

        # Add-on totals
        addon_delivery_hours = 0.0
        addon_delivery_cost = 0.0

        if integrations_stage_hours and integrations_role_hours:
            addon_delivery_hours += sum(integrations_stage_hours.delivery_hours.values())
            addon_delivery_cost += sum(rh.total_cost for rh in integrations_role_hours)

        if reports_stage_hours and reports_role_hours:
            addon_delivery_hours += sum(reports_stage_hours.delivery_hours.values())
            addon_delivery_cost += sum(rh.total_cost for rh in reports_role_hours)

        if degreeworks_stage_hours and degreeworks_role_hours:
            addon_delivery_hours += sum(degreeworks_stage_hours.delivery_hours.values())
            addon_delivery_cost += sum(rh.total_cost for rh in degreeworks_role_hours)

        # Grand totals
        total_presales_hours = base_presales_hours
        total_delivery_hours = base_delivery_hours + addon_delivery_hours
        total_presales_cost = base_presales_cost
        total_delivery_cost = base_delivery_cost + addon_delivery_cost
        total_hours = total_presales_hours + total_delivery_hours
        total_cost = total_presales_cost + total_delivery_cost

        return {
            'total_presales_hours': total_presales_hours,
            'total_delivery_hours': total_delivery_hours,
            'total_presales_cost': total_presales_cost,
            'total_delivery_cost': total_delivery_cost,
            'total_hours': total_hours,
            'total_cost': total_cost
        }

    def get_validation_warnings(self) -> list[str]:
        """Get configuration validation warnings."""
        if not self.validator:
            return ["Validator not initialized"]

        return self.validator.validate_all()

    def get_role_summary(self, results: EstimationResults) -> list[RoleHours]:
        """Get role summary across all packages."""
        if not self.pricing:
            return []

        all_role_hours = results.base_role_hours.copy()

        if results.integrations_role_hours:
            all_role_hours.extend(results.integrations_role_hours)

        if results.reports_role_hours:
            all_role_hours.extend(results.reports_role_hours)

        return self.pricing.summarize_by_role(all_role_hours)

    def get_stage_summary(self, results: EstimationResults) -> list[RoleHours]:
        """Get stage summary for base N2S package only."""
        if not self.pricing:
            return []

        return self.pricing.summarize_by_stage(results.base_role_hours)

    def get_package_summaries(self, results: EstimationResults) -> dict:
        """Get summary information for each package."""
        summaries = {}

        # Base N2S
        base_hours = sum(results.base_n2s.stage_hours.values())
        base_cost = sum(rh.total_cost for rh in results.base_role_hours)
        summaries['Base N2S'] = {
            'hours': base_hours,
            'cost': base_cost,
            'enabled': True
        }

        # Integrations
        if results.integrations_hours and results.integrations_role_hours:
            int_hours = sum(results.integrations_hours.stage_hours.values())
            int_cost = sum(rh.total_cost for rh in results.integrations_role_hours)
            summaries['Integrations'] = {
                'hours': int_hours,
                'cost': int_cost,
                'enabled': True
            }
        else:
            summaries['Integrations'] = {
                'hours': 0.0,
                'cost': 0.0,
                'enabled': False
            }

        # Reports
        if results.reports_hours and results.reports_role_hours:
            rep_hours = sum(results.reports_hours.stage_hours.values())
            rep_cost = sum(rh.total_cost for rh in results.reports_role_hours)
            summaries['Reports'] = {
                'hours': rep_hours,
                'cost': rep_cost,
                'enabled': True
            }
        else:
            summaries['Reports'] = {
                'hours': 0.0,
                'cost': 0.0,
                'enabled': False
            }

        # Degree Works
        if results.degreeworks_hours and results.degreeworks_role_hours:
            dw_hours = sum(results.degreeworks_hours.stage_hours.values())
            dw_cost = sum(rh.total_cost for rh in results.degreeworks_role_hours)
            summaries['Degree Works'] = {
                'hours': dw_hours,
                'cost': dw_cost,
                'enabled': True
            }
        else:
            summaries['Degree Works'] = {
                'hours': 0.0,
                'cost': 0.0,
                'enabled': False
            }

        return summaries

    def get_delivery_split_summary(self, results: EstimationResults) -> dict:
        """Get delivery split summary across all packages."""
        all_role_hours = results.base_role_hours.copy()

        if results.integrations_role_hours:
            all_role_hours.extend(results.integrations_role_hours)

        if results.reports_role_hours:
            all_role_hours.extend(results.reports_role_hours)

        if results.degreeworks_role_hours:
            all_role_hours.extend(results.degreeworks_role_hours)

        total_onshore_hours = sum(rh.onshore_hours for rh in all_role_hours)
        total_offshore_hours = sum(rh.offshore_hours for rh in all_role_hours)
        total_partner_hours = sum(rh.partner_hours for rh in all_role_hours)
        total_hours = total_onshore_hours + total_offshore_hours + total_partner_hours

        total_onshore_cost = sum(rh.onshore_cost for rh in all_role_hours)
        total_offshore_cost = sum(rh.offshore_cost for rh in all_role_hours)
        total_partner_cost = sum(rh.partner_cost for rh in all_role_hours)
        total_cost = total_onshore_cost + total_offshore_cost + total_partner_cost

        if total_hours > 0:
            return {
                'onshore': {
                    'hours': total_onshore_hours,
                    'cost': total_onshore_cost,
                    'hours_pct': total_onshore_hours / total_hours,
                    'cost_pct': total_onshore_cost / total_cost if total_cost > 0 else 0.0
                },
                'offshore': {
                    'hours': total_offshore_hours,
                    'cost': total_offshore_cost,
                    'hours_pct': total_offshore_hours / total_hours,
                    'cost_pct': total_offshore_cost / total_cost if total_cost > 0 else 0.0
                },
                'partner': {
                    'hours': total_partner_hours,
                    'cost': total_partner_cost,
                    'hours_pct': total_partner_hours / total_hours,
                    'cost_pct': total_partner_cost / total_cost if total_cost > 0 else 0.0
                }
            }

        return {
            'onshore': {'hours': 0, 'cost': 0, 'hours_pct': 0, 'cost_pct': 0},
            'offshore': {'hours': 0, 'cost': 0, 'hours_pct': 0, 'cost_pct': 0},
            'partner': {'hours': 0, 'cost': 0, 'hours_pct': 0, 'cost_pct': 0}
        }

    def apply_rate_overrides(self, overrides: list[dict]) -> None:
        """Apply rate overrides to the pricing engine."""
        if not self.pricing:
            return
        for row in overrides:
            self.pricing.update_rate(
                role=row['role'], 
                locale=row['locale'],
                onshore=float(row['onshore']), 
                offshore=float(row['offshore']), 
                partner=float(row['partner'])
            )

    def apply_delivery_mix_overrides(self, global_mix: Optional[dict], role_overrides: list[dict]) -> None:
        """Apply delivery mix overrides to the pricing engine."""
        if not self.pricing:
            return
        if global_mix:
            self.pricing.update_global_delivery_mix(
                float(global_mix['onshore_pct']), 
                float(global_mix['offshore_pct']), 
                float(global_mix['partner_pct'])
            )
        for row in role_overrides:
            self.pricing.update_role_delivery_mix(
                role=row['role'],
                onshore_pct=float(row['onshore_pct']),
                offshore_pct=float(row['offshore_pct']),
                partner_pct=float(row['partner_pct'])
            )

    def reset_pricing_overrides(self) -> None:
        """Reset pricing overrides to workbook defaults."""
        if self.pricing:
            self.pricing.reset_from_config()
