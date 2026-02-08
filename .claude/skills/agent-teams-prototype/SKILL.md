---
name: agent-teams-prototype
description: Agent Teams API の最小プロトタイプを実行し、基本パターン（チーム作成、タスク依存関係、メッセージング、シャットダウン）を検証するスキル。
---

# Agent Teams Prototype

Agent Teams API の最小プロトタイプ（リーダー + 2チームメイト）を実行し、基本的な動作パターンを検証するスキルです。

## 目的

このスキルは以下を提供します：

- **基本パターンの検証手順**: TeamCreate / TaskCreate / TaskUpdate / TaskList / SendMessage の動作確認
- **依存関係パターン**: addBlockedBy による依存タスクのブロック・アンブロック動作の検証
- **ライフサイクル管理**: チームメイトの起動・アイドル・シャットダウンの検証
- **Wave 2以降の前提知識**: 実際のワークフロー移行に必要な基本パターンの確立

## いつ使用するか

### 明示的な使用（ユーザー要求）

- `/run-agent-teams-prototype` コマンドの実行時
- 「Agent Teams プロトタイプを実行して」という要求
- Agent Teams API の動作確認が必要な場合

## 前提条件

以下のエージェント定義が存在すること：

| エージェント | パス | 役割 |
|-------------|------|------|
| prototype-team-lead | `.claude/agents/prototype-team-lead.md` | リーダー |
| prototype-worker-a | `.claude/agents/prototype-worker-a.md` | ワーカーA（独立タスク） |
| prototype-worker-b | `.claude/agents/prototype-worker-b.md` | ワーカーB（依存タスク） |

## 実行手順

### Phase 1: チーム作成

TeamCreate ツールでプロトタイプチームを作成します。

```yaml
TeamCreate:
  team_name: "prototype-team"
  description: "Agent Teams API の基本パターン検証用プロトタイプチーム"
```

**確認**: `~/.claude/teams/prototype-team/` ディレクトリが作成されたこと。

### Phase 2: タスク登録と依存関係の設定

2つのタスクを登録し、依存関係を設定します。

#### タスク1: テストデータの生成（独立タスク）

```yaml
TaskCreate:
  subject: "テストデータファイルの生成"
  description: |
    .tmp/prototype-test-data.json にテストデータを書き出す。
    内容: {"message": "Hello from worker-a", "timestamp": "<current_time>", "worker": "prototype-worker-a", "status": "completed"}
  activeForm: "テストデータファイルを生成中"
```

#### タスク2: テストデータの読み込みと検証（依存タスク）

```yaml
TaskCreate:
  subject: "テストデータの読み込みと検証"
  description: |
    .tmp/prototype-test-data.json を読み込み、内容を検証する。
    検証項目:
    - message フィールドが存在し空でないこと
    - worker フィールドが "prototype-worker-a" であること
    - timestamp フィールドが存在すること
  activeForm: "テストデータを読み込み検証中"
```

#### 依存関係の設定

```yaml
TaskUpdate:
  taskId: "<task-2-id>"
  addBlockedBy: ["<task-1-id>"]
```

**確認**: TaskList で task-2 の blockedBy に task-1 の ID が含まれていること。

### Phase 3: チームメイトの起動とタスク割り当て

2つのチームメイトを起動し、タスクを割り当てます。

#### チームメイトの起動

```yaml
# worker-a（独立タスク担当）
Task:
  subagent_type: "prototype-worker-a"
  team_name: "prototype-team"
  name: "worker-a"
  prompt: |
    あなたは prototype-team の worker-a です。
    TaskList でタスクを確認し、あなたに割り当てられたタスクを実行してください。

    ## 担当タスク
    タスク: テストデータファイルの生成
    出力先: .tmp/prototype-test-data.json

    ## 手順
    1. .tmp/ ディレクトリを確認（なければ作成）
    2. テストデータ JSON を生成して書き出し
    3. TaskUpdate で完了をマーク
    4. リーダーに SendMessage で完了通知

# worker-b（依存タスク担当）
Task:
  subagent_type: "prototype-worker-b"
  team_name: "prototype-team"
  name: "worker-b"
  prompt: |
    あなたは prototype-team の worker-b です。
    TaskList でタスクを確認してください。
    タスクがブロック中の場合は、ブロック解除を待ってから実行してください。

    ## 担当タスク
    タスク: テストデータの読み込みと検証
    入力元: .tmp/prototype-test-data.json

    ## 手順
    1. TaskList でブロック状態を確認
    2. ブロック中ならリーダーに報告して待機
    3. ブロック解除後、ファイルを Read で読み込み
    4. JSON の内容を検証
    5. TaskUpdate で完了をマーク
    6. リーダーに SendMessage で検証結果を通知
```

#### タスク割り当て

```yaml
TaskUpdate:
  taskId: "<task-1-id>"
  owner: "worker-a"

TaskUpdate:
  taskId: "<task-2-id>"
  owner: "worker-b"
```

### Phase 4: 実行監視と依存関係の検証

チームメイトからのメッセージを受信しながら、以下を監視します。

1. **worker-a の完了**: task-1 が completed になること
2. **依存関係の解除**: task-2 の blockedBy が空になること
3. **worker-b の実行開始**: task-2 が in_progress になること
4. **worker-b の完了**: task-2 が completed になること

**重要**: チームメイトからのメッセージは自動的に配信されます。手動でチェックする必要はありません。

### Phase 5: シャットダウンとクリーンアップ

全タスク完了を確認後、チームメイトをシャットダウンします。

