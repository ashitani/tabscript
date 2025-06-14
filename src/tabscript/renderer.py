from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from .models import Score, Section, Bar, Note
from .exceptions import TabScriptError
from typing import List, Tuple, Dict
from .style import StyleManager
from pdf2image import convert_from_path
import os

class NoteRenderer:
    """音符の描画を担当するクラス"""
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager

    def render_note(self, canvas, note: Note, x: float, y: float, y_offset: float = 0, y_positions: List[float] = None):
        """音符を描画"""
        if note.is_rest:
            return
        
        if note.is_chord and getattr(note, 'is_chord_start', False):
            self._draw_chord_notes(canvas, x, note, y_positions, y_offset)
        elif not note.is_chord:
            if '{' in str(note.fret):
                y -= y_offset
            self._draw_fret_number(canvas, x, y, note.fret, note.connect_next)

    def _draw_fret_number(self, canvas, x: float, y: float, fret: str, connect_next: bool = False):
        """フレット番号を描画"""
        canvas.setFont("Helvetica", 10)
        fret_str = "X" if fret == "X" else str(fret)
        
        # 二桁の数字の場合、文字間隔を詰める
        if len(fret_str) > 1 and fret_str.isdigit():
            # 各桁の文字を個別に描画
            text_height = 10
            canvas.setFillColor('white')
            # 背景を少し広めに取る
            text_width = canvas.stringWidth(fret_str, "Helvetica", 10) * 0.8  # 20%縮小
            canvas.rect(x + 1 * mm, y - text_height/2, text_width + 1, text_height, fill=1, stroke=0)
            canvas.setFillColor('black')
            
            # 各桁を個別に描画（間隔を詰める）
            first_digit = fret_str[0]
            second_digit = fret_str[1]
            first_width = canvas.stringWidth(first_digit, "Helvetica", 10)
            second_width = canvas.stringWidth(second_digit, "Helvetica", 10)
            
            # 最初の桁を描画
            canvas.drawString(x + 1 * mm, y - text_height/3, first_digit)
            # 2桁目の位置を調整（間隔を詰める）
            canvas.drawString(x + 1 * mm + first_width * 0.7, y - text_height/3, second_digit)
        else:
            # 一桁の数字やXの場合は通常通り描画
            text_width = canvas.stringWidth(fret_str, "Helvetica", 10)
            text_height = 10
            canvas.setFillColor('white')
            canvas.rect(x + 1 * mm, y - text_height/2, text_width + 1, text_height, fill=1, stroke=0)
            canvas.setFillColor('black')
            canvas.drawString(x + 1 * mm, y - text_height/3, fret_str)

    def _draw_tie(self, canvas, x1: float, y1: float, x2: float, y2: float, is_quarter_circle: bool = False):
        """タイ・スラーを描画
        
        Args:
            canvas: 描画対象のキャンバス
            x1: 開始X座標
            y1: 開始Y座標
            x2: 終了X座標
            y2: 終了Y座標
            is_quarter_circle: 1/4円として描画するかどうか
        """
        # 曲線の制御点を計算
        dx = x2 - x1
        dy = y2 - y1
        control_x1 = x1 + dx * 0.25
        control_y1 = y1 - 3 * mm
        control_x2 = x2 - dx * 0.25
        control_y2 = y2 - 3 * mm
        
        # 1/4円の場合は制御点を調整
        if is_quarter_circle:
            if x2 > x1:  # 右向きの1/4円
                control_x1 = x1 + dx * 0.5
                control_x2 = x2
                control_y1 = y1 - 3 * mm
                control_y2 = y1 - 3 * mm
            else:  # 左向きの1/4円
                control_x1 = x1
                control_x2 = x2 + dx * 0.5
                control_y1 = y1 - 3 * mm
                control_y2 = y1 - 3 * mm
        
        # 曲線を描画
        canvas.setLineWidth(1.0)
        canvas.bezier(x1, y1, control_x1, control_y1, control_x2, control_y2, x2, y2)
        canvas.setLineWidth(self.style_manager.get("normal_line_width"))

    def _draw_chord_notes(self, canvas, x: float, note: Note, y_positions: List[float], y_offset: float = 0):
        """和音の音符を描画"""
        # 最初の音符を描画
        y = y_positions[note.string - 1]
        if '{' in str(note.fret):
            y -= y_offset
        self._draw_fret_number(canvas, x, y, note.fret, note.connect_next)
        
        # 和音の他の音符を描画
        if hasattr(note, 'chord_notes') and note.chord_notes:
            for chord_note in note.chord_notes:
                # 各音符の弦の位置に応じてY座標を取得
                chord_y = y_positions[chord_note.string - 1]
                if '{' in str(chord_note.fret):
                    chord_y -= y_offset
                self._draw_fret_number(canvas, x, chord_y, chord_note.fret, chord_note.connect_next)

