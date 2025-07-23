import streamlit as st
import yfinance as yf
import pandas as pd
import ta

st.title("📈 Bullish Trade Screener - Nifty 100")

# Load Nifty 100 ticker list
nifty100 = pd.read_csv("nifty100_tickers.csv")  # assumes a CSV with tickers
bullish_stocks = []

for ticker in nifty100['Symbol']:
    data = yf.download(ticker + ".NS", period="6mo", interval="1d")
    if len(data) < 50:
        continue

    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()
    data['Volume_MA20'] = data['Volume'].rolling(window=20).mean()

    rsi = ta.momentum.RSIIndicator(data['Close']).rsi()
    macd = ta.trend.MACD(data['Close'])
    macd_line = macd.macd()
    signal_line = macd.macd_signal()

    last = data.iloc[-1]
    rsi_val = rsi.iloc[-1]
    price = last['Close']
    volume = last['Volume']
    high_52wk = data['High'].max()

    if (
        price > last['MA50'] > last['MA200'] and
        55 < rsi_val < 70 and
        macd_line.iloc[-1] > signal_line.iloc[-1] and
        volume > last['Volume_MA20'] and
        price >= 0.95 * high_52wk
    ):
        bullish_stocks.append(ticker)

st.success(f"✅ {len(bullish_stocks)} Bullish Stocks Found")
st.dataframe(pd.DataFrame(bullish_stocks, columns=["Symbol"]))
