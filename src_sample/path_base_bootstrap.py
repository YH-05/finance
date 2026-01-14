import concurrent.futures
import itertools
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm


# ============================================================
def run_portfolio_bootstrap(
    prices_df: pd.DataFrame,
    weights: dict,
    simulation_days: int = 504,
    n_simulations: int = 5000,
    risk_free_rate: float = 0.0,
    generate_plot: bool = True,
    verbose: bool = False,
):
    """
    過去の価格データから開始日をブートストラップ抽出し、
    ポートフォリオの将来パス（価値）をシミュレートする。

    Parameters
    ----------
    prices_df : pd.DataFrame
        インデックスが日付、カラムがティッカーの価格DF
    weights : dict
        ティッカーをキー、ウェイトを値とする辞書
    simulation_days : int, default 504
        1シミュレーションあたりの日数 (デフォルト 504 = 2年)
    n_simulations : int, default 5000
        シミュレーション回数
    risk_free_rate : float, default 0.0
        年率リスクフリーレート（シャープレシオ計算用）
    generate_plot : bool, default True
        プロットを生成するかどうか
    verbose : bool, default False
        詳細なログを出力するかどうか

    Returns
    -------
    tuple
        (dict: 統計結果, matplotlib.figure.Figure: シミュレーションチャート)
    """

    # 1. 入力データの準備
    tickers = list(weights.keys())
    # 辞書からPandas Seriesを作成（順序を固定するため）
    weights_series = pd.Series(weights)[tickers]

    # シミュレーション対象の価格データ（ウェイトが指定されたティッカーのみ）
    prices_subset = prices_df[tickers]

    # 抽出可能な最大開始インデックス
    # (データ長 - シミュレーション日数) が最後の開始可能位置
    max_start_index = len(prices_subset) - simulation_days

    if max_start_index < 0:
        raise ValueError(
            f"データ期間 ({len(prices_subset)}日) が "
            f"シミュレーション日数 ({simulation_days}日) より短いです。"
        )

    all_paths_list = []
    final_returns = []
    max_drawdowns = []

    # --- 修正点 1: 統計量リストの追加 ---
    all_annualized_returns = []
    all_annualized_volatilities = []
    all_sharpe_ratios = []

    # --- 修正点 2: ループ前に年数と日次RFレートを計算 ---
    years = simulation_days / 252.0
    # 日次リスクフリーレートの計算 (シャープレシオ用)
    daily_risk_free_rate = (1 + risk_free_rate) ** (1 / 252) - 1

    # 2. シミュレーションループ
    if verbose:
        print(f"Running {n_simulations} simulations...")
    for _ in range(n_simulations):
        # a. 開始日のランダム抽出
        start_index = np.random.randint(0, max_start_index + 1)

        # b. 過去の価格変動パスを切り出し
        path_df = prices_subset.iloc[start_index : start_index + simulation_days]

        # c. パスの正規化
        normalized_path_df = path_df / path_df.iloc[0]

        # d. ポートフォリオ・パスの計算
        portfolio_path = normalized_path_df.dot(weights_series)
        all_paths_list.append(portfolio_path.reset_index(drop=True))

        # e. 統計量のための計算 (最終リターンとMDD)
        total_return = portfolio_path.iloc[-1] - 1
        final_returns.append(total_return)

        cumulative_max = portfolio_path.cummax()
        drawdown = (portfolio_path - cumulative_max) / cumulative_max
        max_drawdowns.append(drawdown.min())

        # --- 修正点 3: 各パスの効率性（シャープレシオ等）の計算 ---

        # f-1. 年率リターン (トータルリターンから幾何平均で計算)
        # (1 + 最終リターン) ^ (1 / 年数) - 1
        annualized_return = (1 + total_return) ** (1 / years) - 1
        all_annualized_returns.append(annualized_return)

        # f-2. 年率ボラティリティ (日次リターンから計算)
        daily_returns = portfolio_path.pct_change().dropna()
        annualized_volatility = daily_returns.std() * np.sqrt(252)
        all_annualized_volatilities.append(annualized_volatility)

        # f-3. 年率シャープレシオ (日次リターンから計算)
        if daily_returns.empty or daily_returns.std() == 0:
            sharpe_ratio = np.nan
        else:
            # 日次の平均超過リターン
            mean_daily_excess_return = daily_returns.mean() - daily_risk_free_rate
            # 日次の標準偏差
            std_daily_return = daily_returns.std()
            # 年率換算
            sharpe_ratio = (mean_daily_excess_return / std_daily_return) * np.sqrt(252)

        all_sharpe_ratios.append(sharpe_ratio)

    # 3. 統計量の集計
    if verbose:
        print("Aggregating results...")
    all_paths_df = pd.concat(all_paths_list, axis=1, keys=range(n_simulations))

    # 2年後のリターンの分布
    mean_2y_return = np.mean(final_returns)
    variance_2y_return = np.var(final_returns)
    std_dev_2y_return = np.std(final_returns)

    # MDDの分布
    mean_mdd = np.mean(max_drawdowns)
    worst_mdd = np.min(max_drawdowns)

    # --- 修正点 4: 効率性（シャープレシオ等）の集計 ---
    # 各パスから計算した統計量の平均値（または中央値）
    # np.nanmean / np.nanmedian は NaN を無視して計算する
    mean_annualized_return = np.nanmean(all_annualized_returns)
    mean_annualized_volatility = np.nanmean(all_annualized_volatilities)
    mean_sharpe_ratio = np.nanmean(all_sharpe_ratios)
    median_sharpe_ratio = np.nanmedian(all_sharpe_ratios)

    # グラフ描画用に平均パスを計算
    mean_path = all_paths_df.mean(axis=1)

    # (元のコードの計算ロジックは削除)

    stats = {
        "simulation_period_years": years,
        "n_simulations": n_simulations,
        "mean_2y_return": mean_2y_return,
        "variance_2y_return": variance_2y_return,
        "std_dev_2y_return": std_dev_2y_return,
        "median_2y_return": np.median(final_returns),
        "return_5th_percentile (VaR)": np.percentile(final_returns, 5),
        "return_95th_percentile": np.percentile(final_returns, 95),
        "mean_mdd": mean_mdd,
        "worst_mdd (min)": worst_mdd,
        "mdd_5th_percentile": np.percentile(max_drawdowns, 5),
        # --- 修正後の統計量 ---
        "annualized_return (mean of paths)": mean_annualized_return,
        "annualized_volatility (mean of paths)": mean_annualized_volatility,
        "sharpe_ratio (mean of paths)": mean_sharpe_ratio,
        "sharpe_ratio (median of paths)": median_sharpe_ratio,
    }
    # 4. 可視化 (Matplotlib)
    fig = None
    if generate_plot:
        if verbose:
            print("Generating plot...")
        fig, ax = plt.subplots(figsize=(12, 7))

        # 全パスをグレーで描画 (alphaで透明度を調整)
        # n_simulations が多い場合は linewidth を細く、alpha を低く設定
        ax.plot(
            all_paths_df.index,
            all_paths_df,
            color="grey",
            alpha=max(0.05, 1 / np.sqrt(n_simulations)),  # 回数に応じて調整
            linewidth=0.5,
        )

        # 平均パスを赤で描画
        ax.plot(
            mean_path.index,
            mean_path,
            color="red",
            linewidth=2.5,
            label=f"Mean Path (N={n_simulations})",
        )

        # 1.0の基準線 (元本ライン)
        ax.axhline(
            1.0, color="black", linestyle="--", linewidth=1, label="Start Value (1.0)"
        )

        ax.set_xlabel("Elapsed Trading Days (From Start)")
        ax.set_ylabel("Normalized Portfolio Value (Start=1.0)")
        ax.set_title(f"Portfolio Bootstrap Simulation ({years:.1f} Years)")
        # y軸範囲
        # final_returns は、最終的なポートフォリオ価値 - 1 なので、
        # グラフのY軸範囲は「ポートフォリオ価値」で考える必要がある。
        # したがって、final_returns (リターン) に 1 を足してポートフォリオ価値に変換する。

        # 全シミュレーションの最終ポートフォリオ価値
        final_portfolio_values = np.array(final_returns) + 1.0

        # 最終ポートフォリオ価値の最小値と最大値
        min_final_value = final_portfolio_values.min()
        max_final_value = final_portfolio_values.max()

        # Y軸の下限を0.05単位で切り下げ
        # (min_final_value // 0.05) * 0.05 は0.05単位で切り捨てる計算
        # np.floor() を使うと安全
        y_min = np.floor(min_final_value / 0.05) * 0.05

        # Y軸の上限を0.05単位で切り上げ
        # (max_final_value // 0.05 + 1) * 0.05 は0.05単位で切り上げる計算
        # np.ceil() を使うと安全
        y_max = np.ceil(max_final_value / 0.05) * 0.05

        # Y軸の範囲を設定
        ax.set_ylim(y_min, y_max)

        ax.legend()
        ax.grid(True, linestyle=":", alpha=0.7)

    return stats, fig


