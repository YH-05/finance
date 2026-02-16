# notebooklm

Google NotebookLM ブラウザ自動化 MCP サーバーパッケージ

## 概要

Playwright を使用して Google NotebookLM の Web UI を自動操作し、27個の MCP ツールを Claude Code に提供するパッケージです。ノートブック管理、ソース管理、AI チャット、Audio Overview 生成、Studio コンテンツ生成、メモ管理、バッチ処理をプログラマティックに実行できます。

**主な機能:**

- ノートブック CRUD 操作（作成・一覧・サマリー取得・削除）
- ソース管理（テキスト・URL・ファイルアップロード・Web リサーチ）
- AI チャット（質問応答・履歴管理・設定・メモ保存）
- Audio Overview 生成（ポッドキャスト形式の音声要約）
- Studio コンテンツ生成（レポート・インフォグラフィック・スライド・データテーブル）
- メモ管理（作成・一覧・取得・削除）
- バッチ処理（複数ソース追加・複数質問・リサーチワークフロー）
- セッション永続化（Cookie 保存による自動再ログイン）
- Stealth ブラウザ設定（ボット検出回避）

**現在のバージョン:** 0.1.0

## インストール

```bash
# リポジトリ全体の依存関係をインストール
uv sync --all-extras

# Playwright ブラウザをインストール
playwright install chromium
```

### 必要な依存関係

| パッケージ | 用途 | 最小バージョン |
|-----------|------|---------------|
| `playwright` | ブラウザ自動化 | - |
| `fastmcp` | MCP サーバーフレームワーク | - |
| `pydantic` | データモデル定義 | v2 |

## MCP サーバー起動方法

### 方法 1: コマンドラインから直接起動

```bash
notebooklm-mcp
```

### 方法 2: Claude Code に追加

```bash
claude mcp add notebooklm -- uvx notebooklm-mcp
```

