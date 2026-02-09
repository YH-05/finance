# Dify ワークフロー設計書: 競争優位性評価 PoC

## 概要

Y の Dogma に基づいて競争優位性仮説を評価する Dify ワークフローの設計。

| 項目 | 内容 |
|------|------|
| ワークフロータイプ | Workflow（非 Chatflow） |
| 入力 | アナリストレポート（テキスト）+ 銘柄情報 |
| 出力 | Phase 2 形式の評価テーブル（確信度% + コメント） |
| LLM | Claude Sonnet 推奨（コスト/品質バランス）。Opus は精度向上が必要な場合 |

---

## ワークフロー全体図

```
┌─────────┐
│  Start  │ ← 入力: analyst_report, ticker, company_name
└────┬────┘
     │
     ▼
┌─────────────────────┐
│ Node 1: Phase 1     │ ← LLM: 競争優位性仮説の生成
│ 仮説生成            │    System: Phase 1 プロンプト
│                     │    Output: 仮説リスト（JSON）
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Node 2: 構造化      │ ← Code (Python): JSON パース + 整形
│                     │    仮説を個別に分離し、評価用フォーマットに変換
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Node 3: Phase 2     │ ← LLM: 各仮説の評価
│ 評価                │    System: Y の Dogma 全文
│                     │    Output: 評価テーブル + コメント
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Node 4: 警鐘チェック │ ← LLM: 全体印象 + 警鐘事項
│                     │    System: Dogma の警鐘機能セクション
│                     │    Input: 全仮説 + 全評価結果
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Node 5: レポート整形 │ ← Template Transform (Jinja2)
│                     │    Phase 2 + 警鐘 → 最終レポート
└────────┬────────────┘
         │
         ▼
┌─────────┐
│   End   │ → 出力: evaluation_report (Markdown)
└─────────┘
```

---

## Node 定義

### Start ノード

| 変数名 | 型 | 必須 | 説明 |
|--------|-----|------|------|
| `analyst_report` | Paragraph | Yes | アナリストレポート全文（`analyst/raw/` の内容をペースト） |
| `ticker` | Text Input | Yes | 銘柄ティッカー（例: `ANET`） |
| `company_name` | Text Input | Yes | 企業名（例: `Arista Networks`） |

---

### Node 1: Phase 1 仮説生成（LLM）

**目的:** アナリストレポートから競争優位性仮説を構造化して抽出する。

**モデル:** Claude Sonnet（Temperature: 0.3）

**System Prompt:**

```
あなたは企業の競争優位性に着目して投資判断を下す経験豊富な外国株式投資アナリストAIです。

提供されるアナリストレポートから、企業の持続的な競争優位性を抽出し、以下のJSON形式で出力してください。

## 抽出ルール

1. 各優位性は「能力・仕組み」として記述すること。「結果・実績」は優位性ではない
   - 良い例: 「独自OSによるネットワーク運用の技術優位」
   - 悪い例: 「高い市場シェア」「売上成長の加速」

2. 各優位性は「名詞」で表現できる属性であること
   - 良い例: 「買収ターゲット選定能力」「ポートフォリオ管理力」
   - 悪い例: 「海外展開を加速している」「ポートフォリオをシフトしている」

3. 業界の全企業が持つ能力は優位性ではない（相対的に際立つものだけ抽出）

4. 戦略（意思決定）と優位性（構造的な力）を区別すること

5. 前提知識の中で①期初レポートの内容を主とし、②四半期レビューの内容は従として扱うこと

## 出力フォーマット（JSON）

必ず以下のJSON形式で出力してください。JSON以外のテキストは含めないでください。

```json
{
  "ticker": "XXXX",
  "company_name": "企業名",
  "hypotheses": [
    {
      "id": 1,
      "title": "優位性の名称（名詞で表現）",
      "description": "優位性の詳細説明（200-400字）。優位性が機能するメカニズム、競合が模倣できない理由を含む",
      "evidence": [
        "根拠1（定量データを優先）",
        "根拠2",
        "根拠3"
      ],
      "cagr_connection": {
        "parameter": "影響するCAGRパラメータ（例: 売上成長寄与 +X%）",
        "mechanism": "優位性がCAGRに寄与するメカニズム（1-2ステップで説明）",
        "verifiable": true
      },
      "source_type": "① or ②（期初レポート or 四半期レビュー）"
    }
  ],
  "cagr_summary": {
    "eps_cagr": "+X%",
    "components": [
      {"name": "売上成長寄与", "value": "+X%", "basis": "根拠の要約"},
      {"name": "マージン改善寄与", "value": "+X%", "basis": "根拠の要約"},
      {"name": "自社株買い寄与", "value": "+X%", "basis": "根拠の要約"}
    ]
  }
}
```
```

