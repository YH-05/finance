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
| **Web Research（Fast Research）** | ✅ 検索実行確認済み | ソースタイプ（ウェブ/ドライブ）、リサーチモード（Fast/Deep）切替、検索→結果→インポートの全フロー検証済み |
| **Web Research（Deep Research）** | ✅ 実行検証済み | ドロップダウン切替、プレースホルダー変化、アイコン（`travel_explore`）確認済み。5段階ステップ進行、計画フェーズ、停止ボタン、キャンセルダイアログを検証済み。完了まで25分以上（ステップ1/5で停滞しキャンセル）。完了時UIは未確認 |

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

## Studio 機能 詳細調査結果（2026-02-16）

### 調査概要

NotebookLM の Studio 機能のうち、コンテンツ生成・ダウンロード可能な4機能（レポート、インフォグラフィック、スライド資料、Data Table）を Playwright で実際に操作し、生成～エクスポートのフローを検証した。

### 調査結果サマリー

| 機能 | 生成 | 生成時間 | コンテンツ形式 | ダウンロード | コピー | 共有 | エクスポート |
|------|------|---------|--------------|------------|--------|------|------------|
| **レポート** | ✅ | ~15秒 | テキスト（リッチテキスト） | ❌ | ✅（書式保持コピー） | ❌ | ❌ |
| **インフォグラフィック** | ✅ | ~50秒 | 画像 | ✅（ダウンロード） | ❌ | ✅ | ❌ |
| **スライド資料** | ✅ | ~5分 | 画像（複数枚） | ✅（ダウンロード） | ❌ | ✅ | ❌ |
| **Data Table** | ✅ | ~30秒 | HTMLテーブル | ❌ | ❌ | ❌ | ✅（Google スプレッドシート） |

### 各機能の詳細

#### 1. レポート

**生成フロー**:
1. Studio パネルの「レポート」ボタンをクリック
2. フォーマット選択ダイアログが表示される
   - 選択肢: `独自に作成` / `概要説明資料` / `学習ガイド` / `ブログ投稿`
3. フォーマットを選択すると生成開始（~15秒）
4. リッチテキスト形式でレポートが表示（見出し、段落、テーブル等）

**エクスポートオプション**:
- 「書式設定を保持したままコンテンツをコピー」ボタン: ✅ あり
- 「その他のオプション」メニュー:
  - `プロンプトを表示`: 生成に使用したプロンプトを表示
  - `削除`: レポートを削除
  - **ダウンロード機能は存在しない**

**MCP実装への影響**:
- テキストベースなので Playwright の `text_content()` でテキスト取得可能
- ダウンロードは不可だが、テキスト抽出→ファイル保存で代替可能
- フォーマット選択の自動化が必要

#### 2. インフォグラフィック

**生成フロー**:
1. Studio パネルの「インフォグラフィック」ボタンをクリック
2. 自動で生成開始（~50秒）
3. 画像形式でインフォグラフィックが表示
4. ズームコントロール付きビューアで表示

**エクスポートオプション**:
- 「共有」ボタン: ✅ あり
- 「その他のオプション」メニュー:
  - **`ダウンロード`**: ✅ 画像ファイルとしてダウンロード可能
- alt テキストに内容説明が含まれる

**MCP実装への影響**:
- ダウンロード機能あり → Playwright の `download` イベントで取得可能
- 画像形式（PNG/SVG想定）でローカル保存可能
- 生成時間が長め（~50秒）なのでタイムアウト設定に注意

#### 3. スライド資料

**生成フロー**:
1. Studio パネルの「スライド資料」ボタンをクリック
2. 自動で生成開始（~5分、最も長い）
3. 画像形式で複数枚のスライドが表示（検証時は9枚生成）
4. 各スライドはボタンとして個別クリック可能
5. 「スライドショーを開始」ボタンあり

**エクスポートオプション**:
- 「共有」ボタン: ✅ あり
- 「スライドショーを開始」ボタン: ✅ あり
- 「開く」ボタン: ✅ あり（フルスクリーン表示）
- 「その他のオプション」メニュー:
  - **`ダウンロード`**: ✅ ダウンロード可能

**MCP実装への影響**:
- ダウンロード機能あり → Playwright の `download` イベントで取得可能
- 生成時間が非常に長い（~5分）→ 十分なタイムアウト設定が必要
- 複数スライドの一括ダウンロードか個別ダウンロードかは要追加検証

#### 4. Data Table

**生成フロー**:
1. Studio パネルの「Data Table」ボタンをクリック
2. 自動で生成開始（~30秒）
3. HTMLテーブル形式で表示（列: 機能名、機能の概要、期待される効果、情報源）
4. ソース引用番号付き

**エクスポートオプション**:
- 「その他のオプション」メニュー:
  - **`Google スプレッドシートにエクスポート`**: ✅ Google Sheets にエクスポート可能
  - `削除`: テーブルを削除
  - **直接ダウンロードは存在しない**（Google Sheets 経由のみ）

**MCP実装への影響**:
- HTMLテーブルなので Playwright でセル単位のデータ抽出が可能
- 直接ダウンロードは不可だが、テーブルデータをスクレイピング→CSV/JSON保存で代替可能
- Google Sheets エクスポート機能はOAuth認証の問題がありMCP経由では使いにくい

### Studio 機能のUI共通パターン

#### コンテンツ種別によるUIの違い

| パターン | 該当機能 | 特徴 |
|---------|---------|------|
| **テキストベース** | レポート | コピーボタンあり、ダウンロードなし、プロンプト表示可能 |
| **画像ベース** | インフォグラフィック、スライド資料 | ダウンロード可能、共有ボタンあり、ズーム/スライドショーあり |
| **テーブルベース** | Data Table | Google Sheets エクスポート、直接ダウンロードなし |

#### 生成中の共通インジケーター

- 「アーティファクト作成アイコン」が表示される（画像/テーブル系）
- ボタンが `[disabled]` になり「○○を生成しています...」テキストが表示
- 完了通知: `「○○の準備ができました。」` トーストメッセージ

#### セレクターパターン

```python
# Studio パネル内のボタン
page.get_by_role("button", name="レポート").click()
page.get_by_role("button", name="インフォグラフィック").click()
page.get_by_role("button", name="スライド資料").click()
page.get_by_role("button", name="Data Table").click()

# 生成済みアーティファクトのクリック（タイトルで特定）
page.get_by_role("button", name=re.compile(r".*タイトル.*")).click()

# エクスポートメニュー
page.get_by_role("button", name="その他のオプション").click()
page.get_by_role("menuitem", name="ダウンロード").click()
page.get_by_role("menuitem", name="Google スプレッドシートにエクスポート").click()

# レポートのフォーマット選択
page.get_by_role("button", name="概要説明資料").click()  # or 学習ガイド, ブログ投稿

# レポートのコピー
page.get_by_role("button", name="書式設定を保持したままコンテンツをコピー").click()

# ビューアの閉じるボタン
page.get_by_role("button", name="レポートビューアを閉じる").click()
page.get_by_role("button", name="スライド資料を閉じる").click()
page.get_by_role("button", name="表を閉じる").click()
```

### コンテンツ取得方法の検証結果（2026-02-16）

レポートと Data Table について、Playwright 経由でコンテンツを取得する2つの手法（DOMスクレイピング、クリップボードコピー）を検証した。

#### 方法1: DOMスクレイピング（直接テキスト抽出）

**レポート: ✅ 成功**

レポートの DOM 構造:
```
<report-viewer>
  └── <labs-tailwind-doc-viewer>
      ├── <labs-tailwind-structural-element-view-v2>  ← h1（タイトル）
      ├── <labs-tailwind-structural-element-view-v2>  ← h2（セクション見出し）
      ├── <labs-tailwind-structural-element-view-v2>  ← div（段落テキスト）
      ├── <labs-tailwind-structural-element-view-v2>  ← table（テーブル）
      └── ...
```

各 `<labs-tailwind-structural-element-view-v2>` の子要素が実際のコンテンツ要素（`role="heading"` + `aria-level`、`div`、`table` 等）。
子要素の `role` と `aria-level` を参照して Markdown 変換が可能。

```javascript
// 実証済みスクレイピングコード
const viewer = document.querySelector('labs-tailwind-doc-viewer');
const elements = viewer.children;
for (const wrapper of elements) {
  const inner = wrapper.children[0];
  const role = inner.getAttribute('role');
  const ariaLevel = inner.getAttribute('aria-level');
  // role === 'heading' → '#'.repeat(ariaLevel) + text
  // table → セル単位でデータ抽出
  // それ以外 → プレーンテキスト
}
```

取得結果（Markdown 形式で見出し・段落・テーブルすべて正確に再現）:
```markdown
# Google NotebookLM：AIを活用したリサーチと情報統合の概要

## エグゼクティブ・サマリー

Google NotebookLMは、AI（人工知能）を基盤とした高度なリサーチツールである...

## 主要機能の詳細分析
...（以下、見出し・段落・テーブルがすべて構造を保持）
```

**Data Table: ✅ 成功**

Data Table は標準的な HTML `<table>` 要素を使用しており、スクレイピングが最も簡単。

```javascript
// 実証済みスクレイピングコード
const table = document.querySelector('table');
const rows = table.querySelectorAll('tr');
for (const row of rows) {
  const cells = row.querySelectorAll('th, td');
  // 各セルの textContent を取得
}
```

取得結果（JSON 形式で全行・全列を正確に取得）:
```json
[
  ["機能名", "機能の概要", "期待される効果", "情報源"],
  ["質問応答チャット", "アップロードしたソースの内容に基づき...", "膨大な資料の中から...", "[1]"],
  ...
]
```

#### 方法2: クリップボードコピー（書式保持コピーボタン）

**レポート: ✅ 成功**

1. 「書式設定を保持したままコンテンツをコピー」ボタンをクリック
2. `navigator.clipboard.readText()` でクリップボードからテキスト取得
3. プレーンテキスト形式で全文取得（テーブルはタブ区切り）

```javascript
// クリップボード読み取り
await page.click('button[name="書式設定を保持したままコンテンツをコピー"]');
const text = await page.evaluate(() => navigator.clipboard.readText());
```

