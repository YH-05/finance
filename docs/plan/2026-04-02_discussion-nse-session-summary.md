# 議論メモ: 2026-04-02 NSE セッションまとめ

**日付**: 2026-04-02
**議論ID**: disc-2026-04-02-nse-session-summary
**参加**: ユーザー + AI

## セッション概要

NSE モジュールの PR マージから実機テスト、バグ修正、NAS シンボリックリンク修正までを一貫して実施したセッション。

## 実施内容

### 1. PR #3878 マージ + Worktree クリーンアップ
- feat(nse): NSE モジュール実装 Wave0-6 (#3870-#3877)
- 46ファイル、+11,817行。squash merge。
- worktree feature-prj106 削除、ブランチ削除、全8 Issue Done。

### 2. 実機テスト: RELIANCE Industries
- Quote / Financial Results / Search / Event Calendar / Market Status を取得
- CSV出力: `data/market/nse/` (→ NAS)

### 3. バグ修正 3件
- **brotli 依存追加**: NSE API が Brotli 圧縮を強制返却
- **Cookie 取得フォールバック**: 日本 IP から homepage が 403
- **Financial Results symbol 補完**: API レスポンスに symbol が含まれない

### 4. NAS シンボリックリンク修正
- 原因: `data/` 内リンクが `/Volumes/personal_folder/Quants/data/` を指していたが、正しくは `/Volumes/personal_folder/data/`
- 修正: リンク11個のパスから `Quants/` を除去、NAS側に不足ディレクトリ9個を作成

### 5. 持ち株比率の取得（未完了）
- yfinance で取得を試みたが、**NSE API で完結させるべき**とのフィードバック
- NSE API の shareholding pattern エンドポイントを要再調査

## 決定事項

| ID | 内容 | ステータス |
|----|------|-----------|
| dec-2026-04-02-006 | NSE モジュール Wave0-6 全実装完了 | implemented |
| dec-2026-04-02-007 | brotli>=1.2.0 追加 | implemented |
| dec-2026-04-02-008 | _ensure_cookies フォールバック | implemented |
| dec-2026-04-02-009 | parse_financial_results symbol 補完 | implemented |
| dec-2026-04-02-010 | NAS シンボリックリンク修正 | implemented |

## アクションアイテム

| ID | 内容 | 優先度 | ステータス |
|----|------|--------|-----------|
| act-2026-04-02-012 | バグ修正3件 + テスト4件をコミット・PR | 高 | pending |
| act-2026-04-02-013 | NSE API 持ち株比率エンドポイント再調査 | 高 | pending |
| act-2026-04-02-010 | BSE BhavcopyCollector CSV 対応 | 中 | pending |
| act-2026-04-02-011 | ASEAN カバレッジとの統合 | 中 | pending |

## フィードバック

- **NSE データは yfinance で補完しない**。NSE API で取れるはずのデータは NSE API で完結させる。エンドポイント調査を徹底してから実装すること。

## 関連ドキュメント

- `docs/plan/2026-04-02_discussion-bse-nse-investigation.md`
- `docs/plan/2026-04-02_discussion-nse-module-planning.md`
- `docs/plan/2026-04-02_discussion-nse-implementation-complete.md`
- `docs/plan/2026-04-02_discussion-nse-realapi-test-bugfix.md`
