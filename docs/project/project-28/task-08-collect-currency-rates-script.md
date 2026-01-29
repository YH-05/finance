# Task 08: collect_currency_rates.py スクリプト作成

**Phase**: 2 - 為替データ
**依存**: Task 07
**ファイル**: `scripts/collect_currency_rates.py`

## 概要

`CurrencyAnalyzer4Agent` を使用して為替データを収集し、JSONファイルとして出力するCLIスクリプトを作成する。

## 実装仕様

### コマンドライン引数

```bash
uv run python scripts/collect_currency_rates.py [OPTIONS]

Options:
  --output PATH    出力ディレクトリ（デフォルト: data/market）
  --subgroup TEXT  通貨サブグループ（デフォルト: jpy_crosses）
  --help           ヘルプ表示
```

### 出力ファイル

```
{output_dir}/
  currencies_{subgroup}_{YYYYMMDD-HHMM}.json
```

### スクリプト構造

```python
#!/usr/bin/env python3
"""Collect Currency Rate Data Script.

CurrencyAnalyzer4Agent を使用して為替データを収集し、
data/market/ に構造化JSONとして出力する。

Examples
--------
Basic usage:
    $ uv run python scripts/collect_currency_rates.py

Specify output directory:
    $ uv run python scripts/collect_currency_rates.py --output .tmp/test

Specify subgroup:
    $ uv run python scripts/collect_currency_rates.py --subgroup jpy_crosses
"""

def generate_timestamp() -> str: ...

def save_json(data: dict[str, Any], file_path: Path) -> None: ...

def collect_currency_rates(
    output_dir: Path,
    timestamp: str,
    subgroup: str,
) -> dict[str, Any]: ...

def create_parser() -> argparse.ArgumentParser: ...

def main() -> int: ...

if __name__ == "__main__":
    sys.exit(main())
```

### 出力サンプル

```
============================================================
Currency Rate Data Collection Complete
============================================================
Timestamp: 20260129-1030
Output: data/market
Subgroup: jpy_crosses

Files created:
  ✓ currencies_jpy_crosses_20260129-1030.json

Data Summary:
  Pairs: 6
  Latest Date: 2026-01-28
  Strongest (YTD): USD/JPY +2.50%
  Weakest (YTD): AUD/JPY -1.20%
  Trend: 円安傾向
============================================================
```

## 参照パターン

- `scripts/collect_market_performance.py`
- `scripts/collect_interest_rates.py` (Task 03)

## 受け入れ条件

- [ ] --output オプションで出力先を指定可能
- [ ] --subgroup オプションでサブグループを指定可能
- [ ] タイムスタンプ付きファイル名で出力
- [ ] 実行結果のサマリーを標準出力に表示
- [ ] エラー時は適切な終了コードを返す
