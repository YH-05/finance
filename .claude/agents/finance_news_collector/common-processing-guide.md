# 金融ニュース収集エージェント共通処理ガイド

このガイドは、テーマ別ニュース収集エージェント（finance-news-{theme}）の共通処理を定義します。

## 共通設定

- **Issueテンプレート**: `.github/ISSUE_TEMPLATE/news-article.md`（Markdown形式）
- **GitHub Project**: #15 (`PVT_kwHOBoK6AM4BMpw_`)
- **Statusフィールド**: `PVTSSF_lAHOBoK6AM4BMpw_zg739ZE`
- **公開日時フィールド**: `PVTF_lAHOBoK6AM4BMpw_zg8BzrI`（Date型、ソート用）

## 使用ツール

各サブエージェントは以下のツールを使用します：

```yaml
tools:
  - Read              # ファイル読み込み
  - Bash              # gh CLI実行
  - MCPSearch         # MCPツール検索・ロード
  - mcp__rss__fetch_feed   # RSSフィード更新
  - mcp__rss__get_items    # RSS記事取得
```

## Phase 1: 初期化

### ステップ1.1: MCPツールのロード

```python
def load_mcp_tools() -> bool:
    """MCPツールをロードする"""

    try:
        # MCPSearchでRSSツールをロード
        MCPSearch(query="select:mcp__rss__fetch_feed")
        MCPSearch(query="select:mcp__rss__get_items")
        return True
    except Exception as e:
        ログ出力: f"警告: MCPツールのロード失敗: {e}"
        ログ出力: "ローカルフォールバックを使用します"
        return False
```

### ステップ1.2: 既存Issue取得（重複チェック用）

```bash
gh issue list \
    --repo YH-05/finance \
    --label "news" \
    --state all \
    --limit 100 \
    --json number,title,body,createdAt
```

### ステップ1.3: 統計カウンタ初期化

```python
processed = 0
matched = 0
duplicates = 0
created = 0
failed = 0
```

## Phase 2: RSS取得（フィード直接取得）

**重要**: 各サブエージェントは自分の担当フィードから直接記事を取得します。

### ステップ2.1: 担当フィードからの取得

```python
def fetch_assigned_feeds(assigned_feeds: list[dict]) -> list[dict]:
    """担当フィードから記事を取得する

    Parameters
    ----------
    assigned_feeds : list[dict]
        担当フィードのリスト（feed_id, titleを含む）

    Returns
    -------
    list[dict]
        取得した記事のリスト
    """

    all_items = []

    for feed in assigned_feeds:
        feed_id = feed["feed_id"]
        feed_title = feed["title"]

        try:
            # Step 1: フィードを最新化
            mcp__rss__fetch_feed(feed_id=feed_id)

            # Step 2: 記事を取得（24時間以内）
            items = mcp__rss__get_items(
                feed_id=feed_id,
                hours=24,
                limit=50
            )

            # フィード情報を付加
            for item in items:
                item["feed_source"] = feed_title
                item["feed_id"] = feed_id

            all_items.extend(items)
            ログ出力: f"取得完了: {feed_title} ({len(items)}件)"

        except Exception as e:
            ログ出力: f"警告: フィード取得失敗: {feed_title}: {e}"
            # ローカルフォールバックを試行
            local_items = load_from_local(feed_id, feed_title)
            all_items.extend(local_items)

    return all_items
```

### ステップ2.2: ローカルフォールバック

MCPツールが利用できない場合、ローカルに保存されたRSSデータを使用します。

