# コード分析レポート

**分析日時**: 2026-01-14
**対象**: `/Users/yukihata/Desktop/finance/src_sample/`
**分析モード**: --code, --arch, --security, --perf
**分析深度**: --think-hard

---

## サマリー

| 項目 | 値 |
|------|-----|
| 総ファイル数 | 27 |
| 総行数 | 16,126 |
| 関数数 | 142 |
| クラス数 | 10 |

---

## スコア (0-100)

| 観点 | スコア | 評価 |
|------|--------|------|
| コード品質 | 62 | 中程度 |
| アーキテクチャ | 55 | 中程度 |
| セキュリティ | 48 | **要改善** |
| パフォーマンス | 58 | 中程度 |
| **総合** | **56** | 中程度 |

---

## 1. コード品質分析

### 1.1 複雑度分析

| 指標 | 値 |
|------|-----|
| 平均複雑度 | 8.5 |
| 最大複雑度 | 32 |
| 最大複雑度関数 | `BlpapiCustom.get_historical_data` (bloomberg_utils.py) |

#### 高複雑度関数一覧

| ファイル | 関数 | 複雑度 | 推奨対応 |
|----------|------|--------|----------|
| bloomberg_utils.py | `BlpapiCustom.get_historical_data` | 32 | データ取得・整形・エラー処理を分離 |
| bloomberg_utils.py | `BlpapiCustom.get_financial_data` | 28 | チャンク処理とデータ変換を分離 |
| market_report_utils.py | `MarketPerformanceAnalyzer` methods | 25 | 計算ロジックを小さな関数に分割 |
| weekly_report_generator.py | `generate_draft` | 22 | セクション生成を個別メソッドに分離 |
| make_factor.py | `calculate_rolling_betas` | 20 | ファクター生成部分を別関数に抽出 |

### 1.2 重複コード分析

**重複率**: 15.3%

| パターン | 対象ファイル | 行数 | 推奨対応 |
|----------|--------------|------|----------|
| SQLite接続・クエリ実行・クローズ処理 | database_utils.py, fred_database_utils.py, data_prepare.py, init_databases.py | ~120 | 共通のDBコンテキストマネージャを作成 |
| pandas DataFrame取得→ピボット→計算 | weekly_report_generator.py, weekly_insights.py, market_report_utils.py | ~80 | 共通のメトリクス計算ユーティリティを作成 |
| yfinance/FRED APIのエラーハンドリング | calendar_utils.py, weekly_insights.py, market_report_utils.py | ~60 | 共通のリトライデコレータを作成 |

### 1.3 命名規則分析

**準拠率**: 78%

#### 命名規則違反

| ファイル | 問題 | 現状 | 推奨 |
|----------|------|------|------|
| ROIC_make_data_files_ver2.py | ファイル名がsnake_caseでない | `ROIC_make_data_files_ver2.py` | `roic_data_processor.py` |
| implement_FS_BBG_formulas_utils.py | ファイル名が冗長 | - | `factset_bloomberg_formulas.py` |
| bloomberg_utils.py | クラス名が不明瞭 | `BlpapiCustom` | `BloombergApiClient` |

#### 許容される略語

- `df` (DataFrame)
- `conn` (connection)
- `ret` (return)

### 1.4 型ヒントカバレッジ

| 指標 | 値 |
|------|-----|
| 現在のカバレッジ | 72% |
| 目標 | 90% |

#### 完全カバレッジのファイル
- calculate_performance_metrics.py
- data_check_utils.py
- edgar_utils.py
- validate_data.py

#### 部分カバレッジのファイル

| ファイル | カバレッジ | 不足箇所 |
|----------|------------|----------|
| bloomberg_utils.py | 65% | 内部メソッドの戻り値型 |
| market_report_utils.py | 60% | 辞書の詳細型(TypedDict未使用) |
| weekly_insights.py | 55% | コールバック関数の型 |
| google_drive_utils.py | 40% | serviceオブジェクトの型が不明 |
| init_databases.py | 30% | 関数引数に型なし |

### 1.5 Docstringカバレッジ

| 指標 | 値 |
|------|-----|
| 現在のカバレッジ | 68% |
| 目標 | 80% |
| スタイル | Google/NumPy混在 |

#### 良好なDocstringのファイル
- calendar_utils.py
- data_check_utils.py
- fred_database_utils.py
- weekly_report_generator.py

#### Docstring不足のファイル

| ファイル | 不足数 | 例 |
|----------|--------|-----|
| bloomberg_utils.py | 8 | `_handle_security_error`, `_parse_field_data` |
| google_drive_utils.py | 2 | - |
| init_databases.py | 1 | - |
| make_financial_factors.py | 全て | 空ファイル |

---

## 2. アーキテクチャ分析

