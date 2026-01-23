---
name: weekly-data-aggregation
description: "週次レポート用の入力データを集約・正規化するスキル。indices.json, mag7.json, sectors.json, news_from_project.json を統合し、レポート生成に適した形式に変換する。"
allowed-tools: Read, Glob
---

# Weekly Data Aggregation

週次レポート用の入力データを集約・正規化するスキルです。

## 目的

このスキルは以下を提供します：

- **データ集約**: 複数の入力JSONファイルを読み込み、統合
- **データ正規化**: 異なるフォーマットを統一形式に変換
- **データ検証**: 必須フィールドの存在確認とデフォルト値補完
- **メタデータ生成**: レポート対象期間や生成情報の整理

## いつ使用するか

### プロアクティブ使用

`weekly-report-writer` エージェントの最初のフェーズとして自動的に呼び出される。

### 明示的な使用

週次レポート生成ワークフローの一部として呼び出し。

## 入力データ構造

### 入力ディレクトリ

```
articles/weekly_report/{date}/data/
├── indices.json          # 指数パフォーマンス
├── mag7.json             # MAG7 パフォーマンス
├── sectors.json          # セクター分析
├── news_from_project.json # GitHub Project からのニュース
└── news_supplemental.json # 追加検索結果（任意）
```

### indices.json 形式

```json
{
  "indices": [
    {
      "ticker": "^GSPC",
      "name": "S&P 500",
      "weekly_return": 0.025,
      "ytd_return": 0.032,
      "price": 5850.50,
      "change": 143.25
    }
  ],
  "period": {
    "start": "2026-01-14",
    "end": "2026-01-21"
  }
}
```

### mag7.json 形式

```json
{
  "mag7": [
    {
      "ticker": "AAPL",
      "name": "Apple",
      "weekly_return": 0.015,
      "ytd_return": 0.022,
      "price": 245.30,
      "market_cap": 3800000000000,
      "news": ["決算発表控え", "新製品期待"]
    }
  ]
}
```

### sectors.json 形式

```json
{
  "sectors": [
    {
      "name": "Information Technology",
      "ticker": "XLK",
      "weekly_return": 0.028,
      "weight": 0.295,
      "top_holdings": ["AAPL", "MSFT", "NVDA"]
    }
  ],
  "top_sectors": [...],
  "bottom_sectors": [...]
}
```

### news_from_project.json 形式

```json
{
  "news": [
    {
      "issue_number": 171,
      "title": "記事タイトル",
      "category": "macro",
      "summary": "日本語要約",
      "url": "https://github.com/...",
      "original_url": "https://...",
      "created_at": "2026-01-15T08:30:00Z"
    }
  ],
  "by_category": {
    "indices": [],
    "mag7": [],
    "sectors": [],
    "macro": [],
    "tech": [],
    "finance": []
  }
}
```

## 出力データ構造

### aggregated_data.json

```json
{
  "metadata": {
    "report_date": "2026-01-22",
    "period": {
      "start": "2026-01-14",
      "end": "2026-01-21"
    },
    "generated_at": "2026-01-22T09:00:00+09:00",
    "data_sources": {
      "indices": true,
      "mag7": true,
      "sectors": true,
      "news_from_project": true,
      "news_supplemental": false
    },
    "warnings": []
  },
  "indices": {
    "primary": {
      "spx": { "name": "S&P 500", "return": "+2.50%", "raw": 0.025 },
      "rsp": { "name": "S&P 500 Equal Weight", "return": "+1.80%", "raw": 0.018 },
      "vug": { "name": "Vanguard Growth", "return": "+3.20%", "raw": 0.032 },
      "vtv": { "name": "Vanguard Value", "return": "+1.20%", "raw": 0.012 }
    },
    "all": [...],
    "style_analysis": {
      "growth_vs_value": "グロース優位（+2.00%差）",
      "large_vs_small": "大型株優位（+0.70%差）"
    }
  },
  "mag7": {
    "stocks": [...],
    "top_performer": { "ticker": "TSLA", "return": "+3.70%" },
    "bottom_performer": { "ticker": "META", "return": "-1.20%" },
    "average_return": "+1.45%"
  },
  "sectors": {
    "all": [...],
    "top_3": [...],
    "bottom_3": [...],
    "rotation_signal": "グロース回帰"
  },
  "news": {
    "total_count": 25,
    "by_category": {
      "indices": [...],
      "mag7": [...],
      "sectors": [...],
      "macro": [...],
      "tech": [...],
      "finance": []
    },
    "highlights": [
      "Fed議長がインフレ目標達成への自信を示す",
      "NVDA、AI需要の持続性を強調",
      "エネルギーセクター、原油価格上昇で好調"
    ]
  }
}
```

## プロセス

