"""Main Streamlit application for N2S Delivery Estimator."""

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Fix import path for Streamlit execution
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from n2s_estimator.engine.datatypes import EstimationInputs, DeliveryMix
from n2s_estimator.engine.orchestrator import N2SEstimator
from n2s_estimator.engine.validators import validate_pricing_overrides
from n2s_estimator.export.excel import ExcelExporter

# Page configuration
st.set_page_config(
    page_title="N2S Delivery Estimator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_estimator() -> N2SEstimator:
    """Load and cache the N2S estimator."""
    workbook_path = Path(__file__).parent.parent / "data" / "n2s_estimator.xlsx"
    return N2SEstimator(workbook_path)


def initialize_session_state() -> None:
    """Initialize session state variables."""
    if 'inputs' not in st.session_state:
        st.session_state.inputs = EstimationInputs()
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'rate_overrides' not in st.session_state:
        st.session_state.rate_overrides = []  # list of {role, locale, onshore, offshore, partner}
    if 'global_mix_override' not in st.session_state:
        st.session_state.global_mix_override = None  # {onshore_pct, offshore_pct, partner_pct}
    if 'role_mix_overrides' not in st.session_state:
        st.session_state.role_mix_overrides = []  # list of {role, onshore_pct, offshore_pct, partner_pct}


def render_sidebar() -> EstimationInputs:
    """Render sidebar controls and return estimation inputs."""
    st.sidebar.title("N2S Estimator")
    st.sidebar.markdown("---")

    # Core Parameters
    st.sidebar.subheader("Core Parameters")

    product = st.sidebar.selectbox(
        "Product",
        ["Banner", "Colleague"],
        index=0 if st.session_state.inputs.product == "Banner" else 1,
        key="product_select"
    )

    delivery_type = st.sidebar.selectbox(
        "Delivery Type",
        ["Net New", "Modernization"],
        index=0 if st.session_state.inputs.delivery_type == "Net New" else 1,
        key="delivery_type_select"
    )

    size_band = st.sidebar.selectbox(
        "Size of School",
        ["Small (<5k)", "Medium (5-15k)", "Large (15-30k)", "Very Large (>30k)"],
        index=["Small", "Medium", "Large", "Very Large"].index(
            st.session_state.inputs.size_band.split()[0] if st.session_state.inputs.size_band else "Medium"
        ),
        key="size_band_select"
    )

    locale = st.sidebar.selectbox(
        "Locale/Region",
        ["US", "Canada", "UK", "EU", "ANZ", "MENA"],
        index=["US", "Canada", "UK", "EU", "ANZ", "MENA"].index(st.session_state.inputs.locale),
        key="locale_select"
    )

    # Extract size band key
    size_key = size_band.split()[0]  # "Small", "Medium", etc.

    st.sidebar.markdown("---")

    # Add-on Packages
    st.sidebar.subheader("Add-on Packages")

    # Integrations
    st.sidebar.markdown("**Integrations**")
    include_integrations = st.sidebar.checkbox(
        "Include Integrations",
        value=st.session_state.inputs.include_integrations,
        key="include_integrations_check"
    )

    integrations_count = 30
    integrations_simple_pct = 0.60
    integrations_standard_pct = 0.30
    integrations_complex_pct = 0.10

    if include_integrations:
        integrations_count = st.sidebar.number_input(
            "Integration Count",
            min_value=0,
            max_value=1000,
            value=st.session_state.inputs.integrations_count,
            step=1
        )

        st.sidebar.markdown("Tier Mix:")
        integrations_simple_pct = st.sidebar.slider(
            "Simple %",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.inputs.integrations_simple_pct,
            step=0.05,
            key="int_simple"
        )

        integrations_standard_pct = st.sidebar.slider(
            "Standard %",
            min_value=0.0,
            max_value=1.0 - integrations_simple_pct,
            value=min(st.session_state.inputs.integrations_standard_pct, 1.0 - integrations_simple_pct),
            step=0.05,
            key="int_standard"
        )

        integrations_complex_pct = 1.0 - integrations_simple_pct - integrations_standard_pct
        st.sidebar.write(f"Complex %: {integrations_complex_pct:.2%}")

    # Reports
    st.sidebar.markdown("**Reports**")
    include_reports = st.sidebar.checkbox(
        "Include Reports",
        value=st.session_state.inputs.include_reports,
        key="include_reports_check"
    )

    reports_count = 40
    reports_simple_pct = 0.50
    reports_standard_pct = 0.35
    reports_complex_pct = 0.15

    if include_reports:
        reports_count = st.sidebar.number_input(
            "Reports Count",
            min_value=0,
            max_value=1000,
            value=st.session_state.inputs.reports_count,
            step=1
        )

        st.sidebar.markdown("Tier Mix:")
        reports_simple_pct = st.sidebar.slider(
            "Simple %",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.inputs.reports_simple_pct,
            step=0.05,
            key="rep_simple"
        )

        reports_standard_pct = st.sidebar.slider(
            "Standard %",
            min_value=0.0,
            max_value=1.0 - reports_simple_pct,
            value=min(st.session_state.inputs.reports_standard_pct, 1.0 - reports_simple_pct),
            step=0.05,
            key="rep_standard"
        )

        reports_complex_pct = 1.0 - reports_simple_pct - reports_standard_pct
        st.sidebar.write(f"Complex %: {reports_complex_pct:.2%}")

    # Degree Works
    st.sidebar.markdown("**Degree Works**")
    include_degreeworks = st.sidebar.checkbox(
        "Include Degree Works",
        value=getattr(st.session_state.inputs, "include_degreeworks", False),
        help="Adds Degree Works Setup (size-scaled) and PVE scribing volume to the estimate.",
        key="include_degreeworks_check"
    )

    degreeworks_include_setup = True
    degreeworks_use_pve_calculator = True
    degreeworks_majors = degreeworks_minors = degreeworks_certificates = degreeworks_concentrations = 0
    degreeworks_catalog_years = 1
    degreeworks_pve_count = 0
    dw_simple = 0.50
    dw_standard = 0.35
    dw_complex = 0.15

    if include_degreeworks:
        degreeworks_include_setup = st.sidebar.checkbox(
            "Include Setup (size-scaled 300h @ Medium)",
            value=getattr(st.session_state.inputs, "degreeworks_include_setup", True),
            help="One-time Setup & Enablement for Degree Works: environment/config, integration, training, governance, testing."
        )

        degreeworks_use_pve_calculator = st.sidebar.checkbox(
            "Use PVE Calculator",
            value=getattr(st.session_state.inputs, "degreeworks_use_pve_calculator", True),
            help="Program-Version Equivalents (PVEs) = (#Majors) + 0.5 × (#Minors + #Certificates + #Concentrations), then × (#Catalog Years)."
        )

        if degreeworks_use_pve_calculator:
            st.sidebar.markdown("PVE Inputs:")
            degreeworks_majors = st.sidebar.number_input(
                "Majors", 
                min_value=0, 
                value=getattr(st.session_state.inputs, "degreeworks_majors", 0), 
                step=1, 
                help="Number of distinct Majors to scribe at go-live."
            )
            degreeworks_minors = st.sidebar.number_input(
                "Minors", 
                min_value=0, 
                value=getattr(st.session_state.inputs, "degreeworks_minors", 0), 
                step=1
            )
            degreeworks_certificates = st.sidebar.number_input(
                "Certificates", 
                min_value=0, 
                value=getattr(st.session_state.inputs, "degreeworks_certificates", 0), 
                step=1
            )
            degreeworks_concentrations = st.sidebar.number_input(
                "Concentrations", 
                min_value=0, 
                value=getattr(st.session_state.inputs, "degreeworks_concentrations", 0), 
                step=1
            )
            degreeworks_catalog_years = st.sidebar.number_input(
                "Catalog Years", 
                min_value=1, 
                value=getattr(st.session_state.inputs, "degreeworks_catalog_years", 1), 
                step=1, 
                help="How many catalog years are included at go-live."
            )
            computed_pves = (degreeworks_majors + 0.5 * (degreeworks_minors + degreeworks_certificates + degreeworks_concentrations)) * degreeworks_catalog_years
            st.sidebar.info(f"Computed PVEs: **{computed_pves:.1f}**")
        else:
            degreeworks_pve_count = st.sidebar.number_input(
                "Direct PVE Count", 
                min_value=0, 
                value=getattr(st.session_state.inputs, "degreeworks_pve_count", 0), 
                step=1, 
                help="Override the calculator and specify total PVEs directly."
            )

        st.sidebar.markdown("PVE Complexity Mix:")
        dw_simple = st.sidebar.slider(
            "Simple %", 
            min_value=0.0, 
            max_value=1.0, 
            value=getattr(st.session_state.inputs, "degreeworks_simple_pct", 0.50), 
            step=0.05,
            key="dw_simple"
        )
        dw_standard = st.sidebar.slider(
            "Standard %", 
            min_value=0.0, 
            max_value=1.0 - dw_simple, 
            value=min(getattr(st.session_state.inputs, "degreeworks_standard_pct", 0.35), 1.0 - dw_simple), 
            step=0.05,
            key="dw_standard"
        )
        dw_complex = 1.0 - dw_simple - dw_standard
        st.sidebar.write(f"Complex %: {dw_complex:.2%}")
        
        # Degree Works cap controls
        degreeworks_cap_enabled = st.sidebar.checkbox(
            "Cap total Degree Works hours (recommended)",
            value=getattr(st.session_state.inputs, "degreeworks_cap_enabled", True),
            help="Prevents runaway estimates. Defaults by size: Small 300h, Medium 400h, Large 500h, Very Large 600h."
        )

        # Determine default cap by size
        size_default_caps = {"Small": 300.0, "Medium": 400.0, "Large": 500.0, "Very Large": 600.0}
        default_cap = size_default_caps.get(size_key, 400.0)

        degreeworks_cap_hours = None
        if degreeworks_cap_enabled:
            degreeworks_cap_hours = st.sidebar.number_input(
                "Cap (hours)",
                min_value=0.0,
                value=getattr(st.session_state.inputs, "degreeworks_cap_hours", default_cap),
                step=50.0,
                help="Maximum total hours for Degree Works (Setup + PVEs). Leave at the default for size-based guardrails."
            )

    st.sidebar.markdown("---")

    # Advanced Settings (collapsed by default)
    with st.sidebar.expander("Advanced Settings"):
        maturity_factor = st.slider(
            "Maturity Factor",
            min_value=0.5,
            max_value=2.0,
            value=st.session_state.inputs.maturity_factor,
            step=0.05
        )
        
        # Sprint 0 uplift
        default_uplift = 0.02 if delivery_type == "Net New" else 0.01
        sprint0_uplift_pct = st.slider(
            "Sprint 0 uplift (+% of total)", 0.0, 0.05, 
            value=getattr(st.session_state.inputs, "sprint0_uplift_pct", default_uplift),
            step=0.005,
            help="Adds this absolute % of total hours to Sprint 0 and subtracts proportionally from Plan+Configure to keep Stage Weights at 100%."
        )

    # Scenario Management
    st.sidebar.markdown("---")
    st.sidebar.subheader("Scenario Management")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("Save Scenario", width="stretch"):
            scenario_data = {
                'product': product,
                'delivery_type': delivery_type,
                'size_band': size_key,
                'locale': locale,
                'include_integrations': include_integrations,
                'integrations_count': integrations_count,
                'integrations_simple_pct': integrations_simple_pct,
                'integrations_standard_pct': integrations_standard_pct,
                'integrations_complex_pct': integrations_complex_pct,
                'include_reports': include_reports,
                'reports_count': reports_count,
                'reports_simple_pct': reports_simple_pct,
                'reports_standard_pct': reports_standard_pct,
                'reports_complex_pct': reports_complex_pct,
                'maturity_factor': maturity_factor,
                'scenario_overrides': {
                    'rate_overrides': st.session_state.rate_overrides,
                    'global_mix_override': st.session_state.global_mix_override,
                    'role_mix_overrides': st.session_state.role_mix_overrides
                }
            }
            st.download_button(
                "Download JSON",
                data=json.dumps(scenario_data, indent=2),
                file_name="n2s_scenario.json",
                mime="application/json"
            )

    with col2:
        uploaded_file = st.file_uploader(
            "Load Scenario",
            type=['json'],
            label_visibility="collapsed"
        )
        if uploaded_file:
            try:
                scenario_data = json.loads(uploaded_file.read())
                st.session_state.inputs = EstimationInputs(**scenario_data)
                
                # Load pricing overrides if present
                if 'scenario_overrides' in scenario_data:
                    overrides = scenario_data['scenario_overrides']
                    st.session_state.rate_overrides = overrides.get('rate_overrides', [])
                    st.session_state.global_mix_override = overrides.get('global_mix_override', None)
                    st.session_state.role_mix_overrides = overrides.get('role_mix_overrides', [])
                    
                    # Apply overrides to estimator
                    estimator = load_estimator()
                    if st.session_state.rate_overrides:
                        estimator.apply_rate_overrides(st.session_state.rate_overrides)
                    if st.session_state.global_mix_override or st.session_state.role_mix_overrides:
                        estimator.apply_delivery_mix_overrides(
                            st.session_state.global_mix_override, 
                            st.session_state.role_mix_overrides
                        )
                
                st.rerun()
            except Exception as e:
                st.error(f"Error loading scenario: {e}")

    # Create inputs object
    inputs = EstimationInputs(
        product=product,
        delivery_type=delivery_type,
        size_band=size_key,
        locale=locale,
        maturity_factor=maturity_factor,
        integrations_count=integrations_count,
        integrations_simple_pct=integrations_simple_pct,
        integrations_standard_pct=integrations_standard_pct,
        integrations_complex_pct=integrations_complex_pct,
        reports_count=reports_count,
        reports_simple_pct=reports_simple_pct,
        reports_standard_pct=reports_standard_pct,
        reports_complex_pct=reports_complex_pct,
        include_integrations=include_integrations,
        include_reports=include_reports,
        include_degreeworks=include_degreeworks,
        degreeworks_include_setup=degreeworks_include_setup,
        degreeworks_use_pve_calculator=degreeworks_use_pve_calculator,
        degreeworks_majors=degreeworks_majors,
        degreeworks_minors=degreeworks_minors,
        degreeworks_certificates=degreeworks_certificates,
        degreeworks_concentrations=degreeworks_concentrations,
        degreeworks_catalog_years=degreeworks_catalog_years,
        degreeworks_pve_count=degreeworks_pve_count,
        degreeworks_simple_pct=dw_simple,
        degreeworks_standard_pct=dw_standard,
        degreeworks_complex_pct=dw_complex,
        sprint0_uplift_pct=sprint0_uplift_pct,
        degreeworks_cap_enabled=degreeworks_cap_enabled if include_degreeworks else True,
        degreeworks_cap_hours=degreeworks_cap_hours if include_degreeworks else None
    )

    return inputs


def render_summary_cards(estimator: N2SEstimator, results: 'EstimationResults') -> None:
    """Render summary KPI cards."""
    package_summaries = estimator.get_package_summaries(results)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Hours",
            f"{results.total_hours:,.0f}",
            help="Total delivery hours across all packages"
        )

    with col2:
        st.metric(
            "Total Cost",
            f"${results.total_cost:,.0f}",
            help="Total delivery cost across all packages"
        )

    with col3:
        st.metric(
            "Presales Hours",
            f"{results.total_presales_hours:,.0f}",
            help="Total presales hours (Base N2S only)"
        )

    with col4:
        blended_rate = (
            results.total_cost / results.total_delivery_hours 
            if results.total_delivery_hours > 0 else 0
        )
        st.metric(
            "Blended Rate",
            f"${blended_rate:,.0f}/hr",
            help="Average cost per delivery hour"
        )

    # Package breakdown
    st.markdown("### Package Breakdown")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        base_summary = package_summaries['Base N2S']
        st.metric(
            "Base N2S",
            f"{base_summary['hours']:,.0f} hrs",
            f"${base_summary['cost']:,.0f}"
        )

    with col2:
        int_summary = package_summaries['Integrations']
        if int_summary['enabled']:
            st.metric(
                "Integrations",
                f"{int_summary['hours']:,.0f} hrs",
                f"${int_summary['cost']:,.0f}"
            )
        else:
            st.metric("Integrations", "Disabled", "")

    with col3:
        rep_summary = package_summaries['Reports']
        if rep_summary['enabled']:
            st.metric(
                "Reports",
                f"{rep_summary['hours']:,.0f} hrs",
                f"${rep_summary['cost']:,.0f}"
            )
        else:
            st.metric("Reports", "Disabled", "")

    with col4:
        dw_summary = package_summaries['Degree Works']
        if dw_summary['enabled']:
            st.metric(
                "Degree Works",
                f"{dw_summary['hours']:,.0f} hrs",
                f"${dw_summary['cost']:,.0f}"
            )
        else:
            st.metric("Degree Works", "Disabled", "")


