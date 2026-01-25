---
summary: "スキルディレクトリ内にPythonコードを配置するアーキテクチャパターン - utils/でコードとドキュメントを一元化"
created: 2026-01-25
tags: [architecture, skills, python, best-practice]
related: [.claude/skills/finance-news-workflow/]
---

# スキルベースアーキテクチャ: スキル内のPythonコード配置パターン

## 概要

Claude Codeのスキルは、ドキュメント（SKILL.md, guide.md）だけでなく、**Pythonコードも含めることができる**。

スキル専用のPythonコードは `utils/` サブディレクトリに配置することで、コードとドキュメントを一元化できる。

## 標準構造

```
.claude/skills/{skill-name}/
├── SKILL.md                  # スキルの説明
├── guide.md                  # 詳細ガイド
├── templates/                # テンプレート（任意）
├── examples/                 # 使用例（任意）
└── utils/                    # Python実装コード ← 重要
    ├── __init__.py           # パッケージ初期化、API エクスポート
    ├── {module1}.py          # 実装モジュール1
    ├── {module2}.py          # 実装モジュール2
    └── README.md             # ユーティリティの説明

tests/skills/{skill-name}/    # 対応するテスト
├── __init__.py
├── README.md
└── unit/
    ├── __init__.py
    ├── test_{module1}.py
    └── test_{module2}.py
```

## 実例: finance-news-workflow

### Before（エージェントディレクトリに混在）

```
.claude/agents/finance_news_collector/
├── __init__.py                      # Pythonモジュール
├── filtering.py                     # Pythonコード
├── transformation.py                # Pythonコード
└── common-processing-guide.md       # ドキュメント（1248行）← 問題
```

**問題点**:
- エージェントディレクトリにPythonコードとドキュメントが混在
- コードとドキュメントの責務が分離されていない
- スキルベースのアーキテクチャに反する

### After（スキルディレクトリに統合）

```
.claude/skills/finance-news-workflow/
├── SKILL.md
├── guide.md
├── common-processing-guide.md       # ドキュメント（移動）
├── templates/
├── examples/
└── utils/                           # Pythonコード（新規）
    ├── __init__.py
    ├── filtering.py
    ├── transformation.py
    └── README.md

tests/skills/finance_news_workflow/  # テスト（新規）
├── __init__.py
├── README.md
└── unit/
    ├── test_filtering.py
    ├── test_transformation.py
    └── test_edge_cases.py
```

**メリット**:
1. **一元化**: コード・ドキュメント・テストがスキル単位で完結
2. **保守性**: 関連ファイルが近接配置され、変更が容易
3. **再利用性**: スキルとして独立したパッケージ、他プロジェクトへの移植が容易
4. **明確性**: `utils/` でPythonコード、他はドキュメントと明確に分離

## インポートパターン

### utils/__init__.py でAPIをエクスポート

```python
"""Finance news collector module.

金融ニュース収集のためのフィルタリングおよびデータ変換機能を提供します。
"""

from .filtering import (
    is_excluded,
    matches_financial_keywords,
)
from .transformation import convert_to_issue_format

__all__ = [
    "convert_to_issue_format",
    "is_excluded",
    "matches_financial_keywords",
]
```

### 使用側でのインポート

```python
from .claude.skills.finance_news_workflow.utils import (
    matches_financial_keywords,
    is_excluded,
    convert_to_issue_format,
)
```

## コーディング規約

スキル内のPythonコードも `.claude/rules/coding-standards.md` に準拠:

- Python 3.12+ 型ヒント（PEP 695）
- NumPy形式のDocstring
- snake_case命名規則
- テストカバレッジ80%以上

## テスト実行

```bash
# スキル単位でテスト実行
uv run pytest tests/skills/{skill-name}/ -v

# カバレッジ付き
uv run pytest tests/skills/{skill-name}/ \
  --cov=.claude.skills.{skill-name}.utils \
  --cov-report=term-missing
```

## いつ使うか

以下の場合にスキル内にPythonコードを配置する:

1. **スキル専用のロジック**: 他のパッケージ（`src/`）に属さない、スキル固有の処理
2. **軽量なユーティリティ**: 複雑すぎず、スキル内で完結する実装
3. **エージェント間で共有**: 複数のサブエージェントが使用する共通処理

**使わない場合**:
- プロジェクトの主要ロジック → `src/{package}/`
- 大規模な実装 → 独立したパッケージとして `src/` に配置

## 移行手順

既存のエージェントディレクトリのコードをスキルに移行する場合:

1. スキルディレクトリに `utils/` を作成
2. Pythonコードを移動
3. テストを `tests/skills/{skill-name}/` に移動
4. エージェント・コマンドの参照パスを更新
5. 旧ディレクトリを `trash/` に移動
6. README.md を作成（utils/README.md, tests/README.md）

詳細は 2026-01-25 の finance-news-workflow 移行ログを参照。

## 関連ドキュメント

- `.claude/rules/coding-standards.md` - コーディング規約
- `.claude/rules/testing-strategy.md` - テスト戦略
- `.claude/skills/skill-expert/guide.md` - スキル設計ガイド
