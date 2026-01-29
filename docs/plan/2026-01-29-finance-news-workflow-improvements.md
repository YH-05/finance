# 金融ニュース収集ワークフロー改善計画

**作成日**: 2026-01-29
**ステータス**: 提案

## 背景

2026-01-29 の `/finance-news-workflow` 実行で以下の問題が判明：

1. **Index テーマの Task 委譲失敗**: news-article-fetcher への委譲ができずIssue作成が保留
2. **Stock テーマの本文抽出失敗**: CNBC/Seeking Alpha の動的コンテンツ・ペイウォールで14件失敗

### 実行結果サマリー

| テーマ | 新規Issue | 問題 |
|--------|----------|------|
| Index | 16件保留 | Task委譲失敗 |
| Stock | 0件 | 本文抽出失敗（CNBC動的コンテンツ） |
| Sector | 0件 | 全重複 |
| Macro | 14件 | 正常 |
| AI | 16件 | 正常 |
| Finance | 17件 | 正常 |

---

## Issue 1: Task 委譲の不安定性

### 現状

- エージェント定義では `news-article-fetcher` への Task 委譲を設計
- 実行時に一部エージェント（Index）で Task ツールが利用できず保留
- 他のエージェント（Macro, AI, Finance）は直接 `gh issue create` を実行して成功

### 原因分析

1. **ネストした Task 呼び出しの制限**: サブエージェントがさらにサブエージェントを呼び出す際の制限
2. **LLM 判断のばらつき**: 同じ定義でもエージェントごとに異なる実行パスを選択

### 改善案

#### Option A: 直接実行方式に統一（推奨）

`news-article-fetcher` への委譲をやめ、各テーマエージェントが直接 Issue 作成を実行。

**メリット**:
- シンプルな処理フロー
- ネスト制限を回避
- 実績あり（Macro, AI, Finance で成功）

**デメリット**:
- 各エージェント定義にIssue作成ロジックが重複
- WebFetch + 要約生成の処理が各エージェントに分散

**変更内容**:
```markdown
# finance-news-index.md の Phase 4 を変更

Phase 4: Issue作成（直接実行）
├── WebFetch で記事本文取得
├── 日本語要約生成
├── gh issue create 実行
├── gh project item-add 実行
└── Status/Date フィールド設定
```

#### Option B: 委譲を維持しつつ信頼性向上

`news-article-fetcher` 委譲を維持しつつ、フォールバック処理を追加。

**メリット**:
- 処理ロジックを一元管理
- 共通処理の再利用

**デメリット**:
- 複雑な制御フロー
- ネスト制限の根本解決にならない

**変更内容**:
```markdown
Phase 4: バッチ投稿（フォールバック付き）
├── Task(news-article-fetcher) 試行
├── 失敗時 → 直接 gh issue create にフォールバック
└── 結果をマージして報告
```

### 推奨

**Option A（直接実行方式）** を推奨。理由：
- Macro, AI, Finance で実績あり
- シンプルで予測可能な動作
- メンテナンスコストが低い

---

## Issue 2: CNBC 動的コンテンツの本文抽出

### 現状

Stock テーマで以下の問題が発生：

| ソース | 問題 | 影響件数 |
|--------|------|---------|
| CNBC | JavaScript で動的にコンテンツを読み込み | 12件 |
| Seeking Alpha | ペイウォール | 2件 |

trafilatura（現在の本文抽出ライブラリ）は静的 HTML のみ対応。

### 失敗した記事例

- Samsung's profit triples, beating estimates as AI chip demand fuels memory shortage
- Microsoft stock drops 7% on slowing cloud growth
- IBM jumps 8% on earnings beat
- Meta shares jump 10% on stronger-than-expected revenue forecast
- Chip giant ASML surges 7% as AI boom fuels record orders

### 改善案

#### Option C: Playwright ヘッドレスブラウザ導入

MCP Playwright サーバーを活用して動的コンテンツを取得。

**実装方針**:
```python
# article_content_checker.py の Tier 構成を拡張

Tier 1: httpx + trafilatura（高速、静的サイト用）
    ↓ 失敗時
Tier 2: MCP Playwright（動的サイト用）
    ├── mcp__playwright__browser_navigate
    ├── mcp__playwright__browser_snapshot
    └── HTML から本文抽出
    ↓ 失敗時
Tier 3: WebFetch（フォールバック）
```

**対象サイト**:
- cnbc.com（動的コンテンツ）
- bloomberg.com（一部動的）
- その他 JavaScript 依存サイト

**メリット**:
- JavaScript 実行後のコンテンツ取得可能
- ペイウォール回避（一部）
- 既存 MCP インフラを活用

**デメリット**:
- 処理時間増加（ブラウザ起動オーバーヘッド）
- リソース消費増加

#### Option D: RSS Summary ベース簡易 Issue

本文取得できない場合、RSS の summary 情報で簡易 Issue を作成。

**実装方針**:
```python
# 本文取得失敗時のフォールバック

if content_extraction_failed:
    issue_body = f"""
## 概要
{rss_summary}

## 元記事
🔗 {article_url}

⚠️ 本文の自動取得に失敗したため、RSS 要約を表示しています。
"""
```

**メリット**:
- 情報の取り漏れを防止
- 実装が簡単

**デメリット**:
- 要約品質が RSS 依存
- 詳細情報が不足

#### Option E: 代替フィード追加

CNBC の代わりに静的コンテンツを提供するソースを追加。

**候補フィード**:
- Yahoo Finance（静的）
- Reuters（静的）
- Investing.com（静的）

**メリット**:
- 抽出成功率向上
- 多様なソースからの情報収集

**デメリット**:
- フィード管理の複雑化
- 重複記事の増加

### 推奨

**Option C + D の組み合わせ** を推奨：
1. Playwright で動的サイト対応（優先度高いニュース）
2. 失敗時は RSS Summary で簡易 Issue（情報取り漏れ防止）

---

## 実装優先度

| 優先度 | 項目 | 工数 | 効果 |
|--------|------|------|------|
| P1 | Option A: 直接実行方式 | 小 | 高 |
| P2 | Option D: RSS Summary フォールバック | 小 | 中 |
| P3 | Option C: Playwright 導入 | 中 | 高 |
| P4 | Option E: 代替フィード追加 | 小 | 中 |

---

## 関連 Issue

- #1853: Tier 1 失敗時の自動フォールバック実装
- #1852: article_content_checker の閾値緩和
- #1854: バックグラウンドエージェントのタイムアウト対策
- #1855: ワークフロー処理の簡素化

---

## 次のアクション

1. [ ] Option A の実装（エージェント定義の更新）
2. [ ] Option D の実装（RSS Summary フォールバック）
3. [ ] Option C の設計・実装（Playwright 統合）
4. [ ] パフォーマンス計測と最適化
