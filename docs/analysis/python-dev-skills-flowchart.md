# Python開発スキル選択フローチャート

**生成日**: 2026-01-25

---

## スキル選択フロー

### 1. 目的別フローチャート

```mermaid
flowchart TD
    Start([何をしたい?]) --> Q1{目的は?}

    Q1 -->|コードを書く| A[ナレッジベース参照]
    Q1 -->|品質改善| B[品質管理]
    Q1 -->|問題解決| C[デバッグ]
    Q1 -->|レビュー| D[レビュー]

    A --> A1{何を確認?}
    A1 -->|規約| SK1[coding-standards]
    A1 -->|TDD| SK2[tdd-development]
    A1 -->|エラー処理| SK3[error-handling]

    B --> B1{何をする?}
    B1 -->|検証のみ| SK4[scan]
    B1 -->|分析レポート| SK5[analyze]
    B1 -->|改善実装| SK6[improve]
    B1 -->|自動修正| SK7[ensure-quality]

    C --> C1{何を直す?}
    C1 -->|リファクタリング| SK8[safe-refactor]
    C1 -->|バグ修正| SK9[troubleshoot]

    D --> D1{何をレビュー?}
    D1 -->|PR| SK10[review-pr]
    D1 -->|ドキュメント| SK11[review-docs]

    style SK1 fill:#e1f5e1
    style SK2 fill:#e1f5e1
    style SK3 fill:#e1f5e1
    style SK4 fill:#fff4e1
    style SK5 fill:#fff4e1
    style SK6 fill:#fff4e1
    style SK7 fill:#fff4e1
    style SK8 fill:#e1e8f5
    style SK9 fill:#e1e8f5
    style SK10 fill:#f5e1e8
    style SK11 fill:#f5e1e8
```

---

## 2. 品質管理スキルの使い分け

```mermaid
flowchart LR
    Start([品質を向上させたい]) --> Q1{現状は?}

    Q1 -->|問題がある| Q2{どう対処?}
    Q1 -->|問題ない| Q3{何をする?}

    Q2 -->|とりあえず検証| scan[scan<br/>素早くスコアリング]
    Q2 -->|詳しく分析| analyze[analyze<br/>詳細レポート]
    Q2 -->|すぐ修正| ensure[ensure-quality<br/>自動修正]

    Q3 -->|計画的に改善| improve[improve<br/>エビデンスベース改善]
    Q3 -->|リファクタリング| refactor[safe-refactor<br/>テスト維持]

    scan --> Result1[セキュリティスコア<br/>脆弱性リスト]
    analyze --> Result2[YAMLレポート<br/>改善ロードマップ]
    ensure --> Result3[make check-all成功<br/>コード整理完了]
    improve --> Result4[メトリクス改善<br/>検証済み]
    refactor --> Result5[テストパス<br/>品質向上]

    style scan fill:#fff4e1
    style analyze fill:#fff4e1
    style ensure fill:#fff4e1
    style improve fill:#fff4e1
    style refactor fill:#e1e8f5
```

---

## 3. スキル実行順序（推奨ワークフロー）

```mermaid
graph TD
    subgraph "Phase 1: 発見"
        P1[scan<br/>問題検出]
    end

    subgraph "Phase 2: 分析"
        P2[analyze<br/>詳細分析]
    end

    subgraph "Phase 3: 計画"
        P3A[improve<br/>改善計画]
        P3B[safe-refactor<br/>リファクタ計画]
    end

    subgraph "Phase 4: 実装"
        P4[ensure-quality<br/>自動修正]
    end

    subgraph "Phase 5: 検証"
        P5[review-pr<br/>レビュー]
    end

    P1 --> P2
    P2 --> P3A
    P2 --> P3B
    P3A --> P4
    P3B --> P4
    P4 --> P5

    style P1 fill:#ffe4e1
    style P2 fill:#fff4e1
    style P3A fill:#e1f5e1
    style P3B fill:#e1f5e1
    style P4 fill:#e1e8f5
    style P5 fill:#f5e1e8
```

---

## 4. スキル依存関係マップ

```mermaid
graph LR
    subgraph "ナレッジベース"
        KB1[coding-standards]
        KB2[tdd-development]
        KB3[error-handling]
    end

    subgraph "品質管理"
        QA1[scan]
        QA2[analyze]
        QA3[improve]
        QA4[ensure-quality]
    end

    subgraph "実装支援"
        DEV1[safe-refactor]
        DEV2[troubleshoot]
    end

    subgraph "レビュー"
        REV1[review-pr]
        REV2[review-docs]
    end

    KB1 -.参照.-> QA4
    KB1 -.参照.-> DEV1
    KB2 -.参照.-> REV1
    KB3 -.参照.-> DEV2

    QA1 -->|詳細分析| QA2
    QA2 -->|改善実装| QA3
    QA3 -->|品質修正| QA4
    QA4 -->|レビュー| REV1

    DEV1 -->|検証| QA4
    DEV2 -->|修正後| QA4

    style KB1 fill:#e1f5e1
    style KB2 fill:#e1f5e1
    style KB3 fill:#e1f5e1
    style QA1 fill:#fff4e1
    style QA2 fill:#fff4e1
    style QA3 fill:#fff4e1
    style QA4 fill:#fff4e1
    style DEV1 fill:#e1e8f5
    style DEV2 fill:#e1e8f5
    style REV1 fill:#f5e1e8
    style REV2 fill:#f5e1e8
```

