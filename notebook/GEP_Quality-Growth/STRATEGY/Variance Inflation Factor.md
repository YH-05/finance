

VIF（Variance Inflation Factor、分散拡大係数）は、回帰モデルにおける**多重共線性（multicollinearity）の程度を定量化する指標**である。ある説明変数が、他の説明変数群によってどの程度線形に説明されてしまうか（冗長性）を測定する。

## 定義

説明変数 X_k を、それ以外の全説明変数で回帰したときの決定係数を R²_k とすると、VIF は以下で定義される。

```
VIF_k = 1 / (1 − R²_k)
```

- R²_k が0に近い（他変数で説明されない、独立性が高い）→ VIF ≈ 1
- R²_k が1に近い（他変数でほぼ完全に説明される、冗長）→ VIF → ∞

名称が示すとおり、この係数は当該変数の回帰係数の**推定分散を何倍に膨張させるか**を表す。

```
Var(β̂_k) ∝ VIF_k
```

すなわち VIF_k = 10 であれば、多重共線性が存在しない理想的な場合に比べ、係数推定値の分散が10倍（標準誤差は√10倍）に拡大することを意味する。

## 判断基準（慣例）

|VIF値|解釈|
|---|---|
|1|完全に独立|
|1〜5|許容範囲|
|5〜10|多重共線性の懸念あり|
|> 10|深刻な多重共線性|

ただしこの閾値は経験則であり、目的（予測 vs 係数解釈）に依存する。

## このプロジェクトの文脈における含意

クオンツ・ファクター投資、特に因果ファクター投資の観点では、VIFは単なる統計的診断指標を超えた意味を持つ。

### 1. ファクター間の多重共線性とプレミアムの帰属誤り

複数ファクターを同時に回帰に投入する場合（例: value, size, quality, momentum, low-vol）、ファクター間には実質的な相関が存在する。例えばvalueとsize、qualityとlow-volは経済的に重複しうる。VIFが高い状態では、各ファクターの係数（プレミアム）推定が不安定化し、**どのファクターが真にリターンを駆動しているかの帰属が信頼できなくなる**。係数の符号反転や、サンプルをわずかに変えただけでの係数の大幅変動はこの典型的症状である。

### 2. 因果推論における位置づけ — 相関と因果の区別

ここがこのプロジェクトの文脈で最も重要な論点である。**VIFは多重共線性（変数間の統計的相関の強さ）を検出するが、その相関がいかなる因果構造から生じているかは一切区別しない。** 高いVIFは以下のいずれからも生じうる。

- 二変数が共通の**交絡要因（confounder）**を持つ
- 一方が他方の**因果的親（causal parent）**である
- 両者が**Collider**を共通の子として持つ
- 単なる偶然の標本相関（p-hacking的状況）

したがって、VIFが高いという理由だけで機械的に変数を削除すると、**因果構造上必要な変数（交絡を制御するために投入すべき変数）を誤って除去する**危険がある。逆に、VIFが低くても、それがColliderであれば回帰に入れること自体がFactor Mirage（偽の相関）を生む。VIFはこの判別に何ら情報を与えない。

換言すれば、変数選択は本来DAG（因果構造）に基づいて行われるべきであり、VIFはあくまで**「DAGで正当化された変数集合を投入した結果、推定の数値的安定性がどの程度損なわれているか」を事後的に診断する補助指標**として位置づけるのが適切である。VIFを変数選択の主たる根拠にすることは、López de Pradoが批判する「相関ベースのアプローチ」への退行に他ならない。

### 3. 実務上の対処

多重共線性が検出された場合の選択肢と、因果的観点からの評価は以下のとおり。

|対処法|内容|因果的観点からの留意点|
|---|---|---|
|変数削除|高VIF変数を除外|交絡変数を除去すると因果効果の推定にバイアス。DAGで確認必須|
|直交化|残差化・主成分（PCA）化|解釈可能性が失われ、因果的意味を持つ変数が消える|
|正則化|Ridge回帰等で係数を縮小|推定の安定化には有効だが、因果効果の不偏性は保証されない|
|変数集約|経済的に同質なファクターを統合|経済的・因果的な根拠に基づくべき|
|構造の再検討|DAGを描き直し、本来投入すべき変数集合を再定義|最も根本的かつ推奨される対処|

### 4. 計算上の補足

