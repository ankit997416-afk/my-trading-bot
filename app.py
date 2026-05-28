import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Institutional Swing Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Institutional-Grade Swing Trading Scanner")
st.caption("Focus: High-quality trends, relative strength, accumulation & controlled volatility")

# =========================================================
# PRESETS
# =========================================================

TICKER_PRESETS = {

    "Institutional India Universe": [

        # =========================
        # LARGE CAPS
        # =========================

        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "AXISBANK.NS",
        "KOTAKBANK.NS",
        "LT.NS",
        "ITC.NS",
        "BHARTIARTL.NS",
        "ASIANPAINT.NS",
        "ULTRACEMCO.NS",
        "MARUTI.NS",
        "TITAN.NS",
        "SUNPHARMA.NS",
        "BAJFINANCE.NS",
        "HCLTECH.NS",
        "TECHM.NS",
        "POWERGRID.NS",

        # =========================
        # STRONG MIDCAPS
        # =========================

        "POLYCAB.NS",
        "DIXON.NS",
        "PERSISTENT.NS",
        "COFORGE.NS",
        "BSE.NS",
        "CDSL.NS",
        "INDHOTEL.NS",
        "ABB.NS",
        "SIEMENS.NS",
        "CUMMINSIND.NS",
        "SCHAEFFLER.NS",
        "SUPREMEIND.NS",
        "ASTRAL.NS",
        "APLAPOLLO.NS",
        "KEI.NS",
        "HAVELLS.NS",
        "LODHA.NS",
        "OBEROIRLTY.NS",
        "MAXHEALTH.NS",
        "FORTIS.NS",

        # =========================
        # CAPITAL GOODS / DEFENCE
        # =========================

        "BEL.NS",
        "HAL.NS",
        "BDL.NS",
        "BHEL.NS",
        "CGPOWER.NS",
        "KPITTECH.NS",
        "SKFINDIA.NS",

        # =========================
        # CONSUMPTION / RETAIL
        # =========================

        "TRENT.NS",
        "DMART.NS",
        "VBL.NS",
        "RADICO.NS",
        "EMAMILTD.NS",

        # =========================
        # PHARMA / HEALTHCARE
        # =========================

        "DIVISLAB.NS",
        "CIPLA.NS",
        "TORNTPHARM.NS",
        "MANKIND.NS",

        # =========================
        # FINANCIALS
        # =========================

        "CHOLAFIN.NS",
        "SHRIRAMFIN.NS",
        "MUTHOOTFIN.NS",
        "MCX.NS",

        # =========================
        # MANUFACTURING / THEMATIC
        # =========================

        "KAYNES.NS",
        "ZENTECH.NS",
        "AZAD.NS",
        "ENDURANCE.NS",
        "SONACOMS.NS",
        "TIMKEN.NS",
        "SKFINDIA.NS",
        "THERMAX.NS",

        # =========================
        # ENERGY / POWER
        # =========================

        "NTPC.NS",
        "NHPC.NS",
        "JSWENERGY.NS",
        "TATAPOWER.NS",

    ]
}

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("⚙ Scanner Controls")

market = st.sidebar.selectbox(
    "Market Preset",
    list(TICKER_PRESETS.keys())
)

default_tickers = ", ".join(TICKER_PRESETS[market])

raw_input = st.sidebar.text_area(
    "Tickers",
    value=default_tickers,
    height=180
)

min_score = st.sidebar.slider(
    "Minimum Institutional Score",
    40,
    100,
    70
)

min_volume_cr = st.sidebar.slider(
    "Minimum Daily Traded Value (Crores ₹)",
    5,
    500,
    50
)

max_distance_50dma = st.sidebar.slider(
    "Max Distance Above 50 DMA %",
    5,
    30,
    18
)

show_only_top = st.sidebar.slider(
    "Top Results",
    5,
    50,
    15
)

# =========================================================
# PARSE TICKERS
# =========================================================

tickers = [x.strip().upper() for x in raw_input.split(",") if x.strip()]

# =========================================================
# DATA FETCHING
# =========================================================

@st.cache_data(ttl=3600)
def fetch_market_data(tickers):

    end = datetime.now()
    start = end - timedelta(days=450)

    data = yf.download(
        tickers=tickers,
        start=start,
        end=end,
        auto_adjust=True,
        group_by='ticker',
        progress=False,
        threads=True
    )

    return data

# =========================================================
# INDICATORS
# =========================================================

def compute_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / (avg_loss + 1e-9)

    rsi = 100 - (100 / (1 + rs))

    return rsi

# =========================================================
# STOCK ANALYSIS
# =========================================================

