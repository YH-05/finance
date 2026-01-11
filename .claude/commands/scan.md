---
description: セキュリティと品質の包括的検証
---

# /scan - セキュリティと品質の包括的検証

> **役割の明確化**: このコマンドは**検証・スコアリング**に特化しています。
>
> - 問題の自動修正を行いたい場合 → `/ensure-quality`
> - 詳細な分析レポートが欲しい場合 → `/analyze`
> - 改善の実装を行いたい場合 → `/improve`

**目的**: プロジェクトのセキュリティ脆弱性と品質問題を検出し、検証する

## 実行方法

このコマンドは **security-scanner サブエージェント** を使用して実行されます。

### サブエージェント呼び出し

```yaml
subagent_type: "security-scanner"
description: "Security vulnerability scan"
prompt: |
  セキュリティスキャンを実行してください。

  ## 対象
  [指定されたパス、またはプロジェクト全体]

  ## スキャンモード
  [--security, --validate, --owasp など指定されたオプション]

  ## 出力
  - セキュリティスコア
  - OWASP Top 10 準拠状況
  - 検出された脆弱性（重大度別）
  - 推奨アクション

  ## レポート出力
  スキャン完了後、以下のパスにYAML形式でレポートを保存してください：
  - 出力先: src/<library_name>/docs/scan-report-YYYYMMDD.yaml
  - --output オプションが指定された場合はそのパスに出力
```

## 使用方法

```bash
/scan [オプション] [対象]
```

## オプション

### --security

セキュリティ脆弱性のスキャン：

- SQLインジェクション
- XSS（クロスサイトスクリプティング）
- 安全でない乱数生成
- ハードコードされた認証情報
- 不適切な暗号化

### --validate

品質検証の実行：

- コーディング規約の遵守
- 型の一貫性
- テストカバレッジ
- ドキュメントの完全性
- 依存関係の健全性

### --owasp

OWASP Top 10に基づく検証：

- A01: アクセス制御の不備
- A02: 暗号化の失敗
- A03: インジェクション
- A04: 安全でない設計
- A05: セキュリティの設定ミス
- A06: 脆弱で古いコンポーネント
- A07: 識別と認証の失敗
- A08: ソフトウェアとデータの整合性の失敗
- A09: セキュリティログとモニタリングの失敗
- A10: サーバーサイドリクエストフォージェリ

### --fix

検出された問題の自動修正：

- 安全な代替案への置換
- セキュリティパッチの適用
- 設定の強化
- 依存関係の更新

### --output <path>

レポートの出力先を指定：

- デフォルト: `src/<library_name>/docs/scan-report-YYYYMMDD.yaml`
- 例: `--output reports/my-scan.yaml`

## 実行例

### 基本的な使用

```bash
# セキュリティスキャン
/scan --security

# OWASP Top 10チェック
/scan --owasp

# 品質検証
/scan --validate

# 包括的スキャン
/scan --security --owasp --validate
```

### 自動修正付き

```bash
# セキュリティ問題の自動修正
/scan --security --fix

# 修正前の確認
/scan --security --fix --dry-run
```

### 出力先を指定

```bash
# 特定のパスにレポートを出力
/scan --security --output src/my_lib/docs/scan-report-20240115.yaml

# レポートディレクトリに出力
/scan --owasp --output reports/security-scan.yaml
```

## 出力形式

スキャン結果は以下のYAML形式でファイルに保存されます：

### 出力先

```
src/<library_name>/docs/scan-report-YYYYMMDD.yaml
```

- `<library_name>`: スキャン対象のライブラリ名（自動検出）
- `YYYYMMDD`: 実行日（例: 20240115）

### レポート構造

```yaml
# セキュリティスキャンレポート
# 生成日時: YYYY-MM-DD HH:MM:SS
# 生成コマンド: /scan [オプション]

metadata:
  generated_at: "YYYY-MM-DD HH:MM:SS"
  target: "<スキャン対象パス>"
  scan_modes:
    - security
    - owasp
    - validate
  files_scanned: 0

scores:
  security: 0  # 0-100
  overall: 0   # 0-100

vulnerability_summary:
  critical: 0
  high: 0
  medium: 0
  low: 0
  info: 0
  total: 0

owasp_top_10:
  A01_access_control: "PASS"      # PASS/WARN/FAIL
  A02_cryptographic_failures: "PASS"
  A03_injection: "PASS"
  A04_insecure_design: "PASS"
  A05_security_misconfiguration: "PASS"
  A06_vulnerable_components: "PASS"
  A07_authentication_failures: "PASS"
  A08_integrity_failures: "PASS"
  A09_logging_failures: "PASS"
  A10_ssrf: "PASS"

vulnerabilities:
  - id: "SEC-001"
    severity: "CRITICAL"
    category: "SQLインジェクション"
    location: "src/database/query.py:45"
    description: "ユーザー入力が直接SQLクエリに使用されています"
    evidence: "f\"SELECT * FROM users WHERE id = {user_id}\""
    recommendation: "パラメータ化クエリを使用"
    cwe_id: "CWE-89"
    owasp_category: "A03"

quality_validation:
  coding_standards: "PASS"  # PASS/FAIL
  type_consistency: "PASS"
  test_coverage: "85%"
  documentation_coverage: "70%"
  dependency_health: "PASS"

fixes_applied:  # --fix オプション使用時のみ
  - vulnerability_id: "SEC-001"
    fix_type: "パラメータ化クエリへの変換"
    status: "APPLIED"

summary:
  passed_checks: 0
  failed_checks: 0
  warnings: 0
  recommendation: "<総合的な推奨アクション>"
```

## 既存ツールとの統合

`/scan`は以下のツールと連携：

```bash
# セキュリティツール
make security    # banditを実行
make audit       # pip-auditを実行

# 品質ツール
make lint        # ruffでリント
make typecheck   # pyrightで型チェック
make test-cov    # カバレッジ測定

# 統合ワークフロー
/scan --security → make security → make audit → 総合レポート
```

## スキャン項目

### セキュリティチェック

```yaml
認証・認可:
  - パスワードの複雑性
  - セッション管理
  - 権限チェック
  - 多要素認証

データ保護:
  - 暗号化の実装
  - 機密データの処理
  - PII（個人識別情報）の扱い
  - データマスキング

入力検証:
  - サニタイゼーション
  - バリデーション
  - エスケープ処理
  - 型チェック
```

### 品質チェック

```yaml
コード品質:
  - 循環的複雑度
  - 重複コード
  - デッドコード
  - 未使用の変数/関数

保守性:
  - モジュール結合度
  - 依存関係の健全性
  - ドキュメントカバレッジ
  - テストカバレッジ

パフォーマンス:
  - N+1クエリ
  - 非効率なアルゴリズム
  - メモリリーク
  - リソースの適切な解放
```

## ベストプラクティス

1. **定期的な実行**: 日次または週次でスキャンを実行
2. **CI/CD統合**: PRごとに自動スキャン
3. **段階的改善**: 重大度の高い問題から対処
4. **False Positive対応**: 誤検出は適切に除外設定
5. **継続的な更新**: ルールとパターンの定期的な見直し

## 注意事項

- スキャンは補完的なツールであり、専門的なセキュリティ監査の代替ではありません
- `--fix`オプションは必ず変更内容を確認してから適用してください
- 大規模なコードベースではスキャンに時間がかかる場合があります
