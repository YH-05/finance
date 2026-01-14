import marimo

__generated_with = "0.19.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Implement Factset and Bloomberg formulas
    """)
    return


@app.cell
def _():
    # magic command not supported in marimo; please file an issue to add support
    # %load_ext autoreload
    # '%autoreload 2' command supported automatically in marimo
    import pandas as pd
    import numpy as np
    import os, sys
    from dotenv import load_dotenv
    from pathlib import Path
    from tqdm import tqdm
    import yaml
    import datetime
    from dateutil.relativedelta import relativedelta
    import warnings
    warnings.simplefilter('ignore')
    load_dotenv()
    QUANTS_DIR = Path(os.environ.get('QUANTS_DIR'))
    SRC_DIR = Path(os.environ.get('SRC_DIR'))
    FACTSET_ROOT_DIR = Path(os.environ.get('FACTSET_ROOT_DIR'))
    FACTSET_FINANCIALS_DIR = Path(os.environ.get('FACTSET_FINANCIALS_DIR'))  # type: ignore
    FACTSET_INDEX_CONSTITUENTS_DIR = Path(os.environ.get('FACTSET_INDEX_CONSTITUENTS_DIR'))  # type: ignore
    BPM_ROOT_DIR = Path(os.environ.get('BPM_ROOT_DIR'))  # type: ignore
    BPM_DATA_DIR = Path(os.environ.get('BPM_DATA_DIR'))  # type: ignore
    BPM_SRC_DIR = Path(os.environ.get('BPM_SRC_DIR'))  # type: ignore
    BLOOMBERG_DATA_DIR = Path(os.environ.get('BLOOMBERG_DATA_DIR'))  # type: ignore
    BLOOMBERG_PRICE_DIR = Path(os.environ.get('BLOOMBERG_PRICE_DIR'))  # type: ignore
    sys.path.insert(0, str(QUANTS_DIR))  # type: ignore
    import src.factset_utils as factset_utils  # type: ignore
    import src.implement_FS_BBG_formulas_utils as implement_utils  # type: ignore
    import src.bloomberg_utils as bloomberg_utils
    formula_xlsx = FACTSET_ROOT_DIR / 'FDS samples and Factset Formulas.xlsx'
    with open(SRC_DIR / 'BPM_Index-code-map.yaml') as _f:
        bpm_code_map = yaml.safe_load(_f)
    return (
        BLOOMBERG_PRICE_DIR,
        BPM_DATA_DIR,
        FACTSET_FINANCIALS_DIR,
        FACTSET_INDEX_CONSTITUENTS_DIR,
        FACTSET_ROOT_DIR,
        bloomberg_utils,
        bpm_code_map,
        factset_utils,
        implement_utils,
        np,
        pd,
        relativedelta,
        tqdm,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. BPM からダウンロードした Index 構成銘柄の paruqet ファイルを読み取る

    -   (Universe name)\_Constituents.parquet から Factset の P_SYMBOL と FG_COMPANY_NAME をダウンロードするエクセルファイルを作成。
    -   その後、すべてのインデックスをまとめて parquet ファイルに保存。
    """)
    return


@app.cell
def _(BPM_DATA_DIR, display, factset_utils):
    _start_date = '2000-01-31'
    _end_date = '2025-11-30'
    # 対象インデックスディレクトリ
    index_dir = [s for s in list(BPM_DATA_DIR.iterdir()) if s.is_dir() & s.name.startswith('MS')]
    display(index_dir)
    factset_utils.load_bpm_and_export_factset_code_file(index_dir=index_dir, start_date=_start_date, end_date=_end_date)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2.（Factset でデータダウンロード後）ファイル統合

    -   FACTSET のダウンロードが終わったら、Excel を CSV 出力しておくこと。
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2-1. Factset コード統合
    """)
    return


@app.cell
def _(factset_utils):
    factset_utils.unify_factset_code_data()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 2-2. Bloomberg から Ticker と FIGI 取得

    -   blpapi を使用してダウンロード
    -   これにて最終的な構成銘柄の全データ収集完了
    """)
    return


