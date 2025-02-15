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
    args = parse_args()
    
    parser = Parser()
    parser.debug_mode = args.debug  # デバッグモードを設定
    
    if args.debug:
        parser.debug_print("DEBUG: Starting main()")
    
    try:
        score = parser.parse(args.input)
        
        if args.output:
            parser.render_score(args.output)
            print(f"Generated: {args.output}")
        else:
            # 出力ファイル名が指定されていない場合は、入力ファイル名から生成
            output_path = os.path.splitext(args.input)[0] + ".pdf"
            parser.render_score(output_path)
            print(f"Generated: {output_path}")
    
    except (ParseError, TabScriptError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 