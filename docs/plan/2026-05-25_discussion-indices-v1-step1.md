# 議論メモ: FILING_NLP indices_v1 Step1 (universe_builder) 実行 + SPX DoD 判定

**日付**: 2026-05-25
**議論ID**: disc-2026-05-25-indices-v1-step1
**Project**: quants-filing-nlp-embedding
**前回**: [disc-2026-05-25-indices-v1-pipeline](2026-05-25_discussion-indices-v1-pipeline.md), [disc-2026-05-25-prj114-implementation-completion](2026-05-25_discussion-prj114-implementation-completion.md)

## 背景・コンテキスト

Project #114 (FILING_NLP indices_v1) の本実行に向けた `/project-discuss` セッション。
TODO 一覧確認の結果、`act-2026-05-25-104` (SPX chunks 生成 CLI 起動) を発火する前提として、
依存する **Step1: `universe_builder.py` 実行** (act-101) が未消化であることが判明した。

ユーザー判断「Step1 のみ先に実行」に従い、`universe_builder.py` を 2026-05-22 スナップショットで起動し、
出力の検証と DoD 判定までを本セッションで行った。

## Step1 実行結果

### コマンド

```bash
uv run python -m notebook.FILING_NLP.pipeline.universe_builder \
  --snapshot-date 2026-05-22 \
  --index-dir 'notebook/US Index'
```

- 出力先 (default): `/Volumes/personal_folder/Quants/FILING_NLP_v2/universe/universe_indices_v1.parquet` + `index_membership/membership_indices_v1.parquet`
- 所要時間: **約 22 秒**

### CIK 解決ステージ

| ステージ | 解決 | 残 | 累積率 |
|----------|------|-----|--------|
| Union (4 インデックス, before dedup) | 4,440 ticker | - | - |
| Stage 1: `universe_v2.parquet` 直接 join | 4,339 | 101 | 97.7% |
| Stage 2: `/`→`-` 正規化 + `all_tickers` 突合 | +64 → 4,403 | 37 | 99.2% |
| Stage 3: SEC EDGAR `find_company_by_ticker` | +31 → **4,434** | **6** | **99.86%** |

### 出力サマリー

| ファイル | rows | unique CIK | unique ticker |
|----------|------|------------|---------------|
| `universe_indices_v1.parquet` | 2,889 | 2,889 | 2,889 |
| `membership_indices_v1.parquet` | 2,889 | 2,889 | - |
| `unresolved_tickers.json` | 6 | - | 6 |

### per-index resolved CIK 数

| Index | raw ticker | resolved CIK | カバレッジ |
|-------|-----------|--------------|----------|
| SPX | 503 | **500** | 100% (ticker 解決率) / 99.4% (CIK dedup 後) |
| SOX | 30 | 30 | 100% |
| RIY | 1,001 | 987 | 98.6% |
| RAY | 2,906 | 2,880 | 99.1% |

### SPX GICS セクター分布 (resolved 500 CIK)

| Sector | CIK |
|--------|-----|
| Industrials | 79 |
| Financials | 76 |
| Information Technology | 73 |
| Health Care | 59 |
| Consumer Discretionary | 48 |
| Consumer Staples | 36 |
| Utilities | 31 |
| Real Estate | 31 |
| Materials | 26 |
| Energy | 21 |
| Communication Services | 20 |

11 セクター全網羅、極端な偏りなし。

### unresolved 6 件の詳細

すべて **RAY (Russell 3000)** 由来。SEC EDGAR `find_company_by_ticker` で `Company not found`。

| ticker | similar 候補 | 想定原因 |
|--------|-------------|---------|
| FRX | - | First Republic Bank (2023 倒産) の可能性 |
| FRBA | - | First Bank (NJ) のティッカー変更可能性 |
| HIFS | - | Hingham Institution for Savings (薄商い) |
| KEI | - | 不明 |
| NBN | NBND (NetBrands Corp.) | ティッカー類似だが別社 |
| TOWN | TSQ (Townsquare Media) | ティッカー類似だが別社 |

