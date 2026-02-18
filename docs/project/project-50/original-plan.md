# Simple AI Investment Strategy PoC - 実装プラン

## Context

会社の投資チームが選定した投資ユニバース（LIST銘柄、MSCI Kokusai / ACWI ex Japan ベース、約300銘柄）から、AIが競争優位性をベースにポートフォリオを作成するPoC。既存の ca-eval ワークフロー（KB1/KB2/KB3 + dogma.md）を流用し、決算トランスクリプトを入力として300銘柄に対してスケールさせる。

**既存MAS設計（12エージェント・ディベート形式）との差異**: 本PoCは競争優位性のみに特化した「Simple版」。ファンダメンタル/バリュエーション/センチメント/マクロは対象外。

**初期PoCのスコープ**: バックテストは行わず、2015年Q3時点の初期ポートフォリオ構築+判断根拠の出力をゴールとする。

---

## アーキテクチャ全体像

```
Phase 0: KB整備（1回のみ、手動+LLM支援）
  KB1(8ルール)+KB2(12パターン)+KB3(5 few-shot)+dogma.md
    → トランスクリプト分析向けに一般化
    → KB1-T, KB2-T, KB3-T を生成

Phase 1: トランスクリプトから競争優位性を抽出（LLM、各銘柄×各期）
  入力: 決算トランスクリプト(2015 Q1-Q3)
       + SEC 10-K(2014) / 10-Q(2015 Q1-Q3) 補助情報
       + KB参照
  出力: claims.json（5-15件の競争優位性/銘柄）

Phase 2: KB1/KB2/KB3でスコアリング（LLM、各銘柄×各期）
  入力: claims.json + KB1-T + KB2-T + KB3-T + dogma.md
  出力: scored_claims.json（各競争優位性に確信度10-90%）
       → 銘柄スコア（加重集約）

Phase 3: セクター中立化（Python純粋計算）
  入力: scores.json + GICSセクター情報
  処理: セクター内Z-score正規化 → ランク付け
  出力: ranked.json

Phase 4: ポートフォリオ構築（Python純粋計算）
  入力: ranked.json + ベンチマークセクターウェイト
  処理: セクター配分=ベンチマーク、セクター内ウェイト=スコア比例
  出力: portfolio.json（30-50銘柄）

Phase 5: 出力生成（Python）
  入力: portfolio.json + scored_claims.json + claims.json
  出力: portfolio_weights.json/.csv + portfolio_summary.md
       + rationale/{TICKER}_rationale.md（個別銘柄）
```

---

## 確定済み要件

| 項目 | 内容 |
|------|------|
| ユニバース | MSCI Kokusai / ACWI ex Japan ベース、約300銘柄 |
| 分析期間 | 2014 10-K + 2015 Q1-Q3（トランスクリプト+10-Q） |
| カットオフ日 | 2015-09-30（Q3決算発表後） |
| トランスクリプト | S&P Capital IQ JSON（`data/Transcript/`に配置済み、24ファイル: 2014-01〜2015-12） |
| フレームワーク | 独自フレームワーク（7 Powersは参考程度、KB1/KB2/KB3+dogma.mdが主要判断基準） |
| スコアリング | ca-eval方式流用（確信度10-90%）、銘柄スコアは構造的優位性加重平均 |
| ウェイト | セクター配分=ベンチマーク、セクター内=スコア比例 |
| 出力物 | ウェイトリスト + 個別銘柄判断根拠 + ポートフォリオ構築根拠 |
| コスト管理 | サンプル検証（5銘柄）後にフル実行を判断 |

---

## Phase 0: KB整備とトランスクリプト設計

### KB一般化
KB1-3はアナリストレポート分析用に作られている。トランスクリプト用に適応する。

- **KB1-T**: ルール12（期初/四半期区別）を年次/四半期トランスクリプトの文脈に読み替え。他ルール(1-11)はCEO/CFO発言パターンの具体例を追加
- **KB2-T**: 却下パターンA-Gに経営陣発言のパターン例追加（例: パターンA→CEOが「シェアが成長した」=結果を原因とする）
- **KB3-T**: 既存5銘柄(ORLY, COST, LLY, CHD, MNST)のトランスクリプトでfew-shotを作成

### トランスクリプトデータソース

**ソースファイル**: S&P Capital IQ Transcripts（社内提供）
**保存場所**: `data/Transcript/`
**ファイル命名**: `list_transcript_YYYY-MM.json`（トランスクリプト公表年月）
**提供期間**: 2014-01 〜 2015-12（24ファイル、全期間配置済み）

#### ソースデータ構造

