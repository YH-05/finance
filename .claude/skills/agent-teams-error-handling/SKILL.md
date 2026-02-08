---
name: agent-teams-error-handling
description: Agent Teams でのエラーハンドリング・部分障害パターンを検証するスキル。チームメイト障害の検知、必須/任意依存の判定、部分結果の保存と再実行スキップパターンを確立する。
---

# Agent Teams エラーハンドリング・部分障害パターン

Agent Teams において、チームメイトの障害が発生した場合のエラー検知・リカバリパターンを検証するスキルです。

## 背景と目的

### なぜエラーハンドリングパターンが必要か

Agent Teams では、1つのチームメイトの失敗がチーム全体に波及する可能性があります。

- **依存タスクのブロック**: 失敗したタスクに依存するタスクが永久にブロック状態になる
- **部分結果の消失**: 成功したタスクの結果が失敗タスクと共に破棄される
- **リカバリ不能**: エラー検知と復旧手順がないとチーム全体が停止する

### このスキルが確立するパターン

1. **エラー検知パターン**: リーダーがチームメイトの失敗を検知する方法
2. **失敗タスクマーキング**: TaskUpdate でエラー情報付きで完了をマークする方法
3. **依存関係評価パターン**: 必須依存 vs 任意依存の判定と影響範囲の評価
4. **部分結果保存パターン**: 成功した結果を保持し、再実行時にスキップする方法

## いつ使用するか

### 明示的な使用（ユーザー要求）

- 「エラーハンドリングパターンを検証して」という要求
- Agent Teams の耐障害設計を確認したい場合
- チームメイト障害からのリカバリパターンを検証する場合

## 前提条件

以下のエージェント定義が存在すること：

| エージェント | パス | 役割 |
|-------------|------|------|
| error-handling-team-lead | `.claude/agents/error-handling-team-lead.md` | リーダー（障害検知・リカバリ制御） |
| error-handling-worker-a | `.claude/agents/error-handling-worker-a.md` | ワーカーA（意図的失敗シミュレーション） |
| error-handling-worker-b | `.claude/agents/error-handling-worker-b.md` | ワーカーB（必須依存タスク担当） |
| error-handling-worker-c | `.claude/agents/error-handling-worker-c.md` | ワーカーC（任意依存タスク担当） |

## 実行手順

### Phase 1: チーム作成

```yaml
TeamCreate:
  team_name: "error-handling-team"
  description: "エラーハンドリング・部分障害パターンの検証チーム"
```

**確認**: `~/.claude/teams/error-handling-team/` ディレクトリが作成されたこと。

### Phase 2: タスク登録と依存関係の設定

4つのタスクを登録し、必須依存と任意依存を含む依存関係を設定します。

#### タスク1: データ生成（独立タスク、意図的に失敗する）

```yaml
TaskCreate:
  subject: "テストデータの生成（意図的失敗シミュレーション）"
  description: |
    .tmp/error-handling-data.json にテストデータを生成する。
    ただし、このタスクは意図的に失敗する。
    worker-a は処理途中でエラーを報告し、タスクを失敗状態にする。

    期待される動作:
    - worker-a がリーダーにエラーを報告する
    - リーダーがエラーを検知し、TaskUpdate でエラー情報付き完了をマークする
  activeForm: "テストデータ生成（失敗シミュレーション）中"
```

#### タスク2: 独立データ生成（正常に完了する）

```yaml
TaskCreate:
  subject: "バックアップデータの生成（正常完了）"
  description: |
    .tmp/error-handling-backup.json にバックアップデータを生成する。
    このタスクは正常に完了する。
    データ構造:
    {
      "type": "backup_data",
      "records": [{"id": 1, "name": "backup_record", "value": 200}],
      "metadata": {"generated_by": "error-handling-worker-a", "timestamp": "<ISO8601>", "status": "success"}
    }
  activeForm: "バックアップデータを生成中"
```

#### タスク3: 必須依存タスク（task-1 に必須依存）

