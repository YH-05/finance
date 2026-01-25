---
name: scan
description: セキュリティと品質の包括的検証を実行。OWASP Top 10準拠チェック、脆弱性検出、品質スコアリングを提供。プロアクティブに使用。
allowed-tools: Read, Bash, Task
---

# Scan - セキュリティと品質の包括的検証

> **役割の明確化**: このスキルは**検証・スコアリング**に特化しています。
>
> - 問題の自動修正を行いたい場合 → `ensure-quality` スキル
> - 詳細な分析レポートが欲しい場合 → `analyze` スキル
> - 改善の実装を行いたい場合 → `improve` スキル

## 目的

このスキルは以下を提供します：

- **セキュリティ脆弱性の検出**: OWASP Top 10に基づく包括的なセキュリティチェック
- **品質検証**: コーディング規約、型の一貫性、テストカバレッジの検証
- **スコアリング**: セキュリティスコアと総合品質スコアの算出
- **レポート生成**: YAML形式での詳細なスキャン結果レポート

## いつ使用するか

### プロアクティブ使用（自動で使用を検討）

以下の状況では、ユーザーが明示的に要求しなくても使用を検討してください：

1. **リリース前の検証**
   - PRマージ前のセキュリティチェック
   - リリースブランチの品質検証
   - 本番デプロイ前の最終確認

2. **定期的な監査**
   - 週次・月次のセキュリティ監査
   - 依存関係の脆弱性チェック
   - 品質スコアのトラッキング

3. **問題の早期発見**
   - 新機能追加後の脆弱性チェック
   - 外部ライブラリ導入後のリスク評価
   - セキュリティパッチ適用の優先度判定

### 明示的な使用（ユーザー要求）

- `/scan` コマンド
- 「セキュリティチェックして」「脆弱性をスキャンして」などの要求
- security-scanner サブエージェント呼び出し

## プロセス

### ステップ 1: スキャン対象の特定

```bash
# プロジェクト構造を確認
ls -la src/

# スキャン対象のライブラリを特定
# デフォルト: プロジェクト全体
# 指定された場合: 特定のパス
```

### ステップ 2: スキャンモードの設定

以下のモードから必要なものを選択：

| モード | 説明 |
|--------|------|
| `--security` | セキュリティ脆弱性のスキャン |
| `--validate` | 品質検証の実行 |
| `--owasp` | OWASP Top 10に基づく検証 |

### ステップ 3: セキュリティスキャンの実行

```bash
# banditでセキュリティチェック
make security

# pip-auditで依存関係チェック
make audit
```

**検出項目**:
- SQLインジェクション（CWE-89）
- XSS（クロスサイトスクリプティング）
- 安全でない乱数生成
- ハードコードされた認証情報
- 不適切な暗号化

### ステップ 4: OWASP Top 10チェック

以下の各項目を検証：

| ID | カテゴリ | 検証内容 |
|----|---------|---------|
| A01 | アクセス制御 | 権限チェック、認可の実装 |
| A02 | 暗号化の失敗 | 暗号化アルゴリズム、鍵管理 |
| A03 | インジェクション | SQL、コマンド、コードインジェクション |
| A04 | 安全でない設計 | 設計レベルのセキュリティ脆弱性 |
| A05 | セキュリティ設定ミス | デフォルト設定、不要な機能 |
| A06 | 脆弱なコンポーネント | 依存関係の脆弱性 |
| A07 | 認証の失敗 | セッション管理、パスワードポリシー |
| A08 | 整合性の失敗 | データ検証、署名検証 |
| A09 | ログとモニタリング | ログ記録、監視体制 |
| A10 | SSRF | サーバーサイドリクエストフォージェリ |

### ステップ 5: 品質検証の実行

```bash
# コーディング規約チェック
make lint

# 型チェック
make typecheck

# テストカバレッジ測定
make test-cov
```

**検証項目**:
- コーディング規約の遵守
- 型の一貫性
- テストカバレッジ（目標: 80%以上）
- ドキュメントの完全性
- 依存関係の健全性

### ステップ 6: スコアリング

以下の基準でスコアを算出：