```json
{
  "SEDOL": [
    {
      "COMPANYID": 375780.0,
      "COMPANYNAME": "Diageo plc",
      "ISOCOUNTRY2": "GB",
      "IDENTIFIERSTARTDATE": "1980-01-02T00:00:00.000",
      "IDENTIFIERENDDATE": null,
      "ACTIVEFLAG": 1,
      "SECURITYID": 20065797.0,
      "TRADINGITEMID": 243099454.0,
      "EXCHANGEID": 812.0,
      "PRIMARYFLAG": 0,
      "EXCHANGENAME": "Societe Generale",
      "exchangeCountry": 71.0,
      "calendar_year": 2015,
      "calendar_month": 1,
      "year_month": "2015-01-01T00:00:00.000",
      "year_month_label": "2015-01",
      "KEYDEVID": 283092193,
      "eventDate": "2015-01-29T09:30:00.000",
      "eventDateOnly": null,
      "eventHeadline": "Diageo plc, H1 2015 Earnings Call, Jan 29, 2015",
      "eventType": "Earnings Calls",
      "KEYDEVEVENTTYPEID": 48.0,
      "event_link_effective_date": "2018-08-12T01:00:02.000",
      "event_effective_date": "2018-08-12T01:00:02.000",
      "is_current_event_link": 1,
      "is_current_event": 1,
      "TRANSCRIPTID": 785124,
      "TRANSCRIPTCOLLECTIONTYPEID": 8.0,
      "transcript_language_code": "EN",
      "TRANSCRIPTCOLLECTIONTYPENAME": "Audited Copy",
      "has_transcript": 1,
      "is_japanese": 0,
      "is_english": 1,
      "transcript_text1": "...(導入部分、無視)",
      "transcript_text2": "【プレゼン: Name (Role)】...(プレゼン本体、タグ付き)",
      "transcript_text3": "...(Q&A、タグなし生テキスト)",
      "transcript_text4": "【質問: Name (Analysts)】...【回答: Name (Executives)】...(Q&A、タグ付き)",
      "total_component_count": 54,
      "total_characters": 38174.0,
      "first_component_order": 0,
      "last_component_order": 66,
      "Bloomberg_Ticker": "DGE LN Equity",
      "FIGI": "BBG000BS69D5"
    }
  ]
}
```

#### テキストフィールドの使い分け

| フィールド | 内容 | 使用 |
|-----------|------|------|
| `transcript_text1` | 決算コール導入部分（ナビゲーション等） | **無視** |
| `transcript_text2` | プレゼンテーション本体（タグ付き: `【プレゼン: Name (Role)】`）。最大104K文字 | **使用** |
| `transcript_text3` | Q&Aセクション（タグなし生テキスト） | 無視（text4を使用） |
| `transcript_text4` | Q&Aセクション（タグ付き: `【質問:】【回答:】`）。最大73K文字 | **使用** |
| `total_characters` | フルテキストの推定文字数（38K〜91K） | メタデータ記録用 |

**注意**: `All` フィールドは新データには存在しない。

#### タグ構造

```
【プレゼン: Tim Cook (Executives)】  → prepared_remarks セクション
【質問: Brian Pitz (Analysts)】      → qa.question セクション
【回答: Thomas Szkutak (Executives)】 → qa.answer セクション
```

セクション間は `---` で区切られる。

#### 32767文字トランケーション問題

> **✅ ステータス: 解消済み**
> 再提供されたデータ（`data/Transcript/`）では32767文字の上限が撤廃されている。text4は最大73,703文字、text2は最大171,673文字まで格納されており、`text4 == 32767` のレコードは0件。

初回サンプルと再提供データの比較:

| 項目 | 初回サンプル (2015-01) | 再提供データ (2015-01) |
|------|----------------------|----------------------|
| text4最大長 | 32,767（上限張り付き） | 73,703 |
| text4==32767件数 | 12/40 (30%) | 0/125 (0%) |
| text2最大長 | ~33,500 | 66,372 |
| `All` フィールド | あり（~33,500上限） | **なし（削除済み）** |

**ただし**: text4が `null` のレコードが約1.8%存在（Q&Aセッションがないケース: Pre Recorded Callsや一部企業）。text2のみで分析を行う。

#### 銘柄識別子

**主キー**: Bloomberg Ticker → シンプルティッカー変換

変換ルール: `"AAPL US Equity"` → `"AAPL"`（スペース分割の第1要素）

**非標準ティッカーの取り扱い**:

全24ファイルで27件の非標準ティッカー（数字始まり or 短いティッカー）を検出:

| Bloomberg Ticker | シンプル | 企業名 | 備考 |
|-----------------|---------|--------|------|
| `1715651D US Equity` | `1715651D` | EIDP, Inc. (DuPont) | 歴史的ティッカー |
| `1541931D US Equity` | `1541931D` | Altera Corporation | Intel買収済み(2015) |
| `2258717D US Equity` | `2258717D` | Dell EMC | Dell統合済み(2016) |
| `2326248D US Equity` | `2326248D` | CA, Inc. | Broadcom買収済み(2018) |
| `990315D US Equity` | `990315D` | Core Laboratories Inc. | ティッカー変更 |
| `1373183D US Equity` | `1373183D` | Broadcom Inc. | 旧Avago |
| `1482276D US Equity` | `1482276D` | FMC Technologies, Inc. | TechnipFMC統合 |
| `1702253D US Equity` | `1702253D` | WTW Delaware Holdings, LLC | Willis Towers Watson |
| `1844030D NA Equity` | `1844030D` | Unilever PLC | NA市場版 |
| `1856613D US Equity` | `1856613D` | Monsanto Company | Bayer買収済み(2018) |
| `1897377D US Equity` | `1897377D` | Sprint LLC | T-Mobile統合(2020) |
| `1922150D US Equity` | `1922150D` | Linde plc | Praxair統合 |
| `2273854Q LI Equity` | `2273854Q` | Dassault Systèmes SE | 欧州市場 |
| `2599840D US Equity` | `2599840D` | Booking Holdings Inc. | 旧Priceline |
| `9210611D US Equity` | `9210611D` | Sirius XM Holdings Inc. | 再編 |
| `9876641D US Equity` | `9876641D` | Coca-Cola Europacific Partners PLC | 再編 |
| `9983490D US Equity` | `9983490D` | TE Connectivity plc | 再編 |
| `9991429D US Equity` | `9991429D` | Aptiv PLC | 旧Delphi |
| `9993232D US Equity` | `9993232D` | Seagate Technology Holdings plc | 再編 |
| `9999945D US Equity` | `9999945D` | The Cigna Group | 再編 |
| `005935 KS Equity` | `005935` | Samsung Electronics Co., Ltd. | 韓国市場 |
| `035420 KS Equity` | `035420` | NAVER Corporation | 韓国市場 |
| `11 HK Equity` | `11` | Hang Seng Bank Limited | 香港市場 |
| `2330 TT Equity` | `2330` | Taiwan Semiconductor Manufacturing | 台湾市場 |
| `2454 TT Equity` | `2454` | MediaTek Inc. | 台湾市場 |
| `388 HK Equity` | `388` | Hong Kong Exchanges and Clearing | 香港市場 |
| `688 HK Equity` | `688` | China Overseas Land & Investment | 香港市場 |