### 2.1 レイヤー構造

**評価**: 中

#### 問題点
- 明確なレイヤー分離がない（フラット構造）
- ビジネスロジックとデータアクセスが混在
- ユーティリティと分析ロジックの境界が曖昧

#### 推奨構造

```
src_sample/
├── core/                    # データソースクライアント
│   ├── bloomberg/
│   │   └── bloomberg_utils.py
│   ├── factset/
│   │   └── factset_utils.py
│   └── fred/
│       └── fred_database_utils.py
├── analysis/                # 分析ロジック
│   ├── make_factor.py
│   ├── roic_analysis.py
│   └── us_treasury.py
├── utils/                   # ユーティリティ
│   ├── database_utils.py
│   ├── data_check_utils.py
│   └── validate_data.py
└── reports/                 # レポート生成
    ├── weekly_report_generator.py
    ├── market_report_utils.py
    └── weekly_insights.py
```

### 2.2 依存関係分析

**循環インポート**: なし

#### 問題のある依存関係

| 依存元 | 依存先 | 問題 |
|--------|--------|------|
| roic_analysis.py | ROIC_make_data_files_ver2.py | 相対インポートパスが不安定 |
| make_factor.py | us_treasury.py | 同一ディレクトリ内の直接インポート |
| weekly_report_generator.py | 複数モジュール | sys.path操作によるインポート |

#### 外部依存関係

**ヘビー（全体で使用）**
- pandas (全27ファイル)
- yfinance (8ファイル)
- openpyxl (2ファイル)
- selenium (2ファイル)
- blpapi (1ファイル, 専用)

**モデレート**
- numpy (15ファイル)
- matplotlib (4ファイル)
- statsmodels (2ファイル)
- sklearn (2ファイル)

**オプショナル**
- pykalman (1ファイル, try/except)
- polars (1ファイル)

### 2.3 モジュール結合度

#### 高結合度モジュール

| モジュール | Fan-In | Fan-Out | 不安定度 | 推奨 |
|------------|--------|---------|----------|------|
| weekly_report_generator.py | 0 | 5 | 1.0 | 依存注入パターンの適用 |
| bloomberg_utils.py | 2 | 0 | 0.0 | 安定したコアモジュール（維持） |

#### 低結合度モジュール（良好）
- validate_data.py
- ddg_search.py
- edgar_utils.py

### 2.4 設計パターン検出

#### 検出されたパターン

| パターン | ファイル | 説明 |
|----------|----------|------|
| Factory風 | bloomberg_utils.py | チャンク処理でのデータ分割 |
| Strategy風 | roic_analysis.py | 複数のリターン計算方法 |
| Facade | weekly_report_generator.py | 複数データソースの統合API |

#### 導入推奨パターン

| パターン | 対象 | メリット |
|----------|------|----------|
| Repository | database_utils.py系 | データアクセスの抽象化 |
| Dependency Injection | クラス全般 | テスタビリティ向上 |

---

## 3. セキュリティ分析

### 3.1 SQLインジェクション

**リスクレベル**: HIGH

| ID | 重大度 | ファイル | 行 | 説明 | コード例 |
|----|--------|----------|-----|------|----------|
| SEC-001 | **HIGH** | database_utils.py | 複数箇所 | f-stringでテーブル名を直接埋め込み | `f"DROP TABLE IF EXISTS {table_name}"` |
| SEC-002 | MEDIUM | fred_database_utils.py | 165, 265 | シリーズIDをf-stringで直接埋め込み | `f"SELECT MAX(date) FROM \"{series_id}\""` |
| SEC-003 | MEDIUM | verify_bloomberg_utils.py | 102 | テーブル名のパラメータ化なし | `f"SELECT * FROM {table_name}"` |

**緩和策**: テーブル名のホワイトリスト検証（一部実装済み）、正規表現による検証（fred_database_utils.py:73-79で実装済み）

### 3.2 認証情報の露出

**リスクレベル**: MEDIUM

| ID | 重大度 | ファイル | 行 | 説明 | ステータス |
|----|--------|----------|-----|------|------------|
| SEC-004 | MEDIUM | fred_database_utils.py | 23 | APIキーを環境変数から取得 | **MITIGATED** |
| SEC-005 | LOW | google_drive_utils.py | 84-92 | OAuth認証情報ファイルのハードコードパス | 要対応 |
| SEC-006 | LOW | calendar_utils.py | 32 | APIキー取得は環境変数 | **MITIGATED** |

### 3.3 入力検証

**リスクレベル**: MEDIUM