```python
def load_from_local(feed_id: str, feed_title: str) -> list[dict]:
    """ローカルのRSSデータから記事を取得する

    Parameters
    ----------
    feed_id : str
        フィードID
    feed_title : str
        フィード名（ログ用）

    Returns
    -------
    list[dict]
        取得した記事のリスト
    """

    local_path = f"data/raw/rss/{feed_id}/items.json"

    try:
        with open(local_path) as f:
            data = json.load(f)

        items = data.get("items", [])

        # 24時間以内のアイテムのみフィルタ
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_items = []

        for item in items:
            published = item.get("published")
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace('Z', '+00:00'))
                    if dt >= cutoff:
                        item["feed_source"] = feed_title
                        item["feed_id"] = feed_id
                        recent_items.append(item)
                except ValueError:
                    continue

        ログ出力: f"ローカルから取得: {feed_title} ({len(recent_items)}件)"
        return recent_items

    except FileNotFoundError:
        ログ出力: f"警告: ローカルデータなし: {local_path}"
        return []
    except json.JSONDecodeError as e:
        ログ出力: f"警告: JSONパースエラー: {local_path}: {e}"
        return []
```

## Phase 3: AI判断によるテーマ分類

**重要**: キーワードマッチングは使用しません。**AIが記事の内容を読み取り、テーマに該当するか判断**します。

### ステップ3.1: AI判断によるテーマ判定

各記事について、タイトルと要約（summary）を読み取り、以下の基準でテーマに該当するか判断します。

**テーマ別判定基準**:

| テーマ | 判定基準 |
|--------|----------|
| **Index** | 株価指数（日経平均、TOPIX、S&P500、ダウ、ナスダック等）の動向、市場全体の上昇/下落、ETF関連 |
| **Stock** | 個別企業の決算発表、業績予想、M&A、買収、提携、株式公開、経営陣の変更 |
| **Sector** | 特定業界（銀行、保険、自動車、半導体、ヘルスケア、エネルギー等）の動向、規制変更 |
| **Macro** | 金融政策（金利、量的緩和）、中央銀行（Fed、日銀、ECB）、経済指標（GDP、CPI、雇用統計）、為替 |
| **AI** | AI技術、機械学習、生成AI、AI企業（OpenAI、NVIDIA等）、AI投資、AI規制 |

**判定プロセス**:

```
[1] 記事のタイトルと要約を読む
    ↓
[2] 記事の主題を理解する
    ↓
[3] 上記テーマ判定基準に照らして該当するか判断
    ↓
[4] 該当する場合 → Phase 2.2へ
    該当しない場合 → スキップ
```

**判定例**:

| 記事タイトル | AIの判断 | テーマ |
|------------|---------|--------|
| "S&P 500 hits new record high amid tech rally" | 株価指数の動向について → 該当 | Index |
| "Fed signals rate cut in March meeting" | 金融政策・中央銀行の動向 → 該当 | Macro |
| "Apple reports Q4 earnings beat" | 個別企業の決算発表 → 該当 | Stock |
| "Banks face new capital requirements" | 銀行セクターの規制 → 該当 | Sector |
| "OpenAI launches new model capabilities" | AI企業の動向 → 該当 | AI |
| "Celebrity launches new clothing line" | 金融・経済と無関係 → 非該当 | - |

### ステップ3.2: 除外判断

以下のカテゴリに該当する記事は除外します（金融テーマに関連する場合を除く）:

- **スポーツ**: 試合結果、選手移籍など（ただし、スポーツ関連企業の決算等は対象）
- **エンターテインメント**: 映画、音楽、芸能ニュース
- **政治**: 選挙、内閣関連（ただし、金融政策・規制に関連する場合は対象）
- **一般ニュース**: 事故、災害、犯罪

### ステップ3.3: 重複チェック

```python
def calculate_title_similarity(title1: str, title2: str) -> float:
    """タイトルの類似度を計算（Jaccard係数）"""

    words1 = set(title1.lower().split())
    words2 = set(title2.lower().split())

    if not words1 or not words2:
        return 0.0

    common = words1.intersection(words2)
    total = words1.union(words2)

    return len(common) / len(total)


def is_duplicate(new_item: dict, existing_issues: list[dict], threshold: float = 0.85) -> bool:
    """既存Issueと重複しているかチェック"""

    new_link = new_item.get('link', '')
    new_title = new_item.get('title', '')

    for issue in existing_issues:
        # URL完全一致
        body = issue.get('body', '')
        if new_link and new_link in body:
            return True

        # タイトル類似度チェック
        issue_title = issue.get('title', '')
        similarity = calculate_title_similarity(new_title, issue_title)

        if similarity >= threshold:
            return True

    return False
```

