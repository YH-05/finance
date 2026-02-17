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
| トランスクリプト | 手動で用意予定（フォーマット・保存場所は未整備→Phase 0で設計） |
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
**保存場所**: `docs/Multi-Agent-System-for-Investment-Team/data/simple-ai-poc/transcript/`
**ファイル命名**: `list_transcript_YYYY-MM.json`（トランスクリプト公表年月）
**提供期間**: 2015-01 〜 2015-09（10ヶ月分）。今後さらに追加予定。

#### ソースデータ構造

```json
{
  "SEDOL": [
    {
      "COMPANYID": 375780.0,
      "COMPANYNAME": "Diageo plc",
      "ISOCOUNTRY2": "GB",
      "Bloomberg_Ticker": "DGE LN Equity",
      "FIGI": "BBG000BS69D5",
      "SECURITYID": 20065797.0,
      "TRADINGITEMID": 243099454.0,
      "EXCHANGEID": 812.0,
      "EXCHANGENAME": "BATS 'Chi-X Europe'",
      "eventDate": "2015-01-29T09:30:00.000",
      "eventDateOnly": "2015-01-29T00:00:00.000",
      "eventHeadline": "Diageo plc, H1 2015 Earnings Call, Jan 29, 2015",
      "eventType": "Earnings Calls",
      "KEYDEVEVENTTYPEID": 48.0,
      "TRANSCRIPTID": 785124.0,
      "TRANSCRIPTCOLLECTIONTYPEID": 8.0,
      "TRANSCRIPTCOLLECTIONTYPENAME": "Audited Copy",
      "has_transcript": 1.0,
      "is_english": 1.0,
      "transcript_language_code": "EN",
      "transcript_text1": "...(導入部分、無視)",
      "transcript_text2": "【プレゼン: Name (Role)】...(プレゼン本体、タグ付き)",
      "transcript_text3": "...(Q&A、タグなし生テキスト)",
      "transcript_text4": "【質問: Name (Analysts)】...【回答: Name (Executives)】...(Q&A、タグ付き)",
      "total_component_count": 54.0,
      "total_characters": 38174.0,
      "All": "...(text2+text4統合版、~33500文字の独自上限あり、フルテキストには届かない)"
    }
  ]
}
```

#### テキストフィールドの使い分け

| フィールド | 内容 | 使用 |
|-----------|------|------|
| `transcript_text1` | 決算コール導入部分（ナビゲーション等） | **無視** |
| `transcript_text2` | プレゼンテーション本体（タグ付き: `【プレゼン: Name (Role)】`） | **使用** |
| `transcript_text3` | Q&Aセクション（タグなし生テキスト）。**text4と同じ32767上限あり、フォールバック不可** | 無視 |
| `transcript_text4` | Q&Aセクション（タグ付き: `【質問:】【回答:】`）。32767上限あり | **使用** |
| `All` | text2+text4統合版。~33500文字の独自上限あり。text3/text4より若干長いがフルテキストには届かない | 無視 |
| `total_characters` | フルテキストの推定文字数（38K〜91K）。切り詰めなしの参考値 | メタデータ記録用 |

#### タグ構造

```
【プレゼン: Tim Cook (Executives)】  → prepared_remarks セクション
【質問: Brian Pitz (Analysts)】      → qa.question セクション
【回答: Thomas Szkutak (Executives)】 → qa.answer セクション
```

セクション間は `---` で区切られる。

#### 32767文字トランケーション問題

> **⚠️ ステータス: 完全なデータを再提供予定**
> 以下は初回サンプルデータ（2015-01月）の分析結果。全テキストフィールドにS&P Capital IQエクスポート由来の文字数上限（32767 = 2^15 - 1 = Excelセル上限）が存在することが判明。完全なトランスクリプトデータが再提供される予定のため、以下のトランケーション対処方針は暫定。

2015-01月データの分析結果:

| フィールド | 上限 | 切り詰め件数 | 説明 |
|-----------|------|-------------|------|
| text3 | 32767 | 11/40 (27.5%) | Q&A生テキスト。**text4と同じ上限を受けており、フォールバックにならない** |
| text4 | 32767 | 12/40 (30%) | text3にタグを付けたもの。タグ分だけ長くなるため切り詰め件数が1件多い |
| All | ~33500 | 独自上限 | text2+text4の統合版。text3/text4より若干長いがフルテキストには届かない |
| text2 | ~33500 | 0件 | プレゼン本体。最大33505文字。プレゼンは比較的短いため実質的に影響なし |
| total_characters | 制限なし | - | **フルテキストの推定長（38K〜91K文字）。切り詰めなしの参考値** |

**重要な発見**: text3はtext4のタグなし版であり、同じ32767制限を受けている。text3をフォールバックとして使用してもQ&A全文は取得できない。`total_characters` が示す実際のトランスクリプト長（例: JPM 84,976文字）と比較すると、Allフィールドでも38.8%しかカバーできないケースがある。

**対処方針**: 完全なデータが再提供される予定。再提供後にトランケーション状況を再評価し、`transcript_parser.py` の設計を確定する。

#### 銘柄識別子

**主キー**: Bloomberg Ticker → シンプルティッカー変換

変換ルール: `"AAPL US Equity"` → `"AAPL"`（スペース分割の第1要素）

**非標準ティッカーの取り扱い**:

| Bloomberg Ticker | シンプル | 企業名 | 備考 |
|-----------------|---------|--------|------|
| `1715651D US Equity` | `1715651D` | EIDP, Inc. (DuPont) | 歴史的ティッカー |
| `1541931D US Equity` | `1541931D` | Altera Corporation | Intel買収済み |
| `2258717D US Equity` | `2258717D` | Dell EMC | Dell統合済み |
| `2326248D US Equity` | `2326248D` | CA, Inc. | Broadcom買収済み |
| `990315D US Equity` | `990315D` | Core Laboratories Inc. | ティッカー変更 |

