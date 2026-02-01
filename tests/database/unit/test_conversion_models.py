"""Unit tests for format conversion Pydantic models.

Issue #951: Parquet/JSON形式間のフォーマット変換ユーティリティ

テストTODOリスト:
- [x] TypeMapping 基本テスト
- [x] ConversionOptions 基本テスト
- [x] ConversionResult 正常系テスト
- [x] ConversionResult 異常系テスト
- [x] ConversionResult factory methods テスト
- [x] バリデーションエラーテスト
"""

from pathlib import Path

import pytest
from database.types import (
    ConversionOptions,
    ConversionResult,
    TypeMapping,
)
from pydantic import ValidationError


class TestTypeMapping:
    """TypeMapping モデルのテスト。"""

    def test_正常系_基本的なマッピング作成(self) -> None:
        """TypeMappingを正常に作成できることを確認。"""
        mapping = TypeMapping(
            column_name="user_id",
            source_type="int64",
            target_type="integer",
        )

        assert mapping.column_name == "user_id"
        assert mapping.source_type == "int64"
        assert mapping.target_type == "integer"

    def test_正常系_frozenモデルで不変(self) -> None:
        """frozenモデルが変更不可であることを確認。"""
        mapping = TypeMapping(
            column_name="name",
            source_type="string",
            target_type="str",
        )

        with pytest.raises(ValidationError):
            mapping.column_name = "new_name"  # type: ignore[misc]

    def test_異常系_空のカラム名でエラー(self) -> None:
        """空のカラム名でバリデーションエラーが発生することを確認。"""
        with pytest.raises(ValidationError, match="at least 1 character"):
            TypeMapping(
                column_name="",
                source_type="int64",
                target_type="integer",
            )

    def test_異常系_空白のみのカラム名でエラー(self) -> None:
        """空白のみのカラム名でバリデーションエラーが発生することを確認。"""
        with pytest.raises(ValidationError, match="empty or whitespace"):
            TypeMapping(
                column_name="   ",
                source_type="int64",
                target_type="integer",
            )

    def test_正常系_空白を含むカラム名はトリム(self) -> None:
        """前後の空白がトリムされることを確認。"""
        mapping = TypeMapping(
            column_name="  user_id  ",
            source_type="int64",
            target_type="integer",
        )

        assert mapping.column_name == "user_id"


class TestConversionOptions:
    """ConversionOptions モデルのテスト。"""

    def test_正常系_デフォルト値で作成(self) -> None:
        """デフォルト値でConversionOptionsを作成できることを確認。"""
        options = ConversionOptions()

        assert options.compression is None
        assert options.orient == "records"
        assert options.date_format == "iso"
        assert options.infer_types is True

    def test_正常系_全オプション指定(self) -> None:
        """全オプションを指定して作成できることを確認。"""
        options = ConversionOptions(
            compression="gzip",
            orient="columns",
            date_format="epoch",
            infer_types=False,
        )

        assert options.compression == "gzip"
        assert options.orient == "columns"
        assert options.date_format == "epoch"
        assert options.infer_types is False

    def test_正常系_frozenモデルで不変(self) -> None:
        """frozenモデルが変更不可であることを確認。"""
        options = ConversionOptions()

        with pytest.raises(ValidationError):
            options.compression = "snappy"  # type: ignore[misc]

    def test_異常系_不正な圧縮方式でエラー(self) -> None:
        """不正な圧縮方式でバリデーションエラーが発生することを確認。"""
        with pytest.raises(ValidationError):
            ConversionOptions(compression="invalid")  # type: ignore[arg-type]

    def test_異常系_不正なorientでエラー(self) -> None:
        """不正なorientでバリデーションエラーが発生することを確認。"""
        with pytest.raises(ValidationError):
            ConversionOptions(orient="invalid")  # type: ignore[arg-type]


