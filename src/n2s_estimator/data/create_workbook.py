"""Script to create the initial n2s_estimator.xlsx workbook with all required sheets."""

from pathlib import Path

import pandas as pd


def create_workbook() -> None:
    """Create the n2s_estimator.xlsx workbook with all required data."""
    workbook_path = Path(__file__).parent / "n2s_estimator.xlsx"

    with pd.ExcelWriter(workbook_path, engine='openpyxl') as writer:
        # Inputs sheet
        inputs_data = pd.DataFrame({
            'Parameter': ['Baseline Total Hours'],
            'Value': [6700]
        })
        inputs_data.to_excel(writer, sheet_name='Inputs', index=False)

        # Stage Weights sheet
        stage_weights_data = pd.DataFrame({
            'Phase': ['Discovery', 'Discovery', 'Build', 'Build', 'Build', 'Build', 'Build', 'Optimize', 'Optimize'],
            'Stage': ['Start', 'Prepare', 'Sprint 0', 'Plan', 'Configure', 'Test', 'Deploy', 'Go-Live', 'Post Go-Live (Care)'],
            'Stage Weight %': [0.025, 0.025, 0.060, 0.100, 0.340, 0.200, 0.100, 0.060, 0.090]
        })
        stage_weights_data.to_excel(writer, sheet_name='Stage Weights', index=False)

        # Stages sheet (default presales percentages)
        stages_data = pd.DataFrame({
            'Phase': ['Discovery', 'Discovery', 'Build', 'Build', 'Build', 'Build', 'Build', 'Optimize', 'Optimize'],
            'Stage': ['Start', 'Prepare', 'Sprint 0', 'Plan', 'Configure', 'Test', 'Deploy', 'Go-Live', 'Post Go-Live (Care)'],
            'Default Presales %': [0.6, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        })
        stages_data.to_excel(writer, sheet_name='Stages', index=False)

        # Activities sheet (with presales flags) - configured for expected presales percentages
        activities_data = pd.DataFrame({
            'Stage': ['Start', 'Start', 'Prepare', 'Prepare'],
            'Activity': ['Discovery Planning', 'Initial Assessment', 'Requirements Gathering', 'Solution Design'],
            'Activity Weight': [0.6, 0.4, 0.3, 0.7],  # Start: 60% presales, Prepare: 30% presales
            'Is Presales': [True, False, True, False]  # Only Discovery Planning and Requirements are presales
        })
        activities_data.to_excel(writer, sheet_name='Activities', index=False)

        # Role Mix sheet (per stage role distributions) - NO TOTAL ROWS
        role_mix_data = pd.DataFrame({
            'Stage': ['Start', 'Start', 'Start', 'Start', 'Start',
                     'Prepare', 'Prepare', 'Prepare', 'Prepare', 'Prepare',
                     'Sprint 0', 'Sprint 0', 'Sprint 0', 'Sprint 0', 'Sprint 0',
                     'Plan', 'Plan', 'Plan', 'Plan', 'Plan',
                     'Configure', 'Configure', 'Configure', 'Configure', 'Configure',
                     'Test', 'Test', 'Test', 'Test', 'Test',
                     'Deploy', 'Deploy', 'Deploy', 'Deploy', 'Deploy',
                     'Go-Live', 'Go-Live', 'Go-Live', 'Go-Live', 'Go-Live',
                     'Post Go-Live (Care)', 'Post Go-Live (Care)', 'Post Go-Live (Care)', 'Post Go-Live (Care)', 'Post Go-Live (Care)'],
            'Role': ['Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer'],
            'Role Mix %': [0.20, 0.30, 0.25, 0.15, 0.10,
                          0.15, 0.35, 0.25, 0.20, 0.05,
                          0.15, 0.25, 0.35, 0.15, 0.10,
                          0.25, 0.20, 0.30, 0.15, 0.10,
                          0.10, 0.15, 0.45, 0.20, 0.10,
                          0.15, 0.10, 0.20, 0.15, 0.40,
                          0.20, 0.15, 0.35, 0.10, 0.20,
                          0.25, 0.20, 0.30, 0.15, 0.10,
                          0.30, 0.25, 0.20, 0.15, 0.10]
        })
        role_mix_data.to_excel(writer, sheet_name='Role Mix', index=False)

        # Rates sheet (placeholder rates)
        rates_data = pd.DataFrame({
            'Role': ['Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Integration Engineer', 'Technical Architect', 'Integration Lead', 'Reporting Consultant'],
            'Onshore Rate': [150, 175, 160, 140, 130, 170, 180, 165, 155],
            'Offshore Rate': [75, 90, 85, 70, 65, 85, 95, 80, 80],
            'Partner Rate': [120, 140, 130, 110, 100, 135, 145, 125, 125]
        })
        rates_data.to_excel(writer, sheet_name='Rates', index=False)

        # Delivery Mix sheet (global and per-role overrides)
        delivery_mix_data = pd.DataFrame({
            'Role': [None, 'Project Manager', 'Solution Architect'],
            'Onshore %': [0.70, 0.80, 0.75],
            'Offshore %': [0.20, 0.15, 0.20],
            'Partner %': [0.10, 0.05, 0.05]
        })
        delivery_mix_data.to_excel(writer, sheet_name='Delivery Mix', index=False)

        # Legacy→N2S Mapping sheet
        mapping_data = pd.DataFrame({
            'Legacy Phase': ['Discover', 'Discover', 'Design', 'Design', 'Build', 'Deploy', 'Support'],
            'N2S Stage': ['Start', 'Prepare', 'Sprint 0', 'Configure', 'Configure', 'Deploy', 'Post Go-Live (Care)'],
            'Allocation %': [0.5, 0.5, 0.4, 0.6, 1.0, 1.0, 1.0]
        })
        mapping_data.to_excel(writer, sheet_name='Legacy→N2S Mapping', index=False)

        # Add-On Catalog sheet - role percentages must sum to 1.0 per tier
        addon_catalog_data = pd.DataFrame({
            'Package': [
                'Integrations', 'Integrations', 'Integrations', 'Integrations',
                'Integrations', 'Integrations', 'Integrations', 'Integrations',
                'Integrations', 'Integrations', 'Integrations', 'Integrations',
                'Reports', 'Reports', 'Reports', 'Reports',
                'Reports', 'Reports', 'Reports', 'Reports',
                'Reports', 'Reports', 'Reports', 'Reports'
            ],
            'Tier': [
                'Simple', 'Simple', 'Simple', 'Simple',
                'Standard', 'Standard', 'Standard', 'Standard',
                'Complex', 'Complex', 'Complex', 'Complex',
                'Simple', 'Simple', 'Simple', 'Simple',
                'Standard', 'Standard', 'Standard', 'Standard',
                'Complex', 'Complex', 'Complex', 'Complex'
            ],
            'Role': [
                'Integration Engineer', 'Technical Architect', 'QA Engineer', 'Project Manager',
                'Integration Engineer', 'Technical Architect', 'QA Engineer', 'Project Manager',
                'Integration Engineer', 'Technical Architect', 'Integration Lead', 'QA Engineer',
                'Reporting Consultant', 'Solution Architect', 'QA Engineer', 'Project Manager',
                'Reporting Consultant', 'Solution Architect', 'QA Engineer', 'Project Manager',
                'Reporting Consultant', 'Solution Architect', 'Technical Lead', 'QA Engineer'
            ],
            'Unit Hours': [
                80, 80, 80, 80,
                160, 160, 160, 160,
                320, 320, 320, 320,
                24, 24, 24, 24,
                72, 72, 72, 72,
                160, 160, 160, 160
            ],
            'Role %': [
                0.60, 0.25, 0.10, 0.05,  # Simple: sums to 1.0
                0.50, 0.30, 0.15, 0.05,  # Standard: sums to 1.0
                0.45, 0.30, 0.15, 0.10,  # Complex: sums to 1.0
                0.70, 0.20, 0.05, 0.05,  # Reports Simple: sums to 1.0
                0.60, 0.25, 0.10, 0.05,  # Reports Standard: sums to 1.0
                0.55, 0.25, 0.15, 0.05   # Reports Complex: sums to 1.0
            ]
        })
        full_addon_data = addon_catalog_data
        full_addon_data.to_excel(writer, sheet_name='Add-On Catalog', index=False)

        # Product Role Map sheet
        product_role_data = pd.DataFrame({
            'Role': ['Project Manager', 'Solution Architect', 'Technical Lead', 'Business Analyst', 'QA Engineer',
                    'Integration Engineer', 'Technical Architect', 'Integration Lead', 'Reporting Consultant'],
            'Banner Enabled': [1, 1, 1, 1, 1, 1, 1, 1, 1],
            'Colleague Enabled': [1, 1, 1, 1, 1, 0, 1, 0, 1],
            'Multiplier': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        })
        product_role_data.to_excel(writer, sheet_name='Product Role Map', index=False)

        # Rates (Locales) sheet - expanded rate card
        locales = ['US', 'Canada', 'UK', 'EU', 'ANZ', 'MENA']
        roles = [
            'Project Manager', 'Solution Architect', 'Technical Lead', 
            'Business Analyst', 'QA Engineer', 'Integration Engineer', 
            'Technical Architect', 'Integration Lead', 'Reporting Consultant'
        ]

        rates_locales_data = []
        for locale in locales:
            for role in roles:
                # Use base US rates with slight variations for other locales
                base_onshore = rates_data[rates_data['Role'] == role]['Onshore Rate'].iloc[0]
                base_offshore = rates_data[rates_data['Role'] == role]['Offshore Rate'].iloc[0]
                base_partner = rates_data[rates_data['Role'] == role]['Partner Rate'].iloc[0]

                # Apply locale multipliers
                locale_multipliers = {'US': 1.0, 'Canada': 0.95, 'UK': 1.1, 'EU': 1.05, 'ANZ': 1.15, 'MENA': 0.85}
                multiplier = locale_multipliers.get(locale, 1.0)

                rates_locales_data.append({
                    'Role': role,
                    'Locale': locale,
                    'Onshore Rate': int(base_onshore * multiplier),
                    'Offshore Rate': int(base_offshore * multiplier),
                    'Partner Rate': int(base_partner * multiplier)
                })

        rates_locales_df = pd.DataFrame(rates_locales_data)
        rates_locales_df.to_excel(writer, sheet_name='Rates (Locales)', index=False)

        # Assumptions & Inputs sheet (placeholder)
        assumptions_data = pd.DataFrame({
            'Parameter': ['Created'],
            'Value': ['Initial workbook creation']
        })
        assumptions_data.to_excel(writer, sheet_name='Assumptions & Inputs', index=False)

        # Sources sheet
        sources_data = pd.DataFrame({
            'Source': ['N2S_Estimator_v1.xlsx (referenced)', 'fy25q3-ps-efficiency-model-02.xlsx (referenced)'],
            'Timestamp': ['2024-01-01', '2024-01-01'],
            'Notes': ['Base configuration data', 'Role catalog reference']
        })
        sources_data.to_excel(writer, sheet_name='Sources', index=False)

    print(f"Created workbook: {workbook_path}")


if __name__ == "__main__":
    create_workbook()
