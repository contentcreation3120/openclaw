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
    "AI","ML","GPU","CPU","RAM","LLM",
    "VWAP","MACD","OCO","OSO","TP","SL","EOD","ET","AM","PM","NY","VA",
    "OK","VS","RE","HR","PL","EU","UK","AU","CA","DAY","BUY","SELL",
    "GET","SET","ALL","NEW","NOW","OUT","OWN","HOW","WHY","PUT","ASK","ADD",
    "AUTO","ANALYSIS","SWING","TRADE","ENTRY","STOP","SIGNAL","PLAN","CODE",
    "BULL","BEAR","LONG","SHORT","CALL","PUT","OTM","ITM","ATM","DTE",
    "HIGH","LOW","OPEN","CLOSE","HOLD","RISK","GAIN","LOSS","NET","TAM",
    "FULL","CASE","BASE","NOTE","BIAS","MOAT","TERM","TYPE","FORM","RATE",
    "KEY","TOP","FIT","MAP","CAP","WAY","FEE","TAX","USE","ACT","AIM",
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
        headlines = []
        for item in news[:n]:
            # yfinance returns dicts or nested content objects
            title = (
                item.get("title")
                or item.get("headline")
                or (item.get("content") or {}).get("title")
                or ""
            )
            if title:
                headlines.append(title)
        return headlines
    except Exception as e:
        logger.warning(f"news: {symbol} failed — {e}")
        return []


def fetch_insider_trades(symbol: str, n: int = 8) -> list[dict]:
    """Fetch recent insider buy/sell transactions."""
    try:
        tk = yf.Ticker(symbol)
        df = tk.insider_transactions
        if df is None or df.empty:
            return []
        result = []
        for _, row in df.head(n).iterrows():
            txn = str(row.get("Transaction", "") or "").upper()
            action = "BUY" if any(w in txn for w in ("BUY","PURCHASE","ACQUISITION")) else "SELL"
            shares = row.get("Shares", 0) or 0
            value  = row.get("Value", 0) or 0
            result.append({
                "date":    str(row.get("Start Date", ""))[:10],
                "insider": str(row.get("Insider", row.get("Filer Name", "Unknown"))),
                "title":   str(row.get("Position", row.get("Filer Relation", ""))),
                "action":  action,
                "shares":  int(shares),
                "value":   int(value),
            })
        return result
    except Exception as e:
        logger.warning(f"insider_trades: {symbol} failed — {e}")
        return []


def fetch_institutional_holders(symbol: str, n: int = 5) -> list[dict]:
    """Fetch top institutional holders."""
    try:
        tk = yf.Ticker(symbol)
        df = tk.institutional_holders
        if df is None or df.empty:
            return []
        result = []
        for _, row in df.head(n).iterrows():
            pct = float(row.get("pctHeld", row.get("% Out", 0)) or 0)
            result.append({
                "holder": str(row.get("Holder", "")),
                "shares": int(row.get("Shares", 0) or 0),
                "value":  int(row.get("Value",  0) or 0),
                "pct":    round(pct * 100, 2),   # pctHeld is decimal: 0.0737 → 7.37%
            })
        return result
    except Exception as e:
        logger.warning(f"institutional_holders: {symbol} failed — {e}")
        return []