class TripletRenderer:
    """三連符の描画を担当するクラス"""
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager

    def detect_triplet_ranges(self, bar: Bar, note_x_positions: List[float], canvas) -> List[Tuple[float, float, int, int]]:
        """三連符の範囲を検出"""
        triplet_ranges = []
        i = 0
        while i < len(bar.notes):
            tuplet_type = getattr(bar.notes[i], 'tuplet', None)
            if tuplet_type is not None:
                start = i
                n = tuplet_type
                denominators = [int(bar.notes[j].duration) for j in range(i, len(bar.notes)) 
                              if getattr(bar.notes[j], 'tuplet', None) == n and bar.notes[j].duration.isdigit()]
                m = max(denominators) if denominators else 8
                expected = n / m
                actual = 0
                end = i
                while end < len(bar.notes) and getattr(bar.notes[end], 'tuplet', None) == n:
                    if bar.notes[end].duration.isdigit():
                        actual += 1 / int(bar.notes[end].duration)
                    end += 1
                    if abs(actual - expected) < 1e-6:
                        break
                if abs(actual - expected) < 1e-6:
                    x1 = note_x_positions[start] + 1.5 * mm
                    x2 = note_x_positions[end-1] + 1.5 * mm + canvas.stringWidth(str(bar.notes[end-1].fret), "Helvetica", 10)
                    triplet_ranges.append((x1, x2, start, end-1))
                    i = end
                else:
                    i += 1
            else:
                i += 1
        return triplet_ranges

    def draw_triplet_marks(self, canvas, triplet_ranges: List[Tuple[float, float, int, int]], y_positions: List[float], triplet_y: float = None):
        """三連符記号を描画"""
        for x1, x2, start, end in triplet_ranges:
            string_spacing = self.style_manager.get("string_spacing")
            y_triplet = triplet_y if triplet_y is not None else y_positions[0] + string_spacing  # triplet_yが指定されていない場合は従来通り
            text_y_offset = - string_spacing * 0.1
            bracket_height = self.style_manager.get("triplet_bracket_height", 2.5 * mm)
            
            # 上線
            canvas.line(x1, y_triplet, x2, y_triplet)
            
            # 左縦線
            canvas.line(x1, y_triplet, x1, y_triplet - bracket_height)
            
            # 右縦線
            canvas.line(x2, y_triplet, x2, y_triplet - bracket_height)
            
            # 3の数字
            canvas.setFont("Helvetica-Bold", 10)
            text = "3"
            text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
            text_height = 10
            mid_x = (x1 + x2) / 2
            
            # 背景
            canvas.setFillColor('white')
            canvas.rect(mid_x - text_width/2 - 1, y_triplet - text_height/2 - 1 - text_y_offset, 
                       text_width + 2, text_height + 2, fill=1, stroke=0)
            
            # テキスト
            canvas.setFillColor('black')
            canvas.drawString(mid_x - text_width/2, y_triplet - text_height/2 - 1 - text_y_offset, text)

class VoltaRenderer:
    """ボルタブラケットの描画を担当するクラス"""
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager

    def draw_volta_bracket(self, canvas, bar: Bar, x: float, width: float, y_positions: List[float], y: float):
        """ボルタブラケットを描画"""
        # volta_yを基準に水平線の位置を計算
        bracket_y = y
        
        if bar.volta_start or bar.volta_end:
            # 横線を描画
            canvas.setLineWidth(self.style_manager.get("volta_line_width"))
            left_x = x + self.style_manager.get("volta_margin")
            right_x = x + width - self.style_manager.get("volta_margin")
            canvas.line(left_x, bracket_y, right_x, bracket_y)
            canvas.setLineWidth(self.style_manager.get("normal_line_width"))
        
        if bar.volta_start:
            # 左線と数字を描画
            canvas.setLineWidth(self.style_manager.get("volta_line_width"))
            left_x = x + self.style_manager.get("volta_margin")
            canvas.line(left_x, bracket_y, 
                       left_x, y_positions[0] + self.style_manager.get("string_bottom_margin"))
            canvas.setLineWidth(self.style_manager.get("normal_line_width"))
            
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawString(left_x + 2 * mm, 
                            bracket_y - self.style_manager.get("volta_y_offset") - 1.0 * mm,
                            f"{bar.volta_number}.")
        
        if bar.volta_end:
            # 右線を描画
            canvas.setLineWidth(self.style_manager.get("volta_line_width"))
            right_x = x + width - self.style_manager.get("volta_margin")
            canvas.line(right_x, bracket_y, 
                       right_x, y_positions[0] + self.style_manager.get("string_bottom_margin"))
            canvas.setLineWidth(self.style_manager.get("normal_line_width"))

