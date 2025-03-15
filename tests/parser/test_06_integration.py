import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError

def test_complete_score(debug_level):
    """完全なスコアのパースをテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level, skip_validation=True)
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
    {
    1-1:4 2-2:4
    {1
    3-3:4 4-4:4
    1}
    {2
    5-5:4 6-6:4
    2}
    }
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
    # 小節数は2だが、カラム数はbars_per_lineに依存
    assert len(intro.bars) == 2
    assert intro.bars[0].chord == "Am"
    assert intro.bars[1].chord == "Dm7"

    # Aセクションの検証（繰り返し）
    section_a = score.sections[1]
    assert section_a.name == "A"
    assert len(section_a.bars) == 1
    bar = section_a.bars[0]
    assert bar.is_repeat_start
    assert bar.is_repeat_end

    # Bセクション（n番カッコ）の検証
    section_b = score.sections[2]
    assert section_b.name == "B"
    # 小節数は3（共通部分1小節 + 1番1小節 + 2番1小節）
    assert len(section_b.bars) == 3
    
    # 共通部分の検証
    assert section_b.bars[0].is_repeat_start
    
    # 1番カッコの検証
    assert section_b.bars[1].volta_number == 1
    assert section_b.bars[1].volta_start
    assert section_b.bars[1].volta_end
    
    # 2番カッコの検証
    assert section_b.bars[2].volta_number == 2
    assert section_b.bars[2].volta_start
    assert section_b.bars[2].volta_end
    
    # 繰り返し終了の検証
    assert section_b.bars[2].is_repeat_end

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
    parser = Parser(skip_validation=True)
    score = parser.parse("tests/data/sample.tab")
    
    # 基本的な検証
    assert score.title == "Test song"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"
    
    # セクションの検証
    assert len(score.sections) == 2
    assert score.sections[0].name == "Intro"
    assert score.sections[1].name == "A"

def test_repeat_test():
    """繰り返し記号のテスト"""
    parser = Parser(skip_validation=True)
    score = parser.parse("tests/data/repeat_test.tab")
    
    # 期待される構造をチェック
    assert score.title == "sample"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"
    assert len(score.sections) == 1
    
    section = score.sections[0]
    assert section.name == "Repeat Test"
    
    # 複数行にまたがるn番カッコを処理するため、Columnが複数になる
    assert len(section.columns) == 2  # 1から2に変更
    
    # 小節数の検証（共通部分1小節 + 1番カッコ3小節 + 2番カッコ3小節）
    assert len(section.bars) == 7
    
    # 共通部分の検証
    assert section.bars[0].is_repeat_start
    assert not section.bars[0].is_repeat_end
    
    # 1番カッコの小節をチェック
    for i in range(1, 4):  # 1-3小節目
        assert section.bars[i].volta_number == 1
        if i == 1:
            assert section.bars[i].volta_start
        if i == 3:
            assert section.bars[i].volta_end
    
    # 2番カッコの小節をチェック
    for i in range(4, 7):  # 4-6小節目
        assert section.bars[i].volta_number == 2
        if i == 4:
            assert section.bars[i].volta_start
        if i == 6:
            assert section.bars[i].volta_end
            assert section.bars[i].is_repeat_end  # 最後の小節は繰り返し終了も兼ねる 