@app.cell
def _(
    FACTSET_INDEX_CONSTITUENTS_DIR,
    bloomberg_utils,
    factset_utils,
    np,
    pd,
    relativedelta,
    tqdm,
):
    # ------------------------------------
    # parquetファイル読み込み
    _file_list = list(FACTSET_INDEX_CONSTITUENTS_DIR.glob('Index_Constituents_with_Factset_code-compressed-*.parquet'))
    _dfs = [pd.read_parquet(_f) for _f in _file_list]
    df_members = pd.concat(_dfs, ignore_index=True).fillna(np.nan).assign(SEDOL=lambda x: x['SEDOL'].astype(str).str.zfill(7), date=lambda x: pd.to_datetime(x['date']))
    blp = bloomberg_utils.BlpapiCustom()
    output_dfs = []
    for date in tqdm(df_members['date'].unique()):
        _df_slice = df_members.loc[df_members['date'] == date].reset_index(drop=True)
        _sedol_list = _df_slice['SEDOL'].dropna().astype(str).str.zfill(7)
        _sedol_list = [str(s) + ' Equity' for s in _sedol_list.tolist()]
        _cusip_list = [str(s) + ' Equity' for s in _df_slice['CUSIP'].dropna().tolist()]
        _isin_list = [str(s) + ' Equity' for s in _df_slice['ISIN'].dropna().tolist()]
        _start_date = (date + relativedelta(months=1)).replace(day=1).strftime('%Y%m%d')
        _end_date = ((date + relativedelta(months=2)).replace(day=1) - relativedelta(days=1)).strftime('%Y%m%d')
        df_sedol = blp.load_ids_from_blpapi(id_type='SEDOL', id_list=_sedol_list, as_of_date=date)
        df_cusip = blp.load_ids_from_blpapi(id_type='CUSIP', id_list=_sedol_list, as_of_date=date)
        df_isin = blp.load_ids_from_blpapi(id_type='ISIN', id_list=_sedol_list, as_of_date=date)
        df_output = pd.merge(_df_slice, df_sedol, on=['date', 'SEDOL'], how='left')
    # blpapiでデータダウンロード
        df_output = pd.merge(df_output, df_cusip, on=['date', 'CUSIP'], how='left')
        df_output = pd.merge(df_output, df_isin, on=['date', 'ISIN'], how='left')
        output_dfs.append(df_output)
    df_output = pd.concat(output_dfs, ignore_index=True)
    df_output['Weight (%)'] = df_output['Weight (%)'].astype(float)
    factset_utils.split_and_save_dataframe(df_all=df_output, base_dir=FACTSET_INDEX_CONSTITUENTS_DIR, n_splits=6, base_filename='Index_Constituents_w_Factset_and_Bloomberg-compressed-', compression='zstd', index=False)  # 翌月1日  # 翌月末  # merge
    return


