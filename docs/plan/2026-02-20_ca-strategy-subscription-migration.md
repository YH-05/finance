# ca_strategy: Anthropic API 依存を排除し Claude Code Subscription 方式へ移行

## Context

ca_strategy パイプラインの Phase 1（主張抽出）と Phase 2（スコアリング）は、Python の `anthropic.Anthropic()` クライアントで Claude API を直接呼び出している。これには別途 API キーと従量課金が必要であり、ユーザーの方針「Claude Code subscription の範囲内で実行する」と矛盾する。

**方針**: LLM 推論を行う Phase 1-2 を Claude Code エージェント自身が直接実行する方式に移行する。エージェント自身が LLM であるため、KB ファイルを読み込んで推論し、Pydantic 準拠の JSON をファイルに書き出す。Python コードは LLM 呼び出しを行わず、バリデーションと後続フェーズ（Phase 3-5）の実行のみ担当する。多数銘柄の逐次処理は容認する。

---

## 変更概要

### 現在のアーキテクチャ
```
Agent (T2: claim-extractor)
  → Python ClaimExtractor.extract_batch()
    → anthropic.Anthropic().messages.create()  ← API 課金
    → JSON 出力
```

### 移行後のアーキテクチャ
```
Agent (T2: claim-extractor) = LLM 自身
  → KB ファイルを Read で読み込み
  → エージェント自身が推論（subscription 内）
  → Pydantic 準拠 JSON を Write で書き出し
  → Python validator.py で検証
```

---

## Wave 1: 基盤（新規ファイル作成）

### 1-1. `src/dev/ca_strategy/_file_utils.py`（新規）

`_llm_utils.py` からファイル I/O ユーティリティを抽出。LLM 呼び出しに依存しない汎用関数のみ。

- `load_directory(directory: Path) -> dict[str, str]` — 現在の `_llm_utils.py:26`
- `load_file(filepath: Path) -> str` — 現在の `_llm_utils.py:63`
- `build_kb_section(header: str, items: list[tuple[str, str]]) -> list[str]` — 現在の `_llm_utils.py:133`

### 1-2. `src/dev/ca_strategy/validator.py`（新規）

エージェントが書き出した JSON をバリデーションする CLI ツール。

```python
"""Validate agent-written JSON against Pydantic models.

Usage (from agent):
    uv run python -m dev.ca_strategy.validator \
        --phase phase1 \
        --input {workspace_dir}/phase1_output/claims/AAPL_claims.json

Returns exit code 0 if valid, 1 if invalid (with error details to stderr).
"""

def validate_phase1(path: Path) -> list[Claim]: ...
def validate_phase2(path: Path) -> list[ScoredClaim]: ...

if __name__ == "__main__":
    # argparse CLI
```

**再利用する型**: `Claim`, `ScoredClaim`, `RuleEvaluation`, `ConfidenceAdjustment` 等（`types.py` から）

---

## Wave 2: エージェント定義の書き換え

### 2-1. `transcript-claim-extractor.md` 書き換え

**変更の核心**: 「ClaimExtractor を呼び出す」→「エージェント自身が KB を読んで推論し JSON を書く」

主な変更点:
- 「使用する Python クラス」セクションから `ClaimExtractor` を削除
- 処理フローを変更:
  1. KB ファイル（KB1-T 9 件 + KB3-T 5 件 + system_prompt + dogma.md）を Read で全読み込み
  2. transcripts.json を Read で読み込み
  3. **エージェント自身が各銘柄のトランスクリプトを分析し、主張を抽出**（LLM 推論）
  4. `Claim` モデルの JSON スキーマに準拠した JSON を Write で書き出し
  5. `uv run python -m dev.ca_strategy.validator --phase phase1 --input ...` で検証
  6. チェックポイント JSON を Write で保存
- **CostTracker 参照を削除**（subscription なのでトークンコスト不要）
- 完了通知テンプレートからコスト情報を削除

**JSON 出力スキーマ**: `Claim` モデルの `model_json_schema()` を prompt に含める。

### 2-2. `transcript-claim-scorer.md` 書き換え

**変更の核心**: 「ClaimScorer を呼び出す」→「エージェント自身が KB を読んで推論し JSON を書く」

主な変更点:
- 「使用する Python クラス」セクションから `ClaimScorer` を削除
- 処理フローを変更:
  1. KB ファイル（KB1-T 9 件 + KB2-T 12 件 + KB3-T 5 件 + dogma.md）を Read で全読み込み
  2. phase1_claims.json を Read で読み込み
  3. **エージェント自身が各主張を評価し、確信度スコアを算出**（LLM 推論）
  4. `ScoredClaim` モデルの JSON スキーマに準拠した JSON を Write で書き出し
  5. `uv run python -m dev.ca_strategy.validator --phase phase2 --input ...` で検証
  6. チェックポイント JSON を Write で保存
- CostTracker 参照を削除

### 2-3. `ca-strategy-lead.md` 更新

- コスト見積もりセクション（$30 推定）を削除 → 「subscription 内で実行」に変更
- HF0 テンプレートからコスト関連を削除
- HF1 テンプレートからコスト実績を削除
- T2, T3 のタスク説明から「Claude Sonnet 4 で」→「エージェント自身が」に変更
- チームメイト起動 prompt から CostTracker 参照を削除

---

## Wave 3: Python コード整理

### 3-1. `orchestrator.py` に `run_from_agent_output()` 追加

