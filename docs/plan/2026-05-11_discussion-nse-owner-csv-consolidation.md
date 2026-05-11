# 議論メモ: owner_companies.csv の拡張要望 → nifty750_universe.csv への集約

**日付**: 2026-05-11
**議論ID**: `disc-2026-05-11-nse-owner-csv-consolidation`
**前回**: `disc-2026-05-11-nse-owner-clarifications-and-gaps`
**関連プロジェクト**: project-106 (NSE パッケージ拡張 + 全銘柄データ取得ノートブック)

## 背景・コンテキスト

ユーザーから「`owner_companies.csv` に NOT_OWNER 企業も含めるようにして」という要望。実装過程で `nifty750_universe.csv` との冗長性が判明し、ユーザー判断で集約方針に転換した。

## 議論の流れ

### Step 1: owner_companies.csv 拡張 (要望対応)

`build_nifty750_universe.py` の Step 1 (owner_companies.csv 生成) を修正:
- フィルタ `[sheet["is_owner_company"]]` を削除 → 全 800 銘柄を含むように
- カラムリストに `is_owner_company` を追加 (4 列目に配置)
- ソート順を `is_owner_company desc → owner_family → symbol` に変更

実行結果:
- owner_companies.csv: 600 → **800 行 (OWNER 600 + NOT_OWNER 200)**
- カラム数: 16 → **17**

### Step 2: 冗長性発見 → 集約判断

実装後、`nifty750_universe.csv` と比較:

| | owner_companies.csv (拡張後) | nifty750_universe.csv |
|--|---------------------|----------------------|
| 行数 | 800 | 800 |
| カラム数 | 17 | 17 |
| 列セット | 同一 | 同一 |
| ソート | OWNER → family → symbol | OWNER → symbol |

→ 機能的にほぼ同内容。ユーザーに 3 選択肢を提示し、**Option 3 (owner_companies.csv 廃止 + nifty750_universe.csv に集約)** を選択。

### Step 3: 集約実装

- `build_nifty750_universe.py`:
  - Step 1 (owner_companies.csv 生成) を完全削除
  - `OUT_OWNERS` 定数削除
  - Step 2 のソート順を旧 owner_companies.csv の良い特性 `is_owner_company desc → owner_family → symbol` に統一
  - docstring から廃止情報 (dec-2026-05-11-011) を明記
- 既存 `owner_companies.csv` を `trash/2026-05-11_nse-owner-obsolete/` に `git mv`
- 関連ドキュメント参照を全更新:
  - `ARCHIVE_NOTES.md`: 🟢 現役からは削除、🗑️ 廃止済に追加
  - `logic_system_review.md`: 関連ファイル一覧から削除、Section 7 完了済リストに集約経緯追記
  - `docs/plan/2026-05-11_obsolete-nse-files.md`: 「nifty750_universe.csv に集約された冗長ファイル」セクション追加

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|-------------|
| dec-2026-05-11-011 | owner_companies.csv を廃止し nifty750_universe.csv に集約。投資戦略では `df[df["is_owner_company"]]` で OWNER 600 件をフィルタ可能 | clarifications-and-gaps Discussion からの延長、本 Discussion でも RESULTED_IN |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| **act-2026-05-11-024** | owner_companies.csv 廃止 + nifty750_universe.csv 集約の変更 (合計 8 ファイル) を `/push` でコミット・プッシュ。推奨タイトル: `refactor(nse): owner_companies.csv を廃止し nifty750_universe.csv に集約` | 高 | pending |

## 利用方法 (集約後)

```python
import pandas as pd

# 全 800 銘柄
df = pd.read_csv("notebook/NSE/data/exports/nse/nifty750_universe.csv")

# 旧 owner_companies.csv 600 件相当
owners = df[df["is_owner_company"]]

# NOT_OWNER のみ
not_owners = df[~df["is_owner_company"]]

# yaml_classification 別 NOT_OWNER 内訳
not_owners["yaml_classification"].value_counts()
```

## 教訓

- **早期に冗長性を検出する**: 拡張要望に応じる前に、類似ファイルとの関係を確認すべきだった
- **冗長性発見時は即座に集約判断**: 機能的に同じファイルを 2 つ持つコストは将来の維持負債
- **集約時は良い特性を引き継ぐ**: 旧ファイルのソート順 (is_owner_company → owner_family → symbol) を新ファイルに継承

## 次回の議論トピック

- act-2026-05-11-024 (commit + push) の実施
- act-2026-05-11-020 (pending 4 件のステータス整理) の実施
- act-2026-05-11-021 (完成宣言の判定) の実施
- act-2026-05-11-023 (AI レビュー自動化スクリプト実装) の設計検討

## 保存先

- **Neo4j**:
  - Discussion: `disc-2026-05-11-nse-owner-csv-consolidation`
  - Decision: `dec-2026-05-11-011` (二重リンク: clarifications-and-gaps + 本 Discussion)
  - ActionItem: `act-2026-05-11-024` (本集約変更のコミット・プッシュ)
  - リレーション: `(disc)-[:FOLLOWS]->(disc-2026-05-11-nse-owner-clarifications-and-gaps)`、`(project-106)-[:HAS_DISCUSSION]->(disc)`、`(disc)-[:RESULTED_IN]->(dec-011)`、`(disc)-[:PRODUCED]->(act-024)`
- **ドキュメント**: このファイル
