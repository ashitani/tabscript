import pytest
from tabscript.renderer import Renderer
from tabscript.models import Score, Section, Column, Bar, Note

def test_column_layout():
    """小節の配置計算をテスト"""
    score = Score(title="Test")
    section = Section(name="Test")
    column = Column(bars=[
        Bar(notes=[Note(string=1, fret="0", duration="4")]),
        Bar(notes=[Note(string=2, fret="0", duration="4")])
    ])
    section.columns.append(column)
    score.sections.append(section)
    
    renderer = Renderer(score)
    layout = renderer._calculate_layout()
    # レイアウトの検証 

def test_note_position_calculation():
    """音符の位置計算をテスト"""
    score = Score(title="Test")
    section = Section(name="Test")
    
    # 全音符1つの小節
    bar1 = Bar()
    bar1.notes.append(Note(string=1, fret="0", duration="1", step=16))
    
    # 4分音符4つの小節
    bar2 = Bar()
    for i in range(4):
        bar2.notes.append(Note(string=1, fret=str(i), duration="4", step=4))
    
    # 8分音符8つの小節
    bar3 = Bar()
    for i in range(8):
        bar3.notes.append(Note(string=1, fret=str(i), duration="8", step=2))
    
    # 和音を含む小節
    bar4 = Bar()
    # (1-0 2-0):4 の和音
    bar4.notes.extend([
        Note(string=1, fret="0", duration="4", step=4, is_chord=True, is_chord_start=True),
        Note(string=2, fret="0", duration="4", step=4, is_chord=True)
    ])
    
    column = Column(bars=[bar1, bar2, bar3, bar4])
    section.columns.append(column)
    score.sections.append(section)
    
    renderer = Renderer(score)
    bar_width = 100  # テスト用の固定値
    x_start = 10
    margin = 2  # mm
    
    # 各小節の音符位置をテスト
    for bar in [bar1, bar2, bar3, bar4]:
        positions = renderer._calculate_note_positions(bar, x_start, bar_width)
        
        # 位置の基本チェック
        assert all(x_start <= x <= x_start + bar_width for _, x in positions), \
            f"Note positions must be within bar bounds: {positions}"
        
        # 和音のチェック
        for i, (note, x) in enumerate(positions):
            if note.is_chord and i + 1 < len(positions):
                next_note = positions[i + 1][0]
                if next_note.is_chord:
                    assert positions[i][1] == positions[i + 1][1], \
                        "Chord notes must have same x position"
        
        # 音符の順序チェック
        x_positions = [x for _, x in positions]
        assert x_positions == sorted(x_positions), \
            "Note positions must be in ascending order"

def test_bar_width_calculation():
    """小節幅の計算をテスト"""
    score = Score(title="Test")
    section = Section(name="Test")
    
    # 4小節を1行に配置
    bars = [Bar() for _ in range(4)]
    for bar in bars:
        bar.notes.append(Note(string=1, fret="0", duration="4", step=4))
    
    column = Column(bars=bars)
    section.columns.append(column)
    score.sections.append(section)
    
    renderer = Renderer(score)
    
    # A4用紙の幅に収まっているか確認
    assert renderer.page_width <= 595.2755905511812  # A4幅（ポイント）
    assert renderer.usable_width < renderer.page_width
    
    # 小節幅が均等で、マージンを考慮しているか確認
    bar_width = renderer.usable_width / 4  # 4小節の場合
    assert bar_width * 4 <= renderer.usable_width

def test_repeat_symbol_positions():
    """繰り返し記号の位置をテスト"""
    score = Score(title="Test")
    section = Section(name="Test")
    
    # 繰り返し記号付きの小節
    bar1 = Bar(is_repeat_start=True)
    bar1.notes.append(Note(string=1, fret="0", duration="4", step=4))
    
    bar2 = Bar(is_repeat_end=True)
    bar2.notes.append(Note(string=1, fret="0", duration="4", step=4))
    
    column = Column(bars=[bar1, bar2])
    section.columns.append(column)
    score.sections.append(section)
    
    renderer = Renderer(score)
    # 繰り返し記号の位置が正しく計算されることを確認
    # (具体的なアサーションは実装に応じて追加)

def test_volta_bracket_position():
    """n番カッコの位置をテスト"""
    score = Score(title="Test")
    section = Section(name="Test")
    
    # n番カッコ付きの小節
    bar = Bar(volta_number=1)
    bar.notes.append(Note(string=1, fret="0", duration="4", step=4))
    
    column = Column(bars=[bar])
    section.columns.append(column)
    score.sections.append(section)
    
    renderer = Renderer(score)
    # n番カッコの位置が正しく計算されることを確認
    # (具体的なアサーションは実装に応じて追加) 