"""Data loader for N2S Estimator configuration from Excel workbook."""

from pathlib import Path

import pandas as pd

from .datatypes import (
    ActivityDef,
    AddOnPackage,
    AddOnTier,
    ConfigurationData,
    DeliveryMix,
    ProductRoleToggle,
    RateCard,
    RoleMix,
    StagePresales,
    StageWeight,
)


class ConfigurationLoader:
    """Loads and validates configuration data from Excel workbook."""

    def __init__(self, workbook_path: Path) -> None:
        """Initialize loader with workbook path."""
        self.workbook_path = workbook_path
        self._sheets: dict[str, pd.DataFrame] = {}

    def load_configuration(self) -> ConfigurationData:
        """Load complete configuration from workbook."""
        self._load_all_sheets()

        return ConfigurationData(
            baseline_hours=self._load_baseline_hours(),
            stage_weights=self._load_stage_weights(),
            stages_presales=self._load_stages_presales(),
            activities=self._load_activities(),
            role_mix=self._load_role_mix(),
            rates=self._load_rates(),
            delivery_mix=self._load_delivery_mix(),
            addon_packages=self._load_addon_packages(),
            product_role_map=self._load_product_role_map()
        )

    def _load_all_sheets(self) -> None:
        """Load all sheets from workbook into memory."""
        try:
            excel_file = pd.ExcelFile(self.workbook_path)
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(self.workbook_path, sheet_name=sheet_name)
                # Clean up: strip whitespace from string columns and drop completely empty rows
                df = df.dropna(how='all')
                for col in df.select_dtypes(include=['object']).columns:
                    df[col] = df[col].astype(str).str.strip()
                self._sheets[sheet_name] = df
        except Exception as e:
            raise ValueError(f"Failed to load workbook {self.workbook_path}: {e}")

    def _load_baseline_hours(self) -> float:
        """Load baseline hours from Inputs sheet."""
        inputs_df = self._sheets.get('Inputs')
        if inputs_df is None:
            return 6700.0  # Default

        baseline_row = inputs_df[inputs_df['Parameter'] == 'Baseline Total Hours']
        if baseline_row.empty:
            return 6700.0

        return float(baseline_row['Value'].iloc[0])

    def _load_stage_weights(self) -> list[StageWeight]:
        """Load stage weights from Stage Weights sheet."""
        df = self._sheets['Stage Weights']
        weights = []

        for _, row in df.iterrows():
            weights.append(StageWeight(
                phase=row['Phase'],
                stage=row['Stage'],
                weight=float(row['Stage Weight %'])
            ))

        # Validate weights sum to 1.0
        total_weight = sum(w.weight for w in weights)
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Stage weights must sum to 1.0, got {total_weight}")

        return weights

    def _load_stages_presales(self) -> list[StagePresales]:
        """Load stages default presales percentages."""
        df = self._sheets['Stages']
        presales = []

        for _, row in df.iterrows():
            presales.append(StagePresales(
                stage=row['Stage'],
                default_pct=float(row['Default Presales %'])
            ))

        return presales

    def _load_activities(self) -> list[ActivityDef]:
        """Load activities from Activities sheet."""
        if 'Activities' not in self._sheets:
            return []

        df = self._sheets['Activities']
        activities = []

        for _, row in df.iterrows():
            activities.append(ActivityDef(
                stage=row['Stage'],
                activity=row['Activity'],
                weight=float(row['Activity Weight']),
                is_presales=bool(row['Is Presales'])
            ))

        return activities

    def _load_role_mix(self) -> list[RoleMix]:
        """Load role mix from Role Mix sheet."""
        df = self._sheets['Role Mix']
        role_mix = []

        for _, row in df.iterrows():
            # Skip "Total" rows
            if pd.isna(row['Role']) or row['Role'] == '' or 'Total' in str(row['Role']):
                continue

            role_mix.append(RoleMix(
                stage=row['Stage'],
                role=row['Role'],
                pct=float(row['Role Mix %'])
            ))

        # Validate each stage's role mix sums to 1.0
        stages = set(rm.stage for rm in role_mix)
        for stage in stages:
            stage_roles = [rm for rm in role_mix if rm.stage == stage]
            total_pct = sum(rm.pct for rm in stage_roles)
            if abs(total_pct - 1.0) > 0.01:
                print(f"Warning: Stage '{stage}' role mix sums to {total_pct}, not 1.0")

        return role_mix

    def _load_rates(self) -> list[RateCard]:
        """Load rate cards from Rates (Locales) sheet, fallback to Rates sheet."""
        # Try Rates (Locales) first
        if 'Rates (Locales)' in self._sheets:
            df = self._sheets['Rates (Locales)']
            rates = []

            for _, row in df.iterrows():
                rates.append(RateCard(
                    role=row['Role'],
                    locale=row['Locale'],
                    onshore=float(row['Onshore Rate']),
                    offshore=float(row['Offshore Rate']),
                    partner=float(row['Partner Rate'])
                ))

            return rates

        # Fallback to Rates sheet (assume US locale)
        df = self._sheets['Rates']
        rates = []

        for _, row in df.iterrows():
            rates.append(RateCard(
                role=row['Role'],
                locale='US',
                onshore=float(row['Onshore Rate']),
                offshore=float(row['Offshore Rate']),
                partner=float(row['Partner Rate'])
            ))

        return rates

    def _load_delivery_mix(self) -> list[DeliveryMix]:
        """Load delivery mix from Delivery Mix sheet."""
        df = self._sheets['Delivery Mix']
        delivery_mix = []

        for _, row in df.iterrows():
            # Handle global row (Role is None/NaN)
            role = None if pd.isna(row['Role']) or row['Role'] == 'nan' else row['Role']

            delivery_mix.append(DeliveryMix(
                role=role,
                onshore_pct=float(row['Onshore %']),
                offshore_pct=float(row['Offshore %']),
                partner_pct=float(row['Partner %'])
            ))

        return delivery_mix

    def _load_addon_packages(self) -> list[AddOnPackage]:
        """Load add-on packages from Add-On Catalog sheet."""
        if 'Add-On Catalog' not in self._sheets:
            return []

        df = self._sheets['Add-On Catalog']
        packages_dict: dict[str, dict[str, dict[str, float | dict[str, float]]]] = {}

        # Group by package and tier
        for _, row in df.iterrows():
            package_name = row['Package']
            tier_name = row['Tier']
            role = row['Role']
            role_pct = float(row['Role %'])
            unit_hours = float(row['Unit Hours'])

            if package_name not in packages_dict:
                packages_dict[package_name] = {}

            if tier_name not in packages_dict[package_name]:
                packages_dict[package_name][tier_name] = {
                    'unit_hours': unit_hours,
                    'role_distribution': {}
                }

            tier_data = packages_dict[package_name][tier_name]
            if isinstance(tier_data['role_distribution'], dict):
                tier_data['role_distribution'][role] = role_pct

        # Convert to AddOnPackage objects
        packages = []
        for package_name, tiers_dict in packages_dict.items():
            tiers = []
            for tier_name, tier_data in tiers_dict.items():
                unit_hours = tier_data['unit_hours']
                role_dist = tier_data['role_distribution']
                if isinstance(unit_hours, (int, float)) and isinstance(role_dist, dict):
                    tiers.append(AddOnTier(
                        name=tier_name,
                        unit_hours=float(unit_hours),
                        role_distribution=role_dist
                    ))

            packages.append(AddOnPackage(
                name=package_name,
                tiers=tiers
            ))

        return packages

    def _load_product_role_map(self) -> list[ProductRoleToggle]:
        """Load product role map from Product Role Map sheet."""
        if 'Product Role Map' not in self._sheets:
            return []

        df = self._sheets['Product Role Map']
        role_map = []

        for _, row in df.iterrows():
            role_map.append(ProductRoleToggle(
                role=row['Role'],
                banner_enabled=bool(row['Banner Enabled']),
                colleague_enabled=bool(row['Colleague Enabled']),
                multiplier=float(row.get('Multiplier', 1.0))
            ))

        return role_map
