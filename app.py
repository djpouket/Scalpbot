import streamlit as st
import threading
import asyncio
import pandas as pd
import numpy as np
import os
import pytz
import time as time_module
from datetime import datetime
from collections import deque
from dotenv import load_dotenv
import websockets
import json

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="ScalpBot Pro", layout="wide", page_icon="⚡")

QT_BG = "#080b0f"
QT_SURFACE = "#0c1118"
QT_PANEL = "#10151d"
QT_PANEL_SOFT = "#141a23"
QT_BORDER = "#26303b"
QT_TEXT = "#e6edf3"
QT_MUTED = "#8b98a8"
QT_GREEN = "#20e3a2"
QT_CYAN = "#2dd4ff"
QT_AMBER = "#f2b84b"
QT_RED = "#ff5c5c"

def inject_qterminal_style():
    st.markdown(
        f"""
        <style>
        html {{
            scroll-behavior: smooth;
        }}
        :root {{
            --qt-bg: {QT_BG};
            --qt-surface: {QT_SURFACE};
            --qt-panel: {QT_PANEL};
            --qt-panel-soft: {QT_PANEL_SOFT};
            --qt-border: {QT_BORDER};
            --qt-text: {QT_TEXT};
            --qt-muted: {QT_MUTED};
            --qt-green: {QT_GREEN};
            --qt-cyan: {QT_CYAN};
            --qt-amber: {QT_AMBER};
            --qt-red: {QT_RED};
        }}
        .stApp {{
            background:
                linear-gradient(rgba(45, 212, 255, 0.035) 1px, transparent 1px),
                linear-gradient(90deg, rgba(45, 212, 255, 0.026) 1px, transparent 1px),
                linear-gradient(180deg, #080b0f 0%, #07090d 100%);
            background-size: 34px 34px, 34px 34px, auto;
            color: var(--qt-text);
        }}
        .block-container {{
            max-width: 1580px;
            padding-top: 1.1rem;
            padding-bottom: 2.2rem;
            animation: qtFadeIn 260ms ease-out;
        }}
        [data-testid="stHeader"] {{
            background: rgba(8, 11, 15, 0.94);
            border-bottom: 1px solid rgba(38, 48, 59, 0.88);
        }}
        [data-testid="stToolbar"] {{
            color: var(--qt-muted);
        }}
        [data-testid="stToolbar"] button {{
            color: var(--qt-muted);
        }}
        @keyframes qtFadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        h1, h2, h3, p, label, span {{
            letter-spacing: 0;
        }}
        .qt-page-header {{
            position: relative;
            border: 1px solid rgba(45, 212, 255, 0.22);
            border-radius: 8px;
            background:
                linear-gradient(90deg, rgba(32, 227, 162, 0.10), transparent 28%),
                linear-gradient(135deg, rgba(11, 16, 22, 0.98), rgba(13, 19, 28, 0.92));
            padding: 20px 20px 18px 20px;
            margin: -2px 0 14px 0;
            overflow: hidden;
            box-shadow: 0 18px 42px rgba(0, 0, 0, 0.20), inset 0 1px 0 rgba(255, 255, 255, 0.035);
        }}
        .qt-page-header::after {{
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--qt-green), var(--qt-cyan), transparent);
            opacity: 0.88;
        }}
        .qt-kicker {{
            color: var(--qt-cyan);
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 8px;
        }}
        .qt-page-header h1 {{
            margin: 0;
            color: var(--qt-text);
            font-size: clamp(2rem, 2.8vw, 3.1rem);
            line-height: 1.02;
            font-weight: 780;
        }}
        .qt-page-header p {{
            color: var(--qt-muted);
            margin: 8px 0 0 0;
            max-width: 880px;
            font-size: 0.96rem;
            line-height: 1.48;
        }}
        .qt-status-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 14px;
        }}
        .qt-pill {{
            display: inline-flex;
            align-items: center;
            border: 1px solid rgba(45, 212, 255, 0.30);
            border-radius: 999px;
            padding: 7px 10px;
            color: var(--qt-cyan);
            background: rgba(45, 212, 255, 0.08);
            font-size: 0.78rem;
            white-space: nowrap;
        }}
        .qt-pill.ok {{
            color: var(--qt-green);
            border-color: rgba(32, 227, 162, 0.38);
            background: rgba(32, 227, 162, 0.08);
        }}
        .qt-pill.warn {{
            color: var(--qt-amber);
            border-color: rgba(242, 184, 75, 0.38);
            background: rgba(242, 184, 75, 0.08);
        }}
        .qt-control-band {{
            border: 1px solid var(--qt-border);
            border-radius: 8px;
            background:
                linear-gradient(145deg, rgba(45, 212, 255, 0.035), transparent 36%),
                rgba(15, 21, 31, 0.92);
            padding: 14px 14px 6px 14px;
            margin-bottom: 14px;
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.18);
        }}
        div[data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stDataFrame"], .stPlotlyChart {{
            border: 1px solid var(--qt-border);
            border-radius: 8px;
            background: var(--qt-panel);
            transition: border-color 160ms ease, background 160ms ease, box-shadow 160ms ease;
        }}
        .stPlotlyChart {{
            padding: 8px;
            box-shadow: 0 14px 32px rgba(0, 0, 0, 0.16);
        }}
        div[data-testid="stDataFrame"]:hover, .stPlotlyChart:hover {{
            border-color: rgba(45, 212, 255, 0.40);
            background: var(--qt-panel-soft);
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.20);
        }}
        [data-testid="stExpander"] {{
            border: 1px solid var(--qt-border);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(45, 212, 255, 0.035), transparent 42%),
                var(--qt-panel);
        }}
        [data-testid="stExpander"]:hover {{
            border-color: rgba(45, 212, 255, 0.34);
        }}
        [data-testid="stAlert"] {{
            border-radius: 8px;
            border: 1px solid rgba(242, 184, 75, 0.35);
            background: rgba(16, 21, 29, 0.82);
        }}
        button, [role="button"] {{
            border-radius: 8px !important;
            transition: transform 140ms ease, border-color 140ms ease, background 140ms ease, color 140ms ease;
        }}
        button:hover, [role="button"]:hover {{
            transform: translateY(-1px);
        }}
        [data-testid="baseButton-primary"],
        [data-testid="stBaseButton-primary"],
        button[kind="primary"] {{
            background: var(--qt-green);
            border-color: var(--qt-green);
            color: #06100c;
        }}
        [data-testid="stBaseButton-secondary"],
        button[kind="secondary"] {{
            border-color: rgba(45, 212, 255, 0.28);
            background: rgba(12, 17, 24, 0.82);
            color: var(--qt-text);
        }}
        [data-testid="stBaseButton-secondary"]:hover,
        button[kind="secondary"]:hover {{
            border-color: rgba(32, 227, 162, 0.48);
            background: rgba(32, 227, 162, 0.08);
            color: var(--qt-green);
        }}
        [data-testid="stSlider"] [data-baseweb="slider"] > div {{
            color: var(--qt-green);
        }}
        [data-testid="stToggle"] label {{
            color: var(--qt-text);
        }}
        hr {{
            border-color: var(--qt-border);
        }}
        @media (max-width: 720px) {{
            .block-container {{
                padding-left: 0.8rem;
                padding-right: 0.8rem;
                padding-top: 0.7rem;
            }}
            .qt-page-header {{
                padding: 16px;
            }}
            .qt-page-header h1 {{
                font-size: 1.8rem;
            }}
            .stPlotlyChart {{
                padding: 4px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_qterminal_style()

# ── Supabase optionnel ───────────────────────────────────────
try:
    from supabase import create_client
    _SUPABASE_OK = True
except ImportError:
    _SUPABASE_OK = False

# ============================================================
# 1. CONFIG & INIT
# ============================================================
load_dotenv()

def get_config_value(name, default=None):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

def get_float_config(name, default):
    try:
        return float(get_config_value(name, default))
    except (TypeError, ValueError):
        return float(default)

def get_int_config(name, default):
    try:
        return int(float(get_config_value(name, default)))
    except (TypeError, ValueError):
        return int(default)

SUPABASE_URL = get_config_value("SUPABASE_URL")
SUPABASE_KEY = get_config_value("SUPABASE_KEY")
API_KEY      = get_config_value("ALPACA_API_KEY")
SECRET_KEY   = get_config_value("ALPACA_SECRET_KEY")

MAX_RISK_FRACTION     = get_float_config("MAX_RISK_FRACTION", 0.01)
MAX_ORDER_NOTIONAL    = get_float_config("MAX_ORDER_NOTIONAL", 10_000)
MAX_SYMBOL_ORDER_QTY  = get_int_config("MAX_SYMBOL_ORDER_QTY", 1_000)

if not API_KEY or not SECRET_KEY:
    st.error("🚨 Clés API introuvables. Vérifie ton fichier .env ou Streamlit Secrets.")
    st.stop()

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

sb = None
if _SUPABASE_OK and SUPABASE_URL and SUPABASE_KEY:
    try:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass

SYMBOLES = ["QQQ", "SPY", "GLD", "SLV", "NVDA", "AMD", "TSLA", "AAPL"]
BARS_M1  = 60
BARS_M5  = 30

# ============================================================
# 2. STATE PARTAGÉ
# ============================================================
@st.cache_resource
def get_bot_state():
    class State:
        def __init__(self):
            self.lock            = threading.RLock()
            self.bars_m1         = {s: deque(maxlen=BARS_M1) for s in SYMBOLES}
            self.bars_m5         = {s: deque(maxlen=BARS_M5) for s in SYMBOLES}
            self.m5_buf          = {s: [] for s in SYMBOLES}
            self.vwap            = {s: 0.0 for s in SYMBOLES}
            self.cum_pv          = {s: 0.0 for s in SYMBOLES}
            self.cum_vol         = {s: 0.0 for s in SYMBOLES}
            self.trade_queue     = []
            self.auto_executed   = []
            self.pending_orders  = []   # {"order_id", "symbole", "submitted_at", "limit_price"}
            self.stream_started  = False
            self.watcher_started = False
            self.auto_trade_on   = False
            self.auto_seuil      = 8
            self.vwap_date       = datetime.now(pytz.timezone("US/Eastern")).date()
    return State()

state = get_bot_state()

# ============================================================
# 3. UTILITAIRES
# ============================================================
def bars_to_df(bars):
    return pd.DataFrame([{
        "Date":   b.timestamp,
        "Open":   b.open,
        "High":   b.high,
        "Low":    b.low,
        "Close":  b.close,
        "Volume": b.volume
    } for b in bars])

def calc_indicators(df):
    df = df.copy()
    df["EMA9"]  = df["Close"].ewm(span=9,  adjust=False).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    # ── FIX 1 : VWAP reset quotidien ────────────────────────
    if "Date" in df.columns:
        df["_date"] = pd.to_datetime(df["Date"]).dt.date
        typical     = (df["High"] + df["Low"] + df["Close"]) / 3
        df["_tpv"]  = typical * df["Volume"]
        cum_vol     = df.groupby("_date")["Volume"].cumsum().replace(0, np.nan)
        df["VWAP"]  = (
            df.groupby("_date")["_tpv"].cumsum()
            / cum_vol
        ).fillna(df["Close"])
        df.drop(columns=["_date", "_tpv"], inplace=True)
    else:
        typical    = (df["High"] + df["Low"] + df["Close"]) / 3
        cum_vol    = df["Volume"].cumsum().replace(0, np.nan)
        df["VWAP"] = ((typical * df["Volume"]).cumsum() / cum_vol).fillna(df["Close"])

    tr1 = df["High"] - df["Low"]
    tr2 = abs(df["High"] - df["Close"].shift())
    tr3 = abs(df["Low"]  - df["Close"].shift())
    df["TR"]  = np.maximum(tr1, np.maximum(tr2, tr3))
    df["ATR"] = df["TR"].ewm(span=14, adjust=False).mean()
    return df

def agreger_m5(sym):
    buf = state.m5_buf[sym]
    if len(buf) < 5:
        return
    group = buf[-5:]
    class FakeBar: pass
    b           = FakeBar()
    b.timestamp = group[-1].timestamp
    b.open      = group[0].open
    b.high      = max(x.high   for x in group)
    b.low       = min(x.low    for x in group)
    b.close     = group[-1].close
    b.volume    = sum(x.volume for x in group)
    b.symbol    = sym
    state.bars_m5[sym].append(b)

# ============================================================
# 4. MOTEUR SMC
# ============================================================
def detecter_swing(df, n=2):
    """FIX 2 : lookback réduit à 2 (moins de lag)."""
    highs, lows = [], []
    for i in range(n, len(df) - n):
        if df["High"].iloc[i] == df["High"].iloc[i-n:i+n+1].max():
            highs.append(i)
        if df["Low"].iloc[i]  == df["Low"].iloc[i-n:i+n+1].min():
            lows.append(i)
    return highs, lows

def detecter_order_blocks(df, direction=None):
    """
    FIX 3 : filtre par direction.
    FIX 4 : invalidation si prix a traversé la zone après formation.
    """
    obs = []
    if "ATR" not in df.columns or df["ATR"].isna().all():
        return obs
    atr = df["ATR"].dropna().iloc[-1]

    for i in range(2, len(df) - 1):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        body = abs(curr["Close"] - curr["Open"])
        # Seuil abaissé à 1.0× ATR (était 1.5×) pour ne pas rater
        # les OBs formés par un mouvement fluide sans bougie explosive
        disp = body > atr * 1.0

        # OB Haussier
        if disp and prev["Close"] < prev["Open"] and curr["Close"] > prev["High"]:
            ob = {"type": "bullish", "top": prev["High"], "bottom": prev["Low"],
                  "date": prev["Date"], "index": i - 1}
            if not (df["Close"].iloc[i+1:] < ob["bottom"]).any():
                obs.append(ob)

        # OB Baissier
        if disp and prev["Close"] > prev["Open"] and curr["Close"] < prev["Low"]:
            ob = {"type": "bearish", "top": prev["High"], "bottom": prev["Low"],
                  "date": prev["Date"], "index": i - 1}
            if not (df["Close"].iloc[i+1:] > ob["top"]).any():
                obs.append(ob)

    recent = obs[-8:]
    if direction:
        recent = [o for o in recent if o["type"] == direction]
    return recent[-4:]

def detecter_fvg(df, direction=None):
    """FIX 3 : filtre optionnel par direction."""
    fvgs = []
    for i in range(2, len(df)):
        if df["Low"].iloc[i] > df["High"].iloc[i - 2]:
            fvgs.append({"type": "bullish", "top": df["Low"].iloc[i],
                         "bottom": df["High"].iloc[i - 2], "date": df["Date"].iloc[i]})
        if df["High"].iloc[i] < df["Low"].iloc[i - 2]:
            fvgs.append({"type": "bearish", "top": df["Low"].iloc[i - 2],
                         "bottom": df["High"].iloc[i], "date": df["Date"].iloc[i]})
    recent = fvgs[-6:]
    if direction:
        recent = [f for f in recent if f["type"] == direction]
    return recent[-3:]

def detecter_bos_choch(df):
    """
    FIX 2b : confirmation 2 bougies pour éviter faux positifs.
    """
    highs, lows = detecter_swing(df)
    events = []
    if len(highs) < 2 or len(lows) < 2:
        return events

    last_sh = df["High"].iloc[highs[-1]]
    prev_sh = df["High"].iloc[highs[-2]]
    last_sl = df["Low"].iloc[lows[-1]]
    prev_sl = df["Low"].iloc[lows[-2]]

    last      = df.iloc[-1]
    prev_last = df.iloc[-2]

    # Tendance haussière
    if last_sh > prev_sh and last_sl > prev_sl:
        if last["Close"] > last_sh and prev_last["Close"] <= last_sh:
            events.append({"type": "BOS",   "direction": "bullish", "price": last_sh, "date": last["Date"]})
        elif last["Close"] < last_sl and prev_last["Close"] >= last_sl:
            events.append({"type": "CHoCH", "direction": "bearish", "price": last_sl, "date": last["Date"]})
    # Tendance baissière
    elif last_sh < prev_sh and last_sl < prev_sl:
        if last["Close"] < last_sl and prev_last["Close"] >= last_sl:
            events.append({"type": "BOS",   "direction": "bearish", "price": last_sl, "date": last["Date"]})
        elif last["Close"] > last_sh and prev_last["Close"] <= last_sh:
            events.append({"type": "CHoCH", "direction": "bullish", "price": last_sh, "date": last["Date"]})
    return events

def score_confluence(sym):
    """
    FIX 5 : score directionnel — FVG/OB/BOS ne comptent que
    s'ils sont alignés avec le biais de tendance.
    """
    with state.lock:
        bars_m1 = list(state.bars_m1[sym])
        bars_m5 = list(state.bars_m5[sym])
    if len(bars_m1) < 20:
        return 0, [], None
    if len(bars_m5) < 10:
        bars_m5 = bars_m1

    df1 = calc_indicators(bars_to_df(bars_m1))
    df5 = calc_indicators(bars_to_df(bars_m5))

    score, raisons, direction = 0, [], None

    last1 = df1.iloc[-1]
    last5 = df5.iloc[-1]

    # ── Tendance M5 ──────────────────────────────────────────
    if last5["EMA9"] > last5["EMA20"] > last5["EMA50"]:
        score += 2; raisons.append("📈 Tendance M5 haussière (EMA9>20>50)"); direction = "bullish"
    elif last5["EMA9"] < last5["EMA20"] < last5["EMA50"]:
        score += 2; raisons.append("📉 Tendance M5 baissière (EMA9<20<50)"); direction = "bearish"
    else:
        return 0, ["⚪ EMAs M5 entremêlées — pas de biais clair"], None

    # ── VWAP M1 ─────────────────────────────────────────────
    if direction == "bullish" and last1["Close"] > last1["VWAP"]:
        score += 1; raisons.append("💧 Prix au-dessus VWAP M1")
    elif direction == "bearish" and last1["Close"] < last1["VWAP"]:
        score += 1; raisons.append("💧 Prix en-dessous VWAP M1")

    # ── OB M5 (filtrés par direction) ───────────────────────
    obs5 = detecter_order_blocks(df5, direction=direction)
    for ob in obs5:
        if ob["bottom"] <= last1["Close"] <= ob["top"]:
            score += 2
            raisons.append(f"🏦 Prix dans OB {ob['type']} M5 ({ob['bottom']:.2f}-{ob['top']:.2f})")

    # ── FVG M1 (filtrés par direction) ──────────────────────
    fvgs = detecter_fvg(df1, direction=direction)
    for fvg in fvgs:
        if fvg["bottom"] <= last1["Close"] <= fvg["top"]:
            score += 1; raisons.append("⚡ Prix dans FVG M1 aligné")

    # ── BOS / CHoCH M5 (alignés avec direction) ─────────────
    events5 = detecter_bos_choch(df5)
    for ev in events5:
        if ev["direction"] == direction:
            if ev["type"] == "BOS":
                score += 1; raisons.append(f"🔨 BOS {ev['direction']} M5 @ {ev['price']:.2f}")
            elif ev["type"] == "CHoCH":
                score += 2; raisons.append(f"🔄 CHoCH {ev['direction']} M5 @ {ev['price']:.2f}")

    # ── Filtre volatilité ATR ────────────────────────────────
    if last1["ATR"] < 0.05:
        score = max(0, score - 1)

    return min(score, 10), raisons, direction

# ============================================================
# 5. WEBSOCKET ALPACA
# ============================================================
def process_bar(sym, o, h, l, c, v, ts):
    with state.lock:
        now_et = datetime.now(pytz.timezone("US/Eastern"))
        if now_et.date() != state.vwap_date:
            state.vwap_date = now_et.date()
            for s in SYMBOLES:
                state.cum_pv[s]  = 0.0
                state.cum_vol[s] = 0.0

        class Bar: pass
        bar           = Bar()
        bar.timestamp = ts; bar.open = o; bar.high = h
        bar.low = l; bar.close = c; bar.volume = v; bar.symbol = sym

        state.bars_m1[sym].append(bar)
        state.m5_buf[sym].append(bar)
        if len(state.m5_buf[sym]) >= 5:
            agreger_m5(sym)
            state.m5_buf[sym] = state.m5_buf[sym][-4:]

        typical = (h + l + c) / 3
        state.cum_pv[sym]  += typical * v
        state.cum_vol[sym] += v
        state.vwap[sym]     = state.cum_pv[sym] / state.cum_vol[sym] if state.cum_vol[sym] else 0

        # Supabase optionnel
        if sb:
            try:
                sb.table("prix_history").insert(
                    {"symbol": sym, "prix": float(c), "volume": int(v)}
                ).execute()
            except Exception:
                pass

        score, raisons, direction = score_confluence(sym)
        if score >= 5 and raisons:
            # ── SL/TP dynamiques basés sur ATR et OB ────────────
            bars = list(state.bars_m1[sym])
            df_sig = calc_indicators(bars_to_df(bars)) if len(bars) >= 14 else None

            last_close = float(c)
            dir_sig = direction or "bullish"
            atr_val = float(df_sig["ATR"].iloc[-1]) if df_sig is not None else last_close * 0.005
            if not np.isfinite(atr_val) or atr_val <= 0:
                atr_val = max(last_close * 0.005, 0.01)

            # Cherche un OB proche pour ancrer le SL
            limit_entry = last_close  # entrée par défaut = prix actuel
            if df_sig is not None:
                obs_sig = detecter_order_blocks(df_sig, direction=dir_sig)
                fvg_sig = detecter_fvg(df_sig, direction=dir_sig)

                # Priorité FVG > OB pour l'entrée limit
                zone = None
                if fvg_sig:
                    zone = fvg_sig[-1]
                elif obs_sig:
                    zone = obs_sig[-1]

                if zone:
                    # Entrée au milieu de la zone
                    limit_entry = round((zone["top"] + zone["bottom"]) / 2, 2)
                    if dir_sig == "bullish":
                        sl_dyn = round(zone["bottom"] - atr_val * 0.1, 2)
                    else:
                        sl_dyn = round(zone["top"]    + atr_val * 0.1, 2)
                else:
                    # Pas de zone — SL = dernier swing ± 0.1 ATR
                    if dir_sig == "bullish":
                        sl_dyn = round(last_close - atr_val * 1.5, 2)
                    else:
                        sl_dyn = round(last_close + atr_val * 1.5, 2)
            else:
                sl_dyn = round(last_close * 0.99, 2)

            risk = abs(limit_entry - sl_dyn)
            if dir_sig == "bullish":
                tp_dyn = round(limit_entry + risk * 2.0, 2)
            else:
                tp_dyn = round(limit_entry - risk * 2.0, 2)

            sig = {
                "symbole":      sym,
                "score":        score,
                "raisons":      raisons,
                "direction":    dir_sig,
                "entree":       last_close,
                "limit_entry":  limit_entry,
                "sl":           sl_dyn,
                "tp":           tp_dyn,
                "atr":          atr_val,
                "icone":        "📈" if dir_sig == "bullish" else "📉",
                "type":         f"CONFLUENCE {score}/10",
                "time":         datetime.now().strftime("%H:%M:%S")
            }
            existing_idx = next(
                (idx for idx, trade in enumerate(state.trade_queue) if trade["symbole"] == sym),
                None
            )
            if existing_idx is None:
                state.trade_queue.insert(0, sig)
                if len(state.trade_queue) > 10:
                    state.trade_queue.pop()
            else:
                state.trade_queue[existing_idx] = sig

            # Auto-trade
            auto_on    = state.auto_trade_on
            auto_seuil = state.auto_seuil
            if auto_on and score >= auto_seuil:
                if not any(t["symbole"] == sym for t in state.auto_executed[-5:]):
                    ok, msg = executer_ordre(sig)
                    sig["auto"] = True
                    sig["auto_result"] = msg
                    state.auto_executed.insert(0, {**sig, "result": msg, "ok": ok})
                    if len(state.auto_executed) > 20:
                        state.auto_executed.pop()

def start_alpaca_stream():
    WS_URL = "wss://stream.data.alpaca.markets/v2/iex"
    delay  = 15
    while True:
        try:
            async def run():
                async with websockets.connect(WS_URL, ping_interval=20, ping_timeout=10) as ws:
                    await ws.send(json.dumps({"action": "auth", "key": API_KEY, "secret": SECRET_KEY}))
                    await ws.recv()
                    await ws.send(json.dumps({"action": "subscribe", "bars": SYMBOLES}))
                    await ws.recv()
                    async for msg in ws:
                        data = json.loads(msg)
                        for item in data:
                            if item.get("T") == "b" and item["S"] in SYMBOLES:
                                process_bar(
                                    item["S"],
                                    float(item["o"]), float(item["h"]),
                                    float(item["l"]), float(item["c"]),
                                    float(item["v"]),
                                    pd.to_datetime(item["t"])
                                )
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run())
        except Exception as e:
            print(f"⚠️ WS erreur ({e}) — retry dans {delay}s…")
        finally:
            try:
                loop.close()
            except Exception:
                pass
        time_module.sleep(delay)
        delay = min(delay * 2, 300)

# ============================================================
# 6. GRAPHIQUE
# ============================================================
def build_chart(sym):
    with state.lock:
        bars_m1 = list(state.bars_m1[sym])
        bars_m5 = list(state.bars_m5[sym])
    if not bars_m1:
        return None

    df1    = calc_indicators(bars_to_df(bars_m1))
    use_m5 = len(bars_m5) >= 5
    df5    = calc_indicators(bars_to_df(bars_m5)) if use_m5 else df1

    fig = make_subplots(
        rows=3, cols=1,
        row_heights=[0.45, 0.35, 0.20],
        shared_xaxes=False,
        vertical_spacing=0.04,
        subplot_titles=(
            f"{sym} — {'M5' if use_m5 else 'M1'}",
            f"{sym} — M1",
            "Volume M1"
        )
    )

    # ── M5 ──────────────────────────────────────────────────
    obs5  = detecter_order_blocks(df5)
    fvg5  = detecter_fvg(df5)
    ev5   = detecter_bos_choch(df5)

    fig.add_trace(go.Candlestick(
        x=df5["Date"], open=df5["Open"], high=df5["High"],
        low=df5["Low"], close=df5["Close"],
        increasing_line_color=QT_GREEN, decreasing_line_color=QT_RED,
        increasing_fillcolor=QT_GREEN, decreasing_fillcolor=QT_RED,
        line=dict(width=1), showlegend=False
    ), row=1, col=1)

    for y, color, label, dash in [
        (df5["EMA9"],  QT_AMBER, "EMA9",  "solid"),
        (df5["EMA20"], QT_CYAN,  "EMA20", "solid"),
        (df5["EMA50"], QT_MUTED, "EMA50", "solid"),
        (df5["VWAP"],  QT_GREEN, "VWAP",  "dot"),
    ]:
        fig.add_trace(go.Scatter(x=df5["Date"], y=y, mode="lines",
                                 line=dict(color=color, width=1, dash=dash),
                                 showlegend=False), row=1, col=1)

    for fvg in fvg5:
        fig.add_hrect(
            y0=fvg["bottom"], y1=fvg["top"],
            fillcolor="rgba(32,227,162,0.12)" if fvg["type"] == "bullish" else "rgba(255,92,92,0.12)",
            line_width=0, row=1, col=1
        )
    for ob in obs5:
        col_f  = "rgba(242,184,75,0.16)" if ob["type"] == "bullish" else "rgba(45,212,255,0.12)"
        col_b  = "rgba(242,184,75,0.62)" if ob["type"] == "bullish" else "rgba(45,212,255,0.54)"
        fig.add_hrect(y0=ob["bottom"], y1=ob["top"],
                      fillcolor=col_f, line=dict(color=col_b, width=1), row=1, col=1)
    for ev in ev5:
        col_ev = QT_GREEN if ev["direction"] == "bullish" else QT_RED
        fig.add_hline(y=ev["price"], line_color=col_ev, line_dash="dash",
                      line_width=1, row=1, col=1,
                      annotation_text=ev["type"],
                      annotation_font=dict(color=col_ev, size=9))

    # ── M1 ──────────────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df1["Date"], open=df1["Open"], high=df1["High"],
        low=df1["Low"], close=df1["Close"],
        increasing_line_color=QT_GREEN, decreasing_line_color=QT_RED,
        increasing_fillcolor=QT_GREEN, decreasing_fillcolor=QT_RED,
        line=dict(width=1), showlegend=False
    ), row=2, col=1)
    fig.add_trace(go.Scatter(x=df1["Date"], y=df1["EMA9"], mode="lines",
                             line=dict(color=QT_AMBER, width=1), showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=df1["Date"], y=df1["VWAP"], mode="lines",
                             line=dict(color=QT_GREEN, width=1, dash="dot"), showlegend=False), row=2, col=1)
    for ob in detecter_order_blocks(df1)[-2:]:
        fig.add_hrect(
            y0=ob["bottom"], y1=ob["top"],
            fillcolor="rgba(242,184,75,0.14)" if ob["type"] == "bullish" else "rgba(45,212,255,0.12)",
            line_width=0, row=2, col=1
        )

    # ── Volume ───────────────────────────────────────────────
    vol_colors = [
        "rgba(32,227,162,0.62)" if df1["Close"].iloc[k] >= df1["Open"].iloc[k]
        else "rgba(255,92,92,0.58)"
        for k in range(len(df1))
    ]
    fig.add_trace(go.Bar(x=df1["Date"], y=df1["Volume"],
                         marker_color=vol_colors, showlegend=False), row=3, col=1)

    # ── Layout ───────────────────────────────────────────────
    score, _, _ = score_confluence(sym)
    score_color = QT_GREEN if score >= 7 else QT_AMBER if score >= 5 else QT_MUTED
    last_close  = df1["Close"].iloc[-1]
    vwap_val    = df1["VWAP"].iloc[-1]

    fig.update_layout(
        height=480, template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=QT_PANEL,
        margin=dict(l=4, r=4, t=38, b=4), showlegend=False,
        font=dict(color=QT_TEXT, family="Inter, Segoe UI, sans-serif"),
        title=dict(
            text=(
                f"<b>{sym}</b>  "
                f"<span style='color:{QT_MUTED};font-size:10px'>{last_close:.2f}$  VWAP:{vwap_val:.2f}</span>  "
                f"<span style='color:{score_color};font-size:11px'>● Score {score}/10</span>"
            ),
            font=dict(size=13, color=QT_TEXT), x=0.01
        )
    )
    for row in [1, 2, 3]:
        fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(size=8, color=QT_MUTED),
                         tickformat="%H:%M", rangeslider_visible=False, row=row, col=1)
    for row in [1, 2]:
        fig.update_yaxes(showgrid=True, gridcolor="rgba(45,212,255,0.055)", zeroline=False,
                         tickfont=dict(size=8, color=QT_MUTED), side="right", row=row, col=1)
    fig.update_yaxes(showticklabels=False, row=3, col=1)
    fig.update_annotations(font_size=9)
    return fig

# ============================================================
# 7. EXÉCUTION ORDRE
# ============================================================
def executer_ordre(trade: dict):
    try:
        compte  = trading_client.get_account()
        capital = float(compte.equity)
        try:
            buying_power = float(getattr(compte, "buying_power", capital) or capital)
        except (TypeError, ValueError):
            buying_power = capital

        # ── Niveaux issus du signal (ATR + zone OB/FVG) ─────────
        limit_entry = float(trade.get("limit_entry", trade["entree"]))
        sl_price    = float(trade.get("sl", limit_entry * 0.99))
        tp_price    = float(trade.get("tp", limit_entry * 1.02))

        if min(limit_entry, sl_price, tp_price) <= 0:
            return False, "Prix d'entrée, SL ou TP invalide."

        dist_sl = abs(limit_entry - sl_price)
        if dist_sl <= 0:
            return False, "Distance SL nulle."

        side = OrderSide.BUY if trade.get("direction") != "bearish" else OrderSide.SELL
        if side == OrderSide.BUY and not (sl_price < limit_entry < tp_price):
            return False, "Bracket achat invalide : SL < entrée < TP requis."
        if side == OrderSide.SELL and not (tp_price < limit_entry < sl_price):
            return False, "Bracket vente invalide : TP < entrée < SL requis."

        # Sizing : risque plafonné + notional plafonné pour éviter les tailles explosives.
        risk_fraction = min(max(MAX_RISK_FRACTION, 0.0), 0.05)
        risk_budget = capital * risk_fraction
        notional_cap = min(buying_power, MAX_ORDER_NOTIONAL)
        quantite = int(risk_budget / dist_sl)
        quantite = min(quantite, int(notional_cap / limit_entry), MAX_SYMBOL_ORDER_QTY)
        if quantite < 1:
            return False, "Capital insuffisant."

        # ── Ordre Limit bracket (pas Market) ────────────────────
        ordre = LimitOrderRequest(
            symbol=trade["symbole"],
            qty=quantite,
            side=side,
            limit_price=round(limit_entry, 2),
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=round(tp_price, 2)),
            stop_loss=StopLossRequest(stop_price=round(sl_price, 2))
        )
        reponse = trading_client.submit_order(order_data=ordre)

        # ── Enregistrement pour surveillance anti-orphelin ───────
        with state.lock:
            state.pending_orders.append({
                "order_id":     str(reponse.id),
                "symbole":      trade["symbole"],
                "submitted_at": datetime.now(pytz.timezone("US/Eastern")),
                "limit_price":  round(limit_entry, 2),
            })

        atr_info = f" | ATR: {trade.get('atr', 0):.3f}" if trade.get("atr") else ""
        return True, (
            f"✅ Limit Bracket {quantite}× {trade['symbole']} "
            f"@ {limit_entry:.2f} | SL: {sl_price:.2f} | TP: {tp_price:.2f}{atr_info}"
        )
    except Exception as e:
        return False, f"Erreur Alpaca : {e}"


# ============================================================
# 7b. SURVEILLANCE ORDRES ORPHELINS
# ============================================================
ORPHAN_MINUTES = 15   # annulation si non rempli après N bougies M1

def orphan_watcher():
    """
    Tourne en arrière-plan toutes les 60s.
    Annule tout ordre Limit encore 'new' ou 'partially_filled'
    après ORPHAN_MINUTES minutes.
    """
    while True:
        time_module.sleep(60)
        now = datetime.now(pytz.timezone("US/Eastern"))
        to_remove = []

        with state.lock:
            pending_orders = list(state.pending_orders)

        for entry in pending_orders:
            age_minutes = (now - entry["submitted_at"]).total_seconds() / 60

            if age_minutes < ORPHAN_MINUTES:
                continue  # trop tôt

            order_id = entry["order_id"]
            try:
                order = trading_client.get_order_by_id(order_id)
                status = str(order.status)

                if status in ("new", "partially_filled", "accepted", "pending_new"):
                    trading_client.cancel_order_by_id(order_id)
                    msg = (
                        f"🗑️ Orphelin annulé : {entry['symbole']} "
                        f"@ {entry['limit_price']} "
                        f"(non rempli après {ORPHAN_MINUTES} min)"
                    )
                    print(msg)
                    # Injecte dans auto_executed pour traçabilité UI
                    with state.lock:
                        state.auto_executed.insert(0, {
                            "time":     now.strftime("%H:%M:%S"),
                            "symbole":  entry["symbole"],
                            "score":    0,
                            "result":   msg,
                            "ok":       False,
                            "auto":     True,
                            "auto_result": msg,
                        })
                # Rempli ou annulé → on le retire dans tous les cas
                to_remove.append(entry)

            except Exception as e:
                print(f"⚠️ Watcher erreur {order_id}: {e}")
                to_remove.append(entry)  # retire quand même pour ne pas boucler

        with state.lock:
            for entry in to_remove:
                try:
                    state.pending_orders.remove(entry)
                except ValueError:
                    pass

def start_background_threads():
    if not state.stream_started:
        state.stream_started = True
        t = threading.Thread(target=start_alpaca_stream, daemon=True, name="alpaca-ws")
        try:
            from streamlit.runtime.scriptrunner import add_script_run_ctx
            add_script_run_ctx(t)
        except Exception:
            pass
        t.start()

    if not state.watcher_started:
        state.watcher_started = True
        tw = threading.Thread(target=orphan_watcher, daemon=True, name="orphan-watcher")
        try:
            from streamlit.runtime.scriptrunner import add_script_run_ctx
            add_script_run_ctx(tw)
        except Exception:
            pass
        tw.start()

# ============================================================
# 8. INTERFACE
# ============================================================
start_background_threads()

st.markdown(
    f"""
    <section class="qt-page-header">
        <div class="qt-kicker">Live market terminal / SMC radar</div>
        <h1>ScalpBot Pro</h1>
        <p>
            Radar multi-timeframe pour signaux SMC, confluences EMA/VWAP, zones OB/FVG
            et execution Alpaca paper avec garde-fous de risque.
        </p>
        <div class="qt-status-row">
            <span class="qt-pill ok">Paper trading</span>
            <span class="qt-pill">{len(SYMBOLES)} symboles surveilles</span>
            <span class="qt-pill warn">Auto-trade verrouillable</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

# ── Auto-Trade ───────────────────────────────────────────────
with st.container():
    c1, c2, c3 = st.columns([2, 2, 4])
    with c1:
        auto_on = st.toggle(
            "🤖 Auto-Trade",
            value=st.session_state.get("auto_trade_on", False),
            key="auto_trade_on",
            help="Exécution automatique dès que le score dépasse le seuil"
        )
    with c2:
        auto_seuil = st.slider(
            "Seuil score", min_value=5, max_value=10,
            value=st.session_state.get("auto_seuil", 8),
            key="auto_seuil", disabled=not auto_on
        )
    with state.lock:
        state.auto_trade_on = bool(auto_on)
        state.auto_seuil = int(auto_seuil)
    with c3:
        if auto_on:
            st.error(f"🔴 AUTO-TRADE ACTIF — exécution automatique dès score ≥ {auto_seuil}/10")
        else:
            st.info("⚪ Mode manuel — tu valides chaque trade")

# ── Historique auto-trades ────────────────────────────────────
with state.lock:
    auto_history = list(state.auto_executed[:10])
    auto_history_count = len(state.auto_executed)

if auto_history:
    with st.expander(f"📋 Historique auto-trades ({auto_history_count})", expanded=False):
        for t in auto_history:
            icon = "✅" if t.get("ok") else "❌"
            st.markdown(
                f"{icon} `{t['time']}` **{t['symbole']}** score {t['score']}/10 "
                f"— {t.get('result', '')}"
            )

# ── Dashboard live ───────────────────────────────────────────
@st.fragment(run_every="1s")
def tableau_de_bord():
    with state.lock:
        trades = list(state.trade_queue[:5])

    if trades:
        st.subheader("🚨 Signaux de haute probabilité")
        for trade in trades:
            score     = trade.get("score", 0)
            score_col = "🟢" if score >= 7 else "🟡"
            auto_tag  = " 🤖 *auto-exécuté*" if trade.get("auto") else ""
            with st.expander(
                f"{trade['icone']} **{trade['type']}** sur **{trade['symbole']}** "
                f"à {trade['time']}  {score_col} {score}/10{auto_tag}",
                expanded=score >= 7 and not trade.get("auto")
            ):
                for r in trade.get("raisons", []):
                    st.markdown(f"&nbsp;&nbsp;• {r}")
                if not trade.get("auto"):
                    col1, col2 = st.columns([1, 1])
                    if col1.button(f"🚀 Exécuter {trade['symbole']}",
                                   key=f"btn_{trade['time']}_{trade['symbole']}",
                                   use_container_width=True):
                        ok, msg = executer_ordre(trade)
                        st.success(msg) if ok else st.error(msg)
                    if col2.button("🗑️ Ignorer",
                                   key=f"ign_{trade['time']}_{trade['symbole']}",
                                   use_container_width=True):
                        with state.lock:
                            if trade in state.trade_queue:
                                state.trade_queue.remove(trade)
                        st.rerun()
                else:
                    st.success(trade.get("auto_result", ""))
    else:
        st.info("🔍 En attente de données — marché calme ou hors session...")

    st.subheader("📊 Price Action multi-timeframe (M5 / M1)")
    for i in range(0, len(SYMBOLES), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(SYMBOLES):
                sym = SYMBOLES[i + j]
                with cols[j]:
                    fig = build_chart(sym)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True,
                                        config={"displayModeBar": False})
                    else:
                        st.info(f"⏳ En attente de données pour {sym}...")

tableau_de_bord()