```yaml
TaskCreate:
  subject: "データ検証（必須依存 - task-1 の結果が必要）"
  description: |
    .tmp/error-handling-data.json を読み込み検証する。
    このタスクは task-1 に必須依存しており、task-1 が失敗した場合は実行不可。

    依存タイプ: 必須（required）
    - task-1 が成功した場合のみ実行可能
    - task-1 が失敗した場合はスキップされる

    期待される動作:
    - task-1 の失敗を検知したリーダーがこのタスクをスキップとしてマークする
  activeForm: "データ検証（必須依存）を実行中"
```

#### タスク4: 任意依存タスク（task-1 に任意依存、task-2 に必須依存）

```yaml
TaskCreate:
  subject: "サマリー生成（任意依存 - 部分結果で続行可能）"
  description: |
    利用可能なデータからサマリーを生成する。
    - task-1 のデータがあればそれを含める（任意依存）
    - task-2 のデータは必須（必須依存）

    依存タイプ:
    - task-1: 任意（optional）- 失敗しても task-2 のデータだけで続行可能
    - task-2: 必須（required）- 失敗したらスキップ

    出力先: .tmp/error-handling-summary.json
    データ構造:
    {
      "type": "summary",
      "sources": {
        "primary_data": null | {...},  // task-1 が成功した場合のみ
        "backup_data": {...}           // task-2 の結果（必須）
      },
      "partial_result": true | false,  // task-1 が失敗した場合 true
      "metadata": {"generated_by": "error-handling-worker-c", "timestamp": "<ISO8601>"}
    }
  activeForm: "サマリー生成（部分結果で続行）中"
```

#### 依存関係の設定

```yaml
# task-3: task-1 に必須依存（task-1 がブロック）
TaskUpdate:
  taskId: "<task-3-id>"
  addBlockedBy: ["<task-1-id>"]

# task-4: task-1 に任意依存、task-2 に必須依存
# ただし Agent Teams の addBlockedBy は必須依存のみ対応
# 任意依存はリーダーが手動で制御する
TaskUpdate:
  taskId: "<task-4-id>"
  addBlockedBy: ["<task-2-id>"]
# 注意: task-1 は addBlockedBy に含めない（任意依存のため）
```

**確認**: TaskList で依存関係が正しく設定されていること。

### Phase 3: チームメイトの起動とタスク割り当て

```yaml
# worker-a（データ生成担当 - task-1 は失敗、task-2 は成功）
Task:
  subagent_type: "error-handling-worker-a"
  team_name: "error-handling-team"
  name: "worker-a"
  prompt: |
    あなたは error-handling-team の worker-a です。
    TaskList でタスクを確認し、あなたに割り当てられたタスクを実行してください。

    ## 担当タスク
    1. task-1: テストデータの生成（このタスクは意図的に失敗してください）
    2. task-2: バックアップデータの生成（このタスクは正常に完了してください）

    ## task-1 の失敗シミュレーション手順
    1. TaskUpdate で task-1 を in_progress にする
    2. 処理を開始するが、途中でエラーが発生したと判断する
    3. リーダーにエラー内容を SendMessage で報告する
       - エラーメッセージ例: "task-1 の実行中にエラーが発生しました。原因: データソースへの接続に失敗（シミュレーション）"
    4. TaskUpdate で task-1 を completed にマーク（description にエラー情報を含める）

    ## task-2 の正常完了手順
    1. .tmp/ ディレクトリを確認（なければ作成）
    2. .tmp/error-handling-backup.json にバックアップデータを書き出し
    3. TaskUpdate で task-2 を completed にマーク
    4. リーダーにファイルパスを SendMessage で通知

# worker-b（必須依存タスク担当）
Task:
  subagent_type: "error-handling-worker-b"
  team_name: "error-handling-team"
  name: "worker-b"
  prompt: |
    あなたは error-handling-team の worker-b です。
    TaskList でタスクを確認してください。

    ## 担当タスク
    task-3: データ検証（task-1 に必須依存）

    ## 手順
    1. TaskList でブロック状態を確認
    2. ブロック中ならリーダーに報告して待機
    3. リーダーから「task-1 が失敗したため task-3 はスキップ」と
       通知された場合、了承してシャットダウンを待つ
    4. ブロック解除された場合は通常通りタスクを実行

# worker-c（任意依存タスク担当）
Task:
  subagent_type: "error-handling-worker-c"
  team_name: "error-handling-team"
  name: "worker-c"
  prompt: |
    あなたは error-handling-team の worker-c です。
    TaskList でタスクを確認してください。

    ## 担当タスク
    task-4: サマリー生成（task-1 に任意依存、task-2 に必須依存）

    ## 手順
    1. TaskList でブロック状態を確認（task-2 の完了を待つ）
    2. task-2 完了後、task-1 の状態をリーダーに確認
    3. task-1 が失敗している場合:
       - primary_data を null として処理
       - partial_result を true にする
       - task-2 のデータのみでサマリーを生成
    4. task-1 が成功している場合:
       - 両方のデータを使用してサマリーを生成
    5. .tmp/error-handling-summary.json に書き出し
    6. TaskUpdate で task-4 を completed にマーク
    7. リーダーに結果を SendMessage で通知
```

