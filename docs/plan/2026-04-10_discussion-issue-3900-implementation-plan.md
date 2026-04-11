# 議論メモ: Issue #3900 実装手順確定

**日付**: 2026-04-10
**議論ID**: disc-2026-04-10-issue-3900-implementation-plan
**参加**: ユーザー + AI
**対象 Issue**: [#3900 \[Wave3\] ASEAN カバレッジ統合設計](https://github.com/YH-05/quants/issues/3900)

## 背景・コンテキスト

2026-04-08 に Issue #3900 の設計議論を実施し、7つの決定事項（dec-2026-04-08-010〜016）と4つのアクションアイテム（act-2026-04-08-010〜013）を策定したが、直後からユーザーは投資仮説Q&Aシート生成プロジェクト（別案件）に注力していたため、Issue #3900 の実装は未着手のまま保留されていた。

今回（2026-04-10）、`/project-discuss` で NSE データ取得ロジックの実装状況を確認する中で、Issue #3900 が依然として OPEN であり実装未着手であることが判明。議論は「現状把握 → 影響範囲再調査 → 実装手順確定」の3ステップで進行し、最終的に実装手順を確定した。

## 議論のサマリー

### Phase 1: NSE 実装状況の現状把握

- **NSE モジュール完全実装済み**（`src/market/nse/` 46ファイル・11,817行）
  - Session管理、Quote、Index（16種）、Stock List、Corporate（株主構成含む）、Parser、エラー処理、型定義
  - PR #3878（基本実装）+ PR #3901（Project-105 Wave1: 株主構成エンドポイント追加）
  - 単体テスト106行 + 統合テスト464行（実API連携、geo-block自動スキップ）
- **未実装**: データ永続化（DuckDB/SQLite連携）、非同期対応
- **保留中**: Issue #3900（ASEAN統合リネーム）← 今回の議論対象

### Phase 2: 影響範囲再調査

2026-04-08 時点の見積もり（48ファイル・436箇所）が今も正確か検証。

**調査結果（2026-04-10 時点）**:

| 区分 | ファイル数 | 出現箇所 |
|------|-----------|---------|
| `src/market/` 配下（asean_common + AseanMarket） | 26 | 163 |
| `tests/market/` 配下（asean_common + AseanMarket） | 22 | 273 |
| **合計** | **48** | **436** |

**確定事項**:
- 2026-04-08 の見積もりは現在も完全に正確
- 投資仮説Q&A プロジェクトは `asean_common` に一切触れていない → コンフリクトリスクなし
- `docs/plan/` 内の過去議論メモに追加参照あり（例: `persistent-storage-architecture.md:8`）だが `.py` 限定置換で無関係
- NSE/BSE モジュールは `asean_common` 非依存 → リネーム影響を受けない
- **見落としやすい箇所**: `src/market/errors.py:1`, `src/market/__init__.py:5`

### Phase 3: 実装手順の確定

**選択した戦略**: worktree分離 + 単一PR + sed一括置換

**8フェーズ構成（合計見積もり 90-120分）**:

1. **準備** (5min): `/worktree feature/issue-3900` + `make check-all` で green state確認
2. **設計書作成** (30-45min): `docs/design/asean-india-integration.md`（最大ボトルネック）
3. **ディレクトリリネーム** (2min): `git mv src/market/asean_common src/market/market_common` + tests 同様
4. **`asean_common` 置換** (5min): `rg -l "asean_common" --type py -0 | xargs -0 sed -i '' 's/asean_common/market_common/g'` + 残存0確認
5. **`AseanMarket` 置換** (5min): 同パターンで `AseanMarket → MarketExchange`
6. **NSE/BSE enum メンバー追加** (30min): `constants.py` に NSE/BSE、`YFINANCE_SUFFIX_MAP` に `.NS`/`.BO`、`SCREENER_MARKET_MAP` に NSE→"india"（NSE優先フィルタ）
7. **品質確認** (5-15min): `make check-all` + `quality-checker --validate-only`
8. **PR作成** (5min): `/commit-and-pr` で単一PR、`closes: #3900`

**スコープ外**（本PRに含めない）:
- NSE `StockQuote` → `TickerRecord` 変換の実装コード
- `industryInfo` パーサーから TickerRecord への実マッピング
- BSE 実装

これらは設計書に仕様のみ記載し、実装は Phase 2（vnstock/idx-bei/thaifin 統合時）に回す。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-10-001 | Issue #3900 を worktree `feature/issue-3900` で隔離実施 | main汚染回避、436箇所の大規模リネームのため |
| dec-2026-04-10-002 | 単一PR戦略を採用（分割しない） | リネームは中間状態で必ず broken になる。機械的置換なら diff レビュー可能 |
| dec-2026-04-10-003 | リネーム手法は `git mv` + `rg+sed` 一括置換 | 参照は純粋な import/型参照のみ。AST refactor 不要 |
| dec-2026-04-10-004 | 検証は `make check-all` + `quality-checker` エージェント | 機械的置換の誤検出は pyright+pytest で100%検出可能 |
| dec-2026-04-10-005 | NSE/BSE enum メンバー追加は本PRスコープに含める | `MarketExchange` enum、`YFINANCE_SUFFIX_MAP`、`SCREENER_MARKET_MAP` まで |
| dec-2026-04-10-006 | NSE `StockQuote → TickerRecord` 変換実装はスコープ外 | 設計書に仕様記載のみ。実装は Phase 2 着手時 |
| dec-2026-04-10-007 | BSE 実装は本PRスコープ外 | enum メンバー定義のみ。実装は後続Issueに分離 |
| dec-2026-04-10-008 | `sed` 置換対象は `--type py` 限定 | `docs/plan/` の過去議論メモ保護、タイプミスによるドキュメント破壊防止 |

## アクションアイテム

| ID | 内容 | 優先度 | 期限 |
|----|------|--------|------|
| act-2026-04-10-001 | `/worktree feature/issue-3900` で worktree 作成 + ベースライン `make check-all` 確認 | 高 | 次セッション |
| act-2026-04-10-002 | `docs/design/asean-india-integration.md` 設計書作成（30-45min） | 高 | 次セッション |
| act-2026-04-10-003 | ディレクトリリネーム（`git mv` src/tests 両方） | 高 | 次セッション |
| act-2026-04-10-004 | `asean_common → market_common` 一括置換 + 残存0検証 | 高 | 次セッション |
| act-2026-04-10-005 | `AseanMarket → MarketExchange` 一括置換 + 残存0検証 | 高 | 次セッション |
| act-2026-04-10-006 | `MarketExchange` enum に NSE/BSE 追加、`YFINANCE_SUFFIX_MAP`/`SCREENER_MARKET_MAP` 拡張 | 高 | 次セッション |
| act-2026-04-10-007 | `make check-all` + `quality-checker --validate-only` で最終確認 | 高 | 次セッション |
| act-2026-04-10-008 | `/commit-and-pr` で単一PR作成（closes: #3900） | 高 | 次セッション |

## 次回の議論トピック

1. **Phase 2 着手タイミング**: vnstock（ベトナム）/idx-bei（インドネシア）/thaifin（タイ）の国別ライブラリ統合をいつ開始するか
2. **NSE データ永続化**: Collector 単発fetch → DuckDB/SQLite取り込み pipeline の設計
3. **NSE industryInfo → TickerRecord 変換の実装詳細**: `macro → sector`、`industry → industry` マッピングロジックと単体テスト
4. **NSE 実機マーケットアワーテスト**（IST 09:15-15:30）: act-2026-04-02-009 の実施タイミング
5. **非同期化の検討**: アジア市場拡張時のパフォーマンス要件に応じた httpx async 対応

## 参考情報

### 関連ドキュメント
- **Issue #3900**: https://github.com/YH-05/quants/issues/3900
- **前回議論メモ**: `docs/plan/2026-04-08_discussion-asean-integration-design.md`
- **Project-105 計画書**: `docs/plan/2026-04-08_project-105-nse-pipeline-improvements.md`
- **ASEAN データソース戦略**: `docs/plan/2026-03-18_discussion-asean-data-sources.md`

### 関連コード（現状）
- **AseanMarket enum**: `src/market/asean_common/constants.py:32-69`
- **TickerRecord**: `src/market/asean_common/types.py:85-163`
- **NSE StockQuote**: `src/market/nse/types.py:164-229`
- **NSE industryInfo パース**: `src/market/nse/parsers.py:423-428`
- **NSE Session（リネーム時参考）**: `src/market/nse/session.py:81-639`

### 見落としやすいリネーム対象
- `src/market/errors.py:1` — 単発参照
- `src/market/__init__.py:5` — 公開 API エクスポート
- 各国モジュール `errors.py`/`types.py`/`constants.py`（bursa/hose/sgx/set_exchange/pse/idx）
