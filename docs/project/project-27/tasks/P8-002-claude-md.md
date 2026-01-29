# P8-002: CLAUDE.md 更新

## 概要

CLAUDE.md に新しい CLI コマンドを追加する。

## フェーズ

Phase 8: ドキュメント・移行

## 依存タスク

- P8-001: src/news/README.md 更新

## 成果物

- `CLAUDE.md`（更新）

## 実装内容

### 金融コンテンツ作成セクションに追加

```markdown
### 金融コンテンツ作成

| コマンド | 説明 | スキル |
|----------|------|--------|
| `/finance-news-workflow-py` | Python版金融ニュース収集（ドライラン対応） | - |
| `/finance-news-workflow` | 金融ニュース収集の3フェーズワークフロー | `finance-news-workflow` |
...
```

### 新コマンドの詳細

```markdown
## `/finance-news-workflow-py`

Python CLIベースの金融ニュース収集ワークフロー。

```bash
# 基本実行
uv run python -m news.scripts.finance_news_workflow

# オプション
--status index,stock    # 対象Status
--dry-run              # Issue作成スキップ
--max-articles 50      # 記事数制限
--verbose              # 詳細ログ
```

**特徴**:
- trafilatura による安定した本文抽出
- Claude Agent SDK による構造化要約
- asyncio による並列処理
- 詳細なエラーレポート
```

## 受け入れ条件

- [ ] コマンド一覧に新コマンドが追加されている
- [ ] コマンドの使用方法が記載されている
- [ ] オプションの説明がある
- [ ] 既存の `/finance-news-workflow` との違いが明確
- [ ] Markdown 構文が正しい

## 参照

- 既存の CLAUDE.md 構造
- project.md: CLI使用方法 セクション
