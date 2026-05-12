# rev1 圏内・NSE 解決不能 17 銘柄の分類根拠

**生成元**: act-2026-05-12-003 (`disc-2026-05-12-nse-owner-rev1-rerun`)
**生成日**: 2026-05-12

## 背景

`notebook/NSE/data/cache/nse/owners_rev1.json` (632 銘柄) と現 `nifty750_universe.csv` の差分 55 銘柄のうち、
NSE `stocks` テーブルで symbol が解決できない 17 銘柄を抽出。

これらは **NSE Phase 3/4 では取得できない**ため、`nse_fetch_status = "unresolvable_isin"` ラベルを付与し、
`owner_flag_final = rev1 ラベル流用` で universe に統合した。

## 解決不能の主要パターン

| パターン | 件数 | 説明 |
|---------|------|------|
| M&A 消滅 | 7 | 親会社合併・買収による上場廃止 |
| REIT/InvIT | 5 | 不動産投信・インフラ投信（株式とは別資産クラス、NSE stocks テーブル対象外） |
| 上場廃止/破綻 | 3 | 経営破綻・自主廃止 |
| ISIN 変更（Demerger 後） | 1 | PIRAMAL（demerger 後の新 ISIN は別） |
| Holding 廃止/SFB 統合 | 1 | UJJIVAN Financial → UJJIVAN SFB |

## 17 銘柄の詳細

| ISIN | rev1 社名 | rev1 カテゴリ | 推定理由 | 最終分類 |
|------|----------|--------------|----------|----------|
| INE001A01036 | HOUSING DEVELOPMENT FINANCE | Professional | HDFC Ltd → HDFC Bank と合併消滅 (2026-07 統合) | NOT_OWNER (rev1 流用) |
| INE041025011 | EMBASSY OFFICE PARKS REIT | Owner | REIT（不動産投信、株式とは別資産クラス） | OWNER (rev1 流用) |
| INE043D01016 | IDFC LTD | Professional | IDFC Ltd → IDFC First Bank に合併消滅 (2025-10) | NOT_OWNER (rev1 流用) |
| INE0BWS23018 | ALTIUS TELECOM INFRASTRUCTUR | Professional | InvIT/Infrastructure trust（株式とは別資産クラス） | NOT_OWNER (rev1 流用) |
| INE0CCU25019 | MINDSPACE BUSINESS PARKS REI | Owner | REIT（不動産投信、株式とは別資産クラス） | OWNER (rev1 流用) |
| INE0FDU25010 | BROOKFIELD INDIA REAL ESTATE | MNC | REIT（不動産投信、株式とは別資産クラス） | NOT_OWNER (rev1 流用) |
| INE0GGX23010 | POWERGRID INFRASTRUCTURE INV | State | InvIT/Power InvIT（株式とは別資産クラス） | NOT_OWNER (rev1 流用) |
| INE0NDH25011 | NEXUS SELECT TRUST | Professional | REIT（不動産投信、株式とは別資産クラス） | NOT_OWNER (rev1 流用) |
| INE140A01024 | PIRAMAL ENTERPRISES LTD | Owner | Demerger により ISIN 変更（PIRAMAL PHARMA 分離後の新 ISIN は別） | OWNER (rev1 流用) |
| INE274G01010 | DHANI SERVICES LTD | Owner | DHANI Services 上場廃止 | OWNER (rev1 流用) |
| INE334L01012 | UJJIVAN FINANCIAL SERVICES L | Professional | UJJIVAN Financial → UJJIVAN SFB に合併消滅 | NOT_OWNER (rev1 流用) |
| INE455F01025 | JAIPRAKASH ASSOCIATES LTD | Owner | Jaiprakash Associates 上場廃止/破綻 | OWNER (rev1 流用) |
| INE493A01027 | TATA COFFEE LTD | Professional | Tata Coffee → Tata Consumer Products に合併消滅 | NOT_OWNER (rev1 流用) |
| INE752P01024 | FUTURE RETAIL LTD | Owner | Future Retail 上場廃止/破綻 | OWNER (rev1 流用) |
| INE763G01038 | ICICI SECURITIES LTD | Professional | ICICI Securities → ICICI Bank が完全買収・上場廃止 (2026-04) | NOT_OWNER (rev1 流用) |
| INE778U01029 | TCNS CLOTHING CO LTD | Owner | TCNS Clothing → ABFRL に合併消滅 | OWNER (rev1 流用) |
| INE886H01027 | TV18 BROADCAST LTD | Owner | TV18 Broadcast → Network18 に合併消滅 (2024-09 統合) | OWNER (rev1 流用) |

## 加えて: Phase 4 取得失敗 1 銘柄

| ISIN | Symbol | rev1 社名 | rev1 カテゴリ | 失敗理由 | 最終分類 |
|------|--------|----------|--------------|----------|----------|
| INE118H01025 | BSE | BSE LTD | Professional | XBRL namespace mismatch (BSE 自社 XBRL の taxonomy が NSE 想定と異なる) | NOT_OWNER (rev1 流用) |

## owner_candidates.csv / nifty750_universe.csv での扱い

これらの 18 銘柄 (17 unresolvable + 1 BSE) は以下のフィールドで識別可能:

- `nse_fetch_status`: `unresolvable_isin` | `phase4_failed_xbrl`
- `owner_flag`: `rev1_label_only_owner` | `rev1_label_only_professional` | `rev1_label_only_mnc` | `rev1_label_only_state`
- `report_date`: 空欄
- `promoter_total_pct` 等の NSE メタ: 0 または空欄

投資戦略側で「NSE メタが必要な銘柄のみ」を取り出す場合:

```python
df = pd.read_csv("notebook/NSE/data/exports/nse/nifty750_universe.csv")
fully_resolved = df[df["nse_fetch_status"] == "ok"]  # 837 銘柄
```

## 関連ファイル

- `notebook/NSE/data/exports/nse/rev1_missing_from_universe.csv` (55 件)
- `notebook/NSE/data/exports/nse/rev1_unresolvable_resolution.csv` (17 件)
- `notebook/NSE/data/exports/nse/refetch_rev1_log.json` (38 件再取得試行ログ)
- `notebook/NSE/data/exports/nse/persist_rev1_log.json` (37 件永続化ログ)