VIFはモデル全体の多重共線性の存在を示すが、**どの変数ペアが問題かは特定しない**。相関行列や条件数（condition number）、固有値分解と併用することで、問題の構造をより詳細に把握できる。また、VIFは線形相関のみを捉えるため、非線形な依存関係は検出できない点にも留意が必要である。

### まとめ

VIFは、ファクターモデルの推定安定性を診断する有用な統計指標である一方、その出力は相関の強さに関する情報に留まり、因果構造に関する情報を含まない。このプロジェクトの因果ファクター投資の枠組みにおいては、VIFを変数選択の判断基準そのものとして用いるのではなく、**DAGに基づく因果的変数選択を一次的な原則とし、VIFはその結果生じる推定の数値的不安定性を監視する二次的な診断ツール**として位置づけることが、方法論的に整合的である。



## 手法の分類
多重共線性への対処手法は、古典的なものから近年の機械学習・因果推論ベースのものまで多岐にわたる。最新の手法と実装を網羅的に整理する前に、いくつか確認しておくと、より文脈に即した内容を提示できる。

ただ、現時点でも包括的に提示できるため、まず手法の全体像と実装を提示し、因果推論との接続を重視した構成とする。Python実装は実行可能なレベルで記述する。

多重共線性への対処は、目的によって根本的にアプローチが分かれる。

|目的|適切なアプローチ|不適切なアプローチ|
|---|---|---|
|予測精度の最大化|正則化、次元削減、ツリーベース手法|多重共線性を気にしすぎる必要は薄い|
|係数の因果的解釈|DAGに基づく変数選択、因果調整|機械的なVIF削除、PCA|
|推定の数値的安定化|正則化、直交化|—|

以下、診断 → 古典的手法 → 現代的手法 → 因果ベース手法の順に、それぞれPython実装とともに示す。

## 0. 診断: VIFと条件数

まず問題の所在を特定する。

```python
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

def compute_vif(X: pd.DataFrame) -> pd.DataFrame:
    """各説明変数のVIFを計算する。"""
    Xc = add_constant(X)
    vif = pd.DataFrame({
        "feature": Xc.columns,
        "VIF": [variance_inflation_factor(Xc.values, i)
                for i in range(Xc.shape[1])]
    })
    return vif[vif["feature"] != "const"].sort_values("VIF", ascending=False)

def condition_number(X: pd.DataFrame) -> float:
    """設計行列の条件数。30超で多重共線性の懸念、100超で深刻。"""
    Xs = (X - X.mean()) / X.std()
    eigvals = np.linalg.eigvalsh(Xs.corr().values)
    return np.sqrt(eigvals.max() / eigvals.min())
```

条件数（condition number）はVIFを補完する。VIFは個別変数を見るが、条件数は設計行列全体の悪条件性（複数変数が絡む共線性）を捉える。固有値分解で「どの線形結合が縮退しているか」も特定できる。

## 1. 古典的手法

### 1.1 Ridge回帰（L2正則化）

多重共線性の標準的対処。係数を縮小して分散を抑えるが、変数選択は行わない（係数を完全に0にしない）。

```python
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

# alphaは交差検証で選択
model = make_pipeline(
    StandardScaler(),
    RidgeCV(alphas=np.logspace(-3, 3, 50), cv=5)
)
model.fit(X, y)
coefs = pd.Series(model[-1].coef_, index=X.columns)
```

Ridgeは相関の高い変数群に係数を分散させる性質を持つ。これは予測には有効だが、個別係数の因果的解釈には適さない点に留意する。

### 1.2 LASSO / Elastic Net

LASSOはL1正則化により係数を完全に0にし、変数選択を行う。ただし相関の高い変数群からは恣意的に1つだけ選ぶ傾向があり、選択が不安定になる。Elastic NetはL1とL2を組み合わせ、相関変数群を**グループとして**扱うためファクターモデルに適する。

```python
from sklearn.linear_model import ElasticNetCV

enet = make_pipeline(
    StandardScaler(),
    ElasticNetCV(l1_ratio=[.1, .5, .7, .9, .95, .99, 1],
                 alphas=np.logspace(-3, 1, 30), cv=5, max_iter=10000)
)
enet.fit(X, y)
```

l1_ratioが小さいほどRidge寄り（相関変数群を保持）、1に近いほどLASSO寄り（疎な選択）となる。多重共線性下では`l1_ratio`を低めにすると選択が安定する。

