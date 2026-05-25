"""Strategy C 抽出ロジック.

01b_fetch_with_business.ipynb の Cell 4-13 ロジックを関数化したもの。
- get_section: 2 命名規則 (snake_case / Item N) を吸収
- table_to_text / remove_tables_from_text: DOM-level table 除外
- split_subsections: ヒューリスティック subsection 検出
- paragraph_pack: gte-Qwen2 tokenizer ベース packing
"""

from __future__ import annotations

import re
from typing import Any

# =============================================================================
# Section lookup (2 命名規則対応)
# =============================================================================


def get_section(doc: Any, part: str, item: str) -> tuple[Any, str | None]:
    """edgartools の 2 命名規則を吸収する section lookup.

    候補キー:
        1. f"{part_normalized}_{item_normalized}" → "part_i_item_1a"
        2. item → "Item 1A"
        3. item.upper() → "ITEM 1A"

    Returns
    -------
    (section, matched_key) : tuple
        ヒットしなければ (None, None).
    """
    part_norm = part.lower().replace(" ", "_")
    item_norm = item.lower().replace(" ", "_")
    candidates = [
        f"{part_norm}_{item_norm}",
        item,
        item.upper(),
    ]
    for key in candidates:
        sec = doc.sections.get(key)
        if sec is not None:
            return sec, key
    return None, None


# =============================================================================
# Table 除外
# =============================================================================


def table_to_text(table: Any) -> str:
    """TableNode から検索用テキストを再構成."""
    if hasattr(table, "text"):
        t = table.text
        if isinstance(t, str):
            return t
        if callable(t):
            try:
                return t()
            except Exception:
                pass
    if hasattr(table, "content") and isinstance(table.content, str):
        return table.content
    rows = getattr(table, "rows", []) or []
    headers = getattr(table, "headers", []) or []
    parts: list[str] = []
    for h in headers:
        cells = getattr(h, "cells", None) or [h]
        parts.append(" ".join((getattr(c, "content", "") or "").strip() for c in cells))
    for r in rows:
        cells = getattr(r, "cells", []) or []
        parts.append(" ".join((getattr(c, "content", "") or "").strip() for c in cells))
    return "\n".join(p for p in parts if p)


def _norm_ws(s: str) -> str:
    """連続空白 (nbsp 含む) を半角空白 1 個に正規化."""
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


def remove_tables_from_text(section_text: str, tables: list[Any]) -> tuple[str, int]:
    """section text から table 由来テキストを削除.

    Returns
    -------
    (cleaned_text, removed_count) : tuple
    """
    if not tables:
        return section_text, 0

    cleaned = section_text
    removed = 0

    for t in tables:
        try:
            txt = table_to_text(t)
        except Exception:
            continue
        txt = (txt or "").strip()
        if len(txt) < 20:
            continue

        # 戦略 1: 完全一致
        if txt in cleaned:
            cleaned = cleaned.replace(txt, "\n\n[TABLE REMOVED]\n\n", 1)
            removed += 1
            continue

        # 戦略 2: 正規化マッチで anchor 削除
        norm_txt = _norm_ws(txt)
        norm_cleaned = _norm_ws(cleaned)
        if len(norm_txt) >= 30 and norm_txt in norm_cleaned:
            anchor_words = norm_txt[:60].split()[:5]
            if anchor_words:
                pat = re.escape(" ".join(anchor_words)).replace(r"\ ", r"\s+")
                m = re.search(pat, cleaned)
                if m:
                    start = m.start()
                    end_match = cleaned.find("\n\n", start)
                    end = (
                        end_match
                        if end_match >= 0
                        else min(start + len(txt) + 100, len(cleaned))
                    )
                    cleaned = (
                        cleaned[:start] + "\n\n[TABLE REMOVED]\n\n" + cleaned[end:]
                    )
                    removed += 1

    return cleaned, removed


# =============================================================================
# Subsection 検出 (04 + Business 拡張)
# =============================================================================

STRONG_HEADING_PATTERNS = [
    # Risk Factors 系
    r"^Risks?\s+Related\s+to\s+",
    r"^Risks?\s+Relating\s+to\s+",
    r"^Risks?\s+Associated\s+with\s+",
    r"^(Strategic|Operational|Financial|Legal|Regulatory|Market|Macroeconomic|"
    r"Industry|Business|General|Cybersecurity|Tax|Intellectual\s+Property|"
    r"Human\s+Capital|Compliance|Environmental|Climate|Geopolitical|"
    r"Legal\s+and\s+Regulatory\s+Compliance)\s+Risks?\b",
    # MD&A 系
    r"^Overview\b",
    r"^Results\s+of\s+Operations\b",
    r"^Liquidity\s+and\s+Capital\s+Resources\b",
    r"^Critical\s+Accounting\s+(Estimates|Policies|Judgments)\b",
    r"^Recent\s+Accounting\s+Pronouncements\b",
    r"^Off-Balance\s+Sheet\s+Arrangements\b",
    r"^Contractual\s+Obligations\b",
    r"^Foreign\s+Currency\b",
    r"^Segment\s+(Results|Operating\s+Performance|Information)\b",
    # Item 1 Business 系 (v2 新規)
    r"^Products?\b",
    r"^Services\b",
    r"^Markets?\s+and\s+Distribution\b",
    r"^Manufacturing\b",
    r"^Supply\s+(of\s+Components|Chain)\b",
    r"^Research\s+and\s+Development\b",
    r"^Patents,?\s+Trademarks?\b",
    r"^Intellectual\s+Property\b",
    r"^Human\s+Capital(\s+Resources)?\b",
    r"^Employees\b",
    r"^Government\s+Regulation\b",
    r"^Competition\b",
    r"^(Business\s+)?Seasonality\b",
    r"^Available\s+Information\b",
    r"^Corporate\s+(Information|History)\b",
    r"^Operating\s+Segments?\b",
    r"^(Business\s+)?Strategy\b",
    r"^Company\s+Background\b",
    r"^Our\s+Company\b",
    r"^General\b",
    r"^What\s+We\s+Offer\b",
]
STRONG_HEADING_RE = re.compile("|".join(STRONG_HEADING_PATTERNS), re.IGNORECASE)

