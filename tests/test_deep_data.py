"""Test the new deep data fetchers: patterns, insider trades, institutional holders."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openclaw.market_data import (
    build_market_context, detect_chart_patterns,
    fetch_insider_trades, fetch_institutional_holders
)

PASS = FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name}" + (f" -- {detail}" if detail else ""))
        FAIL += 1

print("\n=== DEEP DATA TEST (MSTR) ===\n")

# Chart patterns
print("--- Chart Patterns ---")
p = detect_chart_patterns("MSTR")
for k, v in p.items():
    print(f"  {k}: {v}")
check("patterns returned", bool(p))
check("bias in result", p.get("bias") in ("LONG","SHORT","NEUTRAL"))
check("trend in result", bool(p.get("trend")))
check("candle pattern in result", bool(p.get("candle_pattern")))
print()

# Insider trades
print("--- Insider Trades ---")
ins = fetch_insider_trades("MSTR", 5)
for t in ins:
    print(f"  {t['action']} | {t['date']} | {t['insider'][:30]} | {t['shares']:,} shares")
check("insider trades fetched", len(ins) > 0)
print()

# Institutional holders
print("--- Institutional Holders ---")
inst = fetch_institutional_holders("MSTR", 5)
for h in inst:
    val = f"${h['value']/1e6:.0f}M" if h['value'] else "N/A"
    print(f"  {h['holder'][:40]:<40} {h['pct']:.2f}%  {val}")
check("institutional holders fetched", len(inst) > 0)
print()

# Full research context
print("--- Research Context (first 1000 chars) ---")
ctx = build_market_context("research MSTR", task_type="research")
print(ctx[:1000])
check("context has fundamentals", "Fundamentals" in ctx)
check("context has patterns", "Chart Patterns" in ctx or "Patterns" in ctx)
check("context has insiders", "Insider" in ctx)
check("context has institutions", "Institutional" in ctx)

print(f"\n=== {PASS} passed, {FAIL} failed ===\n")
sys.exit(0 if FAIL == 0 else 1)