@app.cell
def _(FACTSET_ROOT_DIR, display, pd):
    # 必要に応じて欠損値チェック（date, Universeごとに）
    _file_list = list(FACTSET_ROOT_DIR.glob('Index_Constituents/M*_Index_Constituents_with_Factset_code.parquet'))
    _dfs = [pd.read_parquet(_f) for _f in _file_list]
    for _df in _dfs:
        _df['Weight (%)'] = _df['Weight (%)'].astype(float)
        _df['P_SYMBOL_MISS'] = _df['P_SYMBOL'].isnull()
        g = pd.DataFrame(_df.groupby(['date', 'Universe', 'P_SYMBOL_MISS'])['Weight (%)'].agg(['count', 'sum']))
        display(g)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Financial Data Download 用ファイル作成

    -   Factset の Financials データ取得用の関数を Excel ファイルに埋め込む
    -   ユニバースごとに処理
    -   取得期間は最長 20 年(20AY)。長いので、こまめに区切って取る。

    #### 注意！

    -   関数を埋め込んだら、Excel を Factset 端末で開き、関数部分のセルを F2 で開く操作を行ってから、Factset のデータダウンロードを行う。
        -   ➡ そうしないと関数が動かない。
    """)
    return


@app.cell
def _(FACTSET_ROOT_DIR, display, factset_utils):
    # ユニバース一括
    universe_code_list = list(FACTSET_ROOT_DIR.glob('Index_Constituents/MSAWIF*_Index_Constituents_with_Factset_code.parquet'))
    universe_code_list = [s.name.replace('_Index_Constituents_with_Factset_code.parquet', '') for s in universe_code_list]
    display(universe_code_list)
    for _universe_code in universe_code_list:
        factset_utils.implement_factset_formulas(universe_code=_universe_code, year_range='20AY')
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## （Factset からダウンロード後）Formatting downloaded data

    -   落とした財務データの Excel ファイルからデータを収集
    -   Excel ファイル ➡D_Financials●●*{year_range}.xlsx | D_Price*{year_range}.xlsx
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 20AY データの処理（初めて長期データをダウンロードした場合）

    -   5 分くらいかかる
    """)
    return


@app.cell
def _(FACTSET_FINANCIALS_DIR, factset_utils):
    _universe_code = 'MSXJPN_AD'
    _year_range = '20AY'
    _universe_folder = FACTSET_FINANCIALS_DIR / _universe_code
    _file_list = list(_universe_folder.glob(f'D_Financials*_{_year_range}.xlsx')) + list(_universe_folder.glob(f'D_Price_{_year_range}.xlsx'))
    factset_utils.format_factset_downloaded_data(file_list=_file_list, output_folder=_universe_folder, split_save_mode=True)  # type:ignore
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1AY データの処理（データのアップデート時）
    """)
    return


@app.cell
def _(FACTSET_FINANCIALS_DIR, factset_utils):
    _universe_code = 'MSXJPN_AD'
    _year_range = '1AY'
    _universe_folder = FACTSET_FINANCIALS_DIR / _universe_code
    _file_list = list(_universe_folder.glob(f'D_Financials*_{_year_range}.xlsx')) + list(_universe_folder.glob(f'D_Price_{_year_range}.xlsx'))
    factset_utils.format_factset_downloaded_data(file_list=_file_list, output_folder=_universe_folder, split_save_mode=False)  # type: ignore
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Price data

    -   FQL(Factset)でダウンロードした daily price data をエクセルファイルから抽出->paruqet ファイルにエクスポートする
    -   インデックス構成銘柄とベンチマークそれぞれに対して実行
    -   Daily の price データは Bloomberg から取得する
    """)
    return


@app.cell
def _(BLOOMBERG_PRICE_DIR, FACTSET_ROOT_DIR, display, pd, utils):
    _universe_code = 'MSXJPN_AD'
    _df_security = pd.read_parquet(FACTSET_ROOT_DIR / f'Index_Constituents/{_universe_code}_Index_Constituents_with_Factset_code.parquet', columns=['Asset ID', 'SEDOL', 'CUSIP', 'ISIN', 'CODE_JP', 'Country'])
    display(_df_security.shape)
    _sedol_list = list(set([s + ' SEDOL' for s in _df_security['SEDOL'].tolist() if not pd.isna(s)]))
    _cusip_list = list(set([s + ' CUSIP' for s in _df_security['CUSIP'].tolist() if not pd.isna(s)]))
    _isin_list = list(set([s + ' ISIN' for s in _df_security['ISIN'].tolist() if not pd.isna(s)]))
    _code_jp_list = list(set([s + ' CODE_JP' for s in _df_security['CODE_JP'].tolist() if not pd.isna(s)]))
    bql_list_sedol = f"=BQL.LIST({','.join(_sedol_list)})"
    bql_list_cusip = f"=BQL.LIST({','.join(_cusip_list)})"
    bql_list_isin = f"=BQL.LIST({','.join(_isin_list)})"
    print(len(_sedol_list))
    print(len(_cusip_list))
    print(len(_isin_list))
    _output_excel_file = BLOOMBERG_PRICE_DIR / f'{_universe_code}/Price.xlsx'
    _output_excel_file.parent.mkdir(parents=True, exist_ok=True)
    utils.create_excel_safely(output_path=_output_excel_file, data=bql_list_sedol)
    return


