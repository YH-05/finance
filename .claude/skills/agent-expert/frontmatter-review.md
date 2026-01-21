# エージェントフロントマターレビューガイド

このドキュメントは、エージェントファイル（`.claude/agents/*.md`）のフロントマターを検証するためのガイドです。

## 検証対象フィールド

エージェントのフロントマターは以下のフィールドで構成されます：

```yaml
---
name: string          # 必須: エージェント名（kebab-case）
description: string   # 必須: Task tool に表示される説明
category: string      # オプション: エージェントのカテゴリ
skills: string[]      # オプション: 参照するスキルのリスト
allowed-tools: string # オプション: 使用可能なツールのリスト
model: string         # オプション: inherit | sonnet | haiku | opus
color: string         # オプション: 表示色
---
```

## フィールド別検証ルール

### 1. `name` フィールド（必須）

**検証項目**:

| チェック項目 | ルール | 例 |
|-------------|--------|-----|
| 必須 | 空でないこと | ✅ `debugger` |
| 形式 | kebab-case | ✅ `quality-checker` ❌ `qualityChecker` |
| ファイル名一致 | `{name}.md` と一致 | `debugger.md` → `name: debugger` |
| 一意性 | 他のエージェントと重複しない | - |

**検証方法**:

```bash
# ファイル名とnameの一致を確認
filename=$(basename "$file" .md)
name=$(grep '^name:' "$file" | sed 's/name: //')
if [ "$filename" != "$name" ]; then
    echo "WARN: ファイル名 ($filename) と name ($name) が不一致"
fi
```

### 2. `description` フィールド（必須）

**検証項目**:

| チェック項目 | ルール | 推奨 |
|-------------|--------|------|
| 必須 | 空でないこと | - |
| 長さ | 1-2文（50-200文字推奨） | 簡潔かつ明確 |
| トリガーキーワード | 使用タイミングを示すキーワードを含む | `〜を実行する` `〜の場合に使用` |
| 具体性 | 何をするエージェントか明確 | ❌ `コードをチェックする` ✅ `コード品質の検証・自動修正を行う` |

**良い例**:
```yaml
description: コード品質の検証・自動修正を行う統合サブエージェント。モードに応じて検証のみ、自動修正、クイックチェックを実行。
```

**悪い例**:
```yaml
description: コードをチェック  # 曖昧すぎる
```

### 3. `category` フィールド（オプション）

**検証項目**:

| チェック項目 | ルール | 例 |
|-------------|--------|-----|
| 形式 | kebab-case または snake_case | `specialized-domains`, `market_report` |
| 既存カテゴリ | 可能な限り既存のものを使用 | - |

**既存カテゴリ一覧**:
- `specialized-domains`: 汎用的な専門タスク
- `market_report`: 市場レポート記事
- `stock_analysis`: 個別銘柄分析
- `economic_indicators`: 経済指標解説
- `investment_education`: 投資教育
- `quant_analysis`: クオンツ分析

**検証方法**:

```bash
# 既存カテゴリの確認
grep -h '^category:' .claude/agents/*.md | sort | uniq
```

### 4. `skills` フィールド（オプション）

**検証項目**:

| チェック項目 | ルール | 例 |
|-------------|--------|-----|
| 形式 | YAML配列 | `skills: [skill-name-1, skill-name-2]` |
| 存在確認 | `.claude/skills/{skill-name}/SKILL.md` が存在すること | - |
| 命名規則 | kebab-case | `agent-expert`, `deep-research` |

**検証方法**:

```bash
# skills フィールドの参照先が存在するか確認
skills=$(grep '^skills:' "$file" | sed 's/skills: \[//' | sed 's/\]//' | tr ',' '\n')
for skill in $skills; do
    skill=$(echo "$skill" | tr -d ' "')
    if [ ! -f ".claude/skills/$skill/SKILL.md" ]; then
        echo "ERROR: skill '$skill' が存在しません"
    fi
done
```

**有効なスキル一覧**:

```bash
# 利用可能なスキルを一覧表示
ls -d .claude/skills/*/SKILL.md | xargs dirname | xargs basename -a
```

現時点での有効なスキル:
- `agent-expert`
- `agent-memory`
- `architecture-design`
- `create-worktrees`
- `deep-research`
- `development-guidelines`
- `finance-news-collection`
- `functional-design`
- `glossary-creation`
- `prd-writing`
- `project-file`
- `project-status-sync`
- `repository-structure`

### 5. `allowed-tools` フィールド（オプション）

**検証項目**:

| チェック項目 | ルール | 例 |
|-------------|--------|-----|
| 形式 | カンマ区切り文字列 | `Read, Write, Glob, Grep` |
| 有効なツール名 | Claude Code で利用可能なツール | - |
| 最小権限の原則 | 必要なツールのみ指定 | - |

**有効なツール一覧**:

