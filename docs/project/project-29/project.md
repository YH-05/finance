# `configuration/` を `utils_core/` に統合

## プロジェクト情報

- **プロジェクト名**: レガシーコード統合 & SOLID原則準拠アーキテクチャへの移行
- **GitHub Project**: [#29](https://github.com/users/YH-05/projects/29)
- **種別**: リファクタリング（アーキテクチャ改善）
- **優先度**: 高
- **推定時間**: 約25時間
- **ステータス**: Todo
- **削減コード量**: 約710行（重複コード削減）

## 概要

プロジェクト全体のレガシーコードを整理し、モダンなアーキテクチャに統合します：

1. **configuration パッケージ**: `src/utils_core/` に統合し、設定管理を一元化
2. **FRED モジュール**: `sample_data.py` を削除し、`HistoricalCache` に統一
3. **market_report_utils.py**: 機能を適切なモジュールに分離・統合

### 現状の問題点

#### configuration パッケージ

1. **レガシーコードの残存**: `configuration/` ディレクトリ（3ファイル）はほぼ使用されていない
2. **重複実装**: ロギング機能が3箇所に重複
   - `configuration/log.py` (レガシー、debugpy/pandas 依存)
   - `news/utils/logging_config.py` (ローカル実装)
   - `utils_core/logging/config.py` (新しい実装、全体で使用中)
3. **未使用の環境変数**: 30個以上の環境変数定義があるが、実際に使用されているのは5個のみ
4. **直接的な環境変数アクセス**: `os.environ.get()` の直接呼び出しが散在

#### FRED モジュール

5. **レガシーデータローダーの残存**: `market/fred/sample_data.py` の `FredDataLoader` クラスが既存の `HistoricalCache` と機能重複
   - SQLite3ベースの古い実装
   - `configuration` パッケージへの依存
   - 標準loggingの使用（structlog 未使用）
6. **ノートブック内での古いAPI使用**: `notebook/Market-Report2.ipynb` がレガシーAPIを参照

#### market_report_utils モジュール

7. **レガシーコードの残存**: `src_sample/market_report_utils.py`（約2000行）が既存モジュールと機能重複
   - `MarketPerformanceAnalyzer` と `PerformanceAnalyzer` でパフォーマンス計算が重複
   - ティッカーグループがハードコード（symbols.yaml への移行が必要）
   - structlog 未使用（ロギングなし）
8. **アーキテクチャの不統一**: 複数の責務が1ファイルに混在
   - パフォーマンス計算、可視化、データ収集、高度な分析が同一ファイル
   - TSA旅客数、Bloombergデータ、ドル指数分析など、専門クラスが分離されていない
9. **重複実装**: yfinance データ取得が複数箇所に存在
   - curl_cffi を使った独自実装（高速だが、YFinanceFetcher と重複）

### 実際に使用されている環境変数

| 変数名 | 使用箇所 | 必須 |
|--------|---------|------|
| `FRED_API_KEY` | `market/fred/fetcher.py:100` | ✅ |
| `LOG_LEVEL` | `utils_core/logging/config.py:270` | ❌ (デフォルト: INFO) |
| `LOG_FORMAT` | `utils_core/logging/config.py:282` | ❌ (デフォルト: console) |
| `LOG_DIR` | `utils_core/logging/config.py:286` | ❌ |
| `PROJECT_ENV` | `utils_core/logging/config.py:325` | ❌ (デフォルト: development) |

## リファクタリング戦略

### アーキテクチャ選択: Option B

**`utils_core/settings.py` として新規モジュール作成**

**理由**:
- ロギング設定と環境変数管理は責務が異なる（単一責任原則）
- 将来的な拡張（pydantic-settings 導入など）が容易
- インポートパスが明確（`from utils_core.settings import get_setting`）

### 新規モジュール構成

```
src/utils_core/
├── __init__.py
├── types.py                    # 既存（LogLevel, LogFormat）
├── settings.py                 # 新規作成（環境変数管理）
└── logging/
    ├── __init__.py
    └── config.py               # 既存（structlog設定）→ 修正
```

## タスク一覧

### Phase 1: 新規モジュール作成（影響: なし）

- [ ] `src/utils_core/settings.py` を作成
  - [ ] 実際に使用されている5つの環境変数のみを実装
  - [ ] 遅延読み込み（lazy loading）を実装
  - [ ] 型安全なアクセス関数を提供
- [ ] `tests/utils_core/unit/test_settings.py` を作成
  - [ ] 環境変数の取得テスト
  - [ ] デフォルト値テスト
  - [ ] 型変換テスト
  - [ ] エラーケーステスト
- [ ] 検証
  - [ ] `make test-unit` が成功
  - [ ] `make typecheck` が成功

**推定時間**: 1時間

### Phase 2: `utils_core/logging/config.py` のリファクタリング（影響: 小）

- [ ] `utils_core/logging/config.py` を修正
  - [ ] 270行目: `LOG_LEVEL` の取得を settings.py に委譲
  - [ ] 282行目: `LOG_FORMAT` の取得を settings.py に委譲
  - [ ] 286行目: `LOG_DIR` の取得を settings.py に委譲
  - [ ] 287行目: `LOG_FILE_ENABLED` の取得を settings.py に委譲
  - [ ] 325行目: `PROJECT_ENV` の取得を settings.py に委譲
- [ ] 既存のロギングテストを実行して動作確認
- [ ] 検証
  - [ ] 既存のロギングテストが全て成功
  - [ ] `make check-all` が成功

**推定時間**: 30分

### Phase 3: レガシーコードの非推奨化（影響: なし）

- [ ] `configuration/__init__.py` を修正
  - [ ] import 時に Deprecation 警告を表示
  - [ ] 将来のバージョンで削除予定であることを明示
- [ ] 検証
  - [ ] `configuration` をインポートすると警告が表示される
  - [ ] 既存の動作は変わらない

**推定時間**: 15分

### Phase 4: `configuration/log.py` の削除（影響: なし）

- [ ] `configuration/log.py` を削除
- [ ] 検証
  - [ ] `make check-all` が成功
  - [ ] grep で `from configuration.log` が見つからない

**推定時間**: 15分

### Phase 5: `news/utils/logging_config.py` の統合（影響: 中）

- [ ] `news/utils/logging_config.py` と `utils_core/logging/config.py` を比較
- [ ] 機能差分を分析
- [ ] 必要に応じて `utils_core/logging/config.py` に機能をマージ
- [ ] `news/utils/logging_config.py` を削除
- [ ] `news/` パッケージ内のインポート文を更新
- [ ] 検証
  - [ ] `news` パッケージのテストが全て成功
  - [ ] `make check-all` が成功

**推定時間**: 1時間

### Phase 6: `configuration/` ディレクトリの完全削除（影響: なし）

- [ ] `configuration/file_path.py` の削除
- [ ] `configuration/__init__.py` の削除
- [ ] `configuration/` ディレクトリの削除
- [ ] 検証
  - [ ] `make check-all` が成功
  - [ ] grep で `from configuration` が見つからない

**推定時間**: 15分

## 実装の優先順位

### 必須（Must）: Phase 1, 2
- 設定管理の一元化（最重要）
- 推定時間: 1.5時間

### 推奨（Should）: Phase 4, 5, 7
- レガシーコードの削除（品質向上）
  - Phase 4: `configuration/log.py` の削除
  - Phase 5: `news/utils/logging_config.py` の統合
  - Phase 7: `market/fred/sample_data.py` の削除とノートブック更新
- 推定時間: 2時間

### オプション（Could）: Phase 3, 6
- Deprecation 警告、完全削除（将来的な整理）
- 推定時間: 30分

**Phase 1-7 推定時間**: 約4時間

## Critical Files（重要ファイル）

### Phase 1, 2 で作成・修正するファイル

1. **`src/utils_core/settings.py`** [作成]
   - 環境変数管理の中核モジュール
   - 型安全なアクセス関数を提供

2. **`src/utils_core/logging/config.py`** [修正]
   - 270行目: `LOG_LEVEL` の取得
   - 282行目: `LOG_FORMAT` の取得
   - 286行目: `LOG_DIR` の取得
   - 287行目: `LOG_FILE_ENABLED` の取得
   - 325行目: `PROJECT_ENV` の取得

3. **`tests/utils_core/unit/test_settings.py`** [作成]
   - settings.py の包括的テスト

### Phase 4, 5 で削除するファイル

4. **`src/configuration/log.py`** [削除]
   - レガシーロギング実装

5. **`src/news/utils/logging_config.py`** [削除]
   - 重複実装の統合

### Phase 6 で削除するファイル

6. **`src/configuration/file_path.py`** [削除]
7. **`src/configuration/__init__.py`** [削除]

### Phase 7 で削除・修正するファイル

8. **`src/market/fred/sample_data.py`** [削除]
   - レガシーFREDデータローダー（`FredDataLoader` クラス）
   - SQLite3 ベースの実装（`HistoricalCache` で代替）

9. **`notebook/Market-Report2.ipynb`** [修正]
   - `FredDataLoader` の使用を `HistoricalCache` に置き換え

### Phase 8 で作成・修正・削除するファイル

#### Phase 8-1（Strategy パターン）

10. **`src/market/yfinance/session.py`** [作成]
    - HttpSessionProtocol プロトコル定義
    - CurlCffiSession クラス（高速版）
    - StandardRequestsSession クラス（標準版）

11. **`src/market/yfinance/fetcher.py`** [修正]
    - http_session パラメータ追加（依存性注入）
    - セッション管理ロジックの抽象化

#### Phase 8-2（可視化機能のカテゴリ別分離）

12. **`src/analyze/visualization/__init__.py`** [作成]
    - 全プロット関数のエクスポート

13. **`src/analyze/visualization/performance.py`** [作成]
    - apply_df_style, plot_cumulative_returns

14. **`src/analyze/visualization/volatility.py`** [作成]
    - plot_vix_and_high_yield_spread, plot_vix_and_uncertainty_index

15. **`src/analyze/visualization/correlation.py`** [作成]
    - plot_rolling_correlation

16. **`src/analyze/visualization/beta.py`** [作成]
    - plot_rolling_beta

17. **`src/analyze/visualization/currency.py`** [作成]
    - plot_dollar_index_and_metals

#### Phase 8-3（専門クラスの移動）

18. **`src/market/base_collector.py`** [作成]
    - DataCollector 抽象基底クラス

19. **`src/market/tsa.py`** [作成]
    - TSAPassengerDataCollector クラス（DataCollector 継承）

20. **`src/market/bloomberg.py`** [作成]
    - BloombergDataProcessor クラス（DataCollector 継承）

21. **`src/analyze/currency.py`** [作成]
    - DollarsIndexAndMetalsAnalyzer クラス

#### Phase 8-4（高度な分析機能のクラス化）

22. **`src/analyze/statistics/base.py`** [作成]
    - StatisticalAnalyzer 抽象基底クラス

23. **`src/analyze/statistics/correlation.py`** [作成]
    - RollingCorrelationAnalyzer クラス

24. **`src/analyze/statistics/beta.py`** [作成]
    - RollingBetaAnalyzer クラス
    - KalmanBetaAnalyzer クラス

#### Phase 8-5（レガシーコード削除）

25. **`src_sample/market_report_utils.py`** [削除]
    - 全機能を適切なモジュールに移行後、削除

## リスク評価

### Phase 1-7 のリスク

| リスク | 影響度 | 確率 | 対策 |
|-------|--------|------|------|
| 既存コードの破壊 | 低 | 低 | 段階的移行、各Phase後にテスト実行 |
| 環境変数の読み込みタイミング変更 | 低 | 中 | 遅延読み込み（lazy loading）を実装 |
| テストの失敗 | 中 | 低 | Phase 1 で包括的なテスト作成 |
| `news/utils/logging_config.py` の統合時の機能差分 | 中 | 中 | 詳細な比較分析を実施 |
| ノートブック内のFREDコード移行 | 低 | 低 | `HistoricalCache` のAPIは類似、移行は容易 |

### Phase 8 のリスク

| リスク | 影響度 | 確率 | 対策 |
|-------|--------|------|------|
| ノートブック内での market_report_utils 使用 | 中 | 中 | Market-Report3.ipynb を確認し、使用箇所を新APIに置き換え |
| Strategy パターン導入の複雑性 | 中 | 低 | HttpSessionProtocol を明確に定義、既存テストで互換性確認 |
| 3クラス分離による依存関係の複雑化 | 中 | 低 | 依存性注入を使用、モックで各クラスを独立テスト |
| 可視化モジュールの分割による import 変更 | 低 | 中 | `__init__.py` で統一インポートを提供、後方互換性維持 |
| pykalman 依存関係 | 低 | 中 | KalmanBetaAnalyzer で pykalman が必要、オプション依存として定義 |
| 抽象基底クラス導入による学習コスト | 低 | 低 | Docstring で使用例を明記、テストコードで具体例を提供 |
| パフォーマンス計算の互換性 | 低 | 低 | 既存の performance.py のテストを維持、新機能は追加テスト |

## 検証方法

### 各 Phase 終了後の検証

```bash
# 品質チェック
make check-all

# 単体テストのみ
make test-unit

# 型チェックのみ
make typecheck
```

### 最終検証（Phase 7 完了後）

```bash
# 全テスト実行
make test

# configuration パッケージの使用箇所がないことを確認
grep -r "from configuration" src/
grep -r "import configuration" src/

# sample_data の使用箇所がないことを確認
grep -r "sample_data" src/
grep -r "FredDataLoader" src/ notebook/

# 期待される結果: 全てマッチなし
```

### 最終検証（Phase 8 完了後）

```bash
# 全テスト実行
make test

# market_report_utils の使用箇所がないことを確認
grep -r "market_report_utils" src/
grep -r "market_report_utils" notebook/

# 期待される結果: マッチなし

# Phase 8-1: HTTPセッション抽象化の確認
uv run python -c "from market.yfinance.session import HttpSessionProtocol, CurlCffiSession, StandardRequestsSession; print('Phase 8-1: OK')"
uv run python -c "from market.yfinance.fetcher import YFinanceFetcher; fetcher = YFinanceFetcher(); print('Phase 8-1: Fetcher OK')"

# Phase 8-2: 可視化機能のカテゴリ別分離の確認
uv run python -c "from analyze.visualization import plot_cumulative_returns, apply_df_style; print('Phase 8-2: performance OK')"
uv run python -c "from analyze.visualization.volatility import plot_vix_and_high_yield_spread; print('Phase 8-2: volatility OK')"
uv run python -c "from analyze.visualization.correlation import plot_rolling_correlation; print('Phase 8-2: correlation OK')"
uv run python -c "from analyze.visualization.beta import plot_rolling_beta; print('Phase 8-2: beta OK')"
uv run python -c "from analyze.visualization.currency import plot_dollar_index_and_metals; print('Phase 8-2: currency OK')"

# Phase 8-3: 専門クラスと抽象基底クラスの確認
uv run python -c "from market.base_collector import DataCollector; print('Phase 8-3: DataCollector OK')"
uv run python -c "from market.tsa import TSAPassengerDataCollector; print('Phase 8-3: TSA OK')"
uv run python -c "from market.bloomberg import BloombergDataProcessor; print('Phase 8-3: Bloomberg OK')"
uv run python -c "from analyze.currency import DollarsIndexAndMetalsAnalyzer; print('Phase 8-3: Currency OK')"

# Phase 8-4: 統計分析クラスの確認
uv run python -c "from analyze.statistics.base import StatisticalAnalyzer; print('Phase 8-4: base OK')"
uv run python -c "from analyze.statistics.correlation import RollingCorrelationAnalyzer; print('Phase 8-4: correlation OK')"
uv run python -c "from analyze.statistics.beta import RollingBetaAnalyzer, KalmanBetaAnalyzer; print('Phase 8-4: beta OK')"

# 期待される結果: 全て OK
```

## 後方互換性

- **Phase 3**: Deprecation 警告を追加（v0.2.0）
- **Phase 6**: 完全削除（v1.0.0）

移行期間を設けることで、既存コードへの影響を最小化します。

## 将来的な拡張計画

### Pydantic Settings への移行（Optional）

将来的に設定管理をより堅牢にする場合、pydantic-settings への移行を検討できます。現在の `settings.py` の設計は、この移行を容易にするように設計されています。

### 設定のバリデーション強化

環境変数の値に対するより詳細なバリデーションを追加できます（例: ログレベルの有効性チェック）。

## Phase 7: FRED レガシーコードの統合（影響: なし）

### 背景

`src/market/fred/sample_data.py` には `FredDataLoader` クラスが存在しますが、これは既存の `HistoricalCache` クラスと機能が重複しています。

| 機能 | `FredDataLoader` (レガシー) | `HistoricalCache` (モダン) |
|------|---------------------------|---------------------------|
| ストレージ | SQLite3 | JSON |
| 依存関係 | `configuration.file_path` | `utils_core.logging` |
| プリセット管理 | GitHub URL | ローカル JSON |
| ロギング | 標準 logging | structlog (utils_core) |

### 使用箇所

```
notebook/Market-Report2.ipynb
```

### タスク

- [ ] `notebook/Market-Report2.ipynb` を確認
  - [ ] `FredDataLoader` の使用を `HistoricalCache` に置き換え
  - [ ] または該当セルを削除（未使用の場合）
- [ ] `src/market/fred/sample_data.py` の削除
- [ ] 検証
  - [ ] `make check-all` が成功
  - [ ] grep で `sample_data` が見つからない
  - [ ] ノートブックが正常に動作する

**推定時間**: 30分

**依存**: Phase 1, 2 完了後に実施（`configuration` パッケージへの依存解消後）

---

## まとめ

このリファクタリングにより：

### Phase 1-7（configuration & FRED モジュール）

1. **設定管理が一元化**され、`utils_core/settings.py` が唯一の環境変数アクセスポイントとなります
2. **レガシーコードが削除**され、コードベースが整理されます
3. **重複実装が解消**され、保守性が向上します
4. **型安全性が向上**し、環境変数の誤用を防げます
5. **FREDモジュールが整理**され、モダンなアーキテクチャに統一されます

### Phase 8（market_report_utils モジュール - SOLID原則準拠）

6. **単一責任原則（SRP）の徹底**
   - PerformanceAnalyzer: パフォーマンス計算のみに専念
   - MarketDataProvider: データ取得のみに専念
   - PeriodCalculator: 日付計算のみに専念
   - 各可視化モジュール: 特定カテゴリのプロットのみに専念

7. **開放/閉鎖原則（OCP）の実現**
   - 新しいHTTP実装追加時、YFinanceFetcher は変更不要（Strategy パターン）
   - 新しいデータソース追加時、既存コレクターは変更不要（DataCollector 抽象基底クラス）
   - 新しい分析手法追加時、既存アナライザーは変更不要（StatisticalAnalyzer 抽象基底クラス）

8. **リスコフの置換原則（LSP）の適用**
   - 全てのデータコレクターが DataCollector インターフェースで交換可能
   - 全ての統計アナライザーが StatisticalAnalyzer インターフェースで交換可能

9. **依存性逆転原則（DIP）の適用**
   - YFinanceFetcher は HttpSessionProtocol（抽象）に依存
   - PerformanceAnalyzer は MarketDataProvider と PeriodCalculator に依存性注入

10. **可視化機能のカテゴリ別分離**
    - performance, volatility, correlation, beta, currency に分類
    - ファイル肥大化を防止（各100-200行程度）
    - `visualization/__init__.py` で統一インポート提供

11. **クラスベース設計による再利用性向上**
    - 分析パラメータをインスタンス変数で管理（状態管理）
    - 同じパラメータで複数データセットに適用可能

12. **curl_cffi によるパフォーマンス向上**が全体で利用可能になります

13. **structlog ロギング**が全モジュールで統一されます

14. **テスタビリティの大幅向上**
    - モックHTTPセッション注入でテスト容易
    - 各クラスが独立してテスト可能
    - パラメータ化テストが容易

### 実装推奨順序

#### 最優先（基盤整備）
1. **Phase 1-2**: 設定管理の一元化（最重要）
   - 全体の環境変数管理を統一
   - 推定時間: 1.5時間

#### 高優先度（SOLID原則準拠のコア機能）
2. **Phase 8-4, 8-5**: 専門クラスと分析機能の分離
   - 影響範囲が限定的で、SRP準拠
   - 抽象基底クラスの導入により拡張性向上
   - 推定時間: 5時間

3. **Phase 8-3**: 可視化機能のカテゴリ別分離
   - プロット関数の整理
   - 推定時間: 2時間

#### 中優先度（大規模リファクタリング）
4. **Phase 8-1**: Strategy パターン導入
   - YFinanceFetcher の大幅改修が必要
   - 推定時間: 2時間

5. **Phase 8-2**: 責務分離（3クラス化）
   - PerformanceAnalyzer の依存関係調整が必要
   - 推定時間: 2.5時間

#### 最終フェーズ（クリーンアップ）
6. **Phase 4, 5, 7, 8-6**: レガシーコードの削除
   - 全機能の移行完了後に実施
   - 推定時間: 2.5時間

**段階的移行の利点**:
- Phase 8-4, 8-5 を先に実施することで、新しいアーキテクチャパターンを確立
- Phase 8-1, 8-2 で既存パターンを参照しながら実装可能
- 各Phaseが独立しており、並行開発も可能

**総推定時間**: 約4時間（Phase 7 を含む）

## Phase 8: `src_sample/market_report_utils.py` の統合（影響: なし）

### 背景

`src_sample/market_report_utils.py` には多数のクラスと関数が含まれており、一部は `src/analyze/reporting/performance.py` と機能が重複しています。モダンなアーキテクチャへの統合が必要です。

### 機能比較マトリクス

#### 1. パフォーマンス計算（重複あり）

| 機能 | `market_report_utils.py` | `performance.py` |
|------|--------------------------|------------------|
| 期間定義 | YTD, MTD, Last Tuesday, Previous Day | 1D, WoW, 1W, MTD, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y |
| 計算方法 | 独自実装（対数リターン） | pct_change（標準API） |
| グループ定義 | クラス内ハードコード | symbols.yaml（外部設定） |
| ロギング | なし | structlog |

#### 2. データ取得（アプローチが異なる）

| 機能 | `market_report_utils.py` | `performance.py` |
|------|--------------------------|------------------|
| yfinance呼び出し | curl_cffi使用（高速） | YFinanceFetcher（標準） |
| セッション管理 | curl_cffi.Session | yfinance デフォルト |

#### 3. 固有機能（market_report_utils.py のみ）

| カテゴリ | 機能 |
|----------|------|
| **可視化** | apply_df_style, _plot_lines, plot_sp500_indices, plot_mag7_sox, plot_sector_performance, plot_vix_and_high_yield_spread, plot_vix_and_uncertainty_index, plot_rolling_correlation, plot_rolling_beta, plot_us_dollar_index_and_metal_price |
| **データ収集** | TSAPassengerDataCollector（TSA旅客数スクレイピング）, BloombergDataProcessor（Bloombergデータ処理） |
| **分析** | rolling_correlation, calculate_kalman_beta, rolling_beta, DollarsIndexAndMetalsAnalyzer（ドル指数・金属価格分析） |
| **その他** | get_eps_historical_data（実績EPSデータ取得） |

### 統合戦略

#### Phase 8-1: YFinanceFetcher の拡張（Strategy パターン導入）（影響: 中）

**SOLID原則**: 単一責任原則（SRP）、開放/閉鎖原則（OCP）、依存性逆転原則（DIP）に準拠

- [ ] `src/market/yfinance/session.py` を作成（HTTPセッション抽象化）
  - [ ] `HttpSessionProtocol` プロトコル定義
    ```python
    class HttpSessionProtocol(Protocol):
        def get(self, url: str, **kwargs) -> Any: ...
        def close(self) -> None: ...
    ```
  - [ ] `CurlCffiSession` 実装（高速版）
    - curl_cffi.Session を使用
    - impersonate パラメータ設定
  - [ ] `StandardRequestsSession` 実装（標準版）
    - requests.Session を使用
- [ ] `src/market/yfinance/fetcher.py` を修正
  - [ ] コンストラクタに `http_session: HttpSessionProtocol | None` 追加
  - [ ] デフォルトは `CurlCffiSession()` を使用（高速化）
  - [ ] セッション管理ロジックを抽象化に委譲
- [ ] テスト追加
  - [ ] `tests/market/unit/test_yfinance_session.py` 作成
    - CurlCffiSession のテスト
    - StandardRequestsSession のテスト
    - モックHTTPセッションでのテスト
  - [ ] `tests/market/unit/test_yfinance_fetcher.py` 修正
    - 既存テストの互換性確認
    - セッション注入のテスト
- [ ] 検証
  - [ ] `make test-unit` が成功
  - [ ] パフォーマンス比較（curl_cffi vs requests）

**メリット**:
- 新しいHTTP実装（httpx, aiohttp等）追加時、YFinanceFetcher は変更不要（OCP準拠）
- モックHTTPセッション注入でテスト容易（DIP準拠）
- YFinanceFetcher は「データ取得」のみに専念（SRP準拠）

**推定時間**: 2時間

#### Phase 8-2: 可視化機能の分離（カテゴリ別モジュール化）（影響: なし）

**SOLID原則**: 単一責任原則（SRP）、開放/閉鎖原則（OCP）に準拠

- [ ] `src/analyze/visualization/` ディレクトリを作成
- [ ] `src/analyze/visualization/performance.py` を作成
  - [ ] `apply_df_style(df: DataFrame) -> Styler`
    - DataFrameスタイル適用（バー、色分け）
  - [ ] `plot_cumulative_returns(price_df: DataFrame, symbols: list[str], title: str) -> Figure`
    - 累積リターンプロット（汎用）
    - plotly 使用
  - [ ] NumPy形式 Docstring
- [ ] `src/analyze/visualization/volatility.py` を作成
  - [ ] `plot_vix_and_high_yield_spread(df: DataFrame) -> Figure`
    - VIX とハイイールドスプレッドの2軸プロット
  - [ ] `plot_vix_and_uncertainty_index(df: DataFrame, ema_span: int = 30) -> Figure`
    - VIX と不確実性指数の2軸プロット
  - [ ] NumPy形式 Docstring
- [ ] `src/analyze/visualization/correlation.py` を作成
  - [ ] `plot_rolling_correlation(df_corr: DataFrame, ticker: str, target_index: str) -> Figure`
    - ローリング相関係数の推移プロット
  - [ ] NumPy形式 Docstring
- [ ] `src/analyze/visualization/beta.py` を作成（Phase 8-5 で使用）
  - [ ] `plot_rolling_beta(df_beta: DataFrame, tickers: list[str], target_index: str, ...) -> Figure`
    - ローリングベータの推移プロット
  - [ ] NumPy形式 Docstring
- [ ] `src/analyze/visualization/currency.py` を作成
  - [ ] `plot_dollar_index_and_metals(df_cum_return: DataFrame) -> Figure`
    - ドル指数と金属価格の2軸プロット
  - [ ] NumPy形式 Docstring
- [ ] `src/analyze/visualization/__init__.py` を作成
  - [ ] 全プロット関数をエクスポート（統一インポート提供）
  ```python
  from analyze.visualization.performance import plot_cumulative_returns, apply_df_style
  from analyze.visualization.volatility import plot_vix_and_high_yield_spread
  # ...
  ```
- [ ] テスト作成
  - [ ] `tests/analyze/unit/visualization/test_performance.py`
  - [ ] `tests/analyze/unit/visualization/test_volatility.py`
  - [ ] `tests/analyze/unit/visualization/test_correlation.py`
  - [ ] `tests/analyze/unit/visualization/test_currency.py`
  - [ ] 各プロット関数のテスト（Figureオブジェクト生成確認）
- [ ] 検証
  - [ ] `make test-unit` が成功

**メリット**:
- 各モジュールが特定カテゴリのプロットのみ担当（SRP準拠）
- 新しいプロット追加時、該当ファイルのみ修正（OCP準拠）
- ファイル肥大化を防止（各ファイル100-200行程度）
- カテゴリ別にインポート可能で可読性向上

**推定時間**: 2時間

#### Phase 8-3: 専門クラスの移動（抽象基底クラス導入）（影響: なし）

**SOLID原則**: 単一責任原則（SRP）、開放/閉鎖原則（OCP）、リスコフの置換原則（LSP）に準拠

- [ ] `src/market/base_collector.py` を作成（抽象基底クラス）
  - [ ] `DataCollector` 抽象基底クラス定義
    ```python
    class DataCollector(ABC):
        @abstractmethod
        def fetch(self, **kwargs) -> pd.DataFrame: ...

        @abstractmethod
        def validate(self, df: pd.DataFrame) -> bool: ...
    ```
  - [ ] NumPy形式 Docstring
- [ ] `src/market/tsa.py` を作成
  - [ ] `TSAPassengerDataCollector` クラスを移動（DataCollector 継承）
    - `fetch(start_date: str, end_date: str) -> DataFrame` 実装
    - `validate(df: DataFrame) -> bool` 実装
    - ウェブスクレイピングロジック
  - [ ] structlog ロギングに変更
  - [ ] NumPy形式 Docstring
- [ ] `src/market/bloomberg.py` を作成
  - [ ] `BloombergDataProcessor` クラスを移動（DataCollector 継承）
    - `fetch(symbols: list[str]) -> DataFrame` 実装
    - `validate(df: DataFrame) -> bool` 実装
    - Excelファイル読み込み、SQLite保存ロジック
  - [ ] structlog ロギングに変更
  - [ ] NumPy形式 Docstring
- [ ] `src/analyze/currency.py` を作成
  - [ ] `DollarsIndexAndMetalsAnalyzer` クラスを移動
    - FRED データと金属価格データの統合分析
    - 累積リターン計算
  - [ ] structlog ロギングに変更
  - [ ] NumPy形式 Docstring
- [ ] テスト作成
  - [ ] `tests/market/unit/test_base_collector.py`
    - DataCollector インターフェースのテスト
  - [ ] `tests/market/unit/test_tsa.py`
    - TSAPassengerDataCollector のテスト
    - モックHTTPレスポンスでのテスト
  - [ ] `tests/market/unit/test_bloomberg.py`
    - BloombergDataProcessor のテスト
    - モックExcelファイルでのテスト
  - [ ] `tests/analyze/unit/test_currency.py`
    - DollarsIndexAndMetalsAnalyzer のテスト
- [ ] 検証
  - [ ] `make test-unit` が成功

**メリット**:
- 全てのデータコレクターが同じインターフェースで交換可能（LSP準拠）
- 新しいデータソース追加が容易（OCP準拠）
- モックコレクターで統一的なテスト可能

**推定時間**: 2.5時間

#### Phase 8-4: 高度な分析機能の分離（クラスベース設計）（影響: なし）

**SOLID原則**: 単一責任原則（SRP）、開放/閉鎖原則（OCP）、リスコフの置換原則（LSP）に準拠

- [ ] `src/analyze/statistics/base.py` を作成（抽象基底クラス）
  - [ ] `StatisticalAnalyzer` 抽象基底クラス定義
    ```python
    class StatisticalAnalyzer(ABC):
        @abstractmethod
        def calculate(self, df: DataFrame, **kwargs) -> DataFrame: ...

        @abstractmethod
        def validate_input(self, df: DataFrame) -> bool: ...
    ```
  - [ ] NumPy形式 Docstring
- [ ] `src/analyze/statistics/correlation.py` を作成
  - [ ] `RollingCorrelationAnalyzer` クラス実装（StatisticalAnalyzer 継承）
    - `__init__(window: int = 252, min_periods: int = 30)`
      - ウィンドウパラメータを保持
    - `calculate(df: DataFrame, target_column: str) -> DataFrame`
      - ローリング相関係数計算ロジック（既存の rolling_correlation を移植）
    - `validate_input(df: DataFrame) -> bool`
      - 入力データ検証（Date, Ticker, value カラム確認）
  - [ ] structlog ロギング追加
  - [ ] NumPy形式 Docstring
- [ ] `src/analyze/statistics/beta.py` を作成
  - [ ] `RollingBetaAnalyzer` クラス実装（StatisticalAnalyzer 継承）
    - `__init__(window: int = 60, freq: Literal["W", "M"] = "M", window_years: Literal[3, 5] = 3)`
      - 分析パラメータを保持
    - `calculate(df: DataFrame, target_column: str) -> DataFrame`
      - ローリングベータ計算ロジック（既存の rolling_beta を移植）
    - `validate_input(df: DataFrame) -> bool`
      - 入力データ検証
  - [ ] `KalmanBetaAnalyzer` クラス実装（StatisticalAnalyzer 継承）
    - `calculate(df: DataFrame, target_column: str) -> DataFrame`
      - カルマンフィルタベータ推定ロジック（既存の calculate_kalman_beta を移植）
    - `validate_input(df: DataFrame) -> bool`
      - 入力データ検証
    - pykalman 依存関係の確認
  - [ ] structlog ロギング追加
  - [ ] NumPy形式 Docstring
- [ ] テスト作成
  - [ ] `tests/analyze/unit/statistics/test_base.py`
    - StatisticalAnalyzer インターフェースのテスト
  - [ ] `tests/analyze/unit/statistics/test_correlation.py`
    - RollingCorrelationAnalyzer のテスト
    - パラメータ化テスト（window, min_periods の組み合わせ）
  - [ ] `tests/analyze/unit/statistics/test_beta.py`
    - RollingBetaAnalyzer のテスト
    - KalmanBetaAnalyzer のテスト
    - パラメータ化テスト
- [ ] 検証
  - [ ] `make test-unit` が成功

**メリット**:
- 分析パラメータ（window, freq等）をインスタンス変数で管理（状態管理）
- 同じパラメータで複数データセットに適用可能（再利用性）
- モック化とパラメータ化テストが容易（テスタビリティ）
- 新しいベータ推定手法（例: EWMA Beta）を追加しやすい（OCP準拠）

**推定時間**: 2.5時間

#### Phase 8-5: `src_sample/market_report_utils.py` の削除（影響: なし）

- [ ] `src_sample/market_report_utils.py` の削除
- [ ] 検証
  - [ ] `make check-all` が成功
  - [ ] grep で `market_report_utils` が見つからない
  - [ ] `notebook/Market-Report3.ipynb` の動作確認（使用箇所があれば修正）

**推定時間**: 30分

### Phase 8 総推定時間

約 9.5時間（SOLID原則準拠のアーキテクチャ設計を含む）

**内訳**:
- Phase 8-1（Strategy パターン導入）: 2時間
- Phase 8-2（カテゴリ別モジュール化）: 2時間
- Phase 8-3（抽象基底クラス導入）: 2.5時間
- Phase 8-4（クラスベース設計）: 2.5時間
- Phase 8-5（レガシーコード削除）: 0.5時間

**注記**: `*_agent.py` とその参照元ファイル（`performance.py`, `currency.py` 等）は、他のモジュール・ワークフローで使用されているため、リファクタリング対象外としました。

### 移行マッピング表

#### 機能移動先

| 元の場所 | 機能 | 移動先 | 設計パターン |
|---------|------|--------|-------------|
| `MarketPerformanceAnalyzer.yf_download_with_curl` | curl_cffi ダウンロード | `CurlCffiSession` (新規クラス) | Strategy パターン |
| `apply_df_style` | スタイル適用 | `visualization/performance.py` | カテゴリ別分離 |
| `plot_cumulative_returns` | 累積リターンプロット | `visualization/performance.py` | カテゴリ別分離 |
| `plot_vix_and_high_yield_spread` | VIXプロット | `visualization/volatility.py` | カテゴリ別分離 |
| `plot_vix_and_uncertainty_index` | VIX不確実性プロット | `visualization/volatility.py` | カテゴリ別分離 |
| `plot_rolling_correlation` | 相関プロット | `visualization/correlation.py` | カテゴリ別分離 |
| `plot_rolling_beta` | ベータプロット | `visualization/beta.py` | カテゴリ別分離 |
| `plot_dollar_index_and_metals` | ドル指数プロット | `visualization/currency.py` | カテゴリ別分離 |
| `TSAPassengerDataCollector` | TSAデータ収集 | `market/tsa.py` (DataCollector継承) | 抽象基底クラス |
| `BloombergDataProcessor` | Bloombergデータ処理 | `market/bloomberg.py` (DataCollector継承) | 抽象基底クラス |
| `DollarsIndexAndMetalsAnalyzer` | ドル指数・金属分析 | `analyze/currency.py` | 単一クラス |
| `rolling_correlation` | 相関係数計算 | `RollingCorrelationAnalyzer` (新規クラス) | クラスベース設計 |
| `rolling_beta` | ローリングベータ計算 | `RollingBetaAnalyzer` (新規クラス) | クラスベース設計 |
| `calculate_kalman_beta` | カルマンベータ計算 | `KalmanBetaAnalyzer` (新規クラス) | クラスベース設計 |

### 依存関係

- **Phase 8-1**: 独立して実施可能
- **Phase 8-2, 8-3, 8-4**: 独立して並行実施可能
- **Phase 8-5**: Phase 8-1 〜 8-4 完了後に実施

### リスク評価

| リスク | 影響度 | 確率 | 対策 |
|-------|--------|------|------|
| ノートブック内での使用 | 中 | 中 | Market-Report3.ipynb を確認し、使用箇所を新APIに置き換え |
| curl_cffi の依存関係 | 低 | 低 | オプション機能として実装、デフォルトは既存実装 |
| プロット関数の動作確認 | 低 | 低 | 各関数で図の生成を確認するテストを作成 |
| pykalman 依存関係 | 低 | 中 | calculate_kalman_beta で pykalman が必要、オプション依存として定義 |

### 検証方法

```bash
# 全テスト実行
make test

# market_report_utils の使用箇所がないことを確認
grep -r "market_report_utils" src/
grep -r "market_report_utils" notebook/

# 期待される結果: 全てマッチなし
```

## Phase 9: その他のリファクタリング（SOLID原則準拠）（影響: 中）

### 背景

コードベース全体の調査により、以下の改善点が発見されました：

1. **ロギング設定の重複**（560行）: `news/utils/logging_config.py` と `utils_core/logging/config.py` が完全に同一
2. **設定ロジックの重複**: YAML読み込み処理が各関数で個別に実装
3. **型定義の分散**: 共通型が複数ファイルで重複定義
4. **エラーハンドリングの不統一**: エラークラスが複数ファイルに分散

**注記**: `*_agent.py` ファイルは他のモジュールやワークフローで使用されているため、リファクタリング対象外とします。

**総削減可能コード量**: 約710行

### タスク

#### Phase 9-1: ロギング設定の統一（影響: 中）

**SOLID原則**: 単一責任原則（SRP）、Don't Repeat Yourself（DRY）に準拠

- [ ] `src/news/utils/logging_config.py` を削除
  - [ ] `utils_core.logging` からのインポートに統一
- [ ] `src/news/` パッケージ内の全ファイル（25ファイル）を修正
  - [ ] `from news.utils.logging_config import get_logger` → `from utils_core.logging import get_logger` に変更
  - [ ] `from news.utils.logging_config import setup_logging` → `from utils_core.logging import setup_logging` に変更
- [ ] テスト修正
  - [ ] `tests/news/` 内のテストでインポートを修正
- [ ] 検証
  - [ ] `make test-unit` が成功
  - [ ] grep で `news.utils.logging_config` が見つからない

**メリット**:
- 560行の重複コード削除
- ロギング設定の一元管理（SRP準拠）
- 保守性向上

**推定時間**: 2時間

**削減コード量**: 560行

#### Phase 9-2: `analyze.config.loader` の改善（影響: 小）

**SOLID原則**: 単一責任原則（SRP）、Don't Repeat Yourself（DRY）に準拠

- [ ] `src/analyze/config/models.py` を作成（Pydantic モデル）
  - [ ] `SymbolsConfig` Pydantic モデル定義
    ```python
    class SymbolsConfig(BaseModel):
        """symbols.yaml の構造を定義するモデル."""

        indices: dict[str, list[str]]
        mag7: list[str]
        sectors: list[str]
        commodities: list[str]
        return_periods: dict[str, int | str]

        def get_symbols(
            self, group: str, subgroup: str | None = None
        ) -> list[str]:
            """シンボルリストを取得."""
            ...
    ```
- [ ] `src/analyze/config/loader.py` を修正
  - [ ] `_load_symbols_config()` 関数を作成（`@lru_cache` デコレーター）
    - YAML を一度だけ読み込み、SymbolsConfig インスタンスを返す
  - [ ] 既存関数を修正
    - `get_symbols()`: `_load_symbols_config()` を使用
    - `get_return_periods()`: `_load_symbols_config()` を使用
    - `get_symbol_group()`: `_load_symbols_config()` を使用
- [ ] テスト作成
  - [ ] `tests/analyze/unit/config/test_models.py`
    - SymbolsConfig のテスト
  - [ ] `tests/analyze/unit/config/test_loader.py` 修正
    - キャッシュ動作のテスト
- [ ] 検証
  - [ ] `make test-unit` が成功
  - [ ] パフォーマンス測定（YAML読み込み回数の削減）

**メリット**:
- ファイルI/Oの重複削減（キャッシュ）
- YAML構造の型安全性向上（Pydantic）
- パフォーマンス向上

**推定時間**: 3時間

**削減コード量**: 約50行

#### Phase 9-3: `news` パッケージの設定クラス統合（影響: 小）

**SOLID原則**: 単一責任原則（SRP）に準拠

- [ ] `src/news/config/models.py` を修正
  - [ ] `loader.py` の YAML ロード処理を統合
  - [ ] `workflow.py` のワークフロー設定を統合
  - [ ] `errors.py` の例外クラスを統合
- [ ] 以下のファイルを削除
  - [ ] `src/news/config/loader.py`
  - [ ] `src/news/config/workflow.py`
  - [ ] `src/news/config/errors.py`
- [ ] `src/news/config/__init__.py` を修正
  - [ ] `models.py` から必要なクラスをエクスポート
- [ ] テスト修正
  - [ ] `tests/news/unit/config/` 内のテストでインポートを修正
- [ ] 検証
  - [ ] `make test-unit` が成功

**メリット**:
- 設定関連ロジックの一元管理（SRP準拠）
- 100行の重複コード削除

**推定時間**: 2時間

**削減コード量**: 約100行

#### Phase 9-4: `factor` パッケージの型定義統合（影響: 小）

**SOLID原則**: Don't Repeat Yourself（DRY）に準拠

- [ ] `src/factor/types.py` を作成（共通型定義）
  - [ ] 以下の共通型を定義
    - `FactorResult`: ファクター計算結果
    - `FactorMetadata`: ファクターのメタデータ
    - `FactorScore`: ファクタースコア
  - [ ] NumPy形式 Docstring
- [ ] 各サブパッケージの `types.py` を修正
  - [ ] `src/factor/factors/value/types.py`
    - 共通型を `factor.types` からインポート
    - Value ファクター固有の型のみ定義
  - [ ] `src/factor/factors/quality/types.py`
    - 共通型を `factor.types` からインポート
    - Quality ファクター固有の型のみ定義
  - [ ] `src/factor/factors/price/types.py`
    - 共通型を `factor.types` からインポート
    - Price ファクター固有の型のみ定義
- [ ] テスト修正
  - [ ] `tests/factor/` 内のテストでインポートを修正
- [ ] 検証
  - [ ] `make test-unit` が成功

**メリット**:
- 型定義の一元管理（DRY準拠）
- 型の不整合防止

**推定時間**: 2時間

#### Phase 9-5: `market` パッケージのエラーハンドリング統一（影響: 小）

**SOLID原則**: 単一責任原則（SRP）に準拠

- [ ] `src/market/errors.py` を修正
  - [ ] 全エラークラスを集約
    ```python
    class MarketError(Exception):
        """Base exception for market package."""
        pass

    class YFinanceError(MarketError):
        """YFinance specific error."""
        pass

    class BloombergError(MarketError):
        """Bloomberg specific error."""
        pass

    class CacheError(MarketError):
        """Cache related error."""
        pass

    class ExportError(MarketError):
        """Export related error."""
        pass
    ```
  - [ ] NumPy形式 Docstring
- [ ] 以下のファイルを削除
  - [ ] `src/market/yfinance/errors.py`
  - [ ] `src/market/bloomberg/errors.py`
- [ ] 各モジュールのインポートを修正
  - [ ] `from market.errors import YFinanceError` に統一
- [ ] テスト修正
  - [ ] `tests/market/` 内のテストでインポートを修正
- [ ] 検証
  - [ ] `make test-unit` が成功

**メリット**:
- エラークラスの一元管理（SRP準拠）
- 継承階層の明確化
- インポートパスの統一

**推定時間**: 1時間

#### Phase 9-6: `strategy` パッケージの Protocol 活用（影響: 小）

**SOLID原則**: リスコフの置換原則（LSP）、依存性逆転原則（DIP）に準拠

- [ ] `src/strategy/providers/protocol.py` を確認
  - [ ] `DataProviderProtocol` の定義を確認
- [ ] 実装クラスが Protocol に準拠していることを確認
  - [ ] `src/strategy/providers/` 配下の全実装クラスを確認
  - [ ] 必要に応じて Protocol メソッドを実装
- [ ] 型ヒントで Protocol を使用
  - [ ] 関数シグネチャで `DataProviderProtocol` を使用
  ```python
  def calculate_strategy(
      provider: DataProviderProtocol,  # Protocol に依存
      ...
  ) -> DataFrame:
      ...
  ```
- [ ] テスト作成
  - [ ] モック DataProviderProtocol でテスト
- [ ] 検証
  - [ ] `make typecheck` が成功

**メリット**:
- 型チェックの恩恵（LSP準拠）
- 抽象に依存（DIP準拠）
- テスタビリティ向上

**推定時間**: 1時間

#### Phase 9-7: テストファイルの配置修正（影響: なし）

**SOLID原則**: プロジェクト構造の一貫性

- [ ] 以下のテストファイルを移動
  - [ ] `tests/analyze/unit/test_technical.py` → `tests/analyze/unit/technical/test_technical.py`
- [ ] テストインポートを修正
- [ ] 検証
  - [ ] `make test` が成功

**メリット**:
- パッケージ構造とテスト構造の一致
- テストの可読性向上

**推定時間**: 15分

### Phase 9 総推定時間

約 11時間

**内訳**:
- Phase 9-1（ロギング統一）: 2時間
- Phase 9-2（設定ロジック改善）: 3時間
- Phase 9-3（news 設定統合）: 2時間
- Phase 9-4（factor 型定義統合）: 2時間
- Phase 9-5（market エラー統一）: 1時間
- Phase 9-6（strategy Protocol 活用）: 1時間
- Phase 9-7（テストファイル配置）: 15分

**総削減コード量**: 約710行

**注記**: `*_agent.py` ファイルは他のモジュール・ワークフローで使用されているため、リファクタリング対象外としました。

### 依存関係

- **Phase 9-1**: 独立して実施可能
- **Phase 9-2, 9-3, 9-4, 9-5, 9-6**: 独立して並行実施可能
- **Phase 9-7**: 最初に実施（影響範囲が小さく、他Phaseの基盤）

### リスク評価

| リスク | 影響度 | 確率 | 対策 |
|-------|--------|------|------|
| ロギング統一時のインポートミス | 低 | 中 | grep で全ファイルを確認、テストで検証 |
| 設定ロジック変更の互換性 | 低 | 低 | 既存テストで互換性を確認 |
| 型定義統合時の循環インポート | 低 | 中 | インポート順序を調整、`TYPE_CHECKING` を使用 |

### 検証方法

```bash
# 全テスト実行
make test

# ロギング統一の確認
grep -r "news.utils.logging_config" src/
# 期待される結果: マッチなし

# 設定ロジック改善の確認
uv run python -c "from analyze.config.models import SymbolsConfig; print('OK')"
uv run python -c "from analyze.config.loader import get_symbols; symbols = get_symbols('mag7'); print(symbols)"

# 型定義統合の確認
uv run python -c "from factor.types import FactorResult, FactorMetadata; print('OK')"

# エラーハンドリング統一の確認
uv run python -c "from market.errors import MarketError, YFinanceError, BloombergError; print('OK')"

# 期待される結果: 全て OK
```

---

**総推定時間（Phase 1 〜 Phase 9）**: 約25時間

**内訳**:
- Phase 1-7（configuration & FRED モジュール）: 約4時間
- Phase 8（market_report_utils モジュール - SOLID原則準拠）: 約9.5時間
- Phase 9（その他のリファクタリング - SOLID原則準拠）: 約11時間

**総削減コード量**: 約710行

**注記**: `*_agent.py` とその参照元ファイル（`performance.py`, `currency.py`, `interest_rate.py`, `upcoming_events.py` 等）は、他のモジュール・ワークフローで使用されているため、リファクタリング対象外としました。
