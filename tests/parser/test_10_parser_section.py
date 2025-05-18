import pytest
from tabscript.parser.analyzer import StructureAnalyzer
from tabscript.exceptions import ParseError

def test_analyze_section_bars_basic():
    """基本的なセクションの解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = '''1-0:4 2-0:4 3-0:4 4-0:4
$section="Chorus"
1-0:4 2-0:4 3-0:4 4-0:4'''
    metadata, sections = analyzer.analyze(text)
    # 2つのセクションが存在すること
    assert len(sections) == 2
    # 最初のセクションはデフォルトセクション
    assert sections[0]["name"] == ""
    assert len(sections[0]["bars"]) == 1
    assert sections[0]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"
    # 2番目のセクションは"Chorus"
    assert sections[1]["name"] == "Chorus"
    assert len(sections[1]["bars"]) == 1
    assert sections[1]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"

def test_analyze_section_bars_with_newlines():
    """改行を含むセクションの解析をテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = '''1-0:4 2-0:4 3-0:4 4-0:4
    
$section="Chorus"
1-0:4 2-0:4 3-0:4 4-0:4'''
    metadata, sections = analyzer.analyze(text)
    # 2つのセクションが存在すること
    assert len(sections) == 2
    # 最初のセクションはデフォルトセクション
    assert sections[0]["name"] == ""
    assert len(sections[0]["bars"]) == 1
    assert sections[0]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"
    # 2番目のセクションは"Chorus"
    assert sections[1]["name"] == "Chorus"
    assert len(sections[1]["bars"]) == 1
    assert sections[1]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"

def test_invalid_metadata():
    """不正なメタデータ形式でエラーが発生するかテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """$title=Test Song
$section="Section1"
1-0:4 2-0:4 3-0:4 4-0:4
"""
    with pytest.raises(ParseError):
        analyzer.analyze(text)

def test_code_line_not_metadata():
    """@で始まる行がメタデータとして誤認されないことをテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """$title="コードテスト"
$tuning="guitar"
$section="Main"
@C 5-3 4-2 3-0 2-1
@G 6-3 5-2 4-0 3-0
"""
    metadata, sections = analyzer.analyze(text)
    # メタデータが正しく取得できていること
    assert metadata["title"] == "コードテスト"
    assert metadata["tuning"] == "guitar"
    # セクションが1つ
    assert len(sections) == 1
    # 小節内容として@Cや@Gが含まれていること
    bars = sections[0]["bars"]
    assert any("@C" in bar.content for bar in bars)
    assert any("@G" in bar.content for bar in bars)

def test_code_line_parsing():
    """コード表記を含む小節が正しくパースされることをテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = """$title="コードパーステスト"
