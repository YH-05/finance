# 開発プロセス

## 必須コマンド

```bash
# 品質チェック
make check-all          # 全チェック（format, lint, typecheck, test）
make format             # コードフォーマット
make lint               # リント
make typecheck          # 型チェック
make test               # テスト実行
make test-cov           # カバレッジ付きテスト

# 依存関係
uv add package_name     # 通常パッケージ追加
uv add --dev pkg        # 開発用パッケージ追加
uv sync --all-extras    # 全依存関係を同期

# GitHub操作
/commit-and-pr          # PR作成
/merge-pr <number>      # PRマージ
make issue TITLE="x" BODY="y"  # Issue作成
```

## 実装フロー

1. **format** → **lint** → **typecheck** → **test**
2. 新機能は **TDD 必須**
3. 全コードに**ログ必須**
4. 重い処理は**プロファイル実施**

## タスク別ガイド参照

| タスク | 参照先 |
|--------|--------|
| 並行開発計画 | `/plan-worktrees <project_number>` |
| 並行開発環境作成 | `/worktree <branch_name>` |
| 並行開発一括作成 | `/create-worktrees <issue_numbers>` |
| 並行開発一括削除 | `/delete-worktrees <branch_names>` |
| 開発完了クリーンアップ | `/worktree-done <branch_name>` |
| パッケージ作成 | `/new-package <package_name>` |
| 開発開始（パッケージ） | `/new-project @src/<library>/docs/project.md` |
| 開発開始（軽量） | `/new-project "プロジェクト名"` |
| Issue管理 | `/issue @src/<library>/docs/project.md` |
| Issue自動実装 | `/issue-implement <番号>` |
| Issueブラッシュアップ | `/issue-refine 番号` |
| プロジェクト健全性 | `/project-refine` |
| Issueコメント同期 | `/sync-issue #番号` |
| テスト作成 | `/write-tests` |
| コード品質改善 | `/ensure-quality` |
| リファクタリング | `/safe-refactor` |
| コード分析 | `/analyze` |
| 改善実装 | `/improve` |
| セキュリティ検証 | `/scan` |
| デバッグ | `/troubleshoot` |
| タスク管理 | `/task` |
| Git操作 | `/commit-and-pr` |
| PRマージ | `/merge-pr` |
| コンフリクト分析 | `/analyze-conflicts` |
| PRレビュー | `/review-pr` |
| ドキュメントレビュー | `/review-docs` |
| コマンド一覧 | `/index` |

## 金融コンテンツ関連

| タスク | 参照先 |
|--------|--------|
| ニュース収集 | `/collect-finance-news` |
| トピック提案 | `/finance-suggest-topics` |
| 記事初期化 | `/new-finance-article` |
| リサーチ実行 | `/finance-research` |
| 編集・批評 | `/finance-edit` |
| 全工程一括実行 | `/finance-full` |

## コードレビュープロセス

### レビューの目的

1. **品質保証**: バグの早期発見
2. **知識共有**: チーム全体でコードベースを理解
3. **学習機会**: ベストプラクティスの共有

### レビューの優先度表記

```markdown
[必須] セキュリティ: パスワードがログに出力されています
[推奨] パフォーマンス: ループ内でのDB呼び出しを避けましょう
[提案] 可読性: この関数名をもっと明確にできませんか？
[質問] この処理の意図を教えてください
```

### PR サイズの目安

- 小規模 PR (100行以下): 15分
- 中規模 PR (100-300行): 30分
- 大規模 PR (300行以上): 分割を検討

**原則**: 大規模 PR は避け、分割する

## 自動化ツール

| ツール | 用途 |
|--------|------|
| Ruff | リント・フォーマット |
| pyright | 型チェック |
| pytest + Hypothesis | テスト |
| pre-commit | コミット前チェック |
| GitHub Actions | CI/CD |
| uv | パッケージ管理 |

## 詳細参照

- コーディング規約: `docs/coding-standards.md`
- 開発プロセス詳細: `docs/development-process.md`
- テスト戦略: `docs/testing-strategy.md`
