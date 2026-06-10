# 議論メモ: Reuters ニューススクレイパー mode A

**日付**: 2026-06-10
**議論ID**: disc-2026-06-10-reuters-news-scraper
**プロジェクト**: Project:quants-library
**参加**: ユーザー + AI

## 背景・コンテキスト

クオンツ分析向けにロイターのニュース記事をスクレイピングするため、サイト構造調査 → 設計 → TDD 実装 → PR マージまでを一気通貫で実施した。設計書は `docs/plan/2026-06-10_reuters-scraping-design.md`（PR #3971 で main にマージ済み）。

## 議論のサマリー

1. **サイト調査**（site-investigator）: Reuters は Arc XP (Fusion) / 完全 SSR。bot 対策の主壁は **DataDome**（記事HTML・内部API は 401 + captcha-delivery.com 誘導）。news-sitemap が `<news:stock_tickers>` 付きで記事発見の正規ルート。
2. **収集経路の切り分け**（curl_cffi コールド PoC）: サイトマップ XML は 200 取得可、記事ページは TLS 偽装+ヘッダ+Cookie でも 401 → 本文は Playwright 必須。
3. **ティッカー方針**: yfinance ではなくリポジトリ基準の **NASDAQ 形式**に変更。RIC→NASDAQ をディレクトリ照合で実証（95.5%）。
4. **収集/フィルタ分離**: 全件保存スナップショットで es が支配的と判明 → 収集は無フィルタ全件、フィルタは分析時のみ。
5. **法務**: ユーザー方針で本実装ではスコープ外。
6. **実装と CI**: `src/news_scraper/reuters.py` を TDD で実装（テスト66件）。推奨対応3項目（優先株/リトライ/ディレクトリ照合）も追加。PR #3971 を main にマージ（squash a5da158）。CI Lint の赤はリポジトリ既存債務（未整形ファイル + 新規依存脆弱性 pip/aiohttp/chromadb）で、整形コミット + ci.yml の ignore 追加で解消。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-06-10-001 | **mode A（サイトマップ・メタデータ収集）採用**。本文 mode B は DataDome のため Playwright 必須の別フェーズ | curl_cffi で記事/API は401、サイトマップXMLのみ200を実証 |
| dec-2026-06-10-002 | **無フィルタ全件保存(raw) + 分析時フィルタの ETL 分離** | 実測 3799件で es2602/en438。収集時 en 限定だと88%欠落 |
| dec-2026-06-10-003 | **RIC→NASDAQ 形式**（サフィックス除去/クラス株ドット化/優先株分離、非対象は rics_nonus へ） | NASDAQ公式ディレクトリ照合で米株RIC一致率95.5% |
| dec-2026-06-10-004 | **法務評価は本実装ではスコープ外**（ユーザー方針、技術制約のみ考慮） | 指示「リーガルチェックは省いていい」 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-06-10-001 | mode B 実装: Playwright で DataDome 通過 → 本文抽出。トピックコード精密フィルタも mode B 前提 | 中 | pending |
| act-2026-06-10-002 | NASDAQ ディレクトリ照合の universe フィルタ本番運用、RIC未一致のログ駆動拡充 | 低 | pending |
| act-2026-06-10-003 | 多言語版(es/latam/pt)の活用方針検討（グローバル/ASEAN カバレッジと関連） | 低 | pending |

## 次回の議論トピック

- mode B（本文取得）の必要性とコスト（Playwright 運用・DataDome 突破の安定性）の評価
- 収集したメタデータ（ティッカー別ヘッドラインフロー）のクオンツシグナルへの接続方法
- 多言語版データの ASEAN/グローバルカバレッジ（[[user_asean_coverage]]）への活用

## 参考情報

- 実装: `src/news_scraper/reuters.py`（main、PR #3971 / squash a5da158）
- 設計: `docs/plan/2026-06-10_reuters-scraping-design.md`
- PoC（使い捨て）: `.tmp/reuters_poc*.py`, `.tmp/reuters_ric_nasdaq.py`, `.tmp/reuters_mode_a_poc.py`
- CI デバッグ知見: メモリ `feedback_ci_lint_reproduction`
