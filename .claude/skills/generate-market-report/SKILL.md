---
name: generate-market-report
description: "週次マーケットレポートを自動生成するスキル。データ収集→ニュース検索→レポート作成の一連のワークフローを提供。/generate-market-report コマンドで使用。"
allowed-tools: Read, Write, Glob, Grep, Bash, Task, WebSearch
---

# Generate Market Report

週次マーケットレポートを自動生成するスキルです。

## 目的

このスキルは以下を提供します：

- **3種類のレポートモード**: 基本レポート、週次コメント（旧形式）、フル週次レポート（推奨）
- **自動データ収集**: yfinance/FRED 経由の市場データ収集
- **ニュース統合**: GitHub Project / RSS / Tavily からのニュース収集と統合
- **品質検証**: 文字数・フォーマット・データ整合性の自動検証

## いつ使用するか

### プロアクティブ使用

- 毎週水曜日の週次レポート作成時
- 市場データの定期収集と分析が必要な場合

### 明示的な使用

- `/generate-market-report` コマンド
- 「週次レポートを作成して」「マーケットレポートを生成して」などの要求

## モード比較

| モード | 説明 | GitHub Project 連携 | 目標文字数 |
|--------|------|-------------------|-----------|
| 基本モード | 指定日のレポート生成 | なし | - |
| `--weekly-comment` | 火曜〜火曜の週次コメント（旧形式） | なし | 3000字以上 |
| `--weekly` | **フル週次レポート（推奨）** | **あり** | 3200字以上 |

## 処理フロー

### 基本モード

```
Phase 1: 初期化
├── 引数解析・出力ディレクトリ作成
├── 必要ツール確認（RSS MCP, Tavily, gh）
└── テンプレート確認

Phase 2: データ収集
└── Pythonスクリプト実行（market_report_data.py）

Phase 3: ニュース検索
└── カテゴリ別ニュース検索（指数/MAG7/セクター/決算）

Phase 4: レポート生成
└── テンプレート埋め込み → Markdown出力

Phase 5: 完了処理
└── 結果サマリー表示
```

### --weekly モード（推奨）

```
Phase 1: 初期化
├── 対象期間の自動計算（火曜〜火曜）
├── 出力ディレクトリ作成
└── 必要ツール確認

Phase 2: 市場データ収集
└── weekly_comment_data.py → indices/mag7/sectors.json

Phase 3: GitHub Project ニュース取得
└── weekly-report-news-aggregator → news_from_project.json

Phase 4: 追加ニュース検索（--no-search でスキップ可能）
└── 不足カテゴリの補完 → news_supplemental.json

Phase 5: レポート生成（サブエージェント）
├── weekly-data-aggregation スキル
├── weekly-comment-generation スキル
├── weekly-template-rendering スキル
└── weekly-report-validation スキル

Phase 6: 品質検証
└── 文字数・フォーマット・データ整合性チェック

Phase 7: Issue 投稿（--publish 時のみ）
└── weekly-report-publisher → GitHub Issue 作成

Phase 8: 完了処理
└── 結果サマリー表示
```

## 入力パラメータ

| パラメータ | デフォルト | 説明 |
|-----------|-----------|------|
| `--output` | articles/market_report_{date} | 出力ディレクトリ |
| `--date` | 今日 | レポート対象日（YYYY-MM-DD） |
| `--weekly` | false | フル週次レポート生成（推奨） |
| `--weekly-comment` | false | 週次コメント生成（旧形式） |
| `--project` | 15 | GitHub Project 番号（--weekly時） |
| `--no-search` | false | 追加検索を無効化（--weekly時） |
| `--publish` | false | GitHub Issue として投稿 |

## 出力ディレクトリ構造

### --weekly モード

```
articles/weekly_report/{YYYY-MM-DD}/
├── data/
│   ├── indices.json          # 指数パフォーマンス
│   ├── mag7.json             # MAG7 パフォーマンス
│   ├── sectors.json          # セクター分析
│   ├── news_from_project.json # GitHub Project からのニュース
│   ├── news_supplemental.json # 追加検索結果
│   ├── aggregated_data.json  # 集約データ
│   └── comments.json         # 生成コメント
├── 02_edit/
│   └── weekly_report.md      # Markdown レポート
└── validation_result.json    # 品質検証結果
```

## 使用例

### 例1: フル週次レポート生成（推奨）

**状況**: 毎週水曜日に週次レポートを作成したい

