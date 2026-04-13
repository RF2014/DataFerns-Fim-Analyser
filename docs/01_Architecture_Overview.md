# 1. Architecture Overview & Project DNA

## 1.1 Project Objective
The **DataFerns Traffic Reporter (FIM Analyser)** is a modular, high-fidelity traffic data processing application. Its core objective is to ingest binary `.fim` traffic sensor files, perform complex speed, volume, and percentile calculations, and inject this processed demographic data directly into strict, predefined Microsoft Excel reporting templates (`report-template.xlsx`). 

The application was purposefully refactored to eliminate fragile Excel-native macro/formula dependencies (which caused recurring `#REF!` errors and security warnings) and replace them with a "Backend Python Engine → Static Excel Template" model.

## 1.2 Tech Stack
*   **Environment**: Python 3.12 (Isolated Virtual Environment)
*   **Data Processing**: `pandas`, `numpy`
*   **Excel Manipulation**: `openpyxl` (injection) & Windows COM automation (`pywin32` for template maintenance)
*   **GUI Framework**: `PyQt5`
*   **Distribution**: `PyInstaller` (Bundling), `Inno Setup` (Windows Installer)

## 1.3 Core Principles (Logic Isolation)
The application follows a strict Service-Oriented Architecture (SOA) separating the math from the UI and the file input/output routines:

### `dcr_python/src/core/` (The Engine)
*   **`fim_parser.py`**: The ingestion layer. Strictly reads hexadecimal/binary bytes from the FIM payload and outputs a structured pandas `DataFrame`. It implements the Fime0001, 3, and 4 protocol standards.
*   **`analytics.py`**: The mathematical core. It conducts all statistical aggregations (V15, V50, V85, TMJ, StdDev) agnostic of how the data will be presented.

### `dcr_python/src/services/` (The Workers)
*   **`report_service.py`**: The Excel orchestrator. It consumes the calculated DataFrames and maps them strictly to hardcoded spreadsheet coordinates (e.g., `A58`, `AC43`).

### `dcr_python/src/ui/` (The Interface)
*   **`fim_loader.py`**: Main application loop.
*   **`metadata_panel.py`**: Gathers all contextual variables (Location, Speed Limits, Sector/Index ID) that are missing from raw `.fim` binaries but required by the final report.

### `dcr_python/src/` (Assets)
*   **`report-template.xlsx`**: The master graphical layout. This is treated as a static visualization overlay, not a computational engine.
