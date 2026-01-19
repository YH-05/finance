# finance-news-collector 処理時間改善プラン

## 問題

`finance-news-orchestrator` の処理時間が長い（推定54-148秒）

### 根本原因

オーケストレーターが全RSSフィード（21+件）を**逐次処理**している：
1. Phase 1.5: CNBCフィードのフェッチ（最大21回のMCP呼び出し）
2. Phase 2: 各フィードから記事取得（10-20回のMCP呼び出し）

## 解決策

**各サブエージェントに担当フィードを直接割り当て、オーケストレーターからRSS処理を削除**

### 改善後のアーキテクチャ

```
オーケストレーター（軽量化）
├── 既存Issue取得のみ（gh issue list）
└── 設定配布
    ↓
サブエージェント5つが完全並列実行
├── 自分の担当フィードをフェッチ・取得
├── キーワードフィルタリング
└── Issue作成
```

### 推定処理時間

| 項目 | 現状 | 改善後 |
|------|------|--------|
| オーケストレーター | 54-148秒 | 2-5秒 |
| サブエージェント（並列） | フィルタリングのみ | 各3-10秒 |
| **合計** | **54-148秒** | **5-15秒** |

## フィード割り当て

| エージェント | 担当フィード | feed_id |
|-------------|-------------|---------|
| **index** | Markets, Investing | `c04`, `c05` |
| **stock** | Earnings, Business | `c12`, `c11` |
| **ai** | Technology + TechCrunch + Ars Technica + The Verge + Hacker News | `c08`, `af717f84`, `338f1076`, `69722878`, `4dc65edc` |
| **sector** | Health Care, Real Estate, Autos, Energy, Media, Retail | `c14`, `c15`, `c17`, `c18`, `c19`, `c20` |
| **macro** | Economy, Finance, Top News, World News, US News, Asia, Europe, FRB, IMF | `c06`, `c07`, `c01`, `c02`, `c03`, `c09`, `c10`, `a1fd6bfd`, `c4cb2750` |

※ `c01`〜`c21` は `b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4{c01-c21}` の略記

## 変更対象ファイル

### 1. オーケストレーター（大幅削減）
- `.claude/agents/finance-news-orchestrator.md`
  - Phase 1.5（CNBCフェッチ）を削除
  - Phase 2 ステップ2.1（RSS取得）を削除
  - 既存Issue取得とセッション管理のみに簡素化

### 2. サブエージェント（5ファイル）
各ファイルに以下を追加：

| ファイル | 変更内容 |
|---------|---------|
| `.claude/agents/finance-news-index.md` | MCPツール追加、フィード直接取得処理 |
| `.claude/agents/finance-news-stock.md` | 同上 |
| `.claude/agents/finance-news-ai.md` | 同上 |
| `.claude/agents/finance-news-sector.md` | 同上 |
| `.claude/agents/finance-news-macro.md` | 同上 |

### 3. 共通処理ガイド（更新）
- `.claude/agents/finance_news_collector/common-processing-guide.md`
  - フィード直接取得パターンを追加

## 具体的な変更内容

### オーケストレーター変更

```yaml
# 削除するtools
- mcp__rss__fetch_feed
- mcp__rss__get_items

# 残すtools
- Read
- Write
- Bash
- MCPSearch
- mcp__rss__list_feeds  # フィード一覧確認用（オプション）
```

### サブエージェント変更（例：finance-news-index.md）

```yaml
# 追加するtools
tools:
  - Read
  - Bash
  - MCPSearch           # 追加
  - mcp__rss__fetch_feed  # 追加
  - mcp__rss__get_items   # 追加

# 追加するフィード設定
担当フィード:
  - feed_id: "b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c04"
    title: "CNBC - Markets"
  - feed_id: "b1a2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c05"
    title: "CNBC - Investing"
```

### 新しい処理フロー（サブエージェント）

```
Phase 1: 初期化
├── MCPツールロード（MCPSearch）
├── 設定読み込み
└── 既存Issue取得（gh issue list --label "news"）

Phase 2: RSS取得（新規追加）
├── 担当フィードをフェッチ（mcp__rss__fetch_feed）
└── 記事を取得（mcp__rss__get_items）

Phase 3: フィルタリング
├── キーワードマッチング
├── 除外キーワードチェック
└── 重複チェック

Phase 4: GitHub投稿
├── Issue作成
├── Project追加
├── Status設定
└── 公開日時設定

Phase 5: 結果報告
```

## 検証方法

1. **処理時間計測**
   ```bash
   time claude "/collect-finance-news"
   ```

2. **期待結果**
   - 改善前: 54-148秒
   - 改善後: 5-15秒（10倍以上の高速化）

3. **機能確認**
   - 各テーマのIssueが正しく作成されること
   - GitHub Project 15にStatusが正しく設定されること
   - 重複チェックが機能すること

## リスクと対策

| リスク | 対策 |
|--------|------|
| MCPツール接続失敗 | 各エージェントにローカルフォールバック実装済み |
| フィード重複取得 | 各エージェントの担当フィードを明確に分離 |
| 既存Issue重複チェック漏れ | 各エージェントが個別にgh issue listを実行 |

## 実装順序

1. オーケストレーターからRSS処理を削除
2. 各サブエージェントにMCPツールとフィード設定を追加
3. 共通処理ガイドを更新
4. 動作検証