### 方法 3: `.mcp.json` で設定

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uvx",
      "args": ["notebooklm-mcp"]
    }
  }
}
```

## 認証フロー

NotebookLM は Google アカウントでの認証が必要です。セッション管理は以下のフローで動作します。

### 初回起動

1. MCP サーバーが起動し、Playwright ブラウザが **headed モード**（GUI 表示）で起動
2. Google ログインページが表示される
3. ユーザーが手動でログインを完了（最大5分間待機）
4. ログイン成功後、セッション情報（Cookie）が `.notebooklm-session.json` に保存される

### 2回目以降

1. MCP サーバーが起動し、保存されたセッションファイルを検出
2. セッションの有効性を検証（NotebookLM にアクセスし、ログインリダイレクトが発生しないことを確認）
3. 有効な場合は **headless モード**（バックグラウンド）で自動操作を開始
4. セッション期限切れの場合は headed モードに切り替えて再ログインを要求

### セッションファイル

- **パス**: `.notebooklm-session.json`（プロジェクトルート）
- **内容**: Playwright `storage_state()`による Cookie とローカルストレージの保存
- **セキュリティ**: `.gitignore` に追加済み（リポジトリに含まれない）

## MCP ツール一覧（全27ツール）

### Notebook 管理ツール（4ツール）

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `notebooklm_create_notebook` | 新しいノートブックを作成 | `title: str` |
| `notebooklm_list_notebooks` | 全ノートブックを一覧表示 | なし |
| `notebooklm_get_notebook_summary` | AI 生成サマリーを取得 | `notebook_id: str` |
| `notebooklm_delete_notebook` | ノートブックを削除 | `notebook_id: str` |

### Source 管理ツール（9ツール）

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `notebooklm_add_text_source` | テキストをソースとして追加 | `notebook_id: str`, `text: str`, `title?: str` |
| `notebooklm_list_sources` | ノートブック内のソース一覧 | `notebook_id: str` |
| `notebooklm_add_url_source` | URL をソースとして追加 | `notebook_id: str`, `url: str` |
| `notebooklm_add_file_source` | ファイルをソースとして追加 | `notebook_id: str`, `file_path: str` |
| `notebooklm_get_source_details` | ソースの詳細情報を取得 | `notebook_id: str`, `source_index: int` |
| `notebooklm_delete_source` | ソースを削除 | `notebook_id: str`, `source_index: int` |
| `notebooklm_rename_source` | ソースの名前を変更 | `notebook_id: str`, `source_index: int`, `new_name: str` |
| `notebooklm_toggle_source_selection` | ソースの選択/解除を切替 | `notebook_id: str`, `source_index?: int`, `select_all?: bool` |
| `notebooklm_web_research` | Web リサーチでソースを発見・追加 | `notebook_id: str`, `query: str`, `mode?: "fast" \| "deep"` |

### Chat ツール（5ツール）

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `notebooklm_chat` | AI に質問して回答を取得 | `notebook_id: str`, `question: str` |
| `notebooklm_get_chat_history` | チャット履歴を取得 | `notebook_id: str` |
| `notebooklm_clear_chat_history` | チャット履歴をクリア | `notebook_id: str` |
| `notebooklm_configure_chat` | チャット設定（システムプロンプト）を変更 | `notebook_id: str`, `system_prompt: str` |
| `notebooklm_save_chat_to_note` | 質問して回答をメモに保存 | `notebook_id: str`, `question: str` |

### Audio ツール（1ツール）

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `notebooklm_generate_audio_overview` | Audio Overview（ポッドキャスト）を生成 | `notebook_id: str`, `customize_prompt?: str` |

### Studio ツール（1ツール）

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `notebooklm_generate_studio_content` | Studio コンテンツを生成 | `notebook_id: str`, `content_type: StudioContentType`, `report_format?: ReportFormat` |

**StudioContentType**: `"report"` | `"infographic"` | `"slides"` | `"data_table"` | `"flashcards"` | `"quiz"` | `"mind_map"` | `"video_explainer"` | `"memo"`

**ReportFormat** (content_type が `"report"` の場合のみ): `"custom"` | `"briefing_doc"` | `"study_guide"` | `"blog_post"`

### Note 管理ツール（4ツール）

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `notebooklm_create_note` | 新しいメモを作成 | `notebook_id: str`, `content: str`, `title?: str` |
| `notebooklm_list_notes` | ノートブック内のメモ一覧 | `notebook_id: str` |
| `notebooklm_get_note` | メモの全文を取得 | `notebook_id: str`, `note_index: int` |
| `notebooklm_delete_note` | メモを削除 | `notebook_id: str`, `note_index: int` |

### Batch & Workflow ツール（3ツール）

| ツール名 | 説明 | パラメータ |
|---------|------|-----------|
| `notebooklm_batch_add_sources` | 複数ソースを順次追加 | `notebook_id: str`, `sources: list[dict]` |
| `notebooklm_batch_chat` | 複数質問を順次送信 | `notebook_id: str`, `questions: list[str]` |
| `notebooklm_workflow_research` | リサーチワークフローを実行 | `notebook_id: str`, `sources: list[dict]`, `questions: list[str]`, `content_type?: StudioContentType` |

## ディレクトリ構成

```
notebooklm/
├── __init__.py              # 公開 API 定義
├── types.py                 # Pydantic v2 データモデル（15モデル + 4型エイリアス）
├── errors.py                # 例外階層（8種類）
├── constants.py             # 定数定義（URL、タイムアウト、Stealth 設定）
├── selectors.py             # CSS セレクター管理（SelectorManager + 50+ セレクター）
├── browser/                 # ブラウザ自動化レイヤー
│   ├── __init__.py
│   ├── manager.py           # NotebookLMBrowserManager（ライフサイクル管理）
│   └── helpers.py           # ページ操作ヘルパー関数
├── services/                # ドメインサービスレイヤー
│   ├── __init__.py
│   ├── notebook.py          # NotebookService（CRUD 操作）
│   ├── source.py            # SourceService（ソース管理 + Web リサーチ）
│   ├── chat.py              # ChatService（AI チャット操作）
│   ├── audio.py             # AudioService（Audio Overview 生成）
│   ├── studio.py            # StudioService（Studio コンテンツ生成）
│   ├── note.py              # NoteService（メモ管理）
│   └── batch.py             # BatchService（バッチ処理 + ワークフロー）
└── mcp/                     # MCP ツールレイヤー
    ├── __init__.py
    ├── server.py            # FastMCP サーバー（lifespan + ツール登録）
    └── tools/               # 機能別ツールモジュール
        ├── __init__.py
        ├── notebook_tools.py   # Notebook 管理ツール（4ツール）
        ├── source_tools.py     # Source 管理ツール（9ツール）
        ├── chat_tools.py       # Chat ツール（5ツール）
        ├── audio_tools.py      # Audio ツール（1ツール）
        ├── studio_tools.py     # Studio ツール（1ツール）
        ├── note_tools.py       # Note 管理ツール（4ツール）
        └── batch_tools.py      # Batch & Workflow ツール（3ツール）
