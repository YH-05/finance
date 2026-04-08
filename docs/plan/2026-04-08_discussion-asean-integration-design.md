# 議論メモ: ASEAN カバレッジ統合設計書レビュー

**日付**: 2026-04-08
**議論ID**: disc-2026-04-08-asean-integration-design
**参加**: ユーザー + AI

## 背景・コンテキスト

Issue #3900（Wave3: ASEAN カバレッジ統合設計）の設計書全体像をレビュー。
Project-105 Wave1（PR #3901）マージ完了後、NSE/BSEが実装済みの状態で、
既存の ASEAN フレームワーク（`asean_common`）への India 統合設計を議論。

前提:
- 2026-03-18 の ASEAN データソース調査で3フェーズ戦略が決定済み
- NSE モジュール: CorporateCollector / IndicesCollector / QuoteCollector / StockListCollector + ShareholdingPattern 実装済み
- BSE モジュール: bhavcopy CSV + geo-block ワークアラウンド済み

## 議論のサマリー

6つの論点を順番に議論し、全て合意形成完了。

### 論点1: enum リネーム戦略
- 選択肢: MarketExchange / AsiaMarket / リネームなし / 分離管理(Union型)
- **決定**: `MarketExchange`（汎用名、将来US/EU拡張にも対応）

### 論点2: NSE → TickerRecord 型マッピング（sector/industry）
- NSE API 自体にはsector/industryフィールドがない → どこから取得するか
- quote API の `industryInfo` に `macro`/`sector`/`industry`/`basicIndustry` の4階層が存在することを確認
- **決定**: NSE Industry エンドポイント（quote API の industryInfo）から取得
  - `macro` → `sector`（GICS セクター相当）
  - `industry` → `industry`

### 論点3: yfinance サフィックス
- ストレートフォワードな拡張
- **決定**: NSE=`.NS`, BSE=`.BO` を `YFINANCE_SUFFIX_MAP` に追加

### 論点4: tradingview-screener 重複排除
- NSE/BSE 両方が `market="india"` にマップされる問題
- **決定**: NSE 優先。`Query.set_markets("india").where(col("exchange") == "NSE")` パターン

### 論点5: BSE の位置づけ
- **決定**: 当面対象外。`MarketExchange` enum にはメンバーとして含めるが実装は後回し
- geo-block 問題もあり、NSE で十分カバー可能

### 論点6: 移行計画
- 設計書のみか、リネーム実装も含めるか
- **決定**: 設計書 + リネーム実装を一括で実施
- パッケージディレクトリ `asean_common` → `market_common` にリネーム
- 影響範囲: ~48ファイル、~436箇所

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-08-010 | AseanMarket → MarketExchange リネーム。NSE/BSE メンバー追加 | 汎用名。将来 US/EU 拡張対応 |
| dec-2026-04-08-011 | sector/industry は NSE quote API の industryInfo から取得 | macro→sector, industry→industry マッピング |
| dec-2026-04-08-012 | yfinance サフィックス NSE=.NS, BSE=.BO 追加 | 既存パターン拡張 |
| dec-2026-04-08-013 | screener は NSE 優先。market=india + exchange=NSE フィルタ | 重複排除 |
| dec-2026-04-08-014 | BSE は当面実装対象外。enum には含めるが実装後回し | geo-block問題 + NSEで十分 |
| dec-2026-04-08-015 | Issue #3900 スコープ拡大: 設計書+リネーム実装。見積もり 1h→3-4h | ~48ファイル ~436箇所 |
| dec-2026-04-08-016 | ディレクトリ asean_common → market_common リネーム | MarketExchange との命名統一 |

## アクションアイテム

| ID | 内容 | 優先度 | 期限 |
|----|------|--------|------|
| act-2026-04-08-010 | Issue #3900 body をスコープ拡大版に更新 | 高 | 2026-04-08 |
| act-2026-04-08-011 | asean_common → market_common + AseanMarket → MarketExchange リネーム | 高 | - |
| act-2026-04-08-012 | NSE/BSE メンバー追加 + 全MAP拡張 | 中 | - |
| act-2026-04-08-013 | docs/design/asean-india-integration.md 設計書作成 | 中 | - |

## 影響範囲（grep 結果）

### AseanMarket 出現箇所
- `src/`: 12ファイル、85箇所
- `tests/`: 8ファイル、118箇所

### asean_common 出現箇所
- `src/`: 26ファイル、78箇所
- `tests/`: 22ファイル、155箇所

### 合計: ~48ファイル、~436箇所

## 次回の議論トピック

- リネーム実装後の `make check-all` 結果確認
- Phase 2（国別ライブラリ統合: vnstock/idx-bei/thaifin）の設計開始タイミング
- NSE TickerRecord への industryInfo マッピング実装の詳細

## 参考情報

- **Issue #3900**: https://github.com/YH-05/quants/issues/3900
- **前回の ASEAN 調査**: docs/plan/2026-03-18_discussion-asean-data-sources.md
- **AseanMarket enum**: src/market/asean_common/constants.py:32-69
- **TickerRecord**: src/market/asean_common/types.py:85-163
- **NSE StockQuote**: src/market/nse/types.py:164-229
- **NSE industryInfo**: src/market/nse/parsers.py:423-428