**User Prompt:**

```
以下のアナリストレポートから競争優位性仮説を抽出してください。

## 銘柄情報
- ティッカー: {{ticker}}
- 企業名: {{company_name}}

## アナリストレポート

{{analyst_report}}
```

---

### Node 2: 構造化（Code / Python）

**目的:** Phase 1 出力の JSON をパースし、Phase 2 の評価に適した形式に変換する。

```python
import json
import re

def main(phase1_output: str) -> dict:
    """Phase 1 LLM出力からJSONを抽出してパースする"""

    # JSON部分を抽出（```json ... ``` ブロックまたは直接JSON）
    json_match = re.search(r'```json\s*(.*?)\s*```', phase1_output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # 直接JSONの場合
        json_match = re.search(r'\{.*\}', phase1_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            return {
                "error": "JSON not found in Phase 1 output",
                "raw_output": phase1_output[:500]
            }

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return {
            "error": f"JSON parse error: {str(e)}",
            "raw_output": json_str[:500]
        }

    # Phase 2 評価用のフォーマットに変換
    hypotheses_text = ""
    for h in data.get("hypotheses", []):
        hypotheses_text += f"""
### 優位性 {h['id']}: {h['title']}

**説明:** {h['description']}

**根拠:**
"""
        for e in h.get("evidence", []):
            hypotheses_text += f"- {e}\n"

        cagr = h.get("cagr_connection", {})
        hypotheses_text += f"""
**CAGRパラメータへの影響:** {cagr.get('parameter', '不明')}
**メカニズム:** {cagr.get('mechanism', '不明')}
**情報ソース:** {h.get('source_type', '不明')}

---
"""

    cagr_summary = data.get("cagr_summary", {})
    cagr_text = f"**EPS CAGR:** {cagr_summary.get('eps_cagr', '不明')}\n"
    for comp in cagr_summary.get("components", []):
        cagr_text += f"- {comp['name']}: {comp['value']}（{comp['basis']}）\n"

    return {
        "hypotheses_text": hypotheses_text,
        "hypotheses_count": len(data.get("hypotheses", [])),
        "cagr_text": cagr_text,
        "ticker": data.get("ticker", ""),
        "company_name": data.get("company_name", ""),
        "raw_json": json.dumps(data, ensure_ascii=False)
    }
```

**入力変数:** `phase1_output` = Node 1 の `text` 出力
**出力変数:** `hypotheses_text`, `hypotheses_count`, `cagr_text`, `ticker`, `company_name`, `raw_json`

---

### Node 3: Phase 2 評価（LLM）

**目的:** Y の Dogma に基づいて各競争優位性仮説を評価する。

**モデル:** Claude Sonnet（Temperature: 0.2）。精度検証後、必要に応じて Opus に変更。

**System Prompt:**

以下に Y の Dogma 全文をそのまま貼り付ける（`analyst/Competitive_Advantage/analyst_YK/dogma.md` の内容）。

> Dify の System Prompt に `dogma.md` の全文（約207行）をそのまま貼り付ける。
> Knowledge Base（RAG）は使用しない。Dogma は全文を常に参照する必要があるため、
> 検索による部分取得では精度が落ちる。

System Prompt の末尾に以下の評価指示を追加:

