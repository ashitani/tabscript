import os
import pytest
from tabscript.parser import Parser
from tabscript.models import Score, Section, Column, Bar, Note
from tabscript.exceptions import ParseError, TabScriptError

# テスト用のファイルパス
TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def test_parse_simple_file():
    """シンプルなTabScriptファイルをパースできることを確認"""
    # テスト用のTabScriptテキスト
    tabscript_text = """
    $title = "シンプルな例"
    $tuning = "guitar"
    $beat = "4/4"
    
    [イントロ]
    1-0:4 1-2:4 2-0:4 2-2:4
    3-0:4 3-2:4 4-0:4 4-2:4
    
    [Aメロ]
    1-0:8 1-2:8 1-3:8 1-5:8 2-0:8 2-2:8 2-3:8 2-5:8
    """
    
    # パース
    parser = Parser()
    score = parser.parse(tabscript_text)
    
    # 検証
    assert score.title == "シンプルな例"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"
    
    # セクション数の確認
    assert len(score.sections) == 2
    assert score.sections[0].name == "イントロ"
    assert score.sections[1].name == "Aメロ"
    
    # イントロセクションの確認
    intro_section = score.sections[0]
    assert len(intro_section.columns) == 1
    assert len(intro_section.columns[0].bars) == 2
    
    # Aメロセクションの確認
    verse_section = score.sections[1]
    assert len(verse_section.columns) == 1
    assert len(verse_section.columns[0].bars) == 1
    
    # 小節内の音符数の確認
    assert len(intro_section.columns[0].bars[0].notes) == 4
    assert len(intro_section.columns[0].bars[1].notes) == 4
    assert len(verse_section.columns[0].bars[0].notes) == 8

def test_parse_with_repeat_marks():
    """繰り返し記号付きの譜面をパースするテスト"""
    tabscript = """
    $title="Test Score"
    $tuning="guitar"
    
    [Section A]
    { 1-0:4 1-2:4 2-0:4 2-2:4 }
    """
    
    parser = Parser(debug_mode=True)
    score = parser.parse(tabscript)
    
    assert score.title == "Test Score"
    assert score.tuning == "guitar"
    
    # セクションの確認
    assert len(score.sections) == 1
    section_a = score.sections[0]
    assert section_a.name == "Section A"
    
    # 小節の確認
    assert len(section_a.columns) == 1
    assert len(section_a.columns[0].bars) == 1
    
    # 繰り返し記号の確認
    bar = section_a.columns[0].bars[0]
    assert bar.is_repeat_start
    assert bar.is_repeat_end
    
    # 音符の確認
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 1
    assert bar.notes[0].fret == "0"
    assert bar.notes[0].duration == "4"


def test_repeat_symbols_not_as_notes():
    """繰り返し記号が音符としてパースされないことをテスト"""
    # 繰り返し記号を含む簡単なタブ譜
    tab_content = """
    $title="Repeat Test"
    $tuning="guitar"
    $beat="4/4"

    [Test]
    {
    1-1:4 2-2:4
    }
    """
    
    # 一時ファイルに書き出して処理
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tab', delete=False) as f:
        f.write(tab_content)
        temp_file = f.name
    
    parser = Parser()
    score = parser.parse(temp_file)
    
    # 全ての音符のfret属性をチェック
    for section in score.sections:
        for column in section.columns:
            for bar in column.bars:
                for note in bar.notes:
                    # 音符のfret属性に繰り返し記号が含まれていないことを確認
                    assert note.fret != '{', "繰り返し開始記号'{'が音符としてパースされています"
                    assert note.fret != '}', "繰り返し終了記号'}'が音符としてパースされています"
    
    # 代わりに繰り返し記号は小節の属性として設定されているはず
    test_section = score.sections[0]
    assert len(test_section.columns) > 0, "カラムが存在しません"
    
    # 各小節の繰り返し記号フラグをチェック
    first_column = test_section.columns[0]
    assert len(first_column.bars) > 0, "小節が存在しません"
    
    # 少なくとも1つの小節がis_repeat_start=Trueであること
    assert any(bar.is_repeat_start for bar in test_section.get_all_bars()), "繰り返し開始フラグが設定されていません"
    
    # 少なくとも1つの小節がis_repeat_end=Trueであること
    assert any(bar.is_repeat_end for bar in test_section.get_all_bars()), "繰り返し終了フラグが設定されていません"


