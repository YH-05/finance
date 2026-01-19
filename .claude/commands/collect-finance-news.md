---
description: テーマ別に金融ニュースを収集し、GitHub Project 15に自動投稿します
argument-hint: [--since 1d|3d|7d] [--themes "index,stock,..."] [--limit N] [--dry-run]
---

テーマ別金融ニュース収集を実行します。

## 入力パラメータ

| パラメータ | 必須 | デフォルト | 説明 |
|-----------|------|-----------|------|
| --since | - | 1d | 公開日時フィルタ（1d=1日, 3d=3日, 7d=7日以内の記事のみ） |
| --project | - | 15 | GitHub Project番号（Finance News Collection） |
| --limit | - | 50 | 取得する記事数の最大値 |
| --themes | - | all | 対象テーマ（index,stock,sector,macro,ai またはall） |
| --dry-run | - | false | GitHub投稿せずに収集結果のみ表示 |

### --since オプション詳細

記事の**公開日時（published）**を基準に、現在日時からの日数でフィルタリングします。

| 値 | 説明 | 例（現在が2026-01-19の場合） |
|-----|------|------------------------------|
| `1d` | 過去1日（24時間）以内 | 2026-01-18 00:00以降の記事 |
| `3d` | 過去3日以内 | 2026-01-16 00:00以降の記事 |
| `7d` | 過去7日以内 | 2026-01-12 00:00以降の記事 |

**注意**:
- 公開日時（published）はRSSフィードに記載された記事の公開日時です
- GitHub Issueの作成日時ではありません
- 公開日時がない記事は、取得日時（fetched_at）で代替判定します

## 処理フロー

```
Phase 1: 初期化
├── テーマ設定ファイル確認
├── RSS MCP ツール確認
└── GitHub CLI 確認

Phase 2: データ準備（オーケストレーター）
└── finance-news-orchestrator エージェント起動
    ├── RSS記事取得
    ├── 既存Issue取得
    └── 一時ファイル保存

Phase 3: テーマ別収集（並列）
├── finance-news-index      [Status=Index]
├── finance-news-stock      [Status=Stock]
├── finance-news-sector     [Status=Sector]
├── finance-news-macro      [Status=Macro Economics]
└── finance-news-ai         [Status=AI]
    ↓ 各エージェントが並列実行
    ├── キーワードフィルタリング
    ├── 重複チェック
    ├── Issue作成
    ├── Project追加
    └── Status自動設定

Phase 4: 結果報告
└── テーマ別投稿数サマリー表示
```

## 実行手順

### Phase 1: 初期化

#### 1. テーマ設定ファイル確認

```bash
if [ ! -f "data/config/finance-news-themes.json" ]; then
    echo "エラー: テーマ設定ファイルが見つかりません"
    echo "期待されるパス: data/config/finance-news-themes.json"
    exit 1
fi
```

**設定ファイル構造**:
```json
{
  "themes": {
    "index": { "github_status_id": "f75ad846", ... },
    "stock": { "github_status_id": "47fc9ee4", ... },
    "sector": { "github_status_id": "98236657", ... },
    "macro": { "github_status_id": "c40731f6", ... },
    "ai": { "github_status_id": "17189c86", ... }
  },
  "common": { ... },
  "project": {
    "project_id": "PVT_kwHOBoK6AM4BMpw_",
    "status_field_id": "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE",
    "owner": "YH-05",
    "number": 15
  }
}
```

#### 2. RSS MCP ツール確認（リトライ機能付き）

**重要**: MCPサーバーの起動には数秒かかる場合があります。セッション開始直後はツールが見つからない可能性があるため、リトライロジックを実装しています。