```
---

## あなたのタスク

あなたは上記のDogmaを内面化したファンドマネージャーYです。

提供される競争優位性仮説に対して、Dogmaのルールに厳密に従い評価してください。

### 評価プロセス

各仮説に対して以下の順で検証すること:

1. **前提条件チェック**（不合格なら即却下）
   - 事実誤認はないか（ルール9）
   - 業界共通の能力を固有化していないか（ルール3）

2. **優位性の性質チェック**
   - 提示されているのは「能力・仕組み」か、「結果・実績」か（ルール1）
   - 名詞で表現できるか（ルール2）
   - 戦略と優位性を混同していないか（ルール8）

3. **裏付けの質チェック**
   - 定量データはあるか（ルール4）
   - 純粋競合との比較はあるか（ルール7）
   - ネガティブケースでの裏付けはあるか（ルール10）
   - 業界構造との合致はあるか（ルール11）

4. **CAGR接続チェック**（優位性が100%あるものとして独立評価）
   - 直接性: 1-2ステップか（ルール5）
   - 構造的か補完的か（ルール6）
   - 検証可能性: 開示データで寄与を測定できるか

### 出力フォーマット

必ず以下のMarkdownテーブル形式で出力してください。

```markdown
| 優位性 | 評価 | CAGR パラメータへの影響 | 評価 |
|--------|------|------------------------|------|
| 1: [タイトル] | [ランク]([確信度]%)<br>-[コメント1（結論）]<br>-[コメント2（根拠）]<br>-[コメント3（改善提案）] | [CAGR接続の内容] | [ランク]([確信度]%)<br>-[コメント1]<br>-[コメント2] |
```

### コメント記述ルール

1. 最初に評価ランクと確信度を明示
2. 根拠を具体的に（Yが使う表現パターンに倣う）
   - 却下時: 「〜は結果であり優位性ではない」「〜は業界共通であり差別化にならない」
   - 高評価時: 「〜の数値裏付けは納得感を高める」「〜との競合比較で差別化が確認」
3. 改善提案を含める: 「〜の情報があれば納得度が上がる」
4. 一貫性を保つ: 同じパターンの仮説には同じロジックを適用

### スコア分布の参考値

あなたの評価は以下の分布に近づくべきです:
- 90%（かなり納得）: 全体の約6%。業界構造との合致がある場合のみ
- 70%（おおむね納得）: 全体の約26%
- 50%（まあ納得）: 最頻値で約35%。「方向性は認めるが裏付け不十分」が最も多い
- 30%（あまり納得しない）: 全体の約26%
- 10%（却下）: 全体の約6%

安易に高スコアを付けないこと。50%が最も一般的な評価であることを意識すること。
CAGR接続は優位性評価より全体的に高スコアが出る傾向がある。
```

**User Prompt:**

```
以下の競争優位性仮説を評価してください。

## 銘柄: {{ticker}} ({{company_name}})

## 競争優位性仮説（Phase 1 出力）

{{hypotheses_text}}

## CAGR サマリー

{{cagr_text}}
```

---

### Node 4: 警鐘チェック（LLM）

**目的:** 全仮説・全評価を俯瞰し、警鐘事項を指摘する。

**モデル:** Claude Sonnet（Temperature: 0.3）

**System Prompt:**

```
あなたはファンドマネージャーYの投資判断における「警鐘機能」を担うAIです。

以下の観点で評価結果を検証し、警鐘事項を報告してください。

## 警鐘チェック項目

1. **既存判断への無批判的受容**
   - アナリストの主張をそのまま受け入れている仮説はないか
   - 「多くの企業が言っていること」を固有の優位性として扱っていないか

2. **情報ソースの偏り**
   - ①期初レポートの前提は現在も合理的か
   - ②四半期レビューから拡大解釈された優位性はないか

3. **推論パターンの一貫性**
   - 評価基準が仮説間でブレていないか
   - 同じ性質の仮説に異なるスコアが付いていないか

4. **結果と原因の混同**
   - 高シェア、成長加速、高収益を「原因」として扱っている仮説はないか
   - 「結果」を「能力」に言い換えただけの仮説はないか

5. **スコア分布の偏り**
   - 高スコア（70%以上）に偏りすぎていないか
   - 50%が最頻値であるべき

## 出力フォーマット

```markdown
## 警鐘事項

### 重大な懸念（評価の再検討を推奨）
- [具体的な指摘と該当する仮説番号]

### 軽微な懸念（留意事項）
- [具体的な指摘]

### 推論パターンの一貫性チェック
- [一貫性に関する所見]

### スコア分布チェック
- 90%: X個 / 70%: X個 / 50%: X個 / 30%: X個 / 10%: X個
- [分布の偏りに関するコメント]
```
```

**User Prompt:**

```
以下の評価結果を検証し、警鐘事項を報告してください。

## 銘柄: {{ticker}} ({{company_name}})

## Phase 1 仮説

{{hypotheses_text}}

## Phase 2 評価結果

{{phase2_evaluation}}
```

---

### Node 5: レポート整形（Template Transform / Jinja2）

**目的:** 全ノードの出力を統合し、最終レポートを生成する。

**テンプレート:**

```jinja2
# {{ticker}} ({{company_name}}) 競争優位性評価レポート

> 評価基準: Y（吉沢）の Dogma に基づく
> 評価日: {{current_date}}
> 仮説数: {{hypotheses_count}}

---

## Phase 2 評価テーブル

{{phase2_evaluation}}

---

{{alarm_report}}

---

## 参考: CAGR サマリー

{{cagr_text}}
```

---

### End ノード