def detect_chart_patterns(symbol: str) -> dict:
    """Detect trend, MA position, candle pattern, bias from 3mo daily OHLC."""
    try:
        tk   = yf.Ticker(symbol)
        hist = tk.history(period="3mo", interval="1d")
        if hist.empty or len(hist) < 10:
            return {}

        closes = hist["Close"].values
        highs  = hist["High"].values
        lows   = hist["Low"].values
        opens  = hist["Open"].values
        n      = len(closes)

        # Trend (last 20 candles)
        c20 = closes[-min(20,n):]
        if c20[-1] > c20[0] * 1.08:
            trend = "Strong Uptrend"
        elif c20[-1] > c20[0] * 1.02:
            trend = "Uptrend"
        elif c20[-1] < c20[0] * 0.92:
            trend = "Strong Downtrend"
        elif c20[-1] < c20[0] * 0.98:
            trend = "Downtrend"
        else:
            trend = "Sideways / Consolidation"

        # Moving averages
        ma20  = round(float(sum(closes[-min(20,n):]) / min(20,n)), 2)
        ma50  = round(float(sum(closes[-min(50,n):]) / min(50,n)), 2) if n >= 30 else None
        ma200 = round(float(sum(closes[-min(200,n):]) / min(200,n)), 2) if n >= 100 else None

        # Last candle pattern
        o, c, h, l = opens[-1], closes[-1], highs[-1], lows[-1]
        body  = abs(c - o)
        rng   = h - l or 0.0001
        upper = h - max(o, c)
        lower = min(o, c) - l

        if body < rng * 0.1:
            candle = "Doji (indecision)"
        elif c > o and lower > body * 2 and upper < body:
            candle = "Hammer (bullish reversal)"
        elif c < o and upper > body * 2 and lower < body:
            candle = "Shooting Star (bearish reversal)"
        elif c > o and body > rng * 0.7:
            candle = "Strong Bullish Engulfing"
        elif c < o and body > rng * 0.7:
            candle = "Strong Bearish Engulfing"
        else:
            candle = "Mixed / No clear pattern"

        # Bias scoring
        bull = 0
        bear = 0
        if closes[-1] > ma20: bull += 1
        else: bear += 1
        if ma50  and closes[-1] > ma50:  bull += 1
        elif ma50:  bear += 1
        if ma200 and closes[-1] > ma200: bull += 2
        elif ma200: bear += 2
        if trend in ("Uptrend", "Strong Uptrend"):   bull += 2
        elif trend in ("Downtrend", "Strong Downtrend"): bear += 2

        # Higher highs / higher lows check (last 10 candles)
        if n >= 10:
            mid = n // 2
            if highs[-5:].max() > highs[-10:-5].max() and lows[-5:].min() > lows[-10:-5].min():
                bull += 1
            elif highs[-5:].max() < highs[-10:-5].max() and lows[-5:].min() < lows[-10:-5].min():
                bear += 1

        bias = "LONG" if bull > bear else ("SHORT" if bear > bull else "NEUTRAL")

        return {
            "trend":         trend,
            "bias":          bias,
            "bull_signals":  bull,
            "bear_signals":  bear,
            "candle_pattern": candle,
            "ma20":          ma20,
            "ma50":          ma50,
            "ma200":         ma200,
            "recent_high":   round(float(highs[-10:].max()), 2),
            "recent_low":    round(float(lows[-10:].min()),  2),
        }
    except Exception as e:
        logger.warning(f"patterns: {symbol} failed — {e}")
        return {}


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

        if task_type == "research" and not is_futures(sym):
            # Chart patterns
            pat = detect_chart_patterns(sym)
            if pat:
                block += (
                    f"  --- Chart Patterns ---\n"
                    f"  Trend     : {pat['trend']}\n"
                    f"  Bias      : {pat['bias']} (bull signals: {pat['bull_signals']}, bear: {pat['bear_signals']})\n"
                    f"  Last candle: {pat['candle_pattern']}\n"
                    f"  MA20: ${pat['ma20']} | MA50: ${pat.get('ma50','N/A')} | MA200: ${pat.get('ma200','N/A')}\n"
                    f"  Recent 10d High: ${pat['recent_high']} | Low: ${pat['recent_low']}\n"
                )
            # Insider trades
            insiders = fetch_insider_trades(sym, 6)
            if insiders:
                block += "  --- Insider Transactions (recent) ---\n"
                for t in insiders:
                    val_str = f"${t['value']:,}" if t['value'] else "N/A"
                    block += f"  {t['action']:4s} | {t['date']} | {t['insider']} ({t['title']}) | {t['shares']:,} shares | {val_str}\n"
            # Institutional holders
            insts = fetch_institutional_holders(sym, 5)
            if insts:
                block += "  --- Top Institutional Holders ---\n"
                for h in insts:
                    val_str = f"${h['value']/1e6:.0f}M" if h['value'] else "N/A"
                    block += f"  {h['holder'][:35]:<35} {h['pct']:.2f}%  {val_str}\n"

        blocks.append(block)

    if not blocks:
        return ""

    return "--- Live market data (fetched now) ---\n" + "\n".join(blocks) + "\n---\n\n"