**Bloomberg Ticker欠損ケース**（約1%）: SBA Communications、Rite Aid、TC Energy、InterContinental Hotels等。`COMPANYNAME` + SEDOLでフォールバック。

非標準ティッカー（数字始まり/`D`/`Q`サフィックス/短い数字）は `COMPANYNAME` をフォールバック識別子として使用し、`ticker_mapping.json` でマッピングを管理する。

#### 重複処理

- **デデュプキー**: `TRANSCRIPTID`
- 同一SEDOLで異なるTRANSCRIPTID → 別トランスクリプトとして保持（例: 通常 + Pre Recorded）
- 異なるSEDOLで同一TRANSCRIPTID → 最初のレコードを採用（取引所違いの重複）
  - 例: 2015-07月で4件の重複あり（同一トランスクリプトが複数SEDOLに紐づく）
- **`PRIMARYFLAG` フィルタリング**: 同一企業の取引所違いレコードは `PRIMARYFLAG=1` を優先

#### データ規模

**全体統計（24ファイル: 2014-01 〜 2015-12）**:

| 項目 | 値 |
|------|-----|
| ファイル数 | 24（2014-01〜2015-12） |
| ユニークSEDOL数（全ファイル合計） | 347 |
| 全レコード数 | 2,556 |
| 非英語レコード | 11件（スキップ対象） |
| text4が空のレコード | 約1.8%（text2のみで分析） |
| Bloomberg Ticker欠損レコード | 約1%（SEDOLとCOMPANYNAMEでフォールバック） |
| eventType | `Earnings Calls`, `Guidance/Update Calls`, `Operating Results Calls` |
| TRANSCRIPTID重複 | 月あたり数件（異なるSEDOLで同一TID → 取引所違い） |
| 合計ファイルサイズ | 約260MB |

**月別レコード数（抜粋）**:

| 月 | SEDOL数 | レコード数 | text4>32K率 | text4最大長 |
|----|---------|-----------|-------------|-------------|
| 2014-01 | 130 | 134 | 53% | 69,290 |
| 2014-07 | 213 | 217 | 55% | 64,716 |
| 2015-01 | 122 | 125 | 48% | 73,703 |
| 2015-04 | 178 | 181 | 44% | 60,973 |
| 2015-07 | 217 | 223 | 48% | 65,366 |
| 2015-10 | 181 | 185 | 51% | 61,665 |

**注意**: 月ごとのSEDOL数にばらつきがある（15〜217）。これは決算発表月の偏りによるもの（1月・4月・7月・10月が多い = 四半期決算集中月）。

### 内部トランスクリプトフォーマット（パース後）

ソースデータを以下の正規化フォーマットに変換して使用する:

```json
{
  "ticker": "AAPL",
  "sedol": "2046251",
  "bloomberg_ticker": "AAPL US Equity",
  "figi": "BBG000B9XRY4",
  "company_name": "Apple Inc.",
  "country": "US",
  "event_date": "2015-01-27",
  "event_headline": "Apple Inc., Q1 2015 Earnings Call, Jan 27, 2015",
  "transcript_id": 784530,
  "transcript_type": "Audited Copy",
  "sections": [
    {
      "type": "prepared_remarks",
      "speaker": "Tim Cook",
      "role": "Executives",
      "content": "..."
    },
    {
      "type": "qa_question",
      "speaker": "Brian Pitz",
      "role": "Analysts",
      "content": "..."
    },
    {
      "type": "qa_answer",
      "speaker": "Thomas Szkutak",
      "role": "Executives",
      "content": "..."
    }
  ],
  "metadata": {
    "source": "sp_capital_iq",
    "source_file": "list_transcript_2015-01.json",
    "total_characters": 32312,
    "total_components": 54,
    "text2_length": 9090,
    "text4_length": 24790,
    "missing_sections": [],
    "word_count": 5500,
    "event_type": "Earnings Calls",
    "primary_flag": 1
  }
}
```

保存場所: `research/ca_strategy_poc/transcripts/{TICKER}/{YYYYMM}_earnings_call.json`

### 成果物
- `analyst/transcript_eval/kb1_rules_transcript/` (8ファイル)
- `analyst/transcript_eval/kb2_patterns_transcript/` (12ファイル)
- `analyst/transcript_eval/kb3_fewshot_transcript/` (5ファイル)
- `analyst/transcript_eval/system_prompt_transcript.md`
- `research/ca_strategy_poc/config/ticker_mapping.json`（非標準ティッカーマッピング）

