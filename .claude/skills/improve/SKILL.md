---
name: improve
description: エビデンスベースの改善実装。測定可能な証拠に基づいたコード改善の提案と実装を行う。Use PROACTIVELY when コード品質・パフォーマンス・アーキテクチャの改善が必要な場合。
allowed-tools: Read, Bash, Task
---

# Improve

**役割の明確化**: このスキルは**エビデンスベースの改善実装**に特化しています。

- 先に分析を行いたい場合 → `analyze` スキル
- 品質チェックの自動修正 → `ensure-quality` スキル
- 検証・スコアリング → `scan` スキル

## 目的

このスキルは以下を提供します：

- **測定可能な証拠に基づいたコード改善**の提案と実装
- **改善前後のメトリクス測定**と効果検証
- **段階的な改善プロセス**の実行

## いつ使用するか

### プロアクティブ使用（自動で使用を検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討してください：

1. **コード品質の改善が必要**
   - 複雑性が高い（循環的複雑度が高い）
   - 可読性が低い
   - DRY原則違反が多い

2. **パフォーマンス問題の検出**
   - 処理時間が長い
   - メモリ使用量が多い
   - I/O操作が非効率

3. **アーキテクチャの改善機会**
   - 依存関係が複雑
   - モジュール境界が不明瞭
   - スケーラビリティの課題

### 明示的な使用（ユーザー要求）

- 「改善して」「最適化して」「リファクタして」などの直接的な要求
- Task tool で `improvement-implementer` サブエージェントを使用

## プロセス

### 1. 現状分析

改善対象のメトリクスを測定します：

```bash
# コード品質の測定
make check-all

# パフォーマンスの測定（必要に応じて）
make benchmark
```

**測定項目**:
- コード品質スコア（0-100）
- 循環的複雑度（平均・最大）
- パフォーマンススコア（0-100）
- テストカバレッジ

### 2. 計画立案

測定結果に基づき、改善計画を立案します：

**優先順位の設定**:
1. 影響度の高い改善（パフォーマンスボトルネック等）
2. リスクの低い改善（命名、構造化等）
3. アーキテクチャ改善（設計パターン適用等）

**安全性の確保**:
- 既存機能の保持を確認
- 段階的な変更計画
- 継続的なテスト実行

### 3. 実装

小さな原子的変更を繰り返し実行します：

```bash
# 改善を実装
Task(
    subagent_type="improvement-implementer",
    prompt="エビデンスベースの改善を実装"
)

# 品質チェック（検証のみ）
Task(
    subagent_type="quality-checker",
    prompt="改善後のコードを検証（--validate-only）"
)
```

**実装パターン**:
- コード品質: 長い関数の分割、ネスト削減、命名改善
- パフォーマンス: アルゴリズム効率化、キャッシング、並列化
- アーキテクチャ: 設計パターン適用、依存性逆転、モジュール再編成

### 4. 検証

改善効果を測定し、回帰がないことを確認します：

```bash
# テスト実行
make test

# メトリクス再測定
make check-all
```

**検証項目**:
- [ ] 全テストがパスする
- [ ] メトリクスが改善している
- [ ] 回帰が発生していない

## 改善モード

### --quality（コード品質の改善）

- 可読性の向上（命名、構造）
- 保守性の改善（モジュール化、依存関係）
- DRY 原則の適用
- 複雑性の削減
- エラーハンドリングの改善

### --perf（パフォーマンスの最適化）

- アルゴリズムの効率化
- メモリ使用量の削減
- I/O 操作の最適化
- キャッシング戦略の実装
- 並列処理の活用

### --arch（アーキテクチャの改善）

- 設計パターンの適用
- 依存性注入の実装
- レイヤー分離の強化
- モジュール境界の明確化
- スケーラビリティの向上

## 実行モードフラグ

| フラグ | 説明 |
|--------|------|
| `--refactor` | 動作を変えずに内部構造を改善 |
| `--iterate` | 指定された閾値まで繰り返し改善 |
| `--safe` | 保守的な改善のみ実行 |
| `--metrics` | 改善前後のメトリクスを表示 |

## 品質閾値

| 閾値 | 説明 |
|------|------|
| `--threshold low` | 基本的な改善 |
| `--threshold medium` | 標準的な改善（デフォルト） |
| `--threshold high` | 高品質を目指す改善 |
| `--threshold perfect` | 可能な限り最高品質 |

## 出力フォーマット

改善結果はYAML形式でレポートに保存されます：

### 出力先

- デフォルト: `src/<library_name>/docs/improve-report-YYYYMMDD.yaml`
- カスタム: `--output <path>` で指定

### レポート構造

```yaml
metadata:
  generated_at: "YYYY-MM-DD HH:MM:SS"
  target: "<改善対象パス>"
  improvement_modes: [quality, perf]
  execution_mode: "safe"
  threshold: "medium"

before_metrics:
  code_quality_score: 75
  cyclomatic_complexity:
    average: 5.2
    max: 15
  performance_score: 80
  test_coverage: "85%"

improvements:
  - id: "IMP-001"
    type: "コード品質改善"
    location: "src/example.py:45"
    change: "長い関数を3つに分割"
    rationale: "循環的複雑度15→5に削減"
    expected_effect: "可読性向上、保守性改善"

after_metrics:
  code_quality_score: 85
  code_quality_improvement: "+13%"
  cyclomatic_complexity:
    average: 3.8
    max: 8
  complexity_improvement: "-27%"
  performance_score: 85
  performance_improvement: "+6%"
  test_coverage: "85%"

verification:
  quality_checker: "PASS"
  all_tests_passed: true
  regression_detected: false

summary:
  total_improvements: 5
  files_modified: 3
  lines_changed: 120
  overall_improvement: "+15%"
```

