# P5-002: Publisher Issue 本文生成

## 概要

project.md に記載の 4 セクション構造で Issue 本文を生成する。

## フェーズ

Phase 5: GitHub Publisher

## 依存タスク

- P5-001: Publisher 基本クラス構造作成

## 成果物

- `src/news/publisher.py`（更新）

## 実装内容

```python
class Publisher:
    def _generate_issue_body(self, article: SummarizedArticle) -> str:
        """Issue本文を生成

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事

        Returns
        -------
        str
            Markdown形式のIssue本文
        """
        summary = article.summary
        collected = article.extracted.collected

        # キーポイントをマークダウンリストに変換
        key_points_md = "\n".join(f"- {point}" for point in summary.key_points)

        # 関連情報（オプション）
        related_info_section = ""
        if summary.related_info:
            related_info_section = f"""
## 関連情報
{summary.related_info}
"""

        body = f"""# {collected.title}

## 概要
{summary.overview}

## キーポイント
{key_points_md}

## 市場への影響
{summary.market_impact}
{related_info_section}
---
**ソース**: {collected.source.source_name}
**公開日**: {collected.published.strftime('%Y-%m-%d %H:%M') if collected.published else '不明'}
**URL**: {collected.url}
"""
        return body

    def _generate_issue_title(self, article: SummarizedArticle) -> str:
        """Issueタイトルを生成

        Parameters
        ----------
        article : SummarizedArticle
            要約済み記事

        Returns
        -------
        str
            Issueタイトル
        """
        category = article.extracted.collected.source.category
        status = self._status_mapping.get(category, "other")
        return f"[{status}] {article.extracted.collected.title}"
```

## 受け入れ条件

- [ ] 概要、キーポイント、市場への影響、関連情報の 4 セクション
- [ ] ソース、公開日、URL のメタデータ
- [ ] キーポイントがマークダウンリストとして出力される
- [ ] 関連情報がない場合はセクションを省略
- [ ] タイトルにカテゴリプレフィックスが付与される
- [ ] pyright 型チェック成功

## 参照

- project.md: Issue本文フォーマット セクション
