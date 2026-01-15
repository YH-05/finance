"""Global test configuration."""

import sys
from pathlib import Path

# Add .claude/agents to Python path for finance_news_collector module
agents_path = Path(__file__).parent.parent / ".claude" / "agents"
if agents_path.exists() and str(agents_path) not in sys.path:
    sys.path.insert(0, str(agents_path))
