# Project Implementation 設計ガイド

## 概要

このガイドは `project-implementation` スキルの詳細な設計と実装方法を説明します。

## アーキテクチャ

### 処理フロー全体図

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         /project-implement {number}                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 0: 初期化                                                              │
│ ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐         │
│ │ 引数解析          │→ │ 再開判定          │→ │ ブランチ作成/切替│         │
│ └───────────────────┘  └───────────────────┘  └───────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Issue 取得・解析                                                    │
│ ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐         │
│ │ Project Items     │→ │ フィルタリング    │→ │ 依存関係解析      │         │
│ │ 取得              │  │ (Todo/InProgress) │  │ + 順序決定        │         │
│ └───────────────────┘  └───────────────────┘  └───────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 2-N: Issue 実装ループ                                                  │
│ ┌─────────────────────────────────────────────────────────────────────────┐ │
│ │ For each Issue in order:                                                 │ │
│ │ ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────┐ │ │
│ │ │ 進捗保存  │→ │ /clear    │→ │ 実装      │→ │ コミット  │→ │ チェック│ │ │
│ │ └───────────┘  └───────────┘  └───────────┘  └───────────┘  └─────────┘ │ │
│ │                                                               │ ↓       │ │
│ │                                                          失敗時: 中断   │ │
│ └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase Final: 完了処理                                                        │
│ ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐         │
│ │ 最終コミット      │→ │ プッシュ          │→ │ レポート出力      │         │
│ └───────────────────┘  └───────────────────┘  └───────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Phase 0: 初期化詳細

### 引数解析

```bash
# 新規開始
/project-implement 1

# 再開
/project-implement --resume
/project-implement 1 --resume  # Project 番号指定での再開
```

### 再開判定ロジック

```python
def check_resume(project_number: int | None) -> tuple[bool, dict | None]:
    """再開可能かどうかを判定し、進捗データを返す。

    Returns
    -------
    tuple[bool, dict | None]
        (is_resume, progress_data)
    """
    if project_number:
        progress_file = f".tmp/project-{project_number}-progress.json"
    else:
        # --resume のみの場合、既存の進捗ファイルを検索
        progress_files = glob.glob(".tmp/project-*-progress.json")
        if len(progress_files) == 1:
            progress_file = progress_files[0]
        elif len(progress_files) > 1:
            # 複数ある場合はユーザーに選択を求める
            raise MultipleProgressFilesError(progress_files)
        else:
            return (False, None)

    if Path(progress_file).exists():
        with open(progress_file) as f:
            return (True, json.load(f))
    return (False, None)
```

### ブランチ操作

```bash
# 新規開始時
git checkout -b feature/project-{number}

# 再開時（ブランチが存在する場合）
git checkout feature/project-{number}

# ブランチが存在しない場合の確認
git show-ref --verify --quiet refs/heads/feature/project-{number}
```

## Phase 1: Issue 取得・依存関係解析

### Project Items 取得

```bash
# Project Items を JSON で取得
gh project item-list {number} --owner "@me" --format json --limit 100

# Project フィールド情報を取得（blocked フィールド確認用）
gh project field-list {number} --owner "@me" --format json
```

### レスポンス例

```json
{
  "items": [
    {
      "id": "PVTI_xxx",
      "content": {
        "type": "Issue",
        "body": "## 概要\n...\n\ndepends on #10",
        "number": 12,
        "title": "機能A の実装",
        "url": "https://github.com/user/repo/issues/12"
      },
      "status": {
        "name": "Todo"
      },
      "blocked": {
        "value": "#10, #11"
      }
    }
  ]
}
```

### フィルタリング条件

```python
def filter_actionable_issues(items: list[dict]) -> list[dict]:
    """Todo または In Progress ステータスの Issue を抽出。

    Parameters
    ----------
    items : list[dict]
        Project の全アイテム

    Returns
    -------
    list[dict]
        フィルタリングされた Issue リスト
    """
    return [
        item for item in items
        if item.get("content", {}).get("type") == "Issue"
        and item.get("status", {}).get("name") in ("Todo", "In Progress")
    ]
```

### 依存関係抽出