取得結果の特徴:
- 見出しはプレーンテキスト（`#` マークなし）
- 段落間は `\n\n` で区切り
- テーブルはタブ区切り（`\t`）
- 箇条書きは `* ` プレフィックス
- **太字**マーカーは保持される

**Data Table: ❌ クリップボードコピーボタンなし**

Data Table にはコピーボタンが存在しない。DOMスクレイピングのみ。

#### 手法比較と推奨

| 手法 | レポート | Data Table | 構造保持 | 実装難易度 |
|------|---------|-----------|---------|-----------|
| **DOMスクレイピング** | ✅ | ✅ | ✅ Markdown変換可 | 中（DOM構造の解析必要） |
| **クリップボードコピー** | ✅ | ❌ 非対応 | △ プレーンテキスト | 低（ボタン1クリック） |

**推奨**: DOMスクレイピングを主手法とする
- 両機能で統一的に使用可能
- 構造情報（見出しレベル、テーブル構造）を保持できる
- クリップボードはフォールバックとして利用

### MCP ツール設計への反映

調査結果に基づき、Studio 機能の MCP ツールを以下のように再設計する:

#### `notebooklm_generate_studio_content`（既存 #9 を拡張）

```python
# パラメータ
{
    "notebook_id": str,
    "content_type": "report" | "infographic" | "slides" | "data_table",
    "report_format": "custom" | "briefing_doc" | "study_guide" | "blog_post",  # report のみ
    "download": bool,  # True の場合、ダウンロード可能なものはファイル保存
}

# レスポンス
{
    "title": str,                    # 生成されたコンテンツのタイトル
    "content_type": str,             # コンテンツ種別
    "text_content": str | None,      # テキスト系の場合、抽出テキスト
    "table_data": list[dict] | None, # テーブル系の場合、構造化データ
    "download_path": str | None,     # ダウンロードしたファイルパス（画像系）
    "generation_time_seconds": float, # 生成にかかった時間
}
```

---

## ソースペイン 全機能調査結果（2026-02-16）

### 調査概要

NotebookLM のソースペインにあるすべての機能（ソース追加・検索・管理）を Playwright で実際に操作し、UI 構造とセレクターパターンを網羅的に調査した。

### ソース追加方法（7種類）

#### 1. コピーしたテキスト

**UI フロー**:
1. 「ソースを追加」ボタンクリック → ダイアログ表示
2. 「コピーしたテキスト」ボタンクリック
3. テキストエリア（placeholder: "ここにテキストを貼り付けてください"）に入力
4. 「挿入」ボタンクリック

**セレクター**:
```python
page.get_by_role("button", name="コピーしたテキスト").click()
page.get_by_placeholder("ここにテキストを貼り付けてください").fill(text)
page.get_by_role("button", name="挿入").click()
```

**実装可能性**: ✅ 容易

#### 2. ウェブサイト（URL + YouTube）

**UI フロー**:
1. 「ソースを追加」ボタンクリック → ダイアログ表示
2. 「ウェブサイト」ボタンクリック
3. URL 入力フィールド（placeholder: "リンクを貼り付ける"）に入力
4. 「挿入」ボタンクリック

**仕様**:
- 複数 URL 対応（スペースまたは改行で区切り）
- YouTube URL 対応（テキスト文字起こし部分のみインポート）
- 有料記事は非対応
- 公開 YouTube 動画のみサポート
- 最近アップロードされた動画はインポートできない場合あり

**セレクター**:
```python
page.get_by_role("button", name="ウェブサイト").click()
page.get_by_placeholder("リンクを貼り付ける").fill(url)
page.get_by_role("button", name="挿入").click()
```

**実装可能性**: ✅ 容易

#### 3. ファイルアップロード

**UI フロー**:
1. 「ソースを追加」ボタンクリック → ダイアログ表示
2. 「ファイルをアップロード」ボタンクリック → ファイル選択ダイアログ
3. ファイル選択（またはドラッグ&ドロップ）

**対応形式**: PDF、画像、ドキュメント、音声 など

**セレクター**:
```python
# Playwright の file_chooser イベントを使用
with page.expect_file_chooser() as fc_info:
    page.get_by_role("button", name="ファイルをアップロード").click()
file_chooser = fc_info.value
file_chooser.set_files(file_path)
```

**実装可能性**: ✅ 可能（Playwright の file_chooser API で対応）

#### 4. Google Drive

**UI フロー**:
1. 「ソースを追加」ボタンクリック → ダイアログ表示
2. 「ドライブ」ボタンクリック → Google Drive ピッカー（iframe）
3. タブ選択: 最近使用したアイテム / マイドライブ / 共有アイテム / スター付き / パソコン
4. ファイル検索（"ドライブ内を検索、または URL を貼り付け"）
5. ファイル選択

**セレクター**:
```python
page.get_by_role("button", name="ドライブ").click()
# iframe 内の操作が必要
frame = page.frame_locator("iframe").last
frame.get_by_role("tab", name="マイドライブ").click()
frame.get_by_role("combobox", name="ドライブ内を検索、または URL を貼り付け").fill(query)
```

**実装可能性**: ⚠️ 難しい（iframe 内の Google Drive ピッカー操作が複雑）

#### 5. Web 検索（ソース検出）

**UI フロー**:
1. ソースペイン上部の検索バーにクエリ入力
2. **ソースタイプドロップダウン**で「ウェブ」（デフォルト）または「ドライブ」を選択
3. **リサーチモードドロップダウン**で「Fast Research」（デフォルト）または「Deep Research」を選択
4. 「送信」ボタンクリック → 検索中UI:
   - 検索ボックスとドロップダウンが **disabled** に変化
   - `progressbar "ソースを読み込んでいます"` 表示
   - **Fast Research**: ステータステキスト「ウェブサイトをリサーチしています...」（~15〜30秒で完了）
   - **Deep Research**: 「計画を作成しています...」→「計画中...」→「ステップ N/5 が完了しました」（25分以上、5段階ステップ）
     - `button "ソース検出を停止"` (icon: `stop`) が表示される（Fast Research にはない）
5. 検索完了後:
   - **Fast Research**: 「高速リサーチが完了しました！」（icon: `search_spark`）
   - **Deep Research**: 「ディープリサーチが完了しました！」（icon: `travel_explore`）（推定・完了UI未確認）
6. 結果のプレビュー（上位3件 + 「その他 N 件のソース」折りたたみ + AI 要約）
7. 「ソースを表示」（「表示」ボタン）で全結果を展開
8. 全結果ビュー（「ソース > ソース検出」パンくず表示）:
   - 各ソースに: アイコン（`web`/`drive_pdf`/`link`）、タイトル、AI 要約、「ソースのリンクを開く」ボタン、チェックボックス
   - 「すべてのソースを選択」チェックボックス
   - ソース数カウント（例: "10 件のソースを選択しました"）
   - フィードバック: 「高く評価」/「低く評価」ボタン
9. 「インポート」ボタンで選択したソースを一括追加 / 「削除」ボタンで破棄

**セレクター**:
```python
# ソースタイプ選択（ウェブ or ドライブ）
page.get_by_role("button", name="ウェブ").click()              # ドロップダウンを開く
page.get_by_role("menuitem", name="ウェブ").click()             # ウェブを選択
page.get_by_role("menuitem", name="ドライブ").click()           # ドライブを選択

# リサーチモード選択
page.get_by_role("button", name="Fast Research").click()       # ドロップダウンを開く
page.get_by_role("menuitem", name="Fast Research").click()     # Fast Research を選択
page.get_by_role("menuitem", name="Deep Research").click()     # Deep Research を選択

# 検索クエリ入力（プレースホルダーはモードで変化）
# Fast Research: "ウェブで新しいソースを検索"
# Deep Research: "調べたい内容を入力してください"
page.get_by_role("textbox", name="入力されたクエリをもとにソースを検出する").fill(query)
page.get_by_role("textbox", name="入力されたクエリをもとにソースを検出する").press("Enter")

# 結果待機
page.get_by_text("高速リサーチが完了しました！").wait_for()    # Fast Research
page.get_by_text("ディープリサーチが完了しました！").wait_for() # Deep Research（要検証）

# 全ソース表示
page.get_by_role("button", name="ソースを表示").click()

# 個別ソースの選択/解除
page.get_by_role("checkbox", name="ソースタイトル").uncheck()

# インポート
page.get_by_role("button", name="インポート").click()

# 結果破棄
page.get_by_role("button", name="削除").click()
```

**実装可能性**: ✅ 可能（待機処理が必要）

#### 6. Fast Research

**UI フロー**:
1. リサーチモードドロップダウンで「Fast Research」選択（デフォルト）
2. クエリ入力 → 送信
3. ~15〜30秒で結果表示
4. 結果プレビュー: 上位3件の詳細 + 「その他 N 件のソース」
5. 「表示」ボタンで全ソースリスト展開

**説明**: 「結果をすばやく取得したい場合に最適」
**アイコン**: `search_spark`
**プレースホルダー**: 「ウェブで新しいソースを検索」
**完了メッセージ**: 「高速リサーチが完了しました！」
**検索結果数**: 約10件

**セレクター**:
```python
# 現在の選択が Deep Research の場合
page.get_by_role("button", name="Deep Research").click()
page.get_by_role("menuitem", name="Fast Research").click()

# 現在の選択が Fast Research の場合（デフォルト）→ そのまま使用
```

**実装可能性**: ✅ 可能

#### 7. Deep Research（実機検証済み）

**UI フロー**:
1. リサーチモードドロップダウンで「Deep Research」選択
2. クエリ入力 → 送信
3. 計画フェーズ開始（「計画を作成しています...ページを更新しないでください」）
4. 5段階ステップで進行（「ステップ N/5 が完了しました」）
5. 各ステップ間で「計画中...このまま席を離れても大丈夫です」が交互に表示
6. 完了後: ソースリスト + 包括的なレポートが生成される（推定・完了UIは未確認）
7. レポートとソースの両方をノートブックにインポート可能（推定）

**説明**: 「詳細なレポートと結果」
**アイコン**: `travel_explore`
**プレースホルダー**: 「調べたい内容を入力してください」
**完了メッセージ**: 「ディープリサーチが完了しました！」（推定・未確認）
**検索結果数**: 15〜25件 + レポート（推定・未確認）
**所要時間**: 25分以上（ステップ1/5に25分以上かかるケースを実測確認）

