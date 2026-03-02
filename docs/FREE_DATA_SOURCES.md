# Free Data Sources (Personal Investing Stack)

Use this list for personal wealth management, stock picking, and BTC/ETH spot analysis.

1. SEC EDGAR / data.sec.gov
- Use for company filings and core fundamental data (10-K, 10-Q, 8-K).

2. FRED (St. Louis Fed)
- Use for macro data (rates, inflation, labor, growth, liquidity proxies).

3. NY Fed + U.S. Treasury Data
- Use for SOFR, ON RRP, TGA, and related liquidity inputs.

4. CoinGecko API
- Use for BTC/ETH spot prices, market stats, and crypto market context.

5. Twelve Data (Free Tier)
- Use for stock/crypto quotes and common technical indicators.

6. Alpha Vantage (Free Tier)
- Use as a backup source for quotes, indicators, and selected fundamentals.

7. Google News RSS (No Key, Default News Layer)
- Use as default headline/catalyst feed for watchlists and weekly event scans.
- Prefer ticker/company/topic-specific RSS queries plus date filters.
- This replaces API-key news as the default for personal workflow.

8. Massive API (formerly polygon.io, Optional)
- Use as optional market-data backup for stocks (EOD/reference/corporate actions/technical indicators/minute aggregates).
- Free Individual (`Stocks Basic`): 5 API calls/minute, 2 years historical data.
- Requires API key (`MASSIVE_API_KEY`).

## Suggested Priority 

1. Stocks fundamentals: SEC EDGAR
2. Macro/liquidity: FRED + NY Fed + U.S. Treasury
3. Crypto market: CoinGecko
4. Quote/indicator backup: Twelve Data, Alpha Vantage
5. News overlay (default): Google News RSS + web search
6. Optional market-data backup: Massive API (when your key/rate limit permits)

## Default News Workflow (No Key)

1. Use web search for current context and one-off checks.
2. Use Google News RSS for repeatable feeds in watchlists.
3. Build per-asset feeds (AAPL, TSLA, BTC, ETH, Fed, CPI, FOMC).
4. No API-key news source required by default.

## Google News RSS Examples

- Broad markets:
  - `https://news.google.com/rss/search?q=US+stock+market+when:7d&hl=en-US&gl=US&ceid=US:en`
- Single stock:
  - `https://news.google.com/rss/search?q=AAPL+stock+when:7d&hl=en-US&gl=US&ceid=US:en`
- Crypto:
  - `https://news.google.com/rss/search?q=BTC+OR+Bitcoin+when:7d&hl=en-US&gl=US&ceid=US:en`
  - `https://news.google.com/rss/search?q=ETH+OR+Ethereum+when:7d&hl=en-US&gl=US&ceid=US:en`

## Massive API Notes

1. Branding: Polygon is now Massive; old polygon.io references map to Massive services.
2. Env var: set `MASSIVE_API_KEY` in `.env`.
3. Keep Massive as backup source to avoid hitting 5 calls/minute caps during routine scans.
