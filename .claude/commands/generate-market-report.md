---
description: 週次マーケットレポートを自動生成します（データ収集→ニュース検索→レポート作成）
argument-hint: [--output articles/market_report_{date}] [--date YYYY-MM-DD] [--weekly-comment]
---

# /generate-market-report - マーケットレポート生成

週次マーケットレポートを自動生成するコマンドです。

`--weekly-comment` オプションを使用すると、火曜〜火曜の期間を対象とした
3000字以上の詳細なマーケットコメントを生成します。

## 使用例

```bash
# 基本的な使用方法（今日の日付でレポート生成）
/generate-market-report

# 出力先を指定
/generate-market-report --output articles/market_report_20260119

# 特定の日付でレポート生成
/generate-market-report --date 2026-01-19

# 週次コメント生成モード（推奨: 水曜日に実行）
/generate-market-report --weekly-comment

# 週次コメント生成（日付指定）
/generate-market-report --weekly-comment --date 2026-01-22
```

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| --output | - | articles/market_report_{date} | 出力ディレクトリ |
| --date | - | 今日の日付 | レポート対象日（YYYY-MM-DD形式） |
| --weekly-comment | - | false | 週次コメント生成モード（火曜〜火曜の期間を対象） |

## 処理フロー

```
Phase 1: 初期化
├── 引数解析・出力ディレクトリ作成
├── 必要ツール確認（RSS MCP, Tavily, gh）
└── テンプレート確認

Phase 2: データ収集
├── Pythonスクリプト実行（market_report_data.py）
├── returns.json 読み込み
├── sectors.json 読み込み
└── earnings.json 読み込み

Phase 3: ニュース検索
├── 指数関連ニュース検索
├── MAG7/半導体関連ニュース検索
├── セクター関連ニュース検索
└── 決算関連ニュース検索

Phase 4: レポート生成
├── テンプレート読み込み
├── データ埋め込み
├── ニュースコンテキスト追加
└── Markdownファイル出力

Phase 5: 完了処理
└── 結果サマリー表示
```

---

## Phase 1: 初期化

### 1.1 引数解析

```bash
# デフォルト値の設定
DATE=$(date +%Y%m%d)
OUTPUT_DIR="articles/market_report_${DATE}"

# 引数が指定されている場合は上書き
# --output: 出力ディレクトリ
# --date: レポート対象日
```

### 1.2 出力ディレクトリ作成

```bash
mkdir -p "${OUTPUT_DIR}/data"
mkdir -p "${OUTPUT_DIR}/02_edit"
```

**ディレクトリ構造**:
```
{OUTPUT_DIR}/
├── data/
│   ├── returns.json        # 騰落率データ
│   ├── sectors.json        # セクター分析
│   ├── earnings.json       # 決算カレンダー
│   └── news_context.json   # ニュース検索結果
└── 02_edit/
    └── report.md           # Markdownレポート
```

### 1.3 必要ツール確認

#### RSS MCP ツール確認（リトライ機能付き）

```
[試行1] キーワード検索でRSS MCPツールを検索
MCPSearch: query="rss", max_results=5

↓ ツールが見つかった場合
成功 → 次へ

↓ ツールが見つからない場合
[待機] 3秒待機
[試行2] 再度検索

↓ それでも見つからない場合
警告表示（RSS検索スキップ）→ 他の検索手段で続行
```

#### Tavily ツール確認

```
MCPSearch: query="tavily", max_results=3

↓ ツールが見つかった場合
成功 → 次へ

↓ 見つからない場合
警告表示（Tavily検索スキップ）→ 他の検索手段で続行
```

#### GitHub CLI 確認

```bash
if ! command -v gh &> /dev/null; then
    echo "警告: GitHub CLI (gh) がインストールされていません"
fi
```

### 1.4 テンプレート確認

```bash
TEMPLATE_FILE="template/market_report/02_edit/first_draft.md"
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "エラー: テンプレートファイルが見つかりません"
    echo "期待されるパス: $TEMPLATE_FILE"
    exit 1
fi
```

---

## Phase 2: データ収集

### 2.1 Pythonスクリプト実行

```bash
uv run python scripts/market_report_data.py --output "${OUTPUT_DIR}/data"
```

**出力ファイル**:
- `returns.json`: 騰落率データ（主要指数、MAG7、セクターETF、グローバル指数）
- `sectors.json`: セクター分析データ（上位/下位セクター）
- `earnings.json`: 決算カレンダーデータ

