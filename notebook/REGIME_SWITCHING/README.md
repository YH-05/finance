# REGIME_SWITCHING — レジームスイッチングモデル検証

FRED 7 系列を用いた米国経済レジーム抽出（HMM）と、S&P500 週次リターンの市場レジーム回帰（Markov-Switching Regression）を比較する notebook 一式。

## 前提条件

- `FRED_API_KEY` 環境変数が `.env` に設定されていること
- インターネット接続（yfinance 経由で `^GSPC` を取得）
- `hmmlearn`、`statsmodels`、`scikit-learn` が `uv sync` でインストール済み
- dev extras に `nbconvert`、`ipykernel` が含まれていること（`uv sync --extra dev` で同期）

## 実行手順

```bash
# 1. データ準備（FRED 取得・週次変換・標準化・S&P500 取得）
uv run jupyter nbconvert --to notebook --execute --inplace 01_data_preparation.ipynb

# 2. 経済レジーム抽出（多変量 Gaussian HMM, 3 状態）
uv run jupyter nbconvert --to notebook --execute --inplace 02_economic_regime_hmm.ipynb

# 3. 市場レジーム回帰（パターン A: 生 7 系列, パターン B: PCA 削減）
uv run jupyter nbconvert --to notebook --execute --inplace 03_market_regime_ms.ipynb

# 4. モデル①②の比較
uv run jupyter nbconvert --to notebook --execute --inplace 04_comparison.ipynb
```

Jupyter 上で対話的に実行する場合も同じ順序。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `_helpers.py` | データ取得・前処理・可視化の共通関数 |
| `01_data_preparation.ipynb` | FRED 7 系列と S&P500 を取得・週次変換・標準化 |
| `02_economic_regime_hmm.ipynb` | 多変量 Gaussian HMM (3 状態) で経済レジーム抽出 |
| `03_market_regime_ms.ipynb` | MS 回帰 (パターン A / B) で市場レジーム抽出 |
| `04_comparison.ipynb` | モデル①②の対応分析と NBER 比較 |
| `data/` | 中間 parquet ファイル（gitignore 対象） |

## 設計と意思決定

- 仕様書: `docs/superpowers/specs/2026-05-23-regime-switching-notebook-design.md`
- 実装プラン: `docs/superpowers/plans/2026-05-23-regime-switching-notebook.md`

## 使用 FRED 系列

| ID | 名称 | 変換 |
|---|---|---|
| INDPRO | 鉱工業生産指数 | YoY % |
| ICSA | 新規失業保険申請件数 | 4 週 MA の YoY % |
| T10YIE | 10 年 BEI | レベル |
| CPIAUCSL | CPI | YoY % |
| STLFSI4 | セントルイス連銀金融ストレス指数 | レベル |
| BAA10Y | Baa - 10Y スプレッド | レベル |
| T10Y2Y | 10Y - 2Y スプレッド | レベル |
