# Task 18: 統合テスト・動作確認

**Phase**: 4 - 統合
**依存**: Task 15, Task 16, Task 17
**ファイル**: なし（検証タスク）

## 概要

すべての機能を統合した後、エンドツーエンドの動作確認を行う。

## テスト項目

### 1. データ収集スクリプトの統合テスト

```bash
# 統合データ収集スクリプトを実行
uv run python scripts/collect_market_performance.py --output .tmp/integration_test

# 出力ファイルの確認
ls -la .tmp/integration_test/

# 期待される出力ファイル:
# - indices_us_*.json
# - indices_global_*.json
# - mag7_*.json
# - sectors_*.json
# - commodities_*.json
# - interest_rates_*.json    ← 新規
# - currencies_*.json        ← 新規
# - upcoming_events_*.json   ← 新規
# - all_performance_*.json
```

### 2. 個別スクリプトの動作確認

```bash
# 金利データ
uv run python scripts/collect_interest_rates.py --output .tmp/test
cat .tmp/test/interest_rates_*.json | jq '.data | keys'
# 期待: ["DGS10", "DGS2", "DGS30", "FEDFUNDS", "T10Y2Y"]

# 為替データ
uv run python scripts/collect_currency_rates.py --output .tmp/test
cat .tmp/test/currencies_*.json | jq '.symbols | keys'
# 期待: ["AUDJPY=X", "CADJPY=X", "CHFJPY=X", "EURJPY=X", "GBPJPY=X", "USDJPY=X"]

# 来週の注目材料
uv run python scripts/collect_upcoming_events.py --output .tmp/test
cat .tmp/test/upcoming_events_*.json | jq '.summary'
```

### 3. 週次レポート生成の統合テスト

```bash
# /generate-market-report コマンドを実行
# （実際にはClaude Code経由で実行）

# 手動でのテスト手順:
# 1. データ収集スクリプトを実行
uv run python scripts/collect_market_performance.py --output articles/weekly_report/test/data

# 2. 生成されたデータを確認
cat articles/weekly_report/test/data/all_performance_*.json | jq '.categories'
# 期待: 8カテゴリ（既存5 + 新規3）
```

### 4. テンプレートレンダリングの確認

- [ ] `{interest_rates_table}` が正しくテーブルに変換される
- [ ] `{interest_rates_comment}` が適切な文字数で生成される
- [ ] `{currencies_table}` が正しくテーブルに変換される
- [ ] `{currencies_comment}` が適切な文字数で生成される
- [ ] `{earnings_table}` が決算予定を一覧表示
- [ ] `{economic_releases_table}` が経済指標を一覧表示

### 5. 文字数の確認

```bash
# 生成されたレポートの文字数をカウント
wc -m articles/weekly_report/test/02_edit/weekly_report.md
# 期待: 5700字以上
```

### 6. 品質検証

```bash
# weekly-report-validation スキルで検証
# （実際にはClaude Code経由で実行）

# 検証項目:
# - 必須セクションがすべて存在
# - 文字数が目標を達成
# - データ整合性（最新日付の一致等）
# - Markdownフォーマットが正しい
```

## チェックリスト

### データ収集

- [ ] 金利データが5シリーズ取得できる
- [ ] 為替データが6通貨ペア取得できる
- [ ] 決算予定が取得できる（期間内に存在する場合）
- [ ] 経済指標発表予定が取得できる
- [ ] all_performance.json に全8カテゴリが含まれる

### レポート生成

- [ ] テンプレートの全プレースホルダーが置換される
- [ ] 金利・債券市場セクションが出力される
- [ ] 為替市場セクションが出力される
- [ ] 来週の注目材料が決算と経済指標を含む
- [ ] 合計文字数が5700字以上

### 品質

- [ ] Markdownの構文エラーがない
- [ ] データの整合性がある（日付ズレ警告がない）
- [ ] コメントが日本語として自然

## 受け入れ条件

- [ ] 全テスト項目がパスする
- [ ] レポートが正しく生成される
- [ ] 文字数目標を達成
- [ ] エラーなく実行完了
