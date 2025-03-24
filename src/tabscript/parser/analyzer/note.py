def _parse_note(self, token, default_duration="4", chord=None):
    """音符トークンを解析してNoteオブジェクトを返す
    
    Args:
        token: 解析する音符トークン
        default_duration: デフォルトの音価
        chord: コード名（省略可能）
    
    Returns:
        Note: 解析された音符オブジェクト
    """
    self.debug_print(f"parse_note: token='{token}', default_duration='{default_duration}', chord='{chord}'")
    
    # 休符の処理
    if token.startswith('r'):
        return self._parse_rest(token, default_duration)
    
    # 和音の処理
    if token.startswith('(') and token.endswith(')'):
        return self._parse_chord(token, default_duration, chord)
    
    # 上下移動の処理
    if token.startswith('u') or token.startswith('d'):
        return self._parse_move_direction(token, default_duration, chord)
    
    # 接続フラグの確認（トークン全体でチェック）
    connect_next = False
    if token.endswith('&'):
        connect_next = True
        token = token[:-1]  # '&'を削除
    
    # 弦-フレット-音価の分離
    parts = token.split('-')
    
    # 過去の弦とフレットを記録（省略時のデフォルト用）
    last_string = self.last_string
    
    # 標準形式: 弦-フレット:音価
    if len(parts) == 2:
        string_part = parts[0]
        fret_part = parts[1]
        
        # 弦番号を解析
        try:
            string = int(string_part)
            self.last_string = string  # 弦を記録
        except ValueError:
            # 弦番号が数値でない場合はエラー
            raise ValueError(f"Invalid string number: {string_part}")
        
        # フレットと音価を分離
        fret_duration = fret_part.split(':')
        if len(fret_duration) == 1:
            # フレット部分で再度&をチェック（フレット番号内に&がある場合）
            fret = fret_duration[0]
            if fret.endswith('&'):
                connect_next = True
                fret = fret[:-1]  # '&'を削除
            duration = default_duration
        elif len(fret_duration) == 2:
            fret = fret_duration[0]
            # フレット部分で再度&をチェック
            if fret.endswith('&'):
                connect_next = True
                fret = fret[:-1]  # '&'を削除
            duration = fret_duration[1]
            self.last_duration = duration  # 音価を記録
        else:
            raise ValueError(f"Invalid fret-duration format: {fret_part}")
    
    # 省略形式1: フレットのみ（弦を継承）
    elif len(parts) == 1:
        string = last_string  # 直前の弦を継承
        
        # フレットと音価を分離
        fret_duration = parts[0].split(':')
        if len(fret_duration) == 1:
            fret = fret_duration[0]
            duration = default_duration
        elif len(fret_duration) == 2:
            fret = fret_duration[0]
            duration = fret_duration[1]
            self.last_duration = duration  # 音価を記録
        else:
            raise ValueError(f"Invalid fret-duration format: {parts[0]}")
    
    else:
        raise ValueError(f"Invalid note format: {token}")
    
    # デバッグ出力を追加して、&が正しく除去されていることを確認
    self.debug_print(f"After parsing: string={string}, fret={fret}, duration={duration}, connect_next={connect_next}")
    
    # 最終チェック：ミュート音か
    is_muted = (fret.upper() == 'X')
    
    # Noteオブジェクトを作成
    note = Note(
        string=string,
        fret=fret,
        duration=duration,
        chord=chord,
        is_muted=is_muted,
        connect_next=connect_next
    )
    
    return note 

def parse_chord_notation(self, token, default_duration=None, chord=None):
    """和音表記（括弧で囲まれた複数の音符）をパースする
    
    Args:
        token: 和音表記トークン（例：'(1-2 2-2 3-3):4'）
        default_duration: デフォルト音価
        chord: コード名
    
    Returns:
        Note: 和音の主音（chord_notesに他の音符が含まれる）
    """
    # デバッグ出力
    self.debug_print(f"parse_chord_notation: token='{token}', default_duration='{default_duration}', chord='{chord}'")
    
    # 括弧と音価の分離
    if token.startswith('(') and ')' in token:
        chord_content = token[1:token.find(')')].strip()
        
        # 音価の取得（括弧の後に:区切りで音価が指定されている場合）
        duration_part = token[token.find(')'):]
        if ':' in duration_part:
            duration = duration_part.split(':')[1]
        else:
            duration = default_duration
        
        # コンテンツを空白で分割して各音符を取得
        notes_tokens = chord_content.split()
        if not notes_tokens:
            raise ValueError(f"Empty chord notation: {token}")
        
        # 最初の音符を主音として処理
        main_note = self.parse_note(notes_tokens[0], duration, chord)
        
        # 和音フラグの設定
        main_note.is_chord = True
        main_note.is_chord_start = True
        
        # 残りの音符を和音の構成音として追加
        for note_token in notes_tokens[1:]:
            chord_note = self.parse_note(note_token, duration, chord)
            chord_note.is_chord = True
            main_note.chord_notes.append(chord_note)
        
        return main_note
    else:
        raise ValueError(f"Invalid chord notation format: {token}") 