**エラーハンドリング**:
```
↓ スクリプト実行成功
成功 → 次へ

↓ スクリプト実行失敗
エラー報告:
  - エラー内容を表示
  - 部分的に成功したファイルがあれば続行
  - 全て失敗した場合は処理中断
```

### 2.2 JSONファイル読み込み

各JSONファイルを読み込み、構造化データとして保持:

```python
# returns.json の構造
{
  "as_of": "2026-01-19",
  "indices": [...],      # 主要指数
  "mag7": [...],         # Magnificent 7
  "sectors": [...],      # セクターETF
  "global": [...]        # グローバル指数
}

# sectors.json の構造
{
  "as_of": "2026-01-19",
  "period": "1W",
  "top_sectors": [...],    # 上位3セクター
  "bottom_sectors": [...]  # 下位3セクター
}

# earnings.json の構造
{
  "generated_at": "2026-01-19",
  "upcoming_earnings": [...]  # 今後2週間の決算予定
}
```

---

## Phase 3: ニュース検索

### 3.1 検索優先順位

1. **RSS MCP**: `mcp__rss__rss_search_items`（33フィード、高速）
2. **Tavily**: `mcp__tavily__tavily-search`（Web全体検索）
3. **Gemini Search**: `/gemini-search` スキル（バックアップ）
4. **Fetch**: `mcp__fetch__fetch`（特定URL取得）

### 3.2 カテゴリ別ニュース検索

#### 指数関連ニュース

```python
keywords = ["S&P 500", "NASDAQ", "Dow Jones", "日経平均", "TOPIX", "株価指数"]
# RSS MCPで検索
# 結果が不足していればTavilyで補完
```

#### MAG7/半導体関連ニュース

```python
keywords = ["Apple", "Microsoft", "Google", "Amazon", "NVIDIA", "Meta", "Tesla", "半導体", "AI"]
# RSS MCPで検索
# 結果が不足していればTavilyで補完
```

#### セクター関連ニュース

```python
# sectors.json の top_sectors, bottom_sectors から動的にキーワード生成
keywords = [sector["name"] for sector in top_sectors + bottom_sectors]
# RSS MCPで検索
# 結果が不足していればTavilyで補完
```

#### 決算関連ニュース

```python
# earnings.json の upcoming_earnings から動的にキーワード生成
keywords = [earning["symbol"] + " 決算" for earning in upcoming_earnings[:5]]
# RSS MCPで検索
# 結果が不足していればTavilyで補完
```

### 3.3 検索結果の保存

```python
# news_context.json の構造
{
  "searched_at": "2026-01-19T10:00:00Z",
  "categories": {
    "indices": [
      {
        "title": "記事タイトル",
        "source": "Bloomberg",
        "url": "https://...",
        "published": "2026-01-18T...",
        "summary": "記事要約"
      }
    ],
    "mag7": [...],
    "sectors": [...],
    "earnings": [...]
  }
}
```

保存先: `${OUTPUT_DIR}/data/news_context.json`

---

## Phase 4: レポート生成

### 4.1 テンプレート読み込み

```bash
cat template/market_report/02_edit/first_draft.md
```

### 4.2 データ埋め込み

テンプレートのプレースホルダーを実データで置換:

#### 主要指数テーブル

```markdown
| 指数 | 終値 | 1D (%) | 1W (%) | MTD (%) | YTD (%) | 1Y (%) |
|------|------|--------|--------|---------|---------|--------|
| S&P 500 | 6,012.45 | +0.25 | +1.50 | +2.30 | +5.20 | +25.30 |
| ... |
```

#### Magnificent 7 テーブル

```markdown
| 銘柄 | ティッカー | 終値 | 1W (%) | 背景 |
|------|-----------|------|--------|------|
| Apple | AAPL | 245.50 | -2.30 | AI競争激化、幹部退職報道 |
| ... |
```

#### セクター分析テーブル

```markdown
### 上位3セクター
| セクター | 1W (%) | 代表銘柄 | 寄与度 |
|----------|--------|----------|--------|
| IT | +2.50 | AAPL, MSFT | 高 |
| ... |
```

#### 決算発表予定テーブル

```markdown
| 日付 | 銘柄 | ティッカー | EPS予想 | 売上予想 | 着目ポイント |
|------|------|-----------|---------|----------|-------------|
| 01/22 | Apple | AAPL | $2.10 | $119B | AI戦略、Vision Pro販売 |
| ... |
```

### 4.3 ニュースコンテキスト追加

各セクションの「ニュースコンテキスト」部分に、Phase 3で収集したニュースを挿入:

