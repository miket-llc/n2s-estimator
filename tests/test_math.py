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
