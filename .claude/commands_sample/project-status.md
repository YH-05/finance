# プロジェクト状態確認・更新コマンド

## 概要

プロジェクト「prj-note」の現在の状態を確認し、README.mdとCLAUDE.mdを最新状態に自動更新します。

## 主な機能

1. **状態確認**: プロジェクトの現在の進捗・統計を分析
2. **自動更新**: README.mdとCLAUDE.mdを最新情報で更新
3. **同期保持**: docs/project/や.claude/の変更を主要ドキュメントに反映

## 確認・更新内容

### 1. プロジェクト概要

-   README.md と CLAUDE.md からプロジェクトの基本情報を表示
-   開始日、最終更新日、カテゴリ情報

### 2. 実装進捗

-   完了済みステップ（Step 1-7, Phase 1-6）
-   次のステップ（Step 8-10）
-   進捗率（リサーチ: 100%, 執筆: 20%, 公開: 0%）

### 3. コンポーネント統計

-   エージェント: 13 実装済み、6 計画中（合計 19）
-   コマンド: 4 実装済み、1 計画中（合計 5）
-   スキーマ: 10 実装済み
-   検証記事: 2 実装済み、2 計画中

### 4. ファイル構造

articles/ フォルダ内の記事一覧と状態を確認：

```bash
# 記事フォルダ構造の確認
ls -la articles/
```

各記事フォルダの状態確認：

-   01_research/ - リサーチデータの有無
-   02_edit/ - 執筆データの有無
-   03_published/ - 公開データの有無

### 4.1. 記事別リサーチ進捗（workflow フィールド）

各記事の `article-meta.json` から `workflow` フィールドを読み取り、詳細な進捗を表示：

```markdown
## 📊 記事別リサーチ進捗

### unsolved_001_db-cooper

| Phase | 処理 | 状態 | 出力ファイル |
|-------|------|------|-------------|
| 1 | クエリ生成 | ✅ done | queries.json |
| 2 | 情報収集 | ✅ done | raw-data.json |
| 3 | 情報源統合 | ✅ done | sources.json |
| 4 | 主張抽出 | ✅ done | claims.json |
| 5 | 論点整理 | ✅ done (2回) | analysis.json |
| 6 | 採用判断・FC | ✅ done | decisions.json, fact-checks.json |
| 7 | 可視化 | ⏳ pending | - |

**リサーチ進捗**: 85% (6/7 フェーズ完了)
**執筆進捗**: 0% (0/3 フェーズ完了)
**公開進捗**: 0% (0/2 フェーズ完了)

### unsolved_002_zodiac-killer

| Phase | 処理 | 状態 |
|-------|------|------|
| 1-7 | リサーチ | ⏳ 未着手 |
| 8 | 執筆 | ⏳ 未着手 |
| 9 | 公開 | ⏳ 未着手 |

**全体進捗**: 0%
```

#### workflow フィールドの読み取り方法

```javascript
// article-meta.json から workflow を読み取り
const meta = JSON.parse(
    fs.readFileSync(`articles/${articleId}/article-meta.json`, "utf-8")
);
const workflow = meta.workflow;

// リサーチ進捗を計算
const researchFields = [
    "queries",
    "raw_data",
    "sources",
    "claims",
    "analysis",
    "fact_checks",
    "decisions",
    "visualize",
];
const completedResearch = researchFields.filter(
    (f) => workflow.research[f] === "done"
).length;
const researchProgress = Math.round(
    (completedResearch / researchFields.length) * 100
);

// 執筆進捗を計算
const writingFields = ["first_draft", "checks", "revised_draft"];
const completedWriting = writingFields.filter(
    (f) => workflow.writing[f] === "done"
).length;
const writingProgress = Math.round(
    (completedWriting / writingFields.length) * 100
);

// 公開進捗を計算
const publishingFields = ["final_review", "published"];
const completedPublishing = publishingFields.filter(
    (f) => workflow.publishing[f] === "done"
).length;
const publishingProgress = Math.round(
    (completedPublishing / publishingFields.length) * 100
);
```

### 5. 主要パス一覧

