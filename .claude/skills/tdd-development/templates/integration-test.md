# 統合テストテンプレート

このテンプレートは統合テストの標準的な構造を提供します。

## ファイル配置

```
tests/{library}/integration/test_{module}_integration.py
```

## 基本構造

```python
"""Integration tests for {module_name} components.

This module demonstrates how to write integration tests that verify
the interaction between multiple components.
"""

from pathlib import Path

import pytest
from {package}.core import MainClass, MainConfig, process_data
from {package}.types import ItemDict
from {package}.utils import chunk_list, load_json_file, save_json_file
from {package}.utils.logging_config import get_logger

# モジュールレベルのロガー
logger = get_logger(__name__)


class SimpleDataProcessor:
    """Simple data processor for testing integration."""

    def process(self, data: list[ItemDict]) -> list[ItemDict]:
        """Process data by adding a processed flag."""
        logger.debug(f"Processing {len(data)} items")

        processed_data = []
        for item in data:
            processed_item = item.copy()
            processed_item["value"] = item["value"] * 2
            processed_item["processed"] = True
            processed_data.append(processed_item)

        logger.debug(f"Processed {len(processed_data)} items successfully")
        return processed_data


class TestMainClassIntegration:
    """Integration tests for MainClass with other components."""

    def test_正常系_MainClassとヘルパー関数の連携(self, temp_dir: Path) -> None:
        """MainClass とヘルパー関数が正しく連携することを確認。"""
        logger.debug("Starting MainClass and helper function integration test")

        # 1. 設定ファイルを JSON で作成
        config_data = {
            "name": "integration_test",
            "max_items": 5,
            "enable_validation": True,
        }
        config_file = temp_dir / "config.json"
        save_json_file(config_data, config_file)

        # 2. 設定ファイルを読み込んで MainClass を初期化
        loaded_config_data = load_json_file(config_file)
        config = MainConfig(
            name=loaded_config_data["name"],
            max_items=loaded_config_data["max_items"],
            enable_validation=loaded_config_data["enable_validation"],
        )
        main_instance = MainClass(config)

        # 3. テストデータを準備してアイテムを追加
        test_items = [
            {"id": 1, "name": "Item 1", "value": 10},
            {"id": 2, "name": "Item 2", "value": 20},
            {"id": 3, "name": "Item 3", "value": 30},
        ]

        for item in test_items:
            main_instance.add_item(item)

        # 4. データを取得してチャンク化
        all_items = main_instance.get_items()
        chunks = chunk_list(all_items, chunk_size=2)

        # 5. 検証
        assert len(all_items) == 3
        assert len(chunks) == 2  # [2, 1] に分割される
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 1

        logger.info("Integration test completed successfully")

    def test_正常系_データ処理パイプラインの統合(self, temp_dir: Path) -> None:
        """データ処理パイプライン全体の統合テスト。"""
        logger.debug("Starting data processing pipeline integration test")

        # 1. 入力データファイルを作成
        input_data = [
            {"id": 1, "name": "Data 1", "value": 5},
            {"id": 2, "name": "Data 2", "value": 10},
            {"id": 3, "name": "Data 3", "value": 15},
        ]
        input_file = temp_dir / "input.json"
        save_json_file({"items": input_data}, input_file)

        # 2. データファイルを読み込み
        file_data = load_json_file(input_file)
        items_data = file_data["items"]

        # 3. MainClass でデータ管理
        config = MainConfig(name="pipeline_test", max_items=10)
        main_instance = MainClass(config)

        for item in items_data:
            main_instance.add_item(item)

        # 4. データ処理
        processor = SimpleDataProcessor()
        raw_data = main_instance.get_items()
        processed_data = process_data(raw_data, processor)

        # 5. 結果をファイルに保存
        output_file = temp_dir / "output.json"
        save_json_file({"processed_items": processed_data}, output_file)

        # 6. 保存されたファイルを読み込んで検証
        result_data = load_json_file(output_file)
        result_items = result_data["processed_items"]

        # 検証
        assert len(result_items) == 3
        for i, item in enumerate(result_items):
            expected_value = input_data[i]["value"] * 2
            assert item["value"] == expected_value
            assert item["processed"] is True

        logger.info("Data processing pipeline test completed successfully")

    def test_正常系_エラーハンドリングとリカバリー(self, temp_dir: Path) -> None:
        """エラーハンドリングとリカバリーの統合テスト。"""
        logger.debug("Starting error handling and recovery integration test")

        # 1. 不正なデータを含むファイルを作成
        mixed_data = [
            {"id": 1, "name": "Valid Item", "value": 100},
            {"id": 2, "name": "", "value": 200},  # name が空（バリデーションエラー）
            {"id": 3, "name": "Another Valid", "value": 300},
        ]

        config = MainConfig(name="error_test", max_items=5, enable_validation=True)
        main_instance = MainClass(config)

        # 2. データを追加（エラーハンドリング）
        successful_items = []
        failed_items = []

        for item in mixed_data:
            try:
                main_instance.add_item(item)
                successful_items.append(item)
                logger.debug(f"Successfully added item: {item['id']}")
            except ValueError as e:
                failed_items.append(item)
                logger.warning(f"Failed to add item {item['id']}: {e}")

        # 3. 成功したデータのみを処理
        if successful_items:
            valid_data = main_instance.get_items()
            processor = SimpleDataProcessor()
            processed_data = process_data(valid_data, processor)

            # 結果を保存
            output_file = temp_dir / "recovered_output.json"
            save_json_file(
                {
                    "processed_items": processed_data,
                    "failed_items": failed_items,
                    "summary": {
                        "total_input": len(mixed_data),
                        "successful": len(successful_items),
                        "failed": len(failed_items),
                    },
                },
                output_file,
            )

            # 検証
            result = load_json_file(output_file)
            assert len(result["processed_items"]) == 2
            assert len(result["failed_items"]) == 1
            assert result["summary"]["total_input"] == 3

            logger.info("Error handling test completed successfully")

    def test_正常系_大量データ処理のパフォーマンス(self, temp_dir: Path) -> None:
        """大量データ処理時のパフォーマンステスト。"""
        logger.debug("Starting large data processing performance test")

        # 1. 大量のテストデータを生成
        large_dataset = [
            {"id": i, "name": f"Item {i}", "value": i * 10}
            for i in range(1, 1001)  # 1000 件のデータ
        ]

        # 2. MainClass で大量データを管理
        config = MainConfig(name="performance_test", max_items=1500)
        main_instance = MainClass(config)

        # データをバッチで追加
        batch_size = 100
        batches = chunk_list(large_dataset, batch_size)

        for batch_num, batch in enumerate(batches):
            logger.debug(f"Processing batch {batch_num + 1}/{len(batches)}")
            for item in batch:
                main_instance.add_item(item)

        # 3. 全データを取得して処理
        all_data = main_instance.get_items()
        processor = SimpleDataProcessor()
        processed_data = process_data(all_data, processor)

        # 4. 検証
        assert len(all_data) == 1000
        assert len(processed_data) == 1000

        logger.info(f"Large data processing test completed: {len(processed_data)} items")


class TestCascadeErrorHandling:
    """複数コンポーネント間でのエラーの連鎖処理テスト。"""

    def test_異常系_連鎖エラーハンドリング(self, temp_dir: Path) -> None:
        """複数コンポーネント間でのエラーの連鎖処理テスト。"""
        logger.debug("Starting cascade error handling test")

        # 1. 存在しないファイルの読み込みエラー
        nonexistent_file = temp_dir / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            load_json_file(nonexistent_file)

        # 2. 不正な JSON ファイルの処理
        invalid_json_file = temp_dir / "invalid.json"
        invalid_json_file.write_text("{ invalid json content", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_json_file(invalid_json_file)

        # 3. 容量制限エラーの処理
        config = MainConfig(name="limit_test", max_items=2)
        main_instance = MainClass(config)

        main_instance.add_item({"id": 1, "name": "Item 1", "value": 10})
        main_instance.add_item({"id": 2, "name": "Item 2", "value": 20})

        with pytest.raises(ValueError, match="max_items limit"):
            main_instance.add_item({"id": 3, "name": "Item 3", "value": 30})

        assert len(main_instance) == 2

        logger.info("Cascade error handling test completed successfully")


class TestMultiComponentIntegration:
    """複数コンポーネントの統合テスト。"""

    def test_正常系_ファイルIO_データ処理_チャンク化の統合(
        self, temp_dir: Path
    ) -> None:
        """ファイル IO、データ処理、チャンク化の完全な統合テスト。"""
        logger.debug("Starting comprehensive integration test")

        # 1. 複数のデータファイルを作成
        datasets = {
            "users": [
                {"id": 1, "name": "Alice", "value": 100},
                {"id": 2, "name": "Bob", "value": 150},
            ],
            "products": [
                {"id": 3, "name": "Product A", "value": 200},
                {"id": 4, "name": "Product B", "value": 250},
                {"id": 5, "name": "Product C", "value": 300},
            ],
        }

        data_files = {}
        for category, data in datasets.items():
            file_path = temp_dir / f"{category}.json"
            save_json_file({"items": data}, file_path)
            data_files[category] = file_path

        # 2. 各ファイルからデータを読み込み、統合
        all_items = []
        for category, file_path in data_files.items():
            file_data = load_json_file(file_path)
            items = file_data["items"]
            logger.debug(f"Loaded {len(items)} items from {category}")
            all_items.extend(items)

        # 3. MainClass で統合データを管理
        config = MainConfig(name="multi_component_test", max_items=10)
        main_instance = MainClass(config)

        for item in all_items:
            main_instance.add_item(item)

        # 4. データを処理
        processor = SimpleDataProcessor()
        managed_data = main_instance.get_items()
        processed_data = process_data(managed_data, processor)

        # 5. 検証
        assert len(processed_data) == 5
        for result in processed_data:
            assert result["processed"] is True

        logger.info("Comprehensive integration test completed successfully")
```

## フィクスチャ（conftest.py）

```python
"""Pytest fixtures for integration tests."""

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
```

## 統合テストの判定基準

以下の条件がある場合、統合テストを設計：

| 条件 | 例 |
|------|-----|
| 複数コンポーネントの連携 | A → B → C のパイプライン |
| 外部リソースへのアクセス | ファイル、DB、API |
| 非同期処理 | async/await を使用する処理 |
| トランザクション処理 | 複数操作をまとめて実行 |

## ベストプラクティス

### DO（推奨）

- ロガーを使用して処理の流れを記録
- 一時ディレクトリを使用してファイル I/O をテスト
- エラーケースも含めて連携をテスト
- 大量データでのパフォーマンスを確認

### DON'T（非推奨）

- 実際の外部サービスに直接接続（モックを使用）
- テスト間でデータを共有
- 順序に依存するテスト

## 参照

- 実装例: `template/tests/integration/test_example.py`
