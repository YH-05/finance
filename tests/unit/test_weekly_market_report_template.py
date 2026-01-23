"""Unit tests for weekly_market_report_template.md template file.

This module tests that the template file:
1. Contains all required placeholders
2. Placeholder substitution works correctly with sample data
"""

from __future__ import annotations

from pathlib import Path


class TestWeeklyMarketReportTemplate:
    """Tests for weekly_market_report_template.md."""

    TEMPLATE_PATH = Path("template/market_report/weekly_market_report_template.md")

    # Required placeholders from Issue #774
    REQUIRED_PLACEHOLDERS = [
        "{report_date}",
        "{period_start}",
        "{period_end}",
        "{highlights}",
        "{indices_table}",
        "{indices_comment}",
        "{style_analysis}",
        "{mag7_table}",
        "{mag7_comment}",
        "{top_sectors_table}",
        "{top_sectors_comment}",
        "{bottom_sectors_table}",
        "{bottom_sectors_comment}",
        "{macro_comment}",
        "{theme_comment}",
        "{upcoming_events}",
    ]

    def test_正常系_テンプレートファイルが存在する(self) -> None:
        assert self.TEMPLATE_PATH.exists(), (
            f"テンプレートファイルが存在しません: {self.TEMPLATE_PATH}"
        )

    def test_正常系_全プレースホルダーが定義されている(self) -> None:
        template_content = self.TEMPLATE_PATH.read_text(encoding="utf-8")

        missing_placeholders = []
        for placeholder in self.REQUIRED_PLACEHOLDERS:
            if placeholder not in template_content:
                missing_placeholders.append(placeholder)

        assert not missing_placeholders, (
            f"以下のプレースホルダーが不足しています: {missing_placeholders}"
        )

    def test_正常系_サンプルデータで置換テストが成功する(self) -> None:
        template_content = self.TEMPLATE_PATH.read_text(encoding="utf-8")

        # Sample data for substitution test
        sample_data = {
            "report_date": "2026/1/22",
            "period_start": "2026/1/15",
            "period_end": "2026/1/22",
            "highlights": "- S&P 500は週間で1.5%上昇\n- MAG7が市場を牽引\n- エネルギーセクターが堅調",
            "indices_table": "| 指数 | 週間リターン |\n|------|-------------|\n| S&P 500 | +1.50% |\n| 等ウェイト (RSP) | +0.80% |",
            "indices_comment": "主要指数は週を通じて堅調に推移しました。",
            "style_analysis": "グロース銘柄が優勢で、VUGは+2.1%、VTVは+0.5%でした。",
            "mag7_table": "| 銘柄 | 週間リターン |\n|------|-------------|\n| AAPL | +2.5% |\n| MSFT | +1.8% |",
            "mag7_comment": "テック大手は全体的に好調でした。",
            "top_sectors_table": "| セクター | ETF | 週間リターン |\n|----------|-----|-------------|\n| IT | XLK | +2.3% |",
            "top_sectors_comment": "IT セクターはAI関連の期待から上昇しました。",
            "bottom_sectors_table": "| セクター | ETF | 週間リターン |\n|----------|-----|-------------|\n| 公益 | XLU | -1.5% |",
            "bottom_sectors_comment": "公益セクターは金利上昇懸念から軟調でした。",
            "macro_comment": "FRBの発言に注目が集まりました。",
            "theme_comment": "AI投資テーマが引き続き注目されています。",
            "upcoming_events": "- FOMC議事録公表\n- 雇用統計発表",
        }

        # Perform substitution
        result = template_content.format(**sample_data)

        # Verify no unsubstituted placeholders remain
        for placeholder in self.REQUIRED_PLACEHOLDERS:
            assert placeholder not in result, (
                f"プレースホルダー {placeholder} が置換されていません"
            )

        # Verify sample data is present in result
        for key, value in sample_data.items():
            assert value in result, f"サンプルデータ '{key}' が結果に含まれていません"

    def test_正常系_テンプレートが有効なMarkdown形式である(self) -> None:
        template_content = self.TEMPLATE_PATH.read_text(encoding="utf-8")

        # Check for basic Markdown structure
        assert template_content.startswith("#"), (
            "テンプレートはH1ヘッダーで始まる必要があります"
        )
        assert "##" in template_content, "テンプレートにはH2セクションが必要です"
        assert "---" in template_content, (
            "テンプレートにはセクション区切り(---)が必要です"
        )

    def test_正常系_免責事項が含まれている(self) -> None:
        template_content = self.TEMPLATE_PATH.read_text(encoding="utf-8")

        assert "免責事項" in template_content, (
            "テンプレートには免責事項が含まれている必要があります"
        )
        assert "投資助言" in template_content or "投資判断" in template_content, (
            "免責事項には投資に関する注意が必要です"
        )

    def test_正常系_データソース情報が含まれている(self) -> None:
        template_content = self.TEMPLATE_PATH.read_text(encoding="utf-8")

        assert "データソース" in template_content, (
            "テンプレートにはデータソース情報が必要です"
        )
