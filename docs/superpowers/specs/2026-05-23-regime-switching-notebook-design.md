# レジームスイッチングモデル検証 Notebook 設計

- 作成日: 2026-05-23
- 種別: notebook プロジェクト
- 配置: `notebook/REGIME_SWITCHING/`

## 1. 背景・目的

7 種の FRED マクロ・金融指標を用いて、米国経済のレジーム（局面）を
レジームスイッチングモデルで抽出・検証するための notebook を作成する。

検証対象モデルは 2 種:

1. **経済レジーム抽出（教師なし）**: 多変量 HMM で 7 系列の同時観測から経済そのものの局面を抽出する。
2. **市場レジーム回帰（教師あり）**: Markov-Switching Regression で S&P500 週次対数リターンを 7 系列で説明する。

両モデルの結果を比較し、抽出された経済レジームと市場レジームの対応を可視化することで、
モデル選択と特徴量設計の妥当性を確認できる状態を目指す。

## 2. スコープ

### 含む
- FRED から 7 系列を取得・週次（W-FRI）リサンプリング・変換するデータパイプライン
- 経済レジーム抽出（多変量 Gaussian HMM, 3 状態）
- 市場レジーム回帰の 2 パターン（生 7 系列 / PCA 削減版）
- S&P500（`^GSPC`）週次対数リターンの yfinance 経由取得
- 各種可視化（時系列、遷移確率、レジーム別統計、モデル間対応）
- `_helpers.py` への共通関数切り出し
- 依存追加（`hmmlearn`）

### 含まない
- 投資戦略バックテスト（シグナル化やパフォーマンス検証は対象外）
- リアルタイム予測 API 化
- 他マーケット（為替・コモディティ・新興国）への拡張
- モデルパラメータの本格的なチューニング（初期値・状態数固定での検証に留める）

## 3. ディレクトリ構成

```
notebook/REGIME_SWITCHING/
├── _helpers.py                       # データ取得・前処理・可視化の共通関数
├── 01_data_preparation.ipynb         # データ取得・変換・週次リサンプリング・EDA
├── 02_economic_regime_hmm.ipynb      # モデル①: 多変量 HMM 経済レジーム抽出
├── 03_market_regime_ms.ipynb         # モデル②: Markov-Switching 市場レジーム回帰
├── 04_comparison.ipynb               # モデル①②の対応分析・最終可視化
└── data/                             # 前処理後の中間データ（.parquet）
    ├── fred_weekly_raw.parquet       # 週次リサンプリング後の生値
    └── features_weekly.parquet       # 変換・標準化後の特徴量
```

参考実装: `notebook/FILING_NLP/_helpers.py` の構成パターンに倣う。

## 4. データレイヤー

### 4.1 取得対象（FRED）

| FRED ID | 系列名 | 元頻度 | 開始日（参考） | 変換 |
|---|---|---|---|---|
| INDPRO | 鉱工業生産指数 | 月次 | 1919-01 | 前年同月比 % |
| ICSA | 新規失業保険申請件数 | 週次 | 1967-01 | 4 週移動平均の前年比 % |
| T10YIE | 10 年ブレークイーブンインフレ率 | 日次 | 2003-01 | レベル |
| CPIAUCSL | CPI（全項目, SA） | 月次 | 1947-01 | 前年同月比 % |
| STLFSI4 | セントルイス連銀金融ストレス指数 | 週次 | 2003-12 | レベル |
| BAA10Y | Moody's Baa 社債 - 10 年国債スプレッド | 日次 | 1986-01 | レベル |
| T10Y2Y | 10 年 - 2 年国債利回り差 | 日次 | 1976-06 | レベル |

### 4.2 取得手段

`market.fred.HistoricalCache` を使用:

```python
from market.fred import HistoricalCache

cache = HistoricalCache()
for sid in SERIES_IDS:
    cache.sync_series(sid)
df = cache.get_series_df(sid)  # 各系列ごと取得 → 横結合
```

### 4.3 リサンプリング