```
[試行1] キーワード検索でRSS MCPツールを検索
MCPSearch: query="rss", max_results=5

↓ ツールが見つかった場合
成功 → Phase 2へ進む

↓ ツールが見つからない場合（"No matching MCP tools found"）
[待機] 3秒待機（MCPサーバーの起動完了を待つ）

[試行2] 再度キーワード検索
MCPSearch: query="rss", max_results=5

↓ ツールが見つかった場合
成功 → Phase 2へ進む

↓ それでも見つからない場合
エラー報告:
  - RSS MCPサーバーが起動していない可能性
  - .mcp.json の設定確認を促す
  - トラブルシューティング手順を表示
  - 処理を中断
```

**リトライロジックの理由**:
- MCPサーバーは非同期で起動するため、Claude Codeセッション開始直後は利用不可
- `uv run rss-mcp` コマンドの実行に2-5秒程度かかる
- 1回目の検索失敗時、3秒待機してから再検索することで成功率が向上

**検索するRSS MCPツール**:
- `mcp__rss__list_feeds`: 登録済みフィード一覧取得
- `mcp__rss__get_items`: フィードから記事取得
- `mcp__rss__search_items`: キーワード検索
- `mcp__rss__add_feed`: フィード追加
- `mcp__rss__update_feed`: フィード更新
- `mcp__rss__remove_feed`: フィード削除
- `mcp__rss__fetch_feed`: フィード即時取得

#### 3. GitHub CLI 確認

```bash
# gh コマンドの確認
if ! command -v gh &> /dev/null; then
    echo "エラー: GitHub CLI (gh) がインストールされていません"
    echo "インストール方法: https://cli.github.com/"
    exit 1
fi

# 認証確認
if ! gh auth status &> /dev/null; then
    echo "エラー: GitHub認証が必要です"
    echo "認証方法: gh auth login"
    exit 1
fi
```

### Phase 2: データ準備

#### 4. finance-news-orchestrator エージェント起動

```
Task: finance-news-orchestrator
Description: データ準備（RSS記事取得、既存Issue取得、一時ファイル保存）

Parameters:
  - limit: {limit}

Processing:
1. RSS MCPツールで金融フィードから記事を取得
2. GitHub CLIで既存のニュースIssueを取得（label="news", limit=100）
3. 一時ファイルに保存（.tmp/news-collection-{timestamp}.json）
4. 完了報告
```

**一時ファイル構造**:
```json
{
  "session_id": "news-collection-20260115-143000",
  "timestamp": "2026-01-15T14:30:00Z",
  "rss_items": [...],         // RSS記事リスト
  "existing_issues": [...],   // 既存Issueリスト
  "themes": ["index", "stock", "sector", "macro", "ai"]
}
```

### Phase 3: テーマ別収集（並列）

#### 5. テーマ別エージェント並列起動

> **🚨 重要: サブエージェントへのデータ渡しルール 🚨**
>
> 必ず `.claude/rules/subagent-data-passing.md` を参照すること。
> **データの簡略化・省略は絶対禁止**。完全なJSON形式でデータを渡すこと。

**対象テーマの決定**:
```python
# --themes パラメータで指定
if themes == "all":
    target_themes = ["index", "stock", "sector", "macro", "ai"]
else:
    target_themes = themes.split(",")
```

**データ渡し方式（2つのパターン）**:

**パターンA: 一時ファイル経由（推奨）**
```python
# Phase 2で作成した一時ファイルを参照
temp_file = f".tmp/news-collection-{timestamp}.json"

Task(
    subagent_type="finance-news-stock",
    prompt=f"一時ファイルを読み込んで処理してください: {temp_file}"
)
```

**パターンB: プロンプト内でJSON直接渡し**
```python
# 完全なRSSデータをJSON形式で渡す（簡略化禁止）
Task(
    subagent_type="finance-news-stock",
    prompt=f"""以下のRSSデータを処理してください。

## RSS記事データ（完全版）【省略禁止】
```json
{json.dumps(rss_items, ensure_ascii=False, indent=2)}
```

## 既存Issue（重複チェック用）
```json
{json.dumps(existing_issues, ensure_ascii=False, indent=2)}
```
"""
)
```

