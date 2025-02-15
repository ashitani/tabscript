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
    if len(sys.argv) < 2:
        print("Usage: tab2pdf input.tab [input2.tab ...]")
        print("       tab2txt input.tab [input2.tab ...]")
        sys.exit(1)
    
    # コマンド名から出力形式を判断
    is_pdf = 'tab2pdf' in sys.argv[0]
    extension = '.pdf' if is_pdf else '.txt'
    
    # 入力ファイルのパターンを展開
    input_files = []
    for pattern in sys.argv[1:]:
        input_files.extend(glob.glob(pattern))
    
    if not input_files:
        print("No input files found.")
        sys.exit(1)
    
    # 各ファイルを処理
    parser = Parser()
    for input_file in input_files:
        try:
            # 出力ファイル名を生成
            output_file = input_file.rsplit('.', 1)[0] + extension
            
            # パースして出力
            score = parser.parse(input_file)
            parser.render_score(output_file)
            
            print(f"Generated {output_file}")
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")
            continue

if __name__ == "__main__":
    main() 