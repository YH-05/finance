"""Phase 1 LLM claim extraction from earnings call transcripts.

Uses Claude API (Sonnet 4) to extract competitive advantage claims
(5-15 per ticker) from parsed transcripts, applying KB1-T rules and
KB3-T few-shot examples for calibration.

Features
--------
- ClaimExtractor: Main extraction class with batch and single-ticker modes
- Prompt construction from KB1-T rules, KB3-T few-shots, dogma.md, and PoiT
- LLM response parsing into Claim Pydantic models
- CostTracker integration for token usage tracking
- Output persistence as per-ticker JSON files

Output Directory Structure
--------------------------
Writes to::

    {output_dir}/{TICKER}/{YYYYQX}_claims.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import anthropic

from dev.ca_strategy.pit import CUTOFF_DATE, get_pit_prompt_context
from dev.ca_strategy.types import (
    Claim,
    RuleEvaluation,
)
from utils_core.logging import get_logger

if TYPE_CHECKING:
    from dev.ca_strategy.cost import CostTracker
    from dev.ca_strategy.types import Transcript

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MODEL: str = "claude-sonnet-4-20250514"
"""Claude Sonnet 4 model ID."""

_MAX_TOKENS: int = 8192
"""Maximum output tokens for the LLM response."""

_TEMPERATURE: float = 0
"""Temperature for deterministic extraction."""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
class ClaimExtractor:
    """Extract competitive advantage claims from transcripts using Claude API.

    Loads KB1-T rules, KB3-T few-shot examples, system prompt, and dogma.md
    at initialization.  For each transcript, builds a structured prompt and
    calls the Claude API to extract 5-15 claims with rule evaluations.

    Parameters
    ----------
    kb1_dir : Path | str
        Directory containing KB1-T rule markdown files.
    kb3_dir : Path | str
        Directory containing KB3-T few-shot example files.
    system_prompt_path : Path | str
        Path to the system prompt template file.
    dogma_path : Path | str
        Path to the dogma.md file.
    cost_tracker : CostTracker
        CostTracker instance for recording token usage.
    model : str, optional
        Claude model ID to use.  Defaults to Sonnet 4.
    cutoff_date : str | None, optional
        PoiT cutoff date override as ISO string.  Defaults to the module
        constant CUTOFF_DATE.

    Examples
    --------
    >>> extractor = ClaimExtractor(
    ...     kb1_dir=Path("analyst/transcript_eval/kb1_rules_transcript"),
    ...     kb3_dir=Path("analyst/transcript_eval/kb3_fewshot_transcript"),
    ...     system_prompt_path=Path("analyst/transcript_eval/system_prompt_transcript.md"),
    ...     dogma_path=Path("analyst/Competitive_Advantage/analyst_YK/dogma.md"),
    ...     cost_tracker=CostTracker(),
    ... )
    >>> claims = extractor._extract_single(transcript, sec_data)
    """

    def __init__(
        self,
        kb1_dir: Path | str,
        kb3_dir: Path | str,
        system_prompt_path: Path | str,
        dogma_path: Path | str,
        cost_tracker: CostTracker,
        model: str = _MODEL,
        cutoff_date: str | None = None,
    ) -> None:
        self._kb1_dir = Path(kb1_dir)
        self._kb3_dir = Path(kb3_dir)
        self._system_prompt_path = Path(system_prompt_path)
        self._dogma_path = Path(dogma_path)
        self._cost_tracker = cost_tracker
        self._model = model
        self._cutoff_date_str = cutoff_date or CUTOFF_DATE.isoformat()
        self._client = anthropic.Anthropic()

        # Load knowledge base files
        self._kb1_rules = self._load_directory(self._kb1_dir)
        self._kb3_examples = self._load_directory(self._kb3_dir)
        self._system_prompt = self._load_file(self._system_prompt_path)
        self._dogma = self._load_file(self._dogma_path)

        logger.info(
            "ClaimExtractor initialized",
            kb1_rules_count=len(self._kb1_rules),
            kb3_examples_count=len(self._kb3_examples),
            model=self._model,
            cutoff_date=self._cutoff_date_str,
        )

    # -----------------------------------------------------------------------
    # Public methods
    # -----------------------------------------------------------------------
    def extract_batch(
        self,
        transcripts: dict[str, list[Transcript]],
        sec_data_map: dict[str, dict] | None = None,
        output_dir: Path | None = None,
    ) -> dict[str, list[Claim]]:
        """Extract claims from multiple tickers' transcripts.

        Iterates over each ticker's transcripts, calls ``_extract_single``
        for each, and optionally saves results to JSON files.

        Parameters
        ----------
        transcripts : dict[str, list[Transcript]]
            Mapping of ticker to list of transcripts.
        sec_data_map : dict[str, dict] | None, optional
            Mapping of ticker to SEC filing data.  If None, SEC data is
            not provided to the LLM.
        output_dir : Path | None, optional
            Directory to save per-ticker claim JSON files.
            If None, results are not persisted.

        Returns
        -------
        dict[str, list[Claim]]
            Mapping of ticker to list of extracted claims.
        """
        if sec_data_map is None:
            sec_data_map = {}

        result: dict[str, list[Claim]] = {}

        if not transcripts:
            logger.debug("No transcripts provided, returning empty result")
            return result

        total_tickers = len(transcripts)
        logger.info(
            "Batch extraction started",
            ticker_count=total_tickers,
        )

        for ticker, ticker_transcripts in transcripts.items():
            sec_data = sec_data_map.get(ticker)
            ticker_claims: list[Claim] = []

            for transcript in ticker_transcripts:
                claims = self._extract_single(
                    transcript=transcript,
                    sec_data=sec_data,
                )
                ticker_claims.extend(claims)

                # Save individual transcript results
                if output_dir is not None:
                    self._save_claims(
                        claims=claims,
                        transcript=transcript,
                        output_dir=output_dir,
                    )

            result[ticker] = ticker_claims
            logger.debug(
                "Ticker extraction completed",
                ticker=ticker,
                claim_count=len(ticker_claims),
            )

        total_claims = sum(len(v) for v in result.values())
        logger.info(
            "Batch extraction completed",
            ticker_count=total_tickers,
            total_claims=total_claims,
        )

        return result

    # -----------------------------------------------------------------------
    # Internal: single transcript extraction
    # -----------------------------------------------------------------------
    def _extract_single(
        self,
        transcript: Transcript,
        sec_data: dict | None,
    ) -> list[Claim]:
        """Extract claims from a single transcript via Claude API.

        Parameters
        ----------
        transcript : Transcript
            The earnings call transcript to analyze.
        sec_data : dict | None
            SEC filing data for cross-reference.

        Returns
        -------
        list[Claim]
            Extracted claims.  Returns empty list on error.
        """
        ticker = transcript.metadata.ticker
        quarter = transcript.metadata.fiscal_quarter

        logger.debug(
            "Extracting claims",
            ticker=ticker,
            quarter=quarter,
        )

        user_prompt = self._build_extraction_prompt(
            transcript=transcript,
            sec_data=sec_data,
        )

        system_prompt = self._build_system_prompt()

        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=_MAX_TOKENS,
                temperature=_TEMPERATURE,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
            )

            # Record cost
            self._cost_tracker.record(
                phase="phase1",
                tokens_input=message.usage.input_tokens,
                tokens_output=message.usage.output_tokens,
            )

            # Extract text from response
            response_text = self._extract_text_from_response(message)
            if not response_text:
                logger.warning(
                    "Empty LLM response",
                    ticker=ticker,
                    quarter=quarter,
                )
                return []

            # Parse claims
            claims = self._parse_llm_response(response_text)
            logger.debug(
                "Claims extracted",
                ticker=ticker,
                quarter=quarter,
                claim_count=len(claims),
            )
            return claims

        except Exception:
            logger.exception(
                "LLM extraction failed",
                ticker=ticker,
                quarter=quarter,
            )
            return []

    # -----------------------------------------------------------------------
    # Internal: prompt construction
    # -----------------------------------------------------------------------
    def _build_system_prompt(self) -> str:
        """Build the system prompt with cutoff_date injected.

        Returns
        -------
        str
            System prompt with ``{{cutoff_date}}`` replaced.
        """
        prompt = self._system_prompt or ""
        return prompt.replace("{{cutoff_date}}", self._cutoff_date_str)

    def _build_extraction_prompt(
        self,
        transcript: Transcript,
        sec_data: dict | None,
    ) -> str:
        """Build the user prompt for claim extraction.

        Combines transcript content, SEC data, KB1-T rules, KB3-T examples,
        dogma.md, and PoiT constraints into a structured prompt.

        Parameters
        ----------
        transcript : Transcript
            The transcript to analyze.
        sec_data : dict | None
            SEC filing data for cross-reference.

        Returns
        -------
        str
            Complete user prompt for the LLM.
        """
        parts: list[str] = []

        # 1. Transcript metadata
        meta = transcript.metadata
        parts.append(
            f"## 分析対象トランスクリプト\n\n"
            f"- **Ticker**: {meta.ticker}\n"
            f"- **Fiscal Quarter**: {meta.fiscal_quarter}\n"
            f"- **Event Date**: {meta.event_date.isoformat()}\n"
            f"- **Truncated**: {meta.is_truncated}\n"
        )

        # 2. Transcript sections
        parts.append("## トランスクリプト内容\n")
        for section in transcript.sections:
            role_str = f" ({section.role})" if section.role else ""
            parts.append(
                f"### [{section.section_type}] {section.speaker}{role_str}\n\n"
                f"{section.content}\n"
            )

        # 3. SEC data (if available)
        if sec_data is not None:
            parts.append("## SEC Filing データ（事実確認用）\n")
            parts.append(
                f"```json\n{json.dumps(sec_data, ensure_ascii=False, indent=2)}\n```\n"
            )
        else:
            parts.append(
                "## SEC Filing データ\n\nSEC Filing データは利用できません。\n"
            )

        # 4. PoiT constraints
        parts.append(f"## PoiT制約\n\n{get_pit_prompt_context()}\n")

        # 5. KB1-T rules
        parts.append("## KB1-T ルール集（全ルール）\n")
        for name, content in sorted(self._kb1_rules.items()):
            parts.append(f"### {name}\n\n{content}\n")

        # 6. KB3-T few-shot examples
        parts.append("## KB3-T few-shot 評価例\n")
        for name, content in sorted(self._kb3_examples.items()):
            parts.append(f"### {name}\n\n{content}\n")

        # 7. Dogma
        if self._dogma:
            parts.append(f"## dogma.md（KYの評価基準）\n\n{self._dogma}\n")

        # 8. Output instructions
        parts.append(self._build_output_instructions(meta.ticker, meta.fiscal_quarter))

        return "\n".join(parts)

    @staticmethod
    def _build_output_instructions(ticker: str, fiscal_quarter: str) -> str:
        """Build output format instructions for the LLM.

        Parameters
        ----------
        ticker : str
            Ticker symbol.
        fiscal_quarter : str
            Fiscal quarter label.

        Returns
        -------
        str
            Output instructions section.
        """
        return (
            "## 出力指示\n\n"
            "以下のJSON形式で claims.json を出力してください（5-15件）。\n"
            "JSONのみを出力し、他のテキストは含めないでください。\n\n"
            "```json\n"
            "{\n"
            f'  "ticker": "{ticker}",\n'
            f'  "transcript_source": "{fiscal_quarter} Earnings Call",\n'
            '  "extraction_metadata": {\n'
            '    "cutoff_date": "2015-09-30",\n'
            '    "kb1_t_rules_loaded": <int>,\n'
            '    "dogma_loaded": true,\n'
            '    "sec_data_available": <bool>\n'
            "  },\n"
            '  "claims": [\n'
            "    {\n"
            '      "id": "<TICKER>-CA-001",\n'
            '      "claim_type": "competitive_advantage",\n'
            '      "claim": "<主張テキスト>",\n'
            '      "evidence": "<証拠テキスト>",\n'
            '      "rule_evaluation": {\n'
            '        "applied_rules": ["rule_1_t", ...],\n'
            '        "results": {"rule_1_t": true, ...},\n'
            '        "confidence": <0.0-1.0>,\n'
            '        "adjustments": ["<調整理由>"]\n'
            "      }\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "```\n\n"
            "**重要**: \n"
            "- confidence は 0.0-1.0 の範囲（例: 70% → 0.7）\n"
            "- claim_type は competitive_advantage, cagr_connection, factual_claim のいずれか\n"
            "- 各主張に必ず rule_evaluation を含めること（factual_claim 含む）\n"
            "- 主張は5-15件抽出すること\n"
        )

    # -----------------------------------------------------------------------
    # Internal: response parsing
    # -----------------------------------------------------------------------
    def _parse_llm_response(self, response_text: str) -> list[Claim]:
        """Parse LLM JSON response into a list of Claim models.

        Handles JSON wrapped in markdown code blocks (```json ... ```).
        Returns empty list on parse failure or invalid data.

        Parameters
        ----------
        response_text : str
            Raw LLM response text.

        Returns
        -------
        list[Claim]
            Parsed Claim models.
        """
        # Strip markdown code block wrapper if present
        cleaned = self._strip_code_block(response_text)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse LLM response as JSON",
                response_preview=response_text[:200],
            )
            return []

        raw_claims = data.get("claims", [])
        if not raw_claims:
            logger.warning("No claims found in LLM response")
            return []

        claims: list[Claim] = []
        for raw in raw_claims:
            claim = self._parse_single_claim(raw)
            if claim is not None:
                claims.append(claim)

        logger.debug(
            "Claims parsed",
            total_raw=len(raw_claims),
            valid_count=len(claims),
        )
        return claims

    def _parse_single_claim(self, raw: dict) -> Claim | None:
        """Parse a single raw claim dict into a Claim model.

        Parameters
        ----------
        raw : dict
            Raw claim data from LLM response.

        Returns
        -------
        Claim | None
            Parsed Claim, or None if validation fails.
        """
        try:
            # Extract rule_evaluation, handling both nested dict and flat formats
            rule_eval_raw = raw.get("rule_evaluation", {})
            confidence = rule_eval_raw.get("confidence", 0.5)

            # Normalize confidence from percentage to 0-1 if needed
            if isinstance(confidence, (int, float)) and confidence > 1.0:
                confidence = confidence / 100.0

            # Build results dict
            results_raw = rule_eval_raw.get("results", {})
            if isinstance(results_raw, list):
                # Handle list-of-dicts format from LLM
                results_dict: dict[str, bool] = {}
                for item in results_raw:
                    if isinstance(item, dict):
                        rule_id = item.get("rule", "")
                        verdict = item.get("verdict", "")
                        results_dict[rule_id] = verdict in (
                            "pass",
                            "structural",
                            "quantitative",
                            "direct",
                            "primary",
                            True,
                        )
                results = results_dict
            elif isinstance(results_raw, dict):
                results = {
                    k: bool(v) if not isinstance(v, bool) else v
                    for k, v in results_raw.items()
                }
            else:
                results = {}

            # Build adjustments list
            adjustments_raw = rule_eval_raw.get("adjustments", [])
            if isinstance(adjustments_raw, list):
                adjustments = [
                    str(a) if not isinstance(a, str) else a for a in adjustments_raw
                ]
            else:
                adjustments = []

            # Handle confidence_adjustments (alternative key from LLM)
            conf_adj_raw = rule_eval_raw.get("confidence_adjustments", [])
            if isinstance(conf_adj_raw, list):
                for adj in conf_adj_raw:
                    if isinstance(adj, dict):
                        reason = adj.get("reason", "")
                        adjustment_val = adj.get("adjustment", 0)
                        adjustments.append(f"{reason} ({adjustment_val})")

            rule_evaluation = RuleEvaluation(
                applied_rules=rule_eval_raw.get("applied_rules", []),
                results=results,
                confidence=confidence,
                adjustments=adjustments,
            )

            # Get evidence, handling both 'evidence' and
            # 'evidence_from_transcript' keys
            evidence = raw.get("evidence") or raw.get("evidence_from_transcript", "")
            if not evidence:
                evidence = raw.get("claim", "No evidence provided")

            claim = Claim(
                id=raw.get("id", "unknown"),
                claim_type=raw.get("claim_type", "competitive_advantage"),
                claim=raw.get("claim", ""),
                evidence=evidence,
                rule_evaluation=rule_evaluation,
            )
            return claim

        except Exception:
            logger.warning(
                "Failed to parse claim",
                claim_id=raw.get("id", "unknown"),
                exc_info=True,
            )
            return None

    # -----------------------------------------------------------------------
    # Internal: file I/O
    # -----------------------------------------------------------------------
    @staticmethod
    def _load_directory(directory: Path) -> dict[str, str]:
        """Load all markdown files from a directory.

        Parameters
        ----------
        directory : Path
            Directory containing .md files.

        Returns
        -------
        dict[str, str]
            Mapping of filename (without extension) to file content.
        """
        result: dict[str, str] = {}
        if not directory.exists():
            logger.warning(
                "Directory not found",
                path=str(directory),
            )
            return result

        for filepath in sorted(directory.glob("*.md")):
            try:
                content = filepath.read_text(encoding="utf-8")
                result[filepath.stem] = content
                logger.debug(
                    "KB file loaded",
                    file=filepath.name,
                    length=len(content),
                )
            except OSError:
                logger.warning(
                    "Failed to read KB file",
                    path=str(filepath),
                    exc_info=True,
                )

        return result

    @staticmethod
    def _load_file(filepath: Path) -> str:
        """Load a single text file.

        Parameters
        ----------
        filepath : Path
            Path to the file.

        Returns
        -------
        str
            File content, or empty string if the file does not exist.
        """
        if not filepath.exists():
            logger.warning(
                "File not found",
                path=str(filepath),
            )
            return ""

        try:
            return filepath.read_text(encoding="utf-8")
        except OSError:
            logger.warning(
                "Failed to read file",
                path=str(filepath),
                exc_info=True,
            )
            return ""

    @staticmethod
    def _extract_text_from_response(message: anthropic.types.Message) -> str:
        """Extract text content from a Claude API response.

        Parameters
        ----------
        message : anthropic.types.Message
            The API response message.

        Returns
        -------
        str
            Concatenated text content from all TextBlock content blocks.
        """
        texts: list[str] = []
        for block in message.content:
            if hasattr(block, "text"):
                texts.append(block.text)
        return "\n".join(texts)

    @staticmethod
    def _strip_code_block(text: str) -> str:
        """Strip markdown code block delimiters from text.

        Handles both ````` `json ... ``` ````` and plain text.

        Parameters
        ----------
        text : str
            Text that may be wrapped in code block markers.

        Returns
        -------
        str
            Text with code block markers removed.
        """
        pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _save_claims(
        self,
        claims: list[Claim],
        transcript: Transcript,
        output_dir: Path,
    ) -> None:
        """Save extracted claims to a JSON file.

        Parameters
        ----------
        claims : list[Claim]
            Extracted claims.
        transcript : Transcript
            Source transcript.
        output_dir : Path
            Base output directory.
        """
        ticker = transcript.metadata.ticker
        quarter = transcript.metadata.fiscal_quarter.replace(" ", "_")
        ticker_dir = output_dir / ticker
        ticker_dir.mkdir(parents=True, exist_ok=True)

        output_path = ticker_dir / f"{quarter}_claims.json"

        data = {
            "ticker": ticker,
            "fiscal_quarter": transcript.metadata.fiscal_quarter,
            "event_date": transcript.metadata.event_date.isoformat(),
            "cutoff_date": self._cutoff_date_str,
            "claims": [c.model_dump() for c in claims],
        }

        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.debug(
            "Claims saved",
            path=str(output_path),
            claim_count=len(claims),
        )


__all__ = [
    "ClaimExtractor",
]
