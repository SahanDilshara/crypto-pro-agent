import requests

def get_latest_market_news():
    """Fetches real-time crypto headlines and macro updates."""
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
        response = requests.get(url, timeout=5).json()
        articles = response.get("Data", [])[:5]
        
        news_summary = []
        for a in articles:
            news_summary.append(f"- {a['title']} (Source: {a['source']})")
            
        return "\n".join(news_summary) if news_summary else "Market news feed is normal."
    except Exception:
        return "Macro News Feed currently quiet."