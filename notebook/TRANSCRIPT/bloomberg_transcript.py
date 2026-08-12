"""
bloomberg_transcript.py
"""

import json
import re
import shutil
from pathlib import Path
from typing import Optional

import fitz
import pymupdf4llm

# fiscal quarter の英単語 → 数字（モジュールトップに定数として追加）
_FQ_MAP = {"first": 1, "second": 2, "third": 3, "fourth": 4}

# 非英語のトランスクリプトを検出するためのマーカー
_NON_ENGLISH_TITLE_MARKERS = {
    "mandarin": "zh",
    "cantonese": "zh",
    "chinese": "zh",
    "japanese": "ja",
    "korean": "ko",
    "spanish": "es",
    "portuguese": "pt",
    "french": "fr",
    "german": "de",
    "italian": "it",
}

# 役職/肩書きに現れる一般的な単語（人名との判別に使用）
_ROLE_KEYWORDS = {
    # ポジション
    "president",
    "vice",
    "chief",
    "officer",
    "executive",
    "director",
    "manager",
    "head",
    "counsel",
    "general",
    "corporate",
    "secretary",
    "financial",
    "operating",
    "technology",
    "strategy",
    "relations",
    "investor",
    "senior",
    "engineering",
    "software",
    "engineer",
    "founder",
    "chairman",
    "chairperson",
    "board",
    "member",
    "sales",
    "marketing",
    "finance",
    "administrative",
    "development",
    "research",
    "legal",
    "compliance",
    "audit",
    "risk",
    "affairs",
    "communications",
    "advisor",
    "consultant",
    "analyst",
    "interim",
    "acting",
    "associate",
    "assistant",
    "deputy",
    "managing",
    "principal",
    "partner",
    "co-founder",
    "co-ceo",
    "co-president",
    # ドメイン
    "supply",
    "chain",
    "vehicle",
    "product",
    "operations",
    "human",
    "resources",
    "public",
    "external",
    "internal",
    # 地域
    "global",
    "regional",
    "americas",
    "emea",
    "apac",
    "north",
    "south",
    "east",
    "west",
    # 略称
    "ai",
    "hr",
    "it",
    "ir",
    "pr",
    "cfo",
    "ceo",
    "cto",
    "cio",
    "coo",
    "svp",
    "evp",
    "vp",
    # 接続詞・前置詞
    "and",
    "of",
    "the",
    "at",
    "for",
    "in",
    "on",
    "to",
    "&",
    "-",
    # 会社系サフィックス（会社名を人名と誤認しないため）
    "inc",
    "llc",
    "corp",
    "corporation",
    "company",
    "ltd",
    "limited",
    "group",
    "capital",
    "partners",
    "advisors",
    "securities",
    "bank",
    # 地域名（役職に含まれがち）
    "asia",
    "pacific",
    "latin",
    "america",
    "europe",
    "africa",
    "middle",
    "central",
    "japan",
    "china",
    "india",
    "korea",
    "germany",
    "france",
    "uk",
    "us",
    "usa",
    "international",
    "domestic",
    "worldwide",
    # 部門・機能
    "commercial",
    "consumer",
    "enterprise",
    "retail",
    "wholesale",
    "digital",
    "brand",
    "content",
    "media",
    "data",
    "cloud",
    "platform",
    "innovation",
    "quality",
    "safety",
    "manufacturing",
    "logistics",
    "procurement",
    "treasurer",
    "controller",
}

# --- 追加: 話者行パターン用の共通部品 ---
_NAME_PART = r"[A-Z][A-Za-z\.\s\-']+?"
_UNIDENTIFIED_PART = r"Unidentified\s+(?:Speaker|Participant)"

_UNIDENTIFIED_SUFFIX_RE = re.compile(
    rf"\s*{_UNIDENTIFIED_PART}\s*$",
    re.IGNORECASE,
)


def _strip_unidentified_suffix(text: str) -> str:
    """
    参加者の title/firm 末尾に紛れ込んだ
    'Unidentified Speaker' / 'Unidentified Participant' を除去する。

    例:
        "Analyst, HSBC Unidentified Participant" -> "Analyst, HSBC"
        "Head of Investor Relations Unidentified Speaker" -> "Head of Investor Relations"
    """
    if not text:
        return text
    cleaned = _UNIDENTIFIED_SUFFIX_RE.sub("", text)
    return cleaned.rstrip(", \t").strip()


def _looks_like_name_word(w: str) -> bool:
    """人名の1トークンとして妥当か判定"""
    if not w:
        return False
    w_clean = w.rstrip(".,;:").strip()
    if not w_clean:
        return False
    if not w_clean[0].isupper():
        return False
    if w_clean.lower() in _ROLE_KEYWORDS:
        return False
    if not all(c.isalpha() or c in "-'" for c in w_clean):
        return False
    return True


def _find_hidden_participants_in_title(title: str) -> tuple[str, list[dict]]:
    """
    title 文字列内に別人の情報（"Firstname Lastname, Role..."）が混入していないか
    検出し、自分の title と、追加参加者のリストに分離する。

    Bloomberg PDF で BIO ハイパーリンクを持たない参加者が存在する場合、
    直前の参加者の title に次の参加者の情報が吸収されてしまう問題への対処。
    例:  "Chief Executive Officer Karn Budhiraj, Vice President, Supply Chain"
        → ("Chief Executive Officer",
            [{"name": "Karn Budhiraj",
            "title": "Vice President, Supply Chain",
            "bio_id": None}])

    Returns
    -------
    (own_title, extras)
        own_title : str  自分の役職（冒頭部分）のみ
        extras    : list 発見された追加参加者
                        各要素: {"name", "title", "bio_id": None}
    """
    if not title:
        return title, []

    comma_idx = title.find(",")
    if comma_idx < 0:
        return title, []

    before = title[:comma_idx].strip()
    after = title[comma_idx + 1 :].strip()

    words = before.split()
    # 「自分の役職1語以上 + 名前2語」で最低3語必要
    if len(words) < 3:
        return title, []

    # 末尾2単語を「次の参加者の名前候補」とみなす
    candidate = words[-2:]
    if not all(_looks_like_name_word(w) for w in candidate):
        return title, []

    own_part = " ".join(words[:-2]).strip()
    if not own_part:
        return title, []

    # after 側にさらに別人が混入している可能性があるので再帰的に処理
    extra_own_title, more_extras = _find_hidden_participants_in_title(after)
    extras = [
        {
            "name": " ".join(candidate),
            "title": extra_own_title,
            "bio_id": None,
        }
    ] + more_extras

    return own_part, extras


