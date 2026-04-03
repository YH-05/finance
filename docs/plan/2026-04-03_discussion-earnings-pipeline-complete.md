# 議論メモ: EarningsPipeline (market.pipeline) 実装完了

**日付**: 2026-04-03
**議論ID**: disc-2026-04-03-earnings-pipeline-merge
**参加**: ユーザー + AI

## 背景・コンテキスト

Project #108 (Earnings Data Pipeline) の実装が Wave0〜Wave6 にわたって完了し、PR #3887 として main ブランチにマージされた。

## 実装サマリー

- **PR**: #3887 `feat(pipeline): Wave0-6 EarningsPipeline パッケージ実装`
- **マージ日時**: 2026-04-03T06:31:42Z
- **変更規模**: 48ファイル、+11,303行 / -192行

### パッケージ構成 (`src/market/pipeline/`)

| モジュール | 内容 |
|-----------|------|
| `constants.py` | 設定定数 |
| `errors.py` | カスタム例外クラス |
| `models.py` | データモデル（frozen dataclass） |
| `ticker_normalizer.py` | ティッカー正規化 |
| `queue.py` | CollectionQueue（優先度付きキュー） |
| `storage_nasdaq.py` | NASDAQ Earnings Calendar ストレージ |
| `storage_sec.py` | SEC Edgar ストレージ |
| `storage_yfinance.py` | YFinance ストレージ |
| `collector_nasdaq.py` | NASDAQ Earnings Calendar コレクター |
| `collector_sec.py` | SecEdgarCollector（sys.modules スワップで名前空間衝突解決） |
| `collector_yfinance.py` | YFinance コレクター |
| `pipeline.py` | オーケストレーター（3段階収集フロー） |
| `cli.py` | CLI エントリポイント |

### テスト

- **ユニットテスト**: 176件（`tests/market/pipeline/unit/` + `tests/market/unit/pipeline/`）
- **統合テスト**: 17件（`tests/market/pipeline/integration/`、`@pytest.mark.integration`）
- **CI**: Lint / TypeCheck / Unit Tests 全パス

### 技術的ハイライト

- **edgar.* 名前空間衝突**: `edgartools` の `edgar` モジュールと `market.edgar` が衝突する問題を `sys.modules` スワップで根本解決
- **smoke_test_edgar.py**: Wave4 実装前に edgartools API の実際の形状（カラム名・型・欠損パターン）を確認するスクリプトを `scripts/` に追加
- **3段階パイプライン**: NASDAQ Earnings Calendar → SEC Edgar → YFinance の順で企業の決算データを収集

## 決定事項

| ID | 内容 | ステータス |
|----|------|-----------|
| dec-2026-04-03-001 | market.pipeline パッケージ（Wave0-6）を PR #3887 として main にマージ完了 | implemented |

## 次のステップ候補

- `python -m market.pipeline --status` による動作確認（実機テスト）
- NAS・Mac Mini での定期実行（cron/launchd）設定
- Project #108 の残タスク確認（Issues #3880-#3886 は既に Done）

## 参照

- PR: https://github.com/YH-05/quants/pull/3887
- Issue #3879: [Wave0] edgartools スモークテストスクリプトの作成
- 計画書: `docs/project/project-103/project.md`
