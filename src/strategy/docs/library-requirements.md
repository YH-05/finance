# ライブラリ要求定義書 (Library Requirements Document)

## ライブラリ概要

### 名称

**strategy** - ポートフォリオ管理・分析ライブラリ

### ライブラリの目的

-   **ポートフォリオ分析**: 個別株・ETF・投資信託を組み合わせたポートフォリオの構成分析と可視化
-   **リスク管理**: 包括的なリスク指標（ボラティリティ、シャープレシオ、VaR 等）の計算と監視
-   **リバランス支援**: 配分ドリフト検出、コスト計算、タイミング分析によるリバランス判断支援

### 解決する課題

個人投資家やコンテンツ作成者は、ポートフォリオの構成分析やリスク評価を行う際、
複数のツールやスプレッドシートを使い分ける必要があり、一貫した分析が困難である。
本ライブラリは、ポートフォリオ分析に必要な機能を統合的に提供し、
分析結果を複数の形式（DataFrame、JSON、チャート、テキスト）で出力することで、
note 記事作成、投資判断、教育目的など多様なユースケースに対応する。

### 提供する価値

-   **統合的な分析環境**: ポートフォリオ分析に必要な機能をワンストップで提供
-   **多様な出力形式**: pandas DataFrame、JSON、Plotly チャート、マークダウンテキスト、marimo 連携
-   **リスクの可視化**: 複数のリスク指標を計算し、直感的に理解できる形で可視化
-   **疎結合設計**: market_analysis パッケージとインターフェース経由で連携し、独立性を維持

## 想定利用者

### プライマリー利用者: 金融コンテンツクリエイター

-   note.com で金融・投資関連の記事を執筆
-   Python の基本的な使用経験がある
-   ポートフォリオ分析結果を記事の素材として活用したい
-   分析結果をチャートやテキストで簡単に取得したい
-   典型的なシナリオ: 「S&P500 ETF と日本株のポートフォリオを分析し、記事用のチャートを生成する」

### セカンダリー利用者: 個人投資家

-   自身のポートフォリオを定期的に分析・管理
-   リスク指標を理解し、投資判断に活用
-   リバランスのタイミングを判断したい
-   典型的なシナリオ: 「保有ポートフォリオのリスク指標を計算し、リバランスが必要か判断する」

### ターシャリー利用者: 投資学習者

-   投資戦略やリスク管理を学習中
-   シミュレーションを通じて理解を深めたい
-   典型的なシナリオ: 「異なる配分のポートフォリオを比較し、リスクリターン特性を学ぶ」

## 成功指標

### 品質指標

-   テストカバレッジ: 80%以上
-   型カバレッジ: 100%（py.typed 対応、pyright エラーなし）
-   ドキュメントカバレッジ: 全公開 API に NumPy 形式の docstring

### パフォーマンス指標

-   リスク指標計算: 5 年分のデータ（約 1250 営業日）に対して 1 秒以内
-   チャート生成: 1 ポートフォリオあたり 500ms 以内

### 利用者体験指標

-   新規利用者が README のサンプルコードを実行するまで: 5 分以内
-   基本的なポートフォリオ分析の記述: 10 行以内のコード

## 機能要件

### コア機能(MVI)

#### 1. DataProvider インターフェース

**使用例**:
クオンツアナリストとして、任意のデータソースを統一的に扱うために、抽象化されたデータ取得インターフェースが欲しい

**受け入れ条件**:

-   [ ] DataProvider プロトコルが定義されている
-   [ ] 価格データ（OHLCV）の取得メソッドが定義されている
-   [ ] ティッカー情報（セクター、資産クラス等）の取得メソッドが定義されている
-   [ ] 複数銘柄の一括取得が可能
-   [ ] 日付範囲を指定した取得が可能
-   [ ] MarketAnalysisProvider（デフォルト）: market_analysis パッケージ経由のアダプターが実装されている
    -   yfinance/FRED データをキャッシュ活用で取得
    -   market_analysis の YFinanceFetcher/FREDFetcher を内部で使用
-   [ ] カスタムプロバイダー（テスト用モック等）を作成できるインターフェースを提供する
-   [ ] 将来的な拡張ポイント（Factset, Bloomberg 等）のドキュメントが整備されている

**優先度**: P0(必須)

#### 2. ポートフォリオ定義

**使用例**:
金融コンテンツクリエイターとして、記事で分析するポートフォリオを簡単に定義するために、
ティッカーと比率のリストでポートフォリオを作成できる機能が欲しい

**受け入れ条件**:

-   [ ] ティッカーシンボルと比率のリストからポートフォリオを作成できる
-   [ ] 比率の合計が 1.0（100%）でない場合、警告または正規化オプションを提供する
-   [ ] 無効なティッカーシンボルに対して明確なエラーメッセージを返す
-   [ ] ポートフォリオの構成を確認するための repr/str メソッドを提供する
-   [ ] データプロバイダーをコンストラクタまたは set_provider() で設定できる

**優先度**: P0(必須)

#### 3. 資産配分分析

