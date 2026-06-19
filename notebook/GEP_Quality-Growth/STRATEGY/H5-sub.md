
クオリティ・ファクター劣後の要因分解の一環として、H5(セクター/個別銘柄集中=構成効果)を、MSCI ACWIユニバースかつBloomberg FTW（ファクターのL/S累積リターンのヒストリカルデータ）という制約下で検証する方法を解説する。

# H5（セクター集中効果）の識別 — MSCI ACWI × Bloomberg FTW制約下の分析設計

## 1. 制約の整理と分析の核心

利用可能なデータと、それが課す本質的な制約を最初に明確化する。

|項目|利用可否|含意|
|---|---|---|
|ファクターL/S累積リターン（Quality等、ACWI全体）|○ Bloomberg FTW|時系列ベースの分析が主軸|
|セクター別ファクターL/S|△ FTWで取得可なら理想|直接的な寄与度分解が可能|
|個別銘柄ウェイト・リターン|×|Brinson型の厳密な構成効果分解は不可|
|セクター中立版クオリティ指数|△ MSCI提供有無に依存|差分法の成否を分ける|

個別銘柄レベルのホールディングが無いため、**厳密なBrinson-Fachler分解（allocation effect / selection effect）は実行不可能**である。したがって本分析の核心は、「個別銘柄の構成効果を直接測る」のではなく、以下の二つの間接的識別に帰着する。

第一に、**セクター中立版と通常版の差分**によりセクター配分起因の寄与を一括で抽出する（マクロ的アプローチ）。第二に、**セクター別L/Sリターンが取得できる場合、各セクターの寄与度を分解**する（ミクロ的アプローチ）。後者が取得できない場合は、外部のセクター指数を代理変数とした回帰ベースの近似に切り替える。

---

## 2. アプローチA：セクター中立版との差分（最優先・最も明快）

### 2.1 原理

MSCIは多くのファクター指数で「Sector Neutral」版を提供している。クオリティについては典型的に以下が存在する。

- **MSCI ACWI Quality Index**（通常版）：セクター制約なしでクオリティ高スコア銘柄を選好
- **MSCI ACWI Quality Sector Neutral / Sector Capped 系**：各セクターのウェイトを親指数（ACWI）に一致させた上でクオリティを選好

両者の差は、定義上「セクター配分（allocation）の効果」に一致する。

$$ R^{\text{normal}}_t = \underbrace{R^{\text{sector-neutral}}_t}_{\text{セクター内のクオリティ選好}} + \underbrace{\left(R^{\text{normal}}_t - R^{\text{sector-neutral}}_t\right)}_{\text{セクター配分効果}} $$

この差分時系列 $D_t = R^{\text{normal}}_t - R^{\text{sector-neutral}}_t$ が、クオリティ劣後のうちセクター集中に起因する部分である。

### 2.2 検証手順

1. **データ取得**：通常版とセクター中立版のクオリティ指数（ロング・オンリーで可。L/Sが取れればなお良い）の累積リターンを同一期間・同一通貨建てで取得。MSCI ACWIを共通ベンチマークとする。
2. **超過リターン化**：両指数のACWI超過リターンを計算。$E^{\text{normal}}_t = R^{\text{normal}}_t - R^{\text{ACWI}}_t$、同様に $E^{\text{neutral}}_t$。
3. **差分の累積**：$D_t = E^{\text{normal}}_t - E^{\text{neutral}}_t$ を累積し、劣後局面（直近7-8年）における寄与を可視化。
4. **判定**：
    - $E^{\text{neutral}}$ も同程度に劣後 → セクター集中は主因でない（クオリティ・ファクター固有の問題）
    - $E^{\text{neutral}}$ は劣後せず $D_t$ が大きく負 → 劣後はセクター配分起因（H5を支持）

### 2.3 留意点

L/S版が無くロング・オンリー版しか取れない場合、差分はロング側の構成効果のみを捉える。FTWのL/Sはロング−ショートのスプレッドであるため、ロング・オンリー差分との直接接続には注意が必要である。少なくともロング側のセクター集中の寄与方向は判定できる。

---

## 3. アプローチB：セクター別L/Sの寄与度分解（FTWでセクター別が取得可能な場合）

### 3.1 原理

FTWでセクター別のクオリティL/Sリターンが取得できる場合、全体のL/Sリターンを各セクターの寄与に分解する。ただし**FTWのセクター別L/Sはセクター内L/S（intra-sector）か全体L/Sのセクター属性別か**を必ず確認する。両者で解釈が全く異なる。

全体クオリティL/Sリターンは、各セクターの寄与の加重和として近似できる。

$$ R^{L/S}_t \approx \sum_{s=1}^{S} w_{s,t} \cdot r^{L/S}_{s,t} $$

ここで $r^{L/S}_{s,t}$ はセクター $s$ のクオリティL/Sリターン、$w_{s,t}$ はそのセクターの寄与ウェイト。

### 3.2 寄与度（contribution）の算出

累積寄与をセクター別に算出する。

$$ \text{Contrib}_s = \sum_{t \in T} w_{s,t} \cdot r^{L/S}_{s,t} $$

