# [非推奨] Dify ワークフロー設計書: 競争優位性評価 PoC

> **この文書は非推奨です。**
> 最新の設計書は [`analyst/memo/dify_workflow_design.md`](memo/dify_workflow_design.md) を参照してください。

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-02-13 | Phase 0 設計議論（9議論）＋ Dify実装設計議論（13判断）を経て、10ノード・4KB設計に移行 |

## 旧設計との主な差異

| 項目 | 旧設計（本ファイル） | 新設計 |
|------|---------------------|--------|
| ノード数 | 5（LLM×3 + Code×1 + Template×1） | 10（LLM×6 + 知識検索×4） |
| Knowledge Base | 未使用（dogma.md直接貼り付け） | KB1〜KB4（RAG活用） |
| 主張の種別 | 優位性のみ | 3種別（competitive_advantage, cagr_connection, factual_claim） |
| ファクトチェック | なし | 10-K/10-Qとの照合（ステップ3） |
| 検証工程 | 警鐘チェック（1ノード） | JSON検証＋レポート検証（2ノード） |
| フィードバック設計 | なし | テンプレート埋込＋改善サイクル |

## 関連ファイル

- **正式設計書**: `analyst/memo/dify_workflow_design.md`
- **設計議論サマリー**: `analyst/memo/discussion_summary.md`
- **KBチャンクファイル**: `analyst/dify/kb1_rules/`, `analyst/dify/kb2_patterns/`, `analyst/dify/kb3_fewshot/`
- **システムプロンプト**: `analyst/dify/system_prompt.md`
