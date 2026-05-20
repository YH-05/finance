# 議論メモ: PostToolUse hook ブロッキングエラー原因特定と修正

**日付**: 2026-05-18
**議論ID**: disc-2026-05-18-claude-hook-bugfix
**前関連**: disc-2026-05-18-an-fm-pipeline-separation（同日の議論セッション中に発覚）
**ステータス**: 決着

## 背景

/project-discuss スキルで AN/FM 分離方針を Neo4j + docs/plan + memory に保存している最中、Write/Edit ごとに以下の system-reminder が連発した:

```
PostToolUse:Edit hook blocking error from command:
"python3 .claude/skills/sync-claude-config/sync.py --auto 2>/dev/null":
[python3 .claude/skills/sync-claude-config/sync.py --auto 2>/dev/null]: No stderr output
```

stderr が `2>/dev/null` で握り潰されており、診断情報が皆無。ファイル更新自体は成功していたため機能上の支障はなかったが、UI ノイズと潜在的な sync 失敗のリスクがあり原因究明と修正を実施した。

## 議論の経緯

### 1. hook 設定の特定

`.claude/settings.json:165-173` の PostToolUse(Write|Edit) hook:

```json
{
  "matcher": "Write|Edit",
  "hooks": [{
    "type": "command",
    "command": "python3 .claude/skills/sync-claude-config/sync.py --auto 2>/dev/null"
  }]
}
```

### 2. スクリプト本体の挙動確認

`.claude/skills/sync-claude-config/sync.py` の `--auto` モード (`run_auto()`) は `contextlib.suppress(Exception)` で全例外を握り潰しており、起動さえできれば exit 0。つまり問題はスクリプト内部ではなく、起動段階にあると判明。

### 3. cwd 依存の再現

| cwd | 結果 |
|-----|------|
| `/Users/yukihata/Desktop/quants` (project root) | exit 0、正常 |
| `/tmp` (絶対パスでスクリプト指定) | exit 0、正常 |
| `/Users/yukihata` (ホーム、相対パス) | **exit 2** `can't open file '/Users/yukihata/.claude/skills/sync-claude-config/sync.py'` |
| `/` (ルート、相対パス) | **exit 2** `can't open file '//.claude/...'` |

### 4. 根本原因の特定

- **相対パス問題**: hook が `.claude/skills/...` を相対参照しているため、cwd 次第で Python インタプリタが「ファイル発見不能」で exit 2 終了する（スクリプト本体は起動すらしない）
- **cwd 切り替わり**: 編集対象が `~/.claude/projects/.../memory/` のようなプロジェクト外パスのとき、Claude Code は hook の cwd を編集対象付近に切り替える（と推定）。結果 `.claude/...` の解決が失敗
- **診断隠蔽**: `2>/dev/null` で stderr が握り潰され、Claude Code 側に「No stderr output」とだけ残る
- **exit 非ゼロ問題**: Python が exit 2 で終了すると Claude Code は PostToolUse hook を blocking error として扱い system-reminder を出す

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-18-003 | `.claude/settings.json` の PostToolUse(Write\|Edit) hook command を `python3 "$CLAUDE_PROJECT_DIR/.claude/skills/sync-claude-config/sync.py" --auto 2>/dev/null \|\| true` に変更。`$CLAUDE_PROJECT_DIR` は Claude Code が hook 実行時に渡す絶対パス環境変数、`\|\| true` は sync が best-effort 失敗しても UI をブロックしないため。 | 4 cwd パターン全てで exit 0 を確認済。 |

## 適用済み修正

`.claude/settings.json:170` のdiff:

```diff
- "command": "python3 .claude/skills/sync-claude-config/sync.py --auto 2>/dev/null"
+ "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/skills/sync-claude-config/sync.py\" --auto 2>/dev/null || true"
```

検証コマンド:
```bash
# 全 cwd で exit 0
CLAUDE_PROJECT_DIR=/Users/yukihata/Desktop/quants bash -c 'python3 "$CLAUDE_PROJECT_DIR/.claude/skills/sync-claude-config/sync.py" --auto 2>/dev/null || true'
```

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-05-18-006 | `/sync-claude-config` を手動実行し他プロジェクトとの差分を確認。過去 hook がサイレント失敗していた可能性があるため | 中 | 未着手 |
| act-2026-05-18-007 | note-finance や他リポジトリの `.claude/settings.json` で同種の相対パス hook が使われていないか調査・修正 | 低 | 未着手 |

## 教訓（feedback memory に保存）

1. **hook コマンドは絶対パス必須**: `$CLAUDE_PROJECT_DIR` を使う。相対パスは編集対象がプロジェクト外のとき cwd 切り替わりで破綻
2. **best-effort hook は `|| true` で締める**: sync・通知・ログのような非クリティカル処理は exit 非ゼロを返してはいけない。Claude Code が blocking error 扱いする
3. **stderr を `/dev/null` で完全には握り潰さない**: トラブル時のために `2>>$LOG_FILE` 等で残しておく方が安全

## 次回の議論トピック

- act-2026-05-18-006 (他プロジェクト sync 差分確認) を実行し未sync状態を解消
- 他の hook (PermissionRequest 等) で同種の相対パス問題がないかレビュー
