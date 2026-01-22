# 単体テストテンプレート

このテンプレートは単体テストの標準的な構造を提供します。

## ファイル配置

```
tests/{library}/unit/test_{module}.py
```

## 基本構造

```python
"""Unit tests for {module_name} module."""

from typing import Any

import pytest
from {package}.{module} import (
    TargetClass,
    TargetConfig,
    target_function,
)


class TestTargetConfig:
    """Test TargetConfig class."""

    def test_正常系_デフォルト値で初期化される(self) -> None:
        """デフォルト値で Config が作成されることを確認。"""
        config = TargetConfig(name="test")

        assert config.name == "test"
        assert config.max_items == 100  # デフォルト値
        assert config.enable_validation is True  # デフォルト値

    def test_正常系_カスタム値で初期化される(self) -> None:
        """カスタム値で Config が作成されることを確認。"""
        config = TargetConfig(
            name="custom",
            max_items=50,
            enable_validation=False,
        )

        assert config.name == "custom"
        assert config.max_items == 50
        assert config.enable_validation is False

    def test_異常系_max_itemsが負の値でValueError(self) -> None:
        """max_items が負の値の場合、ValueError が発生することを確認。"""
        with pytest.raises(ValueError, match="max_items must be positive"):
            TargetConfig(name="test", max_items=-1)


class TestTargetClass:
    """Test TargetClass."""

    def test_正常系_初期化時は空のリスト(
        self,
        target_instance: TargetClass,
    ) -> None:
        """初期化時にデータが空であることを確認。"""
        assert len(target_instance) == 0
        assert target_instance.get_items() == []

    def test_正常系_アイテムを追加できる(
        self,
        target_instance: TargetClass,
    ) -> None:
        """アイテムを正常に追加できることを確認。"""
        item = {"id": 1, "name": "test_item", "value": 42}
        target_instance.add_item(item)

        assert len(target_instance) == 1
        assert target_instance.get_items() == [item]

    def test_正常系_複数のアイテムを追加できる(
        self,
        target_instance: TargetClass,
        sample_data: list[dict[str, Any]],
    ) -> None:
        """複数のアイテムを追加できることを確認。"""
        for item in sample_data:
            target_instance.add_item(item)

        assert len(target_instance) == len(sample_data)
        assert target_instance.get_items() == sample_data

    def test_正常系_フィルタリングが機能する(
        self,
        target_instance: TargetClass,
        sample_data: list[dict[str, Any]],
    ) -> None:
        """フィルタリングが正しく機能することを確認。"""
        for item in sample_data:
            target_instance.add_item(item)

        filtered = target_instance.get_items(
            filter_key="value",
            filter_value=200,
        )

        assert len(filtered) == 1
        assert filtered[0]["id"] == 2

    def test_異常系_最大数を超えるとValueError(
        self,
        target_config: TargetConfig,
    ) -> None:
        """最大数を超えてアイテムを追加しようとするとエラーになることを確認。"""
        target_config.max_items = 2
        instance = TargetClass(target_config)

        instance.add_item({"id": 1, "name": "item1", "value": 10})
        instance.add_item({"id": 2, "name": "item2", "value": 20})

        with pytest.raises(ValueError, match="max_items limit"):
            instance.add_item({"id": 3, "name": "item3", "value": 30})

    def test_異常系_空の辞書でValueError(
        self,
        target_instance: TargetClass,
    ) -> None:
        """空の辞書を追加しようとするとエラーになることを確認。"""
        with pytest.raises(ValueError, match="Missing required fields"):
            target_instance.add_item({})


class TestTargetFunction:
    """Test target_function."""

    def test_正常系_データが処理される(
        self,
        sample_data: list[dict[str, Any]],
    ) -> None:
        """データが正しく処理されることを確認。"""
        result = target_function(sample_data)

        assert len(result) == len(sample_data)
        assert all(item.get("processed") for item in result)

    def test_異常系_バリデーション有効で空データはエラー(self) -> None:
        """バリデーション有効時、空データでエラーになることを確認。"""
        with pytest.raises(ValueError, match="Data cannot be empty"):
            target_function([], validate=True)

    def test_正常系_バリデーション無効で空データも処理できる(self) -> None:
        """バリデーション無効時、空データも処理できることを確認。"""
        result = target_function([], validate=False)
        assert result == []

    @pytest.mark.parametrize(
        "input_data,expected_length",
        [
            ([{"id": 1}], 1),
            ([{"id": 1}, {"id": 2}], 2),
            ([{"id": i} for i in range(10)], 10),
        ],
    )
    def test_パラメトライズ_様々なサイズのデータを処理できる(
        self,
        input_data: list[dict[str, Any]],
        expected_length: int,
    ) -> None:
        """様々なサイズのデータを処理できることを確認。"""
        result = target_function(input_data)
        assert len(result) == expected_length
```

## フィクスチャ（conftest.py）

```python
"""Pytest configuration and fixtures."""

import pytest
from typing import Any
from {package}.{module} import TargetClass, TargetConfig


@pytest.fixture
def target_config() -> TargetConfig:
    """Create a test configuration."""
    return TargetConfig(
        name="test",
        max_items=10,
        enable_validation=True,
    )


@pytest.fixture
def target_instance(target_config: TargetConfig) -> TargetClass:
    """Create a test TargetClass instance."""
    return TargetClass(target_config)


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    """Create sample data for testing."""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]
```

## 命名規則

| パターン | 例 |
|---------|-----|
| 正常系 | `test_正常系_有効なデータで処理成功` |
| 異常系 | `test_異常系_不正なサイズでValueError` |
| エッジケース | `test_エッジケース_空リストで空結果` |
| パラメトライズ | `test_パラメトライズ_様々なサイズで正しく動作` |

## 参照

- 実装例: `template/tests/unit/test_example.py`
- フィクスチャ例: `template/tests/conftest.py`
