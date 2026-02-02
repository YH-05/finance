# Task 12: metal.py の動作確認

## 概要

`metal.py` の変更が正常に動作することを確認する。

## 詳細

### 検証スクリプト

```python
from analyze.reporting.metal import DollarsIndexAndMetalsAnalyzer

# 1. インスタンス化（データロード確認）
analyzer = DollarsIndexAndMetalsAnalyzer()

# 2. 各プロパティの確認
print("=== price ===")
print(analyzer.price.head())
print(f"データ件数: {len(analyzer.price)}")

print("\n=== cum_return ===")
print(analyzer.cum_return.head())
print(f"データ件数: {len(analyzer.cum_return)}")

# 3. プロット確認
fig = analyzer.plot_us_dollar_index_and_metal_price()
fig.show()
```

### 確認項目

1. **インスタンス化**
   - エラーなくインスタンスが作成される
   - `FRED_DIR` 環境変数が不要になっている

2. **price プロパティ**
   - DataFrameが正常に返される
   - ドル指数とメタル価格が含まれている

3. **cum_return プロパティ**
   - DataFrameが正常に返される
   - 累積リターンが正しく計算されている

4. **plot_us_dollar_index_and_metal_price**
   - プロットが正常に表示される
   - エラーが発生しない

## 受け入れ条件

- [ ] クラスがエラーなくインスタンス化できる
- [ ] すべてのプロパティが正常に動作する
- [ ] プロットが正常に表示される
- [ ] `make check-all` が通る

## 依存関係

- Task 09-10 (metal.pyのすべての変更) に依存

## 見積もり時間

30分
