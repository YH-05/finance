# news.extractors

記事本文のテキスト抽出モジュール。

## 概要

`CollectedArticle`（URL とメタデータのみ）から本文テキストを抽出し、`ExtractedArticle`（本文テキスト付き）に変換します。Trafilatura ベースの抽出と Playwright ベースの JS レンダリングフォールバックに対応。

**抽出フロー:**

```
CollectedArticle → Trafilatura抽出 → [失敗時] → Playwright フォールバック → ExtractedArticle
```

**主な特徴:**

- **自動リトライ**: 指数バックオフ（1s, 2s, 4s）による自動リトライ
- **最小文字数チェック**: `min_body_length` 未満の本文は失敗扱い
- **User-Agent ローテーション**: レート制限対策
- **Playwright フォールバック**: JS レンダリングが必要なページに対応
- **ステータス分類**: SUCCESS / FAILED / PAYWALL / TIMEOUT

## クイックスタート

### 基本的な抽出

```python
from news.extractors import TrafilaturaExtractor

extractor = TrafilaturaExtractor(
    min_body_length=200,
    max_retries=3,
    timeout_seconds=30,
)

result = await extractor.extract(collected_article)
if result.extraction_status == ExtractionStatus.SUCCESS:
    print(f"抽出成功: {len(result.body_text)} 文字")
else:
    print(f"抽出失敗: {result.error_message}")
```

### Playwright フォールバック付き

```python
from news.extractors import TrafilaturaExtractor
from news.config.models import ExtractionConfig

config = ExtractionConfig()

# コンテキストマネージャーで Playwright のライフサイクルを管理
async with TrafilaturaExtractor.from_config(config) as extractor:
    result = await extractor.extract(collected_article)
    # extraction_method: "trafilatura" or "trafilatura+playwright"
    print(f"抽出方法: {result.extraction_method}")
```

## API リファレンス

### BaseExtractor（ABC）

すべての Extractor の抽象基底クラス。

| メソッド/プロパティ | 型 | 説明 |
|-------------------|-----|------|
| `extractor_name` | `str`（抽象） | 抽出器名を返す |
| `extract(article)` | `ExtractedArticle`（抽象） | 記事本文を抽出する（async） |

### TrafilaturaExtractor

Trafilatura ベースの記事本文抽出器。`BaseExtractor` を継承。

**コンストラクタ:**

```python
TrafilaturaExtractor(
    min_body_length: int = 200,
    max_retries: int = 3,
    timeout_seconds: int = 30,
    user_agent_config: UserAgentRotationConfig | None = None,
    playwright_config: PlaywrightFallbackConfig | None = None,
    extraction_config: ExtractionConfig | None = None,
)
```

| パラメータ | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `min_body_length` | `int` | 200 | 最小本文文字数 |
| `max_retries` | `int` | 3 | 最大リトライ回数 |
| `timeout_seconds` | `int` | 30 | タイムアウト秒数 |
| `user_agent_config` | `UserAgentRotationConfig \| None` | None | UA ローテーション設定 |
| `playwright_config` | `PlaywrightFallbackConfig \| None` | None | Playwright フォールバック設定 |

**メソッド:**

| メソッド | 説明 | 戻り値 |
|---------|------|--------|
| `extract(article)` | 記事本文を抽出（async） | `ExtractedArticle` |
| `from_config(config)` | ExtractionConfig から生成（classmethod） | `TrafilaturaExtractor` |

**コンテキストマネージャー:**

`async with` で使用すると Playwright フォールバックが有効化されます。

### PlaywrightExtractor

Playwright ベースの JS レンダリング対応抽出器。

**主な用途:**

- JS レンダリングが必要なページの本文抽出
- TrafilaturaExtractor のフォールバックとして使用

### ExtractionStatus

| ステータス | 説明 |
|-----------|------|
| `SUCCESS` | 抽出成功 |
| `FAILED` | 抽出失敗 |
| `PAYWALL` | ペイウォール検出 |
| `TIMEOUT` | タイムアウト |

## モジュール構成

```
news/extractors/
├── __init__.py       # パッケージエクスポート
├── base.py           # BaseExtractor 抽象基底クラス
├── trafilatura.py    # TrafilaturaExtractor 実装
├── playwright.py     # PlaywrightExtractor 実装
└── README.md         # このファイル
```

## 依存ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| trafilatura | HTML からの本文抽出 |
| playwright | JS レンダリング（オプション） |
| rss.services.article_extractor | 既存の抽出器ラッパー |

## 関連モジュール

- [news.collectors](../collectors/README.md) - 前段階: 記事メタデータ収集
- [news.models](../README.md) - データモデル（CollectedArticle → ExtractedArticle）
- [news.summarizer](../README.md) - 次段階: AI 要約
- [news.config](../config/README.md) - 抽出設定（ExtractionConfig）
