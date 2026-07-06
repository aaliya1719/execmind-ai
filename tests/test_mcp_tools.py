import io
import os
import sys
import tempfile

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.mcp.file_tools import (
    get_dataset_summary,
    list_columns,
    read_uploaded_dataframe,
    validate_dataframe,
)
from app.mcp.report_tools import export_json, export_markdown, export_text


class MockUploadedFile(io.BytesIO):
    def __init__(self, name, content_bytes):
        super().__init__(content_bytes)
        self.name = name
        self.size = len(content_bytes)


def test_dataset_summary_and_columns():
    df = pd.DataFrame(
        {
            "region": ["North", "South", None],
            "sales": [100.0, 150.0, 200.0],
            "category": ["A", "B", "A"],
        }
    )

    summary = get_dataset_summary(df)

    assert summary["rows"] == 3
    assert summary["columns"] == 3
    assert summary["column_names"] == ["region", "sales", "category"]
    assert summary["missing_values"]["region"] == 1
    assert summary["numeric_columns"] == ["sales"]
    assert summary["categorical_columns"] == ["region", "category"]
    assert list_columns(df) == ["region", "sales", "category"]


def test_dataframe_validation():
    valid_df = pd.DataFrame({"sales": [1, 2, 3]})
    invalid_df = pd.DataFrame({"sales": []})

    valid_result = validate_dataframe(valid_df)
    invalid_result = validate_dataframe(invalid_df)

    assert valid_result["is_valid"] is True
    assert valid_result["errors"] == []
    assert invalid_result["is_valid"] is False
    assert invalid_result["errors"]


def test_read_uploaded_dataframe_parses_uploaded_file():
    csv_content = b"region,sales,category\nNorth,100,A\nSouth,150,B"
    uploaded_file = MockUploadedFile("sales.csv", csv_content)

    df = read_uploaded_dataframe(uploaded_file)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 3)


def test_json_export_creates_file_with_report_content():
    report = {"summary": "ok", "rows": 2}

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "exports", "report.json")
        exported_path = export_json(report, output_path)

        assert exported_path == output_path
        assert os.path.exists(exported_path)
        with open(exported_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        assert "summary" in content and "rows" in content


def test_markdown_and_text_exports_create_files():
    report = {"title": "Quarterly", "status": "ready"}

    with tempfile.TemporaryDirectory() as tmpdir:
        markdown_path = os.path.join(tmpdir, "exports", "report.md")
        text_path = os.path.join(tmpdir, "exports", "report.txt")

        exported_markdown = export_markdown(report, markdown_path)
        exported_text = export_text(report, text_path)

        assert exported_markdown == markdown_path
        assert exported_text == text_path
        assert os.path.exists(markdown_path)
        assert os.path.exists(text_path)
        with open(markdown_path, "r", encoding="utf-8") as handle:
            markdown_content = handle.read()
        with open(text_path, "r", encoding="utf-8") as handle:
            text_content = handle.read()

        assert "Quarterly" in markdown_content or "title" in markdown_content
        assert "Quarterly" in text_content or "title" in text_content