これを全期間と劣後局面に分けて集計し、劣後への寄与が特定セクター（ヘルスケア、生活必需品、テクノロジー等）に集中しているかを確認する。

### 3.3 集中度の定量化

寄与の集中度をHerfindahl-Hirschman型の指標で測る。

$$ HHI_{\text{contrib}} = \sum_{s=1}^{S} \left( \frac{|\text{Contrib}_s|}{\sum_j |\text{Contrib}_j|} \right)^2 $$

$HHI$ が高い（1/Sを大きく上回る）ほど、劣後が少数セクターに集中していることを示す。これがH5の定量的根拠となる。

---

## 4. アプローチC：外部セクター指数による回帰近似（セクター別L/Sが取れない場合の代替）

セクター別L/Sがどうしても取れない場合、MSCI ACWIの**セクター別指数（ロング・オンリー）を説明変数とし、クオリティL/Sリターンを回帰することで、どのセクターの動きがクオリティL/Sを駆動しているかを近似的に識別する。**

### 4.1 回帰モデル

$$ R^{L/S, \text{Quality}}_t = \alpha + \sum_{s=1}^{S} \beta_s \cdot \left( R^{\text{Sector}_s}_t - R^{\text{ACWI}}_t \right) + \epsilon_t $$

各セクターのACWI超過リターンに対するクオリティL/Sの感応度 $\beta_s$ を推定する。$\beta_s$ が大きく有意なセクターが、クオリティL/Sを構造的に駆動している。

### 4.2 因果上の注意（ユーザーの関心領域に即して）

この回帰は**因果ではなく連動構造の記述**である点を強調する。セクター指数自体がクオリティ銘柄を含むため、説明変数と被説明変数の間に機械的な重複（mechanical linkage）が生じ、$\beta_s$ は構成効果と共変動効果の混合となる。ここでセクター指数を不用意に多数投入すると、ユーザーが懸念する**Factor Mirage（colliderを回帰に入れることで生じる偽相関）**のリスクがある。具体的には、共通の上流要因（金利・景気レジーム＝H7）がセクターとクオリティ双方を駆動している場合、セクター変数はその経路を媒介・遮断し、係数が誤誘導される。

対処として、(1) ローリング回帰で $\beta_s$ の時間変化を見る、(2) H7のマクロ変数を統制した上で残差感応度を測る、(3) セクター変数を全投入せず、事前にクオリティ高ウェイトのセクター（テクノロジー、ヘルスケア、生活必需品）に絞る、という設計が望ましい。アプローチCはAとBの補完であり、単独で因果的結論を出すべきでない。

---

## 5. 実装例（Python）

アプローチA・B・Cを統合した分析スケルトンを示す。Bloomberg FTWからの取得部分はプレースホルダとし、データフレームの構造を明示する。