| ID | 重大度 | ファイル | 行 | 説明 | 推奨対応 |
|----|--------|----------|-----|------|----------|
| SEC-007 | MEDIUM | ddg_search.py | 15-39 | ユーザー入力のクエリ文字列の検証なし | サニタイゼーション追加 |
| SEC-008 | LOW | bloomberg_utils.py | - | ティッカーシンボルの形式検証なし | 正規表現によるバリデーション |
| SEC-009 | LOW | google_drive_utils.py | 37 | フォルダ名のサニタイゼーションなし | 特殊文字のエスケープ |

### 3.4 その他

| ID | 重大度 | ファイル | 説明 | ステータス |
|----|--------|----------|------|------------|
| SEC-010 | LOW | weekly_insights.py:72 | User-Agentのハードコード | 設定可能にする |
| SEC-011 | INFO | etf_dot_com.py | Seleniumのヘッドレス設定 | **OK** |

---

## 4. パフォーマンス分析

### 4.1 アルゴリズム複雑度

**O(n²)以上の処理**: 3件

| ID | 重大度 | ファイル | 関数 | 複雑度 | 説明 | 推奨対応 |
|----|--------|----------|------|--------|------|----------|
| PERF-001 | **HIGH** | calculate_performance_metrics.py | `calculate_active_returns_parallel` | O(n*m) | 全リターン列に対してループ内でピボット変換 | ベクトル化版を優先使用 |
| PERF-002 | MEDIUM | make_factor.py | `calculate_rolling_betas` | O(n*w) | ローリングウィンドウ内で毎回PCAを実行 | インクリメンタルPCAの検討 |
| PERF-003 | MEDIUM | weekly_insights.py | `_update_valuation_data` | O(n) | 各ティッカーに対して個別API呼び出し | バッチ処理は実装済み |

### 4.2 メモリ効率

| ID | 重大度 | ファイル | 行 | 説明 | 推奨対応 |
|----|--------|----------|-----|------|----------|
| PERF-004 | MEDIUM | calculate_performance_metrics.py | 93 | 全データをコピーしてから処理 | 必要なカラムのみコピー |
| PERF-005 | MEDIUM | bloomberg_utils.py | - | 大量データの一括メモリ保持 | ジェネレータパターンの活用 |
| PERF-006 | LOW | data_prepare.py | 37-40 | 全CSVを一度にメモリ読み込み | chunkサイズ指定の検討 |

### 4.3 I/O操作

**N+1パターン**: 2件

| ID | 重大度 | ファイル | 関数 | 行 | 説明 | 推奨対応 |
|----|--------|----------|------|-----|------|----------|
| PERF-007 | **HIGH** | weekly_insights.py | `_update_valuation_data` | 171-199 | 各ティッカーに個別API呼び出し | yf.downloadでバッチ取得 |
| PERF-008 | MEDIUM | calendar_utils.py | `get_upcoming_earnings` | 179-226 | 各ティッカーに個別API呼び出し | バッチサイズの最適化 |
| PERF-009 | LOW | fred_database_utils.py | `load_data_from_database` | - | 各シリーズIDに個別クエリ | UNION ALLクエリで一括取得 |

### 4.4 キャッシング機会

**検出数**: 5件

| ID | ファイル | 関数 | 推奨対応 |
|----|----------|------|----------|
| PERF-010 | weekly_report_generator.py | `_calculate_metrics` | `@functools.lru_cache` の適用 |
| PERF-011 | market_report_utils.py | - | ディスクキャッシュ(`joblib.Memory`)の検討 |
| PERF-012 | bloomberg_utils.py | - | Redis/メモリキャッシュの検討 |

### 4.5 並列処理

#### 実装済み

| ファイル | 方式 | ステータス |
|----------|------|------------|
| calculate_performance_metrics.py | ProcessPoolExecutor | 適切に実装 |
| path_base_bootstrap.py | ProcessPoolExecutor | 適切に実装 |

#### 導入機会

| ファイル | 関数 | 推奨対応 |
|----------|------|----------|
| weekly_insights.py | `_update_valuation_data` | ThreadPoolExecutorでAPI呼び出しを並列化 |
| calendar_utils.py | `get_upcoming_earnings` | concurrent.futuresでバッチ並列化 |

---

## 5. 発見事項サマリー

### Critical (1件)

| ID | カテゴリ | ファイル | 説明 | 推奨対応 |
|----|----------|----------|------|----------|
| ANA-001 | セキュリティ | database_utils.py | SQLインジェクションの潜在的リスク | ホワイトリスト検証の徹底とパラメータ化 |

### High (3件)

| ID | カテゴリ | ファイル | 説明 | 推奨対応 |
|----|----------|----------|------|----------|
| ANA-002 | コード品質 | bloomberg_utils.py | 単一関数の複雑度が32を超過 | 責務分離によるリファクタリング |
| ANA-003 | パフォーマンス | weekly_insights.py | N+1クエリパターン | バッチ処理とキャッシュの活用 |
| ANA-004 | アーキテクチャ | 全体 | レイヤー構造の欠如 | core/analysis/utils/reportsへの分離 |

