import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError

def test_complete_score():
    """完全なスコアのパースをテスト"""
    parser = Parser()
    score = parser.parse("""
    $title="Complete Test"
    $tuning="guitar"
    $beat="4/4"
    $bars_per_line="2"

    [Intro]
    @Am 3-3:4 4-4:4
    @Dm7 5-5:4 6-6:4

    [A]
    {
    1-1:8 2-2:8 3-3:4
    }

    [B]
    {1
    3-3:4 4-4:4
    1}
    {2
    5-5:4 6-6:4
    2}
    """)

    # メタデータの検証
    assert score.title == "Complete Test"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"

    # セクション数の検証
    assert len(score.sections) == 3
    
    # Introセクションの検証
    intro = score.sections[0]
    assert intro.name == "Intro"
    assert len(intro.columns) == 1
    assert len(intro.columns[0].bars) == 2
    assert intro.columns[0].bars[0].chord == "Am"
    assert intro.columns[0].bars[1].chord == "Dm7"

    # Aセクションの検証（繰り返し）
    section_a = score.sections[1]
    assert section_a.name == "A"
    assert len(section_a.columns) == 1
    bar = section_a.columns[0].bars[0]
    assert bar.is_repeat_start
    assert bar.is_repeat_end

    # Bセクション（n番カッコ）の検証
    section_b = score.sections[2]
    assert section_b.name == "B"
    assert len(section_b.columns) == 1
    assert len(section_b.columns[0].bars) == 2
    assert section_b.columns[0].bars[0].volta_number == 1
    assert section_b.columns[0].bars[1].volta_number == 2

def test_error_cases():
    """様々なエラーケースの統合テスト"""
    parser = Parser()
    
    # 不正なメタデータ + 不正な小節長
    with pytest.raises(ParseError, match="Invalid metadata format"):
        parser.parse("""
        $title=Test
        [Section]
        3-3:4 4-4:4 5-5:4 6-6:4 1-1:4
        """)
    
    # 不正な繰り返し + 不正な弦番号
    with pytest.raises(ParseError, match="Empty repeat bracket"):
        parser.parse("""
        [Section]
        {
        }
        7-0:4
        """)
    
    # 不正なn番カッコ + 不正な音価
    with pytest.raises(ParseError, match="Mismatched volta bracket numbers"):
        parser.parse("""
        [Section]
        {1
        3-3:x
        2}
        """)

def test_sample_tab():
    """サンプルタブ譜ファイルのテスト"""
    parser = Parser()
    score = parser.parse("tests/data/sample.tab")

    assert score.title == "Test song"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"
    assert len(score.sections) == 2
    
    # Introセクションの検証
    intro = score.sections[0]
    assert intro.name == "Intro"
    assert len(intro.columns) == 1
    assert len(intro.columns[0].bars) == 2
    assert intro.columns[0].bars[0].chord == "B"
    
    # Aセクションの検証
    section_a = score.sections[1]
    assert section_a.name == "A"
    assert len(section_a.columns) == 1
    assert len(section_a.columns[0].bars) == 4 