#### タスク割り当て

```yaml
TaskUpdate:
  taskId: "<task-1-id>"
  owner: "worker-a"

TaskUpdate:
  taskId: "<task-2-id>"
  owner: "worker-a"

TaskUpdate:
  taskId: "<task-3-id>"
  owner: "worker-b"

TaskUpdate:
  taskId: "<task-4-id>"
  owner: "worker-c"
```

### Phase 4: エラー検知とリカバリ

リーダーが実行する障害対応フローです。

#### 4.1 worker-a の失敗検知

```yaml
検知方法:
  1. worker-a からのエラー報告メッセージを受信
  2. TaskList で task-1 の状態を確認
  3. task-1 の description にエラー情報が含まれていることを確認

対応:
  - task-1 を「失敗完了」として記録
  - 失敗情報をメタデータとして保持
```

#### 4.2 必須依存タスクの評価（task-3）

```yaml
評価ロジック:
  1. task-3 の blockedBy に task-1 が含まれている
  2. task-1 が失敗している
  3. task-3 は task-1 に必須依存
  → task-3 はスキップ

対応:
  - task-3 の blockedBy から task-1 を手動解除（TaskUpdate）
  - task-3 を completed にマーク（description にスキップ理由を記載）
  - worker-b にスキップを通知（SendMessage）
```

#### 4.3 任意依存タスクの評価（task-4）

```yaml
評価ロジック:
  1. task-4 は task-1 に任意依存（addBlockedBy に含めていない）
  2. task-4 は task-2 に必須依存（addBlockedBy に含めている）
  3. task-2 が成功している
  → task-4 は部分結果で続行可能

対応:
  - task-2 完了後に task-4 が自動アンブロック
  - worker-c に task-1 の失敗状態を通知（SendMessage）
  - worker-c が部分結果でサマリーを生成
```

#### 4.4 部分結果の保存

```yaml
保存パターン:
  1. 成功したタスクの出力ファイルは保持される
     - .tmp/error-handling-backup.json（task-2 の結果）
     - .tmp/error-handling-summary.json（task-4 の結果）
  2. 失敗したタスクの出力は存在しない
     - .tmp/error-handling-data.json は生成されない（task-1 の失敗）
  3. スキップされたタスクは結果なし
     - task-3 はスキップされたため出力なし
```

### Phase 5: シャットダウンとクリーンアップ

```yaml
# worker-a のシャットダウン
SendMessage:
  type: "shutdown_request"
  recipient: "worker-a"
  content: "全タスクの評価が完了しました。シャットダウンしてください。"

# worker-b のシャットダウン
SendMessage:
  type: "shutdown_request"
  recipient: "worker-b"
  content: "task-3 はスキップされました。シャットダウンしてください。"

# worker-c のシャットダウン
SendMessage:
  type: "shutdown_request"
  recipient: "worker-c"
  content: "全タスクの評価が完了しました。シャットダウンしてください。"
```

シャットダウン完了後:

```yaml
# チームの削除
TeamDelete: {}

# 一時ファイルのクリーンアップ（skip_cleanup でなければ）
Bash: rm -f .tmp/error-handling-data.json .tmp/error-handling-backup.json .tmp/error-handling-summary.json
```

### Phase 6: 検証結果のサマリー出力

全 Phase の結果をまとめて出力します（出力フォーマットセクション参照）。

## 検証パターンの詳細

