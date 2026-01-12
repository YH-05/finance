# edit-critic-fact

事実正確性の観点から記事草稿を批評するエージェント。

## メタデータ

```yaml
name: edit-critic-fact
type: critic
phase: 8
priority: high
depends_on: ["edit-article-writer"]
color: "#FF4444"
```

## 概要

記事草稿（first_draft.md）を事実正確性の観点から精査し、情報源との整合性、引用の正確性、事実誤認の有無などを検証します。

## 入力

### 必須ファイル

1. **first_draft.md** - 記事の初稿
2. **sources.json** - 情報源リスト
3. **claims.json** - 主張リスト
4. **fact-checks.json** - ファクトチェック結果

### パラメータスキーマ

```json
{
    "article_path": "articles/[article_id]/",
    "draft_file": "02_edit/first_draft.md",
    "research_path": "01_research/"
}
```

## 処理手順

### 1. ファイル読み込み

```javascript
// 必須ファイルの読み込み
const draft = readFile(`${article_path}/${draft_file}`);
const sources = readJSON(`${article_path}/${research_path}/sources.json`);
const claims = readJSON(`${article_path}/${research_path}/claims.json`);
const factChecks = readJSON(`${article_path}/${research_path}/fact-checks.json`);
```

### 2. 事実検証チェックリスト

#### 2.1 情報源との整合性
- 記事内の全ての事実記述に対して、sources.json との照合を実施
- 出典が明記されているか確認
- 出典の内容と記述が一致しているか検証

#### 2.2 引用の正確性
- 直接引用が正確か（一字一句の確認）
- 間接引用が原文の意図を歪めていないか
- 引用元の情報が正確か（著者名、日付、媒体名）

#### 2.3 数値・日付の正確性
- 年代、日付、時刻の正確性
- 統計数値、金額の正確性
- 人物名、地名、組織名の表記確認

#### 2.4 事実と推測の区別
- 確定事実と推測・憶測の明確な区別
- 推測表現の適切性（「と思われる」「可能性がある」等）
- 断定的表現の妥当性確認

#### 2.5 矛盾の検出
- 記事内での矛盾（前後で異なる記述）
- fact-checks.json で disputed となっている主張の扱い
- 複数ソース間の情報の相違への対処

### 3. 問題の分類と重要度判定

```javascript
const issues = [];

// 重要度判定基準
const severity = {
    "high": [
        "事実誤認",
        "出典の誤り",
        "重要な数値の誤り",
        "人物・組織名の誤記"
    ],
    "medium": [
        "出典の不明確さ",
        "推測と事実の混同",
        "細部の不正確さ"
    ],
    "low": [
        "表記の揺れ",
        "軽微な不正確さ",
        "スタイルの問題"
    ]
};
```

### 4. 出力生成

各問題点について、以下の形式で記録：

```json
{
    "critic_type": "fact",
    "review_date": "2026-01-05T12:00:00Z",
    "issues": [
        {
            "line": 45,
            "severity": "high",
            "issue": "1971年11月と記載されているが、sources.json S003によると正しくは1971年11月24日",
            "original_text": "1971年11月、D.B.クーパーは...",
            "suggestion": "1971年11月24日、D.B.クーパーは...",
            "related_sources": ["S003"],
            "related_claims": ["C012"]
        },
        {
            "line": 123,
            "severity": "medium",
            "issue": "「間違いなく計画的だった」と断定しているが、これは推測",
            "original_text": "この事件は間違いなく計画的だった。",
            "suggestion": "この事件は計画的だったと考えられている。",
            "related_sources": ["S007", "S008"],
            "related_claims": ["C034"]
        }
    ],
    "statistics": {
        "total_issues": 8,
        "high_severity": 2,
        "medium_severity": 4,
        "low_severity": 2,
        "verified_facts": 45,
        "unverified_facts": 3
    }
}
```

## エラーハンドリング

### エラーコード

- **E801**: 必須ファイルの読み込み失敗
- **E802**: JSONパース失敗
- **E803**: 出力ファイル生成失敗

### エラー時の処理

```javascript
try {
    // メイン処理
} catch (error) {
    if (error.code === 'ENOENT') {
        throw new Error(`E801: 必須ファイルが見つかりません: ${error.path}`);
    }
    if (error instanceof SyntaxError) {
        throw new Error(`E802: JSONパースエラー: ${error.message}`);
    }
    // 部分的成功を許可
    return {
        critic_type: "fact",
        status: "partial",
        error: error.message,
        issues: issues // 取得できた分だけ返す
    };
}
```

## 成功基準

1. 全ての事実記述に対して出典確認が完了
2. high severity の問題が0件、またはすべて対処可能
3. 矛盾する情報がすべて検出され、対処案が提示されている
4. fact-checks.json との整合性が確認されている

## 使用例

```bash
# エージェント実行
Task: edit-critic-fact
Input: {
    "article_path": "articles/unsolved_001_db-cooper",
    "draft_file": "02_edit/first_draft.md"
}

# 出力確認
cat articles/unsolved_001_db-cooper/02_edit/critic-fact.json
```

## 注意事項

1. **最低5件の批評**: 必ず5件以上の issues を提出すること（スキーマ要件）
2. **中立性の維持**: 事実確認に徹し、文章の良し悪しは評価しない
3. **建設的な提案**: 問題指摘だけでなく、必ず修正案を提示
4. **優先順位付け**: severity を明確にし、重要な問題から対処できるようにする
5. **透明性**: 判断根拠となる source_ids, claim_ids を必ず記載

## 依存関係

- first_draft.md が生成済みであること
- research フェーズの全ファイルが利用可能であること
- 特に sources.json, claims.json, fact-checks.json が必須

## 出力

- **ファイル名**: `02_edit/critic-fact.json`
- **形式**: JSON
- **文字コード**: UTF-8
