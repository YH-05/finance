# 議論メモ: AN目線シード収集 — 投資仮説Q&A設計と実装

**日付**: 2026-04-10
**議論ID**: disc-2026-04-10-an-seed-collection
**参加**: ユーザー + AI
**前回議論**: disc-2026-04-09-fm-an-perspective
**ステータス**: 実装フェーズ（プロトタイプ完成、7銘柄一括生成中）

## 背景・コンテキスト

前回（2026-04-09）の議論で、FM目線とAN目線の構造的差異、dogmaフィードバックループの限界が確認された（全て未決定）。
今回は推奨レポート全23件を分析し、AN目線の暗黙知抽出の具体的手法を検討・決定し、プロトタイプの実装まで完了した。

## 議論の経緯

### 1. 推奨レポート23件の全件分析

analyst/recommendation/ 配下の23フォルダを全件読み込み分析：
- BUY 7件: FB US, GOOGL US, 2330 TT, NVDA US, AHT LN, VRSK US, MCO US
- SELL 16件: PUB FP, SRCL US, BNZL LN, BXB AU, MMM US, TEL US, RELX NA, HUB AU, PLTR US, SPGI US, 2318 HK, BEZ LN, OKTA US, FRC US, SBNY US, STJ LN

レポート構造: TextBox 1(S/T変化) / 2(バリュエーション/ITG/CAGR) / 3(会社概要) / 4(競争優位性) / 5(ESG、2022年以降)

SELL判断の5タイプを分類:
- Type A: バリュエーション高値（MMM, TEL, SPGI）
- Type B: 競争優位の外部無効化（PUB, SRCL, BNZL, BXB, HUB, BEZ, 2318 HK）
- Type C: 比較劣位（RELX, PLTR）
- Type D: 定量ROE基準未達（FRC, SBNY）
- Type E: CAGR確度崩壊（OKTA, STJ LN）

### 2. 「着眼フレーム」仮説の棄却

当初の分析で「AN目線 = 着眼フレームの選択」と仮説を立てたが、以下の理由で棄却：
- BUY 7件から抽出した「7フレーム」は各社の競争優位性の個別記述に過ぎず、抽象的なフレームではなかった
- さらに抽象化（Helmerの7 Powers等）してもそれはAIの後付け分類であり、Yの思考と一致する保証がない

### 3. Yの特性に関する重要な制約条件（ユーザーからの情報）

1. **Yはフレームワークを意識していない**。「私は入ってきた情報を分析して銘柄推奨のアウトプットを出すだけ」
2. **FM目線 vs AN目線の再定義**:
   - FM目線：推奨理由をフレームワークに落とし込んで「批評する」側。ピンポイントで探すものではない
   - AN目線：推奨ポイント（=投資前提）を「述べ」、その前提が崩れていないかを「検証する」
3. **ロングオンリーファンド**：BUYの理由の設定が最重要。SELLは「もうBUYの理由がない」ことの確認
4. ITG = Implied Terminal Growth

### 4. AN目線の核心の特定

AN目線で未体系化なのは「投資前提をどう設定するか」。

Yのプロセス：
```
大量の情報 → [取捨選択（= 暗黙知）] → 投資前提の設定 → BUY/SELL
```

レポートのTextBox 2/4に書かれているのは「選ばれた情報とその解釈」であり、「選び方のルール」ではない。
Yに聞くべきことは「この銘柄について、どの情報が投資判断に最も影響するか」。

### 5. 大量シード生成の方針決定

SEC EDGAR + Transcriptから投資仮説候補を大量生成し、Yの選択パターンを収集する方針に合意。

### 6. プロトタイプ実装（ABBV USで検証）

#### 6.1 PDF→Markdown変換
- `scripts/convert_transcripts_to_md.py` を作成し、98件のTranscript PDFを一括変換（pymupdf使用、約9秒で完了）
- ファイル名パターン: `YYYYMMDD_*.md`（先頭8文字が日付）

#### 6.2 時系列分割
- 基準日（1年前）で初期仮説構築用と更新情報用に分割
- ABBV US: 初期7件（2023-04〜2025-01）、更新4件（2025-04〜2026-02）

#### 6.3 ABBV USプロトタイプ作成と3回の修正

**第1版**: サブエージェントが初期仮説構築用Transcript + SEC EDGAR → 8候補生成 → Q&Aシート出力
**修正1**: SEC EDGAR参照期間をTranscriptと揃える、冒頭にBUY/SELL総合判断欄追加、バリュエーション仮説なしの注記追加
**修正2**: 備考欄のAI解釈を全て空欄化
**修正3**: 更新情報セクションに「初期仮説への影響」コメント（200字程度）を追加

#### 6.4 最終Q&Aシートの構造

```
冒頭: BUY/SELL総合判断欄 + 納得度スケール説明
ソース情報: 初期仮説構築期間 / 更新情報期間
仮説1-6: ポジティブ仮説（根拠情報テーブル + 更新情報 + 影響コメント + 納得度 + 備考）
仮説7-8: リスク仮説（同構造）
補足: SEC EDGAR財務サマリー（2期間）
```

### 7. スキル・コマンド整備

- `.claude/skills/investment-thesis-qa/SKILL.md` — パイプライン定義
- `.claude/skills/investment-thesis-qa/template.md` — Q&Aシートテンプレート
- `.claude/commands/investment-thesis-qa.md` — `/investment-thesis-qa <ticker>` コマンド

