"""Quick smoke test — run before launching web UI."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openclaw.market_data import extract_tickers, fetch_quote, fetch_fundamentals, fetch_news, build_market_context
from openclaw.router.classifier import classify

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))
        FAIL += 1

print("\n=== OPENCLAW SMOKE TEST ===\n")

# Ticker detection
t = extract_tickers("mstr strategy")
check("lowercase ticker detected", "MSTR" in t, str(t))

t = extract_tickers("MNQ day trade")
check("futures ticker detected", "MNQ" in t, str(t))

t = extract_tickers("RSI VWAP MACD")
check("indicator words filtered", len(t) == 0, str(t))

# Live quote
q = fetch_quote("MSTR")
check("MSTR quote fetched", q is not None and q.get("price") is not None)
if q:
    print(f"         MSTR: ${q['price']} | change: {q.get('change_pct',0):+.2f}% | RSI: {q.get('rsi_14')}")

# Fundamentals
f = fetch_fundamentals("MSTR")
check("MSTR fundamentals fetched", f is not None and f.get("market_cap") not in (None, "N/A"))
if f:
    print(f"         {f['name']} | {f['market_cap']} | P/E: {f['pe_ratio']} | {f['analyst_rating']}")

# News
news = fetch_news("MSTR", 3)
check("MSTR news fetched", len(news) > 0)
for h in news[:3]:
    print(f"         - {h[:90]}")

# Build context (research)
ctx = build_market_context("research MSTR", task_type="research")
check("build_market_context includes fundamentals", "Fundamentals" in ctx or "Analyst" in ctx, ctx[:100])

# Classifier
d = classify("swing trade MSTR")
check("swing trade -> trading", d.task_type == "trading", d.task_type)

d = classify("debug this Python error")
check("debug -> code", d.task_type == "code", d.task_type)

d = classify("plan my trading day")
check("plan -> planning", d.task_type == "planning", d.task_type)

d = classify("session recap 3W 2L")
check("recap -> journal", d.task_type == "journal", d.task_type)

# Auto analysis route
d = classify("auto analysis MSTR")
print(f"         auto analysis classified as: {d.task_type}")

print(f"\n=== {PASS} passed, {FAIL} failed ===\n")
sys.exit(0 if FAIL == 0 else 1)
