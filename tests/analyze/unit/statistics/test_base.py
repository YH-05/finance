"""Unit tests for the StatisticalAnalyzer abstract base class.

This module tests the StatisticalAnalyzer ABC including:
- Abstract method definitions
- Property implementations
- The analyze() convenience method
"""

from abc import ABC
from typing import Any

import pandas as pd
import pytest

from analyze.statistics.base import StatisticalAnalyzer


class ConcreteStatisticalAnalyzer(StatisticalAnalyzer):
    """Concrete implementation for testing."""

    def __init__(self, *, should_validate: bool = True) -> None:
        self._should_validate = should_validate
        self.calculate_call_count = 0
        self.validate_call_count = 0
        self._result_to_return = pd.DataFrame({"result": [1.0, 2.0, 3.0]})

    def calculate(self, df: pd.DataFrame, **kwargs: Any) -> pd.DataFrame:
        self.calculate_call_count += 1
        self.last_kwargs = kwargs
        return self._result_to_return

    def validate_input(self, df: pd.DataFrame) -> bool:
        self.validate_call_count += 1
        return self._should_validate

    def set_result_to_return(self, df: pd.DataFrame) -> None:
        self._result_to_return = df


class TestStatisticalAnalyzerAbstractMethods:
    """Test abstract method definitions."""

    def test_正常系_StatisticalAnalyzerは抽象基底クラスである(self) -> None:
        assert issubclass(StatisticalAnalyzer, ABC)

    def test_正常系_calculateメソッドが抽象メソッドである(self) -> None:
        assert hasattr(StatisticalAnalyzer.calculate, "__isabstractmethod__")
        assert StatisticalAnalyzer.calculate.__isabstractmethod__ is True

    def test_正常系_validate_inputメソッドが抽象メソッドである(self) -> None:
        assert hasattr(StatisticalAnalyzer.validate_input, "__isabstractmethod__")
        assert StatisticalAnalyzer.validate_input.__isabstractmethod__ is True

    def test_異常系_抽象メソッド未実装でインスタンス化できない(self) -> None:
        with pytest.raises(TypeError, match="abstract methods"):
            StatisticalAnalyzer()  # type: ignore[abstract]


class TestStatisticalAnalyzerNameProperty:
    """Test the name property."""

    def test_正常系_nameプロパティがクラス名を返す(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer()
        assert analyzer.name == "ConcreteStatisticalAnalyzer"

    def test_正常系_サブクラスで異なる名前が返る(self) -> None:
        class AnotherAnalyzer(ConcreteStatisticalAnalyzer):
            pass

        analyzer = AnotherAnalyzer()
        assert analyzer.name == "AnotherAnalyzer"


class TestStatisticalAnalyzerCalculateMethod:
    """Test the calculate abstract method implementation."""

    def test_正常系_calculateメソッドがDataFrameを返す(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer()
        df = pd.DataFrame({"price": [100, 101, 102]})
        result = analyzer.calculate(df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_正常系_calculateメソッドがkwargsを受け取る(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer()
        df = pd.DataFrame({"price": [100, 101, 102]})
        analyzer.calculate(df, window=20, target="SPY")
        assert analyzer.last_kwargs == {"window": 20, "target": "SPY"}


class TestStatisticalAnalyzerValidateInputMethod:
    """Test the validate_input abstract method implementation."""

    def test_正常系_validate_inputメソッドがTrueを返す(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer(should_validate=True)
        df = pd.DataFrame({"price": [100, 101, 102]})
        assert analyzer.validate_input(df) is True

    def test_正常系_validate_inputメソッドがFalseを返す(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer(should_validate=False)
        df = pd.DataFrame({"price": [100, 101, 102]})
        assert analyzer.validate_input(df) is False


class TestStatisticalAnalyzerAnalyzeMethod:
    """Test the analyze convenience method."""

    def test_正常系_analyzeがvalidate_inputとcalculateを呼び出す(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer(should_validate=True)
        df = pd.DataFrame({"price": [100, 101, 102]})
        result = analyzer.analyze(df)

        assert analyzer.validate_call_count == 1
        assert analyzer.calculate_call_count == 1
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_正常系_analyzeがkwargsをcalculateに渡す(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer(should_validate=True)
        df = pd.DataFrame({"price": [100, 101, 102]})
        analyzer.analyze(df, window=60, benchmark="QQQ")

        assert analyzer.last_kwargs == {"window": 60, "benchmark": "QQQ"}

    def test_異常系_validate_inputがFalseでValueError(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer(should_validate=False)
        df = pd.DataFrame({"price": [100, 101, 102]})

        with pytest.raises(ValueError, match="Input validation failed"):
            analyzer.analyze(df)

    def test_正常系_空のDataFrameでもvalidate結果に従う(self) -> None:
        analyzer = ConcreteStatisticalAnalyzer(should_validate=True)
        analyzer.set_result_to_return(pd.DataFrame())

        df = pd.DataFrame({"price": [100, 101, 102]})
        result = analyzer.analyze(df)
        assert len(result) == 0


class TestStatisticalAnalyzerDocstrings:
    """Test that all public methods and classes have docstrings."""

    def test_正常系_StatisticalAnalyzerクラスにDocstringがある(self) -> None:
        assert StatisticalAnalyzer.__doc__ is not None
        assert "Abstract base class" in StatisticalAnalyzer.__doc__

    def test_正常系_calculateメソッドにDocstringがある(self) -> None:
        assert StatisticalAnalyzer.calculate.__doc__ is not None
        assert "statistical calculation" in StatisticalAnalyzer.calculate.__doc__

    def test_正常系_validate_inputメソッドにDocstringがある(self) -> None:
        assert StatisticalAnalyzer.validate_input.__doc__ is not None
        assert "Validate" in StatisticalAnalyzer.validate_input.__doc__

    def test_正常系_analyzeメソッドにDocstringがある(self) -> None:
        assert StatisticalAnalyzer.analyze.__doc__ is not None
        assert "convenience method" in StatisticalAnalyzer.analyze.__doc__

    def test_正常系_nameプロパティにDocstringがある(self) -> None:
        assert StatisticalAnalyzer.name.fget.__doc__ is not None
        assert "name" in StatisticalAnalyzer.name.fget.__doc__


class TestStatisticalAnalyzerExports:
    """Test module exports."""

    def test_正常系_StatisticalAnalyzerがエクスポートされている(self) -> None:
        from analyze.statistics.base import __all__

        assert "StatisticalAnalyzer" in __all__

    def test_正常系_パッケージからインポートできる(self) -> None:
        from analyze.statistics import StatisticalAnalyzer as Imported

        assert Imported is StatisticalAnalyzer
