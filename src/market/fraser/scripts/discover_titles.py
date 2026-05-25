"""CLI to discover FRASER ``title_id`` values for the supported document types.

This script queries the FRASER REST API for subjects matching a list of
keywords (e.g. ``"Federal Open Market Committee"``, ``"Beige Book"``)
and, for each match, lists the candidate titles so the operator can
manually confirm the correct ``title_id``. The confirmed mapping is
written to a JSON file (default: ``data/config/fraser_titles.json``)
which is then manually copied into
``src/market/fraser/constants.py:KNOWN_TITLE_IDS`` (HF1 decision — no
automatic AST rewriting).

Examples
--------
Run in interactive mode, writing to the default location::

    $ uv run python -m market.fraser.scripts.discover_titles \\
        --output data/config/fraser_titles.json \\
        --interactive

Run with a custom keyword set::

    $ uv run python -m market.fraser.scripts.discover_titles \\
        --keywords "Beige Book" "Monetary Policy Report"

See Also
--------
market.fraser.session : :class:`FraserSession` used for HTTP calls.
market.fraser.constants : ``KNOWN_TITLE_IDS`` target mapping.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from market.fraser.constants import KNOWN_TITLE_IDS
from market.fraser.errors import FraserError
from market.fraser.session import FraserSession
from market.fraser.types import FraserConfig
from utils_core.logging import get_logger

logger = get_logger(__name__, module="discover_titles")

# Default output path (relative to repository root) for the discovered mapping.
DEFAULT_OUTPUT_PATH: Path = Path("data/config/fraser_titles.json")

# Default keyword list — one entry per :data:`KNOWN_TITLE_IDS` key (six total).
DEFAULT_KEYWORDS: list[str] = [
    "Federal Open Market Committee",
    "FOMC Statements",
    "FOMC Press Conferences",
    "Beige Book",
    "Monetary Policy Report",
    "Federal Reserve Board Speeches",
]

# Mapping from keyword to KNOWN_TITLE_IDS key. Aligned with DEFAULT_KEYWORDS
# index-by-index so callers passing the default list get the canonical six
# slots populated.
_KEYWORD_TO_KEY: dict[str, str] = {
    "Federal Open Market Committee": "fomc_minutes",
    "FOMC Statements": "fomc_statements",
    "FOMC Press Conferences": "fomc_press_conferences",
    "Beige Book": "beige_book",
    "Monetary Policy Report": "monetary_policy_report",
    "Federal Reserve Board Speeches": "frb_speeches",
}


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Parameters
    ----------
    args : list[str] | None
        Argument list. When ``None`` (default), :data:`sys.argv` is used.

    Returns
    -------
    argparse.Namespace
        Parsed arguments with ``output``, ``interactive`` and
        ``keywords`` attributes.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Discover FRASER title_id values for the supported document "
            "types and write the mapping to a JSON file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive run (default output path):
    %(prog)s --interactive

  Non-interactive run with custom keywords:
    %(prog)s --keywords "Beige Book" "Monetary Policy Report"

  Custom output path:
    %(prog)s --output /tmp/fraser_titles.json --interactive
""",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        metavar="PATH",
        help=(
            "Destination JSON file (default: %(default)s). "
            "Existing values are preserved when not re-discovered."
        ),
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help=(
            "Prompt the operator to pick the correct title from the "
            "candidate list for each keyword. When omitted, the first "
            "matching title is selected automatically."
        ),
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=DEFAULT_KEYWORDS,
        metavar="KEYWORD",
        help=(
            "Subject keywords to search (default: the six canonical "
            "FRASER document categories)."
        ),
    )
    return parser.parse_args(args)


def fetch_subjects(session: FraserSession) -> list[dict[str, Any]]:
    """Fetch the full list of FRASER subjects.

    Parameters
    ----------
    session : FraserSession
        Authenticated session used to hit ``GET /subjects``.

    Returns
    -------
    list[dict[str, Any]]
        Parsed ``subjects`` array (each element typically has ``id`` and
        ``name`` keys). Returns an empty list when the API responds with
        a body that does not contain a ``subjects`` key.
    """
    logger.info("Fetching FRASER subjects")
    response = session.get_with_retry("/subjects", params={"fields": "name!id"})
    payload = response.json()
    if isinstance(payload, dict):
        subjects = payload.get("subjects", [])
        if isinstance(subjects, list):
            return [s for s in subjects if isinstance(s, dict)]
    logger.warning(
        "Unexpected /subjects payload shape", payload_type=type(payload).__name__
    )
    return []


