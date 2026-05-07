import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yfinance as yf

tk = yf.Ticker("MSTR")

print("=== insider_transactions columns ===")
df = tk.insider_transactions
if df is not None and not df.empty:
    print(df.columns.tolist())
    print(df.head(2).to_string())
else:
    print("Empty")

print("\n=== institutional_holders columns ===")
df2 = tk.institutional_holders
if df2 is not None and not df2.empty:
    print(df2.columns.tolist())
    print(df2.head(3).to_string())
else:
    print("Empty")