**⛔ 絶対禁止: データの簡略化**
```python
# ❌ これは絶対にやってはいけない
Task(
    prompt="""以下の記事を処理:
    1. "記事タイトル" - 簡単な説明
    2. "記事タイトル" - 簡単な説明
    """
)
# → URLがないためIssue作成不可、重大な障害発生
```

**並列起動**:
```
# 複数のTask toolを並列呼び出し（単一メッセージで複数tool use）

Task: finance-news-index
  - input: .tmp/news-collection-{timestamp}.json（完全なRSSデータ）
  - output: GitHub Issues (Status=Index)

Task: finance-news-stock
  - input: .tmp/news-collection-{timestamp}.json（完全なRSSデータ）
  - output: GitHub Issues (Status=Stock)

Task: finance-news-sector
  - input: .tmp/news-collection-{timestamp}.json（完全なRSSデータ）
  - output: GitHub Issues (Status=Sector)

Task: finance-news-macro
  - input: .tmp/news-collection-{timestamp}.json（完全なRSSデータ）
  - output: GitHub Issues (Status=Macro Economics)

Task: finance-news-ai
  - input: .tmp/news-collection-{timestamp}.json（完全なRSSデータ）
  - output: GitHub Issues (Status=AI)
```

**各エージェントの処理**:
1. 一時ファイルから記事データ読み込み（または直接JSON受信）
2. **入力データ検証**（link, published, title, summaryの存在確認）
3. テーマキーワードでフィルタリング
4. 除外キーワードチェック
5. 重複チェック
6. GitHub Issue作成 (`gh issue create --title "[{theme_ja}] {japanese_title}" --label "news"`)
7. Project追加 (`gh project item-add 15 --owner YH-05 --url {issue_url}`)
8. Status設定 (GraphQL API)

### Phase 4: 結果報告

#### 6. テーマ別サマリー表示

```markdown
## 金融ニュース収集完了

### 実行パラメータ
- **GitHub Project**: #15 (Finance News Collection)
- **公開日時フィルタ**: 過去1日以内（--since 1d）
- **取得上限**: 50件
- **対象テーマ**: index, stock, sector, macro, ai

### 収集結果（テーマ別）

| テーマ | 処理数 | 期間内 | マッチ | 除外 | 重複 | 新規投稿 | 失敗 |
|-------|-------|-------|-------|-----|-----|---------|-----|
| Index | 50 | 35 | 12 | 2 | 7 | 5 | 0 |
| Stock | 50 | 40 | 15 | 1 | 8 | 8 | 0 |
| Sector | 50 | 30 | 8 | 0 | 5 | 3 | 0 |
| Macro | 50 | 45 | 10 | 1 | 6 | 7 | 0 |
| AI | 50 | 25 | 6 | 0 | 4 | 4 | 0 |
| **合計** | 250 | 175 | 51 | 4 | 30 | **27** | 0 |

### 投稿されたニュース（テーマ別抜粋）

**Index（株価指数）**
1. **日経平均、3万円台を回復** [#200]
   - ソース: 日経新聞
   - URL: https://github.com/YH-05/finance/issues/200

**Stock（個別銘柄）**
1. **トヨタ、過去最高益を記録** [#205]
   - ソース: ロイター
   - URL: https://github.com/YH-05/finance/issues/205

**Macro Economics（マクロ経済）**
1. **日銀、政策金利を引き上げ** [#210]
   - ソース: Bloomberg
   - URL: https://github.com/YH-05/finance/issues/210

### 次のアクション

- GitHub Projectで詳細を確認: https://github.com/users/YH-05/projects/15
- 再度収集を実行: /collect-finance-news
```

## dry-run モード

GitHub投稿せずに収集結果のみを確認できます。

```bash
/collect-finance-news --dry-run
```

**dry-runモードの動作**:
- オーケストレーター: データ準備まで実行
- テーマエージェント: フィルタリング・重複チェックまで実行（Issue作成せず）
- 結果表示: 投稿候補の詳細をテーマ別に表示