## Phase 4: GitHub投稿

### ステップ4.0: 記事内容取得と要約生成

**重要**: Issue作成前に、必ず記事URLから実際の内容を取得して日本語要約を生成すること。

```python
def fetch_article_content(url: str, title: str) -> str:
    """記事内容を取得（WebFetch → gemini検索の順で試行）"""

    # 1. WebFetchで記事取得を試行
    try:
        content = WebFetch(
            url=url,
            prompt="""この記事の内容を詳しく要約してください。特に以下の点を含めてください:
            1. 主要な事実と背景
            2. 関連企業や機関の動き
            3. 市場や業界への影響
            4. 数値データや具体的な情報
            5. 今後の展望や予測"""
        )
        return content
    except Exception as e:
        # 2. 失敗した場合は gemini CLI で代替
        domain = url.split('/')[2]
        query = f"{title} {domain}"

        result = subprocess.run(
            ["gemini", "--prompt", f"WebSearch: {query}"],
            capture_output=True,
            text=True
        )
        return result.stdout


def generate_japanese_summary(content: str, max_length: int = 400) -> str:
    """記事内容から日本語要約を生成（400字程度）"""

    prompt = f"""以下の記事内容を、日本語で400字程度に要約してください。

    要約のポイント:
    - 主要な事実と数値データを優先
    - 背景や影響を簡潔に説明
    - 投資判断に有用な情報を強調
    - 箇条書きではなく、文章形式で

    記事内容:
    {content}
    """

    summary = generate_summary(prompt)
    return summary
```

### ステップ4.1: 日時フォーマット関数

**重要**: GitHub Projectでソートするため、公開日時をISO 8601形式に変換します。
また、Issue本文には「収集日時」（Issue作成時の日時）も必ず記載します。

```python
from datetime import datetime, timezone
import pytz


def format_published_iso(published_str: str | None) -> str:
    """公開日をISO 8601形式に変換（YYYY-MM-DD）"""

    if not published_str:
        # 公開日がない場合は現在日時を使用
        return datetime.now(timezone.utc).strftime('%Y-%m-%d')

    try:
        dt = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
    except ValueError:
        # パース失敗時は現在日時を使用
        dt = datetime.now(timezone.utc)

    # Date型フィールドはYYYY-MM-DD形式
    return dt.strftime('%Y-%m-%d')


def format_published_jst(published_str: str | None) -> str:
    """公開日をJST YYYY-MM-DD HH:MM形式に変換（Issue本文用）"""

    jst = pytz.timezone('Asia/Tokyo')

    if not published_str:
        # 公開日がない場合は現在日時を使用
        return datetime.now(jst).strftime('%Y-%m-%d %H:%M')

    try:
        dt = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
    except ValueError:
        # パース失敗時は現在日時を使用
        dt = datetime.now(timezone.utc)

    dt_jst = dt.astimezone(jst)
    return dt_jst.strftime('%Y-%m-%d %H:%M')


def get_collected_at_jst() -> str:
    """収集日時（現在時刻）をJST形式で取得（YYYY-MM-DD HH:MM）

    Issue作成時に呼び出し、収集日時として記録する。
    """

    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).strftime('%Y-%m-%d %H:%M')
```

### ステップ4.2: Issue作成（テンプレート読み込み方式）

**重要: Issueタイトルの日本語化ルール**:
1. **タイトル形式**: `[{theme_ja}] {japanese_title}`
2. **テーマ名プレフィックス（日本語）**:
   - `[株価指数]`, `[個別銘柄]`, `[セクター]`, `[マクロ経済]`, `[AI]`
