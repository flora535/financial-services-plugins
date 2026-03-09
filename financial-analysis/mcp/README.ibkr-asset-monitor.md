# IBKR Asset Monitor MCP (v1)

Read-only MCP server backed by `ib_async` for portfolio monitoring and broker-state snapshot fallback.

## Runtime wiring

MCP wiring lives in `financial-analysis/.mcp.json`.

`ibkr-asset-monitor` runs:
- `uv run --with mcp --with ib_async python financial-analysis/mcp/ibkr_asset_monitor_server.py`

Environment variables passed through:
- `IBKR_HOST`
- `IBKR_PORT`
- `IBKR_CLIENT_ID`
- `IBKR_TIMEOUT_SECONDS`
- `IBKR_READ_ONLY`
- `ASSET_MONITOR_OFFLINE_PATH`

## Current-state flow before broker-state consolidation

Previous split behavior was:
- offline JSON at `financial-analysis/data/offline-assets.json`
- loaded only by `_load_offline_assets()`
- merged only into `get_normalized_portfolio()`
- open orders available only from live `get_open_orders()`
- recent trades available only from live `get_recent_trades()`
- per-order detail available only from live `get_order_status()`

Mismatch:
- intended use: one offline fallback snapshot skills can rely on when TWS/Gateway is unavailable
- previous implementation: asset-only offline merge, no unified broker-state payload
- no in-repo consumer currently stitches positions + orders + trades into one canonical state

## Tools

1. `get_positions(account=None)`
   - Pull current IBKR holdings (what you own).
2. `get_account_summary(account=None)`
   - Pull raw account summary tags.
3. `get_quotes(contracts)`
   - Pull snapshot quotes for provided contracts.
4. `get_fx_rates(base_currency="USD", quote_currencies=None)`
   - Pull FX conversion rates to base currency.
5. `get_normalized_portfolio(base_currency="USD", account=None, include_offline_assets=True, offline_assets_path=None)`
   - Return normalized positions, optionally augmented by offline snapshot positions.
6. `get_open_orders(account=None)`
   - Return currently open orders.
7. `get_recent_trades(limit=50, account=None)`
   - Return recent fills/executions from the current session.
8. `get_order_status(order_id=None, perm_id=None)`
   - Return detailed status, fills, and log for one order.
9. `get_broker_state(base_currency="USD", account=None, recent_trades_limit=50, offline_snapshot_path=None)`
   - Return one canonical broker-state payload.
   - On live success, also writes the fallback snapshot to `ASSET_MONITOR_OFFLINE_PATH`.
   - On live failure, reads the fallback snapshot from disk.

## Canonical broker-state schema

One envelope is used for:
- live consolidated MCP output from `get_broker_state`
- offline fallback snapshot stored on disk

Top-level shape:

```json
{
  "as_of_utc": "2026-03-09T07:00:00+00:00",
  "snapshot_source": "live_ibkr",
  "broker": "ibkr",
  "base_currency": "USD",
  "accounts": [],
  "positions": [],
  "orders_open": [],
  "trades_recent": [],
  "fx_rates": {},
  "metadata": {}
}
```

### Field rules

- `snapshot_source`: `live_ibkr` or `offline_snapshot`
- `broker`: fixed `ibkr`
- `positions`: canonical normalized position rows
- `orders_open`: separate from positions; do not fold pending exposure into holdings
- `trades_recent`: recent executions with order linkage
- `fx_rates`: currency -> base conversion map for the snapshot base currency
- `metadata`: counts, total market value, filters, snapshot path, live/offline state

## Account summary shape

Each account entry contains both normalized fields and raw IB tags:

```json
{
  "account": "U1234567",
  "summary_normalized": {
    "cash": {"tag": "TotalCashValue", "value": 120000.0, "currency": "USD"},
    "net_liquidation": {"tag": "NetLiquidation", "value": 550000.0, "currency": "USD"},
    "buying_power": {"tag": "BuyingPower", "value": 300000.0, "currency": "USD"}
  },
  "summary_raw": {
    "TotalCashValue": {"value": "120000", "currency": "USD"},
    "NetLiquidation": {"value": "550000", "currency": "USD"}
  }
}
```

Normalized v1 fields include:
- `cash`
- `net_liquidation`
- `buying_power`
- `available_funds`
- `excess_liquidity`
- `initial_margin_requirement`
- `maintenance_margin_requirement`
- `gross_position_value`
- `equity_with_loan_value`
- `lookahead_available_funds`
- `lookahead_excess_liquidity`

## Position schema

Canonical position base is the normalized row from `get_normalized_portfolio()`, extended to always include full `contract`.

```json
{
  "source": "live_ibkr",
  "account": "U1234567",
  "contract": {
    "symbol": "AAPL",
    "sec_type": "STK",
    "exchange": "SMART",
    "primary_exchange": "NASDAQ",
    "currency": "USD",
    "con_id": 265598,
    "local_symbol": "AAPL",
    "trading_class": "NMS",
    "ticker_normalized": "AAPL.NASDAQ"
  },
  "ticker_normalized": "AAPL.NASDAQ",
  "currency": "USD",
  "quantity": 100.0,
  "price": 210.5,
  "average_cost": 180.0,
  "market_value": 21050.0,
  "unrealized_pnl": 3050.0,
  "realized_pnl": 0.0,
  "fx_to_base": 1.0,
  "market_value_base": 21050.0,
  "portfolio_weight": 0.0383
}
```

