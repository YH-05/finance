# P9-008: CI/CD 設定確認と更新

## 概要

ローカル環境ではサブスクリプション認証、CI/CD 環境では API キー認証を使い分ける設定を確認・更新する。

## フェーズ

Phase 9: claude-agent-sdk 移行

## 依存タスク

- P9-007: ローカル統合テスト

## 成果物

- CI/CD 設定の確認結果
- 必要に応じて `.github/workflows/` の更新

## 背景

claude-agent-sdk は以下の認証方式をサポート：

| 環境 | 認証方式 | 設定 |
|---|---|---|
| **ローカル** | サブスクリプション認証 | `claude auth login`（API キー不要） |
| **CI/CD** | API キー認証 | `ANTHROPIC_API_KEY` 環境変数 |

### ローカル環境（サブスクリプション優先）

- Claude Pro/Max サブスクリプションで `claude` コマンドにログイン
- **重要**: `ANTHROPIC_API_KEY` を設定しない（設定すると API キーが優先される）
- 使用量はサブスクリプションの制限内でカウント

### CI/CD 環境（API キー必須）

- GitHub Actions などの自動化環境では `claude auth login` が使用できない
- `ANTHROPIC_API_KEY` 環境変数を設定して認証
- API 使用量は従量課金

## 確認項目

### 1. GitHub Secrets の確認

```
Repository Settings > Secrets and variables > Actions
```

| Secret 名 | 説明 | CI/CD で必要 |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API キー | ✅ 統合テスト実行時のみ |

### 2. pytest マーカー設定

```toml
# pyproject.toml

[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests (require Claude API)",
]
```

### 3. GitHub Actions ワークフロー（推奨設定）

```yaml
# .github/workflows/test.yml
name: Test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run unit tests (no API key required)
        run: uv run pytest -m "not integration" --cov

  integration-tests:
    runs-on: ubuntu-latest
    # 統合テストはメインブランチへのプッシュ時のみ実行
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        run: pip install uv

      - name: Install Claude Code CLI
        run: curl -fsSL https://claude.ai/install.sh | bash

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run integration tests
        if: env.ANTHROPIC_API_KEY != ''
        run: uv run pytest -m "integration" -v
```

### 4. 統合テストの条件分岐

```python
# tests/news/integration/conftest.py

import os
import subprocess
import pytest


def is_ci_environment() -> bool:
    """CI 環境かどうかを判定。"""
    return os.environ.get("CI") == "true"


def has_api_key() -> bool:
    """ANTHROPIC_API_KEY が設定されているか確認。"""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def check_subscription_auth() -> tuple[bool, str]:
    """サブスクリプション認証状態を確認。"""
    try:
        result = subprocess.run(
            ["claude", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, "Authenticated via subscription"
        return False, result.stderr
    except FileNotFoundError:
        return False, "Claude CLI not installed"
    except Exception as e:
        return False, str(e)


@pytest.fixture(scope="session", autouse=True)
def verify_claude_auth():
    """Claude 認証を検証（環境に応じて方式を切り替え）。

    - ローカル: サブスクリプション認証（ANTHROPIC_API_KEY 不要）
    - CI/CD: API キー認証（ANTHROPIC_API_KEY 必須）
    """
    if is_ci_environment():
        # CI 環境: API キーが必要
        if not has_api_key():
            pytest.skip(
                "ANTHROPIC_API_KEY not set in CI environment. "
                "Set the secret to run integration tests."
            )
        print("\n✓ Using API key auth (CI environment)")
    else:
        # ローカル環境: サブスクリプション認証を推奨
        if has_api_key():
            print(
                "\n⚠ ANTHROPIC_API_KEY is set. "
                "API usage will be charged instead of subscription."
            )
        else:
            is_auth, message = check_subscription_auth()
            if not is_auth:
                pytest.skip(
                    f"Claude subscription auth required: {message}. "
                    "Run 'claude auth login' to authenticate."
                )
            print(f"\n✓ Using subscription auth: {message}")
```

### 5. ローカル開発時の注意事項

```bash
# ローカル開発時はサブスクリプション認証を使用
# ANTHROPIC_API_KEY を設定しないこと

# 確認
echo $ANTHROPIC_API_KEY  # 空であること

# 設定されている場合は削除
unset ANTHROPIC_API_KEY

# サブスクリプションでログイン
claude auth login
```

## 受け入れ条件

- [ ] ローカル環境でサブスクリプション認証が動作する
- [ ] ローカル環境で `ANTHROPIC_API_KEY` が不要であることを確認
- [ ] CI/CD で `ANTHROPIC_API_KEY` がない場合、統合テストがスキップされる
- [ ] CI/CD で `ANTHROPIC_API_KEY` がある場合、統合テストが実行される
- [ ] 単体テストは API キーなしで成功する
- [ ] GitHub Actions が成功する

## セキュリティ考慮事項

- API キーは GitHub Secrets に保存し、コードにハードコードしない
- ログに API キーを出力しない
- fork からの PR では Secrets にアクセスできないことを考慮
- ローカル開発時は API キーを使用せず、サブスクリプション認証を推奨

## 参照

- [Using Claude Code with your Pro or Max plan](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)
- [GitHub Actions Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Anthropic API Keys](https://console.anthropic.com/settings/keys)