→ `act-2026-05-25-301` として独立調査タスクを発行。SPX/SOX/RIY は影響なし。

## 議論のサマリー

### 論点: SPX DoD 「503 全件解決」をどう判定するか

dec-2026-05-25-106 では「SPX 503 全件解決を Definition of Done」と規定していたが、
Step1 実測で **CIK dedup 後 500 件**となった。

**原因**: デュアル株式 (Class A/B/C を別ティッカーとして上場) 3 ペア:

| 欠落 ticker (Class A) | 残存 ticker (Class B/C) | 同 CIK | 企業 |
|--------------------|---------------------|--------|------|
| GOOGL | GOOG | 1652044 | Alphabet |
| FOXA | FOX | 1754301 | Fox Corp |
| NWSA | NWS | 1564708 | News Corp |

**判定 (dec-301)**: SEC 10-K/10-Q は CIK 単位で提出されるため、Class A/B 両方保持しても同じ filing を二重 fetch するだけで意味がない。
**「500 unique CIK = SPX 503 銘柄 100% カバレッジ」を DoD 達成と判定**し、Step2 起動可。
今後の DoD 表記は ticker 数ではなく `unique CIK 数 + ticker→CIK 解決率` で表現する。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-25-301 | DoD 判定基準を「ticker→CIK 解決率 + unique CIK 数」に変更し、SPX 500 CIK = 503 ticker 100% カバレッジを DoD 達成と判定 | デュアル株式 3 ペアによる必然的な CIK dedup |

## アクションアイテム

### 新規

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-25-301 | RAY unresolved 6 ticker (FRX/FRBA/HIFS/KEI/NBN/TOWN) の調査。SPX/SOX/RIY を阻害しないため Step2 (SPX) 起動を待たせない | low | pending |

### 完了化 (Step1 実行で消化)

| ID | 内容 | 状態 |
|----|------|------|
| act-2026-05-25-101 | universe_builder.py 実装 + 2026-05-22 スナップショット実行 | **completed** |
| act-2026-05-25-102 | run_indices.py 実装 (PR #3949 マージ済み) | **completed** |
| act-2026-05-25-103 | pipeline_indices_v1.ipynb 作成 (PR #3949 マージ済み) | **completed** |
| act-2026-05-25-105 | embed_indices.py 実装 (PR #3949 マージ済み) | **completed** |

### 未消化 (Step2 以降)

| ID | 内容 | 推定時間 |
|----|------|---------|
| act-2026-05-25-104 / act-204 | SPX chunks 生成 CLI 起動 (`run_indices --index-filter in_spx --workers 8 --rate-rps 5`) | 12-24h |
| act-2026-05-25-106 | SPX embedding CLI 起動 (`embed_indices --batch-size 16 --device mps --dtype bfloat16`) | 9-10h |
| act-2026-05-25-107 | 完走後の品質統計レポート (GICS セクター別) | - |
| act-2026-05-25-201 | Issue #3948 (README 作成, 生存バイアス明示) | - |

## 次回の議論トピック

1. **Step2 起動の決定**: SPX chunks 生成を nohup でいつ起動するか (作業マシン占有時間と整合)
2. **act-301 (RAY unresolved 6 件) の調査**: SPX 完走と並行して進めるか、RAY 着手前まで遅延させるか
3. **PR #3949 LOW 指摘修正 (Issue #3951)**: Step2 実行中の空き時間で対応する選択肢

## 参考情報

- Neo4j Discussion: `disc-2026-05-25-indices-v1-step1`
- 元議論: [disc-2026-05-25-indices-v1-pipeline](2026-05-25_discussion-indices-v1-pipeline.md)
- パイロット結果: [disc-2026-05-25-filing-nlp-v2-pilot-results](2026-05-25_discussion-filing-nlp-v2-pilot-results.md)
- GitHub Project: [#114 FILING_NLP indices_v1 パイプライン構築](https://github.com/users/YH-05/projects/114)
- 関連 Issue: #3948 (README), #3951 (PR #3949 LOW 修正)
- NAS パス: `/Volumes/personal_folder/Quants/FILING_NLP_v2/`
