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

from n2s_estimator.engine.datatypes import EstimationInputs
from n2s_estimator.engine.orchestrator import N2SEstimator
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


def render_sidebar() -> EstimationInputs:
    """Render sidebar controls and return estimation inputs."""
    st.sidebar.title("📊 N2S Estimator")
    st.sidebar.markdown("---")

    # Core Parameters
    st.sidebar.subheader("Core Parameters")

    product = st.sidebar.selectbox(
        "Product",
        ["Banner", "Colleague"],
        index=0 if st.session_state.inputs.product == "Banner" else 1
    )

    delivery_type = st.sidebar.selectbox(
        "Delivery Type",
        ["Net New", "Modernization"],
        index=0 if st.session_state.inputs.delivery_type == "Net New" else 1
    )

    size_band = st.sidebar.selectbox(
        "Size of School",
        ["Small (<5k)", "Medium (5-15k)", "Large (15-30k)", "Very Large (>30k)"],
        index=["Small", "Medium", "Large", "Very Large"].index(
            st.session_state.inputs.size_band.split()[0] if st.session_state.inputs.size_band else "Medium"
        )
    )

    locale = st.sidebar.selectbox(
        "Locale/Region",
        ["US", "Canada", "UK", "EU", "ANZ", "MENA"],
        index=["US", "Canada", "UK", "EU", "ANZ", "MENA"].index(st.session_state.inputs.locale)
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
        value=st.session_state.inputs.include_integrations
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
        value=st.session_state.inputs.include_reports
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

    # Scenario Management
    st.sidebar.markdown("---")
    st.sidebar.subheader("Scenario Management")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("Save Scenario", use_container_width=True):
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
                'maturity_factor': maturity_factor
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
        include_reports=include_reports
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

    col1, col2, col3 = st.columns(3)

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
            use_container_width=True,
            column_config={
                'Total Cost': st.column_config.NumberColumn(format="$%d"),
                'Blended Rate': st.column_config.NumberColumn(format="$%d/hr")
            }
        )

    col1, col2 = st.columns(2)

    with col1:
        # Stage summary
        st.markdown("#### Stage Summary")
        stage_summary = estimator.get_stage_summary(results)
        if stage_summary:
            stage_df = pd.DataFrame([{
                'Stage': rh.stage,
                'Hours': rh.total_hours,
                'Cost': rh.total_cost
            } for rh in stage_summary])

            stage_df['Hours'] = stage_df['Hours'].round(1)
            stage_df['Cost'] = stage_df['Cost'].round(0)

            st.dataframe(
                stage_df,
                use_container_width=True,
                column_config={
                    'Cost': st.column_config.NumberColumn(format="$%d")
                }
            )

    with col2:
        # Role summary
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
                use_container_width=True,
                column_config={
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
            use_container_width=True,
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
            use_container_width=True,
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
            use_container_width=True,
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
            use_container_width=True,
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
            st.plotly_chart(fig_pie, use_container_width=True)

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
            st.plotly_chart(fig_package, use_container_width=True)

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
        st.plotly_chart(fig_bar, use_container_width=True)


def render_assumptions_tab(results: 'EstimationResults') -> None:
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

    # Update session state
    st.session_state.inputs = inputs

    # Run estimation
    try:
        results = estimator.estimate(inputs)
        st.session_state.results = results
    except Exception as e:
        st.error(f"Estimation failed: {e}")
        st.stop()

    # Main content area
    st.title("📊 N2S Delivery Estimator")

    # Display validation warnings
    warnings = estimator.get_validation_warnings()
    if warnings:
        with st.expander("⚠️ Configuration Warnings", expanded=False):
            for warning in warnings:
                st.warning(warning)

    # Summary cards
    render_summary_cards(estimator, results)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Base N2S", "Integrations", "Reports", "Charts", "Assumptions"
    ])

    with tab1:
        render_base_n2s_tab(estimator, results)

    with tab2:
        render_integrations_tab(estimator, results)

    with tab3:
        render_reports_tab(estimator, results)

    with tab4:
        render_charts_tab(estimator, results)

    with tab5:
        render_assumptions_tab(results)

    # Excel export
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        if st.button("📁 Export to Excel", type="primary", use_container_width=True):
            try:
                exporter = ExcelExporter()
                excel_data = exporter.export_to_excel(results, estimator)

                filename = f"N2S_Estimate_{inputs.product}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"

                st.download_button(
                    label="Download Excel File",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
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
