"""
Fetches live price, technicals, fundamentals, and news for any ticker via yfinance.
Injected into the prompt automatically when a ticker is detected.
"""
import re
from datetime import datetime
import yfinance as yf
from loguru import logger

_TICKER_RE = re.compile(r'\b([A-Z]{1,5})\b')

FUTURES_SYMBOLS = {
    "MNQ","NQ","ES","YM","RTY","CL","GC","SI","HG","NG","ZB","ZN","ZF","ZT",
    "MNQM5","NQM5","ESM5","YMM5","RTYM5",
}

_COMMON_WORDS = {
    "I","A","AT","OR","IN","ON","BE","IS","AM","DO","IF","MY","ME","UP","GO",
    "BY","US","IT","NO","SO","AS","HE","WE","TO","OF","AN","THE","AND","FOR",
    "RSI","EMA","SMA","ATR","IV","DTE","ETF","IPO","CEO","CFO","API","SQL",
    "AI","ML","GPU","CPU","RAM","LLM","MNQ","NQ","ES","YM","RTY","CL","GC",
    "VWAP","MACD","OCO","OSO","TP","SL","EOD","ET","AM","PM","NY","VA",
    "OK","VS","RE","HR","PL","US","EU","UK","AU","CA","DAY","BUY","SELL",
    "GET","SET","ALL","NEW","NOW","OUT","OWN","HOW","WHY","PUT","ASK","ADD",
}


def is_futures(symbol: str) -> bool:
    return symbol.upper() in FUTURES_SYMBOLS


def extract_tickers(text: str) -> list[str]:
    candidates = _TICKER_RE.findall(text.upper())
    return [t for t in candidates if t not in _COMMON_WORDS and len(t) >= 2]


def _rsi(closes, period=14) -> float:
    deltas = [closes.iloc[i] - closes.iloc[i-1] for i in range(1, len(closes))]
    gains  = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))


def _next_earnings(tk) -> str | None:
    try:
        dates = tk.earnings_dates
        if dates is None or dates.empty:
            return None
        future = [d for d in dates.index if d.to_pydatetime().replace(tzinfo=None) > datetime.now()]
        return future[0].strftime("%Y-%m-%d") if future else None
    except Exception:
        return None


def fetch_quote(symbol: str) -> dict | None:
    try:
        tk = yf.Ticker(symbol)
        info = tk.fast_info
        hist = tk.history(period="5d", interval="1d")
        if hist.empty or info.last_price is None:
            return None

        price      = round(float(info.last_price), 2)
        prev_close = round(float(info.previous_close), 2) if info.previous_close else None
        day_high   = round(float(info.day_high), 2)  if info.day_high  else None
        day_low    = round(float(info.day_low),  2)  if info.day_low   else None
        volume     = int(info.last_volume) if info.last_volume else None
        chg        = round(price - prev_close, 2) if prev_close else None
        chg_pct    = round(chg / prev_close * 100, 2) if (chg and prev_close) else None

        hist_rsi = tk.history(period="3mo", interval="1d")["Close"].dropna()
        rsi = _rsi(hist_rsi, 14) if len(hist_rsi) >= 15 else None

        return {
            "symbol":     symbol,
            "price":      price,
            "change":     chg,
            "change_pct": chg_pct,
            "day_high":   day_high,
            "day_low":    day_low,
            "prev_close": prev_close,
            "volume":     volume,
            "rsi_14":     round(rsi, 1) if rsi else None,
        }
    except Exception as e:
        logger.warning(f"market_data: {symbol} fetch failed — {e}")
        return None


