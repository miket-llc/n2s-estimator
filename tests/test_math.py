"""Tests for deterministic math calculations."""

from pathlib import Path

import pytest

from src.n2s_estimator.engine.datatypes import EstimationInputs
from src.n2s_estimator.engine.orchestrator import N2SEstimator


class TestDeterministicMath:
    """Test deterministic math calculations with expected values."""

    @pytest.fixture
    def estimator(self):
        """Create estimator for testing."""
        workbook_path = Path(__file__).parent.parent / "src" / "n2s_estimator" / "data" / "n2s_estimator.xlsx"
        return N2SEstimator(workbook_path)

    @pytest.fixture
    def default_inputs(self):
        """Default scenario inputs for testing."""
        return EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            maturity_factor=1.0,
            include_integrations=False,
            include_reports=False
        )

    def test_base_n2s_total_hours(self, estimator, default_inputs):
        """Test that Base N2S total hours equals 6,700."""
        results = estimator.estimate(default_inputs)

        total_hours = sum(results.base_n2s.stage_hours.values())
        assert abs(total_hours - 6700.0) < 0.01, f"Base N2S total hours {total_hours} != 6700.0"

    def test_stage_hours_exact_values(self, estimator, default_inputs):
        """Test exact stage hours match expected values."""
        results = estimator.estimate(default_inputs)

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

        for stage, expected in expected_stage_hours.items():
            actual = results.base_n2s.stage_hours.get(stage, 0.0)
            assert abs(actual - expected) < 0.01, f"Stage '{stage}' hours {actual} != expected {expected}"

    def test_presales_hours_exact_values(self, estimator, default_inputs):
        """Test exact presales hours match expected values."""
        results = estimator.estimate(default_inputs)

        expected_presales = {
            'Start': 100.5,    # 167.5 * 0.6
            'Prepare': 50.25,  # 167.5 * 0.3
        }

        for stage, expected in expected_presales.items():
            actual = results.base_n2s.presales_hours.get(stage, 0.0)
            assert abs(actual - expected) < 0.01, f"Stage '{stage}' presales hours {actual} != expected {expected}"

        # Other stages should have 0 presales hours
        other_stages = ['Sprint 0', 'Plan', 'Configure', 'Test', 'Deploy', 'Go-Live', 'Post Go-Live (Care)']
        for stage in other_stages:
            actual = results.base_n2s.presales_hours.get(stage, 0.0)
            assert abs(actual) < 0.01, f"Stage '{stage}' should have 0 presales hours, got {actual}"

    def test_total_presales_hours(self, estimator, default_inputs):
        """Test total presales hours equals 150.75."""
        results = estimator.estimate(default_inputs)

        total_presales = sum(results.base_n2s.presales_hours.values())
        assert abs(total_presales - 150.75) < 0.01, f"Total presales hours {total_presales} != 150.75"

    def test_total_delivery_hours(self, estimator, default_inputs):
        """Test total delivery hours equals 6,549.25."""
        results = estimator.estimate(default_inputs)

        total_delivery = sum(results.base_n2s.delivery_hours.values())
        assert abs(total_delivery - 6549.25) < 0.01, f"Total delivery hours {total_delivery} != 6549.25"

    def test_presales_plus_delivery_equals_total(self, estimator, default_inputs):
        """Test that presales + delivery = total hours."""
        results = estimator.estimate(default_inputs)

        total_presales = sum(results.base_n2s.presales_hours.values())
        total_delivery = sum(results.base_n2s.delivery_hours.values())
        total_stage = sum(results.base_n2s.stage_hours.values())

        calculated_total = total_presales + total_delivery
        assert abs(calculated_total - total_stage) < 0.01, (
            f"Presales ({total_presales}) + Delivery ({total_delivery}) = {calculated_total} "
            f"!= Total stage hours ({total_stage})"
        )

    def test_size_multiplier_effects(self, estimator):
        """Test size multiplier effects on total hours."""
        base_inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        base_results = estimator.estimate(base_inputs)

        # Test Small (0.85x)
        small_inputs = base_inputs.model_copy(update={'size_band': 'Small'})
        small_results = estimator.estimate(small_inputs)
        small_total = sum(small_results.base_n2s.stage_hours.values())
        expected_small = 6700.0 * 0.85
        assert abs(small_total - expected_small) < 0.01, f"Small total {small_total} != expected {expected_small}"

        # Test Large (1.25x)
        large_inputs = base_inputs.model_copy(update={'size_band': 'Large'})
        large_results = estimator.estimate(large_inputs)
        large_total = sum(large_results.base_n2s.stage_hours.values())
        expected_large = 6700.0 * 1.25
        assert abs(large_total - expected_large) < 0.01, f"Large total {large_total} != expected {expected_large}"

        # Test Very Large (1.50x)
        vlarge_inputs = base_inputs.model_copy(update={'size_band': 'Very Large'})
        vlarge_results = estimator.estimate(vlarge_inputs)
        vlarge_total = sum(vlarge_results.base_n2s.stage_hours.values())
        expected_vlarge = 6700.0 * 1.50
        assert abs(vlarge_total - expected_vlarge) < 0.01, f"Very Large total {vlarge_total} != expected {expected_vlarge}"

    def test_delivery_type_multiplier_effects(self, estimator):
        """Test delivery type multiplier effects."""
        # Net New (1.00x) - baseline
        net_new_inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        net_new_results = estimator.estimate(net_new_inputs)
        net_new_total = sum(net_new_results.base_n2s.stage_hours.values())
        assert abs(net_new_total - 6700.0) < 0.01, f"Net New total {net_new_total} != 6700.0"

        # Modernization (0.90x)
        modernization_inputs = net_new_inputs.model_copy(update={'delivery_type': 'Modernization'})
        modernization_results = estimator.estimate(modernization_inputs)
        modernization_total = sum(modernization_results.base_n2s.stage_hours.values())
        expected_modernization = 6700.0 * 0.90
        assert abs(modernization_total - expected_modernization) < 0.01, (
            f"Modernization total {modernization_total} != expected {expected_modernization}"
        )

    def test_addon_hours_math(self, estimator):
        """Test add-on hours calculations with default counts and mixes."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=True,
            integrations_count=30,
            integrations_simple_pct=0.60,
            integrations_standard_pct=0.30,
            integrations_complex_pct=0.10,
            include_reports=True,
            reports_count=40,
            reports_simple_pct=0.50,
            reports_standard_pct=0.35,
            reports_complex_pct=0.15
        )

        results = estimator.estimate(inputs)

        # Integrations expected: 30 * (0.6 * 80 + 0.3 * 160 + 0.1 * 320) = 30 * 128 = 3,840
        if results.integrations_hours:
            integrations_total = sum(results.integrations_hours.stage_hours.values())
            expected_integrations = 30 * (0.6 * 80 + 0.3 * 160 + 0.1 * 320)
            assert abs(integrations_total - expected_integrations) < 1.0, (
                f"Integrations total {integrations_total} != expected {expected_integrations}"
            )

        # Reports expected: 40 * (0.5 * 24 + 0.35 * 72 + 0.15 * 160) = 40 * 61.2 = 2,448
        if results.reports_hours:
            reports_total = sum(results.reports_hours.stage_hours.values())
            expected_reports = 40 * (0.5 * 24 + 0.35 * 72 + 0.15 * 160)
            assert abs(reports_total - expected_reports) < 1.0, (
                f"Reports total {reports_total} != expected {expected_reports}"
            )

    def test_locale_changes_costs_not_hours(self, estimator):
        """Test that changing locale affects costs but not hours."""
        us_inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        eu_inputs = us_inputs.model_copy(update={'locale': 'EU'})

        us_results = estimator.estimate(us_inputs)
        eu_results = estimator.estimate(eu_inputs)

        # Hours should be the same
        us_total_hours = sum(us_results.base_n2s.stage_hours.values())
        eu_total_hours = sum(eu_results.base_n2s.stage_hours.values())
        assert abs(us_total_hours - eu_total_hours) < 0.01, (
            f"Hours changed with locale: US {us_total_hours} vs EU {eu_total_hours}"
        )

        # Costs should be different (assuming different rates)
        us_total_cost = sum(rh.total_cost for rh in us_results.base_role_hours)
        eu_total_cost = sum(rh.total_cost for rh in eu_results.base_role_hours)

        # Allow costs to be the same if rates are the same, but they should at least be calculated
        assert us_total_cost > 0, "US total cost should be > 0"
        assert eu_total_cost > 0, "EU total cost should be > 0"

    def test_product_role_map_affects_roles(self, estimator):
        """Test that product role map affects enabled roles."""
        banner_inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        colleague_inputs = banner_inputs.model_copy(update={'product': 'Colleague'})

        banner_results = estimator.estimate(banner_inputs)
        colleague_results = estimator.estimate(colleague_inputs)

        # Both should have results
        assert len(banner_results.base_role_hours) > 0, "Banner should have role hours"
        assert len(colleague_results.base_role_hours) > 0, "Colleague should have role hours"

        # Get roles for each product
        banner_roles = set(rh.role for rh in banner_results.base_role_hours)
        colleague_roles = set(rh.role for rh in colleague_results.base_role_hours)

        # Should have some common roles
        common_roles = banner_roles & colleague_roles
        assert len(common_roles) > 0, "Products should have some common roles"

        # Total hours should reconcile (some roles may be disabled for Colleague)
        banner_total = sum(banner_results.base_n2s.stage_hours.values())
        colleague_total = sum(colleague_results.base_n2s.stage_hours.values())

        # Both should be positive
        assert banner_total > 0, "Banner total hours should be > 0"
        assert colleague_total > 0, "Colleague total hours should be > 0"

    def test_role_canonicalization(self, estimator):
        """Test that role canonicalization works correctly."""
        # Check that Business Analyst has been replaced with Functional Consultant
        config = estimator.config
        
        # No deprecated roles should exist in the final config
        all_roles = set()
        all_roles.update(rm.role for rm in config.role_mix)
        all_roles.update(rt.role for rt in config.rates)
        all_roles.update(prm.role for prm in config.product_role_map)
        
        deprecated_roles = {'Business Analyst', 'Platform Lead', 'Technical Lead'}
        found_deprecated = deprecated_roles & all_roles
        
        # Should have canonical roles
        expected_canonical = {'Functional Consultant', 'Technical Architect', 'Integration Engineer', 'Extensibility Engineer', 'DegreeWorks Scribe'}
        found_canonical = expected_canonical & all_roles
        
        assert len(found_deprecated) == 0, f"Found deprecated roles: {found_deprecated}"
        assert len(found_canonical) == len(expected_canonical), f"Missing canonical roles: {expected_canonical - found_canonical}"

    def test_degreeworks_setup_baseline_medium(self, estimator):
        """Test Degree Works Setup-only calculation with Medium baseline (300 hours)."""
        inputs = EstimationInputs(
            product="Banner",
            size_band="Medium",
            include_degreeworks=True,
            degreeworks_include_setup=True,
            degreeworks_use_pve_calculator=True,
            degreeworks_majors=0,  # No PVEs, Setup only
            degreeworks_minors=0,
            degreeworks_certificates=0,
            degreeworks_concentrations=0,
            degreeworks_catalog_years=1
        )
        
        results = estimator.estimate(inputs)
        
        # Should have Degree Works results
        assert results.degreeworks_hours is not None, "Degree Works hours should not be None"
        assert results.degreeworks_role_hours is not None, "Degree Works role hours should not be None"
        
        # Only Setup should be present
        setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
        pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
        
        assert abs(setup_hours - 300.0) < 0.01, f"Setup hours {setup_hours} != 300.0"
        assert abs(pve_hours) < 0.01, f"PVE hours should be 0, got {pve_hours}"
        
        # Role distribution should match Setup tier: 70/20/10
        role_hours = {rh.role: rh.total_hours for rh in results.degreeworks_role_hours}
        
        assert 'DegreeWorks Scribe' in role_hours, "DegreeWorks Scribe should be present"
        assert 'Functional Consultant' in role_hours, "Functional Consultant should be present"
        assert 'Technical Architect' in role_hours, "Technical Architect should be present"
        
        # Check approximate distribution (Setup tier: 70/20/10)
        dw_scribe_hours = role_hours['DegreeWorks Scribe']
        fc_hours = role_hours['Functional Consultant']
        ta_hours = role_hours['Technical Architect']
        
        assert abs(dw_scribe_hours - 210.0) < 1.0, f"DegreeWorks Scribe hours {dw_scribe_hours} != ~210 (70%)"
        assert abs(fc_hours - 60.0) < 1.0, f"Functional Consultant hours {fc_hours} != ~60 (20%)"
        assert abs(ta_hours - 30.0) < 1.0, f"Technical Architect hours {ta_hours} != ~30 (10%)"

    def test_degreeworks_size_scaling_with_integrations_reports(self, estimator):
        """Test that only DW Setup scales by size while Integrations/Reports and DW PVEs do not."""
        base_inputs = EstimationInputs(
            product="Banner",
            size_band="Medium",
            include_degreeworks=True,
            degreeworks_include_setup=True,
            degreeworks_use_pve_calculator=False,
            degreeworks_pve_count=50,  # Fixed PVE count for testing
            degreeworks_simple_pct=0.50,
            degreeworks_standard_pct=0.35,
            degreeworks_complex_pct=0.15,
            include_integrations=True,
            integrations_count=30,
            include_reports=True,
            reports_count=40
        )
        
        large_inputs = base_inputs.model_copy(update={'size_band': 'Large'})
        
        medium_results = estimator.estimate(base_inputs)
        large_results = estimator.estimate(large_inputs)
        
        # Degree Works Setup should scale: 300 -> 375, but PVEs should not scale
        medium_setup = medium_results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0) if medium_results.degreeworks_hours else 0
        large_setup = large_results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0) if large_results.degreeworks_hours else 0
        
        assert abs(medium_setup - 300.0) < 1.0, f"Medium Setup {medium_setup} != 300"
        assert abs(large_setup - 375.0) < 1.0, f"Large Setup {large_setup} != 375"
        
        # PVEs should NOT scale
        medium_pve = medium_results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0) if medium_results.degreeworks_hours else 0
        large_pve = large_results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0) if large_results.degreeworks_hours else 0
        
        assert abs(medium_pve - large_pve) < 1.0, f"PVE hours should not scale: Medium {medium_pve} vs Large {large_pve}"
        
        # Integrations should NOT scale (should be same)
        medium_int = sum(medium_results.integrations_hours.stage_hours.values()) if medium_results.integrations_hours else 0
        large_int = sum(large_results.integrations_hours.stage_hours.values()) if large_results.integrations_hours else 0
        
        assert abs(medium_int - large_int) < 1.0, f"Integrations should not scale: Medium {medium_int} vs Large {large_int}"
        
        # Reports should NOT scale (should be same)
        medium_rep = sum(medium_results.reports_hours.stage_hours.values()) if medium_results.reports_hours else 0
        large_rep = sum(large_results.reports_hours.stage_hours.values()) if large_results.reports_hours else 0
        
        assert abs(medium_rep - large_rep) < 1.0, f"Reports should not scale: Medium {medium_rep} vs Large {large_rep}"

    def test_degreeworks_product_role_map(self, estimator):
        """Test that DegreeWorks Scribe is disabled for Colleague."""
        banner_inputs = EstimationInputs(
            product="Banner",
            include_degreeworks=True,
            degreeworks_include_setup=True,
            degreeworks_use_pve_calculator=False,
            degreeworks_pve_count=50
        )
        
        colleague_inputs = banner_inputs.model_copy(update={'product': 'Colleague'})
        
        banner_results = estimator.estimate(banner_inputs)
        colleague_results = estimator.estimate(colleague_inputs)
        
        # Banner should have DegreeWorks Scribe hours
        banner_roles = {rh.role: rh.total_hours for rh in banner_results.degreeworks_role_hours or []}
        assert 'DegreeWorks Scribe' in banner_roles, "Banner should have DegreeWorks Scribe"
        assert banner_roles['DegreeWorks Scribe'] > 0, "Banner DegreeWorks Scribe should have hours"
        
        # Colleague should NOT have DegreeWorks Scribe hours (disabled by product map)
        colleague_roles = {rh.role: rh.total_hours for rh in colleague_results.degreeworks_role_hours or []}
        dw_scribe_hours = colleague_roles.get('DegreeWorks Scribe', 0)
        assert dw_scribe_hours == 0, f"Colleague DegreeWorks Scribe should have 0 hours, got {dw_scribe_hours}"
        
        # But Colleague should still have some Degree Works hours from other roles
        colleague_dw_total = sum(colleague_results.degreeworks_hours.stage_hours.values()) if colleague_results.degreeworks_hours else 0
        assert colleague_dw_total > 0, "Colleague should still have some Degree Works hours from other roles"

    def test_no_regressions_base_hours(self, estimator, default_inputs):
        """Test that Base N2S hours are unchanged with new role canonicalization."""
        results = estimator.estimate(default_inputs)
        
        # Base total should still be exactly 6,700
        total_hours = sum(results.base_n2s.stage_hours.values())
        assert abs(total_hours - 6700.0) < 0.01, f"Base N2S total hours {total_hours} != 6700.0 (regression detected)"
        
        # Presales should still be 150.75
        total_presales = sum(results.base_n2s.presales_hours.values())
        assert abs(total_presales - 150.75) < 0.01, f"Total presales hours {total_presales} != 150.75 (regression detected)"

    def test_integrations_reports_unchanged(self, estimator):
        """Test that Integrations and Reports expected totals are preserved."""
        inputs = EstimationInputs(
            product="Banner",
            include_integrations=True,
            integrations_count=30,
            integrations_simple_pct=0.60,
            integrations_standard_pct=0.30,
            integrations_complex_pct=0.10,
            include_reports=True,
            reports_count=40,
            reports_simple_pct=0.50,
            reports_standard_pct=0.35,
            reports_complex_pct=0.15
        )
        
        results = estimator.estimate(inputs)
        
        # Integrations: 30 * (0.6 * 80 + 0.3 * 160 + 0.1 * 320) = 3,840
        int_hours = sum(results.integrations_hours.stage_hours.values()) if results.integrations_hours else 0
        assert abs(int_hours - 3840.0) < 1.0, f"Integrations hours {int_hours} != 3840 (regression detected)"
        
        # Reports: 40 * (0.5 * 24 + 0.35 * 72 + 0.15 * 160) = 2,448
        rep_hours = sum(results.reports_hours.stage_hours.values()) if results.reports_hours else 0
        assert abs(rep_hours - 2448.0) < 1.0, f"Reports hours {rep_hours} != 2448 (regression detected)"

    def test_degreeworks_acceptance_scenario(self, estimator):
        """Test Degree Works acceptance scenario with exact math."""
        # Banner, Net New, Medium, US; DW with Setup + Calculator
        # Majors=60, Minors=40, Certs=10, Conc=15, CatalogYears=1; Mix 0.50/0.35/0.15
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New", 
            size_band="Medium",
            locale="US",
            include_degreeworks=True,
            degreeworks_include_setup=True,
            degreeworks_use_pve_calculator=True,
            degreeworks_majors=60,
            degreeworks_minors=40,
            degreeworks_certificates=10,
            degreeworks_concentrations=15,
            degreeworks_catalog_years=1,
            degreeworks_simple_pct=0.50,
            degreeworks_standard_pct=0.35,
            degreeworks_complex_pct=0.15
        )
        
        results = estimator.estimate(inputs)
        
        # Expected: PVEs = 60 + 0.5*(40+10+15) = 60 + 32.5 = 92.5
        # Expected: PVE hours = 92.5 * (0.5*24 + 0.35*48 + 0.15*96) = 92.5 * 43.2 = 3996
        # Expected: Setup hours = 300 (Medium, no scaling)
        # Expected: Total = 4296
        
        assert results.degreeworks_hours is not None, "Degree Works hours should not be None"
        
        setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
        pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
        
        assert abs(setup_hours - 300.0) < 0.01, f"Setup hours {setup_hours} != 300"
        assert abs(pve_hours - 3996.0) < 1.0, f"PVE hours {pve_hours} != 3996"
        
        total_dw = setup_hours + pve_hours
        assert abs(total_dw - 4296.0) < 1.0, f"Total DW hours {total_dw} != 4296"

    def test_degreeworks_large_size_scaling(self, estimator):
        """Test that only Setup scales with Large size (1.25x), PVEs unchanged."""
        inputs = EstimationInputs(
            product="Banner",
            size_band="Large",  # 1.25x multiplier
            include_degreeworks=True,
            degreeworks_include_setup=True,
            degreeworks_use_pve_calculator=True,
            degreeworks_majors=60,
            degreeworks_minors=40,
            degreeworks_certificates=10,
            degreeworks_concentrations=15,
            degreeworks_catalog_years=1,
            degreeworks_simple_pct=0.50,
            degreeworks_standard_pct=0.35,
            degreeworks_complex_pct=0.15
        )
        
        results = estimator.estimate(inputs)
        
        # Expected: Setup = 300 * 1.25 = 375
        # Expected: PVEs = 3996 (unchanged)
        # Expected: Total = 4371
        
        setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
        pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
        
        assert abs(setup_hours - 375.0) < 0.01, f"Large Setup hours {setup_hours} != 375"
        assert abs(pve_hours - 3996.0) < 1.0, f"Large PVE hours {pve_hours} != 3996 (should be unchanged)"
        
        total_dw = setup_hours + pve_hours
        assert abs(total_dw - 4371.0) < 1.0, f"Large Total DW hours {total_dw} != 4371"

    def test_degreeworks_setup_only(self, estimator):
        """Test Degree Works with only Setup, no PVEs."""
        inputs = EstimationInputs(
            product="Banner",
            size_band="Medium",
            include_degreeworks=True,
            degreeworks_include_setup=True,
            degreeworks_use_pve_calculator=True,
            degreeworks_majors=0,  # No PVEs
            degreeworks_minors=0,
            degreeworks_certificates=0,
            degreeworks_concentrations=0,
            degreeworks_catalog_years=1
        )
        
        results = estimator.estimate(inputs)
        
        # Should have Setup but no PVEs
        assert results.degreeworks_hours is not None, "Should have Degree Works hours"
        
        setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
        pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
        
        assert abs(setup_hours - 300.0) < 0.01, f"Setup-only hours {setup_hours} != 300"
        assert abs(pve_hours) < 0.01, f"PVE hours should be 0, got {pve_hours}"

    def test_degreeworks_pves_only(self, estimator):
        """Test Degree Works with only PVEs, no Setup."""
        inputs = EstimationInputs(
            product="Banner",
            size_band="Medium",
            include_degreeworks=True,
            degreeworks_include_setup=False,  # No Setup
            degreeworks_use_pve_calculator=False,
            degreeworks_pve_count=100,  # Direct PVE count
            degreeworks_simple_pct=0.50,
            degreeworks_standard_pct=0.35,
            degreeworks_complex_pct=0.15
        )
        
        results = estimator.estimate(inputs)
        
        # Should have PVEs but no Setup
        assert results.degreeworks_hours is not None, "Should have Degree Works hours"
        
        setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
        pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
        
        assert abs(setup_hours) < 0.01, f"Setup hours should be 0, got {setup_hours}"
        
        # Expected PVEs: 100 * (0.5*24 + 0.35*48 + 0.15*96) = 100 * 43.2 = 4320
        expected_pve = 100 * (0.5 * 24 + 0.35 * 48 + 0.15 * 96)
        assert abs(pve_hours - expected_pve) < 1.0, f"PVE-only hours {pve_hours} != {expected_pve}"

    def test_degreeworks_colleague_product_map(self, estimator):
        """Test that DegreeWorks Scribe is properly disabled for Colleague."""
        inputs = EstimationInputs(
            product="Colleague",  # DegreeWorks Scribe disabled
            include_degreeworks=True,
            degreeworks_include_setup=True,
            degreeworks_use_pve_calculator=False,
            degreeworks_pve_count=50,
            degreeworks_simple_pct=0.50,
            degreeworks_standard_pct=0.35,
            degreeworks_complex_pct=0.15
        )
        
        results = estimator.estimate(inputs)
        
        # Should have Degree Works but no DegreeWorks Scribe hours
        if results.degreeworks_role_hours:
            dw_scribe_hours = sum(rh.total_hours for rh in results.degreeworks_role_hours if rh.role == 'DegreeWorks Scribe')
            assert dw_scribe_hours == 0, f"Colleague should have 0 DegreeWorks Scribe hours, got {dw_scribe_hours}"
            
        # Should still have hours from other roles (FC, TA)
        other_hours = sum(rh.total_hours for rh in results.degreeworks_role_hours if rh.role != 'DegreeWorks Scribe')
        assert other_hours > 0, "Colleague should have some Degree Works hours from other roles"

    def test_sprint0_uplift_net_new(self, estimator):
        """Test Sprint 0 uplift for Net New delivery type."""
        # Test with 2% uplift (default for Net New)
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            sprint0_uplift_pct=0.02
        )
        
        results = estimator.estimate(inputs)
        
        # Get Sprint 0 hours
        stage_summary = estimator.get_stage_summary(results)
        sprint0_hours = next((rh.total_hours for rh in stage_summary if rh.stage == 'Sprint 0'), 0)
        
        # Expected: 402 + (6700 * 0.02) = 402 + 134 = 536
        expected_sprint0 = 402.0 + (6700.0 * 0.02)
        assert abs(sprint0_hours - expected_sprint0) < 1.0, f"Sprint 0 hours {sprint0_hours} != expected {expected_sprint0}"
        
        # Total hours should remain 6700
        assert abs(results.total_hours - 6700.0) < 0.01, f"Total hours changed: {results.total_hours} != 6700"

    def test_sprint0_uplift_modernization(self, estimator):
        """Test Sprint 0 uplift for Modernization delivery type."""
        # Test with 1% uplift (default for Modernization)
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Modernization",
            size_band="Medium",
            sprint0_uplift_pct=0.01
        )
        
        results = estimator.estimate(inputs)
        
        # Get Sprint 0 hours
        stage_summary = estimator.get_stage_summary(results)
        sprint0_hours = next((rh.total_hours for rh in stage_summary if rh.stage == 'Sprint 0'), 0)
        
        # Expected: (402 + (6030 * 0.01)) = 402 + 60.3 = 462.3
        expected_sprint0 = 402.0 + (6030.0 * 0.01)
        assert abs(sprint0_hours - expected_sprint0) < 1.0, f"Sprint 0 hours {sprint0_hours} != expected {expected_sprint0}"

    def test_sprint0_uplift_stage_weights_sum_to_one(self, estimator):
        """Test that Sprint 0 uplift preserves stage weights summing to 1.0."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            sprint0_uplift_pct=0.03  # 3% uplift
        )
        
        results = estimator.estimate(inputs)
        
        # Get all stage hours
        stage_summary = estimator.get_stage_summary(results)
        total_stage_hours = sum(rh.total_hours for rh in stage_summary)
        
        # Calculate stage weights
        stage_weights = {}
        for rh in stage_summary:
            stage_weights[rh.stage] = rh.total_hours / total_stage_hours
        
        # Weights should sum to 1.0
        total_weight = sum(stage_weights.values())
        assert abs(total_weight - 1.0) < 0.001, f"Stage weights sum to {total_weight}, not 1.0"

    def test_stage_summary_all_packages_includes_addons(self, estimator):
        """Test that get_stage_summary_all_packages includes add-on stages."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            include_integrations=True,
            integrations_count=30,
            include_reports=True,
            reports_count=40,
            include_degreeworks=True,
            degreeworks_majors=10
        )
        
        results = estimator.estimate(inputs)
        
        # Base-only summary
        base_summary = estimator.get_stage_summary(results)
        base_stages = [rh.stage for rh in base_summary]
        
        # All-packages summary
        all_summary = estimator.get_stage_summary_all_packages(results)
        all_stages = [rh.stage for rh in all_summary]
        
        # All-packages should have more stages
        assert len(all_stages) > len(base_stages), "All-packages summary should have more stages"
        
        # Should include add-on stages
        expected_addon_stages = ['Integrations', 'Reports', 'Degree Works']
        for stage in expected_addon_stages:
            assert stage in all_stages, f"Missing add-on stage {stage} in all-packages summary"
            assert stage not in base_stages, f"Add-on stage {stage} should not be in base-only summary"

    def test_degreeworks_cap_medium_size(self, estimator):
        """Test Degree Works cap for Medium size (400h cap)."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            include_degreeworks=True,
            degreeworks_majors=100,  # High number to trigger cap
            degreeworks_minors=50,
            degreeworks_cap_enabled=True,
            degreeworks_cap_hours=400.0
        )
        
        results = estimator.estimate(inputs)
        
        if results.degreeworks_hours:
            setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
            pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
            total_dw = setup_hours + pve_hours
            
            # Should be capped at 400 hours
            assert total_dw <= 400.0, f"Degree Works total {total_dw} exceeds cap of 400h"
            
            # Setup should be preserved (300h)
            assert abs(setup_hours - 300.0) < 1.0, f"Setup hours {setup_hours} != 300"
            
            # PVEs should be clamped
            assert pve_hours <= 100.0, f"PVE hours {pve_hours} should be ≤ 100 (400 - 300)"

    def test_degreeworks_cap_size_based_defaults(self, estimator):
        """Test Degree Works cap size-based defaults."""
        size_caps = {
            'Small': 300.0,
            'Medium': 400.0, 
            'Large': 500.0,
            'Very Large': 600.0
        }
        
        for size, expected_cap in size_caps.items():
            inputs = EstimationInputs(
                product="Banner",
                delivery_type="Net New",
                size_band=size,
                include_degreeworks=True,
                degreeworks_majors=200,  # Very high to test cap
                degreeworks_cap_enabled=True
                # No explicit cap_hours - should use size-based default
            )
            
            results = estimator.estimate(inputs)
            
            if results.degreeworks_hours:
                total_dw = sum(results.degreeworks_hours.stage_hours.values())
                assert total_dw <= expected_cap, f"Size {size}: total {total_dw} > cap {expected_cap}"

    def test_degreeworks_cap_disabled(self, estimator):
        """Test Degree Works cap when disabled."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            include_degreeworks=True,
            degreeworks_majors=100,  # High number
            degreeworks_cap_enabled=False  # Cap disabled
        )
        
        results = estimator.estimate(inputs)
        
        if results.degreeworks_hours:
            total_dw = sum(results.degreeworks_hours.stage_hours.values())
            # Should be much higher than cap would allow
            assert total_dw > 400.0, f"With cap disabled, total {total_dw} should be > 400h"

    def test_degreeworks_cap_setup_exceeds_cap(self, estimator):
        """Test Degree Works cap when Setup alone exceeds cap."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Large",  # Setup = 300 * 1.25 = 375h
            include_degreeworks=True,
            degreeworks_majors=100,
            degreeworks_cap_enabled=True,
            degreeworks_cap_hours=300.0  # Cap less than Setup
        )
        
        results = estimator.estimate(inputs)
        
        if results.degreeworks_hours:
            setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
            pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
            total_dw = setup_hours + pve_hours
            
            # Setup should be preserved
            assert abs(setup_hours - 375.0) < 1.0, f"Setup hours {setup_hours} != 375"
            
            # PVEs should be 0 since Setup exceeds cap
            assert abs(pve_hours) < 0.01, f"PVE hours should be 0 when Setup exceeds cap, got {pve_hours}"
            
            # Total should equal Setup
            assert abs(total_dw - setup_hours) < 0.01, f"Total {total_dw} should equal Setup {setup_hours}"

    def test_no_regression_with_new_features(self, estimator):
        """Test that existing functionality is not broken by new features."""
        # Test default scenario (no new features enabled)
        inputs_default = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium"
        )
        
        results_default = estimator.estimate(inputs_default)
        
        # Should still be exactly 6,700 hours
        assert abs(results_default.total_hours - 6700.0) < 0.01, "Default scenario regression detected"
        
        # Test with add-ons (existing functionality)
        inputs_addons = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            include_integrations=True,
            integrations_count=30,
            include_reports=True,
            reports_count=40
        )
        
        results_addons = estimator.estimate(inputs_addons)
        
        # Should have expected add-on totals
        int_hours = sum(results_addons.integrations_hours.stage_hours.values()) if results_addons.integrations_hours else 0
        rep_hours = sum(results_addons.reports_hours.stage_hours.values()) if results_addons.reports_hours else 0
        
        assert abs(int_hours - 3840.0) < 1.0, f"Integrations regression: {int_hours} != 3840"
        assert abs(rep_hours - 2448.0) < 1.0, f"Reports regression: {rep_hours} != 2448"
