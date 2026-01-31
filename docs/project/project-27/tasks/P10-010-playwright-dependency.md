# P10-010: playwright依存関係追加

## 概要

PlaywrightをプロジェクトのオプショナルDependencyとして追加する。

## 背景

trafilaturaはJavaScript動的レンダリングに対応していない。Playwrightを使用してJS実行後のDOMから本文を抽出する。

## 変更内容

### 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| `pyproject.toml` | playwright依存関係追加（optional） |

### 実装詳細

```toml
# pyproject.toml

[project.optional-dependencies]
playwright = [
    "playwright>=1.40.0",
]

# または既存のoptionalに追加
all = [
    # 既存の依存関係
    "playwright>=1.40.0",
]
```

### インストール手順

```bash
# 依存関係追加
uv add --optional playwright playwright

# ブラウザバイナリインストール
uv run playwright install chromium
```

### 設定ファイル追加

```yaml
# data/config/news-collection-config.yaml

extraction:
  # ...

  # Playwrightフォールバック設定
  playwright_fallback:
    enabled: true
    browser: "chromium"  # chromium, firefox, webkit
    headless: true
    timeout_seconds: 30
```

## 受け入れ条件

- [ ] `pyproject.toml` にplaywrightが追加される
- [ ] `uv sync --all-extras` でインストールできる
- [ ] `playwright install chromium` が正常に完了する
- [ ] CI/CD環境でのインストール手順がドキュメント化される

## CI/CD対応

```yaml
# .github/workflows/test.yml

- name: Install Playwright browsers
  run: uv run playwright install chromium --with-deps
```

## 依存関係

- 依存先: P10-002
- ブロック: P10-011

## 見積もり

- 作業時間: 15分
- 複雑度: 低