def find_matching_subjects(
    subjects: list[dict[str, Any]],
    keyword: str,
) -> list[dict[str, Any]]:
    """Filter ``subjects`` to those whose ``name`` contains ``keyword``.

    Matching is case-insensitive.

    Parameters
    ----------
    subjects : list[dict[str, Any]]
        Subjects returned by :func:`fetch_subjects`.
    keyword : str
        Substring to look for in each subject's ``name`` field.

    Returns
    -------
    list[dict[str, Any]]
        Subjects whose ``name`` field contains the keyword.
    """
    keyword_lower = keyword.lower()
    return [
        s
        for s in subjects
        if isinstance(s.get("name"), str) and keyword_lower in s["name"].lower()
    ]


def fetch_titles_for_subject(
    session: FraserSession,
    subject_id: int,
) -> list[dict[str, Any]]:
    """Fetch the list of titles associated with a subject.

    Parameters
    ----------
    session : FraserSession
        Authenticated session used to hit ``GET /subject/{id}/titles``.
    subject_id : int
        Subject identifier as returned by ``/subjects``.

    Returns
    -------
    list[dict[str, Any]]
        Parsed ``titles`` array. Returns an empty list when the API
        responds with a body that does not contain a ``titles`` key.
    """
    logger.info("Fetching titles for subject", subject_id=subject_id)
    response = session.get_with_retry(
        f"/subject/{subject_id}/titles",
        params={"fields": "name!id"},
    )
    payload = response.json()
    if isinstance(payload, dict):
        titles = payload.get("titles", [])
        if isinstance(titles, list):
            return [t for t in titles if isinstance(t, dict)]
    logger.warning(
        "Unexpected /subject/{id}/titles payload shape",
        subject_id=subject_id,
        payload_type=type(payload).__name__,
    )
    return []


def _select_title(
    titles: list[dict[str, Any]],
    keyword: str,
    interactive: bool,
) -> int | None:
    """Choose a ``title_id`` from ``titles``, optionally prompting the user.

    Parameters
    ----------
    titles : list[dict[str, Any]]
        Candidate titles (each typically containing ``id`` and ``name``).
    keyword : str
        Keyword used to discover the titles (shown in interactive
        prompts for context).
    interactive : bool
        When ``True``, prompt the operator. When ``False``, pick the
        first candidate automatically.

    Returns
    -------
    int | None
        The selected ``title_id``, or ``None`` when no titles are
        available or the operator skipped the prompt.
    """
    if not titles:
        print(f"  [WARN] no candidate titles for '{keyword}'", file=sys.stderr)
        return None

    if not interactive:
        first = titles[0]
        title_id = first.get("id")
        if isinstance(title_id, int):
            return title_id
        return None

    print(f"\nCandidates for '{keyword}':")
    for idx, title in enumerate(titles, start=1):
        title_id = title.get("id", "?")
        name = title.get("name", "?")
        print(f"  [{idx}] id={title_id} | name={name}")

    while True:
        choice = input(f"Select 1-{len(titles)} (or 's' to skip): ").strip().lower()
        if choice == "s":
            return None
        try:
            idx = int(choice)
        except ValueError:
            print("  Invalid input. Enter a number or 's'.", file=sys.stderr)
            continue
        if 1 <= idx <= len(titles):
            chosen = titles[idx - 1].get("id")
            if isinstance(chosen, int):
                return chosen
            print("  Selected entry has no integer id; pick another.", file=sys.stderr)
        else:
            print(f"  Out of range. Enter 1-{len(titles)} or 's'.", file=sys.stderr)


