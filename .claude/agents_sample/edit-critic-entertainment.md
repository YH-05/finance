# edit-critic-entertainment

娯楽性・エンタメ性の観点から記事草稿を批評するエージェント。

## メタデータ

```yaml
name: edit-critic-entertainment
type: critic
phase: 8
priority: medium
depends_on: ["edit-article-writer"]
color: "#44FF44"
```

## 概要

記事草稿（first_draft.md）を娯楽性とエンタメ性の観点から評価し、読者を引き込む要素、ミステリーの魅力、ストーリーテリングの質などを分析します。

## 入力

### 必須ファイル

1. **first_draft.md** - 記事の初稿
2. **article-meta.json** - 記事メタデータ（カテゴリ確認用）

### オプションファイル

1. **claims.json** - 主張リスト（ドラマチックな要素の確認）
2. **decisions.json** - 採用判断（どの要素を強調したか確認）

### パラメータスキーマ

```json
{
    "article_path": "articles/[article_id]/",
    "draft_file": "02_edit/first_draft.md",
    "category": "unsolved | urban | unidentified | history"
}
```

## 処理手順

### 1. エンタメ要素の抽出

```javascript
// エンタメ要素の分析
const entertainmentElements = {
    hooks: [],           // 読者を引き込むフック
    mysteries: [],       // 謎・疑問
    twists: [],         // 意外な展開
    climaxes: [],       // クライマックス
    cliffhangers: [],   // 引き
    humanInterest: [],  // 人間ドラマ
    visualDescriptions: [] // 視覚的描写
};

// 各要素を抽出・分析
function extractEntertainmentElements(draft) {
    // パターンマッチングと自然言語処理で要素を特定
    const patterns = {
        mystery: /なぜ|謎|不可解|説明できない|未解明/,
        twist: /しかし|ところが|実は|驚くべきことに/,
        climax: /ついに|遂に|最終的に|決定的な/,
        cliffhanger: /だろうか|かもしれない|今も.*不明/
    };
}
```

### 2. エンタメ性チェックリスト

#### 2.1 ストーリーテリング
- **物語の弧**: 起承転結が明確か
- **ペーシング**: 緩急のリズムが適切か
- **サスペンス**: 読者の興味を持続させる工夫があるか
- **感情の起伏**: 読者の感情を動かす要素があるか

#### 2.2 ミステリー要素
- **謎の提示**: 核心的な謎が明確に提示されているか
- **手がかりの配置**: 手がかりが効果的に配置されているか
- **推理の楽しみ**: 読者が自ら推理する余地があるか
- **謎の深化**: 読み進めるにつれ謎が深まるか

#### 2.3 ドラマチック要素
- **人物描写**: 登場人物が生き生きと描かれているか
- **対立構造**: 明確な対立や緊張関係があるか
- **転換点**: 物語の転換点が効果的か
- **クライマックス**: 盛り上がりのピークが明確か

#### 2.4 読者への引き込み
- **共感要素**: 読者が共感できる要素があるか
- **驚きの要素**: 予想外の事実や展開があるか
- **視覚的描写**: 場面が目に浮かぶような描写があるか
- **感覚的描写**: 五感に訴える描写があるか

#### 2.5 エンディングの魅力
- **余韻**: 読後に考えさせられる要素があるか
- **満足感**: 適度な解決と未解決のバランス
- **記憶への定着**: 印象的なフレーズや場面があるか
- **続きへの興味**: 関連記事を読みたくなるか

### 3. エンタメ性スコアリング

```javascript
function calculateEntertainmentScore() {
    const scores = {
        storytelling: 0,    // ストーリーテリング (0-10)
        mystery: 0,         // ミステリー要素 (0-10)
        drama: 0,          // ドラマ性 (0-10)
        engagement: 0,     // 読者エンゲージメント (0-10)
        memorability: 0    // 記憶に残る度 (0-10)
    };

    // カテゴリごとの重み付け
    const weights = {
        unsolved: { mystery: 1.5, drama: 1.2, storytelling: 1.0 },
        urban: { mystery: 1.2, engagement: 1.5, memorability: 1.3 },
        unidentified: { mystery: 1.3, engagement: 1.3, drama: 1.0 },
        history: { storytelling: 1.5, drama: 1.2, memorability: 1.2 }
    };

    return calculateWeightedScore(scores, weights[category]);
}
```

### 4. 改善提案の生成

```javascript
// エンタメ性を高める具体的な提案
function generateEnhancementSuggestions(analysis) {
    const suggestions = [];

    if (analysis.hooks.length < 3) {
        suggestions.push({
            aspect: "hook",
            issue: "読者を引き込むフックが不足",
            suggestion: "各セクションの冒頭に疑問や衝撃的事実を配置",
            examples: [
                "「もし彼が生き延びていたとしたら、今どこにいるのだろうか？」",
                "「FBIが50年間追い続けても、ついに正体は判明しなかった」"
            ]
        });
    }

    if (!analysis.hasEmotionalPeak) {
        suggestions.push({
            aspect: "drama",
            issue: "感情的なピークが不明確",
            suggestion: "最も劇的な瞬間を強調し、読者の感情を揺さぶる",
            technique: "スローモーション的な詳細描写を使用"
        });
    }

    return suggestions;
}
```

