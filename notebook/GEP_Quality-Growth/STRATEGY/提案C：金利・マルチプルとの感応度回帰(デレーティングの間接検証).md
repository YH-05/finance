

## 0. 提案Cの位置づけと前提

提案Cは、クオリティ・ファクターL/Sリターンを金利・割引率などの**連続的な状態変数に回帰し、感応度(β)を定量化する**アプローチである。仮説「クオリティ劣後はデレーティング主導」の核心経路 ——金利上昇 → 割引率上昇 → 高デュレーション資産のマルチプル縮小 → クオリティL/S劣後—— を、レジームを離散化せずに直接検証する。

提案Bが「局面ごとの記述」、MSモデルが「内生的レジーム推定」であったのに対し、提案Cは「**どの状態変数が、どの符号・大きさでクオリティを動かしているか**」という感応度の定量化に特化する。

データ前提を確認する。

|データ|取得元|頻度|
|---|---|---|
|ファクターL/Sトータルリターン指数|Bloomberg(入手済)|日次|
|名目金利(10年)|FRED: DGS10|日次|
|実質金利(10年TIPS)|FRED: DFII10|日次|
|期待インフレ(BEI)|FRED: T10YIE|日次|
|政策金利|FRED: DFF / FEDFUNDS|日次|
|ターム・スプレッド|FRED: T10Y2Y|日次|
|クレジット・スプレッド|FRED: BAMLH0A0HYM2|日次|
|株式ボラティリティ|FRED: VIXCLS|日次|

FRED APIは無料で日次取得可能なため、提案Cは現実的に即実行できる。

---

## 1. 理論的基礎: なぜ金利感応度がデレーティングのプロキシになるか

### 1.1 デュレーションとしてのバリュエーション

株式のバリュエーションは、配当割引モデル(DDM)で割引率に対する感応度として表現できる。Gordon成長モデルでは、

$$ P = \frac{D_1}{r - g}, \quad r = r_f + \text{ERP} $$

価格の割引率 $r$ に対する弾力性は、

$$ \frac{\partial \ln P}{\partial r} = -\frac{1}{r - g} $$

成長率 $g$ が高い(=遠い将来のキャッシュフロー比率が高い)銘柄ほど分母 $r-g$ が小さく、割引率変化に対する価格感応度(エクイティ・デュレーション)が大きい。これが「グロース/高マルチプル銘柄は金利上昇で大きくデレーティングする」という経路の数学的根拠である。

クオリティ・ファクターは定義により高ROE・高マージン・安定成長企業をロングするため、しばしば高マルチプル・長デュレーション特性を帯びる。したがって**クオリティL/Sリターンが実質金利上昇に対して負の感応度を示せば、それはクオリティ・ロング群のデレーティングが進んでいる証拠**となる。これがプロキシの論理である。

### 1.2 名目金利でなく実質金利を見る理由

デレーティングを駆動するのは割引率の実質成分である。名目金利の上昇がインフレ期待の上昇によるものなら、企業の名目キャッシュフローも増えるため割引率上昇の効果は相殺されうる。一方、実質金利の上昇は将来キャッシュフローの実質現在価値を直接圧縮する。

$$ r_{nominal} = r_{real} + \pi^e $$

したがって感応度回帰では、名目金利を実質金利(DFII10)と期待インフレ(T10YIE)に分解し、**実質金利成分への感応度**を主たる検証対象とする。

---

## 2. モデルの定式化

### 2.1 ベースモデル(レベル変化への回帰)

日次のクオリティL/Sリターンを、状態変数の**変化量(差分)に回帰する。リターンはフロー量なので、ストック量である金利は差分を取って整合させる。**

$$ r_{Q,t} = \alpha + \beta_{real},\Delta y^{real}_t + \beta_{\pi},\Delta \pi^e_t + \beta_{term},\Delta,\text{TS}_t + \beta_{credit},\Delta,\text{CS}_t + \beta_{vix},\Delta\ln\text{VIX}_t + \beta_{mkt},r_{mkt,t} + \epsilon_t $$

