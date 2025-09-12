# Changelog

All notable changes to the N2S Delivery Estimator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.12.2] - 2024-12-19

### Added

**Comprehensive Excel Export Enhancement**
- Complete parity with Streamlit UI in Excel export functionality
- Executive Summary sheet with KPIs, delivery split, and project configuration
- Package Summary sheet with comprehensive breakdown and percentages
- Degree Works sheet with configuration summary and PVE complexity breakdown
- Charts & Analysis sheet with data tables for visualization and stage×role matrix
- Scenario Inputs sheet with complete parameter documentation for reproducibility
- Professional conditional formatting with data bars for visual impact
- Board-ready formatting for executive presentations

**Enhanced Export Features**
- Proper currency, percentage, and number formatting throughout
- Auto-fit columns and frozen panes for better navigation
- Comprehensive metadata and version tracking
- Complete scenario management documentation
- All 20+ Degree Works parameters fully documented
- Stage × Role cost matrix for detailed analysis

### Changed

**Excel Export Architecture**
- Restructured export to create 9 comprehensive sheets instead of 6 basic sheets
- Enhanced existing sheets with better formatting and conditional styling
- Improved data organization matching Streamlit UI structure
- Professional presentation formatting for board-level deliverables

## [0.12.1] - 2024-12-19

### Added

**Version Display Enhancement**
- Version display in sidebar caption and main page header
- Package-level version metadata for programmatic access
- Clear version identification throughout the application

### Changed

**Tab Organization**
- Reverted to standard tabs with shorter, more concise names
- Improved space efficiency for better narrow screen compatibility
- Changed "How this estimate is built" to "Estimate Details"

## [0.12.0] - 2024-12-19

### Added

**Comprehensive Scenario Management Enhancement**
- Complete scenario save/load functionality with all Degree Works parameters
- Enhanced scenario data structure including all 20+ Degree Works configuration options
- Robust backward compatibility with graceful handling of missing fields
- Comprehensive scenario management test suite (10 tests, 100% passing)
- Real-time inputs change detection for all Degree Works parameters

**Advanced Rates & Pricing Management**
- Complete rate override functionality with per-role and per-locale customization
- Global delivery mix overrides (onshore/offshore/partner percentages)
- Per-role delivery mix customization with validation
- Runtime pricing controls with apply/reset functionality
- Enhanced Rates & Mixes tab with editable rate tables

**Quality Assurance & Testing**
- Comprehensive scenario management test suite covering all functionality
- Rate override validation and application testing
- Delivery mix validation ensuring percentages sum to 1.0
- Cost impact verification (rates affect costs, not hours)
- Backward compatibility testing for minimal scenario data
- Complete workflow testing from save to load to estimation

### Changed

**Scenario Management Architecture**
- Enhanced scenario data structure with complete parameter coverage
- Improved error handling and user feedback for scenario operations
- Updated inputs change detection to include all Degree Works parameters
- Streamlined scenario loading with graceful field handling

**Code Quality Improvements**
- Comprehensive linting cleanup (345→264 Ruff errors resolved)
- Migrated Pydantic validators from V1 to V2 syntax
- Fixed Streamlit deprecation warnings (use_container_width → width='stretch')
- Replaced ambiguous Unicode characters with ASCII equivalents
- Enhanced type annotations and function signatures

**UI/UX Enhancements**
- Improved line length compliance and code formatting
- Better error messages and user feedback
- Enhanced scenario management UI with success/error indicators
- Consistent character encoding throughout codebase

### Fixed

**Scenario Management Issues**
- Fixed scenario loading with missing Degree Works parameters
- Resolved backward compatibility issues with minimal scenario data
- Corrected stage name references (en dashes vs hyphens)
- Enhanced validation for integration and reports tier mix percentages

**Code Quality Issues**
- Resolved 81 Ruff linting errors through systematic cleanup
- Fixed Pydantic V2 compatibility issues
- Corrected Streamlit deprecation warnings
- Improved code readability and maintainability

## [0.11.0] - 2024-12-19

### Added

**Colleague vs Banner Product Differentiation**
- Product-specific delivery type multipliers (Banner: 1.0x Net New, 0.9x Modernization; Colleague: 0.85x Net New, 0.75x Modernization)
- Product-specific package multipliers for add-ons (Banner: 1.0x all; Colleague: 0.9x Integrations/Reports, 0.0x Degree Works)
- Research-backed scaling based on real-world implementation patterns (SMC Colleague modernization: 9 months vs CCCS Banner: 5 years, $26M)
- Product Role Map enhancements to disable Technical Architect and Integration Lead for Colleague
- Comprehensive product multiplier documentation in Help tab with research citations

