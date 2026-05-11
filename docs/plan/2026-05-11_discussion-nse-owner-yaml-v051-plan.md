# 議論メモ: NSE オーナーラベリング yaml v0.5.1 方針確定 (exclude_when 機構導入)

**日付**: 2026-05-11
**議論ID**: `disc-2026-05-11-nse-owner-yaml-v051-plan`
**前回**: `disc-2026-05-07-nse-owner-labeling-implementation`
**関連プロジェクト**: project-106 (NSE パッケージ拡張 + 全銘柄データ取得ノートブック)

## 背景・コンテキスト

ユーザーから「NSE のオーナー企業抽出ロジックの構築について進捗を一覧で見せて」というリクエスト。Neo4j (Project / Discussion / Decision / ActionItem) と `docs/plan/` の関連 Markdown 19 ファイルから現状を復元し、Phase 1〜5 の進捗を時系列で整理。当面ゴール (NIFTY 750 = 800銘柄) のラベリングは **Precision 98.8% / Recall 100% / F1 99.4%** で実質完成済。

残課題のうち最優先である `act-2026-05-08-001` (yaml v0.5.1 で残 OWNER_WEAK 3 件解消) の方針を本セッションで確定。

## 残 OWNER_WEAK 3 件の状況

| 銘柄 | 現 hybrid | rev1 GT | promoter 内訳 | yaml 状況 |
|------|-----------|---------|---------------|-----------|
| NETWORK18 | OWNER_WEAK | Professional | 全員法人 (Reliance系 + Independent Media Trust) | OWNER と PROFESSIONAL が両方マッチ → UNKNOWN → OWNER_WEAK 降格 |
| JPPOWER | OWNER_WEAK | Owner | JAIPRAKASH ASSOCIATES + JAYPEE INFRA VENTURES | yaml 未マッチ |
| ESCORTS | OWNER_WEAK | Owner | Nanda 一族 6 名 + KUBOTA + 関連法人 9 社 | yaml 未マッチ |

JPPOWER / ESCORTS は owner_keywords 追加で素直に解決可能。NETWORK18 は OWNER+PROFESSIONAL 両マッチ問題のためロジック設計判断が必要。

## NETWORK18 の OWNER+PROFESSIONAL 両マッチ問題分析

現状ロジック (build_owner_review_sheet.py v0.5.0):「OWNER と Professional/State/MNC の両方にキーワードマッチ → UNKNOWN → ハイブリッドで OWNER_WEAK 降格」

### 全 dual match 銘柄の挙動 (4 件)

| 銘柄 | 両マッチ | 現 hybrid | rev1 | 現状判定の正誤 |
|------|----------|-----------|------|----------------|
| NETWORK18 | OWNER+PROFESSIONAL | OWNER_WEAK | Professional | ❌ Professional 確定にしたい |
| TATACOMM | PROFESSIONAL+STATE | NOT_OWNER (Professional) | Professional | ✅ 既に正しい |
| IDEA | OWNER+STATE | NOT_OWNER (State) | State | ✅ 既に正しい |
| HINDZINC | OWNER+STATE | OWNER (Vedanta) | Owner | ✅ 既に正しい (汎用ルール変更で副作用化) |

### RELIANCE INDUSTRIES LIMITED keyword の使用状況 (3 件)

| 銘柄 | 結果 | RIL keyword の役割 |
|------|------|--------------------|
| HATHWAY | OWNER (TP) | Raheja 自然人 promoter もいるので RIL なくても判定可能 |
| ALOKINDS | OWNER (TP) | RIL keyword だけで OWNER 判定 (RIL 厳密化で副作用化) |
| NETWORK18 | OWNER_WEAK | RIL マッチ + Independent Media Trust マッチで競合 |

`Independent Media Trust` は NETWORK18 専用キーワード (他銘柄には出現せず)。

## 4 つの解決策の比較

### Option A: 汎用 Professional/State/MNC 優先ルール

ロジックで「professional/state/mnc にマッチしたら owner_keywords を無視」。

→ HINDZINC で副作用 (Vedanta Owner 判定が State に変わる)、FN +1 / Recall 100% → 99.8%。**却下**。

### Option B: yaml に exclude_when 機構を追加 (採用)

owner_keywords にエントリ単位で除外条件を持たせる:

```yaml
- keyword: "RELIANCE INDUSTRIES LIMITED"
  family: "Ambani"
  exclude_when_also_matches: ["Independent Media Trust"]
  note: "Independent Media Trust 同時マッチは信託 vehicle 経由 → Professional 扱い"
```

→ NETWORK18 のみピンポイント修正、HATHWAY / ALOKINDS / HINDZINC への副作用ゼロ、yaml スキーマ拡張で今後の類似ケースにも対応可能。**採用**。

### Option C: vehicle 名優先ロジック