## Open order schema

Identity rule:
- prefer `perm_id`
- fall back to `order_id` only when `perm_id` is unavailable

```json
{
  "account": "U1234567",
  "order_id": 123,
  "perm_id": 987654321,
  "client_id": 101,
  "action": "BUY",
  "order_type": "LMT",
  "total_quantity": 25.0,
  "limit_price": 195.0,
  "aux_price": null,
  "tif": "DAY",
  "outside_rth": false,
  "status": "Submitted",
  "filled": 0.0,
  "remaining": 25.0,
  "avg_fill_price": null,
  "last_fill_price": null,
  "why_held": null,
  "mkt_cap_price": null,
  "contract": {
    "symbol": "AAPL",
    "sec_type": "STK",
    "exchange": "SMART",
    "primary_exchange": "NASDAQ",
    "currency": "USD",
    "con_id": 265598,
    "local_symbol": "AAPL",
    "trading_class": "NMS",
    "ticker_normalized": "AAPL.NASDAQ"
  }
}
```

## Recent trade schema

Recent trades preserve execution linkage:

```json
{
  "account": "U1234567",
  "exec_id": "0000e0f5.65ee5abc.01.01",
  "order_id": 123,
  "perm_id": 987654321,
  "side": "BOT",
  "shares": 10.0,
  "price": 194.5,
  "time": "2026-03-09 09:42:15",
  "commission": 1.0,
  "commission_currency": "USD",
  "realized_pnl": null,
  "contract": {
    "symbol": "AAPL",
    "sec_type": "STK",
    "exchange": "SMART",
    "primary_exchange": "NASDAQ",
    "currency": "USD",
    "con_id": 265598,
    "local_symbol": "AAPL",
    "trading_class": "NMS",
    "ticker_normalized": "AAPL.NASDAQ"
  }
}
```

## Offline snapshot semantics

Previous offline asset semantics are superseded.

Old meaning:
- asset-only manual position list
- used only inside `get_normalized_portfolio`

New meaning:
- full broker-state fallback snapshot
- same schema as `get_broker_state`
- reused from the same `ASSET_MONITOR_OFFLINE_PATH`
- readable by downstream tools/skills when live IBKR is unavailable

## Snapshot lifecycle

### When snapshot is written

`get_broker_state()` writes the snapshot when live IBKR succeeds.

### What it contains

- account summary context
- normalized positions
- open orders
- recent trades
- FX rates
- metadata including counts and total market value

### How fallback works

If live IBKR connectivity fails:
- `get_broker_state()` reads the on-disk snapshot
- returns the same top-level schema
- flips `snapshot_source` to `offline_snapshot`
- annotates `metadata.live_available = false`
- includes the live error string in `metadata.live_error`

## Live example

```json
{
  "as_of_utc": "2026-03-09T07:00:00+00:00",
  "snapshot_source": "live_ibkr",
  "broker": "ibkr",
  "base_currency": "USD",
  "accounts": [{"account": "U1234567", "summary_normalized": {}, "summary_raw": {}}],
  "positions": [{"account": "U1234567", "ticker_normalized": "AAPL.NASDAQ", "contract": {}}],
  "orders_open": [{"perm_id": 987654321, "contract": {}}],
  "trades_recent": [{"exec_id": "0000e0f5.65ee5abc.01.01", "perm_id": 987654321, "contract": {}}],
  "fx_rates": {"USD": 1.0},
  "metadata": {
    "account_filter": null,
    "recent_trades_limit": 50,
    "position_count": 1,
    "open_order_count": 1,
    "recent_trade_count": 1,
    "total_market_value_base": 21050.0,
    "offline_snapshot_path": "financial-analysis/data/offline-assets.json",
    "live_available": true
  }
}
```

## Offline fallback example

```json
{
  "as_of_utc": "2026-03-09T07:00:00+00:00",
  "snapshot_source": "offline_snapshot",
  "broker": "ibkr",
  "base_currency": "USD",
  "accounts": [{"account": "offline-manual", "summary_normalized": {}, "summary_raw": {}}],
  "positions": [{"account": "offline-manual", "ticker_normalized": "PRIVATE_FUND_A.OFFLINE", "contract": {}}],
  "orders_open": [{"perm_id": 5550001, "contract": {}}],
  "trades_recent": [{"exec_id": "manual-fill-001", "perm_id": 5550001, "contract": {}}],
  "fx_rates": {"USD": 1.0, "CNY": 0.138},
  "metadata": {
    "offline_snapshot_path": "financial-analysis/data/offline-assets.json",
    "live_available": false,
    "live_error": "ConnectionRefusedError(...)"
  }
}
```

## Consumer guidance

Later skill-side consumers should rely on `get_broker_state()` when they need one payload that answers:
- what do I own now?
- what orders are already pending?
- what is pro-forma exposure if orders fill?
- what losses / drift / tax actions exist?

Immediate skill rewrites are intentionally deferred.
