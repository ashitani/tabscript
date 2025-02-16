import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError
from tabscript.models import Score

def test_basic_note_parsing():
    """基本的な音符のパースをテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")  # スコアを初期化
    bar = parser._parse_bar_line("3-3:4 4-4:8 5-5:16")
    
    assert len(bar.notes) == 3
    # 1番目の音符
    assert bar.notes[0].string == 3
    assert bar.notes[0].fret == "3"
    assert bar.notes[0].duration == "4"
    assert bar.notes[0].step == 4
    # 2番目の音符
    assert bar.notes[1].string == 4
    assert bar.notes[1].duration == "8"
    assert bar.notes[1].step == 2
    # 3番目の音符
    assert bar.notes[2].duration == "16"
    assert bar.notes[2].step == 1

def test_chord_parsing():
    """コード名のパースをテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")  # スコアを初期化
    bar = parser._parse_bar_line("@Cmaj7 3-3:4 4-4:4")
    
    assert bar.chord == "Cmaj7"
    assert len(bar.notes) == 2
    assert bar.notes[0].string == 3
    assert bar.notes[0].duration == "4"

def test_rest_parsing():
    """休符のパースをテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")  # スコアを初期化
    bar = parser._parse_bar_line("3-3:4 r4 5-5:4")
    
    assert len(bar.notes) == 3
    assert bar.notes[1].is_rest
    assert bar.notes[1].duration == "4"
    assert bar.notes[1].step == 4

def test_duration_inheritance():
    """音価の継承をテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")  # スコアを初期化
    bar = parser._parse_bar_line("3-3:8 4-4 5-5 6-6")
    
    assert len(bar.notes) == 4
    assert all(note.duration == "8" for note in bar.notes)
    assert all(note.step == 2 for note in bar.notes)

def test_dotted_duration():
    """付点音符のパースをテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")  # スコアを初期化
    bar = parser._parse_bar_line("3-3:4. 4-4:8.")
    
    assert bar.notes[0].duration == "4."
    assert bar.notes[0].step == 6  # 4分音符(4) + 8分音符(2)
    assert bar.notes[1].duration == "8."
    assert bar.notes[1].step == 3  # 8分音符(2) + 16分音符(1)

def test_invalid_note_format():
    """不正な音符形式をテスト"""
    parser = Parser()

    with pytest.raises(ParseError, match="Invalid fret number"):
        parser._parse_bar_line("3-A:4")  # 不正なフレット番号（アルファベット）

    with pytest.raises(ParseError, match="Invalid fret number"):
        parser._parse_bar_line("3-#:4")  # 不正なフレット番号（記号）

    with pytest.raises(ParseError, match="Invalid fret number"):
        parser._parse_bar_line("3-12.5:4")  # 不正なフレット番号（小数）

def test_muted_note():
    """ミュート音のパースをテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")  # スコアを初期化
    bar = parser._parse_bar_line("3-X:4 4-x:4")
    
    assert len(bar.notes) == 2
    assert bar.notes[0].is_muted
    assert bar.notes[0].fret == "X"
    assert bar.notes[1].is_muted
    assert bar.notes[1].fret == "X"

def test_chord_notation():
    """和音記法のテスト"""
    parser = Parser()
    parser.debug_mode = True  # デバッグ出力を有効化
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 基本的な和音
    bar = parser._parse_bar_line("(1-0 2-0 3-0):4")
    assert len(bar.notes) == 3
    assert bar.notes[0].string == 1
    assert bar.notes[0].fret == "0"
    assert bar.notes[0].duration == "4"
    assert bar.notes[1].string == 2
    assert bar.notes[2].string == 3
    
    # 音価の省略
    bar = parser._parse_bar_line("(1-0 2-0)")  # 前の音価を継承
    assert len(bar.notes) == 2
    assert bar.notes[0].duration == "4"
    assert bar.notes[1].duration == "4"
    
    # 複数の和音
    bar = parser._parse_bar_line("(1-0 2-0):4 (3-0 4-0):8")
    assert len(bar.notes) == 4
    assert bar.notes[0].duration == "4"
    assert bar.notes[1].duration == "4"
    assert bar.notes[2].duration == "8"
    assert bar.notes[3].duration == "8"

