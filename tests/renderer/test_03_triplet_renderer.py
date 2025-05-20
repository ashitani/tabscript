import pytest
from reportlab.lib.units import mm
from tabscript.renderer import TripletRenderer
from tabscript.style import StyleManager
from tabscript.models import Bar, Note
from reportlab.pdfgen import canvas
from io import BytesIO

@pytest.fixture
def style_manager():
    return StyleManager()

@pytest.fixture
def triplet_renderer(style_manager):
    return TripletRenderer(style_manager)

@pytest.fixture
def pdf_canvas():
    """テスト用のPDFキャンバスを作成"""
    buffer = BytesIO()
    return canvas.Canvas(buffer)

@pytest.fixture
def sample_bar():
    """テスト用のサンプル小節を作成"""
    bar = Bar()
    # 三連符の音符を追加
    for i in range(3):
        note = Note(string=1, fret=str(i), duration="8")
        note.tuplet = 3
        bar.notes.append(note)
    return bar

def test_detect_triplet_ranges(triplet_renderer, sample_bar, pdf_canvas):
    """三連符の範囲検出テスト"""
    # 音符の位置を計算
    note_x_positions = [100 + (i * 20) for i in range(3)]
    
    # 三連符の範囲を検出
    triplet_ranges = triplet_renderer.detect_triplet_ranges(
        sample_bar, note_x_positions, pdf_canvas
    )
    
    # 1つの三連符が検出されることを確認
    assert len(triplet_ranges) == 1
    
    # 三連符の範囲を確認
    x1, x2, start, end = triplet_ranges[0]
    assert start == 0
    assert end == 2
    assert x1 == note_x_positions[0] + 1.5 * mm
    assert x2 == note_x_positions[2] + 1.5 * mm + pdf_canvas.stringWidth("2", "Helvetica", 10)

def test_detect_triplet_ranges_invalid(triplet_renderer, pdf_canvas):
    """無効な三連符の範囲検出テスト"""
    bar = Bar()
    # 不完全な三連符（2音のみ）
    for i in range(2):
        note = Note(string=1, fret=str(i), duration="8")
        note.tuplet = 3
        bar.notes.append(note)
    
    note_x_positions = [100 + (i * 20) for i in range(2)]
    triplet_ranges = triplet_renderer.detect_triplet_ranges(
        bar, note_x_positions, pdf_canvas
    )
    
    # 不完全な三連符は検出されないことを確認
    assert len(triplet_ranges) == 0

def test_draw_triplet_marks(triplet_renderer, pdf_canvas):
    """三連符記号の描画テスト"""
    # 三連符の範囲を定義
    triplet_ranges = [(100, 200, 0, 2)]
    y_positions = [100 + (i * 3 * mm) for i in range(6)]
    
    # 三連符記号を描画
    triplet_renderer.draw_triplet_marks(pdf_canvas, triplet_ranges, y_positions)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認

def test_draw_triplet_marks_multiple(triplet_renderer, pdf_canvas):
    """複数の三連符記号の描画テスト"""
    # 複数の三連符の範囲を定義
    triplet_ranges = [
        (100, 200, 0, 2),
        (300, 400, 3, 5)
    ]
    y_positions = [100 + (i * 3 * mm) for i in range(6)]
    
    # 三連符記号を描画
    triplet_renderer.draw_triplet_marks(pdf_canvas, triplet_ranges, y_positions)
    # 実際の描画結果は確認できないため、エラーが発生しないことを確認 