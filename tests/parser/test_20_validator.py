import pytest
# from src.tabscript.parser.validator import TabScriptValidator
from tabscript.parser.validator import TabScriptValidator  # srcを削除
from tabscript.exceptions import ParseError  # srcを削除
from fractions import Fraction

def test_duration_validation():
    """音価の検証テスト"""
    validator = TabScriptValidator()
    
    # 有効な音価
    assert validator.validate_duration("4") is True
    assert validator.validate_duration("8") is True
    assert validator.validate_duration("16") is True
    assert validator.validate_duration("4.") is True  # 付点音符
    
    # 無効な音価
    with pytest.raises(ParseError, match="Invalid duration"):
        validator.validate_duration("3")
    with pytest.raises(ParseError, match="Invalid duration"):
        validator.validate_duration("5")
    with pytest.raises(ParseError, match="Invalid duration"):
        validator.validate_duration("4..")  # 二重付点は無効

def test_bar_duration_validation():
    """小節の長さ検証テスト"""
    validator = TabScriptValidator()
    
    # 4/4拍子の場合
    validator.beat = "4/4"
    
    # 正しい長さの小節
    assert validator.validate_bar_duration("4/4", Fraction(4)) is True  # 4分音符4つ
    assert validator.validate_bar_duration("4/4", Fraction(2) + Fraction(1) + Fraction(1)) is True  # 2分音符1つと4分音符2つ
    
    # 長さが足りない小節
    with pytest.raises(ParseError, match="Bar duration is too short"):
        validator.validate_bar_duration("4/4", Fraction(3))  # 4分音符3つ
    
    # 長すぎる小節
    with pytest.raises(ParseError, match="Bar duration is too long"):
        validator.validate_bar_duration("4/4", Fraction(5))  # 4分音符5つ
    
    # 3/4拍子の場合
    validator.beat = "3/4"
    assert validator.validate_bar_duration("3/4", Fraction(3)) is True  # 4分音符3つ
    with pytest.raises(ParseError, match="Bar duration is too long"):
        validator.validate_bar_duration("3/4", Fraction(4))  # 4分音符4つ

def test_chord_notation_duration():
    """和音の音価検証テスト"""
    validator = TabScriptValidator()
    
    # 有効な和音表記
    assert validator.validate_chord_notation("(1-0 2-0 3-0):4") is True
    assert validator.validate_chord_notation("(1-0 2-0):8") is True
    
    # 無効な和音表記
    with pytest.raises(ParseError, match="Invalid chord notation"):
        validator.validate_chord_notation("(1-0 2-0 3-0")  # 閉じ括弧がない
    with pytest.raises(ParseError, match="Invalid chord notation"):
        validator.validate_chord_notation("1-0 2-0 3-0):4")  # 開き括弧がない
    with pytest.raises(ParseError, match="Invalid duration"):
        validator.validate_chord_notation("(1-0 2-0 3-0):3")  # 無効な音価

def test_beat_validation():
    """拍子記号の検証テスト"""
    validator = TabScriptValidator()
    
    # 有効な拍子記号
    assert validator.validate_beat("4/4") is True
    assert validator.validate_beat("3/4") is True
    assert validator.validate_beat("6/8") is True
    
    # 無効な拍子記号
    with pytest.raises(ParseError, match="Invalid beat"):
        validator.validate_beat("5/4")  # 未サポートの拍子
    with pytest.raises(ParseError, match="Invalid beat format"):
        validator.validate_beat("4-4")  # 形式が不正
    with pytest.raises(ParseError, match="Invalid beat format"):
        validator.validate_beat("four/four")  # 数字でない

def test_tuning_validation():
    """チューニングの検証テスト"""
    validator = TabScriptValidator()
    
    # 有効なチューニング
    assert validator.validate_tuning("guitar") is True
    assert validator.validate_tuning("bass") is True
    assert validator.validate_tuning("ukulele") is True
    
    # 無効なチューニング
    with pytest.raises(ParseError, match="Invalid tuning"):
        validator.validate_tuning("violin")  # サポートされていないチューニング

def test_string_number_validation():
    """弦番号の検証テスト"""
    validator = TabScriptValidator()
    
    # ギターの場合（6弦）
    validator.tuning = "guitar"
    assert validator.validate_string_number(1) is True
    assert validator.validate_string_number(6) is True
    with pytest.raises(ParseError, match="Invalid string number"):
        validator.validate_string_number(7)  # 6弦ギターで7弦は無効
    
    # ベースの場合（4弦）
    validator.tuning = "bass"
    assert validator.validate_string_number(1) is True
    assert validator.validate_string_number(4) is True
    with pytest.raises(ParseError, match="Invalid string number"):
        validator.validate_string_number(5)  # 4弦ベースで5弦は無効

def test_fret_number_validation():
    """フレット番号の検証テスト"""
    validator = TabScriptValidator()
    
    # 有効なフレット番号
    assert validator.validate_fret_number("0") is True  # 開放弦
    assert validator.validate_fret_number("12") is True  # 12フレット
    assert validator.validate_fret_number("24") is True  # 24フレット
    assert validator.validate_fret_number("X") is True  # ミュート
    assert validator.validate_fret_number("x") is True  # ミュート（小文字）
    
    # 無効なフレット番号
    with pytest.raises(ParseError, match="Invalid fret number"):
        validator.validate_fret_number("-1")  # 負の値
    with pytest.raises(ParseError, match="Invalid fret number"):
        validator.validate_fret_number("a")  # 数字でもXでもない
