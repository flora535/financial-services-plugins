---
name: portfolio-loop
description: Run a portfolio-wide Research -> Plan -> Execute -> Reflect -> Adjust review using the current IBKR broker-state snapshot. Produces a keep/add/trim/exit/rebalance/TLH/watch view, escalates only flagged holdings into deeper single-name analysis, and ends with explicit review triggers. Triggers on "portfolio loop", "review my portfolio", "portfolio operating review", "full portfolio review", "portfolio thesis review", or "what should I do with my portfolio".
---

# Portfolio Loop

Use this skill as the **phase-1 portfolio operating loop** for the repo.

It belongs in `wealth-management` because it owns the whole-portfolio decision flow. It must **reuse** `financial-analysis` for deep research rather than duplicating single-name analysis.

## Core Rules

1. **Start from broker state, not manual ticker entry.**
   - Use the IBKR asset monitor MCP `get_broker_state` flow as the source of truth.
   - Prefer full portfolio review unless the user explicitly asks for one account.
   - If live IBKR is unavailable, the broker-state tool may fall back to the offline snapshot. Accept that and state it.

2. **Stay portfolio-first.**
   - First review the whole portfolio.
   - Only route flagged holdings into deeper single-name work.
   - Do not turn this into a ticker-by-ticker deep-dive by default.

3. **Execute is checklist-only in phase 1.**
   - No broker automation.
   - No order placement.
   - No journaling backend.

4. **Reuse existing skills.**
   - `financial-analysis:evaluate` for quick position checks.
   - `financial-analysis:comps` when peer context is needed.
   - `financial-analysis:dcf` when intrinsic value matters enough to justify a fuller valuation.
   - `wealth-management:rebalance` for allocation drift actions.
   - `wealth-management:tlh` for harvest candidates.

## Required Workflow

## Step 1: Pull Portfolio State

Use broker state first:
- `get_broker_state(base_currency="USD", account=<if provided>)`

Capture at minimum:
- as-of timestamp
- snapshot source (`live_ibkr` or `offline_snapshot`)
- accounts
- positions
- open orders
- recent trades
- total market value in base currency
- portfolio weights

If broker state is empty or missing positions, stop and say the loop cannot run meaningfully without holdings.

## Step 2: Research — Portfolio Scan First

Create a fast portfolio scan table.

For each holding, summarize:
- ticker / normalized ticker
- account
- market value
- portfolio weight
- unrealized P&L if available
- open-order overlap if relevant
- initial portfolio flag

Use these **portfolio flags**:
- `KEEP` — position looks normal, no immediate action needed
- `ADD CANDIDATE` — strong name or underweight conviction candidate
- `TRIM` — oversized, thesis stretched, or risk concentration too high
- `EXIT/WATCH` — thesis weak, stale, or needs urgent review
- `REBALANCE` — drift / sizing issue more than business issue
- `TLH` — unrealized loss candidate in taxable context
- `DEEP DIVE` — uncertain or important enough to escalate

### Flagging Heuristics

Use simple phase-1 heuristics. Do not over-model.

Flag for **TRIM / REBALANCE** when one or more apply:
- top position concentration looks too high for the portfolio
- multiple positions cluster in the same theme / sector
- open orders are already trying to add to an oversized name
- weight is clearly out of line with the rest of the portfolio

Flag for **TLH** when:
- unrealized loss is present
- position appears to be in a taxable account or taxable context is likely
- harvesting would not obviously break portfolio exposure goals

Flag for **DEEP DIVE** when:
- it is a top position and thesis confidence is unclear
- trim vs hold is not obvious
- valuation appears to be the real decision driver
- a loser may be either a broken thesis or an averaging-down candidate

## Step 3: Route Only Flagged Names Deeper

Do not run deep analysis for the whole book.

Use this routing logic:

| Situation | Next skill |
|---|---|
| Need quick buy/hold/sell check | `financial-analysis:evaluate` |
| Need better peer context | `financial-analysis:comps` |
| Need intrinsic value / valuation floor | `financial-analysis:dcf` |
| Drift is the main issue | `wealth-management:rebalance` |
| Tax loss matters most | `wealth-management:tlh` |