$tuning="guitar"
$section="Main"
@C 5-3 4-2 3-0 2-1
@G 6-3 5-2 4-0 3-0
"""
    metadata, sections = analyzer.analyze(text)
    assert len(sections) == 1
    bars = sections[0]["bars"]
    # コード表記を含む小節が正しくパースされているか
    assert any("@C 5-3 4-2 3-0 2-1" in bar.content for bar in bars)
    assert any("@G 6-3 5-2 4-0 3-0" in bar.content for bar in bars)

def test_parse_triplet_tab_like():
    analyzer = StructureAnalyzer()
    text = '''$title="sample"
$tuning="guitar"
$beat="4/4"
$bars_per_line="4"

$section="A"
[ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3 [ 4-2 4-4 3-2 ]3'''
    metadata, sections = analyzer.analyze(text)
    assert metadata["title"] == "sample"
    assert metadata["tuning"] == "guitar"
    assert len(sections) == 1
    assert sections[0]["name"] == "A"
    assert len(sections[0]["bars"]) == 4

def test_parse_samples_tab_like():
    analyzer = StructureAnalyzer()
    text = '''$title="sample"
$tuning="guitar"
$beat="4/4"
$bars_per_line="4"

$section="4 notes"
6-1 2 3 4
5-1 2 3 4

$section="8 notes"
6-1:8 2 3 4 5-1 2 3 4
5-1 2 3 4 4-1 2 3 4
'''
    metadata, sections = analyzer.analyze(text)
    assert metadata["title"] == "sample"
    assert len(sections) == 2
    assert sections[0]["name"] == "4 notes"
    assert sections[1]["name"] == "8 notes"
    assert len(sections[0]["bars"]) == 2
    assert len(sections[1]["bars"]) == 2

def test_parse_repeat_sample_tab_like():
    analyzer = StructureAnalyzer()
    text = '''$title="sample"
$tuning="guitar"
$beat="4/4"
$bars_per_line="4"

$section="Repeat"
{
@C 5-3:8 4-2 3-0 2-1
@G 6-3 5-2 4-0 3-0
{1
@C 1-3 2-5 3-5 4-5
@G 6-3 5-2 4-0 3-0
 1-3 2-3 3-5 4-5
1}
{2
@G  1-3 2-3 3-5 4-5
2}
}'''
    metadata, sections = analyzer.analyze(text)
    assert metadata["title"] == "sample"
    assert len(sections) == 1
    assert sections[0]["name"] == "Repeat"
    assert len(sections[0]["bars"]) > 0

def test_parse_chord_test_tab_like():
    analyzer = StructureAnalyzer()
    text = '''$title="chord test"
$tuning="guitar"
$beat="4/4"
$bars_per_line="4"

$section="A"
@C (1-3 2-5 3-5 4-5 5-3 6-3):4 (1-x 2-x 3-x 4-x 5-x 6-x) (1-x 2-x 3-x 4-x 5-x 6-x) (1-x 2-x 3-x 4-x 5-x 6-x)'''
    metadata, sections = analyzer.analyze(text)
    assert metadata["title"] == "chord test"
    assert len(sections) == 1
    assert sections[0]["name"] == "A"
    assert len(sections[0]["bars"]) == 1

def test_default_section():
    """$section=が現れる前の小節がデフォルトセクションとして追加されることをテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = '''1-0:4 2-0:4 3-0:4 4-0:4
$section="Chorus"
1-0:4 2-0:4 3-0:4 4-0:4'''
    metadata, sections = analyzer.analyze(text)
    # 2つのセクションが存在すること
    assert len(sections) == 2
    # 最初のセクションはデフォルトセクション
    assert sections[0]["name"] == ""
    assert len(sections[0]["bars"]) == 1
    assert sections[0]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"
    # 2番目のセクションは"Chorus"
    assert sections[1]["name"] == "Chorus"
    assert len(sections[1]["bars"]) == 1
    assert sections[1]["bars"][0].content == "1-0:4 2-0:4 3-0:4 4-0:4"

def test_multiple_sections():
    """複数のセクションが正しく解析されることをテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = '''1-0:4 2-0:4
$section="Verse"
3-0:4 4-0:4
$section="Chorus"
5-0:4 6-0:4'''
    metadata, sections = analyzer.analyze(text)
    # 3つのセクションが存在すること
    assert len(sections) == 3
    # デフォルトセクション
    assert sections[0]["name"] == ""
    assert len(sections[0]["bars"]) == 1
    # Verseセクション
    assert sections[1]["name"] == "Verse"
    assert len(sections[1]["bars"]) == 1
    # Chorusセクション
    assert sections[2]["name"] == "Chorus"
    assert len(sections[2]["bars"]) == 1

def test_empty_default_section():
    """$section=が最初に現れる場合は空のデフォルトセクションが作成されないことをテスト"""
    analyzer = StructureAnalyzer(debug_mode=True)
    text = '''$section="Verse"
1-0:4 2-0:4'''
    metadata, sections = analyzer.analyze(text)
    # 1つのセクションのみ存在すること
    assert len(sections) == 1
    assert sections[0]["name"] == "Verse"
    assert len(sections[0]["bars"]) == 1 