## 2. 次元削減・直交化手法

### 2.1 PCA回帰 / 部分最小二乗回帰（PLS）

PCAは主成分で直交化するが、目的変数を考慮しないため予測に重要な情報を捨てる場合がある。**PLS（Partial Least Squares）**は目的変数との共分散を最大化する成分を抽出するため、回帰文脈ではPCAより優れる。

```python
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import cross_val_score

# 成分数を交差検証で選択
scores = []
for n in range(1, X.shape[1] + 1):
    pls = PLSRegression(n_components=n)
    s = cross_val_score(pls, StandardScaler().fit_transform(X), y,
                        cv=5, scoring="neg_mean_squared_error")
    scores.append(s.mean())
best_n = int(np.argmax(scores)) + 1
pls = PLSRegression(n_components=best_n).fit(
    StandardScaler().fit_transform(X), y)
```

**重大な留意点**: PCA/PLSのいずれも、主成分は元の変数の線形結合であり、**因果的解釈が失われる**。「value因子の効果」を論じたい場合、主成分は対応する経済的実体を持たない。予測専用と割り切る場合のみ採用すべきである。

## 3. 現代的手法（ツリーベース・正則化系）

### 3.1 ツリーベースモデル + 適切な重要度指標

ランダムフォレストや勾配ブースティングは多重共線性に対して頑健（予測精度の意味で）だが、**特徴量重要度が共線変数間で希釈・分散される**問題がある。MDI（不純度減少）はバイアスを持つため、相関に頑健な重要度指標を使う必要がある。

ここで因果ファクター投資の文脈と直結するのが、López de Pradoが提唱する**MDA（Mean Decrease Accuracy）の改良版であるMDI/PFIの扱い**と、**クラスタリングによる共線変数のグループ化**である。

```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform

def clustered_feature_importance(X, y, n_repeats=20):
    """相関の高い変数をクラスタ化し、クラスタ単位でPermutation Importanceを評価する。
    López de Prado のClustered MDA/MDIの簡易版。"""
    # 1. 相関に基づく階層クラスタリング
    corr = X.corr(method="spearman").values
    dist = np.sqrt(0.5 * (1 - corr))          # 相関を距離に変換
    condensed = squareform(dist, checks=False)
    link = hierarchy.linkage(condensed, method="ward")
    # 距離閾値でクラスタ分割
    cluster_ids = hierarchy.fcluster(link, t=0.5, criterion="distance")
    clusters = {c: X.columns[cluster_ids == c].tolist()
                for c in np.unique(cluster_ids)}

    rf = RandomForestRegressor(n_estimators=500, max_features=1,
                               oob_score=True, n_jobs=-1, random_state=0)
    rf.fit(X, y)
    base = rf.oob_score_

    # 2. クラスタ単位でPermutation（クラスタ内全変数を同時にシャッフル）
    importances = {}
    rng = np.random.default_rng(0)
    for c, feats in clusters.items():
        scores = []
        for _ in range(n_repeats):
            Xp = X.copy()
            for f in feats:
                Xp[f] = rng.permutation(Xp[f].values)
            scores.append(base - rf.score(Xp, y))
        importances[tuple(feats)] = np.mean(scores)
    return clusters, importances
```

この手法の核心は、**相関の高い変数を個別に評価せず、クラスタとして一括評価する**点にある。共線変数を別々にシャッフルすると、片方が情報を補完して重要度がともに過小評価される（substitution effect）が、クラスタ単位なら回避できる。これはVIFによる機械的削除よりも情報損失が少ない。

### 3.2 Group LASSO

経済的に同質なファクター群（例: 複数のvalue系指標）をグループとして選択・除外する。個別変数ではなくグループ単位で疎性を課す。

```python
# pip install group-lasso
from group_lasso import GroupLasso

# groups: 各変数が属するグループID配列（同一グループは同じ整数）
groups = np.array([0, 0, 0, 1, 1, 2, 2, 2, 2])  # 例
gl = GroupLasso(groups=groups, group_reg=0.1, l1_reg=0.0,
                scale_reg="group_size", supress_warning=True)
gl.fit(StandardScaler().fit_transform(X.values), y.values)
selected = X.columns[gl.sparsity_mask_]
```

ファクターを経済的根拠でグループ化できる場合、Group LASSOは「value群を残すか落とすか」という解釈可能な変数選択を実現する。