```yaml
セキュリティスコア (0-100):
  脆弱性なし: 100点
  Low: -5点/件
  Medium: -15点/件
  High: -30点/件
  Critical: -50点/件

品質スコア (0-100):
  基本点: 50点
  テストカバレッジ: +30点（80%以上で満点）
  型チェック: +10点（エラーなしで満点）
  リントエラー: +10点（エラーなしで満点）
```

### ステップ 7: レポート生成

```yaml
出力先: src/<library_name>/docs/scan-report-YYYYMMDD.yaml
または: --output オプションで指定されたパス

レポート構造:
  metadata: スキャン情報（日時、対象、モード）
  scores: セキュリティスコア、総合スコア
  vulnerability_summary: 脆弱性サマリー（重大度別）
  owasp_top_10: OWASP Top 10準拠状況
  vulnerabilities: 検出された脆弱性の詳細リスト
  quality_validation: 品質検証結果
  fixes_applied: 自動修正結果（--fixオプション使用時）
  summary: 総合評価と推奨アクション
```

## リソース

### ./guide.md

詳細なスキャンガイド（作成予定）：

- 各スキャンモードの詳細説明
- OWASP Top 10チェック項目の詳細
- スコアリングアルゴリズムの詳細
- False Positive対応ガイド

### ./template.md

レポートテンプレート（作成予定）：

- YAML形式のレポート構造
- 各フィールドの説明
- 脆弱性レポートの記述例

## 使用例

### 例1: 基本的なセキュリティスキャン

**状況**: PRマージ前にセキュリティチェックを実行したい

**入力**:
```bash
/scan --security
```

**処理**:
1. bandit でコードをスキャン
2. pip-audit で依存関係をチェック
3. セキュリティスコアを算出
4. レポートを生成

**期待される出力**:
```yaml
scores:
  security: 95
  overall: 92

vulnerability_summary:
  critical: 0
  high: 0
  medium: 1
  low: 2
  total: 3

summary:
  recommendation: "Medium 1件、Low 2件の脆弱性が検出されました。優先度の高い順に対応してください。"
```

---

### 例2: OWASP Top 10準拠チェック

**状況**: 本番デプロイ前にOWASP Top 10準拠を確認したい

**入力**:
```bash
/scan --owasp
```

**処理**:
1. OWASP Top 10各項目を検証
2. PASS/WARN/FAIL判定
3. 詳細レポート生成

**期待される出力**:
```yaml
owasp_top_10:
  A01_access_control: "PASS"
  A02_cryptographic_failures: "PASS"
  A03_injection: "WARN"
  A04_insecure_design: "PASS"
  A05_security_misconfiguration: "PASS"
  A06_vulnerable_components: "WARN"
  A07_authentication_failures: "PASS"
  A08_integrity_failures: "PASS"
  A09_logging_failures: "PASS"
  A10_ssrf: "PASS"

summary:
  recommendation: "A03（インジェクション）とA06（脆弱なコンポーネント）に警告があります。詳細を確認してください。"
```

---

### 例3: 包括的スキャン（全モード）

**状況**: 週次セキュリティ監査を実施したい

**入力**:
```bash
/scan --security --owasp --validate
```

**処理**:
1. セキュリティスキャン実行
2. OWASP Top 10チェック実行
3. 品質検証実行
4. 総合スコア算出
5. 包括的レポート生成

**期待される出力**:
```yaml
scores:
  security: 88
  overall: 85

vulnerability_summary:
  critical: 0
  high: 1
  medium: 2
  low: 3
  total: 6

quality_validation:
  coding_standards: "PASS"
  type_consistency: "PASS"
  test_coverage: "85%"
  documentation_coverage: "70%"
  dependency_health: "PASS"

summary:
  passed_checks: 42
  failed_checks: 6
  warnings: 3
  recommendation: "High 1件の脆弱性を優先的に対応してください。その後、Medium以下の問題に対処してください。"
```

---

### 例4: 自動修正付きスキャン

**状況**: セキュリティ問題を検出して自動修正したい

**入力**:
```bash
/scan --security --fix
```

**処理**:
1. セキュリティスキャン実行
2. 修正可能な問題を特定
3. 安全な代替案への置換
4. 修正結果をレポート

