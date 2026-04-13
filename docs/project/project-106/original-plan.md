# NSE 全銘柄データ取得ノートブック & market.nse パッケージ拡張

**日付**: 2026-04-13
**Option**: Option 2（`market.nse` パッケージ拡張 → ノートブック作成）

## Context

NSE（National Stock Exchange of India）の全上場株（~2,263銘柄）の基本情報と
詳細な株主構成データを取得するノートブックを `notebook/NSE/` に作成する。

現状:
- `src/market/nse/` パッケージは基本 API（`quote-equity`, `equity-stockIndices`,
  `EQUITY_L.csv`, `getShareholdingPattern` (NextApi) 等）のみ実装済み
- 詳細株主データ取得に必要な 2 エンドポイントは **スタンドアロンスクリプト
  （`scripts/nse_index_shareholding.py`, `scripts/nse_parse_xbrl.py`）としてのみ実装**
  されており、`market.nse` パッケージには未統合
- 特に:
  - `/api/corporate-share-holdings-master`（XBRL URL 取得に必須）
  - XBRL ファイルのパース（40+ カテゴリ別の詳細株主内訳）

目的:
1. `market.nse` パッケージに上記 2 機能を統合し、テスト可能・再利用可能に
2. パッケージを使った対話的ノートブックを作成し、全 2,263 銘柄のデータ取得パイプ
   ラインを実行できるようにする
3. デフォルトで全銘柄を対象とし、既存 SQLite DB (`data/cache/nse/nse_index.db`)
   が存在する場合は再ダウンロードをスキップできる冪等な構成にする

## 実装方針

1. **`market.nse` パッケージに新モジュール追加**（新 Collector + 新パーサ + XBRL モジュール）
2. **対応するテストを追加**（ユニット / プロパティ / fixture）
3. **ノートブック `notebook/NSE/nse_full_download.ipynb` を作成**し、新 API を使用
4. **既存スクリプトは非推奨扱い（削除はしない）**、ノートブックから同等機能を提供

## ファイルマップ

### 新規追加

| パス | 種類 | 内容 |
|------|------|------|
| `src/market/nse/xbrl.py` | モジュール | XBRL パーサ（ContextInfo, ShareholderRow, ParseResult dataclass + `parse_xbrl()` 関数） |
| `src/market/nse/collectors/share_holding.py` | モジュール | `ShareholdingCollector` クラス（`corporate-share-holdings-master` + XBRL ダウンロード統合） |
| `tests/market/nse/unit/test_xbrl.py` | テスト | XBRL パーサのユニットテスト |
| `tests/market/nse/unit/test_share_holding_collector.py` | テスト | ShareholdingCollector のユニットテスト |
| `tests/market/nse/fixtures/xbrl_sample.xml` | fixture | テスト用の XBRL サンプル XML |
| `notebook/NSE/nse_full_download.ipynb` | ノートブック | 全上場株データ取得パイプライン |
| `notebook/NSE/README.md` | ドキュメント | ノートブックの使い方と出力データ説明 |

### 修正

| パス | 修正内容 |
|------|---------|
| `src/market/nse/types.py` | `CorporateShareHolding` dataclass 追加、`__all__` 更新 |
| `src/market/nse/parsers.py` | `parse_corporate_shareholding()` 関数追加、`__all__` 更新 |
| `src/market/nse/constants.py` | `CORPORATE_SHARE_HOLDINGS_ENDPOINT` 定数追加、XBRL 名前空間定数追加 |
| `src/market/nse/collectors/__init__.py` | `ShareholdingCollector` をエクスポート |
| `src/market/nse/__init__.py` | 新 Collector / dataclass / パーサをエクスポート |

## 詳細設計

### 1. `src/market/nse/types.py` に追加

```python
@dataclass(frozen=True)
class CorporateShareHolding:
    """Shareholding overview from /api/corporate-share-holdings-master.

    Contains promoter/public/employee-trust percentages and a URL to the
    detailed XBRL filing. Used as the master record for linking to XBRL
    detail parsing.
    """

    symbol: str
    as_on_date: str              # 例: "31-Dec-2025"
    promoter_group_pct: str      # "pr_and_prgrp"
    public_pct: str              # "public_val"
    employee_trust_pct: str = "" # "employeeTrusts"
    submission_date: str = ""
    broadcast_date: str = ""
    xbrl_url: str = ""           # "xbrl" - XBRL detail file URL
```

### 2. `src/market/nse/parsers.py` に追加

