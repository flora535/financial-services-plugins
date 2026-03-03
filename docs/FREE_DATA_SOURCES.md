# Free Data Sources (Personal Investing Stack)

Use this list for personal wealth management, stock picking, and BTC/ETH spot analysis.

## Integration SOP

When evaluating a new free data source, run through these steps in order:

### 1. Profile the source
- What data does it provide? (fundamentals, market data, macro, alternative)
- Free tier quota — compute daily call budget (e.g. 5/min = ~7,200/day)
- Historical depth on free tier (2yr vs 20yr matters for DCF)
- Auth requirements (API key, OAuth, keyless)

### 2. Find an MCP
- Search for official MCP first (`<provider> MCP server`)
- Then community MCPs on GitHub/npm/PyPI
- No MCP = no integration. We don't build custom connectors.

### 3. Map to existing workflows
The source must serve at least one skill workflow's data needs:

| Workflow | Data consumed |
|----------|--------------|
| Comps | Standardized fundamentals, trading multiples, consensus estimates |
| DCF | Multi-year historical financials, current price/beta, risk-free rate |
| 3-statements | Raw filing data (10-K/10-Q), structured line items |

If it doesn't serve any workflow → "Not Integrated (Nice to Have)".

### 4. Check for duplication vs complementarity
- Does an integrated source already cover this data?
- If yes: does the new source offer meaningfully better quota, depth, or coverage?
- Example: Massive (7,200/day) complements Alpha Vantage (25/day) for multi-ticker comps
- Example: NY Fed SOFR duplicates FRED → skip

### 5. Wire it up (if integrating)
1. Add server entry to `financial-analysis/.mcp.json`
2. Add MCP name to `comps-analysis/SKILL.md` tier 1 list ("FIRST: Check for MCP data sources — If SEC EDGAR MCP, …") if applicable
3. Add MCP name to `dcf-model/SKILL.md` "Data Sources Priority" (L57) and "Available Data Sources" (L1189) if applicable
4. Mark ✅ in `README.md` and `README.zh-CN.md` tables
5. Move entry from "Not Integrated" to "Integrated" in this file with `Used by` field

## Integrated

### 1. SEC EDGAR / data.sec.gov
- **What it provides**: 10-K/10-Q/8-K filings, XBRL structured financials, insider trades, 13-F institutional holdings
- **Free quota**: Unlimited (rate-limited to 10 req/sec with User-Agent)
- **MCP**: [edgartools](https://github.com/dgunning/edgartools) built-in MCP (`uvx edgartools-mcp`)
- **Used by**: comps (fundamentals), DCF (historical financials), 3-statements (filing extraction)

### 2. FRED (St. Louis Fed)
- **What it provides**: 800k+ macro time series — interest rates (Fed Funds, Treasuries), inflation (CPI, PCE), GDP, labor market, credit spreads, SOFR
- **Free quota**: Unlimited (rate-limited, requires API key)
- **MCP**: [fred-mcp-server](https://github.com/stefanoamorelli/fred-mcp-server) (`npx fred-mcp-server`)
- **Used by**: DCF (risk-free rate for WACC/CAPM)

### 3. Alpha Vantage
- **What it provides**: Real-time/historical stock quotes, 50+ technical indicators, company fundamentals (IS/BS/CF), earnings calendar
- **Free quota**: 25 API calls/day
- **MCP**: [Official remote MCP](https://mcp.alphavantage.co)
- **Used by**: DCF (current stock price, beta), comps (market cap, trading data)

### 4. Twelve Data
- **What it provides**: Real-time and historical stock/crypto/forex quotes, 100+ technical indicators (MACD, RSI, Bollinger Bands, etc.), WebSocket streaming
- **Free quota**: 800 calls/day, limited to 8 symbols
- **MCP**: [Official MCP](https://github.com/twelvedata/mcp) (`uvx mcp-server-twelve-data@latest`)
- **Used by**: DCF (deep single-company price/indicator data — 800 calls/day complements Alpha Vantage's 25/day), comps (supplements Alpha Vantage within 8-symbol cap)

### 5. Massive API (formerly Polygon.io)
- **What it provides**: Stocks (OHLC, trades, quotes, aggregates), options chains, forex, crypto, fundamentals, analyst ratings, corporate actions, news, Treasury yields
- **Free quota**: 5 API calls/min (~7,200/day), 2 years historical data (Stocks Basic plan)
- **MCP**: [Official MCP](https://github.com/massive-com/mcp_massive) (`uvx mcp-massive`)
- **Env var**: `MASSIVE_API_KEY`
- **Used by**: Comps (multi-company fundamentals and trading data — 7,200 calls/day vs Alpha Vantage's 25/day makes multi-ticker workflows practical), DCF (current market data)

## Not Integrated (Nice to Have)

### 6. NY Fed + U.S. Treasury
- **What it provides**: SOFR/EFFR/BGCR/TGCR secured/unsecured rates, repo and reverse repo (ON RRP) operations data, SOMA holdings, Treasury General Account (TGA) balances, daily Treasury statements
- **Free quota**: Unlimited (no key required for NY Fed; Treasury Fiscal Data API also keyless)
- **MCP available**: [mcp-newyorkfed](https://github.com/trygordian/mcp-newyorkfed) covers NY Fed rates + repo ops. No MCP for Treasury TGA yet.
- **Why not integrated**: SOFR already available via FRED. ON RRP/TGA are macro liquidity indicators — no current skill workflow consumes them directly.

### 7. CoinGecko
- **What it provides**: 15,000+ coin prices, market cap, 24h volume, circulating supply, historical OHLC, exchange data, NFT collections, on-chain DEX data via GeckoTerminal
- **Free quota**: 50 calls/min (keyless demo access)
- **MCP available**: [Official MCP](https://www.npmjs.com/package/@coingecko/coingecko-mcp) v2.5.0, maintained by CoinGecko
- **Why not integrated**: No current plugin workflow operates on crypto assets. Comps/DCF/3-statements are public equity workflows.

### 8. Google News
- **What it provides**: Keyword/topic/location-filtered news articles, trending search terms
- **Free quota**: Unlimited (no key required)
- **MCP available**: [server-google-news](https://github.com/chanmeng666/server-google-news) — option if dedicated news feed is needed, but web search covers most of its features
- **Why not integrated**: No current skill workflow step consumes news. Web search already handles ad-hoc news lookups.
