import * as vscode from 'vscode';
import { exec } from 'child_process';
import * as path from 'path';

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
    const outputPath = inputPath.replace(/\.tab$/, '.pdf');
    const command = `tab2pdf "${inputPath}"`;
    vscode.window.showInformationMessage(`実行コマンド: ${command}\n入力: ${inputPath}\n出力: ${outputPath}`);
    exec(command, (err: Error | null, stdout: string, stderr: string) => {
      if (err) {
        vscode.window.showErrorMessage(`tab2pdf 実行エラー: ${err.message}\n${stderr}`);
        return;
      }
      if (stdout) {
        vscode.window.showInformationMessage(`tab2pdf 出力: ${stdout}`);
      }
      // PDFファイルの存在確認
      if (!require('fs').existsSync(outputPath)) {
        vscode.window.showErrorMessage(`PDFファイルが生成されませんでした: ${outputPath}`);
        return;
      }
      // PDFファイルをVSCodeで開く
      vscode.commands.executeCommand('vscode.open', vscode.Uri.file(outputPath), vscode.ViewColumn.Beside);
    });
  });
  context.subscriptions.push(disposable);

  // 保存時の自動実行
  vscode.workspace.onDidSaveTextDocument(async (document: vscode.TextDocument) => {
    if (document.fileName.endsWith('.tab')) {
      const inputPath = document.fileName;
      const outputPath = inputPath.replace(/\.tab$/, '.pdf');
      exec(`tab2pdf "${inputPath}"`, (err: Error | null, stdout: string, stderr: string) => {
        if (err) {
          vscode.window.showErrorMessage('tab2pdf 実行エラー: ' + stderr);
          return;
        }
        // PDFファイルをVSCodeで開く
        vscode.commands.executeCommand('vscode.open', vscode.Uri.file(outputPath), vscode.ViewColumn.Beside);
      });
    }
  });
}

export function deactivate() {} 