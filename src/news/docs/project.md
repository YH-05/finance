# news プロジェクト

## 概要

**汎用ニュース収集パッケージ** - 複数のデータソースからニュースを取得し、様々な出力先に保存する。

### 解決する課題

- 複数のニュースソースを統一的に扱いたい
  - python yfinanceで取得できるマーケット・セクター・個別銘柄のニュース
  - webスクレイピングで取得した記事など
- 出力先（ファイル、GitHub Issue、レポート用データ）を柔軟に切り替えたい
  - GitHub ProjectにIssueとしてニュースを投稿したい
  - 日次のニュース収集や週次のレポート作成に役立てたい
- 対象カテゴリ（金融、テクノロジー等）を設定可能にしたい
  - 情報ソースとカテゴリごとに取得方法を定める
- 収集したニュースをAIに翻訳・要約・タグ付けなどをしてもらいたい
  - 情報収集まではpythonの自動化スクリプトで行い、ニュースの解釈をAIに任せる
  - 情報収集をpythonで自動化することにより、AIの無駄なコンテキスト消費を抑える狙い
 
### MCPサーバーやスキルとの使い分け
- tavily mcpサーバーやgemini searchスキル、web searchを使用した検索は、AIが動的にweb検索を行うためのツール
- それに対し、newsパッケージが提供するものは、あらかじめ定めたニュースソースからの情報収集自動化機能(AIに情報を渡すところまで)である
- またrss mcpサーバー(financeプロジェクトで作成しているsrc/rssのこと)はRSSフィード取得に特化しているが、newsパッケージはRSSフィードを取り扱わない

### 設計方針

- **プラグイン方式**: データソースを抽象化し、新しいソースを容易に追加可能
  - yfinanceからのニュース取得を最優先で実装
- **AI処理統合**: Claude Code エージェントと連携し、要約・分類を自動化
- **rss パッケージと独立**: RSS 以外のソース（API、スクレイピング）に対応

## 主要機能

### Phase 1: 基盤構築

- [ ] データソース抽象化（SourceProtocol）
- [ ] 出力先抽象化（SinkProtocol）
- [ ] 設定管理（SourceConfig, SinkConfig）
- [ ] 基本的なニュース記事モデル（Article）

### Phase 2: データソース実装

- [ ] Web API ソース（NewsAPI, Tavily 等）
- [ ] Web スクレイピングソース
  - [ ] 汎用スクレイパー基盤（BeautifulSoup/lxml）
  - [ ] サイト別パーサー設定（CSS セレクタ、XPath）
  - [ ] ページネーション対応
  - [ ] レート制限・礼儀正しいクローリング
- [ ] ソース設定ファイル（YAML/JSON）

### Phase 3: 出力先実装

- [ ] ファイル出力（JSON, Parquet）
- [ ] GitHub Issue/Project 出力
- [ ] 週次レポート用データ出力

### Phase 4: 運用機能

- [ ] 重複チェック機構
- [ ] 取得履歴管理
- [ ] エラーハンドリング・リトライ

### Phase 5: AIエージェント連携

- [ ] ProcessorProtocol（AI処理の抽象化）
- [ ] 要約生成プロセッサ
  - [ ] Claude Code エージェントへの記事データ受け渡し
  - [ ] 日本語要約の生成・保存
- [ ] 分類・タグ付けプロセッサ
  - [ ] カテゴリ自動分類（金融、テクノロジー等）
  - [ ] キーワード・エンティティ抽出
- [ ] パイプライン実行
  - [ ] 収集 → 処理 → 出力の一連のフロー
  - [ ] バッチ処理・並列実行対応

## アーキテクチャ

```
news/
├── core/
│   ├── article.py      # Article モデル（共通データ構造）
│   ├── source.py       # SourceProtocol（データソース抽象化）
│   ├── sink.py         # SinkProtocol（出力先抽象化）
│   └── processor.py    # ProcessorProtocol（AI処理抽象化）
├── sources/
│   ├── api/            # API ソース実装
│   │   ├── newsapi.py
│   │   └── tavily.py
│   └── scraper/        # スクレイピングソース実装
│       ├── base.py     # 汎用スクレイパー基盤
│       ├── parser.py   # サイト別パーサー設定
│       └── sites/      # サイト固有の実装
├── processors/         # AI処理実装
│   ├── summarizer.py   # 要約生成（Claude連携）
│   ├── classifier.py   # 分類・タグ付け
│   └── pipeline.py     # 処理パイプライン
├── sinks/
│   ├── file.py         # ファイル出力（JSON, Parquet）
│   ├── github.py       # GitHub Issue/Project 出力
│   └── report.py       # 週次レポート用出力
├── config/
│   └── loader.py       # 設定ファイル読み込み
└── collector.py        # メインコレクター（オーケストレーション）
```

## 技術的考慮事項

### 依存関係

| パッケージ | 用途 |
|-----------|------|
| `httpx` | HTTP クライアント（API 呼び出し） |
| `pydantic` | 設定・モデル定義 |
| `beautifulsoup4` | Web スクレイピング |
| `lxml` | 高速 HTML/XML パーサー |
| `anthropic` | Claude API（AI処理） |

### 既存パッケージとの関係

| パッケージ | 関係 |
|-----------|------|
| `rss` | **独立** - RSS フィードは rss パッケージが担当 |
| `analyze` | **連携可能** - 収集後の分析処理を委譲 |
| `database` | **利用** - ロギング、ユーティリティを利用 |

### 設定ファイル形式

```yaml
# data/config/news_sources.yaml
sources:
  - type: newsapi
    api_key: ${NEWS_API_KEY}
    categories: [business, technology]
    countries: [us, jp]

  - type: tavily
    api_key: ${TAVILY_API_KEY}
    topics: [AI, finance]

  - type: scraper
    name: example_news_site
    base_url: https://example.com/news
    selectors:
      article_list: "div.article-list > article"
      title: "h2.title"
      link: "a.article-link"
      date: "time.published"
      summary: "p.excerpt"
    rate_limit: 1.0  # 秒間リクエスト数
    pagination:
      type: page_number  # page_number | load_more | infinite_scroll
      max_pages: 5

processors:
  - type: summarizer
    model: claude-3-haiku-20240307
    language: ja
    max_length: 200

  - type: classifier
    categories: [金融, テクノロジー, 経済, 政治]
    extract_keywords: true

sinks:
  - type: file
    format: json
    path: data/raw/news/

  - type: github
    project: 15
    labels: [news]
```

## 成功基準

1. **拡張性**: 新しいデータソースを 1 ファイル追加で対応可能
2. **設定駆動**: コード変更なしで取得対象・出力先を変更可能
3. **信頼性**: 重複なし、エラー時のリトライ、取得履歴管理
4. **テスト**: 各コンポーネントのカバレッジ 80% 以上

## 非スコープ

- センチメント分析（→ analyze パッケージ）
- RSS フィード対応（→ rss パッケージ）
- リアルタイム配信（バッチ処理のみ）
- JavaScript 必須サイトのスクレイピング（Playwright 等は対象外）

---

> 次のステップ: `/issue @src/news/docs/project.md` で Issue を作成し、`feature-implementer` で TDD 実装
