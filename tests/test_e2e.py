"""End-to-end integration tests for N2S Estimator."""

from pathlib import Path

import pytest

from src.n2s_estimator.engine.datatypes import EstimationInputs
from src.n2s_estimator.engine.orchestrator import N2SEstimator
from src.n2s_estimator.export.excel import ExcelExporter


class TestEndToEnd:
    """End-to-end integration tests."""

    @pytest.fixture
    def estimator(self):
        """Create estimator for testing."""
        workbook_path = Path(__file__).parent.parent / "src" / "n2s_estimator" / "data" / "n2s_estimator.xlsx"
        return N2SEstimator(workbook_path)

    def test_default_scenario_base_only(self, estimator):
        """Test default scenario with Base N2S only."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        results = estimator.estimate(inputs)

        # Should have base results
        assert results.base_n2s is not None
        assert len(results.base_role_hours) > 0

        # Should not have add-on results
        assert results.integrations_hours is None
        assert results.integrations_role_hours is None
        assert results.reports_hours is None
        assert results.reports_role_hours is None

        # Total hours should be approximately 6,700
        assert abs(results.total_hours - 6700.0) < 1.0

        # Should have positive costs
        assert results.total_cost > 0
        assert results.total_delivery_cost > 0

        # Presales hours should be 150.75
        assert abs(results.total_presales_hours - 150.75) < 0.01

    def test_scenario_with_addons_enabled(self, estimator):
        """Test scenario with add-ons enabled."""
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

        # Should have all results
        assert results.base_n2s is not None
        assert len(results.base_role_hours) > 0
        assert results.integrations_hours is not None
        assert results.integrations_role_hours is not None
        assert results.reports_hours is not None
        assert results.reports_role_hours is not None

        # Total hours should be greater than base
        base_hours = sum(results.base_n2s.stage_hours.values())
        assert results.total_hours > base_hours

        # Should have reasonable add-on hours
        int_hours = sum(results.integrations_hours.stage_hours.values())
        rep_hours = sum(results.reports_hours.stage_hours.values())

        assert int_hours > 0
        assert rep_hours > 0

        # Total should reconcile
        expected_total = base_hours + int_hours + rep_hours
        assert abs(results.total_hours - expected_total) < 0.01

    def test_product_colleague_with_role_toggles(self, estimator):
        """Test Colleague product with role map toggles."""
        inputs = EstimationInputs(
            product="Colleague",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        results = estimator.estimate(inputs)

        # Should have results
        assert results.base_n2s is not None
        assert len(results.base_role_hours) > 0

        # Should have positive hours and costs
        assert results.total_hours > 0
        assert results.total_cost > 0

        # Get enabled roles
        colleague_roles = {rh.role for rh in results.base_role_hours}

        # Should have some roles enabled
        assert len(colleague_roles) > 0

        # Compare with Banner to see differences
        banner_inputs = inputs.model_copy(update={'product': 'Banner'})
        banner_results = estimator.estimate(banner_inputs)
        banner_roles = {rh.role for rh in banner_results.base_role_hours}

        # Should have some common roles
        common_roles = colleague_roles & banner_roles
        assert len(common_roles) > 0

    def test_size_and_delivery_type_combinations(self, estimator):
        """Test various size and delivery type combinations."""
        base_inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        # Test size variations
        sizes = ["Small", "Medium", "Large", "Very Large"]
        size_multipliers = [0.85, 1.00, 1.25, 1.50]

        for size, multiplier in zip(sizes, size_multipliers, strict=False):
            inputs = base_inputs.model_copy(update={'size_band': size})
            results = estimator.estimate(inputs)

            expected_hours = 6700.0 * multiplier
            assert abs(results.total_hours - expected_hours) < 1.0, (
                f"Size {size}: expected {expected_hours}, got {results.total_hours}"
            )

        # Test delivery type variations
        delivery_types = ["Net New", "Modernization"]
        delivery_multipliers = [1.00, 0.90]

        for delivery_type, multiplier in zip(delivery_types, delivery_multipliers, strict=False):
            inputs = base_inputs.model_copy(update={'delivery_type': delivery_type})
            results = estimator.estimate(inputs)

            expected_hours = 6700.0 * multiplier
            assert abs(results.total_hours - expected_hours) < 1.0, (
                f"Delivery type {delivery_type}: expected {expected_hours}, got {results.total_hours}"
            )

    def test_all_locales_work(self, estimator):
        """Test that all supported locales work."""
        base_inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        locales = ["US", "Canada", "UK", "EU", "ANZ", "MENA"]

        for locale in locales:
            inputs = base_inputs.model_copy(update={'locale': locale})
            results = estimator.estimate(inputs)

            # Should complete without errors
            assert results.total_hours > 0, f"Locale {locale} failed: no hours"
            assert results.total_cost > 0, f"Locale {locale} failed: no cost"

            # Hours should be consistent across locales
            assert abs(results.total_hours - 6700.0) < 1.0, (
                f"Locale {locale} hours {results.total_hours} != 6700"
            )

    def test_validation_warnings(self, estimator):
        """Test that validation warnings are generated appropriately."""
        warnings = estimator.get_validation_warnings()

        # Should not have critical errors
        errors = [w for w in warnings if 'Error:' in w]
        assert len(errors) == 0, f"Validation errors found: {errors}"

    def test_package_summaries(self, estimator):
        """Test package summaries functionality."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=True,
            integrations_count=10,  # Small number for testing
            include_reports=True,
            reports_count=5  # Small number for testing
        )

        results = estimator.estimate(inputs)
        summaries = estimator.get_package_summaries(results)

        # Should have all packages
        assert 'Base N2S' in summaries
        assert 'Integrations' in summaries
        assert 'Reports' in summaries

        # Base should always be enabled
        assert summaries['Base N2S']['enabled'] is True
        assert summaries['Base N2S']['hours'] > 0
        assert summaries['Base N2S']['cost'] > 0

        # Add-ons should be enabled
        assert summaries['Integrations']['enabled'] is True
        assert summaries['Integrations']['hours'] > 0

        assert summaries['Reports']['enabled'] is True
        assert summaries['Reports']['hours'] > 0

    def test_delivery_split_summary(self, estimator):
        """Test delivery split summary functionality."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        results = estimator.estimate(inputs)
        split_summary = estimator.get_delivery_split_summary(results)

        # Should have all splits
        assert 'onshore' in split_summary
        assert 'offshore' in split_summary
        assert 'partner' in split_summary

        # Percentages should sum to 1.0
        total_hours_pct = (
            split_summary['onshore']['hours_pct'] +
            split_summary['offshore']['hours_pct'] +
            split_summary['partner']['hours_pct']
        )
        assert abs(total_hours_pct - 1.0) < 0.01, f"Hours percentages sum to {total_hours_pct}"

        total_cost_pct = (
            split_summary['onshore']['cost_pct'] +
            split_summary['offshore']['cost_pct'] +
            split_summary['partner']['cost_pct']
        )
        assert abs(total_cost_pct - 1.0) < 0.01, f"Cost percentages sum to {total_cost_pct}"

    def test_role_and_stage_summaries(self, estimator):
        """Test role and stage summary functionality."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=False,
            include_reports=False
        )

        results = estimator.estimate(inputs)

        # Role summary
        role_summary = estimator.get_role_summary(results)
        assert len(role_summary) > 0

        # Should be sorted by cost (descending)
        costs = [rh.total_cost for rh in role_summary]
        assert costs == sorted(costs, reverse=True), "Role summary not sorted by cost"

        # Stage summary
        stage_summary = estimator.get_stage_summary(results)
        assert len(stage_summary) > 0

        # Should have expected stages
        stage_names = [rh.stage for rh in stage_summary]
        expected_stages = [
            'Start', 'Prepare', 'Sprint 0', 'Plan', 'Configure',
            'Test', 'Deploy', 'Go-Live', 'Post Go-Live (Care)'
        ]

        for stage in expected_stages:
            assert stage in stage_names, f"Missing stage {stage} in summary"

    def test_excel_export(self, estimator):
        """Test Excel export functionality."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=True,
            integrations_count=5,
            include_reports=True,
            reports_count=3
        )

        results = estimator.estimate(inputs)

        # Test Excel export
        exporter = ExcelExporter()
        excel_data = exporter.export_to_excel(results, estimator)

        # Should generate bytes
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0

        # Should be a valid Excel file (basic check)
        # Excel files start with PK (ZIP signature)
        assert excel_data[:2] == b'PK', "Excel file should start with PK signature"

    def test_sprint0_uplift_integration(self, estimator):
        """Test Sprint 0 uplift integration with full estimation pipeline."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            sprint0_uplift_pct=0.02,
            include_integrations=True,
            integrations_count=10,
            include_reports=True,
            reports_count=5
        )

        results = estimator.estimate(inputs)

        # Should complete without errors
        assert results.total_hours > 0
        assert results.total_cost > 0

        # Sprint 0 should have uplift applied
        stage_summary = estimator.get_stage_summary(results)
        sprint0_hours = next((rh.total_hours for rh in stage_summary if rh.stage == 'Sprint 0'), 0)
        assert sprint0_hours > 402.0, f"Sprint 0 hours {sprint0_hours} should be > 402 (uplift applied)"

    def test_stage_summary_toggle_integration(self, estimator):
        """Test Stage Summary toggle functionality integration."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_integrations=True,
            integrations_count=20,
            include_reports=True,
            reports_count=15,
            include_degreeworks=True,
            degreeworks_majors=5
        )

        results = estimator.estimate(inputs)

        # Test both summary types
        base_summary = estimator.get_stage_summary(results)
        all_summary = estimator.get_stage_summary_all_packages(results)

        # Base summary should have fewer stages
        assert len(base_summary) < len(all_summary), "Base summary should have fewer stages"

        # All summary should include add-on stages
        all_stages = [rh.stage for rh in all_summary]
        assert 'Integrations' in all_stages
        assert 'Reports' in all_stages
        assert 'Degree Works' in all_stages

        # Base summary should not include add-on stages
        base_stages = [rh.stage for rh in base_summary]
        assert 'Integrations' not in base_stages
        assert 'Reports' not in base_stages
        assert 'Degree Works' not in base_stages

    def test_degreeworks_cap_integration(self, estimator):
        """Test Degree Works cap integration with full estimation pipeline."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            include_degreeworks=True,
            degreeworks_majors=50,  # High number to test cap
            degreeworks_minors=25,
            degreeworks_cap_enabled=True,
            degreeworks_cap_hours=400.0
        )

        results = estimator.estimate(inputs)

        # Should complete without errors
        assert results.total_hours > 0
        assert results.total_cost > 0

        # Degree Works should be capped
        if results.degreeworks_hours:
            total_dw = sum(results.degreeworks_hours.stage_hours.values())
            assert total_dw <= 400.0, f"Degree Works total {total_dw} exceeds cap of 400h"

    def test_all_new_features_together(self, estimator):
        """Test all new features working together."""
        inputs = EstimationInputs(
            product="Banner",
            delivery_type="Net New",
            size_band="Medium",
            locale="US",
            # Sprint 0 uplift
            sprint0_uplift_pct=0.02,
            # Add-ons
            include_integrations=True,
            integrations_count=15,
            include_reports=True,
            reports_count=10,
            include_degreeworks=True,
            degreeworks_majors=20,
            # Degree Works cap
            degreeworks_cap_enabled=True,
            degreeworks_cap_hours=400.0
        )

        results = estimator.estimate(inputs)

        # Should complete without errors
        assert results.total_hours > 0
        assert results.total_cost > 0

        # Test Sprint 0 uplift
        stage_summary = estimator.get_stage_summary(results)
        sprint0_hours = next((rh.total_hours for rh in stage_summary if rh.stage == 'Sprint 0'), 0)
        assert sprint0_hours > 402.0, "Sprint 0 uplift not applied"

        # Test Stage Summary toggle
        base_summary = estimator.get_stage_summary(results)
        all_summary = estimator.get_stage_summary_all_packages(results)
        assert len(all_summary) > len(base_summary), "Stage Summary toggle not working"

        # Test Degree Works cap
        if results.degreeworks_hours:
            total_dw = sum(results.degreeworks_hours.stage_hours.values())
            assert total_dw <= 400.0, "Degree Works cap not working"

    def test_ui_compatibility(self, estimator):
        """Test that new features are compatible with UI expectations."""
        # Test that all new fields have sensible defaults
        inputs = EstimationInputs()

        # New fields should have defaults
        assert hasattr(inputs, 'sprint0_uplift_pct')
        assert hasattr(inputs, 'degreeworks_cap_enabled')
        assert hasattr(inputs, 'degreeworks_cap_hours')

        # Defaults should be reasonable
        assert 0.0 <= inputs.sprint0_uplift_pct <= 0.05
        assert isinstance(inputs.degreeworks_cap_enabled, bool)
        assert inputs.degreeworks_cap_hours is None or inputs.degreeworks_cap_hours > 0

        # Test estimation with defaults
        results = estimator.estimate(inputs)
        assert results.total_hours > 0
        assert results.total_cost > 0