| 出力変数 | 型 | 説明 |
|----------|-----|------|
| `evaluation_report` | String | 最終レポート（Markdown） |

---

## Knowledge Base 設定

この PoC では **Knowledge Base（RAG）は使用しない**。

理由:
1. Dogma は全文を常に参照する必要があり、部分検索では精度が落ちる
2. Dogma のサイズ（約207行）は System Prompt に収まる
3. PoC 段階では System Prompt 直接埋め込みの方がデバッグしやすい

将来的にアナリストごとの Dogma を切り替える場合は、Knowledge Base を導入し、変数で Dogma を選択する設計に移行する。

---

## テスト計画

### Phase 1: 動作確認（最優先）

| テスト | 入力 | 期待結果 |
|--------|------|----------|
| ワークフロー疎通 | ANET レポート（`analyst/raw/` から） | エラーなく最終レポートが出力される |
| JSON パース | Phase 1 出力 | Node 2 でエラーなく構造化される |
| 出力フォーマット | - | Phase 2 テーブル形式で出力される |

### Phase 2: In-sample 精度検証

既存の Phase 2 データとの比較で精度を測定する。

| テスト銘柄 | Phase 2 データ | 検証方法 |
|-----------|---------------|----------|
| CHD | `phase2_KY/pattern1_CHD_phase2.md` | AI スコアと Y の実スコアの乖離を測定 |
| MNST | `phase2_KY/pattern1_MNST_phase2.md` | 同上 |

**注意:** Phase 1 出力（AI が生成した仮説）は保存されていないため、In-sample 検証では:
1. `analyst/raw/` のレポートを入力 → Phase 1 で仮説生成
2. Phase 2 で評価
3. **Phase 2 の評価スコアのみ** を Y の実スコアと比較（Phase 1 の仮説が異なる可能性があるため、完全一致は期待しない）

### Phase 3: Out-of-sample テスト

Phase 2 データが存在しない銘柄でテストし、Y にフィードバックを依頼する。

| テスト銘柄 | レポート | 備考 |
|-----------|---------|------|
| ANET | `analyst/raw/ANET_*.md` | Phase 1 サンプル（`phase1/ANET_phase1.md`）あり |
| CPRT | `analyst/raw/CPRT_*.md` | Phase 2 なし |
| AME | `analyst/raw/AME_*.md` | Phase 2 なし |

---

## 精度目標

| 指標 | 目標 |
|------|------|
| 平均スコア乖離（優位性） | ±10% 以内 |
| 平均スコア乖離（CAGR接続） | ±10% 以内 |
| 個別項目の最大乖離 | ±20% 以内 |
| スコア分布（50%が最頻値） | 30-40% の仮説が 50% 評価 |
| 却下すべき仮説の見落とし率 | 0%（事実誤認は必ず検出） |

---

## 改善サイクル

```
Dify ワークフロー実行
    ↓
Y の実スコアとの乖離分析
    ↓
乖離原因の特定
├── Dogma の記述不足 → dogma.md を改訂
├── プロンプトの指示不足 → Node 3 System Prompt を改訂
├── Phase 1 の仮説品質 → Node 1 System Prompt を改訂
└── モデルの限界 → モデル変更（Sonnet → Opus）
    ↓
再実行・再検証
```

---

## 補足: Phase 2 のみのテスト方法

既存の Phase 1 出力が手元にある場合（例: `phase1/ANET_phase1.md`）、Node 1-2 をスキップして Phase 2 評価のみテストできる。

**手順:**
1. Start ノードに `phase1_output` 変数を追加（Paragraph 型）
2. IF/ELSE ノードを追加: `phase1_output` が空でなければ Node 1-2 をスキップ
3. Node 3 に直接 Phase 1 テキストを渡す

ただし、既存の Phase 1 出力（`ANET_phase1.md`）は JSON 形式ではなく Markdown 形式のため、Node 3 の User Prompt に直接テキストとして渡す方が簡単。

---

## ファイル対応表

| Dify 設定箇所 | 参照元ファイル |
|--------------|--------------|
| Node 3 System Prompt | `analyst/Competitive_Advantage/analyst_YK/dogma.md` 全文 |
| Node 1 System Prompt | `analyst/Competitive_Advantage/Competitive_Advantage_template_ver2.md` を簡略化 |
| テスト入力 | `analyst/raw/` 配下のレポート |
| 精度検証の正解データ | `analyst/phase2_KY/` 配下のスコアリング |
| Phase 1 サンプル | `analyst/phase1/ANET_phase1.md` |
