# 議論メモ: NSE オーナー企業スクリーニング設計 + Promoter 分類 1 次情報調査

**日付**: 2026-04-16
**議論 ID**: `disc-2026-04-16-nse-owner-company-filter`
**関連プロジェクト**: `project-106: NSE パッケージ拡張 + 全銘柄データ取得ノートブック`
**前回議論**: `disc-2026-04-14-nse-phase4-completion` (NSE Phase 4 完了 + DB 破損復旧)

## 背景・コンテキスト

project-106 の完了により、NSE 全 2,263 銘柄の shareholding pattern XBRL データが `data/cache/nse/nse_index.db` + 銘柄別 `shareholding_detail.csv` に取得済み。次ステップとして、インドのファミリー企業（創業者・家族が実質支配する上場企業）を category/sub-category 分類から自動抽出するロジックが必要となった。

ユーザー要求:
1. NSE shareholding の category / sub-category 分類から「Promoter が本人・親族」な銘柄を見分ける方法を、SEBI/NSE 1 次情報限定で徹底調査
2. その上で「Promoter が自然人かつ Promoter and Promoter Group 合計持分 > 10%」の銘柄（オーナー企業）を特定する実装

## 議論のサマリー

### フェーズ 1: SEBI/NSE 1 次情報調査

general-purpose エージェントに調査委譲し、以下を verbatim 取得:
- **SEBI (ICDR) Regulations 2009 Reg 2(1)(za)(zb)**: promoter / promoter group 定義（`sebi.gov.in/acts/icdrreg.html`）
- **SEBI (SAST) Regulations 2011 Reg 2(1)(l)**: immediate relative = "spouse / parent / brother / sister / child of person or of spouse"（`sebi.gov.in/sebi_data/attachdocs/1367922725672.pdf`）
- **SEBI (LODR) Regulations 2015 Reg 2(1)(w)(zd)**: ICDR / Companies Act 準用（`sebi.gov.in/sebi_data/attachdocs/1441284401427.pdf`）
- **Companies Act 2013 §2(69) promoter / §2(77) relative**: `indiacode.nic.in/bitstream/123456789/2114/5/A2013-18.pdf`
- **BSE SHP XBRL Taxonomy 2022-09-30**: `bseindia.com/downloads1/SHPTaxonomy.zip` の XSD + Label XML で全 promoter-related Member の正式名・英語ラベル verbatim

成果物: `research/2026-04-16_nse_promoter_classification/research.md`（391 行）+ `sources/`（証拠ファイル一式）。

### フェーズ 2: オーナー企業特定ロジック設計

実データ（RELIANCE 2025-03-31）で重要発見:
- Promoter 合計 50.11% の内訳で `IndividualsOrHinduUndividedFamily` は **0.84%のみ**（Ambani 家 4 名直接）
- 残り 49.26% は `OtherIndianShareholders` = 家族系 holding companies 経由
- SEBI ICDR 2(1)(zb)(iv)(A) により、自然人が 10%以上所有する body corporate は promoter group に含まれるため、この構造は法的に正当

結論: **自然人直接保有だけを見ると RELIANCE 等のファミリー大企業が漏れる**。`自然人 signal > 0` の条件でフィルタすれば direct 型・holding 経由型の両方を捕捉可能。

### フェーズ 3: 実装

`notebook/NSE/nse_owner_company_filter.ipynb`（17 セル）を作成。pandas のみで `data/exports/nse/*.csv` から 3 段階フィルタを実行し `owner_companies.csv` を出力する構成。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| `dec-2026-04-16-001` | Promoter sub-category を「自然人 / 法人・政府 / 信託」の 3 系統に分類。自然人集合は 6 種 | SEBI ICDR 2009 Reg 2(1)(zb) + BSE SHP XBRL Taxonomy 2022-09-30 Member ラベル準拠 |
| `dec-2026-04-16-002` | オーナー企業特定は 3 段階フィルタ: Stage1 promoter≥10%, Stage2 natural_sum>0, Stage3 govt_sum<0.5% | Stage1=SAST 2011 Reg 3 閾値、Stage3=PSU 除外 + 微小政府持分許容 |
| `dec-2026-04-16-003` | 1 次情報は sebi.gov.in / nseindia.com / bseindia.com / indiacode.nic.in の 4 ドメイン限定 | Wikipedia 等の 2 次情報は排除。verbatim 取得失敗項目は research.md §7 に明記 |
| `dec-2026-04-16-004` | 再集計行 `{Indian, Foreign, Goverments, Governments, CentralAndStateGovernments}` は SUM から除外 | XBRL taxonomy の中間集計行を SUM すると二重計上。個別 sub_category を明示列挙 |
| `dec-2026-04-16-005` | Holding company 経由型（RELIANCE 型）も自然人 signal > 0 で捕捉。direct / holding の 2 類型を許容 | SEBI ICDR 2(1)(zb)(iv)(A) により家族系法人は promoter group 所属、PromoterAndPromoterGroup 合計に既ロールアップ済み |
| `dec-2026-04-16-006` | 実装はライブラリ層ではなく notebook 層（pandas）から開始。将来 xbrl.py へ関数化 | `data/exports/nse/*.csv` を入力にすることで market.nse モジュール依存を回避、検証容易性を優先 |

