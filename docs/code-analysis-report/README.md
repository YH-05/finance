# Code Analysis Report

`/analyze` コマンドによって生成されるコード分析レポートを格納するディレクトリです。

## ディレクトリ構成

```
docs/code-analysis-report/
├── README.md                                    # このファイル
├── TEMPLATE.yaml                                # レポートテンプレート
└── analysis-report-YYYYMMDD-<target>.yaml       # 分析レポート
```

## ファイル命名規則

レポートファイルは以下の命名規則に従います：

```
analysis-report-{日付}-{対象}.yaml
```

| 要素 | 説明 | 例 |
|------|------|-----|
| 日付 | 分析実行日 (YYYYMMDD) | 20260118 |
| 対象 | 分析対象のライブラリ名またはファイル名 | market_analysis, rss, full |

### 例

- `analysis-report-20260118-market_analysis.yaml` - market_analysis パッケージの分析
- `analysis-report-20260118-rss.yaml` - rss パッケージの分析
- `analysis-report-20260118-full.yaml` - プロジェクト全体の分析
- `analysis-report-20260118-analysis_py.yaml` - 特定ファイルの分析

## レポート生成方法

```bash
# 特定パッケージの全観点分析
/analyze --all @src/market_analysis/

# コード品質のみ分析
/analyze --code @src/rss/

# プロジェクト全体の詳細分析
/analyze --all --think-hard

# 特定ファイルの分析
/analyze --all @src/market_analysis/api/analysis.py
```

## レポート構造

各レポートには以下のセクションが含まれます：

1. **metadata** - 生成情報、対象、分析モード
2. **summary** - ファイル数、行数、関数数などの基本統計
3. **scores** - 各観点のスコア (0-100)
4. **code_quality** - 複雑度、重複、カバレッジ
5. **architecture** - 責務分離、依存関係、設計パターン
6. **security** - OWASP観点のセキュリティ問題
7. **performance** - アルゴリズム複雑度、I/O、メモリ
8. **findings** - 重大度別の発見事項
9. **improvement_roadmap** - 短期/中期/長期の改善計画
10. **summary_evaluation** - 総合評価

## テンプレート

新しいレポートを作成する際は `TEMPLATE.yaml` を参照してください。
各フィールドの説明とフォーマットが記載されています。

## 関連コマンド

| コマンド | 説明 |
|----------|------|
| `/analyze` | コード分析レポート生成 |
| `/improve` | 分析結果に基づく改善実装 |
| `/ensure-quality` | 品質問題の自動修正 |
| `/scan` | セキュリティスキャン |
