# NotebookLM MCP サーバー 実装計画（Playwright ベース）

## Context（背景）

Google NotebookLM を Claude Code から操作可能にする MCP (Model Context Protocol) サーバーを **完全無料** で開発する。Playwright を使用してブラウザを自動操作することで、Google Cloud API や有料ライセンスなしで NotebookLM の全機能にアクセスする。

### プロジェクト目標

1. **完全無料での NotebookLM 操作を実現**
   - API 料金なし、ライセンス料金なし
   - Google TOS 準拠（Web UI の通常利用）
   - NotebookLM の全機能にアクセス可能

2. **Playwright による安定した自動化**
   - ブラウザ自動操作によるノートブック管理
   - データソース（テキスト、URL、ファイル、Google Drive）の追加・削除
   - Audio Overview（ポッドキャスト）とStudio機能の生成
   - AI チャット機能の活用

3. **MCP 統合による Claude Code との連携**
   - 12個の MCP ツールを提供
   - stdio トランスポートによる通信
   - FastMCP フレームワークを使用

---

## Playwright 検証結果

### 検証済み機能（2026-02-16）

| 機能 | ステータス | 詳細 |
|------|-----------|------|
| **ノートブック作成** | ✅ 確認済み | UI 要素: `ref=e78`, `ref=e135` |
| **テキストソース追加** | ✅ 確認済み | UI 要素: `ref=e1842`、プレースホルダー: "ここにテキストを貼り付けてください" |
| **AI 自動概要生成** | ✅ 確認済み | ソース追加後に自動で生成 |
| **提案質問の自動生成** | ✅ 確認済み | AI が関連質問を自動提案 |
| **チャット機能** | ✅ 確認済み | UI 要素: `ref=e2001`（送信ボタン） |
| **AI 回答取得** | ✅ 確認済み | ソース引用、カスタマイズオプション情報を含む |
| **Audio Overview 生成開始** | ✅ 確認済み | UI 要素: `ref=e1960` |
| **Studio 機能（9種類）** | ✅ UI 確認済み | 動画解説、マインドマップ、レポート、フラッシュカード、クイズ、インフォグラフィック、スライド資料、Data Table、メモ |

### 検証したノートブック

- **URL**: `https://notebooklm.google.com/notebook/c9354f3f-f55b-4f90-a5c4-219e582945cf`
- **作成日時**: 2026-02-16
- **使用したサンプルテキスト**: NotebookLM の音声解説機能に関する説明文

### UI セレクターパターン

Playwright での要素選択パターン:

```python
# ボタンクリック（ref 値使用）
page.get_by_role("button", ref="e78").click()
page.get_by_role("button", ref="e135").click()

# プレースホルダーによる入力フィールド選択
page.get_by_placeholder('ここにテキストを貼り付けてください').fill(text)

# テキスト内容による選択
page.get_by_text("Audio overview", exact=True).click()
page.get_by_text("コピーしたテキスト", exact=True).click()

# 複合セレクター
page.locator('div[role="button"]').filter(has_text="送信").click()
```

---

## 実装可能な MCP ツール（12個）

### 優先度: 🟢 低難易度（まず実装）

#### 1. `notebooklm_create_notebook`
**説明**: 新しいノートブックを作成する
**パラメータ**:
- `title` (str): ノートブック名

**実装のポイント**:
- `ref=e78` または `ref=e135` のボタンをクリック
- タイトル入力フィールドに入力
- 作成確認

#### 2. `notebooklm_add_text_source`
**説明**: テキストデータをソースとして追加
**パラメータ**:
- `notebook_id` (str): ノートブックID（URL の最後の部分）
- `text` (str): 追加するテキスト

**実装のポイント**:
- ノートブックページに遷移
- "コピーしたテキスト" ボタンをクリック（`ref=e1842`）
- プレースホルダー選択: `ここにテキストを貼り付けてください`
- テキスト入力 & 保存

#### 3. `notebooklm_list_notebooks`
**説明**: ユーザーの全ノートブック一覧を取得
**パラメータ**: なし