| 項                | 変数                    | 仮説上の符号 | 解釈                     |
| ---------------- | --------------------- | ------ | ---------------------- |
| $\beta_{real}$   | 実質金利変化(ΔDFII10)       | **負**  | 実質金利上昇でクオリティ劣後=デレーティング |
| $\beta_{\pi}$    | 期待インフレ変化(ΔT10YIE)     | 不定     | インフレ経路の分離              |
| $\beta_{term}$   | タームスプレッド変化(ΔT10Y2Y)   | 正の可能性  | カーブ・スティープ化=景気回復期待      |
| $\beta_{credit}$ | クレジットスプレッド変化(ΔHY OAS) | 正      | スプレッド拡大(リスクオフ)でクオリティ選好 |
| $\beta_{vix}$    | VIX対数変化               | 正      | ボラ上昇時のクオリティの保険機能       |
| $\beta_{mkt}$    | 市場リターン                | ≈0     | L/Sの残存ベータ制御            |
| $\alpha$         | 切片                    | —      | 状態変数で説明されないクオリティ固有ドリフト |

市場リターン項 $r_{mkt}$ を加えるのは、L/Sが完全市場中立でない場合の残存ベータを制御し、金利感応度が単なる株式ベータ経由でないことを担保するためである。

### 2.2 仮説検証の判定基準

- $\beta_{real}$ が**有意に負** → クオリティのデレーティング感応度が確認され、デレーティング主導仮説を支持。
- $\beta_{real}$ の負の感応度が**2023年以降に強まる**(後述のレジーム交互作用)→ 利上げ後にデレーティング経路が活性化したことを示す。
- $\alpha$ が有意に負で、かつ金利変数で説明されない → デレーティングでは説明できないクオリティ固有の劣化(構造問題)を示唆。

---

## 3. 計量経済学上の論点と対処

日次金融データの回帰には固有の落とし穴がある。批判的に対処する。

### 3.1 内生性・同時性

金利と株式リターンは同時決定されうる(リスクオフで金利低下と株価下落が同時発生)。純粋な因果効果でなく相関を測っている可能性を明示する。対処として、(a)金利変化を一期ラグで入れた頑健性チェック、(b)FOMC日など金利が外生的に動くイベント周辺の局所回帰、を併用する。

### 3.2 系列相関・不均一分散

日次リターンの残差は自己相関とボラティリティ・クラスタリングを持つ。**Newey-West(HAC)標準誤差**を必須とする。さらにGARCH誤差項を仮定したモデルで頑健性を確認する。

### 3.3 多重共線性

実質金利・期待インフレ・名目金利は定義上従属(名目=実質+インフレ)。名目金利と実質金利+インフレを同時投入してはならない。VIFを確認し、実質金利+期待インフレの組み合わせを採用する。

### 3.4 非定常性

金利の**水準**は単位根を持つ(非定常)。リターン(定常)を金利水準に回帰すると見せかけの回帰になる。必ず**差分(変化量)**に回帰する。水準関係を見たい場合は共和分・誤差修正モデル(ECM)を別途検討する。

### 3.5 感応度の時変性

これが仮説検証の核心。$\beta_{real}$ が一定でなくレジーム依存である可能性を、以下で捉える。

**(a) レジーム交互作用ダミー**

$$ r_{Q,t} = \alpha + \gamma D_t + \beta_{real}\Delta y^{real}_t + \delta_{real}(D_t \times \Delta y^{real}_t) + \cdots + \epsilon_t $$

$D_t$ は2023年以降ダミー。$\delta_{real}$ が有意に負なら「利上げ後に実質金利感応度が強まった」=仮説支持。

**(b) ローリング回帰**

60〜120日窓で $\beta_{real}$ の時系列推移を可視化。感応度がいつ強まったかを連続的に観察。

**(c) MSモデルとの統合**

提案Bで議論したMS推定レジームを $D_t$ に代入すれば、暦区分でなくデータ駆動レジームでの感応度変化を測れる。三手法の統合点。

---

## 4. Python実装

