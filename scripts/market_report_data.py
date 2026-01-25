#!/usr/bin/env python3
"""Market Report Data Collection Script.

騰落率・セクター分析・決算カレンダーの各モジュールを統合実行し、
JSONファイルを出力するスクリプト。

このスクリプトは以下の3つのモジュールからデータを収集します:

1. **騰落率 (Returns)**: 主要指数、MAG7、セクターETF、グローバル指数の騰落率
2. **セクター分析 (Sectors)**: セクター別のパフォーマンス分析
3. **決算カレンダー (Earnings)**: 今後の決算発表予定

出力ファイル
-----------
- returns.json: 騰落率データ
- sectors.json: セクター分析データ
- earnings.json: 決算カレンダーデータ

Examples
--------
基本的な使用方法:

    $ uv run python scripts/market_report_data.py

出力ディレクトリを指定:

    $ uv run python scripts/market_report_data.py --output .tmp/market-report-20260119/

Notes
-----
- 各モジュールのエラーは独立して処理され、一つのモジュールが失敗しても他は続行
- 出力ディレクトリは自動作成される
- 終了コード 0 は少なくとも1つのファイル作成成功、1 は全て失敗

See Also
--------
market_analysis.analysis.returns : 騰落率計算モジュール
market_analysis.analysis.sector : セクター分析モジュール
market_analysis.analysis.earnings : 決算カレンダーモジュール
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from database.utils.logging_config import get_logger
from market_analysis.analysis.earnings import get_upcoming_earnings
from market_analysis.analysis.returns import generate_returns_report
from market_analysis.analysis.sector import analyze_sector_performance

logger = get_logger(__name__)


def collect_returns_data() -> dict[str, Any]:
    """Collect returns data using generate_returns_report.

    Returns
    -------
    dict[str, Any]
        Returns report containing indices, MAG7, sectors, and global indices data.

    Examples
    --------
    >>> data = collect_returns_data()
    >>> "as_of" in data
    True
    """
    logger.debug("Collecting returns data")
    result = generate_returns_report()
    logger.info("Returns data collected", indices_count=len(result.get("indices", [])))
    return result


def collect_sector_data() -> dict[str, Any]:
    """Collect sector analysis data using analyze_sector_performance.

    Returns
    -------
    dict[str, Any]
        Sector analysis result containing top_sectors and bottom_sectors.

    Examples
    --------
    >>> data = collect_sector_data()
    >>> "top_sectors" in data
    True
    """
    logger.debug("Collecting sector data")
    result = analyze_sector_performance()
    data = result.to_dict()
    logger.info(
        "Sector data collected",
        top_sectors_count=len(data.get("top_sectors", [])),
        bottom_sectors_count=len(data.get("bottom_sectors", [])),
    )
    return data


def collect_earnings_data() -> dict[str, Any]:
    """Collect upcoming earnings data using get_upcoming_earnings.

    Returns
    -------
    dict[str, Any]
        Earnings calendar data containing upcoming earnings events.

    Examples
    --------
    >>> data = collect_earnings_data()
    >>> isinstance(data, dict)
    True
    """
    logger.debug("Collecting earnings data")
    result = get_upcoming_earnings()
    logger.info(
        "Earnings data collected",
        earnings_count=len(result.get("upcoming_earnings", [])),
    )
    return result


def save_all_reports(output_dir: Path) -> None:
    """Collect all reports and save them as JSON files.

    This function orchestrates the collection of returns, sector, and earnings
    data, then saves each to a separate JSON file. If one module fails, the
    others will still be processed.

    Parameters
    ----------
    output_dir : Path
        Directory where JSON files will be saved.

    Raises
    ------
    PermissionError
        If the output directory cannot be created.

    Examples
    --------
    >>> from pathlib import Path
    >>> save_all_reports(Path(".tmp/market-report"))  # doctest: +SKIP
    """
    logger.info("Starting report collection", output_dir=str(output_dir))

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total_count = 3

    # Collect returns data
    try:
        returns_data = collect_returns_data()
        returns_file = output_dir / "returns.json"
        with returns_file.open("w", encoding="utf-8") as f:
            json.dump(returns_data, f, ensure_ascii=False, indent=2)
        logger.info("Returns data saved", file=str(returns_file))
        success_count += 1
    except Exception as e:
        logger.error("Failed to collect returns data", error=str(e), exc_info=True)

    # Collect sector data
    try:
        sector_data = collect_sector_data()
        sectors_file = output_dir / "sectors.json"
        with sectors_file.open("w", encoding="utf-8") as f:
            json.dump(sector_data, f, ensure_ascii=False, indent=2)
        logger.info("Sector data saved", file=str(sectors_file))
        success_count += 1
    except Exception as e:
        logger.error("Failed to collect sector data", error=str(e), exc_info=True)

    # Collect earnings data
    try:
        earnings_data = collect_earnings_data()
        earnings_file = output_dir / "earnings.json"
        with earnings_file.open("w", encoding="utf-8") as f:
            json.dump(earnings_data, f, ensure_ascii=False, indent=2)
        logger.info("Earnings data saved", file=str(earnings_file))
        success_count += 1
    except Exception as e:
        logger.error("Failed to collect earnings data", error=str(e), exc_info=True)

    logger.info(
        "Report collection completed",
        success_count=success_count,
        total_count=total_count,
    )


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured argument parser with --output option.

    Examples
    --------
    >>> parser = create_parser()
    >>> args = parser.parse_args(["--output", "/path/to/output"])
    >>> args.output
    '/path/to/output'
    """
    parser = argparse.ArgumentParser(
        description="Collect market report data (returns, sectors, earnings)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Default output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    default_output = f".tmp/market-report-{timestamp}"

    parser.add_argument(
        "--output",
        type=str,
        default=default_output,
        help=f"Output directory for JSON files (default: {default_output})",
    )

    return parser


def main() -> int:
    """Main entry point for the script.

    Returns
    -------
    int
        Exit code (0 for success, 1 for failure).

    Examples
    --------
    >>> # Run with default arguments (requires mocking in tests)
    >>> # exit_code = main()
    """
    logger.info("Market report data collection started")

    parser = create_parser()
    args = parser.parse_args()

    output_dir = Path(args.output)
    logger.info("Output directory", path=str(output_dir))

    try:
        save_all_reports(output_dir)

        # Check if at least one file was created
        expected_files = ["returns.json", "sectors.json", "earnings.json"]
        existing_files = [f for f in expected_files if (output_dir / f).exists()]

        if not existing_files:
            logger.error("No report files were created")
            return 1

        logger.info(
            "Market report data collection completed successfully",
            files_created=existing_files,
        )
        return 0

    except PermissionError as e:
        logger.error("Permission denied", error=str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
