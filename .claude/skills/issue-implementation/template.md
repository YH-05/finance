# Issue Implementation Templates

Issue 実装時のレポートテンプレート集です。

## 1. 開始レポート

```markdown
======================================================================
                /issue-implement #{number} 開始
======================================================================

## Issue 情報
- タイトル: {title}
- ラベル: {labels}
- URL: {url}

## 開発タイプ
{development_type} → {workflow_description}

## チェックリスト
- [ ] {task1}
- [ ] {task2}
- [ ] {task3}

## 対象（Python の場合）
- パッケージ: {library_name}
- コード: src/{library_name}/core/
- テスト: tests/{library_name}/unit/

## 対象（Agent/Command/Skill の場合）
- 配置先: .claude/{type}s/{name}.md

Phase 0: 検証・準備・タイプ判定 ✓ 完了
```

## 2. 完了レポート（成功）

```markdown
======================================================================
	            /issue-implement #{number} 完了
======================================================================

## サマリー
- Issue: #{number} - {title}
- 実行時間: {duration}
- 作成したPR: #{pr_number}

## Phase 結果

| Phase | 状態 | 詳細 |
|-------|------|------|
| 0. 検証・準備 | ✓ | Issue情報取得済み |
| 1. テスト作成 | ✓ | {test_count} tests |
| 2. 実装 | ✓ | {task_count}/{task_count} tasks |
| 3. 品質保証 | ✓ | make check-all PASS |
| 4. PR作成 | ✓ | #{pr_number} |
| 5. 完了処理 | ✓ | Project: In Progress |

## 作成したファイル
- tests/{library_name}/unit/test_{feature}.py
- src/{library_name}/core/{feature}.py

## 次のステップ

1. PRをレビュー:
   gh pr view {pr_number} --web

2. PRをマージ:
   /merge-pr {pr_number}

3. クリーンアップ（マージ後）:
   /worktree-done feature/issue-{number}-{slug}

======================================================================
```

## 3. 完了レポート（Agent/Command/Skill）

```markdown
======================================================================
	            /issue-implement #{number} 完了
======================================================================

## サマリー
- Issue: #{number} - {title}
- 開発タイプ: {type}
- 作成したPR: #{pr_number}

## Phase 結果

| Phase | 状態 | 詳細 |
|-------|------|------|
| 0. 検証・タイプ判定 | ✓ | {type} と判定 |
| 1. 要件分析 | ✓ | 名前: {name} |
| 2. 設計・作成 | ✓ | ファイル作成完了 |
| 3. 検証 | ✓ | 全チェックパス |
| 4. PR作成 | ✓ | #{pr_number} |

## 作成したファイル
- .claude/{type}s/{name}.md

## 次のステップ

1. PRをレビュー:
   gh pr view {pr_number} --web

2. PRをマージ:
   /merge-pr {pr_number}

======================================================================
```

## 4. エラーレポート

```markdown
======================================================================
                /issue-implement #{number} エラー
======================================================================

## エラー発生 Phase
Phase {n}: {phase_name}

## エラー内容
- 種類: {error_type}
- 詳細: {error_detail}

## 実行された処理
- Phase 0: 検証・準備 ✓
- Phase 1: テスト作成 ✓
- Phase 2: 実装 ✗ ({completed}/{total} tasks)
- Phase 3: 品質保証 - (未実行)
- Phase 4: PR作成 - (未実行)
- Phase 5: 完了処理 - (未実行)

## 推奨アクション
1. {action1}
2. {action2}

======================================================================
```

## 5. Phase別詳細テンプレート

### Phase 1 完了

```markdown
## Phase 1: テスト作成 完了

### 作成したテスト
- `tests/{library_name}/unit/test_{feature}.py`

### テストケース一覧
- test_正常系_{case1}
- test_正常系_{case2}
- test_異常系_{case3}

### テスト実行結果
`make test` → Red (失敗) ✓

受け入れ条件に対応するテストを作成しました。
Phase 2 で実装を進めます。
```

### Phase 2 完了

```markdown
## Phase 2: 実装 完了

### 実装したファイル
- `src/{library_name}/core/{feature}.py`

### 完了したタスク
- [x] {task1}
- [x] {task2}
- [x] {task3}

### テスト実行結果
`make test` → Green (成功) ✓

Issue のチェックボックスを更新しました。
Phase 3 で品質チェックを実行します。
```

### Phase 3 完了

```markdown
## Phase 3: 品質保証 完了

### 実行結果
| チェック | 結果 |
|----------|------|
| make format | ✓ |
| make lint | ✓ |
| make typecheck | ✓ |
| make test | ✓ |
| make check-all | ✓ |

### 自動修正
- {n} 件のフォーマット修正
- {n} 件の型アノテーション追加

Phase 4 で PR を作成します。
```

### Phase 4 完了

```markdown
## Phase 4: PR作成 完了

### PR情報
- PR: #{pr_number}
- ブランチ: feature/issue-{number}-{slug}
- URL: {pr_url}

### CI結果
| Check | 結果 |
|-------|------|
| format | ✓ |
| lint | ✓ |
| typecheck | ✓ |
| test | ✓ |

Phase 5 で完了処理を実行します。
```

## 6. ワークフロー選択表示

```markdown
## 開発タイプ判定

### 判定根拠
- ラベル: {labels}
- キーワード: {detected_keywords}

### 判定結果
**{development_type}** ワークフローを選択

### ワークフロー概要
{workflow_description}

1. {step1}
2. {step2}
3. {step3}
4. {step4}
```
