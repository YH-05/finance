# プロセスガイド (Process Guide)

## 基本原則

### 1. 具体例を豊富に含める

抽象的なルールだけでなく、具体的なコード例を提示します。

**悪い例**:

```
変数名は分かりやすくすること
```

**良い例**:

```python
# ✅ 良い例: 役割が明確
user_authentication = UserAuthenticationService()
task_repository = TaskRepository()

# ❌ 悪い例: 曖昧
auth = Service()
repo = Repository()
```

### 2. 理由を説明する

「なぜそうするのか」を明確にします。

**例**:

```
## エラーを無視しない

理由: エラーを無視すると、問題の原因究明が困難になります。
予期されるエラーは適切に処理し、予期しないエラーは上位に伝播させて
ログに記録できるようにします。
```

### 3. 測定可能な基準を設定

曖昧な表現を避け、具体的な数値を示します。

**悪い例**:

```
コードカバレッジは高く保つこと
```

**良い例**:

```
コードカバレッジ目標:
- ユニットテスト: 80%以上
- 統合テスト: 60%以上
- E2Eテスト: 主要フロー100%
```

## Git 運用ルール

### ブランチ戦略（Git Flow 採用）

**Git Flow とは**:
Vincent Driessen が提唱した、機能開発・リリース・ホットフィックスを体系的に管理するブランチモデル。明確な役割分担により、チーム開発での並行作業と安定したリリースを実現します。

**ブランチ構成**:

```
main (本番環境)
└── develop (開発・統合環境)
    ├── feature/* (新機能開発)
    ├── fix/* (バグ修正)
    ├── refactor/* (リファクタリング)
    ├── docs/* (ドキュメント)
    ├── test/* (テスト追加)
    └── release/* (リリース準備)※必要に応じて
```

**運用ルール**:

-   **main**: 本番リリース済みの安定版コードのみを保持。タグでバージョン管理
-   **develop**: 次期リリースに向けた最新の開発コードを統合。CI での自動テスト実施
-   **feature/\*、fix/\*、refactor/\*、docs/\*、test/\***: develop から分岐し、作業完了後に PR で develop へマージ
-   **直接コミット禁止**: すべてのブランチで PR レビューを必須とし、コード品質を担保
-   **マージ方針**: feature→develop は squash merge、develop→main は merge commit を推奨

**Git Flow のメリット**:

-   ブランチの役割が明確で、複数人での並行開発がしやすい
-   本番環境(main)が常にクリーンな状態に保たれる
-   緊急対応時は hotfix ブランチで迅速に対応可能（必要に応じて導入）

### コミットメッセージの規約

**Conventional Commits を推奨**:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 一覧**:

```
feat: 新機能 (minor version up)
fix: バグ修正 (patch version up)
docs: ドキュメント
style: フォーマット (コードの動作に影響なし)
refactor: リファクタリング
perf: パフォーマンス改善
test: テスト追加・修正
build: ビルドシステム
ci: CI/CD設定
chore: その他 (依存関係更新など)

BREAKING CHANGE: 破壊的変更 (major version up)
```

**良いコミットメッセージの例**:

```
feat(task): 優先度設定機能を追加

ユーザーがタスクに優先度(高/中/低)を設定できるようになりました。

実装内容:
- Taskモデルにpriorityフィールド追加
- CLI に --priority オプション追加
- 優先度によるソート機能実装

破壊的変更:
- Task型の構造が変更されました
- 既存のタスクデータはマイグレーションが必要です

Closes #123
BREAKING CHANGE: Task型にpriority必須フィールド追加
```

### プルリクエストのテンプレート

**効果的な PR テンプレート**:

```markdown
## 変更の種類

-   [ ] 新機能 (feat)
-   [ ] バグ修正 (fix)
-   [ ] リファクタリング (refactor)
-   [ ] ドキュメント (docs)
-   [ ] その他 (chore)

## 変更内容

### 何を変更したか

[簡潔な説明]

### なぜ変更したか

[背景・理由]

### どのように変更したか

-   [変更点 1]
-   [変更点 2]

## テスト

### 実施したテスト

-   [ ] ユニットテスト追加
-   [ ] 統合テスト追加
-   [ ] 手動テスト実施

### テスト結果

[テスト結果の説明]

## 関連 Issue

Closes #[番号]
Refs #[番号]

## レビューポイント

[レビュアーに特に見てほしい点]
```

## テスト戦略

詳細は `docs/testing-strategy.md` を参照。

