# api-usage-researcher エージェント実装計画

## 概要

issue-implement-single スキルの Python ワークフローに、外部API使用時のドキュメント調査フェーズ（Phase 0.5）を新設する。専用サブエージェント `api-usage-researcher` を作成し、Issue 内容から外部ライブラリの使用を自動検出、Context7・WebSearch・プロジェクト内パターンを調査して実装に必要な情報を JSON 形式で収集する。

## 変更後のフロー

```
Phase 0:   Issue検証・タイプ判定
Phase 0.5: 外部API調査（条件付き） ← NEW
Phase 1:   test-writer（api_research 結果を参照）
Phase 2:   pydantic-model-designer（api_research 結果を参照）
Phase 3:   feature-implementer（api_research 結果を参照）
Phase 4:   code-simplifier
Phase 5:   quality-checker
Phase 6:   make check-all
Phase 7:   CIチェック
```

## 修正対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `.claude/agents/api-usage-researcher.md` | **新規作成** |
| `.claude/skills/issue-implement-single/SKILL.md` | Phase 0.5 追加、フロー図更新、サブエージェント連携表更新 |
| `.claude/agents/feature-implementer.md` | Context7 セクションを api-usage-researcher 出力参照に調整 |
| `CLAUDE.md` | エージェント一覧に追加 |

---

## 1. 新規作成: `.claude/agents/api-usage-researcher.md`

### frontmatter

```yaml
---
name: api-usage-researcher
description: |
  外部API使用時のドキュメント調査エージェント。Issue内容から外部ライブラリの使用を検出し、
  Context7・WebSearch・プロジェクト内パターンを調査して実装に必要な情報を収集する。
model: inherit
color: blue
skills:
  - coding-standards
  - error-handling
---
```

### 自動判定ロジック

```yaml
high_confidence_keywords:  # 即座に調査必要と判定
  - yfinance, yf.Ticker, yf.download
  - requests, httpx, aiohttp
  - pandas, pd.DataFrame
  - numpy, np.array
  - pydantic, BaseModel
  - curl_cffi
  - fredapi, fred
  - sec-api, edgar
  - openai, anthropic

medium_confidence_patterns:  # パターンマッチで判定
  - r"import\s+\w+"
  - r"from\s+\w+\s+import"
  - r"pip\s+install", r"uv\s+add"
  - "外部API", "ライブラリ", "パッケージ"
  - "rate limit", "API key", "認証"

decision:
  - 高信頼度キーワード検出 → investigation_needed: true
  - 中信頼度パターン検出 → investigation_needed: true
  - 検出なし → investigation_needed: false（Phase 1 へスキップ）
```

### 調査手段

1. **Context7 MCP**（max 3 calls/library）
   - `mcp__context7__resolve-library-id`
   - `mcp__context7__query-docs`

2. **WebSearch / Tavily**
   - 最新バージョン情報、breaking changes、deprecation

3. **プロジェクト内パターン**
   - `Glob`: `src/**/*{library}*.py`
   - `Grep`: `import {library}`
   - `Read`: 既存実装ファイル

4. **プロジェクトドキュメント**
   - `docs/yfinance-best-practices.md`
   - `docs/architecture/packages.md`
   - `.claude/skills/coding-standards/guide.md`
   - `.claude/skills/coding-standards/examples/type-hints.md`
   - `.claude/skills/error-handling/guide.md`
   - `template/src/template_package/core/example.py`

5. **GitHub Issues 過去事例**
   - `gh issue list --search "{library}"`
   - 類似実装の参照

### 出力スキーマ（JSON）

```json
{
  "investigation_needed": true,
  "detection_confidence": "high|medium|low",
  "detected_from": ["body", "labels", "acceptance_criteria"],
  "libraries": [
    {
      "name": "yfinance",
      "version_info": "0.2.x",
      "apis_to_use": [
        {
          "api": "Ticker.history()",
          "usage_pattern": "ticker = yf.Ticker(symbol, session=session)",
          "parameters": {"period": "string", "interval": "string"},
          "return_type": "pd.DataFrame",
          "notes": "Use curl_cffi session to avoid rate limiting"
        }
      ],
      "best_practices": [
        "Use curl_cffi.requests.Session(impersonate='safari15_5')",
        "Share session at class level"
      ],
      "project_patterns": {
        "existing_usage_files": ["src/market/yfinance/fetcher.py"],
        "conventions": "curl_cffi session with browser impersonation",
        "error_handling": "DataFetchError, ValidationError"
      },
      "context7_docs_summary": "Context7から取得した要約..."
    }
  ],
  "related_issues": [
    {"number": 100, "title": "類似の実装", "relevance": "同じAPIを使用"}
  ],
  "project_docs_referenced": ["docs/yfinance-best-practices.md"],
  "recommendations": ["Follow existing YFinanceFetcher pattern"]
}
```

