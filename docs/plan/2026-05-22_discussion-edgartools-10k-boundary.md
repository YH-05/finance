# 議論メモ: edgartools 10-K Item 1A 境界バグの調査と対処方針

**日付**: 2026-05-22
**議論ID**: `disc-2026-05-22-edgartools-10k-boundary`
**対象**: `notebook/FILING_NLP/04_hierarchical_chunking.ipynb`
**状態**: 議論中断（実装は後日）

## 背景・コンテキスト

`04_hierarchical_chunking.ipynb` で 10-K Item 1A の階層チャンキングを実装中、AMAT (Applied Materials) の最新 10-K で Item 1A の subsection 検出結果に Item 1B/1C の内容が混入していることが判明した。

```
【AMAT】 10-K 2025-12-12 Item 1A:
  [ 0] Item 1A: Risk Factors                | 284 chars
  [ 1] Business and Industry Risks          | 37348 chars
  [ 2] Operational and Financial Risks      | 23812 chars
  [ 3] Legal, Compliance and Other Risks    | 6883 chars
  [ 4] Item 1B: Unresolved Staff Comments   | 5 chars       ← 混入
  [ 5] Risk Management and Strategy         | 2682 chars    ← Item 1C 由来
  [ 6] Governance                           | 2263 chars    ← Item 1C 由来
```

## 根本原因の特定

調査の結果、edgartools v5.x 側の不具合（新パーサの未対応）が原因と確定。

### 決定的な事実

- AMAT 10-K (filing 0001628280-25-056742):
  - `get_item_with_part('Part I', 'Item 1A')` が 73578 chars 返す
  - うち pos 68510 から `Item 1B:` 見出し、pos 68558 から `Item 1C:` 見出しが含まれる
- `obj.items` = `['Item 1', 'Item 1A', 'Item 2', 'Item 3', 'Item 7', 'Item 8']`
  - **Item 1B と Item 1C が認識されていない**
- edgartools の境界判定アルゴリズムは「次に認識した Item の位置までを返す」設計
- そのため Item 1A の境界が Item 2 まで広がり、その間にある Item 1B + Item 1C のテキスト約 5068 chars が巻き込まれる

### なぜ filer 依存か

- MSFT/AAPL 等は heading 用の HTML 構造（h2 や bold タグ）を使っているため Item 1B/1C が正しく認識される
- AMAT は本文と同じマークアップで Item 1B/1C を書いている可能性が高く、edgartools の新パーサのパターン抽出と合っていない

## 議論のサマリー

### 対処の選択肢と評価

| 案 | 概要 | A: filer 別構成 | B: フォーマット差 | C: 本文中参照 | D: エンコーディング | E: edgartools 認識精度 |
|---|------|---|---|---|---|---|
| ① hardcoded 候補のみで切り詰め | 標準的な next-item 候補で固定 | ○ | ○ | ○ | ○ | ◎ |
| ② `obj.items` のみで切り詰め | 動的な候補のみ | ✕ AMAT で破綻 | ◎ | ◎ | ○ | ✕ |
| **③ hybrid (hardcoded + obj.items)** | 両方を merge | ◎ | ○ | ○ | ○ | ◎ |
| **④ ③ + sanity check** | 切り詰めすぎ防止 | ◎ | ○ | ○ | ○ | ◎ |

### なぜ案 ④ がロバストか

1. **行頭アンカー (`(?:\n[ \t]*|\A)`)**: 本文中の "see Item 1B" 等の inline 参照を無視
2. **区切り文字の柔軟マッチ (`[\s.:–\-]`)**: `Item 1B.` / `Item 1B:` / `Item 1B ` / `Item 1B–` 全てに対応
3. **複数候補の最早出現位置で切る**: filer 別バリエーション (1B 無し / 1D 有り) に対応
4. **`obj.items` から動的補完**: edgartools が認識した non-standard Item も拾える
5. **Sanity check (min_chars=500)**: 切り詰めすぎを検知して元テキストを保持

## 決定事項

