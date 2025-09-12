"""Tests for scenario management functionality including rates and pricing overrides."""

import json
from pathlib import Path

import pytest

from src.n2s_estimator.engine.datatypes import EstimationInputs
from src.n2s_estimator.engine.orchestrator import N2SEstimator


class TestScenarioManagement:
    """Test scenario save/load functionality with rates and pricing."""

    @pytest.fixture
    def estimator(self):
        """Create estimator for testing."""
        workbook_path = Path(__file__).parent.parent / "src" / "n2s_estimator" / "data" / "n2s_estimator.xlsx"
        return N2SEstimator(workbook_path)

    @pytest.fixture
    def complex_scenario_data(self):
        """Complex scenario data with all features enabled."""
        return {
            'product': 'Banner',
            'delivery_type': 'Modernization',
            'size_band': 'Large',
            'locale': 'US',
            'include_integrations': True,
            'integrations_count': 25,
            'integrations_simple_pct': 0.60,
            'integrations_standard_pct': 0.30,
            'integrations_complex_pct': 0.10,
            'include_reports': True,
            'reports_count': 15,
            'reports_simple_pct': 0.50,
            'reports_standard_pct': 0.35,
            'reports_complex_pct': 0.15,
            'include_degreeworks': True,
            'degreeworks_include_setup': True,
            'degreeworks_use_pve_calculator': True,
            'degreeworks_majors': 20,
            'degreeworks_minors': 10,
            'degreeworks_certificates': 5,
            'degreeworks_concentrations': 3,
            'degreeworks_catalog_years': 2,
            'degreeworks_pve_count': 0,
            'degreeworks_simple_pct': 0.50,
            'degreeworks_standard_pct': 0.35,
            'degreeworks_complex_pct': 0.15,
            'degreeworks_cap_enabled': True,
            'degreeworks_cap_hours': 500.0,
            'sprint0_uplift_pct': 0.05,
            'maturity_factor': 1.2,
            'scenario_overrides': {
                'rate_overrides': [
                    {
                        'role': 'Technical Architect',
                        'locale': 'US',
                        'onshore': 160.0,
                        'offshore': 80.0,
                        'partner': 110.0
                    },
                    {
                        'role': 'Project Manager',
                        'locale': 'US',
                        'onshore': 130.0,
                        'offshore': 65.0,
                        'partner': 90.0
                    },
                    {
                        'role': 'Solution Architect',
                        'locale': 'US',
                        'onshore': 140.0,
                        'offshore': 70.0,
                        'partner': 95.0
                    }
                ],
                'global_mix_override': {
                    'onshore_pct': 0.75,
                    'offshore_pct': 0.15,
                    'partner_pct': 0.10
                },
                'role_mix_overrides': [
                    {
                        'role': 'Technical Architect',
                        'onshore_pct': 0.85,
                        'offshore_pct': 0.10,
                        'partner_pct': 0.05
                    },
                    {
                        'role': 'Project Manager',
                        'onshore_pct': 0.70,
                        'offshore_pct': 0.20,
                        'partner_pct': 0.10
                    }
                ]
            }
        }

    def test_scenario_data_serialization(self, complex_scenario_data):
        """Test that scenario data can be serialized to JSON."""
        json_str = json.dumps(complex_scenario_data, indent=2)
        assert isinstance(json_str, str)
        assert len(json_str) > 100
        
        # Should be able to deserialize
        deserialized = json.loads(json_str)
        assert deserialized == complex_scenario_data

    def test_estimation_inputs_from_scenario(self, complex_scenario_data):
        """Test creating EstimationInputs from scenario data."""
        inputs_data = {
            'product': complex_scenario_data.get('product', 'Banner'),
            'delivery_type': complex_scenario_data.get('delivery_type', 'Modernization'),
            'size_band': complex_scenario_data.get('size_band', 'Medium'),
            'locale': complex_scenario_data.get('locale', 'US'),
            'maturity_factor': complex_scenario_data.get('maturity_factor', 1.0),
            'integrations_count': complex_scenario_data.get('integrations_count', 0),
            'integrations_simple_pct': complex_scenario_data.get('integrations_simple_pct', 0.0),
            'integrations_standard_pct': complex_scenario_data.get('integrations_standard_pct', 0.0),
            'integrations_complex_pct': complex_scenario_data.get('integrations_complex_pct', 0.0),
            'reports_count': complex_scenario_data.get('reports_count', 0),
            'reports_simple_pct': complex_scenario_data.get('reports_simple_pct', 0.0),
            'reports_standard_pct': complex_scenario_data.get('reports_standard_pct', 0.0),
            'reports_complex_pct': complex_scenario_data.get('reports_complex_pct', 0.0),
            'include_integrations': complex_scenario_data.get('include_integrations', False),
            'include_reports': complex_scenario_data.get('include_reports', False),
            'include_degreeworks': complex_scenario_data.get('include_degreeworks', False),
            'degreeworks_include_setup': complex_scenario_data.get('degreeworks_include_setup', True),
            'degreeworks_use_pve_calculator': complex_scenario_data.get('degreeworks_use_pve_calculator', True),
            'degreeworks_majors': complex_scenario_data.get('degreeworks_majors', 0),
            'degreeworks_minors': complex_scenario_data.get('degreeworks_minors', 0),
            'degreeworks_certificates': complex_scenario_data.get('degreeworks_certificates', 0),
            'degreeworks_concentrations': complex_scenario_data.get('degreeworks_concentrations', 0),
            'degreeworks_catalog_years': complex_scenario_data.get('degreeworks_catalog_years', 1),
            'degreeworks_pve_count': complex_scenario_data.get('degreeworks_pve_count', 0),
            'degreeworks_simple_pct': complex_scenario_data.get('degreeworks_simple_pct', 0.50),
            'degreeworks_standard_pct': complex_scenario_data.get('degreeworks_standard_pct', 0.35),
            'degreeworks_complex_pct': complex_scenario_data.get('degreeworks_complex_pct', 0.15),
            'degreeworks_cap_enabled': complex_scenario_data.get('degreeworks_cap_enabled', True),
            'degreeworks_cap_hours': complex_scenario_data.get('degreeworks_cap_hours', None),
            'sprint0_uplift_pct': complex_scenario_data.get('sprint0_uplift_pct', 0.0)
        }
        
        inputs = EstimationInputs(**inputs_data)
        
        # Verify key parameters
        assert inputs.product == 'Banner'
        assert inputs.delivery_type == 'Modernization'
        assert inputs.size_band == 'Large'
        assert inputs.locale == 'US'
        assert inputs.include_degreeworks is True
        assert inputs.degreeworks_majors == 20
        assert inputs.degreeworks_cap_hours == 500.0
        assert inputs.sprint0_uplift_pct == 0.05
        assert inputs.maturity_factor == 1.2

    def test_rate_overrides_application(self, estimator, complex_scenario_data):
        """Test that rate overrides are applied correctly."""
        # Get original rates
        original_rates = estimator.pricing.get_effective_rates(locale='US')
        original_ta_rate = next(r for r in original_rates if r.role == 'Technical Architect')
        
        # Apply rate overrides
        rate_overrides = complex_scenario_data['scenario_overrides']['rate_overrides']
        estimator.apply_rate_overrides(rate_overrides)
        
        # Get new rates
        new_rates = estimator.pricing.get_effective_rates(locale='US')
        new_ta_rate = next(r for r in new_rates if r.role == 'Technical Architect')
        
        # Verify rates changed
        assert new_ta_rate.onshore == 160.0
        assert new_ta_rate.offshore == 80.0
        assert new_ta_rate.partner == 110.0
        
        # Verify original rates were different
        assert original_ta_rate.onshore != new_ta_rate.onshore
        assert original_ta_rate.offshore != new_ta_rate.offshore
        assert original_ta_rate.partner != new_ta_rate.partner

    def test_delivery_mix_overrides_application(self, estimator, complex_scenario_data):
        """Test that delivery mix overrides are applied correctly."""
        # Apply delivery mix overrides
        global_mix = complex_scenario_data['scenario_overrides']['global_mix_override']
        role_mix_overrides = complex_scenario_data['scenario_overrides']['role_mix_overrides']
        
        estimator.apply_delivery_mix_overrides(global_mix, role_mix_overrides)
        
        # Verify global mix was applied (stored with role=None)
        global_dm = estimator.pricing._delivery_mix_cache.get(None)
        assert global_dm is not None
        assert global_dm.onshore_pct == 0.75
        assert global_dm.offshore_pct == 0.15
        assert global_dm.partner_pct == 0.10
        
        # Verify role-specific mix was applied
        ta_mix = estimator.pricing._delivery_mix_cache.get('Technical Architect')
        assert ta_mix is not None
        assert ta_mix.onshore_pct == 0.85
        assert ta_mix.offshore_pct == 0.10
        assert ta_mix.partner_pct == 0.05

    def test_complete_scenario_workflow(self, estimator, complex_scenario_data):
        """Test complete scenario save/load workflow."""
        # Create inputs from scenario data
        inputs_data = {
            'product': complex_scenario_data.get('product', 'Banner'),
            'delivery_type': complex_scenario_data.get('delivery_type', 'Modernization'),
            'size_band': complex_scenario_data.get('size_band', 'Medium'),
            'locale': complex_scenario_data.get('locale', 'US'),
            'maturity_factor': complex_scenario_data.get('maturity_factor', 1.0),
            'integrations_count': complex_scenario_data.get('integrations_count', 0),
            'integrations_simple_pct': complex_scenario_data.get('integrations_simple_pct', 0.0),
            'integrations_standard_pct': complex_scenario_data.get('integrations_standard_pct', 0.0),
            'integrations_complex_pct': complex_scenario_data.get('integrations_complex_pct', 0.0),
            'reports_count': complex_scenario_data.get('reports_count', 0),
            'reports_simple_pct': complex_scenario_data.get('reports_simple_pct', 0.0),
            'reports_standard_pct': complex_scenario_data.get('reports_standard_pct', 0.0),
            'reports_complex_pct': complex_scenario_data.get('reports_complex_pct', 0.0),
            'include_integrations': complex_scenario_data.get('include_integrations', False),
            'include_reports': complex_scenario_data.get('include_reports', False),
            'include_degreeworks': complex_scenario_data.get('include_degreeworks', False),
            'degreeworks_include_setup': complex_scenario_data.get('degreeworks_include_setup', True),
            'degreeworks_use_pve_calculator': complex_scenario_data.get('degreeworks_use_pve_calculator', True),
            'degreeworks_majors': complex_scenario_data.get('degreeworks_majors', 0),
            'degreeworks_minors': complex_scenario_data.get('degreeworks_minors', 0),
            'degreeworks_certificates': complex_scenario_data.get('degreeworks_certificates', 0),
            'degreeworks_concentrations': complex_scenario_data.get('degreeworks_concentrations', 0),
            'degreeworks_catalog_years': complex_scenario_data.get('degreeworks_catalog_years', 1),
            'degreeworks_pve_count': complex_scenario_data.get('degreeworks_pve_count', 0),
            'degreeworks_simple_pct': complex_scenario_data.get('degreeworks_simple_pct', 0.50),
            'degreeworks_standard_pct': complex_scenario_data.get('degreeworks_standard_pct', 0.35),
            'degreeworks_complex_pct': complex_scenario_data.get('degreeworks_complex_pct', 0.15),
            'degreeworks_cap_enabled': complex_scenario_data.get('degreeworks_cap_enabled', True),
            'degreeworks_cap_hours': complex_scenario_data.get('degreeworks_cap_hours', None),
            'sprint0_uplift_pct': complex_scenario_data.get('sprint0_uplift_pct', 0.0)
        }
        
        inputs = EstimationInputs(**inputs_data)
        
        # Apply pricing overrides
        overrides = complex_scenario_data['scenario_overrides']
        estimator.apply_rate_overrides(overrides['rate_overrides'])
        estimator.apply_delivery_mix_overrides(
            overrides['global_mix_override'],
            overrides['role_mix_overrides']
        )
        
        # Run estimation
        results = estimator.estimate(inputs)
        
        # Verify results
        assert results.base_n2s is not None
        assert results.integrations_hours is not None
        assert results.reports_hours is not None
        assert results.degreeworks_hours is not None
        
        # Verify costs are calculated with custom rates
        assert results.total_cost > 0
        assert results.total_delivery_cost > 0
        
        # Verify Degree Works calculations
        if results.degreeworks_hours:
            setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
            pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
            assert setup_hours > 0
            assert pve_hours > 0
        else:
            # Degree Works should be enabled in this test scenario
            assert inputs.include_degreeworks is True
            assert results.degreeworks_hours is not None, "Degree Works should be enabled and calculated"

    def test_backward_compatibility_minimal_scenario(self, estimator):
        """Test loading minimal scenario data (backward compatibility)."""
        minimal_scenario = {
            'product': 'Banner',
            'delivery_type': 'Net New',
            'size_band': 'Medium',
            'locale': 'US'
        }
        
        # Should handle missing fields gracefully with valid defaults
        inputs_data = {
            'product': minimal_scenario.get('product', 'Banner'),
            'delivery_type': minimal_scenario.get('delivery_type', 'Modernization'),
            'size_band': minimal_scenario.get('size_band', 'Medium'),
            'locale': minimal_scenario.get('locale', 'US'),
            'maturity_factor': minimal_scenario.get('maturity_factor', 1.0),
            'integrations_count': minimal_scenario.get('integrations_count', 0),
            'integrations_simple_pct': minimal_scenario.get('integrations_simple_pct', 1.0),  # Must sum to 1.0
            'integrations_standard_pct': minimal_scenario.get('integrations_standard_pct', 0.0),
            'integrations_complex_pct': minimal_scenario.get('integrations_complex_pct', 0.0),
            'reports_count': minimal_scenario.get('reports_count', 0),
            'reports_simple_pct': minimal_scenario.get('reports_simple_pct', 1.0),  # Must sum to 1.0
            'reports_standard_pct': minimal_scenario.get('reports_standard_pct', 0.0),
            'reports_complex_pct': minimal_scenario.get('reports_complex_pct', 0.0),
            'include_integrations': minimal_scenario.get('include_integrations', False),
            'include_reports': minimal_scenario.get('include_reports', False),
            'include_degreeworks': minimal_scenario.get('include_degreeworks', False),
            'degreeworks_include_setup': minimal_scenario.get('degreeworks_include_setup', True),
            'degreeworks_use_pve_calculator': minimal_scenario.get('degreeworks_use_pve_calculator', True),
            'degreeworks_majors': minimal_scenario.get('degreeworks_majors', 0),
            'degreeworks_minors': minimal_scenario.get('degreeworks_minors', 0),
            'degreeworks_certificates': minimal_scenario.get('degreeworks_certificates', 0),
            'degreeworks_concentrations': minimal_scenario.get('degreeworks_concentrations', 0),
            'degreeworks_catalog_years': minimal_scenario.get('degreeworks_catalog_years', 1),
            'degreeworks_pve_count': minimal_scenario.get('degreeworks_pve_count', 0),
            'degreeworks_simple_pct': minimal_scenario.get('degreeworks_simple_pct', 0.50),
            'degreeworks_standard_pct': minimal_scenario.get('degreeworks_standard_pct', 0.35),
            'degreeworks_complex_pct': minimal_scenario.get('degreeworks_complex_pct', 0.15),
            'degreeworks_cap_enabled': minimal_scenario.get('degreeworks_cap_enabled', True),
            'degreeworks_cap_hours': minimal_scenario.get('degreeworks_cap_hours', None),
            'sprint0_uplift_pct': minimal_scenario.get('sprint0_uplift_pct', 0.0)
        }
        
        inputs = EstimationInputs(**inputs_data)
        results = estimator.estimate(inputs)
        
        # Should work with defaults
        assert results.base_n2s is not None
        assert results.total_hours > 0
        assert results.total_cost > 0

    def test_rate_override_validation(self, estimator):
        """Test rate override validation."""
        # Test valid rate overrides
        valid_overrides = [
            {
                'role': 'Technical Architect',
                'locale': 'US',
                'onshore': 150.0,
                'offshore': 75.0,
                'partner': 100.0
            }
        ]
        
        estimator.apply_rate_overrides(valid_overrides)
        rates = estimator.pricing.get_effective_rates(locale='US')
        ta_rate = next(r for r in rates if r.role == 'Technical Architect')
        
        assert ta_rate.onshore == 150.0
        assert ta_rate.offshore == 75.0
        assert ta_rate.partner == 100.0

    def test_delivery_mix_validation(self, estimator):
        """Test delivery mix validation."""
        # Test valid global mix
        global_mix = {
            'onshore_pct': 0.70,
            'offshore_pct': 0.20,
            'partner_pct': 0.10
        }
        
        estimator.apply_delivery_mix_overrides(global_mix, [])
        
        # Verify global mix was applied
        global_dm = estimator.pricing._delivery_mix_cache.get(None)
        assert global_dm is not None
        assert global_dm.onshore_pct == 0.70
        assert global_dm.offshore_pct == 0.20
        assert global_dm.partner_pct == 0.10
        
        # Verify percentages sum to 1.0
        total = global_dm.onshore_pct + global_dm.offshore_pct + global_dm.partner_pct
        assert abs(total - 1.0) < 0.001

    def test_scenario_data_completeness(self, complex_scenario_data):
        """Test that scenario data includes all required fields."""
        required_fields = [
            'product', 'delivery_type', 'size_band', 'locale',
            'include_integrations', 'include_reports', 'include_degreeworks',
            'degreeworks_include_setup', 'degreeworks_use_pve_calculator',
            'degreeworks_majors', 'degreeworks_minors', 'degreeworks_certificates',
            'degreeworks_concentrations', 'degreeworks_catalog_years',
            'degreeworks_pve_count', 'degreeworks_simple_pct',
            'degreeworks_standard_pct', 'degreeworks_complex_pct',
            'degreeworks_cap_enabled', 'degreeworks_cap_hours',
            'sprint0_uplift_pct', 'maturity_factor'
        ]
        
        for field in required_fields:
            assert field in complex_scenario_data, f"Missing required field: {field}"
        
        # Test scenario overrides structure
        assert 'scenario_overrides' in complex_scenario_data
        overrides = complex_scenario_data['scenario_overrides']
        
        assert 'rate_overrides' in overrides
        assert 'global_mix_override' in overrides
        assert 'role_mix_overrides' in overrides
        
        # Test rate overrides structure
        for rate_override in overrides['rate_overrides']:
            assert 'role' in rate_override
            assert 'locale' in rate_override
            assert 'onshore' in rate_override
            assert 'offshore' in rate_override
            assert 'partner' in rate_override
            assert rate_override['onshore'] > 0
            assert rate_override['offshore'] > 0
            assert rate_override['partner'] > 0

    def test_estimation_with_custom_rates_affects_costs(self, estimator, complex_scenario_data):
        """Test that custom rates actually affect the final costs."""
        # Create inputs
        inputs_data = {
            'product': complex_scenario_data.get('product', 'Banner'),
            'delivery_type': complex_scenario_data.get('delivery_type', 'Modernization'),
            'size_band': complex_scenario_data.get('size_band', 'Medium'),
            'locale': complex_scenario_data.get('locale', 'US'),
            'maturity_factor': complex_scenario_data.get('maturity_factor', 1.0),
            'integrations_count': complex_scenario_data.get('integrations_count', 0),
            'integrations_simple_pct': complex_scenario_data.get('integrations_simple_pct', 0.0),
            'integrations_standard_pct': complex_scenario_data.get('integrations_standard_pct', 0.0),
            'integrations_complex_pct': complex_scenario_data.get('integrations_complex_pct', 0.0),
            'reports_count': complex_scenario_data.get('reports_count', 0),
            'reports_simple_pct': complex_scenario_data.get('reports_simple_pct', 0.0),
            'reports_standard_pct': complex_scenario_data.get('reports_standard_pct', 0.0),
            'reports_complex_pct': complex_scenario_data.get('reports_complex_pct', 0.0),
            'include_integrations': complex_scenario_data.get('include_integrations', False),
            'include_reports': complex_scenario_data.get('include_reports', False),
            'include_degreeworks': complex_scenario_data.get('include_degreeworks', False),
            'degreeworks_include_setup': complex_scenario_data.get('degreeworks_include_setup', True),
            'degreeworks_use_pve_calculator': complex_scenario_data.get('degreeworks_use_pve_calculator', True),
            'degreeworks_majors': complex_scenario_data.get('degreeworks_majors', 0),
            'degreeworks_minors': complex_scenario_data.get('degreeworks_minors', 0),
            'degreeworks_certificates': complex_scenario_data.get('degreeworks_certificates', 0),
            'degreeworks_concentrations': complex_scenario_data.get('degreeworks_concentrations', 0),
            'degreeworks_catalog_years': complex_scenario_data.get('degreeworks_catalog_years', 1),
            'degreeworks_pve_count': complex_scenario_data.get('degreeworks_pve_count', 0),
            'degreeworks_simple_pct': complex_scenario_data.get('degreeworks_simple_pct', 0.50),
            'degreeworks_standard_pct': complex_scenario_data.get('degreeworks_standard_pct', 0.35),
            'degreeworks_complex_pct': complex_scenario_data.get('degreeworks_complex_pct', 0.15),
            'degreeworks_cap_enabled': complex_scenario_data.get('degreeworks_cap_enabled', True),
            'degreeworks_cap_hours': complex_scenario_data.get('degreeworks_cap_hours', None),
            'sprint0_uplift_pct': complex_scenario_data.get('sprint0_uplift_pct', 0.0)
        }
        
        inputs = EstimationInputs(**inputs_data)
        
        # Run estimation without custom rates
        results_default = estimator.estimate(inputs)
        default_cost = results_default.total_cost
        
        # Apply custom rates
        overrides = complex_scenario_data['scenario_overrides']
        estimator.apply_rate_overrides(overrides['rate_overrides'])
        estimator.apply_delivery_mix_overrides(
            overrides['global_mix_override'],
            overrides['role_mix_overrides']
        )
        
        # Run estimation with custom rates
        results_custom = estimator.estimate(inputs)
        custom_cost = results_custom.total_cost
        
        # Costs should be different
        assert abs(custom_cost - default_cost) > 1000, "Custom rates should significantly affect costs"
        
        # Hours should be the same
        assert abs(results_custom.total_hours - results_default.total_hours) < 0.01, "Hours should not change with rates"
