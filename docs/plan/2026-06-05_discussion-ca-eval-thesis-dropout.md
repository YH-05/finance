# 議論メモ: ca-eval 中間プロセスでのアナリスト見解脱落問題の発見と改善提案

**日付**: 2026-06-05
**議論ID**: disc-2026-06-05-ca-eval-thesis-dropout
**Project**: quants-analyst-tacit-knowledge
**参加**: ユーザー + AI
**関連議論**: disc-2026-05-11-feedback-loop-recap（AIレポート×アナリストYフィードバックループ）の一環
**成果物**: `analyst/research/CA_eval_20260226-2105_MSFT/システム改善提案_中間プロセスでのアナリスト見解脱落.md`（コミット `2fbcb5b`）

## 背景・コンテキスト

ca-eval（競争優位性評価）ワークフローの MSFT 評価で、主張#2「Azureクラウドプラットフォーム」の AI 評価が、アナリストの「市場成長以上のIC事業売上CAGR（6/13/24版）」見解を考慮しているかをデータをたどって検証する依頼から始まった。アナリスト自身も `Feedback_MSFT.md` で「AN見解が見落とされているのでは？」と指摘していた。

## 議論のサマリー（検証の流れ）

アナリスト見解「Azureの成長 = 市場成長(LDD) + **シェアゲイン**(MDD) = **市場アウトパフォーム**（Others がシェア喪失）」が、各中間ファイルでどう扱われたかを全段階追跡した。

| 段階 | 生成主体 | シェアゲイン見解の扱い |
|------|---------|----------------------|
| ① parsed-report.json | T2 ca-report-parser | source_text に記述あり（比較命題は非構造化） |
| ② claims.json | T4 ca-claim-extractor | ✅ CAGR 70%の根拠に「市場アウトパフォーム想定」「過去実績と整合」を明示採用 |
| ③ fact-check.json | T5 ca-fact-checker | ❌ 数値事実のみ検証、シェアゲイン命題は検証対象に不在 |
| ③ pattern-verification.json | T6 ca-pattern-verifier | ⚠️ CAGR側に痕跡 / CA側でパターンA・Gにより弱点化 |
| ④ structured.json | T7 ca-report-generator | ❌ スキーマに元見解フィールドなし、数値要約に縮約 |
| ④ critique.json | T8 Lead直接 | ❌ claims.json を読まず「市場成長か固有か不明確」で70%→50% |
| ④ revised-report.md | T8 Lead | ❌ アナリスト断定（シェアゲイン）の正反対に記述 |

**根本原因 = T7→T8 境界**: ①structured.json スキーマに元見解フィールドがない、②T8入力に claims.json が含まれない（ca-eval-lead.md L742）、③T8 が「下流要約 vs KB」のみで批判するため明言済み見解を否定方向に再発見する。

サブエージェント2体（検証データ精読・実装構造調査）を活用してエビデンスを固めた。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-06-05-002 | T7→T8 境界の構造的欠陥を確認、改善は最小介入 A+B+C を優先方針とする | A: structured.schema に analyst_view 追加 / B: T8入力に claims.json 追加 / C: critique に source_reference 必須化。fact-checkが数値のみ・structuredに元見解なし・T8が下流要約とKBのみ、の複合原因 |
| dec-2026-06-05-003 | 今回は実装着手せず、改善提案レポートの作成のみで完了 | ユーザー判断。レポートはリポジトリに保存済み（コミット `2fbcb5b`） |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-06-05-003 | ca-eval 改善の最小介入セット A+B+C を実装（structured.schema/ca-eval-lead.md/critique.schema） | 中 | pending |
| act-2026-06-05-004 | 改善後 MSFT ケースを再実行し、主張#2 の T8 がシェアゲイン見解を引用評価する形に変わることを回帰検証 | 低 | pending |

## 次回の議論トピック

- 改善実装（A+B+C）に着手するかの判断とタイミング
- 補強提案 D/E/F（fact-check の定性命題保護・parsed-report の比較命題構造化・脱落チェックステップ新設）の要否
- 他銘柄（MNST 等）でも同種の見解脱落が起きていないかの横断点検

## 参考情報

- 改善提案レポート全文: `analyst/research/CA_eval_20260226-2105_MSFT/システム改善提案_中間プロセスでのアナリスト見解脱落.md`
- 実装の主要所在: `ca-eval-lead.md` L742（T8入力定義）, `templates/schemas/structured.schema.md`, `critique.schema.md`, `ca-fact-checker.md` L12
- 検証根拠データ: 同ディレクトリ 02_claims/claims.json, 03_verification/*, 04_output/{critique.json, structured.json, revised-report-MSFT.md}, Feedback_MSFT.md
