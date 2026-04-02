# 議論メモ: NSE データ取得モジュール実装計画策定

**日付**: 2026-04-02
**議論ID**: disc-2026-04-02-nse-module-planning
**参加**: ユーザー + AI

## 背景・コンテキスト

BSE API が日本 IP から Akamai WAF にブロックされているため、NSE（National Stock Exchange of India）データ取得モジュールを `src/market/nse/` に新規実装する計画を策定した。設計書（`docs/project/project-102/original-plan.md`）に基づき `/plan-project` ワークフローを全フェーズ実行。

## 議論のサマリー

### Phase 0: 方向確認
- プロジェクトタイプ: package（`src/market/nse/`）
- 目的: BSE モジュールをベースに NSE モジュールを新規作成
- Wave 分割: 設計書の 6 Phase 構成をベースに 7 Wave（Wave 0 を追加）

### Phase 1: リサーチ（project-researcher）
BSE モジュールの完全な実装パターンを調査。6 層構造（session/types/errors/constants/parsers/collectors）、CollectorMixin + DataCollector ABC 多重継承、frozen dataclass + `__post_init__` バリデーションが再利用可能であることを確認。

### Phase 2: 計画策定（project-planner）
7 Wave 構成・30 ファイル（ソース 16 + テスト 14）の実装計画を策定。Wave 2/3 の並行開発で実質 14-17 時間。

### Phase 3: タスク分解（project-decomposer）
8 タスクに分解。クリティカルパス: task-1 → task-3 → task-4 → task-6 → task-7 → task-8

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-02-001 | NSE モジュールを BSE ベースで src/market/nse/ に新規作成 | 7 Wave・30 ファイル構成 |
| dec-2026-04-02-002 | 403 時 Cookie リフレッシュ戦略: `_handle_response()` で NseCookieError → `get_with_retry()` でキャッチ＋リフレッシュ | BSE パターンとの一貫性を優先 |
| dec-2026-04-02-003 | RetryConfig を `market/retry.py` に共通化（BSE/NSE 両参照） | Wave 0 task-1（#3870）で実装 |
| dec-2026-04-02-004 | Cookie 有効期限: 固定値 300秒 + `time.monotonic()` ベース | シンプルで予測可能な実装 |
| dec-2026-04-02-005 | FINANCIAL_FIELD_MAP は Wave 0 で API レスポンス事前調査して確定 | Wave 0 task-2（#3871）で実施 |

## アクションアイテム

| ID | 内容 | 優先度 | GitHub Issue |
|----|------|--------|------|
| act-2026-04-02-001 | [Wave0] RetryConfig 共通化 | 高 | [#3870](https://github.com/YH-05/quants/issues/3870) |
| act-2026-04-02-002 | [Wave0] FINANCIAL_FIELD_MAP 事前調査 | 高 | [#3871](https://github.com/YH-05/quants/issues/3871) |
| act-2026-04-02-003 | [Wave1] errors/constants/types + テスト | 高 | [#3872](https://github.com/YH-05/quants/issues/3872) |
| act-2026-04-02-004 | [Wave2] NseSession + テスト | 中 | [#3873](https://github.com/YH-05/quants/issues/3873) |
| act-2026-04-02-005 | [Wave3] parsers.py + テスト | 中 | [#3874](https://github.com/YH-05/quants/issues/3874) |
| act-2026-04-02-006 | [Wave4] collectors 一括 | 中 | [#3875](https://github.com/YH-05/quants/issues/3875) |
| act-2026-04-02-007 | [Wave5] パッケージ統合 | 中 | [#3876](https://github.com/YH-05/quants/issues/3876) |
| act-2026-04-02-008 | [Wave6] 統合テスト | 低 | [#3877](https://github.com/YH-05/quants/issues/3877) |

## 成果物

- **GitHub Project**: [#106](https://github.com/users/YH-05/projects/106)
- **計画書**: `docs/project/project-102/project.md`
- **設計書**: `docs/project/project-102/original-plan.md`
- **Worktree**: `feature/prj106` → `/Users/yukihata/Desktop/.worktrees/quants/feature-prj106`

## 次のステップ

1. Worktree で Wave 0 から実装開始: `cd ~/.worktrees/quants/feature-prj106 && claude`
2. 並列開発計画: `/plan-worktrees 106`
3. Wave 0 は #3870 と #3871 を並行実装可能