```
prj-note/
├── articles/{article_id}/     # 記事データ
├── .claude/
│   ├── agents/                # エージェント定義（13種）
│   └── commands/              # コマンド定義
├── data/schemas/              # JSONスキーマ（10種）
├── docs/
│   ├── project/               # プロジェクト管理文書
│   └── validation-reports/    # 検証レポート
└── templates/                 # 記事テンプレート
```

### 6. 今後の実装予定

#### 優先度高（実装予定）

1. **Step 8**: article-editor + 批評家エージェント群（8-12 時間）
2. **Step 9**: workflow-guide.md（2-3 時間）
3. **Step 10**: /suggest-topics コマンド（6-8 時間）
4. **本番記事公開**: D.B.クーパー事件を note に公開

#### 保留・後回し

-   research-visualize Phase B-D（3 ヶ月以降）
-   きさらぎ駅・バックルーム検証（Step 8-9 完了後）
-   自動公開ワークフロー（6 ヶ月以降）

### 7. 利用可能なコマンド

| コマンド                   | 説明                   | 状態        |
| -------------------------- | ---------------------- | ----------- |
| `/new-article`             | 新規記事作成           | ✅ 実装済み |
| `/research --article <id>` | リサーチワークフロー   | ✅ 実装済み |
| `/wiki-search <query>`     | Wikipedia 検索         | ✅ 実装済み |
| `/push`                    | Git コミット＆プッシュ | ✅ 実装済み |
| `/suggest-topics`          | トピック提案           | 🔜 計画中   |

### 8. 詳細ドキュメント参照

必要に応じて以下のドキュメントを参照：

-   `README.md` - プロジェクト概要
-   `CLAUDE.md` - 技術仕様書
-   `docs/project/IMPLEMENTATION-PLAN.md` - 実装計画詳細
-   `docs/project/postponed-items-policy.md` - 後回し項目の方針

## 実行手順

### Phase 1: 現在の状態を分析

1. **コンポーネント数の集計**
   - `.claude/agents/` 内のエージェント数をカウント
   - `.claude/commands/` 内のコマンド数をカウント
   - `data/schemas/` 内のスキーマ数をカウント
   - `articles/` 内の記事数と状態を確認

2. **実装状況の確認**
   - 各記事フォルダの 01_research/02_edit/03_published の状態
   - 最新のGitコミットから進捗を確認
   - docs/project/IMPLEMENTATION-PLAN*.md から最新の計画を確認

3. **統計情報の生成**
   ```
   | カテゴリ | 実装済み | 計画中 | 合計 |
   |---------|---------|--------|------|
   | エージェント | [実数] | [実数] | [実数] |
   | コマンド | [実数] | [実数] | [実数] |
   | スキーマ | [実数] | 0 | [実数] |
   | 記事 | [実数] | [実数] | [実数] |
   ```

### Phase 2: ドキュメントの並列更新

1. **統計データJSONの準備**
   - Phase 1で収集した統計情報を以下のJSON形式で整形

   ```json
   {
     "project_info": {
       "name": "prj-note",
       "start_date": "2026-01-01",
       "last_updated": "YYYY-MM-DD"  // 今日の日付
     },
     "components": {
       "agents": {
         "total": <実数>,
         "active": <実数>,
         "deprecated": <実数>,
         "list": [エージェント名のリスト]
       },
       "commands": {
         "total": <実数>,
         "implemented": <実数>,
         "planned": <実数>,
         "list": [コマンド名のリスト]
       },
       "schemas": {
         "total": <実数>,
         "list": [スキーマ名のリスト]
       },
       "articles": {
         "total": <実数>,
         "by_phase": {
           "research": <実数>,
           "edit": <実数>,
           "published": <実数>
         }
       }
     },
     "progress": {
       "research_phase": <0-100>,
       "edit_phase": <0-100>,
       "publish_phase": <0-100>
     },
     "implementation": {
       "completed_steps": "Step 1-X",
       "next_steps": "次のステップの説明",
       "milestones": ["マイルストーンのリスト"]
     }
   }
   ```