**使用例**:
金融コンテンツクリエイターとして、記事用の視覚的な素材を作成するために、
ポートフォリオの資産配分を円グラフや棒グラフで可視化したい

**受け入れ条件**:

-   [ ] 資産配分を円グラフ（Plotly）で出力できる
-   [ ] 資産配分を棒グラフ（Plotly）で出力できる
-   [ ] セクター別・資産クラス別の構成分析ができる
-   [ ] 配分データを DataFrame または JSON で取得できる

**優先度**: P0(必須)

#### 4. リスク指標計算

**使用例**:
個人投資家として、投資判断の根拠を得るために、
ポートフォリオの各種リスク指標を計算し、数値で確認したい

**受け入れ条件**:

-   [ ] ボラティリティ（年率標準偏差）を計算できる
-   [ ] シャープレシオを計算できる（リスクフリーレートは設定可能）
-   [ ] 最大ドローダウン（MDD）を計算できる
-   [ ] VaR（95%、99%信頼水準）を計算できる
-   [ ] ソルティノレシオを計算できる
-   [ ] トレイナーレシオを計算できる（ベンチマーク指定）
-   [ ] 情報レシオを計算できる（ベンチマーク指定）
-   [ ] ベータ値を計算できる（ベンチマーク指定）
-   [ ] すべての指標を一括で取得する summary メソッドを提供する

**優先度**: P0(必須)

#### 5. 期間設定

**使用例**:
投資学習者として、異なる期間でのパフォーマンスを比較するために、
プリセット期間とカスタム期間の両方で分析したい

**受け入れ条件**:

-   [ ] プリセット期間（1 年、3 年、5 年）を選択できる
-   [ ] カスタム期間（開始日・終了日）を指定できる
-   [ ] 期間が不足している場合、利用可能な最大期間で計算し警告を出す

**優先度**: P0(必須)

#### 6. データ出力

**使用例**:
金融コンテンツクリエイターとして、分析結果を様々な形式で活用するために、
DataFrame、JSON、チャート、テキストの複数形式で出力したい

**受け入れ条件**:

-   [ ] 分析結果を pandas DataFrame で取得できる
-   [ ] 分析結果を JSON/辞書形式で取得できる（AI エージェント向け）
-   [ ] 分析結果を Plotly チャートで取得できる
-   [ ] 分析結果をマークダウン形式のレポートテキストで取得できる
-   [ ] marimo ノートブックで直接表示可能な形式で出力できる

**優先度**: P0(必須)

#### 7. 配分ドリフト検出

**使用例**:
個人投資家として、リバランスの必要性を判断するために、
目標配分からの乖離を検出し可視化したい

**受け入れ条件**:

-   [ ] 現在の配分と目標配分の差異を計算できる
-   [ ] 乖離を棒グラフで可視化できる
-   [ ] 閾値を設定し、リバランス推奨の判定ができる

**優先度**: P0(必須)

#### 8. リバランスコスト計算

**使用例**:
個人投資家として、リバランスの費用対効果を判断するために、
取引コストと税金影響の概算を知りたい

**受け入れ条件**:

-   [ ] リバランスに必要な取引コストを概算できる（手数料率は設定可能）
-   [ ] 売却時の税金影響を概算できる（税率は設定可能）
-   [ ] 総コストとリバランス後の期待改善効果を比較表示できる

**優先度**: P1(重要)

#### 9. リバランスタイミング分析

**使用例**:
個人投資家として、適切なリバランス頻度を決めるために、
過去のデータから最適なリバランスタイミングを分析したい

**受け入れ条件**:

-   [ ] 定期リバランス（月次、四半期、年次）のシミュレーションができる
-   [ ] 閾値ベースリバランスのシミュレーションができる
-   [ ] 各戦略のパフォーマンス比較をチャートで表示できる

**優先度**: P1(重要)

### API インターフェース

```python
from strategy import Portfolio, RiskMetrics, Rebalancer
from strategy.providers import MarketAnalysisProvider

# データプロバイダーの設定
# デフォルト: market_analysis パッケージ経由（yfinance/FRED、キャッシュ活用）
provider = MarketAnalysisProvider()

# カスタムプロバイダー（テスト用モック等）
# from strategy.providers import DataProvider
# class MockProvider(DataProvider):
#     def get_prices(self, tickers, start, end): ...
#     def get_ticker_info(self, ticker): ...

# ポートフォリオの定義（プロバイダー指定）
portfolio = Portfolio(
    holdings=[
        ("VOO", 0.4),    # S&P500 ETF
        ("VEA", 0.2),    # 先進国株ETF
        ("VWO", 0.1),    # 新興国株ETF
        ("BND", 0.2),    # 米国債券ETF
        ("GLD", 0.1),    # 金ETF
    ],
    provider=provider,  # データプロバイダーを注入
)

# プロバイダーを後から設定することも可能
portfolio = Portfolio([...])
portfolio.set_provider(provider)

# 期間設定（プリセット）
portfolio.set_period("3y")

# 期間設定（カスタム）
portfolio.set_period(start="2020-01-01", end="2024-12-31")

# 資産配分の可視化
portfolio.plot_allocation()  # Plotly 円グラフ
portfolio.allocation_df      # DataFrame

# リスク指標の計算
metrics = portfolio.risk_metrics()
print(metrics.volatility)     # 年率ボラティリティ
print(metrics.sharpe_ratio)   # シャープレシオ
print(metrics.max_drawdown)   # 最大ドローダウン
print(metrics.var_95)         # 95% VaR
print(metrics.summary())      # 全指標のサマリー

# JSON出力（AIエージェント向け）
metrics.to_dict()

# マークダウンレポート
metrics.to_markdown()

# リバランス分析
rebalancer = Rebalancer(portfolio)
drift = rebalancer.detect_drift(target_weights={...})
cost = rebalancer.estimate_cost(commission_rate=0.001)
```

