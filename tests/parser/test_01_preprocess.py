import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError

def test_empty_line_removal():
    """空行の除去をテスト"""
    parser = Parser()
    text = """

    $title="Test"

    [Section]

    3-3:4

    """
    cleaned = parser._clean_text(text)
    lines = cleaned.split('\n')
    assert len(lines) == 3
    assert lines[0] == '$title="Test"'
    assert lines[1] == '[Section]'
    assert lines[2] == '3-3:4'

def test_comment_removal(debug_level):
    """コメント除去のテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 行コメント
    text = """
    # これはコメント
    $title="Test"  # 行末コメント
    [Section]
    1-1:4 2-2:4  # 音符の後のコメント
    """
    
    result = parser._preprocess_text(text)
    assert "$title=\"Test\"" in result
    assert "[Section]" in result
    assert "1-1:4 2-2:4" in result
    assert "これはコメント" not in result
    assert "行末コメント" not in result
    assert "音符の後のコメント" not in result

def test_multiline_comment(debug_level):
    """複数行コメントのテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 複数行コメント（シングルクォート）
    text = """
    $title="Test"
    '''
    これは複数行コメント
    無視されるべき
    '''
    [Section]
    1-1:4 2-2:4
    """
    
    result = parser._preprocess_text(text)
    assert "$title=\"Test\"" in result
    assert "[Section]" in result
    assert "1-1:4 2-2:4" in result
    assert "これは複数行コメント" not in result
    assert "無視されるべき" not in result
    
    # 複数行コメント（ダブルクォート）
    text = """
    $title="Test"
    \"\"\"
    これは複数行コメント
    無視されるべき
    \"\"\"
    [Section]
    1-1:4 2-2:4
    """
    
    result = parser._preprocess_text(text)
    assert "$title=\"Test\"" in result
    assert "[Section]" in result
    assert "1-1:4 2-2:4" in result
    assert "これは複数行コメント" not in result
    assert "無視されるべき" not in result

def test_repeat_bracket_normalization(debug_level):
    """繰り返し括弧の正規化テスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 複数行の繰り返し括弧
    text = """
    [Section]
    {
    1-1:4 2-2:4
    3-3:4 4-4:4
    }
    """
    
    result = parser._normalize_repeat_brackets(text)
    assert "[Section]" in result
    assert "{ 1-1:4 2-2:4" in result
    assert "3-3:4 4-4:4 }" in result

def test_volta_bracket_normalization(debug_level):
    """n番括弧の正規化テスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 複数行のn番括弧
    text = """
    [Section]
    {
    1-1:4 2-2:4
    {1
    3-3:4 4-4:4
    }1
    {2
    5-5:4 6-6:4
    }2
    }
    """
    
    result = parser._normalize_volta_brackets(text)
    assert "[Section]" in result
    assert "{ 1-1:4 2-2:4" in result
    assert "{1 3-3:4 4-4:4 }1" in result
    assert "{2 5-5:4 6-6:4 }2" in result
    assert " }" in result

def test_empty_repeat_bracket(debug_level):
    """空の繰り返し括弧のテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 空の繰り返し括弧
    text = """
    [Section]
    {
    }
    """
    
    with pytest.raises(Exception, match="Empty repeat bracket"):
        parser._normalize_repeat_brackets(text)

def test_unclosed_repeat_bracket(debug_level):
    """閉じられていない繰り返し括弧のテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 閉じられていない繰り返し括弧
    text = """
    [Section]
    {
    1-1:4 2-2:4
    """
    
    with pytest.raises(Exception, match="Unclosed repeat bracket"):
        parser._normalize_repeat_brackets(text)