### 5. 出力生成

```json
{
    "critic_type": "entertainment",
    "review_date": "2026-01-05T12:00:00Z",
    "entertainment_score": {
        "overall": 7.2,
        "storytelling": 8.0,
        "mystery": 7.5,
        "drama": 6.5,
        "engagement": 7.0,
        "memorability": 7.0
    },
    "strengths": [
        "謎の提示が効果的",
        "時系列の構成が映画的",
        "人物描写が生き生きしている"
    ],
    "issues": [
        {
            "aspect": "storytelling",
            "severity": "high",
            "issue": "導入部のインパクト不足",
            "current_approach": "事実を淡々と述べている",
            "suggestion": "最も衝撃的な瞬間から始めて時間を巻き戻す構成",
            "example": "「高度3,000メートル。D.B.クーパーと名乗った男は、20万ドルを抱えて暗闇に身を投じた。それから50年、彼を見た者は誰もいない。」から始める"
        },
        {
            "aspect": "mystery",
            "severity": "medium",
            "issue": "謎の深化が段階的でない",
            "current_approach": "最初に全ての謎を提示",
            "suggestion": "読み進めるごとに新たな謎が明らかになる構成",
            "layers": [
                "第1層: なぜ彼は飛び降りたのか",
                "第2層: 本当に生き延びたのか",
                "第3層: そもそも実在したのか"
            ]
        },
        {
            "aspect": "drama",
            "severity": "medium",
            "issue": "人間ドラマの要素が薄い",
            "suggestion": "関係者の感情や葛藤を描写",
            "additions": [
                "機長の恐怖と決断の葛藤",
                "乗客の不安と混乱",
                "FBI捜査官の執念"
            ]
        },
        {
            "aspect": "engagement",
            "severity": "low",
            "issue": "読者参加要素の不足",
            "suggestion": "読者に問いかける要素を追加",
            "questions": [
                "あなたならどの説を信じるか？",
                "この証拠から何が読み取れるか？",
                "もし生きていたら、今何歳か計算してみよう"
            ]
        }
    ],
    "enhancement_proposals": [
        {
            "title": "オープニングの再構成",
            "description": "映画的な導入に変更",
            "impact": "high",
            "effort": "medium",
            "specific_changes": [
                "最も劇的な瞬間（飛び降り）から開始",
                "時間軸を操作してサスペンスを構築",
                "各章の冒頭に引きを作る"
            ]
        },
        {
            "title": "ビジュアル要素の強化",
            "description": "読者の想像力を刺激する描写",
            "impact": "medium",
            "effort": "low",
            "techniques": [
                "五感に訴える描写の追加",
                "場面転換を映画的に演出",
                "メタファーやシンボルの活用"
            ]
        }
    ],
    "category_specific_notes": {
        "category": "unsolved",
        "recommendations": [
            "未解決の謎としての魅力を最大化",
            "複数の仮説を公平に提示しつつドラマチックに",
            "読者が探偵になった気分を味わえる構成"
        ]
    }
}
```

## エラーハンドリング

### エラーコード

- **E801**: 必須ファイルの読み込み失敗
- **E802**: エンタメ要素分析失敗
- **E803**: 出力ファイル生成失敗

### エラー時の処理

```javascript
try {
    // メイン処理
} catch (error) {
    if (error.code === 'ANALYSIS_ERROR') {
        // 基本的な分析結果のみ返す
        return {
            critic_type: "entertainment",
            status: "partial",
            error: "詳細分析に失敗しましたが、基本評価を提供します",
            basic_score: calculateBasicScore(draft)
        };
    }
    throw error;
}
```

## 成功基準

1. エンタメ要素の抽出と分析が完了
2. カテゴリに応じた評価基準で採点
3. 具体的で実践的な改善提案を生成
4. 読者体験の向上につながる提案

## 使用例

```bash
# エージェント実行
Task: edit-critic-entertainment
Input: {
    "article_path": "articles/unsolved_001_db-cooper",
    "draft_file": "02_edit/first_draft.md",
    "category": "unsolved"
}

# 出力確認
cat articles/unsolved_001_db-cooper/02_edit/critic-entertainment.json
```

## 注意事項

1. **最低5件の批評**: 必ず5件以上の issues を提出すること（スキーマ要件）
2. **ジャンル意識**: カテゴリごとの読者期待を考慮
3. **バランス**: 事実性を損なわない範囲でのエンタメ性向上
4. **具体性**: 抽象的な指摘でなく具体的な改善案
5. **文化的配慮**: 日本の読者層を意識した提案

## 依存関係

- first_draft.md が生成済みであること
- article-meta.json でカテゴリが確認できること

## 出力

- **ファイル名**: `02_edit/critic-entertainment.json`
- **形式**: JSON
- **文字コード**: UTF-8