class RepeatRenderer:
    """繰り返し記号の描画を担当するクラス"""
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager

    def draw_repeat_start(self, canvas, x: float, y_positions: List[float]):
        """繰り返し開始記号を描画"""
        # 太線を描画
        canvas.setLineWidth(self.style_manager.get("repeat_line_width") )
        canvas.line(x, y_positions[0], x, y_positions[-1])
        canvas.setLineWidth(self.style_manager.get("normal_line_width"))

        # 細線を描画（右にシフト）
        x_shift = x + self.style_manager.get("repeat_line_spacing") + 0.5 * mm  # 0.5mm右にシフト
        canvas.line(x_shift, y_positions[0], x_shift, y_positions[-1])

        # ドットを描画（右にシフト）
        dot_y = (y_positions[0] + y_positions[-1]) / 2
        dot_spacing = 6.0 * mm
        dot_offset = self.style_manager.get("repeat_x_offset") 
        canvas.circle(x + dot_offset,
                     dot_y + dot_spacing/2,
                     self.style_manager.get("repeat_dot_size") * 2/3,
                     fill=1)
        canvas.circle(x + dot_offset,
                     dot_y - dot_spacing/2,
                     self.style_manager.get("repeat_dot_size") * 2/3,
                     fill=1)

    def draw_repeat_end(self, canvas, x: float, y_positions: List[float]):
        """繰り返し終了記号を描画"""
        # 太線を描画
        canvas.setLineWidth(self.style_manager.get("repeat_line_width"))
        canvas.line(x, y_positions[0], x, y_positions[-1])
        canvas.setLineWidth(self.style_manager.get("normal_line_width"))

        # 細線を描画（左にシフト）
        x_shift = x - self.style_manager.get("repeat_line_spacing") - 0.5 * mm  # 0.5mm左にシフト
        canvas.line(x_shift, y_positions[0], x_shift, y_positions[-1])

        # ドットを描画（左にシフト）
        dot_y = (y_positions[0] + y_positions[-1]) / 2
        dot_spacing = 6.0 * mm
        dot_offset = self.style_manager.get("repeat_x_offset")
        canvas.circle(x - dot_offset,
                     dot_y + dot_spacing/2,
                     self.style_manager.get("repeat_dot_size") * 2/3,
                     fill=1)
        canvas.circle(x - dot_offset,
                     dot_y - dot_spacing/2,
                     self.style_manager.get("repeat_dot_size") * 2/3,
                     fill=1)

class DummyBarRenderer:
    """ダミー小節の描画を担当するクラス"""
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager

    def draw_dummy_bar(self, canvas, x: float, width: float, y_positions: List[float]):
        """ダミー小節を描画"""
        center_x = x + (width / 2)
        center_y = (y_positions[0] + y_positions[-1]) / 2
        
        # 斜め線の長さと角度
        slash_length = 12.0 * mm
        dx = (slash_length / 2) * 0.7071
        dy = (slash_length / 2) * 0.7071
        
        # 斜め線
        slash_width = 1.05 * mm
        canvas.setLineWidth(slash_width)
        canvas.line(center_x - dx, center_y - dy,
                   center_x + dx, center_y + dy)
        canvas.setLineWidth(self.style_manager.get("normal_line_width"))
        
        # ドット
        dot_base_length = 6.0 * mm
        dot_dx = (dot_base_length / 2) * 0.7071
        dot_dy = (dot_base_length / 2) * 0.7071
        dot_radius = 0.7 * mm
        dot_offset_x = dot_dx + 1.0 * mm
        dot_offset_y = dot_dy + 0.7 * mm
        canvas.circle(center_x - dot_offset_x, center_y + dot_offset_y, dot_radius, fill=1)
        canvas.circle(center_x + dot_offset_x, center_y - dot_offset_y, dot_radius, fill=1)

