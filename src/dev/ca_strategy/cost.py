"""LLM cost tracking for the CA Strategy pipeline.

Tracks token usage and cost across pipeline phases using
Claude Sonnet 4 pricing.  Supports JSON persistence and
cost threshold warnings.

Features
--------
- CostTracker: Record per-phase token usage and compute costs
- Sonnet 4 pricing: input $3/1M tokens, output $15/1M tokens
- JSON save/load for cost tracking persistence
- Warning threshold ($50 default) with log alerts

Notes
-----
With ~300 tickers processed by LLM, estimated total cost is ~$30.
The default warning threshold of $50 provides headroom while
preventing runaway costs.
"""

from __future__ import annotations

import json
import threading
from typing import TYPE_CHECKING

from utils_core.logging import get_logger

if TYPE_CHECKING:
    from pathlib import Path

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_PRICE_INPUT_PER_TOKEN: float = 3.0 / 1_000_000
"""Sonnet 4 input price: $3 per 1M tokens."""

_PRICE_OUTPUT_PER_TOKEN: float = 15.0 / 1_000_000
"""Sonnet 4 output price: $15 per 1M tokens."""

_DEFAULT_WARNING_THRESHOLD: float = 50.0
"""Default cost warning threshold in USD."""


class CostTracker:
    """Track LLM API costs across pipeline phases.

    Records token usage per phase and computes costs using
    Claude Sonnet 4 pricing (input $3/1M, output $15/1M tokens).

    Parameters
    ----------
    warning_threshold : float, optional
        Cost threshold in USD that triggers a warning log.
        Defaults to 50.0.

    Attributes
    ----------
    warning_threshold : float
        The cost threshold for warning alerts.

    Examples
    --------
    >>> tracker = CostTracker()
    >>> tracker.record("phase1", tokens_input=1_000_000, tokens_output=500_000)
    >>> tracker.get_total_cost()
    10.5
    >>> tracker.get_phase_cost("phase1")
    10.5
    """

    def __init__(self, warning_threshold: float = _DEFAULT_WARNING_THRESHOLD) -> None:
        self.warning_threshold = warning_threshold
        self._phases: dict[str, _PhaseRecord] = {}
        self._lock = threading.Lock()

    def record(self, phase: str, *, tokens_input: int, tokens_output: int) -> None:
        """Record token usage for a pipeline phase.

        Parameters
        ----------
        phase : str
            Phase identifier (e.g. "phase1", "phase2").  Must be non-empty.
        tokens_input : int
            Number of input tokens consumed.  Must be >= 0.
        tokens_output : int
            Number of output tokens generated.  Must be >= 0.

        Raises
        ------
        ValueError
            If phase is empty, or token counts are negative.
        """
        if not phase or not phase.strip():
            msg = "phase must be non-empty string"
            raise ValueError(msg)
        if tokens_input < 0:
            msg = f"tokens_input must be >= 0, got {tokens_input}"
            raise ValueError(msg)
        if tokens_output < 0:
            msg = f"tokens_output must be >= 0, got {tokens_output}"
            raise ValueError(msg)

        with self._lock:
            if phase not in self._phases:
                self._phases[phase] = _PhaseRecord()

            record = self._phases[phase]
            record.tokens_input += tokens_input
            record.tokens_output += tokens_output

            cost = (tokens_input * _PRICE_INPUT_PER_TOKEN) + (
                tokens_output * _PRICE_OUTPUT_PER_TOKEN
            )
            record.cost += cost

            logger.debug(
                "Cost recorded",
                phase=phase,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                incremental_cost=round(cost, 6),
                phase_total=round(record.cost, 6),
            )

            total = self.get_total_cost()
            if total > self.warning_threshold:
                logger.warning(
                    "Cost threshold exceeded",
                    total_cost=round(total, 2),
                    threshold=self.warning_threshold,
                )

    def get_total_cost(self) -> float:
        """Get total cost across all phases.

        Returns
        -------
        float
            Total cost in USD.
        """
        return sum(r.cost for r in self._phases.values())

    def get_phase_cost(self, phase: str) -> float:
        """Get cost for a specific phase.

        Parameters
        ----------
        phase : str
            Phase identifier.

        Returns
        -------
        float
            Cost in USD for the specified phase.  Returns 0.0 if
            the phase has no records.
        """
        record = self._phases.get(phase)
        if record is None:
            return 0.0
        return record.cost

    def save(self, path: Path) -> None:
        """Save cost tracking data to a JSON file.

        Parameters
        ----------
        path : Path
            Path to the output JSON file.  Parent directories are
            created if they do not exist.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, object] = {
            "warning_threshold": self.warning_threshold,
            "total_cost": round(self.get_total_cost(), 6),
            "phases": {
                phase: {
                    "tokens_input": record.tokens_input,
                    "tokens_output": record.tokens_output,
                    "cost": round(record.cost, 6),
                }
                for phase, record in self._phases.items()
            },
        }

        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.debug(
            "Cost data saved",
            path=str(path),
            total_cost=round(self.get_total_cost(), 6),
        )

    @classmethod
    def load(cls, path: Path) -> CostTracker:
        """Load cost tracking data from a JSON file.

        If the file does not exist, returns an empty CostTracker.

        Parameters
        ----------
        path : Path
            Path to the JSON file to load.

        Returns
        -------
        CostTracker
            A CostTracker instance populated with loaded data.
        """
        if not path.exists():
            logger.debug("Cost file not found, returning empty tracker", path=str(path))
            return cls()

        data = json.loads(path.read_text(encoding="utf-8"))
        threshold = data.get("warning_threshold", _DEFAULT_WARNING_THRESHOLD)
        tracker = cls(warning_threshold=threshold)

        phases = data.get("phases", {})
        for phase_name, phase_data in phases.items():
            record = _PhaseRecord()
            tokens_input = phase_data.get("tokens_input", 0)
            tokens_output = phase_data.get("tokens_output", 0)
            cost = phase_data.get("cost", 0.0)

            # Validate loaded values
            if not isinstance(tokens_input, int) or tokens_input < 0:
                logger.warning(
                    "Invalid tokens_input in checkpoint, using 0",
                    phase=phase_name,
                    value=tokens_input,
                )
                tokens_input = 0
            if not isinstance(tokens_output, int) or tokens_output < 0:
                logger.warning(
                    "Invalid tokens_output in checkpoint, using 0",
                    phase=phase_name,
                    value=tokens_output,
                )
                tokens_output = 0
            if not isinstance(cost, (int, float)) or cost < 0:
                logger.warning(
                    "Invalid cost in checkpoint, using 0.0",
                    phase=phase_name,
                    value=cost,
                )
                cost = 0.0

            record.tokens_input = tokens_input
            record.tokens_output = tokens_output
            record.cost = float(cost)
            tracker._phases[phase_name] = record

        logger.debug(
            "Cost data loaded",
            path=str(path),
            total_cost=round(tracker.get_total_cost(), 6),
            phase_count=len(tracker._phases),
        )
        return tracker


class _PhaseRecord:
    """Internal record for a single phase's token usage and cost.

    Attributes
    ----------
    tokens_input : int
        Cumulative input tokens.
    tokens_output : int
        Cumulative output tokens.
    cost : float
        Cumulative cost in USD.
    """

    __slots__ = ("cost", "tokens_input", "tokens_output")

    def __init__(self) -> None:
        self.tokens_input: int = 0
        self.tokens_output: int = 0
        self.cost: float = 0.0


__all__ = [
    "CostTracker",
]
