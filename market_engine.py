import requests
import pandas as pd
import numpy as np

# MT5 Integration
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

def init_mt5():
    if MT5_AVAILABLE and not mt5.initialize():
        return False
    return MT5_AVAILABLE

def get_mt5_gold_symbol():
    """Auto-detects broker Gold symbol on MT5."""
    if not init_mt5():
        return None
    for sym in ["GOLD", "GOLDmicro", "XAUUSD", "XAUUSDm", "XAUUSD.m", "GOLD.m"]:
        if mt5.symbol_info(sym) is not None:
            mt5.symbol_select(sym, True)
            return sym
    return None

def fetch_mt5_klines(symbol="GOLD", timeframe=mt5.TIMEFRAME_M15 if MT5_AVAILABLE else None, limit=100):
    if not init_mt5() or not symbol:
        return None
    try:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, limit)
        if rates is None or len(rates) == 0:
            return None
        df = pd.DataFrame(rates)
        df.rename(columns={"tick_volume": "volume"}, inplace=True)
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        df["taker_base"] = df["volume"] * 0.5
        return df
    except Exception:
        return None

def fetch_binance_klines(symbol="BTCUSDT", interval="15m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    res = requests.get(url, timeout=5).json()
    df = pd.DataFrame(res, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_base", "taker_quote", "ignore"
    ])
    for col in ["open", "high", "low", "close", "volume", "taker_base"]:
        df[col] = df[col].astype(float)
    return df

def fetch_fear_and_greed():
    """Fetches Live Crypto Fear & Greed Index."""
    try:
        res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=3).json()
        data = res.get("data", [{}])[0]
        return f"{data.get('value', '50')} ({data.get('value_classification', 'Neutral')})"
    except Exception:
        return "50 (Neutral)"

def fetch_binance_derivatives_data(symbol="BTCUSDT"):
    """Fetches Live Open Interest, Funding Rate, and Whales vs Retail Ratio."""
    try:
        # 1. Open Interest History (15m change)
        oi_url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=15m&limit=5"
        oi_res = requests.get(oi_url, timeout=4).json()
        
        if isinstance(oi_res, list) and len(oi_res) >= 2:
            latest_oi = float(oi_res[-1]["sumOpenInterestValue"])
            prev_oi = float(oi_res[-2]["sumOpenInterestValue"])
            oi_change_pct = round(((latest_oi - prev_oi) / prev_oi) * 100, 2)
        else:
            latest_oi, oi_change_pct = 0.0, 0.0

        # 2. Predicted Funding Rate
        fr_url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=1"
        fr_res = requests.get(fr_url, timeout=4).json()
        funding_rate = float(fr_res[0]["fundingRate"]) * 100 if isinstance(fr_res, list) and len(fr_res) > 0 else 0.01

        # 3. Top Trader Long/Short Ratio
        ls_url = f"https://fapi.binance.com/futures/data/topLongShortPositionRatio?symbol={symbol}&period=15m&limit=1"
        ls_res = requests.get(ls_url, timeout=4).json()
        ls_ratio = float(ls_res[0]["longShortRatio"]) if isinstance(ls_res, list) and len(ls_res) > 0 else 1.0

        # Status interpretations
        if oi_change_pct < -1.2:
            oi_status = f"Sharp OI Drop ({oi_change_pct}%) - Liquidation Flush (Reversal Ready)"
        elif oi_change_pct > 1.5:
            oi_status = f"Sharp OI Surge (+{oi_change_pct}%) - Aggressive Capital Inflow"
        else:
            oi_status = f"Stable OI ({oi_change_pct}%)"

        if funding_rate < 0:
            fr_status = f"Negative Funding ({funding_rate:.4f}%) - Potential Short Squeeze"
        elif funding_rate > 0.03:
            fr_status = f"High Positive Funding ({funding_rate:.4f}%) - High Long Flush Risk"
        else:
            fr_status = f"Neutral Funding ({funding_rate:.4f}%)"

        return {
            "latest_oi_val": f"${latest_oi/1000000:.2f}M",
            "oi_status": oi_status,
            "funding_status": fr_status,
            "whales_ratio": f"{ls_ratio:.2f} Long/Short"
        }
    except Exception:
        return {
            "latest_oi_val": "N/A",
            "oi_status": "OI Stable",
            "funding_status": "Neutral Funding",
            "whales_ratio": "1.00 Long/Short"
        }

def calculate_liquidation_heatmap_pools(df, current_price):
    swing_high = df["high"].iloc[-50:].max()
    swing_low = df["low"].iloc[-50:].min()
    
    upper_liq_pool = f"${round(swing_high * 1.008, 2)} – ${round(swing_high * 1.018, 2)} (Short Liquidations Target)"
    lower_liq_pool = f"${round(swing_low * 0.992, 2)} – ${round(swing_low * 0.982, 2)} (Long Liquidations Target)"
    
    return {
        "upper_liq_pool": upper_liq_pool,
        "lower_liq_pool": lower_liq_pool,
        "swing_high": swing_high,
        "swing_low": swing_low
    }