Phase 3 以降をチェックポイントファイルから直接実行する新しいエントリポイント。

```python
def run_from_agent_output(self) -> None:
    """Run Phase 3-5 from agent-produced checkpoint files.

    Assumes Phase 1-2 were executed by Claude Code agents
    and checkpoint files exist at:
    - {workspace_dir}/checkpoints/phase1_claims.json
    - {workspace_dir}/checkpoints/phase2_scored.json
    """
    claims = self._load_checkpoint("phase1_claims.json", Claim)
    scored_claims = self._load_checkpoint("phase2_scored.json", ScoredClaim)
    scores = self._aggregate_scores(scored_claims)
    ranked = self._execute_phase(3, self._run_phase3_neutralization, (scored_claims, scores))
    portfolio = self._execute_phase(4, self._run_phase4_portfolio_construction, (ranked, self._config.benchmark))
    self._execute_phase(5, self._run_phase5_output_generation, (portfolio, scored_claims, scores))
```

### 3-2. 既存ファイルの非推奨化

以下のファイルは即座に削除せず、docstring に `Deprecated` マークを追加:

| ファイル | 理由 |
|---------|------|
| `extractor.py` | LLM 呼び出しがエージェントに移行 |
| `scorer.py` | LLM 呼び出しがエージェントに移行 |
| `_llm_utils.py` | `call_llm()` が不要（`_file_utils.py` に I/O 関数を移動済み） |

`batch.py` の `BatchProcessor` は非推奨。`CheckpointManager` は引き続き使用可能（ただし agent が直接 JSON を書くため、Phase 1-2 では使わない可能性あり）。

### 3-3. `_llm_utils.py` → `_file_utils.py` への import パス移行

`_file_utils.py` に移動した関数を参照している箇所の import を更新:
- `extractor.py` (deprecated だが参照整合性のため)
- `scorer.py` (同上)
- `orchestrator.py` (使用していなければ不要)

---

## Wave 4: テスト更新

### 4-1. `validator.py` のユニットテスト（新規）

`tests/dev/ca_strategy/unit/test_validator.py`:
- 正常系: 有効な Claim JSON → パース成功
- 正常系: 有効な ScoredClaim JSON → パース成功
- 異常系: 不正な JSON → ValidationError
- 異常系: 必須フィールド欠落 → ValidationError

### 4-2. `_file_utils.py` のユニットテスト（新規）

`tests/dev/ca_strategy/unit/test_file_utils.py`:
- 既存の `_llm_utils.py` テストからファイル I/O 関連テストを移行
- `load_directory`, `load_file`, `build_kb_section` のテスト

### 4-3. `orchestrator.py` の `run_from_agent_output()` テスト

既存の `test_orchestrator.py` に追加:
- 正常系: チェックポイントファイルから Phase 3-5 が実行できる
- 異常系: チェックポイントファイル不在で FileNotFoundError

### 4-4. 既存テストの維持

`extractor.py`, `scorer.py` のユニットテストは deprecated モジュールとして維持。integration テストは API 不要のためスキップマーク継続。

---

## 修正対象ファイル一覧

| ファイル | 操作 | Wave |
|---------|------|------|
| `src/dev/ca_strategy/_file_utils.py` | **新規** | 1 |
| `src/dev/ca_strategy/validator.py` | **新規** | 1 |
| `.claude/agents/ca-strategy/transcript-claim-extractor.md` | **書き換え** | 2 |
| `.claude/agents/ca-strategy/transcript-claim-scorer.md` | **書き換え** | 2 |
| `.claude/agents/ca-strategy/ca-strategy-lead.md` | **更新** | 2 |
| `src/dev/ca_strategy/orchestrator.py` | **メソッド追加** | 3 |
| `src/dev/ca_strategy/extractor.py` | **Deprecated マーク** | 3 |
| `src/dev/ca_strategy/scorer.py` | **Deprecated マーク** | 3 |
| `src/dev/ca_strategy/_llm_utils.py` | **Deprecated マーク** | 3 |
| `tests/dev/ca_strategy/unit/test_validator.py` | **新規** | 4 |
| `tests/dev/ca_strategy/unit/test_file_utils.py` | **新規** | 4 |
| `tests/dev/ca_strategy/unit/test_orchestrator.py` | **テスト追加** | 4 |

---

## 検証手順

1. `make check-all` — 全チェック（format, lint, typecheck, test）が通ること
2. `uv run pytest tests/dev/ca_strategy/ -v` — 全テスト（603+ テスト）がパスすること
3. `uv run python -m dev.ca_strategy.validator --phase phase1 --input tests/fixtures/sample_claims.json` — CLI が正しく動作すること
4. 既存の integration テスト（extractor, scorer）は `ANTHROPIC_API_KEY` なしでスキップされること

---

## リスクと対策

| リスク | 対策 |
|--------|------|
| エージェントの JSON 出力が Pydantic スキーマに準拠しない | `validator.py` でバリデーション。不正時はエージェントにエラー詳細を返して再生成 |
| 300 銘柄の逐次処理で時間がかかる | ユーザーが容認済み。チェックポイントで中断・再開可能 |
| Deprecated ファイルが残り続ける | 次のメジャーリリースで削除予定のコメントを追加 |
| `_file_utils.py` と `_llm_utils.py` の関数重複 | Wave 3 で `_llm_utils.py` を Deprecated 化し、新コードは `_file_utils.py` を参照 |
