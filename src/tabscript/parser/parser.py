def parse(self, text: str) -> Score:
    """TabScriptテキストをパースしてスコアに変換
    
    Args:
        text: TabScriptテキスト
    
    Returns:
        Score: パースされたスコアオブジェクト
    """
    # 前処理フェーズ
    preprocessed_text = self.preprocessor.preprocess(text)
    
    # 構造解析フェーズ
    analyzer = StructureAnalyzer(self.debug_mode)
    try:
        metadata, sections = analyzer.analyze(preprocessed_text)
    except Exception as e:
        # エラーが ParseError の場合はそのまま投げる
        if isinstance(e, ParseError):
            raise e
        # その他の例外は ParseError に変換
        raise ParseError(str(e))
    
    # スコア構築フェーズ
    builder = ScoreBuilder(self.debug_mode)
    score = builder.build_score(metadata, sections)
    
    # バリデーションフェーズ
    validator = Validator(self.debug_mode)
    validator.validate(score)
    
    return score

def parse_string(self, text: str) -> Score:
    """parse メソッドの別名 (テスト用)
    
    Args:
        text: パースするタブ譜のテキスト
        
    Returns:
        Score: パース結果のスコアオブジェクト
    """
    return self.parse(text) 