"""Reusable MCP utilities for inspecting uploaded datasets.

These helpers provide safe, reusable dataframe operations for agents that
process uploaded CSV or Excel files.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Union

import pandas as pd

from app.utils.file_utils import parse_uploaded_file


def read_uploaded_dataframe(file: Any) -> pd.DataFrame:
    """Read an uploaded file or path into a pandas DataFrame.

    Args:
        file: A file-like object with a filename or a filesystem path.

    Returns:
        A parsed pandas DataFrame.

    Raises:
        ValueError: If the input is missing, unsupported, or malformed.
    """
    if file is None:
        raise ValueError("No file was provided.")

    if hasattr(file, "read"):
        try:
            return parse_uploaded_file(file)
        except ValueError as exc:
            raise ValueError(f"Unable to read uploaded file: {exc}") from exc

    if isinstance(file, (str, os.PathLike)):
        path = os.fspath(file)
        if not os.path.exists(path):
            raise ValueError(f"File does not exist: {path}")

        _, ext = os.path.splitext(path)
        ext = ext.lower()
        try:
            if ext == ".csv":
                return pd.read_csv(path)
            if ext in {".xlsx", ".xls"}:
                return pd.read_excel(path)
            raise ValueError(f"Unsupported file type '{ext}'.")
        except Exception as exc:  # pragma: no cover - defensive branch
            raise ValueError(f"Unable to read file from disk: {exc}") from exc

    raise ValueError("Unsupported file input. Expected a file-like object or path.")


def get_dataset_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Build a compact summary of a dataset for reporting and agents.

    Args:
        df: The pandas DataFrame to inspect.

    Returns:
        A dictionary containing row counts, column metadata, and missing values.
    """
    validate_result = validate_dataframe(df)
    if not validate_result["is_valid"]:
        raise ValueError("Cannot summarize an invalid dataframe: " + "; ".join(validate_result["errors"]))

    missing_values = {str(col): int(df[col].isna().sum()) for col in df.columns}
    numeric_columns = [str(col) for col in df.select_dtypes(include=["number"]).columns]
    categorical_columns = [str(col) for col in df.columns if str(col) not in numeric_columns]

    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": [str(col) for col in df.columns],
        "missing_values": missing_values,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
    }


def list_columns(df: pd.DataFrame) -> List[str]:
    """Return the column names for a DataFrame as a list of strings."""
    validate_result = validate_dataframe(df)
    if not validate_result["is_valid"]:
        raise ValueError("Cannot list columns for an invalid dataframe: " + "; ".join(validate_result["errors"]))

    return [str(col) for col in df.columns]


def validate_dataframe(df: Any) -> Dict[str, Any]:
    """Validate that a value is a non-empty pandas DataFrame.

    Args:
        df: The object to validate.

    Returns:
        A dictionary with an ``is_valid`` flag and a list of errors.
    """
    errors: List[str] = []

    if df is None:
        errors.append("DataFrame is missing.")
    elif not isinstance(df, pd.DataFrame):
        errors.append("Input is not a pandas DataFrame.")
    else:
        if df.empty:
            errors.append("DataFrame has no rows.")
        if len(df.columns) == 0:
            errors.append("DataFrame has no columns.")

    return {"is_valid": not errors, "errors": errors}

