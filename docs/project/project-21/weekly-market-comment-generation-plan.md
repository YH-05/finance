# 週次マーケットコメント生成システム - 実装計画

## 概要

毎週水曜日朝（日本時間）に、前週火曜日〜当週火曜日の米国株式市場パフォーマンスを分析し、3000字以上の詳細なマーケットコメントを自動生成するシステム。

## 実装方針

既存の `/generate-market-report` コマンドに `--weekly-comment` モードを追加。

## 処理フロー

```
/generate-market-report --weekly-comment
    │
    ├── Phase 1: 初期化
    │   └── 対象期間の自動計算（火曜〜火曜）
    │
    ├── Phase 2: データ収集
    │   ├── 指数: S&P500, 等ウェイト(RSP), グロース(VUG), バリュー(VTV)
    │   ├── MAG7: AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA
    │   └── セクター: 上位・下位3セクター（ETFベース）
    │
    ├── Phase 3: ニュース収集（3サブエージェント並列）
    │   ├── weekly-comment-indices-fetcher（指数背景）
    │   ├── weekly-comment-mag7-fetcher（MAG7背景）
    │   └── weekly-comment-sectors-fetcher（セクター背景）
    │
    ├── Phase 4: コメント生成（3000字以上）
    │   └── テンプレート + データ + ニュース → Markdown
    │
    └── Phase 5: 出力
        └── articles/weekly_comment_{date}/02_edit/weekly_comment.md
```

## 実装タスク

### Phase 1: 基盤整備

| タスク | 成果物 |
|--------|-------|
| 週次コメント用データ収集スクリプト | `scripts/weekly_comment_data.py` |
| 期間計算ユーティリティ | `src/market_analysis/utils/date_utils.py` |
| 週次コメントテンプレート | `template/market_report/weekly_comment_template.md` |

### Phase 2: サブエージェント作成

| タスク | 成果物 |
|--------|-------|
| 指数ニュース収集エージェント | `.claude/agents/weekly-comment-indices-fetcher.md` |
| MAG7ニュース収集エージェント | `.claude/agents/weekly-comment-mag7-fetcher.md` |
| セクターニュース収集エージェント | `.claude/agents/weekly-comment-sectors-fetcher.md` |

### Phase 3: コマンド拡張

| タスク | 成果物 |
|--------|-------|
| --weekly-comment オプション追加 | `.claude/commands/generate-market-report.md` |

### Phase 4: テスト

| タスク | 成果物 |
|--------|-------|
| データ収集スクリプトのテスト | `tests/unit/test_weekly_comment_data.py` |
| 期間計算のテスト | `tests/unit/test_date_utils.py` |

## 変更対象ファイル

### 新規作成
- `scripts/weekly_comment_data.py` - データ収集スクリプト
- `src/market_analysis/utils/date_utils.py` - 期間計算ユーティリティ
- `template/market_report/weekly_comment_template.md` - 出力テンプレート
- `.claude/agents/weekly-comment-indices-fetcher.md` - 指数ニュースエージェント
- `.claude/agents/weekly-comment-mag7-fetcher.md` - MAG7ニュースエージェント
- `.claude/agents/weekly-comment-sectors-fetcher.md` - セクターニュースエージェント
- `tests/unit/test_weekly_comment_data.py` - データ収集テスト
- `tests/unit/test_date_utils.py` - 期間計算テスト

### 変更
- `.claude/commands/generate-market-report.md` - --weekly-comment オプション追加

## サブエージェント設計

### weekly-comment-indices-fetcher
- **入力**: 対象期間、指数パフォーマンスデータ
- **処理**: RSS + Tavily で指数関連ニュース検索
- **出力**: 市場センチメント、上昇/下落要因、関連ニュース要約

### weekly-comment-mag7-fetcher
- **入力**: 対象期間、MAG7パフォーマンスデータ
- **処理**: 各銘柄ごとにニュース検索（決算、製品、規制等）
- **出力**: 銘柄別の動向背景、ニュース要約

### weekly-comment-sectors-fetcher
- **入力**: 対象期間、セクター分析データ（上位3・下位3）
- **処理**: 動的キーワードでセクター別ニュース検索
- **出力**: セクター別の上昇/下落要因、ニュース要約

## 出力形式（3000字以上）

```markdown
# 2026/1/22(Wed) Weekly Comment

## Indices (AS OF 1/21)
| 指数 | 週間リターン |
|------|-------------|
| S&P500 | +X.XX% |
| 等ウェイト (RSP) | +X.XX% |
| グロース (VUG) | +X.XX% |
| バリュー (VTV) | +X.XX% |

{指数コメント: 500字以上}

## Magnificent 7
| 銘柄 | 週間リターン |
|------|-------------|
| Apple | +X.XX% |
| ... | ... |

{MAG7コメント: 800字以上、銘柄別背景}

## セクター別パフォーマンス
### 上位3セクター
{上位セクターコメント: 400字以上}

### 下位3セクター
{下位セクターコメント: 400字以上}

## 今後の材料
{来週の注目イベント: 200字以上}
```

## 検証方法

### 1. データ収集テスト
```bash
# 期間計算の確認
uv run python -c "from market_analysis.utils.date_utils import calculate_weekly_comment_period; print(calculate_weekly_comment_period())"

# データ収集スクリプトの実行
uv run python scripts/weekly_comment_data.py --start 2026-01-14 --end 2026-01-21 --output test_output
```

### 2. ユニットテスト
```bash
make test-unit
```

### 3. コマンド実行テスト
```bash
# 週次コメント生成（ドライラン）
/generate-market-report --weekly-comment --date 2026-01-22

# 出力確認
cat articles/weekly_comment_20260122/02_edit/weekly_comment.md | wc -c
# → 3000字以上であることを確認
```

### 4. 品質チェック
```bash
make check-all
```

## 技術的考慮事項

- **バッチダウンロード**: `yf.download()` で複数ティッカーを一括取得
- **並列ニュース収集**: 3つのサブエージェントを同時実行
- **フォールバック**: RSS → Tavily → Gemini の順に検索
- **エラーハンドリング**: リトライ（最大3回、指数バックオフ）
