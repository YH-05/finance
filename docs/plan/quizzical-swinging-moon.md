# ETF.com スクレイピングモジュール実装計画

## Context

`notebook_sample/etf-dot-com.ipynb` と `src_sample/etf_dot_com.py` にETF.comからETFデータをスクレイピングする実験コードが存在する。これを `src/market/etfcom/` サブモジュールとして正式にパッケージ化し、既存の market パッケージアーキテクチャに統合する。

**目的**: ETF.comから全ETFのティッカー一覧、ファンダメンタルデータ、ファンドフローデータを取得するモジュールを、プロジェクトのコーディング規約・テスト戦略に準拠して実装する。

---

## モジュール設計

### アーキテクチャ

```
ETFComFetcher (DataCollector継承)
    ├── WebDriverManager    ← Selenium セッション管理（コンテキストマネージャ）
    ├── parser.py           ← HTMLパース（純粋関数、ブラウザ非依存）
    ├── types.py            ← @dataclass 型定義
    └── constants.py        ← URL、セレクター、設定定数
```

**設計原則**: ブラウザ操作（fetcher）とデータ解析（parser）を分離し、parser を単体テスト可能にする。

### 技術選定

| 項目 | 選定 | 根拠 |
|------|------|------|
| スクレイピング | **Selenium** | 既存コード互換、DataCollector.fetch()が同期インターフェース、Playwrightはasync必須で基底クラス契約と不整合 |
| 基底クラス | **DataCollector** | Webスクレイピング向け（TSAと同パターン）。BaseDataFetcher(fred)はAPI向けで不適 |
| 並列処理 | **シングルブラウザ逐次** | 初期実装は安定性重視。並列はフォローアップで追加可能 |
| 型定義 | **@dataclass** | プロジェクト標準（Pydanticではない） |

---

## ファイル構成

### 新規作成ファイル

```
src/market/etfcom/
├── __init__.py          # re-export: ETFComFetcher, types
├── fetcher.py           # ETFComFetcher(DataCollector), WebDriverManager
├── parser.py            # parse_fundamentals(), parse_fund_flows(), parse_ticker_table()
├── types.py             # ETFTicker, ETFFundamentals, ETFFundFlow, ScrapeConfig
├── constants.py         # URL, セレクター, Chrome options

tests/market/unit/etfcom/
├── __init__.py
├── conftest.py          # サンプルHTML fixtures, mock WebDriver
├── test_types.py
├── test_parser.py
├── test_fetcher.py

tests/market/property/etfcom/
├── __init__.py
├── test_types_property.py

tests/market/integration/etfcom/
├── __init__.py
├── test_fetcher_integration.py  # @pytest.mark.slow
```

### 変更ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/market/errors.py` | `ETFComError`, `ETFComConnectionError`, `ETFComParseError`, `ETFComTimeoutError` 追加 |
| `src/market/__init__.py` | `ETFComFetcher` と新エラークラスの re-export 追加 |
| `pyproject.toml` | `[project.optional-dependencies]` に `etfcom` グループ追加 |

### 重要な参照ファイル（既存・変更不要）

| ファイル | 参照理由 |
|---------|---------|
| `src/market/base_collector.py` | DataCollector ABC（fetch/validate/collect テンプレートメソッド） |
| `src/market/tsa.py` | 最も近い先行実装（DataCollector継承、HTMLスクレイピング、構造化ロギング） |
| `src/market/errors.py` | エラー階層パターン（ErrorCode enum, source別Error） |
| `src/market/yfinance/types.py` | @dataclass 型定義パターン（frozen, Enum） |
| `src/market/fred/constants.py` | 定数管理パターン（Final[str]） |
| `src_sample/etf_dot_com.py` | 移植元コード（4関数） |

---

## データモデル

### ETFFundamentals（17フィールド）

**summary-data セクション** (DOM: `#summary-data`):
- `issuer`, `inception_date`, `expense_ratio`, `aum`, `index_tracked`

**classification-index-data セクション** (DOM: `#classification-index-data`):
- `segment`, `structure`, `asset_class`, `category`, `focus`, `niche`, `region`, `geography`, `weighting_methodology`, `selection_methodology`, `segment_benchmark`

**メタデータ**: `ticker`, `has_loading_values: bool`, `fetched_at: datetime`

### ETFFundFlow

- `ticker: str`, `date: datetime`, `net_flows: float`

### ETFTicker

