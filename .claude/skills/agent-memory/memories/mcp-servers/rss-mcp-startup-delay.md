---
summary: "RSS MCPサーバーの起動遅延問題と対処法（3秒待機リトライで解決）"
created: 2026-01-15
status: resolved
tags: [mcp, rss, startup, retry, troubleshooting]
related: [.claude/commands/collect-finance-news.md, .mcp.json, src/rss/mcp/server.py]
---

# RSS MCP サーバーの起動遅延問題

## 問題の概要

Claude Codeセッション開始直後に RSS MCPツールを使用しようとすると、"No matching MCP tools found" エラーが発生する。これは、MCPサーバーの起動が完了していないことが原因。

## 発生状況

### 失敗パターン（セッション開始直後）

```
MCPSearch: select:mcp__rss__list_feeds
→ Result: No matching MCP tools found

MCPSearch: select:mcp__rss__get_items
→ Result: No matching MCP tools found
```

### 成功パターン（数秒後）

```
MCPSearch: query="rss", max_results=5
→ Result: 7 RSS MCP tools found
```

## 根本原因

1. **非同期起動**: MCPサーバーは Claude Code 起動時に非同期でバックグラウンド起動
2. **起動時間**: `uv run rss-mcp` コマンドの実行には2-5秒かかる
   - Python環境の準備
   - 依存関係の解決
   - MCPサーバープロセスの起動
   - ツール定義の登録
3. **タイミング問題**: セッション開始直後の最初のコマンド実行時にはサーバーが完全に起動していない

## 対処法（実装済み）

### リトライロジック

`.claude/commands/collect-finance-news.md` に実装：

```
[試行1] MCPSearch: query="rss", max_results=5
↓ 失敗時
[待機] 3秒待機
↓
[試行2] MCPSearch: query="rss", max_results=5
↓ それでも失敗時
エラー報告
```

### 実装のポイント

1. **キーワード検索を使用**: `select:mcp__rss__*` ではなく `query="rss"` を使用
   - 完全名指定（`select:`）は起動完了後でないと動作しない
   - キーワード検索の方が柔軟

2. **待機時間**: 3秒
   - 2秒では不十分な場合がある
   - 5秒では待ちすぎ
   - 3秒が最適なバランス

3. **最大2回試行**:
   - 1回目: 即座に検索
   - 2回目: 3秒待機後に検索
   - 2回失敗したら本当に問題がある

## 他のMCPサーバーでの応用

この問題は RSS MCP に限らず、全てのMCPサーバーで発生する可能性がある。

### 起動が遅いMCPサーバーの例

- **Python系**: `uv run` や `uvx` で起動するもの
  - rss-mcp
  - sec-edgar-mcp
  - その他カスタムMCPサーバー

- **Node.js系**: `npx` で起動するもの
  - @modelcontextprotocol/server-*
  - 初回実行時はパッケージダウンロードで更に遅い

### 推奨パターン

MCPツールを使用する全てのコマンドで、リトライロジックを実装すべき：

```
1. MCPSearch: query="{keyword}"
2. 結果が空の場合 → 3秒待機
3. MCPSearch: query="{keyword}" (再試行)
4. それでも空の場合 → エラー報告
```

## 手動対処法

自動リトライでも失敗する場合：

1. **Claude Code を再起動**: MCPサーバーを完全にリセット
2. **.mcp.json の確認**: JSON構文エラーや設定ミスをチェック
3. **MCPサーバーの手動テスト**: `uv run rss-mcp --version` で起動確認
4. **ログ確認**: Claude Code のログでMCPサーバーのエラーを確認

## 関連ファイル

- **コマンド定義**: `.claude/commands/collect-finance-news.md`
- **MCP設定**: `.mcp.json`
- **RSS MCPサーバー**: `src/rss/mcp/server.py`

## 学んだこと

1. **MCPサーバーは即座に利用可能ではない**: 起動に数秒かかる
2. **リトライは必須**: セッション開始直後のコマンドでは特に重要
3. **キーワード検索の方が柔軟**: `select:` よりも `query=` が推奨
4. **3秒待機が最適**: 2秒では不十分、5秒では遅すぎる
5. **エラーメッセージは明確に**: ユーザーに状況を正確に伝える

## ステータス

✅ **解決済み**

- リトライロジックを実装
- コマンド定義に詳細なドキュメントを追加
- エラーハンドリングを強化

今後、新しいMCPツールを使用するコマンドを作成する際は、このパターンを適用すること。
