---
name: source-policy
description: Personal-investor data routing and provenance contract for all financial-analysis and wealth-management skills.
---

# Source Policy (Personal Investor)

## Purpose
One routing contract for all skills. No per-skill custom hierarchy unless explicitly documented.

## Required Output Metadata
For every external numeric claim or market/macro statement, include:
- `source`: provider + endpoint/doc
- `as_of`: ISO date or datetime
- `freshness`: `live|eod|delayed|stale`
- `confidence`: `high|medium|low`
- `fallback_used`: `true|false`

## Domain Routing (Default Order)

### 1) Fundamentals (public companies)
1. SEC EDGAR / `data.sec.gov`
2. Premium MCP (optional verification/enrichment)
3. Web/document fallback (issuer IR, filings mirror)

### 2) Macro & Liquidity
1. FRED
2. NY Fed + U.S. Treasury
3. Premium MCP macro tools (optional)
4. Web fallback

### 3) Prices & Indicators (equities/ETFs)
1. Twelve Data
2. Alpha Vantage
3. Premium MCP market data (optional)
4. Web fallback

### 4) Crypto (BTC/ETH)
1. CoinGecko
2. Twelve Data / Alpha Vantage
3. Web fallback

### 5) News & Catalysts
1. Google News RSS (ticker/topic scoped)
2. Web search for context/confirmation
3. Premium news MCP (optional)

## Conflict Rules
- If two sources differ materially:
  - Prefer higher-authority primary source for that domain.
  - Report both values if delta > 10%.
  - Downgrade confidence to `medium` or `low`.
- Never present unresolved conflicts as a single “fact”.

## Fallback Rules
- If primary fails, move to next source and set `fallback_used=true`.
- If all sources fail:
  - state “data unavailable”
  - do not fabricate
  - propose retry window and missing inputs.

## Freshness Defaults
- Prices/news: same-day required; otherwise mark `stale`.
- Macro series: latest published release acceptable; include release date.
- Fundamentals: latest filed 10-Q/10-K acceptable; include filing date.

## Prohibited Behavior
- No web search as silent primary for fundamentals/macro when preferred free sources are available.
- No number without provenance metadata.
- No fabricated citations.

## Example Citation Line
`Revenue growth 12.4% (source: SEC 10-K FY2025, as_of: 2026-02-18, freshness: eod, confidence: high, fallback_used: false)`
