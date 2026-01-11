---
description: コード品質の自動改善（make check-all相当）
---

# コード品質の自動改善

**役割の明確化**: このコマンドは `make check-all` 相当の**自動修正**に特化しています。

- 検証・スコアリングのみ行いたい場合 → `/scan --validate`
- 分析レポートが欲しい場合 → `/analyze`
- エビデンスベースの改善実装 → `/improve`

`make check-all`が成功するまで、自動的にコードを修正してコード品質を保証します。

## 実行方法

このコマンドは **quality-checker サブエージェント** を使用して実行されます。

### サブエージェント呼び出し

```yaml
subagent_type: "quality-checker"
description: "Auto-fix code quality issues"
prompt: |
  コード品質の自動修正を実行してください。

  ## モード
  --auto-fix

  ## 対象
  [指定されたパス、またはプロジェクト全体]

  ## 目標
  make check-all が成功するまで以下を繰り返し修正:
  1. make format - コードフォーマット
  2. make lint - リントチェック
  3. make typecheck - 型チェック
  4. make test - テスト実行

  ## 参照
  - CLAUDE.md のコーディング規約
  - template/ ディレクトリの実装例
```

## 修正の順序

1. **コードフォーマット** (`make format`) - Ruff による自動フォーマット
2. **リントチェック** (`make lint`) - Ruff によるリントチェックと自動修正
3. **型チェック** (`make typecheck`) - pyright による厳格な型チェック
4. **テスト実行** (`make test`) - 全テストの実行

## 使用例

```bash
# プロジェクト全体の品質修正
/ensure-quality

# 特定のディレクトリの品質修正
/ensure-quality src/mylib/core/
```

## 修正ループ

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  make check-all 実行                                        │
│       │                                                     │
│       ├─→ 成功 → 完了レポート出力                           │
│       │                                                     │
│       └─→ 失敗 → エラー種別を判定                           │
│              │                                              │
│              ├─→ フォーマット → make format → 再検証        │
│              ├─→ リント → make lint + 手動修正 → 再検証     │
│              ├─→ 型エラー → 型ヒント修正 → 再検証           │
│              └─→ テスト失敗 → 実装/テスト修正 → 再検証      │
│                                                             │
│  最大5回ループ後、未解決問題をレポート                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 重要な注意事項

- **CLAUDE.md の規約に従う**: 型ヒント、エラーメッセージ、コーディングスタイルは CLAUDE.md の規約に準拠
- **既存の動作を保持**: テストが失敗した場合、まず実装が仕様通りかを確認し、必要に応じてテストも修正
- **段階的な修正**: 一度にすべてを修正せず、エラーの種類ごとに段階的に対処
- **進捗の報告**: 各ステップでの修正内容と結果を明確に報告

## エラー対処の具体例

### 型エラーの例

```python
# エラー: Incompatible return value type (got "None", expected "str")
def get_name() -> str:
    return None  # 修正前

# 修正後
def get_name() -> str | None:
    return None
```

### リントエラーの例

```python
# エラー: F401 'os' imported but unused
import os  # 修正: 未使用のインポートを削除

# エラー: E501 line too long (120 > 100 characters)
# 修正: 長い行を適切に改行
```

## 出力形式

```yaml
品質修正レポート:
  実行時間: [秒]
  修正サイクル数: [回]

初期状態:
  フォーマット: [PASS/FAIL]
  リント: [PASS/FAIL] ([エラー数]件)
  型チェック: [PASS/FAIL] ([エラー数]件)
  テスト: [PASS/FAIL] ([失敗数]/[総数])

実施した修正:
  - ファイル: [パス]
    問題: [問題の説明]
    修正: [修正内容]

最終状態:
  make check-all: PASS
```

このコマンドを実行することで、プロジェクトのコード品質を一貫して高いレベルに保つことができます。
