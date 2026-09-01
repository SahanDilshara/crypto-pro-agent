import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def evaluate_setup_with_ai(data, smt_status, news_context):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return "STATUS: WAIT\nBIAS: NEUTRAL\nCONFLUENCE_SCORE: 0/3\nTIER: NO_TRADE\nMISSING_TRIGGER: Gemini Key Missing in .env\nREASONING: Check GEMINI_API_KEY in .env"

    genai.configure(api_key=api_key)
    deriv = data.get("deriv_data", {})
    lp = data.get("liq_pools", {})
    
    prompt = f"""
    You are an elite Institutional Quantitative Trader, Liquidation Specialist & Risk Manager for Sahan Dilshara.
    You classify trades into:
    - 🌟 TIER 1: A+ INSTITUTIONAL SETUP (Score 3/3 - High Conviction Full Sizing)
    - ⚡ TIER 2: B+ INTRADAY SCALP (Score 2/3 - High Frequency Scalp Playbooks)
    - ⏳ TIER 3: WAIT / NO-TRADE (Score < 2/3 - Market in chop)

    LIVE ASSET TECHNICAL, LIQUIDATION & ORDER FLOW DATA:
    - Symbol: {data['symbol']} | Current Price: {data['current_price']}
    - 20 EMA: {data['ema20']} | 50 EMA: {data['ema50']} | 200 EMA (Macro Baseline): {data['ema200']}
    - RSI (14): {data['rsi']} | Market Sentiment (Fear & Greed): {data['fear_and_greed']}
    - CVD Delta Absorption: {data['cvd_status']}
    - Futures Open Interest: {deriv.get('oi_status', 'N/A')}
    - Funding Rate: {deriv.get('funding_status', 'N/A')}
    - Top Whales Position Ratio: {deriv.get('whales_ratio', '1.0')}
    - Upper Liquidation Pool Target: {lp.get('upper_liq_pool', 'N/A')}
    - Lower Liquidation Pool Target: {lp.get('lower_liq_pool', 'N/A')}
    - CRT 4H High Sweep: {data['crt_sweep_high']} | CRT 4H Low Sweep: {data['crt_sweep_low']}
    - Asian Range: High={data['asia_high']}, Low={data['asia_low']}
    - Judas Swing Active: Below Asia Low={data['judas_sweep_low']}, Above Asia High={data['judas_sweep_high']}
    - Bullish FVG Active: {data['bullish_fvg']} | Bearish FVG: {data['bearish_fvg']}
    - Quasimodo (QM) Retest Level: {data['qm_level']}
    - SMT Divergence Correlation: {smt_status}

    LATEST NEWS & MACRO CONTEXT:
    {news_context}

    EVALUATION & PLAYBOOK RULES:
    1. Determine Market Bias: [BUY LEAN (Bullish xx%) / SELL LEAN (Bearish xx%) / NEUTRAL].
    2. Confluence Score (0 to 3):
       - Point 1: 4H/1H Macro Trend + 20/50/200 EMA alignment.
       - Point 2: Liquidity Sweep (CRT 4H Sweep OR Asian Range Judas Fakeout OR Liquidation Pool tap).
       - Point 3: Execution Trigger (15m FVG tap OR CVD Delta Absorption OR SMT Divergence).
    3. Classification:
       - Score 3/3 -> TIER: A+ INSTITUTIONAL (STATUS: BUY or SELL)
       - Score 2/3 -> TIER: B+ SCALP (STATUS: BUY or SELL if aligned with Bias and has FVG/EMA trigger)
       - Score < 2/3 -> TIER: WAIT (STATUS: WAIT)

    OUTPUT FORMAT (EXACTLY AS SHOWN):
    STATUS: [BUY / SELL / WAIT]
    TIER: [A+ INSTITUTIONAL / B+ SCALP / NO_TRADE]
    BIAS: [BUY LEAN (xx%) / SELL LEAN (xx%) / NEUTRAL]
    CONFLUENCE_SCORE: [x/3]
    ACTIVE_PLAYBOOK: [e.g., AMD Session Judas Sweep + Silver Bullet FVG OR CRT + CVD Absorption]
    MISSING_TRIGGER: [e.g., Awaiting Asian Low sweep at $xx,xxx OR Waiting for 15m FVG retest]
    REASONING: [1-2 concise institutional sentences explaining setup]
    ENTRY ZONE: [Price Range]
    STOP LOSS (SL): [Exact Price - Tight Invalidation]
    TAKE PROFIT 1 (TP1): [Exact Price - 50% Close & Move SL to BE]
    TAKE PROFIT 2 (TP2): [Exact Price - Liquidation Pool Target]
    ORDER FLOW MATRIX:
    - Open Interest: {deriv.get('oi_status', 'Stable')}
    - CVD Delta: {data['cvd_status']}
    - Funding Rate: {deriv.get('funding_status', 'Neutral')}
    - Whales Ratio: {deriv.get('whales_ratio', '1.0')}
    RISK SIZING NOTE: [Tier 1: Full Margin $6-$8 (3x-5x) | Tier 2: Half Margin $3-$5 (3x)]
    """

    for model_name in ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro", "gemini-1.5-pro"]:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception:
            continue
            
    return "STATUS: WAIT\nTIER: NO_TRADE\nBIAS: NEUTRAL\nCONFLUENCE_SCORE: 1/3\nACTIVE_PLAYBOOK: Range Consolidation\nMISSING_TRIGGER: Awaiting Session Displacement\nREASONING: Price consolidating inside range; waiting for killzone expansion."