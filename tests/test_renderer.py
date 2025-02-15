import pytest
import os
from tabscript import parser

def test_pdf_generation():
    p = parser()
    score = p.parse("tests/data/sample.tab")
    output_path = "tests/data/sample.pdf"
    
    # PDFの生成
    p.render_score(output_path)
    
    # ファイルが生成されたことを確認
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0
    
    # テスト後にファイルを削除
    os.remove(output_path) 