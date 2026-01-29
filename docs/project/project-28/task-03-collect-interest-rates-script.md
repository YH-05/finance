# Task 03: collect_interest_rates.py スクリプト作成

**Phase**: 1 - 金利データ
**依存**: Task 02
**ファイル**: `scripts/collect_interest_rates.py`

## 概要

`InterestRateAnalyzer4Agent` を使用して金利データを収集し、JSONファイルとして出力するCLIスクリプトを作成する。

## 実装仕様

### コマンドライン引数

```bash
uv run python scripts/collect_interest_rates.py [OPTIONS]

Options:
  --output PATH    出力ディレクトリ（デフォルト: data/market）
  --help           ヘルプ表示
```

### 出力ファイル

```
{output_dir}/
  interest_rates_{YYYYMMDD-HHMM}.json
```

### スクリプト構造

```python
#!/usr/bin/env python3
"""Collect Interest Rate Data Script.

InterestRateAnalyzer4Agent を使用して金利データを収集し、
data/market/ に構造化JSONとして出力する。

Examples
--------
Basic usage:
    $ uv run python scripts/collect_interest_rates.py

Specify output directory:
    $ uv run python scripts/collect_interest_rates.py --output .tmp/test
"""

def generate_timestamp() -> str: ...

def save_json(data: dict[str, Any], file_path: Path) -> None: ...

def collect_interest_rates(output_dir: Path, timestamp: str) -> dict[str, Any]: ...

def create_parser() -> argparse.ArgumentParser: ...

def main() -> int: ...

if __name__ == "__main__":
    sys.exit(main())
```

### 出力サンプル

```
============================================================
Interest Rate Data Collection Complete
============================================================
Timestamp: 20260129-1030
Output: data/market

Files created:
  ✓ interest_rates_20260129-1030.json

Data Summary:
  Series: 5
  Latest Date: 2026-01-28
  Yield Curve: Normal (2y-10y spread: +0.45%)
============================================================
```

## 参照パターン

- `scripts/collect_market_performance.py`

## 受け入れ条件

- [ ] --output オプションで出力先を指定可能
- [ ] タイムスタンプ付きファイル名で出力
- [ ] 実行結果のサマリーを標準出力に表示
- [ ] エラー時は適切な終了コードを返す
- [ ] ロギングが実装されている
