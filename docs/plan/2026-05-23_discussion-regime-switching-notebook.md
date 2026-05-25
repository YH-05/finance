# 議論メモ: レジームスイッチングモデル notebook 実装

**日付**: 2026-05-23
**議論ID**: disc-2026-05-23-regime-switching-notebook
**Project**: regime-switching-notebook
**参加**: ユーザー + AI (Claude Opus 4.7)

## 背景・コンテキスト

ユーザーからの依頼:
> FRED の鉱工業生産指数、新規失業保険申請数、10年物ブレークイーブンインフレ率、消費者物価指数、セントルイス連銀金融ストレス指数、Baa格社債と10年国債のスプレッド、10年債と2年債の利回り差を使ってレジームスイッチングモデルをテストする notebook を作成

Superpowers の3スキル連鎖（brainstorming → writing-plans → subagent-driven-development）で完全実装。

## 議論のサマリー

### Brainstorming Phase (設計確定)

3点の論点で合意形成:

1. **モデル目的**: 7系列をどう使うか
   - 選択肢: (1) 経済レジーム抽出 (2) 市場レジーム回帰 (3) 両方
   - **決定: (3) 両方を別モデルで比較**

2. **レジーム数**:
   - 選択肢: 2 / 3 / 両方BIC比較
   - **決定: 3 レジーム (拡大/減速/後退・ストレス)**

3. **データ頻度**:
   - 選択肢: 月次 / 週次 / 日次
   - **決定: 週次 W-FRI**

### Writing-Plans Phase (実装プラン作成)

11タスクのバイトサイズプランを `docs/superpowers/plans/2026-05-23-regime-switching-notebook.md` に作成。
セルフレビューで `fred_series.json` のスキーマ修正（`name_ja`/`name_en`/`frequency`/`units`/`description`）を反映。

### Subagent-Driven Development Phase (実装)

11タスク全て implementer + spec reviewer + code quality reviewer の三段サイクルで実装。
1回も BLOCKED なし。複数タスクで minor 改善（テスト強化、警告対応など）を反復。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-05-23-001 | 経済HMM + 市場MS の2モデル並列構築 | 単一より両方比較が分析価値高い |
| dec-2026-05-23-002 | 3レジーム構成（拡大/減速/後退・ストレス） | 景気サイクルの伝統的分類に整合 |
| dec-2026-05-23-003 | 週次 W-FRI リサンプリング | サンプル数と安定性のバランス |
| dec-2026-05-23-004 | MS 説明変数を Pattern A (raw 7) と B (PCA 80%) で並列 | ユーザー指示。PCA版がAIC/BIC勝利 |
| dec-2026-05-23-005 | MarkovRegression search_reps を 10→20 へ引き上げ | plan のリメディアル指示。LL大幅改善 |
| dec-2026-05-23-006 | japanize-matplotlib で日本語フォント対応 | sns.set_theme 後に japanize() 呼び出し必須 |
| dec-2026-05-23-007 | Subagent-Driven Development + 二段階レビュー | コンテキスト分離 + 品質担保 |
| dec-2026-05-23-008 | main ブランチで直接作業 | ユーザーの明示的選択 |

## 成果物

### コード
- `notebook/REGIME_SWITCHING/_helpers.py` (329行、5関数)
  - `load_fred_weekly`、`transform_features`、`fetch_sp500_weekly_returns`、`label_hmm_states`、`plot_regime_overlay`
- `notebook/REGIME_SWITCHING/01_data_preparation.ipynb` (16セル)
- `notebook/REGIME_SWITCHING/02_economic_regime_hmm.ipynb` (18セル)
- `notebook/REGIME_SWITCHING/03_market_regime_ms.ipynb` (22セル)
- `notebook/REGIME_SWITCHING/04_comparison.ipynb` (14セル)
- `notebook/REGIME_SWITCHING/README.md`
- `tests/notebook/regime_switching/test_helpers.py` (13テスト、全PASS)

### 依存・設定
- `pyproject.toml`: `hmmlearn>=0.3.3`、`japanize-matplotlib`、`nbconvert` (dev)
- `data/config/fred_series.json`: `INDPRO`、`BAA10Y`、`USREC` プリセット追加

### Git
16コミット（spec/plan含む）が main に積まれ、origin/main 先行中（未push）。
コミット範囲: `0b9aca7` → `786e7a5`

### 分析結果
- 経済↔市場マッピング一致率: **72.10%**
- NBER 後退期 86週: 市場は「下落」をほぼ示さず（中立84.9%、上昇15.1%）→ 株価先行性
- AIC/BIC ともに **PCA削減版 (Pattern B)** が勝利
  - Pattern A: AIC=-5568.72, BIC=-5403.29
  - Pattern B: AIC=-5614.67, BIC=-5509.40

### 品質ゲート
- `ruff format --check`: 4 files already formatted ✅
- `ruff check`: All checks passed ✅
- `pyright`: 0 errors ✅
- `pytest tests/notebook/regime_switching/`: 13 passed ✅
- 4 notebook 連続再実行: 全成功 ✅

## アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-05-23-001 | MS回帰の収束強化 (start_params/EMOptions) | 中 |
| act-2026-05-23-002 | label_hmm_states の 4状態以上テスト追加 | 低 |
| act-2026-05-23-003 | default_regime_palette ヘルパー追加 | 低 |
| act-2026-05-23-004 | レジームを特徴量とした投資戦略バックテスト（別プロジェクト化） | 中 |
| act-2026-05-23-005 | origin/main への git push | 中（ユーザー判断待ち） |

## 次回の議論トピック

- バックテスト統合の設計（act-2026-05-23-004 をプロジェクト化する場合）
  - レジーム遷移をシグナルとした投資戦略（リスクオン/オフ切替）
  - 既存 `dev/ca_strategy` パッケージとの統合方針
- HDP-HMM（動的状態数選択）への拡張可能性
- ベイズ化（pymc / pyro での事後分布推定）

## 参考情報

- spec: `docs/superpowers/specs/2026-05-23-regime-switching-notebook-design.md`
- plan: `docs/superpowers/plans/2026-05-23-regime-switching-notebook.md`
- 既存パターン参考: `notebook/FILING_NLP/_helpers.py`
- 使用ライブラリ:
  - `hmmlearn.GaussianHMM` (経済レジーム抽出)
  - `statsmodels.tsa.regime_switching.MarkovRegression` (市場レジーム回帰)
  - `sklearn.decomposition.PCA` (Pattern B 次元削減)
  - `market.fred.HistoricalCache` (FRED データ取得)
  - `market.yfinance.YFinanceFetcher` (S&P500 取得)