PAGE_ARTIFACT_PATTERNS = [
    r"\|",
    r"\bForm\s+(?:10|8|11|20|S)-?\s*[KQABFN]?\b",
    r"\bPage\s+\d+\b",
    r"\bAnnual\s+Report\b",
    r"\bQuarterly\s+Report\b",
    r"\bTable\s+of\s+Contents\b",
]
PAGE_ARTIFACT_RE = re.compile("|".join(PAGE_ARTIFACT_PATTERNS), re.IGNORECASE)

TABLE_MARKER_RE = re.compile(
    r"(Three|Six|Nine|Twelve)\s+Months\s+Ended|"
    r"Year(s)?\s+Ended\s+(December|January|June|September|October|November)|"
    r"Fiscal\s+Year\s+Ended|"
    r"Percentage\s*Change|"
    r"\(In\s+millions|"
    r"\(In\s+thousands",
    re.IGNORECASE,
)


def _is_page_artifact(line: str) -> bool:
    return bool(PAGE_ARTIFACT_RE.search(_norm_ws(line)))


def is_table_like(text: str) -> bool:
    """Safety net: DOM 除外をすり抜けた残骸 table を catch."""
    s = _norm_ws(text)
    digit_ratio = sum(c.isdigit() for c in s) / max(len(s), 1)
    # 短くて数字密度高い (ヘッダー残骸)
    if len(s) < 100 and digit_ratio > 0.2:
        return True
    if TABLE_MARKER_RE.search(text):
        multi_space = len(re.findall(r" {3,}", text))
        if digit_ratio > 0.05 or multi_space > 5:
            return True
    if "[TABLE REMOVED]" in text:
        return True
    return False


def _looks_like_heading(line: str) -> bool:
    s = _norm_ws(line)
    if not (5 <= len(s) <= 120):
        return False
    if s[-1] in ".,;:":
        return False
    if s[0].isdigit() or s[0] in ("•", "-", "*"):
        return False
    if re.match(r"^\([a-z]\)|^\([0-9]+\)|^[ivx]+\.", s, re.IGNORECASE):
        return False
    if re.search(r"\s\d{1,4}\s*$", s):
        return False
    if _is_page_artifact(s):
        return False
    words = re.findall(r"[A-Za-z]+", s)
    if not words:
        return False
    cap = sum(1 for w in words if w[0].isupper())
    return cap / len(words) >= 0.6


def _preprocess(text: str) -> str:
    text = re.sub(r"\n[•·]", "\n\n•", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def split_subsections(text: str) -> list[tuple[str, str]]:
    """テキストを (subsection_title, subsection_text) のリストに分割."""
    text = _preprocess(text.strip())
    blocks = text.split("\n\n")

    items: list[tuple[str, str]] = []
    cur_title = ""
    cur_body: list[str] = []

    def flush() -> None:
        if cur_body:
            items.append((cur_title, "\n\n".join(cur_body).strip()))

    for block in blocks:
        b = block.strip()
        if not b:
            continue
        lines = b.split("\n")
        first_line = lines[0].strip()
        if len(lines) == 1:
            if _is_page_artifact(first_line):
                continue
            if STRONG_HEADING_RE.match(first_line) or _looks_like_heading(first_line):
                flush()
                cur_title = first_line
                cur_body = []
                continue
        elif STRONG_HEADING_RE.match(first_line) and not _is_page_artifact(first_line):
            flush()
            cur_title = first_line
            cur_body = []
            rest = "\n".join(lines[1:]).strip()
            if rest:
                cur_body.append(rest)
            continue
        cur_body.append(b)
    flush()

    if not items:
        return [("", text)]
    return items


# =============================================================================
# Paragraph packing
# =============================================================================


def _sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def paragraph_pack(text: str, tokenizer: Any, max_tokens: int = 1024) -> list[str]:
    """段落単位 packing. 単一段落が max 超 → 文単位で強制分割.

    Returns
    -------
    list[str]
        各要素が max_tokens 以下のチャンク.
    """

    def _tok_count(s: str) -> int:
        return len(tokenizer.encode(s, add_special_tokens=False))

    text = text.strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    cur: list[str] = []
    cur_tok = 0
    for p in paragraphs:
        n = _tok_count(p)
        if n > max_tokens:
            if cur:
                chunks.append("\n\n".join(cur))
                cur, cur_tok = [], 0
            sentences = _sentence_split(p)
            sub_cur: list[str] = []
            sub_tok = 0
            for s in sentences:
                sn = _tok_count(s)
                if sub_tok + sn > max_tokens and sub_cur:
                    chunks.append(" ".join(sub_cur))
                    sub_cur, sub_tok = [], 0
                sub_cur.append(s)
                sub_tok += sn
            if sub_cur:
                chunks.append(" ".join(sub_cur))
            continue
        if cur_tok + n > max_tokens and cur:
            chunks.append("\n\n".join(cur))
            cur, cur_tok = [], 0
        cur.append(p)
        cur_tok += n
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def count_tokens(text: str, tokenizer: Any) -> int:
    """単純な token count ユーティリティ."""
    return len(tokenizer.encode(text, add_special_tokens=False))
