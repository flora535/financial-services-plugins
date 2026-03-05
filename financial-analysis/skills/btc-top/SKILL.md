---
name: btc-top
description: |
  Bitcoin cycle-top risk detector using 7 weighted on-chain + market indicators.
  Produces a 0-100 risk score mapped to Low/Moderate/Elevated/High/Extreme signal.

  Triggers: bitcoin top, is BTC topping, should I sell bitcoin,
  BTC overbought, crypto top signal, bitcoin cycle top, BTC exit timing,
  take profit bitcoin, is bitcoin overvalued
---

# BTC Top-Risk Analysis

7-indicator weighted Bitcoin cycle-top detector. Produces a 0–100 composite risk score
mapped to actionable signal levels. Unlike bottom detection (binary triggers), top signals
are gradient — this uses weighted scoring because tops are gradual, not sharp events.
Post-ETF dynamics shift which indicators work: thresholds are ~25% lower than historical
peaks to account for structural demand changes.

## Data Source Hierarchy

Same priority as btc-bottom and evaluate:
1. **MCP Servers** (Twelve Data, Massive API, FRED)
2. **User-provided data** (on-chain metrics: MVRV, NUPL, LTH supply, ETF flows, funding rate)
3. **Web search** (fallback for on-chain only — flag as Tier 3)

## Step 1: Collect Inputs

