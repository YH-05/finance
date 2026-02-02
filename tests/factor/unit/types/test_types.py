"""Unit tests for factor types module.

このテストモジュールは、factor パッケージの共通型定義を検証します。

テスト対象:
- FactorResult: ファクター計算結果
- FactorMetadata: ファクターのメタデータ
- FactorScore: ファクタースコア
"""

from dataclasses import FrozenInstanceError
from datetime import datetime

import pandas as pd
import pytest

from factor.enums import FactorCategory, NormalizationMethod
from factor.types import FactorConfig, FactorMetadata, FactorResult, FactorScore

# =============================================================================
# FactorResult のテスト（既存機能の確認）
# =============================================================================


class TestFactorResult:
    """FactorResultのテスト。"""

    def test_正常系_必須フィールドのみで初期化(self) -> None:
        """必須フィールドのみでFactorResultが作成できることを確認。"""
        config = FactorConfig(
            name="test_factor",
            category=FactorCategory.MOMENTUM,
        )
        data = pd.DataFrame(
            {"AAPL": [0.1, 0.2, 0.3], "GOOGL": [0.2, 0.3, 0.4]},
            index=pd.date_range("2024-01-01", periods=3, freq="D"),
        )

        result = FactorResult(
            name="test_factor",
            data=data,
            config=config,
        )

        assert result.name == "test_factor"
        assert not result.is_empty
        assert result.symbols == ["AAPL", "GOOGL"]

    def test_正常系_is_emptyが空データでTrue(self) -> None:
        """空のDataFrameでis_emptyがTrueを返すことを確認。"""
        config = FactorConfig(
            name="empty_factor",
            category=FactorCategory.VALUE,
        )
        empty_data = pd.DataFrame()

        result = FactorResult(
            name="empty_factor",
            data=empty_data,
            config=config,
        )

        assert result.is_empty

    def test_正常系_date_rangeが正しいタプルを返す(self) -> None:
        """date_rangeが正しい日付範囲のタプルを返すことを確認。"""
        config = FactorConfig(
            name="test_factor",
            category=FactorCategory.MOMENTUM,
        )
        data = pd.DataFrame(
            {"AAPL": [0.1, 0.2, 0.3]},
            index=pd.date_range("2024-01-01", periods=3, freq="D"),
        )

        result = FactorResult(
            name="test_factor",
            data=data,
            config=config,
        )

        date_range = result.date_range
        assert date_range is not None
        assert date_range[0].date() == datetime(2024, 1, 1).date()
        assert date_range[1].date() == datetime(2024, 1, 3).date()

    def test_正常系_空データでdate_rangeがNone(self) -> None:
        """空のDataFrameでdate_rangeがNoneを返すことを確認。"""
        config = FactorConfig(
            name="empty_factor",
            category=FactorCategory.VALUE,
        )
        empty_data = pd.DataFrame()

        result = FactorResult(
            name="empty_factor",
            data=empty_data,
            config=config,
        )

        assert result.date_range is None


# =============================================================================
# FactorMetadata のテスト
# =============================================================================


class TestFactorMetadata:
    """FactorMetadataのテスト。"""

    def test_正常系_必須フィールドのみで初期化(self) -> None:
        """必須フィールドのみでFactorMetadataが作成できることを確認。"""
        metadata = FactorMetadata(
            name="momentum_factor",
            description="12-month momentum factor",
            category="price",
            required_data=["price"],
            frequency="daily",
        )

        assert metadata.name == "momentum_factor"
        assert metadata.description == "12-month momentum factor"
        assert metadata.category == "price"
        assert metadata.required_data == ["price"]
        assert metadata.frequency == "daily"

    def test_正常系_全フィールドで初期化(self) -> None:
        """全フィールドを指定してFactorMetadataが作成できることを確認。"""
        metadata = FactorMetadata(
            name="value_factor",
            description="Value factor based on P/E ratio",
            category="value",
            required_data=["price", "earnings"],
            frequency="monthly",
            lookback_period=252,
            higher_is_better=False,
            default_parameters={"window": 20, "threshold": 0.5},
        )

        assert metadata.name == "value_factor"
        assert metadata.lookback_period == 252
        assert metadata.higher_is_better is False
        assert metadata.default_parameters == {"window": 20, "threshold": 0.5}

    def test_正常系_デフォルト値が適用される(self) -> None:
        """デフォルト値が正しく適用されることを確認。"""
        metadata = FactorMetadata(
            name="test",
            description="test factor",
            category="quality",
            required_data=["price"],
            frequency="daily",
        )

        assert metadata.lookback_period is None
        assert metadata.higher_is_better is True
        assert metadata.default_parameters == {}

    def test_正常系_frozenでイミュータブル(self) -> None:
        """FactorMetadataがfrozenでイミュータブルであることを確認。"""
        metadata = FactorMetadata(
            name="test",
            description="test factor",
            category="size",
            required_data=["price"],
            frequency="daily",
        )

        with pytest.raises(FrozenInstanceError):
            metadata.name = "changed"

    def test_正常系_category値の検証(self) -> None:
        """categoryフィールドが有効なLiteral値を受け付けることを確認。"""
        valid_categories = ["price", "value", "quality", "size", "macro", "alternative"]

        for category in valid_categories:
            metadata = FactorMetadata(
                name="test",
                description="test",
                category=category,  # type: ignore[arg-type]
                required_data=["price"],
                frequency="daily",
            )
            assert metadata.category == category

    def test_正常系_frequency値の検証(self) -> None:
        """frequencyフィールドが有効なLiteral値を受け付けることを確認。"""
        valid_frequencies = ["daily", "weekly", "monthly", "quarterly"]

        for frequency in valid_frequencies:
            metadata = FactorMetadata(
                name="test",
                description="test",
                category="price",
                required_data=["price"],
                frequency=frequency,  # type: ignore[arg-type]
            )
            assert metadata.frequency == frequency


