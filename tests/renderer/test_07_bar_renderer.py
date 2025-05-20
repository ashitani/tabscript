import pytest
from reportlab.lib.units import mm
from tabscript.renderer import BarRenderer, NoteRenderer, TripletRenderer, VoltaRenderer, RepeatRenderer, DummyBarRenderer
from tabscript.style import StyleManager
from tabscript.models import Bar, Note
from reportlab.pdfgen import canvas
from io import BytesIO

@pytest.fixture
def style_manager():
    return StyleManager()

@pytest.fixture
def bar_renderer(style_manager):
    return BarRenderer(style_manager)

@pytest.fixture
def pdf_canvas():
    return canvas.Canvas(BytesIO())

@pytest.fixture
def y_positions():
    return [100 + i * 8.5 for i in range(6)]  # 6弦分のy座標

@pytest.fixture
def sample_bar():
    bar = Bar()
    bar.notes = [Note(string=1, fret="0", duration="4")]
    return bar

def test_render_bar_normal(bar_renderer, pdf_canvas, y_positions, sample_bar):
    """通常の小節の描画テスト"""
    bar_renderer.render_bar(pdf_canvas, sample_bar, 100, 100, 50, y_positions)

def test_render_bar_with_triplet(bar_renderer, pdf_canvas, y_positions):
    """三連符を含む小節の描画テスト"""
    bar = Bar()
    # 三連符の音符を追加
    for i in range(3):
        note = Note(string=1, fret=str(i), duration="8")
        note.tuplet = 3
        bar.notes.append(note)

    bar_renderer.render_bar(pdf_canvas, bar, 100, 100, 50, y_positions)

def test_render_bar_with_volta(bar_renderer, pdf_canvas, y_positions, sample_bar):
    """ボルタ付き小節の描画テスト"""
    sample_bar.volta_number = 1
    sample_bar.volta_start = True
    sample_bar.volta_end = True

    bar_renderer.render_bar(pdf_canvas, sample_bar, 100, 100, 50, y_positions)

def test_render_bar_with_repeat(bar_renderer, pdf_canvas, y_positions, sample_bar):
    """リピート付き小節の描画テスト"""
    sample_bar.repeat_start = True
    sample_bar.repeat_end = True

    bar_renderer.render_bar(pdf_canvas, sample_bar, 100, 100, 50, y_positions)

def test_render_bar_dummy(bar_renderer, pdf_canvas, y_positions):
    """ダミー小節の描画テスト"""
    bar = Bar()
    bar.is_dummy = True

    bar_renderer.render_bar(pdf_canvas, bar, 100, 100, 50, y_positions)

def test_render_bar_with_chord(bar_renderer, pdf_canvas, y_positions):
    """和音を含む小節の描画テスト"""
    bar = Bar()
    # 和音の音符を追加
    note = Note(string=1, fret="5", duration="4", is_chord=True, is_chord_start=True)
    note.chord_notes = [
        Note(string=2, fret="5", duration="4"),
        Note(string=3, fret="5", duration="4")
    ]
    bar.notes.append(note)

    bar_renderer.render_bar(pdf_canvas, bar, 100, 100, 50, y_positions)

def test_render_bar_with_rest(bar_renderer, pdf_canvas, y_positions):
    """休符を含む小節の描画テスト"""
    bar = Bar()
    # 休符を追加
    note = Note(string=1, fret="0", duration="4", is_rest=True)
    bar.notes.append(note)

    bar_renderer.render_bar(pdf_canvas, bar, 100, 100, 50, y_positions) 