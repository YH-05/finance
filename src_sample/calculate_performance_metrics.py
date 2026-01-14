import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Optional, Tuple

import pandas as pd
from tqdm import tqdm


# ===========================================================================================
def _calculate_active_return_worker(
    args: Tuple[pd.DataFrame, str, str, bool],
) -> Optional[pd.DataFrame]:
    """
    アクティブリターン計算のワーカー関数（並列処理用）

    :param args: (df_returns, return_col, benchmark_ticker, verbose)のタプル
    :return: アクティブリターンデータ（Long形式）、エラー時はNone
    """
    df_returns, return_col, benchmark_ticker, verbose = args

    try:
        active_return_col = return_col.replace("Return", "Active_Return")

        # Wide形式に変換
        df_wide = (
            df_returns.query("variable == @return_col")
            .sort_values(["date", "symbol"])
            .reset_index(drop=True)
        )

        df_wide = pd.pivot(
            df_wide,
            index="date",
            columns="symbol",
            values="value",
        )

        # ベンチマーク存在チェック
        if benchmark_ticker not in df_wide.columns:
            if verbose:
                logging.warning(
                    f"⚠️ ベンチマーク {benchmark_ticker} が見つかりません: {return_col}"
                )
            return None

        # アクティブリターン計算
        df_wide = df_wide.subtract(df_wide[benchmark_ticker], axis=0)  # type: ignore

        # Long形式に戻す
        df_long = (
            df_wide.reset_index()
            .pipe(pd.melt, id_vars=["date"], var_name="symbol", value_name="value")
            .assign(variable=active_return_col)
            .query("symbol != @benchmark_ticker")
            .reset_index(drop=True)
        )

        return df_long

    except Exception as e:
        if verbose:
            logging.error(f"❌ エラー発生 ({return_col}): {e}")
        return None