def analyze_technical_models(symbol="BTCUSDT"):
    is_gold = symbol in ["GOLD", "XAUUSD", "GOLD_MT5", "GOLDmicro"]
    df_15m, df_1h, df_4h = None, None, None
    display_symbol = symbol

    if is_gold and MT5_AVAILABLE and init_mt5():
        mt5_sym = get_mt5_gold_symbol()
        if mt5_sym:
            df_15m = fetch_mt5_klines(mt5_sym, mt5.TIMEFRAME_M15, 100)
            df_1h = fetch_mt5_klines(mt5_sym, mt5.TIMEFRAME_H1, 100)
            df_4h = fetch_mt5_klines(mt5_sym, mt5.TIMEFRAME_H4, 50)
            if df_15m is not None and len(df_15m) > 10:
                display_symbol = f"Gold XAU/USD (MT5: {mt5_sym})"

    if df_15m is None or len(df_15m) < 10 or df_1h is None or len(df_1h) < 10 or df_4h is None or len(df_4h) < 5:
        binance_sym = "PAXGUSDT" if is_gold else symbol
        df_15m = fetch_binance_klines(binance_sym, "15m", 100)
        df_1h = fetch_binance_klines(binance_sym, "1h", 100)
        df_4h = fetch_binance_klines(binance_sym, "4h", 50)
        display_symbol = "Gold XAU/USD (Binance PAXG)" if is_gold else symbol

    current_price = df_15m["close"].iloc[-1]
    
    # EMAs
    ema20 = round(df_15m["close"].ewm(span=20, adjust=False).mean().iloc[-1], 2)
    ema50 = round(df_15m["close"].ewm(span=50, adjust=False).mean().iloc[-1], 2)
    ema200 = round(df_1h["close"].ewm(span=200, adjust=False).mean().iloc[-1], 2)
    
    # RSI (14)
    delta = df_15m["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = round((100 - (100 / (1 + rs))).iloc[-1], 2)
    
    # CVD & Volume Delta
    df_15m["taker_sell"] = df_15m["volume"] - df_15m["taker_base"]
    df_15m["delta"] = df_15m["taker_base"] - df_15m["taker_sell"]
    recent_delta = df_15m["delta"].iloc[-3:].sum()
    price_change_recent = df_15m["close"].iloc[-1] - df_15m["close"].iloc[-3]
    
    if price_change_recent <= 0 and recent_delta > 0:
        cvd_status = "Bullish Absorption (Whales soaking sell orders)"
    elif price_change_recent >= 0 and recent_delta < 0:
        cvd_status = "Bearish Exhaustion (Whales capping the top)"
    else:
        cvd_status = "Delta Flow Aligned with Price"
    
    # CRT (Candle Range Theory 4H Sweep)
    prev_4h_high = df_4h["high"].iloc[-2]
    prev_4h_low = df_4h["low"].iloc[-2]
    curr_4h_high = df_4h["high"].iloc[-1]
    curr_4h_low = df_4h["low"].iloc[-1]
    
    crt_sweep_high = curr_4h_high > prev_4h_high and current_price < prev_4h_high
    crt_sweep_low = curr_4h_low < prev_4h_low and current_price > prev_4h_low
    
    # AMD Asian Range
    asia_candles = df_15m.iloc[-32:-8]
    asia_high = asia_candles["high"].max() if len(asia_candles) > 0 else current_price
    asia_low = asia_candles["low"].min() if len(asia_candles) > 0 else current_price
    
    judas_sweep_low = current_price < asia_low
    judas_sweep_high = current_price > asia_high
    
    # Fair Value Gap (FVG)
    c1, c2, c3 = df_15m.iloc[-3], df_15m.iloc[-2], df_15m.iloc[-1]
    bullish_fvg = c3["low"] > c1["high"]
    bearish_fvg = c3["high"] < c1["low"]
    
    # Quasimodo (QM) / Inducement Level
    recent_high = df_1h["high"].iloc[-20:].max()
    recent_low = df_1h["low"].iloc[-20:].min()
    qm_left_shoulder = round((recent_high + recent_low) / 2, 2)
    
    # Derivatives Feeds
    deriv_data = fetch_binance_derivatives_data("BTCUSDT" if is_gold else symbol)
    liq_pools = calculate_liquidation_heatmap_pools(df_1h, current_price)
    fng_score = fetch_fear_and_greed()
    
    return {
        "symbol": display_symbol,
        "current_price": current_price,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "rsi": rsi,
        "cvd_status": cvd_status,
        "deriv_data": deriv_data,
        "liq_pools": liq_pools,
        "fear_and_greed": fng_score,
        "crt_sweep_high": crt_sweep_high,
        "crt_sweep_low": crt_sweep_low,
        "asia_high": asia_high,
        "asia_low": asia_low,
        "judas_sweep_low": judas_sweep_low,
        "judas_sweep_high": judas_sweep_high,
        "bullish_fvg": bullish_fvg,
        "bearish_fvg": bearish_fvg,
        "qm_level": qm_left_shoulder
    }

def check_smt_divergence():
    try:
        btc_df = fetch_binance_klines("BTCUSDT", "1h", 10)
        eth_df = fetch_binance_klines("ETHUSDT", "1h", 10)
        
        btc_hh = btc_df["high"].iloc[-1] > btc_df["high"].iloc[-3]
        eth_hh = eth_df["high"].iloc[-1] > eth_df["high"].iloc[-3]
        
        if btc_hh and not eth_hh:
            return "Bearish SMT Divergence (BTC made HH, ETH failed)"
        elif not btc_hh and eth_hh:
            return "Bullish SMT Divergence (ETH made HH, BTC accumulating)"
        return "SMT Aligned"
    except Exception:
        return "SMT Neutral"