```
Phase 1: ファイル読み込み
├── 入力ディレクトリの存在確認
├── 各JSONファイルを読み込み
│   ├── indices.json（必須）
│   ├── mag7.json（必須）
│   ├── sectors.json（必須）
│   ├── news_from_project.json（必須）
│   └── news_supplemental.json（任意）
└── パースエラー時は警告を記録

Phase 2: データ検証
├── 必須フィールドの存在確認
├── データ型の検証
├── 欠損値の検出
└── 警告メッセージを収集

Phase 3: データ正規化
├── リターン値をパーセンテージ表記に変換
├── 日付形式を統一（YYYY-MM-DD）
├── ティッカーシンボルを正規化
└── カテゴリ名を統一

Phase 4: データ集約
├── メタデータを生成
├── 指数データを整理
├── MAG7データを整理
├── セクターデータを整理
├── ニュースデータを整理
└── ハイライトを抽出

Phase 5: 出力
└── aggregated_data.json を生成
```

## データ変換ルール

### リターン値の変換

| 入力 | 出力（表示用） | 出力（計算用） |
|------|---------------|---------------|
| `0.025` | `"+2.50%"` | `0.025` |
| `-0.012` | `"-1.20%"` | `-0.012` |
| `0` | `"0.00%"` | `0` |

### ティッカー正規化

| 入力 | 出力 |
|------|------|
| `^GSPC` | `SPX` |
| `^IXIC` | `IXIC` |
| `^DJI` | `DJI` |
| `AAPL` | `AAPL` |

### カテゴリ正規化

| 入力 | 出力 |
|------|------|
| `Index` / `indices` | `indices` |
| `Stock` / `mag7` | `mag7` |
| `Sector` / `sectors` | `sectors` |
| `Macro Economics` / `macro` | `macro` |
| `AI` / `tech` | `tech` |
| `Finance` / `finance` | `finance` |

## デフォルト値補完

入力データが不足している場合、以下のデフォルト値で補完：

| フィールド | デフォルト値 |
|-----------|-------------|
| `weekly_return` | `0.0` |
| `ytd_return` | `null` |
| `news` | `[]` |
| `summary` | `""` |

## 使用例

### 例1: 標準的な集約

**入力**:
```
articles/weekly_report/2026-01-22/data/
├── indices.json ✓
├── mag7.json ✓
├── sectors.json ✓
├── news_from_project.json ✓
```

**出力**:
```json
{
  "metadata": {
    "report_date": "2026-01-22",
    "data_sources": {
      "indices": true,
      "mag7": true,
      "sectors": true,
      "news_from_project": true,
      "news_supplemental": false
    },
    "warnings": []
  },
  ...
}
```

### 例2: データ不足時

**入力**:
```
articles/weekly_report/2026-01-22/data/
├── indices.json ✓
├── mag7.json ✓
├── sectors.json ✗ (欠損)
├── news_from_project.json ✓
```

**出力**:
```json
{
  "metadata": {
    "data_sources": {
      "sectors": false
    },
    "warnings": [
      "sectors.json が見つかりません。デフォルト値で補完します。"
    ]
  },
  "sectors": {
    "all": [],
    "top_3": [],
    "bottom_3": [],
    "rotation_signal": "データなし"
  },
  ...
}
```

## 品質基準

### 必須（MUST）

- [ ] 全ての入力ファイルを読み込む（存在する場合）
- [ ] 必須ファイル不足時は警告を出力
- [ ] データ型を検証し、不正な場合は警告
- [ ] 出力JSONが有効な形式

### 推奨（SHOULD）

- 欠損値を適切なデフォルト値で補完
- スタイル分析（グロース vs バリュー）を含める
- ニュースハイライトを自動抽出

## エラーハンドリング

### E001: 入力ディレクトリが存在しない

```json
{
  "error": "入力ディレクトリが見つかりません",
  "path": "articles/weekly_report/2026-01-22/data/",
  "suggestion": "先にデータ収集フェーズを実行してください"
}
```

### E002: JSONパースエラー

```json
{
  "error": "JSONパースエラー",
  "file": "indices.json",
  "detail": "Unexpected token at line 5"
}
```

### E003: 必須データ欠損

```json
{
  "warning": "必須データが不足しています",
  "missing": ["sectors.json"],
  "action": "デフォルト値で補完して続行"
}
```

## 完了条件

- [ ] 入力ディレクトリからファイルを読み込める
- [ ] データ検証が機能する
- [ ] データ正規化が正しく動作する
- [ ] aggregated_data.json が生成される
- [ ] 警告が適切に記録される

## 関連スキル

- **weekly-comment-generation**: このスキルの出力を使用してコメントを生成
- **weekly-template-rendering**: 集約データをテンプレートに埋め込み
- **weekly-report-validation**: 最終レポートの品質検証

## 参考資料

- `docs/project/project-21/project.md`: 週次レポートプロジェクト計画
- `.claude/agents/weekly-report-news-aggregator.md`: ニュース集約エージェント
