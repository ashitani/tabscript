from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from .models import Score, Section, Bar, Note
from .exceptions import TabScriptError
from typing import List, Tuple

class Renderer:
    def __init__(self, score: Score, debug_mode: bool = False):
        self.score = score
        self.canvas = None
        self.current_x = 0
        self.current_y = 0
        self.debug_mode = debug_mode
        
        self.debug_print(f"__init__: score object id = {id(self.score)}")
        
        # レイアウト設定
        self.margin = 5 * mm
        self.margin_bottom = 20 * mm  # 追加：下マージン
        self.string_spacing = 3 * mm
        self.section_spacing = 5 * mm  # 10mmから5mmに変更
        
        # A4縦向きのサイズ設定
        self.page_width = A4[0]
        self.debug_print(f"page_width = {self.page_width}")
        self.page_height = A4[1]
        self.usable_width = self.page_width - (2 * self.margin)
        self.debug_print(f"usable_width = {self.usable_width}")
        
        # 小節の幅を計算は不要（各Columnが自身のbars_per_lineを持つため）
        self.debug_print(f"A4 size = {A4}")

    def debug_print(self, *args, **kwargs):
        """デバッグモードの時だけ出力"""
        if self.debug_mode:
            print("DEBUG:", *args, **kwargs)

    def render_pdf(self, output_path: str, debug: bool = False):
        """タブ譜をPDFとしてレンダリング"""
        self.debug_print("\n=== render_pdf ===")
        self.debug_print(f"Output path: {output_path}")
        
        # A4縦向きでキャンバスを作成
        self.canvas = canvas.Canvas(output_path, pagesize=A4)
        
        # タイトルと設定を出力
        y = self.page_height - self.margin - 5 * mm
        self.debug_print(f"Initial y position: {y}")
        
        # セクションごとに描画
        for section_index, section in enumerate(self.score.sections):
            self.debug_print(f"\nProcessing section {section_index}: {section.name}")
            
            # セクション名を描画（空のセクション名の場合はスキップ）
            if section.name:
                self.canvas.setFont("Helvetica-Bold", 12)
                self.canvas.drawString(self.margin, y, f"[{section.name}]")
                y -= 8 * mm
            
            # 各行を描画
            for column_index, column in enumerate(section.columns):
                self.debug_print(f"\nProcessing column {column_index}")
                self.debug_print(f"Number of bars: {len(column.bars)}")
                
                # 小節グループを描画
                self._render_bar_group_pdf(column.bars, column.bars_per_line, y)
                y -= 22 * mm  # 行間隔
                
                # 新しいページが必要かチェック
                if y < self.margin_bottom:
                    self.canvas.showPage()
                    y = self.page_height - self.margin - 5 * mm
            
            y -= self.section_spacing  # セクション間の間隔
        
        self.canvas.save()
        self.debug_print("\nPDF generation completed")

    def draw_title(self, y: float):
        """タイトルを描画（センタリング）"""
        self.canvas.setFont("Helvetica-Bold", 16)
        title_width = self.canvas.stringWidth(self.score.title, "Helvetica-Bold", 16)
        x = (self.page_width - title_width) / 2  # センタリングのためのX座標を計算
        self.canvas.drawString(x, y, self.score.title)
        self.current_y -= 5 * mm  # タイトル後の間隔を5mmに縮小

    def draw_metadata(self, y: float):
        """メタデータを描画"""
        # チューニングと拍子の表示を削除
        self.current_y -= 5 * mm  # 15mmから5mmに縮小

    def _render_bar_pdf(self, bar: Bar):
        """1小節を描画"""
        string_count = self._get_string_count()
        bar_margin = 1.5 * mm

        # 小節の分解能を計算
        resolution = self._calculate_bar_resolution(bar)
        total_steps = sum(self._duration_to_steps(note.duration, resolution) for note in bar.notes)
        
        # 各弦の位置を計算
        y_positions = [self.current_y - (i * self.string_spacing) for i in range(string_count)]
        
        # 小節を描画
        current_x = self.margin
        
        # このステップ幅で描画（余白を考慮）
        step_width = (self.usable_width - bar_margin) / total_steps
        
        # 縦線を描画
        self.canvas.line(current_x, y_positions[0], current_x, y_positions[-1])
        
        # 横線を描画
        for y in y_positions:
            self.canvas.line(current_x, y, current_x + self.usable_width, y)
        
        # 音符を配置（余白から開始）
        note_x = current_x + bar_margin
        for note in bar.notes:
            note_steps = self._duration_to_steps(note.duration, resolution)
            
            # コードを描画
            if note.chord:
                self._draw_chord(note_x, y_positions[0], note.chord)
            
            if not note.is_rest:
                if note.is_chord:
                    # 主音を描画
                    y = y_positions[note.string - 1]
                    self._draw_fret_number(note_x, y, note.fret)
                    
                    # 和音の他の音を描画
                    for chord_note in note.chord_notes:
                        y = y_positions[chord_note.string - 1]
                        self._draw_fret_number(note_x, y, chord_note.fret)
                else:
                    # 通常の音符を描画
                    y = y_positions[note.string - 1]
                    self._draw_fret_number(note_x, y, note.fret)
            
            note_x += note_steps * step_width
        
        # 最後の縦線を描画
        self.canvas.line(current_x + self.usable_width, y_positions[0], current_x + self.usable_width, y_positions[-1])

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

    def _parse_duration(self, duration: str) -> Tuple[int, bool]:
        """音価文字列を解析して、基本の音価と付点の有無を返す"""
        self.debug_print(f"\n=== _parse_duration ===")
        self.debug_print(f"Input: duration='{duration}'")
        try:
            if duration.endswith('.'):
                base = int(duration[:-1])
                self.debug_print(f"Found dot: base={base}, has_dot=True")
                return base, True
            else:
                base = int(duration)
                self.debug_print(f"No dot: base={base}, has_dot=False")
                return base, False
        except ValueError as e:
            self.debug_print(f"Error parsing duration: '{duration}'")
            raise e

    def _calculate_bar_resolution(self, bar: Bar) -> int:
        """小節内の分解能を計算"""
        self.debug_print("\n=== _calculate_bar_resolution ===")
        min_duration = float('inf')
        for i, note in enumerate(bar.notes):
            self.debug_print(f"Processing note {i}: duration='{note.duration}'")
            try:
                base, has_dot = self._parse_duration(note.duration)
                self.debug_print(f"  base={base}, has_dot={has_dot}")
                min_duration = min(min_duration, base)  # 最小音価を見つける
                if has_dot:
                    self.debug_print(f"  Note has dot")
            except ValueError as e:
                self.debug_print(f"Error processing duration: {note.duration}")
                raise e
        
        # 最小音価を分解能とする（16分音符なら16）
        result = min_duration
        self.debug_print(f"Final resolution: {result} (min_duration={min_duration})")
        return result

    def _duration_to_steps(self, duration: str, resolution: int) -> int:
        """音価をステップ数に変換"""
        self.debug_print(f"\n=== _duration_to_steps ===")
        self.debug_print(f"Input: duration='{duration}', resolution={resolution}")
        
        base, has_dot = self._parse_duration(duration)
        self.debug_print(f"Parsed: base={base}, has_dot={has_dot}")
        
        # resolution は最小音価なので、
        # 例：resolution=16（16分音符が基準）の場合
        # - 16分音符 = 1ステップ
        # - 8分音符 = 2ステップ
        # - 4分音符 = 4ステップ
        steps = resolution // base  # まず基本のステップ数を計算
        self.debug_print(f"Base steps: {steps}")
        
        if has_dot:
            # 付点の場合は1.5倍（切り捨てを避けるため、先に2倍して3を掛ける）
            steps = (steps * 3) // 2  # 単純に1.5倍
            self.debug_print(f"After dot: {steps}")
        
        self.debug_print(f"Final steps: {steps}")
        return steps  # max(1, steps)は不要（既に1以上のはず）

    def _write_empty_steps(self, f, string_count: int, steps: int):
        """空のステップを出力"""
        for _ in range(string_count):
            f.write("-" * (4 * steps) + "\n")

    def _write_note_steps(self, f, string_count: int, note: Note, steps: int):
        """音符のステップを出力"""
        for string in range(1, string_count + 1):
            if string == note.string:
                # フレット番号を右詰めで出力
                fret_str = str(note.fret).rjust(2, '-')
                f.write(f"--{fret_str}" + "-" * (4 * (steps - 1)) + "\n")
            else:
                f.write("-" * (4 * steps) + "\n") 

    def render_score(self, output_path: str):
        """タブ譜をファイルとして出力"""
        if not self.score:
            raise TabScriptError("No score to render. Call parse() first.")
        
        if output_path.endswith('.pdf'):
            self.render_pdf(output_path)
        else:
            self.render_text(output_path) 

    def _draw_fret_number(self, x: float, y: float, fret: str):
        """フレット番号を描画（ヘルパーメソッド）"""
        self.canvas.setFont("Helvetica", 10)
        fret_str = "X" if fret == "X" else str(fret)
        text_width = self.canvas.stringWidth(fret_str, "Helvetica", 10)
        text_height = 10
        self.canvas.setFillColor('white')
        self.canvas.rect(x + 1 * mm, y - text_height/2, text_width + 1, text_height, fill=1, stroke=0)
        self.canvas.setFillColor('black')
        self.canvas.drawString(x + 1 * mm, y - text_height/3, fret_str)

    def _draw_chord(self, x: float, y: float, chord: str):
        """コード名を描画（ヘルパーメソッド）"""
        self.canvas.setFont("Helvetica", 10)
        text_width = self.canvas.stringWidth(chord, "Helvetica", 10)
        text_height = 10
        self.canvas.drawString(x + 1 * mm, y + 2 * mm, chord) 

    def _render_bar_group_pdf(self, bars: List[Bar], bars_per_line: int, y: float):
        """小節グループをPDFに描画"""
        self.debug_print("\n=== _render_bar_group_pdf ===")
        
        # 小節の幅を計算
        bar_width = (self.usable_width - self.margin) / bars_per_line
        bar_margin = 2 * mm  # 小節の前後のマージン
        self.debug_print(f"Bar width: {bar_width}")
        
        # 各小節を描画
        for i, bar in enumerate(bars):
            x = self.margin + (i * bar_width)
            self.debug_print(f"\nDrawing bar {i} at x={x}, y={y}")
            
            # 繰り返し開始記号を描画
            if bar.is_repeat_start:
                self._draw_repeat_start(x, y)
                self.debug_print("Drew repeat start")
            
            # コードネームを描画（存在する場合）
            if bar.chord:
                self.canvas.setFont("Helvetica", 10)
                self.canvas.drawString(x, y + 3 * mm, bar.chord)
                self.debug_print(f"Drew chord: {bar.chord}")
            
            # 小節線を描画
            self.canvas.line(x, y, x, y - 15 * mm)
            
            # n番カッコを描画（存在する場合）
            if bar.volta_number:
                self._draw_volta(x, y, bar_width, bar.volta_number)
                self.debug_print(f"Drew volta number: {bar.volta_number}")
            
            # 弦を描画
            for string in range(6):
                string_y = y - (string * self.string_spacing)
                self.canvas.line(x, string_y, x + bar_width, string_y)
            
            # 小節内の総ステップ数を計算
            total_steps = sum(note.step for note in bar.notes)
            self.debug_print(f"Total steps in bar: {total_steps}")
            
            # 使用可能な幅を計算
            usable_width = bar_width - (2 * bar_margin)
            step_width = usable_width / total_steps if total_steps > 0 else 0
            
            # 音符を描画
            current_step = 0
            for note in bar.notes:
                if not note.is_rest:
                    # 音符のX座標を計算（ステップ数に基づく）
                    note_x = x + bar_margin + (current_step * step_width)
                    note_y = y - ((note.string - 1) * self.string_spacing)
                    self.canvas.setFont("Helvetica", 8)
                    self.canvas.drawString(note_x, note_y - 2, str(note.fret))
                    self.debug_print(f"Drew note: string={note.string}, fret={note.fret} at x={note_x}")
                current_step += note.step
            
            # 最後の小節線
            x = self.margin + ((i + 1) * bar_width)
            self.canvas.line(x, y, x, y - 15 * mm)
            
            # 繰り返し終了記号を描画
            if bar.is_repeat_end:
                x_end = x + bar_width
                self._draw_repeat_end(x_end, y)
                self.debug_print("Drew repeat end")

    def _draw_slur(self, note_x, note, next_note, x2, y_positions):
        """通常のスラーを描画"""
        x1 = note_x + 1.5 * mm
        y1 = y_positions[note.string - 1] - 2 * mm
        y2 = y_positions[next_note.string - 1] - 2 * mm
        
        # 2本の曲線で描画（より自然な見た目に）
        # 1本目（上側）
        control_y1 = y1 - 3.2 * mm
        control_y2 = y2 - 3.2 * mm
        self.canvas.bezier(x1, y1,
                          x1 + (x2 - x1) * 0.25, control_y1,
                          x1 + (x2 - x1) * 0.75, control_y2,
                          x2, y2)
        
        # 2本目（下側）
        control_y1 = y1 - 2.8 * mm
        control_y2 = y2 - 2.8 * mm
        self.canvas.bezier(x1, y1,
                          x1 + (x2 - x1) * 0.25, control_y1,
                          x1 + (x2 - x1) * 0.75, control_y2,
                          x2, y2)

    def _draw_half_slur(self, note_x, note, x2, y_positions, half: str):
        """スラーの左半分または右半分を描画"""
        x1 = note_x + 1.5 * mm
        y = y_positions[note.string - 1] - 2.0 * mm
        
        if half == "left":
            # 左半分：始点から中央へ（2本の曲線）
            control_y = y - 3.2 * mm
            self.canvas.bezier(x1, y,
                              x1 + (x2 - x1) * 0.25, control_y,
                              x1 + (x2 - x1) * 0.5, control_y,
                              x2, control_y)
            control_y = y - 2.8 * mm
            self.canvas.bezier(x1, y,
                              x1 + (x2 - x1) * 0.25, control_y,
                              x1 + (x2 - x1) * 0.5, control_y,
                              x2, control_y)
        else:
            # 右半分：中央から終点へ（2本の曲線）
            control_y = y - 4.3 * mm
            self.canvas.bezier(x1, control_y,
                              x2 - (x2 - x1) * 0.5, control_y,
                              x2 - (x2 - x1) * 0.25, y,
                              x2, y)
            control_y = y - 3.7 * mm
            self.canvas.bezier(x1, control_y,
                              x2 - (x2 - x1) * 0.5, control_y,
                              x2 - (x2 - x1) * 0.25, y,
                              x2, y) 

    def _calculate_layout(self) -> dict:
        """スコアのレイアウトを計算"""
        layout = {
            'title': {
                'x': 50,  # 左マージン
                'y': 50,  # 上マージン
                'font_size': 16
            },
            'sections': []
        }
        
        current_y = 100  # タイトルの下から開始
        
        for section in self.score.sections:
            section_layout = {
                'name': section.name,
                'y': current_y,
                'columns': []
            }
            
            current_x = 50  # 左マージンから開始
            for column in section.columns:
                column_layout = {
                    'x': current_x,
                    'y': current_y,
                    'width': 200,  # 固定幅（後で調整可能に）
                    'height': 150,  # 固定高さ（後で調整可能に）
                    'bars': []
                }
                
                # 各小節の位置を計算
                bar_width = column_layout['width'] / len(column.bars)
                for i, bar in enumerate(column.bars):
                    bar_layout = {
                        'x': current_x + (i * bar_width),
                        'y': current_y,
                        'width': bar_width,
                        'height': column_layout['height']
                    }
                    column_layout['bars'].append(bar_layout)
                
                section_layout['columns'].append(column_layout)
                current_x += column_layout['width'] + 20  # 20pxの間隔
            
            layout['sections'].append(section_layout)
            current_y += 200  # 次のセクションまでの間隔
        
        return layout 

    def _draw_repeat_start(self, x: float, y: float):
        """繰り返し開始記号を描画"""
        # 太い縦線
        self.canvas.setLineWidth(1.5)
        self.canvas.line(x, y, x, y - 15 * mm)
        
        # ドット
        dot_x = x + 2 * mm
        self.canvas.circle(dot_x, y - 5 * mm, 0.5 * mm, stroke=1, fill=1)
        self.canvas.circle(dot_x, y - 10 * mm, 0.5 * mm, stroke=1, fill=1)
        
        # 線の太さを元に戻す
        self.canvas.setLineWidth(1)

    def _draw_repeat_end(self, x: float, y: float):
        """繰り返し終了記号を描画"""
        # 太い縦線
        self.canvas.setLineWidth(1.5)
        self.canvas.line(x, y, x, y - 15 * mm)
        
        # ドット
        dot_x = x - 2 * mm
        self.canvas.circle(dot_x, y - 5 * mm, 0.5 * mm, stroke=1, fill=1)
        self.canvas.circle(dot_x, y - 10 * mm, 0.5 * mm, stroke=1, fill=1)
        
        # 線の太さを元に戻す
        self.canvas.setLineWidth(1)

    def _draw_volta(self, x: float, y: float, width: float, number: int):
        """n番カッコを描画"""
        # カッコの上部
        bracket_y = y + 6 * mm
        self.canvas.line(x, bracket_y, x, bracket_y + 3 * mm)
        self.canvas.line(x, bracket_y + 3 * mm, x + width, bracket_y + 3 * mm)
        
        # 番号を描画
        self.canvas.setFont("Helvetica", 8)
        self.canvas.drawString(x + 2 * mm, bracket_y + 1 * mm, str(number)) 