def _detect_language(text: str, title: Optional[str] = None) -> str:
    """
    PDF本文の主要言語を判定して ISO 639-1 相当のコードを返す。

    判定ロジック:
      1. タイトルに "Mandarin"/"Cantonese"/"Japanese" 等の言語名が含まれる場合、
         対応する言語コードを返す。
      2. 本文中の CJK 文字(漢字/かな/ハングル)の比率が 10% を超える場合は
         非英語(暫定 "zh")として扱う。
      3. 上記以外は "en"。

    Returns
    -------
    str
        "en", "zh", "ja", "ko", ... 等の言語コード。
    """
    if title:
        title_lower = title.lower()
        for marker, code in _NON_ENGLISH_TITLE_MARKERS.items():
            if marker in title_lower:
                return code

    if text:
        cjk_count = sum(
            1
            for c in text
            if "\u4e00" <= c <= "\u9fff"  # CJK統合漢字
            or "\u3040" <= c <= "\u309f"  # ひらがな
            or "\u30a0" <= c <= "\u30ff"  # カタカナ
            or "\uac00" <= c <= "\ud7af"  # ハングル
        )
        text_len = len(text.strip())
        if text_len > 0 and (cjk_count / text_len) > 0.10:
            # かな/ハングルが優勢なら細かく判定
            has_kana = any("\u3040" <= c <= "\u30ff" for c in text)
            has_hangul = any("\uac00" <= c <= "\ud7af" for c in text)
            if has_kana:
                return "ja"
            if has_hangul:
                return "ko"
            return "zh"

    return "en"


# --- トランスクリプト特有の定型句パターン ---
# 内容の意味に関係ないフレーズ・司会進行のテンプレート表現を除去する
_BOILERPLATE_PATTERNS = [
    # オペレーター指示関連（括弧の有無・大文字小文字を許容）
    r"\(Operator Instructions\.?\)",
    r"\[Operator Instructions\.?\]",
    r"\(Question And Answer\)",
    r"\[Question And Answer\]",
    # 音声問題・技術トラブル
    r"\(Technical Difficulty\)",
    r"\[Technical Difficulty\]",
    r"\(Inaudible\)",
    r"\[Inaudible\]",
    r"\(inaudible\)",
    r"\(Multiple Speakers\)",
    r"\[Multiple Speakers\]",
    r"\(Foreign Language\)",
    r"\[Foreign Language\]",
    r"\(Background Noise\)",
    # 発言者表記の補足 (Bloomberg特有)
    r"\{BIO\s+\d+\s*<GO>\}",
    r"\{BIO\s+\d+\s*&lt;GO&gt;\}",
    r"\[ph\]",  # phonetic (音のみ聞き取り)
    r"\[sic\]",  # 原文ママ
    r"\[sic-[^\]]+\]",
    # ページヘッダー/フッター残骸
    r"FINAL TRANSCRIPT\s+\d{4}-\d{2}-\d{2}",
    r"FINAL TRANSCRIPT[^\n]*?\([A-Z0-9\.\-/]+\s+[A-Z]{1,3}\s+Equity\)",  # ★ / を追加
    r"Printed on\s+\d{2}-\d{2}-\d{4}\s+Page\s+\d+\s+of\s+\d+",
    r"©\s*COPYRIGHT\s+\d{4},?\s+BLOOMBERG LP\.[^\n]*",
    # 定型あいさつ・お決まり文句
    r"Please go ahead\.?",
    r"Your line is (?:now )?open\.?",
    r"Your question,? please\.?",
    r"You may (?:now )?(?:begin|proceed|disconnect)\.?",
    r"Thank you for (?:standing by|joining|attending)[^\.]*\.",
    r"One moment (?:for our next question|please)\.?",
    r"This concludes (?:today's|our) (?:call|conference|presentation|program)\.?",
    r"Ladies and gentlemen,\s*",
]

# コンパイル済みパターン（大文字小文字無視）
_BOILERPLATE_REGEX = [re.compile(p, flags=re.IGNORECASE) for p in _BOILERPLATE_PATTERNS]


def _extract_full_title(text: str) -> Optional[str]:
    """
    ティッカー行 "...(TICKER XX Equity)" の直後から
    "Company Participants" / "Other Participants" / "Presentation" までの
    複数行にまたがるタイトルを1行に結合して返す。

    例:
    "Wolfe Research 19th Annual Global\nTransportation and Industrials\nConference"
        → "Wolfe Research 19th Annual Global Transportation and Industrials Conference"
    "Annual General Meeting"
        → "Annual General Meeting"
    """
    m = re.search(
        r"\([A-Z0-9\.\-/]+\s+[A-Z]{1,3}\s+Equity\)"
        r"(.*?)"
        r"(?:Company Participants|Other Participants|Presentation)",
        text,
        flags=re.DOTALL | re.IGNORECASE,  # ★ 大小文字を無視
    )
    if not m:
        return None

    block = m.group(1)
    # タイトル領域に紛れ込みがちなヘッダー残骸を除去
    block = re.sub(r"FINAL TRANSCRIPT\s+\d{4}-\d{2}-\d{2}", "", block)
    block = re.sub(r"©\s*COPYRIGHT[^\n]*", "", block)
    block = re.sub(r"Printed on[^\n]*", "", block)

    # 連続空白/改行を1つに正規化
    title = re.sub(r"\s+", " ", block).strip()

    # 最低文字数チェック(意味あるタイトルは3文字以上)
    return title if title and len(title) >= 3 else None


def _classify_document_type(title: Optional[str], quarter: Optional[str]) -> str:
    """
    ドキュメント種別を分類する。
      - "earnings"           : 決算コール(タイトルにQ1/Y/H1/S1等 + "Call")
      - "shareholder_meeting": 株主総会
      - "investor_day"       : Investor Day / Analyst Day / Capital Markets Day
      - "conference"         : カンファレンス・投資家向けイベント (broker主催の一問一答)
      - "webinar"            : 製品/技術系ウェビナー、Product & Innovation セッション等
      - "ma_call"            : M&A / Deal announcement コール
      - "other"              : その他
    """
    if quarter:
        return "earnings"
    if not title:
        return "other"
    t = title.lower()

    # ★ 株主総会
    if any(
        k in t
        for k in (
            "annual general meeting",
            "annual meeting",
            "shareholder",
            "stockholder",
            "extraordinary general meeting",
            "special meeting",
            "agm",
            "egm",
        )
    ):
        return "shareholder_meeting"

    # ★ Investor Day / Analyst Day / Capital Markets Day
    if any(
        k in t
        for k in (
            "investor day",
            "analyst day",
            "capital markets day",
            "capital market day",
            "strategy day",
            "technology day",
            "product day",
        )
    ):
        return "investor_day"

    # ★ ウェビナー / 製品ローンチ / 特別セッション
    if any(
        k in t
        for k in (
            "webinar",
            "product & innovation",
            "product and innovation",
            "innovation session",
            "tech talk",
            "product launch",
            "product update",
        )
    ):
        return "webinar"

    # ★ M&A / 買収・提携発表コール
    if any(
        k in t
        for k in (
            "m&a call",
            "m&a announcement",
            "acquisition call",
            "merger call",
            "deal call",
            "transaction call",
        )
    ):
        return "ma_call"

    # ★ ブローカー主催カンファレンス / 業界サミット
    if any(
        k in t
        for k in (
            "conference",
            "summit",
            "symposium",
            "forum",
            "expo",
        )
    ):
        return "conference"

    return "other"


