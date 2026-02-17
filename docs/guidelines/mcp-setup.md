# MCP Server Setup Guide

## Overview

This project uses Model Context Protocol (MCP) servers to provide various integrations and capabilities.

## Initial Setup

### 1. Create `.mcp.json`

Copy the template file to create your local configuration:

```bash
cp .mcp.json.template .mcp.json
```

### 2. Configure API Keys

Edit `.mcp.json` and replace the placeholder values with your actual credentials:

#### Notion

```json
"NOTION_API_KEY": "your_actual_notion_api_key"
```

Get your Notion API key from: https://www.notion.so/my-integrations

#### SEC EDGAR

```json
"SEC_EDGAR_USER_AGENT": "Your Name (your.email@example.com)"
```

Required by SEC EDGAR API. Use your real name and email.

#### Slack

```json
"SLACK_BOT_TOKEN": "your_actual_slack_bot_token"
```

Create a Slack app and get the bot token from: https://api.slack.com/apps

#### Tavily

```json
"TAVILY_API_KEY": "your_actual_tavily_api_key"
```

Get your Tavily API key from: https://tavily.com/

## Platform-Specific Configuration

### Windows

On Windows, `npx` commands require a `cmd /c` wrapper. The template files are already configured for Windows:

```json
{
  "command": "cmd",
  "args": ["/c", "npx", "-y", "package-name"]
}
```

### macOS/Linux

On macOS and Linux, you can use `npx` directly:

```json
{
  "command": "npx",
  "args": ["-y", "package-name"]
}
```

If you're using this project on macOS/Linux, modify the `command` and `args` for npx-based servers in your `.mcp.json`.

## Configured MCP Servers

### Core Servers

| Server | Description | Requirements |
|--------|-------------|--------------|
| git | Git repository operations | None |
| filesystem | File system access | None |
| memory | Persistent memory across sessions | None |
| sequential-thinking | Structured thinking support | None |

### Integration Servers

| Server | Description | API Key Required |
|--------|-------------|------------------|
| notion | Notion API integration | ✅ Yes |
| slack | Slack workspace integration | ✅ Yes |
| tavily | Web search API | ✅ Yes |
| sec-edgar-mcp | SEC EDGAR filings | User-Agent only |

### Utility Servers

| Server | Description | Requirements |
|--------|-------------|--------------|
| fetch | HTTP fetch capabilities | None |
| time | Time and timezone utilities | None |
| wikipedia | Wikipedia API | None |
| reddit | Reddit API | None |
| playwright | Browser automation | None |
| context7 | Documentation context | None |
| rss | RSS feed management | None |

## Security Notes

**IMPORTANT:**
- `.mcp.json` is ignored by git and contains sensitive credentials
- Never commit `.mcp.json` to version control
- `.mcp.json.template` provides the structure without credentials
- Keep your API keys secure and rotate them regularly

## Troubleshooting

### Server Connection Issues

Check server status:
```bash
claude mcp list
```

### Missing Dependencies

Some servers require additional setup:

- **rss**: Uses local `uv run rss-mcp` command
- **sec-edgar-mcp**: Requires `pyrate-limiter<4.0`

Install missing dependencies:
```bash
uv sync --all-extras
```

### Environment Variables

Alternatively, you can use environment variables instead of hardcoding in `.mcp.json`:

1. Create `.env` file:
```bash
NOTION_API_KEY=your_key
SLACK_BOT_TOKEN=your_token
TAVILY_API_KEY=your_key
SEC_EDGAR_USER_AGENT="Your Name (your.email@example.com)"
```

2. Update `.mcp.json` to use `${VAR_NAME}` syntax (see `.mcp.json.example`)

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Claude Code MCP Guide](https://docs.anthropic.com/claude-code/mcp)
