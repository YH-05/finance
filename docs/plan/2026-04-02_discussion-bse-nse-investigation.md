# 議論メモ: BSE API 調査 → NSE モジュール設計

**日付**: 2026-04-02
**議論ID**: disc-2026-04-02-bse-nse-investigation

## 背景・コンテキスト

BSE モジュール（`src/market/bse/`）の統合テストが全スキップ（"BSE API is not reachable"）している問題の調査から開始。BSE API のアクセス障害の根本原因を特定し、代替データソースとして NSE API の実現可能性を検証、最終的に NSE モジュール設計に至った。

## 調査のサマリー

### BSE API ブロックの根本原因

BSE API (`api.bseindia.com`) は **Akamai WAF による IP ジオロケーションベースのブロック** であることを確定。

| テスト手法 | 結果 | 意味 |
|-----------|------|------|
| httpx GET | 302 → error_Bse.html | WAF リダイレクト |
| curl GET | 302 → error_Bse.html | ツール問わずブロック |
| curl_cffi Chrome131 TLS 偽装 | 302 → error_Bse.html | TLS フィンガープリントが原因ではない |
| セッション Cookie 取得 → API | 302 → error_Bse.html | Cookie 不足が原因ではない |
| Playwright headed Chromium | 302 → error_Bse.html | ブラウザ種別が原因ではない |
| NSE API（同一 IP） | 200 OK (JSON) | BSE 固有の制限 |

- IP: 東京, KDDI (106.155.x.x)
- `akamai-grn` ヘッダー確認 → Akamai WAF 確定
- Akamai ボット検知 Cookie (`_abck`, `ak_bmsc`) 未設定 → JS チャレンジではない
- **結論: 日本 IP からの BSE API アクセスは不可能**

### BSE Bhavcopy CSV ダウンロード

`www.bseindia.com` の静的ファイルダウンロードは日本から可能:

| データ | URL パターン | 件数 |
|--------|-------------|------|
| Equity Bhavcopy | `/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_{YYYYMMDD}_F_0000.CSV` | 4,920 銘柄/日 |
| Index Summary | `/bsedata/Index_Bhavcopy/INDEXSummary_{DDMMYYYY}.csv` | 72 インデックス |
| Derivative | `/download/Bhavcopy/Derivative/MS_{YYYYMMDD}-01.csv` | デリバティブ |

### NSE API 検証結果

NSE API (`www.nseindia.com/api/`) は日本から完全にアクセス可能:

| エンドポイント | データ | ステータス |
|---------------|--------|-----------|
| `quote-equity?symbol=X` | リアルタイム株価・PE・セクター・ISIN | ✅ 完全 |
| `equity-stockIndices?index=X` | インデックス構成銘柄 OHLCV | ✅ 完全 |
| `allIndices` | 全 135 インデックス | ✅ 完全 |
| `results-comparision?symbol=X` | 四半期決算 5 期分（売上・利益・EPS 等） | ✅ 完全 |
| `event-calendar` | コーポレートイベント | ✅ 98 件 |
| `market-data-pre-open?key=ALL` | プレオープン全銘柄 | ✅ 2,023 銘柄 |
| `search/autocomplete?q=X` | 銘柄検索 | ✅ |
| `marketStatus` | 市場ステータス | ✅ |
| `corporate-filing-summary?symbol=X` | 開示サマリー | ✅ |
| `last-quarter-details?upto=N` | 利用可能四半期 | ✅ |
| **NSE CSV** `EQUITY_L.csv` | 全上場銘柄リスト | ✅ 2,265 銘柄 |

NSE API の特性:
- Cookie 必須（`www.nseindia.com` を先に GET → Cookie 取得 → API コール）
- Cookie 有効期限 約 5 分（定期リフレッシュ必要）
- ポライトディレイ 0.5s 以上推奨

### yfinance による補完

yfinance `.BO`（BSE）/ `.NS`（NSE）で以下が取得可能:
- 年次決算 4 期分、四半期決算 4 期分
- 配当全履歴、株式分割全履歴
- ヒストリカル OHLCV
- PE/PBR/ROE 等の指標

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-02-001 | NSE モジュールを `src/market/nse/` として新規実装 | BSE API が日本からブロックされる一方、NSE API は完全にアクセス可能 |
| dec-2026-04-02-002 | BSE モジュールのアーキテクチャパターンを踏襲 | 一貫性・保守性のため。session/types/errors/parsers/collectors の構成を維持 |
| dec-2026-04-02-003 | NseSession に Cookie ライフサイクル管理を追加 | BSE は Cookie 不要だが、NSE は Cookie 必須。`_ensure_cookies()` メソッド追加 |
| dec-2026-04-02-004 | RetryConfig は BSE から再利用 | ドメイン非依存のため複製不要 |
| dec-2026-04-02-005 | 推奨データ戦略: NSE API + BSE Bhavcopy + yfinance | 3 ソースの組み合わせで BSE API の全機能をカバー |

## アクションアイテム

| ID | 内容 | 優先度 | 期限 |
|----|------|--------|------|
| act-2026-04-02-001 | NSE モジュール実装（6 Phase） | 高 | — |
| act-2026-04-02-002 | BSE BhavcopyCollector の CSV ダウンロード方式対応（オプション） | 中 | — |
| act-2026-04-02-003 | BSE 統合テストのスキップ理由を README に追記 | 低 | — |

## 成果物

| 成果物 | パス |
|--------|------|
| NSE モジュール設計書 | `docs/plan/2026-04-02_nse-module-design.md` |
| この議論メモ | `docs/plan/2026-04-02_discussion-bse-nse-investigation.md` |

## 次回の議論トピック

- NSE モジュールの実装開始（Phase 1: errors/constants/types から）
- ASEAN カバレッジとの統合（NSE をインド株の主要データソースとして位置づけ）
- BSE モジュールの今後の方針（プロキシ導入 vs Bhavcopy 限定運用）
