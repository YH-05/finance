# Alpha Vantage APIキーローテーション + 失敗銘柄優先蓄積

## Context

EarningsPipeline の Phase 2 で Alpha Vantage API からデータ取得しているが、2つの問題がある:

1. **APIキー1つ（25リクエスト/日）では不足**: earnings と overview の両方を取得できない銘柄が多い
2. **失敗銘柄が翌日優先されない**: failed のまま放置され、新規銘柄と同列に扱われる

**解決策**: 4つのAPIキーを使い切り方式でローテーション（合計100リクエスト/日）し、失敗銘柄の優先度を自動ブーストする。

---

## Step 1: 定数追加 — `constants.py`

**ファイル**: `src/market/alphavantage/constants.py`

セクション3（Environment variable names）に追加:

```python
ALPHA_VANTAGE_API_KEYS_ENV: Final[str] = "ALPHA_VANTAGE_API_KEYS"
"""Environment variable name for multiple Alpha Vantage API keys (comma-separated)."""

DEFAULT_DAILY_LIMIT_PER_KEY: Final[int] = 25
"""Daily API call limit per Alpha Vantage free-tier key."""
```

`__all__` に `"ALPHA_VANTAGE_API_KEYS_ENV"`, `"DEFAULT_DAILY_LIMIT_PER_KEY"` を追加。

---

## Step 2: KeyRotator 新規作成

**ファイル**: `src/market/alphavantage/key_rotator.py`（新規）

```python
class KeyRotator:
    """使い切り方式のAPIキーローテーター。

    1つのキーを daily_limit_per_key 回使い切ったら次のキーに切り替える。
    レートリミットエラー検出時は即座に次のキーへフォールバック。
    """

    def __init__(
        self,
        keys: list[str] | None = None,
        daily_limit_per_key: int = DEFAULT_DAILY_LIMIT_PER_KEY,
    ) -> None:
        # keys未指定時の解決順:
        # 1. ALPHA_VANTAGE_API_KEYS (カンマ区切り)
        # 2. ALPHA_VANTAGE_API_KEY (単一キー)
        # 3. AlphaVantageAuthError

    def next_key(self) -> str:
        # 現在キーの使用回数 < daily_limit → 同じキーを返し +1
        # >= daily_limit → 次のキーへ切り替え
        # 全キー使い切り → AlphaVantageRateLimitError

    def mark_rate_limited(self) -> None:
        # 現在キーを使い切り扱いにして次のキーへ

    @property
    def key_count(self) -> int: ...
    @property
    def total_budget(self) -> int: ...  # key_count × daily_limit
    @property
    def remaining_budget(self) -> int: ...
```

**セキュリティ**: ログにはキーインデックス（`key_index=0`）のみ記録、キー値は出力しない。`__repr__` でもキーをマスク。

---

## Step 3: Session に KeyRotator 注入

**ファイル**: `src/market/alphavantage/session.py`

### 3a. `__init__` に `key_rotator` パラメータ追加（L83）

```python
def __init__(
    self,
    config: AlphaVantageConfig | None = None,
    retry_config: RetryConfig | None = None,
    key_rotator: KeyRotator | None = None,  # 追加
) -> None:
    ...
    self._key_rotator: KeyRotator | None = key_rotator
```

### 3b. `_resolve_api_key()` の修正（L308-330）

```python
def _resolve_api_key(self) -> str:
    if self._key_rotator is not None:
        return self._key_rotator.next_key()
    # 既存ロジック（後方互換）
    api_key = self._config.api_key or os.environ.get(ALPHA_VANTAGE_API_KEY_ENV, "")
    if not api_key:
        raise AlphaVantageAuthError(...)
    return api_key
```

### 3c. `get_with_retry()` でレートリミット時に `mark_rate_limited()` 呼び出し（L243付近）

```python
except (AlphaVantageRateLimitError, AlphaVantageAPIError) as e:
    if isinstance(e, AlphaVantageRateLimitError) and self._key_rotator is not None:
        self._key_rotator.mark_rate_limited()
        logger.info("API key rotated due to rate limit", remaining_budget=self._key_rotator.remaining_budget)
    ...
```