# =============================================================================
# FactorScore のテスト
# =============================================================================


class TestFactorScore:
    """FactorScoreのテスト。"""

    def test_正常系_必須フィールドで初期化(self) -> None:
        """必須フィールドでFactorScoreが作成できることを確認。"""
        scores = pd.DataFrame(
            {"AAPL": [0.5, 0.8, 0.3], "GOOGL": [0.6, 0.7, 0.4]},
            index=pd.date_range("2024-01-01", periods=3, freq="D"),
        )

        factor_score = FactorScore(
            name="momentum_score",
            scores=scores,
            normalization_method=NormalizationMethod.ZSCORE,
        )

        assert factor_score.name == "momentum_score"
        assert not factor_score.is_empty
        assert factor_score.normalization_method == NormalizationMethod.ZSCORE

    def test_正常系_全フィールドで初期化(self) -> None:
        """全フィールドを指定してFactorScoreが作成できることを確認。"""
        scores = pd.DataFrame(
            {"AAPL": [0.5, 0.8, 0.3]},
            index=pd.date_range("2024-01-01", periods=3, freq="D"),
        )
        raw_values = pd.DataFrame(
            {"AAPL": [100, 200, 150]},
            index=pd.date_range("2024-01-01", periods=3, freq="D"),
        )

        factor_score = FactorScore(
            name="value_score",
            scores=scores,
            normalization_method=NormalizationMethod.PERCENTILE,
            raw_values=raw_values,
            higher_is_better=False,
            calculated_at=datetime(2024, 1, 15, 10, 0, 0),
        )

        assert factor_score.name == "value_score"
        assert factor_score.normalization_method == NormalizationMethod.PERCENTILE
        assert factor_score.raw_values is not None
        assert factor_score.higher_is_better is False

    def test_正常系_symbolsがスコアの列名を返す(self) -> None:
        """symbolsプロパティがスコアの列名を返すことを確認。"""
        scores = pd.DataFrame(
            {"AAPL": [0.5], "GOOGL": [0.6], "MSFT": [0.7]},
            index=pd.date_range("2024-01-01", periods=1, freq="D"),
        )

        factor_score = FactorScore(
            name="test",
            scores=scores,
            normalization_method=NormalizationMethod.RANK,
        )

        assert factor_score.symbols == ["AAPL", "GOOGL", "MSFT"]

    def test_正常系_is_emptyが空データでTrue(self) -> None:
        """空のDataFrameでis_emptyがTrueを返すことを確認。"""
        empty_scores = pd.DataFrame()

        factor_score = FactorScore(
            name="empty",
            scores=empty_scores,
            normalization_method=NormalizationMethod.ZSCORE,
        )

        assert factor_score.is_empty

    def test_正常系_date_rangeが正しいタプルを返す(self) -> None:
        """date_rangeが正しい日付範囲のタプルを返すことを確認。"""
        scores = pd.DataFrame(
            {"AAPL": [0.1, 0.2, 0.3]},
            index=pd.date_range("2024-01-01", periods=3, freq="D"),
        )

        factor_score = FactorScore(
            name="test",
            scores=scores,
            normalization_method=NormalizationMethod.ZSCORE,
        )

        date_range = factor_score.date_range
        assert date_range is not None
        assert date_range[0].date() == datetime(2024, 1, 1).date()
        assert date_range[1].date() == datetime(2024, 1, 3).date()

    def test_正常系_空データでdate_rangeがNone(self) -> None:
        """空のDataFrameでdate_rangeがNoneを返すことを確認。"""
        empty_scores = pd.DataFrame()

        factor_score = FactorScore(
            name="empty",
            scores=empty_scores,
            normalization_method=NormalizationMethod.ZSCORE,
        )

        assert factor_score.date_range is None

    def test_正常系_デフォルト値が適用される(self) -> None:
        """デフォルト値が正しく適用されることを確認。"""
        scores = pd.DataFrame(
            {"AAPL": [0.5]},
            index=pd.date_range("2024-01-01", periods=1, freq="D"),
        )

        factor_score = FactorScore(
            name="test",
            scores=scores,
            normalization_method=NormalizationMethod.ZSCORE,
        )

        assert factor_score.raw_values is None
        assert factor_score.higher_is_better is True
        # calculated_at should be set automatically
        assert factor_score.calculated_at is not None


# =============================================================================
# Docstring のテスト
# =============================================================================


class TestDocstrings:
    """Docstringの存在確認テスト。"""

    def test_正常系_FactorResultにdocstringがある(self) -> None:
        """FactorResultにdocstringが存在することを確認。"""
        assert FactorResult.__doc__ is not None
        assert len(FactorResult.__doc__) > 0

    def test_正常系_FactorMetadataにdocstringがある(self) -> None:
        """FactorMetadataにdocstringが存在することを確認。"""
        assert FactorMetadata.__doc__ is not None
        assert len(FactorMetadata.__doc__) > 0

    def test_正常系_FactorScoreにdocstringがある(self) -> None:
        """FactorScoreにdocstringが存在することを確認。"""
        assert FactorScore.__doc__ is not None
        assert len(FactorScore.__doc__) > 0