**Deep Research 固有のUI要素（Fast Research にはない）**:
- `progressbar "ソースを読み込んでいます"` — ステップ進行中に表示
- `generic "ステップ N/5 が完了しました"` — 5段階のステップインジケーター
- `button "ソース検出を停止"` (icon: `stop`) — リサーチをキャンセルするボタン
- `dialog "Deep Research"` — キャンセル確認ダイアログ（「Deep Research をキャンセルしてもよろしいですか？」）

**ステータス遷移（実測）**:
```
0秒:    「計画を作成しています...ページを更新しないでください」
~30秒:  「計画中...このまま席を離れても大丈夫です」
~60秒:  「ステップ 1/5 が完了しました」
~120秒+: 「計画中...」と「ステップ 1/5」が交互に表示（長時間継続）
```

**セレクター**:
```python
# 現在の選択が Fast Research の場合
page.get_by_role("button", name="Fast Research").click()
page.get_by_role("menuitem", name="Deep Research").click()

# 現在の選択が Deep Research の場合 → そのまま使用

# Deep Research のキャンセル
page.get_by_role("button", name="ソース検出を停止").click()
# → dialog "Deep Research" が表示
page.get_by_role("button", name="確認").click()  # キャンセル実行
# page.get_by_role("button", name="キャンセルしない").click()  # キャンセルしない
```

**実装可能性**: ✅ 可能（長時間の待機が必要、タイムアウト 30分推奨。キャンセル機能の実装も必要）

### ソース管理機能

#### ソース一覧表示

**構造**:
- 「すべてのソースを選択」チェックボックス
- 各ソース: アイコン + 名前 + チェックボックス + 「もっと見る」ボタン
- ソース数: "N / 300"（上限 300 件）

**セレクター**:
```python
# ソース一覧のチェックボックス
page.get_by_role("checkbox", name="すべてのソースを選択")
page.get_by_role("checkbox", name="ソース名")

# ソース数取得
page.locator("text=/\\d+ \\/ 300/").text_content()
```

#### ソース詳細表示

**UI フロー**: ソース名をクリック → 詳細ビュー表示

**表示内容**:
1. **ソースガイド**（AI 生成要約）
   - ソース内容の要約テキスト
   - 「ソースガイドを閉じる」ボタン
2. **キートピック**（クリック可能なリスト）
   - listbox 形式で関連トピックを表示
   - 例: "NotebookLM", "AIリサーチツール", "情報の統合"
3. **元テキスト**（ソースの実際の内容）

**セレクター**:
```python
# ソース詳細を開く
page.get_by_label("ソース名").click()

# ソースガイドのテキスト取得
guide_text = page.locator("h4:has-text('ソースガイド') + div").text_content()

# キートピック取得
topics = page.get_by_role("listbox").get_by_role("option").all_text_contents()

# 元テキスト取得（ソースガイドの下に表示）
source_content = page.locator("generic").filter(has_text="元テキスト").text_content()

# ソース一覧に戻る
page.get_by_text("ソース", exact=True).click()  # パンくずリスト
```

#### ソースの削除

**UI フロー**:
1. ソースの「もっと見る」ボタンクリック
2. 「ソースを削除」メニュー項目クリック

**セレクター**:
```python
page.get_by_role("button", name="もっと見る").click()  # 対象ソースのボタン
page.get_by_role("menuitem", name="ソースを削除").click()
```

**実装可能性**: ✅ 容易

#### ソース名の変更

**UI フロー**:
1. ソースの「もっと見る」ボタンクリック
2. 「ソース名を変更」メニュー項目クリック
3. 新しい名前を入力

**セレクター**:
```python
page.get_by_role("button", name="もっと見る").click()
page.get_by_role("menuitem", name="ソース名を変更").click()
# 入力フィールドが表示される（要追加検証）
```

**実装可能性**: ✅ 容易

#### ソースの選択/解除（チャットのコンテキスト制御）

**UI フロー**: チェックボックスのオン/オフで、チャットで参照するソースを制御

**セレクター**:
```python
# 全選択/全解除
page.get_by_role("checkbox", name="すべてのソースを選択").check()
page.get_by_role("checkbox", name="すべてのソースを選択").uncheck()

# 個別選択/解除
page.get_by_role("checkbox", name="ソース名").check()
page.get_by_role("checkbox", name="ソース名").uncheck()
```

**実装可能性**: ✅ 容易

### 実装可能性サマリー

| 機能 | 実装可能性 | 難易度 | 備考 |
|------|-----------|--------|------|
| テキストソース追加 | ✅ | 🟢 低 | 既存計画に含まれる |
| URL ソース追加 | ✅ | 🟢 低 | 複数 URL 対応、YouTube 対応 |
| ファイルアップロード | ✅ | 🟡 中 | Playwright file_chooser API 使用 |
| Google Drive | ⚠️ | 🔴 高 | iframe 内の Google Drive ピッカー操作 |
| Web 検索 + インポート | ✅ | 🟡 中 | 待機処理、結果パース必要 |
| Fast Research | ✅ | 🟡 中 | Web 検索の拡張 |
| Deep Research | ✅ | 🔴 高 | 25分以上の待機（実測確認済み）、5段階ステップ進行、キャンセル機能あり、完了時のUIは未確認 |
| ソース一覧取得 | ✅ | 🟢 低 | ソースリストのスクレイピング |
| ソース詳細取得 | ✅ | 🟢 低 | ソースガイド + キートピック + 元テキスト |
| ソース削除 | ✅ | 🟢 低 | メニュー操作 |
| ソース名変更 | ✅ | 🟢 低 | メニュー操作 |
| ソース選択/解除 | ✅ | 🟢 低 | チェックボックス操作 |

### 新規 MCP ツール提案（調査結果に基づく追加）

#### `notebooklm_search_and_add_sources`（新規）
**説明**: Web 検索でソースを検出し、選択したものをノートブックに追加
**パラメータ**:
```python
{
    "notebook_id": str,
    "query": str,                    # 検索クエリ
    "research_mode": "fast" | "deep", # リサーチモード（デフォルト: fast）
    "search_scope": "web" | "drive",  # 検索範囲（デフォルト: web）
    "max_sources": int,              # インポートする最大ソース数（デフォルト: 全件）
    "auto_import": bool,             # True: 自動インポート / False: 結果のみ返す
}
```
**レスポンス**:
```python
{
    "summary": str,                  # 検索結果の AI 要約
    "sources": [
        {
            "title": str,
            "description": str,      # AI 要約
            "type": "web" | "pdf",
            "url": str | None,
            "selected": bool,
        }
    ],
    "total_count": int,
    "imported_count": int,           # auto_import=True の場合
}
```

#### `notebooklm_rename_source`（新規）
**説明**: ソースの名前を変更
**パラメータ**:
```python
{
    "notebook_id": str,
    "source_name": str,    # 現在のソース名
    "new_name": str,       # 新しいソース名
}
```

#### `notebooklm_select_sources`（新規）
**説明**: チャットで使用するソースを選択/解除
**パラメータ**:
```python
{
    "notebook_id": str,
    "action": "select_all" | "deselect_all" | "select" | "deselect",
    "source_names": list[str] | None,  # action が select/deselect の場合
}
```

#### `notebooklm_get_source_details`（新規）
**説明**: ソースの詳細（ソースガイド、キートピック、元テキスト）を取得
**パラメータ**:
```python
{
    "notebook_id": str,
    "source_name": str,
}
```
**レスポンス**:
```python
{
    "name": str,
    "guide_summary": str,      # AI 生成ソースガイド
    "key_topics": list[str],   # キートピック一覧
    "content": str,            # 元テキスト
}
```

### MCP ツール一覧（更新版: 16個）

| # | ツール名 | 説明 | 難易度 |
|---|---------|------|--------|
| 1 | `notebooklm_create_notebook` | ノートブック作成 | 🟢 |
| 2 | `notebooklm_add_text_source` | テキストソース追加 | 🟢 |
| 3 | `notebooklm_list_notebooks` | ノートブック一覧 | 🟢 |
| 4 | `notebooklm_get_notebook_summary` | 概要取得 | 🟢 |
| 5 | `notebooklm_chat` | AI チャット | 🟡 |
| 6 | `notebooklm_generate_audio_overview` | Audio Overview 生成 | 🟡 |
| 7 | `notebooklm_add_url_source` | URL ソース追加（YouTube 対応） | 🟢 |
| 8 | `notebooklm_add_file_source` | ファイルソース追加 | 🟡 |
| 9 | `notebooklm_generate_studio_content` | Studio コンテンツ生成 | 🔴 |
| 10 | `notebooklm_list_sources` | ソース一覧取得 | 🟢 |
| 11 | `notebooklm_delete_source` | ソース削除 | 🟢 |
| 12 | `notebooklm_delete_notebook` | ノートブック削除 | 🟡 |
| **13** | **`notebooklm_search_and_add_sources`** | **Web 検索でソース検出＆インポート** | **🟡** |
| **14** | **`notebooklm_rename_source`** | **ソース名変更** | **🟢** |
| **15** | **`notebooklm_select_sources`** | **ソース選択/解除（チャットコンテキスト制御）** | **🟢** |
| **16** | **`notebooklm_get_source_details`** | **ソース詳細取得（ガイド・トピック・テキスト）** | **🟢** |

---

## チャットペイン 全機能調査結果（2026-02-16）

### 調査概要

NotebookLM のチャットペインにあるすべての機能（設定ダイアログ、チャットオプション、質問送信、回答取得、回答コンテンツの抽出）を Playwright で実際に操作し、UI 構造とセレクターパターンを網羅的に調査した。

### チャットペインの UI 構成