---

## Phase 1-2: 抽出とスコアリング

### 設計判断: Phase 1とPhase 2は分離

理由:
1. Phase 1出力を人間がレビュー可能にする品質確認ポイント
2. KB調整時にPhase 2のみ再実行できるキャッシュ効率
3. 300銘柄×3四半期のスケールでは中間結果のデバッグが重要

### 使用データ（PoiT: 2015-09-30）

| データソース | 期間 | 形式 | 用途 |
|-------------|------|------|------|
| 決算トランスクリプト | 2014-01 〜 2015-12（24ファイル、`data/Transcript/`） | S&P Capital IQ JSON (`list_transcript_YYYY-MM.json`) | 競争優位性の主張抽出（Phase 1 主入力） |
| SEC 10-K | 2014年度 | SEC EDGAR | 事業概要・リスク要因・競争環境の裏付け |
| SEC 10-Q | 2015 Q1, Q2, Q3 | SEC EDGAR | 四半期業績・経営分析の裏付け |

**トランスクリプトの四半期マッピング**: ファイル名の年月 (`list_transcript_2015-01.json`) はトランスクリプト公表月。`eventHeadline` から決算四半期（Q4 2014, Q1 2015 等）を抽出し、2015年Q1-Q3の決算をフィルタリングする。

### Phase 1 出力: claims.json

各銘柄から5-15件の競争優位性を抽出。各claimに `claim_type`（competitive_advantage / cagr_connection / factual_claim）と初期アセスメントを付与。

### Phase 2 スコアリング: ca-eval方式

1. ゲートキーパー: ルール9(事実誤認→10)、ルール3(業界共通→30以下)
2. 定義チェック: ルール1(能力≠結果), 2(名詞属性), 6(構造的vs補完的), 8(戦略≠優位性)
3. 裏付けチェック: ルール4(定量), 7(純粋競合), 10(ネガティブケース), 11(業界構造)
4. CAGR接続: ルール5(直接メカニズム), 12(年次主/四半期従)
5. KB2パターン照合: 却下A-G(-10~-30%), 高評価I-V(+10~+30%)
6. KB3キャリブレーション: 90%=6%, 70%=26%, 50%=35%, 30%=26%, 10%=6%

### 銘柄スコア集約

構造的優位性加重平均:
- 通常の競争優位性: weight=1.0
- 構造的優位性(ルール6): weight=1.5
- 業界構造合致(ルール11): weight=2.0
- CAGR接続品質によるブースト: ±10%

### PoiT管理

- `cutoff_date = 2015-09-30`
- `cutoff_date` 以前のトランスクリプトのみ使用（`earnings_date`でフィルタ）
- LLMプロンプトに「現在の日付は{cutoff_date}です」を注入
- SEC Filingsは`filing_date`でフィルタ

---

## Phase 3-4: セクター中立化 & ポートフォリオ構築

### Phase 3: セクター中立化

既存 `Normalizer.normalize_by_group()` (`src/factor/core/normalizer.py`) を直接使用。

```python
normalizer.normalize_by_group(
    data=scores_df,
    value_column="aggregate_score",
    group_columns=["as_of_date", "gics_sector"],
    method="zscore", robust=True
)
```

### Phase 4: ポートフォリオ構築

1. 各セクターから選ぶ銘柄数 = `target_portfolio_size` × `benchmark_sector_weight`
2. セクター内ではスコア上位N銘柄を選択
3. セクター内ウェイト = スコア比例配分
4. 既存 `Portfolio` クラス (`src/strategy/portfolio.py`) を使用

---

## Phase 5: 出力生成

### 出力ファイル一覧

| ファイル | 形式 | 内容 |
|---------|------|------|
| `portfolio_weights.json` | JSON | 銘柄ウェイト・スコア・セクター配分の構造化データ |
| `portfolio_weights.csv` | CSV | 同上（Excel等での閲覧・共有用） |
| `portfolio_summary.md` | Markdown | ポートフォリオ全体の構築根拠 |
| `rationale/{TICKER}_rationale.md` | Markdown | 個別銘柄の判断根拠（選定銘柄のみ） |

### portfolio_weights.json

```json
{
  "as_of_date": "2015-10-01",
  "cutoff_date": "2015-09-30",
  "data_sources": {
    "transcripts": ["2015Q1", "2015Q2", "2015Q3"],
    "sec_annual": ["2014_10K"],
    "sec_quarterly": ["2015Q1_10Q", "2015Q2_10Q", "2015Q3_10Q"]
  },
  "total_holdings": 35,
  "holdings": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc.",
      "gics_sector": "Information Technology",
      "weight": 0.042,
      "aggregate_score": 72.5,
      "sector_zscore": 1.85,
      "sector_rank": 1,
      "num_claims": 12,
      "top_claim": "エコシステムロックイン効果"
    }
  ],
  "sector_allocation": [
    {
      "sector": "Information Technology",
      "portfolio_weight": 0.22,
      "benchmark_weight": 0.22,
      "num_holdings": 8,
      "universe_count": 38
    }
  ]
}
```

### portfolio_weights.csv

```
ticker,company_name,gics_sector,weight,aggregate_score,sector_zscore,sector_rank
AAPL,Apple Inc.,Information Technology,0.042,72.5,1.85,1
MSFT,Microsoft Corp.,Information Technology,0.038,68.2,1.52,2
...
```

