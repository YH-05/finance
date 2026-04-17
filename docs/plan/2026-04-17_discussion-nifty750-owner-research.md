# 議論メモ: NIFTY 750 オーナー企業比率 Web 調査

**日付**: 2026-04-17
**議論ID**: `disc-2026-04-17-nifty750-owner-research`
**関連プロジェクト**: `project-106: NSE パッケージ拡張 + 全銘柄データ取得ノートブック`
**前回議論**: `disc-2026-04-17-nse-owner-phase34-reconciliation`

## 背景・コンテキスト

NSE オーナー企業分析 (787 銘柄、OWNER 638/OWNER_WEAK 6/NOT_OWNER 143) の完了を受け、母集団である NIFTY 750 (= Nifty Total Market Index) が市場一般論として本当にオーナー企業中心なのかを外部データで確認。アナリスト Y チームのユニバース (300-400 銘柄) 構築の前提確認として実施。

## 議論のサマリー

### 指数別のファミリー/プロモーター比率（Web調査）

| 指数 | ファミリー/オーナー比率 | 備考 |
|------|------------------------|------|
| NIFTY 50 | 60〜66%（33 社前後） | 研究論文ベース |
| BSE 100 | 約 65% | ファミリー経営 |
| NSE 全上場 | 45% がプロモーター持株 60% 超 | FY2025 開示 |
| 歴史的推移 | 50% 超プロモーター企業: 2001 年 56% → 2018 年 66% | 増加傾向 |

### NIFTY 750 の公式統計は未取得

- 750 銘柄は `Nifty 500 + Nifty Microcap 250` で構成、NSE 時価総額の約 96% をカバー
- 指数ファクトシートは **free-float 計算のためプロモーター持株を除外** して計算されており、「プロモーター比率」統計は公式には未公表
- IiAS 等の複数ソースが「**フロントライン指数から離れるほどファミリー支配比率は上がる**」と一致して指摘
- NSE500 全体で private promoters の平均保有比率は 39.6%（2025 年 3 月期、過去最低）だが、FMCG・自動車・小売では創業家支配が依然強い

### 結論: NIFTY 750 は推定 70% 前後がオーナー企業

- 中小型 500 銘柄が含まれる構造上、NIFTY50 の 60〜66% より高い比率になる
- 自前 NSE 分析の OWNER 比率 81.9% (638/787) はこの市場一般論と整合
- 近年は PE/機関投資家保有の上昇でプロモーター比率は微減傾向だが、「大半がオーナー企業」という構造は維持

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-17-013 | NIFTY 750 構成銘柄の約 70% 前後はオーナー/創業家支配企業であるという仮説を採用 | Web 調査ベース。NIFTY50=60-66%、BSE100=65%、中小型株ほどファミリー支配強化、NIFTY 750 は中小型 500 銘柄を含むため平均より高い比率と推定 |
| dec-2026-04-17-014 | 今回の NSE オーナー分析 787 銘柄 (OWNER 81.9%) の結果は、NIFTY 750 ユニバース全体の市場一般論と整合する | Recall 97.7% / Precision 90.2% の分類結果が Web 調査トレンドに沿う。自前分析がマーケットデータと矛盾しないことを確認 |

## アクションアイテム

| ID | 内容 | 優先度 | 期限 |
|----|------|--------|------|
| act-2026-04-17-012 | OECD India Ownership Structure レポート + NSE India Ownership Tracker (2025年6月) 精読、NIFTY 750 セグメント別 (Large/Mid/Small/Micro) のオーナー比率細分化データを取得 | 低 | 2026-05-31 |

## 参照した Web ソース

- [India Ownership Tracker Q1 FY26 (NSE 公式、2025年6月)](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/India%20Ownership%20Report_June%202025.pdf)
- [Juxtaposition of Family Owned Firms in NIFTY (ICTACT 研究論文)](https://ictactjournals.in/paper/IJMS_V6_I3_Paper_3_1258_1262.pdf)
- [India Inc. promoter holdings continue to fall (Business Standard, 2025-05-13)](https://www.business-standard.com/markets/news/india-inc-promoter-holdings-continue-to-fall-but-experts-see-no-red-flags-125051300571_1.html)
- [Ownership Structure of Listed Companies in India (OECD, 2020)](https://www.oecd.org/content/dam/oecd/en/publications/reports/2020/06/ownership-structure-of-listed-companies-in-india_93433d0a/3345d09d-en.pdf)
- [Nifty Total Market Index (NSE 公式ページ)](https://www.niftyindices.com/indices/equity/broad-based-indices/nifty-total-market)
- [Top Founder/Promoter Family Managed Companies in India (Trade Brains)](https://tradebrains.in/promoter-family-managed-companies-india/)

## 次回の議論トピック

- NSE オーナー分析結果を analyst universe (300-400 銘柄) に反映する際の追加フィルタ設計
- NIFTY 750 の Large/Mid/Small/Micro セグメント別オーナー比率の精密検証 (OECD/NSE 公式レポート精読後)
- ASEAN 銘柄カバレッジ (2026-03 開始) でも同様のオーナー企業分析が必要か検討

## 保存先

- **Neo4j**: Discussion `disc-2026-04-17-nifty750-owner-research` + Decision ×2 (013/014) + ActionItem ×1 (012)
- **ドキュメント**: `docs/plan/2026-04-17_discussion-nifty750-owner-research.md`
- **リレーション**: `(discussion)-[:RESULTED_IN]->(decision)`, `(discussion)-[:PRODUCED]->(action)`, `(discussion)-[:FOLLOWS]->(prev)`, `(project)-[:HAS_DISCUSSION]->(discussion)`

## 補足: 誤上書き事故の記録

議論保存時に dec-2026-04-17-005/006 を誤って上書きする事故発生。即座に検知し、morning session (disc-2026-04-17-nse-owner-analysis-impl) のドキュメントから元内容を復元。新規 Decision は 013/014 で採番。

**再発防止**: MERGE 前に必ず既存 ID の存在確認 (read クエリ) を実施する。
