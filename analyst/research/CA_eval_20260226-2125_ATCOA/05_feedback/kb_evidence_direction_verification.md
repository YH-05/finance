# [K10] KB拡張: 証拠の方向性検証プロセス（narrative駆動防止）

> **区分**: KB ワークフロー / 品質管理
> **優先度**: 高
> **トリガー銘柄**: CPRT
> **トリガー事象**: Erie Insurance 方向誤記（Analysis_Erie_direction_error.md 参照）

## 論点

### 発生した誤記

revised-report-CPRT.md #3（スイッチングコスト）懸念点:

> 「Erie InsuranceのRB→CPRT移行もスイッチが「起きうる」ことの証拠」

### 原典（raw/CPRT US.md line 38、RB Global面談）

> 「事実として、Erie Insurance も競合の 50%シェアを**当社**に移して、**当社独占**の状況になった」

面談相手=RB Global CFO のため「当社」=RB。**実際の方向は CPRT→RB（CPRTの喪失）**。AIは方向を**反転**させた。

### Yの指摘

> 「面談記録の『当社』を RBでなく CPRTと誤解しているため？」

## 問題の本質（3層の破綻）

### Layer 1: 字面解釈（lexical）

- 「スイッチ」というトークン一致で判定
- 方向（gain/loss）を identity として保持しない

### Layer 2: KB字面適用（literal KB）

- KB1ルール10「双方向性」を「スイッチ事例が2つあれば双方向性が示される」と機械適用
- GEICO（IAA→CPRT）と（誤記の）Erie（RB→CPRT）は**同じ方向**なのに対極の証拠として扱う矛盾を見逃す

### Layer 3: narrative駆動のスロット充填

- 「懸念点」セクションに「反例が必要」という narrative 要件
- 素材（Erie事例）を投入するが、**CPRTにとって得か損かの符号検証を省略**
- RB→CPRT は CPRT の**獲得**イベント → 懸念点に置くのは結論と証拠の符号逆転

詳細は [Analysis_Erie_direction_error.md](../../CA_eval_20260226-2046_CPRT/Analysis_Erie_direction_error.md) 参照。

## 根本原因

### T7 ca-report-generator の仕様外動作

ca-report-generator の文書化された入力は claims.json / fact-check.json / pattern-verification.json のみだが、Erie Insurance は**いずれにも存在しない**（原典 raw にのみ記載）。

- T7 が narrative 肉付けのために raw を直接参照した（仕様外）
- 参照時にセクション見出し「20 RB Global」の文脈を失い、主語「当社」をレポート全体の主語（CPRT）で解釈
- T4 ca-claim-extractor が Erie を structured data に落とさなかったため、T7 は raw に降りざるを得なかった

### T8 Lead（Opus）の検証失敗

- draft と structured input のみを批判対象とし、**raw への再突合を行わない**
- critique.json で誤方向を「KB1ルール10の双方向性」として正当化し、誤りを固定化

## KB改訂案

### Proposal A: 事実記述の方向性属性を必須化

structured data（claims.json / fact-check.json）に方向性を明示:

```json
{
  "fc_id": "FC_Erie",
  "claim": "Erie Insurance が CPRT→RB に50%シェア移管",
  "direction": "loss_to_competitor",
  "impact_on_subject": "negative",
  "source_speaker": "RB Global CFO (S3: 2025/10)",
  "source_line": "raw/CPRT US.md:38"
}
```

`direction` フィールド（gain / loss / neutral）と `impact_on_subject` フィールド（positive / negative / neutral）を必須化。

### Proposal B: 「懸念点」スロット充填時の符号検証

revised-report のテンプレートに記述時チェックを義務化:

```yaml
懸念点スロット:
  入れる証拠の必要条件:
    - impact_on_subject: "negative"  # 評価対象企業にとってネガティブでなければならない
  自己検証プロンプト:
    - "この事例は {ticker} にとって得か損か？"
    - "損であれば懸念点に配置可。得であれば強みセクションへ移動"
```

### Proposal C: KB1ルール10適用時の方向性明示

KB1ルール10「双方向性」の適用時、両方向の事例を明示的に分類:

| 方向 | 事例 | 寄与 |
|------|-----|------|
| 他社→CPRT（獲得） | GEICO, Erie(実は逆) | 「スイッチが稀」の裏付け |
| CPRT→他社（喪失） | USAA | 「スイッチが起きうる」の裏付け（懸念点素材） |

両方向で同程度の事例が観察される場合、スイッチングコストは「中程度」。片方向に偏る場合は「強い」。

### Proposal D: T7 ca-report-generator の raw 参照禁止

ca-report-generator の入力を構造化データに厳格に限定:

- narrative 肉付けが必要な場合は、T4 ca-claim-extractor に pipe back（再抽出依頼）
- T4 が raw から追加抽出 → セクションコンテキスト保持したまま構造化
- T7 は構造化データのみから記述生成

### Proposal E: T8 批判に原典突合ステップを追加

T8 Lead の critique プロセスに必須ステップを追加:

```yaml
T8_checklist:
  - step: "各懸念点・反例記述について、原典 raw の該当行を citation として記録"
  - step: "該当行のセクションコンテキスト（話者、面談相手）を確認"
  - step: "記述の方向性（impact_on_subject）が懸念点/強みのスロット符号と一致するか検証"
```

## 類似リスクの検出

KB3 / 他銘柄でも同様の symbolic direction reversal が起きうる箇所:

| 銘柄 | リスク箇所 |
|------|-----------|
| COST | Sam's Club / BJ's 等との競争動向（どちらが獲得/喪失したか） |
| CHD | 買収ブランドの売上推移（買収前後の方向性） |
| ORLY | AZO 等とのシェア推移（どちらが獲得したか） |
| LLY | 臨床試験成否の方向（主力候補 vs 競合候補） |

→ **方向性属性の付与は全ての factual_claims に適用すべき**

## アクション

1. claims.json / fact-check.json スキーマに `direction` / `impact_on_subject` フィールド追加（Proposal A）
2. revised-report-format.md テンプレートに「懸念点スロット符号検証」プロンプト追加（Proposal B）
3. KB1ルール10のガイドラインに方向別分類の義務化を追加（Proposal C）
4. ca-report-generator agent.md から raw 参照を削除、T4 への pipe back 仕様を明記（Proposal D）
5. T8 critique プロセスに原典突合ステップを追加（Proposal E）
6. 既存 KB3 銘柄の factual_claims に direction フィールドを retrofit

## 関連ファイル

- [Analysis_Erie_direction_error.md](../../CA_eval_20260226-2046_CPRT/Analysis_Erie_direction_error.md) - 誤記事象の工程別トレース（本KBの前提資料）
- [Feedback_CPRT.md](../../CA_eval_20260226-2046_CPRT/Feedback_CPRT.md) その他セクション（Yの指摘原文）
- [revised-report-CPRT.md](../../CA_eval_20260226-2046_CPRT/04_output/revised-report-CPRT.md) line 135, 139（誤記箇所）
- [questions_for_analyst_Y.md](../../CA_eval_20260226-2046_CPRT/05_feedback/questions_for_analyst_Y.md) Q20（ワークフロー改善提案）
