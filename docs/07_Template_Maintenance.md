# 7. Template Maintenance Guidelines

## 7.1 Overview
The file `dcr_python/src/report-template.xlsx` represents the visual identity of the entire reporting mechanism. Modifying this template requires extremely strict adherence to internal constraints, otherwise, the reporting engine will crash or visually corrupt the output.

## 7.2 Strict Sheet Naming
The Python engine (`ReportService`) requires the template to have exactly these four sheets intact, named identically:
*   `Synthese_des_donnees`
*   `Sens 1`
*   `Sens 2`
*   `Sens 3`
*(Adding spaces like "Sens 1 " will trigger generation failure).*

## 7.3 Managing External Links & Security Warnings
Legacy templates triggered major Microsoft Excel security warnings because their Data Validations and "Defined Names" referenced missing external network drives (e.g. `[ExternalFile.xlsx]Sheet1!A1`). 
The current valid template dropped in `/src` has had its XML completely purged of these phantom connections using deep-interop Windows tools (see `tmp/master_excel_fix.py` execution history). 
*   **WARNING**: Do NOT copy-paste charts or cells from older legacy spreadsheets into the new master template. This action will invisibly carry over legacy phantom links and instantly resuscitate the security warnings. 

## 7.4 The Mathematical Injection Grid
Currently, the Python engine leverages absolute cell references relative to pre-formatted template structures. 
*   **A daily structural block is 56 rows tall.**
*   The first block begins firmly at `Row 58` resulting in a footer landing precisely on `Row 113`. 
*   The template currently houses **31 identical pre-formatted blocks** stretching continuously downwards.
*   **Rule of Thumb**: You may freely alter colors, fonts, or translations of the textual headers, but shifting a table 3 rows lower will misalign the data injection pipeline.

## 7.5 Expanding Template Length (Advanced)
If a client requires surveys spanning continuously over 31 days (e.g., 60 days duration), you cannot attempt to manually drag and copy blocks inside Excel without risking page-break regressions.
In such an event, you must recreate the automated native COM copy script that leverages `win32com.client` inside Python to invoke Excel secretly and perform 60 strictly aligned copy-paste maneuvers, capturing cell boundaries and row-hiding parameters seamlessly.