def test_volta_bracket_not_as_notes():
    """n番括弧が音符としてパースされないことをテスト"""
    # n番括弧を含むタブ譜
    tab_content = """
    $title="Volta Test"
    $tuning="guitar"
    $beat="4/4"

    [Test]
    {
    1-1:4 2-2:4
    
    {1
    3-3:4 4-4:4
    1}
    
    {2
    5-5:4 6-6:4
    2}
    }
    """
    
    parser = Parser()
    score = parser.parse(tab_content)
    
    # 全ての音符のfret属性をチェック
    for section in score.sections:
        for column in section.columns:
            for bar in column.bars:
                for note in bar.notes:
                    # 音符のfret属性にn番括弧が含まれていないことを確認
                    assert note.fret != '{1', "n番括弧開始記号'{1'が音符としてパースされています"
                    assert note.fret != '1}', "n番括弧終了記号'1}'が音符としてパースされています"
                    assert note.fret != '{2', "n番括弧開始記号'{2'が音符としてパースされています"
                    assert note.fret != '2}', "n番括弧終了記号'2}'が音符としてパースされています"
    
    # n番括弧は小節の属性として設定されているはず
    test_section = score.sections[0]
    
    # volta_numberが1と2の小節が存在することを確認
    all_bars = test_section.get_all_bars()
    volta_numbers = [bar.volta_number for bar in all_bars if bar.volta_number is not None]
    assert 1 in volta_numbers, "volta_number=1の小節が存在しません"
    assert 2 in volta_numbers, "volta_number=2の小節が存在しません"
    
    # volta_startとvolta_endフラグも確認
    assert any(bar.volta_start and bar.volta_number == 1 for bar in all_bars), "volta_start=True, volta_number=1の小節が存在しません"
    assert any(bar.volta_end and bar.volta_number == 1 for bar in all_bars), "volta_end=True, volta_number=1の小節が存在しません"
    assert any(bar.volta_start and bar.volta_number == 2 for bar in all_bars), "volta_start=True, volta_number=2の小節が存在しません"
    assert any(bar.volta_end and bar.volta_number == 2 for bar in all_bars), "volta_end=True, volta_number=2の小節が存在しません"


def test_repeat_test_tab_file():
    """repeat_test.tabファイルで繰り返し記号のパースをテスト"""
    parser = Parser()
    score = parser.parse("tests/data/repeat_test.tab")
    
    # 繰り返し記号がfretに含まれていないことを確認
    repeat_symbols = ['{', '}', '{1', '1}', '{2', '2}']
    
    for section in score.sections:
        for column in section.columns:
            for bar in column.bars:
                for note in bar.notes:
                    assert note.fret not in repeat_symbols, f"繰り返し記号'{note.fret}'が音符としてパースされています" 

def test_parse_with_string_movement():
    """弦移動記号を含むTabScriptファイルをパースできることを確認"""
    tabscript_text = """
    $title = "弦移動のテスト"
    $tuning = "guitar"
    
    [テスト]
    3-0:4 u2:4 d3:4 d1:4
    """
    
    # パース
    parser = Parser()
    score = parser.parse(tabscript_text)
    
    # 検証
    assert score.title == "弦移動のテスト"
    assert score.tuning == "guitar"
    
    assert len(score.sections) == 1
    section = score.sections[0]
    assert section.name == "テスト"
    
    assert len(section.columns) == 1
    bar = section.columns[0].bars[0]
    
    assert len(bar.notes) == 4
    assert bar.notes[0].string == 3
    assert bar.notes[0].fret == "0"
    
    assert bar.notes[1].is_up_move
    assert bar.notes[1].string == 2  # 3弦から1弦上の2弦
    assert bar.notes[1].fret == "2"  # フレット番号は2
    
    assert bar.notes[2].is_down_move
    assert bar.notes[2].string == 3  # 2弦から1弦下の3弦
    assert bar.notes[2].fret == "3"  # フレット番号は3
    
    assert bar.notes[3].is_down_move
    assert bar.notes[3].string == 4  # 3弦から1弦下の4弦
    assert bar.notes[3].fret == "1"  # フレット番号は1

def test_parse_with_chord_notation():
    """コード記法を含むTabScriptファイルをパースできることを確認"""
    tabscript_text = """
    $title = "コード記法のテスト"
    $tuning = "guitar"
    
    [テスト]
    (1-0 2-2 3-2 4-2 5-0 6-0):4 (1-3 2-3 3-0 4-0 5-2 6-3):4
    """
    
    # パース
    parser = Parser()
    score = parser.parse(tabscript_text)
    
    # 検証
    section = score.sections[0]
    bar = section.columns[0].bars[0]
    
    # 修正: コードは個別のノートではなく、和音ノート2つ
    assert len(bar.notes) == 2  # 2つの和音
    
    # 和音の内部構造を検証
    assert bar.notes[0].is_chord
    assert bar.notes[0].is_chord_start
    assert len(bar.notes[0].chord_notes) == 5  # 主音以外に5音
    
    assert bar.notes[1].is_chord
    assert bar.notes[1].is_chord_start
    assert len(bar.notes[1].chord_notes) == 5  # 主音以外に5音

