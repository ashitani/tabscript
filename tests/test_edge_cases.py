import pytest
from tabscript.parser import Parser
from tabscript.exceptions import ParseError

def test_chord_changes():
    """小節内でのコード変更をテスト"""
    parser = Parser()
    score = parser.parse("""
    [Test]
    @Cmaj7 3-3:4 @Dm7 4-5:4
    """)
    
    bar = score.sections[0].columns[0].bars[0]
    assert bar.notes[0].chord == "Cmaj7"
    assert bar.notes[1].chord == "Dm7"


@pytest.mark.parametrize("invalid_input,expected_error", [
    ("3-x:x", "Invalid duration: x"),
    ("@Cmaj7 3-3:3", "Invalid note duration"),
    ("3-3:4 4-4 5-5 3-3 2-2", "Bar duration exceeds time signature"),
 ])
def test_invalid_inputs(invalid_input, expected_error):
    """様々な不正入力に対するエラー処理をテスト"""
    parser = Parser()
    with pytest.raises(ParseError, match=expected_error):
        parser.parse(f"""
        [Test]
        {invalid_input}
        """)


@pytest.mark.parametrize("time_sig,invalid_input,expected_error", [
    # 3/4拍子のテスト
    ("3/4", "3-3:4 4-4 5-5 6-6", "Bar duration exceeds time signature"),  # 4分音符4つ（4/4相当）
    ("3/4", "3-3:8 4-4 5-5 6-6 3-3 4-4 5-5", "Bar duration exceeds time signature"),  # 8分音符7つ（3.5/4相当）
    
    # 6/8拍子のテスト
    ("6/8", "3-3:4 4-4 5-5 6-6", "Bar duration exceeds time signature"),  # 4分音符4つ（8/8相当）
    ("6/8", "3-3:8 4-4 5-5 6-6 3-3 4-4 5-5", "Bar duration exceeds time signature"),  # 8分音符7つ（7/8相当）
])
def test_time_signature_limits(time_sig, invalid_input, expected_error):
    """異なる拍子記号での小節の長さ制限をテスト"""
    parser = Parser()
    with pytest.raises(ParseError, match=expected_error):
        parser.parse(f"""
        $beat="{time_sig}"
        
        [Test]
        {invalid_input}
        """)


def test_valid_bar_lengths():
    """正しい長さの小節が受け入れられることをテスト"""
    parser = Parser()
    
    # 3/4拍子での正しい長さ
    score = parser.parse("""
    $beat="3/4"
    
    [Test]
    3-3:4 4-4 5-5  # 4分音符3つ（ちょうど3/4）
    """)
    assert len(score.sections[0].columns[0].bars[0].notes) == 3
    
    # 6/8拍子での正しい長さ
    score = parser.parse("""
    $beat="6/8"
    
    [Test]
    3-3:8 4-4 5-5 6-6 3-3 6-6  # 8分音符6つ（ちょうど6/8）
    """)
    assert len(score.sections[0].columns[0].bars[0].notes) == 6