---

## Step 4: Client にパススルー

**ファイル**: `src/market/alphavantage/client.py`

### `__init__` に `key_rotator` 追加（L127-136）

```python
def __init__(
    self,
    config: AlphaVantageConfig | None = None,
    retry_config: RetryConfig | None = None,
    cache: SQLiteCache | None = None,
    key_rotator: KeyRotator | None = None,  # 追加
) -> None:
    self._session = AlphaVantageSession(
        config=config, retry_config=retry_config, key_rotator=key_rotator,
    )
    self._cache: SQLiteCache = cache or get_alphavantage_cache()
```

---

## Step 5: `__init__.py` にエクスポート追加

**ファイル**: `src/market/alphavantage/__init__.py`

```python
from market.alphavantage.key_rotator import KeyRotator
```

`__all__` に `"KeyRotator"` を追加。

---

## Step 6: CollectionQueue に priority_boost 追加

**ファイル**: `src/market/pipeline/queue.py`

### `reset_failed()` の修正（L380-438）

```python
def reset_failed(self, max_attempts: int = 3, priority_boost: int = 0) -> int:
    now = _now_iso()
    sql = (
        f"UPDATE {TABLE_NC_COLLECTION_QUEUE}"
        " SET status='pending', error_message=NULL,"
        "     priority=priority+?, updated_at=?"
        " WHERE status='failed' AND attempts < ?"
    )
    self._client.execute(sql, (priority_boost, now, max_attempts))
    ...
```

---

## Step 7: EarningsPipeline の修正

**ファイル**: `src/market/pipeline/pipeline.py`

### 7a. `__init__` の修正（L98-109）

```python
def __init__(
    self,
    av_daily_budget: int | None = None,  # int → int | None に変更
    *,
    queue: CollectionQueue | None = None,
    key_rotator: KeyRotator | None = None,  # 追加
) -> None:
    self._queue = queue or CollectionQueue()

    # KeyRotator: 明示指定 > 環境変数から自動生成 > None
    if key_rotator is not None:
        self._key_rotator = key_rotator
    else:
        try:
            self._key_rotator = KeyRotator()
        except AlphaVantageAuthError:
            self._key_rotator = None

    # Budget: 明示指定 > rotator.total_budget > デフォルト25
    if av_daily_budget is not None:
        self._av_daily_budget = av_daily_budget
    elif self._key_rotator is not None:
        self._av_daily_budget = self._key_rotator.total_budget
    else:
        self._av_daily_budget = AV_DEFAULT_DAILY_BUDGET
```

### 7b. `run_phase2()` の修正（L289-415）

Phase 2 冒頭に追加:
```python
# 失敗エントリを優先度ブースト付きでリセット
reset_count = self._queue.reset_failed(priority_boost=10)
if reset_count > 0:
    logger.info("Phase 2: reset failed entries", reset_count=reset_count, priority_boost=10)
```

AlphaVantageCollector 生成を修正:
```python
if self._key_rotator is not None:
    client = AlphaVantageClient(key_rotator=self._key_rotator)
    av_collector = AlphaVantageCollector(client=client)
else:
    av_collector = AlphaVantageCollector()
```

---

## Step 8: CLI の修正

**ファイル**: `src/market/pipeline/cli.py`

- `--av-budget` のデフォルトを `25` → `None` に変更
- help テキスト更新: `"Auto-detected from API keys if not set. (default: 25 per key)"`
- `--reset-failed` ハンドラに `priority_boost=10` を追加

---

## Step 9: .env に複数キー設定

```bash
# 既存（単一キー、フォールバック用に残す）
ALPHA_VANTAGE_API_KEY=4MWA2RG79U851V6V

# 新規（4キー、カンマ区切り）
ALPHA_VANTAGE_API_KEYS=key1,key2,key3,key4
```

---

## テスト計画

### 新規テスト

**`tests/market/alphavantage/unit/test_key_rotator.py`**（新規）

