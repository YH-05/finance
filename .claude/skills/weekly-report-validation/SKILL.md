---
name: weekly-report-validation
description: "週次レポートの品質検証スキル。Markdownフォーマット、文字数、データ整合性をチェックし、LLMによる内容レビューを実行する。"
allowed-tools: Read
---

# Weekly Report Validation

生成された週次レポートの品質検証を行うスキルです。

## 目的

このスキルは以下を提供します：

- **フォーマット検証**: Markdown構文、テーブル形式の確認
- **文字数検証**: 各セクションと合計の文字数チェック
- **データ整合性検証**: 数値の妥当性、データ一貫性の確認
- **内容品質検証**: LLMによるレビューとフィードバック

## いつ使用するか

### プロアクティブ使用

`weekly-report-writer` エージェントの最終フェーズとして、`weekly-template-rendering` の後に呼び出される。

### 明示的な使用

週次レポート生成ワークフローの一部として、または単独で品質検証を実行。

## 入力データ

### 必須ファイル

```
articles/weekly_report/{date}/02_edit/
├── weekly_report.md       # 検証対象のMarkdownレポート
└── weekly_report.json     # 検証対象の構造化データ
```

### 参照ファイル

```
articles/weekly_report/{date}/data/
├── aggregated_data.json   # 元データ（整合性確認用）
└── comments.json          # コメントデータ（文字数確認用）
```

## 出力データ

### validation_result.json

```json
{
  "metadata": {
    "validated_at": "2026-01-22T10:00:00+09:00",
    "report_date": "2026-01-22",
    "validator_version": "1.0.0"
  },
  "overall": {
    "status": "pass",
    "score": 95,
    "grade": "A"
  },
  "checks": {
    "format": {
      "status": "pass",
      "score": 100,
      "details": {
        "markdown_valid": true,
        "tables_valid": true,
        "headings_consistent": true,
        "links_valid": true
      }
    },
    "character_count": {
      "status": "pass",
      "score": 95,
      "details": {
        "total": 3450,
        "target": 3200,
        "sections": {
          "highlight": { "actual": 220, "target": 200, "status": "pass" },
          "indices": { "actual": 520, "target": 500, "status": "pass" },
          "mag7": { "actual": 850, "target": 800, "status": "pass" },
          "sectors_top": { "actual": 420, "target": 400, "status": "pass" },
          "sectors_bottom": { "actual": 410, "target": 400, "status": "pass" },
          "macro": { "actual": 430, "target": 400, "status": "pass" },
          "themes": { "actual": 320, "target": 300, "status": "pass" },
          "outlook": { "actual": 210, "target": 200, "status": "pass" }
        }
      }
    },
    "data_integrity": {
      "status": "pass",
      "score": 100,
      "details": {
        "numbers_valid": true,
        "dates_consistent": true,
        "calculations_correct": true
      }
    },
    "content_quality": {
      "status": "pass",
      "score": 90,
      "details": {
        "factual_accuracy": "high",
        "readability": "good",
        "investment_disclaimer": true,
        "balanced_view": true
      },
      "llm_feedback": "レポートは全体的に高品質です。指数分析とMAG7の解説が特に充実しています。"
    }
  },
  "issues": [],
  "warnings": [
    {
      "type": "minor",
      "section": "themes",
      "message": "投資テーマセクションの文字数がやや少なめです（320字/目標300字）"
    }
  ],
  "recommendations": [
    "来週のレポートでは、マクロ経済セクションにより詳細な経済指標の分析を追加することを検討してください。"
  ]
}
```

## 検証チェックリスト

### 1. フォーマット検証

| チェック項目 | 説明 | 重要度 |
|-------------|------|--------|
| Markdown構文 | 正しいMarkdown構文か | 必須 |
| テーブル形式 | テーブルが正しくレンダリングされるか | 必須 |
| 見出し階層 | H1 → H2 → H3 の順序が正しいか | 必須 |
| リンク有効性 | 内部リンクが有効か | 推奨 |
| 文字エンコーディング | UTF-8でエンコードされているか | 必須 |

### 2. 文字数検証

| チェック項目 | 条件 | 重要度 |
|-------------|------|--------|
| 合計文字数 | 3000字以上 | 必須 |
| セクション文字数 | 目標の±30%以内 | 推奨 |
| 空セクションなし | 各セクションに内容があるか | 必須 |

### 3. データ整合性検証

| チェック項目 | 説明 | 重要度 |
|-------------|------|--------|
| 数値の妥当性 | リターンが-100%〜+100%の範囲か | 必須 |
| 日付の一貫性 | 対象期間が正しいか | 必須 |
| ランキングの整合性 | 上位/下位セクターが正しい順序か | 推奨 |
| ティッカーの一致 | MAG7銘柄が正しいか | 推奨 |

### 4. 内容品質検証（LLMレビュー）

| チェック項目 | 説明 | 重要度 |
|-------------|------|--------|
| 事実正確性 | データに基づいた記述か | 必須 |
| 読みやすさ | 文章が読みやすいか | 推奨 |
| 投資免責事項 | 適切な免責事項があるか | 必須 |
| バランスの取れた視点 | 一方的でないか | 推奨 |
| 専門用語の適切性 | 過度に専門的でないか | 推奨 |

## プロセス

