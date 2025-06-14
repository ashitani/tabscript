import * as vscode from 'vscode';
import { exec } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

function getWebviewContent(imagePath: string): string {
  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      margin: 0;
      padding: 20px;
      background-color: #1e1e1e;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    .preview-container {
      display: flex;
      flex-direction: column;
      gap: 20px;
      align-items: center;
      max-width: 100%;
    }
    .preview-image {
      max-width: 100%;
      height: auto;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .page-container {
      display: flex;
      flex-direction: column;
      gap: 20px;
      align-items: center;
    }
    .page-number {
      color: #ffffff;
      font-size: 0.9em;
      margin-top: 5px;
    }
  </style>
</head>
<body>
  <div class="preview-container">
    <div class="page-container">
      <div>
        <img src="${vscode.Uri.file(imagePath).with({ scheme: 'vscode-resource' })}" class="preview-image" />
        <div class="page-number">Page 1</div>
      </div>
    </div>
  </div>
</body>
</html>`;
}

// 画像ファイルの検索
function findImageFiles(outputDir: string, baseName: string): string[] {
  const files = fs.readdirSync(outputDir);
  const pattern = new RegExp(`^${baseName}_page\\d+\\.png$`);
  return files
    .filter(file => pattern.test(file))
    .sort((a, b) => {
      const numA = parseInt(a.match(/\d+/)?.[0] || '0');
      const numB = parseInt(b.match(/\d+/)?.[0] || '0');
      return numA - numB;
    })
    .map(file => path.join(outputDir, file));
}

export function activate(context: vscode.ExtensionContext) {
  // コマンド登録
  const disposable = vscode.commands.registerCommand('extension.showPreview', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showInformationMessage('アクティブなエディタがありません');
      return;
    }
    const document = editor.document;
    if (!document.fileName.endsWith('.tab')) {
      vscode.window.showInformationMessage('.tabファイルを開いてください');
      return;
    }
    const inputPath = document.fileName;
    const outputDir = path.join(path.dirname(inputPath), '.tabscript-preview');
    const baseName = path.basename(inputPath, '.tab');
    
    // 出力ディレクトリの作成
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    const command = `tab2html "${inputPath}" --output-dir "${outputDir}"`;
    vscode.window.showInformationMessage(`実行コマンド: ${command}\n入力: ${inputPath}\n出力ディレクトリ: ${outputDir}`);
    
    exec(command, (err: Error | null, stdout: string, stderr: string) => {
      if (err) {
        vscode.window.showErrorMessage(`tab2html 実行エラー: ${err.message}\n${stderr}`);
        return;
      }
      if (stdout) {
        vscode.window.showInformationMessage(`tab2html 出力: ${stdout}`);
      }
      
      // 画像ファイルの検索
      const imageFiles = findImageFiles(outputDir, baseName);
      if (imageFiles.length === 0) {
        vscode.window.showErrorMessage(`PNGファイルが生成されませんでした: ${outputDir}`);
        return;
      }
      
      // HTMLビューワーを表示
      const panel = vscode.window.createWebviewPanel(
        'tabscriptPreview',
        'TabScript Preview',
        vscode.ViewColumn.Beside,
        {
          enableScripts: true,
          retainContextWhenHidden: true
        }
      );
      
      // HTMLコンテンツの生成
      panel.webview.html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #1e1e1e;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .preview-container {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: center;
      align-items: flex-start;
      padding: 10px;
      max-width: 100vw;
      box-sizing: border-box;
    }
    .preview-image {
      width: calc((100vw - 20px - ${imageFiles.length - 1} * 10px) / ${imageFiles.length});
      height: auto;
      object-fit: contain;
    }
  </style>
</head>
<body>
  <div class="preview-container">
    ${imageFiles.map((file, i) => `
      <img src="${vscode.Uri.file(file).with({ scheme: 'vscode-resource' })}" class="preview-image" alt="Page ${i + 1}" />
    `).join('')}
  </div>
</body>
</html>`;
    });
  });
  context.subscriptions.push(disposable);

  // 保存時の自動実行
  vscode.workspace.onDidSaveTextDocument(async (document: vscode.TextDocument) => {
    if (document.fileName.endsWith('.tab')) {
      const inputPath = document.fileName;
      const outputDir = path.join(path.dirname(inputPath), '.tabscript-preview');
      const baseName = path.basename(inputPath, '.tab');
      
      // 出力ディレクトリの作成
      if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir, { recursive: true });
      }
      
      exec(`tab2html "${inputPath}" --output-dir "${outputDir}"`, (err: Error | null, stdout: string, stderr: string) => {
        if (err) {
          vscode.window.showErrorMessage('tab2html 実行エラー: ' + stderr);
          return;
        }
        
        // 画像ファイルの検索
        const imageFiles = findImageFiles(outputDir, baseName);
        if (imageFiles.length === 0) {
          vscode.window.showErrorMessage(`PNGファイルが生成されませんでした: ${outputDir}`);
          return;
        }
        
        // HTMLビューワーを表示
        const panel = vscode.window.createWebviewPanel(
          'tabscriptPreview',
          'TabScript Preview',
          vscode.ViewColumn.Beside,
          {
            enableScripts: true,
            retainContextWhenHidden: true
          }
        );
        
        // HTMLコンテンツの生成
        panel.webview.html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {
      margin: 0;
      padding: 0;
      background-color: #1e1e1e;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
    }
    .preview-container {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      justify-content: center;
      align-items: flex-start;
      padding: 10px;
      max-width: 100vw;
      box-sizing: border-box;
    }
    .preview-image {
      width: calc((100vw - 20px - ${imageFiles.length - 1} * 10px) / ${imageFiles.length});
      height: auto;
      object-fit: contain;
    }
  </style>
</head>
<body>
  <div class="preview-container">
    ${imageFiles.map((file, i) => `
      <img src="${vscode.Uri.file(file).with({ scheme: 'vscode-resource' })}" class="preview-image" alt="Page ${i + 1}" />
    `).join('')}
  </div>
</body>
</html>`;
      });
    }
  });
}

export function deactivate() {} 