### 8. 7銘柄一括実行開始

対象8銘柄:
| ティッカー | 会社 | 業種 | 状態 |
|-----------|------|------|------|
| ABBV US | AbbVie | バイオ医薬品 | 完了 |
| DASH US | DoorDash | フードデリバリー | 実行中 |
| FCX US | Freeport-McMoRan | 銅鉱山 | 実行中 |
| GEV US | GE Vernova | 電力・エネルギー | 実行中 |
| JPM US | JPMorgan Chase | 銀行 | 実行中 |
| KR US | Kroger | 食品小売 | 実行中 |
| MU US | Micron Technology | メモリ半導体 | 実行中 |
| VZ US | Verizon | 通信 | 実行中 |

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-10-001 | AN目線の暗黙知 = Yの「情報の取捨選択基準」であり、フレームワークではない | Yが「フレームワークを意識していない」と明言。23件のレポート分析でも着眼フレーム仮説は個別記述の要約に過ぎなかった |
| dec-2026-04-10-002 | SEC EDGAR + Transcriptから投資仮説を1銘柄8候補生成し、YにQ&Aで回答してもらう | 情報候補をAIが提示→Yが取捨選択→パターン蓄積→基準抽出 |
| dec-2026-04-10-003 | 対象は未推奨の米国企業（8銘柄指定済み） | ABBV, DASH, FCX, GEV, JPM, KR, MU, VZ |
| dec-2026-04-10-004 | 仮説の粒度 =「ある事業セグメントの成長率/利益率がX%になる具体的な理由」レベル | 23件のレポートで確認されたYの投資前提の粒度に合わせる |
| dec-2026-04-10-005 | Q&A形式: 8候補それぞれに納得度ウェイト（90%/70%/50%/30%/10%の5段階） | 四択+Eや上位N選択ではなく、全候補への重み付け |
| dec-2026-04-10-006 | ca_strategyのTranscript処理を参考にする（ファイルパターン変更の可能性あり） | 既存のtranscript→主張抽出の仕組みは流用可能 |
| dec-2026-04-10-007 | Q&Aシート冒頭にBUY/SELL総合判断欄を設置 | アナリストが一見して判断を求められていることを理解できるようにする |
| dec-2026-04-10-008 | 更新情報セクションに「初期仮説への影響」コメント（200字程度）を記述 | 変化の方向（強化/弱体化等）だけでなく、初期仮説と比較して何がどう変わったかを明示する |
| dec-2026-04-10-009 | SEC EDGAR参照期間をTranscriptの期間と揃える | 時系列の整合性を保つ |
| dec-2026-04-10-010 | 備考欄はAIの解釈を書かず空欄にする | アナリストの自由記述用 |
| dec-2026-04-10-011 | /investment-thesis-qa スキルコマンドを作成 | 一括実行可能な再現性の高いパイプラインとして整備 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-04-10-001 | プロトタイプ設計書の作成 | 高 | **完了**（スキルとして整備済み） |
| act-2026-04-10-002 | 対象銘柄の指定 | 高 | **完了**（8銘柄指定済み） |
| act-2026-04-10-003 | PDF→Markdown変換 | 高 | **完了**（98件一括変換済み） |
| act-2026-04-10-004 | 投資仮説8候補の生成 | 高 | **進行中**（ABBV完了、7銘柄実行中） |
| act-2026-04-10-005 | Q&Aシート作成 | 高 | **進行中** |
| act-2026-04-10-006 | 既存23件レポートのBUY 7件を使ったプロンプト精度検証 | 中 | 未着手（任意） |
| act-2026-04-10-007 | 7銘柄のQ&Aシート完成確認 | 高 | 待機中 |
| act-2026-04-10-008 | YへのQ&Aシート提示・回答収集 | 高 | 待機中 |
| act-2026-04-10-009 | 回答パターン分析 → 取捨選択基準の抽出 | 高 | 待機中 |

## 次回の議論トピック

- 7銘柄のQ&Aシート品質確認
- YへのQ&Aシート提示方法（Markdown直接 or 変換形式）
- 回答収集後の分析手法（選択パターンからどう基準を抽出するか）
- バリュエーションデータの拡充方針
- 追加銘柄の選定（必要に応じてユニバースに展開）

## 成果物一覧

| 成果物 | パス |
|--------|------|
| PDF→MD変換スクリプト | `scripts/convert_transcripts_to_md.py` |
| 変換済みTranscript | `analyst/Investment Thesis_sample/*/Transcript/*.md`（98件） |
| ABBV USプロトタイプ | `analyst/Investment Thesis_sample/ABBV US/investment_thesis_qa.md` |
| スキル定義 | `.claude/skills/investment-thesis-qa/SKILL.md` |
| テンプレート | `.claude/skills/investment-thesis-qa/template.md` |
| コマンド定義 | `.claude/commands/investment-thesis-qa.md` |

## 参考情報

- 前回議論: `docs/plan/2026-04-09_discussion-fm-an-perspective.md`
- 推奨レポート: `analyst/recommendation/` (23件)
- dogma v1.0: `analyst/Competitive_Advantage/analyst_YK/dogma/dogma_v1.0.md`
- ca_strategy: `src/dev/ca_strategy/`
- メモリ: `project_fm_an_perspective_discussion.md`