```python
def parse_corporate_shareholding(
    data: list[dict[str, Any]],
    *,
    symbol: str = "",
) -> list[CorporateShareHolding]:
    """Parse /api/corporate-share-holdings-master response.

    Parameters
    ----------
    data : list[dict[str, Any]]
        JSON list returned by endpoint. Each dict represents one
        quarterly shareholding record.
    symbol : str
        NSE symbol to use when record lacks "symbol" field.

    Returns
    -------
    list[CorporateShareHolding]
    """
    # 実装: 既存 parse_shareholding_pattern と同様のパターンを踏襲
```

### 3. `src/market/nse/constants.py` に追加

```python
# Corporate shareholding endpoint
CORPORATE_SHARE_HOLDINGS_ENDPOINT = f"{API_BASE_URL}/corporate-share-holdings-master"

# XBRL namespaces
XBRL_SHP_NS = "http://www.bseindia.com/xbrl/shp/2022-09-30/in-bse-shp"
XBRLI_NS = "http://www.xbrl.org/2003/instance"
XBRLDI_NS = "http://xbrl.org/2006/xbrldi"
```

### 4. `src/market/nse/xbrl.py` 新規モジュール

`scripts/nse_parse_xbrl.py` の以下のロジックを移植：

- **dataclass**:
  - `ContextInfo` - XBRL コンテキスト情報
  - `ShareholderRow` - 詳細行データ
  - `ParseResult` - パース結果（シンボル・日付・行リスト）

- **関数**:
  - `parse_xbrl(xml_bytes: bytes) -> ParseResult` - メインエントリ
  - `_parse_contexts(root)` - 内部
  - `_extract_data_by_context(root)` - 内部
  - `_build_category_rows(contexts, data, meta)` - 内部
  - `_build_detail_rows(contexts, data, meta)` - 内部

- **定数マッピング**:
  - `MEMBER_CATEGORY` - 88個のメンバー → (category, sub_category) マップ
  - `AXIS_TO_SUBCATEGORY` - 47個の軸名 → sub_category マップ

**既存スクリプト変更**: `scripts/nse_parse_xbrl.py` は影響なし（ノートブックへの
置き換えは別タスク）。

### 5. `src/market/nse/collectors/share_holding.py` 新規モジュール

既存 `CorporateCollector`（`corporate.py`）と同じパターンの **非 ABC** クラス：

```python
class ShareholdingCollector(NseCollectorMixin):
    """Collector for corporate shareholding + XBRL detail."""

    def fetch_shareholding(
        self, symbol: str
    ) -> list[CorporateShareHolding]:
        """Fetch shareholding master (promoter/public/XBRL URL)."""
        # uses CORPORATE_SHARE_HOLDINGS_ENDPOINT + parse_corporate_shareholding

    def fetch_xbrl_detail(
        self, xbrl_url: str
    ) -> ParseResult:
        """Download XBRL file and parse to ParseResult."""
        # uses session to download, then xbrl.parse_xbrl()
```

- Input 検証（symbol の長さ・文字種）は既存 `CorporateCollector.get_shareholding_pattern`
  と同じパターンで実装
- `fetch_xbrl_detail` は XBRL URL を直接受け取り、ダウンロード → パースを実行
- ホスト制限は `session.py` の SSRF ホワイトリスト拡張で対応（`nsearchives.nseindia.com`
  は既に許可済み）

### 6. `__init__.py` エクスポート更新

- `src/market/nse/collectors/__init__.py`: `ShareholdingCollector` 追加
- `src/market/nse/__init__.py`: `ShareholdingCollector`, `CorporateShareHolding`,
  `parse_corporate_shareholding`, `parse_xbrl`, `ParseResult`, `ShareholderRow`,
  `ContextInfo` をエクスポート

### 7. テスト戦略

#### `tests/market/nse/unit/test_share_holding_collector.py`

既存 `test_corporate_collector.py` と同じパターン:

- `TestShareholdingCollectorInit` (3 tests)
  - デフォルト初期化 / session 注入 / ABC 非継承確認
- `TestFetchShareholding` (5-6 tests)
  - 正常系リスト取得 / 正しいエンドポイント / symbol バリデーション
  - 空レスポンス / 不正形式レスポンス / 注入セッションはクローズしない
- `TestFetchXbrlDetail` (4-5 tests)
  - 正常系 ParseResult 返却 / URL バリデーション / ダウンロード失敗時例外
  - パース失敗時は NseParseError

#### `tests/market/nse/unit/test_xbrl.py`

- `TestContextInfo` (2 tests) - dataclass
- `TestShareholderRow` (3 tests) - dataclass + as_list()
- `TestParseResult` (2 tests) - dataclass
- `TestParseXbrl` (6-8 tests)
  - 正常系: カテゴリ行 + 詳細行 / メタデータ抽出
  - エッジ: 空 XML / 不正 XML / メンバー不明
  - `fixtures/xbrl_sample.xml` を使用（小さめのサンプル XML 1-2件）