#### パターン1: Issue 本文から

```python
import re

DEPENDENCY_PATTERNS = [
    r"depends on #(\d+)",
    r"depends_on:\s*#(\d+)",
    r"blocked by #(\d+)",
    r"requires #(\d+)",
]

SECTION_PATTERN = r"## 依存タスク\n((?:- \[[ x]\] #\d+\n?)+)"

def extract_dependencies_from_body(body: str) -> list[int]:
    """Issue 本文から依存 Issue 番号を抽出。

    Parameters
    ----------
    body : str
        Issue の本文

    Returns
    -------
    list[int]
        依存している Issue 番号のリスト
    """
    deps = []

    # インラインパターン
    for pattern in DEPENDENCY_PATTERNS:
        matches = re.findall(pattern, body, re.IGNORECASE)
        deps.extend(int(m) for m in matches)

    # セクションパターン
    section_match = re.search(SECTION_PATTERN, body, re.IGNORECASE)
    if section_match:
        task_matches = re.findall(r"#(\d+)", section_match.group(1))
        deps.extend(int(m) for m in task_matches)

    return list(set(deps))  # 重複除去
```

#### パターン2: Project の blocked フィールドから

```python
def extract_dependencies_from_field(blocked_value: str | None) -> list[int]:
    """Project の blocked フィールドから依存 Issue 番号を抽出。

    Parameters
    ----------
    blocked_value : str | None
        blocked フィールドの値（例: "#10, #11"）

    Returns
    -------
    list[int]
        依存している Issue 番号のリスト
    """
    if not blocked_value:
        return []
    matches = re.findall(r"#(\d+)", blocked_value)
    return [int(m) for m in matches]
```

### 依存関係グラフ構築

```python
from collections import defaultdict

def build_dependency_graph(issues: list[dict]) -> dict[int, list[int]]:
    """依存関係グラフを構築。

    Parameters
    ----------
    issues : list[dict]
        Issue リスト

    Returns
    -------
    dict[int, list[int]]
        Issue 番号 → 依存している Issue 番号のリスト
    """
    graph = defaultdict(list)

    for issue in issues:
        number = issue["content"]["number"]
        body = issue["content"].get("body", "") or ""
        blocked = issue.get("blocked", {}).get("value")

        # 本文から抽出
        body_deps = extract_dependencies_from_body(body)

        # blocked フィールドから抽出
        field_deps = extract_dependencies_from_field(blocked)

        # 統合（重複除去）
        all_deps = list(set(body_deps + field_deps))
        graph[number] = all_deps

    return dict(graph)
```

### トポロジカルソート

```python
from collections import deque

def topological_sort(
    issues: list[dict],
    dependencies: dict[int, list[int]],
    done_issues: set[int],
) -> list[int]:
    """依存関係を考慮した実装順序を決定。

    Parameters
    ----------
    issues : list[dict]
        実装対象の Issue リスト
    dependencies : dict[int, list[int]]
        依存関係グラフ
    done_issues : set[int]
        既に完了している Issue 番号

    Returns
    -------
    list[int]
        実装順序（Issue 番号のリスト）

    Raises
    ------
    CircularDependencyError
        循環依存がある場合
    """
    issue_numbers = {i["content"]["number"] for i in issues}
    in_degree = {n: 0 for n in issue_numbers}

    # 入次数の計算
    for number in issue_numbers:
        for dep in dependencies.get(number, []):
            if dep in issue_numbers and dep not in done_issues:
                in_degree[number] += 1

    # 入次数 0 のノードをキューに追加（Issue 番号順）
    queue = deque(sorted([n for n, d in in_degree.items() if d == 0]))
    result = []

    while queue:
        # キューから取り出し
        current = queue.popleft()
        result.append(current)

        # 依存先の入次数を減らす
        for number in issue_numbers:
            if current in dependencies.get(number, []):
                in_degree[number] -= 1
                if in_degree[number] == 0:
                    # ソート済みキューに挿入（Issue 番号順を維持）
                    insert_sorted(queue, number)

    # 循環依存チェック
    if len(result) != len(issue_numbers):
        remaining = issue_numbers - set(result)
        raise CircularDependencyError(remaining)

    return result
```

