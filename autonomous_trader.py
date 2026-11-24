#!/usr/bin/env python3
"""
Fully autonomous 24/7 crypto trader.
Reads the market, decides BUY/SELL/WAIT, and executes automatically.
Credentials come from config.py (never hardcoded here).
Run by cron every 30 minutes. Testnet by default.
"""

import json
import os
import re
import sys
import time
import ccxt
import numpy as np
import pandas as pd

from config import API_KEY, SECRET_KEY, USE_TESTNET

TRADE_MODE = os.getenv("TRADE_MODE", "auto")   # auto | dry_run
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
TIMEFRAMES = ["4h", "1h", "15m"]
SLIPPAGE = 0.9985
RISK_PER_TRADE = 0.01      # 1% of free USDT
MAX_POSITION_PCT = 0.30    # cap 30% of free USDT
MIN_POSITION_USDT = 15.0
MIN_POSITION_VALUE_USDT = 10.0
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TRADE_LOG = os.path.join(BASE_DIR, "trade_log.md")

exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": SECRET_KEY,
    "enableRateLimit": True,
    "options": {"defaultType": "spot", "useServerTime": True, "adjustForTimeDifference": True},
})
if USE_TESTNET:
    exchange.set_sandbox_mode(True)


def log(msg):
    print("[AUTONOMOUS] " + str(msg), flush=True)


def append_log(entry):
    with open(TRADE_LOG, "a") as f:
        f.write(json.dumps(entry, indent=2) + "\n")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())


# ---------------- Market analysis ----------------
def analyze(symbol, tf):
    bars = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=210)
    df = pd.DataFrame(bars, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()
    df["ema200"] = df["close"].ewm(span=200, adjust=False).mean()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))
    tr = np.maximum(df["high"] - df["low"],
                    np.maximum(abs(df["high"] - df["close"].shift()),
                               abs(df["low"] - df["close"].shift())))
    df["atr"] = tr.rolling(14).mean()
    avg_vol = df["volume"].iloc[-21:-1].mean()
    last = df.iloc[-2]  # last CLOSED candle (no repaint)
    price = float(last["close"])

    if price > last["ema200"] and last["ema20"] > last["ema50"]:
        structure = "BULLISH_UPTREND"
    elif price < last["ema200"] and last["ema20"] < last["ema50"]:
        structure = "BEARISH_DOWNTREND"
    else:
        structure = "SIDEWAYS_CHOPPY"

    return {
        "structure": structure,
        "price": round(price, 4),
        "ema20": round(float(last["ema20"]), 4),
        "ema50": round(float(last["ema50"]), 4),
        "rsi": round(float(last["rsi"]), 2),
        "atr": round(float(last["atr"]), 4),
        "volume_ratio": round(float(last["volume"] / avg_vol) if avg_vol > 0 else 1.0, 2),
        "support": round(float(df["low"].iloc[-50:-1].min()), 4),
        "resistance": round(float(df["high"].iloc[-50:-1].max()), 4),
    }


def scan():
    balance = exchange.fetch_balance()
    usdt_free = float(balance.get("USDT", {}).get("free", 0.0))
    data = {"usdt_free": round(usdt_free, 2), "balance": balance, "symbols": {}}
    for sym in SYMBOLS:
        coin = sym.split("/")[0]
        free = float(balance.get(coin, {}).get("free", 0.0))
        used = float(balance.get(coin, {}).get("used", 0.0))
        orders = exchange.fetch_open_orders(sym)
        data["symbols"][sym] = {
            "coin": coin,
            "free": free,
            "used": used,
            "total": free + used,
            "open_orders": len(orders),
            "tf": {tf: analyze(sym, tf) for tf in TIMEFRAMES},
        }
    return data


# ---------------- Log-based state ----------------
def read_log_entries():
    entries = []
    if not os.path.exists(TRADE_LOG):
        return entries
    with open(TRADE_LOG) as f:
        for line in f:
            line = line.strip()
            if line.startswith("{"):
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    return entries


def circuit_breaker_active(entries):
    results = [e.get("result") for e in entries if e.get("result") in ("WIN", "LOSS")]
    if len(results) >= 2 and results[-1] == "LOSS" and results[-2] == "LOSS":
        return True
    return False


def last_buy_price(entries, symbol):
    for e in reversed(entries):
        if e.get("action") == "BUY" and e.get("status") == "EXECUTED" and e.get("symbol") == symbol:
            return e.get("entry_price")
    return None


