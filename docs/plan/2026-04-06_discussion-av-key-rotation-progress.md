# 議論メモ: AV APIキーローテーション + 優先キュー - プロジェクト進捗

**日付**: 2026-04-06
**議論ID**: disc-2026-04-06-av-key-rotation-progress
**参加**: ユーザー + AI

## 背景・コンテキスト

EarningsPipeline Phase 2 の Alpha Vantage API について以下の課題があった:
1. フリーティア制限: 1キー25リクエスト/日で銘柄数に対して不足
2. 失敗銘柄の取りこぼし: API制限で取得できなかった銘柄が翌日も後回しにされる

## 議論のサマリー

- 複数キー対応の方式を検討し、「使い切り方式（1キーを25リクエスト使い切ってから次へ）」に決定
- 4キー構成で合計100リクエスト/日に拡張
- 失敗銘柄のpriority_boost=10による優先蓄積を決定
- `/plan-project` スキルでProject #110・Issue #3888-#3893を登録
- worktree `feature/prj110` を `/Users/yukihata/Desktop/.worktrees/quants/feature-prj110` に作成

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-06-av-001 | KeyRotator（使い切り方式）採用: 1キー→25回使い切り→次キー。4キー×25=100リクエスト/日 | フリーティア上限拡大のため |
| dec-2026-04-06-av-002 | priority_boost=10で失敗銘柄を翌日優先化: reset_failed()でpriority+10 | 翌日も後回しにされる問題を解決 |
| dec-2026-04-06-av-003 | DI注入パターン採用: Pipeline→Client→Session にkey_rotator=Noneで渡す | frozen dataclassのAlphaVantageConfigには混ぜない |
| dec-2026-04-06-av-004 | GitHub Project #110 / Issue #3888-#3893 / worktree feature/prj110 で3 Wave構成 | Wave依存関係に基づく並行開発計画 |

## 実装計画（Wave構成）

| Wave | Issue | タイトル | 状態 |
|------|-------|---------|------|
| W1 | #3888 | KeyRotator クラスの新規作成 | 未着手 |
| W1 | #3889 | CollectionQueue に priority_boost 追加 | 未着手 |
| W2 | #3890 | Session/Client に KeyRotator 注入 | 未着手 |
| W2 | #3891 | KeyRotator テスト拡充 | 未着手 |
| W3 | #3892 | EarningsPipeline と CLI の統合 | 未着手 |
| W3 | #3893 | 品質チェックと E2E 検証 | 未着手 |

## アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| act-2026-04-06-av-001 | Wave 1: #3888 + #3889 を並行実装 | 高 |
| act-2026-04-06-av-002 | Wave 2: #3890 + #3891 を並行実装（Wave1完了後） | 高 |
| act-2026-04-06-av-003 | Wave 3: #3892 → #3893 を順次実装 | 高 |
| act-2026-04-06-av-004 | .envに ALPHA_VANTAGE_API_KEYS=key1,key2,key3,key4 を追加 | 高 |

## 次回の議論トピック

- Wave 1 実装完了後の進捗確認
- APIキー4本の実際の設定確認

## 参考情報

- GitHub Project: [#110](https://github.com/users/YH-05/projects/110)
- 対象パッケージ: `src/market/alphavantage/`, `src/market/pipeline/`
- worktree パス: `/Users/yukihata/Desktop/.worktrees/quants/feature-prj110`
- 実装計画ドキュメント: `docs/project/project-104/project.md`
