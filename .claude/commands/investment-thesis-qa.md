# /investment-thesis-qa — 投資仮説Q&Aシート生成

指定銘柄の投資仮説Q&Aシートを生成する。

## 引数
- `$ARGUMENTS`: ティッカー（例: `ABBV US`, `FCX US`）

## 実行手順

`investment-thesis-qa` スキルをロードして実行する。

### スキルのロード
@.claude/skills/investment-thesis-qa/SKILL.md を参照し、パイプラインを実行する。

### テンプレート
@.claude/skills/investment-thesis-qa/template.md を参照してQ&Aシートを生成する。

### 参考: 成功例
@analyst/Investment Thesis_sample/ABBV US/investment_thesis_qa.md のフォーマットと品質に合わせる。

### 処理フロー

1. **Phase 0**: `analyst/Investment Thesis_sample/$ARGUMENTS/Transcript/` から全.mdファイルを発見し、基準日（1年前）で時系列分割
2. **Phase 1**: SEC EDGAR MCPで会社情報・財務データを取得（期間をTranscriptと揃える）
3. **Phase 2a**: 過去Transcript + SEC EDGARから初期投資仮説8候補を生成（根拠+出典付き）
4. **Phase 2b**: 直近1年Transcript + SEC EDGARから更新情報を検出し、各仮説への影響コメント（200字程度）を記述
5. **Phase 3**: `analyst/Investment Thesis_sample/$ARGUMENTS/investment_thesis_qa.md` にQ&Aシートを出力

### 重要な制約
- 各仮説に出典を明記（EC日付 + ページ番号）
- 8候補のうち1-2件はリスク仮説を含める
- 備考欄はAIの解釈を書かず空欄にする
- Q&Aシートは日本語で記述
- SEC EDGARの参照期間はTranscriptの期間と揃える
