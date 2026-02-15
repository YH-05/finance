# Project #46: IR Scraper Code Generator

## 概要

企業名またはティッカーシンボルを入力すると、その企業のIR（投資家向け情報）ページのPythonスクレイピングコードを自動生成するワークフロー。

## 目的

- IR情報の定期取得を効率化するため、企業ごとのスクレイピングコードを素早く生成する
- 日米両方の上場企業に対応
- 既存の `CompanyScraperEngine` パターンと互換性のあるコードを生成

## アーキテクチャ

```
/ir-scraper <ticker>
    ↓
Command (.claude/commands/ir-scraper.md)
    ↓
Skill (.claude/skills/ir-scraper-generator/SKILL.md)
    ├── Phase 1: 企業特定
    │   Web検索 + yfinance → 企業名 + IRページURL特定
    ├── Phase 2: IRページ分析
    │   Agent: ir-scraper-generator
    │   Playwright snapshot → DOM構造解析 → CSSセレクタ抽出
    ├── Phase 3: コード生成
    │   Agent: ir-scraper-generator (同一エージェント内)
    │   テンプレート + 分析結果 → Python スクレイピングコード
    └── Phase 4: 検証
        生成コードの構文チェック + dry run
    ↓
Output: src/dev/ir_scraper/scrapers/<company>.py
```

## 成果物

### コマンド・スキル・エージェント

| # | ファイル | 説明 |
|---|---------|------|
| 1 | `.claude/commands/ir-scraper.md` | `/ir-scraper <ticker>` スラッシュコマンド |
| 2 | `.claude/skills/ir-scraper-generator/SKILL.md` | ワークフロー制御スキル |
| 3 | `.claude/skills/ir-scraper-generator/guide.md` | IRページ分析・コード生成の詳細ガイド |
| 4 | `.claude/skills/ir-scraper-generator/templates/ir_scraper_template.py.md` | 生成コードのPythonテンプレート |
| 5 | `.claude/agents/ir-scraper-generator.md` | Playwright分析 + コード生成エージェント |

### Python パッケージ（src/dev/）

| # | ファイル | 説明 |
|---|---------|------|
| 6 | `src/dev/__init__.py` | R&Dパッケージ初期化 |
| 7 | `src/dev/ir_scraper/__init__.py` | IRスクレイパーモジュール初期化 |
| 8 | `src/dev/ir_scraper/types.py` | IR専用型定義（IRPageConfig, IRDocument等） |
| 9 | `src/dev/ir_scraper/identifier.py` | 企業特定ユーティリティ（ticker → IR page URL） |
| 10 | `src/dev/ir_scraper/scrapers/__init__.py` | 生成スクレイパー格納先 |

## ワークフロー詳細

### Phase 1: 企業特定

1. ティッカーシンボルまたは企業名を受け取る
2. Web検索 + yfinance API で企業情報を取得
   - 正式名称、ティッカー、証券コード
   - 公式サイトURL
3. IRページURLを特定
   - 一般的なパターン: `/ir/`, `/investor/`, `/investors/`, `ir.{domain}`
   - Web検索: `"{企業名}" IR investor relations site:{domain}`
4. IR URLが見つからない場合、ユーザーに手動入力を促す

### Phase 2: IRページ分析（エージェント）

1. Playwright で IRページにアクセス
2. `browser_snapshot` でDOM構造を取得
3. 以下を分析:
   - ドキュメント一覧のCSSセレクタ（テーブル、リスト等）
   - タイトル・日付・ファイルタイプのセレクタ
   - PDFリンクのパターン
   - ページネーションの有無
   - JavaScript動的レンダリングの必要性
4. 分析結果をJSON形式で出力

### Phase 3: コード生成（エージェント）

1. テンプレート `ir_scraper_template.py.md` を読み込み
2. Phase 2の分析結果を適用
3. 以下の要素を含むPythonコードを生成:
   - `IRPageConfig` データクラス（セレクタ、URL、オプション）
   - `scrape_ir_documents()` 非同期関数（httpx + lxml）
   - `parse_document_list()` 関数
   - `download_documents()` 関数（PDF対応）
   - `main()` CLI実行関数
4. `src/dev/ir_scraper/scrapers/<company_key>.py` に出力

### Phase 4: 検証

1. 生成コードの構文チェック（`python -c "import ast; ast.parse(...)"`)
2. 型チェック（pyright）
3. 可能であればdry run（実際にIRページにアクセスして取得テスト）

## 型定義（src/dev/ir_scraper/types.py）

```python
from dataclasses import dataclass, field
from typing import Literal

type IRDocumentType = Literal[
    "earnings_summary",      # 決算短信
    "securities_report",     # 有価証券報告書
    "quarterly_report",      # 四半期報告書
    "timely_disclosure",     # 適時開示
    "earnings_presentation", # 決算説明会資料
    "earnings_transcript",   # 決算説明会書き起こし (Earnings Call Transcript)
    "annual_report",         # 年次報告書 / 10-K
    "quarterly_filing",      # 10-Q
    "current_report",        # 8-K
    "press_release",         # プレスリリース
    "investor_presentation", # 投資家向けプレゼン
    "other",                 # その他
]

type Market = Literal["jp", "us", "other"]

@dataclass(frozen=True)
class IRPageConfig:
    company_key: str
    company_name: str
    ticker: str
    market: Market
    ir_url: str
    document_list_selector: str = "table tbody tr"
    document_title_selector: str = "td a"
    document_date_selector: str = "td.date"
    document_type_selector: str = "td.type"
    pdf_link_selector: str = "a[href$='.pdf']"
    requires_playwright: bool = False
    rate_limit_seconds: float = 3.0

@dataclass(frozen=True)
class IRDocument:
    url: str
    title: str
    document_type: IRDocumentType
    date: str | None = None
    pdf_url: str | None = None
    file_size: str | None = None
```

