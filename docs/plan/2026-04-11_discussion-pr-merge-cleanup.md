# 議論メモ: PR #3913/#3924 マージ・worktreeクリーンアップ

**日付**: 2026-04-11
**議論ID**: disc-2026-04-11-pr-merge-cleanup
**参加**: ユーザー + AI

## 背景・コンテキスト

Project 105 (NSE/ASEAN統合) の Wave2・Wave3 を main にマージし、
開発 worktree を全削除してクリーンな状態に戻した。

## 作業サマリー

### PR #3913: [Wave2] ETF.com CLI エントリポイントと launchd plist を追加

- **Issue**: #3899
- **マージ日時**: 2026-04-10T23:50:13Z
- **変更内容**: 8ファイル, +1516行
  - `src/market/etfcom/cli.py` / `__main__.py`
  - `tests/market/etfcom/unit/test_cli.py`
  - `scripts/com.quants.etfcom-*.plist` (daily/weekly/monthly)
  - `data/config/etfcom_tickers.json`

#### CI修正（マージ前に対応）

| 問題 | 原因 | 対処 |
|------|------|------|
| Lint: trailing-whitespace | `analyst/` 配下 138ファイルの末尾空白 | pre-commit で自動修正・コミット |
| Lint: bandit B405 | `scripts/nse_parse_xbrl.py` の `xml.etree.ElementTree` | `pyproject.toml` の `[tool.bandit]` exclude_dirs に `scripts/` を追加 |
| Lint: pip-audit 脆弱性 | `cryptography 46.0.6` (CVE-2026-39892), `marimo 0.19.6` (CVE-2026-39987) | `cryptography→46.0.7`, `marimo→0.23.1` にアップデート |

### PR #3924: [Wave3] market_common パッケージ新設・NSE/BSE enum 追加

- **Issue**: #3900
- **マージ日時**: 2026-04-11T00:18:30Z
- **状態**: 着手時点で既にマージ済み

### worktreeクリーンアップ

| ブランチ | worktree | ローカル | リモート |
|---------|----------|---------|---------|
| `feature/issue-3899` | 削除済み | 削除済み | 削除済み |
| `feature/issue-3900` | 削除済み（実行前に削除済み） | 削除済み | 削除済み |

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-11-001 | `scripts/` を bandit 除外ディレクトリに追加 | `scripts/` は本番コードではなく運用スクリプト群のため。nse_parse_xbrl.py の B405 誤検知を解消 |
| dec-2026-04-11-002 | `cryptography→46.0.7`, `marimo→0.23.1` に更新 | pip-audit CVE-2026-39892/CVE-2026-39987 対応。PRマージ前に feature ブランチで修正 |

## 現在の状態

- `main` ブランチのみ（worktree なし）
- Wave2・Wave3 完了
- 次は Wave4 以降（Issue #3900 の残タスクまたは次の Issue）

## 次回の議論トピック

- Project 105 の Wave4 以降の計画確認
- `market_common` パッケージへの移行状況確認
