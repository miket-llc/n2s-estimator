# N2S Estimator - Directory Tree

```
n2s-estimator/
├── src/
│   └── n2s_estimator/                    # Main application package
│       ├── __init__.py                   # Package initialization with version
│       ├── engine/                       # Core calculation engines
│       │   ├── __init__.py              # Engine package initialization
│       │   ├── datatypes.py             # Pydantic data models and validation
│       │   ├── loader.py                # Excel workbook configuration loader
│       │   ├── estimator.py             # Base N2S estimation engine
│       │   ├── pricing.py               # Role expansion and cost calculation
│       │   ├── addons.py                # Add-on packages (Integrations/Reports)
│       │   ├── orchestrator.py          # Main coordination and public API
│       │   └── validators.py            # Configuration validation and drift detection
│       ├── ui/                          # Streamlit user interface
│       │   ├── __init__.py              # UI package initialization
│       │   └── main.py                  # Main Streamlit application entry point
│       ├── export/                      # Excel export functionality
│       │   ├── __init__.py              # Export package initialization
│       │   └── excel.py                 # Styled Excel workbook generation
│       └── data/                        # Configuration data and utilities
│           ├── create_workbook.py       # Workbook generation script
│           └── n2s_estimator.xlsx       # Master configuration workbook
├── tests/                               # Test suite
│   ├── __init__.py                      # Test package initialization
│   ├── test_loaders.py                  # Configuration loading and validation tests
│   ├── test_math.py                     # Deterministic calculation verification
│   └── test_e2e.py                      # End-to-end integration tests
├── README.md                            # User guide and quick start
├── ARCHITECTURE.md                      # Technical architecture documentation
├── QA_SUMMARY.md                        # Quality assurance audit and certification
├── TREE.md                              # This directory structure documentation
├── CHANGELOG.md                         # Version history and changes
├── requirements.txt                     # Python dependencies
├── pyproject.toml                       # Project configuration and build settings
├── .ruff.toml                          # Ruff linter configuration
├── mypy.ini                            # MyPy type checker configuration
├── .pre-commit-config.yaml             # Pre-commit hooks configuration
├── .gitignore                          # Git ignore patterns
└── Makefile                            # Development automation commands
```

## File Purposes

### Core Application (`src/n2s_estimator/`)

**Engine Components:**
- `datatypes.py` - Type-safe data models with business rule validation
- `loader.py` - Robust Excel parsing with error handling and normalization
- `estimator.py` - Deterministic Base N2S calculation pipeline
- `pricing.py` - Role hour expansion and multi-locale cost calculation
- `addons.py` - Independent add-on package estimation (Integrations/Reports)
- `orchestrator.py` - Main API coordinating all estimation components
- `validators.py` - Configuration validation and methodology drift warnings

**User Interface:**
- `main.py` - Complete Streamlit app with sidebar controls, tabs, and charts

**Export:**
- `excel.py` - Board-ready Excel reports with styling and conditional formatting

**Data:**
- `n2s_estimator.xlsx` - Authoritative configuration workbook with all business rules
- `create_workbook.py` - Script to generate/update the configuration workbook

### Test Suite (`tests/`)

**Test Categories:**
- `test_loaders.py` - Configuration loading, validation, and data integrity
- `test_math.py` - Deterministic calculations with expected value verification
- `test_e2e.py` - Complete user scenarios and integration workflows

### Configuration Files

**Quality Gates:**
- `.ruff.toml` - Code linting rules and style enforcement
- `mypy.ini` - Static type checking configuration
- `.pre-commit-config.yaml` - Automated code quality checks
- `Makefile` - Development workflow automation

**Project Setup:**
- `requirements.txt` - Runtime and development dependencies
- `pyproject.toml` - Modern Python project configuration
- `.gitignore` - Version control exclusions

### Documentation

**User Documentation:**
- `README.md` - Installation, usage, and troubleshooting guide
- `ARCHITECTURE.md` - Technical design and data flow documentation
- `TREE.md` - This file - directory structure and file purposes

**Quality Assurance:**
- `QA_SUMMARY.md` - Compliance audit with test results and certification
- `CHANGELOG.md` - Version history and feature evolution

## Key Design Patterns

**Package Organization:**
- Clean separation between data, business logic, UI, and export
- Self-contained modules with clear interfaces
- Minimal cross-dependencies between components

**Configuration Management:**
- Single source of truth in Excel workbook
- Validation at multiple layers (input, loading, runtime)
- Graceful degradation for missing or invalid data

**Testing Strategy:**
- Unit tests for individual components
- Integration tests for complete workflows
- Deterministic verification of expected results

**Development Workflow:**
- Automated quality gates with make commands
- Pre-commit hooks for code consistency
- Comprehensive linting and type checking