**実装のポイント**:
- NotebookLM のホームページに遷移
- ノートブックリストをスクレイピング
- 各ノートブックの ID、タイトル、更新日時を抽出

#### 4. `notebooklm_get_notebook_summary`
**説明**: ノートブックの AI 生成概要を取得
**パラメータ**:
- `notebook_id` (str): ノートブックID

**実装のポイント**:
- ノートブックページに遷移
- 概要セクションのテキストを取得

### 優先度: 🟡 中難易度

#### 5. `notebooklm_chat`
**説明**: AI に質問してノートブックに基づいた回答を取得
**パラメータ**:
- `notebook_id` (str): ノートブックID
- `question` (str): 質問内容

**実装のポイント**:
- ノートブックページに遷移
- チャット入力フィールドに質問を入力
- 送信ボタンクリック（`ref=e2001`）
- AI 回答を取得（引用元も含む）

#### 6. `notebooklm_generate_audio_overview`
**説明**: Audio Overview（ポッドキャスト）を生成
**パラメータ**:
- `notebook_id` (str): ノートブックID
- `customization` (dict, optional): カスタマイズオプション
  - `audience_level` (str): "beginner" | "advanced"
  - `focus_topic` (str): フォーカストピック

**実装のポイント**:
- ノートブックページに遷移
- "Audio overview" ボタンをクリック（`ref=e1960`）
- カスタマイズオプションを入力（オプション）
- 生成開始
- **注意**: 生成完了まで数分かかる場合がある（ポーリング必要）

#### 7. `notebooklm_add_url_source`
**説明**: URL をソースとして追加
**パラメータ**:
- `notebook_id` (str): ノートブックID
- `url` (str): 追加するURL

**実装のポイント**:
- ノートブックページに遷移
- "ウェブサイト" ボタンをクリック
- URL 入力フィールドに入力
- 追加確認

#### 8. `notebooklm_add_file_source`
**説明**: ファイル（PDF、DOCX等）をアップロードしてソースとして追加
**パラメータ**:
- `notebook_id` (str): ノートブックID
- `file_path` (str): ローカルファイルパス

**実装のポイント**:
- ノートブックページに遷移
- "ファイルをアップロード" ボタンをクリック
- ファイル選択ダイアログでファイルを選択
- アップロード完了を待機

### 優先度: 🔴 高難易度

#### 9. `notebooklm_generate_study_guide`
**説明**: 学習ガイドを生成（Studio機能）
**パラメータ**:
- `notebook_id` (str): ノートブックID
- `guide_type` (str): "flashcards" | "quiz" | "report"

**実装のポイント**:
- ノートブックページに遷移
- Studio セクションに移動
- 対応する生成ボタンをクリック
- 生成完了を待機
- **課題**: 各 Studio 機能のセレクターパターンを個別に調査必要

#### 10. `notebooklm_list_sources`
**説明**: ノートブック内の全ソース一覧を取得
**パラメータ**:
- `notebook_id` (str): ノートブックID

**実装のポイント**:
- ノートブックページに遷移
- ソースリストセクションをスクレイピング
- 各ソースのタイトル、タイプ、追加日時を抽出

#### 11. `notebooklm_delete_source`
**説明**: ソースを削除
**パラメータ**:
- `notebook_id` (str): ノートブックID
- `source_id` (str): ソースID

**実装のポイント**:
- ノートブックページに遷移
- 対象ソースのメニューを開く
- "削除" オプションをクリック
- 削除確認
- **課題**: source_id の特定方法を確立する必要あり

#### 12. `notebooklm_delete_notebook`
**説明**: ノートブックを削除
**パラメータ**:
- `notebook_id` (str): ノートブックID

**実装のポイント**:
- ノートブックページに遷移
- 設定メニューを開く
- "削除" オプションをクリック
- 削除確認

---

## パッケージ構造