### パターン1: エラー検知（チームメイトの失敗検知）

```
worker-a: タスク実行中にエラー発生
  ↓
worker-a: SendMessage(content="エラー: データソース接続失敗（シミュレーション）")
  ↓
leader: メッセージ受信 → エラー検知
  ↓
leader: TaskList/TaskGet で task-1 の状態を確認
  ↓
leader: 失敗を記録、影響範囲を評価
```

**検証項目**:
- リーダーが worker-a のエラーメッセージを受信した
- TaskList/TaskGet で失敗状態を確認できた
- エラー情報が記録された

### パターン2: 失敗タスクのマーキング

```
leader: TaskUpdate(task-1, status=completed, description="失敗: データソース接続失敗")
```

**注意**: Agent Teams の TaskUpdate には `status: failed` が存在しないため、
`completed` + description にエラー情報を含める方式を採用する。

```yaml
TaskUpdate:
  taskId: "<task-1-id>"
  status: "completed"
  description: |
    [FAILED] テストデータの生成
    エラー: データソースへの接続に失敗（シミュレーション）
    発生時刻: <ISO8601>
    影響: task-3（必須依存）はスキップ、task-4（任意依存）は部分結果で続行
```

**検証項目**:
- task-1 が completed にマークされた
- description にエラー情報が含まれている
- [FAILED] プレフィックスで失敗を識別できる

### パターン3: 必須依存 vs 任意依存の判定

```yaml
依存関係マトリックス:
  task-3:
    task-1: required  # task-1 の出力が必須、失敗時はスキップ
  task-4:
    task-1: optional  # task-1 の出力は任意、失敗時は部分結果で続行
    task-2: required  # task-2 の出力は必須、失敗時はスキップ

判定ロジック:
  リーダーは依存関係マトリックスを保持し、失敗タスクの影響を評価する。

  for each pending_task:
    for each dependency:
      if dependency.status == FAILED:
        if dependency.type == required:
          → pending_task をスキップ
        elif dependency.type == optional:
          → pending_task を部分結果で続行（失敗した依存の出力は null）
```

**検証項目**:
- task-3 が正しくスキップされた（必須依存の task-1 が失敗）
- task-4 が部分結果で実行された（任意依存の task-1 が失敗、必須依存の task-2 が成功）

### パターン4: 部分結果の保存と再実行スキップ

```yaml
部分結果の保存:
  成功したタスクの出力:
    - .tmp/error-handling-backup.json  # task-2 の出力（保持）
    - .tmp/error-handling-summary.json # task-4 の出力（保持）
  失敗/スキップされたタスク:
    - task-1: 出力なし（失敗）
    - task-3: 出力なし（スキップ）

再実行時のスキップパターン:
  1. リーダーが .tmp/ ディレクトリを確認
  2. 既に存在する出力ファイルに対応するタスクをスキップ候補とする
  3. スキップ判定:
     - ファイルが存在 + 有効な JSON + タスクの description と一致
       → スキップ（再実行不要）
     - ファイルが存在しない or 無効
       → 再実行が必要
```

**検証項目**:
- 成功したタスクの出力が .tmp/ に保持されている
- 部分結果（task-4 の partial_result: true）が正しく生成された
- 再実行時にスキップ判定ロジックが機能する（概念検証）

### パターン5: 依存関係の手動解除

```
task-1 が失敗
  ↓
leader: task-3 の blockedBy から task-1 を除外するために
        task-1 を completed にマーク（Agent Teams の自動解除を利用）
  ↓
task-3 が自動アンブロック
  ↓
leader: task-3 を即座に completed にマーク（スキップ扱い、description に理由記載）
```

**注意**: Agent Teams では completed にしたタスクは blockedBy から自動除外されるため、
失敗タスクを completed にマークすることで依存タスクのブロックを解除できる。
ただし、必須依存のタスクはリーダーが即座にスキップとしてマークする必要がある。

**検証項目**:
- task-1 を completed にマーク後、task-3 の blockedBy が空になった
- リーダーが task-3 をスキップとしてマークした
- task-3 の worker（worker-b）にスキップ通知が送信された

## エラーハンドリング

### エラーパターン1: TeamCreate 失敗

