# ================================================================
# Mapa Bursátil Mundial — Streamlit (definitivo)
# ================================================================
# - Mapa blanco: Plotly (si disponible) / PyDeck (fallback)
# - Etiquetas cortas (emoji + %). Texto grande ~16-18
# - Una sola tabla; MA50 real (Yahoo Chart API)
# - Sidebar con filtros; KPIs; Pestañas
# - Conversión opcional a EUR con EURXXX=X
# - Caché con st.cache_data; sin pip en caliente
# ================================================================

from __future__ import annotations
import streamlit as st
import pandas as pd
import requests
import pytz
from datetime import datetime
from typing import Dict, Optional, Tuple, List

# -------- Plotly si existe; si no, PyDeck fallback ----------
PLOTLY_OK = True
try:
    import plotly.graph_objects as go
except Exception:
    PLOTLY_OK = False
    import pydeck as pdk  # viene con Streamlit

# ---------------- Config general ----------------
st.set_page_config(
    page_title="Mapa Bursátil Mundial",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Mercado catálogo ----------------
MARKETS: Dict[str, Dict] = {
    "^GSPC": {"name": "S&P 500", "country": "Estados Unidos", "currency": "USD", "tz": "America/New_York", "open": 9, "close": 16, "lat": 40.7069, "lon": -74.0113, "fallback": "SPY"},
    "^IXIC": {"name": "NASDAQ", "country": "Estados Unidos", "currency": "USD", "tz": "America/New_York", "open": 9, "close": 16, "lat": 40.7549, "lon": -73.9840, "fallback": None},
    "^GSPTSE": {"name": "TSX", "country": "Canadá", "currency": "CAD", "tz": "America/Toronto", "open": 9, "close": 16, "lat": 43.6487, "lon": -79.3817, "fallback": None},
    "^FTSE": {"name": "FTSE 100", "country": "Reino Unido", "currency": "GBP", "tz": "Europe/London", "open": 8, "close": 16, "lat": 51.5136, "lon": -0.0890, "fallback": None},
    "^GDAXI": {"name": "DAX", "country": "Alemania", "currency": "EUR", "tz": "Europe/Berlin", "open": 9, "close": 17, "lat": 50.1109, "lon": 8.6821, "fallback": None},
    "^FCHI": {"name": "CAC 40", "country": "Francia", "currency": "EUR", "tz": "Europe/Paris", "open": 9, "close": 17, "lat": 48.8566, "lon": 2.3522, "fallback": None},
    "^IBEX": {"name": "IBEX 35", "country": "España", "currency": "EUR", "tz": "Europe/Madrid", "open": 9, "close": 17, "lat": 40.4168, "lon": -3.7038, "fallback": None},
    "^N225": {"name": "Nikkei 225", "country": "Japón", "currency": "JPY", "tz": "Asia/Tokyo", "open": 9, "close": 15, "lat": 35.6828, "lon": 139.7595, "fallback": None},
    "000001.SS": {"name": "Shanghai Comp.", "country": "China", "currency": "CNY", "tz": "Asia/Shanghai", "open": 9, "close": 15, "lat": 31.2304, "lon": 121.4737, "fallback": "MCHI"},
    "^HSI": {"name": "Hang Seng", "country": "Hong Kong", "currency": "HKD", "tz": "Asia/Hong_Kong", "open": 9, "close": 16, "lat": 22.3080, "lon": 114.1716, "fallback": None},
    "^AXJO": {"name": "ASX 200", "country": "Australia", "currency": "AUD", "tz": "Australia/Sydney", "open": 10, "close": 16, "lat": -33.8688, "lon": 151.2093, "fallback": None},
    "^BVSP": {"name": "Bovespa", "country": "Brasil", "currency": "BRL", "tz": "America/Sao_Paulo", "open": 10, "close": 17, "lat": -23.5505, "lon": -46.6333, "fallback": None},
    "^MXX": {"name": "IPC México", "country": "México", "currency": "MXN", "tz": "America/Mexico_City", "open": 8, "close": 15, "lat": 19.4326, "lon": -99.1332, "fallback": None},
}

# ---------------- Yahoo Chart API ----------------
BASE_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}"

