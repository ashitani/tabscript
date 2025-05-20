import pytest
from reportlab.lib.units import mm
from tabscript.renderer import RepeatRenderer
from tabscript.style import StyleManager
from tabscript.models import Bar
from reportlab.pdfgen import canvas
from io import BytesIO

@pytest.fixture
def style_manager():
    return StyleManager()

@pytest.fixture
def repeat_renderer(style_manager):
    return RepeatRenderer(style_manager)

@pytest.fixture
def pdf_canvas():
    return canvas.Canvas(BytesIO())

@pytest.fixture
def y_positions():
    return [100 + i * 8.5 for i in range(6)]  # 6弦分のy座標

def test_draw_repeat_start(repeat_renderer, pdf_canvas, y_positions):
    """リピート開始記号の描画テスト"""
    repeat_renderer.draw_repeat_start(pdf_canvas, 100, y_positions)

def test_draw_repeat_end(repeat_renderer, pdf_canvas, y_positions):
    """リピート終了記号の描画テスト"""
    repeat_renderer.draw_repeat_start(pdf_canvas, 100, y_positions)

def test_draw_repeat_both(repeat_renderer, pdf_canvas, y_positions):
    """リピート開始と終了記号の描画テスト"""
    repeat_renderer.draw_repeat_start(pdf_canvas, 100, y_positions)

def test_draw_repeat_none(repeat_renderer, pdf_canvas, y_positions):
    """リピート記号なしの描画テスト"""
    repeat_renderer.draw_repeat_start(pdf_canvas, 100, y_positions)

def test_draw_repeat_with_volta(repeat_renderer, pdf_canvas, y_positions):
    """ボルタ付きリピート記号の描画テスト"""
    repeat_renderer.draw_repeat_start(pdf_canvas, 100, y_positions) 