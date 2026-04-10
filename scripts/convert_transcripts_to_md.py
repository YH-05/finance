"""Transcript PDF → Markdown 一括変換スクリプト.

analyst/Investment Thesis_sample/ 配下の全Transcript PDFをテキスト抽出し、
同じディレクトリに同名の .md ファイルとして出力する。

Usage:
    uv run python scripts/convert_transcripts_to_md.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pymupdf

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path("analyst/Investment Thesis_sample")


def extract_text_from_pdf(pdf_path: Path) -> str:
    """PDF からテキストを完全抽出し Markdown 形式で返す."""
    doc = pymupdf.open(str(pdf_path))
    pages: list[str] = []
    for i, page in enumerate(doc, 1):
        text = page.get_text("text")
        if text.strip():
            pages.append(f"<!-- Page {i} -->\n\n{text.strip()}")
    doc.close()
    return "\n\n---\n\n".join(pages)


def convert_single(pdf_path: Path) -> Path | None:
    """単一の PDF を Markdown に変換する."""
    # .pdf.pdf → .md（二重拡張子に対応）
    name = pdf_path.name
    if name.endswith(".pdf.pdf"):
        md_name = name[: -len(".pdf.pdf")] + ".md"
    elif name.endswith(".pdf"):
        md_name = name[: -len(".pdf")] + ".md"
    else:
        logger.warning("Unexpected extension: %s", pdf_path)
        return None

    md_path = pdf_path.parent / md_name
    if md_path.exists():
        logger.debug("Already exists, skipping: %s", md_path)
        return md_path

    try:
        text = extract_text_from_pdf(pdf_path)
        md_path.write_text(text, encoding="utf-8")
        logger.info("Converted: %s", md_path.name)
        return md_path
    except Exception:
        logger.exception("Failed to convert: %s", pdf_path)
        return None


def main() -> None:
    """全 Transcript PDF を Markdown に変換する."""
    if not BASE_DIR.exists():
        logger.error("Base directory not found: %s", BASE_DIR)
        sys.exit(1)

    pdf_files = sorted(BASE_DIR.rglob("*.pdf"))
    if not pdf_files:
        logger.error("No PDF files found in %s", BASE_DIR)
        sys.exit(1)

    logger.info("Found %d PDF files", len(pdf_files))

    converted = 0
    skipped = 0
    failed = 0

    for pdf_path in pdf_files:
        # .DS_Store等を除外
        if pdf_path.name.startswith("."):
            continue

        result = convert_single(pdf_path)
        if result is None:
            failed += 1
        elif result.stat().st_size > 0:
            converted += 1
        else:
            skipped += 1

    logger.info(
        "Done: %d converted, %d skipped, %d failed (total %d)",
        converted,
        skipped,
        failed,
        len(pdf_files),
    )


if __name__ == "__main__":
    main()
