"""Unit tests for Parquet schema definitions.

このモジュールは以下のスキーマ定義と検証関数をテストします:
- StockPriceSchema: 株価データスキーマ
- EconomicIndicatorSchema: 経済指標データスキーマ
- validate_stock_price_dataframe(): 株価データフレーム検証関数
- validate_economic_indicator_dataframe(): 経済指標データフレーム検証関数

TDD Red フェーズ: 実装前にテストを作成
"""

import datetime

import pandas as pd
import pytest

from database.parquet_schema import (
    EconomicIndicatorSchema,
    StockPriceSchema,
    ValidationError,
    validate_economic_indicator_dataframe,
    validate_stock_price_dataframe,
)

# =============================================================================
# テスト TODO リスト
# =============================================================================
#
# 株価データスキーマ (StockPriceSchema):
# - [x] test_正常系_有効な株価データでTrue
# - [x] test_異常系_必須カラム欠落でValidationError
# - [x] test_異常系_型不一致でValidationError
# - [x] test_エッジケース_空のDataFrameでValidationError
#
# 経済指標データスキーマ (EconomicIndicatorSchema):
# - [x] test_正常系_有効な経済指標データでTrue
# - [x] test_異常系_必須カラム欠落でValidationError
# - [x] test_異常系_型不一致でValidationError
# - [x] test_エッジケース_空のDataFrameでValidationError
#
# =============================================================================


class TestStockPriceSchema:
    """株価データスキーマ (StockPriceSchema) のテスト。"""

    def test_正常系_有効な株価データでTrue(self) -> None:
        """有効な株価データで validate_stock_price_dataframe が True を返すことを確認。"""
        df = pd.DataFrame(
            {
                "symbol": ["AAPL", "AAPL", "GOOGL"],
                "date": [
                    datetime.date(2024, 1, 1),
                    datetime.date(2024, 1, 2),
                    datetime.date(2024, 1, 1),
                ],
                "open": [150.0, 151.0, 140.0],
                "high": [155.0, 156.0, 145.0],
                "low": [149.0, 150.0, 139.0],
                "close": [154.0, 155.0, 144.0],
                "volume": [1000000, 1100000, 2000000],
                "adjusted_close": [154.0, 155.0, 144.0],
            }
        )

        result = validate_stock_price_dataframe(df)

        assert result is True

    def test_異常系_必須カラム欠落でValidationError(self) -> None:
        """必須カラムが欠落している場合、ValidationError が発生することを確認。"""
        # 'volume' カラムが欠落
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "date": [datetime.date(2024, 1, 1)],
                "open": [150.0],
                "high": [155.0],
                "low": [149.0],
                "close": [154.0],
                # "volume" は欠落
                "adjusted_close": [154.0],
            }
        )

        with pytest.raises(ValidationError, match=r"Missing required column.*volume"):
            validate_stock_price_dataframe(df)

    def test_異常系_型不一致でValidationError(self) -> None:
        """カラムの型が不一致の場合、ValidationError が発生することを確認。"""
        # volume が文字列（int であるべき）
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "date": [datetime.date(2024, 1, 1)],
                "open": [150.0],
                "high": [155.0],
                "low": [149.0],
                "close": [154.0],
                "volume": ["invalid"],  # 文字列（不正）
                "adjusted_close": [154.0],
            }
        )

        with pytest.raises(ValidationError, match=r"Type mismatch.*volume"):
            validate_stock_price_dataframe(df)

    def test_エッジケース_空のDataFrameでValidationError(self) -> None:
        """空の DataFrame の場合、ValidationError が発生することを確認。"""
        df = pd.DataFrame()

        with pytest.raises(ValidationError, match="DataFrame is empty"):
            validate_stock_price_dataframe(df)

    def test_異常系_複数カラム欠落でValidationError(self) -> None:
        """複数のカラムが欠落している場合、ValidationError が発生することを確認。"""
        # symbol, date のみで他は全て欠落
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "date": [datetime.date(2024, 1, 1)],
            }
        )

        with pytest.raises(ValidationError, match="Missing required column"):
            validate_stock_price_dataframe(df)

    @pytest.mark.parametrize(
        "invalid_column,invalid_value,expected_type",
        [
            ("open", "invalid", "float"),
            ("high", "invalid", "float"),
            ("low", "invalid", "float"),
            ("close", "invalid", "float"),
            ("adjusted_close", "invalid", "float"),
        ],
    )
    def test_パラメトライズ_各float型カラムの型不一致でValidationError(
        self,
        invalid_column: str,
        invalid_value: str,
        expected_type: str,
    ) -> None:
        """各 float 型カラムに不正な値がある場合、ValidationError が発生することを確認。"""
        base_data = {
            "symbol": ["AAPL"],
            "date": [datetime.date(2024, 1, 1)],
            "open": [150.0],
            "high": [155.0],
            "low": [149.0],
            "close": [154.0],
            "volume": [1000000],
            "adjusted_close": [154.0],
        }
        base_data[invalid_column] = [invalid_value]
        df = pd.DataFrame(base_data)

        with pytest.raises(ValidationError, match=rf"Type mismatch.*{invalid_column}"):
            validate_stock_price_dataframe(df)


