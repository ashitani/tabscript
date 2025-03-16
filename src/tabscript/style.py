import yaml
from reportlab.lib.units import mm

class StyleManager:
    def __init__(self, style_file=None):
        # デフォルトスタイル
        self.default_styles = {
            # 基本的な間隔
            "string_spacing": 3 * mm,
            "section_spacing": 5 * mm,
            
            # 縦方向のマージン
            "title_margin_bottom": 5 * mm,
            "metadata_margin_bottom": 5 * mm,
            "section_name_margin_bottom": 8 * mm,
            
            # 相対位置
            "chord_offset": 2.5 * mm,
            "volta_bracket_offset": 10 * mm,
            "volta_number_offset": 3.2 * mm,
            "repeat_dot_offset": 3 * mm,
            
            # 行の高さ
            "normal_row_height": 22 * mm,
            "volta_row_height": 35 * mm,
            
            # 線の太さ
            "normal_line_width": 1.0,
            "repeat_line_width": 2.5,
            "volta_line_width": 1.0,
            
            # その他の設定
            "repeat_dot_size": 0.25 * mm,
            "repeat_line_spacing": 1.2 * mm,
            "volta_margin": 0.5 * mm,
            "string_bottom_margin": 1 * mm,
        }
        
        # スタイルファイルがあれば読み込む
        self.styles = self.default_styles.copy()
        if style_file:
            try:
                with open(style_file, 'r') as f:
                    custom_styles = yaml.safe_load(f)
                    # mmの単位を適用
                    for key, value in custom_styles.items():
                        if key.endswith('_mm') or key.endswith('_offset') or key.endswith('_spacing') or key.endswith('_margin'):
                            custom_styles[key] = value * mm
                    self.styles.update(custom_styles)
            except Exception as e:
                print(f"Error loading style file: {e}")
    
    def get(self, key, default=None):
        """スタイル値を取得"""
        return self.styles.get(key, default)
    
    def update(self, styles):
        """スタイルを更新"""
        self.styles.update(styles) 