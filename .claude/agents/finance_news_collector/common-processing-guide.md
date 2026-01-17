# 金融ニュース収集エージェント共通処理ガイド

このガイドは、テーマ別ニュース収集エージェント（finance-news-{theme}）の共通処理を定義します。

## 共通設定ファイル

- **テーマ設定**: `data/config/finance-news-themes.json`
- **Issueテンプレート**: `.github/ISSUE_TEMPLATE/news-article.yml`
- **GitHub Project**: #15 (`PVT_kwHOBoK6AM4BMpw_`)
- **Statusフィールド**: `PVTSSF_lAHOBoK6AM4BMpw_zg739ZE`

## Phase 1: 初期化

### ステップ1.1: 一時ファイル読み込み

```
[1] 一時ファイル読み込み
    ↓
    .tmp/news-collection-{timestamp}.json を読み込む
    ↓ エラーの場合
    エラーログ出力 → 処理中断

[2] テーマ設定読み込み
    ↓
    data/config/finance-news-themes.json を読み込む
    themes["{theme}"] セクションを取得
    ↓ エラーの場合
    エラーログ出力 → 処理中断

[3] 統計カウンタ初期化
    ↓
    processed = 0
    matched = 0
    excluded = 0
    duplicates = 0
    created = 0
    failed = 0
```

## Phase 2: フィルタリング

### ステップ2.1: テーマキーワードマッチング

```python
def matches_theme_keywords(item: dict, theme: dict) -> tuple[bool, list[str]]:
    """テーマのキーワードにマッチするかチェック"""

    # 検索対象テキスト
    text = f"{item['title']} {item.get('summary', '')} {item.get('content', '')}".lower()

    # キーワードマッチング（単語境界認識）
    matched_keywords = []
    for keyword in theme['keywords']['include']:
        # 単語境界パターン（\b）を使用
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            matched_keywords.append(keyword)

    # 最低マッチ数チェック
    min_matches = theme['min_keyword_matches']
    is_match = len(matched_keywords) >= min_matches

    return is_match, matched_keywords
```

### ステップ2.2: 除外キーワードチェック

```python
def is_excluded(item: dict, common: dict, theme: dict) -> bool:
    """除外対象かチェック"""

    text = f"{item['title']} {item.get('summary', '')}".lower()

    # 除外キーワードチェック
    for category, keywords in common['exclude_keywords'].items():
        for keyword in keywords:
            if keyword.lower() in text:
                # 金融キーワードも含む場合は除外しない
                is_match, _ = matches_theme_keywords(item, theme)
                if not is_match:
                    return True

    return False
```

### ステップ2.3: 信頼性スコアリング

```python
def calculate_reliability_score(item: dict, theme: dict, common: dict) -> int:
    """信頼性スコアを計算（0-100）"""

    link = item.get('link', '')

    # Tier判定（情報源の信頼性）
    tier = 1
    for domain in common['sources']['tier1']:
        if domain in link:
            tier = 3
            break
    if tier == 1:
        for domain in common['sources']['tier2']:
            if domain in link:
                tier = 2
                break

    # キーワードマッチ度
    text = f"{item['title']} {item.get('summary', '')} {item.get('content', '')}".lower()
    keyword_matches = sum(1 for kw in theme['keywords']['include'] if kw.lower() in text)
    keyword_ratio = min(keyword_matches / 10, 1.0)

    # Priority boost（重要キーワードボーナス）
    boost = 1.0
    for priority_kw in theme['keywords']['priority_boost']:
        if priority_kw.lower() in item['title'].lower():
            boost = 1.5
            break

    # Reliability weight（テーマ別ウェイト）
    weight = theme.get('reliability_weight', 1.0)

    # スコア計算
    score = tier * keyword_ratio * boost * weight * 100

    return min(int(score), 100)
```

### ステップ2.4: 重複チェック

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

## Phase 3: GitHub投稿

### ステップ3.0: 記事内容取得と要約生成

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


