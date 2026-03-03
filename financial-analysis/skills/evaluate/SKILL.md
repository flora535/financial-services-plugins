---
name: evaluate
description: |
  Quick buy/hold/sell position evaluator for personal investors. Scores valuation,
  fundamentals, technicals, catalysts, and position P&L into a single actionable signal.
  Integrates with comps-analysis for peer context, dcf-model for deeper valuation,
  and wealth-management (tlh, rebalance) for portfolio actions.

  Triggers: evaluate position, should I buy, should I sell, buy or sell, hold or sell,
  position check, stock check, quick valuation, is it time to sell
---

# Position Evaluate

Fast, multi-factor position evaluation producing a **Buy More / Hold / Trim / Sell** signal
with conviction level and reasoning. Not a full DCF or comps model — a quick-decision
framework that chains into those skills when deeper analysis is warranted.

## Data Source Hierarchy

Follow the same priority established in comps-analysis and dcf-model:
1. **MCP Servers** (SEC EDGAR, Massive API, FRED, Twelve Data, Alpha Vantage)
2. User-provided data
3. Web search (fallback only — do NOT use if MCP sources are available)

## Step 1: Collect Inputs

**Required:**
- Ticker (e.g., AAPL)
- Cost basis per share (e.g., $150)

**Optional** (ask, but don't block on):
- Shares held (enables dollar P&L calculation)
- Holding period or purchase date (for short-term vs long-term capital gains)

If holding period not given, show both short-term and long-term tax implications.

## Step 2: Peer Context (Lightweight Comps)

Run a **quick version** of the comps-analysis workflow — 3-4 peers, core multiples only.

Use `edgar_compare` (SEC EDGAR MCP):
- `identifiers`: target ticker + 3-4 peers in same sector
- `metrics`: `["revenue", "net_income", "margins", "growth"]`
- `periods`: 2

Capture from results:
- **Peer median P/E** — is target trading at premium or discount?
- **Peer median EV/EBITDA** — same
- **Peer median revenue growth** — is target growing faster or slower?
- **Peer median margins** — operating quality benchmark

Use the comps-analysis statistical framework: calculate median, 25th percentile, 75th percentile
across the peer set. Position the target within this range.

If `edgar_compare` is unavailable, fall back to individual `edgar_company` calls for 2-3 peers.

## Step 3: Target Company Data

Fetch in parallel where possible. Target ~8-9 total API calls.

### 3A: Price & Fundamentals — Massive API (primary)

Use `search_endpoints` → `call_api`:
- Current quote: price, day change %, volume, 52-week high/low, market cap
- Fundamentals: revenue (TTM), EBITDA, EPS (diluted), gross margin, operating margin, net margin
- Multiples: P/E (trailing), EV/EBITDA, EV/Revenue, dividend yield, P/B

Store with `store_as: "fundamentals"` for potential SQL follow-up.

### 3B: Earnings Trajectory — SEC EDGAR

Use `edgar_company`:
- `identifier`: ticker
- `include`: `["financials"]`
- `period`: `"quarterly"`
- `periods`: 8

From 8 quarters, determine:
- Revenue trend: accelerating, stable, or decelerating growth
- EPS trend: same
- Margin trajectory: expanding, stable, or compressing

### 3C: Catalysts — SEC EDGAR

**Insider activity** via `edgar_ownership`:
- `identifier`: ticker
- `analysis_type`: `"insiders"`
- `days`: 90

Summarize: net insider buying vs selling, any large transactions (>$500K).

**Recent events** via `edgar_filing`:
- `identifier`: ticker
- `form`: `"8-K"`
- `sections`: `["items"]`

Flag material events: guidance changes, M&A, executive departures, buyback announcements.

### 3D: Technicals — Twelve Data (preferred) or Alpha Vantage (fallback)

Fetch with 1 API call:
- RSI (14-day): overbought >70, oversold <30
- MACD: signal line crossover direction (bullish/bearish)
- Price vs 50-day moving average
- Price vs 200-day moving average

Prefer Twelve Data (800 calls/day) over Alpha Vantage (25 calls/day) to conserve AV quota.
If neither available, skip technicals and reduce conviction one level.

### 3E: Macro Context — FRED

Use `fred_get_series`:
- `series_id`: `"DGS10"` — 10-year Treasury yield (opportunity cost benchmark)

## Step 4: Score 5 Factors

Rate each factor from **-2** (strong negative) to **+2** (strong positive).

### Factor 1: Valuation

| Condition | Score |
|-----------|-------|
| P/E AND EV/EBITDA both below peer 25th percentile | +2 |
| P/E OR EV/EBITDA below peer median | +1 |
| Both within ~15% of peer median | 0 |
| P/E OR EV/EBITDA above peer 75th percentile | -1 |
| Both above peer 75th percentile | -2 |

Also compare to stock's own 2-year average multiples if historical data available.

### Factor 2: Fundamentals

| Condition | Score |
|-----------|-------|
| Revenue + EPS both accelerating, margins expanding | +2 |
| Revenue or EPS growing, margins stable | +1 |
| Flat growth, stable margins | 0 |
| Revenue or EPS declining, or margins compressing | -1 |
| Revenue AND EPS declining, margins compressing | -2 |

### Factor 3: Technicals

| Condition | Score |
|-----------|-------|
| Price > 200-DMA, RSI 40-60, MACD bullish | +2 |
| Price > 200-DMA, not overbought | +1 |
| Mixed signals, price near 200-DMA | 0 |
| Price < 200-DMA, RSI not oversold | -1 |
| Price < 200-DMA, bearish MACD, overbought in downtrend | -2 |

If technicals data unavailable, score as 0 and flag in Limitations.

### Factor 4: Catalysts

| Condition | Score |
|-----------|-------|
| Net insider buying + positive 8-K (raised guidance, buyback) | +2 |
| Net insider buying OR positive catalyst | +1 |
| No notable activity | 0 |
| Net insider selling OR negative 8-K (CFO departure, writedown) | -1 |
| Heavy insider selling + negative catalyst | -2 |

### Factor 5: Position & Tax Context

Calculate:
- **Unrealized P&L**: (current price - cost basis) / cost basis
- **Tax status**: short-term (<1yr) vs long-term (>1yr)
- **Estimated tax impact**: what selling would cost in taxes (or save via loss harvest)

| Condition | Score |
|-----------|-------|
| Loss >20%, tax-loss harvest opportunity | +1 (tilts toward sell to harvest) |
| Large long-term gain (>50%), high tax drag from selling | +1 (tilts toward hold) |
| Small gain/loss, minimal tax impact | 0 |
| Short-term gain, selling triggers higher rate | +1 (tilts toward hold if other factors neutral+) |

This factor **biases toward inertia** — tax friction is real for personal investors. A "meh" stock
with a large embedded long-term gain should be held unless other factors are strongly negative.

## Step 5: Generate Signal

### Composite Score

Sum 5 factor scores. Range: -10 to +10.

| Composite | Signal | Conviction |
|-----------|--------|------------|
| +6 to +10 | **Buy More** | High |
| +3 to +5 | **Buy More** | Medium |
| +1 to +2 | **Hold** | Medium |
| -1 to 0 | **Hold** | Low |
| -2 to -3 | **Trim** | Medium |
| -4 to -10 | **Sell** | High |

### Override Rules
- Valuation = -2 AND Fundamentals = -2 → **Sell** regardless of other scores
- Loss >30% AND Fundamentals >= 0 → flag as "potential averaging-down opportunity"
- If technicals skipped → widen conviction one level (High → Medium, Medium → Low)

## Step 5B: Entry Price Levels

**Condition:** Only compute when signal is **Hold** or **Buy More**. Skip entirely for Trim/Sell.

Derive 3 entry tiers from data already collected — no additional API calls needed.

### Calculation

1. **Source multiples from peer set (Step 2):**
   - Light add multiple = peer 75th percentile P/E (quality premium floor)
   - Meaningful add multiple = peer median P/E
   - Back up the truck multiple = peer 25th percentile P/E

2. **Compute tier prices:**
   - `tier_price = target_multiple × trailing_EPS` (EPS from Step 3A)

3. **Cross-check with technicals:**
   - Compare each tier against support levels visible in weekly price data (Step 3D)
   - If a tier aligns within 3% of a technical support zone, note "near {50-DMA / 200-DMA / 52wk low}" in the output

4. **Forward-adjusted column** (if earnings trajectory from Step 3B shows consistent growth):
   - Estimate forward EPS growth rate from the quarterly EPS trend
   - `tier_price_fwd = target_multiple × trailing_EPS × (1 + growth_rate)`
   - If growth rate not determinable, omit this column

5. **Discount from current price:**
   - `discount = (current_price - tier_price) / current_price`

### Adaptive Logic

- **Stock already below Light add price →** shift language: "Already in buy zone — current price is below the Light add tier"
- **All tiers above current price →** note: "Stock already trades below fair entry; consider adding now" (reinforces Buy More signal)
- **Sector adjustment:** Use actual peer percentiles, not hardcoded multiples. The illustrative 30x/27x/23x is mega-cap tech; a bank might use 12x/10x/8x. Always derive from the peer set computed in Step 2.

## Step 6: Output

Print to terminal. If user requests, also save as `{TICKER}-evaluate-{YYYY-MM-DD}.md`.

```
================================================================
  {TICKER} POSITION EVALUATION — {YYYY-MM-DD}
================================================================

SIGNAL: {BUY MORE / HOLD / TRIM / SELL}   Conviction: {High/Med/Low}

----------------------------------------------------------------
  YOUR POSITION
----------------------------------------------------------------
  Cost Basis:      ${cost_basis}
  Current Price:   ${current_price}  ({change_pct}% today)
  Unrealized P&L:  {+/-$amount} ({+/-pct}%)
  Tax Status:      {Short-term / Long-term}
  Tax Note:        {e.g. "Selling triggers ~$X estimated tax"
                    or "Loss harvestable for ~$X tax benefit"}

----------------------------------------------------------------
  FACTOR SCORECARD
----------------------------------------------------------------
  Valuation:     {score}  {one-line reason}
  Fundamentals:  {score}  {one-line reason}
  Technicals:    {score}  {one-line reason}
  Catalysts:     {score}  {one-line reason}
  Position/Tax:  {score}  {one-line reason}
                 -----
  Composite:     {total}/10

----------------------------------------------------------------
  KEY METRICS
----------------------------------------------------------------
  Price:         ${price}  (52wk: ${low} - ${high})
  P/E (TTM):     {pe}x  (Peer median: {peer_pe}x)
  EV/EBITDA:     {ev_ebitda}x  (Peer median: {peer_ev}x)
  Revenue (TTM): ${rev}  ({rev_growth}% YoY)
  EPS (TTM):     ${eps}  ({eps_growth}% YoY)
  Gross Margin:  {gm}%   Oper Margin: {om}%
  RSI (14d):     {rsi}   MACD: {bullish/bearish}
  Div Yield:     {yield}%
  10Y Treasury:  {rate}%

----------------------------------------------------------------
  PEER CONTEXT
----------------------------------------------------------------
  Peers: {Peer1}, {Peer2}, {Peer3}
  Target vs Median:
    P/E:        {target_pe}x vs {median_pe}x ({premium/discount}%)
    EV/EBITDA:  {target_ev}x vs {median_ev}x ({premium/discount}%)
    Rev Growth: {target_g}% vs {median_g}%

----------------------------------------------------------------
  CATALYSTS & RISKS
----------------------------------------------------------------
  Insider Activity (90d): {e.g. "3 buys ($2.1M) / 1 sell ($180K)"}
  Recent 8-K:             {most material event, or "None notable"}
  Key Risk:               {one-sentence top risk}

----------------------------------------------------------------
  REASONING
----------------------------------------------------------------
  {2-4 sentences synthesizing factor scores into a coherent
   narrative. Explain WHY the signal is what it is. Reference
   the strongest factors driving the decision.}

----------------------------------------------------------------
  ENTRY PRICE LEVELS          (Hold / Buy More signals only)
----------------------------------------------------------------
  Based on: EPS ${eps} | Peer median P/E {peer_pe}x | EPS growth ~{g}%

  Tier              Price    P/E    vs Now   Next-Yr Adj   Note
  Light add         ${xxx}   {pe}x  -{y}%    ${xxx}        {support note}
  Meaningful add    ${xxx}   {pe}x  -{y}%    ${xxx}        {support note}
  Back up the truck ${xxx}   {pe}x  -{y}%    ${xxx}        {support note}

  Your cost basis: ${cost}. Any add below ${light} keeps blended
  basis attractive.

  Scaling approach: Set limit orders at each tier (1/3 each).
  Most likely catalyst for these prices: {broad market correction /
  earnings miss / sector rotation}.

----------------------------------------------------------------
  NEXT STEPS
----------------------------------------------------------------
  {Contextual recommendations based on signal:}
  - "Run /financial-analysis:dcf {TICKER} for intrinsic value"
  - "Run /financial-analysis:comps {TICKER} for full peer analysis"
  - "Run /wealth-management:tlh to execute tax-loss harvest"
  - "Run /wealth-management:rebalance to check portfolio impact"
  - "Set limit orders at ${light} / ${meaningful} / ${truck}"
    (Hold/Buy More only — references Entry Price Levels above)

----------------------------------------------------------------
  LIMITATIONS
----------------------------------------------------------------
  - {Any data gaps: "Technicals unavailable", "Only 2 peers found"}
  - No analyst consensus estimates (free data only)
  - Not financial advice — personal decision aid only
================================================================
```

### Next Steps Logic

Show only relevant suggestions:

| Condition | Suggest |
|-----------|---------|
| Signal = Buy More (High) | `/financial-analysis:dcf` for intrinsic value confirmation |
| Valuation factor ambiguous (score 0) | `/financial-analysis:comps` for full peer deep-dive |
| Unrealized loss >10% | `/wealth-management:tlh` to evaluate tax-loss harvest |
| Signal = Trim or Sell | `/wealth-management:rebalance` to check portfolio drift impact |
| Fundamentals unclear | `/financial-analysis:3-statements` for full financial model |
| Signal = Hold or Buy More | Show Entry Price Levels section; suggest "Set limit orders at $X / $X / $X (light / meaningful / back-up-the-truck)" |
