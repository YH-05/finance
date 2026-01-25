---
name: analyze
description: 多次元コード分析（分析レポート出力）。code-analyzerサブエージェントを使用してコード品質、アーキテクチャ、セキュリティ、パフォーマンスを包括的に分析し、YAMLレポートを出力する。
allowed-tools: Read, Bash, Task
---

# Analyze - 多次元コード分析スキル

> **役割の明確化**: このスキルは**分析レポート出力**に特化しています。
>
> - 分析結果に基づく改善実装 → `improve` スキル
> - 問題の自動修正 → `ensure-quality` コマンド
> - セキュリティスコアリング → `scan` コマンド

## 目的

このスキルは以下を提供します：

- **コード品質分析**: 命名規則、複雑性、型ヒント、docstringの品質を評価
- **アーキテクチャ分析**: レイヤー間の結合度、依存関係、設計パターンの適用状況を評価
- **セキュリティ監査**: OWASP Top 10の脆弱性チェック、認証・認可の実装確認
- **パフォーマンス分析**: アルゴリズム複雑度、メモリ効率、I/O最適化機会の特定
- **改善ロードマップ**: 発見事項を基にした段階的改善計画の作成

## いつ使用するか

### プロアクティブ使用（自動で使用を検討）

このスキルは通常、明示的な要求がない限り使用されません。

### 明示的な使用（ユーザー要求）

- `/analyze` コマンド
- 「コード分析して」「品質を確認して」などの要求
- Task tool で `subagent_type="code-analyzer"` を指定された場合

## 分析観点

### コード品質分析（--code）

以下の項目を分析します：

- **命名規則の一貫性**: PEP 8準拠、わかりやすい変数名
- **関数・クラスの複雑性**: サイクロマティック複雑性（10未満推奨）
- **DRY原則の遵守状況**: コード重複の検出
- **型ヒントのカバレッジ**: Python 3.12+ スタイル（PEP 695）の適用状況
- **docstringの品質**: NumPy形式の適用状況

### アーキテクチャ分析（--arch）

以下の項目を分析します：

- **レイヤー間の結合度**: 各レイヤーの独立性
- **依存関係の方向性**: 循環依存の検出
- **設計パターンの適用状況**: SOLID原則の遵守
- **モジュール間の責務分離**: 単一責任原則の適用
- **スケーラビリティの評価**: 拡張性の観点での評価

### セキュリティ監査（--security）

以下の項目を分析します：

- **OWASP Top 10の脆弱性チェック**: Injection、認証の不備など
- **認証・認可の実装確認**: アクセス制御の適切性
- **入力検証とサニタイゼーション**: 入力データの検証状況
- **暗号化とデータ保護**: 機密情報の保護状況
- **エラーハンドリングの安全性**: 例外処理での情報漏洩リスク

### パフォーマンス分析（--perf）

以下の項目を分析します：

- **アルゴリズムの時間計算量**: O(n²)以上のアルゴリズム検出
- **メモリ使用効率**: メモリリークやメモリ非効率パターン
- **I/O操作の最適化機会**: ファイル操作、ネットワーク操作の効率
- **データベースクエリの効率性**: N+1問題の検出
- **キャッシング機会の特定**: キャッシュ導入による最適化機会

## プロセス

### ステップ 1: code-analyzer サブエージェントの呼び出し

Task ツールを使用してサブエージェントを呼び出します：

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
  - 各観点のスコア（0-100）
  - 発見事項（重大度別: critical, high, medium, low）
  - 具体的なメトリクス
  - 改善ロードマップ（短期・中期・長期）

  ## レポート出力
  分析完了後、以下のパスにYAML形式でレポートを保存してください：
  - 出力先: docs/code-analysis-report/analysis-report-YYYYMMDD-<target>.yaml
  - テンプレート参照: docs/code-analysis-report/TEMPLATE.yaml
  - --output オプションが指定された場合はそのパスに出力