## コードレビュープロセス

### レビューの目的

1. **品質保証**: バグの早期発見
2. **知識共有**: チーム全体でコードベースを理解
3. **学習機会**: ベストプラクティスの共有

### 効果的なレビューのポイント

**レビュアー向け**:

1. **建設的なフィードバック**

````markdown
## ❌ 悪い例

このコードはダメです。

## ✅ 良い例

この実装だと O(n²) の時間計算量になります。
dict を使うと O(n) に改善できます:

```python
task_map = {t.id: t for t in tasks}
result = [task_map.get(id) for id in ids]
```
````

````

2. **優先度の明示**
```markdown
[必須] セキュリティ: パスワードがログに出力されています
[推奨] パフォーマンス: ループ内でのDB呼び出しを避けましょう
[提案] 可読性: この関数名をもっと明確にできませんか？
[質問] この処理の意図を教えてください
````

3. **ポジティブなフィードバックも**

```markdown
✨ この実装は分かりやすいですね！
👍 エッジケースがしっかり考慮されています
💡 このパターンは他でも使えそうです
```

**レビュイー向け**:

1. **セルフレビューを実施**

    - PR 作成前に自分でコードを見直す
    - 説明が必要な箇所にコメントを追加

2. **小さな PR を心がける**

    - 1PR = 1 機能
    - 変更ファイル数: 10 ファイル以内を推奨
    - 変更行数: 300 行以内を推奨

3. **説明を丁寧に**
    - なぜこの実装にしたか
    - 検討した代替案
    - 特に見てほしいポイント

### レビュー時間の目安

-   小規模 PR (100 行以下): 15 分
-   中規模 PR (100-300 行): 30 分
-   大規模 PR (300 行以上): 1 時間以上

**原則**: 大規模 PR は避け、分割する

## 自動化の推進（該当する場合）

### 品質チェックの自動化

**自動化項目と採用ツール**:

1. **Lint・フォーマット**

    - **Ruff**
        - Rust ベースで高速なリント・フォーマット
        - Flake8、isort、Black、pyupgrade などの機能を統合
        - 自動修正機能により開発効率が向上
        - 設定ファイル: `pyproject.toml`

2. **型チェック**

    - **pyright**
        - 高速で厳密な型チェック
        - VS Code (Pylance) と同じエンジンで一貫した開発体験
        - 設定ファイル: `pyproject.toml`

3. **テスト実行**

    - **pytest + Hypothesis**
        - Python の標準的なテストフレームワーク
        - Hypothesis によるプロパティベーステストで自動テストケース生成
        - pytest-cov でカバレッジ測定
        - 豊富なプラグインエコシステム

4. **依存関係管理**
    - **uv**
        - Rust ベースで高速なパッケージ管理
        - pip/pipx/virtualenv/pyenv の機能を統合
        - pyproject.toml による依存関係の厳密な管理

**実装方法**:

**1. CI/CD (GitHub Actions)**

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
    test:
        runs-on: ubuntu-latest
        steps:
            - uses: actions/checkout@v4
            - uses: astral-sh/setup-uv@v4
              with:
                  enable-cache: true
            - run: uv sync --all-extras
            - run: make lint
            - run: make typecheck
            - run: make test
```

**2. Pre-commit フック (pre-commit)**

```yaml
# .pre-commit-config.yaml
repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.8.6
      hooks:
          - id: ruff
            args: [--fix]
          - id: ruff-format

    - repo: https://github.com/RobertCraiworthy/pyright-pre-commit
      rev: v1.1.391
      hooks:
          - id: pyright
```

```bash
# 初期設定
uv add --dev pre-commit
pre-commit install
```

**導入効果**:

-   コミット前に自動チェックが走り、不具合コードの混入を防止
-   PR 作成時に自動で CI 実行され、マージ前に品質を担保
-   早期発見により、修正コストを最大 80%削減（バグ検出が本番後の場合と比較）

**この構成を選んだ理由**:

-   Python エコシステムにおける標準的かつモダンな構成
-   Ruff による高速なリント・フォーマットで開発体験が向上
-   pyproject.toml で設定を一元管理できる

## チェックリスト

-   [ ] ブランチ戦略が決まっている
-   [ ] コミットメッセージ規約が明確である
-   [ ] PR テンプレートが用意されている
-   [ ] テストの種類とカバレッジ目標が設定されている
-   [ ] コードレビュープロセスが定義されている
-   [ ] CI/CD パイプラインが構築されている