```

## アーキテクチャ

3層構造で設計されています。

```
MCP ツールレイヤー (mcp/)
    ↓ FastMCP @mcp.tool() デコレータ
ドメインサービスレイヤー (services/)
    ↓ Playwright ページ操作
ブラウザ自動化レイヤー (browser/)
    ↓ Playwright API
Google NotebookLM Web UI
```

### MCP ツールレイヤー

FastMCP サーバーが lifespan コンテキストで `NotebookLMBrowserManager` を管理し、各ツール関数が `ctx.lifespan_context["browser_manager"]` 経由でブラウザにアクセスします。エラーは全て `dict` 形式で返却されます。

### ドメインサービスレイヤー

7つのサービスクラスがビジネスロジックを実装します。

| サービス | 説明 |
|---------|------|
| `NotebookService` | ノートブック CRUD 操作 |
| `SourceService` | ソース追加・削除・リネーム・Web リサーチ |
| `ChatService` | AI チャット・履歴・設定管理 |
| `AudioService` | Audio Overview（ポッドキャスト）生成 |
| `StudioService` | Studio コンテンツ（レポート等）生成 |
| `NoteService` | メモ CRUD 操作 |
| `BatchService` | バッチ処理・リサーチワークフロー |

### ブラウザ自動化レイヤー

`NotebookLMBrowserManager` が Playwright ブラウザのライフサイクルを管理します。

- Stealth 設定（User-Agent、WebGL、navigator.webdriver 偽装）
- セッション永続化（`storage_state()` による Cookie 保存/復元）
- Headed/Headless モード切替

## 公開 API

```python
from notebooklm import (
    # サービスクラス
    NotebookService,
    SourceService,
    ChatService,

    # ブラウザ管理
    NotebookLMBrowserManager,

    # セレクター管理
    SelectorManager,
)
```

### データモデル（types.py）

```python
from notebooklm.types import (
    # Notebook
    NotebookInfo,           # ノートブック基本情報
    NotebookSummary,        # AI 生成サマリー

    # Source
    SourceInfo,             # ソース基本情報
    SourceDetails,          # ソース詳細情報

    # Chat
    ChatResponse,           # チャット応答
    ChatHistory,            # チャット履歴

    # Audio
    AudioOverviewResult,    # Audio Overview 生成結果

    # Studio
    StudioContentResult,    # Studio コンテンツ生成結果

    # Note
    NoteInfo,               # メモ基本情報
    NoteContent,            # メモ全文

    # Utility
    SearchResult,           # Web リサーチ結果
    BatchResult,            # バッチ操作結果
    WorkflowResult,         # ワークフロー結果

    # 型エイリアス
    SourceType,             # "text" | "url" | "file" | "google_drive" | "youtube" | "web_research"
    StudioContentType,      # "report" | "infographic" | "slides" | "data_table" | ...
    ReportFormat,           # "custom" | "briefing_doc" | "study_guide" | "blog_post"
    ResearchMode,           # "fast" | "deep"
)
```

### 例外クラス（errors.py）

```python
from notebooklm.errors import (
    NotebookLMError,          # 基底例外
    AuthenticationError,      # 認証エラー
    NavigationError,          # ページ遷移エラー
    ElementNotFoundError,     # UI 要素未検出
    BrowserTimeoutError,      # タイムアウト
    SessionExpiredError,      # セッション期限切れ
    SourceAddError,           # ソース追加エラー
    ChatError,                # チャットエラー
    StudioGenerationError,    # Studio 生成エラー
)
```

## 使用例

### ノートブック操作

```python
from notebooklm import NotebookService, NotebookLMBrowserManager

async with NotebookLMBrowserManager(headless=False) as manager:
    service = NotebookService(manager)

    # ノートブック作成
    notebook = await service.create_notebook("AI Research Notes")

    # 一覧取得
    notebooks = await service.list_notebooks()

    # サマリー取得
    summary = await service.get_notebook_summary(notebook.notebook_id)

    # 削除
    await service.delete_notebook(notebook.notebook_id)
```

### ソース管理

```python
from notebooklm import SourceService, NotebookLMBrowserManager