### Escalation Gate

- Default to `evaluate` first for flagged holdings.
- Escalate to `comps` if peer-relative valuation or quality is the missing piece.
- Escalate to `dcf` only when valuation conviction is important enough to change sizing.
- Keep the portfolio loop output moving even if you do **not** run deeper skills immediately.

## Step 4: Plan — Produce Portfolio Priorities

Translate the scan into a portfolio-level action list.

Required categories:
- top positions to keep
- top positions to trim / exit / watch
- rebalance candidates
- TLH candidates
- cash / buying-power implications if visible from broker state
- which flagged names need deeper follow-up

Allowed action labels:
- keep
- add
- trim
- exit
- rebalance
- harvest
- watch

Keep this section prioritized and short.

## Step 5: Execute — Checklist Only

Create a practical execution checklist, but **do not** automate anything.

Checklist can include:
- confirm which positions are taxable before harvesting
- review open orders before adding or trimming
- run deeper analysis on flagged holdings before resizing
- stage rebalance trades in tax-advantaged accounts first when possible
- confirm replacement ideas before TLH
- note any dependencies such as waiting for earnings or macro events

## Step 6: Reflect — State the Current Thesis

Write a short portfolio reflection section with:
- current portfolio thesis / current stance
- what changed since the portfolio's current setup appears to have been built
- what parts of the thesis look strongest
- what could be broken or under-reviewed

This is the bridge between current holdings and future action.

## Step 7: Adjust — Define Review Triggers

Always end with explicit triggers.

### Portfolio-level triggers
Examples:
- concentration exceeds comfort band
- cash rises above target idle level
- sector/theme exposure becomes too lopsided
- large macro or rate regime change

### Position-level triggers
Examples:
- earnings miss / guidance cut
- valuation stretches far above prior comfort zone
- thesis catalyst fails to show up
- drawdown crosses a review threshold
- tax-loss opportunity reaches material size

Add:
- next review date or cadence
- what event would force an earlier review

## Output Format

Use these exact top-level sections in order:

1. **Portfolio Thesis / Current Stance**
2. **Research**
3. **Plan**
4. **Execute Checklist**
5. **Reflect**
6. **Adjust**
7. **Next Skills To Run**

### Required Content Inside Output

Your answer must include all of the following:
- snapshot source and as-of date
- total portfolio market value if available
- top positions to keep
- top positions to trim / exit / watch
- rebalance candidates
- TLH candidates
- what would make the current portfolio view wrong
- review date / trigger
- which existing skill to run next for each flagged name if needed

## Example Skeleton

```md
# Portfolio Thesis / Current Stance
- Current stance: ...
- Snapshot: live_ibkr | 2026-03-09T...
- Total portfolio value: ...

# Research
| Holding | Weight | P&L | Flag | Why |
|---|---:|---:|---|---|

# Plan
## Keep
- ...

## Trim / Exit / Watch
- ...

## Rebalance Candidates
- ...

## TLH Candidates
- ...

# Execute Checklist
- [ ] ...

# Reflect
- Thesis that still holds: ...
- What changed: ...
- What looks broken or under-reviewed: ...
- What would make this view wrong: ...

# Adjust
- Next review date: ...
- Portfolio triggers: ...
- Position triggers: ...

# Next Skills To Run
- `financial-analysis:evaluate XYZ at <cost basis>` — reason
- `wealth-management:rebalance` — reason
- `wealth-management:tlh` — reason
```

## Tone

- Be decisive but practical.
- Keep the output portfolio-wide.
- Do not pretend to know missing tax facts — call them out.
- If cost basis, account tax type, or thesis history is missing, say what assumption you made.
- Prefer clear prioritization over long commentary.

## Phase-1 Boundary

Do **not** add:
- a new plugin
- broker execution
- persistent journal storage
- dashboards
- backtests
- chapter notebook ports

This skill is only the first workflow layer that connects existing plugin capabilities into one portfolio operating loop.
