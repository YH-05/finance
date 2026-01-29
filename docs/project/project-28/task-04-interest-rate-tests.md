# Task 04: 金利データ取得の単体テスト作成

**Phase**: 1 - 金利データ
**依存**: Task 01, Task 02
**ファイル**: `tests/analyze/reporting/unit/test_interest_rate.py`

## 概要

`InterestRateAnalyzer` と `InterestRateAnalyzer4Agent` の単体テストを作成する。

## テスト対象

### InterestRateAnalyzer

1. **正常系**: 金利データ取得
2. **正常系**: 期間別変化量計算
3. **正常系**: イールドカーブ分析
4. **異常系**: API エラー時の挙動
5. **エッジケース**: データ欠損時の処理

### InterestRateAnalyzer4Agent

1. **正常系**: JSON形式での出力
2. **正常系**: データ鮮度情報の計算
3. **正常系**: to_dict() の構造検証

## テスト実装

```python
"""金利データ取得のテスト."""

import pytest
from pandas import DataFrame

from analyze.reporting.interest_rate import InterestRateAnalyzer
from analyze.reporting.interest_rate_agent import (
    InterestRateAnalyzer4Agent,
    InterestRateResult,
)


class TestInterestRateAnalyzer:
    """InterestRateAnalyzer のテスト."""

    def test_正常系_金利データを取得できる(self) -> None:
        """FRED から金利データを取得できることを確認."""
        analyzer = InterestRateAnalyzer()
        data = analyzer.get_interest_rate_data()

        assert isinstance(data, DataFrame)
        assert not data.empty
        assert "DGS10" in data["symbol"].unique()

    def test_正常系_期間別変化量を計算できる(self) -> None:
        """期間別の変化量（差分）を正しく計算."""
        # ...

    def test_正常系_イールドカーブ分析ができる(self) -> None:
        """逆イールド判定を正しく行う."""
        analyzer = InterestRateAnalyzer()
        result = analyzer.get_yield_curve_analysis()

        assert "2y_10y_spread" in result
        assert "is_inverted" in result
        assert isinstance(result["is_inverted"], bool)


class TestInterestRateAnalyzer4Agent:
    """InterestRateAnalyzer4Agent のテスト."""

    def test_正常系_JSON形式で出力できる(self) -> None:
        """結果を JSON シリアライズ可能な形式で取得."""
        analyzer = InterestRateAnalyzer4Agent()
        result = analyzer.get_interest_rate_performance()

        assert isinstance(result, InterestRateResult)
        result_dict = result.to_dict()

        assert result_dict["group"] == "interest_rates"
        assert "data" in result_dict
        assert "yield_curve" in result_dict

    def test_正常系_必須フィールドが含まれる(self) -> None:
        """出力に必須フィールドが含まれることを確認."""
        analyzer = InterestRateAnalyzer4Agent()
        result = analyzer.get_interest_rate_performance()
        result_dict = result.to_dict()

        # 必須シリーズの確認
        for series in ["DGS2", "DGS10", "DGS30", "FEDFUNDS", "T10Y2Y"]:
            assert series in result_dict["data"]

        # 各シリーズの必須フィールド確認
        for series_data in result_dict["data"].values():
            assert "name_ja" in series_data
            assert "latest_value" in series_data
            assert "changes" in series_data
```

## テスト実行

```bash
# 単体テストのみ
uv run pytest tests/analyze/reporting/unit/test_interest_rate.py -v

# カバレッジ付き
uv run pytest tests/analyze/reporting/unit/test_interest_rate.py --cov=analyze.reporting.interest_rate
```

## 受け入れ条件

- [ ] 全テストケースがパスする
- [ ] カバレッジ 80% 以上
- [ ] 日本語テスト名で意図が明確
- [ ] モック使用でAPI依存を分離（必要に応じて）