#### `tests/market/nse/unit/test_parsers.py` に追加

- `TestParseCorporateShareholding` (6-8 tests)
  - 正常系リスト解析 / 各フィールド抽出 / xbrl_url 抽出
  - 空リスト / 非リスト入力 / symbol デフォルト

推定テスト追加数: **合計 25-30 テスト**

### 8. ノートブック `notebook/NSE/nse_full_download.ipynb`

#### 前提条件
- デフォルトで全 2,263 銘柄処理（所要 30-40 分）
- 既存 `data/cache/nse/nse_index.db` があれば Phase 1-3 をスキップ可能
- Phase 4 (XBRL) は URL リスト駆動で独立実行可能

#### セル構成

| セル | 種類 | 内容 |
|------|------|------|
| 1 | Markdown | タイトル + 概要 + 前提条件 + 所要時間 |
| 2 | Code | imports (`market.nse` からの Collector 群, pandas, sqlite3, tqdm) |
| 3 | Code | Config（DB パス、出力 CSV パス、ディレイ設定、スキップフラグ） |
| 4 | Markdown | ## Phase 1: 全上場株マスタ（EQUITY_L.csv） |
| 5 | Code | `StockListCollector.fetch_stock_list()` → DataFrame → SQLite `stocks` テーブルに INSERT |
| 6 | Markdown | ## Phase 2: インデックス構成 + sector/industry 補完 |
| 7 | Code | `IndicesCollector.fetch_all_indices()` → 各インデックスを `fetch_index()` でループ → `meta.industry` 等で stocks テーブル UPDATE |
| 8 | Markdown | ## Phase 3: 株主構成マスタ（corporate-share-holdings-master） |
| 9 | Code | `ShareholdingCollector.fetch_shareholding(symbol)` を全銘柄ループで実行 → `shareholdings` テーブル INSERT（`tqdm` 進捗表示、0.5 秒ポライト遅延） |
| 10 | Markdown | ## Phase 4: XBRL 詳細株主データ |
| 11 | Code | Phase 3 で取得した `xbrl_url` リストを走査 → `ShareholdingCollector.fetch_xbrl_detail(url)` → `ShareholderRow` を `shareholding_detail` テーブル INSERT（進捗表示、0.3 秒遅延） |
| 12 | Markdown | ## データ確認・基本集計 |
| 13 | Code | SQLite から各テーブルを pandas で読み込み、件数・サンプル表示 |
| 14 | Markdown | ## CSV エクスポート（オプション） |
| 15 | Code | `data/exports/nse/` 以下へ CSV 出力 |

#### Config セル設計

```python
# フラグで各フェーズをスキップ可能
SKIP_PHASE_1 = False   # stocks テーブルが既にあれば True
SKIP_PHASE_2 = False   # index_members テーブルが既にあれば True
SKIP_PHASE_3 = False   # shareholdings テーブルが既にあれば True
SKIP_PHASE_4 = False   # XBRL 詳細取得（重い）

# 対象銘柄数制限（デバッグ用。None で全銘柄）
LIMIT_SYMBOLS = None

# 出力先
DB_PATH = Path("data/cache/nse/nse_index.db")
EXPORT_DIR = Path("data/exports/nse")
```

#### `notebook/NSE/README.md`

- ノートブックの目的と所要時間
- 出力テーブル定義（`stocks`, `index_members`, `shareholdings`, `shareholding_detail`）
- 使い方（フル実行 / 部分実行 / 既存データからの読み込み）
- データソース API 一覧

## 再利用する既存関数・ユーティリティ

| 既存リソース | パス | 用途 |
|------------|------|------|
| `NseSession` | `src/market/nse/session.py` | HTTP セッション（Cookie 管理、SSRF 防止、ポライト遅延） |
| `NseCollectorMixin` | `src/market/nse/collectors/_base.py` | Collector 基底（session DI） |
| `NseParseError` 等 | `src/market/nse/errors.py` | 例外階層 |
| `parse_shareholding_pattern` | `src/market/nse/parsers.py` | 新パーサの参考実装（既存 NextApi 版） |
| `CorporateCollector.get_shareholding_pattern` | `src/market/nse/collectors/corporate.py` | 新 Collector の参考実装（input validation, session lifecycle） |
| `StockListCollector.fetch_stock_list` | `src/market/nse/collectors/stock_list.py` | Phase 1 で使用 |
| `IndicesCollector.fetch_all_indices` / `fetch_index` | `src/market/nse/collectors/indices.py` | Phase 2 で使用 |
| XBRL 名前空間・マッピング定数 | `scripts/nse_parse_xbrl.py` | `xbrl.py` へ移植 |