## Phase 2-N: Issue 実装詳細

### 実装ループ

```python
pr_number = None  # 作成したPR番号を保持

for issue_number in sorted_issues:
    # 1. 進捗ファイル更新（current を設定）
    update_progress(
        status="in_progress",
        current=issue_number,
    )

    # 2. コンテキスト消去（/clear コマンド相当）
    # 注意: 再開に必要な情報は進捗ファイルに保存済み
    clear_context()

    # 3. Issue 実装（issue-implementation ロジック）
    try:
        implement_issue(issue_number)
    except ImplementationError as e:
        handle_failure(issue_number, e)
        break

    # 4. コミット & プッシュ
    create_commit(issue_number)
    run_command("git push")

    # 5. PR 作成/更新
    if pr_number is None:
        # 初回: PR 作成
        pr_number = create_pull_request(base="main")
        update_progress(pr_number=pr_number)
    # 2回目以降: プッシュで自動更新済み

    # 6. CI チェック待機
    if not wait_for_ci(pr_number):
        if not attempt_auto_fix(max_attempts=3):
            handle_failure(issue_number, "CI check failed")
            break

    # 7. Issue ステータス更新
    update_project_status(issue_number, "Done")

    # 8. 進捗ファイル更新（completed に追加）
    update_progress(
        completed_add=issue_number,
        current=None,
    )
```

### /clear コマンドの実行

```bash
# コンテキストを消去
# 注意: このコマンドは会話履歴をリセットするため、
# 再開に必要な情報は事前に進捗ファイルに保存すること

/clear
```

### issue-implementation ロジックの呼び出し

サブエージェントに委譲して Issue を実装します。

```python
# issue-implementation と同じロジックを使用
# ただし、PR 作成は行わない（Phase 6 はスキップ）

Task(
    prompt=f"""Issue #{issue_number} を実装してください。

## 指示
1. issue-implementation スキルの Phase 0-5 を実行
2. Phase 6 (PR 作成) は実行しない
3. 品質チェック (make check-all) 成功まで

## 参照
- .claude/skills/issue-implementation/SKILL.md
""",
)
```

### コミット & プッシュ

```bash
# Issue 番号とタイトルを含むコミットメッセージ
git add -A
git commit -m "$(cat <<'EOF'
feat(#{number}): {title}

Implements #{number}

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"

# プッシュ（初回は -u フラグ）
git push -u origin feature/project-{project_number}
```

### PR 作成

```bash
# 初回のみ PR を作成
gh pr create --base main --title "feat: Project #{project_number} 実装" --body "..."

# 2回目以降はプッシュで自動的に PR が更新される
```

### CI チェック待機

```bash
# PR の CI ステータスをチェック
gh pr checks {pr_number} --watch

# 失敗したチェックを確認
gh run view --log-failed
```

### 自動修正ループ

```python
def attempt_auto_fix(max_attempts: int = 3) -> bool:
    """CI失敗時の自動修正を試行。

    Parameters
    ----------
    max_attempts : int
        最大試行回数

    Returns
    -------
    bool
        修正成功なら True
    """
    for attempt in range(max_attempts):
        # フォーマット
        run_command("make format")

        # リント修正
        run_command("make lint")

        # 型チェック
        result = run_command("make typecheck")
        if not result.success:
            # 型エラーは自動修正困難な場合あり
            continue

        # テスト
        result = run_command("make test")
        if result.success:
            # 修正をコミット & プッシュ
            run_command('git add -A && git commit -m "fix: CI エラーを修正"')
            run_command('git push')

            # CI 再実行を待機
            if wait_for_ci(pr_number):
                return True

    return False
```

## Phase Final: 完了処理

### 完了レポート出力

全 Issue が完了したら、PR URL を含む完了レポートを出力。

```bash
# PR URL を取得
gh pr view {pr_number} --json url -q .url
```

### Project ステータス更新

```bash
# Issue の Project ステータスを Done に更新
gh project item-edit \
  --id {item_id} \
  --project-id {project_id} \
  --field-id {status_field_id} \
  --single-select-option-id {done_option_id}
```