```python
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import matplotlib.pyplot as plt
# FRED取得: pip install pandas-datareader  もしくは fredapi
from pandas_datareader import data as pdr

# =========================================================
# 0. データ取得
# =========================================================
# --- ファクターL/Sトータルリターン指数（Bloomberg, 入手済） ---
tr = pd.read_csv("acwi_factor_ls_totalreturn.csv", index_col=0, parse_dates=True).sort_index()
r_quality = np.log(tr["Quality"] / tr["Quality"].shift(1))  # 対数日次リターン

# --- 状態変数（FRED） ---
start = "2010-01-01"
fred_codes = {
    "real_yield": "DFII10",   # 10年実質金利
    "bei":        "T10YIE",   # 期待インフレ
    "term":       "T10Y2Y",   # タームスプレッド
    "credit":     "BAMLH0A0HYM2",  # HYクレジットスプレッド
    "vix":        "VIXCLS",   # VIX
}
fred = pd.concat(
    {k: pdr.DataReader(v, "fred", start) for k, v in fred_codes.items()},
    axis=1
)
fred.columns = fred_codes.keys()

# --- 市場リターン（ACWI価格指数などを別途用意。ここではプレースホルダ） ---
# mkt = np.log(acwi_price / acwi_price.shift(1))

# =========================================================
# 1. 変数変換：金利・スプレッドは差分、VIXは対数差分
# =========================================================
X = pd.DataFrame(index=fred.index)
X["d_real"]   = fred["real_yield"].diff()
X["d_bei"]    = fred["bei"].diff()
X["d_term"]   = fred["term"].diff()
X["d_credit"] = fred["credit"].diff()
X["d_lnvix"]  = np.log(fred["vix"]).diff()

# クオリティリターンと結合（共通日付に揃える）
df = pd.concat([r_quality.rename("r_q"), X], axis=1).dropna()

# =========================================================
# 2. 多重共線性チェック（VIF）
# =========================================================
xcols = ["d_real", "d_bei", "d_term", "d_credit", "d_lnvix"]
Xv = sm.add_constant(df[xcols])
vif = pd.Series(
    [variance_inflation_factor(Xv.values, i) for i in range(Xv.shape[1])],
    index=Xv.columns
)
print("VIF:\n", vif.round(2))  # 10超は要注意

# =========================================================
# 3. ベース感応度回帰（HAC標準誤差）
# =========================================================
y = df["r_q"]
Xb = sm.add_constant(df[xcols])
model = sm.OLS(y, Xb).fit(cov_type="HAC", cov_kwds={"maxlags": 10})
print(model.summary())
# β(d_real) の符号・有意性が主たる検証対象

# =========================================================
# 4. レジーム交互作用（2023年以降に感応度が変化したか）
# =========================================================
df2 = df.copy()
df2["D"] = (df2.index >= pd.Timestamp("2023-01-01")).astype(int)
for c in xcols:
    df2[f"{c}_xD"] = df2[c] * df2["D"]

Xint_cols = xcols + ["D"] + [f"{c}_xD" for c in xcols]
Xint = sm.add_constant(df2[Xint_cols])
m_int = sm.OLS(df2["r_q"], Xint).fit(cov_type="HAC", cov_kwds={"maxlags": 10})
print(m_int.summary())
# d_real_xD の係数 = 実質金利感応度のレジーム間変化。有意に負なら仮説支持

# =========================================================
# 5. ローリング回帰（β_real の時変推移）
# =========================================================
window = 90  # 営業日
betas, lows, highs, dates = [], [], [], []
for i in range(window, len(df) + 1):
    sub = df.iloc[i-window:i]
    Xs = sm.add_constant(sub[xcols])
    m = sm.OLS(sub["r_q"], Xs).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    b = m.params["d_real"]
    se = m.bse["d_real"]
    betas.append(b); lows.append(b - 1.96*se); highs.append(b + 1.96*se)
    dates.append(df.index[i-1])

roll = pd.DataFrame({"beta": betas, "lo": lows, "hi": highs}, index=dates)

fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(roll.index, roll["beta"], label="β(Δreal yield)")
ax.fill_between(roll.index, roll["lo"], roll["hi"], alpha=0.2)
ax.axhline(0, color="grey", ls="--", lw=0.8)
ax.axvline(pd.Timestamp("2023-01-01"), color="red", ls=":", lw=1)
ax.set_title("Rolling 90D β to Real Yield — Quality L/S デレーティング感応度")
ax.legend(); plt.tight_layout()

# =========================================================
# 6. 寄与度分解（各期間の劣後を状態変数寄与に分解）
# =========================================================
def contribution(model, sub, cols):
    means = sub[cols].mean()
    contrib = model.params[cols] * means
    out = contrib.copy()
    out["alpha"] = model.params["const"]
    out["total"] = sub["r_q"].mean()
    return out

qe   = df.loc[:"2022-12-31"]
hike = df.loc["2023-01-01":]
m_qe   = sm.OLS(qe["r_q"], sm.add_constant(qe[xcols])).fit(cov_type="HAC", cov_kwds={"maxlags":10})
m_hike = sm.OLS(hike["r_q"], sm.add_constant(hike[xcols])).fit(cov_type="HAC", cov_kwds={"maxlags":10})
attrib = pd.DataFrame({"QE": contribution(m_qe, qe, xcols),
                       "Hike": contribution(m_hike, hike, xcols)})
print(attrib.round(5))
```

