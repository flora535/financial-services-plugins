# Free SEC EDGAR MCP Server

Local MCP server for SEC EDGAR fundamentals workflows.

## Required env

```bash
SEC_USER_AGENT="free-sec-edgar-mcp/1.0 (you@example.com)"
```

## Install + build

```bash
cd mcp/free-sec-edgar
npm install
npm run build
```

## Run locally

```bash
npm start
```

## Exposed tools

- `sec.resolve_company`
- `sec.list_filings`
- `sec.get_company_facts`
- `sec.get_financial_statements`
- `sec.get_filing_section`

## Tool behavior

- SEC is treated as primary fundamentals source.
- Missing metrics return explicit `missingFields` and lowered confidence.
- No fabricated values. Missing fields should be surfaced as `data unavailable` by calling skills.
