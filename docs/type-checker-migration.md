# 型チェッカー移行ガイド

このドキュメントは、将来の型チェッカー移行（pyright → ty など）時に修正が必要な箇所を明確化したものです。

## 現在の構成

| 項目 | 値 |
|------|-----|
| 型チェッカー | pyright |
| バージョン | >= 1.1.403 |
| 実行コマンド | `make typecheck` / `uv run pyright` |
| 設定ファイル | `pyproject.toml` `[tool.pyright]` セクション |

## 変更が必要なファイル一覧

### 1. pyproject.toml

**設定セクション（行91-134）**

```toml
[tool.pyright]
include = ["src", "tests"]
exclude = [".venv", "**/__pycache__", "build", "dist"]
pythonVersion = "3.12"  # 最小サポートバージョン
typeCheckingMode = "basic"
# ... 各種レポート設定
```

→ ty の設定形式に変更が必要。設定オプションの互換性は ty 安定版リリース時に確認すること。

**依存関係（行155-156）**

```toml
[dependency-groups]
dev = [
    "pyright>=1.1.403",  # ← この行を ty に変更
    ...
]
```

### 2. Makefile

**行17（ヘルプ）**

```makefile
typecheck    - 型チェック（pyright）
```

→ `typecheck    - 型チェック（ty）`

**行60-61（typecheck ターゲット）**

```makefile
typecheck:
	uv run pyright
```

→ `uv run ty check`（コマンド形式は ty のドキュメントを確認）

### 3. CLAUDE.md

**行10（ヘッダー）**

```markdown
**Python 3.12+** | uv | Ruff | pyright | pytest + Hypothesis | ...
```

→ `pyright` を `ty` に変更

### 4. docs/development-process.md

**行285-290（型チェックセクション）**

```markdown
### 型チェック

- **pyright**
    - 高速で厳密な型チェック
    - VS Code (Pylance) と同じエンジンで一貫した開発体験
    - 設定ファイル: `pyproject.toml`
```

→ ty の特徴に合わせて説明を更新

### 5. .claude/agents/quality-checker.md

**行249-256（pyright エラー表）**

```markdown
### pyright エラー

| コード | 説明 | 対処法 |
|--------|------|--------|
| reportMissingTypeStubs | 型スタブなし | ... |
| reportIncompatibleMethodOverride | オーバーライド不一致 | ... |
| reportArgumentType | 引数型不一致 | ... |
| reportReturnType | 戻り値型不一致 | ... |
```

→ ty のエラーコード体系に合わせて更新

## 移行チェックリスト

- [ ] ty 安定版リリースの確認（2026年予定）
- [ ] ty の設定オプションと pyright との互換性を確認
- [ ] 上記5ファイルを更新
- [ ] `make check-all` で動作確認
- [ ] CI/CD パイプラインの動作確認

## 参考リンク

- [ty GitHub リポジトリ](https://github.com/astral-sh/ty)
- [Astral 公式ブログ](https://astral.sh/blog)
