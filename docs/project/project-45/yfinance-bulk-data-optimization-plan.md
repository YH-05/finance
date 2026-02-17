# yfinance一括データ取得への修正プラン

## 概要

yfinanceから複数ティッカーのデータを取得する際、forループによる個別取得から`yf.download`の一括取得に変更する。

## 修正対象ファイル

| ファイル | 関数 | 現状 |
|----------|------|------|
| `src/market_analysis/analysis/returns.py` | `_fetch_and_calculate_returns` | forループで個別`yf.download` |
| `src/market_analysis/analysis/sector.py` | `_build_contributors` + `_fetch_stock_return` | forループで個別`yf.download` |

---

## 修正1: returns.py

### 対象関数
`_fetch_and_calculate_returns`（416-505行目）

### 現状のコード構造
```python
for ticker in tickers:
    df = yf.download(ticker, period="6y", progress=False)
    # 各ティッカーの処理...
```

### 修正後の構造
```python
def _fetch_and_calculate_returns(
    tickers: list[str],
    category: str,
) -> list[dict[str, Any]]:
    # 1. 一括ダウンロード
    df = yf.download(tickers, period="6y", progress=False)

    if df is None or df.empty:
        return []

    results: list[dict[str, Any]] = []

    # 2. 各ティッカーのデータを処理
    for ticker in tickers:
        try:
            # MultiIndexからティッカーのClose価格を抽出
            if isinstance(df.columns, pd.MultiIndex):
                if ticker in df["Close"].columns:
                    prices = df["Close"][ticker].dropna()
                else:
                    continue
            else:
                # 単一ティッカーの場合
                prices = df["Close"].dropna()

            # リターン計算
            returns = calculate_multi_period_returns(prices)
            results.append({"ticker": ticker, **returns})
        except Exception as e:
            logger.warning("Failed to process ticker", ticker=ticker, error=str(e))

    return results
```

### 変更点
- forループ内の`yf.download`を削除
- 関数冒頭で全ティッカーを一括ダウンロード
- MultiIndex対応のデータ抽出ロジックを追加

---

## 修正2: sector.py

### 対象関数
- `_build_contributors`（551-588行目）
- `_fetch_stock_return`（591-639行目）

### 現状のコード構造
```python
def _build_contributors(companies, max_contributors=5):
    for company in companies[:max_contributors]:
        stock_return = _fetch_stock_return(symbol)  # 個別呼び出し
        ...

def _fetch_stock_return(symbol, period=5):
    df = yf.download(symbol, period="1mo", progress=False)
    ...
```

### 修正後の構造

#### オプションA: `_build_contributors`内で一括取得（推奨）

```python
def _build_contributors(
    companies: list[dict[str, Any]],
    max_contributors: int = 5,
) -> list[SectorContributor]:
    # 1. シンボルリストを作成
    symbols = [
        company.get("symbol") or company.get("ticker", "")
        for company in companies[:max_contributors]
    ]
    symbols = [s for s in symbols if s]  # 空文字を除外

    if not symbols:
        return []

    # 2. 一括ダウンロード
    df = yf.download(symbols, period="1mo", progress=False)

    # 3. 各シンボルのリターンを計算
    stock_returns: dict[str, float | None] = {}
    if df is not None and not df.empty:
        for symbol in symbols:
            try:
                if isinstance(df.columns, pd.MultiIndex):
                    if symbol in df["Close"].columns:
                        prices = df["Close"][symbol].dropna()
                    else:
                        stock_returns[symbol] = None
                        continue
                else:
                    prices = df["Close"].dropna()

                if len(prices) > 5:
                    stock_returns[symbol] = calculate_return(prices, 5)
                else:
                    stock_returns[symbol] = None
            except Exception:
                stock_returns[symbol] = None

    # 4. SectorContributorオブジェクトを構築
    contributors: list[SectorContributor] = []
    for company in companies[:max_contributors]:
        symbol = company.get("symbol") or company.get("ticker", "")
        if not symbol:
            continue

        contributor = SectorContributor(
            ticker=str(symbol),
            name=str(company.get("name", "")),
            return_1w=stock_returns.get(symbol) or 0.0,
            weight=float(company.get("weight", 0.0)),
        )
        contributors.append(contributor)

    return contributors
```

#### `_fetch_stock_return`の扱い
- 一括取得ロジックを`_build_contributors`に統合後、`_fetch_stock_return`は削除または単一銘柄用のユーティリティとして残す

---

## 実装手順

1. **returns.py の修正**
   - `_fetch_and_calculate_returns`関数を一括取得に変更
   - エラーハンドリングを維持

2. **sector.py の修正**
   - `_build_contributors`関数を一括取得に変更
   - `_fetch_stock_return`関数は削除（または内部ヘルパーとして整理）

3. **テスト実行**
   - `make test` で既存テストがパスすることを確認
   - `make check-all` で品質チェック

---

## 検証方法

```bash
# 1. 型チェック・リント
make check-all

# 2. 関連テスト実行
uv run pytest tests/market_analysis/unit/analysis/ -v

# 3. 動作確認（手動）
uv run python -c "
from market_analysis.analysis.returns import generate_returns_report
report = generate_returns_report()
print(f'indices: {len(report[\"indices\"])} items')
print(f'mag7: {len(report[\"mag7\"])} items')
"

uv run python -c "
from market_analysis.analysis.sector import analyze_sector_performance
result = analyze_sector_performance(n_sectors=2)
print(f'top: {len(result.top_sectors)} sectors')
print(f'bottom: {len(result.bottom_sectors)} sectors')
"
```

---

## 期待される効果

| 指標 | 修正前 | 修正後 |
|------|--------|--------|
| returns.py API呼び出し回数 | 最大30回（4カテゴリ×7-11ティッカー） | 4回（カテゴリごとに1回） |
| sector.py API呼び出し回数 | 最大30回（6セクター×5銘柄） | 6回（セクターごとに1回） |
| 実行時間 | 数分 | 大幅短縮（推定70-80%削減） |

---

## リスクと対策

| リスク | 対策 |
|--------|------|
| 一括取得時のメモリ使用量増加 | 6年分データでも問題ない範囲（検証済み） |
| 一部ティッカー失敗時の影響 | 個別ティッカーのエラーハンドリングを維持 |
| yfinanceのMultiIndex仕様変更 | 型チェックでMultiIndex判定を明示的に実施 |