def render_base_n2s_tab(estimator: N2SEstimator, results: 'EstimationResults') -> None:
    """Render Base N2S analysis tab."""
    st.subheader("Base N2S Package Analysis")

    # Stage x Role table
    st.markdown("#### Stage x Role Breakdown")

    # Create stage x role matrix
    stage_role_data = []
    for rh in results.base_role_hours:
        stage_role_data.append({
            'Stage': rh.stage,
            'Role': rh.role,
            'Hours': rh.total_hours,
            'Onshore Hours': rh.onshore_hours,
            'Offshore Hours': rh.offshore_hours,
            'Partner Hours': rh.partner_hours,
            'Total Cost': rh.total_cost,
            'Blended Rate': rh.blended_rate
        })

    if stage_role_data:
        df = pd.DataFrame(stage_role_data)

        # Format for display
        df['Hours'] = df['Hours'].round(1)
        df['Onshore Hours'] = df['Onshore Hours'].round(1)
        df['Offshore Hours'] = df['Offshore Hours'].round(1)
        df['Partner Hours'] = df['Partner Hours'].round(1)
        df['Total Cost'] = df['Total Cost'].round(0)
        df['Blended Rate'] = df['Blended Rate'].round(0)

        st.dataframe(
            df,
            width="stretch",
            column_config={
                'Total Cost': st.column_config.NumberColumn(format="$%d"),
                'Blended Rate': st.column_config.NumberColumn(format="$%d/hr")
            }
        )

    # Comprehensive Package Summary
    st.markdown("#### Package Summary")
    
    # Calculate totals
    base_hours = sum(rh.total_hours for rh in results.base_role_hours)
    base_cost = sum(rh.total_cost for rh in results.base_role_hours)
    
    integrations_hours = sum(rh.total_hours for rh in results.integrations_role_hours) if results.integrations_role_hours else 0
    integrations_cost = sum(rh.total_cost for rh in results.integrations_role_hours) if results.integrations_role_hours else 0
    
    reports_hours = sum(rh.total_hours for rh in results.reports_role_hours) if results.reports_role_hours else 0
    reports_cost = sum(rh.total_cost for rh in results.reports_role_hours) if results.reports_role_hours else 0
    
    degreeworks_hours = sum(rh.total_hours for rh in results.degreeworks_role_hours) if results.degreeworks_role_hours else 0
    degreeworks_cost = sum(rh.total_cost for rh in results.degreeworks_role_hours) if results.degreeworks_role_hours else 0
    
    total_hours = base_hours + integrations_hours + reports_hours + degreeworks_hours
    total_cost = base_cost + integrations_cost + reports_cost + degreeworks_cost
    
    # Create summary data
    summary_data = [
        {'Package': 'Base N2S', 'Hours': base_hours, 'Cost': base_cost},
        {'Package': 'Integrations', 'Hours': integrations_hours, 'Cost': integrations_cost},
        {'Package': 'Reports', 'Hours': reports_hours, 'Cost': reports_cost},
        {'Package': 'Degree Works', 'Hours': degreeworks_hours, 'Cost': degreeworks_cost},
        {'Package': '**TOTAL**', 'Hours': total_hours, 'Cost': total_cost}
    ]
    
    summary_df = pd.DataFrame(summary_data)
    summary_df['Hours'] = summary_df['Hours'].round(1)
    summary_df['Cost'] = summary_df['Cost'].round(0)
    
    st.dataframe(
        summary_df,
        width="stretch",
        column_config={
            'Hours': st.column_config.NumberColumn(format="%.1f"),
            'Cost': st.column_config.NumberColumn(format="$%d")
        }
    )
    
    st.markdown("---")
    
    # Role Summary
    st.markdown("#### Role Summary")
    role_summary = estimator.get_role_summary(results)
    if role_summary:
        role_df = pd.DataFrame([{
            'Role': rh.role,
            'Hours': rh.total_hours,
            'Cost': rh.total_cost
        } for rh in role_summary])

        role_df['Hours'] = role_df['Hours'].round(1)
        role_df['Cost'] = role_df['Cost'].round(0)

        st.dataframe(
            role_df,
            width="stretch",
            column_config={
                'Hours': st.column_config.NumberColumn(format="%.1f"),
                'Cost': st.column_config.NumberColumn(format="$%d")
            }
        )