def format_published_jst(published_str: str) -> str:
    """公開日をJST YYYY-MM-DD HH:MM形式に変換"""

    from datetime import datetime
    import pytz

    dt = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = dt.astimezone(jst)

    return dt_jst.strftime('%Y-%m-%d %H:%M')
```

### ステップ3.1: Issue作成

**Issueテンプレート** (`.github/ISSUE_TEMPLATE/news-article.yml`) に準拠した形式で作成:

```bash
gh issue create \
    --repo YH-05/finance \
    --title "[NEWS] {title}" \
    --body "$(cat <<'EOF'
### 概要

{japanese_summary}

### 情報源URL

{link}

### 公開日

{published_jst}(JST)

### 信頼性スコア

{credibility_score}点

### カテゴリ

{category}

### フィード/情報源名

{source}

### 優先度

{priority}

### 備考・メモ

- テーマ: {theme_name}
- マッチキーワード: {matched_keywords}
- 信頼性: {score}/100
EOF
)" \
    --label "news"
```

### ステップ3.2: Project追加

```bash
gh project item-add 15 \
    --owner YH-05 \
    --url {issue_url}
```

### ステップ3.3: Status設定（GraphQL API）

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

## Phase 4: 結果報告

### 統計サマリー出力フォーマット

```markdown
## {theme_name} ニュース収集完了

### 処理統計
- **処理記事数**: {processed}件
- **テーママッチ**: {matched}件
- **除外**: {excluded}件
- **重複**: {duplicates}件
- **新規投稿**: {created}件
- **投稿失敗**: {failed}件

### 投稿されたニュース

1. **{title}** [#{issue_number}]
   - ソース: {source}
   - 信頼性: {score}/100
   - URL: https://github.com/YH-05/finance/issues/{issue_number}

### 除外されたニュース
- スポーツ関連: {sports_count}件
- エンタメ関連: {entertainment_count}件
- テーマ不一致: {mismatch_count}件
```

## 共通エラーハンドリング

### E001: 一時ファイル読み込みエラー

```python
try:
    with open(filepath) as f:
        data = json.load(f)
except FileNotFoundError:
    ログ出力: f"エラー: 一時ファイルが見つかりません: {filepath}"
    ログ出力: "オーケストレーターが正しく実行されたか確認してください"
    sys.exit(1)
except json.JSONDecodeError as e:
    ログ出力: f"エラー: JSON形式が不正です: {e}"
    sys.exit(1)
```

### E002: テーマ設定読み込みエラー

```python
try:
    with open("data/config/finance-news-themes.json") as f:
        config = json.load(f)
    theme = config['themes']['{theme}']
    common = config['common']
except FileNotFoundError:
    ログ出力: "エラー: テーマ設定ファイルが見つかりません"
    sys.exit(1)
except KeyError:
    ログ出力: "エラー: '{theme}' テーマが定義されていません"
    sys.exit(1)
```

### E003: Issue作成エラー

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

### E004: Status設定エラー

```python
try:
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={mutation}"],
        capture_output=True,
        text=True,
        check=True
    )
except subprocess.CalledProcessError as e:
    ログ出力: f"警告: Status設定失敗: Issue #{issue_number}"
    ログ出力: f"エラー詳細: {e.stderr}"
    ログ出力: "Issue作成は成功しています。手動でStatusを設定してください。"
    continue
```

### E005: ネットワークエラー

- リトライロジック（最大3回、指数バックオフ）
- エラーログ記録
- 処理継続（失敗した記事をスキップ）

## テーマ別Status ID一覧

| テーマ | Status名 | Option ID |
|--------|----------|-----------|
| index | Index | `f75ad846` |
| stock | Stock | `47fc9ee4` |
| sector | Sector | `98236657` |
| macro | Macro | `c40731f6` |
| ai | AI | `17189c86` |

## 参考資料

- **テーマ設定**: `data/config/finance-news-themes.json`
- **Issueテンプレート**: `.github/ISSUE_TEMPLATE/news-article.yml`
- **オーケストレーター**: `.claude/agents/finance-news-orchestrator.md`
- **コマンド**: `.claude/commands/collect-finance-news.md`
- **GitHub Project**: https://github.com/users/YH-05/projects/15