def analyze_stock(df, ticker, nifty_return):

    try:

        if len(df) < 220:
            return None

        close = df["Close"]
        volume = df["Volume"]

        latest_price = close.iloc[-1]

        # ==========================
        # MOVING AVERAGES
        # ==========================

        sma50 = close.rolling(50).mean()
        sma150 = close.rolling(150).mean()
        sma200 = close.rolling(200).mean()

        latest_sma50 = sma50.iloc[-1]
        latest_sma150 = sma150.iloc[-1]
        latest_sma200 = sma200.iloc[-1]

        # ==========================
        # RSI
        # ==========================

        rsi = compute_rsi(close)
        latest_rsi = rsi.iloc[-1]

        # ==========================
        # VOLUME
        # ==========================

        vol20 = volume.rolling(20).mean()

        latest_vol_ratio = volume.iloc[-1] / (vol20.iloc[-1] + 1)

        # ==========================
        # VOLATILITY
        # ==========================

        atr_proxy = ((df["High"] - df["Low"]) / close).rolling(14).mean()

        latest_atr = atr_proxy.iloc[-1]

        # ==========================
        # DISTANCE FROM 50 DMA
        # ==========================

        distance_50dma = ((latest_price - latest_sma50) / latest_sma50) * 100

        # ==========================
        # RELATIVE STRENGTH
        # ==========================

        stock_return = ((close.iloc[-1] / close.iloc[-60]) - 1) * 100

        rs_value = stock_return - nifty_return

        # ==========================
        # LIQUIDITY
        # ==========================

        traded_value = (
            latest_price *
            volume.iloc[-20:].mean()
        ) / 1e7

        # ==========================
        # TREND SCORE
        # ==========================

        trend_score = 0

        if latest_price > latest_sma50:
            trend_score += 10

        if latest_sma50 > latest_sma150:
            trend_score += 10

        if latest_sma150 > latest_sma200:
            trend_score += 10

        if close.iloc[-1] > close.iloc[-20]:
            trend_score += 5

        # ==========================
        # RELATIVE STRENGTH SCORE
        # ==========================

        rs_score = 0

        if rs_value > 0:
            rs_score += 10

        if rs_value > 5:
            rs_score += 10

        if rs_value > 10:
            rs_score += 10

        # ==========================
        # VOLUME ACCUMULATION SCORE
        # ==========================

        volume_score = 0

        if latest_vol_ratio > 1.2:
            volume_score += 10

        if latest_vol_ratio > 1.5:
            volume_score += 5

        # ==========================
        # VOLATILITY QUALITY SCORE
        # ==========================

        volatility_score = 0

        if latest_atr < 0.05:
            volatility_score += 10

        if distance_50dma < 10:
            volatility_score += 10

        # ==========================
        # RSI QUALITY
        # ==========================

        rsi_score = 0

        if 55 <= latest_rsi <= 75:
            rsi_score += 10

        # ==========================
        # TOTAL SCORE
        # ==========================

        total_score = (
            trend_score +
            rs_score +
            volume_score +
            volatility_score +
            rsi_score
        )

        # ==========================
        # FILTERS
        # ==========================

        if traded_value < min_volume_cr:
            return None

        if distance_50dma > max_distance_50dma:
            return None

        if latest_price < latest_sma200:
            return None

        return {
            "Ticker": ticker,
            "Price": round(latest_price, 2),
            "Institutional Score": round(total_score, 1),
            "RS vs NIFTY": round(rs_value, 2),
            "RSI": round(latest_rsi, 1),
            "Volume Ratio": round(latest_vol_ratio, 2),
            "Distance 50DMA %": round(distance_50dma, 2),
            "ATR Proxy": round(latest_atr * 100, 2),
            "Daily Traded Value Cr": round(traded_value, 2),
            "50 DMA": round(latest_sma50, 2),
            "200 DMA": round(latest_sma200, 2)
        }

    except:
        return None

# =========================================================
# MAIN EXECUTION
# =========================================================

if st.button("🚀 Run Institutional Scan", type="primary"):

    with st.spinner("Scanning for high-probability institutional setups..."):

        market_data = fetch_market_data(tickers)

        results = []

        # ==========================================
        # NIFTY BENCHMARK
        # ==========================================

        nifty = yf.download(
            "^NSEI",
            period="6mo",
            progress=False,
            auto_adjust=True
        )

        nifty_return = (
            (nifty["Close"].iloc[-1] / nifty["Close"].iloc[-60]) - 1
        ) * 100

        progress = st.progress(0)

        for idx, ticker in enumerate(tickers):

            try:

                df = market_data[ticker].copy()

                if df.empty:
                    continue

                result = analyze_stock(df, ticker, nifty_return)

                if result:
                    results.append(result)

            except:
                pass

            progress.progress((idx + 1) / len(tickers))

        progress.empty()

    # =====================================================
    # RESULTS
    # =====================================================

    if len(results) == 0:

        st.warning("No high-quality setups found today.")

    else:

        results_df = pd.DataFrame(results)

        results_df = results_df.sort_values(
            by="Institutional Score",
            ascending=False
        )

        results_df = results_df[
            results_df["Institutional Score"] >= min_score
        ]

        results_df = results_df.head(show_only_top)

        st.success(f"Found {len(results_df)} high-quality institutional setups.")

        st.dataframe(
            results_df.style.background_gradient(
                subset=["Institutional Score"],
                cmap="RdYlGn"
            ),
            use_container_width=True
        )

        # =================================================
        # STOCK CHART
        # =================================================

        st.markdown("---")

        st.subheader("📊 Technical Structure Viewer")

        selected_stock = st.selectbox(
            "Select Stock",
            results_df["Ticker"].tolist()
        )

        if selected_stock:

            chart_df = market_data[selected_stock].copy()

            close = chart_df["Close"]

            chart_df["50DMA"] = close.rolling(50).mean()
            chart_df["200DMA"] = close.rolling(200).mean()

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
                title=f"{selected_stock} Institutional Structure",
                height=650,
                template="plotly_dark",
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # =================================================
        # TOP INSIGHTS
        # =================================================

        st.markdown("---")

        st.subheader("🧠 Scanner Logic")

        st.markdown("""
### What This Scanner Prioritizes
- Strong trend structure
- Relative strength vs NIFTY
- Institutional accumulation behavior
- Controlled volatility
- Liquid quality stocks
- Non-extended setups

### What This Scanner Avoids
- Penny stocks
- Illiquid traps
- Chaotic charts
- Overextended momentum
- Weak relative strength
- Random operator spikes

### Best Use Case
This scanner is designed for:
- 3–4 month swing trades
- Position trading
- Trend continuation setups
- Institutional-style stock selection
""")
