# Project 7: エージェント開発

**GitHub Project**: [#7 エージェント開発](https://github.com/users/YH-05/projects/7)
**作成日**: 2026-01-13
**最終更新**: 2026-01-17

## 概要

エージェントの新規追加・機能改善・パフォーマンス最適化を行うプロジェクト。

## サブプロジェクト一覧

| Issue | タイトル | ステータス | 詳細 |
|-------|---------|-----------|------|
| #47 | 既存リサーチ系エージェントの調査 | 完了 | [調査レポート](./research-agent-survey.md) |
| #48 | 画像収集の要件定義 | 完了 | [要件定義書](./image-collection-requirements.md) |
| #49 | 画像収集エージェントの定義ファイル作成 | 完了 | `.claude/agents/research-image-collector.md` |
| #50 | agents.md への登録と /index 更新 | 完了 | - |
| #51 | エージェント使用ガイドの作成 | 完了 | `docs/image-collector-guide.md` |
| #254 | 金融ニュース収集エージェント群の機能改善 | 完了 | [詳細](#254-金融ニュース収集エージェント群の機能改善) |
| #255 | サブエージェントごとのGitHub Issue登録機能 | 完了 | [詳細](#255-サブエージェントごとのgithub-issue登録機能) |
| #269 | test-writerエージェントの最適化 | 完了 | [詳細](#269-test-writerエージェントの最適化) |

---

## サブプロジェクト詳細

### #47-51: リサーチエージェントの追加

#### 背景

note記事用に画像を収集するエージェントを追加したい。特定サイトからデータを収集する機能が必要。

#### 成果物

| 種類 | 名前 | 説明 |
| ---- | ---- | ---- |
| エージェント | research-image-collector | note記事用の画像収集エージェント |
| ドキュメント | エージェント使用ガイド | 使い方と設定方法 |

#### タスク進捗

- [x] #47: 既存リサーチ系エージェントの調査 → [調査レポート](./research-agent-survey.md)
- [x] #48: 画像収集の要件定義 → [要件定義書](./image-collection-requirements.md)
- [x] #49: 画像収集エージェントの定義ファイル作成 → `.claude/agents/research-image-collector.md`
- [x] #50: agents.md への登録と /index 更新
- [x] #51: エージェント使用ガイドの作成 → `docs/image-collector-guide.md`

---

### #254: 金融ニュース収集エージェント群の機能改善

#### 概要

金融ニュース収集エージェント群（finance-news-*）のリファクタリングと機能改善。

#### 対象エージェント

- `finance-news-orchestrator.md`
- `finance-news-index.md`
- `finance-news-stock.md`
- `finance-news-sector.md`
- `finance-news-macro.md`
- `finance-news-ai.md`

#### 受け入れ条件

- [x] 並列実行制御の改善
- [x] エラーハンドリングの強化
- [x] 一時ファイル管理の最適化

---

### #255: サブエージェントごとのGitHub Issue登録機能

#### 概要

サブエージェントが処理したニュース記事ごとにGitHub Issueを自動登録する機能を実装。

#### 機能要件

- テーマ別エージェントがIssue作成を実行
- 重複Issue防止のチェック機能
- GitHub Project への自動追加

#### 受け入れ条件

- [x] テーマ別エージェントでIssue作成ロジック実装
- [x] 既存Issue重複チェック機能
- [x] 動作検証

---

### #269: test-writerエージェントの最適化

#### 概要

test-writerエージェントのテスト実装に時間がかかりすぎている問題を、サブエージェント分割による並列化で解決する。

#### 現状の問題点

- `test-writer`が全責務を担当（unit + property + integration + TDDサイクル）
- 全処理が順序的に実行され、並列化の余地がない
- 単機能あたり1-2時間のテスト作成時間

#### 提案アーキテクチャ

```
test-orchestrator (オーケストレーター)
    │
    ├── test-planner (Phase 1: 設計)
    │       ↓
    ├── test-unit-writer ─────┐
    │                         ├── (Phase 2: 並列実行)
    ├── test-property-writer ─┘
    │       ↓
    └── test-integration-writer (Phase 3: 依存実行)
```

#### 各サブエージェントの責務

| エージェント | 役割 | 入力 | 出力 |
|-------------|------|------|------|
| test-orchestrator | 全体調整・結果集約 | テスト対象モジュール | 統合レポート |
| test-planner | テスト設計・TODO作成 | 対象コード | `.tmp/test-plan-*.json` |
| test-unit-writer | 単体テスト（TDD） | 設計JSON | `tests/unit/test_*.py` |
| test-property-writer | プロパティテスト | 設計JSON | `tests/property/test_*_property.py` |
| test-integration-writer | 統合テスト | 設計JSON + 単体結果 | `tests/integration/test_*.py` |

#### 処理フロー（最適化後）

```
Phase 1: 設計 (順序)
┌─────────────────────────────────┐
│  test-planner                   │
│  - コード分析                    │
│  - TODOリスト作成                │
│  - テスト設計出力                │
└─────────────────────────────────┘
              ↓

Phase 2: 並列テスト作成
┌─────────────────────┐  ┌─────────────────────┐
│  test-unit-writer   │  │ test-property-writer │
│  - 単体テスト作成    │  │ - プロパティテスト   │
│  - Red→Green→Refactor│ │ - Hypothesis使用     │
└─────────────────────┘  └─────────────────────┘
              ↓ (両方完了後)

Phase 3: 統合テスト (順序)
┌─────────────────────────────────┐
│  test-integration-writer        │
│  - 統合テスト作成               │
│  - コンポーネント連携テスト      │
└─────────────────────────────────┘
              ↓

Phase 4: 集約 (順序)
┌─────────────────────────────────┐
│  test-orchestrator              │
│  - 結果集約                     │
│  - 最終レポート出力             │
│  - カバレッジ確認               │
└─────────────────────────────────┘
```

#### 期待される効果

| 項目 | 現状 | 最適化後 | 改善率 |
|------|------|----------|--------|
| 単体+プロパティ | 順序実行 | 並列実行 | 50%削減 |
| エージェント専門性 | 汎用 | 特化型 | 品質向上 |
| 全体実行時間 | 100% | 60-70% | 30-40%削減 |

#### 実装ファイル

```
.claude/agents/
├── test-writer.md              # 既存（後方互換のため維持）
├── test-orchestrator.md        # 新規: オーケストレーター
├── test-planner.md             # 新規: 設計担当
├── test-unit-writer.md         # 新規: 単体テスト担当
├── test-property-writer.md     # 新規: プロパティテスト担当
└── test-integration-writer.md  # 新規: 統合テスト担当

.claude/commands/
└── write-tests.md              # 更新: test-orchestratorを呼び出すように変更
```

#### 中間ファイルフォーマット

**test-plannerの出力**: `.tmp/test-plan-{timestamp}.json`

```json
{
  "session_id": "test-plan-20260117-120000",
  "target": {
    "module": "src/finance/db/sqlite_client.py",
    "functions": ["execute", "fetch_all", "transaction"]
  },
  "test_cases": {
    "unit": [
      {"name": "test_正常系_execute成功", "priority": "high"},
      {"name": "test_異常系_接続エラー", "priority": "high"}
    ],
    "property": [
      {"name": "test_prop_クエリ結果の一貫性", "strategy": "st.text()"}
    ],
    "integration": [
      {"name": "test_統合_トランザクション完了", "depends_on": ["unit"]}
    ]
  }
}
```

#### 検証方法

1. 新規モジュールに対してテスト作成を実行
2. 従来のtest-writerと新しいtest-orchestratorの実行時間を比較
3. 生成されたテストの品質（カバレッジ、テストケース数）を確認
4. `make test` で全テストがパスすることを確認

#### 注意事項

- TDDの原則（Red→Green→Refactor）は各サブエージェント内で維持
- 既存のtest-writerは後方互換のため残す
- 並列実行の制御はコマンド層（write-tests.md）で行う
- finance-news-orchestratorパターンを参考に実装

#### 受け入れ条件

- [x] test-orchestrator.md を作成
- [x] test-planner.md を作成
- [x] test-unit-writer.md を作成
- [x] test-property-writer.md を作成
- [x] test-integration-writer.md を作成
- [x] write-tests.md を更新
- [x] 新規モジュールでテスト作成を実行し、実行時間を計測
- [x] 従来のtest-writerとの比較検証

---

## 参考資料

- [調査レポート: 既存リサーチ系エージェント](./research-agent-survey.md)
- [要件定義: 画像収集](./image-collection-requirements.md)
- [参考実装: finance-news-orchestrator](../../.claude/agents/finance-news-orchestrator.md)
