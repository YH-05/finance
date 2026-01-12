---
description: Wikipediaを使った包括的な情報検索・抽出・ファクトチェック用データ収集を実行します。重要事実の抽出、関連トピック探索、構造化データ生成。
argument-hint: [query] [--depth=basic|deep] [--lang=ja|en|both] [--mode=research|factcheck] [--focus=keywords]
---

あなたは Wikipedia を使った包括的な情報検索・抽出・ファクトチェック用データ収集を実行します。

## 入力パラメータの解析

ユーザーが指定したパラメータを解析します：

-   **query** (必須): 検索クエリ（例: `ゾディアック事件`, `Zodiac Killer`）
-   **--depth**: オプション（デフォルト: `basic`）
    -   `basic`: 基本的な情報収集（重要事実 5 件、関連トピック 5 件）
    -   `deep`: 詳細な調査（重要事実 15 件、関連トピック 10 件、セクション別分析）
-   **--focus**: オプション（デフォルト: なし）
    -   カンマ区切りでフォーカス領域を指定（例: `暗号,被害者`）
    -   指定されたキーワードに関連する情報を優先的に抽出
-   **--lang**: オプション（デフォルト: `both`）
    -   `ja`: 日本語版のみ
    -   `en`: 英語版のみ
    -   `both`: 両方検索（英語版を優先）
-   **--mode**: オプション（デフォルト: `research`）
    -   `research`: リサーチモード（読みやすいサマリー重視）
    -   `factcheck`: ファクトチェックモード（構造化データ重視）
-   **--related**: オプション（デフォルト: `5`）
    -   関連トピックの取得数（1-20）
-   **--article**: オプション（デフォルト: なし）
    -   記事フォルダパスを指定（例: `articles/unsolved_001_zodiac-killer`）
    -   指定時は `{article}/01_research/wikipedia/` にファイルを保存

必須パラメータが不足している場合は、ユーザーに確認してください。

## 手順

### Phase 1: 検索と記事取得

1. **準備**

    - クエリから安全なディレクトリ名を生成（英語、ケバブケース）
    - 現在の日付を取得（YYYY-MM-DD 形式）
    - TodoWrite ツールでタスクを作成
    - 注: ファイル保存先は `--article` オプション指定時のみ記事フォルダに保存。それ以外はコンソール出力のみ

2. **トピック検索**

    **日本語版検索**（`--lang=ja` または `both`）:

    ```
    mcp__wikipedia__search_wikipedia
    - query: {クエリ}
    - limit: 10
    ```

    **英語版検索**（`--lang=en` または `both`）:

    - 可能であれば英語クエリに変換して検索
    - または元のクエリで英語版を検索

    結果から最も関連性の高い記事を選択（通常は検索結果の 1 位）

3. **記事取得**

    選択した記事について以下を実行：

    ```
    # 全文取得
    mcp__wikipedia__get_article(title)

    # 要約取得
    mcp__wikipedia__get_summary(title)

    # セクション構造取得
    mcp__wikipedia__get_sections(title)
    ```

    両言語で記事がある場合、両方のデータを取得して比較・統合

4. **基本情報の整理**
    - 記事タイトル（日本語/英語）
    - 記事 URL
    - セクション数、推定語数
    - 取得日時

### Phase 2: 詳細情報抽出

5. **重要事実の抽出**

    ```
    mcp__wikipedia__extract_key_facts
    - title: {記事タイトル}
    - count: basic=5, deep=15
    - topic_within_article: {--focus指定があればそれを使用}
    ```

    抽出された事実を以下の形式で構造化：

    ```json
    {
        "id": "fact_001",
        "content": "事実の内容",
        "type": "date|person|location|number|event",
        "section": "該当セクション名（推定）",
        "reliability": "high|medium|low"
    }
    ```

    **事実タイプの自動判定**:

    - `date`: 日付パターン（YYYY 年、YYYY-MM-DD、19XX 年代など）を含む
    - `person`: 人名パターン（大文字始まり、氏名形式）
    - `location`: 地名キーワード（州、市、国など）
    - `number`: 数値を含む（○ 人、○ ドル、○ 件など）
    - `event`: 上記以外の出来事