```
チャットペイン
├── ヘッダー
│   ├── 「チャット」見出し (heading level=2)
│   ├── 「ノートブックを設定」ボタン (tune アイコン)  ← 設定ダイアログを開く
│   └── 「チャット オプション」ボタン (more_vert アイコン) ← メニュー
├── チャット履歴表示エリア
│   ├── ノートブック概要 (AI 自動生成)
│   │   ├── タイトル (heading level=1)
│   │   ├── ソース数
│   │   ├── 概要テキスト (太字マーカー付き)
│   │   ├── アクション: メモに保存 / コピー / 高評価 / 低評価
│   │   └── 提案質問ボタン (3個)
│   ├── 日付区切り (例: "今日 • 8:22")
│   └── 会話ペア (質問 + 回答) × N
│       ├── ユーザー質問 (heading level=3)
│       ├── AI 回答
│       │   ├── テキスト本文 (太字 `**text**`、箇条書き、番号付きリスト)
│       │   ├── ソース引用ボタン (例: `"1: 貼り付けたテキスト"`)
│       │   └── アクション: メモに保存 / コピー / 高評価 / 低評価
│       └── フォローアップ提案ボタン (3個)
└── クエリ入力エリア
    ├── テキストボックス (placeholder: "入力を開始します...")
    ├── ソース数表示 (例: "1 個のソース")
    └── 送信ボタン
```

### 1. チャット設定ダイアログ（ノートブックを設定）

「ノートブックを設定」ボタン（`tune` アイコン）をクリックすると、モーダルダイアログが表示される。

#### 設定項目1: 会話の目的、スタイル、役割の定義

ラジオグループで3つのオプションから選択:

| オプション | 説明 | テキストエリア |
|-----------|------|--------------|
| **デフォルト** | 一般的な研究やブレインストーミングのタスクに最適です。 | なし |
| **学習ガイド** | 教育コンテンツに最適。効率良く新しい概念を理解し、スキルを習得するのに役立ちます。 | なし |
| **カスタム** | ユーザー定義のカスタムプロンプト | あり（最大 10,000 文字） |

**カスタムプロンプトのプレースホルダー例**:
- スタイルをカスタマイズする（「博士課程の学生レベルで回答する」）
- さまざまなロールを提案する（「ロールプレイングの司会者になりきる」）
- プロジェクトの全体的な目標を定義する（「今後の取締役会の準備を手伝う」）

#### 設定項目2: 回答の長さを選択

ラジオグループで3つのオプションから選択:

| オプション | 内部名 | 説明 |
|-----------|--------|------|
| **デフォルト** | `デフォルトのボタン` | 標準的な長さ |
| **長め** | `詳細なスタイルガイド ボタン` | より詳細な回答 |
| **短め** | `簡潔なスタイルガイド ボタン` | 簡潔な回答 |

#### セレクターパターン

```python
# 設定ダイアログを開く
page.get_by_role("button", name="ノートブックを設定").click()

# 会話の目的、スタイル、役割の定義を選択
role_group = page.get_by_role("radiogroup", name="会話の目的、スタイル、役割の定義")
role_group.get_by_label("デフォルトのボタン").click()
role_group.get_by_label("学習ガイド プロンプト ボタン").click()
role_group.get_by_label("カスタムボタン").click()

# カスタムプロンプトを入力（カスタム選択時のみ表示）
page.get_by_role("textbox", name="チャットの応答を制御するカスタム プロンプト").fill("博士課程の学生レベルで回答してください")

# 回答の長さを選択
length_group = page.get_by_role("radiogroup", name="回答の長さを選択")
length_group.get_by_label("デフォルトのボタン").click()
length_group.get_by_label("詳細なスタイルガイド ボタン").click()  # 長め
length_group.get_by_label("簡潔なスタイルガイド ボタン").click()  # 短め

# 保存
page.get_by_role("button", name="設定を保存").click()

# ダイアログを閉じる（保存せずに閉じる場合）
page.get_by_role("button", name="チャット設定を閉じる").click()
```

**実装可能性**: ✅ 容易（ラジオボタンとテキストエリアの操作のみ）

### 2. チャット オプション（三点メニュー）

「チャット オプション」ボタン（`more_vert` アイコン）をクリックするとメニューが表示される。

| メニュー項目 | 説明 |
|------------|------|
| **チャットの履歴を削除** | チャット履歴を削除（「チャットの履歴は非公開です。」の注記付き） |

**セレクター**:
```python
page.get_by_role("button", name="チャット オプション").click()
page.get_by_role("menuitem", name="チャットの履歴を削除").click()
```

**実装可能性**: ✅ 容易

### 3. チャット質問の送信フロー

#### 送信手順

1. テキストボックスに質問を入力
2. 送信ボタンをクリック（またはEnter）
3. ローディング表示: 英語のステータスメッセージ（例: "Defining Core Advantages..."）
4. 回答生成完了（通常 5〜15 秒）
5. 回答テキスト + ソース引用 + アクションボタン + フォローアップ提案が表示

#### セレクターパターン

```python
# 質問を入力
page.get_by_role("textbox", name="クエリボックス").fill("質問内容")

# 送信
page.locator("query-box").get_by_role("button", name="送信").click()

# 回答完了を待機（送信ボタンが再び disabled になった後、テキストが表示されるのを待つ）
# 方法1: ローディング表示の消失を待つ
page.locator("text=返信を作成しました。").wait_for()

# 方法2: 新しいコピーボタンの出現を待つ
page.get_by_role("button", name="モデルの回答をクリップボードにコピー").last.wait_for()
```

**実装可能性**: ✅ 容易

### 4. AI 回答のコンテンツ取得方法

#### 方法1: クリップボードコピー（推奨）

各回答の下にある「モデルの回答をクリップボードにコピー」ボタンを使用。

**検証結果**: ✅ 成功 — Markdown フォーマットが保持された状態で全文取得可能

取得結果の例:
```markdown
ソースに基づくと、NotebookLMの主な利点は以下の3つです。

1.  **大量の文書の効率的な理解**
    NotebookLMを使用することで、膨大な量の文書を効率的に読み解き、理解することができます。

2.  **複数のソースからの情報統合**
    一つの文書だけでなく、複数のソースから情報を統合して扱うことが可能です。

3.  **AIによる多彩なアウトプット生成**
    **音声解説（Audio Overview）**の生成、質問への回答、マインドマップやレポートの自動生成など、AIを活用して多様な形式で情報を整理・出力できます。
```

**実装コード**:
```python
# クリップボード権限を付与
await page.context().grant_permissions(['clipboard-read', 'clipboard-write'])

# 最新の回答のコピーボタンをクリック
copy_buttons = await page.get_by_role("button", name="モデルの回答をクリップボードにコピー").all()
await copy_buttons[-1].click()  # 最新の回答

# クリップボードからテキスト取得
response_text = await page.evaluate("navigator.clipboard.readText()")
```

**取得テキストの特徴**:
- 太字は `**text**` 形式で保持
- 番号付きリストはインデント付き
- 段落間は `\n\n` で区切り
- ソース引用番号は含まれない（テキストのみ）

#### 方法2: DOM テキスト抽出

TreeWalker API を使用してチャットエリアからテキストノードを直接抽出。

**検証結果**: ✅ 成功 — ただしソース引用ボタンのテキストも含まれるためフィルタリングが必要

```javascript
const chatEl = document.querySelector('[class*="chat"]');
const walker = document.createTreeWalker(chatEl, NodeFilter.SHOW_TEXT);
let node;
while (node = walker.nextNode()) {
  const text = node.textContent?.trim();
  if (text && text.length > 10) {
    // テキストを収集
  }
}
```

#### 手法比較

| 手法 | フォーマット保持 | ソース引用 | 実装難易度 | 推奨 |
|------|---------------|-----------|-----------|------|
| **クリップボードコピー** | ✅ Markdown | ❌ 含まれない | 🟢 低 | ✅ 推奨 |
| **DOM テキスト抽出** | △ プレーンテキスト | ✅ 含まれる | 🟡 中 | フォールバック |

**推奨**: クリップボードコピーを主手法とする。ソース引用情報が必要な場合は DOM から引用ボタンのテキストを別途取得する。

### 5. AI 回答の構造要素

#### ソース引用

回答テキスト内に引用ボタンが埋め込まれる。

```python
# 引用ボタンの取得（例: "1: 貼り付けたテキスト"）
citations = page.get_by_role("button", name=re.compile(r"^\d+: ")).all()
for citation in citations:
    citation_text = citation.text_content()  # "1"
    citation_name = citation.get_attribute("name")  # "1: 貼り付けたテキスト"
```

#### フォローアップ提案

回答の後に3つの関連質問ボタンが自動生成される。

```python
# フォローアップ提案の取得（回答の直後に表示されるボタン群）
# 各ボタンは cursor=pointer で、テキストが質問内容
suggestions = page.locator("[ref=e996] button").all()  # コンテナ ref は動的
```

#### 各回答のアクションボタン

| ボタン | アクセシビリティ名 | 機能 |
|--------|------------------|------|
| メモに保存 | `メッセージをメモに保存` | Studio のメモパネルに保存 |
| コピー | `モデルの回答をクリップボードにコピー` | Markdown 形式でクリップボードにコピー |
| 高評価 | `回答に高評価をつける` | フィードバック |
| 低評価 | `回答に低評価をつける` | フィードバック |

#### ノートブック概要のアクションボタン

| ボタン | アクセシビリティ名 | 機能 |
|--------|------------------|------|
| メモに保存 | `メモに保存` | Studio のメモパネルに保存 |
| コピー | `概要をコピー` | 概要テキストをコピー |
| 高評価 | `概要を高く評価` | フィードバック |
| 低評価 | `概要を低く評価` | フィードバック |

### 6. チャット履歴の保持

- チャット履歴はセッションをまたいで保存される（トースト通知: 「チャットの履歴がセッションをまたいで保存されるようになりました。履歴の削除はこちらから行えます。」）
- 「チャット オプション」→「チャットの履歴を削除」で削除可能

### MCP ツール設計への反映

#### `notebooklm_chat` の拡張設計

```python
# パラメータ
{
    "notebook_id": str,
    "question": str,
    "chat_mode": "default" | "study_guide" | "custom",  # 会話モード
    "custom_prompt": str | None,       # カスタムモード時のプロンプト（最大10,000文字）
    "response_length": "default" | "longer" | "shorter",  # 回答の長さ
    "include_citations": bool,         # ソース引用情報を含めるか（デフォルト: True）
}

# レスポンス
{
    "question": str,                   # 送信した質問
    "response": str,                   # AI 回答テキスト（Markdown 形式）
    "citations": [                     # ソース引用（include_citations=True の場合）
        {
            "number": int,             # 引用番号
            "source_name": str,        # ソース名（例: "貼り付けたテキスト"）
        }
    ],
    "suggestions": list[str],         # フォローアップ提案（3個）
    "response_time_seconds": float,    # 回答生成にかかった時間
}
```

