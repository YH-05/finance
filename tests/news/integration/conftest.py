"""Integration test configuration and fixtures for news package.

This module provides fixtures for verifying Claude subscription authentication
and running integration tests that use the actual Claude Agent SDK.

Notes
-----
Integration tests require:
1. Claude Code CLI installed: claude --version
2. Claude subscription authenticated: claude auth login
3. ANTHROPIC_API_KEY NOT set (to use subscription instead of API key)
"""

import os
import subprocess

import pytest


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


def check_api_key_not_set() -> bool:
    """Check that ANTHROPIC_API_KEY is not set.

    Returns
    -------
    bool
        True if ANTHROPIC_API_KEY is not set (preferred for subscription auth).
    """
    return os.environ.get("ANTHROPIC_API_KEY") is None


@pytest.fixture(scope="session", autouse=True)
def verify_subscription_auth() -> None:
    """Verify subscription authentication is available.

    This fixture runs once per test session and checks:
    1. ANTHROPIC_API_KEY is not set (to prefer subscription auth)
    2. Claude CLI is installed

    Note: We cannot easily verify subscription auth status via CLI
    since `claude auth status` is not a valid command. Authentication
    will be verified when actual Claude API calls are made.

    Raises
    ------
    pytest.skip
        If the environment is not configured for subscription auth.
    """
    # Check API key is not set
    if not check_api_key_not_set():
        pytest.skip(
            "ANTHROPIC_API_KEY is set. "
            "Unset it to use subscription auth: unset ANTHROPIC_API_KEY"
        )

    # Check Claude CLI is installed
    is_installed, version_or_error = check_claude_cli_installed()
    if not is_installed:
        pytest.skip(f"Claude CLI not available: {version_or_error}")

    print(f"\n[Integration Test] Claude CLI version: {version_or_error}")
    print("[Integration Test] ANTHROPIC_API_KEY: NOT SET (using subscription auth)")
