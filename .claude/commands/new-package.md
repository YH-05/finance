---
description: モノレポ内に新しいPythonパッケージを作成する
---

# 新規パッケージの作成

現在のリポジトリ内に新しい Python パッケージを作成します。

**引数:** パッケージ名（snake_case）

**使用例:**

```bash
/new-package my_new_package
```

---

## ステップ 1: 引数検証と準備

1. パッケージ名を引数から取得する
2. パッケージ名が snake_case 形式であることを確認する
    - 不正な形式の場合: エラーメッセージを表示して終了
3. 既存パッケージとの重複をチェックする
    - `src/[パッケージ名]`が既に存在する場合: エラーメッセージを表示して終了
4. 以下のパスを生成する:
    - ソースディレクトリ: `src/[パッケージ名]/`
    - テストディレクトリ: `tests/[パッケージ名]/`

## ステップ 2: テンプレート参照

以下のテンプレートファイルを参照し、パッケージ名を置換して使用する:

| テンプレート                                            | 参照用途                 |
| ------------------------------------------------------- | ------------------------ |
| `template/src/template_package/__init__.py`             | パッケージ初期化の構造   |
| `template/src/template_package/types.py`                | 型定義の構造             |
| `template/src/template_package/utils/logging_config.py` | ロギング設定             |
| `template/tests/conftest.py`                            | テストフィクスチャの構造 |

## ステップ 3: パッケージ構造生成

以下のファイルを生成する:

### 3.1 メインパッケージ

**`src/[パッケージ名]/__init__.py`:**

```python
"""[パッケージ名] package."""

from .utils.logging_config import get_logger

__all__ = [
    "get_logger",
]

__version__ = "0.1.0"
```

**`src/[パッケージ名]/py.typed`:**

```text
# PEP 561 marker file
```

**`src/[パッケージ名]/README.md`:**

```markdown
# [パッケージ名]

[パッケージの簡潔な説明を記載]

## 概要

このパッケージは [目的] を提供します。

**現在のバージョン:** 0.1.0

## ディレクトリ構成

\`\`\`
[パッケージ名]/
├── **init**.py # 公開 API 定義（**version**含む）
├── py.typed # PEP 561 マーカー
├── types.py # 型定義
├── core/ # コアビジネスロジック
│ └── **init**.py
└── utils/ # ユーティリティ関数
├── **init**.py
└── logging_config.py # 構造化ロギング設定
\`\`\`

## 実装状況

| モジュール                | 状態        | 備考                                |
| ------------------------- | ----------- | ----------------------------------- |
| `types.py`                | ✅ 実装済み | 基本型定義                          |
| `utils/logging_config.py` | ✅ 実装済み | 構造化ロギング                      |
| `core/`                   | ⏳ 未実装   | `/issue` → `feature-implementer` で実装 |

## 公開 API

\`\`\`python
from [パッケージ名] import get_logger
\`\`\`

## 拡張ガイド

1. **コアモジュール追加**: `/issue` → `feature-implementer` で TDD 実装
2. **ユーティリティ追加**: `/issue` → `feature-implementer` で TDD 実装
3. **型定義追加**: `types.py` に追加

## 関連ドキュメント

-   `template/src/template_package/README.md` - テンプレート実装の詳細
-   `docs/development-guidelines.md` - 開発ガイドライン
```

**`src/[パッケージ名]/types.py`:**

`template/src/template_package/types.py` をコピーし、docstring のパッケージ名を置換する。

### 3.2 サブパッケージ

**`src/[パッケージ名]/core/__init__.py`:**

```python
"""Core functionality of the [パッケージ名] package."""

__all__: list[str] = []
```

**`src/[パッケージ名]/utils/__init__.py`:**

```python
"""Utility functions for the [パッケージ名] package."""

from .logging_config import get_logger

__all__ = [
    "get_logger",
]
```

**`src/[パッケージ名]/utils/logging_config.py`:**

`template/src/template_package/utils/logging_config.py` をそのままコピーする。

### 3.3 ドキュメント構造

**`src/[パッケージ名]/docs/.gitkeep`:**

```text
# ドキュメントディレクトリ
# project.md は /new-project コマンドで作成されます
```

## ステップ 4: テスト構造生成

以下のファイルを生成する:

**`tests/[パッケージ名]/__init__.py`:**

```python
"""Tests for [パッケージ名] package."""
```

**`tests/[パッケージ名]/conftest.py`:**

```python
"""Pytest configuration and fixtures for [パッケージ名]."""

import logging
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_data() -> list[dict[str, Any]]:
    """Create sample data for testing."""
    return [
        {"id": 1, "name": "Item 1", "value": 100},
        {"id": 2, "name": "Item 2", "value": 200},
        {"id": 3, "name": "Item 3", "value": 300},
    ]


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset environment variables for each test."""
    test_env_vars = [var for var in os.environ if var.startswith("TEST_")]
    for var in test_env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture logs for testing with proper level."""
    caplog.set_level(logging.DEBUG)
    return caplog
```

**`tests/[パッケージ名]/unit/__init__.py`:**

```python
"""Unit tests for [パッケージ名] package."""
```

**`tests/[パッケージ名]/property/__init__.py`:**

```python
"""Property-based tests for [パッケージ名] package."""
```

**`tests/[パッケージ名]/integration/__init__.py`:**

```python
"""Integration tests for [パッケージ名] package."""
```

## ステップ 5: pyproject.toml 更新

`pyproject.toml` の `[tool.hatch.build.targets.wheel].packages` に新しいパッケージを追加する:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/project_name", "src/[パッケージ名]"]
```

**注意:** 既存のパッケージリストを維持しつつ、新しいパッケージを追加する。

## ステップ 6: 次のステップ案内

作成完了後、ユーザーに以下の次のステップを案内する:

---

**パッケージ `[パッケージ名]` を作成しました。**

次のステップ:

1. **プロジェクトファイルを作成して設計ドキュメントを生成:**

    ```bash
    /new-project @src/[パッケージ名]/docs/project.md
    ```

    インタビューを通じてプロジェクトファイル（project.md）が作成され、
    続いてLRD・設計ドキュメントが生成されます。

2. **Issue管理・機能実装:**

    ```bash
    /issue @src/[パッケージ名]/docs/project.md
    # → feature-implementer で TDD 実装
    ```

---

## 完了条件

このワークフローは、以下の全ての条件を満たした時点で完了となる:

-   ステップ 3: 全てのパッケージファイルが生成されている（docs/ ディレクトリを含む）
-   ステップ 4: 全てのテストファイルが生成されている
-   ステップ 5: pyproject.toml が更新されている
-   ステップ 6: 次のステップがユーザーに案内されている
