# IBKR Asset Monitor MCP (v1)

Read-only MCP server backed by `ib_async` for portfolio monitoring.

## Tools

1. `get_positions(account=None)`
   - Pull current IBKR holdings (what you own).
2. `get_account_summary(account=None)`
   - Pull account-level values (cash, net liq, buying power, margin tags).
3. `get_quotes(contracts)`
   - Pull snapshot quotes for provided contracts.
4. `get_fx_rates(base_currency="USD", quote_currencies=None)`
   - Pull FX conversion rates to base currency.
5. `get_normalized_portfolio(base_currency="USD", account=None, include_offline_assets=True, offline_assets_path=None)`
   - Return unified portfolio with ticker normalization, currency normalization, and optional offline assets.
6. `get_open_orders(account=None)`
   - Return currently open orders.
7. `get_recent_trades(limit=50, account=None)`
   - Return recent fills/executions from the current session.
8. `get_order_status(order_id=None, perm_id=None)`
   - Return detailed status, fills, and log for one order (lookup by order ID or perm ID).

## Order ID vs Perm ID (use this rule)

- Prefer `perm_id` for tracking and lookups across sessions/clients.
- Use `order_id` only for same-session, client-local workflows.
- Some open orders can show `order_id=0` in cross-client views; `perm_id` is still reliable.
- For AI tool-calling: use `perm_id` first, fall back to `order_id` only when `perm_id` is unavailable.

## Runtime requirements

- TWS or IB Gateway running locally and API enabled.
- `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID` set in environment (see `.env.example`).

## Offline assets

- Copy `financial-analysis/data/offline-assets.example.json` to `financial-analysis/data/offline-assets.json`.
- Add manual positions (private assets, bank cash, other off-broker holdings).
