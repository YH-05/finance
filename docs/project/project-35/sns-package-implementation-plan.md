# sns パッケージ実装計画

## Context

金融記事（articles/）、週次レポート、ニュース速報を **note.com** と **X(Twitter)** に投稿するための `src/sns` パッケージを新規作成する。

現状、記事作成ワークフロー（`/finance-full`）の出力は GitHub Issues への投稿のみであり、note.com や X への投稿機能は存在しない。既存の `news` パッケージの SinkProtocol パターンと `rss` パッケージの HTTP クライアントパターンを再利用し、プラグイン方式のプラットフォーム抽象化を実現する。

**ユーザー要件:**
- 対応: note.com + X(Twitter)
- note.com: Playwright 自動化 + 手動フォールバック（Markdown 出力）
- 投稿トリガー: CLI コマンドで手動
- 対応コンテンツ: 全コンテンツ（金融記事、週次レポート、ニュース速報）

---

## アーキテクチャ概要

```
入力データソース                     変換層                        出力層
─────────────────────────────────────────────────────────────────────────────
articles/{id}/article-meta.json  ─┐
articles/{id}/02_edit/revised_draft.md ─→ ContentAdapter ─→ SnsPost ─→ HookGenerator ─→ SnsPost(with hook)
weekly_report/{date}/...         ─┘                                       │
                                                                          ├─→ NotePlatform (Playwright/Markdown)
                                                                          └─→ XPlatform (X API v2)
```

**コアコンセプト:**
1. **PlatformProtocol** — `news/core/sink.py` の SinkProtocol に相当。投稿先の抽象化
2. **ContentAdapter** — 各コンテンツタイプ（記事/レポート/速報）→ 統一 `SnsPost` への変換
3. **HookGenerator** — Claude Agent SDK でプラットフォーム別フック文を自動生成

---

## ディレクトリ構造

```
src/sns/
├── __init__.py           # 公開API
├── py.typed              # PEP 561
├── README.md             # ドキュメント
├── types.py              # 型定義
├── errors.py             # 例外階層
├── config.py             # 設定（Pydantic）
├── core/
│   ├── __init__.py
│   ├── platform.py       # PlatformProtocol
│   ├── post.py           # SnsPost 統一モデル
│   └── result.py         # PostResult
├── adapters/
│   ├── __init__.py
│   ├── article.py        # 金融記事 → SnsPost
│   ├── weekly_report.py  # 週次レポート → SnsPost
│   └── news_flash.py     # ニュース速報 → SnsPost
├── platforms/
│   ├── __init__.py
│   ├── note.py           # note.com（Playwright + Markdown フォールバック）
│   └── x.py              # X API v2
├── hook_generator.py     # Claude Agent SDK フック文生成
└── poster.py             # 投稿オーケストレーター
```

---

## 再利用する既存ファイル

| 参照元 | 用途 |
|--------|------|
| `src/news/core/sink.py` | PlatformProtocol の設計パターン |
| `src/news/core/article.py` | SnsPost モデルの Pydantic 構造 |
| `src/news/core/result.py` | PostResult の構造 |
| `src/news/summarizer.py` | HookGenerator の Claude Agent SDK パターン |
| `src/rss/core/http_client.py` | X API v2 の httpx リトライパターン |
| `src/rss/exceptions.py` | 例外階層パターン |
| `src/news/__init__.py` | パッケージ公開 API パターン |
| `snippets/sns-announcement.md` | SNS 告知テンプレート |
| `template/src/template_package/` | パッケージ構造テンプレート |

---

## ファイルマップ

