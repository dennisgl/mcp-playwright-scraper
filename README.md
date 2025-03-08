# mcp-playwright-scraper

A Model Context Protocol (MCP) server that scrapes web content and converts it to Markdown.

## Overview

This MCP server provides a simple tool for scraping web content and converting it to Markdown format. It uses:

- **Playwright**: For headless browser automation to handle modern web pages including JavaScript-heavy sites
- **BeautifulSoup**: For HTML parsing and cleanup
- **Pypandoc**: For high-quality HTML to Markdown conversion

## Tools

The server implements a single tool:

- `scrape_to_markdown`: Scrapes content from a URL and converts it to Markdown
  - Required parameter: `url` (string) - The URL to scrape
  - Optional parameter: `verify_ssl` (boolean) - Whether to verify SSL certificates (default: true)

## Installation

### Using uv (recommended)

When using [`uv`](https://docs.astral.sh/uv/) no specific installation is needed. We will
use [`uvx`](https://docs.astral.sh/uv/guides/tools/) to directly run *mcp-playwright-scraper*.

### Using PIP

Alternatively you can install `mcp-playwright-scraper` via pip:

```
pip install mcp-playwright-scraper
```

After installation, you can run it as a script using:

```
python -m mcp_playwright_scraper
```

### Prerequisites

- Python 3.11 or higher
- Playwright browser dependencies
- Pandoc (optional, will be automatically installed by pypandoc if possible)

After installation, you need to install Playwright browser dependencies:

```bash
playwright install --with-deps chromium
```

## Configuration

### Usage with Claude Desktop

Add this to your `claude_desktop_config.json`:

<details>
<summary>Using uvx</summary>

```json
"mcpServers": {
  "mcp-playwright-scraper": {
    "command": "uvx",
    "args": ["mcp-playwright-scraper"]
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
"mcpServers": {
  "mcp-playwright-scraper": {
    "command": "python",
    "args": ["-m", "mcp_playwright_scraper"]
  }
}
```
</details>

### Usage with Claude Code

```bash
# Basic syntax
$ claude mcp add mcp-playwright-scraper -- uvx mcp-playwright-scraper

# Alternatively, with pip installation
$ claude mcp add mcp-playwright-scraper -- python -m mcp_playwright_scraper
```

<details>
<summary>Development/Unpublished Servers Configuration</summary>

```json
"mcpServers": {
  "mcp-playwright-scraper": {
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/mcp-playwright-scraper",
      "run",
      "mcp-playwright-scraper"
    ]
  }
}
```
</details>

### Usage with [Zed](https://github.com/zed-industries/zed)

Add to your Zed settings.json:

<details>
<summary>Using uvx</summary>

```json
"context_servers": [
  "mcp-playwright-scraper": {
    "command": {
      "path": "uvx",
      "args": ["mcp-playwright-scraper"]
    }
  }
],
```
</details>

<details>
<summary>Using pip installation</summary>

```json
"context_servers": {
  "mcp-playwright-scraper": {
    "command": "python",
    "args": ["-m", "mcp_playwright_scraper"]
  }
},
```
</details>

### Usage with Cursor

1. Open Cursor Settings
   - Navigate to Cursor Settings > Features > MCP
   - Click the "+ Add New MCP Server" button
2. Configure the Server
   - Name: `mcp-playwright-scraper`
   - Type: Select `stdio`
   - Command: Enter one of the following:

<details>
<summary>Using uvx</summary>

```
uvx mcp-playwright-scraper
```
</details>

<details>
<summary>Using pip installation</summary>

```
python -m mcp_playwright_scraper
```
</details>

## Usage

Once configured in Claude Desktop, you can explicitly use the scraper with a prompt like:

```
Use the mcp-playwright-scraper to scrape the content from https://example.com and summarize it.
```

## Debugging

You can use the MCP inspector to debug the server:

```bash
npx @modelcontextprotocol/inspector uvx mcp-playwright-scraper
```

Or if you've installed the package in a specific directory or are developing on it:

```bash
cd path/to/mcp-playwright-scraper
npx @modelcontextprotocol/inspector uv run mcp-playwright-scraper
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

## License

This MCP server is licensed under the Apache License, Version 2.0. You are free to use, modify, and distribute the software, subject to the terms and conditions of the Apache License 2.0. For more details, please see the LICENSE file in the project repository or visit http://www.apache.org/licenses/LICENSE-2.0.