def render_integrations_tab(estimator: N2SEstimator, results: 'EstimationResults') -> None:
    """Render Integrations analysis tab."""
    st.subheader("Integrations Add-on Package")

    if not results.integrations_role_hours:
        st.info("Integrations package is not enabled.")
        return

    # Tier breakdown
    st.markdown("#### Tier Breakdown")
    tier_breakdown = estimator.addons.get_tier_breakdown('Integrations', results.inputs)

    if tier_breakdown:
        tier_df = pd.DataFrame([
            {
                'Tier': tier,
                'Count': data['count'],
                'Unit Hours': data['unit_hours'],
                'Total Hours': data['total_hours'],
                'Mix %': data['mix_percentage']
            }
            for tier, data in tier_breakdown.items()
        ])

        tier_df['Count'] = tier_df['Count'].round(1)
        tier_df['Total Hours'] = tier_df['Total Hours'].round(0)

        st.dataframe(
            tier_df,
            width="stretch",
            column_config={
                'Mix %': st.column_config.NumberColumn(format="%.1%")
            }
        )

    # Role breakdown
    st.markdown("#### Role Breakdown")
    if results.integrations_role_hours:
        role_data = []
        for rh in results.integrations_role_hours:
            role_data.append({
                'Role': rh.role,
                'Hours': rh.total_hours,
                'Cost': rh.total_cost,
                'Blended Rate': rh.blended_rate
            })

        role_df = pd.DataFrame(role_data)
        role_df['Hours'] = role_df['Hours'].round(1)
        role_df['Cost'] = role_df['Cost'].round(0)
        role_df['Blended Rate'] = role_df['Blended Rate'].round(0)

        st.dataframe(
            role_df,
            width="stretch",
            column_config={
                'Cost': st.column_config.NumberColumn(format="$%d"),
                'Blended Rate': st.column_config.NumberColumn(format="$%d/hr")
            }
        )