### 進捗ファイルの処理

```python
def cleanup_progress_file(project_number: int, success: bool) -> None:
    """進捗ファイルの後処理。

    Parameters
    ----------
    project_number : int
        Project 番号
    success : bool
        全 Issue 成功なら True
    """
    progress_file = Path(f".tmp/project-{project_number}-progress.json")

    if success:
        # 全 Issue 完了時は削除
        progress_file.unlink(missing_ok=True)
    else:
        # 失敗時は保持（再開用）
        # status を "failed" に更新
        with open(progress_file) as f:
            data = json.load(f)
        data["status"] = "failed"
        with open(progress_file, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
```

## エラーハンドリング詳細

### エラー種別と対処

| エラー種別 | 原因 | 対処 | 再開可能 |
|-----------|------|------|---------|
| `ProjectNotFoundError` | Project が存在しない | エラー表示、一覧案内 | - |
| `NoActionableIssuesError` | Todo/InProgress なし | 完了メッセージ | - |
| `CircularDependencyError` | 循環依存 | 警告、循環除外して継続 | Yes |
| `ImplementationError` | Issue 実装失敗 | 自動修正試行 | Yes |
| `PreCommitError` | pre-commit 失敗 | 自動修正試行 | Yes |
| `PushError` | プッシュ失敗 | 認証確認案内 | Yes |

### 失敗時の処理

```python
def handle_failure(
    project_number: int,
    current_issue: int,
    error: Exception,
) -> None:
    """失敗時の処理。

    1. 現在までの変更をコミット
    2. プッシュ（可能なら）
    3. 進捗ファイルにエラー記録
    4. 中断レポート出力
    """
    # 1. 未コミットの変更があればコミット
    if has_uncommitted_changes():
        run_command(
            f'git commit -m "wip(#{current_issue}): 実装途中（エラー発生）"'
        )

    # 2. プッシュ
    try:
        run_command(f"git push -u origin feature/project-{project_number}")
    except Exception:
        pass  # プッシュ失敗は無視

    # 3. 進捗ファイル更新
    update_progress(
        status="failed",
        last_error=str(error),
    )

    # 4. 中断レポート出力
    output_interrupt_report(project_number, current_issue, error)
```

## ベストプラクティス

### DO（推奨）

1. **進捗ファイルを頻繁に更新**
   - 各 Issue 開始時、完了時に必ず更新
   - /clear 前に必ず保存

2. **コミットは Issue ごとに**
   - 1 Issue = 1 コミット の原則
   - 追跡性を確保

3. **エラー時は早めに中断**
   - 自動修正 3 回失敗で中断
   - 無限ループを避ける

4. **ブランチ名は一貫性を保つ**
   - `feature/project-{number}` の形式
   - 再開時に同じブランチを使用

### DON'T（避けるべき）

1. **進捗ファイルなしで /clear を実行**
   - 再開不可能になる

2. **失敗を無視して継続**
   - 後続の Issue も失敗する可能性

3. **手動でブランチを変更**
   - 進捗ファイルとの整合性が崩れる

4. **複数の Project を同時実行**
   - コンフリクトの原因

## トラブルシューティング

### 問題: 再開時にブランチが見つからない

**原因**: ブランチが削除された、または名前が異なる

**解決方法**:
```bash
# ブランチ一覧を確認
git branch -a | grep project

# 進捗ファイルを確認
cat .tmp/project-*-progress.json

# 進捗ファイルを削除して新規開始
rm .tmp/project-{number}-progress.json
/project-implement {number}
```

### 問題: 循環依存でスタック

**原因**: Issue 間の依存関係が循環している

**解決方法**:
1. 警告で表示された Issue を確認
2. Issue の依存関係を修正
3. 再実行

### 問題: pre-commit が繰り返し失敗

**原因**: 自動修正では解決できない問題

**解決方法**:
1. 進捗ファイルを確認
2. 手動で問題を修正
3. `/project-implement --resume` で再開

### 問題: Project ステータスが更新されない

**原因**: Project へのアクセス権限不足

**解決方法**:
```bash
# 権限を確認
gh auth status

# 権限を更新
gh auth refresh -s project
```