### スキップ時の出力

```json
{
  "investigation_needed": false,
  "detection_confidence": "none",
  "detected_from": [],
  "libraries": [],
  "related_issues": [],
  "project_docs_referenced": [],
  "recommendations": []
}
```

---

## 2. 修正: `.claude/skills/issue-implement-single/SKILL.md`

### 追加セクション: Phase 0.5

```markdown
## Phase 0.5: 外部API調査（条件付き）

Phase 0 完了後、Issue 内容に外部APIの使用が検出された場合のみ実行。

### 実行条件

Issue本文・ラベル・受け入れ条件から以下を検出した場合に実行:
- 外部ライブラリ名（yfinance, pandas, requests 等）
- import 文への言及
- 外部API・認証・rate limiting への言及

### サブエージェント呼び出し

| subagent_type | prompt に含める情報 |
|---------------|---------------------|
| `api-usage-researcher` | Issue番号、タイトル、本文、ラベル、受け入れ条件 |

### 出力の後続 Phase への受け渡し

api_research 結果（JSON）を Phase 1, 2, 3 のプロンプトに含める。
```

### 更新: フロー図

Phase 0.5 を挿入し、api_research 結果の参照を Phase 1-3 に追記。

### 更新: サブエージェント連携表

| Phase | subagent_type | prompt に含める情報 |
|-------|---------------|---------------------|
| 0.5 | `api-usage-researcher` | Issue情報、受け入れ条件（条件付き実行） |
| 1 | `test-writer` | Issue情報、受け入れ条件、対象パッケージ、**api_research結果** |
| 2 | `pydantic-model-designer` | Issue情報、Phase 1のテストファイル、**api_research結果** |
| 3 | `feature-implementer` | Issue番号、ライブラリ名、Phase 2のモデル、**api_research結果** |

---

## 3. 修正: `.claude/agents/feature-implementer.md`

### Context7 セクションの更新

```markdown
## context7 によるドキュメント参照

### 事前調査結果の活用（推奨）

Phase 0.5 で api-usage-researcher が実行された場合、その結果を優先的に参照してください。

api_research 結果に含まれる情報:
- libraries[].apis_to_use: 使用すべきAPI一覧
- libraries[].best_practices: ベストプラクティス
- libraries[].project_patterns: プロジェクト内の既存パターン
- recommendations: 実装推奨事項

### 追加確認が必要な場合

api_research 結果で不足する情報がある場合のみ、context7 を追加で使用してください。
```

---

## 4. 修正: `CLAUDE.md`

### エージェント一覧に追加

「コード品質・分析エージェント」セクションの先頭に追加:

```markdown
| `api-usage-researcher` | 外部API使用時のドキュメント調査（Context7・プロジェクトパターン・ベストプラクティス収集） |
```

### 依存関係に追加

```markdown
- `/issue-implement <番号>` → `issue-implement-single` → `api-usage-researcher`(条件付き), `test-writer`, ...
```

---

## 検証方法

### 1. エージェント動作確認

```bash
# 外部API使用 Issue でテスト
gh issue create --title "Test: yfinance使用" --body "yf.Ticker でデータ取得"
/issue-implement <番号>
# → Phase 0.5 が実行され、api_research 結果が生成されることを確認

# 純粋Python Issue でテスト
gh issue create --title "Test: 内部関数" --body "文字列処理ユーティリティ"
/issue-implement <番号>
# → Phase 0.5 がスキップされることを確認
```

### 2. 出力スキーマ検証

- JSON出力が定義したスキーマに準拠しているか
- 後続Phase（test-writer, feature-implementer）が api_research を参照しているか

### 3. 品質チェック

```bash
make check-all
```

---

## 実装順序

1. `.claude/agents/api-usage-researcher.md` を新規作成
2. `.claude/skills/issue-implement-single/SKILL.md` に Phase 0.5 を追加
3. `.claude/agents/feature-implementer.md` の Context7 セクションを更新
4. `CLAUDE.md` にエージェントを追加
5. テスト Issue で動作確認
6. コミット・PR作成
