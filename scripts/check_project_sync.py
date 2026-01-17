#!/usr/bin/env python3
"""Pre-push hook for project synchronization check.

GitHub Issues / Project と project.md の整合性を検証します。

Usage
-----
python scripts/check_project_sync.py [--strict] [--skip-github]

Options
-------
--strict
    警告もエラーとして扱う
--skip-github
    GitHub API チェックをスキップ（ローカルチェックのみ）

Notes
-----
このスクリプトは以下のチェックを実行します:
- 循環依存の検出
- 優先度と依存関係の整合性検証
- ステータスの整合性検証（project.md vs GitHub Issues）
- Issue未紐付けタスクの検出
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ANSI colors
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


@dataclass
class Issue:
    """GitHub Issue の情報.

    Attributes
    ----------
    number : int
        Issue番号
    title : str
        Issueタイトル
    state : str
        状態（OPEN/CLOSED）
    labels : list[str]
        ラベルリスト
    depends_on : list[int]
        このIssueが依存するIssue番号のリスト
    blocks : list[int]
        このIssueがブロックするIssue番号のリスト
    """

    number: int
    title: str
    state: str
    labels: list[str] = field(default_factory=list)
    depends_on: list[int] = field(default_factory=list)
    blocks: list[int] = field(default_factory=list)


@dataclass
class ProjectTask:
    """project.md のタスク情報.

    Attributes
    ----------
    id : str
        タスクID（例: "1.1"）
    title : str
        タスクタイトル
    issue_number : int | None
        紐付けられたIssue番号（未紐付けの場合はNone）
    priority : str
        優先度（high/medium/low）
    status : str
        ステータス（todo/in_progress/done）
    depends_on : list[int]
        依存するIssue番号のリスト
    """

    id: str
    title: str
    issue_number: int | None
    priority: str
    status: str
    depends_on: list[int] = field(default_factory=list)


@dataclass
class CheckResult:
    """チェック結果.

    Attributes
    ----------
    level : str
        重要度（"critical", "warning", "info"）
    message : str
        結果メッセージ
    details : str
        詳細情報（オプション）
    """

    level: str  # "critical", "warning", "info"
    message: str
    details: str = ""


def run_gh_command(args: list[str]) -> dict[str, Any] | list[Any] | None:
    """gh コマンドを実行して JSON を返す.

    Parameters
    ----------
    args : list[str]
        gh コマンドに渡す引数リスト

    Returns
    -------
    dict[str, Any] | list[Any] | None
        コマンドの実行結果（JSON形式）、失敗時はNone

    Notes
    -----
    - タイムアウトは30秒
    - gh コマンドが見つからない場合やJSON解析に失敗した場合はNoneを返す
    """
    try:
        result = subprocess.run(
            ["gh", *args],  # nosec B607 - gh is GitHub CLI, intentionally used
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return None
        return json.loads(result.stdout) if result.stdout.strip() else None
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def find_project_files() -> list[Path]:
    """project.md ファイルを検索.

    Returns
    -------
    list[Path]
        見つかった project.md ファイルのリスト

    Notes
    -----
    以下の2つのモードに対応:
    - パッケージ開発モード: src/*/docs/project.md
    - 軽量プロジェクトモード: docs/project/*.md
    """
    project_files = []

    # パッケージ開発モード: src/*/docs/project.md
    for path in Path("src").glob("*/docs/project.md"):
        project_files.append(path)

    # 軽量プロジェクトモード: docs/project/*.md
    docs_project = Path("docs/project")
    if docs_project.exists():
        for path in docs_project.glob("*.md"):
            project_files.append(path)

    return project_files


