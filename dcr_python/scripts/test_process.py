"""
Quick test of data processing pipeline
"""
import sys
import os
import pandas as pd

# Setup path to import src as a package
script_dir = os.path.dirname(__file__)
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.core.data_processor import DataProcessor
from src.core.fim_parser import parse_fim_file
from src.models import TrafficMetadata

if __name__ == '__main__':
    # Load a test FIM file
    fim_file = "C:\\DCR4402\\FIM\\C01.fim"
    print(f"Loading FIM file: {fim_file}")
    
    df = parse_fim_file(fim_file)
    if df is None or df.empty:
        print("Failed to parse FIM file")
        sys.exit(1)
    
    print(f"Loaded: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"Columns: {list(df.columns)}")
    print(f"First 5 rows:\n{df.head()}\n")
    
    # Process the data
    processor = DataProcessor()
    metadata = TrafficMetadata(
        filename="C01.fim",
        filepath=fim_file,
        format="FIM",
        sequence=1440,
        mode="1 - TV Conf."
    )
    
    success, message = processor.process_raw_data(df, metadata)
    
    print(f"Processing success: {success}")
    print(f"Message: {message}")
    
    if success and processor.processed_data is not None:
        print(f"\nProcessed data shape: {processor.processed_data.shape}")
        print(f"Processed columns: {list(processor.processed_data.columns)}")
        print(f"First 10 rows:\n{processor.processed_data.head(10)}")
        print(f"\nBasic stats:\n{processor.processed_data.describe()}")
    else:
        print("Processing failed or returned no data")
        sys.exit(1)
