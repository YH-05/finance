# `ROIC_make_data_files.py` の概要

このスクリプトは、FactSet からダウンロードした Excel ファイルを元に、ROIC（投下資本利益率）に関する分析データを作成するためのデータ処理パイプラインです。

主な処理内容は以下の通りです。

1.  インデックス構成銘柄のウェイト情報と、各銘柄の ROIC・リターン情報を Excel から読み込みます。
2.  読み込んだデータを整形し、銘柄 ID（SEDOL, CUSIP）をキーとしてマージします。
3.  過去・将来のリターンや ROIC、ROIC ランク、ROIC の傾き（トレンド）など、分析用の特徴量カラムを追加します。
4.  ROIC ランクの推移に基づき、各銘柄を「高位維持」「低位維持」「高位へ移行」「低位へ下落」などのカテゴリに分類するラベルを付与します。
5.  最終的に、分析に使用する統合されたデータフレームを Parquet 形式で保存します。

また、生成したデータを用いてパフォーマンス分析や可視化を行うための補助関数も含まれています。

## 処理フロー

このスクリプトは、複数の関数をパイプラインのようにつなげて実行することを想定しています。

```python
# 想定される実行例
df = (
    merge_weight_and_roic()
    .pipe(add_forward_return_cols)          # 将来リターンのカラムを追加
    .pipe(add_shifted_roic_cols_month)      # 将来・過去ROICのカラムを追加
    .pipe(add_roic_rank_cols)               # ROICのRankカラムを追加
    # ... さらに他の処理を続ける
)
```

## 主要な関数

### データ読み込みと前処理

#### `get_constituents_weight_from_factset(file_list)`

-   **目的**: 複数の Excel ファイルから MSCI Kokusai インデックスの構成銘柄とウェイト情報を読み込みます。
-   **処理**:
    -   各ファイルを読み込み、不要な行や値を`NaN`に置換します。
    -   データを縦持ち形式（long format）に変換します。
    -   全てのデータを結合し、`MSCI KOKUSAI_weight and full id.parquet`として保存します。

#### `get_id_and_return_from_factset(excel_file)`

-   **目的**: 銘柄 ID、ROIC、価格データを含む Excel ファイルからデータを読み込み、リターンを計算します。
-   **処理**:
    -   `security_id`, `ROIC`, `Price`の各シートを読み込みます。
    -   価格データから月次、3 ヶ月、6 ヶ月、1 年、3 年、5 年のリターンおよび年率換算リターンを計算します。
    -   計算したリターンと ROIC データをマージし、`MSCI KOKUSAI_ROIC.parquet`として保存します。

### データマージと整形

#### `merge_weight_and_roic()`

-   **目的**: 上記 2 つの関数で作成されたウェイト情報と ROIC/リターン情報を統合します。
-   **処理**:
    -   銘柄 ID として`SEDOL`（6 桁）と`CUSIP`（8 桁）を区別し、それぞれでデータをマージします。
    -   ROIC の欠損値を前方補完（`ffill`）します。
    -   最終的に 1 つのデータフレームに結合し、日付と銘柄シンボルでソートして返します。

### 特徴量エンジニアリング

#### `add_forward_return_cols(df)`

-   **目的**: 各銘柄の将来（Forward）リターンを計算します。
-   **処理**: `Rtn_M`, `Rtn_3M`などのリターンカラムを未来方向にシフト（`shift(-n)`）させ、`Rtn_1MForward`などの新しいカラムを追加します。

#### `add_shifted_roic_cols_month(df, shift_direction, month_period)`

-   **目的**: 各銘柄の過去および将来の ROIC データをカラムとして追加します。
-   **処理**: `ROIC`カラムを過去方向（`shift(n)`）または未来方向（`shift(-n)`）にずらし、`ROIC_nM_Ago`や`ROIC_nM_Forward`といったカラムを追加します。

#### `add_roic_rank_cols(df, freq_suffix)`

-   **目的**: 各時点における ROIC および将来/過去 ROIC の値を 5 段階のランクに分類します。
-   **処理**:
    -   `groupby("date")`で各時点ごとにグループ化します。
    -   `pd.qcut`を使用して ROIC の値を 5 分位数に分割し、`rank1`（最高）から`rank5`（最低）までのラベルを付けます。
    -   `duplicates='drop'`引数により、同じ値が複数の分位点にまたがる場合のエラーを回避します。

#### `calculate_roic_slope_month(row, month_period)`

-   **目的**: 将来の複数時点の ROIC データを用いて、その変化の傾き（トレンド）を線形回帰で計算します。
-   **処理**: `numpy.polyfit`を使い、ROIC 時系列データの傾きを求めます。ROIC が改善傾向か悪化傾向かを示す指標となります。

#### `test_assign_roic_label(row, freq, year_period, judge_by_slope)`

-   **目的**: 将来の ROIC ランクの推移に基づいて、各銘柄にカテゴリラベルを付与します。
-   **処理**:
    -   将来の複数時点（例: 1 年後、2 年後...）の ROIC ランクを取得します。
    -   ランクの推移パターンから、以下のラベルを割り当てます。
        -   `remain high`: 期間中ずっと高ランク（rank1, rank2）を維持
        -   `remain low`: 期間中ずっと低ランク（rank4, rank5）を維持
        -   `move to high`: 低ランクから高ランクへ移行
        -   `drop to low`: 高ランクから低ランクへ下落
        -   `others`: 上記以外のパターン
        -   `np.nan`: 期間中にランクデータが欠損している場合

### 分析・可視化関数

#### `calculate_cumulative_return(...)`

-   **目的**: 指定した ROIC ラベルごとに、リターンの平均値を計算し、その累積リターンを算出します。外れ値の影響を抑えるため、リターンをクリッピング（Winsorize）する処理が含まれています。

#### `plot_roic_label_cum_return(df, ...)`

-   **目的**: `calculate_cumulative_return`で計算した ROIC ラベルごとの累積リターンを折れ線グラフでプロットします。

#### `plot_period_return(df, ...)`

-   **目的**: ROIC ラベルごとの年率リターンの分布を箱ひげ図（Box Plot）で可視化します。

#### `plot_sankey_diagram(df, ...)`

-   **目的**: ある時点の ROIC ランクから、別の時点の ROIC ランクへ、銘柄がどのように推移したかをサンキーダイアグラムで可視化します。

## 依存ライブラリ

-   pandas
-   numpy
-   pathlib
-   matplotlib
-   seaborn
-   plotly
