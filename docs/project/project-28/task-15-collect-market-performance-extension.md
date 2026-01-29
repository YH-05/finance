# Task 15: collect_market_performance.py の拡張

**Phase**: 4 - 統合
**依存**: Task 03, Task 08, Task 13
**ファイル**: `scripts/collect_market_performance.py`

## 概要

既存の `collect_market_performance.py` を拡張し、金利・為替・来週の注目材料のデータ収集も統合する。

## 現行の機能

```python
categories: dict[str, tuple[str, str | None]] = {
    "indices_us": ("indices", "us"),
    "indices_global": ("indices", "global"),
    "mag7": ("mag7", None),
    "sectors": ("sectors", None),
    "commodities": ("commodities", None),
}
```

## 拡張内容

### 新カテゴリの追加

```python
# 既存カテゴリ
categories: dict[str, tuple[str, str | None]] = {
    "indices_us": ("indices", "us"),
    "indices_global": ("indices", "global"),
    "mag7": ("mag7", None),
    "sectors": ("sectors", None),
    "commodities": ("commodities", None),
}

# 新カテゴリ（別の Analyzer を使用）
additional_categories = {
    "interest_rates": InterestRateAnalyzer4Agent,
    "currencies": CurrencyAnalyzer4Agent,
    "upcoming_events": UpcomingEvents4Agent,
}
```

### 修正後のスクリプト構造

```python
def collect_all_performance(
    output_dir: Path,
    timestamp: str,
) -> dict[str, dict[str, Any]]:
    """全市場パフォーマンスデータを収集."""
    results: dict[str, dict[str, Any]] = {}

    # 1. 既存カテゴリ（PerformanceAnalyzer4Agent）
    analyzer = PerformanceAnalyzer4Agent()
    for category_name, (group, subgroup) in categories.items():
        result = analyzer.get_group_performance(group, subgroup)
        save_json(result.to_dict(), output_dir / f"{category_name}_{timestamp}.json")
        results[category_name] = result.to_dict()

    # 2. 金利データ（InterestRateAnalyzer4Agent）
    interest_analyzer = InterestRateAnalyzer4Agent()
    interest_result = interest_analyzer.get_interest_rate_performance()
    save_json(interest_result.to_dict(), output_dir / f"interest_rates_{timestamp}.json")
    results["interest_rates"] = interest_result.to_dict()

    # 3. 為替データ（CurrencyAnalyzer4Agent）
    currency_analyzer = CurrencyAnalyzer4Agent()
    currency_result = currency_analyzer.get_currency_performance("jpy_crosses")
    save_json(currency_result.to_dict(), output_dir / f"currencies_{timestamp}.json")
    results["currencies"] = currency_result.to_dict()

    # 4. 来週の注目材料（UpcomingEvents4Agent）
    events_agent = UpcomingEvents4Agent()
    events_result = events_agent.get_upcoming_events()
    save_json(events_result.to_dict(), output_dir / f"upcoming_events_{timestamp}.json")
    results["upcoming_events"] = events_result.to_dict()

    # 統合ファイル
    all_data = {
        "generated_at": datetime.now().isoformat(),
        "timestamp": timestamp,
        "categories": list(results.keys()),
        "data": results,
    }
    save_json(all_data, output_dir / f"all_performance_{timestamp}.json")

    return results
```

### 出力ファイル

```
{output_dir}/
  indices_us_{timestamp}.json
  indices_global_{timestamp}.json
  mag7_{timestamp}.json
  sectors_{timestamp}.json
  commodities_{timestamp}.json
  interest_rates_{timestamp}.json      # 新規
  currencies_{timestamp}.json          # 新規
  upcoming_events_{timestamp}.json     # 新規
  all_performance_{timestamp}.json     # 全統合
```

### 出力サンプル更新

```
============================================================
Market Performance Data Collection Complete
============================================================
Timestamp: 20260129-1030
Output: data/market

Files created:
  ✓ indices_us_20260129-1030.json
  ✓ indices_global_20260129-1030.json
  ✓ mag7_20260129-1030.json
  ✓ sectors_20260129-1030.json
  ✓ commodities_20260129-1030.json
  ✓ interest_rates_20260129-1030.json    # 新規
  ✓ currencies_20260129-1030.json        # 新規
  ✓ upcoming_events_20260129-1030.json   # 新規
  ✓ all_performance_20260129-1030.json

Data Summary:
  indices_us: 8 symbols, periods: [1D, 1W, MTD, ...]
  indices_global: 13 symbols, periods: [1D, 1W, MTD, ...]
  mag7: 7 symbols, periods: [1D, 1W, MTD, ...]
  sectors: 11 symbols, periods: [1D, 1W, MTD, ...]
  commodities: 10 symbols, periods: [1D, 1W, MTD, ...]
  interest_rates: 5 series, yield curve: Normal (+0.45%)
  currencies: 6 pairs, trend: 円安傾向
  upcoming_events: 5 earnings, 3 high-importance releases
============================================================
```

## 受け入れ条件

- [ ] 金利データを収集・出力できる
- [ ] 為替データを収集・出力できる
- [ ] 来週の注目材料を収集・出力できる
- [ ] 統合ファイル（all_performance）に全カテゴリを含む
- [ ] 既存カテゴリの動作に影響がない
- [ ] エラー時も他カテゴリの処理を継続