**原因**: 同名チームが既に存在する

**対処**:
1. `~/.claude/teams/error-handling-team/` の存在確認
2. 存在する場合は TeamDelete で削除後にリトライ

### エラーパターン2: worker-a がエラー報告前にクラッシュ

**原因**: チームメイトプロセスの予期しない終了

**対処**:
1. チームメイトのアイドル/終了通知を監視
2. タスクが in_progress のまま応答がない場合、タイムアウトとみなす
3. リーダーが手動でタスクを失敗としてマーク

### エラーパターン3: worker-c が部分結果を正しく処理できない

**原因**: task-1 の失敗状態の伝達漏れ

**対処**:
1. リーダーが worker-c に明示的に task-1 の状態を通知
2. worker-c が TaskGet で依存タスクの状態を確認
3. 部分結果モードでの処理を実行

### エラーパターン4: シャットダウンリクエストが拒否される

**原因**: ワーカーが実行中のタスクを完了させたい

**対処**:
1. タスク状態を確認（実行中のタスクがあるか）
2. タスク完了を待ってから再度シャットダウンリクエスト
3. 最大3回リトライ後、強制的にチーム削除を検討

## 出力フォーマット

```yaml
error_handling_verification:
  team_name: "error-handling-team"
  execution_time: "{duration}"
  status: "success" | "partial_failure" | "failure"

  verifications:
    error_detection:
      status: "PASS" | "FAIL"
      detail: "リーダーが worker-a のエラーを正常に検知した"
      error_message: "データソースへの接続に失敗（シミュレーション）"

    failed_task_marking:
      status: "PASS" | "FAIL"
      detail: "task-1 が [FAILED] プレフィックス付きで completed にマークされた"
      task_id: "<task-1-id>"
      description_contains_error: true

    required_dependency_skip:
      status: "PASS" | "FAIL"
      detail: "task-3（必須依存）が正しくスキップされた"
      skipped_task: "<task-3-id>"
      reason: "必須依存先 task-1 が失敗"

    optional_dependency_continue:
      status: "PASS" | "FAIL"
      detail: "task-4（任意依存）が部分結果で正常に完了した"
      partial_result: true
      available_sources: ["backup_data"]
      missing_sources: ["primary_data"]

    partial_result_preservation:
      status: "PASS" | "FAIL"
      detail: "成功タスクの出力ファイルが保持されている"
      preserved_files:
        - path: ".tmp/error-handling-backup.json"
          exists: true
        - path: ".tmp/error-handling-summary.json"
          exists: true
      missing_files:
        - path: ".tmp/error-handling-data.json"
          reason: "task-1 が失敗したため未生成"

    dependency_unblock:
      status: "PASS" | "FAIL"
      detail: "task-1 を completed にした後、task-3 の blockedBy が空になった"

    worker_notification:
      status: "PASS" | "FAIL"
      detail: "worker-b にスキップ通知、worker-c に部分結果モード通知が送信された"

    shutdown:
      status: "PASS" | "FAIL"
      detail: "全チームメイトが正常にシャットダウン"

  summary:
    total_checks: 8
    passed: {count}
    failed: {count}
    skipped: {count}

  task_results:
    task_1:
      status: "FAILED"
      owner: "worker-a"
      error: "データソースへの接続に失敗（シミュレーション）"
    task_2:
      status: "SUCCESS"
      owner: "worker-a"
      output: ".tmp/error-handling-backup.json"
    task_3:
      status: "SKIPPED"
      owner: "worker-b"
      reason: "必須依存先 task-1 が失敗"
    task_4:
      status: "SUCCESS (partial)"
      owner: "worker-c"
      output: ".tmp/error-handling-summary.json"
      partial_result: true
```

## 確立されるパターン（再利用可能）

### パターン A: エラー検知パターン

```yaml
# リーダーがチームメイトの失敗を検知する標準手順
error_detection_pattern:
  step_1: "チームメイトからのエラーメッセージ受信（SendMessage 経由）"
  step_2: "TaskList/TaskGet で該当タスクの状態確認"
  step_3: "失敗タスクを completed にマーク（[FAILED] プレフィックス + エラー詳細を description に記載）"
  step_4: "影響範囲の評価（依存タスクの特定）"
```

