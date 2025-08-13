# ================================================================
# MAPA BURSÁTIL MUNDIAL — Streamlit (v4)
# ================================================================
# Reestructura completa con:
# - Una sola tabla resumen
# - Mapa mundial interactivo (Plotly scattergeo, sin Mapbox)
# - MA50 real por mercado (a partir de históricos Yahoo Chart API)
# - UI con sidebar de filtros, pestañas (Mapa, Resumen, Ajustes, Ayuda)
# - Conversión opcional a EUR con tickers FX de Yahoo
# - Cache y manejo de errores suave
#
# Requisitos recomendados:
# streamlit>=1.28.0, pandas>=1.5.0, requests>=2.25.0, pytz>=2023.3, plotly>=5.10.0
# ================================================================

from __future__ import annotations
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional, Tuple, List
import logging
import math

# Plotly para el mapa
import plotly.graph_objects as go

# ----------------------------
# Configuración general
# ----------------------------
st.set_page_config(
    page_title="Mapa Bursátil Mundial",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mapa_bursatil")

# ----------------------------
# Catálogo de mercados (coordenadas, TZ, etc.)
# lat/lon ~ ciudades de los parqués principales
# ----------------------------
MARKETS: Dict[str, Dict] = {
    # Norteamérica
    "^GSPC": {"name": "S&P 500", "country": "Estados Unidos", "currency": "USD", "tz": "America/New_York", "open": 9, "close": 16, "lat": 40.7069, "lon": -74.0113, "fallback": "SPY"},
    "^IXIC": {"name": "NASDAQ", "country": "Estados Unidos", "currency": "USD", "tz": "America/New_York", "open": 9, "close": 16, "lat": 40.7549, "lon": -73.9840, "fallback": None},
    "^GSPTSE": {"name": "TSX", "country": "Canadá", "currency": "CAD", "tz": "America/Toronto", "open": 9, "close": 16, "lat": 43.6487, "lon": -79.3817, "fallback": None},
    # Europa
    "^FTSE": {"name": "FTSE 100", "country": "Reino Unido", "currency": "GBP", "tz": "Europe/London", "open": 8, "close": 16, "lat": 51.5136, "lon": -0.0890, "fallback": None},
    "^GDAXI": {"name": "DAX", "country": "Alemania", "currency": "EUR", "tz": "Europe/Berlin", "open": 9, "close": 17, "lat": 50.1109, "lon": 8.6821, "fallback": None},
    "^FCHI": {"name": "CAC 40", "country": "Francia", "currency": "EUR", "tz": "Europe/Paris", "open": 9, "close": 17, "lat": 48.8566, "lon": 2.3522, "fallback": None},
    "^IBEX": {"name": "IBEX 35", "country": "España", "currency": "EUR", "tz": "Europe/Madrid", "open": 9, "close": 17, "lat": 40.4168, "lon": -3.7038, "fallback": None},
    # Asia-Pacífico
    "^N225": {"name": "Nikkei 225", "country": "Japón", "currency": "JPY", "tz": "Asia/Tokyo", "open": 9, "close": 15, "lat": 35.6828, "lon": 139.7595, "fallback": None},
    "000001.SS": {"name": "Shanghai Comp.", "country": "China", "currency": "CNY", "tz": "Asia/Shanghai", "open": 9, "close": 15, "lat": 31.2304, "lon": 121.4737, "fallback": "MCHI"},
    "^HSI": {"name": "Hang Seng", "country": "Hong Kong", "currency": "HKD", "tz": "Asia/Hong_Kong", "open": 9, "close": 16, "lat": 22.3080, "lon": 114.1716, "fallback": None},
    "^AXJO": {"name": "ASX 200", "country": "Australia", "currency": "AUD", "tz": "Australia/Sydney", "open": 10, "close": 16, "lat": -33.8688, "lon": 151.2093, "fallback": None},
    # LatAm
    "^BVSP": {"name": "Bovespa", "country": "Brasil", "currency": "BRL", "tz": "America/Sao_Paulo", "open": 10, "close": 17, "lat": -23.5505, "lon": -46.6333, "fallback": None},
    "^MXX": {"name": "IPC México", "country": "México", "currency": "MXN", "tz": "America/Mexico_City", "open": 8, "close": 15, "lat": 19.4326, "lon": -99.1332, "fallback": None},
}

# ----------------------------
# Utilidades de tiempo/estado
# ----------------------------

def market_status(tz: str, open_h: int, close_h: int) -> Tuple[bool, str, str]:
    try:
        zone = pytz.timezone(tz)
        now_local = datetime.now(zone)
        is_weekend = now_local.weekday() >= 5
        is_open = (open_h <= now_local.hour < close_h) and not is_weekend
        status = "Abierto" if is_open else ("Cerrado (Fin de semana)" if is_weekend else "Cerrado")
        return is_open, status, now_local.strftime("%H:%M")
    except Exception:
        return False, "Error", "N/A"

# ----------------------------
# Yahoo chart helpers (sin yfinance)
# ----------------------------

BASE_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"

@st.cache_data(ttl=300)
def fetch_chart(sym: str, rng: str = "6mo", interval: str = "1d") -> Optional[dict]:
    try:
        resp = requests.get(
            BASE_CHART.format(sym=sym),
            params={"range": rng, "interval": interval},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        res = data.get("chart", {}).get("result")
        return res[0] if res else None
    except Exception as e:
        log.warning(f"fetch_chart error {sym}: {e}")
        return None

@st.cache_data(ttl=300)
def fetch_intraday(sym: str) -> Optional[Dict]:
    result = fetch_chart(sym, rng="1d", interval="1m")
    if not result:
        return None
    meta = result.get("meta", {})
    current = meta.get("regularMarketPrice")
    prev = meta.get("previousClose")
    vol = meta.get("regularMarketVolume", 0)

    # Si no hay current, toma último close válido del intradía
    if current is None:
        q = result.get("indicators", {}).get("quote", [{}])[0]
        closes = [c for c in q.get("close", []) if c is not None]
        if closes:
            current = closes[-1]
            prev = closes[-2] if len(closes) > 1 else current

    if current is None or prev in (None, 0):
        return None

    chg = (current - prev) / prev * 100
    return {
        "price": float(current),
        "prev": float(prev),
        "chg_pct": float(round(chg, 2)),
        "volume": int(vol) if vol else 0,
        "time": datetime.utcnow().strftime("%H:%M UTC"),
    }

@st.cache_data(ttl=300)
def fetch_history(sym: str) -> Optional[pd.Series]:
    result = fetch_chart(sym, rng="6mo", interval="1d")
    if not result:
        return None
    q = result.get("indicators", {}).get("quote", [{}])[0]
    closes = [c for c in q.get("close", []) if c is not None]
    if not closes:
        return None
    return pd.Series(closes)

@st.cache_data(ttl=600)
def fetch_fx_ratio(to_eur_ticker: str) -> Optional[float]:
    """
    Devuelve FX para convertir MONEDA_ACTIVO → EUR usando tickers tipo "EURUSD=X".
    Regla: si P = precio en MONEDA_ACTIVO, entonces EUR = P / (EURXXX=X)
    """
    res = fetch_chart(to_eur_ticker, rng="1d", interval="1m")
    if not res:
        return None
    meta = res.get("meta", {})
    last = meta.get("regularMarketPrice")
    if last is None:
        q = res.get("indicators", {}).get("quote", [{}])[0]
        closes = [c for c in q.get("close", []) if c is not None]
        last = closes[-1] if closes else None
    return float(last) if last else None

FX_MAP = {
    "USD": "EURUSD=X",
    "GBP": "EURGBP=X",
    "JPY": "EURJPY=X",
    "CAD": "EURCAD=X",
    "HKD": "EURHKD=X",
    "AUD": "EURAUD=X",
    "CNY": "EURCNY=X",
    "BRL": "EURBRL=X",
    "MXN": "EURMXN=X",
    "EUR": None,
}

@st.cache_data(ttl=600)
def currency_to_eur_multiplier(code: str) -> Optional[float]:
    if code == "EUR":
        return 1.0
    tkr = FX_MAP.get(code)
    if not tkr:
        return None
    v = fetch_fx_ratio(tkr)
    return (1.0 / v) if v and v != 0 else None

# ----------------------------
# Lógica de color/emojis
# ----------------------------

def perf_to_emoji(chg: float, intraday_range: Optional[float] = None, vol_threshold: float = 1.5) -> str:
    if intraday_range is not None and intraday_range > vol_threshold:
        return "⚡"
    if chg > 1.0:
        return "☀️"
    if -0.5 <= chg <= 0.5:
        return "⛅"
    if -1.0 <= chg < -0.5:
        return "🌥"
    if chg < -1.0:
        return "🌧"
    return "☁️"

# ----------------------------
# Carga de datos por mercado
# ----------------------------

def load_market(sym: str) -> Optional[Dict]:
    info = MARKETS[sym]
    # 1) intradía
    data = fetch_intraday(sym)
    used = sym
    if data is None and info.get("fallback"):
        data = fetch_intraday(info["fallback"])
        used = info["fallback"] if data else sym
    if data is None:
        return None
    # 2) MA50 con históricos reales
    hist = fetch_history(used)
    ma50 = None
    intraday_rng = None
    if hist is not None and len(hist) >= 50:
        ma50 = float(pd.Series(hist).tail(50).mean())
        # Volatilidad simple del último mes como rango %
        last_21 = pd.Series(hist).tail(21)
        if len(last_21) >= 2:
            intraday_rng = float((last_21.max() - last_21.min()) / last_21.iloc[-1] * 100)
    trend = "alcista" if (ma50 is not None and data["price"] > ma50) else ("bajista" if ma50 else "neutral")
    return {
        "symbol": sym,
        "used": used,
        "name": info["name"],
        "country": info["country"],
        "currency": info["currency"],
        "tz": info["tz"],
        "coords": (info["lat"], info["lon"]),
        "is_open": market_status(info["tz"], info["open"], info["close"])[0],
        "status": market_status(info["tz"], info["open"], info["close"])[1],
        "local_time": market_status(info["tz"], info["open"], info["close"])[2],
        "price": data["price"],
        "prev": data["prev"],
        "chg_pct": data["chg_pct"],
        "volume": data["volume"],
        "ma50": ma50,
        "trend": trend,
        "rng_pct": intraday_rng,
        "updated": data["time"],
    }

# ----------------------------
# Construcción del mapa Plotly
# ----------------------------

def build_map(rows: List[Dict], show_eur: bool) -> None:
    lats, lons, texts, hover = [], [], [], []
    for r in rows:
        lat, lon = r["coords"]
        lats.append(lat)
        lons.append(lon)
        mult = currency_to_eur_multiplier(r["currency"]) if show_eur else None
        eur_val = (r["price"] * mult) if (show_eur and mult) else None
        emoji = perf_to_emoji(r["chg_pct"], r["rng_pct"])
        label = f"{emoji} {r['name']} ({r['country']}) {r['chg_pct']:+.2f}%"
        texts.append(label)
        hov = (
            f"<b>{r['name']}</b> — {r['country']}<br>"
            f"Estado: {'🟢' if r['is_open'] else '🔴'} {r['status']} • {r['local_time']}<br>"
            f"Último: {r['price']:.2f} {r['currency']}"
        )
        if eur_val:
            hov += f" ≈ {eur_val:.2f} EUR"
        if r["ma50"]:
            hov += f"<br>MA50: {r['ma50']:.2f} ({'📈' if r['trend']=='alcista' else '📉'})"
        hov += f"<br>Variación: {r['chg_pct']:+.2f}%"
        hover.append(hov)

    fig = go.Figure(go.Scattergeo(
        lon=lons,
        lat=lats,
        text=texts,
        hovertemplate="%{text}<br>%{customdata}<extra></extra>",
        customdata=hover,
        mode="text+markers",
        marker=dict(size=8),
    ))
    fig.update_geos(
        showcountries=True,
        showland=True,
        landcolor="rgb(240,240,240)",
        lataxis_range=[-60, 75],
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=520)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# Tabla única (ordenable)
# ----------------------------

def build_table(rows: List[Dict], show_eur: bool) -> None:
    table = []
    for r in rows:
        mult = currency_to_eur_multiplier(r["currency"]) if show_eur else None
        eur_val = (r["price"] * mult) if (show_eur and mult) else None
        table.append({
            "Mercado": r["name"],
            "País": r["country"],
            "Precio": f"{r['price']:.2f} {r['currency']}",
            "Precio (EUR)": (f"{eur_val:.2f} EUR" if eur_val else "—"),
            "Var %": r["chg_pct"],
            "MA50": (round(r["ma50"], 2) if r["ma50"] else None),
            "Tendencia": ("📈 Alcista" if r["trend"] == "alcista" else ("📉 Bajista" if r["trend"] == "bajista" else "—")),
            "Estado": ("🟢 Abierto" if r["is_open"] else "🔴 Cerrado"),
            "Hora local": r["local_time"],
        })
    df = pd.DataFrame(table)
    if not df.empty:
        df = df.sort_values("Var %", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos para mostrar.")

# ----------------------------
# KPIs y filtros
# ----------------------------

def kpis(rows: List[Dict]) -> None:
    if not rows:
        return
    pos = sum(1 for r in rows if r["chg_pct"] > 0)
    neg = sum(1 for r in rows if r["chg_pct"] < 0)
    avg = sum(r["chg_pct"] for r in rows) / len(rows)
    best = max(rows, key=lambda r: r["chg_pct"])
    worst = min(rows, key=lambda r: r["chg_pct"])    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Mercados en verde", pos)
    with c2: st.metric("Mercados en rojo", neg)
    with c3: st.metric("% medio", f"{avg:+.2f}%")
    with c4: st.metric("Mayor ↑ / ↓", f"{best['name']} {best['chg_pct']:+.2f}% / {worst['name']} {worst['chg_pct']:+.2f}%")

# ----------------------------
# App principal
# ----------------------------

def main():
    st.title("🌍 Mapa Bursátil Mundial — Widget")
    st.caption("Monitor interactivo de bolsas globales con MA50 real y mapa geográfico")

    # Sidebar
    st.sidebar.header("🎛️ Panel de control")
    if st.sidebar.button("🔄 Actualizar datos", type="primary"):
        st.cache_data.clear()
        st.rerun()

    regions = ["Todos", "Norteamérica", "Europa", "Asia-Pacífico", "América Latina"]
    region = st.sidebar.selectbox("Región", regions)

    perf_filter = st.sidebar.selectbox("Rendimiento", ["Todos", "> 0%", "< 0%", "Entre -0.5% y +0.5%"])

    vol_thresh = st.sidebar.slider("Umbral ⚡ volatilidad (%)", 0.5, 5.0, 1.5, 0.1)
    show_eur = st.sidebar.toggle("Mostrar equivalente en EUR", value=False)

    # Carga y filtrado
    rows: List[Dict] = []
    with st.spinner("Cargando mercados..."):
        for sym, info in MARKETS.items():
            # Filtro por región simple por país
            region_ok = (
                region == "Todos" or
                (region == "Norteamérica" and info["tz"].startswith("America/") and info["country"] in ["Estados Unidos", "Canadá"]) or
                (region == "Europa" and info["tz"].startswith("Europe/")) or
                (region == "Asia-Pacífico" and info["tz"].startswith("Asia/")) or
                (region == "América Latina" and info["country"] in ["Brasil", "México"])
            )
            if not region_ok:
                continue
            r = load_market(sym)
            if r:
                # recalcula emoji con umbral de volatilidad
                r["emoji"] = perf_to_emoji(r["chg_pct"], r["rng_pct"], vol_thresh)
                rows.append(r)

    # Filtro por rendimiento
    if perf_filter == "> 0%":
        rows = [r for r in rows if r["chg_pct"] > 0]
    elif perf_filter == "< 0%":
        rows = [r for r in rows if r["chg_pct"] < 0]
    elif perf_filter == "Entre -0.5% y +0.5%":
        rows = [r for r in rows if -0.5 <= r["chg_pct"] <= 0.5]

    # Pestañas
    tabs = st.tabs(["🗺️ Mapa", "📋 Resumen", "⚙️ Ajustes", "❓ Ayuda"])    

    with tabs[0]:
        kpis(rows)
        build_map(rows, show_eur)
        st.markdown("""
        **Leyenda**  
        ☀️ sube > +1% &nbsp;&nbsp; ⛅ plano −0,5% a +0,5% &nbsp;&nbsp; 🌥 baja leve −1% a −0,5% &nbsp;&nbsp; 🌧 baja < −1% &nbsp;&nbsp; ⚡ alta volatilidad (> umbral)
        """)

    with tabs[1]:
        st.subheader("Tabla única de mercados")
        build_table(rows, show_eur)

    with tabs[2]:
        st.write("Ajusta filtros en la barra lateral. El umbral de ⚡ aplica a la etiqueta del mapa. Usa ‘Actualizar datos’ para forzar recarga y limpiar caché.")
        st.code("""
        - Región: filtra los mercados por zona geográfica.
        - Rendimiento: filtra por variación intradía.
        - Umbral volatilidad: si el rango % mensual supera el umbral, el icono será ⚡.
        - EUR: convierte precios a euros con tickers EURXXX=X.
        """, language="markdown")

    with tabs[3]:
        st.markdown("""
        **Guía rápida**
        - El mapa usa **Plotly scattergeo**, no requiere claves ni Mapbox.
        - La **MA50** se calcula con históricos reales de Yahoo Chart API (6 meses, 1d).
        - El estado **Abierto/Cerrado** se aproxima por horario local del parqué.
        - Solo hay **una tabla resumen** (esta) para evitar duplicados.
        - Si Yahoo no devuelve datos para un índice, se intenta un **ETF fallback**.
        - Todos los datos son **educativos** y pueden estar sujetos a retrasos.
        """)

    st.caption(f"Actualizado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error en la aplicación: {e}")
        log.exception(e)