**コマンド**:
```bash
/generate-market-report --weekly
```

**処理**:
1. 対象期間を自動計算（前週火曜〜当週火曜）
2. 市場データを収集
3. GitHub Project #15 からニュースを取得
4. 不足カテゴリを追加検索で補完
5. 3200字以上のレポートを生成
6. 品質検証を実行

---

### 例2: GitHub Issue として投稿

**状況**: 生成したレポートを Issue として投稿したい

**コマンド**:
```bash
/generate-market-report --weekly --publish
```

**処理**:
1. フル週次レポートを生成
2. GitHub Issue を作成
3. Project #15 に追加（カテゴリ: Weekly Report）

---

### 例3: GitHub Project のみ使用

**状況**: 追加検索なしでレポートを作成したい

**コマンド**:
```bash
/generate-market-report --weekly --no-search
```

**処理**:
1. GitHub Project からのニュースのみ使用
2. 追加検索をスキップ
3. レポートを生成

---

### 例4: 特定日付でレポート生成

**状況**: 過去の日付でレポートを作成したい

**コマンド**:
```bash
/generate-market-report --weekly --date 2026-01-15
```

**処理**:
1. 指定された水曜日を基準に期間を計算
2. その期間のデータでレポートを生成

## 関連リソース

### サブエージェント

| エージェント | 説明 | 使用モード |
|-------------|------|-----------|
| `weekly-report-news-aggregator` | GitHub Project からニュース集約 | --weekly |
| `weekly-report-writer` | 4つのスキルでレポート生成 | --weekly |
| `weekly-report-publisher` | GitHub Issue として投稿 | --publish |
| `weekly-comment-indices-fetcher` | 指数ニュース収集 | --weekly-comment |
| `weekly-comment-mag7-fetcher` | MAG7 ニュース収集 | --weekly-comment |
| `weekly-comment-sectors-fetcher` | セクターニュース収集 | --weekly-comment |

### スキル

| スキル | 説明 |
|--------|------|
| `weekly-data-aggregation` | 入力データの集約・正規化 |
| `weekly-comment-generation` | セクション別コメント生成 |
| `weekly-template-rendering` | テンプレートへのデータ埋め込み |
| `weekly-report-validation` | 品質検証 |

### テンプレート

| テンプレート | 用途 |
|-------------|------|
| `template/market_report/weekly_market_report_template.md` | --weekly モード用 |
| `template/market_report/weekly_comment_template.md` | --weekly-comment モード用 |
| `template/market_report/02_edit/first_draft.md` | 基本モード用 |

### Python スクリプト

| スクリプト | 用途 |
|-----------|------|
| `scripts/market_report_data.py` | 基本モード用データ収集 |
| `scripts/weekly_comment_data.py` | 週次モード用データ収集 |

## エラーハンドリング

### E001: Python スクリプト実行エラー

**原因**: スクリプトが存在しない、依存関係不足、ネットワークエラー

**対処法**:
```bash
# 依存関係を確認
uv sync --all-extras

# スクリプトを直接実行してエラー確認
uv run python scripts/weekly_comment_data.py --output .tmp/test
```

### E010: GitHub Project アクセスエラー

**原因**: Project が存在しない、アクセス権限がない

**対処法**:
```bash
# Project の存在確認
gh project list --owner @me

# 別の Project を指定
/generate-market-report --weekly --project 20
```

### E013: 品質検証失敗

**原因**: 文字数不足、データ整合性エラー

**対処法**:
- コメントを手動で拡充
- `--publish` なしで再実行し、レポートを確認

## 品質基準

### 必須（MUST）

- [ ] 対象期間が正しく計算されている
- [ ] 必須データファイル（indices/mag7/sectors.json）が生成されている
- [ ] --weekly モードで 3200 字以上のレポートが生成される
- [ ] 品質検証結果がファイルに出力される

### 推奨（SHOULD）

- ニュースカテゴリが最低件数を満たしている
- グレード B 以上の品質スコア
- 全セクションにコメントが含まれている

## 完了条件

- [ ] 出力ディレクトリにレポートファイルが生成されている
- [ ] 品質検証が PASS または WARN で完了している
- [ ] --publish 時は GitHub Issue が作成されている
- [ ] 結果サマリーが表示されている

## 関連コマンド

- `/finance-news-workflow`: ニュース収集
- `/new-finance-article`: 記事フォルダ作成
- `/finance-research`: リサーチ実行
