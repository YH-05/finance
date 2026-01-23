# 金融ニュース収集エージェント共通処理ガイド

このガイドは、テーマ別ニュース収集エージェント（finance-news-{theme}）の共通処理を定義します。

## 🚨 最重要: 入力データ検証（Phase 0）

> **参照**: `.claude/rules/subagent-data-passing.md`

サブエージェントが処理を開始する前に、**入力データの完全性を必ず検証**すること。

### 必須フィールドチェック

```python
def validate_article_data(article: dict) -> tuple[bool, str]:
    """記事データの必須フィールドを検証する

    Parameters
    ----------
    article : dict
        検証対象の記事データ

    Returns
    -------
    tuple[bool, str]
        (検証成功, エラーメッセージ)
    """

    required_fields = ["title", "link", "published", "summary"]

    for field in required_fields:
        if field not in article or not article[field]:
            return False, f"必須フィールド '{field}' がありません"

    # URLの形式チェック
    if not article["link"].startswith(("http://", "https://")):
        return False, f"無効なURL形式: {article['link']}"

    return True, ""


def validate_input_data(data: dict) -> tuple[bool, list[str]]:
    """入力データ全体を検証する

    Parameters
    ----------
    data : dict
        プロンプトまたは一時ファイルから受け取ったデータ

    Returns
    -------
    tuple[bool, list[str]]
        (検証成功, エラーメッセージのリスト)
    """

    errors = []

    # 1. rss_items または articles の存在確認
    articles = data.get("rss_items") or data.get("articles") or []
    if not articles:
        errors.append("記事データが空です")
        return False, errors

    # 2. 各記事の必須フィールド検証
    for i, article in enumerate(articles):
        valid, msg = validate_article_data(article)
        if not valid:
            errors.append(f"記事[{i}]: {msg}")

    # 3. 簡略化データの検出（警告）
    if isinstance(articles[0], str):
        errors.append("データが文字列形式です。JSON形式の完全なデータが必要です")

    return len(errors) == 0, errors
```

### 検証失敗時の対応

```python
# Phase 0: 入力データ検証
valid, errors = validate_input_data(input_data)

if not valid:
    # エラー報告して処理中断
    error_report = "\n".join([f"  - {e}" for e in errors])
    print(f"""
## ⛔ 入力データ検証エラー

入力データが不完全なため処理を中断します。

### 検出されたエラー
{error_report}

### 必要なデータ形式

記事データには以下のフィールドが必須です:
- `title`: 記事タイトル
- `link`: 元記事のURL（**絶対に省略禁止**）
- `published`: 公開日時
- `summary`: 記事要約

### 参照
- `.claude/rules/subagent-data-passing.md`
""")
    # 処理を終了
    return
```

### データ形式の例

**正しい形式**:
```json
{
  "rss_items": [
    {
      "item_id": "60af4cc3-0a47-4cfb-ae89-ed8872209f5d",
      "title": "Trump threatens to sue JPMorgan Chase",
      "link": "https://www.cnbc.com/2026/01/17/trump-jpmorgan-chase-debanking.html",
      "published": "2026-01-18T13:47:50+00:00",
      "summary": "President Trump threatened to sue JPMorgan...",
      "content": null,
      "author": null,
      "fetched_at": "2026-01-18T22:40:08.589493+00:00"
    }
  ],
  "existing_issues": [...]
}
```

**禁止される形式**:
```
# ❌ 簡略化されたリスト形式は絶対禁止
1. "Trump threatens JPMorgan" - 銀行関連
2. "BYD is a buy" - EV関連
```

---

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
processed = 0       # 取得した記事総数
date_filtered = 0   # 公開日時フィルタでスキップされた件数
matched = 0         # テーマにマッチした件数
excluded = 0        # 除外キーワードでスキップされた件数
duplicates = 0      # 重複でスキップされた件数
created = 0         # 新規作成したIssue数
failed = 0          # 作成失敗した件数
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

## Phase 2.5: 公開日時フィルタリング【必須】

**重要**: `--since`オプションで指定された期間内の記事のみを処理対象とします。

### ステップ2.5.1: --sinceパラメータの解析

```python
def parse_since_param(since: str) -> int:
    """--sinceパラメータを日数に変換

    Parameters
    ----------
    since : str
        期間指定（例: "1d", "3d", "7d"）

    Returns
    -------
    int
        日数

    Examples
    --------
    >>> parse_since_param("1d")
    1
    >>> parse_since_param("3d")
    3
    >>> parse_since_param("7d")
    7
    """

    if since.endswith("d"):
        try:
            return int(since[:-1])
        except ValueError:
            pass

    # デフォルト: 1日
    return 1
```