- 共通頻度: **週次 W-FRI**（金曜終値ベース）
- 日次系列: `resample("W-FRI").last()`
- 週次系列: 元データの公開曜日に依存するため、`resample("W-FRI").last()` で揃える
- 月次系列: `resample("W-FRI").ffill()` で前方補完

### 4.4 期間

- 開始: **2003-12-01**（STLFSI4 と T10YIE の両方が揃う時点）
- 終了: 最新キャッシュ日付
- 全 7 系列が揃わない週は学習サンプルから除外（先頭の warm-up 期間のみ）

### 4.5 変換と標準化

- 変換: 4.1 表に従い、INDPRO/CPIAUCSL/ICSA は YoY %、他はレベル
- 標準化: 全期間で Z-score（in-sample 推定なので train/test 分割なし）
- 出力: `features_weekly.parquet`（インデックス = W-FRI 週末日付、列 = 7 特徴量）

## 5. モデル①: 経済レジーム抽出

### 5.1 構成
- ライブラリ: `hmmlearn.hmm.GaussianHMM`
- パラメータ:
  - `n_components=3`
  - `covariance_type="full"`
  - `n_iter=200`
  - `random_state=42`（再現性確保）

### 5.2 入力・出力
- 入力: 標準化された 7 系列（W-FRI 週次, shape = (T, 7)）
- 出力:
  - 各週のレジームラベル `state ∈ {0, 1, 2}`
  - 各週の状態事前確率 `predict_proba`
  - 遷移確率行列 `transmat_`、各状態の平均・共分散

### 5.3 状態ラベリング

HMM の状態 ID は学習ごとに任意なので、解釈可能な名前を後付けする:

1. 各状態の **INDPRO YoY 平均値** を計算
2. 降順ソートで `拡大 > 減速 > 後退・ストレス` を割り当て
3. ラベル割り当て後、可視化で利用

### 5.4 検証
- 遷移確率行列の対角優位（状態の持続性）を確認
- NBER 景気後退期（FRED `USREC` を別途取得して可視化のみに利用）との目視照合

## 6. モデル②: 市場レジーム回帰

### 6.1 ターゲット
- S&P500 (`^GSPC`) 終値を yfinance で取得
- 週次リサンプリング後、対数リターン `log(P_t / P_{t-1})` を計算
- 取得 API: `market.yfinance.fetcher.YFinanceFetcher`

### 6.2 構成
- ライブラリ: `statsmodels.tsa.regime_switching.MarkovRegression`
- パラメータ共通:
  - `k_regimes=3`
  - `switching_variance=True`
  - `switching_trend=True`
  - `switching_exog=False`（係数は状態間で固定、平均と分散のみ切替）

### 6.3 説明変数 — 2 パターン並列実行

| パターン | 説明変数 | 目的 |
|---|---|---|
| A: 生 7 系列 | 標準化された 7 特徴量をそのまま投入 | ベースライン |
| B: PCA 削減 | 7 系列に PCA、累積寄与率 80% 以上を満たす最小成分数を使用 | 多重共線性緩和 |

PCA 成分数は自動決定（累積寄与率しきい値）、決定された成分数は notebook 内で明示。

### 6.4 出力
- 各週のスムーズ確率 `smoothed_marginal_probabilities`（3 状態 × T）
- 各状態の平均リターン・分散の推定値
- BIC・AIC（パターン A と B の比較に使用）

## 7. 可視化要件

### 7.1 `01_data_preparation.ipynb`
- 各系列の生値・変換後のラインチャート（7 系列 × 2 = 14 枚を 7×2 サブプロット）
- 変換後の相関ヒートマップ
- W-FRI リサンプル後のサンプル数と欠損数の表

### 7.2 `02_economic_regime_hmm.ipynb`
- レジーム背景塗りつぶし + INDPRO YoY・CPI YoY 重ね描き
- 遷移確率行列のヒートマップ
- レジーム別の各系列平均値テーブル
- NBER 景気後退期との重ね描き

### 7.3 `03_market_regime_ms.ipynb`
- パターン A、B の各々で:
  - S&P500 価格 + レジーム背景塗りつぶし
  - 3 状態スムーズ確率の積み上げチャート
  - レジーム別の平均リターン・年率ボラのテーブル
