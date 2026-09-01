import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from market_engine import analyze_technical_models, check_smt_divergence
from news_engine import get_latest_market_news
from ai_brain import evaluate_setup_with_ai
from telegram_notifier import send_alert

WATCHLIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "GOLD_MT5"]

# Tiny Cloud Health Server (Keeps Cloud Server Active 24/7)
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Sahan's Pro Crypto AI Agent is Running 24/7!")
    def log_message(self, format, *args):
        return

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()

def parse_ai_field(text, field_name, default="N/A"):
    for line in text.split("\n"):
        if line.startswith(f"{field_name}:"):
            return line.replace(f"{field_name}:", "").strip()
    return default

def run_pro_scanner():
    print("\n" + "=" * 70)
    print("🤖 Sahan's Pro Institutional Crypto & Gold AI Agent Running...")
    print("=" * 70)
    
    print("[*] Scanning Global Macro News & Sentiment...")
    news_data = get_latest_market_news()
    
    print("[*] Evaluating SMT Divergence ($BTC vs $ETH)...")
    smt_data = check_smt_divergence()
    
    for symbol in WATCHLIST:
        try:
            tech_data = analyze_technical_models(symbol)
            display_sym = tech_data.get("symbol", symbol)
            price = tech_data.get("current_price", 0.0)
            
            ai_verdict = evaluate_setup_with_ai(tech_data, smt_data, news_data)
            
            status = parse_ai_field(ai_verdict, "STATUS", "WAIT")
            tier = parse_ai_field(ai_verdict, "TIER", "NO_TRADE")
            bias = parse_ai_field(ai_verdict, "BIAS", "NEUTRAL")
            score = parse_ai_field(ai_verdict, "CONFLUENCE_SCORE", "0/3")
            playbook = parse_ai_field(ai_verdict, "ACTIVE_PLAYBOOK", "Consolidation")
            missing = parse_ai_field(ai_verdict, "MISSING_TRIGGER", "Awaiting confirmation")
            reasoning = parse_ai_field(ai_verdict, "REASONING", "Market in range")
            
            # Print Live Structured Dashboard
            print(f"\n📊 [{display_sym}] Current Price: ${price}")
            print(f"   ├─ Market Bias      : {bias}")
            print(f"   ├─ Confluence Score : {score} ({tier})")
            print(f"   ├─ Active Playbook  : {playbook}")
            print(f"   ├─ Missing Trigger  : {missing}")
            print(f"   └─ AI Analysis      : {reasoning}")
            
            # Smart Trigger: Alert on A+ (3/3) or B+ Scalp (2/3)
            is_valid_signal = ("BUY" in status.upper() or "SELL" in status.upper()) or ("2/3" in score or "3/3" in score)
            
            if is_valid_signal and ("NEUTRAL" not in bias.upper() and "0/3" not in score):
                tier_badge = "🌟 [TIER 1: A+ INSTITUTIONAL SETUP]" if "3/3" in score or "A+" in tier.upper() else "⚡ [TIER 2: B+ INTRADAY SCALP]"
                action_badge = "🟢 BUY (LONG)" if "BUY" in bias.upper() else "🔴 SELL (SHORT)"
                
                formatted_message = f"{tier_badge}\n🎯 *PRO SIGNAL: {display_sym}*\n*Action*: {action_badge}\n*Score*: {score}\n\n{ai_verdict}"
                
                print(f"\n[🔥] {tier_badge} TRIGGERED FOR {display_sym}! Sending Telegram Alert...")
                send_alert(formatted_message)
                
        except Exception as e:
            print(f"[!] Error analyzing {symbol}: {e}")
            
    print("\n" + "-" * 70)
    print("[✓] Cycle complete. Continuous scan active (Interval: 15 mins)...")
    print("-" * 70)

if __name__ == "__main__":
    # Start Cloud Health Server in background thread
    threading.Thread(target=start_health_server, daemon=True).start()
    
    # Start Scanner Loop
    run_pro_scanner()
    while True:
        time.sleep(900)
        run_pro_scanner()