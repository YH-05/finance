# P7-004: Phase 7 CLI テスト作成

## 概要

Phase 7 で作成した CLI のテストを作成する。

## フェーズ

Phase 7: CLI

## 依存タスク

- P7-003: CLI ログ設定

## 成果物

- `tests/news/unit/test_cli.py`（新規作成）

## テスト内容

```python
import subprocess
import sys

class TestCLI:
    def test_正常系_ヘルプが表示される(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "news.scripts.finance_news_workflow", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "金融ニュース収集ワークフロー" in result.stdout

    def test_正常系_statusオプションがパースされる(self) -> None:
        ...

    def test_正常系_dry_runオプションがパースされる(self) -> None:
        ...

    def test_正常系_max_articlesオプションがパースされる(self) -> None:
        ...

    def test_正常系_verboseオプションがパースされる(self) -> None:
        ...

    def test_正常系_configオプションがパースされる(self) -> None:
        ...

    def test_異常系_存在しない設定ファイルでエラー(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "news.scripts.finance_news_workflow",
             "--config", "nonexistent.yaml"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1

class TestParseArgs:
    def test_正常系_デフォルト値が設定される(self) -> None:
        ...

    def test_正常系_statusがリストにパースされる(self) -> None:
        ...
```

## 受け入れ条件

- [ ] CLI の全オプションがテストされている
- [ ] subprocess で実際に CLI を起動してテスト
- [ ] parse_args 関数の単体テストも含む
- [ ] エラー時の終了コードテストが含まれている
- [ ] `make test` 成功
- [ ] テスト命名規則に従っている

## 参照

- `.claude/rules/testing-strategy.md`: テスト命名規則
