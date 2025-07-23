import yfinance as yf
import pandas as pd
import ta
import requests
from io import StringIO
from datetime import datetime, timedelta

# === 1. Dynamic Date Range === #
end_date = datetime.today()
start_date = end_date - timedelta(days=4 * 365)  # ~4 years

# === 2. Fetch Nifty 100 Stocks from NSE === #
def get_nifty100_tickers():
    try:
        url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.niftyindices.com/"
        }
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        return df['Symbol'].str.strip().tolist()
    except Exception as e:
        print("❌ Error fetching Nifty 100 tickers:", e)
        return []

tickers = [symbol + ".NS" for symbol in get_nifty100_tickers()]
results = []

# === 3. Backtest Logic === #
def backtest(ticker):
    try:
        df = yf.download(ticker, start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"), progress=False)
        if df.empty or len(df) < 200:
            return

        df['MA50'] = df['Close'].rolling(50).mean()
        df['MA200'] = df['Close'].rolling(200).mean()
        df['Volume_MA20'] = df['Volume'].rolling(20).mean()
        df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['52W_High'] = df['High'].rolling(252).max()

        in_trade = False
        entry_date = entry_price = None

        for i in range(200, len(df)):
            row = df.iloc[i]

            # Entry condition
            if not in_trade and (
                row['Close'] > row['MA50'] > row['MA200'] and
                55 < row['RSI'] < 70 and
                row['MACD'] > row['MACD_signal'] and
                row['Volume'] > row['Volume_MA20'] and
                row['Close'] >= 0.95 * row['52W_High']
            ):
                in_trade = True
                entry_date = row.name
                entry_price = row['Close']

            # Exit condition
            elif in_trade and (
                row['RSI'] < 50 or
                row['MACD'] < row['MACD_signal'] or
                row['Close'] < row['MA50']
            ):
                exit_date = row.name
                exit_price = row['Close']
                pct_return = ((exit_price - entry_price) / entry_price) * 100
                holding_days = (exit_date - entry_date).days

                results.append({
                    "Stock": ticker.replace(".NS", ""),
                    "Entry Date": entry_date.date(),
                    "Entry Price": round(entry_price, 2),
                    "Exit Date": exit_date.date(),
                    "Exit Price": round(exit_price, 2),
                    "% Return": round(pct_return, 2),
                    "Holding Days": holding_days
                })
                in_trade = False
    except Exception as e:
        print(f"⚠️ {ticker} - Error: {e}")

# === 4. Run Backtest for All Tickers === #
print(f"\n🔁 Backtesting {len(tickers)} stocks from {start_date.date()} to {end_date.date()}...\n")
for t in tickers:
    print(f"→ Running for: {t}")
    backtest(t)

# === 5. Export Results === #
df_results = pd.DataFrame(results)

if not df_results.empty:
    df_results.sort_values(by="Entry Date", inplace=True)
    df_results.to_csv("nifty100_bullish_trades_backtest.csv", index=False)
    print("\n✅ Backtest Completed. Top 10 Trades:\n")
    print(df_results.head(10))
else:
    print("\n⚠️ No bullish trades found based on current strategy logic and data.")
