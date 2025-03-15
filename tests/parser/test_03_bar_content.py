import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError
from tabscript.models import Score

def test_basic_note_parsing(debug_level):
    """基本的な音符のパースをテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 基本的な音符表記
    bar = parser._parse_bar_line("1-0:4 2-2:8 3-3:16 4-4:32")
    
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 1
    assert bar.notes[0].fret == "0"
    assert bar.notes[0].duration == "4"
    assert bar.notes[1].string == 2
    assert bar.notes[1].fret == "2"
    assert bar.notes[1].duration == "8"
    assert bar.notes[2].string == 3
    assert bar.notes[2].fret == "3"
    assert bar.notes[2].duration == "16"
    assert bar.notes[3].string == 4
    assert bar.notes[3].fret == "4"
    assert bar.notes[3].duration == "32"

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
    parser.score = Score(title="", tuning="guitar", beat="4/4")  # スコアを初期化

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

def test_repeat_bar_parsing(debug_level):
    """繰り返し記号のパースをテスト（前処理後の形式）"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 基本的な繰り返し（一行形式）
    bar_info = parser._analyze_section_bars([
        "{ 1-1:4 2-2:4 }"  # 前処理済みの一行形式
    ])
    
    assert len(bar_info) == 1
    assert bar_info[0].repeat_start
    assert bar_info[0].repeat_end
    assert bar_info[0].content == "1-1:4 2-2:4"

def test_volta_bracket_parsing(debug_level):
    """n番カッコのパースをテスト（前処理後の形式）"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # n番カッコの基本的なパース（一行形式）
    bar_info = parser._analyze_section_bars([
        "{ 1-1:4 2-2:4",  # 繰り返し開始と共通部分
        "{1 3-3:4 4-4:4 }1",  # 1番カッコ
        "{2 5-5:4 6-6:4 }2 }"  # 2番カッコと繰り返し終了
    ])
    
    assert len(bar_info) == 3  # 共通部分1小節 + 1番1小節 + 2番1小節
    # 共通部分の検証
    assert bar_info[0].repeat_start == True
    assert not bar_info[0].repeat_end
    # 1番カッコの検証
    assert bar_info[1].volta_number == 1
    assert bar_info[1].volta_start == True
    assert bar_info[1].volta_end == True
    # 2番カッコの検証
    assert bar_info[2].volta_number == 2
    assert bar_info[2].volta_start == True
    assert bar_info[2].volta_end == True
    assert bar_info[2].repeat_end == True

def test_multi_bar_volta_bracket_parsing(debug_level):
    """複数小節に渡るn番カッコのパースをテスト（前処理後の形式）"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 複数小節のn番カッコ（一行形式）
    bar_info = parser._analyze_section_bars([
        "{ 1-1:4 2-2:4",  # 繰り返し開始と共通部分
        "{1 3-3:4 4-4:4 5-5:4 6-6:4 }1",  # 1番カッコ（2小節分）
        "{2 7-7:4 8-8:4 9-9:4 10-10:4 }2 }"  # 2番カッコ（2小節分）と繰り返し終了
    ])
    
    assert len(bar_info) == 3
    # 共通部分の検証
    assert bar_info[0].repeat_start == True
    assert not bar_info[0].repeat_end
    # 1番カッコの検証
    assert bar_info[1].volta_number == 1
    assert bar_info[1].volta_start == True
    assert bar_info[1].volta_end == True
    # 2番カッコの検証
    assert bar_info[2].volta_number == 2
    assert bar_info[2].volta_start == True
    assert bar_info[2].volta_end == True
    assert bar_info[2].repeat_end == True 

