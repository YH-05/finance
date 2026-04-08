# 議論メモ: Project-105 セットアップ（NSE/Pipeline改善タスク統合）

**日付**: 2026-04-08
**議論ID**: disc-2026-04-08-project-105-setup
**参加**: ユーザー + AI

## 背景・コンテキスト

PR #3878（NSE実装）以降、5件のコミット（ca94793, dba668a, 62016ae, 93a4358, 22484bf）が
PRなしでmainに直接プッシュされていた。すでにorigin/mainに同期済みで巻き戻し不要だが、
今後は適切なPRワークフローで開発するため、未完了の改善タスク6件を1プロジェクトに統合した。

## 議論のサマリー

1. **NSE実装状況確認**: CorporateCollector / IndicesCollector / QuoteCollector / StockListCollector が実装済み。株主構成エンドポイントのみ未実装。
2. **日本IP問題**: NSEホームページ（www.nseindia.com）はAkamai WAFが日本IPを403ブロック。ただしJSON APIエンドポイントはCookieなしで直接アクセス可能（RELIANCE実機テスト済み）。
3. **非PR化コミットへの対応**: 遡ってPR作成は不可のため、新規プロジェクトとして整理する方針を採用。
4. **Project-105作成**: GitHub Project #111として6タスク（Wave1: 4件並行、Wave2: 1件、Wave3: 1件）を登録。
5. **Worktree作成**: feature/prj111ブランチ + worktree を作成完了。

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| dec-2026-04-08-001 | PR #3878以降5件の直接mainコミットは遡ってPR化しない | origin/mainに同期済みで技術的に不可 |
| dec-2026-04-08-002 | 未完了6タスクをProject-105としてGitHub Project #111に統合。Issue #3895-#3900 | 今後はPRワークフローで品質担保 |
| dec-2026-04-08-003 | feature/prj111ブランチ + worktree（.worktrees/quants/feature-prj111）作成完了 | GitHub Project#111番号に合わせた命名 |
| dec-2026-04-08-004 | NSE shareholding API実装前に /site-investigator で事前調査。Issue #3895にコメント追記済み | エンドポイント未確定リスクの事前排除 |

## アクションアイテム

| ID | 内容 | 優先度 | 状態 |
|----|------|--------|------|
| act-2026-04-08-001 | feature/prj111 worktreeでWave1（#3895/#3896/#3897/#3898）並行実装開始 | 高 | pending |
| act-2026-04-08-002 | Issue #3895: /site-investigator でNSE shareholding APIエンドポイント事前調査 | 高 | pending |
| act-2026-04-08-003 | Issue #3896: SEC operating_cashflow Noneフォールバック実装 | 中 | pending |
| act-2026-04-08-004 | Issue #3897: FRED launchd plist作成（06:00実行） | 中 | pending |
| act-2026-04-08-005 | Issue #3898: BSE 日本IPワークアラウンド実装 | 中 | pending |

## Wave構成

```
Wave 1（並行開発可能）
├── #3895 NSE 株主構成エンドポイント追加  [HIGH]  → Wave3#3900の前提
├── #3896 SEC cashflow フォールバック     [MEDIUM]
├── #3897 FRED launchd plist              [MEDIUM] → Wave2#3899の前提
└── #3898 BSE 日本IPワークアラウンド     [MEDIUM]

Wave 2（#3897完了後）
└── #3899 ETF.com 自動化 launchd統合    [LOW]

Wave 3（#3895完了後）
└── #3900 ASEAN カバレッジ統合設計      [MEDIUM]（設計書のみ）
```

## 次回の議論トピック

- Wave1実装完了後の各タスク結果確認
- NSE shareholding API エンドポイント調査結果（Issue #3895）
- ASEAN統合設計の enum 命名（MarketExchange）戦略の詳細化

## 参考情報

- **GitHub Project**: https://github.com/users/YH-05/projects/111
- **Issue #3895**: https://github.com/YH-05/quants/issues/3895（site-investigator調査手順コメント済み）
- **Worktree**: /Users/yukihata/Desktop/.worktrees/quants/feature-prj111
- **計画書**: docs/plan/2026-04-08_project-105-nse-pipeline-improvements.md
- **プロジェクト追跡**: docs/project/project-105/project.md
