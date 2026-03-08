# Financial Data Sources (Programmer Setup)

Selected sources from Chapter 3 and how to integrate each via CLI and MCP.

| Source | What it provides | CLI integration | MCP integration | Notes |
| --- | --- | --- | --- | --- |
| Yahoo Finance | Free quotes, history, basic fundamentals, ratios | `yfinance`-based scripts or community CLIs (for quick prototyping) | Community Yahoo Finance MCP servers (unofficial) | Best for exploration; scraper-backed paths can break when site changes. |
| Finviz | US-focused screener, market map, filters, headlines | `finvizfinance` Python scripts for screening flows | Community Finviz MCP servers (unofficial) | Great first-pass screener; programmatic access is less stable than paid APIs. |
| EODHD | Global EOD/intraday/fundamental APIs across many exchanges | Direct REST calls or official SDKs in scripts | EODHD MCP server (official/community available) | Better production reliability than scraping. Free tier is limited. |
| OpenBB | Unified interface across stocks, crypto, macro, multiple providers | `openbb-cli` for repeatable command-line workflows | OpenBB MCP tooling/integration available in OpenBB ecosystem | Strong aggregator pattern; check provider credentials and environment compatibility. |

## Practical default stack

1. Use Finviz to screen.
2. Use Yahoo for fast exploratory checks.
3. Use EODHD for more reliable repeatable pulls.
4. Use OpenBB as the orchestration layer when you need multi-provider switching.