```
src/notebooklm/
├── __init__.py
├── playwright_client.py      # Playwright操作の中核クラス
├── notebook.py                # ノートブック管理
├── source.py                  # ソース管理
├── chat.py                    # AI チャット機能
├── audio.py                   # Audio Overview 生成
├── studio.py                  # Studio 機能（学習ガイド等）
└── types.py                   # Pydantic モデル定義

mcp/
├── server.py                  # FastMCP サーバー
├── tools/                     # 各 MCP ツール実装
│   ├── notebook_tools.py      # ノートブック管理ツール
│   ├── source_tools.py        # ソース管理ツール
│   ├── chat_tools.py          # チャットツール
│   ├── audio_tools.py         # Audio Overview ツール
│   └── studio_tools.py        # Studio 機能ツール
└── config.py                  # MCP 設定

tests/
├── unit/                      # 単体テスト
│   ├── test_playwright_client.py
│   ├── test_notebook.py
│   └── test_source.py
└── integration/               # 統合テスト（実際の NotebookLM で検証）
    ├── test_notebook_workflow.py
    └── test_chat_workflow.py

.claude/
└── mcp-settings.json          # MCP サーバー登録設定
```

---

## 認証方法

### 手動ログイン + セッション管理

**フロー**:

1. **初回起動時**: Playwright が Google ログイン画面を表示
2. **ユーザーがブラウザで手動ログイン**
3. **セッション保存**: Playwright の `context.storage_state()` でセッションを保存
4. **2回目以降**: 保存したセッションを読み込んで自動ログイン

**実装例**:

```python
from playwright.sync_api import sync_playwright

class NotebookLMClient:
    def __init__(self, session_file: str = ".notebooklm-session.json"):
        self.session_file = session_file
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def login_and_save_session(self):
        """初回ログイン＆セッション保存"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

        # NotebookLM にアクセス
        self.page.goto("https://notebooklm.google.com")

        # ユーザーが手動でログインするまで待機
        print("ブラウザでログインしてください...")
        self.page.wait_for_url("https://notebooklm.google.com/notebooks")

        # セッション保存
        self.context.storage_state(path=self.session_file)
        print(f"セッションを保存しました: {self.session_file}")

        self.close()

    def load_session_and_start(self):
        """保存済みセッションで起動"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)

        # セッションを読み込んで起動
        self.context = self.browser.new_context(
            storage_state=self.session_file
        )
        self.page = self.context.new_page()
        self.page.goto("https://notebooklm.google.com/notebooks")
```

**セキュリティ**:
- セッションファイル（`.notebooklm-session.json`）は `.gitignore` に追加
- ユーザーの Google 認証情報は保存しない（Cookie のみ）
- セッション有効期限切れ時は再ログイン必要

---

## 実装優先順位

### Phase 1: コアツール実装（🟢 低難易度）

**期間**: 1週間
**目標**: 基本的なノートブック操作を実現

1. `notebooklm_create_notebook` - ノートブック作成
2. `notebooklm_add_text_source` - テキストソース追加
3. `notebooklm_list_notebooks` - ノートブック一覧
4. `notebooklm_get_notebook_summary` - 概要取得

**成果物**:
- `src/notebooklm/playwright_client.py`
- `src/notebooklm/notebook.py`
- `src/notebooklm/source.py`
- `mcp/server.py`（4ツール登録）
- 単体テスト

### Phase 2: チャット＆Audio機能（🟡 中難易度）

**期間**: 1週間
**目標**: AI 機能を活用

5. `notebooklm_chat` - AI チャット
6. `notebooklm_generate_audio_overview` - Audio Overview 生成
7. `notebooklm_add_url_source` - URL ソース追加
8. `notebooklm_add_file_source` - ファイルソース追加

**成果物**:
- `src/notebooklm/chat.py`
- `src/notebooklm/audio.py`
- `mcp/tools/chat_tools.py`
- `mcp/tools/audio_tools.py`
- 統合テスト

### Phase 3: 高度な機能（🔴 高難易度）

**期間**: 2週間
**目標**: 完全な機能セット