3. **タイトル翻訳**: 英語記事の場合は日本語に翻訳（要約生成時に同時に実施）

**テンプレート読み込み→プレースホルダー置換**:

```bash
# Step 1: テンプレートを読み込む
template=$(cat .github/ISSUE_TEMPLATE/news-article.md | tail -n +7)  # frontmatter除外

# Step 2: 収集日時を取得（Issue作成直前に実行）
collected_at=$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M')

# Step 3: プレースホルダーを置換
body="${template//\{\{summary\}\}/$japanese_summary}"
body="${body//\{\{url\}\}/$link}"
body="${body//\{\{published_date\}\}/$published_jst(JST)}"
body="${body//\{\{collected_at\}\}/$collected_at(JST)}"
body="${body//\{\{credibility\}\}/3点 - 中程度}"
body="${body//\{\{category\}\}/$category}"
body="${body//\{\{feed_source\}\}/$source}"
body="${body//\{\{priority\}\}/Medium - 通常の記事化候補}"
body="${body//\{\{notes\}\}/- テーマ: $theme_name
- AI判定理由: $判定理由}"

# Step 4: Issue作成
gh issue create \
    --repo YH-05/finance \
    --title "[{theme_ja}] {japanese_title}" \
    --body "$body" \
    --label "news"
```

**テンプレートプレースホルダー一覧** (`.github/ISSUE_TEMPLATE/news-article.md`):

| プレースホルダー | 説明 | 例 |
|-----------------|------|-----|
| `{{summary}}` | 日本語要約（400字以上） | - |
| `{{url}}` | 情報源URL | `https://...` |
| `{{published_date}}` | 公開日時 | `2026-01-15 10:00(JST)` |
| `{{collected_at}}` | 収集日時 | `2026-01-15 14:30(JST)` |
| `{{credibility}}` | 信頼性スコア | `3点 - 中程度` |
| `{{category}}` | カテゴリ | `Index（株価指数）` |
| `{{feed_source}}` | フィード名 | `CNBC - Markets` |
| `{{priority}}` | 優先度 | `Medium - 通常の記事化候補` |
| `{{notes}}` | 備考・メモ | テーマ、AI判定理由 |

### ステップ4.3: Project追加

```bash
gh project item-add 15 \
    --owner YH-05 \
    --url {issue_url}
```

### ステップ4.4: Status設定（GraphQL API）

**Step 1: Issue Node IDを取得**

```bash
gh api graphql -f query='
query {
  repository(owner: "YH-05", name: "finance") {
    issue(number: {issue_number}) {
      id
    }
  }
}'
```

**Step 2: Project Item IDを取得**

```bash
gh api graphql -f query='
query {
  node(id: "{issue_node_id}") {
    ... on Issue {
      projectItems(first: 10) {
        nodes {
          id
          project {
            number
          }
        }
      }
    }
  }
}'
```

**Step 3: Statusフィールドを設定**

```bash
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PVT_kwHOBoK6AM4BMpw_"
      itemId: "{project_item_id}"
      fieldId: "PVTSSF_lAHOBoK6AM4BMpw_zg739ZE"
      value: {
        singleSelectOptionId: "{status_option_id}"
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}'
```

**⚠️ 注意: ステップ4.4完了後、必ず続けてステップ4.5（公開日時設定）を実行すること！**

### ステップ4.5: 公開日時フィールドを設定（Date型）【必須・最重要】

> **🚨 絶対に省略しないでください！🚨**
>
> このステップを省略すると、GitHub Projectで「No date」と表示され、
> 記事の時系列管理ができなくなります。

**⚠️ 必須**: このステップを省略するとGitHub Projectで「No date」と表示されます。
**⚠️ 必須**: Issue作成後、Status設定と共に必ず実行すること。
**⚠️ 確認**: 実行後、GitHub Project上で日付が正しく表示されていることを確認すること。

