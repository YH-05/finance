"""
ddg_search.py
"""

import json

from ddgs import DDGS
from mcp.server.fastmcp import FastMCP

# MCPサーバーの定義
mcp = FastMCP("DuckDuckGo Search")


@mcp.tool()
def web_search(query: str, site_limit: str = None, max_results: int = 5) -> str:
    """
    DuckDuckGoを使ってWeb検索を行います。

    Parameters
    ----------
    query : str
        検索したいキーワード
    site_limit : str, optional
        検索を特定のドメインに限定する場合に指定します (例: "github.com", "qiita.com")
    max_results : int, default 5
        取得する検索結果の最大数

    Returns
    -------
    str
        検索結果のJSON文字列
    """

    # 検索クエリの構築
    # site_limitが指定されている場合は、クエリに "site:domain" を追加する
    # ddgsの仕様上、キーワード文字列に含めるのが正解です
    final_query = query
    if site_limit:
        final_query = f"{query} site:{site_limit}"

    results = []

    # DDGS().text()の使用 (最新のdeedy5/ddgs仕様に準拠)
    # backend="auto" で最適な接続先を自動選択させます
    try:
        raw_results = DDGS().text(
            keywords=final_query,
            region="wt-wt",
            safesearch="moderate",
            max_results=max_results,
            backend="auto",
        )

        # 結果が見つからない場合、raw_resultsは空のリストまたはNoneになる可能性があります
        if not raw_results:
            return "検索結果が見つかりませんでした。"

        # AIが読みやすい形式に整形
        for res in raw_results:
            results.append(
                {
                    "title": res.get("title", "No Title"),
                    "link": res.get("href", ""),
                    "snippet": res.get("body", ""),
                }
            )

        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"検索中にエラーが発生しました: {e!s}"


if __name__ == "__main__":
    # スクリプトとして実行された際にMCPサーバーを開始
    mcp.run()