async with NotebookLMBrowserManager() as manager:
    service = SourceService(manager)
    notebook_id = "c9354f3f-f55b-4f90-a5c4-219e582945cf"

    # テキストソース追加
    source = await service.add_text_source(
        notebook_id=notebook_id,
        text="AI market analysis report...",
        title="Q4 2025 Analysis",
    )

    # URL ソース追加
    url_source = await service.add_url_source(
        notebook_id=notebook_id,
        url="https://example.com/research-paper.pdf",
    )

    # ソース一覧
    sources = await service.list_sources(notebook_id)

    # Web リサーチ（Fast）
    results = await service.web_research(
        notebook_id=notebook_id,
        query="AI investment trends 2026",
        mode="fast",
    )
```

### AI チャット

```python
from notebooklm import ChatService, NotebookLMBrowserManager

async with NotebookLMBrowserManager() as manager:
    service = ChatService(manager)
    notebook_id = "c9354f3f-f55b-4f90-a5c4-219e582945cf"

    # 質問して回答を取得
    response = await service.chat(
        notebook_id,
        "What are the key findings from the research?",
    )
    print(response.answer)
    print(response.citations)

    # チャット履歴取得
    history = await service.get_chat_history(notebook_id)

    # システムプロンプト設定
    await service.configure_chat(
        notebook_id,
        "Answer in Japanese. Focus on quantitative data.",
    )
```

## タイムアウト設定

長時間操作には個別のタイムアウトが設定されています。

| 操作 | タイムアウト | 説明 |
|------|------------|------|
| ページ遷移 | 30秒 | `page.goto()` のタイムアウト |
| UI 要素待機 | 10秒 | `wait_for_selector()` のタイムアウト |
| チャット応答 | 60秒 | AI 回答生成の待機時間 |
| ソース追加 | 60秒 | ソース処理の待機時間 |
| ファイルアップロード | 2分 | 大容量ファイルの処理時間 |
| 手動ログイン待機 | 5分 | 初回 Google ログインの待機時間 |
| Audio Overview | 10分 | ポッドキャスト生成時間 |
| Studio コンテンツ | 10分 | レポート・スライド等の生成時間 |
| Deep Research | 30分 | 5段階リサーチプロセスの実行時間 |

## CSS セレクター管理

UI 要素の特定には `SelectorManager` による優先度ベースのフォールバックが使用されます。

### フォールバック優先順位

| 優先度 | 方法 | 安定性 | 説明 |
|--------|------|--------|------|
| 1 | `aria-label` | 高 | アクセシビリティ属性ベース |
| 2 | `placeholder` | 中 | 入力フィールド用 |
| 3 | `role+text` | 中 | セマンティック HTML |
| 10+ | `ref` 属性 | 低 | UI 更新で頻繁に変更 |

```python
from notebooklm.selectors import SelectorManager

manager = SelectorManager()

# チャット送信ボタンのセレクター候補を取得（優先度順）
candidates = manager.get_candidates("chat_send_button")
for c in candidates:
    print(f"[{c.priority}] {c.method}: {c.selector}")

# カテゴリ別にグループ取得
chat_groups = manager.get_groups_by_category("chat")
```

## 開発ガイド

### テスト実行

```bash
# 全テスト実行
make test

# カバレッジ付きテスト
make test-cov

# notebooklm パッケージのテストのみ
uv run pytest tests/notebooklm/ -v
```

### 品質チェック

```bash
# 全チェック実行
make check-all

# フォーマット
make format

# リント
make lint

# 型チェック
make typecheck
```

### 拡張方法

1. **新しいサービス追加**: `services/` にクラスを作成し、`services/__init__.py` でエクスポート
2. **新しい MCP ツール追加**: `mcp/tools/` にモジュールを作成し、`mcp/server.py` で登録
3. **セレクター追加**: `selectors.py` のビルダー関数に `SelectorGroup` を追加
4. **データモデル追加**: `types.py` に Pydantic モデルを追加
5. **例外追加**: `errors.py` に `NotebookLMError` のサブクラスを追加

## 関連ドキュメント

- `docs/project/project-48/project.md` - プロジェクト計画書
- `src/rss/mcp/server.py` - 参考: RSS MCP サーバー実装
- `template/src/template_package/README.md` - テンプレート README

## 更新履歴

このREADME.mdは、MCP ツールの追加・変更、認証フローの変更、アーキテクチャ変更があった場合に更新してください。
