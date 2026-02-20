# Simple AI Investment Strategy PoC

## 概要

AI駆動の競争優位性ベース投資戦略の簡易PoC。既存の`src/dev/ca_strategy/`パイプラインを修正して実行する。フルMAS（Multi-Agent System）の前段として位置づけ。

## 確定事項

| 項目 | 決定内容 |
|------|----------|
| 位置づけ | Simple PoCはフルMASの前段 |
| アプローチ | 既存ca_strategyパイプラインを修正して実行 |
| ユニバース | 408銘柄（`data/Transcript/list_portfolio_20151224.json`）、346銘柄にトランスクリプトあり |
| データソース | 既存S&P Capital IQトランスクリプトJSON（2015Q1-Q3） |
| 抽出フレームワーク（Phase 1） | **7 Powers**（Hamilton Helmer）— ✅ 実装済み |
| 評価フレームワーク（Phase 2） | KB1-T/KB2-T/KB3-T + dogma.md — ✅ 構造化出力を追加して強化済み |
| PoiTカットオフ | 2015-09-30 |
| 匿名化 | 完全匿名化（ティッカー、企業名、役員名、製品名） |
| ポートフォリオ | 2種類：等ウェイト AND セクター中立＋スコア比例 |
| 銘柄数 | スコア閾値ベース、複数閾値を実験 |
| リバランス | なし（2015Q4〜現在までBuy & Hold） |
| ベンチマーク | ACWI（MSCI ACWI） |
| 評価方法 | 複合評価：パフォーマンス＋アナリスト相関＋透明性 |
| 答え合わせ | AIスコアとKY/AKスコアを比較（順位相関＋ヒット率＋定性） |
| コスト上限 | 〜$50 |
| 欠損銘柄 | トランスクリプトなし62銘柄はスキップ |

## パイプライン（5フェーズ）

### Phase 0: 前処理（✅ 既存・完了）
- S&P Capital IQ月次トランスクリプトJSONをPer-ticker JSONに変換
- `transcript_parser.py`で実行済み

### Phase 1: 主張抽出（✅ 実装済み）
- 抽出フレームワーク: Hamilton Helmerの7 Powersを使用
  - Scale Economies, Network Economies, Counter-Positioning, Switching Costs, Branding, Cornered Resource, Process Power
- 決算トランスクリプトから競争優位性の主張を5-15件/銘柄で抽出
- 完全匿名化を適用（ティッカー、企業名、役員名、製品名）
- `extractor.py`: `seven_powers_path`オプション追加済み（KB1-Tとのデュアルモード対応）
- `seven_powers_framework.md`: 7 Powers KB（244行）を`analyst/transcript_eval/`に作成済み
- `types.py`: `PowerClassification`, `EvidenceSource`モデル追加済み

### Phase 2: スコアリング（✅ 構造化出力を追加して強化済み）
- KB1-T（9ルール）で評価
- KB2-T（12パターン：却下A-G、高評価I-V）で確信度調整
- KB3-T（5銘柄few-shot）でキャリブレーション
- dogma.md（アナリストY評価哲学）を参照
- 4段階評価: ゲートキーパー → KB1-T → KB2-T → KB3-Tキャリブレーション
- 確信度: 10-90%（目標分布: 90%:6%, 70%:26%, 50%:35%, 30%:26%, 10%:6%）
- `scorer.py`: 既存ロジック流用 + 構造化出力対応
- `types.py`: `GatekeeperResult`, `KB1RuleApplication`, `KB2PatternMatch`モデル追加済み

### Phase 3: 集約・中立化（✅ 既存・変更なし）
- 銘柄別スコア集約（構造的重み付き）
- セクター内Z-scoreでセクター中立化ランキング生成
- 既存: `aggregator.py`, `neutralizer.py`

### Phase 4: ポートフォリオ構築（🔧 要修正）
- **変更点**: 2種類のポートフォリオを構築
  1. 等ウェイト — **未実装**
  2. セクター中立＋スコア比例 — 既存
- スコア閾値ベースで銘柄数を決定（複数閾値を実験）
- リバランスなし（2015Q4〜現在までBuy & Hold）
- 既存: `portfolio_builder.py` → 等ウェイト版の追加が必要

### Phase 5: 出力・評価（🔧 要修正）
- ポートフォリオウェイト（JSON/CSV/Markdown） — 既存`output.py`
- 銘柄別rationale — 既存`output.py`
- **変更点**: 評価セクションを追加 — **未実装**
  - ベンチマーク: ACWI（MSCI ACWI）対比パフォーマンス
  - アナリスト相関: AIスコアとKY/AKスコアの比較（順位相関＋ヒット率＋定性）
  - 透明性評価

## 実装に必要な作業

### 完了済み
1. ~~**7 Powersフレームワークの定義** — リサーチ＆KB化~~ ✅ `analyst/transcript_eval/seven_powers_framework.md`
2. ~~**extractor.pyのプロンプト修正** — 7 Powers用の抽出プロンプト~~ ✅ `seven_powers_path`オプション・構造化出力
3. ~~**types.py 構造化モデル追加** — Phase 1/2の構造化出力~~ ✅ `PowerClassification`, `EvidenceSource`, `GatekeeperResult`, `KB1RuleApplication`, `KB2PatternMatch`
4. ~~**scorer.py 構造化出力対応**~~ ✅ Phase 2評価結果の構造化パース

### 未実装
5. **等ウェイトポートフォリオ構築** — `portfolio_builder.py`への追加
6. **評価モジュール** — ACWI対比パフォーマンス、アナリスト相関計算

### 設定ファイル（未作成）
7. **universe.json** — 408銘柄（list_portfolio_20151224.json準拠）
8. **benchmark_weights.json** — ACWI用

### 既存流用（変更なし）
- `aggregator.py` — スコア集約
- `neutralizer.py` — セクター中立化
- `transcript.py` — トランスクリプト読込
- `cost.py` — コスト追跡
- `pit.py` — PoiT制約管理
- `batch.py` — バッチ処理・チェックポイント

## コスト見積もり

| Phase | 処理内容 | 呼び出し回数 | 推定コスト |
|-------|---------|-------------|-----------|
| Phase 1 | 主張抽出（346銘柄） | 約346回 | 約$17 |
| Phase 2 | スコアリング（346銘柄） | 約346回 | 約$17 |
| **合計** | | **約692回** | **約$34** |

上限$50以内に収まる見込み。
