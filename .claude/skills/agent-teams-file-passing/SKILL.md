---
name: agent-teams-file-passing
description: Agent Teams でのファイルベースデータ受け渡しパターンを検証するスキル。SendMessage はテキストベースのため、50KB超のデータはファイル経由で受け渡す必要があることを実証する。
---

# Agent Teams ファイルベースデータ受け渡しパターン

Agent Teams において、チームメイト間で大容量データ（50KB以上）をファイル経由で受け渡すパターンを検証するスキルです。

## 背景と目的

### なぜファイルベースが必要か

SendMessage はテキストベースのメッセージングツールです。以下の制約があります：

- **テキストサイズ制限**: 大量データ（50KB超）を SendMessage に含めると、メッセージが肥大化しパフォーマンスに影響する
- **構造化データの劣化**: JSON データを文字列としてメッセージに含めると、パース時のエラーリスクが高まる
- **再利用不可**: メッセージに含めたデータは永続化されず、再参照できない

### ファイルベースパターンのメリット

- **サイズ制限なし**: 50KB, 100KB, 1MB 以上のデータも問題なく受け渡し可能
- **構造保持**: JSON ファイルとして書き出すため、データ構造が正確に保持される
- **再利用性**: ファイルとして永続化されるため、複数チームメイトから参照可能
- **トレーサビリティ**: ファイルパスによるデータの追跡が容易

## いつ使用するか

### 明示的な使用（ユーザー要求）

- 「ファイルベースデータ受け渡しを検証して」という要求
- Agent Teams のデータ受け渡しパターンを確認したい場合
- 大容量 JSON データのチームメイト間受け渡しを検証する場合

## 前提条件

以下のエージェント定義が存在すること：

| エージェント | パス | 役割 |
|-------------|------|------|
| file-passing-team-lead | `.claude/agents/file-passing-team-lead.md` | リーダー（タスク管理・検証監視） |
| file-passing-worker-a | `.claude/agents/file-passing-worker-a.md` | ワーカーA（データ生成） |
| file-passing-worker-b | `.claude/agents/file-passing-worker-b.md` | ワーカーB（データ検証） |

## 実行手順

### Phase 1: チーム作成

```yaml
TeamCreate:
  team_name: "file-passing-team"
  description: "ファイルベースデータ受け渡しパターンの検証チーム"
```

**確認**: `~/.claude/teams/file-passing-team/` ディレクトリが作成されたこと。

### Phase 2: タスク登録と依存関係の設定

3つのタスクを登録し、依存関係を設定します。

#### タスク1: 小容量テストデータの生成（独立タスク）

```yaml
TaskCreate:
  subject: "小容量テストデータの生成（~1KB）"
  description: |
    .tmp/file-passing-small.json に小容量のテストデータを生成する。
    データ構造:
    {
      "type": "small_test",
      "records": [{"id": 1, "name": "test_record", "value": 100}],
      "metadata": {"generated_by": "file-passing-worker-a", "timestamp": "<ISO8601>"}
    }
    目標サイズ: 約1KB
  activeForm: "小容量テストデータを生成中"
```

#### タスク2: 大容量テストデータの生成（独立タスク）

```yaml
TaskCreate:
  subject: "大容量テストデータの生成（50KB以上）"
  description: |
    .tmp/file-passing-large.json に大容量のテストデータを生成する。
    データ構造:
    {
      "type": "large_test",
      "records": [
        {"id": 1, "name": "record_0001", "value": <random>, "category": "...", "description": "...", "tags": [...], "metadata": {...}},
        ...（500件以上のレコード）
      ],
      "metadata": {"generated_by": "file-passing-worker-a", "timestamp": "<ISO8601>", "record_count": <N>, "estimated_size_kb": <size>}
    }
    目標サイズ: 50KB以上
  activeForm: "大容量テストデータを生成中"
```

#### タスク3: テストデータの検証（依存タスク）

```yaml
TaskCreate:
  subject: "テストデータの読み込みと検証"
  description: |
    worker-a が生成した2つのテストデータファイルを読み込み、以下を検証する。

    検証対象:
    1. .tmp/file-passing-small.json
       - ファイル存在確認
       - 有効な JSON であること
       - type が "small_test" であること
       - records 配列が存在すること

    2. .tmp/file-passing-large.json
       - ファイル存在確認
       - 有効な JSON であること
       - type が "large_test" であること
       - records 配列が500件以上であること
       - ファイルサイズが50KB以上であること

    結果報告: 統計情報のみ（ファイル数、合計サイズ、レコード数）をSendMessageで報告。データ本体は含めない。
  activeForm: "テストデータを読み込み検証中"
```

#### 依存関係の設定