def test_parse_with_connect():
    """接続記号(&)を含むTabScriptファイルをパースできることを確認"""
    tabscript_text = """
    $title = "接続記号のテスト"
    $tuning = "guitar"
    
    [テスト]
    1-0:4& 1-0:4 2-2:4& 3-4:4
    """
    
    # パース
    parser = Parser()
    score = parser.parse(tabscript_text)
    
    # 検証
    section = score.sections[0]
    bar = section.columns[0].bars[0]
    
    # 接続記号の確認
    assert len(bar.notes) == 4
    assert bar.notes[0].connect_next == True
    assert bar.notes[1].connect_next == False
    assert bar.notes[2].connect_next == True
    assert bar.notes[3].connect_next == False

def test_parse_with_rest_and_muted():
    """休符とミュート音符を含むTabScriptファイルをパースできることを確認"""
    tabscript_text = """
    $title = "休符とミュートのテスト"
    $tuning = "guitar"
    
    [テスト]
    r:4 1-x:4 r:8 2-x:8 3-0:4
    """
    
    # パース
    parser = Parser()
    score = parser.parse(tabscript_text)
    
    # 検証
    assert score.title == "休符とミュートのテスト"
    assert score.tuning == "guitar"
    
    assert len(score.sections) == 1
    section = score.sections[0]
    assert section.name == "テスト"
    
    assert len(section.columns) == 1
    bar = section.columns[0].bars[0]
    
    assert len(bar.notes) == 5
    assert bar.notes[0].is_rest
    assert bar.notes[0].duration == "4"
    assert bar.notes[1].string == 1
    assert bar.notes[1].is_muted
    assert bar.notes[2].is_rest
    assert bar.notes[2].duration == "8"
    assert bar.notes[3].string == 2
    assert bar.notes[3].is_muted
    assert bar.notes[4].string == 3
    assert bar.notes[4].fret == "0"

def test_parse_from_file():
    """実際のファイルからパースできることを確認"""
    # テスト用のファイルパス
    file_path = os.path.join(TEST_FILES_DIR, "sample.tab")
    
    # ファイルが存在しない場合はスキップ
    if not os.path.exists(file_path):
        pytest.skip(f"テストファイル {file_path} が見つかりません")
    
    # パース
    parser = Parser()
    score = parser.parse(file_path)
    
    # 基本的な検証
    assert isinstance(score, Score)
    assert len(score.sections) > 0

def test_complex_score():
    """複雑なスコアをパースできることを確認"""
    tabscript_text = """
    $title = "複雑なスコア"
    $tuning = "guitar"
    $beat = "4/4"
    $bars_per_line = "2"
    
    [イントロ]
    {
    1-0:8 1-2:8 1-3:8 1-5:8 2-0:8 2-2:8 2-3:8 2-5:8
    3-0:8 3-2:8 3-3:8 3-5:8 4-0:8 4-2:8 4-3:8 4-5:8
    }
    
    [Aメロ]
    {1
    1-0:4 1-2:4 2-0:4 2-2:4
    3-0:4 3-2:4 4-0:4 4-2:4
    1}
    {2
    1-3:4 1-5:4 2-3:4 2-5:4
    3-3:4 3-5:4 4-3:4 4-5:4
    2}
    
    [Bメロ]
    (1-0 2-2 3-2 4-2 5-0 6-0):4 (1-3 2-3 3-0 4-0 5-2 6-3):4
    (1-2 2-0 3-0 4-0 5-2 6-3):4 (1-0 2-2 3-2 4-2 5-0 6-0):4
    """
    
    # パース
    parser = Parser()
    score = parser.parse(tabscript_text)
    
    # 検証
    assert score.title == "複雑なスコア"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"
    
    # セクション数の確認
    assert len(score.sections) == 3
    
    # イントロセクションの確認
    intro_section = score.sections[0]
    assert intro_section.name == "イントロ"
    assert len(intro_section.columns) == 1
    assert len(intro_section.columns[0].bars) == 2
    assert intro_section.columns[0].bars[0].is_repeat_start == True
    assert intro_section.columns[0].bars[1].is_repeat_end == True
    
    # Aメロセクションの確認
    verse_a_section = score.sections[1]
    assert verse_a_section.name == "Aメロ"
    assert len(verse_a_section.columns) == 2  # bars_per_line=2なので2カラムになるはず
    
    # テスト通過後のデバッグ出力
    print(f"TEST SUCCESS: verse_a_section columns={len(verse_a_section.columns)}")
    for i, column in enumerate(verse_a_section.columns):
        print(f"Column {i}: bars={len(column.bars)}")
        for j, bar in enumerate(column.bars):
            print(f"  Bar {j}: volta_number={bar.volta_number}, start={bar.volta_start}, end={bar.volta_end}")
    
    # Bメロセクションの確認
    verse_b_section = score.sections[2]
    assert verse_b_section.name == "Bメロ"
    assert len(verse_b_section.columns) == 1
    assert len(verse_b_section.columns[0].bars) == 2
    
    # コードの確認
    assert len(verse_b_section.columns[0].bars[0].notes) == 2  # 2つのコード（各6音）
    assert len(verse_b_section.columns[0].bars[1].notes) == 2  # 2つのコード（各6音）
