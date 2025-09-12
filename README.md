# 📊 N2S Delivery Estimator

A professional Streamlit application for estimating N2S (Banner/Colleague) delivery projects with configurable parameters, add-on packages, and Excel export capabilities.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-50%2B%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-70%25-yellowgreen)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.49%2B-red)
![Version](https://img.shields.io/badge/version-0.10.0-blue)

**🌐 Live Application**: Currently running at `http://localhost:8501` (when started locally)

## Overview

The N2S Delivery Estimator provides:

- **Base N2S Package Estimation**: Core delivery hours based on size, type, and product
- **Sprint 0 Uplift**: Configurable percentage boost to Sprint 0 stage (defaults: Net New 2%, Modernization 1%)
- **Add-on Packages**: Independent pricing for Integrations, Reports, and Degree Works
- **Stage Summary Toggle**: View base-only or all-packages stage breakdowns
- **Degree Works Cap**: Size-based guardrails to prevent runaway estimates (Small 300h, Medium 400h, Large 500h, Very Large 600h)
- **Multi-locale Support**: Rate cards for US, Canada, UK, EU, ANZ, and MENA
- **Delivery Split Options**: Onshore/Offshore/Partner mix configurations
- **Excel Export**: Board-ready reports with styling and conditional formatting

## Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)

### Installation

```bash
# Clone and navigate to the repository
cd n2s-estimator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
streamlit run src/n2s_estimator/ui/main.py
```

The application will open in your browser at `http://localhost:8501`.

## 🆕 New Features (v0.10.0)

### Sprint 0 Uplift
- **Configurable Boost**: Add percentage of total hours to Sprint 0 stage
- **Smart Defaults**: Net New projects get 2% uplift, Modernization gets 1%
- **Proportional Adjustment**: Uplift is subtracted from Plan and Configure stages
- **Weight Preservation**: Stage weights always sum to 100%

### Stage Summary Toggle
- **All Packages View**: Shows Integrations, Reports, and Degree Works stages
- **Base-Only View**: Traditional view with just Base N2S stages
- **Real-time Switching**: Toggle between views without re-estimation
- **Clear Labeling**: Visual indicators show which view is active

### Degree Works Cap
- **Size-Based Guardrails**: Automatic caps by school size
  - Small: 300 hours
  - Medium: 400 hours  
  - Large: 500 hours
  - Very Large: 600 hours
- **Smart Clamping**: PVEs are reduced when total exceeds cap
- **Setup Preservation**: Setup hours are never reduced
- **Override Capability**: Custom cap values supported
- **Visual Feedback**: Clear indication when cap is applied

### Enhanced UI Controls
- **Advanced Settings**: Sprint 0 uplift slider in collapsible section
- **Degree Works Controls**: Cap enable/disable and custom values
- **Help Integration**: Contextual help text for all new features
- **Validation Warnings**: User-friendly feedback for edge cases

## Configuration

### Workbook Configuration

The application uses `src/n2s_estimator/data/n2s_estimator.xlsx` for all configuration data:

- **Stage Weights**: Allocation percentages across project phases
- **Role Mix**: Role distribution per stage
- **Rates**: Per-role rates by locale and delivery type
- **Add-on Catalog**: Unit hours and role distributions for add-ons
- **Product Role Map**: Role enablement by product (Banner/Colleague)

### Key Parameters

**Core Parameters:**
- Product: Banner or Colleague
- Delivery Type: Net New (1.0x) or Modernization (0.9x)
- Size: Small (0.85x), Medium (1.0x), Large (1.25x), Very Large (1.5x)
- Locale: US, Canada, UK, EU, ANZ, MENA

**Add-on Packages:**
- Integrations: Simple (80h), Standard (160h), Complex (320h)
- Reports: Simple (24h), Standard (72h), Complex (160h)

### Default Assumptions

- Base N2S: 6,700 hours
- Integrations: 30 items (60% Simple, 30% Standard, 10% Complex)
- Reports: 40 items (50% Simple, 35% Standard, 15% Complex)
- Global Delivery Split: 70% Onshore, 20% Offshore, 10% Partner

## Features

### Scenario Management

- **Save Scenario**: Download current parameters as JSON
- **Load Scenario**: Upload previously saved scenario
- **Parameter Persistence**: Settings maintained during session

### Excel Export

Generated reports include:
- Summary with KPIs and charts
- Stage × Role breakdowns
- Add-on package details
- Rates and delivery mixes
- Assumptions and inputs
- Data sources and metadata

### Validation

- Stage weights sum to 1.0
- Role mix percentages sum to 1.0 per stage
- Delivery splits sum to 1.0
- Add-on tier mixes sum to 1.0
- Methodology drift warnings (>10% deviation)

## Development

### Quality Gates

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make typecheck

# Security scan
make security

# Run tests
make test

# Coverage report
make coverage

# Run all checks
make all
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_loaders.py    # Configuration loading
pytest tests/test_math.py       # Deterministic calculations
pytest tests/test_e2e.py        # End-to-end scenarios

# With coverage
pytest --cov=src/n2s_estimator --cov-report=term-missing
```

### Project Structure

```
src/n2s_estimator/
├── engine/          # Core calculation engines
│   ├── datatypes.py    # Pydantic data models
│   ├── loader.py       # Configuration loading
│   ├── estimator.py    # Base N2S estimation
│   ├── pricing.py      # Role expansion & pricing
│   ├── addons.py       # Add-on package calculations
│   ├── orchestrator.py # Main coordination
│   └── validators.py   # Data validation
├── ui/              # Streamlit user interface
│   └── main.py         # Main application
├── export/          # Excel export functionality
│   └── excel.py        # Styled workbook generation
└── data/            # Configuration data
    └── n2s_estimator.xlsx
```

## Expected Results

### Default Scenario (Banner, Net New, Medium, US)

**Base N2S Package (~6,700 hours):**
- Total Hours: 6,700
- Presales Hours: 150.75 (Start: 100.5, Prepare: 50.25)
- Delivery Hours: 6,549.25

**Stage Breakdown:**
- Start: 167.5h, Prepare: 167.5h, Sprint 0: 402h
- Plan: 670h, Configure: 2,278h, Test: 1,340h
- Deploy: 670h, Go-Live: 402h, Post Go-Live: 603h

**Add-ons (when enabled):**
- Integrations (30 items, default mix): ~3,840 hours
- Reports (40 items, default mix): ~2,448 hours

## Changelog

### v0.10.0 (2024-12-19)
- **Sprint 0 Uplift**: Configurable percentage boost to Sprint 0 stage
- **Stage Summary Toggle**: Switch between base-only and all-packages views
- **Degree Works Cap**: Size-based guardrails to prevent runaway estimates
- **Enhanced UI**: Advanced settings panel with contextual help
- **Comprehensive Testing**: 50+ test cases covering all new features

### v0.9.0 (2024-01-20)
- Initial release with Base N2S estimation
- Integrations and Reports add-on packages
- Multi-locale support and Excel export
- Complete test suite and documentation

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and dependencies installed
2. **Workbook Loading**: Verify `n2s_estimator.xlsx` exists in `src/n2s_estimator/data/`
3. **Validation Warnings**: Check that percentages sum to 1.0 in configuration sheets

### Performance

- Configuration loading: ~0.5s
- Estimation calculation: <0.1s
- Excel export: ~2-3s

### Support

For issues or feature requests, check the validation warnings in the application sidebar and ensure all configuration data sums correctly.

## License

Internal use only. See project documentation for details.