## 4. 因果ベースの手法（このプロジェクトで最も重要）

多重共線性を「統計的に消す」のではなく、**因果構造に基づいて投入すべき変数集合を決定する**アプローチ。前回述べたとおり、これが方法論的に一次的な原則となる。

### 4.1 因果発見による変数選択

PCアルゴリズムやLiNGAMでDAGを推定し、目的変数の親（直接原因）のみを選択する。共線変数のうち、交絡経路でつながっているだけのものを構造的に除外できる。

```python
# pip install causal-learn
from causallearn.search.ConstraintBased.PC import pc
from causallearn.utils.cit import fisherz

data = np.column_stack([X.values, y.values])
labels = list(X.columns) + ["y"]

# PCアルゴリズムでCPDAGを推定
cg = pc(data, alpha=0.05, indep_test=fisherz)
cg.draw_pydot_graph(labels=labels)

# yの親（隣接ノード）を抽出 → これが因果的に正当な説明変数集合
y_idx = len(labels) - 1
adj = cg.G.graph
parents = [labels[i] for i in range(len(labels)-1)
           if adj[i, y_idx] != 0 or adj[y_idx, i] != 0]
```

```python
# LiNGAM（非ガウス・線形・非巡回を仮定）: 因果順序まで特定可能
# pip install lingam
import lingam

model = lingam.DirectLiNGAM()
model.fit(np.column_stack([X.values, y.values]))
# adjacency_matrix_[i, j] = jからiへの因果係数
adj_matrix = model.adjacency_matrix_
order = model.causal_order_
```

DAG推定後、**バックドア基準**に基づき交絡変数のみを制御変数として投入し、Colliderは投入しない。これにより、多重共線性が高くても「因果効果の推定に必要な変数」と「Factor Mirageを生むColliderや冗長変数」を原理的に区別できる。VIFによる対処と決定的に異なるのはこの点である。

### 4.2 do-calculusによる調整集合の特定

DAGが定まれば、`dowhy`等で最小十分調整集合（minimal sufficient adjustment set）を自動導出できる。これにより「どの共線変数を残し、どれを落とすべきか」が因果的に正当化される。

```python
# pip install dowhy
from dowhy import CausalModel

# graphはDOT形式またはnetworkxで指定（4.1の推定結果や事前知識から構築）
model = CausalModel(
    data=df,
    treatment="value_factor",      # 効果を推定したいファクター
    outcome="y",
    graph=causal_graph_dot         # DAG定義
)
identified = model.identify_effect(proceed_when_unidentifiable=False)
print(identified)   # backdoor調整集合が出力される
```

## 推奨される統合ワークフロー

このプロジェクトの因果ファクター投資の枠組みでは、以下の順序が方法論的に整合的である。

1. **診断**: VIF + 条件数で多重共線性の存在と程度を把握する（手法0）。
2. **目的の明確化**: 予測か因果解釈かを決定する。これが全ての分岐点となる。
3. **因果解釈が目的の場合**: 因果発見（PC/LiNGAM）でDAGを推定し（4.1）、do-calculusで調整集合を特定する（4.2）。VIFが高くても、調整に必要な変数は保持する。Colliderは除外する。
4. **予測が目的の場合**: Elastic Net（1.2）またはクラスタ化重要度を伴うツリーベース手法（3.1）を採用する。PCAは解釈を要さない場合のみ。
5. **共通の補強**: 経済的に同質なファクター群はGroup LASSO（3.2）またはクラスタリング（3.1）でグループ単位に扱い、個別の機械的削除を避ける。
6. **検証**: いずれの手法でも、変数選択後にDeflated Sharpe Ratio等で多重検定調整を行い、選択が偶然でないことを確認する。

最も強調すべき点は、**多重共線性の「排除」を自己目的化しないこと**である。López de Pradoの立場からすれば、共線性そのものが問題なのではなく、因果構造を無視した変数選択が偽の発見（Factor Mirage）を生むことが問題である。VIFや正則化は数値的安定性の補助手段に留め、変数選択の一次的根拠はDAGに基づく因果的正当化に置くべきである。

最新手法の具体的なベンチマーク比較や、特定のファクターセットを用いた実データでの実装まで踏み込む場合は、対象とするファクター群と利用可能なデータ（リターン系列の頻度、ユニバース）を指定されたい。それに応じて実行可能な完全なパイプラインを構築する。
