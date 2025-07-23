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
