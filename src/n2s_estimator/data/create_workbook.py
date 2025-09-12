"""Script to create the initial n2s_estimator.xlsx workbook with all required sheets."""

from pathlib import Path

import pandas as pd


def create_workbook() -> None:
    """Create the n2s_estimator.xlsx workbook with all required data."""
    workbook_path = Path(__file__).parent / "n2s_estimator.xlsx"

    with pd.ExcelWriter(workbook_path, engine='openpyxl') as writer:
        # Role Aliases sheet - for canonicalization
        role_aliases_data = pd.DataFrame({
            'Alias': [
                'Business Analyst', 'Platform Lead', 
                'Integration Developer', 'Integration Consultant', 'Extensibility Developer',
                'DW Scribe', 'Degree Works Scribe'
            ],
            'Canonical Role': [
                'Functional Consultant', 'Technical Architect',
                'Integration Engineer', 'Integration Engineer', 'Extensibility Engineer',
                'DegreeWorks Scribe', 'DegreeWorks Scribe'
            ]
        })
        role_aliases_data.to_excel(writer, sheet_name='Role Aliases', index=False)

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

        # Role Mix sheet (per stage role distributions) - Updated with new canonical roles
        role_mix_stages = []
        role_mix_roles = []
        role_mix_pcts = []
        
        # Start - PM 0.20, SA 0.30, TA 0.05, FC 0.35 (was BA 0.15 + TL 0.25), QA 0.10
        for role, pct in [('Project Manager', 0.20), ('Solution Architect', 0.30), ('Technical Architect', 0.05), ('Functional Consultant', 0.35), ('QA Engineer', 0.10)]:
            role_mix_stages.append('Start')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
            
        # Prepare - PM 0.15, SA 0.35, FC 0.45 (was BA 0.20 + TL 0.25), QA 0.05  
        for role, pct in [('Project Manager', 0.15), ('Solution Architect', 0.35), ('Functional Consultant', 0.45), ('QA Engineer', 0.05)]:
            role_mix_stages.append('Prepare')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
            
        # Sprint 0 - PM 0.15, SA 0.25, FC 0.50 (was BA 0.15 + TL 0.35), QA 0.10
        for role, pct in [('Project Manager', 0.15), ('Solution Architect', 0.25), ('Functional Consultant', 0.50), ('QA Engineer', 0.10)]:
            role_mix_stages.append('Sprint 0')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
            
        # Plan - PM 0.25, SA 0.20, TA 0.05, FC 0.40 (was BA 0.15 + TL 0.30), QA 0.10
        for role, pct in [('Project Manager', 0.25), ('Solution Architect', 0.20), ('Technical Architect', 0.05), ('Functional Consultant', 0.40), ('QA Engineer', 0.10)]:
            role_mix_stages.append('Plan')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
            
        # Configure - PM 0.10, SA 0.15, TA 0.28, FC 0.20, QA 0.10, IL 0.07, IE 0.06, EE 0.04 
        for role, pct in [('Project Manager', 0.10), ('Solution Architect', 0.15), ('Technical Architect', 0.28), ('Functional Consultant', 0.20), ('QA Engineer', 0.10), ('Integration Lead', 0.07), ('Integration Engineer', 0.06), ('Extensibility Engineer', 0.04)]:
            role_mix_stages.append('Configure')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
            
        # Test - PM 0.15, SA 0.10, TA 0.04, FC 0.15, QA 0.40, IE 0.06, EE 0.10
        for role, pct in [('Project Manager', 0.15), ('Solution Architect', 0.10), ('Technical Architect', 0.04), ('Functional Consultant', 0.15), ('QA Engineer', 0.40), ('Integration Engineer', 0.06), ('Extensibility Engineer', 0.10)]:
            role_mix_stages.append('Test')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
            
        # Deploy - PM 0.20, SA 0.15, TA 0.06, FC 0.10, QA 0.20, IE 0.15, EE 0.14
        for role, pct in [('Project Manager', 0.20), ('Solution Architect', 0.15), ('Technical Architect', 0.06), ('Functional Consultant', 0.10), ('QA Engineer', 0.20), ('Integration Engineer', 0.15), ('Extensibility Engineer', 0.14)]:
            role_mix_stages.append('Deploy')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
            
        # Go-Live - PM 0.25, SA 0.20, FC 0.45 (was BA 0.15 + TL 0.30), QA 0.10
        for role, pct in [('Project Manager', 0.25), ('Solution Architect', 0.20), ('Functional Consultant', 0.45), ('QA Engineer', 0.10)]:
            role_mix_stages.append('Go-Live')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
            
        # Post Go-Live - PM 0.30, SA 0.25, FC 0.35 (was BA 0.15 + TL 0.20), QA 0.10
        for role, pct in [('Project Manager', 0.30), ('Solution Architect', 0.25), ('Functional Consultant', 0.35), ('QA Engineer', 0.10)]:
            role_mix_stages.append('Post Go-Live (Care)')
            role_mix_roles.append(role)
            role_mix_pcts.append(pct)
        
        role_mix_data = pd.DataFrame({
            'Stage': role_mix_stages,
            'Role': role_mix_roles,
            'Role Mix %': role_mix_pcts
        })
        role_mix_data.to_excel(writer, sheet_name='Role Mix', index=False)

        # Rates sheet (placeholder rates) - Updated with canonical roles
        rates_data = pd.DataFrame({
            'Role': [
                'Project Manager', 'Solution Architect', 'Functional Consultant', 'QA Engineer',
                'Integration Engineer', 'Technical Architect', 'Integration Lead', 'Reporting Consultant',
                'Extensibility Engineer', 'DegreeWorks Scribe'
            ],
            'Onshore Rate': [150, 175, 160, 140, 130, 170, 180, 165, 155, 145],
            'Offshore Rate': [75, 90, 85, 70, 65, 85, 95, 80, 80, 72],
            'Partner Rate': [120, 140, 130, 110, 100, 135, 145, 125, 125, 116]
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

        # Add-On Catalog sheet - includes proper Degree Works with Setup + PVE tiers
        addon_catalog_data = pd.DataFrame({
            'Package': [
                # Integrations (unchanged)
                'Integrations', 'Integrations', 'Integrations', 'Integrations',
                'Integrations', 'Integrations', 'Integrations', 'Integrations',
                'Integrations', 'Integrations', 'Integrations', 'Integrations',
                # Reports (unchanged)
                'Reports', 'Reports', 'Reports', 'Reports',
                'Reports', 'Reports', 'Reports', 'Reports',
                'Reports', 'Reports', 'Reports', 'Reports',
                # Degree Works - Setup + PVE tiers
                'Degree Works', 'Degree Works', 'Degree Works',  # Setup tier
                'Degree Works', 'Degree Works', 'Degree Works',  # PVE Simple
                'Degree Works', 'Degree Works', 'Degree Works',  # PVE Standard  
                'Degree Works', 'Degree Works', 'Degree Works'   # PVE Complex
            ],
            'Tier': [
                # Integrations
                'Simple', 'Simple', 'Simple', 'Simple',
                'Standard', 'Standard', 'Standard', 'Standard',
                'Complex', 'Complex', 'Complex', 'Complex',
                # Reports
                'Simple', 'Simple', 'Simple', 'Simple',
                'Standard', 'Standard', 'Standard', 'Standard',
                'Complex', 'Complex', 'Complex', 'Complex',
                # Degree Works
                'Setup', 'Setup', 'Setup',
                'PVE Simple', 'PVE Simple', 'PVE Simple',
                'PVE Standard', 'PVE Standard', 'PVE Standard',
                'PVE Complex', 'PVE Complex', 'PVE Complex'
            ],
            'Role': [
                # Integrations (unchanged)
                'Integration Engineer', 'Technical Architect', 'QA Engineer', 'Project Manager',
                'Integration Engineer', 'Technical Architect', 'QA Engineer', 'Project Manager',
                'Integration Engineer', 'Technical Architect', 'Integration Lead', 'QA Engineer',
                # Reports (unchanged)
                'Reporting Consultant', 'Solution Architect', 'QA Engineer', 'Project Manager',
                'Reporting Consultant', 'Solution Architect', 'QA Engineer', 'Project Manager',
                'Reporting Consultant', 'Solution Architect', 'QA Engineer', 'Project Manager',
                # Degree Works
                'DegreeWorks Scribe', 'Functional Consultant', 'Technical Architect',  # Setup
                'DegreeWorks Scribe', 'Functional Consultant', 'Technical Architect',  # PVE Simple
                'DegreeWorks Scribe', 'Functional Consultant', 'Technical Architect',  # PVE Standard
                'DegreeWorks Scribe', 'Functional Consultant', 'Technical Architect'   # PVE Complex
            ],
            'Unit Hours': [
                # Integrations (unchanged)
                80, 80, 80, 80,
                160, 160, 160, 160,
                320, 320, 320, 320,
                # Reports (unchanged)
                24, 24, 24, 24,
                72, 72, 72, 72,
                160, 160, 160, 160,
                # Degree Works
                300, 300, 300,  # Setup: 300h
                24, 24, 24,     # PVE Simple: 24h per PVE
                48, 48, 48,     # PVE Standard: 48h per PVE
                96, 96, 96      # PVE Complex: 96h per PVE
            ],
            'Role %': [
                # Integrations (unchanged)
                0.60, 0.25, 0.10, 0.05,  # Simple: sums to 1.0
                0.50, 0.30, 0.15, 0.05,  # Standard: sums to 1.0
                0.45, 0.30, 0.15, 0.10,  # Complex: sums to 1.0
                # Reports (unchanged)
                0.70, 0.20, 0.05, 0.05,  # Reports Simple: sums to 1.0
                0.60, 0.25, 0.10, 0.05,  # Reports Standard: sums to 1.0
                0.55, 0.25, 0.15, 0.05,  # Reports Complex: sums to 1.0
                # Degree Works
                0.70, 0.20, 0.10,        # Setup: DWS 70%, FC 20%, TA 10%
                0.70, 0.20, 0.10,        # PVE Simple: DWS 70%, FC 20%, TA 10%
                0.60, 0.25, 0.15,        # PVE Standard: DWS 60%, FC 25%, TA 15%
                0.50, 0.30, 0.20         # PVE Complex: DWS 50%, FC 30%, TA 20%
            ],
            'Scale By Size': [
                # Integrations (unchanged - no scaling)
                0, 0, 0, 0,
                0, 0, 0, 0,  
                0, 0, 0, 0,
                # Reports (unchanged - no scaling)
                0, 0, 0, 0,
                0, 0, 0, 0,
                0, 0, 0, 0,
                # Degree Works
                1, 1, 1,  # Setup: size-scaled
                0, 0, 0,  # PVE Simple: not size-scaled
                0, 0, 0,  # PVE Standard: not size-scaled
                0, 0, 0   # PVE Complex: not size-scaled
            ]
        })
        full_addon_data = addon_catalog_data
        full_addon_data.to_excel(writer, sheet_name='Add-On Catalog', index=False)

        # Product Role Map sheet - Updated with canonical roles
        product_role_data = pd.DataFrame({
            'Role': [
                'Project Manager', 'Solution Architect', 'Functional Consultant', 'QA Engineer',
                'Integration Engineer', 'Technical Architect', 'Integration Lead', 'Reporting Consultant',
                'Extensibility Engineer', 'DegreeWorks Scribe'
            ],
            'Banner Enabled': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],  # All roles enabled for Banner
            'Colleague Enabled': [1, 1, 1, 1, 1, 0, 0, 1, 1, 0],  # Technical Architect, Integration Lead, DegreeWorks Scribe disabled for Colleague
            'Multiplier': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        })
        product_role_data.to_excel(writer, sheet_name='Product Role Map', index=False)

        # Rates (Locales) sheet - expanded rate card with canonical roles
        locales = ['US', 'Canada', 'UK', 'EU', 'ANZ', 'MENA']
        roles = [
            'Project Manager', 'Solution Architect', 
            'Functional Consultant', 'QA Engineer', 'Integration Engineer', 
            'Technical Architect', 'Integration Lead', 'Reporting Consultant',
            'Extensibility Engineer', 'DegreeWorks Scribe'
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
