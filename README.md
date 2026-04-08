# FIM Analyzer - Project Overview

This repository contains the Python-based FIM Analyzer GUI and supporting tools. It is structured around the main application in `dcr_python/` plus standalone verification and debugging scripts at the root.

## Quick Start

### Prerequisites
- Python 3.11+ recommended

### Install
```bash
cd dcr_python
pip install -r requirements.txt
```

### Run the GUI
```bash
python src/main.py
```

## Repository Structure

```
GUI/
├── dcr_python/                # Main application (source, tests, docs)
│   ├── src/                   # Application code (core, UI, models, utils)
│   ├── tests/                 # Unit tests
│   ├── requirements.txt       # Python dependencies
│   ├── setup.py               # Packaging config
│   └── README.md              # App-specific documentation
├── debug_page4.py             # Debug helpers for page 4 logic
├── fix_page4_logic.py         # Patch/validation scripts for page 4
├── fix_vehicle_class.py       # Vehicle class fixes and verification
├── test_*.py                  # Standalone test and validation scripts
├── test_suspicious_data.fim   # Sample input file for debugging
└── PAGE4_FIX_VERIFICATION.txt # Notes/verification results
```

## Which Files Matter for Development

- **Main app**: `dcr_python/src/` (core logic + UI)
- **Dependencies**: `dcr_python/requirements.txt`
- **Tests**: `dcr_python/tests/` and root `test_*.py`
- **Docs**: `dcr_python/README.md` and `dcr_python/*_SUMMARY.md`

## Running Tests (Optional)

From `dcr_python/`:
```bash
python -m pytest
```

## Notes

- Build artifacts and virtual environments are intentionally excluded from the repo. If needed, rebuild with your local environment.
