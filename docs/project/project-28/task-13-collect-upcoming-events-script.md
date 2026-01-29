# Task 13: collect_upcoming_events.py スクリプト作成

**Phase**: 3 - 来週の注目材料
**依存**: Task 12
**ファイル**: `scripts/collect_upcoming_events.py`

## 概要

`UpcomingEvents4Agent` を使用して来週の注目材料（決算・経済指標）を収集し、JSONファイルとして出力するCLIスクリプトを作成する。

## 実装仕様

### コマンドライン引数

```bash
uv run python scripts/collect_upcoming_events.py [OPTIONS]

Options:
  --output PATH      出力ディレクトリ（デフォルト: data/market）
  --start-date DATE  開始日（YYYY-MM-DD、デフォルト: 明日）
  --end-date DATE    終了日（YYYY-MM-DD、デフォルト: 1週間後）
  --help             ヘルプ表示
```

### 出力ファイル

```
{output_dir}/
  upcoming_events_{YYYYMMDD-HHMM}.json
```

### スクリプト構造

```python
#!/usr/bin/env python3
"""Collect Upcoming Events Script.

UpcomingEvents4Agent を使用して来週の注目材料を収集し、
data/market/ に構造化JSONとして出力する。

Examples
--------
Basic usage (next 7 days):
    $ uv run python scripts/collect_upcoming_events.py

Specify date range:
    $ uv run python scripts/collect_upcoming_events.py \
        --start-date 2026-02-01 --end-date 2026-02-07

Specify output directory:
    $ uv run python scripts/collect_upcoming_events.py --output .tmp/test
"""

def parse_date(date_str: str) -> date: ...

def generate_timestamp() -> str: ...

def save_json(data: dict[str, Any], file_path: Path) -> None: ...

def collect_upcoming_events(
    output_dir: Path,
    timestamp: str,
    start_date: date,
    end_date: date,
) -> dict[str, Any]: ...

def create_parser() -> argparse.ArgumentParser: ...

def main() -> int: ...

if __name__ == "__main__":
    sys.exit(main())
```

### 出力サンプル

```
============================================================
Upcoming Events Collection Complete
============================================================
Timestamp: 20260129-1030
Output: data/market
Period: 2026-01-30 to 2026-02-05

Files created:
  ✓ upcoming_events_20260129-1030.json

Earnings (5 companies):
  2026-02-01: AAPL (After Market Close)
  2026-02-03: MSFT (After Market Close)
  2026-02-04: GOOGL (After Market Close)
  ...

Economic Releases (3 high-importance):
  2026-02-07: 雇用統計 (Employment Situation)
  2026-02-12: 消費者物価指数 (CPI)
  ...

Highlight: 今週はApple、Microsoftの決算と雇用統計に注目
============================================================
```

## 参照パターン

- `scripts/collect_market_performance.py`
- `scripts/collect_interest_rates.py` (Task 03)
- `scripts/collect_currency_rates.py` (Task 08)

## 受け入れ条件

- [ ] --output オプションで出力先を指定可能
- [ ] --start-date, --end-date オプションで期間を指定可能
- [ ] タイムスタンプ付きファイル名で出力
- [ ] 決算予定と経済指標発表予定の両方を含む
- [ ] 実行結果のサマリーを標準出力に表示
- [ ] エラー時は適切な終了コードを返す
