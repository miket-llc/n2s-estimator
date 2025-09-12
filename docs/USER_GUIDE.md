# N2S Delivery Estimator - User Guide

## Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Core Parameters](#core-parameters)
4. [Add-On Packages](#add-on-packages)
5. [Advanced Settings](#advanced-settings)
6. [Rates & Pricing](#rates--pricing)
7. [Scenario Management](#scenario-management)
8. [Results & Export](#results--export)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Overview

The N2S Delivery Estimator is a comprehensive tool for estimating delivery hours and costs for N2S (Next to Self-Service) implementations. It supports both Banner and Colleague products with different delivery types (Modernization vs Net New) and provides detailed breakdowns by phase, stage, activity, and role.

### Key Features
- **Product-Specific Estimation**: Banner vs Colleague with different multipliers
- **Delivery Type Support**: Modernization and Net New implementations
- **Add-On Packages**: Integrations, Reports, and Degree Works
- **Scenario Management**: Save and load different estimation scenarios
- **Rate Customization**: Per-role and per-locale rate overrides
- **Excel Export**: Board-ready deliverables

---

## Getting Started

### First Time Setup
1. **Launch the Application**: Navigate to `http://localhost:8501`
2. **Review Default Settings**: The application loads with sensible defaults
3. **Configure Core Parameters**: Start with Product, Delivery Type, and School Size
4. **Run Initial Estimation**: Click "Generate Estimation" to see baseline results

### Understanding the Interface
- **Left Sidebar**: Input parameters and controls
- **Main Area**: Results display and detailed breakdowns
- **Tabs**: Organized sections for different aspects of the estimation

---

## Core Parameters

### Product Selection
Choose between **Banner** and **Colleague**:

**Banner**:
- Full feature set available
- Standard multipliers (1.0x Net New, 0.9x Modernization)
- All add-on packages supported

**Colleague**:
- Reduced feature set (Technical Architect and Integration Lead disabled)
- Lower multipliers (0.85x Net New, 0.75x Modernization)
- Limited add-on support (0.9x Integrations/Reports, 0.0x Degree Works)

### Delivery Type
- **Net New**: Greenfield implementation with full feature set
- **Modernization**: Upgrading existing system with reduced scope

### School Size
- **Small**: <5,000 students
- **Medium**: 5,000-15,000 students  
- **Large**: 15,000-30,000 students
- **Very Large**: >30,000 students

### Locale/Region
Select the geographic region for rate calculations:
- **US Onshore**
- **US Offshore**
- **India**
- **Philippines**
- **Mexico**
- **Brazil**

---

## Add-On Packages

### Integrations Package
Tiered approach based on complexity:

**Simple Integrations** (Default: 100%)
- Basic data feeds
- Standard API connections
- Simple file transfers

**Standard Integrations** (Default: 0%)
- Custom API development
- Complex data transformations
- Multi-system integrations

**Complex Integrations** (Default: 0%)
- Enterprise service bus
- Real-time data synchronization
- Custom middleware development

### Reports Package
Tiered approach based on sophistication:

**Simple Reports** (Default: 100%)
- Standard operational reports
- Basic dashboards
- Pre-built templates

**Standard Reports** (Default: 0%)
- Custom report development
- Advanced analytics
- Interactive dashboards

**Complex Reports** (Default: 0%)
- Predictive analytics
- Machine learning integration
- Real-time reporting systems

### Degree Works Package
Comprehensive academic planning system:

**Setup Configuration**:
- Enable/disable Degree Works inclusion
- Include setup hours in estimation
- Use PVE calculator for complexity assessment

**Academic Structure**:
- **Majors**: Number of degree programs
- **Minors**: Number of minor programs
- **Certificates**: Number of certificate programs
- **Concentrations**: Number of concentration areas
- **Catalog Years**: Number of active catalog years

**PVE (Program Verification Engine) Configuration**:
- **PVE Count**: Number of verification rules
- **Complexity Distribution**:
  - Simple: Basic rule validation (default: 60%)
  - Standard: Multi-condition rules (default: 30%)
  - Complex: Cross-program validation (default: 10%)

**Cap Management**:
- Enable/disable hour caps
- Override default cap values
- Size-based cap limits (Small: 300h, Medium: 400h, Large: 500h, Very Large: 600h)

---

## Advanced Settings

### Sprint 0 Uplift
Configurable percentage added to Sprint 0 stage:
- **Net New**: +2% (default)
- **Modernization**: +1% (default)
- Automatically reduces Plan and Configure stages to maintain 100% total

### Maturity Factor
Adjustment based on organizational maturity:
- **Low Maturity**: 1.2x multiplier
- **Medium Maturity**: 1.0x multiplier (default)
- **High Maturity**: 0.8x multiplier

### Stage Summary Toggle
- **Base Only**: Shows only core N2S estimation
- **All Packages**: Includes Integrations, Reports, and Degree Works

---

## Rates & Pricing

### Default Rate Cards
Pre-configured rates by locale and role:
- **US Onshore**: $150-250/hour
- **US Offshore**: $100-150/hour
- **India**: $25-50/hour
- **Philippines**: $30-55/hour
- **Mexico**: $40-70/hour
- **Brazil**: $45-75/hour

### Rate Overrides
Customize rates for specific roles and locales:
1. **Add Override**: Click "Add Rate Override"
2. **Select Role**: Choose from available roles
3. **Select Locale**: Choose geographic region
4. **Set Rates**: Enter onshore, offshore, and partner rates
5. **Apply Changes**: Click "Apply Rate Overrides"

### Delivery Mix Configuration
Control resource allocation:

**Global Mix** (applies to all roles):
- Onshore percentage
- Offshore percentage  
- Partner percentage
- Must sum to 100%

**Per-Role Mix** (role-specific overrides):
- Override global mix for specific roles
- Useful for specialized roles requiring specific locations

---

## Scenario Management

### Saving Scenarios
1. **Configure Parameters**: Set all desired inputs
2. **Apply Rate Overrides**: Customize pricing if needed
3. **Save Scenario**: Enter descriptive name and click "Save Scenario"
4. **Confirmation**: Success message confirms save

### Loading Scenarios
1. **Select Scenario**: Choose from dropdown list
2. **Load Scenario**: Click "Load Scenario"
3. **Parameter Update**: All inputs update automatically
4. **Rate Application**: Custom rates applied if saved

### Scenario Data Includes
- All core parameters (Product, Delivery Type, Size, Locale)
- Add-on package configurations
- Degree Works settings (all 20+ parameters)
- Rate overrides and delivery mix settings
- Advanced settings (Sprint 0 uplift, maturity factor)

### Backward Compatibility
- Older scenarios load gracefully
- Missing parameters use sensible defaults
- No data loss when upgrading

---

## Results & Export

### Estimation Results
**Summary View**:
- Total hours and costs
- Presales vs Delivery split
- Add-on package totals
- Key metrics and ratios

**Detailed Breakdowns**:
- **By Stage**: Hours and costs per implementation stage
- **By Role**: Resource allocation by role type
- **By Activity**: Detailed activity-level breakdown
- **By Package**: Separate totals for each add-on

### Excel Export
**Comprehensive Workbook**:
- Executive summary sheet
- Detailed breakdowns by stage, role, and activity
- Add-on package details
- Rate and pricing information
- Scenario metadata

**Export Process**:
1. **Generate Estimation**: Ensure results are current
2. **Download Excel**: Click "Download Excel Report"
3. **File Naming**: Automatic naming with timestamp
4. **Board Ready**: Formatted for executive presentation

---

## Troubleshooting

### Common Issues

**"Estimation failed" Error**:
- Check that all required parameters are set
- Verify rate overrides sum to 100%
- Ensure valid numeric inputs

**Scenario Loading Issues**:
- Check scenario file format (JSON)
- Verify all required fields present
- Try loading a different scenario

**Rate Override Problems**:
- Ensure percentages sum to 100%
- Check for valid numeric values
- Verify role and locale selections

**Excel Export Issues**:
- Ensure estimation has been generated
- Check browser download permissions
- Try refreshing the page

### Validation Warnings
The application shows warnings for:
- Disabled packages (e.g., Degree Works for Colleague)
- Invalid rate configurations
- Missing required parameters
- Configuration conflicts

### Performance Tips
- Use scenario management for repeated configurations
- Save rate overrides as scenarios for reuse
- Export results regularly for backup
- Clear browser cache if experiencing issues

---

## Best Practices

### Estimation Workflow
1. **Start Simple**: Begin with core parameters only
2. **Add Complexity**: Gradually add add-on packages
3. **Validate Results**: Check totals and breakdowns
4. **Save Scenarios**: Create named scenarios for different cases
5. **Export Results**: Generate Excel reports for stakeholders

### Scenario Management
- **Descriptive Names**: Use clear, meaningful scenario names
- **Version Control**: Save multiple versions for comparison
- **Documentation**: Add notes about scenario purpose
- **Regular Backups**: Export scenarios periodically

### Rate Customization
- **Baseline First**: Start with default rates
- **Incremental Changes**: Apply overrides gradually
- **Documentation**: Note reasons for rate changes
- **Validation**: Always verify percentage totals

### Quality Assurance
- **Cross-Check**: Compare with previous estimates
- **Sensitivity Analysis**: Test different parameter combinations
- **Stakeholder Review**: Validate assumptions with business users
- **Documentation**: Maintain estimation rationale

### Collaboration
- **Shared Scenarios**: Use consistent naming conventions
- **Rate Standards**: Establish organization-wide rate cards
- **Process Documentation**: Document estimation methodology
- **Training**: Ensure team members understand the tool

---

## Support and Resources

### Application Information
- **Version**: 0.12.0
- **Last Updated**: December 2024
- **Repository**: https://github.com/miket-llc/n2s-estimator

### Getting Help
- **Configuration Warnings**: Check the warnings section in the UI
- **Validation Errors**: Review error messages for guidance
- **Scenario Issues**: Try loading default scenarios
- **Rate Problems**: Reset to default rates and reconfigure

### Feature Requests
For new features or improvements, please:
1. Document the use case
2. Provide example scenarios
3. Include expected behavior
4. Submit through the project repository

---

*This user guide covers the N2S Delivery Estimator v0.12.0. For the most current information, refer to the application's Help tab and inline documentation.*