```markdown
**ニュースコンテキスト:**
- [記事タイトル1](URL) - ソース名
- [記事タイトル2](URL) - ソース名
```

### 4.4 Markdownファイル出力

```bash
# 出力先
${OUTPUT_DIR}/02_edit/report.md
```

**日付の置換**:
- `{date}` → `2026年1月19日`
- `{week}` → `第3週`

---

## Phase 5: 完了処理

### 5.1 結果サマリー表示

```markdown
================================================================================
                    /generate-market-report 完了
================================================================================

## 生成されたファイル

| ファイル | パス | サイズ |
|----------|------|--------|
| 騰落率データ | {output}/data/returns.json | 15KB |
| セクター分析 | {output}/data/sectors.json | 8KB |
| 決算カレンダー | {output}/data/earnings.json | 5KB |
| ニュースコンテキスト | {output}/data/news_context.json | 12KB |
| **レポート** | {output}/02_edit/report.md | 25KB |

## データサマリー

### 主要指数
- S&P 500: +1.50% (1W)
- NASDAQ: +2.30% (1W)
- 日経平均: -0.50% (1W)

### 上位セクター
1. IT: +2.50%
2. エネルギー: +1.80%
3. 金融: +1.20%

### 下位セクター
1. ヘルスケア: -2.90%
2. 公益: -2.20%
3. 素材: -1.50%

### 決算予定（今後2週間）
- {count}社の決算発表予定

### ニュース検索結果
- 指数関連: {count}件
- MAG7関連: {count}件
- セクター関連: {count}件
- 決算関連: {count}件

## 次のアクション

1. レポートを確認:
   cat {output}/02_edit/report.md

2. 編集・修正:
   edit {output}/02_edit/report.md

3. 公開準備:
   cp {output}/02_edit/report.md {output}/03_published/{date}_weekly_market_report.md

================================================================================
```

---

## エラーハンドリング

### E001: Pythonスクリプト実行エラー

**発生条件**:
- `scripts/market_report_data.py` が存在しない
- 依存モジュールのインポートエラー
- ネットワークエラー（Yahoo Finance API）

**対処法**:
```
エラー: Pythonスクリプトの実行に失敗しました

確認項目:
1. スクリプトが存在するか確認:
   ls scripts/market_report_data.py

2. 依存関係を確認:
   uv sync --all-extras

3. スクリプトを直接実行してエラー内容を確認:
   uv run python scripts/market_report_data.py --output .tmp/test

4. ネットワーク接続を確認
```

### E002: RSS MCP ツールエラー

**発生条件**:
- RSS MCPサーバーが起動していない
- MCPサーバーの起動が完了していない

**対処法**:
- 3秒待機して再試行（自動）
- 2回失敗した場合は警告を表示し、他の検索手段で続行

### E003: Tavily ツールエラー

**発生条件**:
- Tavily MCPツールが設定されていない
- APIキーが無効

**対処法**:
- 警告を表示し、他の検索手段で続行

### E004: テンプレートエラー

**発生条件**:
- テンプレートファイルが存在しない
- テンプレートの構造が不正

**対処法**:
```
エラー: テンプレートファイルが見つかりません

期待されるパス: template/market_report/02_edit/first_draft.md

対処法:
1. テンプレートディレクトリを確認:
   ls template/market_report/

2. テンプレートを復元:
   git checkout template/market_report/02_edit/first_draft.md
```

### E005: 出力ディレクトリエラー

**発生条件**:
- ディレクトリ作成権限がない
- ディスク容量不足

**対処法**:
```
エラー: 出力ディレクトリを作成できません

対処法:
1. 権限を確認:
   ls -la articles/

2. 手動でディレクトリを作成:
   mkdir -p articles/market_report_{date}/data
   mkdir -p articles/market_report_{date}/02_edit
```

---

# 週次コメントモード（--weekly-comment）

`--weekly-comment` オプションを指定すると、火曜〜火曜の期間を対象とした
詳細なマーケットコメント（3000字以上）を生成します。

## 週次コメント処理フロー

