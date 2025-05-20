from reportlab.lib.units import mm

class StyleManager:
    """スタイル設定を管理するクラス"""
    
    # デフォルトのスタイル設定
    DEFAULT_STYLES = {
        # ページ設定
        "page_width": 210 * mm,
        "page_height": 297 * mm,
        "margin": 20 * mm,
        "margin_bottom": 20 * mm,
        
        # タイトル設定
        "title_font": "Helvetica-Bold",
        "title_size": 16,
        "title_margin_bottom": 5 * mm,
        
        # セクション設定
        "section_name_font": "Helvetica-Bold",
        "section_name_size": 12,
        "section_name_margin_bottom": 5 * mm,
        "section_spacing": 10 * mm,
        "section_row_spacing": 5 * mm,
        
        # 小節設定
        "bar_group_margin": 5 * mm,
        "bar_group_margin_bottom": 3 * mm,
        "bar_margin": 1.5 * mm,
        
        # 弦設定
        "string_spacing": 3 * mm,
        "string_bottom_margin": 4 * mm,
        
        # 音符設定
        "note_font": "Helvetica",
        "note_size": 10,
        "note_offset": 1 * mm,
        
        # コード設定
        "chord_font": "Helvetica",
        "chord_size": 10,
        "chord_x_offset": 2 * mm,
        "chord_y_offset": 2 * mm,
        "chord_vertical_margin": 2.5 * mm,
        
        # 三連符設定
        "triplet_font": "Helvetica-Bold",
        "triplet_size": 10,
        "triplet_x_offset": 6 * mm,
        "triplet_y_offset": 4 * mm,
        "triplet_bracket_height": 2.0 * mm,
        "triplet_vertical_margin": 4 * mm,
        
        # ボルタ設定
        "volta_font": "Helvetica-Bold",
        "volta_size": 10,
        "volta_x_offset": 6 * mm,
        "volta_y_offset": 2 * mm,
        "volta_margin": 0.5 * mm,
        "volta_line_width": 0.5 * mm,
        "volta_vertical_margin": 6 * mm,
        
        # リピート設定
        "repeat_line_width": 1.2 * mm,
        "repeat_line_spacing": 0.8 * mm,
        "repeat_x_offset": 2.75 * mm,
        "repeat_dot_size": 0.8 * mm,
        
        # 線の太さ
        "normal_line_width": 0.5 * mm,
        "thick_line_width": 1.5 * mm,
        
        # 中括弧設定
        "brace_y_offset": 5 * mm,
    }
    
    def __init__(self, style_file=None):
        """スタイルマネージャーを初期化
        
        Args:
            style_file: スタイル設定ファイルのパス（オプション）
        """
        self.styles = self.DEFAULT_STYLES.copy()
        if style_file:
            self._load_style_file(style_file)
    
    def get(self, key: str, default=None):
        """スタイル設定を取得
        
        Args:
            key: スタイル設定のキー
            default: デフォルト値（キーが存在しない場合）
        
        Returns:
            スタイル設定の値
        """
        return self.styles.get(key, default)
    
    def set(self, key: str, value):
        """スタイル設定を設定
        
        Args:
            key: スタイル設定のキー
            value: スタイル設定の値
        """
        self.styles[key] = value
    
    def _load_style_file(self, style_file: str):
        """スタイル設定ファイルを読み込む
        
        Args:
            style_file: スタイル設定ファイルのパス
        """
        try:
            with open(style_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 数値の場合は変換
                        if value.isdigit():
                            value = float(value)
                        elif value.endswith('mm'):
                            value = float(value[:-2]) * mm
                        
                        self.styles[key] = value
        except Exception as e:
            print(f"Warning: Failed to load style file: {e}") 