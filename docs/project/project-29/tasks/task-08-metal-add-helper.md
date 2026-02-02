# Task 08: metal.py - _load_dollars_indexヘルパーメソッドの追加

## 概要

`DollarsIndexAndMetalsAnalyzer` クラスに `_load_dollars_index()` ヘルパーメソッドを追加する。

## 詳細

### 追加するメソッド

`_load_metal_price()` メソッドの後（59行目付近）に追加:

```python
def _load_dollars_index(self) -> pd.DataFrame:
    """ドル指数データをキャッシュから読み込む。

    Returns
    -------
    pd.DataFrame
        DTWEXAFEGS（ドル指数）データ

    Raises
    ------
    ValueError
        キャッシュにデータがない場合
    """
    df = self.fred_cache.get_series_df("DTWEXAFEGS")
    if df is None:
        raise ValueError(
            "DTWEXAFEGS not found in cache. "
            "Run: HistoricalCache().sync_series('DTWEXAFEGS')"
        )
    return df.rename_axis("Date")
```

## 受け入れ条件

- [ ] `_load_dollars_index()` メソッドが追加されている
- [ ] NumPy形式のDocstringが記述されている
- [ ] キャッシュにデータがない場合は `ValueError` を発生させる
- [ ] 戻り値のインデックス名が "Date" になっている
- [ ] 型チェック (`make typecheck`) が通る

## 依存関係

- Task 07 (__init__クリーンアップ) に依存

## 見積もり時間

20分