| テスト | 内容 |
|--------|------|
| `test_正常系_単一キーで初期化できる` | 1キー, total_budget=25 |
| `test_正常系_複数キーで初期化できる` | 4キー, total_budget=100 |
| `test_正常系_next_keyで使用回数がインクリメントされる` | 1回呼ぶとremaining-1 |
| `test_正常系_キー使い切り時に次のキーに切り替わる` | 25回→次キー |
| `test_正常系_mark_rate_limitedで即座に次のキーへ` | 5回使用後mark→次キー |
| `test_正常系_全キー使い切り時にRateLimitError` | 全budget消費 |
| `test_正常系_remaining_budgetが正しい` | 計算検証 |
| `test_正常系_env_ALPHA_VANTAGE_API_KEYSから読み取り` | monkeypatch |
| `test_正常系_env_ALPHA_VANTAGE_API_KEYにフォールバック` | monkeypatch |
| `test_異常系_キーなしでAuthError` | 環境変数なし |

### 既存テストへの追加

**`tests/market/alphavantage/unit/test_session.py`** に追加:
- `test_正常系_key_rotator使用時はnext_keyが呼ばれる`
- `test_正常系_key_rotator未指定時は従来のapi_key解決`
- `test_正常系_RateLimitError時にmark_rate_limitedが呼ばれる`

**`tests/market/pipeline/unit/test_queue.py`** に追加:
- `test_正常系_priority_boostでリセット時に優先度が上がる`
- `test_正常系_priority_boost_0ではpriorityが変わらない`

**`tests/market/pipeline/unit/test_pipeline.py`** に追加:
- `test_正常系_key_rotatorがPhase2に注入される`
- `test_正常系_Phase2冒頭でreset_failedが呼ばれる`
- `test_正常系_av_daily_budgetがrotatorから自動計算される`

---

## 実装順序

```
Step 1 (constants.py)  ─┐
                         ├─→ Step 2 (key_rotator.py + テスト) ─→ Step 3 (session.py)
Step 6 (queue.py + テスト)                                        ─→ Step 4 (client.py)
                                                                     ─→ Step 5 (__init__.py)
                                                                     ─→ Step 7 (pipeline.py + テスト)
                                                                     ─→ Step 8 (cli.py)
```

- Step 1 と Step 6 は並列実行可能（互いに独立）
- Step 2 は Step 1 に依存
- Step 3-5 は Step 2 に依存
- Step 7 は Step 4 と Step 6 の両方に依存
- Step 8 は Step 7 に依存

---

## 検証手順

### 1. ユニットテスト
```bash
uv run pytest tests/market/alphavantage/unit/test_key_rotator.py -v
uv run pytest tests/market/alphavantage/unit/test_session.py -v -k "key_rotator"
uv run pytest tests/market/pipeline/unit/test_queue.py -v -k "priority_boost"
uv run pytest tests/market/pipeline/unit/test_pipeline.py -v -k "key_rotator or reset_failed"
```

### 2. 品質チェック
```bash
make check-all
```

### 3. E2E 動作確認（ドライラン）
```bash
# .env に ALPHA_VANTAGE_API_KEYS を設定後
python -m market.pipeline --dry-run
# → phases: [1,2,3,4], av_budget: 100 が表示されること

python -m market.pipeline --status
# → queue_stats と av_daily_budget: 100 が表示されること
```

### 4. Phase 2 単体実行
```bash
python -m market.pipeline --phase 2
# → 4キーでローテーションしながら最大100リクエスト処理
# → ログに "API key rotated" が表示されるか確認
```

---

## リスクと対策

| リスク | 対策 |
|--------|------|
| ログにAPIキーが漏れる | key_index のみログ出力、repr でマスク |
| AlphaVantageConfig が frozen | KeyRotator は Config 外の独立パラメータとして注入 |
| CLI の `--av-budget` デフォルト変更 | `None` はauto-detect、明示指定は従来通り動作 |
| スレッドセーフティ | パイプラインは同期実行のため問題なし。将来対応時に Lock 追加 |
