
# 提案A: ファクター間スプレッド分解(プロキシ法)の詳細

## 1. 基本アイデアと理論的正当化

### 1.1 なぜプロキシが成立するのか

個別銘柄のP/EやEPSが取得できない状況で、「クオリティ劣後はデレーティング主導か」を検証したい。ここで利用するのは、**各ファクターL/Sリターンが特定の経済的構成要素へのエクスポージャーを内包している**という構造である。

クオリティ・ファクターのリターンを、本来の分解式に対応づけると以下になる。

$$ R_{Quality}^{L/S} = \underbrace{(\text{配当スプレッド})}_{\text{小}} + \underbrace{(\text{EPS成長スプレッド})}_{\text{ファンダメンタルズ}} + \underbrace{(\text{マルチプル変化スプレッド})}_{\text{デレーティング}} $$

ここで重要な観察は、**バリュー・ファクターL/Sは本質的にマルチプル(安さ)へのベットである**という点である。バリューのロングは低P/E・低P/B銘柄、ショートは高P/B銘柄であり、バリューがアウトパフォームする局面とは「割安銘柄のマルチプルが拡大し割高銘柄のマルチプルが縮小する」=市場全体でマルチプル圧縮(リレーティングの逆転)が進む局面と概ね一致する。

したがって、クオリティL/SリターンをバリューL/Sリターンに回帰したとき、

- **回帰係数 $\beta_{Val}$** = クオリティのリターンのうちマルチプル(バリュエーション)変動で説明される部分
- **残差 + 切片 $\alpha$** = マルチプルに依存しないクオリティ固有成分(ファンダメンタルズ起因に近い)

という対応が得られる。これが「個別銘柄データなしでデレーティング寄与を近似する」プロキシ法の核心である。

### 1.2 プロキシの限界(批判的明示)

この対応は厳密な恒等式ではなく、あくまで統計的近似である。以下の留保を明示しておく。

- バリューL/Sは「マルチプル変化」だけでなくバリュー銘柄固有のEPS動学も含む。純粋なマルチプル成分ではない。
- クオリティとバリューは構成銘柄が部分的に重複・反発しうる(高クオリティ高P/B vs 低クオリティ低P/B)。両者の関係は時変。
- $\beta_{Val}$ は「マルチプル感応度」であって「マルチプル寄与の水準」そのものではない。寄与の水準を出すには後述の寄与度分解(§4)が必要。

---

## 2. 回帰モデルの定式化

### 2.1 ベースモデル

クオリティL/Sの月次(または日次)リターンを、他ファクターL/Sリターンに回帰する多変量時系列回帰。

$$ R_{Quality,t} = \alpha + \beta_{Val} R_{Value,t} + \beta_{Size} R_{Size,t} + \beta_{Mom} R_{Mom,t} + \beta_{LowVol} R_{LowVol,t} + \epsilon_t $$

|項|解釈|
|---|---|
|$\alpha$|他ファクターで説明されないクオリティ固有リターン(クオリティの「真のα」)|
|$\beta_{Val}$|**本分析の主役**。バリュー(マルチプル)感応度。負の値はクオリティとバリューの逆相関を示す|
|$\beta_{Size}$|小型株エクスポージャー。クオリティは大型株偏重になりやすく通常負|
|$\beta_{Mom}$|モメンタム連動。クオリティとモメンタムは正相関しやすい|
|$\beta_{LowVol}$|低ボラ連動。クオリティと低ボラは経済的に近接|
|$\epsilon_t$|残差。いずれのファクターでも説明されない成分|

### 2.2 グロースが利用可能な場合の拡張

グロースL/Sが入手可能なら、デレーティング感応度をより直接的に切り分けられる。グロース銘柄は高マルチプル・高デュレーション資産であり、金利上昇局面でのデレーティングを最も強く受ける。

$$ R_{Quality,t} = \alpha + \beta_{Val} R_{Value,t} + \beta_{Growth} R_{Growth,t} + \beta_{Size} R_{Size,t} + \beta_{Mom} R_{Mom,t} + \beta_{LowVol} R_{LowVol,t} + \epsilon_t $$

ただしバリューとグロースは強い負相関を持つため、両方を同時投入すると**多重共線性**が発生する。VIF(分散拡大係数)を確認し、必要なら一方のみ採用するか、両者の差(Value−Growth)を単一説明変数にする。

---

## 3. レジーム別の係数比較(仮説検証の中核)

仮説は「2023年以降のクオリティ劣後はデレーティング主導」である。これは**回帰係数の時変性**として検証する。

### 3.1 サブサンプル回帰

2期間で別々に回帰を推定し、係数を比較する。

|係数|2010–2022(QE)|2023–現在(利上げ後)|仮説が支持される場合の符号変化|
|---|---|---|---|
|$\alpha$(クオリティ固有)|$\alpha_1$|$\alpha_2$|$\alpha_2 \approx \alpha_1$(固有αは維持)|
|$\beta_{Val}$|$\beta_{Val,1}$|$\beta_{Val,2}$|$\beta_{Val,2}$ が大きく負方向へ拡大|