**Optional** (ask, don't block):
- Current BTC price (if not provided, fetch via MCP in Step 3A)
- MVRV ratio (from Glassnode, CryptoQuant, etc.)
- NUPL value
- LTH supply % (and direction: rising/falling)
- Recent ETF net flow data (weekly)
- Funding rate (8h average)

If on-chain metrics not provided, attempt web search in Steps 3D–3F. If still unavailable,
mark as `data unavailable` and apply missing-data conviction caps.

## Step 2: Timeliness Gate

Before analysis, verify data freshness. Check timestamps as each source returns.

| Data Type | Stale If Older Than | Action |
|-----------|-------------------|--------|
| Quote / price | 1 hour (crypto trades 24/7) | Re-query; if still stale, warn + cap conviction at Medium |
| RSI / MACD (weekly) | 1 day | Re-query; if stale, skip technicals |
| Fear & Greed | 1 day | Warn if stale |
| On-chain (MVRV, NUPL, LTH) | 7 days | Acceptable — on-chain moves slowly |
| ETF flows | 3 days | Re-query; if stale, warn |
| Funding rate | 1 day | Re-query; if stale, warn |
| FRED macro series | 7 days | Acceptable — macro moves slowly |

If **2+ data sources** stale after re-query → cap conviction at **Low** regardless of score.

## Step 3: Fetch Data

Target ~7-9 API calls, parallelizable. Run all sub-steps concurrently.

### 3A: Price & Volume — Massive API

Use `search_endpoints` → `call_api`:
- BTC/USD quote: price, 24h change %, volume, market cap
- 52-week high/low
- 30-day average volume

### 3B: Technicals — Twelve Data

Use Twelve Data MCP (preferred — 800 calls/day):
- Weekly RSI (14-period) for BTC/USD
- MACD on weekly timeframe
- Price vs 50-day and 200-day moving average
- **Also fetch RSI from 4 weeks ago** for divergence detection

If Twelve Data unavailable, fall back to Alpha Vantage. If neither available, skip
technicals — score indicator #1 as unavailable.

### 3C: Fear & Greed — Alternative.me

Direct HTTP fetch (no API key needed):
```
GET https://api.alternative.me/fng/
```

Parse JSON response → extract `value` (0-100) and `value_classification`.

Also fetch `?limit=14` to check if Fear & Greed has been >80 for 2+ weeks (sustained euphoria).

### 3D: On-chain Metrics — User Input or Web Search

For each metric not provided by user, attempt web search:
- **MVRV ratio**: search `"Bitcoin MVRV ratio" site:glassnode.com OR site:cryptoquant.com OR site:lookintobitcoin.com`
- **NUPL**: search `"Bitcoin NUPL" site:glassnode.com OR site:cryptoquant.com OR site:lookintobitcoin.com`
- **LTH Supply ratio**: search `"Bitcoin long term holder supply" site:glassnode.com OR site:cryptoquant.com`
  - Need both current % and direction (declining = distribution signal)

For each metric:
- If found via web search: use value, flag source as **Tier 3 (web search)** in output
- If not found: mark `data unavailable`, exclude from scoring denominator

### 3E: ETF Flows — User Input or Web Search

Search for recent Bitcoin ETF flow data:
- Search `"Bitcoin ETF net flow" site:sosovalue.com OR site:farside.co.uk`
- Need: last 2 weeks of daily net flow data
- Classify: net inflows / declining inflows / net outflows

### 3F: Funding Rate — Web Search

Search for perpetual futures funding rate:
- Search `"Bitcoin perpetual funding rate" site:coinglass.com`
- Need: current 8-hour average funding rate
- Also compute annualized rate for context

### 3G: Macro Context — FRED

Reuse evaluate's macro framework. Use `fred_get_series` for each (3 calls, parallelizable):

| Series ID | What | Why |
|-----------|------|-----|
| `DGS10` | 10-year Treasury yield | Risk-free rate / opportunity cost |
| `T10Y2Y` | 10Y-2Y Treasury spread | Yield curve inversion = recession signal |
| `BAMLH0A0HYM2` | ICE BofA High Yield spread | Credit stress — widens before risk-off |

Derive macro backdrop:

| Condition | Backdrop |
|-----------|----------|
| 10Y falling + spread positive + HY spread narrowing | 🟢 Supportive |
| Mixed signals or stable readings | 🟡 Neutral |
| 10Y rising sharply OR spread inverted OR HY spread >500bp | 🔴 Hostile |

## Step 4: Score 7 Indicators (Weighted, 0–10 each)

Each indicator scores 0–10 on a gradient scale. Unlike btc-bottom (binary triggers),
top signals are continuous — a stock can be "somewhat overbought" (score 5) or
"extremely overbought" (score 10).

| # | Indicator | Weight | 0 (Safe) | 5 (Caution) | 10 (Danger) | Source |
|---|-----------|--------|----------|-------------|-------------|--------|
| 1 | Weekly RSI | 20% | < 65 | 70–80 | > 80 + bearish divergence | Twelve Data |
| 2 | MVRV Ratio | 20% | < 1.5 | 1.5–2.5 | > 2.5 | User / web search |
| 3 | NUPL | 10% | < 0.4 | 0.4–0.6 | > 0.6 | User / web search |
| 4 | Fear & Greed | 10% | < 60 | 60–80 | > 80 sustained 2+ wks | Alternative.me |
| 5 | LTH Distribution | 15% | Supply rising | Flat | Declining >3% from peak, 4+ wks | User / web search |
| 6 | ETF Net Flows | 15% | Net inflows | Declining inflows | Net outflows 2+ wks | User / web search |
| 7 | Funding Rate | 10% | < 0.02%/8h | 0.02–0.05% | > 0.05% sustained | Web search |

### Interpolation

Score linearly within ranges. Examples:
- RSI 72 → score ~3 (between 65=0 and 80=5, closer to 5)
- MVRV 2.0 → score ~5 (midpoint of 1.5–2.5 range)
- Funding rate 0.035% → score ~5 (midpoint of 0.02–0.05 range)

### RSI Divergence Bonus

If bearish divergence detected (price makes higher high + RSI makes lower high vs 4 weeks ago),
add +3 to RSI score (cap at 10). Divergence is the strongest single top signal historically.

### Composite Score Calculation

**Composite score** = Σ(indicator_score × weight) × 10

Range: 0–100.

**Unavailable indicators**: redistribute weight proportionally among available ones.
Example: if NUPL (10%) unavailable, remaining 90% of weight scales to 100%:
each remaining indicator's effective weight = original_weight / 0.90.

## Step 5: Generate Signal

| Score | Signal | Action |
|-------|--------|--------|
| 0–25 | **Low Risk** | Hold / accumulate |
| 26–50 | **Moderate Risk** | Hold, reduce leverage, monitor |
| 51–70 | **Elevated Risk** | Begin de-risking (take 20–40% profit) |
| 71–85 | **High Risk** | Aggressive profit-taking |
| 86–100 | **Extreme Risk** | Max de-risk |

### Conviction Caps

| Unavailable Indicators | Max Conviction |
|----------------------|---------------|
| 0 | High |
| 1 | High |
| 2 | Medium |
| 3+ | Low |

Also: available indicators < 4 → max signal = **Moderate Risk** (prevent false positives from sparse data).

Final conviction = min(signal-based, staleness cap, missing-data cap).

### Override Rules

- Macro backdrop 🟢 Supportive → reduce score by 5 (euphoria needs hostile macro to crash)
- Macro backdrop 🔴 Hostile → add 5 to score (tightening accelerates tops)
- RSI bearish divergence present → minimum signal = **Moderate Risk** (divergence alone is meaningful)

## Step 5B: De-Risking Schedule

| Signal | Suggested Action | Strategy |
|--------|-----------------|----------|
| Low Risk | 0% sell | Hold / add |
| Moderate Risk | 0–10% sell | Tighten stops |
| Elevated Risk | 20–40% sell | DCA out: 4 weekly tranches |
| High Risk | 40–60% sell | Accelerate selling |
| Extreme Risk | 60–80% sell | Keep 20% "moon bag" only |

## Step 5C: Pre-Mortem (Inverted — Bull Case)

After scoring, force one falsification exercise:

> "If BTC rallies another 50% from here despite these warning signs, the most likely cause is: ___"

Derive from strongest bullish counter-signal (e.g. ETF still buying, macro supportive).
This is mandatory — never skip it.

## Step 6: Output

Print to terminal.

```
================================================================
  BTC TOP-RISK ANALYSIS — {YYYY-MM-DD HH:MM UTC}
================================================================

RISK SCORE: {0-100}
SIGNAL: {LOW RISK / MODERATE RISK / ELEVATED RISK / HIGH RISK / EXTREME RISK}
Conviction: {Low/Med/High}
{if capped: "(capped from {original} — {reason})"}

----------------------------------------------------------------
  DATA FRESHNESS
----------------------------------------------------------------
  Price (Massive):    {timestamp}  {✅/⚠️}
  Technicals (12D):   {timestamp}  {✅/⚠️/⛔}
  Fear & Greed:       {timestamp}  {✅/⚠️}
  MVRV:               {timestamp}  {✅/⚠️/⛔ unavailable}
  NUPL:               {timestamp}  {✅/⚠️/⛔ unavailable}
  LTH Supply:         {timestamp}  {✅/⚠️/⛔ unavailable}
  ETF Flows:          {timestamp}  {✅/⚠️/⛔ unavailable}
  Funding Rate:       {timestamp}  {✅/⚠️/⛔ unavailable}
  Macro (FRED):       {date}       {✅}

----------------------------------------------------------------
  INDICATOR DASHBOARD
----------------------------------------------------------------
  #  Indicator        Value     Score/10  Wt    Source          Note
  1  Weekly RSI       {val}     {s}/10   20%   Twelve Data     {divergence? Y/N}
  2  MVRV Ratio       {val}     {s}/10   20%   {source}        {zone}
  3  NUPL             {val}     {s}/10   10%   {source}        {zone name}
  4  Fear & Greed     {val}     {s}/10   10%   Alternative.me  {classification}
  5  LTH Distribution {dir}     {s}/10   15%   {source}        {supply change %}
  6  ETF Net Flows    ${flow}   {s}/10   15%   {source}        {inflow/outflow}
  7  Funding Rate     {rate}%   {s}/10   10%   {source}        {annualized}
                                ----
  Weighted Score: {X}/100

----------------------------------------------------------------
  BTC PRICE CONTEXT
----------------------------------------------------------------
  Price:         ${price}  (24h: {change}%)
  Market Cap:    ${mcap}
  52wk Range:    ${low} — ${high}  (current = {pct}% of range)
  200-DMA:       ${dma}  (price {above/below} by {pct}%)
  ATH:           ${ath}  (current = {pct}% of ATH)

----------------------------------------------------------------
  MACRO BACKDROP
----------------------------------------------------------------
  10Y Treasury:  {rate}%
  Yield Curve:   {spread}  {normal/flat/inverted}
  HY Spread:     {spread}bp  {tight/normal/wide}
  Backdrop:      {🟢 Supportive / 🟡 Neutral / 🔴 Hostile}
  Score adjustment: {+5 / 0 / -5}

----------------------------------------------------------------
  REASONING
----------------------------------------------------------------
  {2-4 sentences: why this risk level, which indicators drove it,
   key divergences or confluence, macro impact on timing}

----------------------------------------------------------------
  PRE-MORTEM (BULL CASE)
----------------------------------------------------------------
  If BTC rallies 50%+ despite warnings, the most likely cause is:
  {one sentence from strongest counter-signal}

----------------------------------------------------------------
  DE-RISKING SCHEDULE
----------------------------------------------------------------
  Signal:     {signal}
  Suggested:  Sell {X-Y}% of BTC position
  Strategy:   {DCA out schedule or hold}
  Keep:       {remaining}% as core / "moon bag"

----------------------------------------------------------------
  HISTORICAL PARALLEL
----------------------------------------------------------------
  Current score closest to: {date} ({score}/100)
  BTC then: ${price} → ${trough} ({pct}% drawdown over {months} months)

----------------------------------------------------------------
  NEXT STEPS
----------------------------------------------------------------
  {Contextual — see Next Steps Logic below}

----------------------------------------------------------------
  LIMITATIONS
----------------------------------------------------------------
  - {Missing on-chain data flags}
  - On-chain metrics sourced via web search (Tier 3) — verify independently
  - Post-ETF era: historical top patterns may not repeat — thresholds adjusted down ~25%
  - Model based on 4 historical cycles — sample size is small
  - Not financial advice — personal research aid only
================================================================
```

### Next Steps Logic

Show only relevant suggestions:

| Condition | Suggest |
|-----------|---------|
| RSI bearish divergence | "Watch for confirmation: price lower high on daily = distribution" |
| ETF data missing | "Check sosovalue.com/btc for latest ETF flow data" |
| Score < 26 (Low Risk) | "Re-run in 2-4 weeks or when Fear & Greed exceeds 75" |
| Score 26-50 (Moderate) | "Run `/financial-analysis:btc-bottom` to cross-check — conflicting signals possible in ranges" |
| Macro = 🔴 Hostile | "Macro tightening accelerates tops — consider faster de-risk" |
| Score > 70 (High/Extreme) | "Consider `/wealth-management:rebalance` to check overall portfolio crypto exposure" |