| ツール名 | 説明 |
|----------|------|
| `Read` | ファイル読み込み |
| `Write` | ファイル書き込み |
| `Edit` | ファイル編集 |
| `Glob` | ファイルパターン検索 |
| `Grep` | 内容検索 |
| `Bash` | コマンド実行 |
| `Task` | サブエージェント起動 |
| `WebSearch` | Web検索 |
| `WebFetch` | Webページ取得 |
| `AskUserQuestion` | ユーザーへの質問 |
| `TodoWrite` | タスク管理 |
| `MCPSearch` | MCPツール検索 |
| `NotebookEdit` | Jupyter Notebook編集 |

**検証方法**:

```bash
# allowed-tools の値を検証
valid_tools="Read|Write|Edit|Glob|Grep|Bash|Task|WebSearch|WebFetch|AskUserQuestion|TodoWrite|MCPSearch|NotebookEdit"

allowed=$(grep '^allowed-tools:' "$file" | sed 's/allowed-tools: //')
for tool in $(echo "$allowed" | tr ',' '\n'); do
    tool=$(echo "$tool" | tr -d ' ')
    if ! echo "$tool" | grep -qE "^($valid_tools)$"; then
        echo "WARN: 不明なツール '$tool'"
    fi
done
```

**注意事項**:
- `allowed-tools` を指定しない場合、エージェントは全てのツールにアクセス可能
- 制限が必要な場合のみ明示的に指定
- スキル（`.claude/skills/`）では `allowed-tools` でツールを制限することが推奨される

### 6. `model` フィールド（オプション）

**検証項目**:

| チェック項目 | ルール | 用途 |
|-------------|--------|------|
| 有効な値 | `inherit`, `sonnet`, `haiku`, `opus` のいずれか | - |
| `inherit` | 親から継承（デフォルト） | 一般的なタスク |
| `haiku` | 高速・低コスト | 単純なタスク |
| `sonnet` | バランス型 | 標準的なタスク |
| `opus` | 高性能 | 複雑なタスク |

**デフォルト**: `inherit`（指定しない場合）

### 7. `color` フィールド（オプション）

**検証項目**:

| チェック項目 | ルール | 例 |
|-------------|--------|-----|
| 有効な値 | 定義済みの色名 | `lime`, `blue`, `purple`, `orange`, `cyan`, `yellow` |

**用途**: UI表示時の識別色

## 検証チェックリスト

エージェントフロントマターをレビューする際は、以下のチェックリストを使用してください：

### 必須項目

- [ ] `name` が設定されている
- [ ] `name` がkebab-caseである
- [ ] `name` がファイル名と一致している
- [ ] `description` が設定されている
- [ ] `description` が具体的で明確である

### オプション項目（設定されている場合）

- [ ] `category` が既存のものか、または新規カテゴリとして適切か
- [ ] `skills` の参照先スキルが全て存在する
- [ ] `allowed-tools` のツール名が全て有効である
- [ ] `allowed-tools` が最小権限の原則に従っている
- [ ] `model` が有効な値である（inherit/sonnet/haiku/opus）
- [ ] `color` が有効な色名である

### 整合性チェック

- [ ] `description` にトリガーキーワードが含まれている
- [ ] 類似エージェントと責任範囲が重複していない
- [ ] エージェントの目的と `description` が一致している

## 自動検証スクリプト例

```bash
#!/bin/bash
# エージェントフロントマター検証スクリプト

agent_file="$1"

if [ ! -f "$agent_file" ]; then
    echo "ERROR: ファイルが存在しません: $agent_file"
    exit 1
fi

errors=0
warnings=0

# name チェック
name=$(grep '^name:' "$agent_file" | sed 's/name: //')
filename=$(basename "$agent_file" .md)

if [ -z "$name" ]; then
    echo "ERROR: name が設定されていません"
    ((errors++))
elif [ "$name" != "$filename" ]; then
    echo "ERROR: name ($name) とファイル名 ($filename) が不一致"
    ((errors++))
fi

# description チェック
description=$(grep '^description:' "$agent_file" | sed 's/description: //')
if [ -z "$description" ]; then
    echo "ERROR: description が設定されていません"
    ((errors++))
elif [ ${#description} -lt 20 ]; then
    echo "WARN: description が短すぎます (${#description}文字)"
    ((warnings++))
fi

# skills チェック
if grep -q '^skills:' "$agent_file"; then
    # YAML配列をパース
    skills_line=$(grep '^skills:' "$agent_file")
    # [skill1, skill2] 形式を想定
    skills=$(echo "$skills_line" | sed 's/skills: \[//' | sed 's/\]//' | tr ',' '\n')
    for skill in $skills; do
        skill=$(echo "$skill" | tr -d ' "')
        if [ -n "$skill" ] && [ ! -d ".claude/skills/$skill" ]; then
            echo "ERROR: スキル '$skill' が存在しません"
            ((errors++))
        fi
    done
fi

# 結果サマリー
echo "---"
echo "検証結果: エラー=$errors, 警告=$warnings"
if [ $errors -gt 0 ]; then
    exit 1
fi
```

## 関連ドキュメント

- `guide.md`: エージェント設計の詳細ガイド
- `template.md`: エージェントテンプレート
- `SKILL.md`: agent-expert スキル定義