class TestConversionResult:
    """ConversionResult モデルのテスト。"""

    def test_正常系_成功結果の作成(self) -> None:
        """成功結果を正常に作成できることを確認。"""
        result = ConversionResult(
            success=True,
            input_path=Path("data.parquet"),
            output_path=Path("data.json"),
            rows_converted=1000,
            columns=["id", "name", "value"],
        )

        assert result.success is True
        assert result.input_path == Path("data.parquet")
        assert result.output_path == Path("data.json")
        assert result.rows_converted == 1000
        assert result.columns == ["id", "name", "value"]
        assert result.error_message is None
        assert result.type_mappings is None

    def test_正常系_失敗結果の作成(self) -> None:
        """失敗結果を正常に作成できることを確認。"""
        result = ConversionResult(
            success=False,
            input_path=Path("invalid.parquet"),
            output_path=Path("output.json"),
            rows_converted=0,
            columns=[],
            error_message="File not found",
        )

        assert result.success is False
        assert result.error_message == "File not found"
        assert result.rows_converted == 0

    def test_正常系_TypeMappingsを含む結果(self) -> None:
        """TypeMappingsを含む結果を作成できることを確認。"""
        mappings = [
            TypeMapping(column_name="id", source_type="int64", target_type="integer"),
            TypeMapping(column_name="name", source_type="string", target_type="str"),
        ]

        result = ConversionResult(
            success=True,
            input_path=Path("data.parquet"),
            output_path=Path("data.json"),
            rows_converted=100,
            columns=["id", "name"],
            type_mappings=mappings,
        )

        assert result.type_mappings is not None
        assert len(result.type_mappings) == 2
        assert result.type_mappings[0].column_name == "id"

    def test_異常系_成功なのにエラーメッセージがある(self) -> None:
        """success=Trueでerror_messageがあるとエラーになることを確認。"""
        with pytest.raises(
            ValidationError, match="error_message must be None when success is True"
        ):
            ConversionResult(
                success=True,
                input_path=Path("data.parquet"),
                output_path=Path("data.json"),
                rows_converted=100,
                columns=["id"],
                error_message="Should not have this",
            )

    def test_異常系_失敗なのにエラーメッセージがない(self) -> None:
        """success=Falseでerror_messageがないとエラーになることを確認。"""
        with pytest.raises(
            ValidationError, match="error_message is required when success is False"
        ):
            ConversionResult(
                success=False,
                input_path=Path("invalid.parquet"),
                output_path=Path("output.json"),
                rows_converted=0,
                columns=[],
            )

    def test_異常系_負の行数でエラー(self) -> None:
        """負の行数でバリデーションエラーが発生することを確認。"""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            ConversionResult(
                success=True,
                input_path=Path("data.parquet"),
                output_path=Path("data.json"),
                rows_converted=-1,
                columns=["id"],
            )

    def test_異常系_空のカラム名を含む(self) -> None:
        """空のカラム名を含むとバリデーションエラーが発生することを確認。"""
        with pytest.raises(ValidationError, match="empty or whitespace"):
            ConversionResult(
                success=True,
                input_path=Path("data.parquet"),
                output_path=Path("data.json"),
                rows_converted=100,
                columns=["id", "", "name"],
            )


class TestConversionResultFactoryMethods:
    """ConversionResult ファクトリメソッドのテスト。"""

    def test_正常系_create_success(self) -> None:
        """create_successファクトリメソッドのテスト。"""
        result = ConversionResult.create_success(
            input_path=Path("data.parquet"),
            output_path=Path("data.json"),
            rows_converted=500,
            columns=["id", "name", "value"],
        )

        assert result.success is True
        assert result.input_path == Path("data.parquet")
        assert result.output_path == Path("data.json")
        assert result.rows_converted == 500
        assert result.columns == ["id", "name", "value"]
        assert result.error_message is None

    def test_正常系_create_success_with_mappings(self) -> None:
        """create_successファクトリメソッドでtype_mappingsを渡せることを確認。"""
        mappings = [
            TypeMapping(column_name="id", source_type="int64", target_type="integer"),
        ]

        result = ConversionResult.create_success(
            input_path=Path("data.parquet"),
            output_path=Path("data.json"),
            rows_converted=100,
            columns=["id"],
            type_mappings=mappings,
        )

        assert result.type_mappings is not None
        assert len(result.type_mappings) == 1

    def test_正常系_create_failure(self) -> None:
        """create_failureファクトリメソッドのテスト。"""
        result = ConversionResult.create_failure(
            input_path=Path("invalid.parquet"),
            output_path=Path("output.json"),
            error_message="Invalid Parquet format",
        )

        assert result.success is False
        assert result.input_path == Path("invalid.parquet")
        assert result.output_path == Path("output.json")
        assert result.rows_converted == 0
        assert result.columns == []
        assert result.error_message == "Invalid Parquet format"
        assert result.type_mappings is None
