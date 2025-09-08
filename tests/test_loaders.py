"""Tests for configuration loaders and data validation."""

from pathlib import Path

import pytest

from src.n2s_estimator.engine.loader import ConfigurationLoader
from src.n2s_estimator.engine.validators import ConfigurationValidator


class TestConfigurationLoader:
    """Test configuration loading and validation."""

    @pytest.fixture
    def workbook_path(self):
        """Get path to test workbook."""
        return Path(__file__).parent.parent / "src" / "n2s_estimator" / "data" / "n2s_estimator.xlsx"

    @pytest.fixture
    def config(self, workbook_path):
        """Load configuration for testing."""
        loader = ConfigurationLoader(workbook_path)
        return loader.load_configuration()

    def test_stage_weights_sum_to_one(self, config):
        """Test that stage weights sum to 1.0."""
        total_weight = sum(sw.weight for sw in config.stage_weights)
        assert abs(total_weight - 1.0) < 0.001, f"Stage weights sum to {total_weight}, should be 1.0"

    def test_stage_weights_structure(self, config):
        """Test stage weights structure and expected stages."""
        expected_stages = [
            'Start', 'Prepare', 'Sprint 0', 'Plan', 'Configure',
            'Test', 'Deploy', 'Go-Live', 'Post Go-Live (Care)'
        ]

        actual_stages = [sw.stage for sw in config.stage_weights]
        assert actual_stages == expected_stages, f"Expected stages {expected_stages}, got {actual_stages}"

        # Check specific weights match expected values
        expected_weights = {
            'Start': 0.025,
            'Prepare': 0.025,
            'Sprint 0': 0.060,
            'Plan': 0.100,
            'Configure': 0.340,
            'Test': 0.200,
            'Deploy': 0.100,
            'Go-Live': 0.060,
            'Post Go-Live (Care)': 0.090
        }

        for sw in config.stage_weights:
            expected = expected_weights[sw.stage]
            assert abs(sw.weight - expected) < 0.001, f"Stage {sw.stage} weight {sw.weight} != expected {expected}"

    def test_role_mix_sums_to_one(self, config):
        """Test that each stage's role mix sums to 1.0."""
        stages = set(rm.stage for rm in config.role_mix)

        for stage in stages:
            stage_roles = [rm for rm in config.role_mix if rm.stage == stage]
            total_pct = sum(rm.pct for rm in stage_roles)
            assert abs(total_pct - 1.0) < 0.01, f"Stage '{stage}' role mix sums to {total_pct}, should be 1.0"

    def test_delivery_mix_sums_to_one(self, config):
        """Test that delivery mix percentages sum to 1.0."""
        for dm in config.delivery_mix:
            total_pct = dm.onshore_pct + dm.offshore_pct + dm.partner_pct
            role_desc = f"role '{dm.role}'" if dm.role else "global"
            assert abs(total_pct - 1.0) < 0.001, f"Delivery mix for {role_desc} sums to {total_pct}, should be 1.0"

    def test_baseline_hours(self, config):
        """Test that baseline hours is set correctly."""
        assert config.baseline_hours == 6700.0, f"Baseline hours {config.baseline_hours} != 6700.0"

    def test_rates_exist_for_locale(self, config):
        """Test that rates exist for selected locale."""
        # Should have rates for US locale at minimum
        us_rates = [r for r in config.rates if r.locale == 'US']
        assert len(us_rates) > 0, "No rates found for US locale"

        # Check that we have rates for key roles
        key_roles = ['Project Manager', 'Solution Architect', 'Technical Lead']
        us_roles = [r.role for r in us_rates]

        for role in key_roles:
            assert role in us_roles, f"No US rate found for role '{role}'"

    def test_addon_packages_structure(self, config):
        """Test add-on packages structure."""
        package_names = [p.name for p in config.addon_packages]
        expected_packages = ['Integrations', 'Reports']

        for expected in expected_packages:
            assert expected in package_names, f"Missing add-on package '{expected}'"

        # Check tier structure
        for package in config.addon_packages:
            tier_names = [t.name for t in package.tiers]
            expected_tiers = ['Simple', 'Standard', 'Complex']

            for expected_tier in expected_tiers:
                assert expected_tier in tier_names, f"Missing tier '{expected_tier}' in package '{package.name}'"

    def test_addon_tier_role_distributions(self, config):
        """Test that add-on tier role distributions sum to 1.0."""
        for package in config.addon_packages:
            for tier in package.tiers:
                total_pct = sum(tier.role_distribution.values())
                assert abs(total_pct - 1.0) < 0.01, (
                    f"Package '{package.name}' tier '{tier.name}' role distribution "
                    f"sums to {total_pct}, should be 1.0"
                )

    def test_product_role_map(self, config):
        """Test product role map structure."""
        if config.product_role_map:
            roles = [prm.role for prm in config.product_role_map]

            # Should have key roles
            key_roles = ['Project Manager', 'Solution Architect', 'Technical Lead']
            for role in key_roles:
                assert role in roles, f"Product role map missing role '{role}'"

            # Check that Banner and Colleague flags are boolean
            for prm in config.product_role_map:
                assert isinstance(prm.banner_enabled, bool), f"Banner enabled for {prm.role} is not boolean"
                assert isinstance(prm.colleague_enabled, bool), f"Colleague enabled for {prm.role} is not boolean"
                assert prm.multiplier >= 0.0, f"Multiplier for {prm.role} is negative"


class TestConfigurationValidator:
    """Test configuration validation."""

    @pytest.fixture
    def workbook_path(self):
        """Get path to test workbook."""
        return Path(__file__).parent.parent / "src" / "n2s_estimator" / "data" / "n2s_estimator.xlsx"

    @pytest.fixture
    def config(self, workbook_path):
        """Load configuration for testing."""
        loader = ConfigurationLoader(workbook_path)
        return loader.load_configuration()

    @pytest.fixture
    def validator(self, config):
        """Create validator for testing."""
        return ConfigurationValidator(config)

    def test_validation_passes(self, validator):
        """Test that validation passes for good configuration."""
        warnings = validator.validate_all()

        # Should have no validation errors (warnings about methodology drift are OK)
        errors = [w for w in warnings if 'Error:' in w]
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_stage_weights_validation(self, validator):
        """Test stage weights validation."""
        try:
            validator.validate_stage_weights()
        except Exception as e:
            pytest.fail(f"Stage weights validation failed: {e}")

    def test_role_mix_validation(self, validator):
        """Test role mix validation."""
        try:
            validator.validate_role_mix()
        except Exception as e:
            pytest.fail(f"Role mix validation failed: {e}")

    def test_delivery_mix_validation(self, validator):
        """Test delivery mix validation."""
        try:
            validator.validate_delivery_mix()
        except Exception as e:
            pytest.fail(f"Delivery mix validation failed: {e}")

    def test_addon_tiers_validation(self, validator):
        """Test add-on tiers validation."""
        try:
            validator.validate_addon_tiers()
        except Exception as e:
            pytest.fail(f"Add-on tiers validation failed: {e}")