### Medium (5件)

| ID | カテゴリ | ファイル | 説明 | 推奨対応 |
|----|----------|----------|------|----------|
| ANA-005 | コード品質 | 複数 | 重複コード（DB接続処理） | 共通ユーティリティの抽出 |
| ANA-006 | コード品質 | 複数 | 型ヒントカバレッジ不足（72%） | TypedDict追加 |
| ANA-007 | セキュリティ | google_drive_utils.py | 認証ファイルパスのハードコード | 設定ファイル化または環境変数化 |
| ANA-008 | パフォーマンス | make_factor.py | ローリングウィンドウ内での重い計算 | インクリメンタルアルゴリズムの検討 |
| ANA-009 | コード品質 | make_financial_factors.py | 空ファイル（14行、実装なし） | 削除または実装 |

### Low (3件)

| ID | カテゴリ | ファイル | 説明 | 推奨対応 |
|----|----------|----------|------|----------|
| ANA-010 | コード品質 | ROIC_make_data_files_ver2.py | ファイル名がsnake_caseでない | roic_data_processor.pyに改名 |
| ANA-011 | コード品質 | 複数 | Docstringスタイルの不統一 | NumPy Styleに統一 |
| ANA-012 | パフォーマンス | data_prepare.py | 全データの一括メモリ読み込み | チャンク読み込みの検討 |

---

## 6. 改善ロードマップ

### 短期（1週間以内）- HIGH優先度

| タスク | 対象ファイル | 工数 | 期待効果 |
|--------|--------------|------|----------|
| SQLインジェクション対策の強化 | database_utils.py, fred_database_utils.py | 2時間 | セキュリティリスク軽減 |
| 空ファイルの削除または実装 | make_financial_factors.py | 30分 | コードベースのクリーンアップ |
| 高複雑度関数の分割 | bloomberg_utils.py | 4時間 | 保守性向上 |

### 中期（1ヶ月以内）- MEDIUM優先度

| タスク | 説明 | 工数 | 期待効果 |
|--------|------|------|----------|
| DB接続処理の共通化 | コンテキストマネージャの作成 | 1日 | コード重複15%削減 |
| 型ヒントカバレッジ向上 | TypedDictの導入、戻り値型の追加 | 2日 | 静的解析精度向上（目標90%） |
| N+1パターンの解消 | weekly_insights.py, calendar_utils.py | 1日 | API呼び出し回数50%削減 |
| キャッシュ機構の導入 | yfinance/FRED API結果のキャッシュ | 1日 | レスポンス時間改善 |

### 長期（3ヶ月以内）- LOW優先度

| タスク | 説明 | 工数 | 期待効果 |
|--------|------|------|----------|
| ディレクトリ構造の再編成 | core/analysis/utils/reportsへの分離 | 1週間 | 保守性・拡張性向上 |
| 依存性注入パターンの導入 | テスタビリティ向上のためのDI | 1週間 | テストカバレッジ向上可能に |
| Docstringスタイルの統一 | NumPy Styleへの統一 | 2日 | ドキュメント品質向上 |
| 命名規則の統一 | ファイル名・クラス名の改善 | 1日 | コードの一貫性向上 |

---

## 7. メトリクス詳細

### ファイルサイズ

#### 最大ファイル

| ファイル | 行数 |
|----------|------|
| bloomberg_utils.py | 2,847 |
| market_report_utils.py | 1,892 |
| factset_utils.py | 1,456 |
| us_treasury.py | 863 |
| ROIC_make_data_files_ver2.py | 756 |

#### 最小ファイル

| ファイル | 行数 |
|----------|------|
| make_financial_factors.py | 14 |
| validate_data.py | 38 |
| edgar_utils.py | 39 |
| init_databases.py | 52 |
| ddg_search.py | 77 |

### 外部依存関係

**総数**: 28パッケージ

| カテゴリ | パッケージ |
|----------|------------|
| コア | pandas, numpy, sqlite3 (stdlib) |
| データソース | yfinance, fredapi, blpapi, edgar |
| 可視化 | matplotlib, seaborn, plotly |
| 分析 | statsmodels, sklearn, pykalman |
| Web | selenium, requests, ddgs |
| Office | openpyxl, polars |
| Google | google-auth, google-api-python-client |

### その他

| 指標 | 値 |
|------|-----|
| コード対コメント比率 | 8.5:1 |

---

## 分析完了情報

| 項目 | 値 |
|------|-----|
| 生成日時 | 2026-01-14T00:00:00+09:00 |
| 生成ツール | Claude Opus 4.5 Code Analysis Agent |
