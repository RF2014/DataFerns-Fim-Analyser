# DCR 2000 - Traffic Data Analysis Application

A Python port of the VBA-based DCR (Débit, Congesion, Réduction) traffic analysis application, featuring a modern desktop GUI with data processing capabilities.

## Features

- **File Management**: Import FIM/DBL traffic files, export to IFX format
- **Data Processing**: Calculate traffic metrics (speed, flow, vehicle classification)
- **Report Generation**: Create various traffic analysis reports
- **Data Aggregation**: Combine multiple data sources
- **Visualizations**: Charts and statistical analysis
- **Desktop GUI**: PyQt5-based user interface

## Project Structure

```
dcr_python/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── core/                   # Core business logic
│   │   ├── __init__.py
│   │   ├── file_manager.py     # File I/O operations
│   │   ├── data_processor.py   # Data processing pipeline
│   │   ├── calculations.py     # Traffic calculations
│   │   └── reports.py          # Report generation
│   ├── ui/                     # User interface
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main application window
│   │   ├── dialogs.py          # Dialog windows
│   │   └── widgets.py          # Custom widgets
│   ├── utils/                  # Utility functions
│   │   ├── __init__.py
│   │   ├── constants.py        # Application constants
│   │   ├── validators.py       # Data validators
│   │   └── helpers.py          # Helper functions
│   └── models/                 # Data models
│       ├── __init__.py
│       └── traffic_data.py     # Traffic data models
├── tests/                      # Unit tests
├── requirements.txt            # Python dependencies
├── setup.py                    # Setup configuration
└── README.md                   # This file
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python src/main.py
```

Or after installation:
```bash
dcr-app
```

## Dependencies

- **PyQt5**: Desktop GUI framework
- **pandas**: Data manipulation and analysis
- **openpyxl**: Excel file operations
- **numpy**: Numerical computing
- **python-dateutil**: Date/time utilities
- **pytz**: Timezone support

## File Formats

- **FIM**: Raw traffic data input format
- **DBL**: DBL traffic data input format
- **IFX**: Processed traffic data output format

## Architecture

### Core Modules

- **File Manager**: Handles import/export of FIM, DBL, and IFX files
- **Data Processor**: Main processing pipeline for traffic data
- **Calculations**: Traffic metrics (flow, speed, vehicle classification)
- **Reports**: Generates various report formats

### UI Components

- Main Window: Application menu and central widget
- File Dialogs: Import/export file selection
- Data Input: User information entry (vehicle types, road types, etc.)
- Visualization: Charts and tables for traffic analysis

## Migration Notes

This application is a complete port of the original VBA application to Python. Key differences:

- **UI Framework**: VBA Excel dialogs → PyQt5 native dialogs
- **Data Processing**: Excel VBA → pandas DataFrames
- **File Handling**: VBA file I/O → Python file operations with openpyxl
- **Calculations**: Direct VBA conversion to Python with numpy support

## License

Copyright © SA 1997-2025