**仮説支持の判定基準**:

- $\beta_{Val}$ が2023年以降に有意に負方向へシフト → クオリティの劣後がバリュー(マルチプル)ローテーションに連動して発生していることを示す。すなわちデレーティング主導の傍証。
- 同時に $\alpha$(クオリティ固有成分)が大きく劣化していない → ファンダメンタルズ(EPS成長スプレッド)由来の構造劣化ではない。
- 逆に $\alpha$ そのものが大幅に負へ転落していれば、バリューでは説明できないクオリティ固有の悪化であり、「構造的消滅」シナリオを示唆する。

### 3.2 係数差の統計的検定

サブサンプル間の係数差が偶然でないかを検定する。

- **Chow検定**: 全係数の構造変化を一括検定。帰無仮説「両期間で係数が同一」。
- **交互作用ダミー法**(推奨): 期間ダミー $D_t$(2023年以降=1)を導入し、全データを一括推定する。係数差の標準誤差と有意性が直接得られる。

$$ R_{Quality,t} = \alpha + \gamma D_t + \beta_{Val} R_{Value,t} + \delta_{Val}(D_t \times R_{Value,t}) + (\text{他ファクターも同様}) + \epsilon_t $$

ここで $\delta_{Val}$ が「バリュー感応度のレジーム間変化」であり、その t 値が有意に負なら仮説支持。$\gamma$ は固有αのレベルシフト。

### 3.3 連続的な時変推定(補完)

サブサンプル分割は分割点に恣意性がある。これを補うため:

- **ローリング回帰**: 36〜60ヶ月窓で $\beta_{Val}$ の時系列推移を可視化。2022→2023の遷移が滑らかか急変かを観察。
- **Kalmanフィルタ / 状態空間モデル**: 係数を状態変数として連続推定。分割点を仮定せず構造変化を捉える。

---

## 4. 寄与度分解(感応度から寄与水準へ)

回帰係数は「感応度」であり、「劣後リターンのうち何%がバリュー経由か」という**寄与水準**を出すには分散・共分散分解を行う。

### 4.1 リターン寄与分解

各期間のクオリティ累積リターンを、説明変数の寄与に分解する。

$$ \bar{R}_{Quality} = \alpha + \beta_{Val}\bar{R}_{Value} + \beta_{Size}\bar{R}_{Size} + \cdots $$

例えば2023年以降のクオリティ累積リターンが $-8\%$ で、$\beta_{Val}\bar{R}_{Value} = -6\%$ なら、劣後の大半がバリュー(マルチプル)ローテーション経由と定量的に言える。

### 4.2 分散分解(R²ベース)

クオリティリターンの分散のうち各ファクターが説明する割合を、共分散ベースで配分する。

$$ \text{Var}(R_{Quality}) = \sum_i \beta_i ,\text{Cov}(R_{Quality}, R_i) + \text{Var}(\epsilon) $$

各項を $\text{Var}(R_{Quality})$ で除すと寄与シェアになる。Shapley値ベースの分解を使えば変数順序に依存しない公平な配分が可能(ユーザーの関心領域に整合)。

---

## 5. Python実装