GitHub ProjectでIssueを公開日時でソートするため、必ず設定してください。

```bash
gh api graphql -f query='
mutation {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: "PVT_kwHOBoK6AM4BMpw_"
      itemId: "{project_item_id}"
      fieldId: "PVTF_lAHOBoK6AM4BMpw_zg8BzrI"
      value: {
        date: "{published_iso}"
      }
    }
  ) {
    projectV2Item {
      id
    }
  }
}'
```

**日付形式**: `YYYY-MM-DD`（例: `2026-01-15`）

## Phase 5: 結果報告

### 統計サマリー出力フォーマット

```markdown
## {theme_name} ニュース収集完了

### 処理統計
- **処理記事数**: {processed}件
- **テーママッチ**: {matched}件（AI判断）
- **重複**: {duplicates}件
- **新規投稿**: {created}件
- **投稿失敗**: {failed}件

### 投稿されたニュース

1. **{title}** [#{issue_number}]
   - ソース: {source}
   - 公開日時: {published_jst}
   - AI判定理由: {判定理由}
   - URL: https://github.com/YH-05/finance/issues/{issue_number}
```

## テーマ別Status ID一覧

| テーマ | Status名 | Option ID |
|--------|----------|-----------|
| index | Index | `f75ad846` |
| stock | Stock | `47fc9ee4` |
| sector | Sector | `98236657` |
| macro | Macro Economics | `c40731f6` |
| ai | AI | `17189c86` |

## GitHub Projectフィールド一覧

| フィールド名 | フィールドID | 型 | 用途 |
|-------------|-------------|-----|------|
| Status | `PVTSSF_lAHOBoK6AM4BMpw_zg739ZE` | SingleSelect | テーマ分類 |
| 公開日時 | `PVTF_lAHOBoK6AM4BMpw_zg8BzrI` | Date | ソート用 |

## 共通エラーハンドリング

### E001: MCPツール接続エラー

```python
def handle_mcp_error(feed_id: str, feed_title: str, error: Exception) -> list[dict]:
    """MCPツール接続失敗時のフォールバック処理

    Parameters
    ----------
    feed_id : str
        フィードID
    feed_title : str
        フィード名（ログ用）
    error : Exception
        発生したエラー

    Returns
    -------
    list[dict]
        ローカルから取得した記事（取得できない場合は空リスト）
    """

    ログ出力: f"警告: MCPツール接続失敗: {feed_title}"
    ログ出力: f"エラー詳細: {error}"
    ログ出力: "ローカルフォールバックを試行します"

    # ローカルデータから取得を試みる
    return load_from_local(feed_id, feed_title)
```

### E002: Issue作成エラー

```python
try:
    result = subprocess.run(
        ["gh", "issue", "create", ...],
        capture_output=True,
        text=True,
        check=True
    )
except subprocess.CalledProcessError as e:
    ログ出力: f"警告: Issue作成失敗: {item['title']}"
    ログ出力: f"エラー詳細: {e.stderr}"

    if "rate limit" in str(e.stderr).lower():
        ログ出力: "GitHub API レート制限に達しました。1時間待機してください。"

    failed += 1
    continue
```

### E003: 公開日時設定エラー

```python
try:
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={mutation}"],
        capture_output=True,
        text=True,
        check=True
    )
except subprocess.CalledProcessError as e:
    ログ出力: f"警告: 公開日時設定失敗: Issue #{issue_number}"
    ログ出力: f"エラー詳細: {e.stderr}"
    ログ出力: "Issue作成は成功しています。手動で公開日時を設定してください。"
    continue
```

## 参考資料

- **Issueテンプレート**: `.github/ISSUE_TEMPLATE/news-article.md`（Markdown形式）
- **オーケストレーター**: `.claude/agents/finance-news-orchestrator.md`
- **コマンド**: `.claude/commands/collect-finance-news.md`
- **GitHub Project**: https://github.com/users/YH-05/projects/15