class TestEconomicIndicatorSchema:
    """経済指標データスキーマ (EconomicIndicatorSchema) のテスト。"""

    def test_正常系_有効な経済指標データでTrue(self) -> None:
        """有効な経済指標データで validate_economic_indicator_dataframe が True を返すことを確認。"""
        df = pd.DataFrame(
            {
                "series_id": ["GDP", "CPI", "UNEMPLOYMENT"],
                "date": [
                    datetime.date(2024, 1, 1),
                    datetime.date(2024, 1, 1),
                    datetime.date(2024, 1, 1),
                ],
                "value": [25000.5, 3.2, 4.1],
                "unit": ["billions_usd", "percent", "percent"],
            }
        )

        result = validate_economic_indicator_dataframe(df)

        assert result is True

    def test_異常系_必須カラム欠落でValidationError(self) -> None:
        """必須カラムが欠落している場合、ValidationError が発生することを確認。"""
        # 'unit' カラムが欠落
        df = pd.DataFrame(
            {
                "series_id": ["GDP"],
                "date": [datetime.date(2024, 1, 1)],
                "value": [25000.5],
                # "unit" は欠落
            }
        )

        with pytest.raises(ValidationError, match=r"Missing required column.*unit"):
            validate_economic_indicator_dataframe(df)

    def test_異常系_型不一致でValidationError(self) -> None:
        """カラムの型が不一致の場合、ValidationError が発生することを確認。"""
        # value が文字列（float であるべき）
        df = pd.DataFrame(
            {
                "series_id": ["GDP"],
                "date": [datetime.date(2024, 1, 1)],
                "value": ["invalid"],  # 文字列（不正）
                "unit": ["billions_usd"],
            }
        )

        with pytest.raises(ValidationError, match=r"Type mismatch.*value"):
            validate_economic_indicator_dataframe(df)

    def test_エッジケース_空のDataFrameでValidationError(self) -> None:
        """空の DataFrame の場合、ValidationError が発生することを確認。"""
        df = pd.DataFrame()

        with pytest.raises(ValidationError, match="DataFrame is empty"):
            validate_economic_indicator_dataframe(df)

    def test_異常系_series_idがNoneでValidationError(self) -> None:
        """series_id が None の場合、ValidationError が発生することを確認。"""
        df = pd.DataFrame(
            {
                "series_id": [None],
                "date": [datetime.date(2024, 1, 1)],
                "value": [25000.5],
                "unit": ["billions_usd"],
            }
        )

        with pytest.raises(ValidationError, match=r"Null values.*series_id"):
            validate_economic_indicator_dataframe(df)

    def test_異常系_dateがNoneでValidationError(self) -> None:
        """date が None の場合、ValidationError が発生することを確認。"""
        df = pd.DataFrame(
            {
                "series_id": ["GDP"],
                "date": [None],
                "value": [25000.5],
                "unit": ["billions_usd"],
            }
        )

        with pytest.raises(ValidationError, match=r"Null values.*date"):
            validate_economic_indicator_dataframe(df)

    @pytest.mark.parametrize(
        "series_id,unit",
        [
            ("GDP", "billions_usd"),
            ("CPI", "percent"),
            ("UNEMPLOYMENT", "percent"),
            ("INTEREST_RATE", "percent"),
            ("INFLATION", "percent"),
        ],
    )
    def test_パラメトライズ_様々な経済指標で有効(
        self,
        series_id: str,
        unit: str,
    ) -> None:
        """様々な経済指標で正常に検証できることを確認。"""
        df = pd.DataFrame(
            {
                "series_id": [series_id],
                "date": [datetime.date(2024, 1, 1)],
                "value": [100.0],
                "unit": [unit],
            }
        )

        result = validate_economic_indicator_dataframe(df)

        assert result is True


class TestSchemaDefinitions:
    """スキーマ定義クラスのテスト。"""

    def test_StockPriceSchemaのフィールド定義(self) -> None:
        """StockPriceSchema が正しいフィールドを持つことを確認。"""
        expected_fields = {
            "symbol": str,
            "date": datetime.date,
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": int,
            "adjusted_close": float,
        }

        # スキーマのフィールド定義を検証
        assert hasattr(StockPriceSchema, "fields")
        for field_name, field_type in expected_fields.items():
            assert field_name in StockPriceSchema.fields
            assert StockPriceSchema.fields[field_name] == field_type

    def test_EconomicIndicatorSchemaのフィールド定義(self) -> None:
        """EconomicIndicatorSchema が正しいフィールドを持つことを確認。"""
        expected_fields = {
            "series_id": str,
            "date": datetime.date,
            "value": float,
            "unit": str,
        }

        # スキーマのフィールド定義を検証
        assert hasattr(EconomicIndicatorSchema, "fields")
        for field_name, field_type in expected_fields.items():
            assert field_name in EconomicIndicatorSchema.fields
            assert EconomicIndicatorSchema.fields[field_name] == field_type


class TestValidationErrorDetails:
    """ValidationError の詳細情報のテスト。"""

    def test_ValidationError_欠落カラム情報を含む(self) -> None:
        """ValidationError が欠落カラムの情報を含むことを確認。"""
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "date": [datetime.date(2024, 1, 1)],
            }
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_stock_price_dataframe(df)

        # エラーメッセージに欠落カラムの情報が含まれることを確認
        error = exc_info.value
        assert hasattr(error, "missing_columns") or "Missing" in str(error)

    def test_ValidationError_型不一致情報を含む(self) -> None:
        """ValidationError が型不一致の情報を含むことを確認。"""
        df = pd.DataFrame(
            {
                "symbol": ["AAPL"],
                "date": [datetime.date(2024, 1, 1)],
                "open": [150.0],
                "high": [155.0],
                "low": [149.0],
                "close": [154.0],
                "volume": ["invalid"],  # 文字列（不正）
                "adjusted_close": [154.0],
            }
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_stock_price_dataframe(df)

        # エラーメッセージに型不一致の情報が含まれることを確認
        error = exc_info.value
        assert "volume" in str(error)