### ステップ2.5.2: 公開日時によるフィルタリング

```python
from datetime import datetime, timedelta, timezone

def filter_by_published_date(
    items: list[dict],
    since_days: int,
) -> tuple[list[dict], int]:
    """公開日時でフィルタリング

    Parameters
    ----------
    items : list[dict]
        RSS記事リスト
    since_days : int
        現在日時から遡る日数

    Returns
    -------
    tuple[list[dict], int]
        (フィルタリング後の記事リスト, 期間外でスキップされた件数)

    Notes
    -----
    - published フィールドは記事の公開日時（RSSのpubDate）
    - published がない場合は fetched_at で代替判定
    - 両方ない場合は処理対象に含める（除外しない）
    """

    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    filtered = []
    skipped = 0

    for item in items:
        # 公開日時を取得（published → fetched_at の順でフォールバック）
        date_str = item.get("published") or item.get("fetched_at")

        if not date_str:
            # 日時情報がない場合は処理対象に含める
            filtered.append(item)
            continue

        try:
            # ISO 8601形式をパース
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

            if dt >= cutoff:
                filtered.append(item)
            else:
                skipped += 1
                ログ出力: f"期間外スキップ: {item.get('title', 'タイトルなし')} (公開: {date_str})"

        except ValueError:
            # パース失敗時は処理対象に含める
            filtered.append(item)

    ログ出力: f"公開日時フィルタ: {len(items)}件 → {len(filtered)}件 (過去{since_days}日以内)"
    return filtered, skipped
```

### ステップ2.5.3: フィルタリング実行

各エージェントはRSS取得後、テーマ判定前に以下を実行:

```python
# --since パラメータをパース（デフォルト: 1d）
since_days = parse_since_param(args.get("since", "1d"))

# 公開日時でフィルタリング
items, date_skipped = filter_by_published_date(items, since_days)

# 統計に記録
stats["date_filtered"] = date_skipped
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

### ステップ4.0: 記事内容取得と要約生成【サブエージェント委譲】

> **🚨 コンテキスト効率化のため、WebFetch処理をサブエージェントに委譲します 🚨**
>
> 記事本文の取得と日本語要約の生成は `news-article-fetcher` サブエージェントが担当します。
> これにより、WebFetch結果（HTML→Markdown本文）がテーマエージェントのコンテキストを圧迫しません。

**重要**: Issue作成前に、必ず `news-article-fetcher` サブエージェントで記事本文を取得して日本語要約を生成すること。

#### 4.0.1: サブエージェント委譲の利点

| 指標 | 従来方式 | サブエージェント方式 |
|-----|---------|-------------------|
| テーマエージェントのコンテキスト | 各記事の本文+要約が蓄積 | URLと結果のみ |
| 要約生成ロジック | 5ファイルに重複 | 1ファイルに集約 |
| 保守性 | 5ファイル同時修正が必要 | 1ファイルのみ修正 |
| 処理の独立性 | 低（WebFetch失敗がエージェント全体に影響） | 高（サブエージェント内で完結） |

#### 4.0.2: サブエージェント呼び出し方式

フィルタリング後の記事リストを `news-article-fetcher` サブエージェントに渡します。

```python
# ステップ4.0.1: フィルタリング済み記事リストを準備
articles_to_fetch = []
for item in filtered_items:
    articles_to_fetch.append({
        "url": item["link"],
        "title": item["title"],
        "summary": item.get("summary", ""),
        "feed_source": item["source_feed"],
        "published": item.get("published", "")
    })

# ステップ4.0.2: news-article-fetcher サブエージェントを呼び出し
fetch_result = Task(
    subagent_type="news-article-fetcher",
    description="記事本文取得と要約生成",
    prompt=f"""以下の記事リストから本文を取得し、日本語要約を生成してください。

入力:
{json.dumps({"articles": articles_to_fetch, "theme": theme_name}, ensure_ascii=False, indent=2)}

出力形式（JSON）:
{{
  "results": [
    {{
      "url": "...",
      "original_title": "...",
      "japanese_title": "...",
      "japanese_summary": "...",
      "success": true
    }}
  ],
  "stats": {{
    "total": N,
    "success": M,
    "failed": K
  }}
}}
""",
    model="haiku"
)