---

## 5. 状況別スキル選択マトリックス

| 状況 | 推奨スキル | 理由 |
|------|-----------|------|
| **PR作成前** | ensure-quality | 自動修正でmake check-allを通す |
| **週次レビュー** | scan → analyze | 素早くスコアリング→詳細分析 |
| **リファクタリング計画** | analyze → improve | 分析→エビデンスベース改善 |
| **バグ発生** | troubleshoot | 体系的なデバッグ |
| **パフォーマンス問題** | analyze --perf → improve | 詳細分析→最適化実装 |
| **セキュリティ懸念** | scan --security --owasp | OWASP準拠チェック |
| **コードレビュー** | review-pr | 7サブエージェント並列レビュー |
| **レガシーコード改善** | safe-refactor | テストカバレッジ維持 |
| **新機能実装** | tdd-development | TDDサイクル |
| **CI/CD失敗** | ensure-quality | 自動修正 |

---

## 6. スキルの出力物マップ

```mermaid
graph TD
    subgraph "スキル"
        S1[scan]
        S2[analyze]
        S3[improve]
        S4[ensure-quality]
        S5[safe-refactor]
        S6[review-pr]
    end

    subgraph "出力物"
        O1[scan-report.yaml<br/>スコア+脆弱性リスト]
        O2[analysis-report.yaml<br/>詳細分析+ロードマップ]
        O3[improve-report.yaml<br/>改善前後メトリクス]
        O4[品質改善レポート<br/>修正内容+統計]
        O5[リファクタリング完了<br/>品質メトリクス]
        O6[pr-review.yaml<br/>+GitHubコメント]
    end

    S1 --> O1
    S2 --> O2
    S3 --> O3
    S4 --> O4
    S5 --> O5
    S6 --> O6

    style O1 fill:#ffe4e1
    style O2 fill:#fff4e1
    style O3 fill:#e1f5e1
    style O4 fill:#e1e8f5
    style O5 fill:#e1e8f5
    style O6 fill:#f5e1e8
```

---

## 7. 緊急度×重要度マトリックス

```
        重要度
         ↑
    高   |  improve          | scan
         |  (計画的改善)      | (セキュリティ検証)
         |                  |
    ─────┼──────────────────┼───────→ 緊急度
         |                  |
    低   |  analyze          | ensure-quality
         |  (詳細分析)        | (自動修正)
         |                  |
```

**使い分け**:
- **緊急 & 重要**: scan（セキュリティ問題を即検出）
- **緊急 & 低重要**: ensure-quality（PR前の自動修正）
- **非緊急 & 重要**: improve（計画的な改善）
- **非緊急 & 低重要**: analyze（詳細な分析レポート）

---

## 8. スキル学習パス

```mermaid
graph LR
    Start([Python開発スタート]) --> Level1

    subgraph "Level 1: 基礎"
        Level1[coding-standards]
        Level1 --> L1A[tdd-development]
        L1A --> L1B[error-handling]
    end

    subgraph "Level 2: 品質管理"
        Level2[ensure-quality]
        Level2 --> L2A[scan]
        L2A --> L2B[analyze]
    end

    subgraph "Level 3: 改善"
        Level3[improve]
        Level3 --> L3A[safe-refactor]
    end

    subgraph "Level 4: デバッグ・レビュー"
        Level4[troubleshoot]
        Level4 --> L4A[review-pr]
    end

    L1B --> Level2
    L2B --> Level3
    L3A --> Level4

    style Level1 fill:#e1f5e1
    style L1A fill:#e1f5e1
    style L1B fill:#e1f5e1
    style Level2 fill:#fff4e1
    style L2A fill:#fff4e1
    style L2B fill:#fff4e1
    style Level3 fill:#e1e8f5
    style L3A fill:#e1e8f5
    style Level4 fill:#f5e1e8
    style L4A fill:#f5e1e8
```

---

## 凡例

### カラーコード

- 🟢 **緑**: ナレッジベース（読み取り専用）
- 🟡 **黄**: 品質管理（分析・検証）
- 🔵 **青**: 実装支援（リファクタリング・デバッグ）
- 🔴 **赤**: レビュー（PR・ドキュメント）

### スキルタイプ

- **ナレッジベース**: 参照のみ、実行なし
- **分析・検証**: レポート生成、スコアリング
- **実装・修正**: コード変更を伴う
- **レビュー**: 第三者視点での評価

---

**フローチャート完了**: 2026-01-25