## アクションアイテム

| ID | 内容 | 優先度 | 期限 |
|----|------|--------|------|
| `act-2026-04-16-001` | `nse_owner_company_filter.ipynb` 実行、`owner_companies.csv` 出力確認 | 高 | - |
| `act-2026-04-16-002` | `xbrl.py` に `_PROMOTER_NATURAL_PERSON_SUBS` / `_PROMOTER_GOVT_SUBS` / `is_owner_company()` を追加する Issue 起票 | 中 | - |
| `act-2026-04-16-003` | サンプル銘柄（RELIANCE/INFY/TCS/BAJFINANCE/ASIANPAINT）の shareholder_name レベル検証。holding company 経由型の人名結合ロジック導入可否判断 | 中 | - |
| `act-2026-04-16-004` | `research/2026-04-16_nse_promoter_classification/` を commit、`analyst/` にリンク追加 | 中 | - |
| `act-2026-04-16-005` | `owner_companies.csv` をアナリスト Y チームのスクリーニング済みユニバース（300-400 銘柄）と統合 | 低 | - |

## 次回の議論トピック

- オーナー企業 CSV の実データ確認後、アナリスト Y チームのスクリーニング条件（財務・流動性）とマージして ASEAN 対応版ユニバースに発展させるか
- Holding company 経由型の精緻化（shareholder_name テキストマッチで家族名を検出）
- xbrl.py への関数化 Issue の粒度決定（PR サイズ、テスト範囲）

## 参考情報

### 1 次情報 URL（verbatim 取得済み）

- SEBI ICDR 2009: https://www.sebi.gov.in/acts/icdrreg.html
- SEBI ICDR 2018 (2025-03-08 改訂版): https://www.sebi.gov.in/legal/regulations/mar-2025/securities-and-exchange-board-of-india-issue-of-capital-and-disclosure-requirements-regulations-2018-last-amended-on-march-8-2025-_93559.html
- SEBI SAST 2011 Gazette: https://www.sebi.gov.in/sebi_data/attachdocs/1367922725672.pdf
- SEBI LODR 2015 Gazette: https://www.sebi.gov.in/sebi_data/attachdocs/1441284401427.pdf
- Companies Act 2013: https://www.indiacode.nic.in/bitstream/123456789/2114/5/A2013-18.pdf
- BSE XBRL SHP Taxonomy ZIP: https://www.bseindia.com/downloads1/SHPTaxonomy.zip
- NSE SHP Template PDF: https://nsearchives.nseindia.com/web/sites/default/files/inline-files/Shareholding_Pattern_UR_31%2030062021.pdf

### 成果物

- `research/2026-04-16_nse_promoter_classification/research.md` — 391 行の 1 次情報ベース調査レポート
- `research/2026-04-16_nse_promoter_classification/sources/` — BSE XBRL taxonomy ZIP、LODR/SAST Gazette PDF、Companies Act PDF 等の verbatim コピー
- `notebook/NSE/nse_owner_company_filter.ipynb` — pandas オーナー企業スクリーナー（17 セル）

### 未解決事項（research.md §7.2）

- **ICDR 2018 の条項番号 (oo)/(pp)/(l) verbatim**: SEBI HTML が PDF 直リンクを返さず、番号は検索結果スニペットレベル。ワーディングは ICDR 2009 と同一なので実用上問題なし
- **Companies Rules 2014 Rule 4 の relative 8 項リスト**: MCA / India Code が 403。ICDR の immediate relative（4 項）で Table II A(1)(a) 判定には十分
- **SEBI Circular SEBI/HO/CFD/CMD/CIR/P/2017/128 原 PDF**: 後続 circular の引用のみ確認。代替として 2021-06 NSE archives PDF + 2022-06 circular を採用

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-04-16-nse-owner-company-filter`
  - Decision × 6: `dec-2026-04-16-001` 〜 `dec-2026-04-16-006`
  - ActionItem × 5: `act-2026-04-16-001` 〜 `act-2026-04-16-005`
  - リレーション: `Project:project-106 -HAS_DISCUSSION-> Discussion`, `Discussion -FOLLOWS_UP-> disc-2026-04-14-nse-phase4-completion`, `Discussion -RESULTED_IN-> Decision`, `Discussion -PRODUCED-> ActionItem`
- **ドキュメント**: `docs/plan/2026-04-16_discussion-nse-owner-company-filter.md`
