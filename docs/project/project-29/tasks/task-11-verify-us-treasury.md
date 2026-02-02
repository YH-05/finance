# Task 11: us_treasury.py の動作確認

## 概要

`us_treasury.py` の変更が正常に動作することを確認する。

## 詳細

### 検証スクリプト

```python
from analyze.reporting.us_treasury import (
    plot_us_interest_rates_and_spread,
    load_yield_data_from_cache,
    plot_us_corporate_bond_spreads,
)

# 1. 金利チャートの表示確認
plot_us_interest_rates_and_spread(start_date="2020-01-01")

# 2. イールドデータのロード確認
df = load_yield_data_from_cache()
print(df.head())
print(f"データ件数: {len(df)}")

# 3. 社債スプレッドチャートの表示確認
plot_us_corporate_bond_spreads()
```

### 確認項目

1. **plot_us_interest_rates_and_spread**
   - プロットが正常に表示される
   - 金利データが正しく読み込まれている
   - エラーが発生しない

2. **load_yield_data_from_cache**
   - DataFrameが正常に返される
   - 必要なカラムがすべて含まれている
   - データが空でない

3. **plot_us_corporate_bond_spreads**
   - プロットが正常に表示される
   - スプレッドデータが正しく読み込まれている
   - エラーが発生しない

## 受け入れ条件

- [ ] すべての関数がエラーなく動作する
- [ ] プロットが正常に表示される
- [ ] データが正しく読み込まれている
- [ ] `make check-all` が通る

## 依存関係

- Task 03-05 (us_treasury.pyのすべての変更) に依存

## 見積もり時間

30分
