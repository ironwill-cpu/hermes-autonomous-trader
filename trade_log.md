# Autonomous Trader Trade Log

## 2026-11-24 09:11 UTC
- Initial setup and verification.

## 2026-11-24 09:20 UTC
- Scanner run: SUCCESS
- Mode: TESTNET
- USDT free: 10000.00
- Market: BEARISH_DOWNTREND across all symbols.
=== 2026-11-24 12:09:37 UTC - Scanner Run ===
{
  "status": "SUCCESS",
  "mode": "TESTNET",
  "usdt_free": 9900.47,
  "coin_holdings": {
    "BTC": {
      "free": 1.0,
      "locked_in_orders": 0.00165,
      "total": 1.00165
    },
    "ETH": {
      "free": 1.0,
      "locked_in_orders": 0.0,
      "total": 1.0
    },
    "SOL": {
      "free": 4.0,
      "locked_in_orders": 0.0,
      "total": 4.0
    }
  },
  "open_orders_count": {
    "BTC/USDT": 2,
    "ETH/USDT": 0,
    "SOL/USDT": 0
  },
  "markets": {
    "BTC/USDT": {
      "4h_macro": {
        "structure": "BEARISH_DOWNTREND",
        "price": 60435.9,
        "ema_20": 60926.5105,
        "ema_50": 62511.7802,
        "ema_200": 70675.6669,
        "rsi_14": 57.22,
        "atr_14": 7534.6229,
        "volume_ratio": 0.83,
        "support_50": 49826.4,
        "resistance_50": 71477.77
      },
      "1h_primary": {
        "structure": "BEARISH_DOWNTREND",
        "price": 60435.9,
        "ema_20": 60707.4046,
        "ema_50": 60871.6168,
        "ema_200": 61827.8932,
        "rsi_14": 36.71,
        "atr_14": 1585.9236,
        "volume_ratio": 0.89,
        "support_50": 49826.4,
        "resistance_50": 67612.96
      },
      "15m_entry": {
        "structure": "BEARISH_DOWNTREND",
        "price": 60435.9,
        "ema_20": 60111.5063,
        "ema_50": 60459.4522,
        "ema_200": 60759.1885,
        "rsi_14": 52.64,
        "atr_14": 299.6557,
        "volume_ratio": 0.85,
        "support_50": 54000.0,
        "resistance_50": 67612.96
      }
    },
    "ETH/USDT": {
      "4h_macro": {
        "structure": "BEARISH_DOWNTREND",
        "price": 1703.52,
        "ema_20": 1712.633,
        "ema_50": 1758.8225,
        "ema_200": 2025.8968,
        "rsi_14": 59.43,
        "atr_14": 66.7014,
        "volume_ratio": 1.08,
        "support_50": 1316.67,
        "resistance_50": 1865.75
      },
      "1h_primary": {
        "structure": "BEARISH_DOWNTREND",
        "price": 1703.52,
        "ema_20": 1706.8167,
        "ema_50": 1711.3259,
        "ema_200": 1737.0575,
        "rsi_14": 39.4,
        "atr_14": 22.105,
        "volume_ratio": 1.04,
        "support_50": 1383.66,
        "resistance_50": 1843.24
      },
      "15m_entry": {
        "structure": "BEARISH_DOWNTREND",
        "price": 1703.52,
        "ema_20": 1691.9276,
        "ema_50": 1700.2268,
        "ema_200": 1709.553,
        "rsi_14": 54.67,
        "atr_14": 13.41,
        "volume_ratio": 1.17,
        "support_50": 1663.84,
        "resistance_50": 1737.1
      }
    },
    "SOL/USDT": {
      "4h_macro": {
        "structure": "BEARISH_DOWNTREND",
        "price": 70.92,
        "ema_20": 71.507,
        "ema_50": 72.7217,
        "ema_200": 84.1792,
        "rsi_14": 55.75,
        "atr_14": 3.235,
        "volume_ratio": 0.93,
        "support_50": 59.11,
        "resistance_50": 84.02
      },
      "1h_primary": {
        "structure": "SIDEWAYS_CHOPPY",
        "price": 70.92,
        "ema_20": 71.6972,
        "ema_50": 71.6566,
        "ema_200": 71.6035,
        "rsi_14": 34.03,
        "atr_14": 0.7329,
        "volume_ratio": 0.97,
        "support_50": 59.11,
        "resistance_50": 78.93
      },
      "15m_entry": {
        "structure": "BEARISH_DOWNTREND",
        "price": 70.92,
        "ema_20": 70.9018,
        "ema_50": 71.4314,
        "ema_200": 71.5368,
        "rsi_14": 39.71,
        "atr_14": 0.3664,
        "volume_ratio": 1.26,
        "support_50": 69.97,
        "resistance_50": 72.68
      }
    }
  }
}

{
  "at": "2026-11-24 13:04:05 UTC",
  "action": "SCAN",
  "decision": "SELL",
  "reason": "Held asset trend flipped bearish",
  "symbol": "BTC/USDT"
}
{
  "at": "2026-11-24 13:05:02 UTC",
  "action": "SCAN",
  "decision": "SELL",
  "reason": "Held asset trend flipped bearish",
  "symbol": "BTC/USDT"
}
{
  "status": "EXECUTED",
  "action": "SELL",
  "symbol": "BTC/USDT",
  "sell_price": 60445.89,
  "sold_quantity": 1.00165,
  "order_id": "17380201",
  "pnl": null,
  "result": null,
  "at": "2026-11-24 13:05:04 UTC"
}
{
  "at": "2026-11-24 13:06:15 UTC",
  "action": "SCAN",
  "decision": "SELL",
  "reason": "Held asset trend flipped bearish",
  "symbol": "ETH/USDT"
}
{
  "status": "EXECUTED",
  "action": "SELL",
  "symbol": "ETH/USDT",
  "sell_price": 1705.67,
  "sold_quantity": 1.0,
  "order_id": "12061800",
  "pnl": null,
  "result": null,
  "at": "2026-11-24 13:06:17 UTC"
}
