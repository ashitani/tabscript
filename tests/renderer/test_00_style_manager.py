import pytest
from reportlab.lib.units import mm
from tabscript.style import StyleManager

def test_style_manager_default_values():
    """デフォルト値のテスト"""
    style_manager = StyleManager()
    
    # ページ設定のテスト
    assert style_manager.get("page_width") == 210 * mm
    assert style_manager.get("page_height") == 297 * mm
    assert style_manager.get("margin") == 20 * mm
    
    # タイトル設定のテスト
    assert style_manager.get("title_font") == "Helvetica-Bold"
    assert style_manager.get("title_size") == 16
    
    # 弦設定のテスト
    assert style_manager.get("string_spacing") == 3 * mm
    
    # 音符設定のテスト
    assert style_manager.get("note_font") == "Helvetica"
    assert style_manager.get("note_size") == 10

def test_style_manager_custom_values():
    """カスタム値の設定と取得のテスト"""
    style_manager = StyleManager()
    
    # 新しい値を設定
    style_manager.set("custom_value", 10 * mm)
    assert style_manager.get("custom_value") == 10 * mm
    
    # 既存の値を上書き
    style_manager.set("string_spacing", 4 * mm)
    assert style_manager.get("string_spacing") == 4 * mm

def test_style_manager_default_value():
    """デフォルト値の取得テスト"""
    style_manager = StyleManager()
    
    # 存在しないキーの場合
    assert style_manager.get("non_existent_key", "default") == "default"
    assert style_manager.get("non_existent_key") is None

def test_style_manager_load_file(tmp_path):
    """スタイル設定ファイルの読み込みテスト"""
    # テスト用のスタイルファイルを作成
    style_file = tmp_path / "test_style.txt"
    style_file.write_text("""
    # コメント行は無視される
    string_spacing=4
    custom_value=5mm
    title_size=20
    """)
    
    style_manager = StyleManager(str(style_file))
    
    # ファイルから読み込んだ値の確認
    assert style_manager.get("string_spacing") == 4
    assert style_manager.get("custom_value") == 5 * mm
    assert style_manager.get("title_size") == 20
    
    # デフォルト値は変更されていないことを確認
    assert style_manager.get("page_width") == 210 * mm

def test_style_manager_invalid_file():
    """無効なスタイルファイルのテスト"""
    style_manager = StyleManager("non_existent_file.txt")
    
    # デフォルト値が維持されていることを確認
    assert style_manager.get("string_spacing") == 3 * mm
    assert style_manager.get("title_size") == 16 