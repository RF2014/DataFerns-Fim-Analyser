# 3. Analytics Engine

## 3.1 Overview
`core/analytics.py` houses all statistical computation logic. It receives the standardized `DataFrame` from the parsing layer and applies mathematical operations to derive the key performance indicators (KPIs) required by the client reports.

## 3.2 Core Mathematical Operations

### 3.2.1 Percentile Speeds (`compute_percentile_speed`)
The system calculates `V15`, `V50` (Median), and `V85` speeds. 
Because the `.fim` payload often groups vehicles into speed brackets (e.g., 20-30 km/h), the engine processes distributions by iterating over continuous bin centers (`centers = [15, 35, 45...]`) and allocating a cumulative probability weight to each count. The target percentile is interpolated against this cumulative bin distribution.

### 3.2.2 Mean Speed & Standard Deviation (Ecart Type)
*   **Mean ($V_{moy}$)**: Computed globally as `compute_weighted_speed`. It is a strict population mean mapping the bin centers against vehicle frequency.
*   **Standard Deviation (Ecart Type)**: Represents the variance of the speed distribution around the mean, critical for understanding speed homogenization (traffic safety).

### 3.2.3 Infractions Analysis
Using the `VMAX` parameter (the legal speed limit given via the UI), the system calculates true infraction counts. It iteratively sums frequency bins where the bin center strictly exceeds `VMAX`. It also derives the `% Infractions` as `(Infractions / Total Vehicles) * 100`.

### 3.2.4 Time-Series Aggregation
*   **TMH (Trafic Moyen Horaire)**: Average hourly traffic volume calculated over the total duration of the survey.
*   **TMJ (Trafic Moyen Journalier)**: Average daily traffic.
*   **Hourly Binning (`compute_hourly_bins`)**: Rotates the DataFrame to produce a `24x12` matrix. The Y-axis represents the 24 hours of a day, and the X-axis holds the 12 speed-bracket distributions. This matrix maps directly to the central visual graphs in the `Synthese` sheets.

## 3.3 Directional Logic
The engine dynamically pivots on the `direction` attribute (`Sens 1`, `Sens 2`). If processing global synthesis, it operates on a generated `Total` sub-frame that merges both directions.