# ===========================================================================================
def calculate_active_returns_parallel(
    df_returns: pd.DataFrame,
    return_cols: List[str],
    benchmark_ticker: str,
    max_workers: Optional[int] = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    アクティブリターンを並列処理で計算する

    :param df_returns: リターンデータ（Long形式）
    :param return_cols: 処理対象のリターン列名リスト
    :param benchmark_ticker: ベンチマークティッカー（例: "SPX Index"）
    :param max_workers: 並列実行する最大ワーカー数（Noneの場合はCPUコア数）
    :param verbose: 進捗表示フラグ
    :return: アクティブリターンデータ（Long形式）
    """
    if verbose:
        print("=" * 60)
        print("📊 アクティブリターン並列計算開始")
        print(f"   処理列数: {len(return_cols)}列")
        print(f"   ベンチマーク: {benchmark_ticker}")
        print(f"   並列度: {max_workers if max_workers else 'CPU自動'}")
        print("=" * 60)

    # データコピー
    df_active_returns = df_returns.copy()

    # 引数リストの準備
    args_list = [
        (df_active_returns, return_col, benchmark_ticker, verbose)
        for return_col in return_cols
    ]

    result_list = []
    success_count = 0
    error_count = 0

    # 並列処理実行
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Future objectsの作成
        futures = {
            executor.submit(_calculate_active_return_worker, args): args[1]
            for args in args_list
        }

        # 進捗バー付きで結果を収集
        if verbose:
            futures_iterator = tqdm(
                as_completed(futures), total=len(futures), desc="⏳ 処理中"
            )
        else:
            futures_iterator = as_completed(futures)

        for future in futures_iterator:
            return_col = futures[future]

            try:
                result = future.result()

                if result is not None and not result.empty:
                    result_list.append(result)
                    success_count += 1

                    if verbose:
                        print(f"✅ 完了: {return_col} ({len(result):,}件)")
                else:
                    error_count += 1
                    if verbose:
                        print(f"⚠️ スキップ: {return_col}")

            except Exception as e:
                error_count += 1
                if verbose:
                    print(f"❌ エラー: {return_col} - {e}")

    # 結果の統合
    if result_list:
        df_result = pd.concat(result_list, ignore_index=True)

        if verbose:
            print("=" * 60)
            print("📊 処理完了統計")
            print(f"   成功: {success_count}列")
            print(f"   エラー: {error_count}列")
            print(f"   総データ件数: {len(df_result):,}件")
            print(f"   成功率: {(success_count / len(return_cols) * 100):.1f}%")
            print("=" * 60)

        return df_result
    else:
        if verbose:
            print("⚠️ 処理可能なデータがありませんでした")
        return pd.DataFrame()


# ===========================================================================================
def calculate_active_returns_parallel_chunked(
    df_returns: pd.DataFrame,
    return_cols: List[str],
    benchmark_ticker: str,
    chunk_size: int = 5,
    max_workers: Optional[int] = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    アクティブリターンをチャンク分割して並列処理で計算する（メモリ効率版）

    :param df_returns: リターンデータ（Long形式）
    :param return_cols: 処理対象のリターン列名リスト
    :param benchmark_ticker: ベンチマークティッカー
    :param chunk_size: 一度に処理する列数
    :param max_workers: 並列実行する最大ワーカー数
    :param verbose: 進捗表示フラグ
    :return: アクティブリターンデータ（Long形式）
    """
    if verbose:
        print("=" * 60)
        print("📊 チャンク並列処理モード")
        print(f"   総列数: {len(return_cols)}列")
        print(f"   チャンクサイズ: {chunk_size}列")
        print(f"   総チャンク数: {(len(return_cols) + chunk_size - 1) // chunk_size}個")
        print("=" * 60)

    result_list = []

    # チャンクに分割
    for i in range(0, len(return_cols), chunk_size):
        chunk_cols = return_cols[i : i + chunk_size]
        chunk_num = i // chunk_size + 1
        total_chunks = (len(return_cols) + chunk_size - 1) // chunk_size

        if verbose:
            print(f"\n🔄 チャンク {chunk_num}/{total_chunks} 処理中...")

        # チャンク単位で並列処理
        df_chunk = calculate_active_returns_parallel(
            df_returns=df_returns,
            return_cols=chunk_cols,
            benchmark_ticker=benchmark_ticker,
            max_workers=max_workers,
            verbose=verbose,
        )

        if not df_chunk.empty:
            result_list.append(df_chunk)

    # 全チャンクの統合
    if result_list:
        df_final = pd.concat(result_list, ignore_index=True)

        if verbose:
            print("\n" + "=" * 60)
            print("✅ 全チャンク処理完了")
            print(f"   最終データ件数: {len(df_final):,}件")
            print("=" * 60)

        return df_final
    else:
        return pd.DataFrame()


from typing import List

import pandas as pd


# ===========================================================================================
def calculate_active_returns_vectorized(
    df_returns: pd.DataFrame,
    return_cols: List[str],
    benchmark_ticker: str,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    アクティブリターンをベクトル演算で高速に計算する（並列処理なし）

    ロジック:
    1. 対象のReturn列のみを抽出
    2. ベンチマークのデータだけを切り出し、日付と変数名(variable)をキーにして元のデータにマージ
    3. 一括で引き算を実行
    """
    if verbose:
        print("=" * 60)
        print("⚡ アクティブリターン高速計算（ベクトル化）")
        print(f"   処理列数: {len(return_cols)}列")
        print(f"   ベンチマーク: {benchmark_ticker}")
        print("=" * 60)

    # 1. 対象となる変数の行だけを抽出（コピーコストを最小限に）
    # queryよりisinの方が高速なケースが多いです
    df_target = df_returns[df_returns["variable"].isin(return_cols)].copy()

    # 2. ベンチマークのデータを抽出して整形
    # dateとvariableをキーにしてマージするため、必要な列だけにする
    df_benchmark = df_target[df_target["symbol"] == benchmark_ticker]

    if df_benchmark.empty:
        logging.error(f"❌ ベンチマーク {benchmark_ticker} がデータ内に存在しません。")
        return pd.DataFrame()

    # ベンチマークの値を 'bench_value' として用意
    df_benchmark = df_benchmark[["date", "variable", "value"]].rename(
        columns={"value": "bench_value"}
    )

    # 3. 元データにベンチマークの値をマージ (Left Join)
    # これにより、各行の横に「引くべきベンチマークの値」が並びます
    df_merged = pd.merge(df_target, df_benchmark, on=["date", "variable"], how="left")

    # 4. 一括計算 (ベクトル演算)
    # ベンチマークが見つからない(NaN)場合は計算結果もNaNになります
    df_merged["active_value"] = df_merged["value"] - df_merged["bench_value"]

    # 5. 整形
    # - ベンチマーク自身の行を除去
    # - variable名を変更 (例: 1M_Return -> 1M_Active_Return)
    # - 必要な列だけを残す

    # 文字列置換もベクトル化
    df_merged["variable"] = df_merged["variable"].str.replace("Return", "Active_Return")

    # ベンチマーク以外のシンボルを抽出
    df_result = df_merged[df_merged["symbol"] != benchmark_ticker]

    # 最終的な列の選択とリネーム
    df_final = df_result[["date", "symbol", "variable", "active_value"]].rename(
        columns={"active_value": "value"}
    )

    if verbose:
        print(f"✅ 計算完了: {len(df_final):,}件のデータを生成しました")
        print("=" * 60)

    return df_final
