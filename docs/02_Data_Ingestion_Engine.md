# 2. Data Ingestion Engine

## 2.1 Overview
At the heart of the system is `core/fim_parser.py`. Sensor devices generate `.fim` files which are predominantly binary representations of chronological traffic events or interval data. The parser must unpak these byte streams into a unified analytic `DataFrame`.

## 2.2 Protocol Processing
The sensor files have specific file signatures indicating their generation type:

1.  **FIME0001 (Raw Event Traces)**: 
    *   Chronological vehicle-by-vehicle passes.
    *   Each record usually denotes `Timestamp`, `Speed`, `Length`, `Direction`, and `Class (VL/PL)`.
2.  **FIME0003 & FIME0004 (Binned Interval Data)**:
    *   Aggregated datasets where raw events are pre-grouped into distinct speed bins (e.g., 0-15, 15-30km/h) for a specific hour or time interval.

## 2.3 The parsing flow (`FimParser` class):
1.  **Header Extraction**: The parser reads the top metadata block of the file to determine the survey's official start timestamp and operational mode.
2.  **Byte Traversal**: Depending on the protocol, the parser iterates over the payload bytes using standard `struct.unpack` logic.
3.  **Standardization**: Regardless of the input protocol, the output is strictly standardized into a `pandas.DataFrame`. 
    *   If the data is "Event Trace" (Fime0001), it is synthetically binned by the `AnalyticsEngine` later.
    *   If the data is "Binned" (Fime0003/4), it builds interval rows with pre-calculated column distributions (`Bin1`, `Bin2`, etc.).

## 2.4 Error Tolerances
The parser is built to skip malformed byte chunks to salvage partial survey data rather than crashing. Any missing FIM metadata (like `Sector ID` or `Index`) is inherently offloaded to the user via the `MetadataPanel` GUI.
