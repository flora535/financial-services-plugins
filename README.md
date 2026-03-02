# Personal Investor Financial Plugins

<p align="right"><a href="./README.md">English</a> | <a href="./README.zh-CN.md">简体中文</a></p>

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

## Data Source Hierarchy

Fallback hierarchy is defined directly in each core analysis skill (upstream style), not in a shared policy file:
- `financial-analysis/skills/comps-analysis/SKILL.md`
- `financial-analysis/skills/dcf-model/SKILL.md`
- `financial-analysis/skills/3-statements/SKILL.md` (conditional SEC extraction path)

Default priority for fundamentals is SEC-first:
1. SEC MCP / SEC EDGAR
2. Structured secondary sources (Twelve Data / Alpha Vantage / optional premium MCP)
3. Web/document fallback with explicit provenance

### SEC MCP (local) setup
```bash
cd financial-analysis/mcp/sec-edgar
npm install
npm run build
```

`financial-analysis/.mcp.json` is configured to run:
`node mcp/sec-edgar/dist/index.js`

Premium MCP connectors are retained in `financial-analysis/.mcp.json` as optional secondary sources.

Required metadata for external claims:
- `source`
- `as_of`
- `freshness`
- `confidence`
- `fallback_used`

### Free Source Pitfalls (Important)
- SEC requests need a real `SEC_USER_AGENT`; avoid burst scraping.
- FRED auth/version patterns and timestamps must be normalized before comparison.
- NY Fed/Treasury endpoints are path-sensitive; use known-good endpoints.
- Twelve Data / Alpha Vantage can return HTTP 200 with business-level errors.
- Google News RSS parsing should not assume multi-line XML.
- Massive is fallback-only for normal workflows (free-tier rate limits).
- If data is stale/missing after retry, mark `data unavailable` and reduce confidence.

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

## Repository Structure

```text
financial-services-plugins/
├── .claude-plugin/marketplace.json
├── financial-analysis/
│   ├── .claude-plugin/plugin.json
│   ├── .mcp.json
│   ├── mcp/sec-edgar/
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
