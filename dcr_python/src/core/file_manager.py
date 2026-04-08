"""
File management operations - import/export FIM, DBL, and IFX files
"""

import os
import glob
from typing import List, Optional, Tuple
import pandas as pd
from openpyxl import load_workbook, Workbook
from pathlib import Path

from ..utils import validators, helpers
from .fim_parser import parse_fim_file


class FileManager:
    """Manages file operations for traffic data"""
    
    def __init__(self, fim_dir: str = "", ifx_dir: str = "", dbl_dir: str = ""):
        """
        Initialize FileManager with directory paths.
        
        Args:
            fim_dir: Directory for FIM files
            ifx_dir: Directory for IFX files
            dbl_dir: Directory for DBL files
        """
        self.fim_dir = fim_dir or ""
        self.ifx_dir = ifx_dir or ""
        self.dbl_dir = dbl_dir or ""
    
    def list_fim_files(self) -> List[str]:
        """
        List all FIM files in the FIM directory.
        
        Returns:
            List of FIM filenames
        """
        if not self.fim_dir or not os.path.isdir(self.fim_dir):
            return []
        
        files = glob.glob(os.path.join(self.fim_dir, "*.FIM"))
        files += glob.glob(os.path.join(self.fim_dir, "*.fim"))
        return [os.path.basename(f) for f in files]
    
    def list_dbl_files(self) -> List[str]:
        """
        List all DBL files in the DBL directory.
        
        Returns:
            List of DBL filenames
        """
        if not self.dbl_dir or not os.path.isdir(self.dbl_dir):
            return []
        
        files = glob.glob(os.path.join(self.dbl_dir, "*.DBL"))
        files += glob.glob(os.path.join(self.dbl_dir, "*.dbl"))
        return [os.path.basename(f) for f in files]
    
    def list_ifx_files(self) -> List[str]:
        """
        List all IFX files in the IFX directory.
        
        Returns:
            List of IFX filenames
        """
        if not self.ifx_dir or not os.path.isdir(self.ifx_dir):
            return []
        
        files = glob.glob(os.path.join(self.ifx_dir, "*.IFX"))
        files += glob.glob(os.path.join(self.ifx_dir, "*.ifx"))
        return [os.path.basename(f) for f in files]
    
    def open_file(self, filename: str, file_type: str) -> Optional[pd.DataFrame]:
        """
        Open a traffic data file.
        
        Args:
            filename: The filename to open
            file_type: The file type (FIM, DBL, IFX)
        
        Returns:
            DataFrame if successful, None otherwise
        """
        try:
            if file_type.upper() == "FIM":
                filepath = os.path.join(self.fim_dir, filename)
            elif file_type.upper() == "DBL":
                filepath = os.path.join(self.dbl_dir, filename)
            elif file_type.upper() == "IFX":
                filepath = os.path.join(self.ifx_dir, filename)
            else:
                return None
            
            if not os.path.isfile(filepath):
                return None

            # Special handling for FIM files: use flexible parser
            if filepath.lower().endswith('.fim'):
                parsed_df, fim_metadata = parse_fim_file(filepath)
                if parsed_df is not None:
                    # Store FIM metadata on the dataframe for later use by data processor
                    # This includes: year, month, day, start_hour, start_minute, interval_minutes, num_sensors
                    # vl_columns, pl_columns, rows_per_block, num_data_rows
                    if hasattr(parsed_df, 'attrs'):
                        parsed_df.attrs['fim_metadata'] = fim_metadata
                    return parsed_df

            # Try to read as Excel file first
            try:
                return pd.read_excel(filepath, sheet_name=0)
            except Exception:
                # Try to read as CSV as a fallback
                try:
                    return pd.read_csv(filepath)
                except Exception:
                    # Last resort: read entire file as a single-column text table
                    try:
                        return pd.read_table(filepath, header=None)
                    except Exception as e:
                        print(f"Error opening file {filename}: {str(e)}")
                        return None
        
        except Exception as e:
            print(f"Error opening file {filename}: {str(e)}")
            return None
    
    def import_file(self, source_path: str, destination_dir: str) -> Tuple[bool, Optional[str]]:
        """
        Import a file to the destination directory.
        
        Args:
            source_path: Full path to the source file
            destination_dir: Destination directory (fim_dir, dbl_dir, or ifx_dir)
        
        Returns:
            Tuple of (success: bool, destination_path: Optional[str])
        """
        try:
            if not os.path.isfile(source_path):
                return False, None
            
            if not os.path.isdir(destination_dir):
                helpers.ensure_directory_exists(destination_dir)
            
            filename = os.path.basename(source_path)
            dest_path = os.path.join(destination_dir, filename)
            
            # Avoid overwriting existing files
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    new_filename = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(destination_dir, new_filename)
                    counter += 1
            
            # Copy file
            import shutil
            shutil.copy2(source_path, dest_path)
            return True, dest_path
        
        except Exception as e:
            print(f"Error importing file: {str(e)}")
            return False, None
    
    def export_file(self, data: pd.DataFrame, filename: str, export_format: str = "IFX") -> Tuple[bool, Optional[str]]:
        """
        Export data to a file.
        
        Args:
            data: DataFrame to export
            filename: Output filename
            export_format: Export format (IFX, CSV, XLSX)
        
        Returns:
            Tuple of (success: bool, filepath: Optional[str])
        """
        try:
            if export_format.upper() == "IFX":
                dest_dir = self.ifx_dir
                if filename.upper().endswith(".IFX"):
                    filepath = os.path.join(dest_dir, filename)
                else:
                    filepath = os.path.join(dest_dir, f"{filename}.IFX")
            elif export_format.upper() == "CSV":
                filepath = os.path.join(dest_dir, filename if filename.endswith(".csv") else f"{filename}.csv")
            elif export_format.upper() == "XLSX":
                filepath = os.path.join(dest_dir, filename if filename.endswith(".xlsx") else f"{filename}.xlsx")
            else:
                return False, None
            
            # Ensure directory exists
            helpers.ensure_directory_exists(os.path.dirname(filepath))
            
            # Export based on format
            if export_format.upper() in ["IFX", "XLSX"]:
                data.to_excel(filepath, index=False)
            elif export_format.upper() == "CSV":
                data.to_csv(filepath, index=False)
            
            return True, filepath
        
        except Exception as e:
            print(f"Error exporting file: {str(e)}")
            return False, None
    
    def get_file_info(self, filename: str, file_type: str) -> dict:
        """
        Get information about a file.
        
        Args:
            filename: The filename
            file_type: The file type (FIM, DBL, IFX)
        
        Returns:
            Dictionary with file information
        """
        try:
            if file_type.upper() == "FIM":
                filepath = os.path.join(self.fim_dir, filename)
            elif file_type.upper() == "DBL":
                filepath = os.path.join(self.dbl_dir, filename)
            elif file_type.upper() == "IFX":
                filepath = os.path.join(self.ifx_dir, filename)
            else:
                return {}
            
            if not os.path.isfile(filepath):
                return {}
            
            stat_info = os.stat(filepath)
            
            return {
                "filename": filename,
                "filepath": filepath,
                "size": stat_info.st_size,
                "created": stat_info.st_ctime,
                "modified": stat_info.st_mtime,
                "type": file_type.upper()
            }
        
        except Exception as e:
            print(f"Error getting file info: {str(e)}")
            return {}
