"""automation パッケージのモジュールエントリポイント。

Examples
--------
モジュールとして実行:
    $ uv run python -m automation
    $ uv run python -m automation --days 3 --dry-run
"""

from automation.news_collector import main

if __name__ == "__main__":
    raise SystemExit(main())
