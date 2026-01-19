# 計画: analysis.py コード分析レポートの要対処事項をIssue化

## 概要

`docs/code-analysis-report/analysis-report-20260119-analysis_py.yaml` の分析レポートで特定された要対処事項を GitHub Project #6（market_analysis）に Issue として登録し、`src/market_analysis/docs/project.md` を更新する。

## 決定事項

- **作成範囲**: 全10件一括作成
- **ラベル**: `refactor`

## 作成するIssue一覧

### 短期（1週間以内）- Priority: high

| # | タイトル | 関連Finding | 工数 |
|---|---------|------------|------|
| 1 | print を logger.error に置き換え（analysis.py） | ANA-005, SEC-001 | XS |
| 2 | _find_column の再利用によるコード重複削減 | ANA-003 | S |
| 3 | 未使用変数・パラメータの整理（analysis.py） | ANA-007, ANA-008 | XS |
| 4 | コメントアウトされたコード（TICKERS_WORLD）と対応メソッドの整理 | ANA-006 | XS |

### 中期（1ヶ月以内）- Priority: medium

| # | タイトル | 関連Finding | 工数 |
|---|---------|------------|------|
| 5 | MarketPerformanceAnalyzer の責務分離 | ANA-002 | L |
| 6 | Analysis クラスから静的メソッドを CorrelationApi クラスに分離 | - | M |
| 7 | パラメータ検証ロジックの共通化（デコレータ/バリデータ） | - | M |

### 長期 - Priority: low

| # | タイトル | 関連Finding | 工数 |
|---|---------|------------|------|
| 8 | MarketPerformanceAnalyzer の遅延読み込み（Lazy Loading）化 | ANA-001, ANA-004 | L |
| 9 | MarketPerformanceAnalyzer への依存性注入（DI）パターン導入 | ANA-001 | L |
| 10 | 非同期データ取得の導入 | ANA-004 | L |

## 実行手順

### Step 1: Issue作成（10件）

`gh issue create` コマンドで各Issueを作成:

- タイトル: `[refactor]: <タスク名>`
- ラベル: `refactor`
- 本文: 分析レポートの該当箇所を引用し、具体的な実装指針を記載

### Step 2: GitHub Project #6 への追加

作成した各Issueを Project #6 に追加:
```bash
gh project item-add 6 --owner YH-05 --url <issue_url>
```

### Step 3: project.md の更新

`src/market_analysis/docs/project.md` の「GitHub Project #6 Issue一覧」セクションに新規Issueを追加。

## 変更対象ファイル

- `src/market_analysis/docs/project.md` - Issue一覧テーブルに10件追加

## 検証方法

1. `gh issue list --label refactor` で作成されたIssueを確認
2. `gh project item-list 6 --owner YH-05` でProject追加を確認
3. `project.md` の更新内容を確認