@app.cell
def _(BLOOMBERG_PRICE_DIR, FACTSET_ROOT_DIR, implement_utils, pd):
    _universe_code = 'MSXJPN_AD'
    _df_security = pd.read_parquet(FACTSET_ROOT_DIR / f'Index_Constituents/{_universe_code}_Index_Constituents_with_Factset_code.parquet', columns=['Asset ID', 'SEDOL', 'CUSIP', 'ISIN', 'CODE_JP', 'Country'])
    _sedol_list = implement_utils.create_identifier_list(_df_security['SEDOL'], 'SEDOL')
    _cusip_list = implement_utils.create_identifier_list(_df_security['CUSIP'], 'CUSIP')
    _isin_list = implement_utils.create_identifier_list(_df_security['ISIN'], 'ISIN')
    _code_jp_list = implement_utils.create_identifier_list(_df_security['CODE_JP'], 'CODE_JP')
    print('=== 識別子統計 ===')
    print(f'SEDOL: {len(_sedol_list)}銘柄')
    # メイン処理
    print(f'CUSIP: {len(_cusip_list)}銘柄')
    print(f'ISIN: {len(_isin_list)}銘柄')
    print(f'CODE_JP: {len(_code_jp_list)}銘柄')
    identifier_dict = {'SEDOL': _sedol_list, 'CUSIP': _cusip_list, 'ISIN': _isin_list, 'CODE_JP': _code_jp_list}
    _output_excel_file = BLOOMBERG_PRICE_DIR / f'{_universe_code}/Price.xlsx'
    # 各識別子の統計情報を表示
    # 識別子辞書を作成
    # Excelファイルを作成
    implement_utils.create_excel_with_chunked_data(_output_excel_file, identifier_dict, chunk_size=500)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Price
    """)
    return


@app.cell
def _(BLOOMBERG_PRICE_DIR, BPM_DATA_DIR, bpm_code_map, np, pd):
    _universe_code = 'MSXJPN_AD'
    universe_name = bpm_code_map[_universe_code]
    _df = pd.read_parquet(BPM_DATA_DIR / f'{universe_name}/{universe_name}_Constituents.parquet').replace('N/A', np.nan).dropna(axis=1, how='all')
    _df['Weight (%)'] = _df['Weight (%)'].astype(float)
    all_columns = [col for col in _df.columns.tolist() if not col in ['SEDOL', 'CUSIP', 'ISIN']]
    output_excel = BLOOMBERG_PRICE_DIR / f'{_universe_code}_Price.xlsx'
    with pd.ExcelWriter(output_excel) as _f:
        for id_type in ['SEDOL', 'CUSIP', 'ISIN']:
            _df_slice = _df[all_columns + [id_type]].dropna(subset=id_type)
            _df_slice.to_excel(_f, sheet_name=id_type, index=False)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Index Constituents
    """)
    return


