def test_repeat_test():
    """繰り返し記号のテスト"""
    # ファイルを読み込んでパース
    parser = Parser()
    score = parser.parse("tests/data/repeat_test.tab")
    
    # 期待される構造をチェック
    assert score.title == "sample"
    assert score.tuning == "guitar"
    assert score.beat == "4/4"
    assert len(score.sections) == 1
    
    section = score.sections[0]
    assert section.name == "Repeat Test"
    assert len(section.columns) == 1
    
    column = section.columns[0]
    assert len(column.bars) == 8  # 4小節 × 2回
    
    # 1番括弧の小節をチェック
    for i in range(4):
        bar = column.bars[i]
        assert len(bar.notes) == 4
        if i == 0:
            assert bar.is_repeat_start
        if i == 3:
            assert bar.is_repeat_end
            assert bar.volta_number == 1
    
    # 2番括弧の小節をチェック
    for i in range(4, 8):
        bar = column.bars[i]
        assert len(bar.notes) == 4
        if i == 4:
            assert bar.is_repeat_start
        if i == 7:
            assert bar.is_repeat_end
            assert bar.volta_number == 2 