# ステップ4.0.3: 結果を使用
for result in fetch_result["results"]:
    if result["success"]:
        japanese_title = result["japanese_title"]
        japanese_summary = result["japanese_summary"]
        # → Issue作成へ進む
    else:
        ログ出力: f"要約生成失敗: {result['url']}"
        # フォールバック要約を使用（result["japanese_summary"]に警告付き要約が入っている）
```

#### 4.0.3: サブエージェントの戻り値

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `url` | str | 元記事のURL（RSSオリジナル、WebFetchリダイレクト先ではない） |
| `original_title` | str | 元のタイトル（英語の場合あり） |
| `japanese_title` | str | 日本語タイトル（翻訳済み） |
| `japanese_summary` | str | 4セクション構成の日本語要約（400字以上） |
| `success` | bool | 処理成功フラグ |
| `error` | str? | 失敗時のエラーメッセージ（オプション） |

> **🚨 URL設定の重要ルール 🚨**: サブエージェントから返される `url` は、
> RSSオリジナルのlinkをそのまま保持しています。WebFetchでリダイレクトが
> 発生しても、Issue記載のURLはこの値を使用してください。

#### 4.0.4: 要約フォーマット（4セクション構成）

サブエージェントが生成する要約は以下のフォーマットに従います:

```markdown
### 概要
- [主要事実を箇条書きで3行程度]
- [数値データがあれば含める]
- [関連企業があれば含める]

### 背景
[この出来事の背景・経緯を記載。記事に記載がなければ「[記載なし]」]

### 市場への影響
[株式・為替・債券等への影響を記載。記事に記載がなければ「[記載なし]」]

### 今後の見通し
[今後予想される展開・注目点を記載。記事に記載がなければ「[記載なし]」]
```

**重要ルール**:
- 各セクションについて、**記事内に該当する情報がなければ「[記載なし]」と記述**する
- 情報を推測・創作してはいけない
- 記事に明示的に書かれている内容のみを記載する

| セクション | 内容 | 記載なしの例 |
|-----------|------|-------------|
| 概要 | 主要事実、数値データ | （常に何か記載できるはず） |
| 背景 | 経緯、原因、これまでの流れ | 速報で背景説明がない場合 |
| 市場への影響 | 株価・為替・債券への影響 | 影響の言及がない場合 |
| 今後の見通し | 予想、アナリスト見解 | 将来予測の言及がない場合 |

#### 4.0.5: サブエージェントの詳細仕様

サブエージェントの詳細な実装については以下を参照:
`.claude/agents/news-article-fetcher.md`

**サブエージェント内部での処理**:
1. 各記事URLに対してWebFetchで本文取得
2. 4セクション構成の日本語要約を生成
3. 英語タイトルを日本語に翻訳
4. 失敗時はRSS概要を使用したフォールバック要約を生成
5. 結果をJSON形式で一括返却

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

### ステップ4.1.5: URL必須バリデーション【投稿前チェック】

> **🚨 Issue作成前に必ず実行すること 🚨**
>
> URLが存在しない記事は**絶対にIssue作成してはいけません**。

```python
def validate_url_for_issue(item: dict, fetch_result: dict | None = None) -> tuple[bool, str | None]:
    """Issue作成前にURLの存在を検証する

    Parameters
    ----------
    item : dict
        RSSから取得した記事アイテム
    fetch_result : dict | None
        news-article-fetcherの結果（オプション）

    Returns
    -------
    tuple[bool, str | None]
        (検証成功, エラーメッセージ)

    Notes
    -----
    - URLがない記事はIssue作成しない
    - 空文字列もURLなしとして扱う
    """

    url = item.get("link", "").strip()

    if not url:
        return False, f"URLなし: {item.get('title', '不明')}"

    if not url.startswith(("http://", "https://")):
        return False, f"無効なURL形式: {url}"

    return True, None


# 使用例: Phase 4投稿ループ
for item in filtered_items:
    # URL必須バリデーション
    valid, error = validate_url_for_issue(item)
    if not valid:
        ログ出力: f"⛔ スキップ（URL必須違反）: {error}"
        stats["skipped_no_url"] += 1
        continue

    # Issue作成へ進む
    ...