```yaml
TaskUpdate:
  taskId: "<task-3-id>"
  addBlockedBy: ["<task-1-id>", "<task-2-id>"]
```

**確認**: TaskList で task-3 の blockedBy に task-1 と task-2 の ID が含まれていること。

### Phase 3: チームメイトの起動とタスク割り当て

```yaml
# worker-a（データ生成担当）
Task:
  subagent_type: "file-passing-worker-a"
  team_name: "file-passing-team"
  name: "worker-a"
  prompt: |
    あなたは file-passing-team の worker-a です。
    TaskList でタスクを確認し、あなたに割り当てられたタスクを実行してください。

    ## 担当タスク
    1. .tmp/file-passing-small.json の生成（~1KB）
    2. .tmp/file-passing-large.json の生成（50KB以上）

    ## 重要ルール
    - SendMessage にはファイルパスとメタデータのみを含めること
    - データ本体は絶対に SendMessage に含めない

# worker-b（データ検証担当）
Task:
  subagent_type: "file-passing-worker-b"
  team_name: "file-passing-team"
  name: "worker-b"
  prompt: |
    あなたは file-passing-team の worker-b です。
    TaskList でタスクを確認してください。
    タスクがブロック中の場合は、ブロック解除を待ってから実行してください。

    ## 担当タスク
    テストデータの読み込みと検証

    ## 入力ファイル
    1. .tmp/file-passing-small.json
    2. .tmp/file-passing-large.json

    ## 重要ルール
    - SendMessage には統計情報のみを含めること（ファイル数、サイズ、レコード数）
    - データ本体は絶対に SendMessage に含めない
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
```

### Phase 4: 実行監視と検証

チームメイトからのメッセージを受信しながら、以下を監視します。

1. **worker-a のタスク完了**: task-1 と task-2 が completed になること
2. **依存関係の解除**: task-3 の blockedBy が空になること
3. **worker-b の検証実行**: task-3 が in_progress → completed になること
4. **SendMessage の制約遵守**: メッセージにデータ本体が含まれていないこと

**重要**: チームメイトからのメッセージは自動的に配信されます。

### Phase 5: シャットダウンとクリーンアップ

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

# 一時ファイルのクリーンアップ（skip_cleanup でなければ）
Bash: rm -f .tmp/file-passing-small.json .tmp/file-passing-large.json
```

### Phase 6: 検証結果のサマリー出力

全 Phase の結果をまとめて出力します（出力フォーマットセクション参照）。

## 検証パターンの詳細

### パターン1: 小容量 JSON ファイルの受け渡し（~1KB）

```
worker-a: Write(.tmp/file-passing-small.json)
  ↓
worker-a: TaskUpdate(status=completed)
  ↓
worker-a: SendMessage(content="ファイルパス: .tmp/file-passing-small.json, サイズ: ~1KB")
  ↓
worker-b: Read(.tmp/file-passing-small.json)
  ↓
worker-b: JSON パース → 構造検証 → PASS/FAIL
```

**検証項目**:
- ファイルが正常に作成される
- Read で正常に読み込める
- JSON として正しくパースできる
- 期待するフィールドが存在する

### パターン2: 大容量 JSON ファイルの受け渡し（50KB以上）

```
worker-a: Write(.tmp/file-passing-large.json)  ← 500件以上のレコード
  ↓
worker-a: TaskUpdate(status=completed)
  ↓
worker-a: SendMessage(content="ファイルパス: .tmp/file-passing-large.json, サイズ: XXkB, レコード数: N")
  ↓
worker-b: Read(.tmp/file-passing-large.json)
  ↓
worker-b: JSON パース → サイズ検証（50KB以上）→ レコード数検証（500以上）→ PASS/FAIL
```

**検証項目**:
- 50KB 以上のファイルが正常に作成される
- Read で正常に読み込める（大容量でもエラーなし）
- JSON として正しくパースできる
- レコード数が期待値以上である
- ファイルサイズが 50KB 以上である

### パターン3: SendMessage メタデータのみ制約

```
# 正しいパターン（メタデータのみ）
SendMessage:
  content: |
    タスク完了。
    ファイルパス: .tmp/file-passing-large.json
    サイズ: 52KB
    レコード数: 500

# 禁止パターン（データ本体を含む）
SendMessage:
  content: |
    タスク完了。
    データ: [{"id": 1, "name": "record_0001", ...}, ...]  ← 絶対禁止
```

**検証項目**:
- worker-a の SendMessage にデータ本体が含まれていない
- worker-b の SendMessage にデータ本体が含まれていない
- ファイルパスとメタデータ（サイズ、レコード数）のみが送信される

### パターン4: ファイル存在確認パターン

```
worker-b: ファイル存在確認
  ├── 存在する → 読み込み開始
  └── 存在しない → エラー報告