def parse_project_md(path: Path) -> tuple[list[ProjectTask], int | None]:
    """project.md をパースしてタスク一覧と GitHub Project 番号を抽出.

    Parameters
    ----------
    path : Path
        project.md ファイルのパス

    Returns
    -------
    tuple[list[ProjectTask], int | None]
        (タスク一覧, GitHub Project番号)のタプル
        Project番号が見つからない場合はNone

    Notes
    -----
    タスク形式: #### 機能 X.Y: タイトル
    必須フィールド: Issue, 優先度, ステータス
    オプション: depends_on
    """
    content = path.read_text(encoding="utf-8")
    tasks: list[ProjectTask] = []
    project_number: int | None = None

    # GitHub Project 番号の抽出
    project_match = re.search(r"\*\*GitHub Project\*\*:\s*\[#(\d+)\]", content)
    if project_match:
        project_number = int(project_match.group(1))

    # タスクの抽出（#### 機能 X.Y: タイトル 形式）
    task_pattern = re.compile(
        r"####\s+(?:機能\s+)?(\d+\.\d+):\s*(.+?)(?:\n|$)", re.MULTILINE
    )
    issue_pattern = re.compile(r"Issue:\s*\[#(\d+)\]")
    priority_pattern = re.compile(r"優先度:\s*(high|medium|low)", re.IGNORECASE)
    status_pattern = re.compile(r"ステータス:\s*(todo|in_progress|done)", re.IGNORECASE)
    depends_pattern = re.compile(r"depends_on:\s*\[#(\d+)\]")

    # 各タスクブロックを処理
    sections = re.split(r"(?=####\s+)", content)
    for section in sections:
        task_match = task_pattern.match(section)
        if not task_match:
            continue

        task_id = task_match.group(1)
        title = task_match.group(2).strip()

        issue_match = issue_pattern.search(section)
        issue_number = int(issue_match.group(1)) if issue_match else None

        priority_match = priority_pattern.search(section)
        priority = priority_match.group(1).lower() if priority_match else "medium"

        status_match = status_pattern.search(section)
        status = status_match.group(1).lower() if status_match else "todo"

        depends_on = [int(m.group(1)) for m in depends_pattern.finditer(section)]

        tasks.append(
            ProjectTask(
                id=task_id,
                title=title,
                issue_number=issue_number,
                priority=priority,
                status=status,
                depends_on=depends_on,
            )
        )

    return tasks, project_number


def parse_issue_dependencies(body: str) -> tuple[list[int], list[int]]:
    """Issue 本文から依存関係を抽出.

    Parameters
    ----------
    body : str
        Issue本文

    Returns
    -------
    tuple[list[int], list[int]]
        (depends_on, blocks)のタプル
        depends_on: このIssueが依存するIssue番号のリスト
        blocks: このIssueがブロックするIssue番号のリスト

    Notes
    -----
    認識パターン:
    - depends_on: #123, depends on #123
    - blocks: #123
    """
    depends_on: list[int] = []
    blocks: list[int] = []

    depends_pattern = re.compile(r"depends[_\s]on[:\s]*#(\d+)", re.IGNORECASE)
    blocks_pattern = re.compile(r"blocks[:\s]*#(\d+)", re.IGNORECASE)

    depends_on = [int(m.group(1)) for m in depends_pattern.finditer(body)]
    blocks = [int(m.group(1)) for m in blocks_pattern.finditer(body)]

    return depends_on, blocks


def fetch_github_issues() -> list[Issue]:
    """GitHub Issues を取得.

    Returns
    -------
    list[Issue]
        取得したIssueのリスト、失敗時は空リスト

    Notes
    -----
    - gh CLI を使用してIssueを取得
    - 最大200件まで取得
    - 依存関係情報も自動的にパース
    """
    data = run_gh_command(
        [
            "issue",
            "list",
            "--state",
            "all",
            "--json",
            "number,title,body,state,labels",
            "--limit",
            "200",
        ]
    )
    if not data or not isinstance(data, list):
        return []

    issues: list[Issue] = []
    for item in data:
        labels = [label.get("name", "") for label in item.get("labels", [])]
        depends_on, blocks = parse_issue_dependencies(item.get("body", ""))
        issues.append(
            Issue(
                number=item["number"],
                title=item["title"],
                state=item["state"],
                labels=labels,
                depends_on=depends_on,
                blocks=blocks,
            )
        )
    return issues