```
/generate-market-report --weekly-comment
    │
    ├── Phase 1: 初期化
    │   ├── 対象期間の自動計算（火曜〜火曜）
    │   │   └── 水曜日実行: 前週火曜〜当週火曜
    │   └── 出力ディレクトリ作成
    │       └── articles/weekly_comment_{YYYYMMDD}/
    │
    ├── Phase 2: データ収集
    │   ├── Pythonスクリプト実行（weekly_comment_data.py）
    │   ├── indices.json: S&P500, RSP, VUG, VTV
    │   ├── mag7.json: MAG7 + SOX
    │   └── sectors.json: 上位・下位3セクター
    │
    ├── Phase 3: ニュース収集（3サブエージェント並列）
    │   ├── weekly-comment-indices-fetcher（指数背景）
    │   ├── weekly-comment-mag7-fetcher（MAG7背景）
    │   └── weekly-comment-sectors-fetcher（セクター背景）
    │
    ├── Phase 4: コメント生成（3000字以上）
    │   ├── テンプレート読み込み
    │   │   └── template/market_report/weekly_comment_template.md
    │   ├── データ埋め込み
    │   ├── ニュースコンテキスト統合
    │   └── Markdownファイル出力
    │
    └── Phase 5: 出力
        └── articles/weekly_comment_{date}/02_edit/weekly_comment.md
```

## 週次コメント出力ディレクトリ構造

```
articles/weekly_comment_{YYYYMMDD}/
├── data/
│   ├── indices.json        # 指数騰落率（S&P500, RSP, VUG, VTV）
│   ├── mag7.json           # MAG7 + SOX騰落率
│   ├── sectors.json        # セクター分析（上位・下位3）
│   ├── metadata.json       # 期間情報
│   └── news_context.json   # ニュース検索結果
└── 02_edit/
    └── weekly_comment.md   # 週次コメント（3000字以上）
```

## 週次コメント Phase 1: 初期化（詳細）

### 1.1 対象期間の自動計算

```python
from market_analysis.utils.date_utils import calculate_weekly_comment_period

# 例: 2026/1/22（水曜日）に実行した場合
period = calculate_weekly_comment_period()
# period["start"] = 2026-01-14 (火曜日)
# period["end"] = 2026-01-21 (火曜日)
# period["report_date"] = 2026-01-22 (水曜日)
```

### 1.2 出力ディレクトリ作成

```bash
# デフォルトパス
OUTPUT_DIR="articles/weekly_comment_${REPORT_DATE}"

# 構造作成
mkdir -p "${OUTPUT_DIR}/data"
mkdir -p "${OUTPUT_DIR}/02_edit"
```

## 週次コメント Phase 2: データ収集（詳細）

### 2.1 Pythonスクリプト実行

```bash
uv run python scripts/weekly_comment_data.py \
    --start ${START_DATE} \
    --end ${END_DATE} \
    --output "${OUTPUT_DIR}/data"
```

### 2.2 出力データ形式

#### indices.json
```json
{
  "as_of": "2026-01-21",
  "period": {"start": "2026-01-14", "end": "2026-01-21"},
  "indices": [
    {"ticker": "^GSPC", "name": "S&P 500", "weekly_return": 0.025},
    {"ticker": "RSP", "name": "S&P 500 Equal Weight", "weekly_return": 0.018},
    {"ticker": "VUG", "name": "Vanguard Growth ETF", "weekly_return": 0.032},
    {"ticker": "VTV", "name": "Vanguard Value ETF", "weekly_return": 0.012}
  ]
}
```

#### mag7.json
```json
{
  "as_of": "2026-01-21",
  "period": {"start": "2026-01-14", "end": "2026-01-21"},
  "mag7": [
    {"ticker": "TSLA", "name": "Tesla", "weekly_return": 0.037},
    ...
  ],
  "sox": {"ticker": "^SOX", "name": "SOX Index", "weekly_return": 0.031}
}
```

#### sectors.json
```json
{
  "as_of": "2026-01-21",
  "period": {"start": "2026-01-14", "end": "2026-01-21"},
  "top_sectors": [...],
  "bottom_sectors": [...],
  "all_sectors": [...]
}
```

## 週次コメント Phase 3: ニュース収集（詳細）

### 3.1 サブエージェント並列実行

3つのサブエージェントを**並列**で実行:

```python
# 並列実行（Task tool を複数同時呼び出し）
Task(
    subagent_type="weekly-comment-indices-fetcher",
    description="指数ニュース収集",
    prompt="...",
    run_in_background=True
)

Task(
    subagent_type="weekly-comment-mag7-fetcher",
    description="MAG7ニュース収集",
    prompt="...",
    run_in_background=True
)

Task(
    subagent_type="weekly-comment-sectors-fetcher",
    description="セクターニュース収集",
    prompt="...",
    run_in_background=True
)
```

### 3.2 各サブエージェントへの入力

