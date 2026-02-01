# TIPSデータの活用方法

## 概要

TIPS（Treasury Inflation-Protected Securities）は物価連動国債で、インフレ調整後の実質利回りを示す。

## FREDシリーズID

| シリーズID | 名前                             | 説明                     |
| ---------- | -------------------------------- | ------------------------ |
| `DFII5`    | 5年物価連動国債利回り            | 中期実質金利             |
| `DFII7`    | 7年物価連動国債利回り            |                          |
| `DFII10`   | 10年物価連動国債利回り           | 長期実質金利の代表的指標 |
| `DFII20`   | 20年物価連動国債利回り           |                          |
| `DFII30`   | 30年物価連動国債利回り           | 超長期実質金利           |
| `T5YIE`    | 5年ブレークイーブンインフレ率    | 中期インフレ期待         |
| `T10YIE`   | 10年ブレークイーブンインフレ率   | 長期インフレ期待         |
| `T5YIFR`   | 5年先5年フォワードインフレ期待率 | 長期インフレ期待の安定性 |

## 1. 実質金利の把握

```python
from finance.market.fred import FREDFetcher

fetcher = FREDFetcher()

# 10年実質金利を取得
real_rate_10y = fetcher.fetch("DFII10")
print(f"10年実質金利: {real_rate_10y.iloc[-1]:.2f}%")
```

**解釈**: 実質金利がプラスなら「インフレを上回るリターン」、マイナスなら「インフレ負け」。

## 2. ブレークイーブン・インフレ率の計算

```python
# 名目金利とTIPS利回りの差 = 市場のインフレ期待
nominal_10y = fetcher.fetch("DGS10")
tips_10y = fetcher.fetch("DFII10")

breakeven = nominal_10y - tips_10y  # = T10YIE と同等
```

**活用**: FRBの2%目標と比較して、市場がインフレをどう見ているか判断。

## 3. インフレ期待の期間構造

```python
# 短期 vs 長期のインフレ期待を比較
be_5y = fetcher.fetch("T5YIE")    # 5年インフレ期待
be_10y = fetcher.fetch("T10YIE")  # 10年インフレ期待
forward = fetcher.fetch("T5YIFR") # 5年先5年（長期安定性）

# 5年先5年が安定 → 長期インフレ期待がアンカーされている
```

## 4. 実質イールドカーブ

```python
import pandas as pd

# 実質金利のイールドカーブ
maturities = ["DFII5", "DFII7", "DFII10", "DFII20", "DFII30"]
real_curve = {m: fetcher.fetch(m).iloc[-1] for m in maturities}

# 名目イールドカーブと比較
nominal_maturities = ["DGS5", "DGS7", "DGS10", "DGS20", "DGS30"]
nominal_curve = {m: fetcher.fetch(m).iloc[-1] for m in nominal_maturities}
```

## 投資判断での活用例

| 指標             | シグナル                                       |
| ---------------- | ---------------------------------------------- |
| 実質金利上昇     | グロース株に逆風、バリュー株に追い風           |
| 実質金利マイナス | 金・コモディティに追い風                       |
| BEI上昇          | インフレヘッジ資産（TIPS、コモディティ）に有利 |
| T5YIFR安定       | FRBの信認維持、長期債に安心感                  |

## 週次レポートでの活用案

```python
# 週次変化を追跡
real_10y_current = fetcher.fetch("DFII10").iloc[-1]
real_10y_week_ago = fetcher.fetch("DFII10").iloc[-5]
change = real_10y_current - real_10y_week_ago

print(f"10年実質金利: {real_10y_current:.2f}% (週間{change:+.2f}%)")
```

## 関連ファイル

- 設定: `data/config/fred_series.json`
- Fetcher: `src/market/fred/fetcher.py`
