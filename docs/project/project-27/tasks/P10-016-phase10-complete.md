# P10-016: Phase 10テスト・ドキュメント

## 概要

Phase 10の全機能をテストし、ドキュメントを更新する。

## タスク内容

### 1. 統合テスト

Phase 10の全機能が連携して動作することを確認:

```bash
# ドライランで全機能テスト
uv run python -m news.scripts.finance_news_workflow --dry-run --verbose

# ログ確認
tail -f logs/news-workflow-*.log
```

### 2. テスト実行

```bash
# 全テスト実行
make test

# Phase 10関連のテストのみ
uv run pytest tests/news/ -v -k "phase10 or playwright or domain or user_agent"

# カバレッジ
make test-cov
```

### 3. ドキュメント更新

| ファイル | 更新内容 |
|----------|----------|
| `src/news/README.md` | 新機能の説明追加 |
| `CLAUDE.md` | Phase 10完了のマーク |
| `data/config/news-collection-config.yaml` | 設定項目のコメント追加 |

### 4. src/news/README.md 更新内容

```markdown
## 信頼性向上機能 (Phase 10)

### ドメインブロックリスト

ペイウォールやボット検出を行うサイトを自動的にスキップ:

```yaml
# data/config/news-collection-config.yaml
blocked_domains:
  - seekingalpha.com
  - wsj.com
  - reuters.com
```

### User-Agentローテーション

複数のUser-Agentをランダムに使用:

```yaml
extraction:
  user_agent_rotation:
    enabled: true
    user_agents:
      - "Mozilla/5.0 (Windows NT 10.0; ..."
```

### Playwrightフォールバック

trafilatura失敗時にPlaywrightで再取得:

```yaml
extraction:
  playwright_fallback:
    enabled: true
    browser: chromium
    headless: true
```

### ログ出力

- コンソール: INFO（`--verbose` でDEBUG）
- ファイル: 常にDEBUG（詳細な障害分析用）
- 出力先: `logs/news-workflow-{date}.log`
```

## 受け入れ条件

- [ ] 全テストがパス（`make check-all`）
- [ ] ドライランが正常に完了
- [ ] ログにDEBUG情報が出力される
- [ ] ブロックドメインがスキップされる
- [ ] フォールバックが動作する（該当サイトがある場合）
- [ ] ドキュメントが更新される

## チェックリスト

### A. ログ改善
- [ ] P10-001: logs/がGit管理対象
- [ ] P10-002: ファイルログがDEBUGレベル

### B. Publication対策
- [ ] P10-003: item_id空チェック
- [ ] P10-004: 既存Item検出

### C. ドメインブロック
- [ ] P10-005: blocked_domains設定
- [ ] P10-006: Config読み込み
- [ ] P10-007: Collectorフィルタ

### D. User-Agent
- [ ] P10-008: user_agents設定
- [ ] P10-009: ローテーション実装

### E. Playwrightフォールバック
- [ ] P10-010: playwright依存関係
- [ ] P10-011: PlaywrightExtractor
- [ ] P10-012: フォールバック実装
- [ ] P10-013: テスト

### F. RSSフィード検証
- [ ] P10-014: フィード検証強化
- [ ] P10-015: 無効フィードスキップ

## 期待される改善効果

| 問題 | 改善前 | 改善後（期待値） |
|------|--------|-----------------|
| Body text too short | 225件 | 50件以下（Playwrightフォールバック） |
| Publication failed | 154件 | 0件（item_id空チェック） |
| HTTP 403 | 14件 | 0件（ドメインブロック） |
| HTTP 401 | 2件 | 0件（ドメインブロック） |
| Invalid feed | 2件 | 0件（検証強化+スキップ） |

## 依存関係

- 依存先: P10-004, P10-007, P10-009, P10-013, P10-015

## 見積もり

- 作業時間: 60分
- 複雑度: 中
