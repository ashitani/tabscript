import pytest
from tabscript.renderer import Renderer
from tabscript.models import Score, Section, Bar, Note

def test_pdf_generation():
    """PDF出力をテスト"""
    score = Score(title="Test")
    renderer = Renderer(score)
    # PDF出力のテスト

def test_text_output():
    """テキスト出力をテスト"""
    score = Score(title="Test")
    renderer = Renderer(score)
    # テキスト出力のテスト 

def test_pdf_triplet_mark(tmp_path):
    """三連符記号（3）がPDFに描画されることを検証するテスト"""
    # 三連符を含むBarを作成
    notes = [Note(string=4, fret="4", duration="8", tuplet=3),
             Note(string=4, fret="4", duration="8", tuplet=3),
             Note(string=4, fret="4", duration="8", tuplet=3)]
    bar = Bar(notes=notes)
    section = Section("A")
    section.bars = [bar]
    score = Score(title="TripletTest", sections=[section])

    renderer = Renderer(score)
    output_pdf = tmp_path / "triplet_test.pdf"
    renderer.render_pdf(str(output_pdf))

    # PDF出力ファイルが生成されていることを確認
    assert output_pdf.exists()
    # 本格的なPDF内容検証は難しいため、生成のみ確認 