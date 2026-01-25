"""Test configuration for finance news workflow tests.

Set up import paths and module aliases for testing.
"""

import sys
from pathlib import Path

# Add the utils directory to the Python path as 'finance_news_collector'
# This allows tests to import from finance_news_collector.filtering etc.
_utils_path = (
    Path(__file__).parent.parent.parent.parent
    / ".claude/skills/finance-news-workflow/utils"
)

if _utils_path.exists():
    # Create a module alias
    if str(_utils_path.parent) not in sys.path:
        sys.path.insert(0, str(_utils_path.parent))

    # Make utils importable as finance_news_collector
    if str(_utils_path) not in sys.path:
        sys.path.insert(0, str(_utils_path.parent))

    # Import the utils module and register it as finance_news_collector
    import importlib.util

    # Create finance_news_collector package
    if "finance_news_collector" not in sys.modules:
        # Load utils as finance_news_collector
        spec = importlib.util.spec_from_file_location(
            "finance_news_collector",
            _utils_path / "__init__.py",
            submodule_search_locations=[str(_utils_path)],
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["finance_news_collector"] = module
            spec.loader.exec_module(module)

            # Also register submodules
            for submodule_name in ["filtering", "transformation"]:
                submodule_path = _utils_path / f"{submodule_name}.py"
                if submodule_path.exists():
                    sub_spec = importlib.util.spec_from_file_location(
                        f"finance_news_collector.{submodule_name}",
                        submodule_path,
                    )
                    if sub_spec and sub_spec.loader:
                        sub_module = importlib.util.module_from_spec(sub_spec)
                        sys.modules[f"finance_news_collector.{submodule_name}"] = (
                            sub_module
                        )
                        sub_spec.loader.exec_module(sub_module)