```

**検証項目**:
- ファイルが存在する場合は正常に読み込み・検証が行われる
- ファイルが存在しない場合は適切なエラーがリーダーに報告される

## エラーハンドリング

### エラーパターン1: ファイル未生成（File Not Found）

**原因**: worker-a がファイル生成に失敗した、またはパスが間違っている

**対処法**:
1. worker-a のタスク完了状態を確認
2. SendMessage で報告されたファイルパスを確認
3. worker-a にファイルパスの確認を依頼

### エラーパターン2: 無効な JSON

**原因**: ファイルの内容が正しい JSON 形式でない

**対処法**:
1. ファイルの先頭・末尾を Read で確認
2. JSON パースエラーの詳細を記録
3. worker-a にファイル再生成を依頼

### エラーパターン3: サイズ不足

**原因**: 大容量ファイルが 50KB 未満

**対処法**:
1. 実際のファイルサイズを確認（`wc -c` で測定）
2. レコード数を確認
3. worker-a にレコード数を増やして再生成を依頼

### エラーパターン4: SendMessage にデータ本体が含まれる

**原因**: worker がルールを無視してデータ本体を SendMessage に含めた

**対処法**:
1. メッセージ内容を確認
2. 該当 worker に警告を送信
3. ファイルベースパターンでの再送を依頼

## 出力フォーマット

```yaml
file_passing_verification:
  team_name: "file-passing-team"
  execution_time: "{duration}"
  status: "success" | "partial_failure" | "failure"

  verifications:
    small_file_write:
      status: "PASS" | "FAIL"
      detail: ".tmp/file-passing-small.json が正常に生成された"
      file_size_bytes: {size}

    large_file_write:
      status: "PASS" | "FAIL"
      detail: ".tmp/file-passing-large.json が正常に生成された（50KB以上）"
      file_size_bytes: {size}
      record_count: {count}

    small_file_read:
      status: "PASS" | "FAIL"
      detail: "小容量ファイルの読み込みと JSON パースが正常に完了"

    large_file_read:
      status: "PASS" | "FAIL"
      detail: "大容量ファイルの読み込みと JSON パースが正常に完了"

    structure_validation:
      status: "PASS" | "FAIL"
      detail: "両ファイルのデータ構造が期待通り"
      small_fields: ["type", "records", "metadata"]
      large_fields: ["type", "records", "metadata"]

    size_validation:
      status: "PASS" | "FAIL"
      detail: "ファイルサイズが基準を満たしている"
      small_size_kb: {size}
      large_size_kb: {size}
      large_exceeds_50kb: true | false

    sendmessage_constraint:
      status: "PASS" | "FAIL"
      detail: "SendMessage にデータ本体が含まれていない"

    dependency_resolution:
      status: "PASS" | "FAIL"
      detail: "task-1/task-2 完了後に task-3 が自動アンブロックされた"

    shutdown:
      status: "PASS" | "FAIL"
      detail: "全チームメイトが正常にシャットダウン"

  summary:
    total_checks: 9
    passed: {count}
    failed: {count}
    skipped: {count}

  file_stats:
    small_file:
      path: ".tmp/file-passing-small.json"
      size_bytes: {size}
      record_count: {count}
    large_file:
      path: ".tmp/file-passing-large.json"
      size_bytes: {size}
      record_count: {count}
```

## 完了条件

- [ ] TeamCreate でチームが正常に作成された
- [ ] TaskCreate で3タスクが登録された
- [ ] addBlockedBy で依存関係が正しく設定された（task-3 が task-1, task-2 にブロック）
- [ ] worker-a が小容量テストデータ（~1KB）を正常に生成した
- [ ] worker-a が大容量テストデータ（50KB以上）を正常に生成した
- [ ] worker-a の SendMessage にデータ本体が含まれていない
- [ ] task-1, task-2 完了後に task-3 のブロックが自動解除された
- [ ] worker-b が両ファイルを Read で正常に読み込み検証した
- [ ] worker-b の SendMessage に統計情報のみが含まれている（データ本体なし）
- [ ] 全チームメイトが正常にシャットダウンした
- [ ] 検証結果サマリーが出力された

## 関連

- **エージェント**: `.claude/agents/file-passing-team-lead.md`
- **エージェント**: `.claude/agents/file-passing-worker-a.md`
- **エージェント**: `.claude/agents/file-passing-worker-b.md`
- **ルール**: `.claude/rules/subagent-data-passing.md`
- **Issue #3233**: Agent Teams 共通実装パターンのプロトタイプ作成
- **Issue #3234**: ファイルベースデータ受け渡しパターンの検証
- **Issue #3235**: エラーハンドリング・部分障害パターンの確立
- **Issue #3236**: Agent Teams 共通実装パターンドキュメントの作成
