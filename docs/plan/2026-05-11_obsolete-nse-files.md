# NSE Owner Extraction — 廃止ファイル経緯ドキュメント (2026-05-11)

project-106 NSE owner labeling の v0.5.1 リリース時に役割終了したファイル群の経緯記録。
**実体は `trash/2026-05-11_nse-owner-obsolete/` に存在** (`.gitignore` 除外のため git 履歴外、ローカルのみ)。
本ドキュメントは git 管理側から廃止経緯をトレース可能にする目的で `docs/plan/` に配置。

## 関連 housekeeping 議論

- 議論メモ: `docs/plan/2026-05-11_discussion-nse-owner-housekeeping.md`
- Neo4j: `disc-2026-05-11-nse-owner-housekeeping` / `dec-2026-05-11-009` (3層クリーンアップ方式) / `act-2026-05-11-022`

## 廃止ファイル一覧

### v0.5.0 提案・調査資料 (yaml v0.5.1 リリースで陳腐化)

| ファイル | 元の位置 | 役割 | 廃止理由 |
|----------|---------|------|----------|
| `yaml_v0.5.0_proposal.md` | `notebook/NSE/data/exports/nse/` | v0.5.0 拡張提案 (P0 10 件の判定ドラフト) | dec-2026-05-07-005 で承認 → v0.5.0 リリース → さらに v0.5.1 (act-2026-05-11-018) に更新済 |
| `yaml_v0.5.0_evidence.md` | 同上 | P0 銘柄の Web 裏取り調査結果 | v0.5.0 に反映後、HCG/STYRENIX を v0.5.1 で訂正済 (dec-2026-05-08-001/002) |
| `yaml_extension_candidates.md` | 同上 | rev1 圏外 OWNER_WEAK 銘柄リスト | v0.5.0 提案の前段、v0.5.1 まで反映済 |

### shareholding データの古いバージョン

| ファイル | 元の位置 | サイズ | 廃止理由 |
|----------|---------|--------|----------|
| `_shareholding_detail.csv` | `notebook/NSE/data/exports/nse/` | 9.3 MB | `shareholding_detail.csv` (May 7, 11.9 MB) で更新済。`_` 接頭辞は古いバックアップ (Apr 17 時点) |
| `_shareholdings.csv` | 同上 | 7.1 MB | `shareholdings.csv` (May 7, 9.0 MB) で更新済 |

### nifty750_universe.csv に集約された冗長ファイル

| ファイル | 元の位置 | 役割 | 廃止理由 |
|----------|---------|------|----------|
| `owner_companies.csv` | `notebook/NSE/data/exports/nse/` | 当初は OWNER 600 件のみだったが、ユーザー要望で全 800 銘柄 (NOT_OWNER 含む) + is_owner_company 列に拡張 → nifty750_universe.csv とほぼ同内容になった | dec-2026-05-11-011 で `nifty750_universe.csv` に集約。`df[df["is_owner_company"]]` でフィルタすれば旧 owner_companies.csv 相当の OWNER 600 件を取得可能 |

## 関連 Neo4j ノード

- Discussion: `disc-2026-05-11-nse-owner-yaml-v051-plan` / `disc-2026-05-11-nse-owner-v051-implementation`
- Decision: `dec-2026-05-11-003` 〜 `008`
- ActionItem: `act-2026-05-11-018` (v0.5.1 実装、completed)

## 復元したい場合

```bash
mv trash/2026-05-11_nse-owner-obsolete/<filename> notebook/NSE/data/exports/nse/
git add notebook/NSE/data/exports/nse/<filename>
```

注: `trash/` は `.gitignore` 除外のため `git mv` ではなく `mv` を使う。

## 参照ドキュメント

- 計画: `docs/plan/2026-05-11_discussion-nse-owner-yaml-v051-plan.md`
- 実装: `docs/plan/2026-05-11_nse-owner-v051-implementation.md`
- yaml 履歴: `data/config/nse_promoter_classifier.yaml` (changelog セクション)