非標準ティッカー（数字始まり）は `COMPANYNAME` をフォールバック識別子として使用し、`ticker_mapping.json` でマッピングを管理する。

#### 重複処理

- **デデュプキー**: `TRANSCRIPTID`
- 同一SEDOLで異なるTRANSCRIPTID → 別トランスクリプトとして保持（例: 通常 + Pre Recorded）
- 同一SEDOLで同一TRANSCRIPTID → 最初のレコードを採用（取引所違いの重複）
- 2015-01月データでは TRANSCRIPTID の重複は0件

#### データ規模（2015-01月サンプル）

| 項目 | 値 |
|------|-----|
| ユニークSEDOL数 | 38 |
| 全レコード数 | 40 |
| デデュプ後レコード数 | 40（重複なし） |
| 複数レコードSEDOL | 2件（取引所違い、Pre Recorded違い） |
| 対象国 | US, GB, CA |
| 言語 | 全て英語 |
| text2+text4 平均長 | ~50,000文字 |
| 月間ファイル数 | 10ファイル（2015-01 〜 2015-09） |

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
    "text4_truncated": false,
    "word_count": 5500
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
| 決算トランスクリプト | 2015-01 〜 2015-09（10ファイル） | S&P Capital IQ JSON (`list_transcript_YYYY-MM.json`) | 競争優位性の主張抽出（Phase 1 主入力） |
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

**入力**: `docs/Multi-Agent-System-for-Investment-Team/data/simple-ai-poc/transcript/list_transcript_YYYY-MM.json`
**出力**: `research/ca_strategy_poc/transcripts/{TICKER}/{YYYYMM}_earnings_call.json`

#### 処理フロー

```
1. JSONロード（トレーリングカンマ修正）
2. SEDOLループ → レコードループ
3. TRANSCRIPTIDデデュプ（同一IDは最初のレコードを採用）
4. Bloomberg Ticker → シンプルティッカー変換
   - "AAPL US Equity" → "AAPL"
   - 非標準ティッカー（数字始まり）→ ticker_mapping.json で解決
5. text2パース（プレゼンセクション）
   - 【プレゼン: Name (Role)】 タグを正規表現で分割
   - 各セクションの speaker / role / content を抽出
6. text4パース（Q&Aセクション）
   - 【質問: Name (Analysts)】【回答: Name (Executives)】 タグを分割
   - --- 区切りで質問・回答ペアを構成
7. トランケーション検知
   - len(text4) == 32767 → metadata.text4_truncated = True
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
  "990315D": {"ticker": "CLB", "company_name": "Core Laboratories Inc.", "note": "ティッカー変更"}
}
```

#### エッジケース処理

| ケース | 対処 |
|--------|------|
| トレーリングカンマのあるJSON | `re.sub(r',(\s*[}\]])', r'\1', content)` で修正 |
| text4=32767（トランケーション） | `metadata.text4_truncated = True` を記録 |
| 非標準ティッカー（数字始まり） | `ticker_mapping.json` でマッピング、未登録なら `COMPANYNAME` でログ出力 |
| text2/text4が空またはnull | 空セクションとして記録、`metadata.missing_sections` に記録 |
| 同一SEDOL複数レコード | TRANSCRIPTIDでデデュプ |
| 非英語トランスクリプト | `is_english != 1.0` のレコードをスキップ |

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
2. `transcript_parser.py` 実装 + 全10ファイル（2015-01 ~ 2015-09）のパース実行
3. `ticker_mapping.json` 作成（非標準ティッカーのマッピング、全ファイルスキャン後に確定）
4. Pydanticモデル定義（`types.py`）
5. KB3の5銘柄(ORLY, COST, LLY, CHD, MNST)のパース済みトランスクリプトを確認
6. KB1-T/KB2-T/KB3-T作成
7. universe.json作成（300銘柄+GICSセクター+ベンチマークウェイト）
8. エージェント設計・定義ファイル作成

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
| **全テキストフィールドの32767文字トランケーション** | text3/text4が同じ32767上限、Allも~33500上限。text3はtext4のフォールバックにならない。**完全なデータを再提供予定**。再提供後にトランケーション状況を再評価する。 |
| **非標準ティッカー（数字始まり）のマッピング** | `ticker_mapping.json` で手動マッピング管理。5銘柄確認済み（DD, ALTR, EMC, CA, CLB）。新ファイル追加時に未登録ティッカーを検出しログ出力。 |
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

**注意**: ソースデータ (`docs/Multi-Agent-System-for-Investment-Team/data/simple-ai-poc/transcript/`) はリポジトリに含まれるが読み取り専用。`transcript_parser.py` がパースして `research/ca_strategy_poc/transcripts/` に正規化フォーマットで出力する。

---

## 実装 Wave（依存関係順）

| Wave | 名前 | ファイル | 見積 |
|------|------|---------|------|
| 1 | 基盤（型定義・ユーティリティ・パーサー） | `types.py`, `batch.py`, `transcript_parser.py`, `__init__.py`, `py.typed` | 2-3日 |
| 2 | ローダー・集約 | `transcript.py`, `aggregator.py`, `neutralizer.py` | 2日 |
| 3 | LLM処理 | `extractor.py`, `scorer.py` | 3-4日 |
| 4 | ポートフォリオ・出力 | `portfolio_builder.py`, `output.py` | 2-3日 |
| 5 | 統合 | `orchestrator.py` | 2日 |

**Wave 1 の変更点**: `transcript_parser.py` を Wave 1 に追加。パーサーは他のコンポーネントより先に実装する必要がある（パース済みデータがないと Wave 2 以降のテストが書けないため）。

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
