# P5-003: Publisher カテゴリ → GitHub Status 解決

## 概要

設定ファイルの status_mapping を使用して GitHub Status を決定する。

## フェーズ

Phase 5: GitHub Publisher

## 依存タスク

- P5-002: Publisher Issue 本文生成

## 成果物

- `src/news/publisher.py`（更新）

## 実装内容

```python
class Publisher:
    def _resolve_status(self, article: SummarizedArticle) -> tuple[str, str]:
        """カテゴリからGitHub Statusを解決

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事

        Returns
        -------
        tuple[str, str]
            (Status名, Status Option ID)

        Example
        -------
        >>> publisher._resolve_status(article)
        ("index", "3925acc3")
        """
        category = article.extracted.collected.source.category

        # status_mapping でカテゴリ → Status名 を解決
        # 例: "market" → "index", "tech" → "ai"
        status_name = self._status_mapping.get(category, "finance")  # デフォルト: finance

        # github_status_ids で Status名 → Option ID を解決
        # 例: "index" → "3925acc3"
        status_id = self._status_ids.get(status_name, self._status_ids["finance"])

        return status_name, status_id
```

設定ファイル参照:
```yaml
status_mapping:
  tech: "ai"
  market: "index"
  finance: "finance"
  yf_index: "index"
  yf_stock: "stock"
  yf_ai_stock: "ai"
  yf_sector_etf: "sector"
  yf_macro: "macro"

github_status_ids:
  index: "3925acc3"
  stock: "f762022e"
  sector: "48762504"
  macro: "730034a5"
  ai: "6fbb43d0"
  finance: "ac4a91b1"
```

## 受け入れ条件

- [ ] ArticleSource.category から GitHub Status を解決
- [ ] github_status_ids から Status ID を取得
- [ ] 未知のカテゴリの場合は "finance" がフォールバック
- [ ] pyright 型チェック成功

## 参照

- project.md: 設定ファイル - status_mapping, github_status_ids セクション
