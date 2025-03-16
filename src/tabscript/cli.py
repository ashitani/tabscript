#!/usr/bin/env python3
import sys
import os
import glob
import argparse
from tabscript import Parser, Renderer
from tabscript.exceptions import ParseError, TabScriptError

# 標準出力をバッファリングなしに設定
if sys.stdout.isatty():
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(description='Convert TabScript files to PDF or text')
    parser.add_argument('input', help='Input TabScript file')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    return parser.parse_args()

def main():
    """コマンドラインインターフェース"""
    # 引数のパース
    parser = argparse.ArgumentParser(description='Convert TabScript files to PDF or text')
    parser.add_argument('files', nargs='+', help='Input TabScript files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--debug-level', type=int, choices=[1, 2, 3], default=1, 
                        help='Debug level (1: basic, 2: detailed, 3: verbose)')
    args = parser.parse_args()
    
    # 出力形式の判断
    is_pdf = 'tab2pdf' in sys.argv[0]
    extension = '.pdf' if is_pdf else '.txt'
    
    # パーサーの初期化
    tab_parser = Parser(debug_mode=args.debug, debug_level=args.debug_level)  # デバッグレベルを設定
    
    # 各ファイルを処理
    for input_file in args.files:
        try:
            # 出力ファイル名を生成
            output_file = input_file.rsplit('.', 1)[0] + extension
            
            # パースして出力
            score = tab_parser.parse(input_file)
            
            # レンダラーの初期化とレンダリング
            if is_pdf:
                renderer = Renderer(score, debug_mode=args.debug)
                renderer.render_pdf(output_file, debug=args.debug)
            else:
                # テキスト出力の場合の処理（未実装）
                with open(output_file, 'w') as f:
                    f.write(str(score))
            
            print(f"Generated {output_file}")
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")
            if args.debug:
                import traceback
                traceback.print_exc()
            continue

if __name__ == "__main__":
    main() 