def render_reports_tab(estimator: N2SEstimator, results: 'EstimationResults') -> None:
    """Render Reports analysis tab."""
    st.subheader("Reports Add-on Package")

    if not results.reports_role_hours:
        st.info("Reports package is not enabled.")
        return

    # Tier breakdown
    st.markdown("#### Tier Breakdown")
    tier_breakdown = estimator.addons.get_tier_breakdown('Reports', results.inputs)

    if tier_breakdown:
        tier_df = pd.DataFrame([
            {
                'Tier': tier,
                'Count': data['count'],
                'Unit Hours': data['unit_hours'],
                'Total Hours': data['total_hours'],
                'Mix %': data['mix_percentage']
            }
            for tier, data in tier_breakdown.items()
        ])

        tier_df['Count'] = tier_df['Count'].round(1)
        tier_df['Total Hours'] = tier_df['Total Hours'].round(0)

        st.dataframe(
            tier_df,
            width="stretch",
            column_config={
                'Mix %': st.column_config.NumberColumn(format="%.1%")
            }
        )

    # Role breakdown
    st.markdown("#### Role Breakdown")
    if results.reports_role_hours:
        role_data = []
        for rh in results.reports_role_hours:
            role_data.append({
                'Role': rh.role,
                'Hours': rh.total_hours,
                'Cost': rh.total_cost,
                'Blended Rate': rh.blended_rate
            })

        role_df = pd.DataFrame(role_data)
        role_df['Hours'] = role_df['Hours'].round(1)
        role_df['Cost'] = role_df['Cost'].round(0)
        role_df['Blended Rate'] = role_df['Blended Rate'].round(0)

        st.dataframe(
            role_df,
            width="stretch",
            column_config={
                'Cost': st.column_config.NumberColumn(format="$%d"),
                'Blended Rate': st.column_config.NumberColumn(format="$%d/hr")
            }
        )