def _sanitize_filename_component(s: str, max_len: int = 120) -> str:
    """
    ファイル名の一部として使える文字列に整形する。
        - OSで使えない文字 (\\/:*?"<>|) をハイフンに置換
        - 連続空白を1つに圧縮
        - 末尾のドット/空白を除去 (Windows対策)
        - 長すぎる場合は切り詰め
    """
    if not isinstance(s, str) or not s.strip():
        return "Untitled"
    s = re.sub(r'[\\/:*?"<>|]+', "-", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.rstrip(". ")
    if len(s) > max_len:
        s = s[:max_len].rstrip(". ")
    return s or "Untitled"


def _strip_boilerplate(text: str) -> str:
    """
    トランスクリプト特有の内容に関係ない定型句を除去する。

    Parameters
    ----------
    text : str
        除去対象のテキスト。

    Returns
    -------
    str
        定型句を除去し、余分な空白を圧縮したテキスト。
    """
    if not isinstance(text, str) or not text:
        return text

    result = text
    for pat in _BOILERPLATE_REGEX:
        result = pat.sub("", result)

    # 削除後に残る不要な空白・句読点を整形
    result = re.sub(r"[ \t]+", " ", result)  # 連続空白 → 1つ
    result = re.sub(r" *\n *", "\n", result)  # 行頭行末の空白除去
    result = re.sub(r"\n{3,}", "\n\n", result)  # 3行以上の空行 → 2行
    result = re.sub(r"^[ \t,;\.]+", "", result, flags=re.MULTILINE)  # 行頭のゴミ記号
    return result.strip()


def _sanitize_field(value):
    """
    JSON出力用フィールドから マークダウン記号・改行・定型句を除去する。
    transcript_body 以外の全ての文字列フィールドに適用する想定。
    """
    if not isinstance(value, str):
        return value
    s = _strip_boilerplate(value)  # ★ 定型句除去を追加
    s = re.sub(r"#{2,}", "", s)  # マークダウン見出し記号を除去
    s = s.replace("\r", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def process_pdf(pdf_path: Path):
    """
    単一のBloomberg決算トランスクリプトPDFを処理し、構造化されたJSONを出力する。

    処理内容:
        1. PDFから会議メタデータ（日付/ティッカー/四半期/会社名/タイトル）を抽出
        2. 参加者（Company Participants / Other Participants）を抽出
        3. Presentation〜Q&Aセクションの本文をマークダウン化
        4. 発言単位（speaker / role / text）に分割
        5. 話者ごとに集約したビューを作成
        6. 上記すべてを1つのJSONファイル(元PDFと同ディレクトリ、拡張子.json)に保存

    出力JSONの構造:
        {
            "metadata": {
                "source_file": str,
                "date": "YYYY-MM-DD",
                "title": str,
                "company": str,
                "ticker": str,
                "quarter": "Q1 2026" | "Y 2025" | "H1 2026" | "S1 2026" | None,
                "period_type": "quarter" | "annual" | "half" | None,
                "quarter_source": "title" | "body" | None,
                "language": "en" | "zh" | "ja" | ...,
                "document_type": "earnings" | "conference" | "shareholder_meeting" | "other"
            },
            "participants": {
                "company_participants": [{"name", "bio_id", "title"}, ...],
                "other_participants":   [{"name", "bio_id", "firm"},  ...]
            },
            "transcript_body": str,       # マークダウン整形済み本文
            "speeches": [                 # 発言単位のリスト（時系列順）
                {"speaker": str, "role": str, "text": str}, ...
            ],
            "speeches_by_speaker": {      # 話者ごとに集約
                <speaker>: {"role", "speech_count", "texts": [...]}
            }
        }

    Parameters
    ----------
    pdf_path : pathlib.Path
        入力するBloombergトランスクリプトPDFのパス。

    Returns
    -------
    str or None
        処理結果を示すメッセージ:
            - "OK: <filename>"     : 成功
            - "Error <filename>: <理由>" : 例外発生
            - None                 : 入力PDFが存在しない場合
        （現在コメントアウトされている再実行スキップを有効にすると
        "Skip: <filename>" も返り得る）

    Side Effects
    ------------
    - 元PDFと同じディレクトリに `<pdf_path.stem>.json` を作成する。
        既存のJSONは上書きされる。
    - 元PDFファイルは変更しない（読み取り専用）。

    Notes
    -----
    - この関数は例外を送出せず、エラー内容を戻り値の文字列にまとめて返す。
        並列処理（concurrent.futures 等）から呼び出すことを想定しているため、
        1件の失敗が全体を停止させないようになっている。
    - 冪等性を確保したい場合は、関数冒頭の `output_path.exists()` チェックの
        コメントアウトを外して再実行スキップを有効化する。

    Examples
    --------
    >>> from pathlib import Path
    >>> process_pdf(Path("MU-US_2023Q3_2.pdf"))
    'OK: MU-US_2023Q3_2.pdf'

    >>> # 並列実行の例
    >>> from concurrent.futures import ProcessPoolExecutor
    >>> pdfs = list(Path("data").glob("*.pdf"))
    >>> with ProcessPoolExecutor() as ex:
    ...     for result in ex.map(process_pdf, pdfs):
    ...         print(result)
    """

    output_path = pdf_path.with_suffix(".json")
    # if output_path.exists():
    #     return f"Skip: {pdf_path.name}"
    if not pdf_path.exists():
        return None
    try:
        info = extract_transcript_info(str(pdf_path))
        lang = info.get("language", "en")
        if lang != "en":
            return f"Skip (non-English: {lang}): {pdf_path.name}"

        result = extract_transcript(pdf_path)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return f"OK: {pdf_path.name}"
    except Exception as e:
        return f"Error {pdf_path.name}: {e}"


def _parse_quarter_from_title(text: str):
    """タイトル行から Q1/Y/H1/S1 パターンを抽出（S1/S2 = Semester = 半期）"""
    pattern = re.compile(
        r"^\s*((Q[1-4]|Y|H[1-2]|S[1-2])\s+(\d{4})[^\n]*?Call)\s*$",  # ★ S[1-2] を追加
        flags=re.MULTILINE,
    )
    m = pattern.search(text)
    if not m:
        return None
    prefix, year = m.group(2), m.group(3)
    if prefix.startswith("Q"):
        period_type = "quarter"
    elif prefix == "Y":
        period_type = "annual"
    else:  # H1/H2/S1/S2 いずれも「半期」扱い
        period_type = "half"
    return {
        "title": m.group(1).strip(),
        "quarter": f"{prefix} {year}",
        "period_type": period_type,
    }


def _parse_quarter_from_body(text: str):
    """
    本文中の "fiscal (first|second|third|fourth) quarter YYYY" や
    "fiscal year YYYY" / "full year YYYY" から四半期・通期を推定
    """
    # 四半期
    m = re.search(
        r"fiscal\s+(first|second|third|fourth)\s+quarter\s+(\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return {
            "quarter": f"Q{_FQ_MAP[m.group(1).lower()]} {m.group(2)}",
            "period_type": "quarter",
        }

    # 通期
    m = re.search(
        r"(?:full[-\s]year|fiscal\s+year)\s+(\d{4})",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return {"quarter": f"Y {m.group(1)}", "period_type": "annual"}

    return None


def _extract_title_line_fallback(text: str, ticker_line_marker: str = "Equity)"):
    """
    タイトル行に Q1/Y などが含まれない場合、"...(TICKER XX Equity)" 行の
    直後の非空行をタイトルとして採用する。
    例: "Micron's Post Earnings Analyst Call"
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        if ticker_line_marker in ln and i + 1 < len(lines):
            return lines[i + 1]
    return None


def get_participant_names_from_links(pdf_path: Path, page_num: int = 0):
    """PDFのハイパーリンクから参加者名を取得（読み順ソート）"""
    doc = fitz.open(pdf_path)
    page = doc[page_num]

    names = []
    for link in page.get_links():
        uri = link.get("uri", "")
        if "blinks.bloomberg.com" in uri and "BIO" in uri:
            rect = link["from"]
            name = page.get_text("text", clip=rect, sort=True).strip()
            name = re.sub(r"\s+", " ", name)
            # ★ 修正: %20 (URLエンコードされたスペース) を明示的にスキップ
            bio_match = re.search(r"BIO(?:%20|\s)+(\d+)", uri)
            bio_id = bio_match.group(1) if bio_match else None
            if name:
                names.append((name, rect.y0, bio_id))

    doc.close()
    names.sort(key=lambda x: x[1])

    seen = set()
    unique = []
    for n, _, bio in names:
        key = bio or n
        if key not in seen:
            seen.add(key)
            unique.append({"name": n, "bio_id": bio})
    return unique


def split_text_by_names(text: str, names: list[str]):
    positions = []
    for name in names:
        idx = text.find(name)
        if idx >= 0:
            positions.append((idx, name))
    positions.sort()

    results = []
    for i, (idx, name) in enumerate(positions):
        start = idx + len(name)
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        title = text[start:end].strip()
        title = title.lstrip(",").strip().rstrip(",").strip()
        results.append((name, title))
    return results


def rename_and_move_pdf(pdf_path: str | Path, output_dir: str | Path) -> str:
    """
    トランスクリプトPDFを、種別に応じたファイル名で ticker 配下のフォルダに移動する。

    命名規則:
    - 決算コール (document_type == "earnings"):
        {YYYY}{Qn|Yn|Hn|Sn}_{ticker}_{date}.pdf
        例: "2026Q2_TSLA-US_2026-07-23.pdf"
    - その他 (カンファレンス, 株主総会, etc.):
        {date}_{ticker}_{title}.pdf
        例: "2026-05-21_CNR-CN_Wolfe Research 19th Annual Global Transportation and Industrials Conference.pdf"

    Returns
    -------
    str : 実行結果メッセージ ("Moved: ..." / "Skip (already exists): ...")
    """
    pdf_path = Path(pdf_path)
    data = extract_transcript_info(str(pdf_path))

    if not data.get("ticker") or not data.get("date"):
        raise ValueError(
            f"Missing required metadata for renaming: "
            f"ticker={data.get('ticker')}, date={data.get('date')} "
            f"(file={data.get('file')})"
        )

    # ticker はスラッシュ等を含む可能性があるので安全化 (例: "RR/ LN" -> "RR-LN")
    ticker_safe = re.sub(r'[\\/:*?"<>|\s]+', "-", data["ticker"])
    ticker_dir = Path(output_dir) / ticker_safe
    ticker_dir.mkdir(exist_ok=True, parents=True)

    doc_type = data.get("document_type", "other")

    # ファイル名生成は quarter の有無で判別 (document_type には依存しない)
    if data.get("quarter"):
        # 決算コール: {YYYY}{Qn}_{ticker}_{date}_{title}.pdf
        prefix, year = data["quarter"].split()
        quarter_tag = f"{year}{prefix}"

        # ★ タイトルもファイル名に含める
        title_raw = data.get("title")
        if title_raw:
            title_safe = _sanitize_filename_component(title_raw)
            new_name = f"{quarter_tag}_{ticker_safe}_{data['date']}_{title_safe}.pdf"
        else:
            # タイトル取得失敗時のフォールバック(従来の命名)
            new_name = f"{quarter_tag}_{ticker_safe}_{data['date']}.pdf"
    else:
        # 決算以外: {date}_{ticker}_{title}.pdf
        title_raw = data.get("title")
        if not title_raw:
            raise ValueError(
                f"Cannot generate filename: title is missing for non-earnings PDF. "
                f"file={data.get('file')}, ticker={data.get('ticker')}, "
                f"document_type={data.get('document_type')}"
            )
        title_safe = _sanitize_filename_component(title_raw)
        new_name = f"{data['date']}_{ticker_safe}_{title_safe}.pdf"

    new_pdf_path = ticker_dir / new_name

    if new_pdf_path.exists():
        return f"Skip (already exists): {new_pdf_path.name}"

    shutil.move(str(pdf_path), str(new_pdf_path))
    return f"Moved: {pdf_path.name} → {new_pdf_path.name}"


def repair_other_named_pdfs(root_dir: str | Path) -> list[str]:
    """
    既存の '*_Other.pdf' を検出し、PDF本文から正しい title を再抽出して
    リネームし直す。

    Parameters
    ----------
    root_dir : Path
        検索起点ディレクトリ (再帰的に検索)

    Returns
    -------
    list[str]
        処理結果メッセージのリスト
    """
    root_dir = Path(root_dir)
    results = []

    for pdf in root_dir.rglob("*_Other.pdf"):
        try:
            info = extract_transcript_info(str(pdf))
            title = info.get("title")

            if not title or title.lower() == "other":
                results.append(f"Skip (still no title): {pdf.name}")
                continue

            ticker_safe = re.sub(r'[\\/:*?"<>|\s]+', "-", info["ticker"])
            title_safe = _sanitize_filename_component(title)
            new_name = f"{info['date']}_{ticker_safe}_{title_safe}.pdf"
            new_path = pdf.parent / new_name

            if new_path.exists():
                results.append(f"Skip (target exists): {new_name}")
                continue

            shutil.move(str(pdf), str(new_path))
            # 対応するJSONもリネーム
            old_json = pdf.with_suffix(".json")
            new_json = new_path.with_suffix(".json")
            if old_json.exists() and not new_json.exists():
                shutil.move(str(old_json), str(new_json))

            results.append(f"Fixed: {pdf.name} → {new_name}")
        except Exception as e:
            results.append(f"Error {pdf.name}: {e}")

    return results


def extract_transcript_info(pdf_path: str) -> dict:
    """
    Bloombergの決算トランスクリプトPDFから以下の情報を抽出する:
    - date       : 決算コールの日付 (YYYY-MM-DD)
    - ticker     : 銘柄ティッカー (例: MU US, EXTR US, NOKIA FH, SOTL IN)
    - quarter    : 決算コールの区分
                    - 四半期  : "Q1 2026", "Q2 2026" ...
                    - 通期    : "Y 2025"
                    - 半期    : "H1 2026" 等
    - title      : PDFタイトル(そのままの文字列, 例: "Q1 2026 Post Earnings Analyst Call")
    - period_type: "quarter" / "annual" / "half"
    - company    : 会社名
    - file       : ファイル名
    """
    doc = fitz.open(pdf_path)
    text = doc[0].get_text("text", sort=True)
    doc.close()

    # --- 1) 日付 ---
    date_str: Optional[str] = None
    m = re.search(r"FINAL TRANSCRIPT\s+(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if m:
        y, mo, d = m.groups()
        date_str = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    # --- 2) ティッカー & 会社名 ---
    # 注: Bloombergティッカーはクラス表記に "/" を含むことがある
    #     (例: "RR/ LN" for Rolls-Royce, "BRK/A US" for Berkshire Hathaway A)
    company, ticker = None, None
    m = re.search(
        r"^(.*?)\s*\(([A-Z0-9\.\-/]+\s+[A-Z]{1,3})\s+Equity\)",  # ★ / を追加
        text,
        flags=re.MULTILINE,
    )
    if m:
        company = m.group(1).strip()
        # ティッカー内の余分な空白は圧縮しつつスラッシュは維持
        ticker = re.sub(r"\s+", " ", m.group(2)).strip()

    # --- 3) タイトル & 四半期区分 ---
    quarter: Optional[str] = None
    period_type: Optional[str] = None
    title: Optional[str] = None
    quarter_source: Optional[str] = None

    # (1) タイトル行から (Q1 2026 ... Call 形式)
    r = _parse_quarter_from_title(text)
    if r:
        title = r["title"]
        quarter = r["quarter"]
        period_type = r["period_type"]
        quarter_source = "title"
    else:
        # (2) 本文の "fiscal third quarter 2023" 等から抽出
        r = _parse_quarter_from_body(text)
        if r:
            quarter = r["quarter"]
            period_type = r["period_type"]
            quarter_source = "body"

        # ★ 決算コール以外(カンファレンス/株主総会等)にも対応:
        #   複数行にまたがるタイトルをまとめて抽出
        title = _extract_full_title(text)
        if not title:
            # 保険: 従来の単一行フォールバック
            title = _extract_title_line_fallback(text)

    # --- 4) 言語判定 ---
    language = _detect_language(text, title=title)

    # --- 5) ドキュメント種別分類 ---
    document_type = _classify_document_type(title, quarter)

    return {
        "file": Path(pdf_path).name,
        "date": date_str,
        "ticker": _sanitize_field(ticker),
        "quarter": _sanitize_field(quarter),
        "period_type": period_type,
        "title": _sanitize_field(title),
        "company": _sanitize_field(company),
        "quarter_source": quarter_source,
        "language": language,
        "document_type": document_type,  # ★ 追加
    }


def upgrade_earnings_filenames_with_title(root_dir: str | Path) -> list[str]:
    """
    既存の決算コールPDF ({YYYY}{Qn}_{ticker}_{date}.pdf 形式) を検出し、
    title を付加した新形式にリネームする。

    正規表現で以下のパターンにマッチするファイルが対象:
      YYYYQn_TICKER_YYYY-MM-DD.pdf
      YYYYY_TICKER_YYYY-MM-DD.pdf      (通期)
      YYYYSn_TICKER_YYYY-MM-DD.pdf     (半期)
      YYYYHn_TICKER_YYYY-MM-DD.pdf     (半期)
    """
    root_dir = Path(root_dir)
    results = []

    pattern = re.compile(
        r"^(\d{4}(?:Q[1-4]|Y|H[1-2]|S[1-2]))_"
        r"([A-Z0-9\-]+)_"
        r"(\d{4}-\d{2}-\d{2})\.pdf$"
    )

    for pdf in root_dir.rglob("*.pdf"):
        m = pattern.match(pdf.name)
        if not m:
            continue

        try:
            info = extract_transcript_info(str(pdf))
            title = info.get("title")
            if not title:
                results.append(f"Skip (no title): {pdf.name}")
                continue

            quarter_tag, ticker_safe, date_str = m.groups()
            title_safe = _sanitize_filename_component(title)
            new_name = f"{quarter_tag}_{ticker_safe}_{date_str}_{title_safe}.pdf"

            if new_name == pdf.name:
                results.append(f"Skip (already up-to-date): {pdf.name}")
                continue

            new_path = pdf.parent / new_name
            if new_path.exists():
                results.append(f"Skip (target exists): {new_name}")
                continue

            # PDFをリネーム
            shutil.move(str(pdf), str(new_path))

            # 対応するJSONも一緒にリネーム
            old_json = pdf.with_suffix(".json")
            new_json = new_path.with_suffix(".json")
            if old_json.exists() and not new_json.exists():
                shutil.move(str(old_json), str(new_json))

            results.append(f"Upgraded: {pdf.name} → {new_name}")
        except Exception as e:
            results.append(f"Error {pdf.name}: {e}")

    return results


def diagnose_pdf_title(pdf_path: str | Path) -> dict:
    """
    PDFの1ページ目のテキストと title 抽出結果を確認するためのデバッグ関数。
    """
    doc = fitz.open(pdf_path)
    text = doc[0].get_text("text", sort=True)
    doc.close()

    # 実際のテキストの最初の30行を表示
    lines = [ln for ln in text.splitlines()][:30]

    # title 抽出を試す
    title_from_full = _extract_full_title(text)
    title_from_fallback = _extract_title_line_fallback(text)

    print(f"\n=== {Path(pdf_path).name} ===")
    print("First 30 lines of extracted text:")
    for i, ln in enumerate(lines, 1):
        print(f"  {i:2d}: {ln!r}")
    print(f"\n_extract_full_title()          = {title_from_full!r}")
    print(f"_extract_title_line_fallback() = {title_from_fallback!r}")

    return {
        "text_head": lines,
        "title_full": title_from_full,
        "title_fallback": title_from_fallback,
    }


def extract_transcript_info_list(pdf_paths: list) -> list:
    """複数PDFをまとめて処理"""
    return [extract_transcript_info(p) for p in pdf_paths]


def extract_participants(pdf_path: Path, md_text: str) -> dict:
    """
    参加者情報を辞書形式で抽出。

    複数のセクション終端候補に対応し、Other Participants が存在しない
    PDFでも Company Participants を正しく抽出できる。
    """
    all_names = get_participant_names_from_links(pdf_path)
    name_to_bio = {p["name"]: p["bio_id"] for p in all_names}
    all_name_list = [p["name"] for p in all_names]

    # ★ セクション終端を「複数候補」に変更
    #   最初に見つかったマーカーで終了とする
    sections = {
        "company_participants": (
            "Company Participants",
            ["Other Participants", "Presentation"],  # ★ 候補リスト
        ),
        "other_participants": (
            "Other Participants",
            ["Presentation"],
        ),
    }

    result = {"company_participants": [], "other_participants": []}

    for key, (section_name, end_markers) in sections.items():
        # 開始位置を探す
        start_pattern = re.escape(section_name)
        start_match = re.search(start_pattern, md_text)
        if not start_match:
            continue
        start_pos = start_match.end()

        # ★ 最も早く出現する終端マーカーを探す
        end_pos = len(md_text)
        for marker in end_markers:
            m = re.search(re.escape(marker), md_text[start_pos:])
            if m:
                candidate_pos = start_pos + m.start()
                end_pos = min(end_pos, candidate_pos)

        block = md_text[start_pos:end_pos]

        # マークダウンの箇条書き記号を除去
        cleaned = re.sub(r"^\s*-\s*", " ", block, flags=re.MULTILINE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # ★ 戦略A: BIOリンクから取得した名前をアンカーとして分割
        names_in_section = [n for n in all_name_list if n in cleaned]

        pairs = []
        if names_in_section:
            pairs = split_text_by_names(cleaned, names_in_section)

        # ★ 戦略B: BIOリンクがない参加者も救う
        #   1行に "Name1, Title1 Name2, Title2 ..." が詰め込まれている場合、
        #   BIOリンクありの名前で split した後の title 内に別人が混入している可能性
        for name, title in pairs:
            entry_list = _split_multi_participants_in_block(name, title, name_to_bio)
            for entry_name, entry_title in entry_list:
                _append_participant(
                    result[key], entry_name, entry_title, name_to_bio, key
                )

        # ★ 戦略C: BIOリンクありの名前が1つも見つからなかった場合、
        #   ブロック全体をカンマパースで解釈
        if not pairs and cleaned:
            for entry_name, entry_title in _parse_participants_from_block(cleaned):
                _append_participant(
                    result[key], entry_name, entry_title, name_to_bio, key
                )

    return result


def _split_multi_participants_in_block(name, title, name_to_bio):
    """
    1つの "name, title" ペアから、title 内に別人が混入している場合に分割する。
    例: name="Alok Deshpande",
        title="Director, Camera and Photos Software Engineering Ann Thai, Senior Director, Marketplace Platforms"
      → [("Alok Deshpande", "Director, Camera and Photos Software Engineering"),
         ("Ann Thai", "Senior Director, Marketplace Platforms")]

    BIOリンク付きの既知の名前がある場合、その位置で切る。
    """
    result = [(name, title)]

    # title 内に既知の参加者名(BIO付き)がないか確認
    known_names_in_title = []
    for known_name in name_to_bio.keys():
        if known_name == name:
            continue
        idx = title.find(known_name)
        if idx > 0:  # 先頭ではなく途中に出現
            known_names_in_title.append((idx, known_name))

    if not known_names_in_title:
        return result

    # 位置順にソートして分割
    known_names_in_title.sort()

    result = []
    current_name = name
    current_start = 0
    for idx, next_name in known_names_in_title:
        # current_name の title は current_start から idx 直前まで
        current_title = title[current_start:idx].strip()
        # 末尾のカンマ等を除去
        current_title = current_title.rstrip(", \t")
        result.append((current_name, current_title))
        current_name = next_name
        current_start = idx + len(next_name)
        # 先頭カンマ等をスキップ
        current_start_str = title[current_start:].lstrip(", \t")
        current_start = len(title) - len(current_start_str)

    # 最後
    last_title = title[current_start:].strip().rstrip(", \t").lstrip(", \t")
    result.append((current_name, last_title))

    return result


def _parse_participants_from_block(block: str) -> list[tuple[str, str]]:
    """
    参加者セクションブロックが「BIOリンクなし」で、カンマ区切りで並んでいる場合に、
    "Firstname Lastname, Title..." のパターンをヒューリスティックに抽出する。

    ヒント: 参加者名は "大文字始まりの単語 が2〜4語連続" である傾向がある。
    """
    result = []
    # "大文字始まりの2〜4語" のシーケンスを検出
    #   例: "Alok Deshpande" "Sumbul Ahmad Desai" "Sebastien Marineau-Mes"
    name_pattern = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z\-]+){1,3})\b")

    matches = list(name_pattern.finditer(block))
    if not matches:
        return result

    for i, m in enumerate(matches):
        name = m.group(1)
        # 明らかにセクション名などはスキップ
        if name in ("Company Participants", "Other Participants", "Presentation"):
            continue
        # 次の名前まで、または末尾まで
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
        title = block[start:end].strip()
        # 先頭のカンマ・区切り文字を除去
        title = title.lstrip(", \t").rstrip(", \t")
        if name and len(name.split()) >= 2:  # 2語以上を有効な人名とみなす
            result.append((name, title))

    return result


def _append_participant(target_list, name, title, name_to_bio, section_key):
    """participants リストにエントリを追加する共通処理"""
    if not name:
        return
    if name in ("Company Participants", "Other Participants", "Presentation"):
        return

    title = re.sub(r"\s*#+\s*$", "", title).strip()
    title = title.replace("&amp;", "&").replace("&#x27;", "'")

    # title 内に別人が混入している場合を分離
    own_title, hidden_extras = _find_hidden_participants_in_title(title)
    # ★ 追加: Unidentified Speaker/Participant の紛れ込みを除去
    title = _strip_unidentified_suffix(own_title)

    entry = {
        "name": _sanitize_field(name),
        "bio_id": name_to_bio.get(name),
    }
    if section_key == "company_participants":
        entry["title"] = _sanitize_field(title)
    else:
        entry["firm"] = _sanitize_field(title)
    target_list.append(entry)

    for extra in hidden_extras:
        extra_title = _strip_unidentified_suffix(extra["title"])  # ★ 追加
        extra_entry = {
            "name": _sanitize_field(extra["name"]),
            "bio_id": name_to_bio.get(extra["name"]),
        }
        if section_key == "company_participants":
            extra_entry["title"] = _sanitize_field(extra_title)
        else:
            extra_entry["firm"] = _sanitize_field(extra_title)
        target_list.append(extra_entry)


def clean_markdown_text(md_text: str) -> str:
    """マークダウンから発言抽出用のプレーンテキストを作成"""
    text = md_text

    # コピーライト削除
    text = re.sub(r"©\s*COPYRIGHT.*?expressly prohibited\.", "", text, flags=re.DOTALL)
    text = re.sub(r"Printed on \d+-\d+-\d+ Page \d+ of \d+", "", text)

    # 単独行の日付（YYYY-MM-DD）を削除
    text = re.sub(r"^\s*\d{4}-\d{2}-\d{2}\s*$", "", text, flags=re.MULTILINE)

    # "FINAL TRANSCRIPT [Company] (TICKER XX Equity)" ヘッダー残骸を削除
    # - 行アンカー ^...$ を外し、行内でもマッチ
    # - 取引所コード (US/HK/FH/JT/SW 等) を汎用化
    # - 前後の空行/改行も一緒に吸収
    text = re.sub(
        r"\s*FINAL TRANSCRIPT[^\n]*?\([A-Z0-9\.\-/]+\s+[A-Z]{1,3}\s+Equity\)\s*",  # ★ / を追加
        " ",
        text,
        flags=re.IGNORECASE,
    )

    # HTMLエンティティ
    text = text.replace("&amp;", "&").replace("&#x27;", "'")
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')

    # マークダウンリンク [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # 取り消し線 ~~text~~ → text
    text = re.sub(r"~~([^~]+)~~", r"\1", text)

    # 過剰な空行を圧縮
    text = re.sub(r"\n{3,}", "\n\n", text)

    # BIOタグの内部スペース・改行を正規化
    # 例:
    #   "{ BIO 16900434 < GO > }"     → "{BIO 16900434 <GO>}"
    #   "{\n BIO 16900434 <GO>\n}"    → "{BIO 16900434 <GO>}"
    # re.DOTALL で改行もマッチ対象に含める
    text = re.sub(
        r"\{\s*BIO\s+(\d+)\s*<\s*GO\s*>\s*\}",
        r"{BIO \1 <GO>}",
        text,
        flags=re.DOTALL,
    )

    return text


def extract_transcript_body(cleaned_text: str) -> str:
    """本文（Presentation以降～Disclaimerまで）を抽出"""
    pres_match = re.search(r"\bPresentation\b", cleaned_text)
    start_pos = pres_match.start() if pres_match else 0

    end_match = re.search(r"This transcript may not be", cleaned_text)
    end_pos = end_match.start() if end_match else len(cleaned_text)

    body = cleaned_text[start_pos:end_pos].strip()

    # セクション見出しをマークダウン化（既に "## " が付いていても正規化）
    body = re.sub(
        r"^\s*#*\s*Presentation\s*$",
        "## Presentation",
        body,
        flags=re.MULTILINE,
    )
    body = re.sub(
        r"^\s*#*\s*Questions And Answers\s*$",
        "## Questions And Answers",
        body,
        flags=re.MULTILINE,
    )

    # 過剰な空行を圧縮
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body


def extract_speeches(cleaned_text: str, participants: dict) -> list:
    """発言を(speaker, role, text)のリストで抽出"""
    company_names = {p["name"]: p for p in participants["company_participants"]}
    other_names = {p["name"]: p for p in participants["other_participants"]}

    pres_match = re.search(r"\bPresentation\b", cleaned_text)
    start_pos = pres_match.end() if pres_match else 0

    end_match = re.search(r"This transcript may not be", cleaned_text)
    end_pos = end_match.start() if end_match else len(cleaned_text)

    body = cleaned_text[start_pos:end_pos]

    lines = body.split("\n")
    segments = []
    current_speaker = None
    current_role = None
    current_buffer = []

    # ★ 埋め込み検出: BIO付き名前 or Unidentified Speaker/Participant
    embedded_pattern = re.compile(
        rf"([QA])\s*-\s*(?:"
        rf"({_NAME_PART})\s*\{{\s*BIO\s+(\d+)\s*<\s*GO\s*>\s*\}}"
        rf"|"
        rf"({_UNIDENTIFIED_PART})"
        rf")",
        re.IGNORECASE,
    )

    def flush():
        if not (current_speaker and current_buffer):
            return

        content = "\n".join(current_buffer).strip()

        matches = list(embedded_pattern.finditer(content))

        if matches:
            # 最初の match より前は current_speaker の発言
            first = matches[0]
            head_text = content[: first.start()].strip()
            head_text = _strip_boilerplate(head_text)
            head_text = _sanitize_field(head_text)
            if head_text:
                segments.append(
                    {
                        "speaker": _sanitize_field(current_speaker),
                        "role": current_role,
                        "text": head_text,
                    }
                )

            for i, m in enumerate(matches):
                if m.group(2):  # BIO付き名前
                    name = m.group(2).strip()
                    bio = m.group(3)
                else:  # Unidentified Speaker/Participant
                    name = m.group(4).strip()
                    bio = None
                spk, role = resolve_speaker(name, bio, company_names, other_names)

                body_start = m.end()
                body_end = (
                    matches[i + 1].start() if i + 1 < len(matches) else len(content)
                )
                body_text = content[body_start:body_end].strip()
                body_text = _strip_boilerplate(body_text)
                body_text = _sanitize_field(body_text)
                if body_text:
                    segments.append(
                        {
                            "speaker": _sanitize_field(spk),
                            "role": role,
                            "text": body_text,
                        }
                    )
            return

        # 通常処理（埋め込みなし）
        content = _strip_boilerplate(content)
        content = _sanitize_field(content)
        if content:
            segments.append(
                {
                    "speaker": _sanitize_field(current_speaker),
                    "role": current_role,
                    "text": content,
                }
            )

    # ★ 名前パターンにハイフン/アポストロフィを許可
    re_bio = re.compile(
        rf"^#*\s*({_NAME_PART})\s*"
        r"\{\s*BIO\s+(\d+)\s*<\s*GO\s*>\s*\}\s*$"
    )
    re_qa = re.compile(
        rf"^#*\s*[QA]\s*-\s*({_NAME_PART})\s*"
        r"\{\s*BIO\s+(\d+)\s*<\s*GO\s*>\s*\}\s*$"
    )
    # ★ 追加: BIOなしの Unidentified 話者
    re_qa_unid = re.compile(
        rf"^#*\s*[QA]\s*-\s*({_UNIDENTIFIED_PART})\s*$",
        re.IGNORECASE,
    )
    re_unid_alone = re.compile(
        rf"^#*\s*({_UNIDENTIFIED_PART})\s*$",
        re.IGNORECASE,
    )
    re_operator = re.compile(r"^#*\s*Operator\s*$")
    re_qa_section = re.compile(
        r"^#*\s*(Questions And Answers|\(Question And Answer\))\s*$"
    )

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_buffer.append("")
            continue

        m = re_bio.match(stripped)
        if m:
            flush()
            name = m.group(1).strip()
            bio = m.group(2)
            current_speaker, current_role = resolve_speaker(
                name, bio, company_names, other_names
            )
            current_buffer = []
            continue

        m = re_qa.match(stripped)
        if m:
            flush()
            name = m.group(1).strip()
            bio = m.group(2)
            current_speaker, current_role = resolve_speaker(
                name, bio, company_names, other_names
            )
            current_buffer = []
            continue

        # ★ 追加: "Q - Unidentified Participant" / "A - Unidentified Speaker"
        m = re_qa_unid.match(stripped)
        if m:
            flush()
            name = m.group(1).strip()
            current_speaker, current_role = resolve_speaker(
                name, None, company_names, other_names
            )
            current_buffer = []
            continue

        # ★ 追加: 単独行の "Unidentified Speaker" / "Unidentified Participant"
        m = re_unid_alone.match(stripped)
        if m:
            flush()
            name = m.group(1).strip()
            current_speaker, current_role = resolve_speaker(
                name, None, company_names, other_names
            )
            current_buffer = []
            continue

        if re_operator.match(stripped):
            flush()
            current_speaker = "Operator"
            current_role = "operator"
            current_buffer = []
            continue

        if re_qa_section.match(stripped):
            flush()
            current_speaker = None
            current_role = None
            current_buffer = []
            continue

        current_buffer.append(stripped)

    flush()
    return segments


def build_speeches_by_speaker(speeches: list) -> dict:
    """発言リストを話者ごとにグループ化した辞書を作成"""
    by_speaker = {}
    for s in speeches:
        speaker = s["speaker"]
        if speaker not in by_speaker:
            by_speaker[speaker] = {
                "role": s["role"],
                "speech_count": 0,
                "texts": [],
            }
        by_speaker[speaker]["texts"].append(s["text"])
        by_speaker[speaker]["speech_count"] += 1
    return by_speaker


def resolve_speaker(name: str, bio: str, company_names: dict, other_names: dict):
    """話者名からロール(company/analyst/operator/unidentified)を判定"""

    # ★ 追加: Unidentified Speaker / Participant を独立話者として扱う
    if re.match(r"Unidentified\s+Speaker", name, re.IGNORECASE):
        return "Unidentified Speaker", "company_unidentified"
    if re.match(r"Unidentified\s+Participant", name, re.IGNORECASE):
        return "Unidentified Participant", "analyst_unidentified"

    # BIO IDで照合
    for p_name, p in company_names.items():
        if p.get("bio_id") == bio:
            return p_name, "company"
    for p_name, p in other_names.items():
        if p.get("bio_id") == bio:
            return p_name, "analyst"

    # 名前一致（部分一致含む）
    for p_name in company_names:
        if name in p_name or p_name in name:
            return p_name, "company"
    for p_name in other_names:
        if name in p_name or p_name in name:
            return p_name, "analyst"

    return name, "unknown"


def extract_metadata(
    md_text: str, filename: str, pdf_path: Optional[Path] = None
) -> dict:
    """タイトル・日付・企業名・四半期を抽出（本文フォールバック対応）"""
    meta = {"source_file": str(pdf_path) if pdf_path else filename}

    # PDFパスが渡っていれば extract_transcript_info を再利用
    if pdf_path is not None:
        info = extract_transcript_info(str(pdf_path))
        meta.update(
            {
                "date": info.get("date"),
                "title": info.get("title"),
                "company": info.get("company"),
                "ticker": info.get("ticker"),
                "quarter": info.get("quarter"),
                "period_type": info.get("period_type"),
                "quarter_source": info.get("quarter_source"),
                "language": info.get("language"),
                "document_type": info.get("document_type"),  # ★ 追加
            }
        )
        return meta

    # フォールバック: md_text のみから抽出
    m = re.search(r"(\d{4}-\d{2}-\d{2})\s+FINAL TRANSCRIPT", md_text)
    if m:
        meta["date"] = m.group(1)

    # タイトル: Q1 2026 ... Call 形式を優先
    m = re.search(r"((?:Q[1-4]|Y|H[1-2]|S[1-2])\s+\d{4}[^\n]*?Call)", md_text)
    if m:
        meta["title"] = _sanitize_field(m.group(1))
    else:
        # 本文の "fiscal (first|...) quarter YYYY"
        m2 = re.search(
            r"fiscal\s+(first|second|third|fourth)\s+quarter\s+(\d{4})",
            md_text,
            flags=re.IGNORECASE,
        )
        if m2:
            meta["quarter"] = f"Q{_FQ_MAP[m2.group(1).lower()]} {m2.group(2)}"
            meta["period_type"] = "quarter"

    m = re.search(
        r"FINAL TRANSCRIPT\s+(.+?\s*\([A-Z0-9\.\-/]+\s+[A-Z]{1,3}\s+Equity\))",  # ★ / を追加
        md_text,
    )
    if m:
        meta["company"] = _sanitize_field(m.group(1))

    # 本文からもう一度言語判定（フォールバック時）
    meta.setdefault("language", _detect_language(md_text, title=meta.get("title")))

    return meta


def extract_transcript(pdf_path: Path) -> dict:
    """PDFから完全な構造化データを抽出"""
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    doc.close()

    md_text = pymupdf4llm.to_markdown(pdf_path, pages=list(range(num_pages)))
    cleaned_text = clean_markdown_text(md_text)

    # pdf_path を渡してフォールバックを効かせる
    metadata = extract_metadata(md_text, pdf_path.name, pdf_path=pdf_path)

    participants = extract_participants(pdf_path, md_text)
    speeches = extract_speeches(cleaned_text, participants)
    transcript_body = extract_transcript_body(cleaned_text)
    speeches_by_speaker = build_speeches_by_speaker(speeches)

    return {
        "metadata": metadata,
        "participants": participants,
        "transcript_body": transcript_body,
        "speeches": speeches,
        "speeches_by_speaker": speeches_by_speaker,
    }
