"""Utilities for validating and parsing uploaded business files.

Supports CSV and Excel ingestion with robust error handling.
"""

import os
import pandas as pd
from typing import Tuple

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

def validate_uploaded_file(file_obj) -> Tuple[bool, str]:
    """Validate that the uploaded file exists, is non-empty, and has a supported extension.
    
    Args:
        file_obj: The file-like object uploaded by the user.
        
    Returns:
        A tuple of (is_valid, error_message).
    """
    if file_obj is None:
        return False, "No file uploaded."
        
    # Check file name and extension
    filename = getattr(file_obj, "name", "")
    if not filename:
        return False, "Uploaded file does not have a valid filename."
        
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Supported types are: {', '.join(SUPPORTED_EXTENSIONS)}"
        
    # Check file size (Streamlit's UploadedFile has a size property)
    size = getattr(file_obj, "size", 0)
    if size <= 0:
        return False, "The uploaded file is empty."
        
    return True, ""

def parse_uploaded_file(file_obj) -> pd.DataFrame:
    """Parse the uploaded file into a pandas DataFrame.
    
    Args:
        file_obj: The file-like object uploaded by the user.
        
    Returns:
        A clean pandas DataFrame.
        
    Raises:
        ValueError: If parsing fails or the file is malformed.
    """
    is_valid, error_msg = validate_uploaded_file(file_obj)
    if not is_valid:
        raise ValueError(error_msg)
        
    filename = file_obj.name
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    try:
        # Reset file pointer to the beginning to ensure re-reads work
        file_obj.seek(0)
        
        if ext == ".csv":
            encodings = ["utf-8", "utf-8-sig", "cp1252", "latin-1"]
            df = None
            last_err = None
            for enc in encodings:
                try:
                    file_obj.seek(0)
                    df = pd.read_csv(file_obj, encoding=enc)
                    break
                except (UnicodeDecodeError, UnicodeError) as e:
                    last_err = e
            if df is None:
                raise ValueError(
                    f"Unable to decode CSV file. Attempted encodings: {', '.join(encodings)}. "
                    f"Last error: {last_err}"
                )
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_obj)
        else:
            raise ValueError(f"Unsupported file type for parsing: {ext}")
            
        if df.empty:
            raise ValueError("The file contains no data rows.")
            
        # Clean column names (strip whitespace)
        df.columns = [str(col).strip() for col in df.columns]
        
        return df
    except pd.errors.EmptyDataError:
        raise ValueError("The uploaded CSV file is empty or has no columns.")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing CSV file. The formatting might be malformed: {e}")
    except Exception as e:
        raise ValueError(f"Error reading file '{filename}': {str(e)}")