```python
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =========================================================
# 0. データ準備
# Bloombergから取得した各ファクターL/Sの「累積リターン指数」を想定
# columns: ['Quality', 'Value', 'Size', 'Momentum', 'LowVol', 'Growth']
# index: 日付
# =========================================================
cum = pd.read_csv("acwi_factor_ls_cum.csv", index_col=0, parse_dates=True)

# 累積指数 → 期間リターン（対数リターン推奨：加法的に分解できる）
ret = np.log(cum / cum.shift(1)).dropna()
# 月次化する場合（日次データなら）
ret_m = np.log(cum / cum.shift(1)).resample("ME").sum()  # 対数リターンは合計でリサンプル

# =========================================================
# 1. ベース多変量回帰（全期間）
# =========================================================
def run_factor_regression(df, y_col="Quality",
                          x_cols=("Value", "Size", "Momentum", "LowVol")):
    X = sm.add_constant(df[list(x_cols)])
    y = df[y_col]
    # HAC（Newey-West）標準誤差：時系列の自己相関・不均一分散に頑健
    model = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
    return model

model_full = run_factor_regression(ret_m)
print(model_full.summary())

# =========================================================
# 2. レジーム別サブサンプル回帰
# =========================================================
split_date = "2023-01-01"
ret_qe   = ret_m.loc[:split_date]
ret_hike = ret_m.loc[split_date:]

m_qe   = run_factor_regression(ret_qe)
m_hike = run_factor_regression(ret_hike)

comparison = pd.DataFrame({
    "QE(2010-2022)":  m_qe.params,
    "Hike(2023-)":    m_hike.params,
    "Δ(Hike-QE)":     m_hike.params - m_qe.params,
})
print(comparison)

# =========================================================
# 3. 交互作用ダミー法（係数差の有意性を直接検定）
# =========================================================
df = ret_m.copy()
df["D"] = (df.index >= pd.Timestamp(split_date)).astype(int)
x_cols = ["Value", "Size", "Momentum", "LowVol"]

# 各ファクターとダミーの交互作用項を生成
for c in x_cols:
    df[f"{c}_x_D"] = df[c] * df["D"]

X_cols = x_cols + ["D"] + [f"{c}_x_D" for c in x_cols]
X = sm.add_constant(df[X_cols])
y = df["Quality"]
m_interact = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
print(m_interact.summary())
# Value_x_D の係数 = β_Val のレジーム間変化。有意に負なら仮説支持

# =========================================================
# 4. ローリング回帰（β_Val の時変推移）
# =========================================================
window = 36  # 月
roll_beta_val = []
dates = []
for i in range(window, len(ret_m) + 1):
    sub = ret_m.iloc[i-window:i]
    X = sm.add_constant(sub[x_cols])
    m = sm.OLS(sub["Quality"], X).fit()
    roll_beta_val.append(m.params["Value"])
    dates.append(ret_m.index[i-1])

roll_beta_val = pd.Series(roll_beta_val, index=dates, name="rolling_beta_Value")

fig, ax = plt.subplots(figsize=(11, 4))
roll_beta_val.plot(ax=ax)
ax.axhline(0, color="grey", lw=0.8, ls="--")
ax.axvline(pd.Timestamp(split_date), color="red", lw=1, ls=":")
ax.set_title("Rolling 36M β(Value) of Quality L/S — デレーティング感応度の時変")
ax.set_ylabel("β_Value")
plt.tight_layout()

# =========================================================
# 5. リターン寄与分解（各期間）
# =========================================================
def return_attribution(model, df, x_cols):
    means = df[x_cols].mean()
    contrib = model.params[x_cols] * means          # 各ファクター寄与
    alpha = model.params["const"]                    # 固有α
    total = df["Quality"].mean()
    out = contrib.copy()
    out["alpha(idiosyncratic)"] = alpha
    out["total(actual mean)"] = total
    out["residual_check"] = total - (contrib.sum() + alpha)
    return out

attr_qe   = return_attribution(m_qe,   ret_qe,   x_cols)
attr_hike = return_attribution(m_hike, ret_hike, x_cols)
attribution = pd.DataFrame({"QE": attr_qe, "Hike": attr_hike})
print(attribution)
```

---

## 6. 結果の解釈フローと運用示唆

推定後、以下の判定ツリーで仮説を評価する。

|パターン|$\beta_{Val}$ の変化|$\alpha$ の変化|結論|運用示唆|
|---|---|---|---|---|
|①|負方向へ大きく拡大・有意|ほぼ不変|**デレーティング主導(仮説支持)**|構造的消滅でなく一時的逆風。ポジション維持の根拠。金利反転で回復期待|
|②|不変|大幅に負へ|クオリティ固有の劣化|バリューで説明できない悪化。EPS成長スプレッド鈍化を疑い、別途検証要。減配・縮小を検討|
|③|負方向へ拡大|も負へ|複合要因|デレーティングと固有劣化の両方。寄与度分解(§4)で主因の比率を確認|
|④|不変|不変|レジーム変化なし|そもそも「劣後」が統計的に有意か再検証|

### 補完すべき分析(本分析の弱点を埋める)

提案Aは「マルチプル感応度」をバリューでプロキシするが、これがEPS成長スプレッドの代理になっていない保証はない。次のステップで補強する。

1. **提案C(金利感応度回帰)との接続**: $\beta_{Val}$ の拡大が金利変数で説明できるなら、デレーティング経路(金利→マルチプル→クオリティ劣後)が因果的に裏づく。
2. **アナリスト予想改訂指数の活用**: 入手可能なら、クオリティ・ロング群とショート群の予想EPS改訂スプレッドを別系列で取得し、$\alpha$ の動きと突き合わせる。$\alpha$ 劣化と予想改訂悪化が連動すればパターン②、連動しなければ①。

---

## 実装上の注意点まとめ

- **対数リターンを使用**: 加法分解が成立し、寄与度分解が clean になる。
- **HAC標準誤差**: 月次ファクターリターンは自己相関・ボラティリティクラスタリングを持つため、Newey-West補正は必須。
- **多重共線性チェック**: バリューとグロースを同時投入する場合はVIFを確認。
- **多重検定調整**: レジーム分割点を複数試す、ファクターを取捨選択する過程でp-hackingが入る。最終的なシャープ比較にはDeflated Sharpe Ratioを適用。
- **構造変化点の内生的特定**: 2023年という分割を外生的に置くのではなく、Bai-Perron検定で内生的に変化点を推定し、結果が頑健か確認する。