- `ticker: str` + スクリーナーテーブルのカラム + `fetched_at: datetime`

---

## 段階的実装ステップ

### Phase 1: 基盤（types, constants, errors）

**スコープ**:
- `src/market/etfcom/__init__.py`, `types.py`, `constants.py` 作成
- `src/market/errors.py` に ETFCom エラー階層追加（`Exception` 直接継承、FREDError/BloombergErrorと同パターン）
- `ErrorCode` に `ETFCOM_PARSE_ERROR`, `ETFCOM_TIMEOUT`, `ETFCOM_CONNECTION_FAILED` 追加
- `src/market/__init__.py` にエラークラスの re-export 追加
- `pyproject.toml` に `etfcom = ["selenium>=4.15.0", "webdriver-manager>=4.0.0"]` 追加

**テスト**: `test_types.py`（dataclass生成、frozen不変条件）

### Phase 2: パーサー（純粋関数）

**スコープ**:
- `src/market/etfcom/parser.py` 作成
- `parse_fundamentals()`, `parse_fund_flow_row()`, `parse_ticker_table()`
- `is_loading_value()`, `is_placeholder_value()`, `clean_numeric_string()`

**テスト**: `test_parser.py`（loading..., --, 空データ, 不正日付）
**プロパティテスト**: `test_types_property.py`

### Phase 3: WebDriverManager

**スコープ**:
- コンテキストマネージャ（headless Chrome起動/終了）
- `handle_cookie_consent()`, `scrape_key_value_data()` (loading...リトライ付き)
- `src_sample/etf_dot_com.py:263-356` から移植・改善

**テスト**: モックWebDriverで context manager protocol, cookie処理

### Phase 4: Ticker一覧取得

**スコープ**: `ETFComFetcher.fetch_all_tickers()` — スクリーナーページのページネーション

### Phase 5: Fundamentals取得

**スコープ**: `ETFComFetcher.fetch_fundamentals(tickers)` — 逐次アクセス、loading/-- 処理

### Phase 6: Fund Flows取得

**スコープ**: `ETFComFetcher.fetch_fund_flows(tickers, start_date, end_date)` — ページネーション

### Phase 7: DataCollector統合 + 公開API

**スコープ**: `fetch(**kwargs)` mode ディスパッチ、`validate()`、`__init__.py` export

### Phase 8: 品質・ドキュメント

**スコープ**: `make check-all`、Docstring、README、CLAUDE.md更新

---

## 並列化の可能性

Phase 4, 5, 6 は互いに独立しており並列実装可能:

```
Phase 1 (基盤)
    ↓
Phase 2 (パーサー) ── Phase 3 (WebDriverManager)
    ↓                      ↓
    ┌──────────┬──────────┐
    ↓          ↓          ↓
Phase 4    Phase 5    Phase 6
    └──────────┼──────────┘
               ↓
        Phase 7 (統合)
               ↓
        Phase 8 (品質)
```

---

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| ETF.com DOM構造変更 | セレクター破損 | 全セレクターを `constants.py` に集約、統合テストで早期検知 |
| loading... データ残存 (~1%) | データ品質低下 | リトライ5回+安定性チェック、`None` + `has_loading_values` フラグ |
| アンチスクレイピング対策 | ブロック | 現実的User-Agent、ポライトディレイ、シングルブラウザ |
| Selenium/ChromeDriver版不整合 | 起動失敗 | webdriver-manager自動管理、README にフォールバック記載 |
| `"--"` プレースホルダーデータ | 無効データ混入 | `is_placeholder_value()` で検出→ `None` 変換 |

---

## 検証方法

### テスト実行
```bash
# 単体テスト
uv run pytest tests/market/unit/etfcom/ -v

# プロパティテスト
uv run pytest tests/market/property/etfcom/ -v

# 統合テスト（実ブラウザ）
uv run pytest tests/market/integration/etfcom/ -v -m slow

# 品質チェック
make check-all
```

### 手動検証
```python
from market.etfcom import ETFComFetcher

fetcher = ETFComFetcher()

# Ticker一覧取得
tickers_df = fetcher.fetch(mode="tickers")

# Fundamentals取得（少数でテスト）
fundamentals_df = fetcher.fetch(mode="fundamentals", tickers=["VOO", "SPY", "QQQ"])

# Fund Flows取得
flows_df = fetcher.fetch(mode="fund_flows", tickers=["VOO"])
```