## 生成コードの例

```python
# src/dev/ir_scraper/scrapers/apple.py (自動生成)
"""Apple Inc. (AAPL) IRページスクレイパー.

自動生成日: 2026-02-14
IR URL: https://investor.apple.com/sec-filings/default.aspx
対象市場: US
"""
from __future__ import annotations

import asyncio

import httpx
from lxml.html import fromstring

from dev.ir_scraper.types import IRDocument, IRPageConfig

CONFIG = IRPageConfig(
    company_key="apple",
    company_name="Apple Inc.",
    ticker="AAPL",
    market="us",
    ir_url="https://investor.apple.com/sec-filings/default.aspx",
    document_list_selector="table.filing-list tbody tr",
    document_title_selector="td.views-field-title a",
    document_date_selector="td.views-field-field-filing-date",
    document_type_selector="td.views-field-field-filing-type",
    pdf_link_selector="td a[href$='.pdf']",
    requires_playwright=False,
    rate_limit_seconds=3.0,
)

async def scrape_ir_documents(
    config: IRPageConfig = CONFIG,
    max_documents: int = 20,
) -> list[IRDocument]:
    """IRドキュメント一覧を取得する."""
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(config.ir_url)
        response.raise_for_status()

    doc = fromstring(response.text)
    rows = doc.cssselect(config.document_list_selector)

    documents: list[IRDocument] = []
    for row in rows[:max_documents]:
        # タイトル抽出
        title_els = row.cssselect(config.document_title_selector)
        if not title_els:
            continue
        title = title_els[0].text_content().strip()
        url = title_els[0].get("href", "")

        # 日付抽出
        date_els = row.cssselect(config.document_date_selector)
        date = date_els[0].text_content().strip() if date_els else None

        # PDF URL抽出
        pdf_els = row.cssselect(config.pdf_link_selector)
        pdf_url = pdf_els[0].get("href") if pdf_els else None

        documents.append(
            IRDocument(
                url=url,
                title=title,
                document_type="other",
                date=date,
                pdf_url=pdf_url,
            )
        )

    return documents

if __name__ == "__main__":
    results = asyncio.run(scrape_ir_documents())
    for doc in results:
        print(f"[{doc.date}] {doc.title}")
        if doc.pdf_url:
            print(f"  PDF: {doc.pdf_url}")
```

## リスクと対策

| リスク | 対策 |
|--------|------|
| IRページの構造が企業ごとに大きく異なる | Playwright snapshotで実際のDOM構造を分析し企業固有のセレクタを特定 |
| JSレンダリングが必要なIRページがある | 生成コードに `requires_playwright` フラグを含め、Playwright対応パターンも生成可能にする |
| IR URLの自動特定が困難な場合がある | 自動特定失敗時にユーザーに手動URL入力を促すフォールバック |
| 生成コードのCSSセレクタが壊れる可能性 | StructureValidator パターンを参考に、ヘルスチェック機能を生成コードに含める |

## 依存関係

### 既存資産の活用

| 既存コンポーネント | 活用方法 |
|-------------------|---------|
| `CompanyScraperEngine` | 生成コードの設計パターンの参考 |
| `ScrapingPolicy` | レート制限・UA回転の参考 |
| `StructureValidator` | セレクタ健全性チェックの参考 |
| `src/edgar/` | SEC Filings関連のデータ取得（米国企業向け補完） |
| Playwright MCP | IRページのDOM分析に使用 |

### 新規依存

- `src/dev/` パッケージの新設（pyproject.toml への追加が必要）

## タスク分解

### Wave 1: 基盤構築（依存なし）

| # | タスク | 説明 |
|---|--------|------|
| 1 | src/dev パッケージ作成 | `__init__.py`, `ir_scraper/types.py`, `ir_scraper/identifier.py`, `ir_scraper/scrapers/__init__.py` |
| 2 | コマンド作成 | `.claude/commands/ir-scraper.md` |

### Wave 2: スキル・エージェント（Wave 1に依存）

| # | タスク | 説明 |
|---|--------|------|
| 3 | スキル作成 | `SKILL.md`, `guide.md`, `templates/ir_scraper_template.py.md` |
| 4 | エージェント作成 | `.claude/agents/ir-scraper-generator.md` |

### Wave 3: 統合・テスト（Wave 2に依存）

| # | タスク | 説明 |
|---|--------|------|
| 5 | 統合テスト | 実際の企業（AAPL, 7203.T等）で動作確認 |
| 6 | ドキュメント更新 | CLAUDE.md, README.md への追記 |

## ステータス

- [x] Phase 0: 方向確認
- [x] Phase 1: リサーチ
- [x] Phase 2: 計画策定
- [ ] Phase 3: タスク分解・Issue登録
- [ ] Phase 4: 実装