2. **2つのエージェントを並列起動**

   ⚠️ **重要**: 単一のメッセージ内で2つの Task tool を同時に呼び出すこと

   **Task tool 呼び出し1** - `update-readme` エージェント:
   ```
   subagent_type: update-readme
   description: README.md を統計データに基づいて更新
   prompt:
     以下の統計データに基づいてREADME.mdを更新してください。

     統計データ:
     {上記のJSON}

     更新対象:
     - 最終更新日（行77, 行188）
     - プロジェクト構造セクション（行64）
     - 主要コマンドセクション（行153-164）
     - プロジェクト統計セクション（行168-176）
     - 進捗率セクション（行200-205）
   ```

   **Task tool 呼び出し2** - `update-claude-md` エージェント:
   ```
   subagent_type: update-claude-md
   description: CLAUDE.md を統計データに基づいて更新
   prompt:
     以下の統計データに基づいてCLAUDE.mdを更新してください。

     統計データ:
     {上記のJSON}

     更新対象:
     - エージェント一覧ヘッダー（行370）
     - プロジェクト構造セクション（行487-491）
     - コマンドセクション（必要に応じて）
   ```

3. **更新結果の集約**
   - update-readme の結果: 更新したセクションと変更概要
   - update-claude-md の結果: 更新したセクションと変更概要
   - 両方の結果を統合してレポート生成

### Phase 3: レポート生成

1. **状態レポートの表示**
   - プロジェクト概要（開始日、最終更新日、カテゴリ）
   - 実装進捗（完了済み/進行中/次のステップ）
   - コンポーネント統計（実装済み/計画中の数）
   - 記事状況（各記事の進捗状態）
   - 最近のGitコミット（直近10件）

2. **並列更新結果の報告**
   - ✅ **README.md 更新結果**:
     - 更新したセクション一覧
     - 変更内容の概要
     - エラー（あれば）

   - ✅ **CLAUDE.md 更新結果**:
     - 更新したセクション一覧
     - 変更内容の概要
     - エラー（あれば）

   - 📝 **全体サマリー**:
     - 処理時間（並列化により約半分に短縮）
     - 更新された項目数の合計
     - 成功/失敗の統計

### Phase 4: 整合性チェック

1. **ドキュメント間の整合性確認**
   - README.md と CLAUDE.md の情報が一致しているか確認
   - 実装計画書との整合性チェック

2. **警告の表示**
   - ⚠️ 矛盾する情報があれば警告
   - 💡 改善提案があれば提示

## 自動更新のルール

### README.md 更新箇所

- `**最終更新**: YYYY-MM-DD` を今日の日付に
- エージェント数、コマンド数、スキーマ数を実数に
- 進捗率を現在の状態から計算
- 利用可能なコマンド一覧を最新化

### CLAUDE.md 更新箇所

- エージェント一覧（全○○種）の数を実数に
- 各エージェントの存在確認と一覧更新
- コマンド一覧の更新
- プロジェクト構造の説明文内の数値更新

## 使用例

```bash
# 状態確認と自動更新を実行
/project-status

# 出力例:
📊 プロジェクト状態分析中...
✅ エージェント: 20種類を検出（アクティブ: 18, 非推奨: 2）
✅ コマンド: 9種類を検出（実装済み: 8, 計画中: 1）
✅ スキーマ: 10種類を検出
✅ 記事: 2件（リサーチ中: 2, 執筆中: 1, 公開済み: 0）

📝 統計データJSON生成完了

🔄 README.md と CLAUDE.md を並列更新中...
   ├─ update-readme エージェント起動 ✓
   └─ update-claude-md エージェント起動 ✓

✅ README.md 更新完了
   - 最終更新日: 2026-01-06
   - プロジェクト統計セクション更新
   - 主要コマンドセクション更新
   - 進捗率セクション更新

✅ CLAUDE.md 更新完了
   - エージェント一覧ヘッダー更新: 全20種（アクティブ18種）
   - プロジェクト構造セクション更新

⚡ 並列処理により処理時間を約50%短縮

[詳細な状態レポートが表示される]
```
