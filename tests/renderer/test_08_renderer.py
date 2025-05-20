import pytest
from reportlab.lib.units import mm
from tabscript.renderer import Renderer, BarRenderer, NoteRenderer, TripletRenderer, VoltaRenderer, RepeatRenderer, DummyBarRenderer
from tabscript.style import StyleManager
from tabscript.models import Score, Section, Bar, Note, Column
from io import BytesIO

@pytest.fixture
def style_manager():
    return StyleManager()

@pytest.fixture
def renderer(style_manager):
    score = Score(title="Test Score", tuning="guitar", beat="4/4", bars_per_line=4)
    return Renderer(score)

@pytest.fixture
def sample_score():
    """テスト用のサンプルスコアを作成"""
    score = Score(title="Test Score", tuning="guitar", beat="4/4", bars_per_line=4)
    section = Section("Test Section")
    
    # 8小節のセクションを作成
    bars = []
    for i in range(8):
        bar = Bar()
        # 基本的な音符を追加
        for j in range(4):
            note = Note(string=1, fret=str(j), duration="4")
            bar.notes.append(note)
        bars.append(bar)
    
    # 小節を2つのカラムに分割
    column1 = Column(bars=bars[:4])
    column2 = Column(bars=bars[4:])
    section.columns = [column1, column2]
    
    score.sections.append(section)
    return score

def test_render_pdf(renderer, sample_score, tmp_path):
    """PDFレンダリングのテスト"""
    output_path = tmp_path / "test_output.pdf"
    renderer.render_pdf(str(output_path))
    
    # 出力ファイルが存在することを確認
    assert output_path.exists()
    # ファイルサイズが0より大きいことを確認
    assert output_path.stat().st_size > 0

def test_render_pdf_with_multiple_sections(renderer, sample_score, tmp_path):
    """複数セクションのPDFレンダリングテスト"""
    # 2つ目のセクションを追加
    section2 = Section("Second Section")
    
    # 4小節のセクションを作成
    bars = []
    for i in range(4):
        bar = Bar()
        for j in range(4):
            note = Note(string=1, fret=str(j), duration="4")
            bar.notes.append(note)
        bars.append(bar)
    
    # 小節を1つのカラムに配置
    column = Column(bars=bars)
    section2.columns = [column]
    
    sample_score.sections.append(section2)
    
    output_path = tmp_path / "test_output.pdf"
    renderer.render_pdf(str(output_path))
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_render_pdf_with_special_bars(renderer, sample_score, tmp_path):
    """特殊な小節を含むPDFレンダリングテスト"""
    # 三連符を含む小節を追加
    bar = Bar()
    for i in range(3):
        note = Note(string=1, fret=str(i), duration="8")
        note.tuplet = 3
        bar.notes.append(note)
    sample_score.sections[0].columns[0].bars.append(bar)
    
    # ボルタ付き小節を追加
    bar = Bar()
    bar.volta_number = 1
    bar.volta_start = True
    bar.volta_end = True
    for i in range(4):
        note = Note(string=1, fret=str(i), duration="4")
        bar.notes.append(note)
    sample_score.sections[0].columns[0].bars.append(bar)
    
    # リピート付き小節を追加
    bar = Bar()
    bar.is_repeat_start = True
    bar.is_repeat_end = True
    for i in range(4):
        note = Note(string=1, fret=str(i), duration="4")
        bar.notes.append(note)
    sample_score.sections[0].columns[0].bars.append(bar)
    
    output_path = tmp_path / "test_output.pdf"
    renderer.render_pdf(str(output_path))
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_render_pdf_with_chords(renderer, sample_score, tmp_path):
    """和音を含むPDFレンダリングテスト"""
    # 和音を含む小節を追加
    bar = Bar()
    note = Note(string=1, fret="5", duration="4", is_chord=True, is_chord_start=True)
    note.chord_notes = [
        Note(string=2, fret="5", duration="4"),
        Note(string=3, fret="5", duration="4")
    ]
    bar.notes.append(note)
    sample_score.sections[0].columns[0].bars.append(bar)
    
    output_path = tmp_path / "test_output.pdf"
    renderer.render_pdf(str(output_path))
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_render_pdf_with_rests(renderer, sample_score, tmp_path):
    """休符を含むPDFレンダリングテスト"""
    # 休符を含む小節を追加
    bar = Bar()
    note = Note(string=1, fret="0", duration="4", is_rest=True)
    bar.notes.append(note)
    sample_score.sections[0].columns[0].bars.append(bar)
    
    output_path = tmp_path / "test_output.pdf"
    renderer.render_pdf(str(output_path))
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0 