# ============================================================
def run_multiple_bootstrap_simulations(
    prices_df: pd.DataFrame,
    simulation_days: int = 504,
    n_simulations: int = 1000,
    risk_free_rate: float = 0.0,
    weight_step: float = 0.05,
    output_path: Path = Path("bootstrap_results.csv"),
    max_workers: int = None,
):
    """
    複数のウェイト組み合わせでポートフォリオのブートストラップシミュレーションを実行し、
    結果をファイルに保存する。

    Parameters
    ----------
    prices_df : pd.DataFrame
        インデックスが日付、カラムがティッカーの価格DF
    simulation_days : int, default 504
        1シミュレーションあたりの日数
    n_simulations : int, default 1000
        1ウェイトあたりのシミュレーション回数
    risk_free_rate : float, default 0.0
        年率リスクフリーレート
    weight_step : float, default 0.05
        ウェイトの刻み幅 (例: 0.05)
    output_path : Path, default Path("bootstrap_results.csv")
        結果を保存するファイルパス ('.csv' or '.json')
    max_workers : int, optional
        並列処理に使用する最大プロセス数. Defaults to None (os.cpu_count()).

    Returns
    -------
    pd.DataFrame
        全てのシミュレーション結果をまとめたDataFrame
    """

    def _generate_weights(tickers, step):
        """ウェイトの合計が1になる組み合わせを生成するジェネレータ"""
        n_tickers = len(tickers)
        n_units = int(1 / step)

        for combo in itertools.combinations_with_replacement(range(n_tickers), n_units):
            counts = np.bincount(combo, minlength=n_tickers)
            yield dict(zip(tickers, counts * step, strict=False))

    tickers = prices_df.columns.tolist()
    print("Generating weight combinations...")
    weight_combinations = list(_generate_weights(tickers, weight_step))
    print(f"Total {len(weight_combinations)} weight combinations to simulate.")

    all_results = []

    # for weights in weight_combinations:
    #     try:
    #         # 各ウェイトでシミュレーションを実行
    #         stats, _ = run_portfolio_bootstrap(
    #             prices_df=prices_df,
    #             weights=weights,
    #             simulation_days=simulation_days,
    #             n_simulations=n_simulations,
    #             risk_free_rate=risk_free_rate,
    #             generate_plot=False,
    #             verbose=False,
    #         )

    #         # ウェイト情報を統計結果に追加
    #         result_row = weights.copy()
    #         result_row.update(stats)
    #         all_results.append(result_row)

    #     except ValueError as e:
    #         print(f"Skipping simulation for weights {weights} due to error: {e}")
    #         continue

    # ProcessPoolExecutorを使用してシミュレーションを並列実行
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 各ウェイトの組み合わせに対してシミュレーションタスクを投入
        print("Submitting simulation tasks to executor...")
        futures = {
            executor.submit(
                run_portfolio_bootstrap,
                prices_df,
                weights,
                simulation_days,
                n_simulations,
                risk_free_rate,
                False,
                False,
            ): weights
            for weights in weight_combinations
        }
        print("Collecting simulation results...")

        # tqdmを使って進捗バーを表示しながら、完了したタスクから結果を取得
        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(weight_combinations),
            desc="Simulating weight combinations",
        ):
            weights = futures[future]
            try:
                stats, _ = future.result()
                result_row = {**weights, **stats}
                all_results.append(result_row)
            except Exception as e:
                print(f"Simulation for weights {weights} failed with error: {e}")
        print("All simulations completed.")

    if not all_results:
        print("No simulations were successfully completed.")
        return pd.DataFrame()

    # 結果をDataFrameに変換
    results_df = pd.DataFrame(all_results)

    # ファイル形式に応じて保存
    if output_path.suffix == ".csv":
        results_df.to_csv(output_path, index=False)
        print(f"Results saved to {output_path}")
    elif output_path.suffix == ".json":
        results_df.to_json(output_path, orient="records", indent=4)
        print(f"Results saved to {output_path}")
    else:
        print(
            f"Warning: Unsupported file extension for '{output_path}'. "
            "Please use '.csv' or '.json'."
        )

    return results_df


# ============================================================
def print_bootstrap_stats(simulation_stats: dict) -> None:
    """
    ブートストラップシミュレーションの統計情報を整形して表示する。

    Parameters
    ----------
    simulation_stats : dict
        `run_portfolio_bootstrap` 関数からの統計情報辞書
    """
    print("--- Simulation Statistics (2-Year Horizon) ---")
    print("=" * 55)
    for key, value in simulation_stats.items():
        # 値に応じてフォーマットを調整
        if "mdd" in key or "return" in key or "volatility" in key:
            print(f"{key:<40}: {value: >10.2%}")
        elif "variance" in key:
            print(f"{key:<40}: {value: >10.4f}")
        elif key == "n_simulations" or key == "simulation_period_years":
            print(f"{key:<40}: {int(value): >10}")
        else:
            print(f"{key:<40}: {value: >10.3f}")
    print("=" * 55)


# ============================================================