```

**統計に追加するフィールド**:

```python
stats["skipped_no_url"] = 0  # URLなしでスキップした件数
```

**結果報告への追加**:

```markdown
- **URLなしスキップ**: {skipped_no_url}件
```

### ステップ4.2: Issue作成（テンプレート読み込み方式）

**重要: Issueタイトルの日本語化ルール**:
1. **タイトル形式**: `[{theme_ja}] {japanese_title}`
2. **テーマ名プレフィックス（日本語）**:
   - `[株価指数]`, `[個別銘柄]`, `[セクター]`, `[マクロ経済]`, `[AI]`
3. **タイトル翻訳**: 英語記事の場合は日本語に翻訳（要約生成時に同時に実施）

**🚨 URL設定の重要ルール 🚨**:

> **絶対に守ること**: `{{url}}`には**RSSから取得したオリジナルのlink**をそのまま使用すること。
>
> - ✅ 正しい: RSSの`link`フィールドの値をそのまま使用
> - ❌ 間違い: WebFetchのリダイレクト先URL
> - ❌ 間違い: URLを推測・生成する
> - ❌ 間違い: URLを短縮・変換する
>
> URLが存在しない場合は記事をスキップしてください。

```python
def get_article_url(rss_item: dict) -> str | None:
    """RSSアイテムから記事URLを取得する

    Parameters
    ----------
    rss_item : dict
        RSSから取得した記事アイテム

    Returns
    -------
    str | None
        記事のURL（RSSのlinkフィールドの値そのまま）
        linkが存在しない場合はNone

    Notes
    -----
    - linkフィールドの値を一切変換・加工せずにそのまま返す
    - WebFetchで別URLにリダイレクトされても、Issue記載はオリジナルURLを使用
    """

    url = rss_item.get("link")

    if not url:
        ログ出力: f"警告: URLなしの記事をスキップ: {rss_item.get('title', '不明')}"
        return None

    # URLは一切変換せず、そのまま返す
    return url
```

**テンプレート読み込み→プレースホルダー置換**:

```bash
# Step 1: テンプレートを読み込む
template=$(cat .github/ISSUE_TEMPLATE/news-article.md | tail -n +7)  # frontmatter除外

# Step 2: 収集日時を取得（Issue作成直前に実行）
collected_at=$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M')

# Step 3: RSSからオリジナルURLを取得（絶対に変換しない）
# $link はRSSの"link"フィールドから取得した値をそのまま使用
# WebFetchでリダイレクトされても、このURLは変更しない

# Step 4: プレースホルダーを置換
body="${template//\{\{summary\}\}/$japanese_summary}"
body="${body//\{\{url\}\}/$link}"  # ← RSSオリジナルURLをそのまま使用
body="${body//\{\{published_date\}\}/$published_jst(JST)}"
body="${body//\{\{collected_at\}\}/$collected_at(JST)}"
body="${body//\{\{category\}\}/$category}"
body="${body//\{\{feed_source\}\}/$source}"
body="${body//\{\{notes\}\}/- テーマ: $theme_name
- AI判定理由: $判定理由}"

# Step 4: Issue作成（closed状態で作成）
issue_url=$(gh issue create \
    --repo YH-05/finance \
    --title "[{theme_ja}] {japanese_title}" \
    --body "$body" \
    --label "news")

# Issue番号を抽出
issue_number=$(echo "$issue_url" | grep -oE '[0-9]+$')

# Step 5: Issueをcloseする（ニュースIssueはclosed状態で保存）
gh issue close "$issue_number" --repo YH-05/finance
```

**テンプレートプレースホルダー一覧** (`.github/ISSUE_TEMPLATE/news-article.md`):

| プレースホルダー | 説明 | 例 |
|-----------------|------|-----|
| `{{summary}}` | 日本語要約（400字以上） | - |
| `{{url}}` | 情報源URL | `https://...` |
| `{{published_date}}` | 公開日時 | `2026-01-15 10:00(JST)` |
| `{{collected_at}}` | 収集日時 | `2026-01-15 14:30(JST)` |
| `{{category}}` | カテゴリ | `Index（株価指数）` |
| `{{feed_source}}` | フィード名 | `CNBC - Markets` |
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
- **URLなしスキップ**: {skipped_no_url}件
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
| index | Index | `3925acc3` |
| stock | Stock | `f762022e` |
| sector | Sector | `48762504` |
| macro | Macro Economics | `730034a5` |
| ai | AI | `6fbb43d0` |
| finance | Finance | `ac4a91b1` |

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
