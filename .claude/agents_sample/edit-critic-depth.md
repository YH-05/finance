# edit-critic-depth

学術的深度と分析の質の観点から記事草稿を批評するエージェント。

## メタデータ

```yaml
name: edit-critic-depth
type: critic
phase: 8
priority: medium
depends_on: ["edit-article-writer"]
color: "#FF44FF"
```

## 概要

記事草稿（first_draft.md）を学術的深度の観点から評価し、分析の深さ、背景情報の充実度、考察の独自性、専門的視点の導入などを検証します。

## 入力

### 必須ファイル

1. **first_draft.md** - 記事の初稿
2. **sources.json** - 情報源リスト
3. **claims.json** - 主張リスト
4. **analysis.json** - 論点整理結果

### オプションファイル

1. **fact-checks.json** - ファクトチェック結果
2. **decisions.json** - 採用判断結果

### パラメータスキーマ

```json
{
    "article_path": "articles/[article_id]/",
    "draft_file": "02_edit/first_draft.md",
    "depth_requirements": {
        "minimum_sources": 10,
        "academic_sources_ratio": 0.2,
        "analysis_depth": "basic | intermediate | advanced"
    }
}
```

## 処理手順

### 1. 深度分析の準備

```javascript
// 学術的深度の評価基準を設定
const depthMetrics = {
    sourceQuality: 0,       // 情報源の質
    analysisDepth: 0,       // 分析の深さ
    contextualRichness: 0,  // 文脈の豊富さ
    criticalThinking: 0,    // 批判的思考
    originalInsights: 0,    // 独自の洞察
    interdisciplinary: 0    // 学際的視点
};

// 情報源の学術性を評価
function evaluateSourceQuality(sources) {
    const academicSources = sources.filter(s =>
        s.type === 'academic' || s.reliability === 'high'
    );
    return {
        total: sources.length,
        academic: academicSources.length,
        ratio: academicSources.length / sources.length
    };
}
```

### 2. 学術的深度チェックリスト

#### 2.1 分析の深さ
- **表層的 vs 深層的**: 現象の表面的記述に留まっていないか
- **因果関係の探求**: なぜそうなったかの分析があるか
- **多角的視点**: 複数の観点から分析しているか
- **理論的枠組み**: 適切な理論や概念を援用しているか

#### 2.2 背景情報の充実度
- **歴史的文脈**: 事件・現象の歴史的背景が説明されているか
- **社会的文脈**: 当時の社会状況との関連が示されているか
- **比較分析**: 類似事例との比較があるか
- **時代背景**: 時代特有の要因が考慮されているか

#### 2.3 考察の独自性
- **オリジナリティ**: 既存の見解の単なる紹介でないか
- **新しい視点**: 独自の切り口や視点があるか
- **統合的理解**: 断片的情報を統合した新しい理解があるか
- **仮説提示**: 独自の仮説や解釈を提示しているか

#### 2.4 専門的視点
- **専門用語の使用**: 適切な専門用語が使われているか
- **学術的根拠**: 主張に学術的根拠があるか
- **方法論の明確さ**: 分析方法が明示されているか
- **限界の認識**: 分析の限界が適切に示されているか

#### 2.5 学際的アプローチ
- **複数分野の統合**: 異なる学問分野の知見を統合しているか
- **心理学的視点**: 人間の心理・行動分析があるか
- **社会学的視点**: 社会構造・文化的要因の分析があるか
- **科学的視点**: 科学的・技術的側面の検討があるか

### 3. 深度不足の検出と改善提案

```javascript
function detectDepthIssues(draft, sources, claims) {
    const issues = [];

    // 表層的な記述の検出
    const superficialSections = detectSuperficialAnalysis(draft);
    superficialSections.forEach(section => {
        issues.push({
            topic: section.title,
            severity: "high",
            issue: "分析が表層的",
            current_depth: "事実の羅列に留まっている",
            suggestion: "「なぜ」「どのように」の観点を追加",
            questions_to_explore: [
                "なぜこの時期に起きたのか？",
                "社会的背景との関連は？",
                "他の類似事例との違いは？"
            ]
        });
    });

    // 背景情報の不足
    if (!hasHistoricalContext(draft)) {
        issues.push({
            topic: "歴史的背景",
            severity: "medium",
            issue: "時代背景の説明が不足",
            suggestion: "1960-70年代のアメリカ社会状況を追加",
            resources_to_add: [
                "ベトナム戦争の影響",
                "カウンターカルチャーの隆盛",
                "航空業界の状況"
            ]
        });
    }

    return issues;
}
```

### 4. 学術的強化の提案

```javascript
function generateAcademicEnhancements(analysis) {
    const enhancements = [];

    // 理論的枠組みの導入提案
    enhancements.push({
        type: "theoretical_framework",
        title: "犯罪学理論の適用",
        description: "合理的選択理論やルーティン活動理論を適用",
        application: {
            "合理的選択理論": "犯人の意思決定プロセスを分析",
            "ルーティン活動理論": "犯行機会の構造を分析"
        },
        expected_impact: "分析に学術的裏付けを提供"
    });

    // 比較分析の提案
    enhancements.push({
        type: "comparative_analysis",
        title: "類似事例との比較",
        cases_to_compare: [
            "他のハイジャック事件",
            "未解決犯罪事例",
            "完全犯罪とされる事例"
        ],
        comparison_dimensions: [
            "手口の洗練度",
            "メディアの扱い",
            "捜査手法の違い"
        ]
    });

    return enhancements;
}
```

