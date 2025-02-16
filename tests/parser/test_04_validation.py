import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError

def test_bar_duration():
    """小節の長さの検証"""
    parser = Parser()
    
    # 正しい長さの小節
    score = parser.parse("""
    [Test]
    3-3:4 4-4:4 5-5:4 6-6:4
    """)
    bar = score.sections[0].columns[0].bars[0]
    total_steps = sum(note.step for note in bar.notes)
    assert total_steps == 16  # 4/4拍子なら16ステップ
    
    # 長すぎる小節
    with pytest.raises(ParseError, match="Bar duration exceeds time signature"):
        parser.parse("""
        [Test]
        3-3:4 4-4:4 5-5:4 6-6:4 1-1:4
        """)

def test_time_signature_validation():
    """拍子記号との整合性をテスト"""
    parser = Parser()
    
    # 3/4拍子での検証
    score = parser.parse("""
    $beat="3/4"
    [Test]
    3-3:4 4-4:4 5-5:4
    """)
    bar = score.sections[0].columns[0].bars[0]
    total_steps = sum(note.step for note in bar.notes)
    assert total_steps == 12  # 3/4拍子なら12ステップ
    
    # 6/8拍子での検証
    score = parser.parse("""
    $beat="6/8"
    [Test]
    3-3:8 4-4:8 5-5:8 6-6:8 1-1:8 2-2:8
    """)
    bar = score.sections[0].columns[0].bars[0]
    total_steps = sum(note.step for note in bar.notes)
    assert total_steps == 12  # 6/8拍子なら12ステップ

def test_repeat_validation():
    """繰り返し記号の妥当性をテスト"""
    parser = Parser()
    
    # 空の繰り返しはエラー
    with pytest.raises(ParseError, match="Empty repeat bracket"):
        parser.parse("""
        [Test]
        {
        }
        """)
    
    # 終了記号のない繰り返しはエラー
    with pytest.raises(ParseError, match="Unclosed repeat bracket"):
        parser.parse("""
        [Test]
        {
        3-3:4
        """)

def test_volta_validation():
    """n番カッコの妥当性をテスト"""
    parser = Parser()
    
    # n番号の不一致はエラー
    with pytest.raises(ParseError, match="Mismatched volta bracket numbers"):
        parser.parse("""
        [Test]
        {1
        3-3:4
        2}
        """)
    
    # 入れ子のn番カッコはエラー
    with pytest.raises(ParseError, match="Nested volta brackets are not allowed"):
        parser.parse("""
        [Test]
        {1
        {2
        3-3:4
        2}
        1}
        """)

def test_string_number_validation():
    """弦番号の妥当性をテスト"""
    parser = Parser()
    
    # 不正な弦番号（ギターの場合）
    with pytest.raises(ParseError, match="Invalid string number"):
        parser.parse("""
        [Test]
        7-0:4
        """)
    
    # ベースの場合は4弦まで
    with pytest.raises(ParseError, match="Invalid string number"):
        parser.parse("""
        $tuning="bass"
        [Test]
        5-0:4
        """) 