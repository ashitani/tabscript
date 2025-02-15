from tabscript.parser import Parser

def test_comment_preprocessing():
    """コメント除去の前処理をテスト"""
    parser = Parser()
    parser.debug_mode = True  # デバッグ出力を有効化
    
    # 単一行コメントのテスト（行頭のみ）
    input_text = """
    # これはコメント
    [Section]
    # これもコメント
    3-3:4 4-4 # これは行末コメントだが残る
    @A#m7 5-5:4  # これも残る
    """
    processed = parser._preprocess_text(input_text)
    print("\nProcessed text:")
    print(processed)
    assert "[Section]" in processed
    assert "3-3:4 4-4 # これは行末コメントだが残る" in processed
    assert "@A#m7 5-5:4  # これも残る" in processed
    assert "これはコメント" not in processed
    assert "これもコメント" not in processed

    # 複数行コメントのテスト
    input_text = """
    [Section A]
    '''
    これは複数行
    コメントです
    '''
    3-3:4 @A#m7 4-4  # コードに#を含む
    """
    processed = parser._preprocess_text(input_text)
    print("\nProcessed text (multiline):")
    print(processed)
    assert "[Section A]" in processed
    assert "3-3:4 @A#m7 4-4  # コードに#を含む" in processed
    assert "これは複数行" not in processed
    assert "コメントです" not in processed

    # 複数の複数行コメントのテスト
    input_text = """
    [Section A]
    '''
    コメント1
    '''
    3-3:4
    '''
    コメント2
    '''
    4-4:4
    """
    processed = parser._preprocess_text(input_text)
    assert "[Section A]" in processed
    assert "3-3:4" in processed
    assert "4-4:4" in processed
    assert "コメント1" not in processed
    assert "コメント2" not in processed

    # ダブルクォートの複数行コメントのテスト
    input_text = '''
    [Section]
    """
    これもコメント
    """
    3-3:4
    '''
    processed = parser._preprocess_text(input_text)
    assert "[Section]" in processed
    assert "3-3:4" in processed
    assert "これもコメント" not in processed 