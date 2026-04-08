# 議論メモ: NSE株主構成API — エンドポイント修正

**日付**: 2026-04-08
**議論ID**: disc-2026-04-08-nse-shareholding-fix
**参加**: ユーザー + AI

## 背景・コンテキスト

Wave1（PR #3901）で実装した `get_shareholding_pattern()` の実機テストを試みたところ、
`/api/corporates-shareholding` エンドポイントが404を返すことが判明。
Playwright MCPでNSEサイトのネットワークリクエストを監視し、正しいエンドポイントを特定・修正した。

## 調査の経緯

1. **初期テスト**: `CorporateCollector().get_shareholding_pattern("RELIANCE")` → JSONDecodeError
2. **原因切り分け**: NSEホームページが日本IPから403（geo-block）→ Cookie取得不可
3. **重要発見**: 2026-04-02の調査ドキュメント（Bug 2）に「NSE APIエンドポイントはCookieなしで直接アクセス可能」と記録あり
4. **Cookieなしテスト**: `/api/quote-equity` は200 OK、`/api/corporates-shareholding` は404
5. **Playwright MCP調査**: NSEサイトのネットワークリクエストを監視し、実際のエンドポイントを発見:
   ```
   /api/NextApi/apiClient/GetQuoteApi?functionName=getShareholdingPattern&symbol=RELIANCE&noOfRecords=5
   ```
6. **httpx直接テスト**: Cookieなしで200 OK、5四半期分のデータ取得成功

## 実際のAPIレスポンス構造

### RELIANCE（promoter あり）
```json
{
  "31-Dec-2025": {
    "ndsid": "207095",
    "series": "equity",
    "Total": "100.00",
    "public": {"name": "Public", "value": "49.99"},
    "promoter_group": {"name": "Promoter & Promoter Group", "value": "50.01"}
  }
}
```

### HDFCBANK（promoter なし）
```json
{
  "31-Mar-2026": {
    "ndsid": "207379",
    "series": "equity",
    "Total": "100.00",
    "public": {"name": "Public", "value": "100.00"}
  }
}
```

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-08-011 | shareholdingエンドポイントを `/api/corporates-shareholding` → `/api/NextApi/apiClient/GetQuoteApi?functionName=getShareholdingPattern` に変更 | Playwright MCPでNSEサイトのネットワークリクエストを監視して特定 |
| dec-2026-04-08-012 | `ShareholdingPattern` から `fii`/`dii` フィールドを削除。promoter/publicの2分類のみ | 実APIがFII/DII内訳を提供しない |
| dec-2026-04-08-013 | NSEのshareholdingエンドポイントはCookie不要で日本IPからアクセス可能 | httpx直接テストで200 OK確認済み |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-04-08-008 | PR #3902 をマージ（プロパティテスト修正） | 高 | pending |
| act-2026-04-08-009 | 他のNSEエンドポイントもNextApi形式に移行が必要か調査 | 中 | pending |

## 変更ファイル（7ファイル）

| ファイル | 変更内容 |
|---------|---------|
| `src/market/nse/constants.py` | `SHAREHOLDING_FIELD_MAP` を実API構造に更新 |
| `src/market/nse/types.py` | `ShareholdingPattern` — `fii`/`dii` 削除、`ndsid`/`series`/`total` 追加 |
| `src/market/nse/parsers.py` | dict形式パース対応、nested value抽出、`symbol` 引数追加 |
| `src/market/nse/collectors/corporate.py` | エンドポイントURL・パラメータ変更 |
| `src/market/nse/__init__.py` | docstring更新 |
| `tests/market/nse/unit/test_shareholding.py` | 全テスト書き換え（21件） |
| `tests/market/nse/property/test_parsers_property.py` | プロパティテスト更新 |

## 実機テスト結果

| 銘柄 | 結果 | 件数 |
|------|------|------|
| RELIANCE | promoter=50.01%, public=49.99% | 5四半期 |
| HDFCBANK | promoter="", public=100.00% | 5四半期 |

## 教訓

- site-investigator調査時にPlaywrightのCookieが使われるため、Cookieが必要なエンドポイントでも200を返す。**実装後は必ずhttpxからのCookieなし直接テストが必要**。
- NSEは `NextApi` プロキシ形式に移行中。既存エンドポイント（`/api/corporates-*`）は順次廃止される可能性がある。

## 参考情報

- **PR #3902**: https://github.com/YH-05/quants/pull/3902
- **直接mainコミット**: aeec404（本体修正6ファイル）
- **GitHub Project**: https://github.com/users/YH-05/projects/111