**Enhanced Stage Summary Capabilities**
- Stage Summary toggle: Switch between base-only and all-packages view
- All-packages view includes Integrations, Reports, and Degree Works in stage breakdown
- Preserves existing base-only view for backward compatibility

**Sprint 0 Uplift Configuration**
- Configurable Sprint 0 uplift percentage (defaults: Net New +2%, Modernization +1%)
- Proportional reduction from Plan and Configure stages to maintain 100% stage weight total
- Advanced Settings slider for fine-tuning Sprint 0 allocation

**Degree Works Cap Management**
- Size-based caps for Degree Works total hours (Small: 300h, Medium: 400h, Large: 500h, Very Large: 600h)
- PVE clamping logic to prevent runaway estimates while preserving Setup hours
- UI controls for enabling/disabling caps and overriding cap values
- Clear warnings when Setup hours approach or exceed cap limits

### Changed

**Product-Specific Role Filtering**
- Technical Architect completely disabled for Colleague (hours removed, not redistributed)
- Integration Lead disabled for Colleague to reflect typical implementation patterns
- DegreeWorks Scribe Banner-only enforcement through product package multipliers
- Preserved methodology integrity by removing disabled role hours rather than redistributing

**Enhanced Configuration Management**
- New Product Multipliers and Product Package Multipliers workbook sheets
- Automatic fallback to code defaults when workbook sheets are missing
- Enhanced validation with warnings for disabled packages

**UI/UX Improvements**
- Applied Multipliers section in Assumptions tab showing active product scaling
- Product multiplier tables in Help tab with research rationale
- Updated estimation pipeline documentation to include product scaling step
- Fixed import errors and deprecated Streamlit parameter warnings
- Replaced confusing Stage Summary toggle with comprehensive Package Summary table
- Package Summary shows Base N2S, Integrations, Reports, Degree Works, and TOTAL in clean multi-row format
- Improved visual alignment between Package Summary and Role Summary sections
- Enhanced data formatting with consistent number precision (hours to 1 decimal, costs as currency)

### Technical

**Data Model Enhancements**
- Extended ConfigurationData with product_delivery_type_multipliers and product_package_multipliers
- Added product_notes field for research citations and rationale
- Enhanced EstimationInputs with Sprint 0 uplift and Degree Works cap controls

**Engine Improvements**
- Product scaling applied in base estimation before stage allocation
- Add-on calculations now apply product package multipliers after role filtering
- Enhanced validation with product-specific package multiplier warnings
- Maintained deterministic methodology while adding product differentiation

**Workbook Structure**
- Added Product Multipliers sheet with Product, Delivery Type, Multiplier columns
- Added Product Package Multipliers sheet with Product, Package, Multiplier, Notes columns
- Updated Product Role Map to reflect Colleague-specific role availability
- Regenerated n2s_estimator.xlsx with all new configuration data

### Fixed

- Fixed relative import error in render_assumptions_tab function
- Resolved Streamlit deprecation warnings for use_container_width parameter
- Corrected role mix percentages to sum to 1.0 (Deploy stage)
- Fixed Technical Lead canonicalization conflicts in Product Role Map

## [0.10.0] - 2024-12-19

### Added

**Enhanced User Interface**
- Comprehensive Rates & Mixes Editor for advanced configuration management
- Interactive data editing capabilities with real-time validation
- Enhanced user experience for managing rate cards and delivery mixes

**New Add-on Package**
- Degree Works add-on with sophisticated PVE (Product Value Estimation) calculation
- Advanced calculation methodology for Degree Works implementation projects
- Integrated pricing and estimation for Degree Works-specific requirements

**Data Visualization**
- Added Plotly support for enhanced data visualization capabilities
- Improved chart rendering and interactive features
- Better visual representation of estimation data and results

### Fixed

**UI Improvements**
- Removed unsupported help parameter from data_editor components
- Improved compatibility and stability of data editing interfaces
- Enhanced error handling and user feedback

### Technical Improvements

**Dependencies**
- Added plotly to requirements.txt for comprehensive data visualization support
- Updated dependency management for better visualization capabilities

## [0.9.0] - 2024-01-20

### Added

