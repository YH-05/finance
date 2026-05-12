# 廃止経緯: notebook/NSE/data/cache/nse/owners_rev2.json

**日付**: 2026-05-12
**廃止対象**: `notebook/NSE/data/cache/nse/owners_rev2.json`
**移動先**: `trash/2026-05-12_obsolete-owners_rev2/owners_rev2.json` (.gitignore 除外)
**関連議論**: `disc-2026-05-12-nse-owner-rev1-rerun`

## 背景

2026-05-12 セッションで、ユーザーが「rev1 に SAMMAAN 等が含まれていないのではないか」という疑念から `owners_rev1.json` をベースに `owners_rev2.json` を新規作成。
しかし正規化（ISIN ソート + キー昇順）後の SHA256 で完全一致を確認した。

| 項目 | rev1 | rev2 |
|------|------|------|
| エントリ数 | 632 | 632 |
| ISIN セット | 同一 | 同一 |
| カテゴリ | 同一 | 同一 |
| company name | 同一 | 同一 |
| normalize 後 SHA256 | 一致 | 一致 |
| ファイルサイズ | 88,328 bytes | 98,444 bytes（インデント差のみ） |

差分は **JSON フォーマット（インデント・キー順序）のみ**で、内容上の差分はゼロ。

## 真の問題

ユーザーが SAMMAAN 漏れを指摘した真の原因は rev2 でも rev1 でもなく、`build_owner_review_sheet.py` の **LEFT MERGE ロジック**にあった:

```python
# build_owner_review_sheet.py (line 133)
merged = cand.merge(rev1, on="isin", how="left")
```

- `cand` = `owner_candidates.csv` (NSE Phase 3/4 取得済 787 銘柄)
- これに rev1 (632銘柄) を LEFT MERGE
- → rev1 にあるが NSE 取得側で漏れた銘柄 (SAMMAAN 等 55件) は universe から欠落

## 廃止理由

- rev2 は rev1 と内容が完全一致のため、別ファイルとして保持する価値なし
- ユーザー方針: `feedback_trash_gitignored_pattern.md` に基づき trash/ へ移動

## 後続作業

`disc-2026-05-12-nse-owner-rev1-rerun` で以下を実施:
1. rev1 にあるが universe に無い 55 銘柄を export
2. うち NSE symbol 解決可能な 38 銘柄を再取得
3. 解決不能 17 銘柄 + 取得失敗銘柄は `nse_fetch_status` ラベル付きで rev1 ラベルのみ流用
4. nifty750_universe.csv に統合