6. **フォーカス領域の詳細抽出**（`--focus` 指定時）

    フォーカスキーワードごとに：

    ```
    mcp__wikipedia__summarize_article_for_query
    - title: {記事タイトル}
    - query: {フォーカスキーワード}
    - max_length: 250
    ```

    各キーワードに特化した情報を抽出

7. **セクション別分析**（`--depth=deep`）

    主要なセクション（目次の第 1-2 レベル）について：

    ```
    mcp__wikipedia__summarize_article_section
    - title: {記事タイトル}
    - section_title: {セクション名}
    - max_length: 150
    ```

    各セクションの要約を `sections/{section-name}.md` に保存

### Phase 3: 関連情報マッピング

8. **関連トピック探索**

    ```
    mcp__wikipedia__get_related_topics
    - title: {記事タイトル}
    - limit: {--relatedパラメータの値}
    ```

    各関連トピックについて簡易要約を取得：

    ```
    mcp__wikipedia__get_summary(related_title)
    ```

    関連度を以下で評価：

    - Wikipedia 推奨: high
    - 記事内で複数回言及: medium
    - その他: low

9. **リンク分析**

    ```
    mcp__wikipedia__get_links(title)
    ```

    取得したリンクを分類：

    - **人物リンク**: 人名パターンに一致
    - **地名リンク**: 地名キーワードを含む
    - **事件・出来事リンク**: "事件", "事象", "incident", "case"などを含む
    - **組織リンク**: "部", "局", "department", "agency"などを含む
    - **その他**: 上記以外

    各カテゴリで Top 5-10 をリストアップ

10. **座標情報の取得**（該当する場合）

    ```
    mcp__wikipedia__get_coordinates(title)
    ```

    地理的な記事の場合、座標情報を取得・保存

### Phase 4: ファクトチェック用データ整理（`--mode=factcheck`）

11. **検証可能な事実の構造化**

    抽出したすべての事実について：

    ```json
    {
        "id": "fact_001",
        "type": "date|person|location|number|event",
        "content": "1968年12月20日に最初の確認された攻撃",
        "section": "Crimes",
        "source_url": "https://en.wikipedia.org/wiki/Zodiac_Killer#Crimes",
        "reliability": "high",
        "verification_status": "pending",
        "extracted_date": "2025-12-20",
        "notes": ""
    }
    ```

    **信頼性レベルの判定**:

    -   `high`: 具体的な日付・名前・数値を含む明確な事実
    -   `medium`: やや抽象的または推定を含む
    -   `low`: "reportedly", "allegedly"などの限定表現を含む

12. **矛盾検出**

    同じトピック内で矛盾する可能性のある情報を検出：

    -   同じ事象について異なる日付
    -   同じ統計について異なる数値
    -   矛盾する場所情報

    検出した場合：

    ```json
    {
        "type": "potential_conflict",
        "facts": ["fact_001", "fact_015"],
        "reason": "異なる被害者数が記載されている",
        "requires_verification": true
    }
    ```

13. **出典リストの生成**

    -   記事本文から脚注・参考文献を抽出（可能な範囲で）
    -   Wikipedia 記事自体を一次出典として記録
    -   引用フォーマットで整形：
        ```
        [^1]: Wikipedia "Zodiac Killer" https://en.wikipedia.org/wiki/Zodiac_Killer (2025-12-20閲覧)
        ```

### Phase 5: データ保存（`--article` 指定時のみ）