class BarRenderer:
    """小節の描画を担当するクラス"""
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager
        self.note_renderer = NoteRenderer(style_manager)
        self.triplet_renderer = TripletRenderer(style_manager)
        self.volta_renderer = VoltaRenderer(style_manager)
        self.repeat_renderer = RepeatRenderer(style_manager)
        self.dummy_bar_renderer = DummyBarRenderer(style_manager)

    def render_bar(self, canvas, bar: Bar, x: float, y: float, width: float, y_positions: List[float], y_offset: float = 0):
        """小節を描画"""
        # 小節の余白を計算
        bar_margin = 1.5 * mm
        
        # 繰り返し記号のためのマージンを追加
        repeat_margin = 2.0 * mm if bar.is_repeat_start or bar.is_repeat_end else 0
        
        # 小節の幅を計算
        usable_width = width - (2 * bar_margin) - repeat_margin
        
        # 音符の開始位置を計算
        note_x = x + bar_margin
        if bar.is_repeat_start and bar.volta_number is None:
            note_x += repeat_margin  # 反復開始記号分、右にずらす
        
        # 音符の終了位置を計算
        note_end_x = x + width - bar_margin
        if bar.is_repeat_end or bar.volta_end:
            note_end_x -= repeat_margin  # 反復終了記号分、左にずらす
        
        # 実際に使用可能な幅を再計算
        usable_width = note_end_x - note_x
        
        # 縦線を描画
        if bar.is_repeat_start and bar.volta_number is None:  # volta_numberがNoneの場合のみ描画
            self.repeat_renderer.draw_repeat_start(canvas, x, y_positions)
        elif bar.is_repeat_end or bar.volta_end:  # 反復終了またはボルタ終了の場合
            self.repeat_renderer.draw_repeat_end(canvas, x + width, y_positions)
        else:
            canvas.line(x, y_positions[0], x, y_positions[-1])
        
        # 横線を描画
        for y in y_positions:
            canvas.line(x, y, x + width, y)
        
        # 音符を描画
        if not bar.is_dummy:
            self._draw_notes(canvas, bar, note_x, usable_width, y_positions, y_offset)
        else:
            self.dummy_bar_renderer.draw_dummy_bar(canvas, x, width, y_positions)
        
        # 最後の縦線を描画
        canvas.line(x + width, y_positions[0], x + width, y_positions[-1])

        # 小節の最初の音符が前の小節から接続されている場合
        if bar.notes and not bar.notes[0].is_rest and bar.notes[0].string > 0:
            first_note = bar.notes[0]
            if hasattr(first_note, 'connect_prev') and first_note.connect_prev:
                # 小節の左端を超えた位置から1/4円を描画
                self.note_renderer._draw_tie(
                    canvas,
                    x - 2 * mm,
                    y_positions[first_note.string - 1]-2*mm,
                    note_x,
                    y_positions[first_note.string - 1]-2*mm,
                    is_quarter_circle=True
                )

    def _draw_notes(self, canvas, bar: Bar, x: float, width: float, y_positions: List[float], y_offset: float):
        """音符を描画"""
        # 音符の位置を計算
        note_x_positions = self._calculate_note_positions(bar, x, width)
        
        # 音符を描画
        for i, note in enumerate(bar.notes):
            note_x = note_x_positions[i]
            if not note.is_rest:
                y = y_positions[note.string - 1]
                self.note_renderer.render_note(canvas, note, note_x, y, y_offset, y_positions)
                
                # タイ・スラーの描画
                if note.connect_next:
                    if i < len(bar.notes) - 1:  # 同じ小節内の次の音符
                        next_note = bar.notes[i + 1]
                        if not next_note.is_rest and next_note.string == note.string:
                            next_x = note_x_positions[i + 1]
                            next_y = y_positions[next_note.string - 1]
                            fret_width = canvas.stringWidth(str(next_note.fret), "Helvetica", 10)
                            next_x = next_x + fret_width / 2
                            self.note_renderer._draw_tie(canvas, note_x + 2 * mm, y-2*mm, next_x+1*mm, next_y-2*mm)
                    else:  # 小節の最後の音符で、次の小節に接続
                        # 小節の右端を超えた位置まで1/4円を描画
                        bar_end_x = x + width
                        self.note_renderer._draw_tie(
                            canvas,
                            note_x + 2 * mm,
                            y-2*mm,
                            bar_end_x + 2 * mm,
                            y-2*mm,
                            is_quarter_circle=True
                        )

    def _calculate_note_positions(self, bar: Bar, x: float, width: float) -> List[float]:
        """音符の位置を計算"""
        note_x_positions = []
        current_x = x
        total_steps = sum(note.step for note in bar.notes)
        step_width = width / total_steps if total_steps > 0 else width
        
        for note in bar.notes:
            note_x_positions.append(current_x)
            current_x += note.step * step_width
        
        return note_x_positions

    def _draw_chord(self, canvas, x: float, y: float, chord: str):
        """コード名を描画"""
        canvas.setFont("Helvetica", 10)
        canvas.drawString(x + 0.5 * mm, y, chord)

