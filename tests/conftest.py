"""Global test configuration."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent

# Add src/ to Python path for package imports in CI environment
src_path = project_root / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Add .claude/agents to Python path for finance_news_collector module
agents_path = project_root / ".claude" / "agents"
if agents_path.exists() and str(agents_path) not in sys.path:
    sys.path.insert(0, str(agents_path))