---

## 5. 結果の解釈フレーム

回帰推定後、以下のパターンで仮説を判定する。

|$\beta_{real}$(全期間)|$\delta_{real}$(交互作用)|$\alpha$(Hike期)|結論|運用示唆|
|---|---|---|---|---|
|有意に負|有意に負(感応度増大)|ほぼ0|**デレーティング主導(仮説強支持)**|金利反転で回復見込み。ポジション維持の根拠。実質金利ピークアウトが転換シグナル|
|有意に負|不変|0|デレーティング感応はあるが利上げ後特有でない|構造的な金利感応であり、金利高止まりが続く限り逆風持続|
|弱い・非有意|—|有意に負|金利で説明されない固有劣化|デレーティング仮説は棄却寄り。EPS成長スプレッド鈍化を疑う。提案Aのα分析と突合|
|有意に負|有意に負|も負|複合(デレーティング+固有劣化)|寄与度分解(§6)で主因比率を確認。回復は部分的にとどまる可能性|


---

## 6. 提案Cの限界(批判的明示)

- **感応度 ≠ 源泉分解**: $\beta_{real}$ はクオリティリターンの金利感応度であって、「リターンの何%がデレーティング由来か」を厳密には与えない。寄与度分解(§6)はモデル依存の近似である。
- **相関であって因果ではない**: 金利とクオリティリターンの同時性・内生性を完全には排除できない。「実質金利→デレーティング→クオリティ劣後」というDAG上の因果は、回帰係数だけでは識別できない。FOMCイベント局所分析やラグ構造で補強するが、決定的な識別には至らない。
- **デレーティングの内生性**: 実質金利上昇への負の感応度が、将来EPS成長期待の下方修正を市場が織り込んだ結果である可能性(媒介 vs 交絡)は、本回帰では切り分けられない。これは提案Aのα分析、ないしアナリスト予想改訂データの併用を要する。
- **サンプル長**: 利上げ後期間(2023-現在)が短く、レジーム交互作用 $\delta_{real}$ の推定は不確実性が大きい。過度な確信を避け、信頼区間を併記する。

---

## 実行手順のまとめ

1. FREDから状態変数を日次取得、金利・スプレッドは差分、VIXは対数差分に変換。
2. VIFで多重共線性を確認し、実質金利+期待インフレの組で名目金利の二重計上を回避。
3. HAC標準誤差でベース感応度回帰、$\beta_{real}$ の符号・有意性を確認。
4. レジーム交互作用で $\delta_{real}$ を推定し、利上げ後の感応度変化を検定。
5. ローリング回帰で $\beta_{real}$ の時変を可視化、転換点を特定。
6. 寄与度分解と提案A・Bの結果を統合し、解釈フレームで最終判定。

提案A(バリュー感応度)、B(レジーム別記述)、C(金利感応度)の三者を組み合わせることで、個別銘柄のEPS・P/Eデータがない制約下でも、「クオリティ劣後はデレーティング主導か」という仮説に対して相互補強的かつ頑健な結論を導ける。

入手済みBloombergデータの具体的なファクター構成と、市場リターン指数(ACWI価格指数等)の取得可否を共有してもらえれば、上記コードをFRED取得部分まで含めて実データで動く完全な形に仕上げる。
