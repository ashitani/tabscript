import pytest
from tabscript.parser.analyzer import StructureAnalyzer
from tabscript.exceptions import ParseError

def test_analyze_section_structure():
    """セクション構造の解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4
[Chorus]
1-0:4 2-0:4 3-0:4 4-0:4"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 2
    
    # デフォルトセクションの検証
    assert sections[0]["name"] == ""
    assert len(sections[0]["bars"]) == 1
    assert sections[0]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"
    
    # 名前付きセクションの検証
    assert sections[1]["name"] == "Chorus"
    assert len(sections[1]["bars"]) == 1
    assert sections[1]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"

def test_analyze_section_bars_with_newlines():
    """改行を含むセクションの解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """1-0:4 2-0:4 3-0:4 4-0:4

[Chorus]
1-0:4 2-0:4 3-0:4 4-0:4"""
    
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 2
    
    # デフォルトセクションの検証
    assert sections[0]["name"] == ""
    assert len(sections[0]["bars"]) == 1
    assert sections[0]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"
    
    # 名前付きセクションの検証
    assert sections[1]["name"] == "Chorus"
    assert len(sections[1]["bars"]) == 1
    assert sections[1]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"

def test_analyze_metadata():
    """メタデータの解析をテスト"""
    text = """$title = "テスト曲"
$tuning = "guitar"
$beat = "4/4"
$key = "C"

[Verse]
1-0:4 2-0:4 3-0:4 4-0:4

[Chorus]
1-0:4 2-0:4 3-0:4 4-0:4"""

    analyzer = StructureAnalyzer()
    metadata, sections = analyzer.analyze(text)

    # メタデータの検証
    assert metadata["title"] == "テスト曲"
    assert metadata["tuning"] == "guitar"
    assert metadata["beat"] == "4/4"
    assert metadata["key"] == "C"

    # セクション構造の検証
    assert len(sections) == 2
    assert sections[0]["name"] == "Verse"
    assert sections[1]["name"] == "Chorus"

def test_analyze_metadata_with_quotes():
    """引用符を含むメタデータの解析をテスト"""
    text = """$title = "テスト曲（ギター）"
$tuning = "guitar"
$beat = "4/4"
$key = "C"

[Verse]
1-0:4 2-0:4 3-0:4 4-0:4"""

    analyzer = StructureAnalyzer()
    metadata, sections = analyzer.analyze(text)

    # メタデータの検証
    assert metadata["title"] == "テスト曲（ギター）"
    assert metadata["tuning"] == "guitar"
    assert metadata["beat"] == "4/4"
    assert metadata["key"] == "C"

    # セクション構造の検証
    assert len(sections) == 1
    assert sections[0]["name"] == "Verse" 