def check_circular_dependencies(issues: list[Issue]) -> list[CheckResult]:
    """循環依存を検出.

    Parameters
    ----------
    issues : list[Issue]
        チェック対象のIssueリスト

    Returns
    -------
    list[CheckResult]
        検出された循環依存のリスト

    Notes
    -----
    深さ優先探索（DFS）を使用して循環を検出します。
    同一の循環パターンは1回のみ報告されます。
    """
    results: list[CheckResult] = []

    # 依存関係グラフを構築
    graph: dict[int, list[int]] = {}
    for issue in issues:
        graph[issue.number] = issue.depends_on

    def find_cycle(
        start: int, visited: set[int], rec_stack: set[int], path: list[int]
    ) -> list[int] | None:
        visited.add(start)
        rec_stack.add(start)
        path.append(start)

        for dep in graph.get(start, []):
            if dep not in visited and dep in graph:
                cycle = find_cycle(dep, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif dep in rec_stack and dep in path:
                # 循環を検出
                cycle_start = path.index(dep)
                return [*path[cycle_start:], dep]

        path.pop()
        rec_stack.remove(start)
        return None

    visited: set[int] = set()
    reported_cycles: set[frozenset[int]] = set()

    for issue_num in graph:
        if issue_num not in visited:
            cycle = find_cycle(issue_num, visited, set(), [])
            if cycle:
                cycle_set = frozenset(cycle)
                if cycle_set not in reported_cycles:
                    cycle_str = " → ".join(f"#{n}" for n in cycle)
                    results.append(
                        CheckResult(
                            level="critical",
                            message="依存関係の循環を検出",
                            details=cycle_str,
                        )
                    )
                    reported_cycles.add(cycle_set)

    return results


def check_priority_consistency(
    tasks: list[ProjectTask], issues: list[Issue]
) -> list[CheckResult]:
    """優先度と依存関係の整合性をチェック.

    Parameters
    ----------
    tasks : list[ProjectTask]
        project.mdのタスクリスト
    issues : list[Issue]
        GitHub Issueリスト

    Returns
    -------
    list[CheckResult]
        検出された優先度矛盾のリスト

    Notes
    -----
    高優先度タスクが低優先度タスクに依存している場合、警告を発行します。
    """
    results: list[CheckResult] = []

    # Issue 番号 → 優先度のマップを作成
    priority_map: dict[int, str] = {}
    for task in tasks:
        if task.issue_number:
            priority_map[task.issue_number] = task.priority

    # Issue のラベルからも優先度を取得
    for issue in issues:
        if issue.number not in priority_map:
            for label in issue.labels:
                if label.startswith("priority:"):
                    priority_map[issue.number] = label.split(":")[1]
                    break

    priority_order = {"high": 3, "medium": 2, "low": 1}

    for task in tasks:
        if not task.issue_number:
            continue
        task_priority = priority_order.get(task.priority, 2)

        for dep_num in task.depends_on:
            dep_priority_str = priority_map.get(dep_num, "medium")
            dep_priority = priority_order.get(dep_priority_str, 2)

            if task_priority > dep_priority:
                results.append(
                    CheckResult(
                        level="warning",
                        message=f"優先度矛盾: #{task.issue_number} ({task.priority}) が #{dep_num} ({dep_priority_str}) に依存",
                        details=f"#{dep_num} の優先度を {task.priority} に引き上げることを検討",
                    )
                )

    return results


def check_status_consistency(
    tasks: list[ProjectTask], issues: list[Issue]
) -> list[CheckResult]:
    """ステータスの整合性をチェック.

    Parameters
    ----------
    tasks : list[ProjectTask]
        project.mdのタスクリスト
    issues : list[Issue]
        GitHub Issueリスト

    Returns
    -------
    list[CheckResult]
        検出されたステータス不整合のリスト

    Notes
    -----
    以下のケースで警告を発行:
    - project.md: done だが GitHub: open
    - project.md: todo/in_progress だが GitHub: closed
    """
    results: list[CheckResult] = []

    issue_state_map = {issue.number: issue.state for issue in issues}

    for task in tasks:
        if not task.issue_number:
            continue

        github_state = issue_state_map.get(task.issue_number)
        if not github_state:
            continue

        # project.md: done だが GitHub: open
        if task.status == "done" and github_state == "OPEN":
            results.append(
                CheckResult(
                    level="warning",
                    message=f"ステータス不整合: #{task.issue_number}",
                    details="project.md: done, GitHub: open",
                )
            )

        # project.md: todo/in_progress だが GitHub: closed
        if task.status in ("todo", "in_progress") and github_state == "CLOSED":
            results.append(
                CheckResult(
                    level="warning",
                    message=f"ステータス不整合: #{task.issue_number}",
                    details=f"project.md: {task.status}, GitHub: closed",
                )
            )

    return results


def check_orphan_tasks(tasks: list[ProjectTask]) -> list[CheckResult]:
    """Issue に紐づいていないタスクを検出.

    Parameters
    ----------
    tasks : list[ProjectTask]
        project.mdのタスクリスト

    Returns
    -------
    list[CheckResult]
        Issue未紐付けタスクのリスト（infoレベル）

    Notes
    -----
    Issue番号がNoneのタスクを検出し、/issueコマンドでの作成を推奨します。
    """
    results: list[CheckResult] = []

    for task in tasks:
        if task.issue_number is None:
            results.append(
                CheckResult(
                    level="info",
                    message=f"Issue 未紐付け: 機能 {task.id} - {task.title}",
                    details="/issue コマンドで Issue を作成することを検討",
                )
            )

    return results


def print_results(
    results: list[CheckResult], project_file: Path
) -> tuple[int, int, int]:
    """結果を表示し、各レベルの件数を返す.

    Parameters
    ----------
    results : list[CheckResult]
        チェック結果リスト
    project_file : Path
        チェック対象のproject.mdファイルパス

    Returns
    -------
    tuple[int, int, int]
        (critical件数, warning件数, info件数)のタプル
    """
    critical_count = 0
    warning_count = 0
    info_count = 0

    print(f"\n{CYAN}{BOLD}=== {project_file} ==={RESET}")

    for result in results:
        if result.level == "critical":
            critical_count += 1
            icon = f"{RED}🔴 CRITICAL{RESET}"
        elif result.level == "warning":
            warning_count += 1
            icon = f"{YELLOW}🟠 WARNING{RESET}"
        else:
            info_count += 1
            icon = f"{CYAN}🟡 INFO{RESET}"

        print(f"  {icon}: {result.message}")
        if result.details:
            print(f"       → {result.details}")

    return critical_count, warning_count, info_count


def main() -> int:
    """メイン処理.

    Returns
    -------
    int
        終了コード
        0: 成功、1: Critical エラーまたは Warning（strictモード）

    Notes
    -----
    実行モード:
    - 通常モード: Criticalエラーのみで失敗
    - strictモード (--strict): Warningでも失敗
    - ローカルモード (--skip-github): GitHub API呼び出しをスキップ
    """
    strict_mode = "--strict" in sys.argv
    skip_github = "--skip-github" in sys.argv

    print(f"{BOLD}🔍 プロジェクト整合性チェック{RESET}")

    project_files = find_project_files()
    if not project_files:
        print(f"{YELLOW}project.md が見つかりません。スキップします。{RESET}")
        return 0

    total_critical = 0
    total_warning = 0
    total_info = 0

    # GitHub Issues を取得（スキップオプションがなければ）
    issues: list[Issue] = []
    if not skip_github:
        print(f"{CYAN}GitHub Issues を取得中...{RESET}")
        issues = fetch_github_issues()
        if not issues:
            print(
                f"{YELLOW}GitHub Issues の取得に失敗しました。ローカルチェックのみ実行します。{RESET}"
            )

    for project_file in project_files:
        results: list[CheckResult] = []

        # project.md をパース
        tasks, _project_number = parse_project_md(project_file)
        if not tasks:
            print(f"{YELLOW}{project_file}: タスクが見つかりません{RESET}")
            continue

        # ローカルチェック
        results.extend(check_orphan_tasks(tasks))

        # GitHub を使ったチェック
        if issues:
            results.extend(check_circular_dependencies(issues))
            results.extend(check_priority_consistency(tasks, issues))
            results.extend(check_status_consistency(tasks, issues))

        # 結果表示
        if results:
            critical, warning, info = print_results(results, project_file)
            total_critical += critical
            total_warning += warning
            total_info += info
        else:
            print(f"\n{GREEN}✓ {project_file}: 問題なし{RESET}")

    # サマリー
    print(f"\n{BOLD}=== サマリー ==={RESET}")
    print(f"  🔴 Critical: {total_critical}")
    print(f"  🟠 Warning:  {total_warning}")
    print(f"  🟡 Info:     {total_info}")

    # 終了コード決定
    if total_critical > 0:
        print(f"\n{RED}{BOLD}❌ Critical エラーがあります。push を中止します。{RESET}")
        print("   `/project-refine` コマンドで修正してください。")
        return 1

    if strict_mode and total_warning > 0:
        print(
            f"\n{YELLOW}{BOLD}❌ Warning があります（strict モード）。push を中止します。{RESET}"
        )
        print("   `/project-refine` コマンドで修正してください。")
        return 1

    if total_warning > 0:
        print(
            f"\n{YELLOW}⚠ Warning があります。`/project-refine` での確認を推奨します。{RESET}"
        )

    print(f"\n{GREEN}{BOLD}✓ チェック完了{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
