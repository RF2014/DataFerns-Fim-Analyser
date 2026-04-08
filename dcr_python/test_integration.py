"""
Integration test: FileManager + DataProcessor with new FIM parser
"""
from src.core.file_manager import FileManager
from src.core.data_processor import DataProcessor
from src.models import TrafficMetadata
from datetime import datetime

# Initialize components
fm = FileManager(fim_dir='C:\\DCR4402\\FIM')
dp = DataProcessor()

print('=== Integration Test: FileManager + DataProcessor ===\n')

# Step 1: Load FIM file via FileManager
print('Step 1: Loading C01.fim via FileManager...')
df = fm.open_file('C01.fim', 'FIM')

if df is None:
    print('✗ Failed to load file')
    exit(1)

print(f'✓ File loaded successfully')
print(f'  Shape: {df.shape}')
print(f'  Columns: {list(df.columns)}')

# Check for metadata
fim_metadata = None
if hasattr(df, 'attrs') and 'fim_metadata' in df.attrs:
    fim_metadata = df.attrs['fim_metadata']
    print(f'  FIM Metadata found:')
    print(f'    Date: {fim_metadata.get("year")}-{fim_metadata.get("month")}-{fim_metadata.get("day")}')
    print(f'    Start: {fim_metadata.get("start_hour")}:{fim_metadata.get("start_minute"):02d}')
    print(f'    Sensors: {fim_metadata.get("num_sensors")}')
    print(f'    Rows per block: {fim_metadata.get("rows_per_block")}')

# Step 2: Process data via DataProcessor
print(f'\nStep 2: Processing data via DataProcessor...')

# Create metadata
metadata = TrafficMetadata(
    filename='C01.fim',
    filepath='C:\\DCR4402\\FIM\\C01.fim',
    format='FIM',
    sequence=5,  # 5-minute intervals
    mode='TV Conf.',
    created_date=datetime.now(),
    description='FIM traffic data from C01'
)

success, message = dp.process_raw_data(df, metadata, interval_minutes=5)
print(f'✓ Data processing: {message}')

if success and dp.processed_data is not None:
    print(f'  Processed shape: {dp.processed_data.shape}')
    print(f'  Processed columns: {list(dp.processed_data.columns)}')
    
    # Display first few rows
    print(f'\n  First 10 rows of processed data:')
    print(dp.processed_data.head(10))
    
    # Step 3: Get summaries
    print(f'\nStep 3: Generating summaries...')
    
    hourly = dp.get_hourly_summary()
    if not hourly.empty:
        print(f'  Hourly summary shape: {hourly.shape}')
        print(f'  Hourly summary columns: {list(hourly.columns)}')
        print(f'  First 5 hours:')
        print(hourly.head())
    
    daily = dp.get_daily_summary()
    if daily:
        print(f'\n  Daily summary keys: {list(daily.keys())}')
    
    print(f'\n✓ Integration test completed successfully!')
else:
    print(f'✗ Data processing failed: {message}')
