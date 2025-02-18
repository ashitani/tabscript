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
    
    # 基本的なコード
    bar = parser._parse_bar_line("@Cmaj7 3-3:4 4-4:4")
    assert bar.chord == "Cmaj7"
    assert len(bar.notes) == 2
    assert bar.notes[0].string == 3
    assert bar.notes[0].duration == "4"
    assert bar.notes[0].chord == "Cmaj7"  # 最初の音符にコードが付与
    assert bar.notes[1].chord == None # 2番目の音符にはコードは付与されない
    # 小節内でのコード変更
    bar = parser._parse_bar_line("@Am 3-3:4 @Dm 4-4:4")
    assert len(bar.notes) == 2
    assert bar.notes[0].chord == "Am"
    assert bar.notes[1].chord == "Dm"
    
    # 和音にもコードが適用される
    bar = parser._parse_bar_line("@Em (1-0 2-0 3-0):4")
    assert len(bar.notes) == 1  # メインの音符1つ
    main_note = bar.notes[0]
    assert main_note.chord == "Em"
    assert len(main_note.chord_notes) == 2
    
    # シャープ記号を含むコード
    bar = parser._parse_bar_line("@A#m7 3-3:4 4-4:4")
    assert bar.chord == "A#m7"
    assert len(bar.notes) == 2
    assert bar.notes[0].chord == "A#m7"
    assert bar.notes[1].chord == None

    # コードのみの小節
    bar = parser._parse_bar_line("@Am")
    assert bar.chord == "Am"
    assert len(bar.notes) == 0
    
    # 複雑なコード進行
    bar = parser._parse_bar_line("@Am7 3-3:8 @Dm7 4-4:8 @G7 5-5:8 @Cmaj7 6-6:8")
    assert len(bar.notes) == 4
    assert bar.notes[0].chord == "Am7"
    assert bar.notes[1].chord == "Dm7"
    assert bar.notes[2].chord == "G7"
    assert bar.notes[3].chord == "Cmaj7"

    # コードが連続する場合
    bar = parser._parse_bar_line("@Am @Bm 3-3:4")
    assert bar.chord == "Bm"
    assert len(bar.notes) == 1
    assert bar.notes[0].chord == "Bm"

    # コードと和音が混在する場合
    bar = parser._parse_bar_line("@Am (1-0 2-0):4 @Bm 3-3:4")
    assert len(bar.notes) == 2
    assert bar.notes[0].chord == "Am"
    assert bar.notes[1].chord == "Bm"

    # コードと休符が混在する場合
    bar = parser._parse_bar_line("@Am r4 @Bm 3-3:4")
    assert len(bar.notes) == 2
    assert bar.notes[0].chord == "Am"
    assert bar.notes[1].chord == "Bm"

    # コードが小節の最後に指定された場合
    bar = parser._parse_bar_line("3-3:4 @Am")
    assert bar.chord == "Am"
    assert len(bar.notes) == 1
    assert bar.notes[0].chord == None # 小節の最後にコードが指定された場合、音符にはコードは付与されない

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
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 基本的な和音
    bar = parser._parse_bar_line("(1-0 2-0 3-0):4")
    assert len(bar.notes) == 1  # メインの音符1つ
    main_note = bar.notes[0]
    assert main_note.string == 1
    assert main_note.fret == "0"
    assert main_note.duration == "4"
    assert main_note.is_chord
    assert main_note.is_chord_start
    assert len(main_note.chord_notes) == 2  # 残りの2つの音符
    
    # 和音ノートの確認
    assert main_note.chord_notes[0].string == 2
    assert main_note.chord_notes[0].fret == "0"
    assert main_note.chord_notes[0].is_chord
    assert not main_note.chord_notes[0].is_chord_start
    
    assert main_note.chord_notes[1].string == 3
    assert main_note.chord_notes[1].fret == "0"
    assert main_note.chord_notes[1].is_chord
    assert not main_note.chord_notes[1].is_chord_start

    # コード付きの和音
    bar = parser._parse_bar_line("@Am (1-0 2-1 3-2):4")
    assert len(bar.notes) == 1
    main_note = bar.notes[0]
    assert main_note.chord == "Am"
    assert main_note.is_chord
    assert main_note.is_chord_start
    assert len(main_note.chord_notes) == 2

    # ミュート音を含む和音
    bar = parser._parse_bar_line("(1-X 2-0 3-x):4")
    assert len(bar.notes) == 1
    main_note = bar.notes[0]
    assert main_note.is_muted
    assert len(main_note.chord_notes) == 2
    assert main_note.chord_notes[0].fret == "0"
    assert not main_note.chord_notes[0].is_muted
    assert main_note.chord_notes[1].is_muted

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
    assert bar.notes[1].string == 5  # 弦が継承
    assert bar.notes[2].string == 4  # 弦が上移動
    assert bar.notes[2].fret == "2"
    assert bar.notes[3].string == 4  # 弦が継承
    # 下移動
    bar = parser._parse_bar_line("5-5:8 7 d4 5")
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 5
    assert bar.notes[0].fret == "5"
    assert bar.notes[1].string == 5 #弦が継承
    assert bar.notes[2].string == 6 # 弦が下移動
    assert bar.notes[2].fret == "4"
    assert bar.notes[2].string == 6 #弦が継承
    
    # 移動記号と音価の組み合わせ
    bar = parser._parse_bar_line("5-3:8 u2:16 d4:8 5")
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 5
    assert bar.notes[1].string == 4
    assert bar.notes[1].duration == "16"
    assert bar.notes[2].string == 5
    assert bar.notes[2].duration == "8" 
    assert bar.notes[3].string == 5

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

