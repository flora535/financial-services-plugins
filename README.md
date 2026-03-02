# Personal Investor Financial Plugins

A focused Claude plugin suite for personal investors and advisors.

This repository now contains only two plugins:
- `financial-analysis`
- `wealth-management`

The suite is optimized for free-source-first research with explicit provenance tagging on outputs.

## Plugin Marketplace

| Plugin | Type | How it helps |
|--------|------|--------------|
| **[financial-analysis](./financial-analysis)** | Core | Build comps, DCF, and 3-statement models for public equities with source metadata and fallback handling. |
| **[wealth-management](./wealth-management)** | Add-on | Prepare client reviews/reports, build financial plans, rebalance portfolios, and identify tax-loss harvesting opportunities. |

## Data Source Policy

Both plugins follow one shared policy:
- [source-policy](./financial-analysis/skills/source-policy/SKILL.md)

Default routing is domain-based and free-first:
1. Fundamentals: SEC EDGAR first
2. Macro/liquidity: FRED + NY Fed + U.S. Treasury first
3. Prices/indicators: Twelve Data then Alpha Vantage
4. Crypto: CoinGecko first
5. News/catalysts: Google News RSS + web confirmation

Premium MCP connectors are retained in `financial-analysis/.mcp.json` as optional secondary sources.

Required metadata for external claims:
- `source`
- `as_of`
- `freshness`
- `confidence`
- `fallback_used`

## Getting Started

### Cowork
Install plugins from [claude.com/plugins](https://claude.com/plugins/).

### Claude Code
```bash
# Add the marketplace (replace with your fork)
claude plugin marketplace add flora535/financial-services-plugins

# Install the core plugin first
claude plugin install financial-analysis@financial-services-plugins

# Install wealth management add-on
claude plugin install wealth-management@financial-services-plugins
```

## Repository Structure

```text
financial-services-plugins/
├── .claude-plugin/marketplace.json
├── financial-analysis/
│   ├── .claude-plugin/plugin.json
│   ├── .mcp.json
│   ├── commands/
│   └── skills/
└── wealth-management/
    ├── .claude-plugin/plugin.json
    ├── commands/
    └── skills/
```

## Breaking Changes

- Removed plugins:
  - `investment-banking`
  - `equity-research`
  - `private-equity`
  - `partner-built/lseg`
  - `partner-built/spglobal`
- Marketplace now publishes only `financial-analysis` and `wealth-management`.
- Data-routing defaults changed to free-source-first with mandatory provenance metadata.

## License

[Apache License 2.0](./LICENSE)

## Disclaimer

These plugins assist with financial workflows but do not provide financial or investing advice. Always verify conclusions with qualified professionals before acting.
