"""Unit tests for the DataCollector abstract base class.

This module tests the DataCollector ABC including:
- Abstract method definitions
- Property implementations
- The collect() convenience method
"""

from abc import ABC

import pandas as pd
import pytest

from market.base_collector import DataCollector


class ConcreteDataCollector(DataCollector):
    """Concrete implementation for testing."""

    def __init__(self, *, should_validate: bool = True) -> None:
        self._should_validate = should_validate
        self.fetch_call_count = 0
        self.validate_call_count = 0
        self._data_to_return = pd.DataFrame({"value": [1, 2, 3]})

    def fetch(self, **kwargs) -> pd.DataFrame:
        self.fetch_call_count += 1
        self.last_kwargs = kwargs
        return self._data_to_return

    def validate(self, df: pd.DataFrame) -> bool:
        self.validate_call_count += 1
        return self._should_validate

    def set_data_to_return(self, df: pd.DataFrame) -> None:
        self._data_to_return = df


class TestDataCollectorAbstractMethods:
    """Test abstract method definitions."""

    def test_正常系_DataCollectorは抽象基底クラスである(self) -> None:
        assert issubclass(DataCollector, ABC)

    def test_正常系_fetchメソッドが抽象メソッドである(self) -> None:
        assert hasattr(DataCollector.fetch, "__isabstractmethod__")
        assert DataCollector.fetch.__isabstractmethod__ is True

    def test_正常系_validateメソッドが抽象メソッドである(self) -> None:
        assert hasattr(DataCollector.validate, "__isabstractmethod__")
        assert DataCollector.validate.__isabstractmethod__ is True

    def test_異常系_抽象メソッド未実装でインスタンス化できない(self) -> None:
        with pytest.raises(TypeError, match="abstract methods"):
            DataCollector()  # type: ignore[abstract]


class TestDataCollectorNameProperty:
    """Test the name property."""

    def test_正常系_nameプロパティがクラス名を返す(self) -> None:
        collector = ConcreteDataCollector()
        assert collector.name == "ConcreteDataCollector"

    def test_正常系_サブクラスで異なる名前が返る(self) -> None:
        class AnotherCollector(ConcreteDataCollector):
            pass

        collector = AnotherCollector()
        assert collector.name == "AnotherCollector"


class TestDataCollectorFetchMethod:
    """Test the fetch abstract method implementation."""

    def test_正常系_fetchメソッドがDataFrameを返す(self) -> None:
        collector = ConcreteDataCollector()
        result = collector.fetch()
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_正常系_fetchメソッドがkwargsを受け取る(self) -> None:
        collector = ConcreteDataCollector()
        collector.fetch(start_date="2024-01-01", symbol="TEST")
        assert collector.last_kwargs == {"start_date": "2024-01-01", "symbol": "TEST"}


class TestDataCollectorValidateMethod:
    """Test the validate abstract method implementation."""

    def test_正常系_validateメソッドがTrueを返す(self) -> None:
        collector = ConcreteDataCollector(should_validate=True)
        df = pd.DataFrame({"value": [1, 2, 3]})
        assert collector.validate(df) is True

    def test_正常系_validateメソッドがFalseを返す(self) -> None:
        collector = ConcreteDataCollector(should_validate=False)
        df = pd.DataFrame({"value": [1, 2, 3]})
        assert collector.validate(df) is False


class TestDataCollectorCollectMethod:
    """Test the collect convenience method."""

    def test_正常系_collectがfetchとvalidateを呼び出す(self) -> None:
        collector = ConcreteDataCollector(should_validate=True)
        result = collector.collect()

        assert collector.fetch_call_count == 1
        assert collector.validate_call_count == 1
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_正常系_collectがkwargsをfetchに渡す(self) -> None:
        collector = ConcreteDataCollector(should_validate=True)
        collector.collect(start_date="2024-01-01", end_date="2024-12-31")

        assert collector.last_kwargs == {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }

    def test_異常系_validateがFalseでValueError(self) -> None:
        collector = ConcreteDataCollector(should_validate=False)

        with pytest.raises(ValueError, match="Data validation failed"):
            collector.collect()

    def test_正常系_空のDataFrameでもvalidate結果に従う(self) -> None:
        collector = ConcreteDataCollector(should_validate=True)
        collector.set_data_to_return(pd.DataFrame())

        result = collector.collect()
        assert len(result) == 0


class TestDataCollectorDocstrings:
    """Test that all public methods and classes have docstrings."""

    def test_正常系_DataCollectorクラスにDocstringがある(self) -> None:
        assert DataCollector.__doc__ is not None
        assert "Abstract base class" in DataCollector.__doc__

    def test_正常系_fetchメソッドにDocstringがある(self) -> None:
        assert DataCollector.fetch.__doc__ is not None
        assert "Fetch data" in DataCollector.fetch.__doc__

    def test_正常系_validateメソッドにDocstringがある(self) -> None:
        assert DataCollector.validate.__doc__ is not None
        assert "Validate" in DataCollector.validate.__doc__

    def test_正常系_collectメソッドにDocstringがある(self) -> None:
        assert DataCollector.collect.__doc__ is not None
        assert "convenience method" in DataCollector.collect.__doc__

    def test_正常系_nameプロパティにDocstringがある(self) -> None:
        assert DataCollector.name.fget.__doc__ is not None
        assert "name" in DataCollector.name.fget.__doc__


class TestDataCollectorExports:
    """Test module exports."""

    def test_正常系_DataCollectorがエクスポートされている(self) -> None:
        from market.base_collector import __all__

        assert "DataCollector" in __all__