#### `notebooklm_configure_chat`（新規）

```python
# パラメータ
{
    "notebook_id": str,
    "mode": "default" | "study_guide" | "custom",
    "custom_prompt": str | None,       # mode=custom の場合（最大10,000文字）
    "response_length": "default" | "longer" | "shorter",
}
```

#### `notebooklm_get_chat_history`（新規）

```python
# パラメータ
{
    "notebook_id": str,
}

# レスポンス
{
    "summary": str,                    # ノートブック概要
    "suggested_questions": list[str],  # 提案質問
    "messages": [
        {
            "role": "user" | "assistant",
            "content": str,
            "citations": list[dict] | None,
            "suggestions": list[str] | None,
        }
    ],
}
```

#### `notebooklm_clear_chat_history`（新規）

```python
# パラメータ
{
    "notebook_id": str,
}
```

### 実装可能性サマリー

| 機能 | 実装可能性 | 難易度 | 備考 |
|------|-----------|--------|------|
| チャット設定変更（モード） | ✅ | 🟢 低 | ラジオボタン操作 |
| チャット設定変更（カスタムプロンプト） | ✅ | 🟢 低 | テキストエリア入力 |
| チャット設定変更（回答の長さ） | ✅ | 🟢 低 | ラジオボタン操作 |
| 質問送信 | ✅ | 🟢 低 | テキスト入力 + 送信ボタン |
| 回答テキスト取得（クリップボード） | ✅ | 🟢 低 | コピーボタン + clipboard API |
| 回答テキスト取得（DOM） | ✅ | 🟡 中 | TreeWalker + フィルタリング |
| ソース引用情報取得 | ✅ | 🟢 低 | 引用ボタンの name 属性 |
| フォローアップ提案取得 | ✅ | 🟢 低 | ボタンテキスト取得 |
| チャット履歴削除 | ✅ | 🟢 低 | メニュー操作 |
| 回答完了の待機 | ✅ | 🟡 中 | ポーリング or イベント待機 |

### MCP ツール一覧（最終版: 19個）

| # | ツール名 | 説明 | 難易度 |
|---|---------|------|--------|
| 1 | `notebooklm_create_notebook` | ノートブック作成 | 🟢 |
| 2 | `notebooklm_add_text_source` | テキストソース追加 | 🟢 |
| 3 | `notebooklm_list_notebooks` | ノートブック一覧 | 🟢 |
| 4 | `notebooklm_get_notebook_summary` | 概要取得 | 🟢 |
| 5 | `notebooklm_chat` | AI チャット（設定・引用・提案含む） | 🟡 |
| 6 | `notebooklm_generate_audio_overview` | Audio Overview 生成 | 🟡 |
| 7 | `notebooklm_add_url_source` | URL ソース追加（YouTube 対応） | 🟢 |
| 8 | `notebooklm_add_file_source` | ファイルソース追加 | 🟡 |
| 9 | `notebooklm_generate_studio_content` | Studio コンテンツ生成 | 🔴 |
| 10 | `notebooklm_list_sources` | ソース一覧取得 | 🟢 |
| 11 | `notebooklm_delete_source` | ソース削除 | 🟢 |
| 12 | `notebooklm_delete_notebook` | ノートブック削除 | 🟡 |
| 13 | `notebooklm_search_and_add_sources` | Web 検索でソース検出＆インポート | 🟡 |
| 14 | `notebooklm_rename_source` | ソース名変更 | 🟢 |
| 15 | `notebooklm_select_sources` | ソース選択/解除（チャットコンテキスト制御） | 🟢 |
| 16 | `notebooklm_get_source_details` | ソース詳細取得（ガイド・トピック・テキスト） | 🟢 |
| **17** | **`notebooklm_configure_chat`** | **チャット設定変更（モード・プロンプト・長さ）** | **🟢** |
| **18** | **`notebooklm_get_chat_history`** | **チャット履歴取得** | **🟡** |
| **19** | **`notebooklm_clear_chat_history`** | **チャット履歴削除** | **🟢** |

---

## ノート管理機能（メモパネル）要件定義

### 概要

NotebookLM の Studio パネルには「メモ」機能がある。チャットの回答を「メモに保存」したり、手動でメモを作成・編集できる。この機能を MCP ツールとして公開し、Claude Code からノートの CRUD 操作を可能にする。

### 想定される使用シーン

1. **リサーチメモの蓄積**: チャットで得た重要な回答をメモとして保存し、後で参照
2. **分析ノートの作成**: 手動でメモを作成し、分析結果や考察を記録
3. **レポート素材の整理**: Studio のレポートやチャット回答をメモに整理し、記事作成の素材として活用
4. **ワークフロー連携**: メモの内容を取得し、他のツール（記事作成、レポート生成等）に連携

### MCP ツール設計

#### `notebooklm_create_note`（新規 #20）

**説明**: ノートブック内にメモを手動で作成
**パラメータ**:
```python
{
    "notebook_id": str,
    "title": str | None,     # メモのタイトル（オプション）
    "content": str,          # メモのテキスト内容
}
```
**レスポンス**:
```python
{
    "title": str,            # 設定されたタイトル
    "content": str,          # 作成されたメモの内容
    "note_type": "manual",   # 手動作成メモ
    "created_at": str,       # 作成日時
}
```
**実装のポイント（Playwright 調査済み）**:
1. Studio パネルの `button "メモを追加します"` をクリック
2. タイトル入力: `textbox "メモのタイトルを編集可能"` に入力
3. 本文入力: `RICH-TEXT-EDITOR.note-editor` 内の ProseMirror エディタ（`contenteditable=true`）に入力
4. ツールバーあり: 標準/H1/H2/H3、太字、斜体、リスト、リンク
5. DOM 構造: `NOTE-EDITOR > FORM.note-form > [note-title-container, RICH-TEXT-EDITOR.note-editor]`

```python
# セレクターパターン
page.get_by_role("button", name="メモを追加します").click()
page.get_by_role("textbox", name="メモのタイトルを編集可能").fill(title)
# 本文は contenteditable の paragraph 要素に入力
page.locator("rich-text-editor.note-editor [contenteditable=true] p").click()
page.keyboard.type(content)
```

#### `notebooklm_list_notes`（新規 #21）

**説明**: ノートブック内の全メモ一覧を取得
**パラメータ**:
```python
{
    "notebook_id": str,
}
```
**レスポンス**:
```python
{
    "notes": [
        {
            "index": int,             # メモのインデックス（0始まり）
            "title": str,             # メモのタイトル
            "note_type": "manual" | "chat_saved",  # 手動作成 or チャット保存
            "content_preview": str,   # メモの先頭部分（プレビュー）
        }
    ],
    "total_count": int,
}
```
**実装のポイント（Playwright 調査済み）**:
- Studio パネルのアーティファクトリストからメモを抽出
- メモは `sticky_note_2` アイコンで識別可能
- Studio パネルには全アーティファクト（メモ、レポート、インフォグラフィック等）が統一リストで表示される
- メモ種類の判別: 手動作成は `RICH-TEXT-EDITOR.note-editor`、チャット保存は `LABS-TAILWIND-DOC-VIEWER.note-editor--readonly`

#### `notebooklm_get_note`（新規 #22）

**説明**: 特定のメモの全文を取得
**パラメータ**:
```python
{
    "notebook_id": str,
    "note_index": int,        # メモのインデックス（0始まり、一覧順）
}
```
**レスポンス**:
```python
{
    "title": str,             # メモのタイトル
    "content": str,           # メモの全文
    "note_type": "manual" | "chat_saved",  # 手動作成 or チャット保存
    "is_readonly": bool,      # 読み取り専用かどうか
}
```
**実装のポイント（Playwright 調査済み）**:
- Studio パネルでメモをクリックして詳細を表示
- **手動作成メモ**: `RICH-TEXT-EDITOR.note-editor` 内の ProseMirror から `textContent` で取得
- **チャット保存メモ**: `LABS-TAILWIND-DOC-VIEWER.note-editor.note-editor--readonly` から取得（読み取り専用、"保存した回答は表示専用です" 表示あり）
- DOM 構造: `NOTE-EDITOR > FORM.note-form`
- タイトル: `textbox "メモのタイトルを編集可能"` から取得

```python
# コンテンツ取得セレクター
# 手動メモの場合
page.locator("rich-text-editor.note-editor [contenteditable=true]").text_content()
# チャット保存メモの場合
page.locator("labs-tailwind-doc-viewer.note-editor--readonly").text_content()
```

#### `notebooklm_delete_note`（新規 #23）

**説明**: メモを削除
**パラメータ**:
```python
{
    "notebook_id": str,
    "note_index": int,        # 削除するメモのインデックス
}
```
**実装のポイント（Playwright 調査済み）**:

**方法 A: メモ詳細画面から削除**:
1. メモをクリックして詳細表示
2. `button "メモを削除"` をクリック
3. 確認ダイアログ表示 → `button "削除の確認"` をクリック

**方法 B: コンテキストメニューから削除**:
1. メモの `button "もっと見る"` をクリック
2. コンテキストメニューの `menuitem "削除"` をクリック
3. 確認ダイアログ表示 → `button "削除の確認"` をクリック

```python
# 方法 A（推奨: より安定）
page.get_by_role("button", name="メモを削除").click()
page.get_by_role("button", name="削除の確認").click()

# 方法 B
page.get_by_role("button", name="もっと見る").click()
page.get_by_role("menuitem", name="削除").click()
page.get_by_role("button", name="削除の確認").click()
```

**コンテキストメニュー全アクション**:
- ソースに変換
- すべてのメモをソースに変換
- Google ドキュメントにエクスポート
- Google スプレッドシートにエクスポート
- 削除

#### `notebooklm_save_chat_to_note`（新規 #24）

**説明**: チャットの最新回答をメモに保存
**パラメータ**:
```python
{
    "notebook_id": str,
    "message_index": int | None,  # None の場合は最新の回答
}
```
**実装のポイント**:
- チャット回答の「メモに保存」ボタン（`メッセージをメモに保存`）をクリック
- セレクター: `page.get_by_role("button", name="メッセージをメモに保存")`

### UI 調査ステータス