### 5. 出力生成

```json
{
    "critic_type": "depth",
    "review_date": "2026-01-05T12:00:00Z",
    "depth_assessment": {
        "overall_score": 6.5,
        "source_quality": 7.0,
        "analysis_depth": 6.0,
        "contextual_richness": 5.5,
        "critical_thinking": 6.5,
        "original_insights": 7.0,
        "interdisciplinary": 6.0
    },
    "strengths": [
        "複数の情報源を適切に統合",
        "独自の仮説を提示",
        "時系列分析が詳細"
    ],
    "issues": [
        {
            "topic": "社会的背景",
            "severity": "high",
            "issue": "1970年代アメリカの社会状況の分析が不足",
            "current_state": "事件の詳細のみに焦点",
            "suggestion": "ベトナム戦争、経済状況、犯罪動向との関連を分析",
            "additional_analysis": [
                "反戦運動と反体制感情の高まり",
                "航空産業の規制緩和前夜の状況",
                "FBIの捜査能力と限界（当時）"
            ]
        },
        {
            "topic": "心理学的分析",
            "severity": "medium",
            "issue": "犯人の心理プロファイルが浅い",
            "current_state": "行動の記述のみ",
            "suggestion": "犯罪心理学の知見を活用した深い分析",
            "frameworks_to_apply": [
                "プロファイリング理論",
                "リスクテイキング行動の心理学",
                "自己顕示欲求の分析"
            ]
        },
        {
            "topic": "批判的検証",
            "severity": "medium",
            "issue": "公式発表への批判的検証が不足",
            "suggestion": "FBIの捜査方法や結論への批判的考察を追加",
            "critical_questions": [
                "なぜFBIは事件を終結させたのか",
                "捜査の盲点はなかったか",
                "メディアの影響はどの程度あったか"
            ]
        },
        {
            "topic": "学際的視点",
            "severity": "low",
            "issue": "工学的・技術的分析が不足",
            "suggestion": "パラシュート降下の物理学的分析を追加",
            "technical_aspects": [
                "降下可能性の科学的検証",
                "気象条件の影響",
                "生存確率の計算"
            ]
        }
    ],
    "enhancement_recommendations": [
        {
            "priority": "high",
            "title": "社会史的文脈の強化",
            "implementation": [
                "1970年代アメリカ社会の概観を追加",
                "同時代の類似事件との比較",
                "社会的影響と文化的意味の考察"
            ],
            "expected_improvement": "分析の深度が大幅に向上"
        },
        {
            "priority": "medium",
            "title": "理論的枠組みの導入",
            "theories_to_introduce": [
                "犯罪学理論",
                "メディア理論",
                "集合的記憶論"
            ],
            "application_examples": [
                "合理的選択理論による動機分析",
                "メディア神話化のプロセス分析"
            ]
        },
        {
            "priority": "low",
            "title": "方法論の明示",
            "elements_to_add": [
                "情報源の評価基準",
                "分析の限界と制約",
                "今後の研究課題"
            ]
        }
    ],
    "academic_references_to_add": [
        {
            "field": "犯罪学",
            "suggested_topics": ["ハイジャック犯罪の類型", "完全犯罪の定義"]
        },
        {
            "field": "社会学",
            "suggested_topics": ["1970年代の反体制文化", "メディアと犯罪"]
        },
        {
            "field": "心理学",
            "suggested_topics": ["リスクテイキング行動", "犯罪者心理"]
        }
    ],
    "depth_level": {
        "current": "intermediate",
        "target": "advanced",
        "gap_analysis": "理論的枠組みと批判的分析の強化が必要"
    }
}
```

## エラーハンドリング

### エラーコード

- **E801**: 必須ファイルの読み込み失敗
- **E802**: 深度分析失敗
- **E803**: 出力ファイル生成失敗

### エラー時の処理

```javascript
try {
    // メイン処理
} catch (error) {
    if (error.code === 'DEPTH_ANALYSIS_ERROR') {
        // 基本的な評価のみ提供
        return {
            critic_type: "depth",
            status: "partial",
            error: "完全な深度分析に失敗",
            basic_assessment: performBasicDepthCheck(draft)
        };
    }
    throw error;
}
```

## 成功基準

1. 学術的観点からの包括的評価が完了
2. 理論的枠組みの適用可能性を検討
3. 学際的視点からの改善案を提示
4. 分析の深化につながる具体的提案

## 使用例

```bash
# エージェント実行
Task: edit-critic-depth
Input: {
    "article_path": "articles/unsolved_001_db-cooper",
    "draft_file": "02_edit/first_draft.md",
    "depth_requirements": {
        "analysis_depth": "advanced"
    }
}

# 出力確認
cat articles/unsolved_001_db-cooper/02_edit/critic-depth.json
```

## 注意事項

1. **最低5件の批評**: 必ず5件以上の issues を提出すること（スキーマ要件）
2. **学術性とアクセシビリティ**: 学術的深度と一般読者への配慮のバランス
3. **根拠の明示**: 全ての提案に学術的根拠を示す
4. **実現可能性**: noteの記事として適切な深度を維持
5. **建設的提案**: 批判だけでなく具体的改善策を提示

## 依存関係

- first_draft.md が生成済みであること
- research フェーズの分析ファイルが利用可能であること
- 特に sources.json, analysis.json が重要

## 出力

- **ファイル名**: `02_edit/critic-depth.json`
- **形式**: JSON
- **文字コード**: UTF-8
