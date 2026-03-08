---
name: btc-bottom
description: |
  Bitcoin cycle-bottom detector using 6 on-chain + market indicators.
  Produces Weak/Moderate/Strong/Very Strong/Extreme signal with conviction.

  Triggers: bitcoin bottom, is BTC at the bottom, should I buy bitcoin,
  BTC oversold, crypto bottom signal, bitcoin cycle bottom, BTC entry timing
---

# BTC Bottom-Call Analysis

6-indicator Bitcoin cycle-bottom detector. Scores on-chain + market signals to assess
whether BTC is near a generational buying opportunity. On-chain metrics that lack MCP
sources are handled via user input or web search fallback with explicit flags and
conviction caps.

## Data Source Hierarchy

Same priority as evaluate and comps-analysis:
1. **MCP Servers** (Twelve Data, Massive API, FRED)
2. **User-provided data** (on-chain metrics: MVRV, LTH supply, miner cost)
3. **Web search** (fallback for on-chain only — flag as Tier 3)

## Step 1: Collect Inputs

**Optional** (ask, but don't block on):
- Current BTC price (if not provided, fetch via MCP in Step 3A)
- MVRV ratio (from Glassnode, CryptoQuant, etc.)
- LTH (Long-Term Holder) supply percentage
- Miner breakeven price

If on-chain metrics not provided, attempt web search in Step 3D. If still unavailable,
mark as `data unavailable` and apply missing-data conviction caps.

## Step 2: Timeliness Gate

Before analysis, verify data freshness. Check timestamps as each source returns.

| Data Type | Stale If Older Than | Action |
|-----------|-------------------|--------|
| Quote / price | 1 hour (crypto trades 24/7) | Re-query; if still stale, warn + cap conviction at Medium |
| RSI / MACD (weekly) | 1 day | Re-query; if stale, skip technicals |
| Fear & Greed | 1 day | Warn if stale |
| On-chain (MVRV, LTH) | 7 days | Acceptable — on-chain moves slowly |
| Miner cost | 14 days (difficulty adjusts biweekly) | Acceptable |
| FRED macro series | 7 days | Acceptable — macro moves slowly |

If **2+ data sources** stale after re-query -> cap conviction at **Low** regardless of score.

## Step 3: Fetch Data

Target ~6-8 API calls, parallelizable. Run all sub-steps concurrently.

### 3A: Price & Volume — Massive API

Use `search_endpoints` -> `call_api`:
- BTC/USD quote: price, 24h change %, volume, market cap
- 30-day average volume (for volume dry-up calculation)
- 52-week high/low

### 3B: Technicals — Twelve Data

Use Twelve Data MCP (preferred — 800 calls/day):
- Weekly RSI (14-period) for BTC/USD
- MACD on weekly timeframe
- Price vs 50-day and 200-day moving average

If Twelve Data unavailable, fall back to Alpha Vantage. If neither available, skip
technicals — score indicator #1 as unavailable.

### 3C: Fear & Greed — Alternative.me

Direct HTTP fetch (no API key needed):
```
GET https://api.alternative.me/fng/
```

Parse JSON response -> extract `value` (0-100) and `value_classification`.

### 3D: On-chain Metrics — Glassnode MCP (if available), User Input, or Web Search

For each metric not provided by user, try this order:
1. Glassnode MCP `fetch_metric` (if MCP configured)
2. User-provided value
3. Web search fallback

Notes:
- Do not assume Glassnode public mode always includes required metrics.
- In public/no-key mode, historical range may be limited (commonly 30 days).
- If MVRV/LTH/miner-cost metric query fails or returns empty, mark as unavailable and continue.

Web search fallback patterns:
- **MVRV ratio**: search `"Bitcoin MVRV ratio" site:glassnode.com OR site:cryptoquant.com OR site:lookintobitcoin.com`
- **LTH Supply ratio**: search `"Bitcoin long term holder supply" site:glassnode.com OR site:cryptoquant.com`
- **Miner breakeven price**: search `"Bitcoin miner breakeven cost" site:glassnode.com OR site:cryptoquant.com OR site:hashrateindex.com`

For each metric:
- If found via web search: use value, flag source as **Tier 3 (web search)** in output
- If not found: mark `data unavailable`, exclude from denominator in scoring

### 3E: Macro Context — FRED

Reuse evaluate's macro framework. Use `fred_get_series` for each (3 calls, parallelizable):

| Series ID | What | Why |
|-----------|------|-----|
| `DGS10` | 10-year Treasury yield | Risk-free rate / opportunity cost |
| `T10Y2Y` | 10Y-2Y Treasury spread | Yield curve inversion = recession signal |
| `BAMLH0A0HYM2` | ICE BofA High Yield spread | Credit stress — widens before risk-off |

Derive macro backdrop:

| Condition | Backdrop |
|-----------|----------|
| 10Y falling + spread positive + HY spread narrowing | Supportive |
| Mixed signals or stable readings | Neutral |
| 10Y rising sharply OR spread inverted OR HY spread >500bp | Hostile |

### 3F: Funding + Derivatives Context — OKX Public API (Deterministic, optional)

Use OKX public endpoints when derivatives context is needed (no auth):
- Funding (current): `GET https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP`
- Funding history: `GET https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=21`
- Long/short ratio: `GET https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&period=1H`
- Open interest: `GET https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP`

Do not add these as extra scored indicators by default; use as confidence context only.

## Step 4: Score 6 Indicators

Each indicator: **triggered** / **not triggered** / **data unavailable**

| # | Indicator | Trigger Condition | Source |
|---|-----------|----------|--------|
| 1 | Weekly RSI | < 30 | Twelve Data (MCP) |
| 2 | Volume Dry-Up | Current vol < 70% of 30-day avg | Massive (MCP) |
| 3 | MVRV Ratio | < 1.0 (network underwater) | User input / web search |
| 4 | Fear & Greed | < 25 (Extreme Fear) | Alternative.me (HTTP) |
| 5 | Miner Shutdown | Price at or below miner breakeven cost | User input / web search |
| 6 | LTH Supply | Rising AND > 70% of circulating supply | User input / web search |

**Trigger ratio** = triggered count / available count (exclude unavailable from denominator).

## Step 5: Generate Signal

### Signal Table

| Triggered | Signal | Conviction |
|-----------|--------|------------|
| 0-1 | **No Bottom** | -- |
| 2 | **Weak** | Low |
| 3 | **Moderate** | Medium |
| 4 | **Strong** | Medium-High |
| 5 | **Very Strong** | High |
| 6 | **Extreme (Historic)** | Very High |

**Cap rule**: If available indicators < 4, max signal = **Moderate** (prevent false positives from sparse data).

### Missing-Data Conviction Caps

| Unavailable Indicators | Max Conviction |
|----------------------|---------------|
| 0 | Very High |
| 1 | High |
| 2 | Medium |
| 3+ | Low |

Final conviction = min(signal-based, staleness cap, missing-data cap).

### Override Rules
- Macro backdrop Hostile -> reduce conviction one level
- MVRV < 1.0 alone is insufficient — needs at least 1 confirming signal to count toward trigger total

## Step 5B: Position Sizing

| Signal | Suggested Allocation | Strategy |
|--------|---------------------|----------|
| No Bottom | 0% | Wait for more signals |
| Weak | 5-10% of crypto allocation | Micro test position |
| Moderate | 10-20% | Begin DCA |
| Strong | 20-40% | Accelerate DCA |
| Very Strong | 40-60% | Aggressive accumulation |
| Extreme | 60-80% | Max conviction, frontload |

Include DCA schedule: "Split into 4 weekly tranches of ~{size/4}% each"

## Step 5C: Pre-Mortem

After scoring, force one falsification exercise:

> "If BTC drops another 40% from here, the most likely cause is: ___"

Derive from the weakest indicator + macro backdrop. This is mandatory — never skip it.

## Step 6: Output

Print to terminal.

```
================================================================
  BTC BOTTOM-CALL ANALYSIS — {YYYY-MM-DD HH:MM UTC}
================================================================

SIGNAL: {NO BOTTOM / WEAK / MODERATE / STRONG / VERY STRONG / EXTREME}
Conviction: {Low/Med/Med-High/High/Very High}
{if capped: "(capped from {original} — {reason})"}

----------------------------------------------------------------
  DATA FRESHNESS
----------------------------------------------------------------
  Price (Massive):    {timestamp}  {checkmark/warning}
  Technicals (12D):   {timestamp}  {checkmark/warning/unavailable}
  Fear & Greed:       {timestamp}  {checkmark/warning}
  MVRV:               {timestamp}  {checkmark/warning/unavailable}
  LTH Supply:         {timestamp}  {checkmark/warning/unavailable}
  Miner Cost:         {timestamp}  {checkmark/warning/unavailable}
  Macro (FRED):       {date}       {checkmark}

----------------------------------------------------------------
  INDICATOR DASHBOARD
----------------------------------------------------------------
  #  Indicator        Value     Signal       Source          Note
  1  Weekly RSI       {val}     {Y/N}        Twelve Data     {oversold/neutral}
  2  Volume Dry-Up    {pct}%    {Y/N}        Massive         {vs 30d avg}
  3  MVRV Ratio       {val}     {Y/N/n.a.}   {source}        {underwater/profit}
  4  Fear & Greed     {val}     {Y/N}        Alternative.me  {classification}
  5  Miner Shutdown   ${cost}   {Y/N/n.a.}   {source}        {margin to price}
  6  LTH Supply       {pct}%   {Y/N/n.a.}   {source}        {rising/falling}
                                ----
  Triggered: {X} / {Y} available

----------------------------------------------------------------
  BTC PRICE CONTEXT
----------------------------------------------------------------
  Price:         ${price}  (24h: {change}%)
  Market Cap:    ${mcap}
  Volume (24h):  ${vol}  (vs 30d avg: {pct}%)
  52wk Range:    ${low} — ${high}
  200-DMA:       ${dma}  (price {above/below} by {pct}%)

----------------------------------------------------------------
  MACRO BACKDROP
----------------------------------------------------------------
  10Y Treasury:  {rate}%
  Yield Curve:   {spread}  {normal/flat/inverted}
  HY Spread:     {spread}bp  {tight/normal/wide}
  Backdrop:      {Supportive / Neutral / Hostile}

----------------------------------------------------------------
  REASONING
----------------------------------------------------------------
  {2-4 sentences: why this signal, which indicators drove it,
   how macro context affects conviction}

----------------------------------------------------------------
  PRE-MORTEM
----------------------------------------------------------------
  If BTC drops another 40% from here, the most likely cause is:
  {one sentence from weakest indicator + macro}

----------------------------------------------------------------
  POSITION SIZING
----------------------------------------------------------------
  Signal:     {signal}
  Suggested:  {X-Y}% of crypto allocation
  Strategy:   Split into 4 weekly tranches of ~{size/4}% each
  Stop ref:   If price breaks ${support} on elevated volume, reduce by {Y}%

----------------------------------------------------------------
  HISTORICAL PARALLEL
----------------------------------------------------------------
  Last time {N}+ indicators aligned: {date}
  BTC price then: ${price} -> ${peak} ({pct}% over {months} months)

----------------------------------------------------------------
  NEXT STEPS
----------------------------------------------------------------
  {Contextual — see Next Steps Logic below}

----------------------------------------------------------------
  LIMITATIONS
----------------------------------------------------------------
  - {Missing on-chain data flags}
  - On-chain metrics sourced via web search (Tier 3) — verify independently
  - Model based on 4 historical cycles — sample size is small
  - Not financial advice — personal research aid only
================================================================
```

### Next Steps Logic

Show only relevant suggestions:

| Condition | Suggest |
|-----------|---------|
| Signal >= Moderate | "Run `/financial-analysis:evaluate BTC` at {price} for position scoring" |
| Macro = Hostile | "Monitor macro-liquidity before committing capital" |
| On-chain data missing | "Provide MVRV/LTH from Glassnode dashboard for higher conviction" |
| Signal = No Bottom | "Re-run in 1-2 weeks or when Fear & Greed drops below 25" |
| Signal = No Bottom | "Run `/financial-analysis:btc-top` to check if BTC is instead near a top" |