def fetch_fundamentals(symbol: str) -> dict | None:
    try:
        tk  = yf.Ticker(symbol)
        inf = tk.info
        if not inf or inf.get("quoteType") == "FUTURE":
            return None

        mcap = inf.get("marketCap")
        mcap_str = (
            f"${mcap/1e12:.2f}T" if mcap and mcap >= 1e12 else
            f"${mcap/1e9:.2f}B"  if mcap and mcap >= 1e9  else
            f"${mcap/1e6:.0f}M"  if mcap else "N/A"
        )
        rev = inf.get("totalRevenue")
        rev_str = (
            f"${rev/1e9:.2f}B" if rev and rev >= 1e9 else
            f"${rev/1e6:.0f}M" if rev else "N/A"
        )
        margin = inf.get("profitMargins")

        return {
            "name":            inf.get("longName") or inf.get("shortName", symbol),
            "sector":          inf.get("sector", "N/A"),
            "industry":        inf.get("industry", "N/A"),
            "market_cap":      mcap_str,
            "pe_ratio":        round(inf.get("trailingPE"), 1) if inf.get("trailingPE") else "N/A",
            "eps":             inf.get("trailingEps", "N/A"),
            "revenue":         rev_str,
            "profit_margin":   f"{margin*100:.1f}%" if margin else "N/A",
            "week52_high":     inf.get("fiftyTwoWeekHigh"),
            "week52_low":      inf.get("fiftyTwoWeekLow"),
            "analyst_target":  inf.get("targetMeanPrice"),
            "analyst_rating":  (inf.get("recommendationKey") or "N/A").upper(),
            "earnings_date":   _next_earnings(tk),
            "beta":            round(inf.get("beta"), 2) if inf.get("beta") else "N/A",
            "short_float":     f"{inf.get('shortPercentOfFloat',0)*100:.1f}%" if inf.get("shortPercentOfFloat") else "N/A",
        }
    except Exception as e:
        logger.warning(f"fundamentals: {symbol} failed — {e}")
        return None


def fetch_news(symbol: str, n: int = 5) -> list[str]:
    try:
        tk   = yf.Ticker(symbol)
        news = tk.news or []
        return [item.get("title", "") for item in news[:n] if item.get("title")]
    except Exception as e:
        logger.warning(f"news: {symbol} failed — {e}")
        return []


def build_market_context(text: str, task_type: str = None) -> str:
    tickers = extract_tickers(text)
    if not tickers:
        return ""

    deep = task_type in ("research", "trading_stocks", "trading", "auto_analysis")
    blocks = []

    for sym in tickers[:3]:
        q = fetch_quote(sym)
        if not q:
            continue

        chg_str = (
            f"{q['change']:+.2f} ({q['change_pct']:+.2f}%)"
            if q["change"] is not None else "N/A"
        )
        rsi_str = str(q["rsi_14"]) if q["rsi_14"] else "N/A"

        block = (
            f"[LIVE DATA — {q['symbol']}]\n"
            f"  Price     : ${q['price']}  {chg_str}\n"
            f"  Day range : ${q['day_low']} – ${q['day_high']}\n"
            f"  Volume    : {q['volume']:,}\n"
            f"  RSI (14d) : {rsi_str}\n"
        )

        if deep and not is_futures(sym):
            f_ = fetch_fundamentals(sym)
            if f_:
                block += (
                    f"  --- Fundamentals ---\n"
                    f"  Company   : {f_['name']}\n"
                    f"  Sector    : {f_['sector']} / {f_['industry']}\n"
                    f"  Mkt Cap   : {f_['market_cap']}  |  P/E: {f_['pe_ratio']}  |  EPS: {f_['eps']}\n"
                    f"  Revenue   : {f_['revenue']}  |  Margin: {f_['profit_margin']}\n"
                    f"  52w High  : ${f_['week52_high']}  |  52w Low: ${f_['week52_low']}\n"
                    f"  Analyst   : {f_['analyst_rating']}  |  Target: ${f_['analyst_target']}\n"
                    f"  Earnings  : {f_['earnings_date'] or 'N/A'}\n"
                    f"  Beta      : {f_['beta']}  |  Short float: {f_['short_float']}\n"
                )
            news = fetch_news(sym, 5)
            if news:
                block += "  --- Recent News ---\n"
                for h in news:
                    block += f"  • {h}\n"

        blocks.append(block)

    if not blocks:
        return ""

    return "--- Live market data (fetched now) ---\n" + "\n".join(blocks) + "\n---\n\n"