| 機能 | 調査ステータス | 備考 |
|------|--------------|------|
| メモ作成 | ✅ 確認済み | `button "メモを追加します"` → タイトル textbox → ProseMirror contenteditable |
| メモ一覧取得 | ✅ 確認済み | Studio パネルのアーティファクトリスト、`sticky_note_2` アイコンで識別 |
| メモ全文取得 | ✅ 確認済み | 手動: `RICH-TEXT-EDITOR.note-editor`、保存: `LABS-TAILWIND-DOC-VIEWER.note-editor--readonly` |
| メモ削除 | ✅ 確認済み | `button "メモを削除"` or コンテキストメニュー → 確認ダイアログ `button "削除の確認"` |
| チャット→メモ保存 | ✅ 確認済み | `button "メッセージをメモに保存"` → AI自動タイトル生成、読み取り専用メモとして保存 |

### Playwright 調査結果サマリー（2026-02-16）

#### メモの種類（2種類）

| 種別 | 作成方法 | エディタ | 編集可否 |
|------|---------|---------|---------|
| **手動メモ** | `button "メモを追加します"` | `RICH-TEXT-EDITOR.note-editor` (ProseMirror, contenteditable) | ✅ 編集可能 |
| **チャット保存メモ** | `button "メッセージをメモに保存"` | `LABS-TAILWIND-DOC-VIEWER.note-editor.note-editor--readonly` | ❌ 読み取り専用 |

#### DOM 構造

```
NOTE-EDITOR
└── FORM.note-form
    ├── div.note-title-container
    │   └── textbox "メモのタイトルを編集可能"
    ├── div.note-header__notices  (チャット保存メモのみ: "保存した回答は表示専用です")
    └── RICH-TEXT-EDITOR.note-editor          (手動メモ)
        └── [contenteditable=true]
            └── p (ProseMirror 段落)
    └── LABS-TAILWIND-DOC-VIEWER.note-editor.note-editor--readonly  (チャット保存メモ)
```

#### 主要セレクター

```python
# メモ作成
page.get_by_role("button", name="メモを追加します").click()
page.get_by_role("textbox", name="メモのタイトルを編集可能").fill(title)
page.locator("rich-text-editor.note-editor [contenteditable=true] p").click()
page.keyboard.type(content)

# メモ削除（詳細画面から）
page.get_by_role("button", name="メモを削除").click()
page.get_by_role("button", name="削除の確認").click()

# メモ削除（コンテキストメニューから）
page.get_by_role("button", name="もっと見る").click()
page.get_by_role("menuitem", name="削除").click()
page.get_by_role("button", name="削除の確認").click()

# チャット→メモ保存
page.get_by_role("button", name="メッセージをメモに保存").click()

# メモ内容取得（手動メモ）
page.locator("rich-text-editor.note-editor [contenteditable=true]").text_content()

# メモ内容取得（チャット保存メモ）
page.locator("labs-tailwind-doc-viewer.note-editor--readonly").text_content()
```

#### コンテキストメニューアクション

| アクション | セレクター | 備考 |
|-----------|----------|------|
| ソースに変換 | `menuitem "ソースに変換"` | メモをソースとして追加 |
| すべてのメモをソースに変換 | `menuitem "すべてのメモをソースに変換"` | 全メモ一括変換 |
| Google ドキュメントにエクスポート | `menuitem "Google ドキュメントにエクスポート"` | Google Drive 連携 |
| Google スプレッドシートにエクスポート | `menuitem "Google スプレッドシートにエクスポート"` | Google Drive 連携 |
| 削除 | `menuitem "削除"` | 確認ダイアログあり |

### 実装優先度

- **Phase 2 に含める**: `notebooklm_save_chat_to_note`（既存UIボタン利用、低難易度）
- **Phase 3 に含める**: その他のメモ CRUD 操作（UI調査後に実装）

---

## バッチ処理・自動化 要件定義

### 概要

複数のノートブックやソースを効率的に処理するための高レベル操作を MCP ツールとして提供する。個別ツールの組み合わせでは煩雑になる反復的な操作を一括で実行可能にする。

### 想定される使用シーン

1. **リサーチプロジェクト一括セットアップ**: 複数のトピックについてノートブックを作成し、関連ソースを一括追加
2. **定期レポート生成**: 既存ノートブックのソースを更新し、最新の概要・レポートを一括生成
3. **ソース一括追加**: 複数のURL / テキスト / ファイルを一度にノートブックに追加
4. **ナレッジベース構築**: 大量の資料を体系的にNotebookLMに投入

### MCP ツール設計

#### `notebooklm_batch_add_sources`（新規 #25）

**説明**: 複数のソースを一括でノートブックに追加
**パラメータ**:
```python
{
    "notebook_id": str,
    "sources": [
        {
            "type": "text" | "url" | "file",
            "content": str,        # text: テキスト内容, url: URL, file: ファイルパス
            "title": str | None,   # テキストソースの場合の名前（オプション）
        }
    ],
    "continue_on_error": bool,     # True: エラーがあっても続行（デフォルト: True）
}
```
**レスポンス**:
```python
{
    "results": [
        {
            "index": int,
            "type": str,
            "status": "success" | "error",
            "error_message": str | None,
        }
    ],
    "stats": {
        "total": int,
        "success": int,
        "error": int,
    },
}
```
**実装のポイント**:
- 各ソースを順次追加（NotebookLM のUI制約上、並列追加は不安定）
- エラー発生時の continue_on_error フラグで制御
- ソース追加後の処理完了を個別に待機

#### `notebooklm_workflow_research`（新規 #26）

**説明**: リサーチワークフローを一連で実行（ノートブック作成→ソース追加→チャット→コンテンツ生成）
**パラメータ**:
```python
{
    "title": str,                      # ノートブックタイトル
    "sources": [                       # 追加するソース（batch_add_sources と同形式）
        {
            "type": "text" | "url" | "file",
            "content": str,
        }
    ],
    "questions": list[str] | None,     # チャットで質問するリスト（オプション）
    "generate_content": list[str] | None,  # 生成するコンテンツ種別（オプション）
    # 例: ["report", "audio_overview", "infographic"]
    "chat_config": {                   # チャット設定（オプション）
        "mode": "default" | "study_guide" | "custom",
        "custom_prompt": str | None,
        "response_length": "default" | "longer" | "shorter",
    } | None,
}
```
**レスポンス**:
```python
{
    "notebook_id": str,                # 作成されたノートブックID
    "notebook_url": str,               # ノートブックURL
    "sources_added": int,              # 追加されたソース数
    "summary": str,                    # AI 生成概要
    "chat_responses": [                # チャット回答（questions 指定時）
        {
            "question": str,
            "response": str,
            "citations": list[dict],
        }
    ],
    "generated_content": [             # 生成コンテンツ（generate_content 指定時）
        {
            "type": str,
            "status": "success" | "error",
            "content": str | None,
            "download_path": str | None,
        }
    ],
    "total_time_seconds": float,
}
```
**実装のポイント**:
- 各ステップを順次実行し、エラー発生時は部分結果を返す
- ソース追加後にAI概要生成を待機してからチャット・コンテンツ生成に進む
- 長時間実行になるため、進捗ログを出力

#### `notebooklm_batch_chat`（新規 #27）

**説明**: 複数の質問を一括でチャットに送信し、回答をまとめて取得
**パラメータ**:
```python
{
    "notebook_id": str,
    "questions": list[str],            # 質問リスト
    "include_citations": bool,         # ソース引用を含めるか（デフォルト: True）
    "delay_between_questions": float,  # 質問間の待機秒数（デフォルト: 2.0）
}
```
**レスポンス**:
```python
{
    "responses": [
        {
            "question": str,
            "response": str,
            "citations": list[dict] | None,
            "response_time_seconds": float,
        }
    ],
    "total_time_seconds": float,
}
```

### 実装優先度

- **Phase 2 に含める**: `notebooklm_batch_add_sources`（既存ツールの繰り返し呼出）
- **Phase 3 に含める**: `notebooklm_workflow_research`, `notebooklm_batch_chat`（複合ワークフロー）

---

## MCP ツール一覧（更新版: 27個）

| # | ツール名 | 説明 | 難易度 | Phase |
|---|---------|------|--------|-------|
| 1 | `notebooklm_create_notebook` | ノートブック作成 | 🟢 | 1 |
| 2 | `notebooklm_add_text_source` | テキストソース追加 | 🟢 | 1 |
| 3 | `notebooklm_list_notebooks` | ノートブック一覧 | 🟢 | 1 |
| 4 | `notebooklm_get_notebook_summary` | 概要取得 | 🟢 | 1 |
| 5 | `notebooklm_chat` | AI チャット（設定・引用・提案含む） | 🟡 | 2 |
| 6 | `notebooklm_generate_audio_overview` | Audio Overview 生成 | 🟡 | 2 |
| 7 | `notebooklm_add_url_source` | URL ソース追加（YouTube 対応） | 🟢 | 2 |
| 8 | `notebooklm_add_file_source` | ファイルソース追加 | 🟡 | 2 |
| 9 | `notebooklm_generate_studio_content` | Studio コンテンツ生成 | 🔴 | 3 |
| 10 | `notebooklm_list_sources` | ソース一覧取得 | 🟢 | 1 |
| 11 | `notebooklm_delete_source` | ソース削除 | 🟢 | 2 |
| 12 | `notebooklm_delete_notebook` | ノートブック削除 | 🟡 | 3 |
| 13 | `notebooklm_search_and_add_sources` | Web 検索でソース検出＆インポート | 🟡 | 2 |
| 14 | `notebooklm_rename_source` | ソース名変更 | 🟢 | 2 |
| 15 | `notebooklm_select_sources` | ソース選択/解除（チャットコンテキスト制御） | 🟢 | 2 |
| 16 | `notebooklm_get_source_details` | ソース詳細取得（ガイド・トピック・テキスト） | 🟢 | 2 |
| 17 | `notebooklm_configure_chat` | チャット設定変更（モード・プロンプト・長さ） | 🟢 | 2 |
| 18 | `notebooklm_get_chat_history` | チャット履歴取得 | 🟡 | 3 |
| 19 | `notebooklm_clear_chat_history` | チャット履歴削除 | 🟢 | 2 |
| **20** | **`notebooklm_create_note`** | **メモを手動作成** | **🟡** | **3** |
| **21** | **`notebooklm_list_notes`** | **メモ一覧取得** | **🟡** | **3** |
| **22** | **`notebooklm_get_note`** | **メモ全文取得** | **🟡** | **3** |
| **23** | **`notebooklm_delete_note`** | **メモ削除** | **🟡** | **3** |
| **24** | **`notebooklm_save_chat_to_note`** | **チャット回答をメモに保存** | **🟢** | **2** |
| **25** | **`notebooklm_batch_add_sources`** | **複数ソースの一括追加** | **🟡** | **2** |
| **26** | **`notebooklm_workflow_research`** | **リサーチワークフロー一括実行** | **🔴** | **3** |
| **27** | **`notebooklm_batch_chat`** | **複数質問の一括チャット** | **🟡** | **3** |

