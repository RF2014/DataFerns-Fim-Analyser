# 4. Reporting Engine & Excel Output

## 4.1 Overview
`services/report_service.py` is the application's bridge to the client. It takes the calculated mathematical outputs and surgically injects them into a pre-styled, static `report-template.xlsx` template to produce the final client delivery.

## 4.2 Structural Rules (The "Template Immutable Law")
The legacy system relied on fragile Excel-native formulas stretching across sheets, which regularly collapsed causing massive `#REF!` corruptions and Excel security triggers (Link Update Warnings).

**The Solution:** The logic was forcefully transferred out of Excel and into Python. 
1. `report-template.xlsx` is strictly treated as a "dumb" visual skin.
2. The template contains four strictly enforced canonical sheet names: `Synthese_des_donnees`, `Sens 1`, `Sens 2`, and `Sens 3`.
3. The engine uses `openpyxl.load_workbook(keep_links=False)` as a baseline defense against phantom macro execution or external file path triggers.

## 4.3 Safe Writing Protocol
Writing directly to formatted Excel templates poses crash risks when attempting to address "Merged Cells". 
*   `ReportService._safe_write(ws, r, c, val)` intercepts any write command. If cell `C10` is part of a merge block spanning `C10:E10`, `_safe_write` intelligently locates the "Anchor Point" (`C10`) of the block and applies the value payload there, bypassing `openpyxl` merge corruption errors.

## 4.4 Global Metadata Propagation
Placeholders (e.g., `{{LOCATION}}`, `{{VMAX}}`, `{{SURVEY_PERIOD}}`, `{{P1_START}}`) govern the textual descriptions in the report. 
Instead of relying on Excel formulas linking cell `A1` to cell `Z500`, `ReportService._global_metadata_propagation` performs a brute-force sweep of every string cell in the workbook. It performs raw text replacement, making every header and footer totally independent and crash-proof.

## 4.5 Dynamic Height Constraints
A standard traffic report may cover anywhere from 2 to 31 continuous survey days.
Instead of runtime "block cloning" (which breaks print layouts and alignments in openpyxl), the `report-template.xlsx` was expanded via a native Excel COM macro one time during development.
*   **The template holds exactly 31 daily blocks.**
*   `ReportService` evaluates the survey length `len(days)`. It writes payload data iteratively into the available blocks. 
*   For any trailing block that exceeds the study length, the Python engine triggers `ws.row_dimensions[row].hidden = True`, elegantly collapsing the redundant blocks out of existence so the printer never attempts to print blank pages.
