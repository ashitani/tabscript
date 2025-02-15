from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from .models import Score, Section, Bar, Note
from .exceptions import TabScriptError
from typing import List, Tuple

class Renderer:
    def __init__(self, score: Score):
        self.score = score
        self.canvas = None
        self.current_x = 0
        self.current_y = 0
        self.debug_mode = False
        
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
        self.debug_mode = debug
        
        self.debug_print(f"render_pdf start: score object id = {id(self.score)}")
        
        # A4縦向きでキャンバスを作成
        self.canvas = canvas.Canvas(output_path, pagesize=A4)
        
        # タイトルと設定を出力
        y = self.page_height - self.margin - 5 * mm
        self.draw_title(y)
        y -= 5 * mm
        self.draw_metadata(y)
        y -= 5 * mm
        
        # セクションごとに描画
        for section in self.score.sections:
            self.debug_print(f"Processing section: {section.name}")
            
            # セクション名を描画
            self.canvas.setFont("Helvetica-Bold", 12)
            self.canvas.drawString(self.margin, y, f"[{section.name}]")
            y -= 8 * mm
            
            # 各行を描画
            for column in section.columns:
                self._render_bar_group_pdf(column.bars, column.bars_per_line, y)
                y -= 22 * mm  # 20mmから22mmに変更
            
            y -= self.section_spacing + 2 * mm  # セクション間の間隔を2mm広く
            
            # 新しいページが必要かチェック
            if y < self.margin_bottom:
                self.canvas.showPage()
                y = self.page_height - self.margin - 5 * mm
        
        self.canvas.save()

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
            # タイトルと設定を出力
            f.write(f"Title: {self.score.title}\n")
            f.write(f"Tuning: {self.score.tuning}\n")
            f.write(f"Beat: {self.score.beat}\n\n")

            # 各セクションを出力
            for section in self.score.sections:
                f.write(f"[{section.name}]\n\n")
                
                # 各小節を出力
                for bar in section.bars:
                    self._render_bar_text(f, bar)
                    f.write("\n")  # 小節間に空行を挿入
                
                f.write("\n")  # セクション間に空行を挿入

    def _render_bar_text(self, f, bar: Bar):
        """小節をテキスト形式で出力"""
        string_count = self._get_string_count()
        resolution = self._calculate_bar_resolution(bar)
        bar_margin = 1  # 2から1に変更（1文字分の余白）
        
        # 各弦の内容を構築
        lines = ["" for _ in range(string_count + 1)]  # +1 for chord line
        
        # 余白を追加
        for i in range(len(lines)):
            lines[i] = "-" * bar_margin
        
        # 各音符をステップに変換して配置
        for note in bar.notes:
            steps = self._duration_to_steps(note.duration, resolution)
            
            # コード行の処理
            if note.chord:
                # コードの前後にパディングを追加
                chord_str = note.chord.center(4 * steps)
                lines[0] += chord_str
            else:
                # コードがない場合は空白を追加
                lines[0] += " " * (4 * steps)
            
            if note.is_rest:
                # 休符の場合は全ての弦に空白を追加
                for i in range(string_count):
                    lines[i + 1] += "-" * (4 * steps)
            else:
                # 和音の場合は全ての構成音を同時に配置
                if note.is_chord:
                    # 主音を配置
                    for string in range(string_count):
                        if string + 1 == note.string:
                            fret_str = "X " if note.is_muted else str(note.fret).rjust(2, '-')
                            lines[string + 1] += f"--{fret_str}" + "-" * (4 * (steps - 1))
                        else:
                            lines[string + 1] += "-" * (4 * steps)
                    # 和音の他の音を配置
                    for chord_note in note.chord_notes:
                        lines[chord_note.string] = (
                            lines[chord_note.string][:-4*steps] +
                            f"--{'X ' if chord_note.is_muted else str(chord_note.fret).rjust(2, '-')}" +
                            "-" * (4 * (steps - 1))
                        )
                else:
                    # 通常の音符の場合
                    for string in range(string_count):
                        if string + 1 == note.string:
                            fret_str = "X " if note.is_muted else str(note.fret).rjust(2, '-')
                            lines[string + 1] += f"--{fret_str}" + "-" * (4 * (steps - 1))
                        else:
                            lines[string + 1] += "-" * (4 * steps)
        
        # 各弦の内容を小節線で囲んで出力
        f.write(f"|{lines[0]}|\n")  # コード行
        for line in lines[1:]:
            f.write(f"|{line}|\n")

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
        """小節グループを描画"""
        self.debug_print("\n=== _render_bar_group_pdf ===")
        self.debug_print("Input bars:")
        for i, bar in enumerate(bars):
            self.debug_print(f"\nBar {i}:")
            self.debug_print(f"  Resolution: {bar.resolution}")
            for j, note in enumerate(bar.notes):
                self.debug_print(f"  Note {j}:")
                self.debug_print(f"    string: {note.string}")
                self.debug_print(f"    fret: {note.fret}")
                self.debug_print(f"    duration: {note.duration}")
                self.debug_print(f"    step: {note.step}")  # パース時に計算済み！

        string_count = self._get_string_count()
        bar_margin = 1.5 * mm  # 小節の前後のマージン
        
        # 小節グループの幅を計算
        if bars_per_line == 1:
            group_width = self.usable_width
            bar_width = group_width
        else:
            group_width = self.usable_width / bars_per_line * len(bars)
            bar_width = group_width / len(bars)
        
        # 各弦の位置を計算（current_yの代わりにyを使用）
        y_positions = [y - (i * self.string_spacing) for i in range(string_count)]
        
        # 小節を順に描画
        current_x = self.margin
        for bar_index, bar in enumerate(bars):
            # 小節内の総ステップ数を計算（パース時の値を使用）
            total_steps = sum(note.step for note in bar.notes)
            self.debug_print(f"  total_steps: {total_steps}")
            
            # このステップ幅で描画（前後の余白を考慮）
            usable_width = bar_width - (2 * bar_margin)  # 前後のマージンを引く
            step_width = usable_width / total_steps
            
            # 縦線と横線を描画
            self.canvas.line(current_x, y_positions[0], current_x, y_positions[-1])
            for y in y_positions:
                self.canvas.line(current_x, y, current_x + bar_width, y)
            
            # 音符を配置（開始マージンから開始）
            note_x = current_x + bar_margin
            for note in bar.notes:
                # パース時に計算済みのステップ数を使用
                note_width = note.step * step_width
                
                # コードを描画
                if note.chord:
                    self._draw_chord(note_x, y_positions[0], note.chord)
                
                # 音符を描画
                if not note.is_rest:
                    y = y_positions[note.string - 1]
                    self._draw_fret_number(note_x, y, note.fret)
                
                note_x += note_width
            
            current_x += bar_width
        
        # 最後の縦線を描画
        self.canvas.line(current_x, y_positions[0], current_x, y_positions[-1]) 