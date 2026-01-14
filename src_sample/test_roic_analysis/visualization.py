import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns


class ROICVisualizer:
    """ROIC分析のための可視化ツール。

    静的（Matplotlib/Seaborn）およびインタラクティブ（Plotly）なグラフを生成します。
    """

    def __init__(self):
        """ROICVisualizerのインスタンスを初期化します。

        このコンストラクタは、可視化のためのデフォルトスタイルとして
        seabornの 'whitegrid' を設定し、matplotlibの図のサイズを初期設定します。
        """
        # Set default style
        sns.set_style("whitegrid")
        plt.rcParams["figure.figsize"] = (10, 6)

    def plot_cumulative_returns(
        self,
        df_cum_return: pd.DataFrame,
        title: str = "Cumulative Returns",
        figsize: tuple = (10, 6),
    ):
        """累積リターンの時系列プロットをMatplotlib/Seabornで描画します。

        Parameters
        ----------
        df_cum_return : pd.DataFrame
            インデックスが日付で、各列が異なる戦略の累積リターンを示すDataFrame。
        title : str, optional
            グラフのタイトル, by default "Cumulative Returns"
        figsize : tuple, optional
            グラフの図のサイズ, by default (10, 6)
        """
        plt.figure(figsize=figsize)
        sns.lineplot(data=df_cum_return)
        plt.title(title)
        plt.ylabel("Cumulative Return")
        plt.xlabel("Date")
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def plot_factor_heatmap(
        self,
        portfolio_returns: pd.DataFrame,
        title: str = "Factor Double Sort Analysis",
        fmt: str = ".2%",
    ):
        """ダブルソート分析の結果をヒートマップで描画します。

        Parameters
        ----------
        portfolio_returns : pd.DataFrame
            ダブルソート分析によって得られた、各ポートフォリオの平均リターンを
            格納した行列形式のDataFrame。
        title : str, optional
            グラフのタイトル, by default "Factor Double Sort Analysis"
        fmt : str, optional
            ヒートマップ内のアノテーションのフォーマット指定子, by default '.2%'
        """
        plt.figure(figsize=(10, 8))
        sns.heatmap(portfolio_returns, annot=True, fmt=fmt, cmap="RdYlGn", center=0)
        plt.title(title)
        plt.show()

    def plot_sankey_diagram(
        self,
        df: pd.DataFrame,
        source_col: str,
        target_col: str,
        title: str = "ROIC Rank Transition",
    ):
        """ROICランクの推移などをサンキーダイアグラムで描画します。

        この関数は `plotly` を使用してインタラクティブなサンキーダイアグラムを生成します。
        例えば、ある時点でのROICランク（source_col）から、次の時点でのROICランク
        （target_col）への銘柄の遷移を可視化するのに使用できます。

        Parameters
        ----------
        df : pd.DataFrame
            遷移元と遷移先のデータを含むDataFrame。
        source_col : str
            遷移元のランクやカテゴリが含まれる列名。
        target_col : str
            遷移先のランクやカテゴリが含まれる列名。
        title : str, optional
            グラフのタイトル, by default "ROIC Rank Transition"
        """
        df_plot = df[[source_col, target_col]].dropna().copy()

        # Aggregate counts
        sankey_data = (
            df_plot.groupby([source_col, target_col]).size().reset_index(name="count")
        )

        # Create unique labels
        source_labels = sorted(df_plot[source_col].unique().tolist())
        target_labels = sorted(df_plot[target_col].unique().tolist())

        # Add suffix to distinguish source and target nodes if they share names
        # Or assume they are distinct enough or handle mapping carefully

        # Map labels to indices
        all_labels = [f"{l} (Start)" for l in source_labels] + [
            f"{l} (End)" for l in target_labels
        ]
        unique_labels = list(dict.fromkeys(all_labels))  # Preserve order
        label_to_id = {label: i for i, label in enumerate(unique_labels)}

        source_ids = []
        target_ids = []
        values = []

        for _, row in sankey_data.iterrows():
            src = f"{row[source_col]} (Start)"
            tgt = f"{row[target_col]} (End)"

            source_ids.append(label_to_id[src])
            target_ids.append(label_to_id[tgt])
            values.append(row["count"])

        # Plot
        fig = go.Figure(
            data=[
                go.Sankey(
                    node=dict(
                        pad=15,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=unique_labels,
                        color="blue",  # Can be customized
                    ),
                    link=dict(source=source_ids, target=target_ids, value=values),
                )
            ]
        )

        fig.update_layout(title_text=title, font_size=10)
        fig.show()

    def plot_bar_chart(
        self,
        series: pd.Series,
        title: str = "Performance Metrics",
        ylabel: str = "Value",
        color: str = "skyblue",
    ):
        """単純な棒グラフを描画します。

        Parameters
        ----------
        series : pd.Series
            プロットするデータ。インデックスがX軸のカテゴリ、値がY軸の高さになります。
        title : str, optional
            グラフのタイトル, by default "Performance Metrics"
        ylabel : str, optional
            Y軸のラベル, by default "Value"
        color : str, optional
            棒グラフの色, by default 'skyblue'
        """
        plt.figure(figsize=(10, 6))
        series.plot(kind="bar", color=color)
        plt.title(title)
        plt.ylabel(ylabel)
        plt.grid(axis="y")
        plt.tight_layout()
        plt.show()