9. `notebooklm_generate_study_guide` - Studio 機能
10. `notebooklm_list_sources` - ソース一覧
11. `notebooklm_delete_source` - ソース削除
12. `notebooklm_delete_notebook` - ノートブック削除

**成果物**:
- `src/notebooklm/studio.py`
- `mcp/tools/studio_tools.py`
- 全機能の統合テスト
- ドキュメント完成

---

## リスクと制約

### リスク

| リスク | 影響度 | 対策 |
|--------|--------|------|
| **UI 変更への依存** | 高 | セレクターパターンのバージョン管理、フォールバック実装 |
| **速度の遅さ** | 中 | ヘッドレスモード活用、並列実行の検討 |
| **認証セッション期限切れ** | 中 | 定期的なセッション更新、エラーハンドリング強化 |
| **Audio Overview 生成の遅延** | 低 | ポーリング実装、タイムアウト設定 |
| **Google による制限** | 低 | 通常の Web UI 利用のため TOS 準拠 |

### 制約

| 制約 | 詳細 |
|------|------|
| **速度** | API 比で 5～10倍遅い（ブラウザレンダリング必要） |
| **安定性** | UI の小変更で動作不良の可能性 |
| **並列実行** | 単一ブラウザインスタンスでは制限あり |
| **エラーハンドリング** | UI 操作のタイムアウト、要素未検出への対応が複雑 |

---

## 利点

### ✅ 完全無料

- API 料金なし
- ライセンス料金なし
- GCP プロジェクト不要

### ✅ TOS 準拠

- 公式 Web UI の通常利用と同じ
- 非公式 API やスクレイピングではない
- Google による制限のリスク低

### ✅ 全機能アクセス

- NotebookLM の全機能が利用可能
- UI で提供されている機能はすべて自動化可能
- Studio 機能（9種類）も実装可能

### ✅ 認証の簡便さ

- Google アカウントの通常ログインのみ
- Service Account や IAM 設定不要
- セッション管理のみで継続利用可能

---

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| **ブラウザ自動化** | Playwright (Python) |
| **MCP フレームワーク** | FastMCP |
| **HTTP 通信** | stdio トランスポート |
| **型定義** | Pydantic v2 |
| **テスト** | pytest, Hypothesis |
| **パッケージ管理** | uv |

---

## 次のステップ

### 1. GitHub Issue 作成

以下の Issue を作成:

- **Issue #1**: `[notebooklm] Phase 1: コアツール実装（4ツール）`
- **Issue #2**: `[notebooklm] Phase 2: チャット＆Audio機能（4ツール）`
- **Issue #3**: `[notebooklm] Phase 3: 高度な機能（4ツール）`
- **Issue #4**: `[notebooklm] ドキュメント作成`
- **Issue #5**: `[notebooklm] パッケージ README 更新`

### 2. パッケージ作成

```bash
/new-package notebooklm
```

### 3. 依存関係追加

```bash
cd src/notebooklm
uv add playwright fastmcp pydantic
uv run playwright install chromium
```

### 4. 実装開始

```bash
/issue-implement 1
```

---

## 参考リソース

### Playwright 公式ドキュメント

- [Playwright Python API](https://playwright.dev/python/)
- [セレクター](https://playwright.dev/python/docs/selectors)
- [認証とセッション管理](https://playwright.dev/python/docs/auth)

### NotebookLM

- [NotebookLM](https://notebooklm.google.com)
- [検証済みノートブック](https://notebooklm.google.com/notebook/c9354f3f-f55b-4f90-a5c4-219e582945cf)

### MCP

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP](https://github.com/jlowin/fastmcp)

---

## 関連ファイル

| ファイル | 説明 |
|---------|------|
| `docs/plan/2026-02-16_notebooklm-mcp-server-plan.md` | Enterprise API + notebooklm-py ベースの実装計画（参考） |
| `.notebooklm-session.json` | Playwright セッションファイル（作成予定、.gitignore 追加） |

---

## 更新履歴

- **2026-02-16**: 初版作成（Playwright 検証結果をもとに作成）
