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

def test_comment_removal():
    """コメントの除去をテスト"""
    parser = Parser()
    text = """
    # 全行コメント
    $title="Test"  # 行末コメント
    '''
    複数行コメント
    '''
    [Section]
    3-3:4
    """
    cleaned = parser._clean_text(text)
    assert '$title="Test"' in cleaned
    assert '[Section]' in cleaned
    assert '3-3:4' in cleaned
    assert 'コメント' not in cleaned
    assert '複数行コメント' not in cleaned

def test_multiline_comment_edge_cases():
    """複数行コメントの特殊ケースをテスト"""
    parser = Parser()
    text = """
    '''未終了の複数行コメント
    $title="Test"
    """
    cleaned = parser._clean_text(text)
    assert '$title="Test"' not in cleaned

    text = """
    $title="Test"
    ''' コメント ''' $beat="4/4" ''' コメント '''
    [Section]
    """
    cleaned = parser._clean_text(text)
    assert '$title="Test"' in cleaned
    assert '$beat="4/4"' in cleaned
    assert '[Section]' in cleaned 

def test_bracket_normalization():
    """括弧記号の正規化をテスト"""
    parser = Parser()
    
    # 単一番号のn番カッコ
    text = """
    {1
    3-3:4 4-4:4
    1}
    """
    cleaned = parser._clean_text(text)
    assert "{1 3-3:4 4-4:4 }1" in cleaned
    
    # 複数番号のn番カッコ
    text = """
    {1,2
    3-3:4 4-4:4
    1,2}
    """
    cleaned = parser._clean_text(text)
    assert "{1,2 3-3:4 4-4:4 }1,2" in cleaned
    
    # 通常の繰り返し記号
    text = """
    {
    3-3:4 4-4:4
    }
    """
    cleaned = parser._clean_text(text)
    assert "{ 3-3:4 4-4:4 }" in cleaned
    
    # 入れ子のn番カッコはエラー
    text = """
    {1
    {2
    3-3:4
    2}
    1}
    """
    with pytest.raises(ParseError, match="Nested volta brackets are not allowed"):
        parser._clean_text(text) 