@app.cell
def _(MSCI_KOKUSAI_OUTPUT_DIR, display, pd, tqdm):
    _excel_file = MSCI_KOKUSAI_OUTPUT_DIR / 'D_price_Daily.xlsx'
    df_price_universe = pd.read_excel(_excel_file, sheet_name='FG_PRICE')
    df_date_universe = pd.read_excel(_excel_file, sheet_name='date')
    _dfs = []
    for _symbol in tqdm(df_price_universe.columns.tolist()):
        _data_price = df_price_universe[_symbol].values
        _data_date = df_date_universe[_symbol].values
        _df_slice = pd.DataFrame(data={'date': _data_date, 'value': _data_price}).assign(P_SYMBOL=_symbol, variable='FG_PRICE')
        _dfs.append(_df_slice)
    df_kokusai = pd.concat(_dfs, ignore_index=True).dropna(subset=['date', 'value'], how='all', ignore_index=True).reindex(columns=['date', 'P_SYMBOL', 'variable', 'value'])
    display(df_kokusai.head())
    print(df_kokusai.shape)
    df_kokusai = df_kokusai.assign(date=lambda x: pd.to_datetime(x['date'])).sort_values(['P_SYMBOL', 'date'], ignore_index=True)
    df_kokusai_1 = df_kokusai[df_kokusai['date'] <= pd.to_datetime('2009-12-31')]
    df_kokusai_2 = df_kokusai[(df_kokusai['date'] >= pd.to_datetime('2010-01-01')) & (df_kokusai['date'] <= pd.to_datetime('2014-12-31'))]
    df_kokusai_3 = df_kokusai[(df_kokusai['date'] >= pd.to_datetime('2015-01-01')) & (df_kokusai['date'] <= pd.to_datetime('2019-12-31'))]
    df_kokusai_4 = df_kokusai[df_kokusai['date'] >= pd.to_datetime('2020-01-01')]
    display(df_kokusai_1)
    display(df_kokusai_2)
    display(df_kokusai_3)
    display(df_kokusai_4)
    df_kokusai_1.to_parquet(MSCI_KOKUSAI_OUTPUT_DIR / 'MSCI_KOKUSAI_Price_1.parquet', index=False)
    df_kokusai_2.to_parquet(MSCI_KOKUSAI_OUTPUT_DIR / 'MSCI_KOKUSAI_Price_2.parquet', index=False)
    df_kokusai_3.to_parquet(MSCI_KOKUSAI_OUTPUT_DIR / 'MSCI_KOKUSAI_Price_3.parquet', index=False)
    df_kokusai_4.to_parquet(MSCI_KOKUSAI_OUTPUT_DIR / 'MSCI_KOKUSAI_Price_4.parquet', index=False)
    # export
    del (df_kokusai_1, df_kokusai_2, df_kokusai_3, df_kokusai_4, df_kokusai, _dfs, df_price_universe, df_date_universe)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Benchmark
    """)
    return


@app.cell
def _(MSCI_KOKUSAI_OUTPUT_DIR, display, pd, tqdm):
    _excel_file = MSCI_KOKUSAI_OUTPUT_DIR / 'D_Benchmark_Price.xlsx'
    df_price_benchmark = pd.read_excel(_excel_file, sheet_name='FG_PRICE')
    df_date_benchmark = pd.read_excel(_excel_file, sheet_name='date')
    _dfs = []
    for _symbol in tqdm(df_price_benchmark.columns.tolist()):
        _data_price = df_price_benchmark[_symbol].values
        _data_date = df_date_benchmark[_symbol].values
        _df_slice = pd.DataFrame(data={'date': _data_date, 'value': _data_price}).assign(P_SYMBOL=_symbol, variable='FG_PRICE')
        _dfs.append(_df_slice)
    df_benchmark = pd.concat(_dfs, ignore_index=True).dropna(subset=['date', 'value'], how='all', ignore_index=True).reindex(columns=['date', 'P_SYMBOL', 'variable', 'value'])
    df_benchmark.replace({'991200': 'MSCI Kokusai Index (World ex Japan)', 'SP50': 'S&P 500'}, inplace=True)
    df_benchmark = df_benchmark.assign(date=lambda x: pd.to_datetime(x['date'])).sort_values(['P_SYMBOL', 'date'], ignore_index=True)
    display(df_benchmark)
    print(df_benchmark.shape)
    df_benchmark.to_parquet(MSCI_KOKUSAI_OUTPUT_DIR / 'Benchmark_Price.parquet', index=False)
    del (df_benchmark, _dfs, df_price_benchmark, df_date_benchmark)
    return


@app.cell
def _():
    import marimo as mo
    return (mo,)


if __name__ == "__main__":
    app.run()
