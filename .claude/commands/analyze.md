---
description: 多次元コード分析（分析レポート出力）
---

# /analyze - 多次元コード分析

> **役割の明確化**: このコマンドは**分析レポート出力**に特化しています。
>
> - 分析結果に基づく改善実装 → `/improve`
> - 問題の自動修正 → `/ensure-quality`
> - セキュリティスコアリング → `/scan --security`

**目的**: コード、アーキテクチャ、セキュリティ、パフォーマンスの包括的な分析

## 実行方法

このコマンドは **code-analyzer サブエージェント** を使用して実行されます。

### サブエージェント呼び出し

```yaml
subagent_type: "code-analyzer"
description: "Multi-dimensional code analysis"
prompt: |
  コード分析を実行してください。

  ## 対象
  [指定されたパス、またはプロジェクト全体]

  ## 分析モード
  [--code, --arch, --security, --perf など指定されたオプション]

  ## 分析深度
  [--think, --think-hard, --ultrathink]

  ## 出力
  - 各観点のスコア
  - 発見事項（重大度別）
  - 具体的なメトリクス
  - 改善ロードマップ

  ## レポート出力
  分析完了後、以下のパスにYAML形式でレポートを保存してください：
  - 出力先: src/<library_name>/docs/analysis-report-YYYYMMDD.yaml
  - --output オプションが指定された場合はそのパスに出力
```

## 使用方法

```bash
/analyze [オプション] [対象]
```

## オプション

### --code

コード品質の分析を実行：

- 命名規則の一貫性
- 関数・クラスの複雑性（サイクロマティック複雑性）
- DRY原則の遵守状況
- 型ヒントのカバレッジ
- docstringの品質

### --arch

アーキテクチャの分析：

- レイヤー間の結合度
- 依存関係の方向性
- 設計パターンの適用状況
- モジュール間の責務分離
- スケーラビリティの評価

### --security

セキュリティ監査：

- OWASP Top 10の脆弱性チェック
- 認証・認可の実装確認
- 入力検証とサニタイゼーション
- 暗号化とデータ保護
- エラーハンドリングの安全性

### --perf

パフォーマンス分析：

- アルゴリズムの時間計算量
- メモリ使用効率
- I/O操作の最適化機会
- データベースクエリの効率性
- キャッシング機会の特定

### --output <path>

レポートの出力先を指定：

- デフォルト: `src/<library_name>/docs/analysis-report-YYYYMMDD.yaml`
- 例: `--output reports/my-analysis.yaml`

### 分析深度フラグ

- `--think`: 標準的な分析（デフォルト）
- `--think-hard`: 深い分析
- `--ultrathink`: 最も詳細な分析

## 実行例

### 基本的な使用

```bash
# カレントディレクトリのコード品質分析
/analyze --code

# 特定ファイルのセキュリティ監査
/analyze --security src/auth/

# 全体的なアーキテクチャ分析
/analyze --arch --think-hard
```

### 複合分析

```bash
# コードとセキュリティの包括的分析
/analyze --code --security --think-hard

# パフォーマンスボトルネックの特定
/analyze --perf --ultrathink src/core/
```

### 出力先を指定

```bash
# 特定のパスにレポートを出力
/analyze --code --output src/my_lib/docs/analysis-report-20240115.yaml

# レポートディレクトリに出力
/analyze --arch --output reports/architecture-analysis.yaml
```

## 出力形式

分析結果は以下のYAML形式でファイルに保存されます：

### 出力先

```
src/<library_name>/docs/analysis-report-YYYYMMDD.yaml
```

- `<library_name>`: 分析対象のライブラリ名（自動検出）
- `YYYYMMDD`: 分析実行日（例: 20240115）

### レポート構造

```yaml
# 分析レポート
# 生成日時: YYYY-MM-DD HH:MM:SS
# 生成コマンド: /analyze [オプション]

metadata:
  generated_at: "YYYY-MM-DD HH:MM:SS"
  target: "<分析対象パス>"
  analysis_modes:
    - code
    - arch
    - perf
  depth: "think-hard"

summary:
  total_files: 0
  total_lines: 0
  total_functions: 0
  total_classes: 0

scores:
  code_quality: 0  # 0-100
  architecture: 0  # 0-100
  performance: 0   # 0-100
  overall: 0       # 0-100

code_quality:
  complexity:
    average: 0.0
    max: 0
    max_function: "<関数名>"
    high_complexity_functions:
      - name: "<関数名>"
        file: "<ファイルパス>"
        line: 0
        complexity: 0

  duplication:
    rate: "0%"
    locations:
      - files:
          - "<ファイル1>"
          - "<ファイル2>"
        lines: "10-20"

  type_hint_coverage: "0%"
  docstring_coverage: "0%"

architecture:
  layer_structure: "<評価>"
  circular_dependencies: false
  problematic_dependencies:
    - source: "<依存元>"
      target: "<依存先>"
      reason: "<理由>"

performance:
  quadratic_or_worse_algorithms: 0
  memory_inefficient_patterns: 0
  n_plus_one_queries: 0
  caching_opportunities: 0

findings:
  critical:
    - id: "ANA-001"
      category: "<コード品質/アーキテクチャ/パフォーマンス>"
      location: "<ファイル>:<行番号>"
      description: "<問題の説明>"
      evidence: "<メトリクス値や具体例>"
      recommendation: "<改善案>"

  high: []
  medium: []
  low: []

improvement_roadmap:
  short_term:  # 1週間以内
    - priority: 1
      task: "<タスク内容>"
      related_findings:
        - "ANA-001"

  mid_term:  # 1ヶ月以内
    - priority: 1
      task: "<タスク内容>"

  long_term:
    - priority: 1
      task: "<タスク内容>"
```

## 既存ツールとの連携

`/analyze`は以下のツールと連携して動作します：

- `pyright`: 型チェックの結果を統合
- `ruff`: リンター出力を分析に含める
- `bandit`: セキュリティ問題の検出
- `pytest`: テストカバレッジの確認

## 分析深度の違い

### --think（標準）

- 主要なメトリクスの収集
- 明らかな問題の検出
- 基本的な改善提案

### --think-hard（深い分析）

- 詳細なメトリクス収集
- パターンベースの問題検出
- 具体的なリファクタリング案

### --ultrathink（最も詳細）

- 全ファイルの詳細分析
- 依存関係の完全なグラフ化
- 段階的な改善計画の作成
- 優先順位付きのアクションアイテム

## 注意事項

- 大規模なコードベースでは`--ultrathink`の使用に時間がかかる場合があります
- セキュリティ分析は補完的なツールとして使用し、専門的なセキュリティ監査の代替にはなりません
- パフォーマンス分析は静的解析に基づくため、実際のベンチマークと併用してください
- レポートファイルは上書きされるため、履歴を残す場合は日付付きファイル名を使用してください