```python
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# =========================================================
# 0. データ構造の前提
#   - すべて月次/日次リターン（累積ではなく期間リターン）に変換済みとする
#   - FTWから取得した累積リターンは pct_change で期間リターン化
# =========================================================

# 累積リターン -> 期間リターン変換ユーティリティ
def cum_to_period(cum_series: pd.Series) -> pd.Series:
    """FTWの累積リターン（指数値 or 累積%）を期間リターンに変換"""
    # 指数値（基準=100等）の場合
    return cum_series.pct_change().dropna()

# =========================================================
# アプローチA: セクター中立版との差分
# =========================================================
def approach_A(df: pd.DataFrame, regime_start: str) -> dict:
    """
    df columns:
      'quality_normal'  : MSCI ACWI Quality 通常版リターン
      'quality_neutral' : MSCI ACWI Quality Sector Neutral版リターン
      'acwi'            : MSCI ACWI リターン
    """
    E_normal  = df['quality_normal'] - df['acwi']   # 通常版 超過
    E_neutral = df['quality_neutral'] - df['acwi']  # 中立版 超過
    D = E_normal - E_neutral                        # セクター配分効果

    # 累積
    cum = pd.DataFrame({
        'E_normal_cum':  (1 + E_normal).cumprod() - 1,
        'E_neutral_cum': (1 + E_neutral).cumprod() - 1,
        'D_cum':         (1 + D).cumprod() - 1,
    })

    # 劣後局面の集計
    sub = df.loc[regime_start:]
    result = {
        'allocation_effect_total': (1 + (sub['quality_normal'] - sub['quality_neutral'])).prod() - 1,
        'neutral_excess_total':    (1 + (sub['quality_neutral'] - sub['acwi'])).prod() - 1,
        'normal_excess_total':     (1 + (sub['quality_normal'] - sub['acwi'])).prod() - 1,
        'cum_df': cum,
    }
    # 判定
    if result['neutral_excess_total'] > result['normal_excess_total']:
        result['verdict'] = "セクター配分が劣後を悪化（H5支持）"
    else:
        result['verdict'] = "中立版も劣後（クオリティ固有の問題、H5は主因でない）"
    return result


# =========================================================
# アプローチB: セクター別L/Sの寄与度分解
# =========================================================
def approach_B(sector_ls: pd.DataFrame, weights: pd.DataFrame,
               regime_start: str) -> pd.DataFrame:
    """
    sector_ls : columns=セクター名, 各セクターのクオリティL/Sリターン（期間リターン）
    weights   : columns=セクター名, 各セクターの寄与ウェイト（合計1）
                ※ FTWで取れない場合はACWIのセクター時価ウェイトで近似
    """
    sub_ls = sector_ls.loc[regime_start:]
    sub_w  = weights.loc[regime_start:]

    # 期間ごとの寄与 = weight * L/S return
    contrib_t = sub_w * sub_ls

    # 累積寄与（線形近似: 期間寄与の総和）
    contrib_total = contrib_t.sum(axis=0).sort_values()

    # 集中度 HHI
    abs_contrib = contrib_total.abs()
    shares = abs_contrib / abs_contrib.sum()
    hhi = (shares ** 2).sum()
    n_sectors = len(contrib_total)

    out = contrib_total.to_frame('cum_contribution')
    out['share_of_abs'] = shares
    out.attrs['HHI'] = hhi
    out.attrs['HHI_equal'] = 1 / n_sectors  # 均等分散の基準値
    out.attrs['concentrated'] = hhi > 2 * (1 / n_sectors)
    return out


# =========================================================
# アプローチC: 外部セクター指数による回帰近似
# =========================================================
def approach_C(quality_ls: pd.Series, sector_excess: pd.DataFrame,
               macro: pd.DataFrame = None) -> pd.DataFrame:
    """
    quality_ls    : クオリティL/Sリターン（期間）
    sector_excess : columns=セクター名, 各セクターのACWI超過リターン
    macro         : H7統制用マクロ変数（実質金利, ISM, 信用スプレッド等）
    """
    X = sector_excess.copy()
    if macro is not None:
        X = X.join(macro, how='inner')   # H7統制を追加
    X = sm.add_constant(X)
    y = quality_ls.reindex(X.index).dropna()
    X = X.reindex(y.index)

    # Newey-West（系列相関・不均一分散にロバスト）
    model = sm.OLS(y, X).fit(cov_type='HAC', cov_kwds={'maxlags': 6})
    res = pd.DataFrame({
        'beta':   model.params,
        't_stat': model.tvalues,
        'p_val':  model.pvalues,
    })
    res.attrs['adj_r2'] = model.rsquared_adj
    return res


# =========================================================
# ローリング感応度（時間変化の確認・Factor Mirage対策）
# =========================================================
def rolling_beta(quality_ls: pd.Series, sector_excess: pd.Series,
                 window: int = 36) -> pd.Series:
    betas = []
    idx = []
    for i in range(window, len(quality_ls)):
        y = quality_ls.iloc[i-window:i]
        x = sm.add_constant(sector_excess.iloc[i-window:i])
        try:
            b = sm.OLS(y, x).fit().params.iloc[1]
            betas.append(b); idx.append(quality_ls.index[i])
        except Exception:
            continue
    return pd.Series(betas, index=idx)
```

---

## 6. 判定の統合と運用示唆

三つのアプローチの結果を突き合わせ、以下の整理で結論を導く。

|アプローチA（中立版差分）|アプローチB（寄与集中）|アプローチC（回帰）|解釈|運用示唆|
|---|---|---|---|---|
|配分効果が大きく負|HHI高・特定セクター集中|特定 $\beta_s$ が支配的|H5強く支持：劣後はセクター集中由来|セクター中立運用で回避可能、クオリティ概念自体は健全|
|配分効果ほぼゼロ|HHI低・分散|係数分散|H5棄却：クオリティ・ファクター固有の問題|H1（ファンダメンタルズ）・H0（デレーティング）を優先検証|
|配分効果が中程度|一部集中|マクロ統制で $\beta_s$ 消失|セクター集中は見かけ、真因はH7|景気レジーム次第、セクター調整では解決せず|

最も注意すべきは三行目である。セクター変数で劣後が説明できても、それが上流のマクロ・レジーム（H7）の写しであれば、セクター中立化という運用対応は的を外す。したがってアプローチCでは必ずマクロ変数を統制した残差感応度を確認し、H5とH7を切り分ける必要がある。

---

## 7. 次のステップ — データ取得可否の確認

実装の優先順位を確定するため、以下を確認したい。

第一に、**MSCI ACWI Quality のセクター中立版（Sector Neutral / Capped）の累積リターン**がBloomberg経由で取得可能か。取得できればアプローチAが最も明快で、これを主軸に据える。第二に、**FTWのセクター別クオリティL/Sリターン**が取得可能か、また取得できる場合それがセクター内L/Sか全体L/Sのセクター属性別かを確認したい。これによりアプローチBの可否と解釈が定まる。いずれも不可の場合はアプローチC（外部セクター指数回帰）を主軸とするが、その場合はFactor Mirageの制約から結論を補助的なものに留める。

取得可能なデータ系列の具体的なティッカー・期間・頻度を共有してもらえれば、上記スケルトンを実データに接続した完全な検証コードに展開する。