```

### ステップ 2: 分析対象の特定

以下の優先順位で分析対象を決定します：

1. **明示的なパス指定**: `@src/market_analysis/` など
2. **カレントディレクトリ**: 引数なしの場合
3. **プロジェクト全体**: `--all` 指定時

### ステップ 3: 分析モードの決定

| オプション | 分析内容 |
|-----------|---------|
| `--all` | 全観点（code, arch, security, perf）を一括分析 |
| `--code` | コード品質のみ |
| `--arch` | アーキテクチャのみ |
| `--security` | セキュリティのみ |
| `--perf` | パフォーマンスのみ |

複数指定可（例: `--code --security`）

### ステップ 4: 分析深度の設定

| フラグ | 分析深度 |
|--------|---------|
| `--think` | 標準的な分析（デフォルト） |
| `--think-hard` | 深い分析 |
| `--ultrathink` | 最も詳細な分析 |

### ステップ 5: 分析実行

code-analyzer サブエージェントが以下を実施：

1. **既存ツールの実行**:
   - `pyright`: 型チェック結果の統合
   - `ruff`: リンター出力の分析
   - `bandit`: セキュリティ問題の検出
   - `pytest`: テストカバレッジの確認

2. **メトリクス収集**:
   - サイクロマティック複雑性
   - コード重複率
   - 型ヒントカバレッジ
   - docstringカバレッジ

3. **問題の検出**:
   - 循環依存
   - セキュリティ脆弱性
   - パフォーマンスボトルネック

### ステップ 6: レポート生成

分析結果をYAML形式で以下に出力：

```
docs/code-analysis-report/analysis-report-YYYYMMDD-<target>.yaml
```

ファイル命名例：

| 分析対象 | 出力ファイル名 |
|----------|----------------|
| `@src/market_analysis/` | `analysis-report-20260118-market_analysis.yaml` |
| `@src/rss/` | `analysis-report-20260118-rss.yaml` |
| プロジェクト全体 | `analysis-report-20260118-full.yaml` |

## リソース

### docs/code-analysis-report/TEMPLATE.yaml

レポートの詳細構造テンプレート：

```yaml
metadata:
  generated_at: "YYYY-MM-DD HH:MM:SS"
  target: "<分析対象パス>"
  analysis_modes:
    - code
    - arch
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

## 使用例

### 例1: 全観点の包括的分析

**状況**: プロジェクト全体の品質を確認したい

**実行**:
```bash
/analyze --all
```

**処理**:
1. code-analyzer サブエージェントを呼び出し
2. code, arch, security, perf の全観点を分析
3. レポートを `docs/code-analysis-report/analysis-report-20260118-full.yaml` に出力

**期待される出力**:
- 各観点のスコア（0-100）
- 発見事項（重大度別）
- 改善ロードマップ（短期・中期・長期）

---

### 例2: 特定ファイルのセキュリティ監査

**状況**: 認証モジュールのセキュリティを確認したい

**実行**:
```bash
/analyze --security src/auth/
```

**処理**:
1. code-analyzer サブエージェントを呼び出し
2. src/auth/ ディレクトリのセキュリティを分析
3. OWASP Top 10の脆弱性をチェック
4. レポートを `docs/code-analysis-report/analysis-report-20260118-auth.yaml` に出力

**期待される出力**:
- セキュリティスコア
- 検出された脆弱性（critical, high, medium, low）
- 改善案

---

### 例3: パフォーマンスボトルネックの特定

**状況**: コアモジュールのパフォーマンスを詳細に分析したい

**実行**:
```bash
/analyze --perf --ultrathink src/core/
```

**処理**:
1. code-analyzer サブエージェントを呼び出し
2. src/core/ ディレクトリのパフォーマンスを最も詳細に分析
3. O(n²)以上のアルゴリズムを検出
4. キャッシング機会を特定
5. レポートを `docs/code-analysis-report/analysis-report-20260118-core.yaml` に出力

**期待される出力**:
- パフォーマンススコア
- 時間計算量の問題（O(n²)以上）
- メモリ非効率パターン
- 最適化機会