| Wave | 操作 | ファイル | 説明 |
|------|------|---------|------|
| 1 | create | `src/sns/__init__.py` | パッケージ公開 API |
| 1 | create | `src/sns/py.typed` | PEP 561 マーカー |
| 1 | create | `src/sns/types.py` | 型定義（Enum, type alias） |
| 1 | create | `src/sns/errors.py` | 例外階層（SnsError, PlatformError, AuthenticationError 等） |
| 1 | create | `src/sns/config.py` | SnsConfig, NoteConfig, XConfig（Pydantic） |
| 1 | create | `src/sns/core/__init__.py` | core パッケージ |
| 1 | create | `src/sns/core/post.py` | SnsPost モデル（Pydantic BaseModel） |
| 1 | create | `src/sns/core/result.py` | PostResult モデル |
| 1 | create | `src/sns/core/platform.py` | PlatformProtocol（@runtime_checkable） |
| 2 | create | `src/sns/adapters/__init__.py` | adapters パッケージ |
| 2 | create | `src/sns/adapters/article.py` | article-meta.json + revised_draft.md → SnsPost |
| 2 | create | `src/sns/adapters/weekly_report.py` | weekly_report → SnsPost |
| 2 | create | `src/sns/adapters/news_flash.py` | ニュース速報 → SnsPost |
| 3 | create | `src/sns/platforms/__init__.py` | platforms パッケージ |
| 3 | create | `src/sns/platforms/note.py` | Playwright 自動化 + Markdown フォールバック |
| 3 | create | `src/sns/platforms/x.py` | X API v2 (httpx + OAuth) |
| 3 | create | `src/sns/hook_generator.py` | Claude Agent SDK フック文生成 |
| 4 | create | `src/sns/poster.py` | 投稿オーケストレーター |
| 4 | create | `src/sns/README.md` | パッケージドキュメント |
| 5 | modify | `pyproject.toml` | packages に `src/sns` 追加 |
| 5 | create | `tests/sns/conftest.py` | テストフィクスチャ |
| 5 | create | `tests/sns/unit/` | 単体テスト（7ファイル） |
| 5 | create | `tests/sns/property/` | プロパティテスト |

---

## リスク評価

| リスク | 影響度 | 対策 |
|--------|--------|------|
| note.com UI 変更で Playwright 破綻 | 高 | Markdown フォールバックを常に提供。セレクタを config 化 |
| X API v2 レート制限 | 中 | 投稿間隔設定可能化。指数バックオフ |
| note.com ログインセッション管理 | 中 | Cookie ベースのセッション永続化。切れ検知+フォールバック |
| Playwright 依存が重い | 低 | optional dependency として管理（既に pyproject.toml に設定済み） |

---

## 実装順序

### Wave 1: 基盤（モデル・Protocol・例外・設定）
- `core/post.py`, `core/result.py`, `core/platform.py`
- `types.py`, `errors.py`, `config.py`
- `__init__.py`, `py.typed`
- 依存: なし

### Wave 2: コンテンツアダプター
- `adapters/article.py`, `adapters/weekly_report.py`, `adapters/news_flash.py`
- 依存: Wave 1

### Wave 3: プラットフォーム実装 + フック生成
- `platforms/note.py`, `platforms/x.py`, `hook_generator.py`
- 依存: Wave 1, 2

### Wave 4: 統合・ドキュメント
- `poster.py`, `README.md`
- 依存: Wave 1-3

### Wave 5: ビルド設定・テスト
- `pyproject.toml` 修正、テストスイート
- 依存: Wave 1-4

---

## pyproject.toml 変更

```toml
# tool.hatch.build.targets.wheel.packages に追加
packages = [..., "src/sns"]

# optional-dependencies に追加
sns = [
    "tweepy>=4.14.0",  # X API v2（httpx直接なら不要）
]
```

---

## 検証方法

1. **Wave 1 完了後**: `make typecheck` で型チェック通過を確認
2. **Wave 2 完了後**: アダプターが article-meta.json から SnsPost を正しく変換できることを単体テストで確認
3. **Wave 3 完了後**: X API v2 のモックテスト、note.com の Markdown フォールバック出力確認
4. **Wave 4 完了後**: `poster.py` のE2E統合テスト（dry_run モードで全プラットフォーム通過確認）
5. **全Wave完了後**: `make check-all`（format, lint, typecheck, test）が全て成功
