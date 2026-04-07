# 議論メモ: VS Code Python インタープリター設定とAnaconda廃止

**日付**: 2026-04-06
**議論ID**: disc-2026-04-06-vscode-env-setup
**参加**: ユーザー + AI

## 背景・コンテキスト

VS Code上で以下の警告が表示された:
> 既定のインタープリター パス '/opt/anaconda3/bin/python' を解決できませんでした: Could not resolve interpreter path '/opt/anaconda3/bin/python'

## 原因

VS Codeユーザー設定（`~/Library/Application Support/Code/User/settings.json`）に以下が設定されていたが、Anacondaがこのマシンに未インストール（`/opt/anaconda3` が存在しない）。

```json
"python.defaultInterpreterPath": "/opt/anaconda3/bin/python",
"python.condaPath": "/opt/anaconda3/bin/conda"
```

## 実施した対応

1. `.vscode/settings.json` を新規作成:
   ```json
   { "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python" }
   ```
2. VS Codeユーザー設定のAnaconda参照2行を削除し、`"${workspaceFolder}/.venv/bin/python"` に変更

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-06-001 | `.vscode/` は `.gitignore` のまま維持（git管理しない） | Windowsとmacosで `bin/python` vs `Scripts/python.exe` のパスが異なるため共有不可 |
| dec-2026-04-06-002 | Anacondaは今後使用しない。uv環境（`.venv`）を標準とする | Anacondaが未インストールで使用実態もない |
| dec-2026-04-06-003 | VS Codeのデフォルトインタープリターは `${workspaceFolder}/.venv/bin/python`（macOS/Linux） | uvの標準venvパス。`uv sync` 後に自動利用可能 |

## アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-04-06-001 | Windowsマシンで `.venv\Scripts\python.exe` をVS Codeインタープリターに手動設定 | 中 |

## 次回の議論トピック

- 特になし（環境設定の一時対応）

## 参考情報

- macOS: `.venv/bin/python` → `uv sync` で自動作成済み（Python 3.12.12）
- Windows: `.venv/Scripts/python.exe` → `uv sync` 後に VS Code で手動選択が必要
- `.vscode/` の git 除外ルール: `.gitignore` 21行目