class LayoutCalculator:
    """レイアウト計算を担当するクラス"""
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager

    def calculate_section_layout(self, bars_per_line: int, page_width: float) -> tuple:
        """bars_per_lineに基づいてレイアウトを計算"""
        bar_group_size = bars_per_line
        num_groups = 1  # 1行ごとに1グループとみなす
        bar_group_margin = self.style_manager.get("bar_group_margin")
        margin = self.style_manager.get("margin", 10 * mm)  # デフォルト値として10mmを設定
        available_width = page_width - (2 * margin) - (bar_group_margin * (num_groups - 1))
        bar_width = available_width / bar_group_size
        bar_group_width = bar_width * bar_group_size
        return bar_width, bar_group_width, bar_group_margin

    def calculate_bar_positions(self, bars_per_line: int, x: float, bar_width: float, bar_group_width: float, bar_group_margin: float) -> list:
        """bars_per_lineに基づいて小節の位置を計算"""
        positions = []
        for i in range(bars_per_line):
            # 三連符記号がある場合は追加のマージンを設定
            bar_x = x + (i * bar_width) 
            positions.append(bar_x)
        return positions

    def calculate_string_positions(self, y: float) -> list:
        """弦の位置を計算
        
        Args:
            y: 開始Y座標
            
        Returns:
            各弦のY座標のリスト
        """
        string_spacing = self.style_manager.get("string_spacing")
        string_count = self.style_manager.get("string_count", 6)  # デフォルトは6弦
        return [y - (i * string_spacing) for i in range(string_count)]