| ID | 内容 | コンテキスト |
|----|------|------------|
| `dec-2026-05-22-001` | hybrid 案 ④ を採用 | edgartools の upstream 修正を待たず、自前で境界クリーンアップする方針。trim_to_next_item 関数 + sanity check で実装。 |

## アクションアイテム

| ID | 内容 | 優先度 |
|----|------|--------|
| `act-2026-05-22-001` | `trim_to_next_item(text, candidates)` 関数を実装 | high |
| `act-2026-05-22-002` | `NEXT_ITEM_CANDIDATES` 辞書 + `_candidate_next_items()` 動的補完ロジック | high |
| `act-2026-05-22-003` | Cell 4 への組み込み + `trim_log` 記録 + sanity check | high |
| `act-2026-05-22-004` | 実装後の検証: AMAT 以外で境界ズレが発生する filer の発掘 | medium |

## 実装の設計詳細

### NEXT_ITEM_CANDIDATES

```python
NEXT_ITEM_CANDIDATES = {
    ("10-K", "item_1a"): ["Item 1B", "Item 1C", "Item 1D", "Item 1E", "Item 2"],
    ("10-K", "item_7"):  ["Item 7A", "Item 8"],
    ("10-Q", "item_1a"): ["Item 2", "Item 3", "Item 4", "Item 5", "Item 6"],
    ("10-Q", "item_7"):  ["Item 3", "Item 4"],
}

CURRENT_ITEM_LABEL = {"item_1a": "Item 1A", "item_7": "Item 7"}
```

### trim_to_next_item

```python
def trim_to_next_item(text: str, candidates: list[str]) -> tuple[str, str | None, int]:
    if not candidates:
        return text, None, 0
    earliest = None
    matched = None
    for cand in candidates:
        pat = rf"(?im)(?:\n[ \t]*|\A){re.escape(cand)}\b[\s.:–\-]"
        m = re.search(pat, text)
        if not m:
            continue
        pos = m.start()
        while pos < len(text) and text[pos] in "\n\r \t":
            pos += 1
        if earliest is None or pos < earliest:
            earliest = pos
            matched = cand
    if earliest is None:
        return text, None, 0
    trimmed = text[:earliest].rstrip()
    return trimmed, matched, len(text) - len(trimmed)
```

### hybrid 候補生成

```python
def _candidate_next_items(obj, form: str, key: str) -> list[str]:
    candidates = list(NEXT_ITEM_CANDIDATES.get((form, key), []))
    cur_label = CURRENT_ITEM_LABEL.get(key)
    if cur_label and hasattr(obj, "items"):
        try:
            obj_items = list(obj.items) if obj.items else []
            cur_idx = obj_items.index(cur_label)
            for it in obj_items[cur_idx + 1:]:
                if it not in candidates:
                    candidates.append(it)
        except (ValueError, AttributeError):
            pass
    return candidates
```

### Cell 4 への組み込み

```python
text = obj.get_item_with_part(part, item, markdown=False)
if isinstance(text, str) and text:
    candidates = _candidate_next_items(obj, form, key)
    trimmed, matched, n_trim, sanity_ok = trim_with_sanity(text, candidates)
    if matched and sanity_ok:
        trim_log.append({
            "ticker": ticker, "filing_id": fid, "form": form,
            "item_key": key, "matched_next": matched,
            "trimmed_chars": n_trim,
        })
        text = trimmed
    section_rows.append({...})
```

## 次回の議論トピック

- 実装後の trim_log 検証結果のレビュー
- AMAT 以外で発見された境界ズレ filer への対応方針
- 案 ④ のサニティチェック閾値 (min_chars=500) の妥当性検証
- edgartools 本体への issue 起票の要否

## 参考情報

- edgartools 警告メッセージ: `TenK falling back to legacy parser for 'Item 1A' (filing: ...). New parser sections available: [...]. This fallback will be removed in v6.0.`
- 関連ソース: `.venv/lib/python3.12/site-packages/edgar/company_reports/ten_k.py:508-514`
- 関連ノートブック: `notebook/FILING_NLP/04_hierarchical_chunking.ipynb`
- 関連メモリ: なし (新規論点)
