# Personal Investor Financial Plugins
**Karami Follow-the-Soup Edition**

This is a personal fork rebuilt from Anthropic's official financial plugins.  
The original version is more enterprise/institution oriented, with many modules that are too complex and rarely useful for personal investors.
So this fork keeps only the two most essential plugins:
- `financial-analysis` for valuation and research
- `wealth-management` for portfolio and planning
And adds several budget-friendly free data sources to replace expensive subscriptions.

<p align="right"><a href="./README.md">English</a> | <a href="./README.zh-CN.md">简体中文</a></p>

A focused Claude plugin suite for personal investors and advisors.

This repository now contains only two plugins:
- `financial-analysis`
- `wealth-management`

The suite is optimized for free-source-first research and requires provenance metadata in outputs.

## Plugin Marketplace

| Plugin | Type | How it helps |
|------|------|------|
| **[financial-analysis](./financial-analysis)** | Core | Comparable analysis (Comps), DCF, and 3-statement modeling for U.S. equities, with source metadata and fallback handling. |
| **[wealth-management](./wealth-management)** | Add-on | Client review/reporting, financial planning, portfolio rebalancing, and tax-loss harvesting workflows. |

## Data Source Strategy

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
- `financial-analysis` includes local `free-sec-edgar` MCP support.
- Data-source fallback rules are defined directly in each skill `SKILL.md`.

## License

[Apache License 2.0](./LICENSE)

## Disclaimer

These plugins assist with financial workflows but do not provide financial or investing advice. Always verify conclusions with qualified professionals before acting.
