#!/usr/bin/env python3
"""IBKR asset monitor MCP server (read-only v1).

Tools:
- get_positions
- get_account_summary
- get_quotes
- get_fx_rates
- get_normalized_portfolio
- get_open_orders
- get_recent_trades
- get_order_status
- get_broker_state
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

try:
    from ib_async import IB, Contract, Forex, Stock  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise RuntimeError(
        "Missing dependencies. Install with: pip install mcp ib_async"
    ) from exc


mcp = FastMCP("IBKR Asset Monitor")
_IB: IB | None = None

# Reduce noisy/sensitive IB client logs in stdio MCP mode.
logging.getLogger("ib_async").setLevel(logging.WARNING)
logging.getLogger("ib_async.client").setLevel(logging.WARNING)
logging.getLogger("ib_async.wrapper").setLevel(logging.WARNING)


ACCOUNT_SUMMARY_NORMALIZED_TAGS = {
    "cash": "TotalCashValue",
    "net_liquidation": "NetLiquidation",
    "buying_power": "BuyingPower",
    "available_funds": "AvailableFunds",
    "excess_liquidity": "ExcessLiquidity",
    "initial_margin_requirement": "InitMarginReq",
    "maintenance_margin_requirement": "MaintMarginReq",
    "gross_position_value": "GrossPositionValue",
    "equity_with_loan_value": "EquityWithLoanValue",
    "lookahead_available_funds": "LookAheadAvailableFunds",
    "lookahead_excess_liquidity": "LookAheadExcessLiquidity",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _as_float(value: Any) -> float | None:
    if _is_finite(value):
        return float(value)
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None
    return None


def _normalize_ticker(symbol: str | None, exchange: str | None) -> str:
    sym = (symbol or "UNKNOWN").strip().upper()
    ex = (exchange or "UNKNOWN").strip().upper().replace(" ", "")
    return f"{sym}.{ex}"


def _get_env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _get_env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _offline_snapshot_path(path_override: str | None) -> Path:
    default_path = Path("financial-analysis/data/offline-assets.json")
    return Path(path_override or os.getenv("ASSET_MONITOR_OFFLINE_PATH", str(default_path)))


def _connect_ib() -> IB:
    global _IB

    if _IB and _IB.isConnected():
        return _IB

    host = os.getenv("IBKR_HOST", "127.0.0.1")
    port = _get_env_int("IBKR_PORT", 7497)
    client_id = _get_env_int("IBKR_CLIENT_ID", 101)
    timeout = _get_env_float("IBKR_TIMEOUT_SECONDS", 8.0)
    read_only = os.getenv("IBKR_READ_ONLY", "true").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    ib = IB()
    try:
        ib.connect(host=host, port=port, clientId=client_id, timeout=timeout, readonly=read_only)
    except TypeError:
        ib.connect(host=host, port=port, clientId=client_id, timeout=timeout)
    _IB = ib
    return ib


def _contract_from_spec(spec: dict[str, Any]) -> Contract:
    sec_type = str(spec.get("sec_type", "STK")).upper()

    if sec_type == "CASH":
        base = str(spec.get("base") or spec.get("symbol") or "").upper().strip()
        quote = str(spec.get("quote") or spec.get("currency") or "").upper().strip()
        if not base or not quote:
            raise ValueError("CASH contract requires base+quote (or symbol+currency)")
        return Forex(f"{base}{quote}")

    symbol = str(spec.get("symbol", "")).strip().upper()
    if not symbol:
        raise ValueError("Contract spec requires symbol")

    exchange = str(spec.get("exchange", "SMART")).strip().upper() or "SMART"
    currency = str(spec.get("currency", "USD")).strip().upper() or "USD"

    contract = Stock(symbol, exchange, currency)
    primary_exchange = spec.get("primary_exchange")
    if primary_exchange:
        contract.primaryExchange = str(primary_exchange).strip().upper()
    return contract


def _contract_payload(contract: Any) -> dict[str, Any]:
    exchange = getattr(contract, "primaryExchange", None) or getattr(contract, "exchange", None)
    return {
        "symbol": getattr(contract, "symbol", None),
        "sec_type": getattr(contract, "secType", None),
        "exchange": getattr(contract, "exchange", None),
        "primary_exchange": getattr(contract, "primaryExchange", None),
        "currency": getattr(contract, "currency", None),
        "con_id": getattr(contract, "conId", None),
        "local_symbol": getattr(contract, "localSymbol", None),
        "trading_class": getattr(contract, "tradingClass", None),
        "ticker_normalized": _normalize_ticker(getattr(contract, "symbol", None), exchange),
    }


def _ticker_price(ticker: Any) -> float | None:
    if hasattr(ticker, "marketPrice") and callable(ticker.marketPrice):
        market = _as_float(ticker.marketPrice())
        if market is not None:
            return market

    for field in ("last", "bid", "ask", "close"):
        value = _as_float(getattr(ticker, field, None))
        if value is not None:
            return value
    return None


def _load_offline_assets(path_override: str | None) -> tuple[dict[str, Any] | None, str | None]:
    path = _offline_snapshot_path(path_override)
    if not path.exists():
        return None, None

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Offline snapshot file must be a broker-state JSON object")
    return payload, str(path)


def _write_offline_snapshot(snapshot: dict[str, Any], path_override: str | None) -> str:
    path = _offline_snapshot_path(path_override)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return str(path)


def _fx_rates_to_base(ib: IB, currencies: set[str], base_currency: str) -> dict[str, float]:
    base = base_currency.upper()
    rates: dict[str, float] = {base: 1.0}

    needed = sorted(ccy for ccy in currencies if ccy and ccy.upper() != base)
    if not needed:
        return rates

    contracts = [Forex(f"{ccy.upper()}{base}") for ccy in needed]
    tickers = ib.reqTickers(*contracts)

    for ccy, ticker in zip(needed, tickers):
        px = _ticker_price(ticker)
        if px is not None and px > 0:
            rates[ccy.upper()] = px
            continue

        inverse = Forex(f"{base}{ccy.upper()}")
        inv_ticker = ib.reqTickers(inverse)[0]
        inv_px = _ticker_price(inv_ticker)
        if inv_px is not None and inv_px > 0:
            rates[ccy.upper()] = 1.0 / inv_px

    return rates


def _raw_account_summary(ib: IB, account: str | None) -> dict[str, dict[str, dict[str, str]]]:
    rows = ib.accountSummary(account) if account else ib.accountSummary()

    summary: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        acct = row.account
        if acct not in summary:
            summary[acct] = {}
        summary[acct][row.tag] = {
            "value": row.value,
            "currency": row.currency,
        }
    return summary


def _normalized_account_summary(raw_summary: dict[str, dict[str, str]]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for field, tag in ACCOUNT_SUMMARY_NORMALIZED_TAGS.items():
        raw = raw_summary.get(tag)
        normalized[field] = {
            "tag": tag,
            "value": _as_float(raw.get("value")) if raw else None,
            "currency": raw.get("currency") if raw else None,
        }
    return normalized


def _account_payloads(ib: IB, account: str | None) -> list[dict[str, Any]]:
    raw_summary = _raw_account_summary(ib, account)
    accounts: list[dict[str, Any]] = []

    for acct in sorted(raw_summary):
        raw = raw_summary[acct]
        accounts.append(
            {
                "account": acct,
                "summary_normalized": _normalized_account_summary(raw),
                "summary_raw": raw,
            }
        )

    return accounts


def _live_positions(ib: IB, account: str | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    portfolio_items = ib.portfolio(account) if account else ib.portfolio()

    for item in portfolio_items:
        contract = item.contract
        market_value = _as_float(getattr(item, "marketValue", None))
        if market_value is None:
            position = _as_float(getattr(item, "position", None)) or 0.0
            market_price = _as_float(getattr(item, "marketPrice", None)) or 0.0
            market_value = position * market_price

        contract_payload = _contract_payload(contract)
        rows.append(
            {
                "source": "live_ibkr",
                "account": getattr(item, "account", None),
                "contract": contract_payload,
                "ticker_normalized": contract_payload["ticker_normalized"],
                "currency": getattr(contract, "currency", None),
                "quantity": _as_float(getattr(item, "position", None)),
                "price": _as_float(getattr(item, "marketPrice", None)),
                "average_cost": _as_float(getattr(item, "averageCost", None)),
                "market_value": market_value,
                "unrealized_pnl": _as_float(getattr(item, "unrealizedPNL", None)),
                "realized_pnl": _as_float(getattr(item, "realizedPNL", None)),
            }
        )

    return rows


def _open_orders_payload(ib: IB, account: str | None) -> list[dict[str, Any]]:
    trades = list(ib.reqAllOpenOrders())

    rows: list[dict[str, Any]] = []
    for trade in trades:
        order = trade.order
        status = trade.orderStatus
        acct = getattr(order, "account", None)
        if account and acct != account:
            continue

        rows.append(
            {
                "account": acct,
                "order_id": getattr(order, "orderId", None),
                "perm_id": getattr(order, "permId", None),
                "client_id": getattr(order, "clientId", None),
                "action": getattr(order, "action", None),
                "order_type": getattr(order, "orderType", None),
                "total_quantity": _as_float(getattr(order, "totalQuantity", None)),
                "limit_price": _as_float(getattr(order, "lmtPrice", None)),
                "aux_price": _as_float(getattr(order, "auxPrice", None)),
                "tif": getattr(order, "tif", None),
                "outside_rth": getattr(order, "outsideRth", None),
                "status": getattr(status, "status", None),
                "filled": _as_float(getattr(status, "filled", None)),
                "remaining": _as_float(getattr(status, "remaining", None)),
                "avg_fill_price": _as_float(getattr(status, "avgFillPrice", None)),
                "last_fill_price": _as_float(getattr(status, "lastFillPrice", None)),
                "why_held": getattr(status, "whyHeld", None),
                "mkt_cap_price": _as_float(getattr(status, "mktCapPrice", None)),
                "contract": _contract_payload(trade.contract),
            }
        )

    rows.sort(key=lambda r: ((r.get("perm_id") or 0), (r.get("order_id") or 0)), reverse=True)
    return rows


def _recent_trades_payload(ib: IB, limit: int, account: str | None) -> list[dict[str, Any]]:
    if limit <= 0:
        raise ValueError("limit must be > 0")
    limit = min(limit, 500)

    fills = ib.fills()

    rows: list[dict[str, Any]] = []
    for fill in fills:
        execution = fill.execution
        contract = fill.contract
        commission = fill.commissionReport
        acct = getattr(execution, "acctNumber", None)
        if account and acct != account:
            continue

        rows.append(
            {
                "account": acct,
                "exec_id": getattr(execution, "execId", None),
                "order_id": getattr(execution, "orderId", None),
                "perm_id": getattr(execution, "permId", None),
                "side": getattr(execution, "side", None),
                "shares": _as_float(getattr(execution, "shares", None)),
                "price": _as_float(getattr(execution, "price", None)),
                "time": str(getattr(execution, "time", "")) or None,
                "commission": _as_float(getattr(commission, "commission", None)),
                "commission_currency": getattr(commission, "currency", None),
                "realized_pnl": _as_float(getattr(commission, "realizedPNL", None)),
                "contract": _contract_payload(contract),
            }
        )

    rows.sort(key=lambda r: r.get("time") or "", reverse=True)
    return rows[:limit]


def _snapshot_fx_rate(
    fx_rates: dict[str, float],
    from_currency: str | None,
    to_currency: str,
) -> float | None:
    source = (from_currency or to_currency).upper()
    target = to_currency.upper()
    if source == target:
        return 1.0

    source_to_snapshot = _as_float(fx_rates.get(source))
    target_to_snapshot = _as_float(fx_rates.get(target))
    if source_to_snapshot is None or target_to_snapshot is None or target_to_snapshot == 0:
        return None
    return source_to_snapshot / target_to_snapshot


def _finalize_position_rows(rows: list[dict[str, Any]], fx_rates: dict[str, float], base_currency: str) -> tuple[list[dict[str, Any]], float]:
    total_base_value = 0.0
    base = base_currency.upper()

    for row in rows:
        currency = str(row.get("currency") or base).upper()
        rate = _snapshot_fx_rate(fx_rates, currency, base)
        row["fx_to_base"] = rate

        market_value = _as_float(row.get("market_value"))
        if rate is None or market_value is None:
            row["market_value_base"] = None
            continue

        market_value_base = market_value * rate
        row["market_value_base"] = market_value_base
        total_base_value += market_value_base

    for row in rows:
        market_value_base = _as_float(row.get("market_value_base"))
        row["portfolio_weight"] = (
            market_value_base / total_base_value if (market_value_base is not None and total_base_value > 0) else None
        )

    rows.sort(key=lambda r: abs(_as_float(r.get("market_value_base")) or 0.0), reverse=True)
    return rows, total_base_value


def _build_live_broker_state(
    ib: IB,
    base_currency: str,
    account: str | None,
    recent_trades_limit: int,
) -> dict[str, Any]:
    base = base_currency.upper().strip()
    positions = _live_positions(ib, account)
    accounts = _account_payloads(ib, account)
    orders_open = _open_orders_payload(ib, account)
    trades_recent = _recent_trades_payload(ib, recent_trades_limit, account)

    currencies = {base}
    currencies.update(str(position.get("currency") or base).upper() for position in positions)
    for account_payload in accounts:
        for field in account_payload.get("summary_normalized", {}).values():
            currency = field.get("currency")
            if currency:
                currencies.add(str(currency).upper())

    fx_rates = _fx_rates_to_base(ib, currencies, base)
    positions, total_market_value_base = _finalize_position_rows(positions, fx_rates, base)

    return {
        "as_of_utc": _now_iso(),
        "snapshot_source": "live_ibkr",
        "broker": "ibkr",
        "base_currency": base,
        "accounts": accounts,
        "positions": positions,
        "orders_open": orders_open,
        "trades_recent": trades_recent,
        "fx_rates": fx_rates,
        "metadata": {
            "account_filter": account,
            "recent_trades_limit": recent_trades_limit,
            "position_count": len(positions),
            "open_order_count": len(orders_open),
            "recent_trade_count": len(trades_recent),
            "total_market_value_base": total_market_value_base,
        },
    }


def _filter_snapshot_for_account(snapshot: dict[str, Any], account: str | None) -> dict[str, Any]:
    if not account:
        return snapshot

    filtered = {
        **snapshot,
        "accounts": [row for row in snapshot.get("accounts", []) if row.get("account") == account],
        "positions": [row for row in snapshot.get("positions", []) if row.get("account") == account],
        "orders_open": [row for row in snapshot.get("orders_open", []) if row.get("account") == account],
        "trades_recent": [row for row in snapshot.get("trades_recent", []) if row.get("account") == account],
    }
    metadata = dict(snapshot.get("metadata", {}))
    metadata["account_filter"] = account
    filtered["metadata"] = metadata
    return filtered


def _rebase_snapshot(snapshot: dict[str, Any], base_currency: str) -> dict[str, Any]:
    target_base = base_currency.upper().strip()
    current_base = str(snapshot.get("base_currency") or "USD").upper()
    if target_base == current_base:
        return snapshot

    fx_rates = snapshot.get("fx_rates") or {}
    if target_base not in fx_rates:
        raise ValueError(
            f"Offline snapshot cannot be rebased to {target_base}; missing FX rate in snapshot payload"
        )

    rebased = {
        **snapshot,
        "base_currency": target_base,
        "accounts": json.loads(json.dumps(snapshot.get("accounts", []))),
        "positions": json.loads(json.dumps(snapshot.get("positions", []))),
        "orders_open": json.loads(json.dumps(snapshot.get("orders_open", []))),
        "trades_recent": json.loads(json.dumps(snapshot.get("trades_recent", []))),
    }

    rebased_fx_rates: dict[str, float] = {target_base: 1.0}
    for currency in fx_rates:
        rate = _snapshot_fx_rate(fx_rates, currency, target_base)
        if rate is not None:
            rebased_fx_rates[currency] = rate
    rebased["fx_rates"] = rebased_fx_rates

    positions, total_market_value_base = _finalize_position_rows(
        rebased.get("positions", []), rebased_fx_rates, target_base
    )
    rebased["positions"] = positions

    metadata = dict(rebased.get("metadata", {}))
    metadata["total_market_value_base"] = total_market_value_base
    rebased["metadata"] = metadata
    return rebased


def _offline_positions_from_snapshot(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    positions = snapshot.get("positions", [])
    if not isinstance(positions, list):
        raise ValueError("Offline snapshot positions must be a JSON array")
    return json.loads(json.dumps(positions))


@mcp.tool()
def get_positions(account: str | None = None) -> dict[str, Any]:
    """Return current IBKR positions (what you own) with normalized tickers."""
    ib = _connect_ib()
    records = ib.positions(account) if account else ib.positions()

    positions: list[dict[str, Any]] = []
    for rec in records:
        contract = rec.contract
        exchange = getattr(contract, "primaryExchange", None) or getattr(contract, "exchange", None)
        positions.append(
            {
                "account": rec.account,
                "symbol": contract.symbol,
                "sec_type": contract.secType,
                "exchange": contract.exchange,
                "primary_exchange": getattr(contract, "primaryExchange", None),
                "currency": contract.currency,
                "con_id": getattr(contract, "conId", None),
                "position": _as_float(rec.position),
                "average_cost": _as_float(rec.avgCost),
                "ticker_normalized": _normalize_ticker(contract.symbol, exchange),
            }
        )

    return {
        "as_of_utc": _now_iso(),
        "count": len(positions),
        "positions": positions,
    }


@mcp.tool()
def get_account_summary(account: str | None = None) -> dict[str, Any]:
    """Return account summary metrics (cash, net liquidation, buying power, margin tags)."""
    ib = _connect_ib()
    summary = _raw_account_summary(ib, account)

    return {
        "as_of_utc": _now_iso(),
        "accounts": summary,
    }


@mcp.tool()
def get_quotes(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    """Return snapshot quotes for provided contracts.

    Contract example:
    {"symbol":"AAPL","sec_type":"STK","exchange":"SMART","currency":"USD"}
    """
    if not contracts:
        raise ValueError("contracts is required and must be non-empty")

    ib = _connect_ib()
    ib_contracts = [_contract_from_spec(spec) for spec in contracts]
    ib.qualifyContracts(*ib_contracts)
    tickers = ib.reqTickers(*ib_contracts)

    rows: list[dict[str, Any]] = []
    for contract, ticker in zip(ib_contracts, tickers):
        exchange = getattr(contract, "primaryExchange", None) or getattr(contract, "exchange", None)
        rows.append(
            {
                "symbol": contract.symbol,
                "sec_type": contract.secType,
                "exchange": contract.exchange,
                "primary_exchange": getattr(contract, "primaryExchange", None),
                "currency": contract.currency,
                "con_id": getattr(contract, "conId", None),
                "bid": _as_float(getattr(ticker, "bid", None)),
                "ask": _as_float(getattr(ticker, "ask", None)),
                "last": _as_float(getattr(ticker, "last", None)),
                "close": _as_float(getattr(ticker, "close", None)),
                "market_price": _ticker_price(ticker),
                "ticker_normalized": _normalize_ticker(contract.symbol, exchange),
                "time": str(getattr(ticker, "time", "")) or None,
            }
        )

    return {
        "as_of_utc": _now_iso(),
        "count": len(rows),
        "quotes": rows,
    }


@mcp.tool()
def get_fx_rates(base_currency: str = "USD", quote_currencies: list[str] | None = None) -> dict[str, Any]:
    """Return FX conversion rates to base currency.

    Example: base_currency='USD', quote_currencies=['EUR','JPY'] returns EUR->USD and JPY->USD.
    """
    ib = _connect_ib()
    base = base_currency.upper().strip()

    if quote_currencies:
        currencies = {ccy.upper().strip() for ccy in quote_currencies if ccy and ccy.strip()}
    else:
        positions = ib.positions()
        currencies = {getattr(p.contract, "currency", "") for p in positions}

    rates = _fx_rates_to_base(ib, currencies, base)
    missing = sorted(ccy for ccy in currencies if ccy.upper() not in rates)

    return {
        "as_of_utc": _now_iso(),
        "base_currency": base,
        "rates": rates,
        "missing": missing,
    }


@mcp.tool()
def get_normalized_portfolio(
    base_currency: str = "USD",
    account: str | None = None,
    include_offline_assets: bool = True,
    offline_assets_path: str | None = None,
) -> dict[str, Any]:
    """Return unified portfolio with ticker/currency normalization and optional offline snapshot positions."""
    base = base_currency.upper().strip()
    rows: list[dict[str, Any]] = []
    used_offline_path: str | None = None

    try:
        ib = _connect_ib()
        rows.extend(_live_positions(ib, account))
        fx_rates = _fx_rates_to_base(
            ib,
            {str(row.get("currency") or base).upper() for row in rows} | {base},
            base,
        )
    except Exception:
        ib = None
        fx_rates = {base: 1.0}

    if include_offline_assets:
        offline_snapshot, used_offline_path = _load_offline_assets(offline_assets_path)
        if offline_snapshot:
            snapshot = _filter_snapshot_for_account(_rebase_snapshot(offline_snapshot, base), account)
            rows.extend(_offline_positions_from_snapshot(snapshot))
            for currency, rate in (snapshot.get("fx_rates") or {}).items():
                if _as_float(rate) is not None:
                    fx_rates[str(currency).upper()] = float(rate)

    rows, total_market_value_base = _finalize_position_rows(rows, fx_rates, base)

    return {
        "as_of_utc": _now_iso(),
        "base_currency": base,
        "fx_rates": fx_rates,
        "offline_assets_path": used_offline_path,
        "total_market_value_base": total_market_value_base,
        "positions": rows,
    }


@mcp.tool()
def get_open_orders(account: str | None = None) -> dict[str, Any]:
    """Return currently open IBKR orders (read-only).

    Each row includes both `order_id` and `perm_id`.
    Prefer `perm_id` for cross-session/cross-client tracking.
    """
    ib = _connect_ib()
    rows = _open_orders_payload(ib, account)
    return {
        "as_of_utc": _now_iso(),
        "count": len(rows),
        "open_orders": rows,
    }


@mcp.tool()
def get_recent_trades(limit: int = 50, account: str | None = None) -> dict[str, Any]:
    """Return recent fills/executions known by the current IBKR session.

    Each execution includes both `order_id` and `perm_id`.
    Prefer `perm_id` for durable reconciliation.
    """
    ib = _connect_ib()
    rows = _recent_trades_payload(ib, limit, account)
    return {
        "as_of_utc": _now_iso(),
        "count": len(rows),
        "total_available": len(ib.fills()),
        "recent_trades": rows,
    }


@mcp.tool()
def get_order_status(order_id: int | None = None, perm_id: int | None = None) -> dict[str, Any]:
    """Return detailed status for one order by `order_id` or `perm_id`.

    Prefer `perm_id` when available.
    """
    if order_id is None and perm_id is None:
        raise ValueError("Provide order_id or perm_id")

    ib = _connect_ib()

    if perm_id is not None:
        # Prefetch broader open-order universe for cross-client visibility.
        ib.reqAllOpenOrders()

    trade_match = None
    for trade in ib.trades():
        t_order_id = getattr(trade.order, "orderId", None)
        t_perm_id = getattr(trade.order, "permId", None)
        if (order_id is not None and t_order_id == order_id) or (perm_id is not None and t_perm_id == perm_id):
            trade_match = trade
            break

    if trade_match is None:
        return {
            "as_of_utc": _now_iso(),
            "found": False,
            "order_id": order_id,
            "perm_id": perm_id,
            "message": "Order ID not found in current session cache.",
        }

    order = trade_match.order
    status = trade_match.orderStatus
    log_rows: list[dict[str, Any]] = []
    for entry in getattr(trade_match, "log", []):
        log_rows.append(
            {
                "time": str(getattr(entry, "time", "")) or None,
                "status": getattr(entry, "status", None),
                "message": getattr(entry, "message", None),
                "error_code": getattr(entry, "errorCode", None),
            }
        )

    fill_rows: list[dict[str, Any]] = []
    for fill in getattr(trade_match, "fills", []):
        execution = fill.execution
        commission = fill.commissionReport
        fill_rows.append(
            {
                "exec_id": getattr(execution, "execId", None),
                "time": str(getattr(execution, "time", "")) or None,
                "side": getattr(execution, "side", None),
                "shares": _as_float(getattr(execution, "shares", None)),
                "price": _as_float(getattr(execution, "price", None)),
                "commission": _as_float(getattr(commission, "commission", None)),
                "commission_currency": getattr(commission, "currency", None),
                "realized_pnl": _as_float(getattr(commission, "realizedPNL", None)),
            }
        )

    return {
        "as_of_utc": _now_iso(),
        "found": True,
        "order_id": getattr(order, "orderId", None),
        "perm_id": getattr(order, "permId", None),
        "account": getattr(order, "account", None),
        "client_id": getattr(order, "clientId", None),
        "action": getattr(order, "action", None),
        "order_type": getattr(order, "orderType", None),
        "total_quantity": _as_float(getattr(order, "totalQuantity", None)),
        "limit_price": _as_float(getattr(order, "lmtPrice", None)),
        "aux_price": _as_float(getattr(order, "auxPrice", None)),
        "tif": getattr(order, "tif", None),
        "status": getattr(status, "status", None),
        "filled": _as_float(getattr(status, "filled", None)),
        "remaining": _as_float(getattr(status, "remaining", None)),
        "avg_fill_price": _as_float(getattr(status, "avgFillPrice", None)),
        "last_fill_price": _as_float(getattr(status, "lastFillPrice", None)),
        "why_held": getattr(status, "whyHeld", None),
        "contract": _contract_payload(trade_match.contract),
        "fills": fill_rows,
        "log": log_rows,
    }


@mcp.tool()
def get_broker_state(
    base_currency: str = "USD",
    account: str | None = None,
    recent_trades_limit: int = 50,
    offline_snapshot_path: str | None = None,
) -> dict[str, Any]:
    """Return canonical IBKR broker state and persist a fallback snapshot on live success.

    Falls back to the on-disk broker-state snapshot when live IBKR connectivity is unavailable.
    """
    base = base_currency.upper().strip()

    try:
        ib = _connect_ib()
        snapshot = _build_live_broker_state(ib, base, account, recent_trades_limit)
        written_path = _write_offline_snapshot(snapshot, offline_snapshot_path)
        metadata = dict(snapshot.get("metadata", {}))
        metadata["offline_snapshot_path"] = written_path
        metadata["live_available"] = True
        snapshot["metadata"] = metadata
        return snapshot
    except Exception as exc:
        offline_snapshot, used_offline_path = _load_offline_assets(offline_snapshot_path)
        if not offline_snapshot:
            raise RuntimeError(
                f"Live IBKR unavailable and no offline broker-state snapshot found: {exc}"
            ) from exc

        snapshot = _filter_snapshot_for_account(_rebase_snapshot(offline_snapshot, base), account)
        snapshot["snapshot_source"] = "offline_snapshot"
        metadata = dict(snapshot.get("metadata", {}))
        metadata["offline_snapshot_path"] = used_offline_path
        metadata["live_available"] = False
        metadata["live_error"] = str(exc)
        metadata["recent_trades_limit"] = recent_trades_limit
        snapshot["metadata"] = metadata
        return snapshot


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