### portfolio_summary.md

```markdown
# ポートフォリオ構築根拠

## 基本情報
- 構築日: 2015-10-01
- カットオフ: 2015-09-30
- 保有銘柄数: 35 / ユニバース300

## データソース
- 決算トランスクリプト: 2015 Q1-Q3（3四半期×300銘柄）
- SEC 10-K: 2014年度
- SEC 10-Q: 2015 Q1-Q3

## セクター配分
| セクター | BM Weight | PF Weight | 銘柄数 | 上位銘柄 |
|----------|-----------|-----------|--------|----------|
| IT       | 22%       | 22%       | 8      | AAPL, MSFT, ... |
| ...      | ...       | ...       | ...    | ... |

## 銘柄選定基準
- セクター内Z-score上位N銘柄を選択
- 構造的優位性（ルール6）を1.5倍加重
- 業界構造合致（ルール11）を2.0倍加重

## スコア分布
- 全体平均: XX、標準偏差: XX
- 選定銘柄平均: XX、標準偏差: XX
- 上位10銘柄集中度: XX%
```

### rationale/{TICKER}_rationale.md

```markdown
# AAPL - Apple Inc. 判断根拠

## サマリー
- 銘柄スコア: 72.5 / 100
- セクター内ランク: 1位 / 38銘柄（Information Technology）
- セクター内Z-score: 1.85
- ポートフォリオウェイト: 4.2%

## 競争優位性の評価

### CA-1: エコシステムロックイン効果 (確信度: 75%)
- **根拠**: 2015Q2トランスクリプトでCook CEOが「iPhoneユーザーの98%が
  次もiPhoneを購入する意向」と言及
- **KB1適用**: ルール6(構造的優位性) → weight=1.5
- **KB2照合**: パターンI(スイッチングコスト実証) → +15%
- **SEC裏付け**: 2014 10-K Item 7でサービス売上CAGR 12%を確認

### CA-2: ブランドプレミアム (確信度: 50%)
- **根拠**: 2015Q1トランスクリプトでCFOが「ASP維持」に言及
- **KB1適用**: ルール1注意(能力≠結果、定量裏付け不十分)
- **KB2照合**: パターンB(一般的主張) → -10%

## SEC Filings 補助情報
- **2014 10-K**: Item 1(事業概要), Item 7(MD&A)から抽出した要点
- **2015 Q2 10-Q**: 四半期業績トレンド

## CAGR接続品質: B+ (ブースト+5%)
- iPhone売上→サービス売上の接続メカニズムが明確
```

---

## 新規実装コンポーネント

### Python (`src/dev/ca_strategy/` 新規パッケージ)

| コンポーネント | ファイル | 概要 | 優先度 |
|---------------|---------|------|--------|
| 型定義 | `types.py` | Pydanticモデル（transcript, claims, scores, portfolio, rationale） | P0 |
| バッチ処理 | `batch.py` | チェックポイント付きバッチ処理・並列処理・リトライ | P0 |
| **トランスクリプトパーサー** | **`transcript_parser.py`** | **S&P Capital IQ JSON → 内部フォーマット変換（タグパース、デデュプ、ティッカー変換）** | **P0** |
| トランスクリプトローダー | `transcript.py` | パース済みJSON読み込み・バリデーション・PoiTフィルタリング | P1 |
| 抽出器 | `extractor.py` | Phase 1 LLM呼び出し（バッチ処理） | P2 |
| スコアラー | `scorer.py` | Phase 2 LLM呼び出し（バッチ処理） | P2 |
| スコア集約 | `aggregator.py` | 銘柄スコア集約ロジック（構造的優位性加重平均） | P2 |
| セクター中立化 | `neutralizer.py` | Phase 3（Normalizerラッパー） | P2 |
| ポートフォリオ構築 | `portfolio_builder.py` | Phase 4（セクター配分・ウェイト計算） | P2 |
| 出力生成 | `output.py` | Phase 5: ウェイトリスト+根拠ファイル生成 | P2 |
| オーケストレーター | `orchestrator.py` | 全フェーズ統合・チェックポイント再開 | P3 |

### transcript_parser.py の詳細設計

S&P Capital IQ の `list_transcript_YYYY-MM.json` を内部フォーマットに変換するパーサー。

**入力**: `data/Transcript/list_transcript_YYYY-MM.json`
**出力**: `research/ca_strategy_poc/transcripts/{TICKER}/{YYYYMM}_earnings_call.json`

#### 処理フロー

```
1. JSONロード（トレーリングカンマ修正）
2. SEDOLループ → レコードループ
3. フィルタリング
   - is_english != 1 → スキップ
   - has_transcript != 1 → スキップ
4. TRANSCRIPTIDデデュプ
   - 異なるSEDOLで同一TRANSCRIPTID → PRIMARYFLAG=1を優先
5. Bloomberg Ticker → シンプルティッカー変換
   - "AAPL US Equity" → "AAPL"
   - 非標準ティッカー（数字始まり/短い数字）→ ticker_mapping.json で解決
   - Bloomberg Ticker欠損 → SEDOL + COMPANYNAME でフォールバック
6. text2パース（プレゼンセクション）
   - 【プレゼン: Name (Role)】 タグを正規表現で分割
   - 各セクションの speaker / role / content を抽出
7. text4パース（Q&Aセクション）
   - text4がnullの場合 → metadata.missing_sections = ["qa"]
   - 【質問: Name (Analysts)】【回答: Name (Executives)】 タグを分割
   - --- 区切りで質問・回答ペアを構成
8. 内部フォーマットJSON出力
```