# ---------------- Decision engine ----------------
def decide(data, entries):
    blocked = circuit_breaker_active(entries)
    actions = []

    for sym, s in data["symbols"].items():
        m4, m1, m15 = s["tf"]["4h"], s["tf"]["1h"], s["tf"]["15m"]
        coin_value = s["total"] * m1["price"]
        has_position = coin_value >= MIN_POSITION_VALUE_USDT
        price = m1["price"]

        # EXIT: held asset turning bearish or hitting TP/SL
        if has_position:
            if m4["structure"] == "BEARISH_DOWNTREND" or m1["structure"] == "BEARISH_DOWNTREND":
                actions.append({"signal": "SELL", "symbol": sym, "strength": "strong",
                                "reason": "Held asset trend flipped bearish"})
            elif price >= m1["resistance"] * 0.995:
                actions.append({"signal": "SELL", "symbol": sym, "strength": "weak",
                                "reason": "Price near resistance - book profit"})
            continue

        # ENTRY: strict trend alignment on 4h+1h, clean 15m entry
        if blocked:
            continue
        if s["open_orders"] > 0:
            continue
        aligned_bull = (m4["structure"] == "BULLISH_UPTREND" and
                        m1["structure"] == "BULLISH_UPTREND")
        pullback = (m4["structure"] == "BULLISH_UPTREND" and
                    m1["structure"] == "SIDEWAYS_CHOPPY" and
                    price <= m1["ema20"] * 1.01 and 40 <= m1["rsi"] <= 62)
        if aligned_bull or pullback:
            if m15["rsi"] < 70 and price < m15["resistance"] * 0.99:
                atr = m1["atr"]
                sl = price - 1.8 * atr
                tp = price + 3.6 * atr
                sl_pct = (price - sl) / price
                risk = data["usdt_free"] * RISK_PER_TRADE
                size = min(risk / max(sl_pct, 0.001), data["usdt_free"] * MAX_POSITION_PCT)
                size = max(size, MIN_POSITION_USDT)
                actions.append({"signal": "BUY", "symbol": sym, "strength": "strong" if aligned_bull else "weak",
                                "reason": "Trend aligned bullish" if aligned_bull else "Bullish pullback",
                                "sl": round(sl, 4), "tp": round(tp, 4), "amount": round(size, 2)})

    sells = [a for a in actions if a["signal"] == "SELL"]
    buys = [a for a in actions if a["signal"] == "BUY"]
    if sells:
        return sells[0]
    if buys:
        return buys[0]
    return {"signal": "WAIT", "reason": "Circuit breaker" if blocked else "No clean setup", "symbol": None}


# ---------------- Execution ----------------
def do_buy(decision):
    sym, amount = decision["symbol"], decision["amount"]
    t = exchange.fetch_ticker(sym)
    price = float(t["last"])
    qty = float(exchange.amount_to_precision(sym, amount / price))
    sl = float(exchange.price_to_precision(sym, decision["sl"]))
    tp = float(exchange.price_to_precision(sym, decision["tp"]))
    exchange.create_market_buy_order(sym, qty)
    try:
        exchange.private_post_order_oco({
            "symbol": exchange.market_id(sym), "side": "SELL",
            "quantity": exchange.amount_to_precision(sym, qty),
            "price": exchange.price_to_precision(sym, tp),
            "stopPrice": exchange.price_to_precision(sym, sl),
            "stopLimitPrice": exchange.price_to_precision(sym, sl * SLIPPAGE),
            "stopLimitTimeInForce": "GTC",
        })
        protection = "OCO_SET"
    except Exception:
        try:
            exchange.create_order(sym, "STOP_LOSS_LIMIT", "sell", qty, sl * SLIPPAGE,
                                  {"stopPrice": sl, "timeInForce": "GTC"})
            protection = "SL_ONLY"
        except Exception:
            protection = "NONE"
    return {"status": "EXECUTED", "action": "BUY", "symbol": sym, "entry_price": price,
            "quantity": qty, "amount_usdt": amount, "sl": sl, "tp": tp,
            "protection": protection, "at": now()}


def do_sell(decision, entries):
    sym = decision["symbol"]
    coin = sym.split("/")[0]
    for o in exchange.fetch_open_orders(sym):
        try:
            exchange.cancel_order(o["id"], sym)
        except Exception:
            pass
    bal = exchange.fetch_balance()
    free = float(bal.get(coin, {}).get("free", 0.0))
    if free <= 0:
        return {"status": "SKIPPED", "action": "SELL", "symbol": sym, "reason": "No free balance"}
    t = exchange.fetch_ticker(sym)
    sell_price = float(t["last"])
    qty = float(exchange.amount_to_precision(sym, free))
    order = exchange.create_market_sell_order(sym, qty)
    entry = last_buy_price(entries, sym)
    result = None
    pnl = None
    if entry:
        pnl = round((sell_price - entry) / entry, 5)
        result = "WIN" if pnl > 0 else "LOSS"
    return {"status": "EXECUTED", "action": "SELL", "symbol": sym, "sell_price": sell_price,
            "sold_quantity": qty, "order_id": order.get("id"), "pnl": pnl,
            "result": result, "at": now()}


# ---------------- Main ----------------
def run():
    log("Cycle start | mode=%s | trade_mode=%s" % ("TESTNET" if USE_TESTNET else "LIVE", TRADE_MODE))
    try:
        entries = read_log_entries()
        data = scan()
        log("USDT free: %s" % data["usdt_free"])
        for sym, s in data["symbols"].items():
            log("%s total=%.6f orders=%d | 4h=%s 1h=%s 15m=%s" % (
                sym, s["total"], s["open_orders"],
                s["tf"]["4h"]["structure"], s["tf"]["1h"]["structure"], s["tf"]["15m"]["structure"]))

        decision = decide(data, entries)
        log("DECISION: %s %s (%s)" % (decision["signal"], decision.get("symbol") or "", decision["reason"]))
        append_log({"at": now(), "action": "SCAN", "decision": decision["signal"],
                    "reason": decision["reason"], "symbol": decision.get("symbol")})

        if decision["signal"] == "WAIT":
            log("Nothing to do this cycle.")
            return
        if TRADE_MODE != "auto":
            log("dry_run: would %s %s but no order placed." % (decision["signal"], decision.get("symbol")))
            return

        if decision["signal"] == "BUY":
            res = do_buy(decision)
        else:
            res = do_sell(decision, entries)
        append_log(res)
        log("EXECUTED: %s" % json.dumps(res))
    except ccxt.BaseError as e:
        log("EXCHANGE ERROR: %s" % e)
        append_log({"at": now(), "action": "ERROR", "message": str(e)})
    except Exception as e:
        log("ERROR: %s" % e)
        append_log({"at": now(), "action": "ERROR", "message": str(e)})


if __name__ == "__main__":
    run()
