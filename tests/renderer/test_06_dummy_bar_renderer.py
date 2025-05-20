import pytest
from reportlab.lib.units import mm
from tabscript.renderer import DummyBarRenderer
from tabscript.style import StyleManager
from tabscript.models import Bar
from reportlab.pdfgen import canvas
from io import BytesIO

@pytest.fixture
def style_manager():
    return StyleManager()

@pytest.fixture
def dummy_bar_renderer(style_manager):
    return DummyBarRenderer(style_manager)

@pytest.fixture
def pdf_canvas():
    return canvas.Canvas(BytesIO())

@pytest.fixture
def y_positions():
    return [100 + i * 8.5 for i in range(6)]  # 6弦分のy座標

def test_draw_dummy_bar(dummy_bar_renderer, pdf_canvas, y_positions):
    """ダミー小節の描画テスト"""
    dummy_bar_renderer.draw_dummy_bar(pdf_canvas, 100, 50, y_positions)

def test_draw_dummy_bar_with_volta(dummy_bar_renderer, pdf_canvas, y_positions):
    """ボルタ付きダミー小節の描画テスト"""
    dummy_bar_renderer.draw_dummy_bar(pdf_canvas, 100, 50, y_positions)

def test_draw_dummy_bar_with_repeat(dummy_bar_renderer, pdf_canvas, y_positions):
    """リピート付きダミー小節の描画テスト"""
    dummy_bar_renderer.draw_dummy_bar(pdf_canvas, 100, 50, y_positions)

def test_draw_dummy_bar_with_both(dummy_bar_renderer, pdf_canvas, y_positions):
    """ボルタとリピート付きダミー小節の描画テスト"""
    dummy_bar_renderer.draw_dummy_bar(pdf_canvas, 100, 50, y_positions)

def test_draw_dummy_bar_not_dummy(dummy_bar_renderer, pdf_canvas, y_positions):
    """ダミー小節でない場合の描画テスト"""
    dummy_bar_renderer.draw_dummy_bar(pdf_canvas, 100, 50, y_positions) 