### Phase 別サマリー

| Phase | ツール数 | 内容 |
|-------|---------|------|
| **Phase 1** | 5個 (#1-4, #10) | コアツール（ノートブック作成、テキストソース追加、一覧、概要、ソース一覧） |
| **Phase 2** | 13個 (#5-8, #11, #13-17, #19, #24-25) | チャット・Audio・ソース管理・メモ保存・バッチソース追加 |
| **Phase 3** | 9個 (#9, #12, #18, #20-23, #26-27) | Studio生成・ノート管理・ワークフロー・削除系 |

---

## 実装優先順位（更新版）

### Phase 1: コアツール（5ツール）

**目標**: 基本的なノートブック操作を実現

| # | ツール | 難易度 |
|---|--------|--------|
| 1 | `notebooklm_create_notebook` | 🟢 |
| 2 | `notebooklm_add_text_source` | 🟢 |
| 3 | `notebooklm_list_notebooks` | 🟢 |
| 4 | `notebooklm_get_notebook_summary` | 🟢 |
| 10 | `notebooklm_list_sources` | 🟢 |

**成果物**: `playwright_client.py`, `notebook.py`, `source.py`, `mcp/server.py`

### Phase 2: チャット・ソース管理・基本自動化（13ツール）

**目標**: AI 機能の活用、ソース管理、基本的なバッチ処理

| # | ツール | 難易度 |
|---|--------|--------|
| 5 | `notebooklm_chat` | 🟡 |
| 6 | `notebooklm_generate_audio_overview` | 🟡 |
| 7 | `notebooklm_add_url_source` | 🟢 |
| 8 | `notebooklm_add_file_source` | 🟡 |
| 11 | `notebooklm_delete_source` | 🟢 |
| 13 | `notebooklm_search_and_add_sources` | 🟡 |
| 14 | `notebooklm_rename_source` | 🟢 |
| 15 | `notebooklm_select_sources` | 🟢 |
| 16 | `notebooklm_get_source_details` | 🟢 |
| 17 | `notebooklm_configure_chat` | 🟢 |
| 19 | `notebooklm_clear_chat_history` | 🟢 |
| 24 | `notebooklm_save_chat_to_note` | 🟢 |
| 25 | `notebooklm_batch_add_sources` | 🟡 |

**成果物**: `chat.py`, `audio.py`, `batch.py`, 統合テスト

### Phase 3: 高度な機能・ノート管理・ワークフロー（9ツール）

**目標**: 完全な機能セット、ノート管理、自動化ワークフロー

| # | ツール | 難易度 |
|---|--------|--------|
| 9 | `notebooklm_generate_studio_content` | 🔴 |
| 12 | `notebooklm_delete_notebook` | 🟡 |
| 18 | `notebooklm_get_chat_history` | 🟡 |
| 20 | `notebooklm_create_note` | 🟡 |
| 21 | `notebooklm_list_notes` | 🟡 |
| 22 | `notebooklm_get_note` | 🟡 |
| 23 | `notebooklm_delete_note` | 🟡 |
| 26 | `notebooklm_workflow_research` | 🔴 |
| 27 | `notebooklm_batch_chat` | 🟡 |

**成果物**: `studio.py`, `note.py`, `workflow.py`, 全機能の統合テスト、ドキュメント

**前提**: Phase 3 のノート管理ツール (#20-23) の Playwright UI 調査は完了済み（2026-02-16）。全セレクターパターン確認済みのため、即座に実装可能

---

## Web Research（Fast Research / Deep Research）詳細調査結果（2026-02-16）

### 調査概要

NotebookLM の「ウェブで新しいソースを検索」機能を Playwright で実際に操作し、Fast Research と Deep Research の切り替え、検索実行、結果表示、インポートまでの完全なUIフローとセレクターパターンを検証した。

### UI 構成図

```
ソースペイン上部
├── 「ソースを追加」ボタン (add アイコン)
└── 検索エリア
    ├── 検索アイコン (search)
    ├── 検索テキストボックス
    │   ├── role: textbox
    │   ├── name: "入力されたクエリをもとにソースを検出する"
    │   └── placeholder:
    │       ├── Fast Research → "ウェブで新しいソースを検索"
    │       └── Deep Research → "調べたい内容を入力してください"
    ├── ソースタイプドロップダウン
    │   ├── button "ウェブ" (language アイコン + keyboard_arrow_down)
    │   └── menu (展開時)
    │       ├── menuitem "ウェブ" → "ウェブ上の最適なソース" (language アイコン)
    │       └── menuitem "ドライブ" → "Google ドライブのコンテンツ" (Google ドライブロゴ)
    ├── リサーチモードドロップダウン
    │   ├── button "Fast Research" / "Deep Research" (+ keyboard_arrow_down)
    │   └── menu (展開時)
    │       ├── menuitem "Fast Research" → "結果をすばやく取得したい場合に最適" (search_spark アイコン)
    │       └── menuitem "Deep Research" → "詳細なレポートと結果" (travel_explore アイコン)
    └── 送信ボタン (arrow_forward アイコン, クエリ空の場合 disabled)
```

### ドロップダウン詳細

#### ソースタイプドロップダウン

| 選択肢 | アイコン | 説明 | ARIA role |
|--------|---------|------|-----------|
| **ウェブ**（デフォルト） | `language` | ウェブ上の最適なソース | `menuitem` |
| **ドライブ** | Google ドライブのロゴ（`img`） | Google ドライブのコンテンツ | `menuitem` |

```python
# ソースタイプを切り替える
page.get_by_role("button", name="ウェブ").click()        # ドロップダウンを開く
page.get_by_role("menuitem", name="ドライブ").click()     # ドライブに切替

page.get_by_role("button", name="ドライブ").click()       # ドロップダウンを開く
page.get_by_role("menuitem", name="ウェブ").click()       # ウェブに切替
```

**注意**: ボタンの `name` は現在選択中の値で変化する。

#### リサーチモードドロップダウン

| 選択肢 | アイコン | 説明 | ARIA role |
|--------|---------|------|-----------|
| **Fast Research**（デフォルト） | `search_spark` | 結果をすばやく取得したい場合に最適 | `menuitem` |
| **Deep Research** | `travel_explore` | 詳細なレポートと結果 | `menuitem` |

```python
# Fast Research → Deep Research に切り替え
page.get_by_role("button", name="Fast Research").click()
page.get_by_role("menuitem", name="Deep Research").click()

# Deep Research → Fast Research に切り替え
page.get_by_role("button", name="Deep Research").click()
page.get_by_role("menuitem", name="Fast Research").click()
```

**注意**: ボタンの `name` は現在選択中のモード名で変化する。

### 検索実行フロー

#### Step 1: モード設定（オプション）

```python
# ソースタイプ設定（デフォルト: ウェブ）
# page.get_by_role("button", name="ウェブ").click()
# page.get_by_role("menuitem", name="ドライブ").click()

# リサーチモード設定（デフォルト: Fast Research）
# page.get_by_role("button", name="Fast Research").click()
# page.get_by_role("menuitem", name="Deep Research").click()
```

#### Step 2: クエリ入力＆送信

```python
search_box = page.get_by_role("textbox", name="入力されたクエリをもとにソースを検出する")
search_box.fill("2026 US equity market outlook AI investment")
search_box.press("Enter")
```

#### Step 3: 検索中の状態

検索開始後、UIが以下のように変化:

**Fast Research の検索中状態:**

| 要素 | 検索中の状態 |
|------|------------|
| テキストボックス | `disabled`、入力したクエリがプレースホルダーとして表示 |
| ソースタイプボタン | `disabled` |
| リサーチモードボタン | `disabled` |
| 送信ボタン | `disabled` |
| プログレスバー | `progressbar "ソースを読み込んでいます"` が新規表示 |
| ステータステキスト | 「ウェブサイトをリサーチしています...」 |

**Deep Research の検索中状態（実機検証済み）:**

| 要素 | 検索中の状態 |
|------|------------|
| テキストボックス | `disabled`、入力したクエリがプレースホルダーとして表示 |
| ソースタイプボタン | `disabled` |
| リサーチモードボタン | `disabled` |
| 送信ボタン | `disabled` |
| プログレスバー | `progressbar "ソースを読み込んでいます"` |
| ステータステキスト | 以下のメッセージが時系列で遷移: |
| | 1. 「計画を作成しています...ページを更新しないでください」 |
| | 2. 「計画中...このまま席を離れても大丈夫です」 |
| | 3. 「ステップ 1/5 が完了しました」 |
| | 4. 以降「計画中...」と「ステップ N/5」が交互に表示 |
| 停止ボタン | `button "ソース検出を停止"` (icon: `stop`) — Fast Research にはない |

**Deep Research のステータス遷移（実測値）:**

| 経過時間 | ステータスメッセージ |
|---------|-------------------|
| 0秒 | 「計画を作成しています...ページを更新しないでください」 |
| ~30秒 | 「計画中...このまま席を離れても大丈夫です」 |
| ~60秒 | 「ステップ 1/5 が完了しました」 |
| ~120秒以降 | 「計画中...」と「ステップ 1/5」が交互に表示（25分以上継続） |

**Deep Research のキャンセルフロー:**

```
「ソース検出を停止」クリック
  └── dialog "Deep Research"
      ├── メッセージ: "Deep Research をキャンセルしてもよろしいですか？"
      ├── button "キャンセルしない" → ダイアログ閉じ、リサーチ継続
      └── button "確認" → リサーチ停止、UIが初期状態に戻る
```

```python
# 検索中の待機（Fast Research の場合）
page.get_by_text("高速リサーチが完了しました！").wait_for(timeout=60000)

# 検索中の待機（Deep Research の場合）
# 注意: 25分以上かかる可能性あり。タイムアウトは最低30分を推奨
page.get_by_text("ディープリサーチが完了しました！").wait_for(timeout=1800000)  # 30分

# Deep Research のステップ進行を監視する場合
page.get_by_text("ステップ 1/5 が完了しました").wait_for(timeout=120000)
page.get_by_text("ステップ 2/5 が完了しました").wait_for(timeout=600000)
# ... ステップ 5/5 まで

# Deep Research のキャンセル
page.get_by_role("button", name="ソース検出を停止").click()
page.get_by_role("button", name="確認").click()  # キャンセル確認
```

#### Step 4: 結果プレビュー表示

Fast Research 完了後に表示される結果プレビュー:

```
検索結果プレビュー
├── ヘッダー
│   ├── search_spark アイコン
│   ├── 「高速リサーチが完了しました！」テキスト
│   └── 「表示」ボタン (ソースを表示)
├── 上位3件のソース
│   ├── ソース1: アイコン(drive_pdf/web) + タイトル + AI要約
│   ├── ソース2: アイコン + タイトル + AI要約
│   └── ソース3: アイコン + タイトル + AI要約
├── 「その他 N 件のソース」(link アイコン)
└── アクションバー
    ├── 「高く評価」ボタン (thumb_up)
    ├── 「低く評価」ボタン (thumb_down)
    ├── 「削除」ボタン
    └── 「インポート」ボタン (add アイコン)
```

```python
# 結果プレビューからインポート（全件）
page.get_by_role("button", name="インポート").click()

# 結果を破棄
page.get_by_role("button", name="削除").click()
```

#### Step 5: 全ソースリスト表示（「表示」クリック後）

「表示」ボタンをクリックすると、パンくず表示「ソース > ソース検出」で全ソースリスト画面に遷移:

```
ソース検出ビュー
├── パンくず: 「ソース」> 「ソース検出」
├── 検索クエリ表示 (travel_explore アイコン + クエリテキスト)
├── AI 要約テキスト（検索結果全体の説明）
├── ソースリスト
│   ├── 「すべてのソースを選択」チェックボックス
│   └── ソース N 件
│       ├── アイコン (drive_pdf / web)
│       ├── タイトル
│       ├── 「ソースのリンクを開く」ボタン (open_in_new アイコン)
│       ├── AI 要約（関連性の説明）
│       └── チェックボックス（選択/解除）
└── フッター
    ├── 「高く評価」/ 「低く評価」ボタン
    ├── 「N 件のソースを選択しました」テキスト
    └── 「インポート」ボタン
```

```python
# 「表示」ボタンで全ソースリストを開く
page.get_by_role("button", name="ソースを表示").click()

# 個別ソースの選択解除
page.get_by_role("checkbox", name="ソースタイトル").uncheck()

# 全選択/全解除
page.get_by_role("checkbox", name="すべてのソースを選択").uncheck()
page.get_by_role("checkbox", name="すべてのソースを選択").check()

# インポート実行
page.get_by_role("button", name="インポート").click()

# ソース一覧に戻る（パンくず）
page.get_by_text("ソース", exact=True).click()
```

### Fast Research vs Deep Research 比較

| 項目 | Fast Research | Deep Research |
|------|--------------|---------------|
| **アイコン** | `search_spark` | `travel_explore` |
| **説明** | 結果をすばやく取得したい場合に最適 | 詳細なレポートと結果 |
| **プレースホルダー** | ウェブで新しいソースを検索 | 調べたい内容を入力してください |
| **完了メッセージ** | 高速リサーチが完了しました！ | ディープリサーチが完了しました！（推定・未確認） |
| **所要時間** | ~15〜30秒 | 25分以上（ステップ1/5で停滞を確認、完了まで30分以上かかる可能性） |
| **ステップ表示** | なし | 5段階（「ステップ N/5 が完了しました」） |
| **計画フェーズ** | なし | あり（「計画を作成しています...」→「計画中...」） |
| **停止ボタン** | なし | `button "ソース検出を停止"` (icon: `stop`) |
| **キャンセル確認** | なし | `dialog "Deep Research"` → 「Deep Research をキャンセルしてもよろしいですか？」 |
| **ソース数** | ~10件 | ~15〜25件（推定・未確認） |
| **レポート生成** | なし | あり（包括的なレポートをソースとして生成）（推定・未確認） |
| **検索中表示** | progressbar + 「ウェブサイトをリサーチしています...」 | progressbar 「ソースを読み込んでいます」 + ステップ進行表示 |
| **結果構造** | ソースリスト + AI 要約 | ソースリスト + AI 要約 + レポート（推定・未確認） |

### MCP ツール `notebooklm_search_and_add_sources` の実装要件

#### 完全なセレクターパターン（Playwright 検証済み）

```python
async def search_and_add_sources(
    page,
    query: str,
    research_mode: str = "fast",  # "fast" | "deep"
    search_scope: str = "web",    # "web" | "drive"
    auto_import: bool = True,
):
    """Web Research 機能でソースを検出しインポートする"""

    # 1. ソースタイプ設定
    if search_scope == "drive":
        # 現在のボタンテキストに応じてドロップダウンを開く
        scope_button = page.get_by_role("button", name="ウェブ")
        if not await scope_button.count():
            scope_button = page.get_by_role("button", name="ドライブ")
        await scope_button.click()
        await page.get_by_role("menuitem", name="ドライブ").click()

    # 2. リサーチモード設定
    if research_mode == "deep":
        mode_button = page.get_by_role("button", name="Fast Research")
        if not await mode_button.count():
            mode_button = page.get_by_role("button", name="Deep Research")
        await mode_button.click()
        await page.get_by_role("menuitem", name="Deep Research").click()

    # 3. クエリ入力 & 送信
    search_box = page.get_by_role("textbox", name="入力されたクエリをもとにソースを検出する")
    await search_box.fill(query)
    await search_box.press("Enter")

    # 4. 結果待機
    if research_mode == "fast":
        await page.get_by_text("高速リサーチが完了しました！").wait_for(timeout=60000)
    else:
        # Deep Research は25分以上かかる場合あり（5段階ステップで進行）
        # ステータス遷移: 「計画を作成しています...」→「計画中...」→「ステップ N/5 が完了しました」
        # キャンセル: page.get_by_role("button", name="ソース検出を停止").click()
        #           → dialog → page.get_by_role("button", name="確認").click()
        await page.get_by_text("ディープリサーチが完了しました！").wait_for(timeout=1800000)  # 30分

    # 5. 全ソース表示
    await page.get_by_role("button", name="ソースを表示").click()

    # 6. ソースリスト取得（スクレイピング）
    sources = []
    # ... DOM からソース情報を抽出

    # 7. インポート（auto_import=True の場合）
    if auto_import:
        await page.get_by_role("button", name="インポート").click()

    return sources
```

#### 注意事項

1. **ドロップダウンボタンの `name` は動的**: 現在選択中の値がボタン名になるため、`"Fast Research"` か `"Deep Research"` のどちらかを試す必要がある
2. **Deep Research のタイムアウト**: 最低 30 分のタイムアウトを設定すべき（実測でステップ1/5に25分以上かかるケースを確認）
3. **検索中は全UI要素が disabled**: 検索実行中にソースタイプやモードの変更は不可
4. **プレースホルダーの変化**: モード切替時に検索ボックスのプレースホルダーが自動で変化（Fast: "ウェブで新しいソースを検索", Deep: "調べたい内容を入力してください"）
5. **Deep Research のレポート**: ソースリストに加えてレポートが最上位ソースとして追加される（推定・完了時UIは未確認）
6. **Deep Research のキャンセル**: `button "ソース検出を停止"` → 確認ダイアログ `dialog "Deep Research"` → `button "確認"` でキャンセル可能。キャンセル後、UIは初期状態に戻る
7. **Deep Research の5段階ステップ**: 「ステップ N/5 が完了しました」で進行表示。計画フェーズ（「計画を作成しています...」→「計画中...」）が先行する
8. **削除確認ダイアログ**: 検索結果の削除時に `dialog` が表示される（「ノートブックにインポートせずに削除しますか？」→ `button "確認"`）

---

## 更新履歴

- **2026-02-16**: Deep Research 実行検証結果を追記。5段階ステップ進行（「ステップ N/5 が完了しました」）、計画フェーズ（「計画を作成しています...」→「計画中...」）、停止ボタン（「ソース検出を停止」）、キャンセル確認ダイアログ（`dialog "Deep Research"`）を実機確認。所要時間は25分以上（ステップ1/5で停滞しキャンセル）。完了時のUIは未確認のため推定値を明示
- **2026-02-16**: Web Research（Fast Research / Deep Research）詳細調査結果を追記。Playwright で実際にドロップダウン操作・検索実行・結果表示を検証。ソースタイプ（ウェブ/ドライブ）とリサーチモード（Fast/Deep）の切り替えUI、検索中の状態変化、結果プレビュー・全ソースリストの構造を完全にドキュメント化
- **2026-02-16**: メモパネル Playwright UI 調査完了。2種類のメモ（手動/チャット保存）のDOM構造・セレクターパターン・コンテキストメニュー・削除フローを確認。全ツール (#20-24) の実装ポイントを更新
- **2026-02-16**: ノート管理機能（#20-24）、バッチ処理・自動化（#25-27）を追加。MCP ツール一覧を19個→27個に更新。Phase別実装計画を再編成
- **2026-02-16**: チャットペイン全機能調査結果を追記（設定ダイアログ、チャットオプション、質問送信フロー、回答コンテンツ取得方法、新規MCPツール3個提案）
- **2026-02-16**: ソースペイン全機能調査結果を追記（7種類のソース追加方法、ソース管理機能、新規 MCP ツール4個提案）
- **2026-02-16**: レポート・Data Table のコンテンツ取得検証結果を追記（DOMスクレイピング・クリップボードコピー）
- **2026-02-16**: Studio 機能の詳細調査結果を追記（レポート、インフォグラフィック、スライド資料、Data Table）
- **2026-02-16**: 初版作成（Playwright 検証結果をもとに作成）
