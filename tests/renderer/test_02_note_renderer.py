import pytest
from reportlab.lib.units import mm
from tabscript.renderer import NoteRenderer
from tabscript.style import StyleManager
from tabscript.models import Note
from reportlab.pdfgen import canvas
from io import BytesIO

@pytest.fixture
def style_manager():
    return StyleManager()

@pytest.fixture
def note_renderer(style_manager):
    return NoteRenderer(style_manager)

@pytest.fixture
def pdf_canvas():
    """テスト用のPDFキャンバスを作成"""
    buffer = BytesIO()
    return canvas.Canvas(buffer)

@pytest.fixture
def y_positions():
    """テスト用の弦の位置を生成"""
    return [100 + (i * 3 * mm) for i in range(6)]

def test_render_note_rest(note_renderer, pdf_canvas):
    """休符の描画テスト"""
    note = Note(string=1, fret="0", duration="4", is_rest=True)
    note_renderer.render_note(pdf_canvas, note, 100, 100)
    # 休符は何も描画されないことを確認
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_render_note_normal(note_renderer, pdf_canvas):
    """通常の音符の描画テスト"""
    note = Note(string=1, fret="5", duration="4")
    note_renderer.render_note(pdf_canvas, note, 100, 100)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_render_note_with_brace(note_renderer, pdf_canvas):
    """中括弧付きの音符の描画テスト"""
    note = Note(string=1, fret="{5}", duration="4")
    note_renderer.render_note(pdf_canvas, note, 100, 100, y_offset=5 * mm)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_render_note_chord(note_renderer, pdf_canvas, y_positions):
    """和音の音符の描画テスト"""
    note = Note(string=1, fret="5", duration="4", is_chord=True, is_chord_start=True)
    note.chord_notes = [
        Note(string=2, fret="5", duration="4"),
        Note(string=3, fret="5", duration="4")
    ]
    note_renderer.render_note(pdf_canvas, note, 100, 100, y_positions=y_positions)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_draw_fret_number(note_renderer, pdf_canvas):
    """フレット番号の描画テスト"""
    # 通常のフレット番号
    note_renderer._draw_fret_number(pdf_canvas, 100, 100, "5")
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認
    
    # X記号
    note_renderer._draw_fret_number(pdf_canvas, 100, 100, "X")
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認
    
    # 接続記号付き
    note_renderer._draw_fret_number(pdf_canvas, 100, 100, "5", connect_next=True)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_draw_chord_notes(note_renderer, pdf_canvas, y_positions):
    """和音の音符の描画テスト"""
    note = Note(string=1, fret="5", duration="4", is_chord=True, is_chord_start=True)
    note.chord_notes = [
        Note(string=2, fret="5", duration="4"),
        Note(string=3, fret="5", duration="4")
    ]
    note_renderer._draw_chord_notes(pdf_canvas, 100, note, y_positions)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認 