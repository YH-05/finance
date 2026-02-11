"""market.industry パッケージのモジュールエントリポイント。

Examples
--------
モジュールとして実行:
    $ uv run python -m market.industry.collect
    $ uv run python -m market.industry.collect --sector Technology
    $ uv run python -m market.industry.collect --ticker AAPL
    $ uv run python -m market.industry.collect --source mckinsey
"""

from market.industry.collector import main

if __name__ == "__main__":
    raise SystemExit(main())