14. **ファイル保存**

    `--article` オプションが指定された場合のみ、以下のファイルを `{article}/01_research/wikipedia/` に保存：

    **article.md** - 記事全文（マークダウン形式）

    ```markdown
    # {記事タイトル}

    **出典**: {Wikipedia URL}
    **言語**: {ja/en}
    **取得日**: {YYYY-MM-DD}

    ## 要約

    {要約内容}

    ## 本文

    {記事本文}
    ```

    **summary.md** - 要約とキーポイント

    ```markdown
    # {トピック} - Wikipedia 検索サマリー

    ## 基本情報

    -   タイトル: {title}
    -   URL: {url}
    -   セクション数: {count}

    ## 重要事実

    1. {fact 1}
    2. {fact 2}
       ...

    ## 関連トピック

    1. {related topic 1}
    2. {related topic 2}
       ...
    ```

    **facts.json** - 構造化された事実データ

    ```json
    {
      "topic": "{トピック名}",
      "source": {
        "title": "{記事タイトル}",
        "url": "{URL}",
        "language": "ja|en",
        "accessed_date": "YYYY-MM-DD"
      },
      "facts": [...],
      "statistics": {
        "total_facts": 45,
        "by_type": {...},
        "by_reliability": {...}
      },
      "conflicts": [...]
    }
    ```

    **related.json** - 関連情報マップ

    ```json
    {
      "topic": "{トピック}",
      "related_topics": [...],
      "important_links": {
        "persons": [...],
        "locations": [...],
        "events": [...],
        "organizations": [...]
      },
      "link_network": {...}
    }
    ```

    **links.json** - リンク分析結果

    ```json
    {
      "total_links": 156,
      "categorized": {
        "persons": [...],
        "locations": [...],
        "events": [...],
        "organizations": [...],
        "other": [...]
      }
    }
    ```

    **metadata.json** - 検索メタデータ

    ```json
    {
      "query": "{元のクエリ}",
      "parameters": {
        "depth": "basic|deep",
        "focus": [...],
        "lang": "ja|en|both",
        "mode": "research|factcheck"
      },
      "execution_date": "YYYY-MM-DD",
      "articles_found": {
        "ja": "{日本語版タイトル}",
        "en": "{英語版タイトル}"
      }
    }
    ```

    **sections/** ディレクトリ（`--depth=deep`の場合）

    -   各セクションの詳細を個別の Markdown ファイルとして保存

15. **MCP Memory への記録**（オプション）

    `--article` 指定時、重要な知見を MCP Memory に記録：

    ```
    # エンティティ作成
    mcp__memory__create_entities
    - トピック（事件名など）
    - 重要人物（被害者、容疑者、捜査官など）
    - 重要な場所
    - 記事ID（article_id をエンティティとして記録）

    # 関係性の記録
    mcp__memory__create_relations
    - article_id → トピック (COVERS)
    - トピック → 人物 (INVOLVES)
    - トピック → 場所 (OCCURRED_AT)
    - 人物 → 組織 (BELONGS_TO)

    # 観察情報の追加
    mcp__memory__add_observations
    - 各エンティティに重要事実を追加
    ```

### Phase 6: レポート生成と出力

16. **コンソール出力の生成**

    **research モード**の場合：

    ```markdown
    🔍 **Wikipedia 検索結果**: {トピック}

    ## 📄 基本情報

    -   **記事タイトル**: {title (ja)} / {title (en)}
    -   **URL**: {url}
    -   **記事構成**: {セクション数}セクション、推定{語数}語
    -   **取得日**: {date}

    ## ⭐ 重要事実 (Top {count})

    1. 【{type}】{content}
    2. 【{type}】{content}
       ...

    {--focus 指定がある場合}

    ## 🎯 フォーカス領域: {focus_keyword}

    {focused_summary}

    ## 🔗 関連トピック ({count}件)

    1. **{title}** - {summary}
    2. **{title}** - {summary}
       ...

    ## 📊 リンク分析

    -   人物: {count}件（主要: {top 3}）
    -   場所: {count}件（主要: {top 3}）
    -   事件: {count}件（主要: {top 3}）

    {--article 指定時のみ表示}

    ## 📂 保存先

    -   記事全文: {article}/01_research/wikipedia/article.md
    -   要約: {article}/01_research/wikipedia/summary.md
    -   事実データ: {article}/01_research/wikipedia/facts.json
    -   関連情報: {article}/01_research/wikipedia/related.json

    ## 💡 次のステップ

    -   記事作成: `/new-article` で新規記事フォルダを作成
    -   追加リサーチ: `/research "{topic}"` で Web 情報も収集
    -   情報源として記録: research-source エージェントで sources.json に追加
    ```

    **factcheck モード**の場合：

    ```markdown
    ✅ **Wikipedia ファクトチェックデータ収集完了**: {トピック}

    ## 📊 収集統計

    -   **検証可能な事実**: {total}件
    -   **日付情報**: {count}件
    -   **人物情報**: {count}件
    -   **場所情報**: {count}件
    -   **数値情報**: {count}件
    -   **その他事実**: {count}件

    ## 🎯 信頼性評価

    -   高信頼性: {count}件 ({percentage}%)
    -   中信頼性: {count}件 ({percentage}%)
    -   低信頼性: {count}件 ({percentage}%)

    {矛盾が検出された場合}

    ## ⚠️ 検証が必要な項目

    1. {conflict description}
        - 事実 A: {fact}
        - 事実 B: {fact}
        - 推奨: 追加ソースで確認

    {--article 指定時のみ表示}

    ## 📂 ファクトチェック用データ

    -   構造化データ: {article}/01_research/wikipedia/facts.json
    -   出典リスト: {article}/01_research/wikipedia/article.md

    ## 🔜 次のステップ

    -   品質チェック: research-checks エージェントで品質確認
    -   追加リサーチ: `/research "{topic}"` で Web 情報も収集
    -   主張抽出: research-claims エージェントで claims.json を作成
    ```

## エラーハンドリング

### 記事が見つからない場合

```
❌ Wikipedia記事が見つかりませんでした: {query}

💡 **提案**:
- 検索語を変更してみてください
  - 例: "ゾディアック" → "ゾディアック事件"
  - 例: "Zodiac" → "Zodiac Killer"
- 英語版で検索: /wiki-search "{english_query}" --lang=en
- 類似する記事:
  1. {similar 1}
  2. {similar 2}
```

### セクションが見つからない場合

```
⚠️ セクション "{section}" が見つかりませんでした

利用可能なセクション:
1. {section 1}
2. {section 2}
...
```

### API 制限エラー

```
⚠️ Wikipedia API の一時的な制限に達しました

リトライ中... (試行 {n}/3)
```

エラーが継続する場合はユーザーに通知し、部分的な結果を返す

### 不完全なデータ

```
⚠️ 一部のデータ取得に失敗しました

取得済み:
- 記事本文: ✅
- 要約: ✅
- セクション一覧: ❌ (失敗)
- 関連トピック: ✅

処理を継続します...
```

## 最適化とベストプラクティス

1. **並列処理の活用**

    - 日本語版と英語版の検索は並行して実行可能
    - 複数の関連トピックの要約取得も並列化

2. **キャッシュの活用**

    - 同じ記事に対する再検索の場合、既存データを確認
    - metadata.json で実行日時を確認し、7 日以内なら再利用を提案

3. **段階的な情報取得**

    - 基本情報 → 詳細情報 → 関連情報の順で段階的に取得
    - TodoWrite で進捗を適切に報告

4. **データ品質の確保**
    - 空の結果や不完全なデータは警告を表示
    - 信頼性評価は保守的に（不確実な場合は低めに評価）

## 注意事項

-   Wikipedia API の利用規約を遵守してください
-   大量のリクエストを避け、適度な間隔を空けてください
-   抽出した情報はあくまで Wikipedia 時点のものであり、最新情報は別途確認が必要です
-   ファクトチェックモードのデータは参考情報であり、必ず複数ソースでの確認を推奨してください
-   個人情報やプライバシーに配慮してデータを扱ってください

## プロジェクト固有の情報

このコマンドはミステリーブログ執筆プロジェクトで使用されます：

-   **記事フォルダ構造**: `articles/{article_id}/01_research/wikipedia/`
-   **article_id 命名規則**: `{カテゴリ}_{通番3桁}_{テーマ英語名}`
    -   例: `unsolved_001_zodiac-killer`, `urban_003_kisaragi-station`
-   **カテゴリ**: `unsolved`（未解決事件）, `urban`（都市伝説）, `unidentified`（不思議現象）, `history`（歴史の謎）
-   **関連エージェント**: research-source, research-claims, research-decisions, research-checks