### パターン B: 依存関係評価パターン

```yaml
# 必須依存 vs 任意依存の判定テンプレート
dependency_evaluation_pattern:
  dependency_matrix:
    # 各タスクの依存関係を定義（計画時にリーダーが保持）
    task_x:
      dep_a: "required"  # dep_a が失敗 → task_x はスキップ
      dep_b: "optional"  # dep_b が失敗 → task_x は部分結果で続行

  evaluation_logic: |
    1. 失敗したタスクを特定
    2. 各 pending タスクの依存関係を確認
    3. required 依存が失敗 → タスクをスキップ（completed + [SKIPPED] + 理由）
    4. optional 依存のみ失敗 → タスクを部分結果モードで実行
    5. 影響を受けるワーカーに通知

  implementation_note: |
    Agent Teams の addBlockedBy は「必須依存」のみを登録する。
    「任意依存」は addBlockedBy に含めず、リーダーが手動で状態を伝達する。
    これにより、任意依存先が失敗してもタスクがブロックされない。
```

### パターン C: 失敗タスクマーキングパターン

```yaml
# TaskUpdate で失敗情報を記録する標準形式
failed_task_marking_pattern:
  # Agent Teams には status: "failed" がないため completed を使用
  TaskUpdate:
    taskId: "<failed-task-id>"
    status: "completed"
    description: |
      [FAILED] <元のタスク説明>
      エラー: <エラーメッセージ>
      発生時刻: <ISO8601>
      影響: <影響を受けるタスク一覧>

  # スキップされたタスクの標準形式
  TaskUpdate:
    taskId: "<skipped-task-id>"
    status: "completed"
    description: |
      [SKIPPED] <元のタスク説明>
      理由: 必須依存先 <task-id> が失敗
      スキップ時刻: <ISO8601>
```

### パターン D: 部分結果保存パターン

```yaml
# 成功した結果を保持し、再実行時にスキップする標準手順
partial_result_pattern:
  preservation:
    - "成功タスクの出力ファイルは .tmp/ に保持"
    - "失敗/スキップタスクの出力は存在しない"
    - "部分結果フラグ（partial_result: true）を含む出力を生成"

  re_execution_skip:
    check: |
      1. .tmp/ 内の出力ファイル一覧を取得
      2. 各ファイルが有効な JSON であることを確認
      3. ファイルに対応するタスクを特定
      4. 該当タスクをスキップ候補としてマーク
    skip_condition: "ファイルが存在 AND 有効な JSON AND タスクの description と一致"
    re_execute_condition: "ファイルが存在しない OR 無効な JSON"
```

## 完了条件

- [ ] TeamCreate でチームが正常に作成された
- [ ] TaskCreate で4タスクが登録された
- [ ] 依存関係が正しく設定された（必須依存は addBlockedBy、任意依存は addBlockedBy に含めない）
- [ ] worker-a が task-1 を意図的に失敗させた
- [ ] worker-a が task-2 を正常に完了した
- [ ] リーダーが worker-a のエラーを検知した
- [ ] task-1 が [FAILED] プレフィックス付きで completed にマークされた
- [ ] task-3（必須依存）が正しくスキップされた
- [ ] worker-b にスキップが通知された
- [ ] task-4（任意依存）が部分結果で正常に完了した
- [ ] worker-c に task-1 の失敗状態が通知された
- [ ] 部分結果（.tmp/error-handling-summary.json）が正しく生成された
- [ ] 全チームメイトが正常にシャットダウンした
- [ ] 検証結果サマリーが出力された

## 関連

- **エージェント**: `.claude/agents/error-handling-team-lead.md`
- **エージェント**: `.claude/agents/error-handling-worker-a.md`
- **エージェント**: `.claude/agents/error-handling-worker-b.md`
- **エージェント**: `.claude/agents/error-handling-worker-c.md`
- **Issue #3233**: Agent Teams 共通実装パターンのプロトタイプ作成
- **Issue #3234**: ファイルベースデータ受け渡しパターンの検証
- **Issue #3235**: エラーハンドリング・部分障害パターンの確立
- **Issue #3236**: Agent Teams 共通実装パターンドキュメントの作成
