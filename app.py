import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Simple Swing Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📈 NIFTY Universe Swing Scanner")
st.caption("Simple trend-following scanner for probable swing candidates")

# =====================================================
# NIFTY BROAD UNIVERSE
# =====================================================

NIFTY_UNIVERSE = [

    # BANKS
    "HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS","KOTAKBANK.NS",

    # IT
    "TCS.NS","INFY.NS","HCLTECH.NS","TECHM.NS","WIPRO.NS","LTIM.NS",

    # AUTO
    "MARUTI.NS","TATAMOTORS.NS","M&M.NS","BAJAJ-AUTO.NS","EICHERMOT.NS",

    # CAPITAL GOODS
    "SIEMENS.NS","ABB.NS","CGPOWER.NS","POLYCAB.NS","KEI.NS","APLAPOLLO.NS",

    # DEFENCE
    "HAL.NS","BEL.NS","BDL.NS","BHEL.NS",

    # PHARMA
    "SUNPHARMA.NS","CIPLA.NS","DIVISLAB.NS","TORNTPHARM.NS",

    # CONSUMPTION
    "ITC.NS","HINDUNILVR.NS","NESTLEIND.NS","VBL.NS","TRENT.NS",

    # FINANCIALS
    "BAJFINANCE.NS","CHOLAFIN.NS","SHRIRAMFIN.NS","MUTHOOTFIN.NS",

    # THEMATIC
    "DIXON.NS","KAYNES.NS","KPITTECH.NS","PERSISTENT.NS","COFORGE.NS",

    # ENERGY
    "RELIANCE.NS","NTPC.NS","POWERGRID.NS","TATAPOWER.NS","JSWENERGY.NS",

    # REAL ESTATE
    "DLF.NS","LODHA.NS","OBEROIRLTY.NS"
]

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Scanner Settings")

top_n = st.sidebar.slider(
    "Top Candidates",
    5,
    30,
    15
)

# =====================================================
# DATA FETCH
# =====================================================

@st.cache_data(ttl=3600)
def fetch_data(tickers):

    end = datetime.now()
    start = end - timedelta(days=400)

    data = yf.download(
        tickers,
        start=start,
        end=end,
        group_by='ticker',
        auto_adjust=True,
        progress=False,
        threads=True
    )

    return data

# =====================================================
# ANALYSIS FUNCTION
# =====================================================

def analyze_stock(df, ticker):

    try:

        if len(df) < 200:
            return None

        close = df["Close"]
        volume = df["Volume"]

        current_price = close.iloc[-1]

        sma50 = close.rolling(50).mean().iloc[-1]
        sma200 = close.rolling(200).mean().iloc[-1]

        avg_volume = volume.iloc[-20:].mean()

        # =====================================
        # BASIC LIQUIDITY FILTER
        # =====================================

        if avg_volume < 200000:
            return None

        # =====================================
        # MOMENTUM
        # =====================================

        return_3m = (
            (close.iloc[-1] / close.iloc[-60]) - 1
        ) * 100

        # =====================================
        # DISTANCE FROM 50 DMA
        # =====================================

        distance_50 = (
            (current_price - sma50) / sma50
        ) * 100

        # =====================================
        # SCORE
        # =====================================

        score = 0

        # Trend structure
        if current_price > sma50:
            score += 25

        if sma50 > sma200:
            score += 25

        # Momentum
        if return_3m > 10:
            score += 25

        if return_3m > 20:
            score += 15

        # Avoid overextended stocks
        if distance_50 < 20:
            score += 10

        return {
            "Ticker": ticker,
            "Price": round(current_price, 2),
            "3M Return %": round(return_3m, 2),
            "Distance From 50DMA %": round(distance_50, 2),
            "Score": score
        }

    except:
        return None

# =====================================================
# RUN SCANNER
# =====================================================

if st.button("🚀 Run Scanner", type="primary"):

    with st.spinner("Scanning NIFTY universe..."):

        market_data = fetch_data(NIFTY_UNIVERSE)

        results = []

        progress = st.progress(0)

        for idx, ticker in enumerate(NIFTY_UNIVERSE):

            try:

                df = market_data[ticker]

                result = analyze_stock(df, ticker)

                if result:
                    results.append(result)

            except:
                pass

            progress.progress((idx + 1) / len(NIFTY_UNIVERSE))

        progress.empty()

    # =================================================
    # RESULTS
    # =================================================

    if len(results) == 0:

        st.warning("No candidates found.")

    else:

        results_df = pd.DataFrame(results)

        results_df = results_df.sort_values(
            by="Score",
            ascending=False
        )

        results_df = results_df.head(top_n)

        st.success(f"Found {len(results_df)} probable swing candidates.")

        st.dataframe(
            results_df,
            use_container_width=True
        )

        # =============================================
        # CHART VIEWER
        # =============================================

        st.markdown("---")

        selected_stock = st.selectbox(
            "Select Stock",
            results_df["Ticker"]
        )

        chart_df = market_data[selected_stock].copy()

        chart_df["50DMA"] = chart_df["Close"].rolling(50).mean()
        chart_df["200DMA"] = chart_df["Close"].rolling(200).mean()

        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=chart_df.index,
                open=chart_df["Open"],
                high=chart_df["High"],
                low=chart_df["Low"],
                close=chart_df["Close"],
                name="Price"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df["50DMA"],
                name="50 DMA"
            )
        )

        fig.add_trace(
            go.Scatter(
                x=chart_df.index,
                y=chart_df["200DMA"],
                name="200 DMA"
            )
        )

        fig.update_layout(
            height=650,
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            title=f"{selected_stock} Structure"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )
