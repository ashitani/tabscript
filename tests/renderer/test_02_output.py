import pytest
from tabscript.renderer import Renderer
from tabscript.models import Score

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