「holding vehicle / 信託名がマッチした側を優先」。vehicle 判定基準の新規定義が必要で設計複雑化、HINDZINC でも State 側に副作用リスク。**却下**。

### Option D: RELIANCE INDUSTRIES LIMITED keyword 厳密化

`Reliance Industrial Investments and Holdings` 等に置換。

→ ALOKINDS が RIL マッチ消滅 + 自然人 promoter なしで判定不能化。**却下**。

## 決定事項

| ID | 内容 | ステータス |
|----|------|-----------|
| dec-2026-05-11-003 | yaml v0.5.1 で Option B (exclude_when 機構追加) を採用 | active |
| dec-2026-05-11-004 | NETWORK18: RIL keyword に exclude_when_also_matches: ["Independent Media Trust"] 追加 | active |
| dec-2026-05-11-005 | JPPOWER: owner_keywords に "JAIPRAKASH ASSOCIATES" / "JAYPEE INFRA VENTURES" 追加 (family: Gaur) | active |
| dec-2026-05-11-006 | ESCORTS: owner_keywords に "NIKHIL NANDA" / "HAR PARSHAD AND COMPANY" / "NIKY TASHA" 追加 (family: Nanda)。Kubota は MNC 扱いせず rev1=Owner を尊重 | active |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|----|------|--------|-----------|
| act-2026-05-11-018 | yaml v0.5.1 リリース + exclude_when 機構実装 + 再実行で OWNER_WEAK 0 到達確認 | 高 | pending |
| act-2026-05-08-001 | (旧) yaml v0.5.1 で残 OWNER_WEAK 3件解消 | — | **superseded by act-2026-05-11-018** |

### act-2026-05-11-018 実装内訳

1. `data/config/nse_promoter_classifier.yaml`:
   - `exclude_when_also_matches` スキーマフィールド追加
   - RELIANCE INDUSTRIES LIMITED に Independent Media Trust 排他条件追加
   - JPPOWER 用 2 keyword (JAIPRAKASH ASSOCIATES / JAYPEE INFRA VENTURES) 追加
   - ESCORTS 用 3 keyword (NIKHIL NANDA / HAR PARSHAD AND COMPANY / NIKY TASHA) 追加
2. `notebook/NSE/scripts/build_owner_review_sheet.py`:
   - yaml ロード/マッチロジックに `exclude_when_also_matches` 評価を追加 (10-20 行)
3. `build_owner_review_sheet.py` を再実行し `owner_review_sheet.csv` 更新
4. メトリクス確認 — 期待値: OWNER_WEAK 3→0、TP=414/FP=4/FN=0/TN=161、**Precision 99.04% / Recall 100% / F1 99.5%**

## 期待メトリクス推移

| 段階 | 銘柄数 | TP | FP | FN | TN | Precision | Recall | F1 | OWNER_WEAK |
|------|--------|----|----|----|----|-----------|--------|-----|-----------|
| v0.5.0 (現状) | 800 | 412 | 5 | 0 | 160 | 98.8% | 100% | 99.4% | 3 |
| v0.5.1 (期待) | 800 | 414 | 4 | 0 | 161 | **99.04%** | **100%** | **99.5%** | **0** |

## 次回の議論トピック

- act-2026-05-11-018 実装完了後、メトリクスが期待値通りか確認 (NETWORK18 が確実に Professional 確定するか、HINDZINC への副作用がないか)
- act-2026-05-07-002 (owner_companies.csv 確定版 + analyst universe ISIN JOIN) への着手判断
- 完成宣言の判定基準 (Precision 99.04% で十分か、追加品質ゲートが必要か)
- pending のまま実質完了/代替済み 4 件のステータス整理 (act-2026-04-17-006, -007, -011, act-2026-04-16-005)

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-11-nse-owner-yaml-v051-plan`
  - Decision: `dec-2026-05-11-003` (Option B 採用)、`dec-2026-05-11-004` (NETWORK18)、`dec-2026-05-11-005` (JPPOWER)、`dec-2026-05-11-006` (ESCORTS)
  - ActionItem: `act-2026-05-11-018` (v0.5.1 実装)、`act-2026-05-08-001` (superseded)
  - リレーション: `(disc)-[:RESULTED_IN]->(dec×4)`、`(disc)-[:PRODUCED]->(act-018)`、`(act-018)-[:SUPERSEDES]->(act-2026-05-08-001)`、`(disc)-[:FOLLOWS]->(disc-2026-05-07-nse-owner-labeling-implementation)`、`(project-106)-[:HAS_DISCUSSION]->(disc)`
- **ドキュメント**: このファイル (`docs/plan/2026-05-11_discussion-nse-owner-yaml-v051-plan.md`)
- **対象コード**: `data/config/nse_promoter_classifier.yaml` (v0.5.0 → v0.5.1)、`notebook/NSE/scripts/build_owner_review_sheet.py`