def test_repeat_bar_parsing():
    """繰り返し記号のパースをテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 基本的な繰り返し
    bar_info = parser._analyze_section_bars([
        "{ 1-1:4 2-2:4 }"  # 一行形式
    ])
    
    assert len(bar_info) == 1
    assert bar_info[0].repeat_start == True
    assert bar_info[0].repeat_end == True
    assert bar_info[0].content == "1-1:4 2-2:4"

def test_volta_bracket_parsing():
    """n番カッコのパースをテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # n番カッコの基本的なパース
    bar_info = parser._analyze_section_bars([
        "{ 1-1:4 2-2:4 }",  # 繰り返し開始
        "{1 3-3:4 4-4:4 }1",  # 1番カッコ
        "{2 5-5:4 6-6:4 }2"   # 2番カッコ
    ])
    
    assert len(bar_info) == 3
    # 繰り返しの検証
    assert bar_info[0].repeat_start == True
    assert bar_info[0].repeat_end == True
    # 1番カッコの検証
    assert bar_info[1].volta_number == 1
    assert bar_info[1].volta_start == True
    assert bar_info[1].volta_end == True
    # 2番カッコの検証
    assert bar_info[2].volta_number == 2
    assert bar_info[2].volta_start == True
    assert bar_info[2].volta_end == True

def test_multi_bar_volta_bracket_parsing():
    """複数小節に渡るn番カッコのパースをテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 複数小節のn番カッコ
    bar_info = parser._analyze_section_bars([
        "{ 1-1:4 2-2:4 }",  # 繰り返し開始
        "{1 3-3:4 4-4:4 5-5:4 6-6:4 }1",  # 1番カッコ（2小節分）
        "{2 7-7:4 8-8:4 9-9:4 10-10:4 }2"  # 2番カッコ（2小節分）
    ])
    
    assert len(bar_info) == 3
    # 繰り返しの検証
    assert bar_info[0].repeat_start == True
    assert bar_info[0].repeat_end == True
    # 1番カッコの検証
    assert bar_info[1].volta_number == 1
    assert bar_info[1].volta_start == True
    assert bar_info[1].volta_end == True
    # 2番カッコの検証
    assert bar_info[2].volta_number == 2
    assert bar_info[2].volta_start == True
    assert bar_info[2].volta_end == True 