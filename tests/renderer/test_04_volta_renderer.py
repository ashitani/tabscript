import pytest
from reportlab.lib.units import mm
from tabscript.renderer import VoltaRenderer
from tabscript.style import StyleManager
from tabscript.models import Bar
from reportlab.pdfgen import canvas
from io import BytesIO

@pytest.fixture
def style_manager():
    return StyleManager()

@pytest.fixture
def volta_renderer(style_manager):
    return VoltaRenderer(style_manager)

@pytest.fixture
def pdf_canvas():
    """テスト用のPDFキャンバスを作成"""
    buffer = BytesIO()
    return canvas.Canvas(buffer)

@pytest.fixture
def y_positions():
    """テスト用の弦の位置を生成"""
    return [100 + (i * 3 * mm) for i in range(6)]

def test_draw_volta_bracket_start(volta_renderer, pdf_canvas, y_positions):
    """ボルタブラケット開始の描画テスト"""
    bar = Bar()
    bar.volta_number = 1
    bar.volta_start = True
    
    volta_renderer.draw_volta_bracket(pdf_canvas, bar, 100, 50, y_positions, 100)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_draw_volta_bracket_end(volta_renderer, pdf_canvas, y_positions):
    """ボルタブラケット終了の描画テスト"""
    bar = Bar()
    bar.volta_number = 1
    bar.volta_end = True
    
    volta_renderer.draw_volta_bracket(pdf_canvas, bar, 100, 50, y_positions, 100)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_draw_volta_bracket_both(volta_renderer, pdf_canvas, y_positions):
    """ボルタブラケット開始と終了の描画テスト"""
    bar = Bar()
    bar.volta_number = 1
    bar.volta_start = True
    bar.volta_end = True
    
    volta_renderer.draw_volta_bracket(pdf_canvas, bar, 100, 50, y_positions, 100)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_draw_volta_bracket_none(volta_renderer, pdf_canvas, y_positions):
    """ボルタブラケットなしの描画テスト"""
    bar = Bar()
    bar.volta_number = 1
    
    volta_renderer.draw_volta_bracket(pdf_canvas, bar, 100, 50, y_positions, 100)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_draw_volta_bracket_no_number(volta_renderer, pdf_canvas, y_positions):
    """ボルタ番号なしの描画テスト"""
    bar = Bar()
    bar.volta_start = True
    bar.volta_end = True
    
    volta_renderer.draw_volta_bracket(pdf_canvas, bar, 100, 50, y_positions, 100)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認 