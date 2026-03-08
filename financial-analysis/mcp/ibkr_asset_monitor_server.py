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
"""

from __future__ import annotations

import math
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _as_float(value: Any) -> float | None:
    if _is_finite(value):
        return float(value)
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


def _load_offline_assets(path_override: str | None) -> tuple[list[dict[str, Any]], str | None]:
    default_path = Path("financial-analysis/data/offline-assets.json")
    path = Path(path_override or os.getenv("ASSET_MONITOR_OFFLINE_PATH", str(default_path)))
    if not path.exists():
        return [], None

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Offline assets file must be a JSON array")
    return payload, str(path)


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
    """Return unified portfolio with ticker/currency normalization and optional offline assets."""
    ib = _connect_ib()
    base = base_currency.upper().strip()

    rows: list[dict[str, Any]] = []
    portfolio_items = ib.portfolio(account) if account else ib.portfolio()

    for item in portfolio_items:
        contract = item.contract
        exchange = getattr(contract, "primaryExchange", None) or getattr(contract, "exchange", None)
        market_value = _as_float(getattr(item, "marketValue", None))
        if market_value is None:
            position = _as_float(getattr(item, "position", None)) or 0.0
            market_price = _as_float(getattr(item, "marketPrice", None)) or 0.0
            market_value = position * market_price

        rows.append(
            {
                "source": "ibkr",
                "account": getattr(item, "account", None),
                "symbol": contract.symbol,
                "sec_type": contract.secType,
                "exchange": contract.exchange,
                "primary_exchange": getattr(contract, "primaryExchange", None),
                "ticker_normalized": _normalize_ticker(contract.symbol, exchange),
                "currency": contract.currency,
                "quantity": _as_float(getattr(item, "position", None)),
                "price": _as_float(getattr(item, "marketPrice", None)),
                "average_cost": _as_float(getattr(item, "averageCost", None)),
                "market_value": market_value,
                "unrealized_pnl": _as_float(getattr(item, "unrealizedPNL", None)),
                "realized_pnl": _as_float(getattr(item, "realizedPNL", None)),
            }
        )

    used_offline_path: str | None = None
    if include_offline_assets:
        offline_assets, used_offline_path = _load_offline_assets(offline_assets_path)
        for asset in offline_assets:
            symbol = str(asset.get("symbol") or asset.get("ticker") or "OFFLINE").upper().strip()
            exchange = str(asset.get("exchange") or "OFFLINE").upper().strip()
            currency = str(asset.get("currency") or base).upper().strip()

            quantity = _as_float(asset.get("quantity"))
            price = _as_float(asset.get("price"))
            market_value = _as_float(asset.get("market_value"))
            if market_value is None and quantity is not None and price is not None:
                market_value = quantity * price

            rows.append(
                {
                    "source": "offline",
                    "account": asset.get("account"),
                    "symbol": symbol,
                    "sec_type": str(asset.get("sec_type") or "OFFLINE"),
                    "exchange": exchange,
                    "primary_exchange": None,
                    "ticker_normalized": _normalize_ticker(symbol, exchange),
                    "currency": currency,
                    "quantity": quantity,
                    "price": price,
                    "average_cost": _as_float(asset.get("average_cost") or asset.get("cost_basis")),
                    "market_value": market_value,
                    "unrealized_pnl": _as_float(asset.get("unrealized_pnl")),
                    "realized_pnl": _as_float(asset.get("realized_pnl")),
                }
            )

    currencies = {str(row.get("currency") or base).upper() for row in rows}
    fx = _fx_rates_to_base(ib, currencies, base)

    total_base_value = 0.0
    for row in rows:
        currency = str(row.get("currency") or base).upper()
        rate = fx.get(currency)
        row["fx_to_base"] = rate

        mv = _as_float(row.get("market_value"))
        if rate is None or mv is None:
            row["market_value_base"] = None
            continue

        base_value = mv * rate
        row["market_value_base"] = base_value
        total_base_value += base_value

    for row in rows:
        mv_base = _as_float(row.get("market_value_base"))
        row["portfolio_weight"] = (mv_base / total_base_value) if (mv_base is not None and total_base_value > 0) else None

    rows.sort(key=lambda r: abs(_as_float(r.get("market_value_base")) or 0.0), reverse=True)

    return {
        "as_of_utc": _now_iso(),
        "base_currency": base,
        "fx_rates": fx,
        "offline_assets_path": used_offline_path,
        "total_market_value_base": total_base_value,
        "positions": rows,
    }


@mcp.tool()
def get_open_orders(account: str | None = None) -> dict[str, Any]:
    """Return currently open IBKR orders (read-only).

    Each row includes both `order_id` and `perm_id`.
    Prefer `perm_id` for cross-session/cross-client tracking.
    """
    ib = _connect_ib()
    trades = list(ib.reqAllOpenOrders())

    rows: list[dict[str, Any]] = []
    for trade in trades:
        order = trade.order
        status = trade.orderStatus
        acct = getattr(order, "account", None)
        if account and acct != account:
            continue

        payload = {
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
        rows.append(payload)

    rows.sort(key=lambda r: ((r.get("perm_id") or 0), (r.get("order_id") or 0)), reverse=True)
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
    if limit <= 0:
        raise ValueError("limit must be > 0")
    limit = min(limit, 500)

    ib = _connect_ib()
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
    limited = rows[:limit]
    return {
        "as_of_utc": _now_iso(),
        "count": len(limited),
        "total_available": len(rows),
        "recent_trades": limited,
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
