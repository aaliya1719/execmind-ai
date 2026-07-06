"""MCP utilities for exporting agent reports to disk.

These helpers create the destination folders automatically and write common
report formats that can be consumed by downstream tools or users.
"""

from __future__ import annotations

import json
import os
from typing import Any, Union


def _ensure_parent_directory(output_path: str) -> None:
    """Create the parent directory for an export path if it does not exist."""
    directory = os.path.dirname(output_path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def _render_markdown(report: Any) -> str:
    """Convert a report payload into a simple markdown string."""
    if isinstance(report, dict):
        lines = ["# Report", ""]
        for key, value in report.items():
            lines.append(f"- **{key}:** {value}")
        return "\n".join(lines) + "\n"
    if isinstance(report, (list, tuple)):
        return "\n".join([f"- {item}" for item in report]) + "\n"
    return str(report)


def _render_text(report: Any) -> str:
    """Convert a report payload into plain text."""
    if isinstance(report, dict):
        lines = []
        for key, value in report.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines) + "\n"
    if isinstance(report, (list, tuple)):
        return "\n".join([str(item) for item in report]) + "\n"
    return str(report)


def export_json(report: Any, output_path: Union[str, os.PathLike[str]]) -> str:
    """Export a report payload to a JSON file.

    Args:
        report: The report object to serialize.
        output_path: Destination path for the exported JSON file.

    Returns:
        The absolute output path that was written.

    Raises:
        ValueError: If the output path is empty or the report cannot be encoded.
    """
    if not output_path:
        raise ValueError("An output path is required.")

    output_path = os.fspath(output_path)
    try:
        _ensure_parent_directory(output_path)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        return output_path
    except (TypeError, ValueError, OSError) as exc:
        raise ValueError(f"Unable to export JSON report: {exc}") from exc


def export_markdown(report: Any, output_path: Union[str, os.PathLike[str]]) -> str:
    """Export a report payload to a markdown file."""
    if not output_path:
        raise ValueError("An output path is required.")

    output_path = os.fspath(output_path)
    try:
        _ensure_parent_directory(output_path)
        content = _render_markdown(report)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return output_path
    except OSError as exc:
        raise ValueError(f"Unable to export markdown report: {exc}") from exc


def export_text(report: Any, output_path: Union[str, os.PathLike[str]]) -> str:
    """Export a report payload to a plain text file."""
    if not output_path:
        raise ValueError("An output path is required.")

    output_path = os.fspath(output_path)
    try:
        _ensure_parent_directory(output_path)
        content = _render_text(report)
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        return output_path
    except OSError as exc:
        raise ValueError(f"Unable to export text report: {exc}") from exc