**出力例**:
```markdown
## 金融ニュース収集（dry-run）

### フィルタリング結果（テーマ別）

**Index（株価指数） - 投稿候補: 5件**

✅ 1. 日経平均、3万円台を回復
   - ソース: 日経新聞
   - キーワード: 日経平均, 株価, 指数
   - URL: https://www.nikkei.com/article/...

✅ 2. S&P500、史上最高値を更新
   - ソース: Reuters
   - キーワード: S&P500, 指数, 最高値
   - URL: https://www.reuters.com/...

**Stock（個別銘柄） - 投稿候補: 8件**

✅ 1. トヨタ、過去最高益を記録
   - ソース: ロイター
   - キーワード: トヨタ, 決算, 業績
   - URL: https://www.reuters.com/...

❌ 除外: 2件
🔄 重複: 7件

### 実際に投稿する場合

/collect-finance-news
```

## エラーハンドリング

### E001: テーマ設定ファイルエラー

**発生条件**:
- `data/config/finance-news-themes.json` が存在しない
- JSON形式が不正

**対処法**:
```
エラー: テーマ設定ファイルが見つかりません

期待されるパス: data/config/finance-news-themes.json

対処法:
1. テンプレートファイルをコピー:
   cp data/config/finance-news-filter.json data/config/finance-news-themes.json
2. テーマ別設定に変換（手動またはスクリプト実行）
```

### E002: RSS MCP ツールエラー

**発生条件**:
- RSS MCPサーバーが起動していない
- MCPサーバーの起動が完了していない（起動中）
- .mcp.json の設定が不正

**自動対処（リトライロジック）**:
コマンドは自動的に以下の対処を行います：

1. **1回目の検索失敗** → 3秒待機してから再検索
2. **2回目も失敗** → エラー報告

これにより、セッション開始直後のMCPサーバー起動遅延による失敗を自動的に回避します。

**手動対処法（2回目も失敗した場合）**:
```
エラー: RSS MCPツールが利用できません（2回試行後）

確認項目:
1. .mcp.json に RSS MCPサーバーの設定があるか確認
   場所: .mcp.json
   設定例:
   {
     "rss": {
       "command": "uv",
       "args": ["run", "rss-mcp"],
       "env": {
         "RSS_DATA_DIR": "./data/raw/rss"
       }
     }
   }

2. MCPサーバーが正しく起動しているか確認
   テスト: uv run rss-mcp --version

3. Claude Code を再起動（MCPサーバーを完全リセット）

4. それでも失敗する場合は .mcp.json の構文エラーをチェック

詳細: src/rss/mcp/server.py を参照
```

**一般的な原因**:
- **起動遅延**: MCPサーバーの起動に2-5秒かかる（自動リトライで解決）
- **設定エラー**: .mcp.jsonのJSON構文エラー
- **依存関係エラー**: uvまたはPython環境の問題
- **ポート競合**: 他のプロセスがポートを使用中

### E003: GitHub CLI エラー

**発生条件**:
- `gh` コマンドがインストールされていない
- GitHub認証が切れている

**対処法**:
```
エラー: GitHub CLI (gh) がインストールされていません

インストール方法:
- macOS: brew install gh
- Linux: https://cli.github.com/
- Windows: https://cli.github.com/

認証方法:
gh auth login
```

### E004: ネットワークエラー

**発生条件**:
- RSS フィードへの接続失敗
- GitHub API への接続失敗

**対処法**:
- エラーログを確認
- リトライ（最大3回、指数バックオフ）
- 一時的なエラーの場合は時間をおいて再実行

### E005: GitHub API レート制限

**発生条件**:
- 1時間あたり5000リクエストを超過

**対処法**:
```
エラー: GitHub API レート制限に達しました

対処法:
- 1時間待機してから再実行
- または --limit オプションで取得数を減らす:
  /collect-finance-news --limit 10
```