#### DataProvider プロトコル

```python
from typing import Protocol
import pandas as pd

class DataProvider(Protocol):
    """データ取得の抽象インターフェース（Protocol）"""

    def get_prices(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """指定期間の価格データ（OHLCV）を取得

        Parameters
        ----------
        tickers : list[str]
            取得するティッカーシンボルのリスト
        start : str
            開始日（YYYY-MM-DD形式）
        end : str
            終了日（YYYY-MM-DD形式）

        Returns
        -------
        pd.DataFrame
            MultiIndex DataFrame（columns: ticker, rows: date）
            各ティッカーに対して Open, High, Low, Close, Volume を含む
        """
        ...

    def get_ticker_info(self, ticker: str) -> dict:
        """ティッカーの情報（セクター、資産クラス等）を取得

        Parameters
        ----------
        ticker : str
            ティッカーシンボル

        Returns
        -------
        dict
            ティッカー情報を含む辞書
            - sector: セクター名
            - industry: 業種
            - asset_class: 資産クラス（equity, bond, commodity, etc.）
            - name: 銘柄名
        """
        ...
```

```python
# MarketAnalysisProvider の実装例
from strategy.providers import MarketAnalysisProvider

provider = MarketAnalysisProvider()
prices = provider.get_prices(
    tickers=["VOO", "BND", "GLD"],
    start="2020-01-01",
    end="2024-12-31",
)
info = provider.get_ticker_info("VOO")
print(info)
# {'sector': 'Financial Services', 'industry': 'Exchange Traded Fund',
#  'asset_class': 'equity', 'name': 'Vanguard S&P 500 ETF'}
```

#### 将来の拡張: 商用データプロバイダー

```python
# 将来的な Factset/Bloomberg 対応の例（P2）
# from strategy.providers import FactsetProvider, BloombergProvider
#
# # Factset API 経由
# provider = FactsetProvider(api_key="...")
#
# # Bloomberg API 経由
# provider = BloombergProvider(connection="...")
#
# # 同じインターフェースで利用可能
# portfolio = Portfolio(holdings=[...], provider=provider)
```

### 将来的な機能(Post-MVI)

#### トレーディング戦略基盤

戦略インターフェースとシグナル生成機能の提供

**優先度**: P2(できれば)

#### バックテストエンジン

過去データでの戦略パフォーマンス検証

**優先度**: P2(できれば)

#### 最適化アルゴリズム

平均分散最適化、リスクパリティ、Black-Litterman 等の実装

**優先度**: P2(できれば)

#### 商用データプロバイダー

Factset、Bloomberg、Refinitiv 等の商用データソースへの対応。
DataProvider プロトコルに準拠したアダプターを実装。

**優先度**: P2(できれば)

## 非機能要件

### パフォーマンス

-   リスク指標計算: 5 年分データ（約 1250 営業日）に対して 1 秒以内
-   チャート生成: 1 ポートフォリオあたり 500ms 以内
-   メモリ使用量: 10 銘柄・5 年分データで 100MB 以内

### 互換性

-   Python 3.12+ 対応
-   型チェッカー（pyright）でエラーなし
-   主要 OS（Linux, macOS, Windows）での動作

### 信頼性

-   全公開 API のテストカバレッジ: 80%以上
-   エラー発生時の明確なメッセージ（原因と対処法を含む）
-   外部 API エラー時の適切なフォールバック

### テスト要件

-   TDD（Red-Green-Refactor）で開発
-   ユニットテスト: 全リスク指標計算のテスト
-   プロパティテスト: Hypothesis による境界値テスト
-   統合テスト: market_analysis パッケージとの連携テスト

### 依存関係

-   market_analysis パッケージ（DataProvider インターフェース経由）
-   pandas, numpy（データ処理）
-   plotly（可視化）
-   scipy（統計計算）

## スコープ外

明示的にスコープ外とする項目:

-   リアルタイムデータの取得と監視
-   自動売買・注文執行機能
-   税務申告用の詳細なレポート生成
-   暗号資産のサポート（将来的には検討）
-   バックテストエンジン（P2 として将来実装）
-   最適化アルゴリズム（P2 として将来実装）

---

> このドキュメントは `/new-project @src/strategy/docs/project.md` で作成されました