## 使用例

### 例1: コード品質の改善

**状況**: 複雑な関数が多く、可読性が低い

**入力**:
```bash
Task(
    subagent_type="improvement-implementer",
    prompt="コード品質の改善を実行（--quality）"
)
```

**処理**:
1. 現状のメトリクスを測定
2. 長い関数、深いネスト、曖昧な命名を特定
3. 小さな原子的変更で改善
4. 各変更後にテスト実行
5. 改善効果を測定

**期待される出力**:
```yaml
after_metrics:
  code_quality_score: 85  # 75→85 (+13%)
  cyclomatic_complexity:
    average: 3.8  # 5.2→3.8 (-27%)
    max: 8  # 15→8 (-47%)
```

---

### 例2: パフォーマンスの反復改善

**状況**: 処理時間が長く、ユーザーエクスペリエンスに影響

**入力**:
```bash
Task(
    subagent_type="improvement-implementer",
    prompt="パフォーマンス改善を反復実行（--perf --iterate --threshold high）"
)
```

**処理**:
1. ボトルネックを特定（プロファイリング）
2. アルゴリズムの効率化
3. キャッシング戦略の実装
4. 改善効果を測定
5. 閾値に達するまで繰り返し

**期待される出力**:
```yaml
improvements:
  - id: "IMP-001"
    type: "パフォーマンス最適化"
    location: "src/process.py:120"
    change: "O(n²) → O(n) アルゴリズムに変更"
    rationale: "処理時間 500ms→50ms (-90%)"
    expected_effect: "応答時間の大幅短縮"
```

---

### 例3: 安全なリファクタリング

**状況**: アーキテクチャを改善したいが、既存機能は保持したい

**入力**:
```bash
Task(
    subagent_type="improvement-implementer",
    prompt="安全なリファクタリングを実行（--arch --refactor --safe）"
)
```

**処理**:
1. 現在のアーキテクチャを分析
2. 保守的な改善のみを計画
3. 設計パターンを段階的に適用
4. 各ステップでテスト実行
5. 動作の保持を確認

**期待される出力**:
```yaml
verification:
  quality_checker: "PASS"
  all_tests_passed: true
  regression_detected: false
```

---

### 例4: メトリクス付き品質改善

**状況**: 改善効果を定量的に測定したい

**入力**:
```bash
Task(
    subagent_type="improvement-implementer",
    prompt="メトリクス付き品質改善（--quality --metrics --threshold perfect）"
)
```

**処理**:
1. 改善前メトリクスを詳細に測定
2. 可能な限り高品質を目指して改善
3. 各改善の効果を測定
4. 改善後メトリクスを詳細に測定
5. レポートに全メトリクスを記録

**期待される出力**:
```yaml
summary:
  total_improvements: 15
  files_modified: 8
  lines_changed: 450
  overall_improvement: "+35%"
```

## 品質基準

このスキルの成果物は以下の品質基準を満たす必要があります：

### 必須（MUST）

- [ ] 改善前のメトリクスが測定されている
- [ ] 改善内容に測定可能な根拠がある（エビデンスベース）
- [ ] 改善後のメトリクスが測定されている
- [ ] 全テストがパスしている
- [ ] 回帰が発生していない
- [ ] レポートがYAML形式で保存されている

### 推奨（SHOULD）

- 改善は小さな原子的変更で実施されている
- 各改善の期待効果が明記されている
- 改善のトレードオフが評価されている
- 既存ツール（make format, lint, test等）を活用している

## エラーハンドリング

### テストが失敗する

**原因**: 改善によって既存機能が壊れた

**対処法**:
1. 直前の変更をロールバック
2. より小さな変更に分割
3. テストを追加して保護

### メトリクスが改善しない

**原因**: 改善方針が適切でない

**対処法**:
1. 分析結果を再確認
2. 別の改善アプローチを検討
3. 専門家にレビューを依頼

### 回帰が検出される

**原因**: 改善が既存の動作に影響

**対処法**:
1. 回帰テストを追加
2. 影響範囲を特定
3. 段階的なロールバック

## 完了条件

このスキルは以下の条件を満たした場合に完了とする：

- [ ] 改善前メトリクスが測定・記録されている
- [ ] 改善が実装されている
- [ ] 改善後メトリクスが測定・記録されている
- [ ] 全テストがパスしている
- [ ] 回帰が発生していない
- [ ] レポートがYAML形式で保存されている
- [ ] ユーザーに改善結果が報告されている

## 既存ツールとの連携

改善プロセスは以下のツールを活用します：

| ツール | 用途 |
|--------|------|
| `make format` | コードフォーマットの統一 |
| `make lint` | リント違反の自動修正 |
| `make typecheck` | 型の一貫性確認 |
| `make test` | 改善後の動作確認 |
| `make benchmark` | パフォーマンス改善の測定 |

## 注意事項

- `--iterate`モードは処理時間が長くなる可能性があります
- 大規模な変更前は必ずバックアップまたは git のコミットを作成してください
- パフォーマンス改善は必ずベンチマークで検証してください
- テストカバレッジが低い場合は、先にテストを追加することを推奨します

## 関連スキル

- **analyze**: コード分析（改善前の分析に使用）
- **ensure-quality**: 品質チェックの自動修正
- **scan**: セキュリティと品質の包括的検証
- **coding-standards**: コーディング規約（品質改善の基準）
- **tdd-development**: TDD開発プロセス（テスト追加時に参照）

## 参考資料

- `.claude/rules/evidence-based.md`: エビデンスベース開発の原則
- `.claude/rules/coding-standards.md`: コーディング規約
- `.claude/agents/improvement-implementer.md`: 実装エージェント