class Renderer:
    def __init__(self, score: Score, debug_mode: bool = False, style_file=None, show_length: bool = False):
        """レンダラーを初期化
        
        Args:
            score: 描画対象のスコア
            debug_mode: デバッグモードフラグ
            style_file: スタイル設定ファイルのパス
            show_length: 音価（三連符を含む）を表示するかどうか（デフォルトはFalse）
        """
        self.score = score
        self.debug_mode = debug_mode
        self.show_length = show_length
        
        # レイアウト設定
        self.page_width = 210 * mm
        self.page_height = 297 * mm
        self.margin = 10 * mm
        self.margin_bottom = 20 * mm
        
        # スタイルマネージャーを初期化
        self.style_manager = StyleManager(style_file)
        
        # スタイルマネージャーにマージンを設定
        self.style_manager.set("margin", self.margin)
        self.style_manager.set("margin_bottom", self.margin_bottom)
        
        # レンダラーを初期化
        self.bar_renderer = BarRenderer(self.style_manager)
        self.layout_calculator = LayoutCalculator(self.style_manager)
        
    def debug_print(self, *args, **kwargs):
        """デバッグモードの時だけ出力"""
        if self.debug_mode:
            print("DEBUG:", *args, **kwargs)

    def render_pdf(self, output_path: str):
        """タブ譜をPDFとしてレンダリング"""
        self.debug_print(f"render_pdf start: score object id = {id(self.score)}")
        
        # 弦の数を設定
        string_count = self._get_string_count()
        self.style_manager.set("string_count", string_count)
        self.debug_print(f"String count: {string_count}")
        
        # A4縦向きでキャンバスを作成
        canvas_obj = canvas.Canvas(output_path, pagesize=A4)
        
        # 現在のページ番号を初期化
        current_page = 1
        
        # マージンを取得
        margin = self.style_manager.get("margin", 10 * mm)
        margin_bottom = self.style_manager.get("margin_bottom", 20 * mm)
        
        # 1. タイトルを描画
        y = self.page_height - margin
        self._draw_title(canvas_obj, y)
        
        # 2. タイトルの下に移動
        y -= self.style_manager.get("title_margin_bottom")
        
        # 3. メタデータを描画
        self._draw_metadata(canvas_obj, y)
        y -= 5 * mm
        
        # セクションごとに描画
        for section_index, section in enumerate(self.score.sections):
            self.debug_print(f"Processing section: {section.name}")
            self.debug_print(f"Section attributes: {dir(section)}")
            self.debug_print(f"Section page_breaks: {getattr(section, 'page_breaks', None)}")
            
            # 4. セクション名を描画（空のセクション名の場合はスキップ）
            if section.name:
                canvas_obj.setFont("Helvetica-Bold", 12)
                canvas_obj.drawString(margin, y, f"[{section.name}]")
                y -= self.style_manager.get("section_name_margin_bottom")
            
            # 小節数を追跡
            current_bar_count = 0
            
            # 各行を描画
            for i, column in enumerate(section.columns):
                bars_per_line = getattr(column, 'bars_per_line', self.score.bars_per_line)
                self.debug_print(f"Section: {section.name}, Column: {i}, bars_per_line: {bars_per_line}")
                # 改行後の初期位置
                if i == 0:  # 最初のカラム
                    # セクション名の下の位置を維持
                    pass
                else:  # 2行目以降
                    # 前のカラムの最後の弦の位置から計算
                    y = y_positions[-1] - self.style_manager.get("string_bottom_margin")

                # レイアウトを計算
                bar_width, bar_group_width, bar_group_margin = self.layout_calculator.calculate_section_layout(
                    bars_per_line, self.page_width - (2 * margin)
                )
                self.debug_print(f"Section: {section.name}, Column: {i}, Bar width: {bar_width}, Bar group width: {bar_group_width}")
                bar_positions = self.layout_calculator.calculate_bar_positions(
                    bars_per_line, margin, bar_width, bar_group_width, bar_group_margin
                )

                # 三連符、コード、ボルタの有無をチェック
                has_triplet = False  # 三連符の有無をチェック
                has_chord = False    # コードの有無をチェック
                has_volta = False

                # 各小節の要素をチェック
                for bar in column.bars:
                    # 三連符のチェック（音価表示が有効な場合のみ）
                    if self.show_length:
                        for note in bar.notes:
                            if hasattr(note, 'tuplet') and note.tuplet:
                                has_triplet = True
                                break
                    
                    # コードのチェック（小節内の最初の音符を探す）
                    if bar.notes:
                        first_note = bar.notes[0]
                        if first_note.chord:
                            has_chord = True
                    
                    # ボルタのチェック
                    if bar.volta_number is not None:
                        has_volta = True

                # 要素の重ね順：三連符 > コード > ボルタブラケット
                triplet_y = y  # 三連符の位置
                chord_y = y  # コードの位置
                volta_y = y  # ボルタブラケットの位置

                # 三連符、コード、ボルタの有無に応じて行の開始位置を下げる
                if has_volta:
                    volta_y = y  # ボルタブラケットの位置
                    y -= self.style_manager.get("volta_vertical_margin", 4 * mm)

                if has_chord:
                    chord_y = y  # コードの位置
                    y -= self.style_manager.get("chord_vertical_margin", 4 * mm)

                if has_triplet and self.show_length:
                    triplet_y = y  # 三連符の位置
                    y -= self.style_manager.get("triplet_vertical_margin", 4 * mm)

                base_y = y

                # 弦の位置を計算
                y_positions = self.layout_calculator.calculate_string_positions(y)

                # 小節と音符を描画
                for j, bar in enumerate(column.bars):
                    # 小節の余白を計算
                    bar_margin = 1.5 * mm
                    repeat_margin = 2.0 * mm if bar.is_repeat_start or bar.is_repeat_end else 0
                    usable_width = bar_width - (2 * bar_margin) - repeat_margin
                    note_x = bar_positions[j] + bar_margin + (repeat_margin if bar.is_repeat_start else 0)

                    # 音符の位置を計算
                    note_positions = self.bar_renderer._calculate_note_positions(bar, note_x, usable_width)

                    # ボルタブラケットを描画（最上段）
                    if bar.volta_number is not None:
                        self.bar_renderer.volta_renderer.draw_volta_bracket(
                            canvas_obj, bar, bar_positions[j], bar_width, y_positions, volta_y
                        )
                    
                    # コードを描画（中段）
                    if bar.notes:
                        self.debug_print(f"Checking notes in bar for chords:")
                        # 各音符のコードを描画（明示的に指定されたコードのみ）
                        for i, note in enumerate(bar.notes):
                            self.debug_print(f"Note {i}: is_rest={note.is_rest}, chord={note.chord}, is_chord_start={getattr(note, 'is_chord_start', False)}")
                            if note.chord and getattr(note, 'is_chord_start', False):
                                self.debug_print(f"Drawing chord '{note.chord}' at position {note_positions[i]}")
                                self.bar_renderer._draw_chord(
                                    canvas_obj,
                                    note_positions[i],  # 現在の音符の位置を使用
                                    chord_y,
                                    note.chord
                                )

                    # 三連符記号を描画（下段）- 音価表示が有効な場合のみ
                    if self.show_length:
                        triplet_ranges = self.bar_renderer.triplet_renderer.detect_triplet_ranges(bar, note_positions, canvas_obj)
                        if triplet_ranges:
                            self.bar_renderer.triplet_renderer.draw_triplet_marks(canvas_obj, triplet_ranges, y_positions, triplet_y)

                    # 小節と音符を描画
                    self.bar_renderer.render_bar(
                        canvas_obj, bar, bar_positions[j], base_y, bar_width, y_positions
                    )
                    current_bar_count += 1  # 小節数をインクリメント
                
                # 7. 最高弦の下端から下に移動
                y = y_positions[-1] - self.style_manager.get("string_bottom_margin")
                
                # カラム描画後に改ページ判定（小節数ベース）
                if hasattr(section, 'page_breaks') and current_bar_count in section.page_breaks:
                    self.debug_print(f"Section: {section.name}, Current bar count: {current_bar_count}, page_breaks: {section.page_breaks}")
                    self.debug_print(f"Should break page: {current_bar_count in section.page_breaks}")
                    # 現在のページのページ番号を描画
                    self._draw_page_number(canvas_obj, current_page)
                    canvas_obj.showPage()
                    current_page += 1
                    # 新しいページでは最小限の余白から描画を始める
                    y = self.page_height - (margin - self.style_manager.get("section_name_margin_bottom"))
                    # 三連符、コード、ボルタの位置も上端に合わせる
                    triplet_y = y
                    chord_y = y
                    volta_y = y
                    base_y = y
                    # 弦の位置を再計算
                    y_positions = self.layout_calculator.calculate_string_positions(y)
            
            # セクション間の間隔
            y -= self.style_manager.get("section_spacing")
            
            # 新しいページが必要かチェック（最後のセクションでない場合のみ）
            if y < margin_bottom and section_index < len(self.score.sections) - 1:
                # 現在のページのページ番号を描画
                self._draw_page_number(canvas_obj, current_page)
                canvas_obj.showPage()
                current_page += 1
                # 新しいページでは必ず上端から描画を始める
                y = self.page_height - margin
        
        # 最後のページのページ番号を描画
        self._draw_page_number(canvas_obj, current_page)
        canvas_obj.save()

    def _draw_title(self, canvas_obj, y: float):
        """タイトルを描画（センタリング）"""
        canvas_obj.setFont("Helvetica-Bold", 16)
        title_width = canvas_obj.stringWidth(self.score.title, "Helvetica-Bold", 16)
        x = (self.page_width - title_width) / 2  # センタリングのためのX座標を計算
        canvas_obj.drawString(x, y, self.score.title)

    def _draw_metadata(self, canvas_obj, y: float):
        """メタデータを描画"""
        y -= 5 * mm  # 15mmから5mmに縮小

    def render_text(self, output_path: str):
        """タブ譜をテキスト形式でレンダリング"""
        with open(output_path, 'w') as f:
            # タイトルのみ出力（空でない場合）
            if self.score.title:
                f.write(f"{self.score.title}\n\n")

            # 各セクションを出力
            for section in self.score.sections:
                # セクション名が空でない場合のみ表示
                if section.name:
                    f.write(f"[{section.name}]\n\n")
                
                # 各行（Column）を出力
                for column in section.columns:
                    self._render_column_text(f, column)
                    f.write("\n")  # 行間に空行を挿入
                
                f.write("\n")  # セクション間に空行を挿入

    def _render_column_text(self, f, column):
        """1行（複数の小節）をテキスト形式で出力"""
        string_count = self._get_string_count()
        
        # 各小節の内容を構築
        bar_contents = []
        for bar_index, bar in enumerate(column.bars):
            # コード行と弦の行を作成
            lines = ["" for _ in range(string_count + 1)]  # +1 for chord line
            
            # 小節の開始を示す縦線（最初の小節のみ、コード行以外）
            for i in range(1, len(lines)):  # コード行はスキップ
                lines[i] = "|" if bar_index == 0 else ""
            lines[0] = " "  # コード行は空白から開始
            
            # 各音符を配置
            current_pos = len(lines[0])  # 現在の水平位置を追跡
            for note in bar.notes:
                # コードがある場合は表示
                if note.chord:
                    # 必要なら空白を追加してコードを配置
                    while len(lines[0]) < current_pos:
                        lines[0] += " "
                    lines[0] += f" {note.chord} "
                
                # 音符の処理
                if note.is_rest:
                    # 休符の場合は全ての弦に-を追加
                    for i in range(1, len(lines)):  # コード行はスキップ
                        lines[i] += "-" * 4
                else:
                    # 通常の音符
                    for i in range(1, len(lines)):  # コード行はスキップ
                        if i == note.string:  # 弦番号をそのまま使用（1弦が一番上）
                            fret_str = str(note.fret)
                            if note.connect_next:
                                lines[i] += f"-{fret_str}&-"  # スラーの場合は&を追加
                            else:
                                lines[i] += f"-{fret_str}--"
                        else:
                            lines[i] += "----"
                
                # 連符の場合は音符の長さを調整
                if hasattr(note, 'tuplet') and note.tuplet:
                    # 連符の場合は音符の長さを2/3に（三連符の場合）
                    for i in range(1, len(lines)):
                        if len(lines[i]) > 0:
                            lines[i] = lines[i][:-2]  # 最後の2文字を削除
                
                current_pos = len(lines[1])  # 音符の後の位置を更新
            
            # コード行の長さを他の行に合わせる
            while len(lines[0]) < len(lines[1]):
                lines[0] += " "
            
            # 小節の終了を示す縦線（コード行以外）
            for i in range(1, len(lines)):  # コード行はスキップ
                lines[i] += "|"
            lines[0] += " "  # コード行は空白で終了
            
            bar_contents.append(lines)
        
        # 全ての小節を横に並べて出力
        for string in range(len(bar_contents[0])):
            for bar_lines in bar_contents:
                f.write(bar_lines[string])
            f.write("\n")

    def render_png(self, output_path: str, dpi: int = 200):
        """タブ譜をPNGとしてレンダリング
        
        Args:
            output_path: 出力ファイルのパス
            dpi: 画像の解像度（デフォルト: 200）
        """
        # 一時的なPDFファイルを作成
        temp_pdf = output_path.replace('.png', '_temp.pdf')
        self.render_pdf(temp_pdf)
        
        try:
            # PDFをPNGに変換
            images = convert_from_path(temp_pdf, dpi=dpi)
            
            # 最初のページを保存
            if images:
                images[0].save(output_path, 'PNG')
        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_pdf):
                os.remove(temp_pdf)

    def render_score(self, output_path: str):
        """タブ譜をファイルとして出力"""
        if not self.score:
            raise TabScriptError("No score to render. Call parse() first.")
        
        if output_path.endswith('.pdf'):
            self.render_pdf(output_path)
        elif output_path.endswith('.png'):
            self.render_png(output_path)
        else:
            self.render_text(output_path)

    def _get_string_count(self) -> int:
        """チューニング設定から弦の数を取得"""
        tuning_map = {
            "guitar": 6,
            "guitar7": 7,
            "bass": 4,
            "bass5": 5,
            "ukulele": 4
        }
        return tuning_map.get(self.score.tuning, 6)  # デフォルトは6弦 

    def _draw_page_number(self, canvas_obj, current_page: int):
        """ページ番号を描画
        
        Args:
            canvas_obj: 描画対象のキャンバス
            current_page: 現在のページ番号
        """
        canvas_obj.setFont("Helvetica", 8)  # 小さいフォントサイズ
        page_text = f"{self.score.title} {current_page}"
        text_width = canvas_obj.stringWidth(page_text, "Helvetica", 8)
        x = self.page_width - 10 * mm - text_width  # 右端から10mmの位置から文字列の幅を引く
        y = self.page_height - 10 * mm  # 上端から10mmの位置
        canvas_obj.drawString(x, y, page_text) 