```yaml
# worker-a のシャットダウン
SendMessage:
  type: "shutdown_request"
  recipient: "worker-a"
  content: "全タスクが完了しました。シャットダウンしてください。"

# worker-b のシャットダウン
SendMessage:
  type: "shutdown_request"
  recipient: "worker-b"
  content: "全タスクが完了しました。シャットダウンしてください。"
```

シャットダウン完了後:

```yaml
# チームの削除
TeamDelete: {}

# 一時ファイルのクリーンアップ
Bash: rm -f .tmp/prototype-test-data.json
```

### Phase 6: 検証結果のサマリー出力

全 Phase の結果をまとめて出力します。

```yaml
prototype_verification:
  team_name: "prototype-team"
  status: "success"

  verifications:
    team_create:
      status: "PASS"
      detail: "TeamCreate でチームが正常に作成された"

    task_create_and_dependency:
      status: "PASS"
      detail: "TaskCreate で2タスク登録、addBlockedBy で依存関係を設定"

    dependency_blocking:
      status: "PASS"
      detail: "task-2 が task-1 によって正しくブロックされた"

    dependency_unblocking:
      status: "PASS"
      detail: "task-1 完了後に task-2 が自動的にアンブロックされた"

    send_message:
      status: "PASS"
      detail: "チームメイト → リーダーの SendMessage が正常に動作"

    shutdown:
      status: "PASS"
      detail: "shutdown_request → shutdown_response で全チームメイトが正常終了"

  summary:
    total_checks: 6
    passed: 6
    failed: 0
```

## 検証パターンの詳細

### パターン1: TeamCreate / TeamDelete

```
TeamCreate(team_name) → チーム作成
  ↓
作業実行
  ↓
TeamDelete() → チーム削除
```

**検証項目**:
- チームが作成される（~/.claude/teams/{team_name}/ が存在）
- チーム削除が正常に完了する

### パターン2: TaskCreate + addBlockedBy

```
TaskCreate(task-1) → 独立タスク
TaskCreate(task-2) → 依存タスク
TaskUpdate(task-2, addBlockedBy: [task-1]) → 依存関係設定
```

**検証項目**:
- TaskList で task-2 の blockedBy に task-1 が含まれる
- task-1 が pending/in_progress の間、task-2 は開始不可

### パターン3: 依存関係の自動解除

```
TaskUpdate(task-1, status: completed) → task-1 完了
  ↓ 自動
TaskList で task-2 の blockedBy が空になる → task-2 開始可能
```

**検証項目**:
- task-1 を completed にした直後に TaskList で task-2 の blockedBy が空

### パターン4: SendMessage（通知パターン）

```
worker → leader: "task 完了、出力ファイル: {path}"
leader → worker: shutdown_request
worker → leader: shutdown_response(approve: true)
```

**検証項目**:
- メッセージが正しく配信される
- ファイルパスのみで、データ本体を含めない

### パターン5: シャットダウンライフサイクル

```
leader: SendMessage(type: shutdown_request, recipient: worker)
  ↓
worker: SendMessage(type: shutdown_response, approve: true)
  ↓
worker プロセスが終了
  ↓
leader: TeamDelete()
```

**検証項目**:
- shutdown_request が正しく送信される
- shutdown_response(approve: true) が返される
- チームメイトのプロセスが終了する

## 既知のパターンと注意事項

### アイドル状態について

チームメイトは毎ターン終了後にアイドル状態になります。これは正常な動作です。

- アイドル通知が自動送信される
- アイドル状態のチームメイトにメッセージを送ると復帰する
- アイドル = エラーではない

### SendMessage のサイズ制限

SendMessage はテキストベースで、大量データの転送には不適切です。

- ファイルパスとメタデータのみを送信する
- データ本体は .tmp/ ファイル経由で受け渡す
- 50KB超のデータは必ずファイル経由にする

### タスクの状態遷移

```
pending → in_progress → completed
                      → (failed: 手動設定)
```

- addBlockedBy でブロックされたタスクは、blockedBy が空になるまで開始不可
- completed になったタスクは、他のタスクの blockedBy から自動的に除外される

## エラーハンドリング

### チーム作成失敗

**原因**: 同名チームが既に存在する

**対処**:
1. `~/.claude/teams/prototype-team/` の存在を確認
2. 存在する場合は TeamDelete で削除後にリトライ

### チームメイト起動失敗

**原因**: エージェント定義ファイルが見つからない

**対処**:
1. `.claude/agents/prototype-worker-a.md` の存在確認
2. `.claude/agents/prototype-worker-b.md` の存在確認
3. ファイルがない場合はエラーサマリーを出力

### タスク完了待ちタイムアウト

**原因**: チームメイトが応答しない

**対処**:
1. TaskList でタスクの状態を確認
2. チームメイトに SendMessage で状態確認
3. 応答がない場合は強制シャットダウンを検討

## 完了条件

- [ ] TeamCreate でチームが正常に作成された
- [ ] TaskCreate で2タスクが登録された
- [ ] addBlockedBy で依存関係が正しく設定された
- [ ] チームメイトが正常に起動した
- [ ] 依存タスク完了後に後続タスクが自動アンブロックされた
- [ ] SendMessage でメッセージ送受信が動作した
- [ ] shutdown_request/response でチームが正常終了した
- [ ] 検証結果サマリーが出力された

## 関連

- **エージェント**: `.claude/agents/prototype-team-lead.md`
- **エージェント**: `.claude/agents/prototype-worker-a.md`
- **エージェント**: `.claude/agents/prototype-worker-b.md`
- **Issue #3233**: Agent Teams 共通実装パターンのプロトタイプ作成
- **Issue #3234**: ファイルベースデータ受け渡しパターンの検証
- **Issue #3235**: エラーハンドリング・部分障害パターンの確立
- **Issue #3236**: Agent Teams 共通実装パターンドキュメントの作成