### E006: 並列実行エラー

**発生条件**:
- 一部のテーマエージェントが失敗

**対処法**:
- 成功したテーマの結果は有効
- 失敗したテーマのみ再実行可能:
  ```bash
  /collect-finance-news --themes "stock,ai"
  ```

## 高度な使用例

### 例1: 過去3日以内のニュースを収集

```bash
/collect-finance-news --since 3d
```

過去3日以内に公開された記事のみを収集します。

### 例2: 過去1週間のニュースを収集（週次レポート用）

```bash
/collect-finance-news --since 7d --themes "index,macro"
```

過去7日以内のIndex・Macroテーマのニュースを収集します。

### 例3: 特定のテーマのみ収集

```bash
/collect-finance-news --themes "index,macro"
```

IndexとMacro Economicsテーマのみニュースを収集します。

### 例4: 少量のニュースを収集

```bash
/collect-finance-news --limit 10
```

テスト用に10件のみ収集します（各テーマエージェントに渡される）。

### 例5: dry-runで事前確認

```bash
/collect-finance-news --dry-run --since 3d --limit 10
```

投稿せずに、過去3日以内の記事のフィルタリング結果を確認します。

### 例6: 別のGitHub Projectに投稿（非推奨）

```bash
/collect-finance-news --project 14
```

Finance News Collection以外のプロジェクトに投稿します（通常は不要）。

## 設定カスタマイズ

### テーマ別キーワードの編集

```bash
# テーマ設定ファイルを編集
vi data/config/finance-news-themes.json
```

**編集可能な項目**:
- `themes.{theme}.keywords.include`: テーマ別includeキーワード
- `themes.{theme}.keywords.priority_boost`: 優先度ブーストキーワード
- `themes.{theme}.min_keyword_matches`: 最低マッチ数
- `common.exclude_keywords`: 共通除外キーワード
- `common.sources.tier1/tier2/tier3`: 情報源Tier分類
- `common.filtering.title_similarity_threshold`: タイトル類似度閾値

### RSS フィードの追加

RSS MCPツールを使用して新しいフィードを追加:

```python
# MCPツールでフィードを追加
mcp__rss__add_feed(
    url="https://example.com/finance/rss",
    title="新しい金融ニュースソース",
    category="finance",
    fetch_interval="daily",
    enabled=True
)
```

## 制約事項

1. **GitHub API レート制限**: 1時間あたり5000リクエスト（認証済み）
2. **RSS記事の取得制限**: 1回のリクエストで最大100件
3. **重複チェックの範囲**: 直近100件のIssueのみ
4. **実行頻度**: 1日1回を推奨（フィードの更新頻度に依存）
5. **並列実行**: 5エージェント同時実行によるGitHub API負荷増加
6. **Issue番号の連続性**: 並列実行のため、Issue番号は連続しない可能性あり

## 関連リソース

- **エージェント**:
  - `.claude/agents/finance-news-orchestrator.md` (オーケストレーター)
  - `.claude/agents/finance-news-index.md` (Indexテーマ)
  - `.claude/agents/finance-news-stock.md` (Stockテーマ)
  - `.claude/agents/finance-news-sector.md` (Sectorテーマ)
  - `.claude/agents/finance-news-macro.md` (Macro Economicsテーマ)
  - `.claude/agents/finance-news-ai.md` (AIテーマ)
- **テーマ設定**: `data/config/finance-news-themes.json`
- **GitHub Project**: https://github.com/users/YH-05/projects/15
- **RSS MCPツール**: `src/rss/mcp/server.py`

## 関連コマンド

- **フィード管理**: RSS MCPツールで直接管理
- **Issue確認**: `gh issue list --label "news"`
- **設定確認**: `cat data/config/finance-news-themes.json`
- **一時ファイル確認**: `ls -lh .tmp/`
- **一時ファイル削除**: `rm .tmp/news-collection-*.json`
