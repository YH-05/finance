---
description: エビデンスベースの改善実装
---

# /improve - エビデンスベースの改善

**役割の明確化**: このコマンドは**エビデンスベースの改善実装**に特化しています。

- 先に分析を行いたい場合 → `/analyze`
- 品質チェックの自動修正 → `/ensure-quality`
- 検証・スコアリング → `/scan --validate`

**目的**: 測定可能な証拠に基づいたコード改善の提案と実装

## 実行方法

このコマンドは **improvement-implementer サブエージェント** を使用して実行されます。

### サブエージェント呼び出し

```yaml
subagent_type: "improvement-implementer"
description: "Evidence-based code improvement"
prompt: |
  エビデンスベースの改善を実装してください。

  ## 対象
  [指定されたパス、またはプロジェクト全体]

  ## 改善モード
  [--quality, --perf, --arch など指定されたオプション]

  ## 実行モード
  [--safe, --iterate, --refactor など]

  ## 出力
  - 改善前メトリクス
  - 実施した改善内容
  - 改善後メトリクス
  - 効果の検証結果

  ## レポート出力
  改善完了後、以下のパスにYAML形式でレポートを保存してください：
  - 出力先: src/<library_name>/docs/improve-report-YYYYMMDD.yaml
  - --output オプションが指定された場合はそのパスに出力
```

## 使用方法

```bash
/improve [オプション] [対象]
```

## オプション

### --quality

コード品質の改善：

- 可読性の向上（命名、構造）
- 保守性の改善（モジュール化、依存関係）
- DRY 原則の適用
- 複雑性の削減
- エラーハンドリングの改善

### --perf

パフォーマンスの最適化：

- アルゴリズムの効率化
- メモリ使用量の削減
- I/O 操作の最適化
- キャッシング戦略の実装
- 並列処理の活用

### --arch

アーキテクチャの改善：

- 設計パターンの適用
- 依存性注入の実装
- レイヤー分離の強化
- モジュール境界の明確化
- スケーラビリティの向上

### 実行モードフラグ

- `--refactor`: 動作を変えずに内部構造を改善
- `--iterate`: 指定された閾値まで繰り返し改善
- `--safe`: 保守的な改善のみ実行
- `--metrics`: 改善前後のメトリクスを表示

### 品質閾値

- `--threshold low`: 基本的な改善
- `--threshold medium`: 標準的な改善（デフォルト）
- `--threshold high`: 高品質を目指す改善
- `--threshold perfect`: 可能な限り最高品質

### --output <path>

レポートの出力先を指定：

- デフォルト: `src/<library_name>/docs/improve-report-YYYYMMDD.yaml`
- 例: `--output reports/my-improvement.yaml`

## 実行例

### 基本的な使用

```bash
# コード品質の改善
/improve --quality src/

# パフォーマンスの反復改善
/improve --perf --iterate --threshold high

# 安全なリファクタリング
/improve --arch --refactor --safe
```

### 高度な使用

```bash
# メトリクス付き品質改善
/improve --quality --metrics --threshold perfect

# 複合的な改善
/improve --quality --perf --arch --iterate
```

### 出力先を指定

```bash
# 特定のパスにレポートを出力
/improve --quality --output src/my_lib/docs/improve-report-20240115.yaml

# レポートディレクトリに出力
/improve --perf --output reports/performance-improvement.yaml
```

## 改善プロセス

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. 現状分析                                                │
│     ├── 現在のメトリクスを測定                              │
│     ├── 改善機会を特定                                      │
│     └── 優先順位を設定                                      │
│                                                             │
│  2. 計画立案                                                │
│     ├── 安全な改善パスを設計                                │
│     ├── 既存機能の保持を確認                                │
│     └── 段階的な変更計画                                    │
│                                                             │
│  3. 実装                                                    │
│     ├── 小さな原子的変更                                    │
│     ├── 継続的なテスト実行                                  │
│     └── quality-checker(--validate-only) で検証             │
│                                                             │
│  4. 検証                                                    │
│     ├── 動作の保持を確認                                    │
│     ├── メトリクスの改善を測定                              │
│     └── 回帰テストの実行                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 出力形式

改善結果は以下のYAML形式でファイルに保存されます：

### 出力先

```
src/<library_name>/docs/improve-report-YYYYMMDD.yaml
```

- `<library_name>`: 改善対象のライブラリ名（自動検出）
- `YYYYMMDD`: 実行日（例: 20240115）

### レポート構造

```yaml
# 改善実装レポート
# 生成日時: YYYY-MM-DD HH:MM:SS
# 生成コマンド: /improve [オプション]

metadata:
  generated_at: "YYYY-MM-DD HH:MM:SS"
  target: "<改善対象パス>"
  improvement_modes:
    - quality
    - perf
  execution_mode: "safe"
  threshold: "medium"

before_metrics:
  code_quality_score: 0  # 0-100
  cyclomatic_complexity:
    average: 0.0
    max: 0
  performance_score: 0  # 0-100
  test_coverage: "0%"

improvements:
  - id: "IMP-001"
    type: "<改善の種類>"
    location: "<ファイル>:<行番号>"
    change: "<具体的な変更内容>"
    rationale: "<測定データに基づく理由>"
    expected_effect: "<期待される改善効果>"

after_metrics:
  code_quality_score: 0  # 0-100
  code_quality_improvement: "+0%"
  cyclomatic_complexity:
    average: 0.0
    max: 0
  complexity_improvement: "-0%"
  performance_score: 0  # 0-100
  performance_improvement: "+0%"
  test_coverage: "0%"

verification:
  quality_checker: "PASS"  # PASS/FAIL
  all_tests_passed: true
  regression_detected: false

summary:
  total_improvements: 0
  files_modified: 0
  lines_changed: 0
  overall_improvement: "+0%"
```

## 改善パターン

### コード品質

- 長い関数の分割
- ネストの深さ削減
- 明確な変数名への変更
- 型ヒントの追加
- エラーメッセージの改善

### パフォーマンス

- リスト内包表記の活用
- 不要なループの削除
- キャッシュの実装
- 遅延評価の導入
- バッチ処理の実装

### アーキテクチャ

- ファサードパターンの適用
- 依存性の逆転
- インターフェースの抽出
- モジュールの再編成
- 横断的関心事の分離

## 既存ツールとの連携

改善プロセスは以下のツールを活用：

- `make format`: コードフォーマットの統一
- `make lint`: リント違反の自動修正
- `make typecheck`: 型の一貫性確認
- `make test`: 改善後の動作確認
- `make benchmark`: パフォーマンス改善の測定

## 注意事項

- `--iterate`モードは処理時間が長くなる可能性があります
- 大規模な変更前は必ずバックアップまたは git のコミットを作成してください
- パフォーマンス改善は必ずベンチマークで検証してください
- テストカバレッジが低い場合は、先にテストを追加することを推奨します