**期待される出力**:
```yaml
vulnerabilities:
  - id: "SEC-001"
    severity: "HIGH"
    category: "安全でない乱数生成"
    location: "src/utils/token.py:12"
    description: "random.random()は暗号学的に安全ではありません"
    evidence: "token = random.random()"
    recommendation: "secrets.token_hex()を使用"

fixes_applied:
  - vulnerability_id: "SEC-001"
    fix_type: "secrets.token_hex()への変換"
    status: "APPLIED"
    changed_files:
      - "src/utils/token.py"
```

## オプション

### --security

セキュリティ脆弱性のスキャンを実行。

**検出項目**:
- SQLインジェクション
- XSS（クロスサイトスクリプティング）
- 安全でない乱数生成
- ハードコードされた認証情報
- 不適切な暗号化

### --validate

品質検証を実行。

**検証項目**:
- コーディング規約の遵守
- 型の一貫性
- テストカバレッジ
- ドキュメントの完全性
- 依存関係の健全性

### --owasp

OWASP Top 10に基づく検証を実行。

**検証カテゴリ**:
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

検出された問題の自動修正を実行。

**修正内容**:
- 安全な代替案への置換
- セキュリティパッチの適用
- 設定の強化
- 依存関係の更新

### --output <path>

レポートの出力先を指定。

**デフォルト**: `src/<library_name>/docs/scan-report-YYYYMMDD.yaml`

**例**: `--output reports/my-scan.yaml`

## 既存ツールとの統合

このスキルは以下のツールと連携：

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

## スキャン項目詳細

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

## 品質基準

このスキルの成果物は以下の品質基準を満たす必要があります：

### 必須（MUST）

- [ ] セキュリティスコアが算出されている
- [ ] 検出された脆弱性が重大度別に分類されている
- [ ] YAML形式のレポートが生成されている
- [ ] 推奨アクションが明記されている
- [ ] CWE IDとOWASPカテゴリが紐づいている

### 推奨（SHOULD）

- OWASP Top 10準拠状況が含まれている
- 品質検証結果が含まれている
- False Positiveの除外設定が適切
- レポートが構造化されており読みやすい

## ベストプラクティス

1. **定期的な実行**: 日次または週次でスキャンを実行
2. **CI/CD統合**: PRごとに自動スキャン
3. **段階的改善**: 重大度の高い問題から対処
4. **False Positive対応**: 誤検出は適切に除外設定
5. **継続的な更新**: ルールとパターンの定期的な見直し

## 注意事項

- このスキルは補完的なツールであり、専門的なセキュリティ監査の代替ではありません
- `--fix`オプションは必ず変更内容を確認してから適用してください
- 大規模なコードベースではスキャンに時間がかかる場合があります

## エラーハンドリング

### スキャンツールが見つからない

**原因**: bandit, pip-auditがインストールされていない

**対処法**:
```bash
# 開発依存関係をインストール
uv sync --all-extras
```

### レポート出力に失敗

**原因**: 出力先ディレクトリが存在しない

**対処法**:
```bash
# ディレクトリを作成
mkdir -p src/<library_name>/docs/
```

### スキャンがタイムアウト

**原因**: 大規模なコードベース

**対処法**:
- 特定のパスに絞ってスキャン
- 段階的にスキャン範囲を拡大

## 完了条件

このスキルは以下の条件を満たした場合に完了とする：

- [ ] 全スキャンモードが実行されている
- [ ] セキュリティスコアが算出されている
- [ ] YAML形式のレポートが生成されている
- [ ] 検出された脆弱性が重大度別にリストされている
- [ ] 推奨アクションが明記されている

## 関連スキル・コマンド

- **ensure-quality**: 問題の自動修正を実行
- **analyze**: 詳細な分析レポートを生成
- **improve**: エビデンスベースの改善実装
- **troubleshoot**: 体系的なデバッグ

## サブエージェント呼び出し

このスキルは **security-scanner サブエージェント** を使用して実行されます。

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

## 参考資料

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- bandit: https://bandit.readthedocs.io/
- pip-audit: https://pypi.org/project/pip-audit/
- CWE（Common Weakness Enumeration）: https://cwe.mitre.org/
