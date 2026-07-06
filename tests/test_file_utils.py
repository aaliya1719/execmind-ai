import sys
import io
import pandas as pd
import tempfile
import os

# Append project root dynamically to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.file_utils import parse_uploaded_file, validate_uploaded_file

class MockUploadedFile(io.BytesIO):
    def __init__(self, name, content_bytes):
        super().__init__(content_bytes)
        self.name = name
        self.size = len(content_bytes)

def test_file_parsing():
    print("Starting file parsing tests...")
    
    # 1. Test Valid UTF-8 CSV
    csv_content = b"Date,Sales,Product\n2026-07-01,100,Widget A\n2026-07-02,150,Widget B"
    valid_csv = MockUploadedFile("sales.csv", csv_content)
    df = parse_uploaded_file(valid_csv)
    print(f"Valid CSV Parse: Success. Shape={df.shape} (Expected: (2, 3))")
    assert df.shape == (2, 3)
    
    # 2. Test UTF-8 with BOM (utf-8-sig)
    bom_content = b"\xef\xbb\xbfDate,Sales,Product\n2026-07-01,100,Widget A"
    valid_bom = MockUploadedFile("sales_bom.csv", bom_content)
    df_bom = parse_uploaded_file(valid_bom)
    print(f"BOM CSV Parse: Success. Columns={list(df_bom.columns)} (Expected: ['Date', 'Sales', 'Product'])")
    assert list(df_bom.columns) == ["Date", "Sales", "Product"], "BOM was not stripped"

    # 3. Test Latin-1 Encoding
    latin_content = "Date,Sales,Product,Currency\n2026-07-01,100,Widget A,£".encode("latin-1")
    valid_latin = MockUploadedFile("sales_latin.csv", latin_content)
    df_latin = parse_uploaded_file(valid_latin)
    currency_val = df_latin["Currency"].iloc[0]
    print(f"Latin-1 CSV Parse: Success. Currency (ord)={ord(currency_val)} (Expected pound sign: 163)")
    assert ord(currency_val) == 163

    # 4. Test CP1252 Encoding
    # 0x80 is the Euro sign (€) in CP1252
    cp_content = b"Date,Sales,Product,Symbol\n2026-07-01,100,Widget A,\x80"
    valid_cp = MockUploadedFile("sales_cp.csv", cp_content)
    df_cp = parse_uploaded_file(valid_cp)
    symbol_val = df_cp["Symbol"].iloc[0]
    print(f"CP1252 CSV Parse: Success. Symbol (ord)={ord(symbol_val)} (Expected Euro sign: 8364)")
    assert ord(symbol_val) == 8364
    
    # 5. Test Column Whitespace Stripping
    csv_content_ws = b" Date , Sales ,Product\n2026-07-01,100,Widget A"
    valid_csv_ws = MockUploadedFile("sales_ws.csv", csv_content_ws)
    df_ws = parse_uploaded_file(valid_csv_ws)
    print(f"Whitespace Columns Stripped: {list(df_ws.columns)}")
    assert list(df_ws.columns) == ["Date", "Sales", "Product"]

    # 6. Test Unsupported Format
    invalid_format = MockUploadedFile("sales.txt", b"some text content")
    try:
        parse_uploaded_file(invalid_format)
        print("ERROR: Should have failed for txt format.")
    except ValueError as e:
        print(f"Unsupported format error caught: '{e}'")

    # 7. Test Empty File
    empty_file = MockUploadedFile("empty.csv", b"")
    try:
        parse_uploaded_file(empty_file)
        print("ERROR: Should have failed for empty file.")
    except ValueError as e:
        print(f"Empty file error caught: '{e}'")

    # 8. Test Valid Excel Ingestion (XLSX)
    df_dummy = pd.DataFrame({"Date": ["2026-07-01"], "Sales": [500]})
    temp_excel_path = os.path.join(tempfile.gettempdir(), "test_excel.xlsx")
    df_dummy.to_excel(temp_excel_path, index=False)
    
    with open(temp_excel_path, "rb") as f:
        excel_bytes = f.read()
    os.remove(temp_excel_path)
    
    valid_excel = MockUploadedFile("sales.xlsx", excel_bytes)
    df_xl = parse_uploaded_file(valid_excel)
    print(f"Valid Excel Parse: Success. Shape={df_xl.shape}")
    assert df_xl.shape == (1, 2)

    print("All encoding and parsing tests passed successfully!")

if __name__ == "__main__":
    test_file_parsing()
