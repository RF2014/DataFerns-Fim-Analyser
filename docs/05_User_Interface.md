# 5. User Interface (PyQt5)

## 5.1 Architecture
The user interface is entirely component-driven utilizing `PyQt5`. It acts strictly as an I/O gathering controller. No traffic mathematics or spreadsheet manipulation executes within the UI views.

## 5.2 Application State
The state matrix is tracked inside `models/state.py` (`AppState`). Once a `.fim` binary is uploaded and decoded by the Parser, the statistical preview is pushed into `AppState.current_df`. The UI views simply "react" to the data availability by rendering DataTables or unlocking the "Generate Report" buttons.

## 5.3 Context Gathering (`MetadataPanel`)
Binary sensory reports inherently lack contextual identifiers (Street name, Zone IDs, Specific survey dates, local Speed Limits).
The `MetadataPanel` (`src/ui/metadata_panel.py`) presents a modal dialog intercepting the final execution flow. It captures:
*   Physical metadata (`Location`, `Sect`, `Ind`, `Count`)
*   Environmental variables (`VMAX` limit)
*   Temporal constraints (3 unique `Custom P-Periods`)
These variables are packaged into a Python `Dict` structure and piped directly to the mathematical and reporting layers as contextual rules or literal sting replacements for the report's footers and headers.