@st.cache_data(ttl=300)
def fetch_chart(sym: str, rng: str = "6mo", interval: str = "1d") -> Optional[dict]:
    try:
        r = requests.get(
            BASE_CHART.format(sym=sym),
            params={"range": rng, "interval": interval},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        res = data.get("chart", {}).get("result")
        return res[0] if res else None
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_intraday(sym: str) -> Optional[Dict]:
    res = fetch_chart(sym, rng="1d", interval="1m")
    if not res:
        return None
    meta = res.get("meta", {})
    current = meta.get("regularMarketPrice")
    prev = meta.get("previousClose")
    if current is None:
        q = res.get("indicators", {}).get("quote", [{}])[0]
        closes = [c for c in q.get("close", []) if c is not None]
        if closes:
            current = closes[-1]
            prev = closes[-2] if len(closes) > 1 else current
    if current is None or prev in (None, 0):
        return None
    chg = (current - prev) / prev * 100

    # rango último mes (para icono ⚡)
    rng_pct = None
    hist = fetch_chart(sym, rng="1mo", interval="1d")
    try:
        if hist:
            q = hist.get("indicators", {}).get("quote", [{}])[0]
            closes = [c for c in q.get("close", []) if c is not None]
            if len(closes) >= 2 and closes[-1] != 0:
                rng_pct = (max(closes) - min(closes)) / closes[-1] * 100
    except Exception:
        rng_pct = None

    return {
        "price": float(current),
        "prev": float(prev),
        "chg_pct": float(round(chg, 2)),
        "rng_pct": float(round(rng_pct, 2)) if rng_pct is not None else None,
        "time": datetime.utcnow().strftime("%H:%M UTC"),
    }

@st.cache_data(ttl=300)
def fetch_history(sym: str) -> Optional[pd.Series]:
    res = fetch_chart(sym, rng="6mo", interval="1d")
    if not res:
        return None
    q = res.get("indicators", {}).get("quote", [{}])[0]
    closes = [c for c in q.get("close", []) if c is not None]
    return pd.Series(closes) if closes else None

# ---------------- FX a EUR ----------------
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
    res = fetch_chart(tkr, rng="1d", interval="1m")
    if not res:
        return None
    meta = res.get("meta", {})
    last = meta.get("regularMarketPrice")
    if last is None:
        q = res.get("indicators", {}).get("quote", [{}])[0]
        closes = [c for c in q.get("close", []) if c is not None]
        last = closes[-1] if closes else None
    try:
        last = float(last)
        return (1.0 / last) if last != 0 else None
    except Exception:
        return None

# ---------------- Estado del mercado ----------------
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

# ---------------- Emojis / etiquetas cortas ----------------
def perf_to_emoji(chg: float, intraday_range: Optional[float], vol_threshold: float) -> str:
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

def short_label(chg_pct: float, emoji: str) -> str:
    # Solo emoji + variación %
    return f"{emoji} {chg_pct:+.2f}%"

# ---------------- Cargar mercado ----------------
def load_market(sym: str) -> Optional[Dict]:
    info = MARKETS[sym]
    data = fetch_intraday(sym)
    used = sym
    if data is None and info.get("fallback"):
        data = fetch_intraday(info["fallback"])
        used = info["fallback"] if data else sym
    if data is None:
        return None

    hist = fetch_history(used)
    ma50 = None
    if hist is not None and len(hist) >= 50:
        ma50 = float(pd.Series(hist).tail(50).mean())

    is_open, status, local_time = market_status(info["tz"], info["open"], info["close"])

    return {
        "symbol": sym,
        "used": used,
        "name": info["name"],
        "country": info["country"],
        "currency": info["currency"],
        "tz": info["tz"],
        "coords": (info["lat"], info["lon"]),
        "is_open": is_open,
        "status": status,
        "local_time": local_time,
        "price": data["price"],
        "prev": data["prev"],
        "chg_pct": data["chg_pct"],
        "rng_pct": data["rng_pct"],
        "ma50": ma50,
        "trend": ("📈 Alcista" if (ma50 is not None and data["price"] > ma50) else ("📉 Bajista" if ma50 else "—")),
        "updated": data["time"],
    }

# ---------------- Mapa (Plotly) ----------------
def draw_map_plotly(rows: List[Dict], show_eur: bool, vol_threshold: float) -> None:
    lats, lons, texts, hover = [], [], [], []
    for r in rows:
        mult = currency_to_eur_multiplier(r["currency"]) if show_eur else None
        eur_val = (r["price"] * mult) if (show_eur and mult) else None
        emoji = perf_to_emoji(r["chg_pct"], r["rng_pct"], vol_threshold)
        label = short_label(r["chg_pct"], emoji)

        hov = (
            f"<b>{r['name']}</b><br>"
            f"{r['country']} • {'🟢' if r['is_open'] else '🔴'} {r['status']} • {r['local_time']}<br>"
            f"Último: {r['price']:.2f} {r['currency']}"
        )
        if eur_val:
            hov += f" ≈ {eur_val:.2f} EUR"
        if r["ma50"] is not None:
            hov += f"<br>MA50: {r['ma50']:.2f} ({'📈' if 'Alcista' in r['trend'] else '📉'})"
        hov += f"<br>Variación: {r['chg_pct']:+.2f}%"

        lats.append(r["coords"][0]); lons.append(r["coords"][1])
        texts.append(label); hover.append(hov)

    fig = go.Figure(go.Scattergeo(
        lon=lons,
        lat=lats,
        text=texts,
        hovertemplate="%{text}<br>%{customdata}<extra></extra>",
        customdata=hover,
        mode="text+markers",
        marker=dict(size=10),
        textfont=dict(size=16, color="black"),  # texto grande, mapa blanco
    ))

    fig.update_geos(
        projection_type="natural earth",
        showcoastlines=True, coastlinecolor="#E5E5E5",
        showland=True, landcolor="#FFFFFF",
        showcountries=True, countrycolor="#E5E5E5",
        showocean=True, oceancolor="#FFFFFF",
        showlakes=True, lakecolor="#FFFFFF",
        lataxis_range=[-60, 75],
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=640,  # más alto
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- Mapa (PyDeck fallback) ----------------
def draw_map_pydeck(rows: List[Dict], show_eur: bool, vol_threshold: float) -> None:
    data = []
    for r in rows:
        emoji = perf_to_emoji(r["chg_pct"], r["rng_pct"], vol_threshold)
        label = short_label(r["chg_pct"], emoji)
        data.append({"lat": r["coords"][0], "lon": r["coords"][1], "label": label})

    df = pd.DataFrame(data)

    text_layer = pdk.Layer(
        "TextLayer",
        df,
        get_position='[lon, lat]',
        get_text="label",
        get_size=18,                # grande
        get_color=[0, 0, 0, 255],
        get_angle=0,
        pickable=True,
        billboard=True,
    )
    view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1.3)
    st.pydeck_chart(pdk.Deck(
        layers=[text_layer],
        initial_view_state=view_state,
        map_style="light",  # claro
        tooltip={"text": "{label}"},
    ))

# ---------------- Tabla única ----------------
def build_table(rows: List[Dict], show_eur: bool) -> None:
    data = []
    for r in rows:
        mult = currency_to_eur_multiplier(r["currency"]) if show_eur else None
        eur_val = (r["price"] * mult) if (show_eur and mult) else None
        data.append({
            "Mercado": r["name"],
            "Var %": r["chg_pct"],
            "Último": f"{r['price']:.2f} {r['currency']}",
            "MA50": round(r["ma50"], 2) if r["ma50"] is not None else None,
            "Estado": ("🟢" if r["is_open"] else "🔴"),
            "EUR": (f"{eur_val:.2f}" if eur_val else "—") if show_eur else "—",
        })
    df = pd.DataFrame(data)
    if df.empty:
        st.info("No hay datos para mostrar.")
    else:
        df = df.sort_values("Var %", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- KPIs ----------------
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

# ---------------- App ----------------
def main():
    st.title("🌍 Mapa Bursátil Mundial — Widget")
    st.caption("Monitor interactivo de bolsas globales con MA50 real y mapa geográfico")

    st.sidebar.header("🎛️ Panel de control")
    if st.sidebar.button("🔄 Actualizar datos", type="primary"):
        st.cache_data.clear()
        st.rerun()

    region = st.sidebar.selectbox("Región", ["Todos", "Norteamérica", "Europa", "Asia-Pacífico", "América Latina"])
    perf_filter = st.sidebar.selectbox("Rendimiento", ["Todos", "> 0%", "< 0%", "Entre -0.5% y +0.5%"])
    vol_thresh = st.sidebar.slider("Umbral ⚡ volatilidad (%)", 0.5, 5.0, 1.5, 0.1)
    show_eur = st.sidebar.toggle("Mostrar equivalente en EUR", value=False)

    rows: List[Dict] = []
    with st.spinner("Cargando mercados..."):
        for sym, info in MARKETS.items():
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
                rows.append(r)

    if perf_filter == "> 0%":
        rows = [r for r in rows if r["chg_pct"] > 0]
    elif perf_filter == "< 0%":
        rows = [r for r in rows if r["chg_pct"] < 0]
    elif perf_filter == "Entre -0.5% y +0.5%":
        rows = [r for r in rows if -0.5 <= r["chg_pct"] <= 0.5]

    tab_map, tab_table, tab_settings, tab_help = st.tabs(["🗺️ Mapa", "📋 Resumen", "⚙️ Ajustes", "❓ Ayuda"])

    with tab_map:
        kpis(rows)
        if PLOTLY_OK:
            draw_map_plotly(rows, show_eur, vol_thresh)
        else:
            st.warning("Plotly no está disponible en este entorno. Mostrando mapa fallback con PyDeck.")
            draw_map_pydeck(rows, show_eur, vol_thresh)
        st.markdown("**Leyenda**  ☀️ > +1%   ⛅ −0,5% a +0,5%   🌥 −1% a −0,5%   🌧 < −1%   ⚡ volatilidad alta")

    with tab_table:
        st.subheader("Tabla única de mercados")
        build_table(rows, show_eur)

    with tab_settings:
        st.write("Ajusta filtros en la barra lateral. Usa ‘Actualizar datos’ para limpiar caché y recargar.")
        st.code("""
- Región: filtra por zona geográfica.
- Rendimiento: filtra por variación intradía.
- Umbral ⚡: si el rango % del último mes supera el umbral, el icono será ⚡.
- EUR: convierte precios a euros con EURXXX=X.
        """, language="markdown")

    with tab_help:
        st.markdown("""
**Guía rápida**
- Mapa blanco; etiquetas cortas (emoji + %).
- MA50 calculada con históricos (6 meses, 1d).
- Estado abierto/cerrado aproximado por horario local.
- Si Yahoo falla en un índice, se intenta ETF fallback.
- Datos educativos, pueden tener retraso.
        """)

    st.caption(f"Actualizado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

if __name__ == "__main__":
    main()
