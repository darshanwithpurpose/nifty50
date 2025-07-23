import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import requests
from io import StringIO

st.set_page_config(page_title="Nifty 100 Bullish Screener", layout="wide")
st.title("📈 Nifty 100 Bullish Trade Screener")

# ---- Function to Fetch Nifty 100 Tickers from NSE ---- #
@st.cache_data
def get_nifty100_tickers():
    try:
        url = "https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv"
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.niftyindices.com/"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        df = pd.read_csv(StringIO(response.text))
        return df['Symbol'].str.strip().tolist()
    except Exception as e:
        st.error("❌ Failed to fetch Nifty 100 tickers from NSE.")
        return []

# ---- Fetch and Process Stocks ---- #
nifty100 = get_nifty100_tickers()
if not nifty100:
    st.stop()

selected_stocks = []
progress_bar = st.progress(0)

for i, ticker in enumerate(nifty100):
    progress_bar.progress((i + 1) / len(nifty100))

    symbol = ticker + ".NS"
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        if df.empty or len(df) < 200:
            continue

        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['MA200'] = df['Close'].rolling(window=200).mean()
        df['Volume_MA20'] = df['Volume'].rolling(window=20).mean()
        df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()

        last = df.iloc[-1]
        high_52wk = df['High'].max()

        # ---- Bullish Criteria ---- #
        if (
            last['Close'] > last['MA50'] > last['MA200'] and
            55 < last['RSI'] < 70 and
            last['MACD'] > last['MACD_signal'] and
            last['Volume'] > last['Volume_MA20'] and
            last['Close'] >= 0.95 * high_52wk
        ):
            selected_stocks.append({
                "Symbol": ticker,
                "Close Price": round(last['Close'], 2),
                "RSI(14)": round(last['RSI'], 2),
                "Volume": int(last['Volume']),
                "52-Week High": round(high_52wk, 2)
            })
    except Exception:
        continue

progress_bar.empty()

# ---- Show Results ---- #
st.subheader("🔍 Bullish Candidates from Nifty 100")
if selected_stocks:
    st.dataframe(pd.DataFrame(selected_stocks))
    st.success(f"✅ {len(selected_stocks)} bullish stock(s) found.")
else:
    st.warning("⚠️ No bullish setups found based on the current logic.")

st.caption("Logic: Price > MA50 > MA200 • RSI(14) between 55–70 • MACD Bullish Crossover • Volume > 20-day average • Close near 52W High")