def test_inheritance():
    """弦番号と音価の継承をテスト"""
    parser = Parser()
    parser.debug_mode = True
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 弦番号の継承
    bar = parser._parse_bar_line("6-1 2 3 4")
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 6
    assert bar.notes[0].fret == "1"
    assert bar.notes[1].string == 6  # 前の音符から弦番号を継承
    assert bar.notes[1].fret == "2"
    assert bar.notes[2].string == 6
    assert bar.notes[2].fret == "3"
    assert bar.notes[3].string == 6
    assert bar.notes[3].fret == "4"
    
    # 音価の継承
    bar = parser._parse_bar_line("6-1:8 2 3 4")
    assert len(bar.notes) == 4
    assert bar.notes[0].duration == "8"
    assert bar.notes[1].duration == "8"  # 前の音符から音価を継承
    assert bar.notes[2].duration == "8"
    assert bar.notes[3].duration == "8"
    
    # 弦番号と音価の両方を継承
    bar = parser._parse_bar_line("6-1:8 2 5-3 4")
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 6
    assert bar.notes[0].duration == "8"
    assert bar.notes[1].string == 6  # 6弦を継承
    assert bar.notes[1].duration == "8"  # 8分音符を継承
    assert bar.notes[2].string == 5  # 新しい弦番号
    assert bar.notes[2].duration == "8"  # 8分音符を継承
    assert bar.notes[3].string == 5  # 5弦を継承
    assert bar.notes[3].duration == "8"  # 8分音符を継承 

def test_move_notation():
    """移動記号のパースをテスト"""
    parser = Parser()
    parser.debug_mode = True
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 上移動
    bar = parser._parse_bar_line("5-3:8 5 u2 3")
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 5
    assert bar.notes[0].fret == "3"
    assert not bar.notes[0].is_up_move
    assert bar.notes[2].string == 5  # 弦番号を継承
    assert bar.notes[2].fret == "2"
    assert bar.notes[2].is_up_move
    assert not bar.notes[2].is_down_move
    
    # 下移動
    bar = parser._parse_bar_line("5-5:8 7 d4 5")
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 5
    assert bar.notes[0].fret == "5"
    assert not bar.notes[0].is_down_move
    assert bar.notes[2].string == 5  # 弦番号を継承
    assert bar.notes[2].fret == "4"
    assert bar.notes[2].is_down_move
    assert not bar.notes[2].is_up_move
    
    # 移動記号と音価の組み合わせ
    bar = parser._parse_bar_line("5-3:8 u2:16 d4:8 5")
    assert len(bar.notes) == 4
    assert bar.notes[1].is_up_move
    assert bar.notes[1].duration == "16"
    assert bar.notes[2].is_down_move
    assert bar.notes[2].duration == "8" 

def test_tie_slur_notation():
    """タイ・スラー記法のテスト"""
    parser = Parser()
    parser.debug_mode = True
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 音符にタイ・スラー
    bar = parser._parse_bar_line("4-3& 5")
    assert len(bar.notes) == 2
    assert bar.notes[0].string == 4
    assert bar.notes[0].fret == "3"
    assert bar.notes[0].connect_next
    assert not bar.notes[1].connect_next
    
    # 音価にタイ・スラー
    bar = parser._parse_bar_line("4-3:8& 5:4")
    assert len(bar.notes) == 2
    assert bar.notes[0].duration == "8"
    assert bar.notes[0].connect_next
    assert not bar.notes[1].connect_next
    
    # 複数のタイ・スラー
    bar = parser._parse_bar_line("4-3:8& 3-5& 2-3& 5")
    assert len(bar.notes) == 4
    assert bar.notes[0].connect_next
    assert bar.notes[1].connect_next
    assert bar.notes[2].connect_next
    assert not bar.notes[3].connect_next 