- パターン A vs B の BIC/AIC 比較表

### 7.4 `04_comparison.ipynb`
- 経済レジーム（モデル①）と市場レジーム（モデル②パターン B）のクロス集計表
- 同一時間軸での両レジーム並列表示
- NBER 景気後退期との 3 系統比較

## 8. 共通モジュール `_helpers.py`

切り出す関数群（概要）:

```python
def load_fred_weekly(series_ids: list[str], start: str = "2003-12-01") -> pd.DataFrame:
    """全 FRED 系列を取得し W-FRI に揃える。"""

def transform_features(df: pd.DataFrame) -> pd.DataFrame:
    """4.5 節の変換と Z-score 標準化を適用。"""

def fetch_sp500_weekly_returns(start: str = "2003-12-01") -> pd.Series:
    """yfinance から ^GSPC を取得し W-FRI 週次対数リターンを返す。"""

def label_hmm_states(model, X: np.ndarray, indpro_yoy: pd.Series) -> dict[int, str]:
    """INDPRO YoY 平均で状態をソートして拡大/減速/後退ラベルを割り当てる。"""

def plot_regime_overlay(ax, series: pd.Series, regimes: pd.Series, palette: dict) -> None:
    """レジーム背景を塗りつぶした時系列プロット。"""
```

実装詳細・型ヒント・ロギングは実装プラン側で決定。

## 9. 依存関係

### 追加が必要なもの

`hmmlearn` を `pyproject.toml` の依存に追加:

```bash
uv add hmmlearn
```

### 既存依存（追加不要）
- `statsmodels >= 0.14.6`（pyproject 確認済）
- `pandas` / `numpy` / `matplotlib` / `seaborn`
- `scikit-learn >= 1.8.0`（PCA 用、pyproject.toml 確認済）
- 内部パッケージ: `market.fred.HistoricalCache`, `market.yfinance.fetcher.YFinanceFetcher`

## 10. 受け入れ条件

- [ ] `notebook/REGIME_SWITCHING/` フォルダと 4 個の notebook、`_helpers.py` が作成されている
- [ ] `01_data_preparation.ipynb` が 7 系列を取得・週次リサンプリング・変換まで実行でき、`features_weekly.parquet` を出力する
- [ ] `02_economic_regime_hmm.ipynb` で 3 状態 HMM が収束し、可視化と状態ラベリングが実行できる
- [ ] `03_market_regime_ms.ipynb` でパターン A と B の両方が収束し、BIC/AIC 比較が可能
- [ ] `04_comparison.ipynb` で両モデルレジームのクロス集計と並列可視化が実行できる
- [ ] `hmmlearn` が `pyproject.toml` に追加され `uv sync` が成功する
- [ ] 全 notebook が `Restart Kernel → Run All` で再現実行できる（FRED キャッシュ済み前提）

## 11. リスクと対応

| リスク | 影響 | 対応 |
|---|---|---|
| `MarkovRegression` の収束失敗（局所最適） | モデル②結果が不安定 | `search_reps=10` で複数初期値から最大尤度を選択 |
| サンプル数不足（2003-12 開始 → 約 1,150 週） | 3 状態 × 8 パラメータでギリギリ | パターン B（PCA）で次元削減し緩和 |
| `STLFSI4` 公開停止リスク（過去にも改称あり） | データ取得失敗 | 取得時に明示的エラーメッセージ、代替系列は仕様外で別途検討 |
| HMM 状態ラベリングが INDPRO 平均で曖昧 | 解釈ミス | ラベル割り当て後の各状態統計を必ず可視化して妥当性確認 |
| PCA 主成分の符号反転 | 解釈が反転 | 主成分ローディングをプロットして方向を明示 |

## 12. 完了後の次ステップ（仕様外）

- レジームを特徴量とした投資戦略バックテスト
- ベイズ化（pymc / pyro での事後分布推定）
- 動的状態数選択（HDP-HMM）
