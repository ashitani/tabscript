class Note:
    """音符を表すクラス"""
    
    def __init__(self, string=None, fret=None, duration=None, step=None, is_rest=False, is_muted=False, is_chord=False, is_chord_start=False, is_triplet=False, triplet_notes=None, connect_next=False, is_up_move=False, is_down_move=False, chord=None):
        self.string = string  # 弦番号
        self.fret = fret      # フレット番号
        self.duration = duration  # 音価
        self.step = step      # 小節内での位置
        self.is_rest = is_rest  # 休符
        self.is_muted = is_muted  # ミュート
        self.is_chord = is_chord  # 和音
        self.is_chord_start = is_chord_start  # 和音の開始音符
        self.is_triplet = is_triplet  # 三連符グループ
        self.triplet_notes = triplet_notes if triplet_notes is not None else []  # 三連符グループ内の音符リスト
        self.connect_next = connect_next  # 次の音符と接続
        self.is_up_move = is_up_move  # 上移動
        self.is_down_move = is_down_move  # 下移動
        self.chord = chord  # コード名
        # 音符の種類に応じた初期化
        if fret == "r":
            self.is_rest = True
        elif fret in ["x", "X"]:
            self.is_muted = True
            self.fret = "x"  # 小文字xで統一 