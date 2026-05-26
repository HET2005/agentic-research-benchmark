import json
import yfinance as yf
from typing import Optional

def yf_search(query: str, period: str = "1mo") -> str:
    ticker_str = _resolve_ticker(query)
    if not ticker_str:
        return json.dumps({"error": f"Could not resolve ticker: {query}"})
    try:
        ticker = yf.Ticker(ticker_str)
        info = ticker.info or {}
        hist = ticker.history(period=period)
        if hist.empty:
            return json.dumps({"error": f"No history for {ticker_str}"})
        records = []
        for date, row in hist.tail(10).iterrows():
            records.append({"date": str(date.date()), "close": round(float(row["Close"]), 4), "volume": int(row["Volume"])})
        return json.dumps({
            "ticker": ticker_str,
            "company_name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", "N/A"),
            "52w_low": info.get("fiftyTwoWeekLow", "N/A"),
            "description": (info.get("longBusinessSummary","") or "")[:400],
            "price_history": records,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "ticker": ticker_str})

def _resolve_ticker(query: str) -> Optional[str]:
    q = query.strip().upper()
    if q and len(q) <= 8 and q.replace(".", "").replace("-", "").replace("=", "").replace("^", "").isalnum():
        return q
    try:
        results = yf.Search(query, max_results=1)
        quotes = results.quotes
        if quotes:
            return quotes[0].get("symbol", None)
    except Exception:
        pass
    return None