# Personal Investor Financial Plugins
**Small-Fry Grabbing Crumbs Edition**

<p align="center"><a href="./README.md">English</a> | <a href="./README.zh-CN.md">简体中文</a></p>


This is a personal fork rebuilt from Anthropic's official financial plugins.  
The original version is built for enterprise/institution workflows: too many modules, too much overhead, and a lot of stuff most personal investors will never touch.
So this fork keeps only the two essentials:
- `financial-analysis` handles valuation and research
- `wealth-management` handles portfolio and planning
And adds free data sources on top, so regular investors can still get useful coverage without paying for every premium feed.

A focused Claude plugin suite for personal investors and advisors.

This repository now contains only two plugins:
- `financial-analysis`
- `wealth-management`

The suite is optimized for free-source-first research.

## Plugin Marketplace

| Plugin | Type | How it helps |
|------|------|------|
| **[financial-analysis](./financial-analysis)** | Core | Comparable analysis (Comps), DCF, and 3-statement modeling for U.S. equities. |
| **[wealth-management](./wealth-management)** | Add-on | Client review/reporting, financial planning, portfolio rebalancing, and tax-loss harvesting workflows. |

## Free Data Sources Added

See [docs/FREE_DATA_SOURCES.md](./docs/FREE_DATA_SOURCES.md) for details.

| Source | Free Quota | Integrated | MCP | Notes |
|--------|------------|------------|-----|-------|
| SEC EDGAR | Unlimited (rate-limited) | ✅ | [edgartools](https://github.com/dgunning/edgartools) built-in MCP | 10-K/10-Q/8-K filings, XBRL financials, insider trades, 13-F holdings |
| FRED | Unlimited (rate-limited) | ✅ | [fred-mcp-server](https://github.com/stefanoamorelli/fred-mcp-server) | 800k+ series: rates, inflation, GDP, labor, credit spreads |
| Alpha Vantage | 25 calls/day | ✅ | [Official remote MCP](https://mcp.alphavantage.co) | Quotes, indicators, fundamentals |
| NY Fed + U.S. Treasury | Unlimited | ❌ | — | SOFR, ON RRP, TGA |
| CoinGecko | 50 calls/min | ❌ | — | BTC/ETH spot prices |
| Twelve Data | 800 calls/day, 8 symbols | ✅ | [Official MCP](https://github.com/twelvedata/mcp) | Stock/crypto quotes |
| Google News | Unlimited | ❌ | [server-google-news](https://github.com/chanmeng666/server-google-news) | News search; web search covers most of this |
| Massive API | 5 calls/min, 2yr history | ✅ | [Official MCP](https://github.com/massive-com/mcp_massive) | Stocks, fundamentals, analyst ratings, options, crypto |

## Getting Started

### Cowork
Install plugins from [claude.com/plugins](https://claude.com/plugins/).

### Claude Code
```bash
# Add the marketplace
claude plugin marketplace add flora535/financial-services-plugins

# Install the core plugin first
claude plugin install financial-analysis@financial-services-plugins

# Install wealth management add-on
claude plugin install wealth-management@financial-services-plugins
```

## Notes
- `financial-analysis` prefers upstream MCPs for all free data sources.

## Contributing
Contributions are welcome, especially MCP integrations for additional **free** data sources that improve coverage for personal-investor workflows.

Priority contributions:
- New MCP connectors for credible free sources
- Reliability improvements (clear error handling, rate-limit-aware behavior, reproducible outputs)

## License

[Apache License 2.0](./LICENSE)

## Disclaimer

These plugins assist with financial workflows but do not provide financial or investing advice. Always verify conclusions with qualified professionals before acting.