#### タグパース正規表現

```python
TAG_PATTERN = re.compile(r'【(プレゼン|質問|回答): (.+?) \((.+?)\)】')
# group(1): type (プレゼン/質問/回答)
# group(2): speaker name
# group(3): role (Executives/Analysts)
```

#### 非標準ティッカーマッピング（`ticker_mapping.json`）

```json
{
  "1715651D": {"ticker": "DD", "company_name": "EIDP, Inc.", "note": "DuPont歴史的ティッカー"},
  "1541931D": {"ticker": "ALTR", "company_name": "Altera Corporation", "note": "Intel買収済み(2015)"},
  "2258717D": {"ticker": "EMC", "company_name": "Dell EMC", "note": "Dell統合済み(2016)"},
  "2326248D": {"ticker": "CA", "company_name": "CA, Inc.", "note": "Broadcom買収済み(2018)"},
  "990315D": {"ticker": "CLB", "company_name": "Core Laboratories Inc.", "note": "ティッカー変更"},
  "1373183D": {"ticker": "AVGO", "company_name": "Broadcom Inc.", "note": "旧Avago Technologies"},
  "1482276D": {"ticker": "FTI", "company_name": "FMC Technologies, Inc.", "note": "TechnipFMC統合"},
  "1702253D": {"ticker": "WLTW", "company_name": "WTW Delaware Holdings, LLC", "note": "Willis Towers Watson"},
  "1844030D": {"ticker": "UL", "company_name": "Unilever PLC", "note": "NA市場版"},
  "1856613D": {"ticker": "MON", "company_name": "Monsanto Company", "note": "Bayer買収済み(2018)"},
  "1897377D": {"ticker": "S", "company_name": "Sprint LLC", "note": "T-Mobile統合(2020)"},
  "1922150D": {"ticker": "LIN", "company_name": "Linde plc", "note": "Praxair統合"},
  "2273854Q": {"ticker": "DSY", "company_name": "Dassault Systèmes SE", "note": "欧州市場"},
  "2599840D": {"ticker": "BKNG", "company_name": "Booking Holdings Inc.", "note": "旧Priceline"},
  "9210611D": {"ticker": "SIRI", "company_name": "Sirius XM Holdings Inc.", "note": "再編"},
  "9876641D": {"ticker": "CCEP", "company_name": "Coca-Cola Europacific Partners PLC", "note": "再編"},
  "9983490D": {"ticker": "TEL", "company_name": "TE Connectivity plc", "note": "再編"},
  "9991429D": {"ticker": "APTV", "company_name": "Aptiv PLC", "note": "旧Delphi"},
  "9993232D": {"ticker": "STX", "company_name": "Seagate Technology Holdings plc", "note": "再編"},
  "9999945D": {"ticker": "CI", "company_name": "The Cigna Group", "note": "再編"},
  "005935": {"ticker": "005930.KS", "company_name": "Samsung Electronics Co., Ltd.", "note": "韓国市場"},
  "035420": {"ticker": "035420.KS", "company_name": "NAVER Corporation", "note": "韓国市場"},
  "11": {"ticker": "0011.HK", "company_name": "Hang Seng Bank Limited", "note": "香港市場"},
  "2330": {"ticker": "2330.TW", "company_name": "Taiwan Semiconductor Manufacturing", "note": "台湾市場"},
  "2454": {"ticker": "2454.TW", "company_name": "MediaTek Inc.", "note": "台湾市場"},
  "388": {"ticker": "0388.HK", "company_name": "Hong Kong Exchanges and Clearing", "note": "香港市場"},
  "688": {"ticker": "0688.HK", "company_name": "China Overseas Land & Investment", "note": "香港市場"}
}
```

#### エッジケース処理

| ケース | 対処 |
|--------|------|
| トレーリングカンマのあるJSON | `re.sub(r',(\s*[}\]])', r'\1', content)` で修正 |
| text4がnull | `metadata.missing_sections = ["qa"]` を記録、text2のみで分析（約1.8%） |
| 非標準ティッカー（数字始まり/短い数字） | `ticker_mapping.json` でマッピング（27件確認済み）、未登録なら `COMPANYNAME` でログ出力 |
| Bloomberg Ticker欠損 | SEDOLをキーとして使用、`COMPANYNAME` でフォールバック識別（約1%） |
| FIGI欠損 | ティッカー解決には影響なし（約2.7%） |
| text2/text4が空またはnull | 空セクションとして記録、`metadata.missing_sections` に記録 |
| 異なるSEDOLで同一TRANSCRIPTID | `PRIMARYFLAG=1` を優先、なければ最初のレコードを採用 |
| 同一SEDOLで複数レコード | TRANSCRIPTIDが異なれば全て保持（通常+Pre Recorded等） |
| 非英語トランスクリプト | `is_english != 1` のレコードをスキップ（全体で11件） |
| eventType が `Earnings Calls` 以外 | `Guidance/Update Calls`、`Operating Results Calls` も保持（Phase 1で活用判断） |

### エージェント (`.claude/agents/ca-strategy/`)

**ステータス: 未策定。** 名前のみ仮定義、定義ファイルは未作成。

