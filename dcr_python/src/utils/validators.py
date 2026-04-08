"""
Validation functions for user input
"""

import os
import re


def validate_filename(filename: str, extension: str) -> bool:
    """
    Validate that a filename has the correct extension and valid characters.
    
    Args:
        filename: The filename to validate
        extension: The required extension (e.g., 'FIM', 'IFX')
    
    Returns:
        True if valid, False otherwise
    """
    if not filename:
        return False
    
    # Check extension
    if not filename.upper().endswith(f".{extension.upper()}"):
        return False
    
    # Check for invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, filename):
        return False
    
    return True


def validate_file_path(filepath: str) -> bool:
    """
    Validate that a file path exists and is readable.
    
    Args:
        filepath: The file path to validate
    
    Returns:
        True if file exists and is readable, False otherwise
    """
    return os.path.isfile(filepath) and os.access(filepath, os.R_OK)


def validate_directory(dirpath: str) -> bool:
    """
    Validate that a directory exists and is accessible.
    
    Args:
        dirpath: The directory path to validate
    
    Returns:
        True if directory exists and is accessible, False otherwise
    """
    return os.path.isdir(dirpath) and os.access(dirpath, os.R_OK)


def validate_sequence(sequence: int) -> bool:
    """
    Validate that a sequence value is valid.
    
    Args:
        sequence: The sequence value to validate
    
    Returns:
        True if valid sequence, False otherwise
    """
    valid_sequences = [15, 30, 60, 1440]
    return sequence in valid_sequences


def validate_number_of_lanes(lanes: str) -> bool:
    """
    Validate that lanes value is in expected format.
    
    Args:
        lanes: The lanes value to validate
    
    Returns:
        True if valid, False otherwise
    """
    valid_lanes = [
        "2 Voies : 1x1",
        "3 Voies : 2x1",
        "4 Voies : 2x2",
        "6 Voies : 3x3",
        "Voie Unique"
    ]
    return lanes in valid_lanes
