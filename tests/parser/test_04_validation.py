import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError
from tabscript.models import Score, Bar, Note
from fractions import Fraction

def test_bar_duration_validation(debug_level):
    """小節の長さ検証をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 正しい長さの小節（4/4拍子で全音符1つ）
    bar = Bar()
    note = Note(string=1, fret="0", duration="1")
    note.step = Fraction(4)  # 全音符は4ステップ
    bar.notes.append(note)
    
    # 全音符は4/4拍子で正しい長さ
    assert parser._validate_bar_duration(bar) == True
    
    # 短すぎる小節（4/4拍子で2分音符1つ）
    bar = Bar()
    note = Note(string=1, fret="0", duration="2")
    note.step = Fraction(2)  # 2分音符は2ステップ
    bar.notes.append(note)
    
    # 2分音符は4/4拍子で短すぎる
    assert parser._validate_bar_duration(bar) == False
    
    # 長すぎる小節（4/4拍子で全音符+4分音符）
    bar = Bar()
    note1 = Note(string=1, fret="0", duration="1")
    note1.step = Fraction(4)  # 全音符は4ステップ
    note2 = Note(string=1, fret="0", duration="4")
    note2.step = Fraction(1)  # 4分音符は1ステップ
    bar.notes.extend([note1, note2])
    
    # 全音符+4分音符は4/4拍子で長すぎる
    assert parser._validate_bar_duration(bar) == False

def test_string_number_validation(debug_level):
    """弦番号の検証をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 有効な弦番号（ギター: 1-6）
    for string in range(1, 7):
        bar = Bar()
        bar.notes.append(Note(string=string, fret="0", duration="4"))
        # エラーが発生しないこと
        assert parser._validate_string_number(string) == True
    
    # 弦番号0は休符として有効
    assert parser._validate_string_number(0) == True
    
    # 無効な弦番号（ギター: 7以上）
    with pytest.raises(ParseError, match="Invalid string number"):
        parser._validate_string_number(7)

def test_fret_number_validation(debug_level):
    """フレット番号の検証をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 有効なフレット番号（0-24, x）
    for fret in range(0, 25):
        assert parser._validate_fret_number(str(fret)) == True
    
    assert parser._validate_fret_number("x") == True
    
    # 無効なフレット番号（負の数、25以上、文字）
    with pytest.raises(ParseError, match="Invalid fret number"):
        parser._validate_fret_number("-1")
    
    with pytest.raises(ParseError, match="Invalid fret number"):
        parser._validate_fret_number("25")
    
    with pytest.raises(ParseError, match="Invalid fret number"):
        parser._validate_fret_number("a")

def test_duration_validation(debug_level):
    """音価の検証をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 有効な音価（1, 2, 4, 8, 16, 32, 64, 付点付き）
    valid_durations = ["1", "2", "4", "8", "16", "32", "64", 
                       "1.", "2.", "4.", "8.", "16.", "32."]
    for duration in valid_durations:
        assert parser._validate_duration(duration) == True
    
    # 無効な音価
    invalid_durations = ["0", "3", "5", "128", "a", "4..", "..4"]
    for duration in invalid_durations:
        with pytest.raises(ParseError, match="Invalid duration"):
            parser._validate_duration(duration)

def test_beat_validation(debug_level):
    """拍子記号の検証をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 有効な拍子記号
    valid_beats = ["4/4", "3/4", "6/8", "5/4", "7/8", "12/8"]
    for beat in valid_beats:
        assert parser._validate_beat(beat) == True
    
    # 無効な拍子記号
    invalid_beats = ["4", "4/", "/4", "a/4", "4/a", "0/4", "4/0", "-1/4"]
    for beat in invalid_beats:
        with pytest.raises(ParseError, match="Invalid beat"):
            parser._validate_beat(beat)

def test_tuning_validation(debug_level):
    """チューニングの検証をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 有効なチューニング
    valid_tunings = ["guitar", "bass", "ukulele", "guitar7", "bass5"]
    for tuning in valid_tunings:
        assert parser._validate_tuning(tuning) == True
    
    # 無効なチューニング
    invalid_tunings = ["guitar8", "bass6", "piano", "violin"]
    for tuning in invalid_tunings:
        with pytest.raises(ParseError, match="Invalid tuning"):
            parser._validate_tuning(tuning)

def test_skip_validation(debug_level):
    """検証スキップのテスト"""
    # 検証をスキップするパーサー
    parser = Parser(debug_mode=True, debug_level=debug_level, skip_validation=True)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 長すぎる小節でもエラーにならない
    bar = Bar()
    for _ in range(5):  # 4/4拍子で4分音符5つ（長すぎる）
        bar.notes.append(Note(string=1, fret="0", duration="4"))
    
    # skip_validation=Trueなのでエラーにならない
    parser._validate_bar_duration(bar)

def test_chord_notation_duration():
    """コード形式の音符の長さ検証をテスト"""
    parser = Parser(debug_mode=True, debug_level=3)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # コード形式の音符（全音符）
    bar = Bar()
    
    # コード形式の音符を作成
    main_note = Note(string=1, fret="2", duration="1")
    main_note.is_chord = True
    main_note.is_chord_start = True
    main_note.step = Fraction(4)  # 全音符は4ステップ
    
    # コードの他の音符
    chord_notes = [
        Note(string=2, fret="4", duration="1", is_chord=True, step=Fraction(4)),
        Note(string=3, fret="4", duration="1", is_chord=True, step=Fraction(4)),
        Note(string=4, fret="4", duration="1", is_chord=True, step=Fraction(4)),
        Note(string=5, fret="2", duration="1", is_chord=True, step=Fraction(4)),
        Note(string=6, fret="2", duration="1", is_chord=True, step=Fraction(4))
    ]
    
    main_note.chord_notes = chord_notes
    bar.notes.append(main_note)
    bar.notes.extend(chord_notes)  # 和音の他の音符も追加
    
    # コード形式の音符は全音符（4/4拍子で正しい長さ）
    assert parser._validate_bar_duration(bar) == True 