def test_unclosed_volta_bracket(debug_level):
    """閉じられていないn番括弧のテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 閉じられていないn番括弧
    text = """
    [Section]
    {
    1-1:4 2-2:4
    {1
    3-3:4 4-4:4
    """
    
    with pytest.raises(Exception, match="Unclosed volta bracket"):
        parser._normalize_volta_brackets(text)

def test_mismatched_volta_numbers(debug_level):
    """n番括弧の番号不一致のテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # n番括弧の番号不一致
    text = """
    [Section]
    {
    1-1:4 2-2:4
    {1
    3-3:4 4-4:4
    }2
    }
    """
    
    with pytest.raises(ParseError, match="Mismatched volta bracket numbers"):
        parser._normalize_volta_brackets(text)

def test_clean_text_does_not_normalize_brackets():
    """clean_textは括弧の正規化をしない"""
    parser = Parser()
    text = """
    {
    1-1:4 2-2:4
    }
    """
    cleaned = parser._clean_text(text)
    assert cleaned == """{
1-1:4 2-2:4
}"""

def test_normalize_volta_brackets(debug_level):
    """n番カッコの正規化をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    text = """
    {1
    1-1:4 2-2:4
    1}
    """
    
    expected = "{1 1-1:4 2-2:4 }1"
    
    result = parser._normalize_volta_brackets(text)
    assert expected in result

def test_normalize_repeat_brackets(debug_level):
    """繰り返し記号の正規化をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    text = """
    {
    1-1:4 2-2:4
    }
    """
    
    expected = "{ 1-1:4 2-2:4 }"
    
    result = parser._normalize_repeat_brackets(text)
    assert expected in result

def test_extract_structure(debug_level):
    """構造抽出をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    text = """
    $title="Test Score"
    $tuning="guitar"
    $beat="4/4"
    
    [Intro]
    1-1:4 2-2:4
    3-3:4 4-4:4
    
    [Verse]
    5-5:4 6-6:4
    """
    
    structure = parser._extract_structure(text)
    
    # メタデータの検証
    assert structure.metadata["title"] == "Test Score"
    assert structure.metadata["tuning"] == "guitar"
    assert structure.metadata["beat"] == "4/4"
    
    # セクションの検証
    assert len(structure.sections) == 2
    assert structure.sections[0].name == "Intro"
    assert len(structure.sections[0].content) == 2
    assert "1-1:4 2-2:4" in structure.sections[0].content[0]
    
    assert structure.sections[1].name == "Verse"
    assert len(structure.sections[1].content) == 1
    assert "5-5:4 6-6:4" in structure.sections[1].content[0]

def test_analyze_section_bars(debug_level):
    """小節解析をテスト"""
    parser = Parser(debug_mode=True, debug_level=debug_level)
    
    # 基本的な小節
    content = ["1-1:4 2-2:4", "3-3:4 4-4:4"]
    bar_infos = parser._analyze_section_bars(content)
    
    assert len(bar_infos) == 2
    assert bar_infos[0].content == "1-1:4 2-2:4"
    assert not bar_infos[0].repeat_start
    assert not bar_infos[0].repeat_end
    
    # 繰り返し記号付きの小節
    content = ["{ 1-1:4 2-2:4 }", "3-3:4 4-4:4"]
    bar_infos = parser._analyze_section_bars(content)
    
    assert len(bar_infos) == 2
    assert bar_infos[0].content == "1-1:4 2-2:4"
    assert bar_infos[0].repeat_start
    assert bar_infos[0].repeat_end
    
    # n番カッコ付きの小節
    content = ["{1 1-1:4 2-2:4 }1", "{2 3-3:4 4-4:4 }2"]
    bar_infos = parser._analyze_section_bars(content)
    
    assert len(bar_infos) == 2
    assert bar_infos[0].content == "1-1:4 2-2:4"
    assert bar_infos[0].volta_number == 1
    assert bar_infos[0].volta_start
    assert bar_infos[0].volta_end
    
    assert bar_infos[1].content == "3-3:4 4-4:4"
    assert bar_infos[1].volta_number == 2
    assert bar_infos[1].volta_start
    assert bar_infos[1].volta_end 