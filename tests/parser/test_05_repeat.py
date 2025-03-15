import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError
import tempfile
import os

def test_repeat_basic():
    """基本的な繰り返し記号のテスト"""
    parser = Parser(skip_validation=True)
    score = parser.parse("""
    $title="Repeat Test"
    $tuning="guitar"
    $beat="4/4"
    
    [A]
    {
    1-1:4 2-2:4
    }
    """)
    
    assert len(score.sections) == 1
    section = score.sections[0]
    assert len(section.bars) == 1
    
    # 繰り返し記号の検証
    bar = section.bars[0]
    assert bar.is_repeat_start
    assert bar.is_repeat_end
    assert bar.volta_number is None

def test_repeat_separate_brackets():
    """開始と終了が別々の繰り返し記号のテスト"""
    parser = Parser(skip_validation=True)
    score = parser.parse("""
    $title="Repeat Test"
    $tuning="guitar"
    $beat="4/4"
    
    [A]
    {
    1-1:4 2-2:4
    3-3:4 4-4:4
    }
    """)
    
    assert len(score.sections) == 1
    section = score.sections[0]
    assert len(section.bars) == 2
    
    # 繰り返し開始の検証
    assert section.bars[0].is_repeat_start
    assert not section.bars[0].is_repeat_end
    
    # 繰り返し終了の検証
    assert not section.bars[1].is_repeat_start
    assert section.bars[1].is_repeat_end

def test_volta_brackets():
    """n番カッコのテスト"""
    parser = Parser(skip_validation=True)
    score = parser.parse("""
    $title="Volta Test"
    $tuning="guitar"
    $beat="4/4"
    
    [A]
    {1
    1-1:4 2-2:4
    1}
    
    {2
    3-3:4 4-4:4
    2}
    """)
    
    assert len(score.sections) == 1
    section = score.sections[0]
    assert len(section.bars) == 2
    
    # 1番カッコの検証
    assert section.bars[0].volta_number == 1
    assert section.bars[0].volta_start
    assert section.bars[0].volta_end
    
    # 2番カッコの検証
    assert section.bars[1].volta_number == 2
    assert section.bars[1].volta_start
    assert section.bars[1].volta_end

def test_repeat_with_volta():
    """繰り返し記号とn番カッコの組み合わせテスト"""
    parser = Parser(skip_validation=True)
    score = parser.parse("""
    $title="Repeat with Volta"
    $tuning="guitar"
    $beat="4/4"
    
    [A]
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
    
    assert len(score.sections) == 1
    section = score.sections[0]
    assert len(section.bars) == 3  # 共通部分1小節 + 1番1小節 + 2番1小節
    
    # 共通部分の検証
    assert section.bars[0].is_repeat_start
    assert not section.bars[0].is_repeat_end
    
    # 1番カッコの検証
    assert section.bars[1].volta_number == 1
    assert section.bars[1].volta_start
    assert section.bars[1].volta_end
    
    # 2番カッコの検証
    assert section.bars[2].volta_number == 2
    assert section.bars[2].volta_start
    assert section.bars[2].volta_end
    
    # 繰り返し終了の検証
    assert section.bars[2].is_repeat_end

def test_complex_repeat_structure():
    """複雑な繰り返し構造のテスト"""
    parser = Parser(skip_validation=True)
    score = parser.parse("""
    $title="Complex Repeat"
    $tuning="guitar"
    $beat="4/4"
    
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
    assert score.title == "Complex Repeat"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"
    
    # セクション数の検証
    assert len(score.sections) == 3
    
    # Introセクションの検証
    intro = score.sections[0]
    assert intro.name == "Intro"
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

# 以下、新しく追加するテスト

def test_repeat_end_only():
    """繰り返し終了のみの小節のテスト"""
    parser = Parser(skip_validation=True)
    score = parser.parse("""
    $title="Repeat End Only"
    $tuning="guitar"
    $beat="4/4"
    
    [A]
    {
    1-1:4 2-2:4
    3-3:4 4-4:4
    }
    """)
    
    assert len(score.sections) == 1
    section = score.sections[0]
    assert len(section.bars) == 2
    
    # 繰り返し開始の検証
    assert section.bars[0].is_repeat_start
    assert not section.bars[0].is_repeat_end
    
    # 繰り返し終了の検証
    assert not section.bars[1].is_repeat_start
    assert section.bars[1].is_repeat_end

def test_multi_bar_volta():
    """複数小節にまたがるn番カッコのテスト"""
    parser = Parser(skip_validation=True)
    score = parser.parse("""
    $title="Multi-bar Volta"
    $tuning="guitar"
    $beat="4/4"
    
    [A]
    {
    1-1:4 2-2:4 3-3:4 4-4:4
    
    {1
    5-5:4 6-6:4 5-5:4 4-4:4
    3-3:4 4-4:4 5-5:4 6-6:4
    1-1:4 2-2:4 3-3:4 4-4:4
    1}
    
    {2
    6-6:4 5-5:4 4-4:4 3-3:4
    2-2:4 3-3:4 4-4:4 5-5:4
    1-1:4 2-2:4 3-3:4 4-4:4
    2}
    }
    """)
    
    assert len(score.sections) == 1
    section = score.sections[0]
    
    # 小節数の検証（共通部分1小節 + 1番3小節 + 2番3小節）
    assert len(section.bars) == 7
    
    # 共通部分の検証
    assert section.bars[0].is_repeat_start
    assert not section.bars[0].is_repeat_end
    
    # 1番カッコの検証（3小節）
    for i in range(1, 4):
        assert section.bars[i].volta_number == 1
        if i == 1:
            assert section.bars[i].volta_start
        if i == 3:
            assert section.bars[i].volta_end
    
    # 2番カッコの検証（3小節）
    for i in range(4, 7):
        assert section.bars[i].volta_number == 2
        if i == 4:
            assert section.bars[i].volta_start
        if i == 6:
            assert section.bars[i].volta_end
            assert section.bars[i].is_repeat_end  # 最後の小節は繰り返し終了も兼ねる

def test_file_parsing():
    """ファイルからのパースをテスト"""
    # テスト用の一時ファイルを作成
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.tab', delete=False) as f:
        f.write("""
$title="File Test"
$tuning="guitar"
$beat="4/4"

[Test]
1-1:4 2-2:4 3-3:4 4-4:4
5-5:4 6-6:4 5-5:4 4-4:4
""")
        temp_file = f.name
    
    try:
        # ファイルからパース
        parser = Parser(skip_validation=True)
        score = parser.parse(temp_file)
        
        # 基本的な検証
        assert score.title == "File Test"
        assert score.tuning == "guitar"
        assert score.beat == "4/4"
        assert len(score.sections) == 1
        assert score.sections[0].name == "Test"
        assert len(score.sections[0].bars) == 2
    finally:
        # 一時ファイルを削除
        os.unlink(temp_file)

def test_bar_duration_skip_validation():
    """小節の長さ検証をスキップするテスト"""
    # 不完全な小節（4/4拍子なのに2拍分しかない）
    parser = Parser(skip_validation=True)
    score = parser.parse("""
    $title="Skip Validation"
    $tuning="guitar"
    $beat="4/4"
    
    [Test]
    1-1:4 2-2:4  # 2拍分しかない（4拍必要）
    """)
    
    # 検証をスキップしているので、エラーにならずにパースできる
    assert len(score.sections) == 1
    assert len(score.sections[0].bars) == 1
    assert len(score.sections[0].bars[0].notes) == 2 