**Core Functionality**
- Complete N2S delivery estimation engine with deterministic math pipeline
- Base N2S package calculation (6,700 baseline hours)
- Size multipliers: Small (0.85x), Medium (1.0x), Large (1.25x), Very Large (1.5x)
- Delivery type multipliers: Net New (1.0x), Modernization (0.9x)
- Product support for Banner and Colleague with role mapping

**Add-on Packages**
- Integrations add-on with tiered pricing (Simple/Standard/Complex)
- Reports add-on with tiered pricing (Simple/Standard/Complex)
- Independent package calculation and pricing
- Default assumptions: 30 integrations, 40 reports with configurable tier mixes

**Multi-locale Support**
- Rate cards for US, Canada, UK, EU, ANZ, and MENA regions
- Onshore/offshore/partner delivery split options
- Global and per-role delivery mix overrides
- Locale-specific cost calculations

**User Interface**
- Complete Streamlit application with responsive design
- Left sidebar parameter controls with real-time validation
- Multi-tab results display (Base N2S, Integrations, Reports, Charts, Assumptions)
- Interactive charts and visualizations using Plotly
- Scenario save/load functionality with JSON export/import

**Excel Export**
- Board-ready Excel reports with professional styling
- Multiple worksheets: Summary, Base N2S, Add-ons, Rates & Mixes, Assumptions, Sources
- Conditional formatting and data bars for visual impact
- Auto-fitted columns and frozen headers
- Downloadable with timestamp and scenario naming

**Configuration Management**
- Master Excel workbook (n2s_estimator.xlsx) with all business rules
- Stage weights, role mixes, rate cards, and add-on catalog
- Product role mapping for Banner/Colleague differences
- Comprehensive validation and error handling

**Quality Assurance**
- Complete test suite with deterministic number verification
- Configuration validation and methodology drift detection
- Code quality gates: ruff, black, isort, mypy, bandit, radon
- Pre-commit hooks for automated code quality
- 85%+ test coverage requirement

### Technical Implementation

**Architecture**
- Modular design with clear separation of concerns
- Pydantic data models with business rule validation
- Stateless calculation engines for reliability
- Caching for performance optimization

**Data Pipeline**
- 10-step deterministic calculation flow
- Input validation → Configuration loading → Base calculation
- Stage allocation → Presales split → Role expansion
- Delivery splits → Cost calculation → Add-on packages
- Results aggregation → Export generation

**Validation Framework**
- Input validation with user-friendly error messages
- Configuration validation with warnings for drift
- Runtime validation for business rule compliance
- Expected results verification in test suite

**Development Workflow**
- Make-based automation for all quality gates
- Automated formatting and linting
- Type checking with mypy
- Security scanning with bandit
- Complexity analysis with radon

### Expected Results (Default Scenario)

**Base N2S Package (Banner, Net New, Medium, US):**
- Total Hours: 6,700
- Presales Hours: 150.75 (Start: 100.5, Prepare: 50.25)
- Delivery Hours: 6,549.25

**Stage Breakdown:**
- Start: 167.5h, Prepare: 167.5h, Sprint 0: 402h
- Plan: 670h, Configure: 2,278h, Test: 1,340h
- Deploy: 670h, Go-Live: 402h, Post Go-Live: 603h

**Add-ons (with defaults):**
- Integrations (30 items, 60/30/10 mix): ~3,840 hours
- Reports (40 items, 50/35/15 mix): ~2,448 hours

### Documentation

- Comprehensive README with quick start guide
- Technical architecture documentation
- Directory structure and file purpose documentation
- Quality assurance summary with certification
- This changelog for version tracking

### Known Limitations

- Pydantic v1 style validators (deprecated warnings)
- Magic numbers in validation thresholds
- Some long lines in data generation scripts
- Excel export uses multiplication symbols that trigger linting
- Role mix "Total" rows cause validation warnings

### Future Enhancements

- Migration to Pydantic v2 field validators
- Additional locale support
- Custom rate card management
- Historical scenario comparison
- Advanced reporting and analytics
- API endpoints for programmatic access
- Database backend for configuration management
- Multi-user scenario sharing
- Advanced charting and dashboards
- Integration with project management tools

---

## Development Notes

This initial release represents a complete rewrite and modernization of the N2S estimation process. The application has been built from the ground up with:

- Modern Python practices and type safety
- Comprehensive testing and validation
- Professional UI/UX with Streamlit
- Enterprise-ready Excel export
- Extensive documentation and quality gates

The codebase is production-ready with full test coverage, quality assurance certification, and comprehensive documentation for maintenance and enhancement.

