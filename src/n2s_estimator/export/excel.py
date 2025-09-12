"""Excel export functionality for N2S Estimator results."""

import io
from datetime import datetime
from typing import Any

import xlsxwriter
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

from ..engine.datatypes import EstimationResults
from ..engine.orchestrator import N2SEstimator


class ExcelExporter:
    """Exports N2S estimation results to styled Excel workbook."""

    def __init__(self) -> None:
        """Initialize Excel exporter."""
        self.workbook: Workbook = None
        self.formats: dict[str, Any] = {}

    def export_to_excel(self, results: EstimationResults, estimator: N2SEstimator) -> bytes:
        """
        Export estimation results to Excel workbook.

        Returns bytes of the Excel file for download.
        """
        # Create in-memory buffer
        output = io.BytesIO()

        # Create workbook
        self.workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        self._create_formats()

        # Create comprehensive sheets matching Streamlit UI
        self._create_executive_summary_sheet(results, estimator)
        self._create_package_summary_sheet(results, estimator)
        self._create_base_n2s_sheet(results, estimator)

        if results.integrations_role_hours:
            self._create_integrations_sheet(results, estimator)

        if results.reports_role_hours:
            self._create_reports_sheet(results, estimator)

        if results.degreeworks_role_hours:
            self._create_degreeworks_sheet(results, estimator)

        self._create_charts_and_analysis_sheet(results, estimator)
        self._create_rates_and_mixes_sheet(results, estimator)
        self._create_scenario_inputs_sheet(results, estimator)
        self._create_assumptions_sheet(results)
        self._create_sources_sheet()

        # Close workbook and return bytes
        self.workbook.close()
        output.seek(0)
        return output.read()

    def _create_formats(self) -> None:
        """Create cell formats for styling."""
        self.formats = {
            'header': self.workbook.add_format({
                'bold': True,
                'font_color': 'white',
                'bg_color': '#4472C4',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            }),
            'currency': self.workbook.add_format({
                'num_format': '$#,##0',
                'align': 'right'
            }),
            'currency_bold': self.workbook.add_format({
                'num_format': '$#,##0',
                'align': 'right',
                'bold': True
            }),
            'percent': self.workbook.add_format({
                'num_format': '0.0%',
                'align': 'right'
            }),
            'hours': self.workbook.add_format({
                'num_format': '#,##0',
                'align': 'right'
            }),
            'hours_bold': self.workbook.add_format({
                'num_format': '#,##0',
                'align': 'right',
                'bold': True
            }),
            'bold': self.workbook.add_format({
                'bold': True
            }),
            'title': self.workbook.add_format({
                'font_size': 16,
                'bold': True,
                'font_color': '#4472C4'
            }),
            'subtitle': self.workbook.add_format({
                'font_size': 12,
                'bold': True
            }),
            'note': self.workbook.add_format({
                'font_size': 10,
                'font_color': '#666666',
                'italic': True
            })
        }

    def _create_executive_summary_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create executive summary sheet with key metrics and KPIs."""
        worksheet = self.workbook.add_worksheet('Executive Summary')

        # Title and metadata
        worksheet.write(0, 0, 'N2S Delivery Estimator - Executive Summary', self.formats['title'])
        worksheet.write(1, 0, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        worksheet.write(2, 0, f"Version: 0.12.1")

        # Key metrics in a clean layout
        row = 4
        worksheet.write(row, 0, 'Key Performance Indicators', self.formats['subtitle'])
        row += 1

        # Calculate package totals
        base_hours = sum(rh.total_hours for rh in results.base_role_hours)
        base_cost = sum(rh.total_cost for rh in results.base_role_hours)
        
        integrations_hours = sum(rh.total_hours for rh in results.integrations_role_hours) if results.integrations_role_hours else 0
        integrations_cost = sum(rh.total_cost for rh in results.integrations_role_hours) if results.integrations_role_hours else 0
        
        reports_hours = sum(rh.total_hours for rh in results.reports_role_hours) if results.reports_role_hours else 0
        reports_cost = sum(rh.total_cost for rh in results.reports_role_hours) if results.reports_role_hours else 0
        
        degreeworks_hours = sum(rh.total_hours for rh in results.degreeworks_role_hours) if results.degreeworks_role_hours else 0
        degreeworks_cost = sum(rh.total_cost for rh in results.degreeworks_role_hours) if results.degreeworks_role_hours else 0

        # Key metrics table
        metrics = [
            ('Total Project Hours', results.total_hours, 'hours_bold'),
            ('Total Project Cost', results.total_cost, 'currency_bold'),
            ('', '', ''),
            ('Base N2S Hours', base_hours, 'hours'),
            ('Base N2S Cost', base_cost, 'currency'),
            ('', '', ''),
            ('Integrations Hours', integrations_hours, 'hours'),
            ('Integrations Cost', integrations_cost, 'currency'),
            ('', '', ''),
            ('Reports Hours', reports_hours, 'hours'),
            ('Reports Cost', reports_cost, 'currency'),
            ('', '', ''),
            ('Degree Works Hours', degreeworks_hours, 'hours'),
            ('Degree Works Cost', degreeworks_cost, 'currency'),
            ('', '', ''),
            ('Presales Hours', results.total_presales_hours, 'hours'),
            ('Presales Cost', results.total_presales_cost, 'currency'),
            ('Delivery Hours', results.total_delivery_hours, 'hours'),
            ('Delivery Cost', results.total_delivery_cost, 'currency')
        ]

        for metric, value, fmt in metrics:
            if metric:  # Skip empty rows
                worksheet.write(row, 0, metric, self.formats['bold'])
                worksheet.write(row, 1, value, self.formats[fmt])
            row += 1

        # Delivery split summary
        row += 1
        worksheet.write(row, 0, 'Delivery Split Summary', self.formats['subtitle'])
        row += 1

        delivery_split = estimator.get_delivery_split_summary(results)
        split_headers = ['Split Type', 'Hours', 'Hours %', 'Cost', 'Cost %']
        for col, header in enumerate(split_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        for split_name in ['onshore', 'offshore', 'partner']:
            split_data = delivery_split[split_name]
            worksheet.write(row, 0, split_name.title())
            worksheet.write(row, 1, split_data['hours'], self.formats['hours'])
            worksheet.write(row, 2, split_data['hours_pct'], self.formats['percent'])
            worksheet.write(row, 3, split_data['cost'], self.formats['currency'])
            worksheet.write(row, 4, split_data['cost_pct'], self.formats['percent'])
            row += 1

        # Project configuration summary
        row += 1
        worksheet.write(row, 0, 'Project Configuration', self.formats['subtitle'])
        row += 1

        config_data = [
            ('Product', results.inputs.product),
            ('Delivery Type', results.inputs.delivery_type),
            ('Size Band', results.inputs.size_band),
            ('Locale/Region', results.inputs.locale),
            ('Maturity Factor', f'{results.inputs.maturity_factor:.2f}'),
            ('Sprint 0 Uplift', f'{results.inputs.sprint0_uplift_pct:.1%}')
        ]

        for param, value in config_data:
            worksheet.write(row, 0, param, self.formats['bold'])
            worksheet.write(row, 1, value)
            row += 1

        self._autofit_columns(worksheet, 5)

    def _create_package_summary_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create comprehensive package summary sheet matching Streamlit Package Summary."""
        worksheet = self.workbook.add_worksheet('Package Summary')

        worksheet.write(0, 0, 'Comprehensive Package Summary', self.formats['title'])

        # Calculate package totals
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

        # Package breakdown table
        row = 2
        headers = ['Package', 'Hours', 'Cost', 'Hours %', 'Cost %', 'Enabled']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        packages = [
            ('Base N2S', base_hours, base_cost, base_hours/total_hours if total_hours > 0 else 0, base_cost/total_cost if total_cost > 0 else 0, True),
            ('Integrations', integrations_hours, integrations_cost, integrations_hours/total_hours if total_hours > 0 else 0, integrations_cost/total_cost if total_cost > 0 else 0, results.inputs.include_integrations),
            ('Reports', reports_hours, reports_cost, reports_hours/total_hours if total_hours > 0 else 0, reports_cost/total_cost if total_cost > 0 else 0, results.inputs.include_reports),
            ('Degree Works', degreeworks_hours, degreeworks_cost, degreeworks_hours/total_hours if total_hours > 0 else 0, degreeworks_cost/total_cost if total_cost > 0 else 0, results.inputs.include_degreeworks),
            ('TOTAL', total_hours, total_cost, 1.0, 1.0, True)
        ]

        for package, hours, cost, hours_pct, cost_pct, enabled in packages:
            worksheet.write(row, 0, package, self.formats['bold'] if package == 'TOTAL' else None)
            worksheet.write(row, 1, hours, self.formats['hours_bold'] if package == 'TOTAL' else self.formats['hours'])
            worksheet.write(row, 2, cost, self.formats['currency_bold'] if package == 'TOTAL' else self.formats['currency'])
            worksheet.write(row, 3, hours_pct, self.formats['percent'])
            worksheet.write(row, 4, cost_pct, self.formats['percent'])
            worksheet.write(row, 5, 'Yes' if enabled else 'No')
            row += 1

        # Add conditional formatting for totals row
        worksheet.conditional_format(
            2, 1, row-1, 2,  # Hours and Cost columns
            {'type': 'data_bar', 'bar_color': '#4472C4'}
        )

        self._autofit_columns(worksheet, 6)

    def _create_summary_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create summary sheet with KPIs and charts."""
        worksheet = self.workbook.add_worksheet('Summary')

        # Title
        worksheet.write(0, 0, 'N2S Delivery Estimate Summary', self.formats['title'])
        worksheet.write(1, 0, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Key metrics
        row = 3
        worksheet.write(row, 0, 'Key Metrics', self.formats['subtitle'])
        row += 1

        metrics = [
            ('Total Hours', results.total_hours, 'hours_bold'),
            ('Total Cost', results.total_cost, 'currency_bold'),
            ('Presales Hours', results.total_presales_hours, 'hours'),
            ('Delivery Hours', results.total_delivery_hours, 'hours'),
            ('Presales Cost', results.total_presales_cost, 'currency'),
            ('Delivery Cost', results.total_delivery_cost, 'currency')
        ]

        for metric, value, fmt in metrics:
            worksheet.write(row, 0, metric, self.formats['bold'])
            worksheet.write(row, 1, value, self.formats[fmt])
            row += 1

        # Package breakdown
        row += 1
        worksheet.write(row, 0, 'Package Breakdown', self.formats['subtitle'])
        row += 1

        package_summaries = estimator.get_package_summaries(results)

        # Headers
        headers = ['Package', 'Hours', 'Cost', 'Enabled']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        for package, summary in package_summaries.items():
            worksheet.write(row, 0, package)
            worksheet.write(row, 1, summary['hours'], self.formats['hours'])
            worksheet.write(row, 2, summary['cost'], self.formats['currency'])
            worksheet.write(row, 3, 'Yes' if summary['enabled'] else 'No')
            row += 1

        # Delivery split
        row += 1
        worksheet.write(row, 0, 'Delivery Split', self.formats['subtitle'])
        row += 1

        delivery_split = estimator.get_delivery_split_summary(results)

        split_headers = ['Split', 'Hours', 'Hours %', 'Cost', 'Cost %']
        for col, header in enumerate(split_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        for split_name in ['onshore', 'offshore', 'partner']:
            split_data = delivery_split[split_name]
            worksheet.write(row, 0, split_name.title())
            worksheet.write(row, 1, split_data['hours'], self.formats['hours'])
            worksheet.write(row, 2, split_data['hours_pct'], self.formats['percent'])
            worksheet.write(row, 3, split_data['cost'], self.formats['currency'])
            worksheet.write(row, 4, split_data['cost_pct'], self.formats['percent'])
            row += 1

        # Auto-fit columns
        self._autofit_columns(worksheet, 5)

    def _create_base_n2s_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create Base N2S detailed breakdown sheet."""
        worksheet = self.workbook.add_worksheet('Base N2S - Stage×Role')

        # Title
        worksheet.write(0, 0, 'Base N2S Package - Stage × Role Breakdown', self.formats['title'])

        # Stage x Role table
        row = 2
        headers = [
            'Stage', 'Role', 'Total Hours', 'Onshore Hours', 'Offshore Hours',
            'Partner Hours', 'Onshore Cost', 'Offshore Cost', 'Partner Cost',
            'Total Cost', 'Blended Rate'
        ]

        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        for rh in results.base_role_hours:
            worksheet.write(row, 0, rh.stage)
            worksheet.write(row, 1, rh.role)
            worksheet.write(row, 2, rh.total_hours, self.formats['hours'])
            worksheet.write(row, 3, rh.onshore_hours, self.formats['hours'])
            worksheet.write(row, 4, rh.offshore_hours, self.formats['hours'])
            worksheet.write(row, 5, rh.partner_hours, self.formats['hours'])
            worksheet.write(row, 6, rh.onshore_cost, self.formats['currency'])
            worksheet.write(row, 7, rh.offshore_cost, self.formats['currency'])
            worksheet.write(row, 8, rh.partner_cost, self.formats['currency'])
            worksheet.write(row, 9, rh.total_cost, self.formats['currency'])
            worksheet.write(row, 10, rh.blended_rate, self.formats['currency'])
            row += 1

        # Add conditional formatting for top costs
        if row > 4:  # If we have data
            worksheet.conditional_format(
                3, 9, row-1, 9,  # Total Cost column
                {'type': 'data_bar', 'bar_color': '#4472C4'}
            )

        # Stage summary
        row += 2
        worksheet.write(row, 0, 'Stage Summary', self.formats['subtitle'])
        row += 1

        stage_headers = ['Stage', 'Hours', 'Cost']
        for col, header in enumerate(stage_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        stage_summary = estimator.get_stage_summary(results)
        for rh in stage_summary:
            worksheet.write(row, 0, rh.stage)
            worksheet.write(row, 1, rh.total_hours, self.formats['hours'])
            worksheet.write(row, 2, rh.total_cost, self.formats['currency'])
            row += 1

        # Role summary
        role_start_col = 5
        worksheet.write(2 + len(results.base_role_hours) + 3, role_start_col, 'Role Summary', self.formats['subtitle'])

        role_row = 2 + len(results.base_role_hours) + 4
        role_headers = ['Role', 'Hours', 'Cost']
        for col, header in enumerate(role_headers):
            worksheet.write(role_row, role_start_col + col, header, self.formats['header'])
        role_row += 1

        role_summary = estimator.get_role_summary(results)
        for rh in role_summary:
            worksheet.write(role_row, role_start_col, rh.role)
            worksheet.write(role_row, role_start_col + 1, rh.total_hours, self.formats['hours'])
            worksheet.write(role_row, role_start_col + 2, rh.total_cost, self.formats['currency'])
            role_row += 1

        # Auto-fit and freeze
        self._autofit_columns(worksheet, len(headers))
        worksheet.freeze_panes(3, 0)  # Freeze header row

    def _create_integrations_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create Integrations add-on sheet."""
        worksheet = self.workbook.add_worksheet('Integrations')

        worksheet.write(0, 0, 'Integrations Add-on Package', self.formats['title'])

        # Tier breakdown
        row = 2
        worksheet.write(row, 0, 'Tier Breakdown', self.formats['subtitle'])
        row += 1

        tier_breakdown = estimator.addons.get_tier_breakdown('Integrations', results.inputs)

        if tier_breakdown:
            tier_headers = ['Tier', 'Count', 'Unit Hours', 'Total Hours', 'Mix %']
            for col, header in enumerate(tier_headers):
                worksheet.write(row, col, header, self.formats['header'])
            row += 1

            for tier, data in tier_breakdown.items():
                worksheet.write(row, 0, tier)
                worksheet.write(row, 1, data['count'], self.formats['hours'])
                worksheet.write(row, 2, data['unit_hours'], self.formats['hours'])
                worksheet.write(row, 3, data['total_hours'], self.formats['hours'])
                worksheet.write(row, 4, data['mix_percentage'], self.formats['percent'])
                row += 1

        # Role breakdown
        row += 1
        worksheet.write(row, 0, 'Role Breakdown', self.formats['subtitle'])
        row += 1

        role_headers = ['Role', 'Hours', 'Total Cost', 'Blended Rate']
        for col, header in enumerate(role_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        if results.integrations_role_hours:
            for rh in results.integrations_role_hours:
                worksheet.write(row, 0, rh.role)
                worksheet.write(row, 1, rh.total_hours, self.formats['hours'])
                worksheet.write(row, 2, rh.total_cost, self.formats['currency'])
                worksheet.write(row, 3, rh.blended_rate, self.formats['currency'])
                row += 1

        self._autofit_columns(worksheet, 5)

    def _create_reports_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create Reports add-on sheet."""
        worksheet = self.workbook.add_worksheet('Reports')

        worksheet.write(0, 0, 'Reports Add-on Package', self.formats['title'])

        # Tier breakdown
        row = 2
        worksheet.write(row, 0, 'Tier Breakdown', self.formats['subtitle'])
        row += 1

        tier_breakdown = estimator.addons.get_tier_breakdown('Reports', results.inputs)

        if tier_breakdown:
            tier_headers = ['Tier', 'Count', 'Unit Hours', 'Total Hours', 'Mix %']
            for col, header in enumerate(tier_headers):
                worksheet.write(row, col, header, self.formats['header'])
            row += 1

            for tier, data in tier_breakdown.items():
                worksheet.write(row, 0, tier)
                worksheet.write(row, 1, data['count'], self.formats['hours'])
                worksheet.write(row, 2, data['unit_hours'], self.formats['hours'])
                worksheet.write(row, 3, data['total_hours'], self.formats['hours'])
                worksheet.write(row, 4, data['mix_percentage'], self.formats['percent'])
                row += 1

        # Role breakdown
        row += 1
        worksheet.write(row, 0, 'Role Breakdown', self.formats['subtitle'])
        row += 1

        role_headers = ['Role', 'Hours', 'Total Cost', 'Blended Rate']
        for col, header in enumerate(role_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        if results.reports_role_hours:
            for rh in results.reports_role_hours:
                worksheet.write(row, 0, rh.role)
                worksheet.write(row, 1, rh.total_hours, self.formats['hours'])
                worksheet.write(row, 2, rh.total_cost, self.formats['currency'])
                worksheet.write(row, 3, rh.blended_rate, self.formats['currency'])
                row += 1

        self._autofit_columns(worksheet, 4)

    def _create_degreeworks_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create comprehensive Degree Works add-on sheet."""
        worksheet = self.workbook.add_worksheet('Degree Works')

        worksheet.write(0, 0, 'Degree Works Add-on Package', self.formats['title'])

        # Configuration summary
        row = 2
        worksheet.write(row, 0, 'Configuration Summary', self.formats['subtitle'])
        row += 1

        inputs = results.inputs
        config_data = [
            ('Include Degree Works', 'Yes' if inputs.include_degreeworks else 'No'),
            ('Include Setup Hours', 'Yes' if inputs.degreeworks_include_setup else 'No'),
            ('Use PVE Calculator', 'Yes' if inputs.degreeworks_use_pve_calculator else 'No'),
            ('Majors Count', inputs.degreeworks_majors),
            ('Minors Count', inputs.degreeworks_minors),
            ('Certificates Count', inputs.degreeworks_certificates),
            ('Concentrations Count', inputs.degreeworks_concentrations),
            ('Catalog Years', inputs.degreeworks_catalog_years),
            ('PVE Count', inputs.degreeworks_pve_count),
            ('Simple PVE %', f'{inputs.degreeworks_simple_pct:.1%}'),
            ('Standard PVE %', f'{inputs.degreeworks_standard_pct:.1%}'),
            ('Complex PVE %', f'{inputs.degreeworks_complex_pct:.1%}'),
            ('Cap Enabled', 'Yes' if inputs.degreeworks_cap_enabled else 'No'),
            ('Cap Hours', inputs.degreeworks_cap_hours if inputs.degreeworks_cap_enabled else 'N/A')
        ]

        for param, value in config_data:
            worksheet.write(row, 0, param, self.formats['bold'])
            worksheet.write(row, 1, value)
            row += 1

        # PVE breakdown
        row += 1
        worksheet.write(row, 0, 'PVE Complexity Breakdown', self.formats['subtitle'])
        row += 1

        pve_headers = ['Complexity', 'Count', 'Unit Hours', 'Total Hours', 'Mix %']
        for col, header in enumerate(pve_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        # Calculate PVE breakdown
        total_pve = inputs.degreeworks_pve_count
        simple_count = total_pve * inputs.degreeworks_simple_pct
        standard_count = total_pve * inputs.degreeworks_standard_pct
        complex_count = total_pve * inputs.degreeworks_complex_pct

        # These would need to come from the actual calculation - using estimates
        pve_data = [
            ('Simple', simple_count, 8, simple_count * 8, inputs.degreeworks_simple_pct),
            ('Standard', standard_count, 16, standard_count * 16, inputs.degreeworks_standard_pct),
            ('Complex', complex_count, 32, complex_count * 32, inputs.degreeworks_complex_pct)
        ]

        for complexity, count, unit_hours, total_hours, mix_pct in pve_data:
            worksheet.write(row, 0, complexity)
            worksheet.write(row, 1, count, self.formats['hours'])
            worksheet.write(row, 2, unit_hours, self.formats['hours'])
            worksheet.write(row, 3, total_hours, self.formats['hours'])
            worksheet.write(row, 4, mix_pct, self.formats['percent'])
            row += 1

        # Role breakdown
        row += 1
        worksheet.write(row, 0, 'Role Breakdown', self.formats['subtitle'])
        row += 1

        role_headers = ['Role', 'Hours', 'Total Cost', 'Blended Rate']
        for col, header in enumerate(role_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        if results.degreeworks_role_hours:
            for rh in results.degreeworks_role_hours:
                worksheet.write(row, 0, rh.role)
                worksheet.write(row, 1, rh.total_hours, self.formats['hours'])
                worksheet.write(row, 2, rh.total_cost, self.formats['currency'])
                worksheet.write(row, 3, rh.blended_rate, self.formats['currency'])
                row += 1

        self._autofit_columns(worksheet, 5)

    def _create_charts_and_analysis_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create charts and analysis sheet with data tables for visualization."""
        worksheet = self.workbook.add_worksheet('Charts & Analysis')

        worksheet.write(0, 0, 'Charts & Analysis Data', self.formats['title'])
        worksheet.write(1, 0, 'Data tables for creating charts and visualizations', self.formats['note'])

        # Delivery split data
        row = 3
        worksheet.write(row, 0, 'Delivery Split Data', self.formats['subtitle'])
        row += 1

        delivery_split = estimator.get_delivery_split_summary(results)
        split_headers = ['Split Type', 'Hours', 'Cost', 'Hours %', 'Cost %']
        for col, header in enumerate(split_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        for split_name in ['onshore', 'offshore', 'partner']:
            split_data = delivery_split[split_name]
            worksheet.write(row, 0, split_name.title())
            worksheet.write(row, 1, split_data['hours'], self.formats['hours'])
            worksheet.write(row, 2, split_data['cost'], self.formats['currency'])
            worksheet.write(row, 3, split_data['hours_pct'], self.formats['percent'])
            worksheet.write(row, 4, split_data['cost_pct'], self.formats['percent'])
            row += 1

        # Package breakdown data
        row += 1
        worksheet.write(row, 0, 'Package Breakdown Data', self.formats['subtitle'])
        row += 1

        package_summaries = estimator.get_package_summaries(results)
        package_headers = ['Package', 'Hours', 'Cost', 'Enabled']
        for col, header in enumerate(package_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        for package, summary in package_summaries.items():
            worksheet.write(row, 0, package)
            worksheet.write(row, 1, summary['hours'], self.formats['hours'])
            worksheet.write(row, 2, summary['cost'], self.formats['currency'])
            worksheet.write(row, 3, 'Yes' if summary['enabled'] else 'No')
            row += 1

        # Stage x Role cost matrix
        row += 1
        worksheet.write(row, 0, 'Stage x Role Cost Matrix', self.formats['subtitle'])
        row += 1

        if results.base_role_hours:
            # Get unique stages and roles
            stages = sorted(set(rh.stage for rh in results.base_role_hours))
            roles = sorted(set(rh.role for rh in results.base_role_hours))

            # Create matrix headers
            headers = ['Stage'] + roles
            for col, header in enumerate(headers):
                worksheet.write(row, col, header, self.formats['header'])
            row += 1

            # Fill matrix
            for stage in stages:
                worksheet.write(row, 0, stage)
                for col, role in enumerate(roles):
                    # Find cost for this stage/role combination
                    cost = 0
                    for rh in results.base_role_hours:
                        if rh.stage == stage and rh.role == role:
                            cost = rh.total_cost
                            break
                    worksheet.write(row, col + 1, cost, self.formats['currency'])
                row += 1

        self._autofit_columns(worksheet, 10)

    def _create_scenario_inputs_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create comprehensive scenario inputs sheet."""
        worksheet = self.workbook.add_worksheet('Scenario Inputs')

        worksheet.write(0, 0, 'Complete Scenario Inputs', self.formats['title'])
        worksheet.write(1, 0, 'All parameters used in this estimation scenario', self.formats['note'])

        inputs = results.inputs

        # Core parameters
        row = 3
        worksheet.write(row, 0, 'Core Parameters', self.formats['subtitle'])
        row += 1

        core_params = [
            ('Product', inputs.product),
            ('Delivery Type', inputs.delivery_type),
            ('Size Band', inputs.size_band),
            ('Locale/Region', inputs.locale),
            ('Maturity Factor', inputs.maturity_factor),
            ('Sprint 0 Uplift %', inputs.sprint0_uplift_pct)
        ]

        for param, value in core_params:
            worksheet.write(row, 0, param, self.formats['bold'])
            worksheet.write(row, 1, value)
            row += 1

        # Add-on packages
        row += 1
        worksheet.write(row, 0, 'Add-on Packages', self.formats['subtitle'])
        row += 1

        # Integrations
        worksheet.write(row, 0, 'Integrations', self.formats['bold'])
        row += 1
        integrations_params = [
            ('Include Integrations', inputs.include_integrations),
            ('Integrations Count', inputs.integrations_count),
            ('Simple %', inputs.integrations_simple_pct),
            ('Standard %', inputs.integrations_standard_pct),
            ('Complex %', inputs.integrations_complex_pct)
        ]
        for param, value in integrations_params:
            worksheet.write(row, 0, f'  {param}', self.formats['bold'])
            worksheet.write(row, 1, value)
            row += 1

        # Reports
        worksheet.write(row, 0, 'Reports', self.formats['bold'])
        row += 1
        reports_params = [
            ('Include Reports', inputs.include_reports),
            ('Reports Count', inputs.reports_count),
            ('Simple %', inputs.reports_simple_pct),
            ('Standard %', inputs.reports_standard_pct),
            ('Complex %', inputs.reports_complex_pct)
        ]
        for param, value in reports_params:
            worksheet.write(row, 0, f'  {param}', self.formats['bold'])
            worksheet.write(row, 1, value)
            row += 1

        # Degree Works
        worksheet.write(row, 0, 'Degree Works', self.formats['bold'])
        row += 1
        degreeworks_params = [
            ('Include Degree Works', inputs.include_degreeworks),
            ('Include Setup', inputs.degreeworks_include_setup),
            ('Use PVE Calculator', inputs.degreeworks_use_pve_calculator),
            ('Majors', inputs.degreeworks_majors),
            ('Minors', inputs.degreeworks_minors),
            ('Certificates', inputs.degreeworks_certificates),
            ('Concentrations', inputs.degreeworks_concentrations),
            ('Catalog Years', inputs.degreeworks_catalog_years),
            ('PVE Count', inputs.degreeworks_pve_count),
            ('Simple PVE %', inputs.degreeworks_simple_pct),
            ('Standard PVE %', inputs.degreeworks_standard_pct),
            ('Complex PVE %', inputs.degreeworks_complex_pct),
            ('Cap Enabled', inputs.degreeworks_cap_enabled),
            ('Cap Hours', inputs.degreeworks_cap_hours)
        ]
        for param, value in degreeworks_params:
            worksheet.write(row, 0, f'  {param}', self.formats['bold'])
            worksheet.write(row, 1, value)
            row += 1

        self._autofit_columns(worksheet, 2)

    def _create_rates_and_mixes_sheet(self, results: EstimationResults, estimator: N2SEstimator) -> None:
        """Create effective rates and delivery mixes sheet."""
        worksheet = self.workbook.add_worksheet('Rates & Mixes')

        worksheet.write(0, 0, 'Effective Rates & Delivery Mixes', self.formats['title'])
        worksheet.write(1, 0, 'Source: Workbook defaults + Runtime overrides', self.formats['note'])

        # Effective rates for selected locale
        row = 3
        worksheet.write(row, 0, f'Rates for {results.inputs.locale}', self.formats['subtitle'])
        row += 1

        rate_headers = ['Role', 'Onshore Rate', 'Offshore Rate', 'Partner Rate']
        for col, header in enumerate(rate_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        # Get effective rates using new API
        effective_rates = estimator.pricing.get_effective_rates(locale=results.inputs.locale)
        for rate in effective_rates:
            worksheet.write(row, 0, rate.role)
            worksheet.write(row, 1, rate.onshore, self.formats['currency'])
            worksheet.write(row, 2, rate.offshore, self.formats['currency'])
            worksheet.write(row, 3, rate.partner, self.formats['currency'])
            row += 1

        # Delivery mixes
        row += 1
        worksheet.write(row, 0, 'Delivery Mixes', self.formats['subtitle'])
        row += 1

        mix_headers = ['Role', 'Onshore %', 'Offshore %', 'Partner %', 'Source']
        for col, header in enumerate(mix_headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        # Get effective delivery mixes using new API
        effective_mixes = estimator.pricing.get_effective_delivery_mix()

        # Global mix (role=None)
        global_mix = None
        for mix in effective_mixes:
            if mix.role is None:
                global_mix = mix
                break

        if global_mix:
            worksheet.write(row, 0, 'Global (Default)')
            worksheet.write(row, 1, global_mix.onshore_pct, self.formats['percent'])
            worksheet.write(row, 2, global_mix.offshore_pct, self.formats['percent'])
            worksheet.write(row, 3, global_mix.partner_pct, self.formats['percent'])
            worksheet.write(row, 4, 'Workbook' if not hasattr(estimator.pricing, '_delivery_mix_cache') or estimator.pricing._delivery_mix_cache.get(None) is None else 'Overridden')
            row += 1

        # Per-role overrides
        for mix in effective_mixes:
            if mix.role is not None:
                worksheet.write(row, 0, f'{mix.role} (Override)')
                worksheet.write(row, 1, mix.onshore_pct, self.formats['percent'])
                worksheet.write(row, 2, mix.offshore_pct, self.formats['percent'])
                worksheet.write(row, 3, mix.partner_pct, self.formats['percent'])
                worksheet.write(row, 4, 'Workbook' if not hasattr(estimator.pricing, '_delivery_mix_cache') or estimator.pricing._delivery_mix_cache.get(mix.role) is None else 'Overridden')
                row += 1

        self._autofit_columns(worksheet, 5)

    def _create_assumptions_sheet(self, results: EstimationResults) -> None:
        """Create assumptions and inputs sheet."""
        worksheet = self.workbook.add_worksheet('Assumptions & Inputs')

        worksheet.write(0, 0, 'Assumptions & Inputs', self.formats['title'])

        inputs = results.inputs

        # Core parameters
        row = 2
        worksheet.write(row, 0, 'Core Parameters', self.formats['subtitle'])
        row += 1

        core_params = [
            ('Product', inputs.product),
            ('Delivery Type', inputs.delivery_type),
            ('Size Band', inputs.size_band),
            ('Locale/Region', inputs.locale),
            ('Maturity Factor', f'{inputs.maturity_factor:.2f}')
        ]

        for param, value in core_params:
            worksheet.write(row, 0, param, self.formats['bold'])
            worksheet.write(row, 1, value)
            row += 1

        # Add-on packages
        row += 1
        worksheet.write(row, 0, 'Add-on Packages', self.formats['subtitle'])
        row += 1

        # Integrations
        worksheet.write(row, 0, 'Integrations', self.formats['bold'])
        if inputs.include_integrations:
            worksheet.write(row, 1, f'{inputs.integrations_count} items')
            row += 1
            worksheet.write(row, 1, f'Simple: {inputs.integrations_simple_pct:.1%}')
            row += 1
            worksheet.write(row, 1, f'Standard: {inputs.integrations_standard_pct:.1%}')
            row += 1
            worksheet.write(row, 1, f'Complex: {inputs.integrations_complex_pct:.1%}')
        else:
            worksheet.write(row, 1, 'Disabled')
        row += 1

        # Reports
        worksheet.write(row, 0, 'Reports', self.formats['bold'])
        if inputs.include_reports:
            worksheet.write(row, 1, f'{inputs.reports_count} items')
            row += 1
            worksheet.write(row, 1, f'Simple: {inputs.reports_simple_pct:.1%}')
            row += 1
            worksheet.write(row, 1, f'Standard: {inputs.reports_standard_pct:.1%}')
            row += 1
            worksheet.write(row, 1, f'Complex: {inputs.reports_complex_pct:.1%}')
        else:
            worksheet.write(row, 1, 'Disabled')
        row += 1

        # Multipliers
        row += 1
        worksheet.write(row, 0, 'Applied Multipliers', self.formats['subtitle'])
        row += 1

        multipliers = [
            ('Size Multipliers', ''),
            ('  Small (<5k)', '0.85x'),
            ('  Medium (5-15k)', '1.00x'),
            ('  Large (15-30k)', '1.25x'),
            ('  Very Large (>30k)', '1.50x'),
            ('', ''),
            ('Delivery Type Multipliers', ''),
            ('  Modernization', '0.90x'),
            ('  Net New', '1.00x')
        ]

        for param, value in multipliers:
            if param and not param.startswith('  '):
                worksheet.write(row, 0, param, self.formats['bold'])
            else:
                worksheet.write(row, 0, param)
            worksheet.write(row, 1, value)
            row += 1

        self._autofit_columns(worksheet, 2)

    def _create_sources_sheet(self) -> None:
        """Create sources and metadata sheet."""
        worksheet = self.workbook.add_worksheet('Sources')

        worksheet.write(0, 0, 'Sources & Metadata', self.formats['title'])

        row = 2
        worksheet.write(row, 0, 'Data Sources', self.formats['subtitle'])
        row += 1

        sources = [
            ('n2s_estimator.xlsx', 'Configuration workbook', datetime.now().strftime('%Y-%m-%d')),
            ('N2S_Estimator_v1.xlsx', 'Reference data (specified)', '2024-01-01'),
            ('fy25q3-ps-efficiency-model-02.xlsx', 'Role catalog reference', '2024-01-01')
        ]

        headers = ['Source File', 'Description', 'Timestamp']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, self.formats['header'])
        row += 1

        for source, desc, timestamp in sources:
            worksheet.write(row, 0, source)
            worksheet.write(row, 1, desc)
            worksheet.write(row, 2, timestamp)
            row += 1

        # Metadata
        row += 1
        worksheet.write(row, 0, 'Export Metadata', self.formats['subtitle'])
        row += 1

        metadata = [
            ('Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('Application', 'N2S Delivery Estimator'),
            ('Version', 'v0.12.1'),
            ('Format', 'Excel XLSX')
        ]

        for key, value in metadata:
            worksheet.write(row, 0, key, self.formats['bold'])
            worksheet.write(row, 1, value)
            row += 1

        self._autofit_columns(worksheet, 3)

    def _autofit_columns(self, worksheet: Worksheet, num_columns: int) -> None:
        """Auto-fit column widths and apply filters."""
        # Set reasonable column widths
        for col in range(num_columns):
            worksheet.set_column(col, col, 15)

        # Apply autofilter to first data table
        if num_columns > 0:
            worksheet.autofilter(2, 0, 2, num_columns - 1)

