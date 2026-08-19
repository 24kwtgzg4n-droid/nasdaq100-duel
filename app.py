"""
NASDAQ-100 Duell-Ranking App – iPhone / Mobile optimiert
Paarweise Relative-Strength-Rankings basierend auf der Steigung der EMA(3) des Kursverhältnisses.
Drei Zeitrahmen: Tag / Woche / Monat
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path
import time

# ============================================================
# Konfiguration
# ============================================================

HISTORY_FILE = Path(__file__).parent / "rankings_history.json"
MAX_HISTORY = 15

NASDAQ100_TICKERS = [
    "AAPL", "ABNB", "ADBE", "ADI", "ADP", "ADSK", "AEP", "AMAT", "AMD", "AMGN",
    "AMZN", "APP", "ARM", "ASML", "AVGO", "AXON", "AZN", "BIIB", "BKNG", "BKR",
    "CCEP", "CDNS", "CDW", "CEG", "CHTR", "CMCSA", "COST", "CPRT", "CRWD", "CSCO",
    "CSGP", "CSX", "CTAS", "CTSH", "DASH", "DDOG", "DXCM", "EA", "EXC", "FANG",
    "FAST", "FTNT", "GEHC", "GFS", "GILD", "GOOG", "GOOGL", "HON", "IDXX", "INTC",
    "INTU", "ISRG", "KDP", "KHC", "KLAC", "LIN", "LRCX", "LULU", "MAR", "MCHP",
    "MDLZ", "MELI", "META", "MNST", "MRVL", "MSFT", "MSTR", "MU", "NFLX", "NVDA",
    "NXPI", "ODFL", "ON", "ORLY", "PANW", "PAYX", "PCAR", "PDD", "PEP", "PLTR",
    "PYPL", "QCOM", "REGN", "ROP", "ROST", "SBUX", "SNPS", "TEAM", "TMUS", "TSLA",
    "TTWO", "TXN", "VRTX", "WBD", "WDAY", "XEL", "ZS", "ALNY", "TTD", "WMT"
]

TICKER_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "AMZN": "Amazon",
    "GOOGL": "Alphabet A", "GOOG": "Alphabet C", "META": "Meta", "TSLA": "Tesla",
    "AVGO": "Broadcom", "COST": "Costco", "AMD": "AMD", "NFLX": "Netflix",
    "ADBE": "Adobe", "PEP": "PepsiCo", "CSCO": "Cisco", "INTC": "Intel",
    "QCOM": "Qualcomm", "TXN": "Texas Instruments", "AMGN": "Amgen",
    "HON": "Honeywell", "INTU": "Intuit", "AMAT": "Applied Materials",
    "SBUX": "Starbucks", "ADP": "ADP", "ISRG": "Intuitive Surgical",
    "VRTX": "Vertex", "BKNG": "Booking", "LRCX": "Lam Research",
    "REGN": "Regeneron", "MU": "Micron", "ADI": "Analog Devices",
    "KLAC": "KLA", "PANW": "Palo Alto", "SNPS": "Synopsys", "CDNS": "Cadence",
    "MELI": "MercadoLibre", "CRWD": "CrowdStrike", "MAR": "Marriott",
    "ORLY": "O'Reilly", "CTAS": "Cintas", "FTNT": "Fortinet", "ADSK": "Autodesk",
    "NXPI": "NXP", "AEP": "American Electric Power", "PAYX": "Paychex",
    "ROST": "Ross Stores", "KDP": "Keurig Dr Pepper", "PCAR": "PACCAR",
    "MNST": "Monster", "FAST": "Fastenal", "ODFL": "Old Dominion",
    "CTSH": "Cognizant", "EA": "Electronic Arts", "XEL": "Xcel Energy",
    "EXC": "Exelon", "BKR": "Baker Hughes", "FANG": "Diamondback",
    "GEHC": "GE HealthCare", "WBD": "Warner Bros Discovery", "WDAY": "Workday",
    "TEAM": "Atlassian", "ZS": "Zscaler", "DDOG": "Datadog", "TTD": "Trade Desk",
    "PLTR": "Palantir", "APP": "AppLovin", "ARM": "Arm", "MSTR": "MicroStrategy",
    "PDD": "PDD Holdings", "ASML": "ASML", "LIN": "Linde", "ABNB": "Airbnb",
    "DASH": "DoorDash", "CEG": "Constellation Energy", "GILD": "Gilead",
    "BIIB": "Biogen", "IDXX": "IDEXX", "DXCM": "DexCom", "ALNY": "Alnylam",
    "CHTR": "Charter", "CMCSA": "Comcast", "CSX": "CSX", "CPRT": "Copart",
    "CSGP": "CoStar", "LULU": "Lululemon", "ON": "ON Semiconductor",
    "GFS": "GlobalFoundries", "TTWO": "Take-Two", "WMT": "Walmart",
    "PYPL": "PayPal", "KHC": "Kraft Heinz", "MDLZ": "Mondelez",
    "CCEP": "Coca-Cola Europacific", "AZN": "AstraZeneca", "ROP": "Roper",
    "MRVL": "Marvell", "MCHP": "Microchip", "CDW": "CDW"
}

# ============================================================
# Hilfsfunktionen
# ============================================================

def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"daily": [], "weekly": [], "monthly": []}
    return {"daily": [], "weekly": [], "monthly": []}


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_name(ticker):
    return TICKER_NAMES.get(ticker, ticker)


def download_prices(tickers, period="2y", progress_bar=None, status_text=None):
    all_data = {}
    chunk_size = 15
    total = len(tickers)
    failed = []

    for i in range(0, total, chunk_size):
        chunk = tickers[i:i + chunk_size]
        try:
            df = yf.download(
                chunk,
                period=period,
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                threads=True,
                progress=False,
                timeout=25
            )
            if len(chunk) == 1:
                t = chunk[0]
                if not df.empty and "Close" in df.columns:
                    all_data[t] = df["Close"].dropna()
                else:
                    failed.append(t)
            else:
                for t in chunk:
                    try:
                        if t in df.columns.get_level_values(0):
                            s = df[t]["Close"].dropna()
                            if len(s) > 10:
                                all_data[t] = s
                            else:
                                failed.append(t)
                        else:
                            failed.append(t)
                    except Exception:
                        failed.append(t)
        except Exception:
            failed.extend(chunk)

        done = min(i + chunk_size, total)
        if progress_bar is not None:
            progress_bar.progress(done / total)
        if status_text is not None:
            status_text.text(f"Lade Kurse… {done}/{total}")

        time.sleep(0.4)

    return all_data, failed


def prepare_close_matrix(price_dict):
    if not price_dict:
        return pd.DataFrame()
    df = pd.DataFrame(price_dict)
    df = df.sort_index().ffill().dropna(how="all")
    return df


def compute_scores(close_df):
    tickers = list(close_df.columns)
    n = len(tickers)
    scores = {t: 0 for t in tickers}

    if n < 2 or len(close_df) < 5:
        return scores

    for i in range(n):
        for j in range(i + 1, n):
            a = tickers[i]
            b = tickers[j]
            try:
                ratio = close_df[a] / close_df[b]
                ratio = ratio.replace([np.inf, -np.inf], np.nan).dropna()
                if len(ratio) < 5:
                    continue
                ema = ratio.ewm(span=3, adjust=False).mean()
                if len(ema) < 2:
                    continue
                last = ema.iloc[-1]
                prev = ema.iloc[-2]
                if pd.isna(last) or pd.isna(prev):
                    continue
                if last > prev:
                    scores[a] += 1
                elif last < prev:
                    scores[b] += 1
            except Exception:
                continue
    return scores


def make_ranking(scores, timeframe_label):
    items = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    ranking = []
    rank = 0
    prev_score = None
    for idx, (ticker, score) in enumerate(items):
        if score != prev_score:
            rank = idx + 1
            prev_score = score
        ranking.append({
            "Rang": rank,
            "Ticker": ticker,
            "Name": get_name(ticker),
            "Punkte": score,
            "Max": len(scores) - 1
        })
    return ranking


def resample_closes(close_df, rule):
    if close_df.empty:
        return close_df
    return close_df.resample(rule).last().dropna(how="all")


# ============================================================
# Streamlit UI – iPhone / Mobile optimiert
# ============================================================

st.set_page_config(
    page_title="NASDAQ-100 Duell",
    page_icon="⚔️",
    layout="centered",          # besser für Handys
    initial_sidebar_state="collapsed"
)

# Mobile-optimiertes CSS
st.markdown("""
<style>
    /* Größere Touch-Flächen und bessere Lesbarkeit auf iPhone */
    .stButton > button {
        height: 3.2rem !important;
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        font-size: 0.95rem;
        padding: 0 12px;
    }
    div[data-testid="stDataFrame"] {
        font-size: 0.9rem;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    h1 {
        font-size: 1.6rem !important;
        margin-bottom: 0.3rem !important;
    }
    .stCaption {
        font-size: 0.85rem !important;
    }
    /* Sidebar auf Mobile kompakter */
    section[data-testid="stSidebar"] {
        width: 280px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚔️ NASDAQ-100 Duell")
st.caption("Relative Strength · EMA(3) · Tag / Woche / Monat")

# Sidebar
with st.sidebar:
    st.header("Steuerung")
    st.markdown("""
**Regeln**
- Verhältnis = Kurs A / Kurs B
- EMA(3) auf dem Verhältnis
- **Nur letzter Wert**:
  - steigt → A +1
  - fällt → B +1
  - gleich → beide 0
- Jede Aktie gegen jede andere
    """)
    st.divider()
    update_btn = st.button(
        "🔄 Aktualisieren",
        type="primary",
        use_container_width=True
    )
    st.caption("Lädt 2 Jahre Daten und berechnet alle Rankings.")

# Session State
if "close_daily" not in st.session_state:
    st.session_state.close_daily = None
if "rankings" not in st.session_state:
    st.session_state.rankings = {"daily": None, "weekly": None, "monthly": None}
if "last_update" not in st.session_state:
    st.session_state.last_update = None
if "failed_tickers" not in st.session_state:
    st.session_state.failed_tickers = []

# Update
if update_btn:
    progress = st.progress(0.0)
    status = st.empty()

    status.text("Lade NASDAQ-100 Kurse…")
    price_dict, failed = download_prices(
        NASDAQ100_TICKERS,
        period="2y",
        progress_bar=progress,
        status_text=status
    )

    if not price_dict:
        st.error("Keine Daten geladen. Warte 1–2 Minuten und versuche es erneut (Yahoo Rate-Limit).")
    else:
        status.text("Bereite Daten vor…")
        progress.progress(0.82)
        close_daily = prepare_close_matrix(price_dict)
        st.session_state.close_daily = close_daily
        st.session_state.failed_tickers = failed

        status.text("Berechne Tages-Ranking…")
        scores_d = compute_scores(close_daily)
        ranking_d = make_ranking(scores_d, "daily")

        status.text("Berechne Wochen-Ranking…")
        close_w = resample_closes(close_daily, "W-FRI")
        scores_w = compute_scores(close_w)
        ranking_w = make_ranking(scores_w, "weekly")

        status.text("Berechne Monats-Ranking…")
        close_m = resample_closes(close_daily, "ME")
        scores_m = compute_scores(close_m)
        ranking_m = make_ranking(scores_m, "monthly")

        st.session_state.rankings = {
            "daily": ranking_d,
            "weekly": ranking_w,
            "monthly": ranking_m
        }
        st.session_state.last_update = datetime.now().strftime("%Y-%m-%d %H:%M")

        history = load_history()
        ts = st.session_state.last_update
        for key, ranking in [("daily", ranking_d), ("weekly", ranking_w), ("monthly", ranking_m)]:
            entry = {"timestamp": ts, "ranking": ranking, "n_tickers": len(ranking)}
            history[key].insert(0, entry)
            history[key] = history[key][:MAX_HISTORY]
        save_history(history)

        progress.progress(1.0)
        status.text(f"✅ Fertig! {len(close_daily.columns)} Aktien")
        time.sleep(0.6)
        status.empty()
        progress.empty()
        st.rerun()

# Anzeige
if st.session_state.rankings["daily"] is None:
    st.info("👆 Tippe oben links auf das **☰ Menü** und dann auf **Aktualisieren**.")
    st.markdown("""
### So funktioniert’s
1. Lädt die NASDAQ-100-Aktien
2. Berechnet für jedes Paar das Kursverhältnis + EMA(3)
3. Vergibt Punkte nur nach der **letzten Steigung**
4. Erstellt drei Rankings: Tag · Woche · Monat
5. Speichert die Historie lokal
    """)
else:
    last = st.session_state.last_update
    n = len(st.session_state.rankings["daily"])
    st.success(f"**{last}**  ·  {n} Aktien")

    if st.session_state.failed_tickers:
        with st.expander(f"⚠️ {len(st.session_state.failed_tickers)} Ticker fehlgeschlagen"):
            st.write(", ".join(st.session_state.failed_tickers))

    tab_d, tab_w, tab_m, tab_hist = st.tabs(["📅 Tag", "📆 Woche", "🗓️ Monat", "📜 Historie"])

    def show_ranking_table(ranking):
        if not ranking:
            st.warning("Kein Ranking verfügbar.")
            return
        df = pd.DataFrame(ranking)[["Rang", "Ticker", "Name", "Punkte"]]
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(520, 38 + len(df) * 35)
        )

    with tab_d:
        st.subheader("Tages-Ranking")
        show_ranking_table(st.session_state.rankings["daily"])

    with tab_w:
        st.subheader("Wochen-Ranking")
        show_ranking_table(st.session_state.rankings["weekly"])

    with tab_m:
        st.subheader("Monats-Ranking")
        show_ranking_table(st.session_state.rankings["monthly"])

    with tab_hist:
        st.subheader("Letzte Rankings")
        history = load_history()
        hist_tab_d, hist_tab_w, hist_tab_m = st.tabs(["Tag", "Woche", "Monat"])

        def show_history(entries):
            if not entries:
                st.info("Noch keine Historie.")
                return
            for i, entry in enumerate(entries):
                with st.expander(f"{entry['timestamp']}  ·  {entry['n_tickers']} Aktien", expanded=(i == 0)):
                    df = pd.DataFrame(entry["ranking"])[["Rang", "Ticker", "Name", "Punkte"]]
                    st.dataframe(df, use_container_width=True, hide_index=True)

        with hist_tab_d:
            show_history(history.get("daily", []))
        with hist_tab_w:
            show_history(history.get("weekly", []))
        with hist_tab_m:
            show_history(history.get("monthly", []))

st.divider()
st.caption("Yahoo Finance · EMA(3) · Nur letzter Wert zählt · Gleichstand = 0 Punkte für beide")
