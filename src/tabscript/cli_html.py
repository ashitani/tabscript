#!/usr/bin/env python3
import sys
import os
import argparse
from tabscript import Parser, Renderer
from tabscript.exceptions import ParseError, TabScriptError
from pdf2image import convert_from_path

def main():
    """HTML出力用のコマンドラインインターフェース"""
    # 引数のパース
    parser = argparse.ArgumentParser(description='Convert TabScript files to HTML')
    parser.add_argument('files', nargs='+', help='Input TabScript files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--debug-level', type=int, choices=[1, 2, 3], default=1, 
                        help='Debug level (1: basic, 2: detailed, 3: verbose)')
    parser.add_argument('--show-length', action='store_true',
                        help='Show note lengths and tuplets (default: False)')
    parser.add_argument('--dpi', type=int, default=200,
                        help='Image DPI for PNG conversion (default: 200)')
    parser.add_argument('--output-dir', default='.',
                        help='Output directory for HTML and images (default: current directory)')
    args = parser.parse_args()
    
    # パーサーの初期化
    tab_parser = Parser(debug_mode=args.debug, debug_level=args.debug_level)
    
    # 各ファイルを処理
    for input_file in args.files:
        try:
            # 出力ファイル名を生成
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_dir = os.path.dirname(os.path.abspath(input_file))
            os.makedirs(output_dir, exist_ok=True)
            
            # 出力ファイルのパス
            png_path = os.path.join(output_dir, f"{base_name}.png")
            html_path = os.path.join(output_dir, f"{base_name}.html")
            
            # パースして出力
            score = tab_parser.parse(input_file)
            
            # レンダラーの初期化とレンダリング
            renderer = Renderer(score, debug_mode=args.debug, show_length=args.show_length)
            
            # 一時的なPDFファイルを作成
            temp_pdf = os.path.join(output_dir, f"{base_name}_temp.pdf")
            renderer.render_pdf(temp_pdf)
            
            try:
                # PDFをPNGに変換
                images = convert_from_path(temp_pdf, dpi=args.dpi)
                
                # 各ページをPNGとして保存
                png_paths = []
                for i, image in enumerate(images):
                    png_path = os.path.join(output_dir, f"{base_name}_page{i+1}.png")
                    image.save(png_path, 'PNG')
                    png_paths.append(os.path.basename(png_path))
            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_pdf):
                    os.remove(temp_pdf)
            
            # HTMLファイルの生成
            with open(html_path, 'w', encoding='utf-8') as f:
                html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{score.title}</title>
    <style>
        body {{
            margin: 0;
            padding: 10px;
            background-color: #f0f0f0;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
        }}
        .preview-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            justify-content: center;
            align-items: flex-start;
            width: 100%;
            max-width: 100%;
            padding: 0;
            box-sizing: border-box;
        }}
        .preview-row {{
            display: flex;
            gap: 5px;
            justify-content: center;
            width: 100%;
            margin-bottom: 5px;
            box-sizing: border-box;
        }}
        .preview-image {{
            width: calc((100vw - 20px) / 3);
            height: calc(100vh - 20px);
            object-fit: contain;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            box-sizing: border-box;
        }}
    </style>
</head>
<body>
    <div class="preview-container">
'''
                # 画像の行を生成
                for j in range(0, len(png_paths), 3):
                    html_content += '        <div class="preview-row">\n'
                    for i, png_path in enumerate(png_paths[j:j+3]):
                        html_content += f'            <img src="{png_path}" class="preview-image" alt="Page {i+1}" />\n'
                    html_content += '        </div>\n'
                
                html_content += '''    </div>
</body>
</html>'''
                f.write(html_content)
            
            print(f"Generated {html_path} and {len(png_paths)} PNG files")
            
        except Exception as e:
            print(f"Error processing {input_file}: {str(e)}")
            if args.debug:
                import traceback
                traceback.print_exc()
            continue

if __name__ == '__main__':
    main() 