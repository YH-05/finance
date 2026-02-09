# market.cache

SQLite ベースのキャッシュモジュール。TTL（有効期限）対応、スレッドセーフ。

## 概要

市場データの取得結果をローカルにキャッシュし、API 呼び出し回数を削減します。インメモリキャッシュとファイルベースの永続キャッシュの両方に対応。

**主な特徴:**

- **TTL 対応**: エントリごとの有効期限管理
- **スレッドセーフ**: `threading.Lock` による排他制御
- **自動クリーンアップ**: 期限切れエントリの自動削除
- **最大エントリ制限**: 古いエントリの自動削除
- **pandas DataFrame 対応**: DataFrame のシリアライズ / デシリアライズ
- **グローバルインスタンス**: シングルトンパターンでのキャッシュ共有

## クイックスタート

### 基本的な使い方

```python
from market.cache import SQLiteCache

# インメモリキャッシュ（デフォルト）
cache = SQLiteCache()

# データを保存（TTL: 1時間）
cache.set("key1", {"price": 150.0}, ttl=3600)

# データを取得
value = cache.get("key1")  # → {"price": 150.0}

# 期限切れ後は None
value = cache.get("expired_key")  # → None
```

### 永続キャッシュ

```python
from market.cache import create_persistent_cache

# ファイルベースのキャッシュ（24時間有効）
cache = create_persistent_cache(
    db_path="./data/cache/market_data.db",
    ttl_seconds=86400,
    max_entries=10000,
)

# データを保存・取得（セッションをまたいで永続化）
cache.set("AAPL_daily", df)
df = cache.get("AAPL_daily")
```

### グローバルキャッシュ

```python
from market.cache import get_cache, reset_cache

# グローバルキャッシュの取得（遅延初期化）
cache = get_cache()
cache.set("key", "value")

# リセット（テスト時など）
reset_cache()
```

### キャッシュキーの生成

```python
from market.cache import generate_cache_key

# シンボル・期間・ソースから一意のキーを生成
key = generate_cache_key(
    symbol="AAPL",
    start_date="2024-01-01",
    end_date="2024-12-31",
    interval="1d",
    source="yfinance",
)
# → SHA-256 ハッシュ値（64文字）
```

### コンテキストマネージャー

```python
with SQLiteCache() as cache:
    cache.set("key", "value")
    value = cache.get("key")
    # 自動的にクローズ
```

## API リファレンス

### SQLiteCache

SQLite ベースのキャッシュクラス。

**コンストラクタ:**

```python
SQLiteCache(config: CacheConfig | None = None)
```

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `get(key)` | キャッシュからデータを取得 | `Any \| None` |
| `set(key, value, ttl, metadata)` | データをキャッシュに保存 | `None` |
| `delete(key)` | エントリを削除 | `bool` |
| `clear()` | 全エントリを削除 | `int`（削除数） |
| `cleanup_expired()` | 期限切れエントリを削除 | `int`（削除数） |
| `get_stats()` | キャッシュ統計を取得 | `dict[str, Any]` |
| `close()` | DB 接続を閉じる | `None` |

### CacheConfig

キャッシュ設定（frozen dataclass）。

| フィールド | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `enabled` | `bool` | True | キャッシュ有効/無効 |
| `ttl_seconds` | `int` | 3600 | TTL（秒）。正の整数のみ |
| `max_entries` | `int` | 1000 | 最大エントリ数。正の整数のみ |
| `db_path` | `str \| None` | None | DB パス。None でインメモリ |

### ユーティリティ関数

| 関数 | 説明 | 戻り値 |
|------|------|--------|
| `generate_cache_key(symbol, start_date, end_date, interval, source)` | キャッシュキーを生成 | `str` |
| `get_cache(config)` | グローバルキャッシュを取得/作成 | `SQLiteCache` |
| `reset_cache()` | グローバルキャッシュをリセット | `None` |
| `create_persistent_cache(db_path, ttl_seconds, max_entries)` | 永続キャッシュを作成 | `SQLiteCache` |

### 定数

| 定数 | 説明 |
|------|------|
| `DEFAULT_CACHE_CONFIG` | デフォルト設定（インメモリ、TTL 1時間、最大1000件） |
| `DEFAULT_CACHE_DB_PATH` | デフォルト DB パス: `data/cache/market_data.db` |
| `PERSISTENT_CACHE_CONFIG` | 永続キャッシュ設定（TTL 24時間、最大10000件） |

### 例外

| 例外 | 説明 |
|------|------|
| `CacheError` | キャッシュ操作エラー（operation, key, cause 情報付き） |

## シリアライズ

SQLiteCache は以下の型を自動的にシリアライズ/デシリアライズします:

| データ型 | シリアライズ方式 |
|---------|----------------|
| `pd.DataFrame` | pickle |
| `pd.Series` | pickle |
| `dict`, `list` | JSON |
| その他 | pickle |

## モジュール構成

```
market/cache/
├── __init__.py   # パッケージエクスポート
├── cache.py      # SQLiteCache 実装、ユーティリティ関数
├── types.py      # CacheConfig 定義
└── README.md     # このファイル
```

## 関連モジュール

- [market.yfinance](../yfinance/README.md) - Yahoo Finance データ取得（キャッシュ利用）
- [market.fred](../fred/README.md) - FRED データ取得（独自キャッシュ + 共通キャッシュ）
