"""Integration test configuration and fixtures for news package.

This module provides fixtures for verifying Claude authentication
and running integration tests that use the actual Claude Agent SDK.

Authentication modes:
1. **Local environment**: Uses subscription auth (claude auth login)
   - ANTHROPIC_API_KEY should NOT be set
   - Requires Claude Pro/Max subscription
2. **CI/CD environment**: Uses API key auth
   - ANTHROPIC_API_KEY must be set
   - Skips tests if not set

Notes
-----
Integration tests require:
- Local: `claude auth login` with Claude Pro/Max subscription
- CI/CD: `ANTHROPIC_API_KEY` environment variable set in GitHub Secrets
"""

import os
import subprocess

import pytest


def is_ci_environment() -> bool:
    """Check if running in CI environment.

    Returns
    -------
    bool
        True if CI environment variable is set to "true".
    """
    return os.environ.get("CI") == "true"


def has_api_key() -> bool:
    """Check if ANTHROPIC_API_KEY is set.

    Returns
    -------
    bool
        True if ANTHROPIC_API_KEY environment variable is set.
    """
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def check_claude_cli_installed() -> tuple[bool, str]:
    """Check if Claude CLI is installed.

    Returns
    -------
    tuple[bool, str]
        (is_installed, version_or_error_message)
    """
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, result.stderr.strip() or "Unknown error"
    except FileNotFoundError:
        return False, "Claude CLI not installed"
    except subprocess.TimeoutExpired:
        return False, "Timeout checking Claude CLI version"
    except Exception as e:
        return False, str(e)


@pytest.fixture(scope="session", autouse=True)
def verify_claude_auth() -> None:
    """Verify Claude authentication is available (environment-aware).

    This fixture runs once per test session and checks authentication
    based on the environment:

    **CI environment**:
    - Requires ANTHROPIC_API_KEY to be set
    - Skips tests if not set (allows PR builds without secrets)

    **Local environment**:
    - Prefers subscription auth (ANTHROPIC_API_KEY not set)
    - Warns if ANTHROPIC_API_KEY is set (API usage will be charged)
    - Requires Claude CLI to be installed

    Raises
    ------
    pytest.skip
        If the environment is not configured for authentication.
    """
    if is_ci_environment():
        # CI environment: API key required
        if not has_api_key():
            pytest.skip(
                "ANTHROPIC_API_KEY not set in CI environment. "
                "Set the secret to run integration tests."
            )
        print("\n[Integration Test] Using API key auth (CI environment)")
    # Local environment: subscription auth preferred
    elif has_api_key():
        print(
            "\n[Integration Test] WARNING: ANTHROPIC_API_KEY is set. "
            "API usage will be charged instead of subscription."
        )
        print("[Integration Test] Using API key auth")
    else:
        # Check Claude CLI is installed for subscription auth
        is_installed, version_or_error = check_claude_cli_installed()
        if not is_installed:
            pytest.skip(
                f"Claude CLI not available: {version_or_error}. "
                "Run 'npm install -g @anthropic-ai/claude-code' to install, "
                "then 'claude auth login' to authenticate with subscription."
            )
        print(f"\n[Integration Test] Claude CLI version: {version_or_error}")
        print("[Integration Test] Using subscription auth (ANTHROPIC_API_KEY not set)")
