---
name: investment-thesis-qa
description: 指定銘柄の投資仮説Q&Aシートを生成する。SEC EDGAR + Earnings Call Transcriptから投資仮説を1銘柄8候補生成し、アナリストに納得度を回答してもらうためのシート。/investment-thesis-qa <ticker> で実行。Transcriptが analyst/Investment Thesis_sample/<ticker>/Transcript/ に配置済みであることが前提。銘柄分析、投資仮説生成、AN目線シード収集に使用。
---

# 投資仮説Q&Aシート生成

アナリストの暗黙知（情報の取捨選択基準）を引き出すためのQ&Aシートを生成するスキル。
Earnings Call Transcript + SEC EDGARから投資仮説を1銘柄8候補生成し、各仮説に対するアナリストの「納得度」を収集する。

## 使い方

```
/investment-thesis-qa ABBV US
/investment-thesis-qa "FCX US"
```

引数にティッカーを指定する。スペースを含むティッカーもそのまま渡せる。

## 前提条件

- `analyst/Investment Thesis_sample/<ticker>/Transcript/` にMarkdown化済みのEarnings Call Transcriptが配置されていること
- ファイル名の先頭8文字が `YYYYMMDD` 形式であること（それ以降のパターンは問わない）
- PDFからMDへの変換がまだの場合は `uv run python scripts/convert_transcripts_to_md.py` を先に実行すること

## パイプライン概要

```
Phase 0: Transcript発見 + 時系列分割（基準日 = 1年前）
    ↓
Phase 1: SEC EDGAR情報取得（初期期間 / 更新期間）
    ↓
Phase 2a: 初期投資仮説8候補生成（過去Transcript + SEC EDGAR）
    ↓
Phase 2b: 更新情報検出 + 初期仮説への影響コメント（直近1年Transcript + SEC EDGAR）
    ↓
Phase 3: Q&Aシート出力（template.md に従って生成）
```

## 詳細手順

### Phase 0: Transcript発見と時系列分割

1. `analyst/Investment Thesis_sample/<ticker>/Transcript/` から全 `.md` ファイルを取得
2. ファイル名の先頭8文字（YYYYMMDD）で日付を特定しソート
3. 基準日（**今日から1年前**）で2グループに分割:
   - **初期仮説構築用**: 基準日より前のTranscript
   - **更新情報用**: 基準日以降のTranscript
4. 各グループの最古・最新日付を記録（ソース情報テーブルに使う）

ファイル名から日付を取得する際は先頭8文字のみに依存すること。それ以降の命名パターンは将来変更される可能性がある。

### Phase 1: SEC EDGAR情報取得

ティッカーから会社名を特定するためにまず SEC EDGAR MCP を使う:

```
mcp__sec-edgar-mcp__get_company_info — 会社名・CIK取得
mcp__sec-edgar-mcp__get_financials — 財務データ取得
mcp__sec-edgar-mcp__get_key_metrics — 主要指標取得
```

取得した財務データは時系列に合わせて分割する:
- **初期仮説構築期間**: Transcript期間と揃えた会計年度のfiling
- **更新情報期間**: 直近1年に対応するfiling

### Phase 2a: 初期投資仮説8候補生成

初期仮説構築用Transcript（全件読み込み）+ SEC EDGAR（初期期間）をベースに、8つの投資仮説候補を生成する。

**仮説の粒度**: 「ある事業セグメントの成長率/利益率がX%になる具体的な理由」レベル。抽象的すぎず（「競争優位がある」）、細かすぎない（「Q3のR&D費が$2.3B」）。

**以下の観点から幅広く候補を生成する（全てカバーする必要はない）**:

| 観点 | 例 |
|------|-----|
| 主力製品/事業の売上成長ドライバー | 製品シェア拡大、適応拡大、価格力 |
| パイプライン/新規事業の成長寄与 | 新薬承認、新規参入市場 |
| 競争環境と価格力 | 競合参入、寡占構造、価格弾性 |
| 利益率の改善/悪化要因 | ミックス改善、コスト構造変化 |
| 資本配分 | 自社株買い、配当、M&A |
| 規制・政策リスク | 薬価交渉、関税、規制変更 |
| セグメントミックスの変化 | 高マージン事業の比率変化 |
| マクロ環境の影響 | 金利、為替、景気サイクル |

**重要なルール**:
- 8候補のうち **1-2件はリスク仮説**（投資前提が崩れるシナリオ）を含める
- 仮説は互いに**重複しない**ようにする
- 各仮説に必ず **根拠情報テーブル**（情報 + 出典）を付ける
- 出典は **EC日付 + ページ番号**（Markdownファイル内の `<!-- Page X -->` コメントを参照）

### Phase 2b: 更新情報検出と影響コメント

更新情報用Transcript（全件読み込み）+ SEC EDGAR（更新期間）を使って、Phase 2aで生成した各仮説に対して:

1. **変化の方向**: 以下から選択
   - 強化 / 変化なし / 弱体化 / リスク顕在化 / リスク低減

2. **初期仮説への影響コメント**: 200字程度で以下を記述
   - 初期仮説構築時点ではどうだったか
   - 直近1年で何が変わったか
   - その変化が投資前提にどのような影響を与えたか
   - このコメントが、アナリストが仮説の変化を一目で理解できる情報になっていること

3. **更新情報の箇条書き**: 具体的な数字・事実を箇条書きで列挙
4. **出典**: EC日付 + ページ番号

### Phase 3: Q&Aシート出力

`template.md` の構造に従ってMarkdownファイルを生成し、以下のパスに書き出す:

```
analyst/Investment Thesis_sample/<ticker>/investment_thesis_qa.md
```

テンプレートの詳細は `.claude/skills/investment-thesis-qa/template.md` を参照。

## 制約事項

| ルール | 理由 |
|--------|------|
| 各仮説に必ず出典を明記 | アナリストが元情報を検証できるようにする |
| 備考欄はAIの解釈を書かず空欄にする | アナリストの自由記述用 |
| Q&Aシートは日本語で記述 | 回答者が日本語話者のため |
| SEC EDGARの参照期間をTranscriptと揃える | 時系列の整合性を保つ |
| 価格/バリュエーション仮説は含めない | データソース未整備のため（今後対応予定） |

## 参考: 成功例

`analyst/Investment Thesis_sample/ABBV US/investment_thesis_qa.md` が完成済みのプロトタイプ。フォーマットと品質はこれに合わせる。

## 関連ファイル

| ファイル | 用途 |
|---------|------|
| `.claude/skills/investment-thesis-qa/template.md` | Q&Aシートのテンプレート |
| `scripts/convert_transcripts_to_md.py` | PDF→Markdown変換スクリプト |
| `analyst/Investment Thesis_sample/ABBV US/investment_thesis_qa.md` | プロトタイプ（参考用） |
| `docs/plan/2026-04-10_discussion-an-perspective-seed-collection.md` | 設計議論メモ |