def test_string_movement_notation():
    """上下移動記号のテスト"""
    parser = Parser(debug_mode=True)
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    parser.last_string = 3  # 3弦から開始
    
    # 上移動（u）のテスト
    bar = parser._parse_bar_line("u2:4 u3:8")
    assert len(bar.notes) == 2
    
    # 1つ目の音符（u2:4）
    assert bar.notes[0].string == 2  # 3弦から1弦上に移動
    assert bar.notes[0].fret == "2"
    assert bar.notes[0].duration == "4"
    assert bar.notes[0].is_up_move
    
    # 2つ目の音符（u3:8）
    assert bar.notes[1].string == 1  # 2弦から1弦上に移動
    assert bar.notes[1].fret == "3"
    assert bar.notes[1].duration == "8"
    assert bar.notes[1].is_up_move
    
    # 下移動（d）のテスト
    parser.last_string = 2  # 2弦から開始
    bar = parser._parse_bar_line("d3:4 d2:8")
    assert len(bar.notes) == 2
    
    # 1つ目の音符（d3:4）
    assert bar.notes[0].string == 3  # 2弦から1弦下に移動
    assert bar.notes[0].fret == "3"
    assert bar.notes[0].duration == "4"
    assert bar.notes[0].is_down_move
    
    # 2つ目の音符（d2:8）
    assert bar.notes[1].string == 4  # 3弦から1弦下に移動
    assert bar.notes[1].fret == "2"
    assert bar.notes[1].duration == "8"
    assert bar.notes[1].is_down_move
    
    # 音価の省略テスト
    parser.last_string = 3
    parser.last_duration = "4"
    bar = parser._parse_bar_line("u2 d3")
    assert len(bar.notes) == 2
    
    # 1つ目の音符（u2）- 音価は継承
    assert bar.notes[0].string == 2
    assert bar.notes[0].fret == "2"
    assert bar.notes[0].duration == "4"  # 継承された音価
    
    # 2つ目の音符（d3）- 音価は継承
    assert bar.notes[1].string == 3  # 2弦から1弦下に移動
    assert bar.notes[1].fret == "3"
    assert bar.notes[1].duration == "4"  # 継承された音価
    
    # 範囲外の移動テスト
    parser.last_string = 1  # 1弦から開始
    with pytest.raises(ParseError):
        parser._parse_bar_line("u2:4")  # 1弦からさらに上は存在しない
    
    parser.last_string = 6  # 6弦から開始
    with pytest.raises(ParseError):
        parser._parse_bar_line("d2:4")  # 6弦からさらに下は存在しない（標準ギターの場合） 

def test_string_movement_duration_calculation():
    """上下移動記号を含む小節の音価計算のテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    parser.last_string = 5  # 5弦から開始
    
    # 上移動記号を含む小節
    bar = parser._parse_bar_line("5-5:8 7 u4 5 7 u4 6 7")
    
    # 各音符のステップ数を確認
    assert len(bar.notes) == 8
    for note in bar.notes:
        assert note.step == 2  # 各音符は8分音符（2ステップ）
    
    # 小節の長さが4/4拍子に一致することを確認
    total_steps = sum(note.step for note in bar.notes)
    assert total_steps == 16  # 4/4拍子は16ステップ

def test_chord_duration_calculation():
    """和音の音価計算のテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 和音を含む小節の音価計算
    bar = parser._parse_bar_line("@C (1-3 2-5 3-5 4-5 5-3 6-3):4 (1-x 2-x 3-x 4-x 5-x 6-x):4 (1-x 2-x 3-x 4-x 5-x 6-x):4 (1-x 2-x 3-x 4-x 5-x 6-x):4")
    
    # 小節の長さが4/4拍子に一致することを確認
    total_steps = sum(note.step for note in bar.notes)
    assert total_steps == 16  # 4/4拍子は16ステップ
    
    # 各和音の音価が正しいことを確認
    for note in bar.notes:
        assert note.step == 4  # 各和音は4分音符（4ステップ） 

def test_continued_string_movement():
    """弦移動が複数行にまたがる場合のテスト"""
    parser = Parser()
    parser.score = Score(title="", tuning="guitar", beat="4/4")
    
    # 1行目: 5弦から開始して上移動を含む
    bar1 = parser._parse_bar_line("5-3:8 5 u2 3 5 u2 4 5")
    assert len(bar1.notes) == 8
    assert sum(note.step for note in bar1.notes) == 16  # 4/4拍子
    
    # 最後の音符の弦番号を記録
    last_string = bar1.notes[-1].string
    parser.last_string = last_string
    
    # 2行目: 前の行から弦番号を継承
    bar2 = parser._parse_bar_line("5 4 2 d5 3 2 d5 3")
    assert len(bar2.notes) == 8
    assert sum(note.step for note in bar2.notes) == 16  # 4/4拍子
    
    # 最初の音符が前の行の最後の音符の弦番号を継承していることを確認
    assert bar2.notes[0].string == last_string 