```json
{
  "period": {"start": "2026-01-14", "end": "2026-01-21"},
  "data_file": "articles/weekly_comment_20260122/data/indices.json"
}
```

### 3.3 ニュースコンテキスト統合

```json
// news_context.json
{
  "generated_at": "2026-01-22T09:00:00+09:00",
  "indices": {
    "market_sentiment": "bullish",
    "key_drivers": [...],
    "commentary_draft": "..."
  },
  "mag7": {
    "mag7_analysis": [...],
    "sox_analysis": {...},
    "commentary_draft": "..."
  },
  "sectors": {
    "top_sectors_analysis": [...],
    "bottom_sectors_analysis": [...],
    "commentary_draft": {...}
  }
}
```

## 週次コメント Phase 4: コメント生成（詳細）

### 4.1 テンプレート読み込み

```bash
TEMPLATE="template/market_report/weekly_comment_template.md"
```

### 4.2 プレースホルダー置換

| プレースホルダー | 値の例 |
|-----------------|--------|
| `{report_date_formatted}` | `2026/1/22(Wed)` |
| `{end_date_formatted}` | `1/21` |
| `{spx_return}` | `+2.50%` |
| `{rsp_return}` | `+1.80%` |
| `{vug_return}` | `+3.20%` |
| `{vtv_return}` | `+1.20%` |
| `{indices_comment}` | サブエージェント生成テキスト |
| `{mag7_table}` | MAG7テーブル（Markdown形式） |
| `{mag7_comment}` | サブエージェント生成テキスト |
| `{top_sectors_table}` | 上位セクターテーブル |
| `{top_sectors_comment}` | サブエージェント生成テキスト |
| `{bottom_sectors_table}` | 下位セクターテーブル |
| `{bottom_sectors_comment}` | サブエージェント生成テキスト |

### 4.3 出力文字数目標

| セクション | 最低文字数 |
|-----------|-----------|
| 指数コメント | 500字 |
| MAG7コメント | 800字 |
| 上位セクターコメント | 400字 |
| 下位セクターコメント | 400字 |
| 今後の材料 | 200字 |
| **合計** | **3000字以上** |

## 週次コメント出力例

```markdown
# 2026/1/22(Wed) Weekly Comment

## Indices (AS OF 1/21)

| 指数 | 週間リターン |
|------|-------------|
| S&P 500 | +2.50% |
| 等ウェイト (RSP) | +1.80% |
| グロース (VUG) | +3.20% |
| バリュー (VTV) | +1.20% |

外株です。S&P500指数は週間+2.50%上昇しました。市場全体は...
（500字以上のコメント）

## Magnificent 7

| 銘柄 | 週間リターン |
|------|-------------|
| Tesla | +3.70% |
| NVIDIA | +1.90% |
...

MAG7では、TSLAが+3.70%で週間トップパフォーマーとなりました...
（800字以上のコメント）

## セクター別パフォーマンス

### 上位3セクター
（400字以上のコメント）

### 下位3セクター
（400字以上のコメント）

## 今後の材料
（200字以上のコメント）
```

---

## 制約事項

1. **データソース**: Yahoo Finance APIの制限により、リアルタイムデータではなく前日終値ベース
2. **ニュース検索**: RSS MCP は登録済みフィード（33件）のみ検索可能
3. **決算データ**: earnings.json は今後2週間分の主要企業のみ
4. **レポート言語**: 日本語での出力を前提
5. **週次コメント期間**: 火曜〜火曜の7日間（水曜日に実行推奨）

---

## 関連リソース

- **Pythonスクリプト**: `scripts/market_report_data.py`
- **週次コメントスクリプト**: `scripts/weekly_comment_data.py`
- **テンプレート**: `template/market_report/02_edit/first_draft.md`
- **週次コメントテンプレート**: `template/market_report/weekly_comment_template.md`
- **サンプルレポート**: `template/market_report/sample/20251210_weekly_comment.md`
- **データスキーマ**: `data/schemas/`
- **日付ユーティリティ**: `src/market_analysis/utils/date_utils.py`

## 週次コメント用サブエージェント

- **指数ニュース収集**: `.claude/agents/weekly-comment-indices-fetcher.md`
- **MAG7ニュース収集**: `.claude/agents/weekly-comment-mag7-fetcher.md`
- **セクターニュース収集**: `.claude/agents/weekly-comment-sectors-fetcher.md`

## 関連コマンド

- **ニュース収集**: `/collect-finance-news`
- **記事作成**: `/new-finance-article`
- **リサーチ実行**: `/finance-research`