| エージェント | 概要 | ステータス |
|-------------|------|-----------|
| `ca-strategy-lead` | Agent Teams リーダー（全Phase制御） | 未作成 |
| `transcript-claim-extractor` | Phase 1: トランスクリプトからCA抽出 | 未作成 |
| `transcript-claim-scorer` | Phase 2: KB1/KB2/KB3スコアリング | 未作成 |
| `score-aggregator` | 銘柄スコア集約 | 未作成 |
| `sector-neutralizer` | Phase 3: セクター中立化 | 未作成 |
| `portfolio-constructor` | Phase 4: ポートフォリオ構築 | 未作成 |
| `output-generator` | Phase 5: 出力生成 | 未作成 |

エージェント設計の詳細（プロンプト、ツール、入出力、Agent Teams構成）は別途策定が必要。
既存 `ca-claim-extractor` のロジックをベースに、トランスクリプト版に適応する。

---

## 既存コンポーネント再利用

| コンポーネント | ファイル | 用途 |
|---------------|---------|------|
| `Normalizer` | `src/factor/core/normalizer.py` | Phase 3: セクター内Z-score正規化 |
| `Portfolio` | `src/strategy/portfolio.py` | Phase 4: ポートフォリオ管理 |
| `EdgarFetcher` | `src/edgar/fetcher.py` | Phase 1: 10-K/10-Q取得 |
| `SectionExtractor` | `src/edgar/extractors/section.py` | Phase 1: Item 1, 7抽出 |
| KB1/KB2/KB3 | `analyst/dify/kb1_rules/` 等 | Phase 0: ベースライン |
| dogma.md | `analyst/Competitive_Advantage/analyst_YK/dogma.md` | 全Phase: 判断軸 |
| ca-claim-extractor | `.claude/agents/ca-claim-extractor.md` | Phase 1-2: ロジックのベース |

---

## コスト見積もり

### LLMコスト（Sonnet 4使用時、初期PoC: 300銘柄×3四半期）

| フェーズ | コスト |
|---------|--------|
| Phase 1 (抽出) | ~$15 |
| Phase 2 (スコアリング) | ~$15 |
| **合計** | **~$30** |

### コスト最適化オプション
- **結果キャッシュ**: KB調整後の再実行でPhase 1をスキップ → 50%削減
- **Phase 1+2統合**: 30%削減（デバッグ性と引き換え）

---

## 段階的実行計画

### Step 0: 準備作業
1. ~~トランスクリプトフォーマット確定~~ → **完了**: S&P Capital IQ形式が確定、内部フォーマットも設計済み
2. ~~トランスクリプトデータ配置~~ → **完了**: `data/Transcript/` に24ファイル（2014-01〜2015-12）配置済み。32767文字トランケーション問題も解消済み。
3. `transcript_parser.py` 実装 + 全24ファイルのパース実行
4. `ticker_mapping.json` 作成（非標準ティッカー27件のマッピング確認済み、全ファイルスキャン結果を反映）
5. Pydanticモデル定義（`types.py`）
6. KB3の5銘柄(ORLY, COST, LLY, CHD, MNST)のパース済みトランスクリプトを確認
7. KB1-T/KB2-T/KB3-T作成
8. universe.json作成（300銘柄+GICSセクター+ベンチマークウェイト）
9. エージェント設計・定義ファイル作成

### Step 1: 5銘柄キャリブレーション
1. Phase 1+2を5銘柄（KB3銘柄）で実行
2. KYの既存Phase 2スコア（`analyst/phase2_KY/`）と比較
3. **成功基準**: 確信度スコアがKY評価と平均±10%以内
4. 乖離が大きければKB調整

### Step 2: サンプル検証
1. 各セクターから3銘柄、計30銘柄で2015 Q1-Q3を実行
2. Phase 1→2→3→4→5の全パイプライン検証
3. **成功基準**: パイプライン完走、セクター配分がBMに一致、出力ファイルの品質確認
4. コスト実測→フル実行判断

### Step 3: フル実行
1. 300銘柄のトランスクリプト準備（2015 Q1-Q3）
2. 300銘柄のSEC Filings取得（2014 10-K + 2015 Q1-Q3 10-Q）
3. バッチ実行（50銘柄ずつ、チェックポイント付き）
4. 出力生成 + 投資チームレビュー

---

## 主要リスクと対策

| リスク | 対策 |
|--------|------|
| ~~**トランスクリプト300銘柄の手動準備が困難**~~ | ~~代替案: SEC 10-K Item 7 (MD&A) を擬似トランスクリプトとして自動取得~~ → **解決済み**: S&P Capital IQ のJSON形式でトランスクリプト提供が確定。`transcript_parser.py` で自動パース。 |
| ~~**全テキストフィールドの32767文字トランケーション**~~ | ~~text3/text4が同じ32767上限~~ → **解決済み**: 再提供データでは上限撤廃。text4最大73,703文字、text2最大171,673文字。 |
| **非標準ティッカー（数字始まり）のマッピング** | `ticker_mapping.json` で手動マッピング管理。27銘柄確認済み。新ファイル追加時に未登録ティッカーを検出しログ出力。 |
| **Bloomberg Ticker / FIGI 欠損** | 約1%のレコードでBloomberg Ticker欠損。SEDOLキー + COMPANYNAMEでフォールバック。 |
| **text4がnullのレコード** | 約1.8%。Q&Aセッションなし（Pre Recorded Calls等）。text2のみで分析可能。 |
| **LLMスコアリングの一貫性** | temperature=0、KB3 few-shotキャリブレーション、3回実行の中央値採用 |
| **PoiTバイアス** | cutoff_date=2015-09-30 プロンプト注入 + eventDate/filing_date フィルタ |
| **サバイバーシップバイアス** | PoCでは明示的に注記。将来フェーズでヒストリカルユニバース対応を検討 |
| **KB一般化の品質** | Step 1の5銘柄キャリブレーションで検証 |

