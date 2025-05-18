from reportlab.lib.units import mm

class StyleManager:
    """タブ譜のスタイル設定を管理するクラス"""
    
    def __init__(self, style_file=None):
        """スタイルマネージャーを初期化
        
        Args:
            style_file: スタイル設定ファイルのパス（省略可）
        """
        # デフォルトのスタイル設定
        self.styles = {
            # 基本的な間隔
            "string_spacing": 3 * mm,        # 弦と弦の間隔
            "section_spacing": 5 * mm,       # セクション間の間隔
            
            # 縦方向のマージン
            "title_margin_bottom": 5 * mm,   # タイトルの下のマージン
            "metadata_margin_bottom": 5 * mm, # メタデータの下のマージン
            "section_name_margin_bottom": 8 * mm, # セクション名の下のマージン
            
            # 相対位置
            "chord_offset": 2.5 * mm,        # コードと1弦の間隔
            "volta_bracket_offset": 10 * mm, # ボルタブラケットと1弦の間隔
            "volta_number_offset": 3.2 * mm, # ボルタ番号とブラケットの間隔
            "repeat_dot_offset": 3 * mm,     # リピート記号のドットのオフセット
            
            # 行の高さ
            "normal_row_height": 22 * mm,    # 通常の行の高さ
            "volta_row_height": 35 * mm,     # ボルタブラケットを含む行の高さ
            
            # 線の太さ
            "normal_line_width": 1.0,        # 通常の線の太さ
            "repeat_line_width": 2.5,        # リピート記号の線の太さ
            "volta_line_width": 1.0,         # ボルタブラケットの線の太さ
            
            # その他の設定
            "repeat_dot_size": 0.375 * mm,    # リピート記号のドットのサイズ（0.25mmから1.5倍に拡大）
            "repeat_line_spacing": 1.2 * mm, # リピート記号の線の間隔
            "volta_margin": 0.5 * mm,        # ボルタブラケットの小節境界からのマージン
            "string_bottom_margin": 1 * mm,  # 1弦からの下マージン（ボルタ線など）
            "triplet_offset": 4.5*mm,          # 三連符記号のオフセット
        }
        
        # スタイル設定ファイルが指定されていれば読み込む
        if style_file:
            self._load_style_file(style_file)
    
    def _load_style_file(self, style_file):
        """スタイル設定ファイルを読み込む（将来の拡張用）"""
        # 現在は実装しない
        pass
    
    def get(self, key, default=None):
        """スタイル設定値を取得
        
        Args:
            key: 取得するスタイル設定のキー
            default: キーが存在しない場合のデフォルト値
            
        Returns:
            スタイル設定値
        """
        return self.styles.get(key, default)
    
    def set(self, key, value):
        """スタイル設定値を設定
        
        Args:
            key: 設定するスタイル設定のキー
            value: 設定する値
        """
        self.styles[key] = value 