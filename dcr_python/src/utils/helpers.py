"""
Helper functions for common operations
"""

import os
from pathlib import Path
from typing import Optional


def ensure_directory_exists(dirpath: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dirpath: The directory path
    
    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        Path(dirpath).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def get_file_extension(filepath: str) -> str:
    """
    Get the file extension from a filepath.
    
    Args:
        filepath: The file path
    
    Returns:
        The extension (without dot) in uppercase
    """
    _, ext = os.path.splitext(filepath)
    return ext.lstrip('.').upper()


def get_filename_without_extension(filepath: str) -> str:
    """
    Get the filename without extension.
    
    Args:
        filepath: The file path
    
    Returns:
        The filename without extension
    """
    return os.path.splitext(os.path.basename(filepath))[0]


def change_file_extension(filepath: str, new_extension: str) -> str:
    """
    Change the file extension.
    
    Args:
        filepath: The file path
        new_extension: The new extension (with or without dot)
    
    Returns:
        The new filepath with changed extension
    """
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension
    
    base, _ = os.path.splitext(filepath)
    return base + new_extension


def format_file_list(filepaths: list) -> list:
    """
    Format a list of filepaths to just filenames.
    
    Args:
        filepaths: List of file paths
    
    Returns:
        List of filenames
    """
    return [os.path.basename(fp) for fp in filepaths]


def safe_file_operation(operation_func, *args, **kwargs):
    """
    Safely execute a file operation with error handling.
    
    Args:
        operation_func: The function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Tuple of (success: bool, result: Any, error: Optional[Exception])
    """
    try:
        result = operation_func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        return False, None, e
