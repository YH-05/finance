# Agent Teams 共通実装パターン

Agent Teams API を使用したマルチエージェントワークフローの共通実装パターンをまとめたドキュメントです。Phase 0 の3つの検証タスク（プロトタイプ・ファイルベースデータ受け渡し・エラーハンドリング）の結果を基に整備しました。

## 目次

1. [チーム定義の標準構造](#1-チーム定義の標準構造)
2. [タスク登録と依存関係の設定パターン](#2-タスク登録と依存関係の設定パターン)
3. [ファイルベースデータ受け渡しの規約](#3-ファイルベースデータ受け渡しの規約)
4. [SendMessage の使用規約](#4-sendmessage-の使用規約)
5. [エラーハンドリングと部分障害リカバリのパターン](#5-エラーハンドリングと部分障害リカバリのパターン)
6. [チームメイトのライフサイクル管理](#6-チームメイトのライフサイクル管理)

---

## 1. チーム定義の標準構造

### 1.1 チーム作成

TeamCreate で新しいチームを作成します。チーム名はワークフローを識別する一意な名前を使用します。

```yaml
TeamCreate:
  team_name: "<workflow-name>-team"
  description: "<チームの目的を簡潔に記述>"
```

**作成されるリソース**:

| リソース | パス |
|---------|------|
| チーム設定 | `~/.claude/teams/<team-name>/config.json` |
| タスクリスト | `~/.claude/tasks/<team-name>/` |

### 1.2 チーム構成の基本形

すべてのチームは「リーダー + N チームメイト」の構成を取ります。

```
リーダー（orchestrator / team-lead）
├── チームメイトA（worker-a）
├── チームメイトB（worker-b）
└── チームメイトC（worker-c）
```

**リーダーの責務**:

- TeamCreate / TeamDelete によるチームライフサイクル管理
- TaskCreate / TaskUpdate によるタスク登録・依存関係設定
- タスクの割り当て（TaskUpdate で owner を設定）
- 実行監視（TaskList でタスク状態を確認）
- エラー検知と影響範囲の評価
- シャットダウン制御

**チームメイトの責務**:

- TaskList で割り当てタスクの確認
- タスク実行（ファイル読み書き、Bash コマンド実行など）
- TaskUpdate でタスク状態を更新（in_progress / completed）
- SendMessage でリーダーへの完了・エラー通知
- シャットダウンリクエストへの応答

### 1.3 エージェント定義の標準テンプレート

#### リーダーエージェント

```markdown
---
name: <workflow>-team-lead
description: <ワークフロー名>のリーダーエージェント
model: inherit
color: yellow
---

# <Workflow> Team Lead

## 目的
- チーム作成・タスク管理・実行監視を行う

## 処理フロー
Phase 1: チーム作成（TeamCreate）
Phase 2: タスク登録・依存関係設定（TaskCreate / TaskUpdate）
Phase 3: チームメイト起動・タスク割り当て（Task / TaskUpdate）
Phase 4: 実行監視（TaskList / SendMessage 受信）
Phase 5: シャットダウン・クリーンアップ（SendMessage / TeamDelete）
```

#### チームメイトエージェント

```markdown
---
name: <workflow>-worker-a
description: <担当内容>を実行するワーカー
model: inherit
color: green
tools: Read, Write, Bash, Glob
---

# <Workflow> Worker A

## 目的
- 割り当てられたタスクを実行する

## 処理フロー
1. TaskList でタスク確認
2. タスク実行（ファイル生成・処理など）
3. TaskUpdate で完了をマーク
4. SendMessage でリーダーに通知
5. シャットダウンリクエストに応答
```

### 1.4 チームメイトの起動

Task ツールを使用してチームメイトを起動します。`team_name` と `name` パラメータが必須です。

```yaml
Task:
  subagent_type: "<agent-name>"
  team_name: "<team-name>"
  name: "<worker-name>"
  prompt: |
    あなたは <team-name> の <worker-name> です。
    TaskList でタスクを確認し、割り当てられたタスクを実行してください。

    ## 担当タスク
    <タスクの説明>

    ## 手順
    1. TaskList でタスク確認
    2. <具体的な処理手順>
    3. TaskUpdate で完了をマーク
    4. リーダーに SendMessage で通知
```

---

## 2. タスク登録と依存関係の設定パターン

### 2.1 タスク登録

TaskCreate でタスクを登録します。`subject`（簡潔なタイトル）、`description`（詳細な説明）、`activeForm`（実行中のスピナー表示テキスト）を指定します。

```yaml
TaskCreate:
  subject: "テストデータの生成"
  description: |
    .tmp/output-data.json にテストデータを生成する。
    データ構造:
    {
      "type": "test_data",
      "records": [...],
      "metadata": {"generated_by": "worker-a", "timestamp": "<ISO8601>"}
    }
  activeForm: "テストデータを生成中"
```

### 2.2 依存関係の設定（addBlockedBy）

TaskUpdate の `addBlockedBy` を使用して、タスク間の依存関係を設定します。blockedBy に指定されたタスクが全て completed になるまで、対象タスクは開始できません。

```yaml
# task-2 は task-1 の完了を待つ
TaskUpdate:
  taskId: "<task-2-id>"
  addBlockedBy: ["<task-1-id>"]
```

**複数タスクへの依存**:

```yaml
# task-3 は task-1 と task-2 の両方の完了を待つ
TaskUpdate:
  taskId: "<task-3-id>"
  addBlockedBy: ["<task-1-id>", "<task-2-id>"]
```

### 2.3 依存関係の自動解除

タスクを `completed` にマークすると、そのタスクを blockedBy に含む他のタスクから自動的に除外されます。

```
TaskUpdate(task-1, status: completed)
  ↓ 自動
TaskList で task-2 の blockedBy が空になる → task-2 が開始可能
```

### 2.4 タスクの状態遷移

```
pending → in_progress → completed
```

- `pending`: 初期状態。blockedBy が空でないタスクは開始不可
- `in_progress`: 実行中。チームメイトが TaskUpdate で設定
- `completed`: 完了。正常完了・失敗完了・スキップ完了のいずれか

**注意**: Agent Teams には `status: failed` が存在しません。失敗は `completed` + description にエラー情報を含める方式で表現します（詳細はセクション5参照）。

### 2.5 タスク割り当て

TaskUpdate の `owner` パラメータでタスクをチームメイトに割り当てます。

```yaml
TaskUpdate:
  taskId: "<task-id>"
  owner: "worker-a"
```

### 2.6 依存関係パターンの使い分け

| パターン | 用途 | 設定方法 |
|---------|------|---------|
| 直列依存 | A → B → C（順序実行） | B に addBlockedBy: [A], C に addBlockedBy: [B] |
| 並列→合流 | A,B → C（並列実行後に合流） | C に addBlockedBy: [A, B] |
| 扇形展開 | A → B,C,D（1つから複数へ） | B,C,D にそれぞれ addBlockedBy: [A] |
| 必須依存のみ | 必須タスクの結果が必要 | addBlockedBy に登録 |
| 任意依存 | あれば使うが、なくても続行可能 | addBlockedBy に含めない（リーダーが手動制御） |

---

## 3. ファイルベースデータ受け渡しの規約

### 3.1 基本原則

チームメイト間のデータ受け渡しは、ファイルシステム経由で行います。SendMessage はメタデータ（ファイルパス、サイズ、統計情報）のみに限定します。

**理由**:

- SendMessage はテキストベースで、50KB超のデータ転送に不適切
- JSON データを文字列としてメッセージに含めると、パース時のエラーリスクが高まる
- ファイルとして永続化されるため、複数チームメイトから参照可能で再利用性が高い

### 3.2 ファイル配置規約

一時ファイルは `.tmp/` ディレクトリに配置します。

```
.tmp/
├── <workflow>-<data-name>.json     # ワークフロー固有データ
├── <workflow>-<session-id>.json    # セッション固有データ
└── <workflow>-summary.json         # サマリーデータ
```

**命名規則**: `<workflow-name>-<data-description>.json`

**例**:

```
.tmp/file-passing-small.json
.tmp/file-passing-large.json
.tmp/error-handling-backup.json
.tmp/error-handling-summary.json
```

### 3.3 データ書き出しパターン（Write）

チームメイトが処理結果をファイルに書き出す標準手順です。

```yaml
# Step 1: .tmp/ ディレクトリの存在確認（なければ作成）
Bash: mkdir -p .tmp

# Step 2: JSON データを書き出し
Write:
  file_path: ".tmp/<workflow>-<data-name>.json"
  content: |
    {
      "type": "<data_type>",
      "records": [...],
      "metadata": {
        "generated_by": "<worker-name>",
        "timestamp": "<ISO8601>",
        "record_count": <N>,
        "estimated_size_kb": <size>
      }
    }

# Step 3: タスクを完了にマーク
TaskUpdate:
  taskId: "<task-id>"
  status: "completed"

# Step 4: リーダーにメタデータのみを通知
SendMessage:
  type: "message"
  recipient: "<leader-name>"
  content: |
    タスク完了。
    ファイルパス: .tmp/<workflow>-<data-name>.json
    サイズ: <size>KB
    レコード数: <count>
  summary: "タスク完了、データファイル生成済み"
```

### 3.4 データ読み込みパターン（Read）

後続チームメイトがファイルからデータを読み込む標準手順です。

```yaml
# Step 1: ファイルの存在確認
Bash: ls -la .tmp/<workflow>-<data-name>.json

# Step 2: ファイルを読み込み
Read:
  file_path: ".tmp/<workflow>-<data-name>.json"

# Step 3: JSON パース → データ構造検証
#   - 必須フィールドの存在確認
#   - データ型の検証
#   - レコード数の検証

# Step 4: 検証結果をリーダーに報告（統計情報のみ）
SendMessage:
  type: "message"
  recipient: "<leader-name>"
  content: |
    データ検証完了。
    ファイル: .tmp/<workflow>-<data-name>.json
    レコード数: <count>
    検証結果: PASS
  summary: "データ検証完了 PASS"
```

### 3.5 サイズ別の推奨パターン

| データサイズ | 推奨パターン | 備考 |
|------------|------------|------|
| ~1KB | ファイル経由 | 小容量でも一貫性のためファイルを使用 |
| 1KB ~ 50KB | ファイル経由 | 標準パターン |
| 50KB ~ 1MB | ファイル経由（必須） | SendMessage は絶対禁止 |
| 1MB 以上 | ファイル経由 + 分割検討 | Read の行数制限に注意 |

### 3.6 ファイル形式の標準

すべてのデータファイルは JSON 形式で、以下の標準構造を持ちます。

```json
{
  "type": "<data_type>",
  "records": [],
  "metadata": {
    "generated_by": "<worker-name>",
    "timestamp": "<ISO8601>",
    "record_count": 0,
    "status": "success"
  }
}
```

---

## 4. SendMessage の使用規約

### 4.1 基本原則: 通知のみ、データ本体は禁止

SendMessage は軽量なテキストメッセージングツールです。データ本体の送信は禁止し、通知目的のみに使用します。

### 4.2 許可されるメッセージ内容

| 用途 | 含めてよい情報 | 例 |
|------|--------------|-----|
| タスク完了通知 | ファイルパス、サイズ、レコード数 | `"ファイルパス: .tmp/data.json, サイズ: 52KB"` |
| エラー報告 | エラーメッセージ、発生時刻 | `"エラー: データソース接続失敗"` |
| 状態確認応答 | タスクID、状態 | `"task-1 はブロック中です"` |
| スキップ通知 | タスクID、スキップ理由 | `"task-3 はスキップされます（task-1 失敗のため）"` |

### 4.3 禁止されるメッセージ内容

```yaml
# 禁止: データ本体を含む
SendMessage:
  content: |
    タスク完了。
    データ: [{"id": 1, "name": "record_0001", ...}, ...]  # 絶対禁止

# 禁止: 大量の JSON を含む
SendMessage:
  content: |
    結果:
    ```json
    {"records": [...hundreds of records...]}  # 絶対禁止
    ```
```

### 4.4 メッセージタイプ別のテンプレート

#### 完了通知（worker → leader）

```yaml
SendMessage:
  type: "message"
  recipient: "<leader-name>"
  content: |
    task-<N> が完了しました。
    出力ファイル: .tmp/<workflow>-<data-name>.json
    サイズ: <size>KB
    レコード数: <count>
  summary: "task-<N> 完了、出力ファイル生成済み"
```

#### エラー報告（worker → leader）

```yaml
SendMessage:
  type: "message"
  recipient: "<leader-name>"
  content: |
    task-<N> の実行中にエラーが発生しました。
    エラー: <error_message>
    発生時刻: <ISO8601>
  summary: "task-<N> エラー発生"
```

#### スキップ通知（leader → worker）

```yaml
SendMessage:
  type: "message"
  recipient: "<worker-name>"
  content: |
    task-<N> はスキップされます。
    理由: 必須依存先 task-<M> が失敗したため。
  summary: "task-<N> スキップ通知"
```

#### 部分結果モード通知（leader → worker）

```yaml
SendMessage:
  type: "message"
  recipient: "<worker-name>"
  content: |
    task-<M> が失敗しました（任意依存）。
    task-<N> は task-<K> のデータのみで部分結果モードで実行してください。
    primary_data は null として処理してください。
  summary: "部分結果モードで task-<N> を実行"
```

#### シャットダウンリクエスト（leader → worker）

```yaml
SendMessage:
  type: "shutdown_request"
  recipient: "<worker-name>"
  content: "全タスクが完了しました。シャットダウンしてください。"
```

#### シャットダウン応答（worker → leader）

```yaml
SendMessage:
  type: "shutdown_response"
  request_id: "<受信した request_id>"
  approve: true
```

### 4.5 broadcast の使用制限

broadcast は全チームメイトに一斉送信するため、コストが高くなります。以下の場合にのみ使用します。

```yaml
# 許可: 全体に影響するクリティカルな通知
SendMessage:
  type: "broadcast"
  content: "クリティカルエラーが発生しました。全タスクを中断してください。"
  summary: "クリティカルエラー - 全タスク中断"

# 禁止: 特定のチームメイトへの通知
# → type: "message" と recipient を使用すること
```

---

## 5. エラーハンドリングと部分障害リカバリのパターン

### 5.1 エラー検知パターン

リーダーがチームメイトの失敗を検知する標準手順です。

```
worker: タスク実行中にエラー発生
  ↓
worker: SendMessage(content="エラー: <エラーメッセージ>")
  ↓
leader: メッセージ受信 → エラー検知
  ↓
leader: TaskList/TaskGet で該当タスクの状態を確認
  ↓
leader: 失敗を記録、影響範囲を評価
```

**検知のトリガー**:

1. チームメイトからのエラーメッセージ受信（SendMessage 経由）
2. TaskList/TaskGet でタスク状態の確認
3. チームメイトのアイドル/終了通知の監視

### 5.2 失敗タスクのマーキングパターン

Agent Teams には `status: "failed"` が存在しないため、`completed` + description にエラー情報を含める方式を採用します。

#### 失敗タスクのマーク

```yaml
TaskUpdate:
  taskId: "<failed-task-id>"
  status: "completed"
  description: |
    [FAILED] <元のタスク説明>
    エラー: <エラーメッセージ>
    発生時刻: <ISO8601>
    影響: <影響を受けるタスク一覧>
```

#### スキップタスクのマーク

```yaml
TaskUpdate:
  taskId: "<skipped-task-id>"
  status: "completed"
  description: |
    [SKIPPED] <元のタスク説明>
    理由: 必須依存先 task-<N> が失敗
    スキップ時刻: <ISO8601>
```

**識別方法**: description の先頭プレフィックスで状態を判定

| プレフィックス | 意味 |
|--------------|------|
| （なし） | 正常完了 |
| `[FAILED]` | 失敗完了 |
| `[SKIPPED]` | スキップ |

### 5.3 必須依存 vs 任意依存の判定

依存関係には「必須依存」と「任意依存」の2種類があります。Agent Teams の `addBlockedBy` は必須依存のみを登録し、任意依存はリーダーが手動で制御します。

#### 依存関係マトリックス

リーダーは計画時に以下の依存関係マトリックスを定義・保持します。

```yaml
dependency_matrix:
  task-3:
    task-1: required   # task-1 が失敗 → task-3 はスキップ
  task-4:
    task-1: optional   # task-1 が失敗 → task-4 は部分結果で続行
    task-2: required   # task-2 が失敗 → task-4 はスキップ
```

#### addBlockedBy の設定ルール

```yaml
# 必須依存のみ addBlockedBy に登録
TaskUpdate:
  taskId: "<task-3-id>"
  addBlockedBy: ["<task-1-id>"]   # task-1 は必須

# 任意依存は addBlockedBy に含めない
TaskUpdate:
  taskId: "<task-4-id>"
  addBlockedBy: ["<task-2-id>"]   # task-2 のみ必須
# 注意: task-1（任意依存）は addBlockedBy に含めない
# → task-1 が失敗してもブロックされない
```

#### 失敗時の評価ロジック

```python
# リーダーの評価アルゴリズム（疑似コード）
for pending_task in pending_tasks:
    for dependency in dependency_matrix[pending_task]:
        if dependency.status == "FAILED":
            if dependency.type == "required":
                # 必須依存が失敗 → タスクをスキップ
                mark_as_skipped(pending_task, reason=f"必須依存先 {dependency.id} が失敗")
                notify_worker(pending_task.owner, "スキップ通知")
            elif dependency.type == "optional":
                # 任意依存が失敗 → 部分結果モードで続行
                notify_worker(pending_task.owner, "部分結果モードで実行")
```

### 5.4 部分結果の保存と再実行スキップ

#### 保存パターン

成功したタスクの出力ファイルは `.tmp/` に保持し、失敗・スキップされたタスクの出力は存在しません。

```yaml
実行結果:
  成功タスクの出力:
    - .tmp/<workflow>-backup.json    # task-2 の出力（保持）
    - .tmp/<workflow>-summary.json   # task-4 の出力（保持、partial_result: true）
  失敗タスク:
    - task-1: 出力なし（失敗）
  スキップタスク:
    - task-3: 出力なし（スキップ）
```

#### 部分結果フラグ

任意依存が失敗した場合、出力に `partial_result: true` フラグを含めます。

```json
{
  "type": "summary",
  "sources": {
    "primary_data": null,
    "backup_data": {"type": "backup_data", "records": [...]}
  },
  "partial_result": true,
  "metadata": {
    "generated_by": "worker-c",
    "timestamp": "2026-02-08T12:00:00+09:00",
    "missing_sources": ["primary_data"],
    "available_sources": ["backup_data"]
  }
}
```

#### 再実行時のスキップ判定

```yaml
再実行スキップロジック:
  1. .tmp/ 内の出力ファイル一覧を取得
  2. 各ファイルが有効な JSON であることを確認
  3. ファイルに対応するタスクを特定
  4. 該当タスクをスキップ候補としてマーク

  スキップ条件:
    - ファイルが存在する
    - かつ有効な JSON である
    - かつタスクの description と一致する

  再実行条件:
    - ファイルが存在しない
    - またはファイルが無効な JSON
```

### 5.5 依存関係の手動解除

失敗したタスクを `completed` にマークすることで、blockedBy からの自動除外を利用して依存関係を解除します。

```
task-1 が失敗
  ↓
leader: task-1 を completed にマーク（description に [FAILED] + エラー情報）
  ↓
task-3 の blockedBy から task-1 が自動除外 → task-3 がアンブロック
  ↓
leader: task-3 を即座に completed にマーク（[SKIPPED] + 理由を記載）
  ↓
worker-b にスキップ通知を送信
```

### 5.6 エラーハンドリングのチェックリスト

リーダーがエラー発生時に実行するチェックリストです。

- [ ] チームメイトからのエラーメッセージを受信したか
- [ ] TaskList/TaskGet で失敗タスクの状態を確認したか
- [ ] 失敗タスクを `[FAILED]` プレフィックス付きで completed にマークしたか
- [ ] 依存関係マトリックスを参照し、影響範囲を評価したか
- [ ] 必須依存タスクを `[SKIPPED]` としてマークしたか
- [ ] 任意依存タスクのワーカーに部分結果モードを通知したか
- [ ] 影響を受けるワーカーにスキップまたは部分結果モードを通知したか
- [ ] 成功タスクの出力ファイルが保持されていることを確認したか

---

## 6. チームメイトのライフサイクル管理

### 6.1 ライフサイクル全体像

```
起動 → タスク確認 → タスク実行 → 完了報告 → アイドル → [追加タスク | シャットダウン]
```

```
リーダー                          チームメイト
  │                                │
  ├── Task(subagent_type, ...)──→ 起動
  │                                │
  ├── TaskUpdate(owner)           タスク確認（TaskList）
  │                                │
  │                               タスク実行
  │                                │
  │  ←── SendMessage(完了通知) ── 完了報告
  │                                │
  │                               アイドル（自動）
  │                                │
  │  ←── アイドル通知（自動）       │
  │                                │
  ├── SendMessage(shutdown_req) ──→ │
  │                                │
  │  ←── shutdown_response ────── 終了
  │
  ├── TeamDelete
```

### 6.2 アイドル状態の理解

チームメイトは毎ターン終了後にアイドル状態になります。これは正常な動作です。

**重要なルール**:

- アイドル = エラーではない
- アイドル通知は自動送信される
- アイドル状態のチームメイトにメッセージを送ると復帰する
- アイドル通知に対して即座にリアクションする必要はない

```yaml
# チームメイトからのメッセージ受信 → アイドル通知、のフロー
worker-a: SendMessage("task-1 完了")
  ↓ 自動
worker-a: アイドル通知がリーダーに配信
  ↓
leader: メッセージの内容に基づいてアクション（アイドルは無視してよい）
```

### 6.3 シャットダウンフロー

全タスク完了後、チームメイトを順番にシャットダウンします。

```yaml
# Step 1: 全タスク完了を確認
TaskList: {}
# → 全タスクが completed であることを確認

# Step 2: 各チームメイトにシャットダウンリクエスト
SendMessage:
  type: "shutdown_request"
  recipient: "worker-a"
  content: "全タスクが完了しました。シャットダウンしてください。"

# Step 3: シャットダウン応答を待つ
# チームメイトから shutdown_response(approve: true) が返される

# Step 4: 全チームメイトのシャットダウン完了後、チームを削除
TeamDelete: {}
```

### 6.4 シャットダウンリクエストの応答

チームメイトはシャットダウンリクエストを受信したら、必ず応答する必要があります。

```yaml
# 承認（通常のケース）
SendMessage:
  type: "shutdown_response"
  request_id: "<受信した request_id>"
  approve: true

# 拒否（実行中のタスクがある場合）
SendMessage:
  type: "shutdown_response"
  request_id: "<受信した request_id>"
  approve: false
  content: "task-3 を実行中のため、完了後にシャットダウンします"
```

### 6.5 クリーンアップ

チーム削除後、一時ファイルをクリーンアップします。

```yaml
# チーム削除
TeamDelete: {}

# 一時ファイルのクリーンアップ
Bash: rm -f .tmp/<workflow>-*.json
```

### 6.6 異常時のリカバリ

| 異常状態 | 検知方法 | 対処 |
|---------|---------|------|
| チームメイト無応答 | タスクが in_progress のまま応答なし | タイムアウトとみなし、リーダーが手動でタスクを失敗マーク |
| シャットダウン拒否 | shutdown_response(approve: false) | タスク完了を待ってから再送（最大3回） |
| チームメイトクラッシュ | 予期しない終了通知 | リーダーが手動でタスクを失敗マーク、影響範囲を評価 |
| チーム作成失敗 | TeamCreate エラー | 同名チームの存在確認、TeamDelete 後にリトライ |

---

## 付録

### A. 検証結果サマリーの標準テンプレート

リーダーはワークフロー完了時に検証結果サマリーを出力します。

```yaml
<workflow>_verification:
  team_name: "<team-name>"
  execution_time: "<duration>"
  status: "success" | "partial_failure" | "failure"

  verifications:
    <check_name>:
      status: "PASS" | "FAIL"
      detail: "<検証結果の説明>"

  summary:
    total_checks: <N>
    passed: <count>
    failed: <count>
    skipped: <count>

  task_results:
    task_<N>:
      status: "SUCCESS" | "FAILED" | "SKIPPED" | "SUCCESS (partial)"
      owner: "<worker-name>"
      output: "<file-path>"  # 成功時のみ
      error: "<error-msg>"   # 失敗時のみ
      reason: "<skip-reason>" # スキップ時のみ
```

### B. 関連ドキュメント

| ドキュメント | パス | 説明 |
|------------|------|------|
| サブエージェントデータ渡しルール | `.claude/rules/subagent-data-passing.md` | サブエージェントへのデータ受け渡しの基本ルール |
| プロトタイプスキル | `.claude/skills/agent-teams-prototype/SKILL.md` | task-1: 基本パターンの検証スキル |
| ファイルベースデータ受け渡しスキル | `.claude/skills/agent-teams-file-passing/SKILL.md` | task-2: データ受け渡しの検証スキル |
| エラーハンドリングスキル | `.claude/skills/agent-teams-error-handling/SKILL.md` | task-3: エラーハンドリングの検証スキル |

### C. 関連 Issue

| Issue | タイトル | 状態 |
|-------|---------|------|
| #3233 | [Wave1] Agent Teams 共通実装パターンのプロトタイプ作成 | task-1 |
| #3234 | [Wave1] ファイルベースデータ受け渡しパターンの検証 | task-2 |
| #3235 | [Wave1] エラーハンドリング・部分障害パターンの確立 | task-3 |
| #3236 | [Wave1] Agent Teams 共通実装パターンドキュメントの作成 | 本ドキュメント |
