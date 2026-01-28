"""Type definitions for the utils package."""

from typing import Literal

type LogFormat = Literal["json", "console", "plain"]
type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