def render_degreeworks_tab(estimator: N2SEstimator, results: 'EstimationResults', inputs: 'EstimationInputs') -> None:
    """Render Degree Works analysis tab."""
    st.subheader("Degree Works Add-on Package")

    if not results.degreeworks_role_hours:
        st.info("Degree Works package is not enabled.")
        return

    # Show Setup vs PVEs breakdown first
    if results.degreeworks_hours:
        st.markdown("#### Setup vs PVEs Breakdown")
        setup_hours = results.degreeworks_hours.stage_hours.get('Degree Works – Setup', 0)
        pve_hours = results.degreeworks_hours.stage_hours.get('Degree Works – PVEs', 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Setup Hours", f"{setup_hours:,.0f}", help="One-time setup and enablement (size-scaled)")
        with col2:
            st.metric("PVE Hours", f"{pve_hours:,.0f}", help="Program-Version Equivalents scribing")
        with col3:
            st.metric("Total DW Hours", f"{setup_hours + pve_hours:,.0f}")
            
        # Show cap information if enabled
        if inputs.degreeworks_cap_enabled:
            size_default_caps = {"Small": 300.0, "Medium": 400.0, "Large": 500.0, "Very Large": 600.0}
            default_cap = size_default_caps.get(inputs.size_band, 400.0)
            cap_hours = inputs.degreeworks_cap_hours or default_cap
            st.info(f"Degree Works total is capped at **{cap_hours:.0f} hours** for size '{inputs.size_band}'. PVEs are clamped after Setup.")

    # PVE Calculator Summary
    inputs = results.inputs
    if inputs.degreeworks_use_pve_calculator:
        st.markdown("#### PVE Calculator Summary")
        computed_pves = (
            inputs.degreeworks_majors + 
            0.5 * (inputs.degreeworks_minors + inputs.degreeworks_certificates + inputs.degreeworks_concentrations)
        ) * inputs.degreeworks_catalog_years
        
        st.write(f"**Formula:** Majors + 0.5 × (Minors + Certificates + Concentrations) × Catalog Years")
        st.write(f"**Calculation:** {inputs.degreeworks_majors} + 0.5 × ({inputs.degreeworks_minors} + {inputs.degreeworks_certificates} + {inputs.degreeworks_concentrations}) × {inputs.degreeworks_catalog_years} = **{computed_pves:.1f} PVEs**")

    # Tier breakdown
    st.markdown("#### Tier Breakdown")
    tier_breakdown = estimator.addons.get_tier_breakdown('Degree Works', results.inputs)

    if tier_breakdown:
        tier_df = pd.DataFrame([
            {
                'Tier': tier,
                'Count': data['count'],
                'Unit Hours': data['unit_hours'],
                'Total Hours': data['total_hours'],
                'Mix %': data['mix_percentage']
            }
            for tier, data in tier_breakdown.items()
        ])

        tier_df['Count'] = tier_df['Count'].round(1)
        tier_df['Total Hours'] = tier_df['Total Hours'].round(0)

        st.dataframe(
            tier_df,
            width="stretch",
            column_config={
                'Mix %': st.column_config.NumberColumn(format="%.1%")
            }
        )

    # Role breakdown
    st.markdown("#### Role Breakdown")
    if results.degreeworks_role_hours:
        role_data = []
        for rh in results.degreeworks_role_hours:
            role_data.append({
                'Role': rh.role,
                'Hours': rh.total_hours,
                'Cost': rh.total_cost,
                'Blended Rate': rh.blended_rate
            })

        role_df = pd.DataFrame(role_data)
        role_df['Hours'] = role_df['Hours'].round(1)
        role_df['Cost'] = role_df['Cost'].round(0)
        role_df['Blended Rate'] = role_df['Blended Rate'].round(0)

        st.dataframe(
            role_df,
            width="stretch",
            column_config={
                'Cost': st.column_config.NumberColumn(format="$%d"),
                'Blended Rate': st.column_config.NumberColumn(format="$%d/hr")
            }
        )


def render_charts_tab(estimator: N2SEstimator, results: 'EstimationResults') -> None:
    """Render charts and visualizations."""
    st.subheader("Charts & Visualizations")

    col1, col2 = st.columns(2)

    with col1:
        # Delivery split pie chart
        st.markdown("#### Delivery Split")
        delivery_split = estimator.get_delivery_split_summary(results)

        if delivery_split:
            pie_data = {
                'Split': ['Onshore', 'Offshore', 'Partner'],
                'Cost': [
                    delivery_split['onshore']['cost'],
                    delivery_split['offshore']['cost'],
                    delivery_split['partner']['cost']
                ]
            }

            fig_pie = px.pie(
                values=pie_data['Cost'],
                names=pie_data['Split'],
                title="Cost by Delivery Split"
            )
            st.plotly_chart(fig_pie, width="stretch")

    with col2:
        # Package breakdown pie chart
        st.markdown("#### Package Breakdown")
        package_summaries = estimator.get_package_summaries(results)

        package_data: dict[str, list] = {
            'Package': [],
            'Cost': []
        }

        for package, summary in package_summaries.items():
            if summary['enabled'] and summary['cost'] > 0:
                package_data['Package'].append(package)
                package_data['Cost'].append(summary['cost'])

        if package_data['Package']:
            fig_package = px.pie(
                values=package_data['Cost'],
                names=package_data['Package'],
                title="Cost by Package"
            )
            st.plotly_chart(fig_package, width="stretch")

    # Stacked bar chart by stage and role
    st.markdown("#### Cost by Stage x Role")

    if results.base_role_hours:
        stage_role_data = []
        for rh in results.base_role_hours:
            stage_role_data.append({
                'Stage': rh.stage,
                'Role': rh.role,
                'Cost': rh.total_cost
            })

        df = pd.DataFrame(stage_role_data)

        fig_bar = px.bar(
            df,
            x='Stage',
            y='Cost',
            color='Role',
            title="Base N2S Cost by Stage and Role",
            labels={'Cost': 'Cost ($)'}
        )

        fig_bar.update_layout(height=500)
        st.plotly_chart(fig_bar, width="stretch")


def render_help_tab() -> None:
    """Render comprehensive help and documentation tab."""
    st.subheader("How this estimate is built")
    
    # Pipeline explanation
    st.markdown("### 📋 Estimation Pipeline")
    st.markdown("""
    **10-Step Process:**
    
    1. **Start from Base N2S baseline** (6,700h)
    2. **Apply Size & Delivery Type multipliers** (Small 0.85x, Medium 1.0x, Large 1.25x, Very Large 1.5x; Modernization 0.9x, Net New 1.0x)
    3. **Apply Product scaler** (Banner: 1.0x Net New, 0.9x Modernization; Colleague: 0.85x Net New, 0.75x Modernization)
    4. **Apply Sprint 0 uplift** (configurable % of total added to Sprint 0, subtracted from Plan+Configure)
    5. **Allocate to stages** via adjusted Stage Weights (Start 2.5%, Prepare 2.5%, Plan 10%, Configure 34%, Test 20%, Deploy 10%, etc.)
    6. **Split presales vs delivery** by Activities/Stages (Start 60% presales, Prepare 30% presales, others 0%)
    7. **Expand delivery hours to roles** by per-stage Role Mix (Configure heavily weighted to technical roles)
    8. **Apply Onshore/Offshore/Partner split** (global 70/20/10 or per-role overrides)
    9. **Price via rate cards** (selected Locale affects rates, not hours)
    10. **Add-ons** (Integrations, Reports, Degree Works) computed similarly with product package multipliers
    11. **Subtotals by package** (Base N2S + enabled add-ons)
    12. **Export** a styled Excel workbook with all breakdowns
    """)
    
    # Degree Works Setup explanation
    st.markdown("### 🏗️ Degree Works Setup (size-scaled)")
    st.info("""
    **One-time Setup & Enablement** (300h @ Medium, scaled by Size)
    
    **Covers:**
    - Environment/config setup
    - Integration with existing systems  
    - Training and documentation
    - Governance and workflows
    - Testing and validation
    
    **Delivery only** (no presales component)
    """)
    
    # Degree Works PVEs explanation  
    st.markdown("### 📚 Degree Works PVEs (Program-Version Equivalents)")
    st.info("""
    **PVEs approximate** how many requirement blocks must be scribed at go-live:
    
    **Formula:** `PVEs = Majors + 0.5 × (Minors + Certificates + Concentrations) × Catalog Years`
    
    **Complexity tiers:**
    - **Simple** (24h): Straightforward degree requirements
    - **Standard** (48h): Moderate complexity with some conditional logic
    - **Complex** (96h): Advanced requirements with extensive rules
    
    **You set the mix** based on your institution's catalog complexity.
    
    **Delivery only** (no presales component)
    """)
    
    # Degree Works cap explanation
    st.markdown("### 🛡️ Degree Works Cap (Size-based Guardrails)")
    st.info("""
    **Degree Works totals are capped by size** (Small 300h, Medium 400h, Large 500h, Very Large 600h by default). 
    We clamp PVEs after applying Setup so the overall DW estimate cannot exceed the cap.
    
    **Cap Logic:**
    - Setup hours are always preserved (size-scaled)
    - PVEs are clamped if total would exceed cap
    - If Setup alone approaches cap, PVEs drop to near-zero
    - Cap can be overridden in Advanced Settings
    """)
    
    # Product multipliers explanation
    st.markdown("### 🏢 Product Multipliers")
    st.info("""
    **Why Colleague estimates are lower by default:**
    
    Colleague implementations and modernizations at small–mid sized colleges often complete faster than large Banner programs 
    (e.g., SMC's Colleague SaaS modernization in ~9 months), while multi‑campus Banner ERP programs can span years with higher complexity. 
    Our estimator reflects that by applying product‑specific multipliers and by disabling Technical Architect for Colleague.
    
    **Sources:** SMC modernization (9 months); CCCS Banner program (5 years, $26M).
    """)
    
    # Product multiplier tables
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Product × Delivery Type Multipliers")
        st.dataframe({
            'Product': ['Banner', 'Banner', 'Colleague', 'Colleague'],
            'Delivery Type': ['Net New', 'Modernization', 'Net New', 'Modernization'],
            'Multiplier': ['1.00x', '0.90x', '0.85x', '0.75x']
        }, use_container_width=True)
    
    with col2:
        st.markdown("#### Product × Package Multipliers")
        st.dataframe({
            'Product': ['Banner', 'Banner', 'Banner', 'Colleague', 'Colleague', 'Colleague'],
            'Package': ['Integrations', 'Reports', 'Degree Works', 'Integrations', 'Reports', 'Degree Works'],
            'Multiplier': ['1.00x', '1.00x', '1.00x', '0.90x', '0.90x', '0.00x']
        }, use_container_width=True)
    
    # Important notes
    st.markdown("### ⚠️ Notes & Guardrails")
    st.warning("""
    **Key Rules:**
    - **Only Setup is size-scaled** (300h → 375h for Large schools)
    - **PVEs are NOT size-scaled** (complexity is independent of school size)
    - **DegreeWorks Scribe is Banner-only** by default (Product Role Map)
    - **All tier mixes must sum to 100%** (validated automatically)
    - **Integrations & Reports** calculations remain completely unchanged
    - **Stage Summary toggle** shows base-only vs all-packages view
    - **Sprint 0 uplift** adds configurable % to Sprint 0, subtracts from Plan+Configure
    """)
    
    # Role distribution details
    st.markdown("### 👥 Role Distributions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Setup & PVE Simple:**")
        st.write("- DegreeWorks Scribe: 70%")
        st.write("- Functional Consultant: 20%") 
        st.write("- Technical Architect: 10%")
    
    with col2:
        st.markdown("**PVE Standard & Complex:**")
        st.write("- **Standard:** DWS 60%, FC 25%, TA 15%")
        st.write("- **Complex:** DWS 50%, FC 30%, TA 20%")
        st.write("- *(More complex = more consulting/architecture)*")


def render_assumptions_tab(results: 'EstimationResults', estimator: 'N2SEstimator') -> None:
    """Render assumptions and inputs summary."""
    st.subheader("Assumptions & Inputs")

    inputs = results.inputs

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Core Parameters")
        st.write(f"**Product:** {inputs.product}")
        st.write(f"**Delivery Type:** {inputs.delivery_type}")
        st.write(f"**Size Band:** {inputs.size_band}")
        st.write(f"**Locale:** {inputs.locale}")
        st.write(f"**Maturity Factor:** {inputs.maturity_factor:.2f}")
        
        st.markdown("#### Applied Multipliers")
        # Product delivery type multiplier
        product_mult = (
            estimator.config.product_delivery_type_multipliers
                .get(inputs.product, {})
                .get(inputs.delivery_type, 1.0)
        )
        st.write(f"**Product × Delivery Type:** {product_mult:.2f}x")
        
        # Size multiplier
        size_mult = estimator.config.size_multipliers.get(inputs.size_band, 1.0)
        st.write(f"**Size Band:** {size_mult:.2f}x")
        
        # Package multipliers for enabled add-ons
        if inputs.include_integrations or inputs.include_reports or inputs.include_degreeworks:
            st.write("**Package Multipliers:**")
            if inputs.include_integrations:
                pkg_mult = estimator.config.product_package_multipliers.get(inputs.product, {}).get('Integrations', 1.0)
                st.write(f"  - Integrations: {pkg_mult:.2f}x")
            if inputs.include_reports:
                pkg_mult = estimator.config.product_package_multipliers.get(inputs.product, {}).get('Reports', 1.0)
                st.write(f"  - Reports: {pkg_mult:.2f}x")
            if inputs.include_degreeworks:
                pkg_mult = estimator.config.product_package_multipliers.get(inputs.product, {}).get('Degree Works', 1.0)
                st.write(f"  - Degree Works: {pkg_mult:.2f}x")

    with col2:
        st.markdown("#### Add-on Packages")

        if inputs.include_integrations:
            st.write(f"**Integrations:** {inputs.integrations_count} items")
            st.write(f"  - Simple: {inputs.integrations_simple_pct:.1%}")
            st.write(f"  - Standard: {inputs.integrations_standard_pct:.1%}")
            st.write(f"  - Complex: {inputs.integrations_complex_pct:.1%}")
        else:
            st.write("**Integrations:** Disabled")

        if inputs.include_reports:
            st.write(f"**Reports:** {inputs.reports_count} items")
            st.write(f"  - Simple: {inputs.reports_simple_pct:.1%}")
            st.write(f"  - Standard: {inputs.reports_standard_pct:.1%}")
            st.write(f"  - Complex: {inputs.reports_complex_pct:.1%}")
        else:
            st.write("**Reports:** Disabled")

        if inputs.include_degreeworks:
            st.write("**Degree Works:**")
            if inputs.degreeworks_include_setup:
                st.write(f"  - Setup: 300h @ Medium (size-scaled)")
            if inputs.degreeworks_use_pve_calculator:
                computed_pves = (
                    inputs.degreeworks_majors + 
                    0.5 * (inputs.degreeworks_minors + inputs.degreeworks_certificates + inputs.degreeworks_concentrations)
                ) * inputs.degreeworks_catalog_years
                st.write(f"  - PVEs: {computed_pves:.1f} (calculated)")
                st.write(f"    • Majors: {inputs.degreeworks_majors}, Others: {inputs.degreeworks_minors + inputs.degreeworks_certificates + inputs.degreeworks_concentrations}")
            else:
                st.write(f"  - PVEs: {inputs.degreeworks_pve_count} (direct)")
            st.write(f"  - PVE Mix: Simple {inputs.degreeworks_simple_pct:.1%}, Standard {inputs.degreeworks_standard_pct:.1%}, Complex {inputs.degreeworks_complex_pct:.1%}")
        else:
            st.write("**Degree Works:** Disabled")

    # Multipliers
    st.markdown("#### Applied Multipliers")
    st.write("**Size Multipliers:**")
    st.write("- Small (<5k): 0.85x")
    st.write("- Medium (5-15k): 1.00x")
    st.write("- Large (15-30k): 1.25x")
    st.write("- Very Large (>30k): 1.50x")

    st.write("**Delivery Type Multipliers:**")
    st.write("- Modernization: 0.90x")
    st.write("- Net New: 1.00x")


def render_rates_tab(estimator: N2SEstimator) -> None:
    """Render Rates & Mixes editor tab."""
    st.subheader("Rates & Mixes")
    
    # Show validation warnings for current overrides
    pricing_warnings = validate_pricing_overrides(
        st.session_state.rate_overrides,
        st.session_state.global_mix_override,
        st.session_state.role_mix_overrides
    )
    
    if pricing_warnings:
        with st.expander("⚠️ Pricing Override Warnings", expanded=True):
            for warning in pricing_warnings:
                st.warning(warning)

    # --- Delivery Mix Editors ---
    st.markdown("### Delivery Mix")
    col_g, col_r = st.columns([1, 2])

    with col_g:
        st.markdown("**Global Delivery Split**")
        # Start with effective current global or defaults
        eff_mix = estimator.pricing._delivery_mix_cache.get(None) if estimator.pricing else None
        g_on = st.number_input(
            "Onshore %", 
            min_value=0.0, 
            max_value=1.0,
            value=(eff_mix.onshore_pct if eff_mix else 0.70), 
            step=0.05, 
            key="g_on",
            help="Sets the default Onshore/Offshore/Partner percentages for all roles not explicitly overridden. Must total 100%."
        )
        g_off = st.number_input(
            "Offshore %", 
            min_value=0.0, 
            max_value=1.0,
            value=(eff_mix.offshore_pct if eff_mix else 0.20), 
            step=0.05, 
            key="g_off"
        )
        g_pa = 1.0 - g_on - g_off
        st.write(f"Partner %: {g_pa:.2f}")
        if abs(g_on + g_off + g_pa - 1.0) > 0.001:
            st.error("Global mix must sum to 1.0")
        if st.button("Apply Global Mix"):
            st.session_state.global_mix_override = {
                'onshore_pct': g_on, 
                'offshore_pct': g_off, 
                'partner_pct': g_pa
            }
            estimator.apply_delivery_mix_overrides(st.session_state.global_mix_override, [])
            st.success("Global delivery mix applied.")

    with col_r:
        st.markdown("**Per‑Role Delivery Overrides**")
        # Build a frame of effective per-role mix for enabled roles
        if estimator.pricing:
            roles = sorted(set(rm.role for rm in estimator.config.role_mix))
            rows = []
            for role in roles:
                dm = estimator.pricing._delivery_mix_cache.get(role)
                if not dm:
                    # show global values for reference
                    base = estimator.pricing._delivery_mix_cache.get(None)
                    dm = base or DeliveryMix(role=role, onshore_pct=0.70, offshore_pct=0.20, partner_pct=0.10)
                rows.append({
                    'Role': role,
                    'Onshore %': round(dm.onshore_pct, 3),
                    'Offshore %': round(dm.offshore_pct, 3),
                    'Partner %': round(dm.partner_pct, 3)
                })
            df_mix = st.data_editor(
                pd.DataFrame(rows),
                width="stretch",
                num_rows="dynamic",
                key="mix_editor"
            )
            st.caption("Overrides the global split for selected roles. Each row must total 100%.")
            if st.button("Apply Per‑Role Mix"):
                overrides = []
                for _, r in df_mix.iterrows():
                    total = float(r['Onshore %']) + float(r['Offshore %']) + float(r['Partner %'])
                    if abs(total - 1.0) > 0.001:
                        st.error(f"Mix for role {r['Role']} must sum to 1.0")
                        st.stop()
                    overrides.append({
                        'role': r['Role'],
                        'onshore_pct': float(r['Onshore %']),
                        'offshore_pct': float(r['Offshore %']),
                        'partner_pct': float(r['Partner %'])
                    })
                st.session_state.role_mix_overrides = overrides
                estimator.apply_delivery_mix_overrides(None, overrides)
                st.success("Per‑role delivery overrides applied.")

    st.markdown("---")

    # --- Rates Editor ---
    st.markdown("### Rate Cards")
    col_l, col_a = st.columns([1, 3])

    with col_l:
        locale_selector = st.selectbox("Locale to edit", ["US", "Canada", "UK", "EU", "ANZ", "MENA"], index=0)
        show_all = st.checkbox("Show all locales table", value=False, help="If unchecked, edits the selected locale only.")
        st.info("Tip: Hours are unaffected by locale; rates change cost only.")

    # Build editable DataFrame of rates
    if estimator.pricing:
        if show_all:
            rc_list = estimator.pricing.get_effective_rates(locale=None)
            data = [{
                'Role': rc.role, 
                'Locale': rc.locale,
                'Onshore Rate': rc.onshore, 
                'Offshore Rate': rc.offshore, 
                'Partner Rate': rc.partner
            } for rc in rc_list]
        else:
            rc_list = estimator.pricing.get_effective_rates(locale=locale_selector)
            data = [{
                'Role': rc.role, 
                'Locale': locale_selector,
                'Onshore Rate': rc.onshore, 
                'Offshore Rate': rc.offshore, 
                'Partner Rate': rc.partner
            } for rc in rc_list]

        df_rates = st.data_editor(
            pd.DataFrame(data),
            width="stretch",
            num_rows="dynamic",
            key="rates_editor",
            column_config={
                'Onshore Rate': st.column_config.NumberColumn(min_value=0.01, step=5.0, format="$%.2f"),
                'Offshore Rate': st.column_config.NumberColumn(min_value=0.01, step=5.0, format="$%.2f"),
                'Partner Rate': st.column_config.NumberColumn(min_value=0.01, step=5.0, format="$%.2f"),
            }
        )
        st.caption("Rates are per role and locale. Editing here updates this scenario only. Hours do not change with locale; costs do.")

        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("Apply Rates"):
                overrides = []
                for _, r in df_rates.iterrows():
                    # basic validation
                    if r['Onshore Rate'] <= 0 or r['Offshore Rate'] <= 0 or r['Partner Rate'] <= 0:
                        st.error(f"Rates must be > 0 for role {r['Role']} ({r['Locale']})")
                        st.stop()
                    overrides.append({
                        'role': r['Role'],
                        'locale': r['Locale'],
                        'onshore': float(r['Onshore Rate']),
                        'offshore': float(r['Offshore Rate']),
                        'partner': float(r['Partner Rate'])
                    })
                st.session_state.rate_overrides = overrides
                estimator.apply_rate_overrides(overrides)
                st.success("Rates applied.")
        with c2:
            if st.button("Reset to Workbook Defaults", help="Discard all runtime pricing overrides and reload workbook rates & mixes."):
                estimator.reset_pricing_overrides()
                st.session_state.rate_overrides = []
                st.session_state.global_mix_override = None
                st.session_state.role_mix_overrides = []
                st.info("Pricing reset to workbook values. Re‑run estimation if needed.")
        with c3:
            if st.button("Recalculate with Current Pricing"):
                st.rerun()


def main() -> None:
    """Main application entry point."""
    initialize_session_state()

    # Load estimator
    try:
        estimator = load_estimator()
    except Exception as e:
        st.error(f"Failed to load estimator: {e}")
        st.stop()

    # Render sidebar and get inputs
    inputs = render_sidebar()

    # Check if inputs have changed and force rerun if needed
    inputs_changed = False
    if hasattr(st.session_state, 'inputs'):
        old_inputs = st.session_state.inputs
        if (inputs.product != old_inputs.product or 
            inputs.delivery_type != old_inputs.delivery_type or
            inputs.size_band != old_inputs.size_band or
            inputs.locale != old_inputs.locale or
            inputs.include_integrations != old_inputs.include_integrations or
            inputs.include_reports != old_inputs.include_reports or
            inputs.include_degreeworks != old_inputs.include_degreeworks):
            inputs_changed = True

    # Update session state
    st.session_state.inputs = inputs

    # Force rerun if inputs changed
    if inputs_changed:
        st.rerun()

    # Run estimation
    try:
        results = estimator.estimate(inputs)
        st.session_state.results = results
    except Exception as e:
        st.error(f"Estimation failed: {e}")
        st.stop()

    # Main content area
    st.title("N2S Delivery Estimator")

    # Display validation warnings
    warnings = estimator.get_validation_warnings()
    if warnings:
        with st.expander("⚠️ Configuration Warnings", expanded=False):
            for warning in warnings:
                st.warning(warning)

    # Summary cards
    render_summary_cards(estimator, results)

    # Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Base N2S", "Integrations", "Reports", "Degree Works", "Charts", "How this estimate is built", "Assumptions", "Rates & Mixes"
    ])

    with tab1:
        render_base_n2s_tab(estimator, results)

    with tab2:
        render_integrations_tab(estimator, results)

    with tab3:
        render_reports_tab(estimator, results)

    with tab4:
        render_degreeworks_tab(estimator, results, inputs)

    with tab5:
        render_charts_tab(estimator, results)

    with tab6:
        render_help_tab()

    with tab7:
        render_assumptions_tab(results, estimator)

    with tab8:
        render_rates_tab(estimator)

    # Excel export
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("📁 Export to Excel", type="primary", width="stretch"):
            try:
                exporter = ExcelExporter()
                excel_data = exporter.export_to_excel(results, estimator)

                filename = f"N2S_Estimate_{inputs.product}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"

                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width="stretch"
                )

                st.success("Excel file generated successfully!")
            except Exception as e:
                st.error(f"Excel export failed: {e}")

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "N2S Delivery Estimator v0.9 | Built with Streamlit"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
