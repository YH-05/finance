# Task 09: 為替データ取得の単体テスト作成

**Phase**: 2 - 為替データ
**依存**: Task 06, Task 07
**ファイル**: `tests/analyze/reporting/unit/test_currency.py`

## 概要

`CurrencyAnalyzer` と `CurrencyAnalyzer4Agent` の単体テストを作成する。

## テスト対象

### CurrencyAnalyzer

1. **正常系**: 為替データ取得
2. **正常系**: 期間別騰落率計算
3. **異常系**: 無効なサブグループ指定
4. **エッジケース**: データ欠損時の処理

### CurrencyAnalyzer4Agent

1. **正常系**: JSON形式での出力
2. **正常系**: サマリー情報の計算
3. **正常系**: データ鮮度情報の計算
4. **正常系**: to_dict() の構造検証

## テスト実装

```python
"""為替データ取得のテスト."""

import pytest
from pandas import DataFrame

from analyze.reporting.currency import CurrencyAnalyzer
from analyze.reporting.currency_agent import (
    CurrencyAnalyzer4Agent,
    CurrencyResult,
)


class TestCurrencyAnalyzer:
    """CurrencyAnalyzer のテスト."""

    def test_正常系_為替データを取得できる(self) -> None:
        """yfinance から為替データを取得できることを確認."""
        analyzer = CurrencyAnalyzer()
        data = analyzer.get_currency_data("jpy_crosses")

        assert isinstance(data, DataFrame)
        assert not data.empty
        assert "USDJPY=X" in data["symbol"].unique()

    def test_正常系_期間別騰落率を計算できる(self) -> None:
        """期間別の騰落率を正しく計算."""
        analyzer = CurrencyAnalyzer()
        returns = analyzer.get_currency_performance("jpy_crosses")

        assert not returns.empty
        assert "return_pct" in returns.columns
        assert "period" in returns.columns

    def test_異常系_無効なサブグループでエラー(self) -> None:
        """存在しないサブグループ指定時にエラー."""
        analyzer = CurrencyAnalyzer()
        with pytest.raises(ValueError):
            analyzer.get_currency_data("invalid_subgroup")


class TestCurrencyAnalyzer4Agent:
    """CurrencyAnalyzer4Agent のテスト."""

    def test_正常系_JSON形式で出力できる(self) -> None:
        """結果を JSON シリアライズ可能な形式で取得."""
        analyzer = CurrencyAnalyzer4Agent()
        result = analyzer.get_currency_performance("jpy_crosses")

        assert isinstance(result, CurrencyResult)
        result_dict = result.to_dict()

        assert result_dict["group"] == "currencies"
        assert result_dict["subgroup"] == "jpy_crosses"
        assert result_dict["base_currency"] == "JPY"

    def test_正常系_サマリー情報が含まれる(self) -> None:
        """最強/最弱通貨のサマリーが含まれる."""
        analyzer = CurrencyAnalyzer4Agent()
        result = analyzer.get_currency_performance("jpy_crosses")
        result_dict = result.to_dict()

        assert "summary" in result_dict
        assert "strongest_currency" in result_dict["summary"]
        assert "weakest_currency" in result_dict["summary"]

    def test_正常系_全通貨ペアが含まれる(self) -> None:
        """6通貨ペアすべてが含まれる."""
        analyzer = CurrencyAnalyzer4Agent()
        result = analyzer.get_currency_performance("jpy_crosses")
        result_dict = result.to_dict()

        expected_pairs = [
            "USDJPY=X", "EURJPY=X", "GBPJPY=X",
            "AUDJPY=X", "CADJPY=X", "CHFJPY=X",
        ]
        for pair in expected_pairs:
            assert pair in result_dict["symbols"]
```

## テスト実行

```bash
# 単体テストのみ
uv run pytest tests/analyze/reporting/unit/test_currency.py -v

# カバレッジ付き
uv run pytest tests/analyze/reporting/unit/test_currency.py --cov=analyze.reporting.currency
```

## 受け入れ条件

- [ ] 全テストケースがパスする
- [ ] カバレッジ 80% 以上
- [ ] 日本語テスト名で意図が明確
- [ ] 6通貨ペアすべてのテストを含む