```
Phase 1: ファイル読み込み
├── weekly_report.md 読み込み
├── weekly_report.json 読み込み
├── aggregated_data.json 読み込み（参照用）
└── comments.json 読み込み（参照用）

Phase 2: フォーマット検証
├── Markdown構文チェック
├── テーブル形式チェック
├── 見出し階層チェック
└── リンク有効性チェック

Phase 3: 文字数検証
├── 各セクションの文字数計測
├── 目標との比較
├── 空セクションチェック
└── 合計文字数確認

Phase 4: データ整合性検証
├── 数値の範囲チェック
├── 日付の一貫性チェック
├── ランキング順序チェック
└── 元データとの照合

Phase 5: 内容品質検証
├── LLMによるレビュー実行
│   ├── 事実正確性評価
│   ├── 読みやすさ評価
│   ├── 免責事項確認
│   └── バランス評価
└── フィードバック生成

Phase 6: 結果出力
├── スコア計算
├── 問題・警告リスト作成
├── 推奨事項生成
└── validation_result.json 出力
```

## スコアリング

### 総合スコア計算

```
overall_score = (
  format_score × 0.25 +
  character_count_score × 0.25 +
  data_integrity_score × 0.25 +
  content_quality_score × 0.25
)
```

### グレード判定

| スコア | グレード | 説明 |
|--------|---------|------|
| 95-100 | A | 優秀 - 修正不要 |
| 85-94 | B | 良好 - 軽微な改善推奨 |
| 70-84 | C | 可 - 改善が必要 |
| 50-69 | D | 要改善 - 複数の問題あり |
| 0-49 | F | 不合格 - 再生成が必要 |

### 合否判定

- **pass**: 総合スコア70以上、かつ必須チェック全てパス
- **fail**: 総合スコア70未満、または必須チェックに失敗

## LLMレビュープロンプト

```markdown
以下の週次マーケットレポートをレビューしてください。

## レビュー観点

1. **事実正確性**: データに基づいた正確な記述か
2. **読みやすさ**: 一般投資家が理解しやすい文章か
3. **バランス**: 楽観・悲観が偏りすぎていないか
4. **投資免責**: 適切な免責事項が含まれているか
5. **専門性**: 適切な専門用語の使用か

## 出力形式

{
  "factual_accuracy": "high/medium/low",
  "readability": "excellent/good/fair/poor",
  "balanced_view": true/false,
  "investment_disclaimer": true/false,
  "feedback": "全体的なフィードバック",
  "improvements": ["改善点1", "改善点2"]
}

## レポート内容

{report_content}
```

## 使用例

### 例1: 合格（グレードA）

**入力**: 高品質なレポート

**出力**:
```json
{
  "overall": {
    "status": "pass",
    "score": 95,
    "grade": "A"
  },
  "issues": [],
  "warnings": []
}
```

### 例2: 合格（グレードB、警告あり）

**入力**: 文字数がやや少ないレポート

**出力**:
```json
{
  "overall": {
    "status": "pass",
    "score": 85,
    "grade": "B"
  },
  "issues": [],
  "warnings": [
    {
      "type": "minor",
      "section": "macro",
      "message": "マクロ経済セクションの文字数が目標を下回っています（280字/目標400字）"
    }
  ]
}
```

### 例3: 不合格（グレードD）

**入力**: 問題のあるレポート

**出力**:
```json
{
  "overall": {
    "status": "fail",
    "score": 55,
    "grade": "D"
  },
  "issues": [
    {
      "type": "critical",
      "check": "character_count",
      "message": "合計文字数が目標を大幅に下回っています（1800字/目標3000字）"
    },
    {
      "type": "critical",
      "check": "format",
      "message": "MAG7テーブルが正しくレンダリングされません"
    }
  ],
  "recommendations": [
    "コメント生成を再実行し、各セクションの文字数を増やしてください",
    "テーブル形式を確認し、Markdown構文を修正してください"
  ]
}
```

## 品質基準

### 必須（MUST）

- [ ] 全ての必須チェックを実行
- [ ] 問題があれば明確に報告
- [ ] validation_result.json を出力
- [ ] 合否判定を提供

### 推奨（SHOULD）

- 具体的な改善推奨を提供
- LLMレビューを実行
- スコアとグレードを提供
- 警告を適切に分類

## エラーハンドリング

### E001: レポートファイル不足

```json
{
  "error": "検証対象のファイルが見つかりません",
  "missing": ["weekly_report.md"],
  "suggestion": "先に weekly-template-rendering を実行してください"
}
```

### E002: LLMレビュー失敗

```json
{
  "warning": "LLMレビューを実行できませんでした",
  "detail": "API timeout",
  "action": "LLMレビューをスキップし、他のチェックのみで判定"
}
```

## 完了条件

- [ ] フォーマット検証が完了
- [ ] 文字数検証が完了
- [ ] データ整合性検証が完了
- [ ] 内容品質検証が完了（LLMレビュー）
- [ ] validation_result.json が出力される
- [ ] 合否判定が提供される

## 関連スキル

- **weekly-data-aggregation**: 元データを提供
- **weekly-comment-generation**: コメントデータを提供
- **weekly-template-rendering**: 検証対象レポートを生成

## 参考資料

- `docs/project/project-21/project.md`: 週次レポートプロジェクト計画
- `docs/coding-standards.md`: 品質基準の参考