## 実装順序

1. **constants.py / types.py の追加**（`CorporateShareHolding`, エンドポイント URL, XBRL 名前空間）
2. **parsers.py に `parse_corporate_shareholding` 追加**
3. **`xbrl.py` 新規作成**（`scripts/nse_parse_xbrl.py` からロジック移植 + ドキュメント追加）
4. **`collectors/share_holding.py` 新規作成**（`ShareholdingCollector` クラス）
5. **`__init__.py` エクスポート更新**
6. **テスト追加**（xbrl → parsers → collector の順、TDD）
7. **`make check-all` で品質チェック**
8. **ノートブック作成 + README 作成**
9. **ノートブックを実際に実行して動作確認**
10. **コミット → PR 作成**

## 検証方法

### コード品質検証

```bash
# 自動チェック
make check-all  # format, lint, typecheck, test

# 特定テストのみ実行
uv run pytest tests/market/nse/unit/test_xbrl.py -v
uv run pytest tests/market/nse/unit/test_share_holding_collector.py -v
uv run pytest tests/market/nse/unit/test_parsers.py::TestParseCorporateShareholding -v
```

### 統合動作確認

1. ノートブックを JupyterLab / VSCode で開き、全セル順次実行
2. 既存 DB を削除して真っさらな状態からフル実行（Phase 1-4）
3. `data/cache/nse/nse_index.db` の各テーブル件数確認:
   - `stocks`: ~2,263 行
   - `index_members`: ~9,100 行
   - `shareholdings`: ~100,000 行
   - `shareholding_detail`: ~146,000 行
4. サンプル銘柄（RELIANCE, TCS, HDFCBANK）で以下を検証:
   - 基本情報（ISIN, sector, industry）が取得できている
   - 株主構成カテゴリ（promoter / public / FII / mutual funds 等）が確認できる

### テスト実行確認

```bash
# XBRL モジュール
uv run pytest tests/market/nse/unit/test_xbrl.py -v

# ShareholdingCollector
uv run pytest tests/market/nse/unit/test_share_holding_collector.py -v

# パーサ
uv run pytest tests/market/nse/unit/test_parsers.py::TestParseCorporateShareholding -v

# 全 NSE テスト（既存 + 新規）
uv run pytest tests/market/nse/ -v

# カバレッジ
uv run pytest tests/market/nse/ --cov=src/market/nse --cov-report=term-missing
```

## リスク・懸念点

| リスク | 影響 | 軽減策 |
|-------|------|-------|
| XBRL パーサの XML スキーマ変動 | XBRL 2022-09-30 以外の schema が来た場合 parse 失敗 | `MEMBER_CATEGORY` 未マップ時は "Unknown" にフォールバック（既存実装踏襲） |
| ノートブック実行 30-40 分の中断リスク | 長時間実行中のネット断・セッション切れ | ポライト遅延 + 指数バックオフは `NseSession.get_with_retry` で吸収、Phase ごとに独立実行可能な SKIP_PHASE_N フラグを用意 |
| `xml.etree.ElementTree` のセキュリティ | XML 外部エンティティ攻撃（XXE） | NSE 公式ソースのみを対象とするため中リスク。既存スクリプト踏襲で `# nosec` コメント付与 |
| DB locked エラー（NAS 保存時） | SQLite が NAS で書き込み失敗 | 既存決定通り、ローカル書き込み → 手動 NAS コピーの 2 段階方式を維持（既存 `decision-dec-2026-04-08-014` 踏襲） |
| 新 API エンドポイント名衝突 | `CorporateCollector.get_shareholding_pattern` と名前紛らわしい | 新クラス名を `ShareholdingCollector` にして住み分け、docstring で差分明示 |

## 不確実性・仮定

- `corporate-share-holdings-master` の `date` フィールド形式は `"31-Dec-2025"` と仮定
  （`nse_index_shareholding.py` の実装を根拠）。実際のフォーマットは実装時に検証
- XBRL ファイルが全銘柄で `in-bse-shp` 名前空間を使用すると仮定（既存スクリプトで 2,236/2,253 = 99.3% 成功）

## 参考ドキュメント

- `docs/plan/2026-04-08_discussion-nse-scripts.md` - 既存スクリプトの設計経緯
- `docs/plan/2026-04-08_discussion-nse-shareholding-fix.md` - NextApi shareholding fix 経緯
- `docs/plan/2026-04-08_project-105-nse-pipeline-improvements.md` - Project #105 プラン
- `scripts/nse_index_shareholding.py` - `corporate-share-holdings-master` エンドポイント実装
- `scripts/nse_parse_xbrl.py` - XBRL パーサ実装