def discover_title_ids(
    session: FraserSession,
    keywords: list[str],
    interactive: bool,
) -> dict[str, int]:
    """Discover ``title_id`` values for each keyword.

    Parameters
    ----------
    session : FraserSession
        Authenticated session.
    keywords : list[str]
        Keywords to match against subject names.
    interactive : bool
        Whether to prompt the operator when multiple titles match.

    Returns
    -------
    dict[str, int]
        Mapping from :data:`KNOWN_TITLE_IDS` key to confirmed
        ``title_id``. Only keys for which a title was confirmed are
        included.
    """
    subjects = fetch_subjects(session)
    if not subjects:
        logger.warning("No subjects returned by FRASER API")
        return {}

    discovered: dict[str, int] = {}
    for keyword in keywords:
        target_key = _KEYWORD_TO_KEY.get(keyword)
        if target_key is None:
            logger.warning(
                "Keyword not mapped to a KNOWN_TITLE_IDS slot, skipping",
                keyword=keyword,
            )
            continue

        matches = find_matching_subjects(subjects, keyword)
        if not matches:
            print(f"  [WARN] no subjects matched '{keyword}'", file=sys.stderr)
            continue

        # Collect candidate titles across all matching subjects.
        candidates: list[dict[str, Any]] = []
        seen_ids: set[int] = set()
        for subject in matches:
            subject_id = subject.get("id")
            if not isinstance(subject_id, int):
                continue
            try:
                titles = fetch_titles_for_subject(session, subject_id)
            except FraserError as exc:
                logger.warning(
                    "Failed to fetch titles for subject",
                    subject_id=subject_id,
                    error=str(exc),
                )
                continue
            for title in titles:
                title_id = title.get("id")
                if isinstance(title_id, int) and title_id not in seen_ids:
                    seen_ids.add(title_id)
                    candidates.append(title)

        chosen_id = _select_title(candidates, keyword, interactive)
        if chosen_id is not None:
            discovered[target_key] = chosen_id
            print(f"  [OK] {target_key} = {chosen_id}")

    return discovered


def write_titles_json(
    output_path: Path,
    discovered: dict[str, int],
) -> None:
    """Merge ``discovered`` with existing data and write to ``output_path``.

    Existing values in the file (if any) are preserved unless overridden
    by a newly discovered title_id. Confirmed FOMC Minutes (677) is also
    backfilled from :data:`KNOWN_TITLE_IDS` when missing so the produced
    file contains all six canonical keys.

    Parameters
    ----------
    output_path : Path
        Destination file path. Parent directories are created when
        needed.
    discovered : dict[str, int]
        Newly discovered title_id values.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any] = {}
    if output_path.exists():
        try:
            loaded = json.loads(output_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning(
                "Failed to read existing output, will overwrite",
                output_path=str(output_path),
                error=str(exc),
            )
            existing = {}

    # Backfill known canonical IDs (e.g. fomc_minutes=677) when not present.
    merged: dict[str, int | None] = dict(existing)
    for key, known_value in KNOWN_TITLE_IDS.items():
        if key not in merged and known_value is not None:
            merged[key] = known_value

    # Apply discovered overrides.
    for key, value in discovered.items():
        merged[key] = value

    output_path.write_text(
        json.dumps(merged, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    logger.info(
        "Wrote FRASER title_id mapping",
        output_path=str(output_path),
        key_count=len(merged),
    )


def run(args: argparse.Namespace) -> int:
    """Execute the discovery workflow.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Process exit code (0 on success, 1 on failure).
    """
    config = FraserConfig()
    try:
        with FraserSession(config=config) as session:
            discovered = discover_title_ids(
                session=session,
                keywords=args.keywords,
                interactive=args.interactive,
            )
    except FraserError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        logger.error("Discovery failed", error=str(exc))
        return 1

    write_titles_json(args.output, discovered)
    print(f"\nWrote {len(discovered)} discovered title_id(s) to {args.output}")
    print(
        "Reminder: manually copy these values into "
        "src/market/fraser/constants.py:KNOWN_TITLE_IDS (HF1 confirmed)."
    )
    return 0


def main() -> int:
    """CLI entry point.

    Returns
    -------
    int
        Process exit code.
    """
    args = parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
