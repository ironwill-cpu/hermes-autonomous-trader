import sys
import json
import ccxt

# --- CONFIGURATION ---
API_KEY = "UncKoy7aMOMwx3jsSi0gRYJGpIFPRZuAWFZU7oO9kKPsiOzRl0J2aKpdwXOPcBPv"
SECRET_KEY = "N36PalyoyN5IuiDgSfUer7U0MwyKt1O93KF1kV0SHkNvqeyJ0DHH3tyfDXm9S09h"
USE_TESTNET = True  # Set to False ONLY when switching to real live funds
# ---------------------

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": SECRET_KEY,
    "enableRateLimit": True,
    "options": {"defaultType": "spot", "useServerTime": True, "adjustForTimeDifference": True},
})

if USE_TESTNET:
    exchange.set_sandbox_mode(True)


def execute_buy(symbol, usdt_amount, stop_loss_price, take_profit_price):
    exchange.load_markets()
    ticker = exchange.fetch_ticker(symbol)
    current_price = float(ticker["last"])

    raw_qty = float(usdt_amount) / current_price
    qty = float(exchange.amount_to_precision(symbol, raw_qty))
    sl_price = float(exchange.price_to_precision(symbol, float(stop_loss_price)))
    tp_price = float(exchange.price_to_precision(symbol, float(take_profit_price)))
    sl_limit = float(exchange.price_to_precision(symbol, sl_price * 0.998))

    # 1. Place Market Buy Order
    buy_order = exchange.create_market_buy_order(symbol, qty)
    filled_qty = float(buy_order.get("filled") or qty)
    filled_qty = float(exchange.amount_to_precision(symbol, filled_qty))

    # 2. Place Exchange-Side OCO (Stop-Loss + Take-Profit) Protection
    protection_status = "OCO_SET"
    protection_detail = {}
    try:
        oco = exchange.private_post_order_oco({
            "symbol": exchange.market_id(symbol),
            "side": "SELL",
            "quantity": exchange.amount_to_precision(symbol, filled_qty),
            "price": exchange.price_to_precision(symbol, tp_price),
            "stopPrice": exchange.price_to_precision(symbol, sl_price),
            "stopLimitPrice": exchange.price_to_precision(symbol, sl_limit),
            "stopLimitTimeInForce": "GTC",
        })
        protection_detail = {"oco_id": oco.get("orderListId")}
    except Exception as oco_err:
        # Fallback: place Stop-Loss Limit order if OCO is unavailable on pair/testnet
        protection_status = f"FALLBACK_SL_ONLY ({str(oco_err)})"
        sl_order = exchange.create_order(
            symbol=symbol,
            type="STOP_LOSS_LIMIT",
            side="sell",
            amount=filled_qty,
            price=sl_limit,
            params={"stopPrice": sl_price, "timeInForce": "GTC"},
        )
        protection_detail = {"sl_order_id": sl_order.get("id")}

    return {
        "status": "BUY_EXECUTED",
        "mode": "TESTNET" if USE_TESTNET else "LIVE",
        "symbol": symbol,
        "entry_price": current_price,
        "quantity": filled_qty,
        "stop_loss": sl_price,
        "take_profit": tp_price,
        "protection": protection_status,
        "protection_detail": protection_detail,
    }


def execute_sell(symbol):
    exchange.load_markets()
    coin = symbol.split("/")[0]

    # 1. Cancel any open OCO / Stop-Loss / Take-Profit orders first to unlock balance
    open_orders = exchange.fetch_open_orders(symbol)
    for order in open_orders:
        try:
            exchange.cancel_order(order["id"], symbol)
        except Exception:
            pass

    # 2. Fetch unlocked coin balance and sell at market price
    balance = exchange.fetch_balance()
    free_qty = float(balance.get(coin, {}).get("free", 0.0))
    if free_qty <= 0:
        return {"status": "SKIPPED", "reason": f"No {coin} balance available to sell."}

    qty = float(exchange.amount_to_precision(symbol, free_qty))
    sell_order = exchange.create_market_sell_order(symbol, qty)
    return {
        "status": "SELL_EXECUTED",
        "mode": "TESTNET" if USE_TESTNET else "LIVE",
        "symbol": symbol,
        "sold_quantity": qty,
        "order_id": sell_order.get("id"),
    }


if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            raise ValueError("Usage: trade_executor.py buy <SYMBOL> <USDT_AMT> <SL> <TP> | sell <SYMBOL>")

        action = sys.argv[1].lower()
        symbol = sys.argv[2].upper()

        if action == "buy":
            if len(sys.argv) != 6:
                raise ValueError("Usage: trade_executor.py buy <SYMBOL> <USDT_AMT> <SL> <TP>")
            res = execute_buy(symbol, sys.argv[3], sys.argv[4], sys.argv[5])
        elif action == "sell":
            res = execute_sell(symbol)
        else:
            raise ValueError("Action must be 'buy' or 'sell'")

        print(json.dumps(res, indent=2))
    except Exception as e:
        print(json.dumps({"status": "ERROR", "message": str(e)}))
