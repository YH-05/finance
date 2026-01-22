# コーディング規約

このファイルはコーディング規約の概要です。詳細なガイドと例は **coding-standards スキル**を参照してください。

## スキル参照

| リソース | パス |
|---------|------|
| クイックリファレンス | `.claude/skills/coding-standards/SKILL.md` |
| 詳細ガイド | `.claude/skills/coding-standards/guide.md` |
| 型ヒント例 | `.claude/skills/coding-standards/examples/type-hints.md` |
| Docstring例 | `.claude/skills/coding-standards/examples/docstrings.md` |
| エラーメッセージ例 | `.claude/skills/coding-standards/examples/error-messages.md` |
| 命名規則例 | `.claude/skills/coding-standards/examples/naming.md` |
| ロギング例 | `.claude/skills/coding-standards/examples/logging.md` |

## 概要

| 項目 | 規約 |
|------|------|
| 型ヒント | Python 3.12+ スタイル（PEP 695） |
| Docstring | NumPy 形式 |
| クラス名 | PascalCase |
| 関数/変数名 | snake_case |
| 定数 | UPPER_SNAKE |
| プライベート | _prefix |

## クイックリファレンス

### 型ヒント（PEP 695）

```python
# 組み込み型を直接使用
def process_items(items: list[str]) -> dict[str, int]: ...

# ジェネリック関数（PEP 695 新構文）
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None
```

### 命名規則

```python
# 変数: snake_case、Boolean: is_, has_, should_, can_
user_name = "John"
is_completed = True

# 関数: snake_case、動詞で始める
def fetch_user_data() -> User: ...

# クラス: PascalCase
class TaskManager: ...

# 定数: UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
```

### エラーメッセージ

```python
# 具体的で解決策を示す
raise ValueError(f"Expected positive integer, got {count}")
raise FileNotFoundError(f"Config not found. Create by: python -m {__package__}.init")
```

### アンカーコメント

```python
# AIDEV-NOTE: 実装の意図や背景の説明
# AIDEV-TODO: 未完了タスク
# AIDEV-QUESTION: 確認が必要な疑問点
```

## 詳細参照

- **完全なガイド**: `.claude/skills/coding-standards/guide.md`
- **従来のドキュメント**: `docs/coding-standards.md`