---

## パッケージ構造

```
src/dev/
├── __init__.py
└── ca_strategy/
    ├── __init__.py
    ├── py.typed
    ├── types.py              # Pydanticモデル（~350行）
    ├── batch.py              # チェックポイント付きバッチ処理（~200行）
    ├── transcript_parser.py  # S&P Capital IQ → 内部フォーマット変換（~250行）
    ├── transcript.py         # パース済みトランスクリプトローダー（~150行）
    ├── extractor.py          # Phase 1: LLM抽出（~250行）
    ├── scorer.py             # Phase 2: LLMスコアリング（~280行）
    ├── aggregator.py         # 銘柄スコア集約（~150行）
    ├── neutralizer.py        # Phase 3: セクター中立化（~100行）
    ├── portfolio_builder.py  # Phase 4: ポートフォリオ構築（~180行）
    ├── output.py             # Phase 5: 出力生成（~300行）
    └── orchestrator.py       # 全Phase統合（~350行）
```

## ワークスペース構造

```
research/ca_strategy_poc/
├── config/
│   ├── universe.json               # ユニバース（300銘柄+GICSセクター）
│   ├── benchmark_weights.json      # ベンチマークセクターウェイト
│   └── ticker_mapping.json         # 非標準ティッカー→正規ティッカーのマッピング
├── transcripts/                    # パース済みトランスクリプト（transcript_parser.py出力）
│   ├── AAPL/
│   │   ├── 201501_earnings_call.json
│   │   ├── 201504_earnings_call.json
│   │   └── 201507_earnings_call.json
│   ├── AMZN/
│   │   └── ...
│   └── _parse_stats.json           # パース実行の統計情報
├── phase0_kb/
│   ├── kb1_rules_transcript/
│   ├── kb2_patterns_transcript/
│   └── kb3_fewshot_transcript/
├── phase1_claims/{ticker}/{YYYYMM}_claims.json
├── phase2_scores/{ticker}/{YYYYMM}_scored.json
│   └── 20151001_scores.json        # 全銘柄集約
├── phase3_ranked/20151001_ranked.json
├── phase4_portfolio/20151001_portfolio.json
├── output/
│   ├── portfolio_weights.json
│   ├── portfolio_weights.csv
│   ├── portfolio_summary.md
│   └── rationale/
│       ├── AAPL_rationale.md
│       ├── AMZN_rationale.md
│       └── ...
└── execution/
    └── execution_log.json
```

**注意**: ソースデータ (`data/Transcript/`) はリポジトリに含まれるが読み取り専用。`transcript_parser.py` がパースして `research/ca_strategy_poc/transcripts/` に正規化フォーマットで出力する。

---

## 実装 Wave（依存関係順）

| Wave | 名前 | ファイル | 見積 |
|------|------|---------|------|
| 1 | 基盤（型定義・ユーティリティ・パーサー） | `types.py`, `batch.py`, `transcript_parser.py`, `__init__.py`, `py.typed` | 2-3日 |
| 2 | ローダー・集約 | `transcript.py`, `aggregator.py`, `neutralizer.py` | 2日 |
| 3 | LLM処理 | `extractor.py`, `scorer.py` | 3-4日 |
| 4 | ポートフォリオ・出力 | `portfolio_builder.py`, `output.py` | 2-3日 |
| 5 | 統合 | `orchestrator.py` | 2日 |

**Wave 1 の変更点**: `transcript_parser.py` を Wave 1 に追加。パーサーは他のコンポーネントより先に実装する必要がある（パース済みデータがないと Wave 2 以降のテストが書けないため）。24ファイル（2014-01〜2015-12）のパースが必要で、非標準ティッカー27件のマッピングも含む。

---

## 検証方法

1. **Step 1完了時**: 5銘柄のスコアをKY評価と比較（±10%以内）
2. **Step 2完了時**: 30銘柄×3四半期のパイプライン完走確認、出力ファイル品質確認、コスト実測
3. **Step 3完了時**: 全300銘柄のポートフォリオ構築、ウェイトリスト+根拠ファイル出力
4. **最終検証**: 投資チームによる定性レビュー（AIの銘柄選択理由が妥当か、根拠ファイルの説得力）

---

## /plan-project 進捗

| Phase | ステータス | 備考 |
|-------|-----------|------|
| Phase 0: 初期化・方向確認 | 完了 | プランファイルからの実行、`src/dev/ca_strategy/` に配置確定 |
| Phase 1: リサーチ | 完了 | `.tmp/plan-project-ca-strategy-poc/research-findings.json` |
| Phase 2: 計画策定 | 完了 | `.tmp/plan-project-ca-strategy-poc/implementation-plan.json` |
| Phase 3: タスク分解 | 未着手 | 次回再開時に実行 |
| Phase 4: GitHub Project 登録 | 未着手 | Phase 3 完了後に実行 |