---

### 例4: 複合分析（コードとセキュリティ）

**状況**: コード品質とセキュリティを同時に確認したい

**実行**:
```bash
/analyze --code --security --think-hard
```

**処理**:
1. code-analyzer サブエージェントを呼び出し
2. コード品質とセキュリティを深く分析
3. レポートを `docs/code-analysis-report/analysis-report-20260118-full.yaml` に出力

**期待される出力**:
- コード品質スコア（複雑性、型ヒント、docstring）
- セキュリティスコア（脆弱性検出）
- 統合された改善ロードマップ

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

## 品質基準

このスキルの成果物は以下の品質基準を満たす必要があります：

### 必須（MUST）

- [ ] YAML形式のレポートが正しく生成されている
- [ ] 指定された分析観点が全て含まれている
- [ ] 各観点のスコア（0-100）が算出されている
- [ ] 発見事項が重大度別（critical, high, medium, low）に分類されている
- [ ] 改善ロードマップ（短期・中期・長期）が含まれている

### 推奨（SHOULD）

- 発見事項に具体的なメトリクス値が含まれている
- 改善案が実装可能な形で提示されている
- 関連する既存ツール（pyright, ruff, bandit）の結果が統合されている

## 出力フォーマット

### 分析完了時

```
================================================================================
                    コード分析完了
================================================================================

## 分析対象
- パス: {target_path}
- 分析モード: {modes}
- 分析深度: {depth}

## スコア
| 観点 | スコア |
|------|--------|
| コード品質 | {code_quality_score}/100 |
| アーキテクチャ | {architecture_score}/100 |
| セキュリティ | {security_score}/100 |
| パフォーマンス | {performance_score}/100 |
| 総合 | {overall_score}/100 |

## 発見事項サマリー
- Critical: {critical_count}件
- High: {high_count}件
- Medium: {medium_count}件
- Low: {low_count}件

## レポート出力先
{output_path}

================================================================================
```

## エラーハンドリング

### エラーパターン1: 分析対象が見つからない

**原因**: 指定されたパスが存在しない

**対処法**:
1. パスの存在を確認
2. カレントディレクトリを確認
3. 正しいパスを再指定

### エラーパターン2: 既存ツールの実行エラー

**原因**: pyright, ruff, bandit などのツールが正しく実行できない

**対処法**:
1. 該当ツールのインストールを確認
2. ツールのバージョンを確認
3. エラーメッセージを確認して対処

### エラーパターン3: レポート出力エラー

**原因**: 出力先ディレクトリが存在しない

**対処法**:
1. `docs/code-analysis-report/` ディレクトリを作成
2. 書き込み権限を確認

## 注意事項

- 大規模なコードベースでは`--ultrathink`の使用に時間がかかる場合があります
- セキュリティ分析は補完的なツールとして使用し、専門的なセキュリティ監査の代替にはなりません
- パフォーマンス分析は静的解析に基づくため、実際のベンチマークと併用してください
- レポートは日付とターゲット名で一意に命名されるため、同日・同対象の再実行で上書きされます

## 完了条件

このスキルは以下の条件を満たした場合に完了とする：

- [ ] code-analyzer サブエージェントが正しく呼び出されている
- [ ] 指定された分析モードが全て実行されている
- [ ] YAML形式のレポートが正しく生成されている
- [ ] レポートに全必須セクションが含まれている
- [ ] 発見事項が重大度別に分類されている
- [ ] 改善ロードマップが提示されている

## 関連スキル

- **improve**: 分析結果に基づく改善実装
- **coding-standards**: コード品質の基準（分析時の参照）
- **tdd-development**: テストカバレッジの評価（分析に含まれる）
- **error-handling**: エラーハンドリングの品質（分析に含まれる）

## 参考資料

- `docs/code-analysis-report/TEMPLATE.yaml`: レポートテンプレート
- `.claude/agents/code-analyzer.md`: code-analyzer サブエージェント
- `CLAUDE.md`: プロジェクト全体のガイドライン
