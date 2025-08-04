# ====================================================================
# MERCADOS FINANCIEROS GLOBALES - WIDGET EN TIEMPO REAL
# ====================================================================
# Aplicación Streamlit para monitorear los principales índices bursátiles
# mundiales con datos en tiempo real y visualización tipo mapa meteorológico
# ====================================================================

# 1. INSTALACIÓN DE LIBRERÍAS REQUERIDAS
# Solo usa librerías estándar de Streamlit Cloud - NO requiere instalación adicional

# 2. IMPORTACIÓN DE LIBRERÍAS
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import pytz
import json
import time
import random
from typing import Dict, List, Tuple, Optional
import logging

# 3. CONFIGURACIÓN Y VARIABLES GLOBALES
# ====================================================================

# Configuración de página
st.set_page_config(
    page_title="🌍 Mercados Globales | Widget Financiero",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Diccionario de mercados globales con información completa
GLOBAL_MARKETS = {
    # NORTEAMÉRICA
    "^GSPC": {
        "name": "S&P 500",
        "country": "Estados Unidos",
        "flag": "🇺🇸",
        "continent": "Norteamérica",
        "timezone": "America/New_York",
        "market_open": 9,
        "market_close": 16,
        "currency": "USD",
        "description": "Índice de las 500 empresas más importantes de EE.UU.",
        "base_price": 5800
    },
    "^IXIC": {
        "name": "NASDAQ",
        "country": "Estados Unidos", 
        "flag": "🇺🇸",
        "continent": "Norteamérica",
        "timezone": "America/New_York",
        "market_open": 9,
        "market_close": 16,
        "currency": "USD",
        "description": "Índice tecnológico principal de EE.UU.",
        "base_price": 19500
    },
    "^GSPTSE": {
        "name": "TSX",
        "country": "Canadá",
        "flag": "🇨🇦",
        "continent": "Norteamérica", 
        "timezone": "America/Toronto",
        "market_open": 9,
        "market_close": 16,
        "currency": "CAD",
        "description": "Índice principal de la bolsa de Toronto",
        "base_price": 25200
    },
    
    # EUROPA
    "^FTSE": {
        "name": "FTSE 100",
        "country": "Reino Unido",
        "flag": "🇬🇧",
        "continent": "Europa",
        "timezone": "Europe/London",
        "market_open": 8,
        "market_close": 16,
        "currency": "GBP",
        "description": "100 empresas más grandes del Reino Unido",
        "base_price": 8300
    },
    "^GDAXI": {
        "name": "DAX",
        "country": "Alemania",
        "flag": "🇩🇪", 
        "continent": "Europa",
        "timezone": "Europe/Berlin",
        "market_open": 9,
        "market_close": 17,
        "currency": "EUR",
        "description": "Índice de las 40 empresas principales de Alemania",
        "base_price": 21400
    },
    "^FCHI": {
        "name": "CAC 40",
        "country": "Francia",
        "flag": "🇫🇷",
        "continent": "Europa", 
        "timezone": "Europe/Paris",
        "market_open": 9,
        "market_close": 17,
        "currency": "EUR",
        "description": "40 empresas más importantes de Francia",
        "base_price": 7520
    },
    "^IBEX": {
        "name": "IBEX 35",
        "country": "España",
        "flag": "🇪🇸",
        "continent": "Europa",
        "timezone": "Europe/Madrid", 
        "market_open": 9,
        "market_close": 17,
        "currency": "EUR",
        "description": "35 empresas principales de España",
        "base_price": 12150
    },
    
    # ASIA-PACÍFICO
    "^N225": {
        "name": "Nikkei 225",
        "country": "Japón",
        "flag": "🇯🇵",
        "continent": "Asia-Pacífico",
        "timezone": "Asia/Tokyo",
        "market_open": 9,
        "market_close": 15,
        "currency": "JPY", 
        "description": "225 empresas principales de Japón",
        "base_price": 39700
    },
    "000001.SS": {
        "name": "Shanghai Composite",
        "country": "China",
        "flag": "🇨🇳",
        "continent": "Asia-Pacífico",
        "timezone": "Asia/Shanghai",
        "market_open": 9,
        "market_close": 15,
        "currency": "CNY",
        "description": "Índice compuesto de Shanghai",
        "base_price": 3320
    },
    "^HSI": {
        "name": "Hang Seng",
        "country": "Hong Kong",
        "flag": "🇭🇰", 
        "continent": "Asia-Pacífico",
        "timezone": "Asia/Hong_Kong",
        "market_open": 9,
        "market_close": 16,
        "currency": "HKD",
        "description": "Índice principal de Hong Kong",
        "base_price": 19750
    },
    "^AXJO": {
        "name": "ASX 200",
        "country": "Australia",
        "flag": "🇦🇺",
        "continent": "Asia-Pacífico",
        "timezone": "Australia/Sydney",
        "market_open": 10,
        "market_close": 16,
        "currency": "AUD",
        "description": "200 empresas principales de Australia",
        "base_price": 8420
    },
    
    # AMÉRICA LATINA
    "^BVSP": {
        "name": "Bovespa",
        "country": "Brasil",
        "flag": "🇧🇷",
        "continent": "América Latina",
        "timezone": "America/Sao_Paulo",
        "market_open": 10,
        "market_close": 17,
        "currency": "BRL",
        "description": "Índice principal de Brasil",
        "base_price": 122800
    },
    "^MXX": {
        "name": "IPC",
        "country": "México",
        "flag": "🇲🇽",
        "continent": "América Latina",
        "timezone": "America/Mexico_City",
        "market_open": 8,
        "market_close": 15,
        "currency": "MXN",
        "description": "Índice de Precios y Cotizaciones de México",
        "base_price": 55800
    }
}

# Configuración de emojis meteorológicos por rendimiento
WEATHER_EMOJIS = {
    "strong_gain": "☀️",      # Ganancia fuerte (>2%)
    "moderate_gain": "🌤️",   # Ganancia moderada (0.5% - 2%)
    "slight_gain": "⛅",     # Ganancia leve (0% - 0.5%)
    "neutral": "☁️",         # Neutral (-0.5% - 0%)
    "slight_loss": "🌧️",    # Pérdida leve (-0.5% - -1%)
    "moderate_loss": "⛈️",   # Pérdida moderada (-1% - -2.5%)
    "strong_loss": "🌩️"      # Pérdida fuerte (<-2.5%)
}

# 4. FUNCIONES PRINCIPALES
# ====================================================================

@st.cache_data(ttl=300)  # Cache por 5 minutos
def fetch_market_data_yahoo_api(symbol: str) -> Optional[Dict]:
    """
    Intenta obtener datos reales de Yahoo Finance API
    
    Args:
        symbol: Símbolo del índice (ej: ^GSPC)
        
    Returns:
        Diccionario con datos del mercado o None si hay error
    """
    try:
        # Intentar Yahoo Finance API pública
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                
                if 'meta' in result:
                    meta = result['meta']
                    
                    # Obtener precios
                    current_price = meta.get('regularMarketPrice')
                    previous_close = meta.get('previousClose')
                    volume = meta.get('regularMarketVolume', 0)
                    
                    # Si no hay precio actual, usar datos históricos
                    if not current_price and 'indicators' in result:
                        quotes = result['indicators']['quote'][0]
                        closes = quotes.get('close', [])
                        valid_closes = [c for c in closes if c is not None]
                        if valid_closes:
                            current_price = valid_closes[-1]
                            if len(valid_closes) > 1:
                                previous_close = valid_closes[-2]
                    
                    if current_price and previous_close and previous_close > 0:
                        change_percent = ((current_price - previous_close) / previous_close) * 100
                        
                        # Calcular MA50 si hay suficientes datos
                        ma50 = None
                        ma50_trend = "neutral"
                        
                        if 'indicators' in result and 'quote' in result['indicators']:
                            quotes = result['indicators']['quote'][0]
                            closes = quotes.get('close', [])
                            valid_closes = [c for c in closes if c is not None]
                            
                            if len(valid_closes) >= 50:
                                ma50 = sum(valid_closes[-50:]) / 50
                                ma50_trend = "alcista" if current_price > ma50 else "bajista"
                        
                        return {
                            "symbol": symbol,
                            "current_price": round(float(current_price), 2),
                            "previous_close": round(float(previous_close), 2),
                            "change_percent": round(float(change_percent), 2),
                            "change_absolute": round(float(current_price - previous_close), 2),
                            "volume": int(volume) if volume else 0,
                            "ma50": round(float(ma50), 2) if ma50 else None,
                            "ma50_trend": ma50_trend,
                            "last_updated": datetime.now().strftime("%H:%M:%S"),
                            "data_source": "🟢 Yahoo Finance API"
                        }
        
    except Exception as e:
        logger.warning(f"Error con Yahoo API para {symbol}: {str(e)}")
    
    return None

def generate_realistic_market_data(symbol: str, market_info: Dict) -> Dict:
    """
    Genera datos realistas basados en patrones reales de mercado
    
    Args:
        symbol: Símbolo del mercado
        market_info: Información del mercado
        
    Returns:
        Diccionario con datos simulados realistas
    """
    base_price = market_info.get("base_price", 1000)
    
    # Obtener estado del mercado para influir en la volatilidad
    market_status = get_market_status(
        market_info["timezone"],
        market_info["market_open"],
        market_info["market_close"]
    )
    
    # Ajustar volatilidad según si el mercado está abierto
    if market_status["is_open"]:
        # Mayor volatilidad cuando está abierto
        volatility = random.uniform(0.005, 0.025)  # 0.5% - 2.5%
    else:
        # Menor volatilidad cuando está cerrado
        volatility = random.uniform(0.001, 0.015)  # 0.1% - 1.5%
    
    # Sesgo ligeramente alcista (mercados tienden a subir a largo plazo)
    bias = random.uniform(-0.003, 0.005)  # Sesgo hacia el alza
    
    # Calcular precio actual
    price_change = (volatility + bias) * random.choice([-1, 1])
    current_price = base_price * (1 + price_change)
    previous_close = base_price * (1 + price_change - random.uniform(0.001, 0.01))
    
    # Calcular cambio porcentual
    change_percent = ((current_price - previous_close) / previous_close) * 100
    
    # MA50 simulado (tendencia general)
    ma50_bias = random.choice([1, 1, 1, -1])  # 75% probabilidad alcista
    ma50 = current_price * (1 + (ma50_bias * random.uniform(0.01, 0.05)))
    ma50_trend = "alcista" if current_price > ma50 else "bajista"
    
    # Volumen simulado proporcional al tamaño del mercado
    volume_base = max(1000000, int(base_price * 1000))
    volume = random.randint(int(volume_base * 0.5), int(volume_base * 2))
    
    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "previous_close": round(previous_close, 2),
        "change_percent": round(change_percent, 2),
        "change_absolute": round(current_price - previous_close, 2),
        "volume": volume,
        "ma50": round(ma50, 2),
        "ma50_trend": ma50_trend,
        "last_updated": datetime.now().strftime("%H:%M:%S"),
        "data_source": "🟡 Simulación Realista"
    }

def fetch_market_data(symbol: str) -> Optional[Dict]:
    """
    Obtiene datos del mercado, primero intenta fuentes reales, luego simula
    
    Args:
        symbol: Símbolo del índice
        
    Returns:
        Diccionario con datos del mercado
    """
    if symbol not in GLOBAL_MARKETS:
        return None
        
    market_info = GLOBAL_MARKETS[symbol]
    
    # Intentar obtener datos reales primero
    real_data = fetch_market_data_yahoo_api(symbol)
    if real_data:
        return real_data
    
    # Si no se pueden obtener datos reales, generar datos realistas
    return generate_realistic_market_data(symbol, market_info)

def get_weather_emoji(change_percent: float) -> str:
    """
    Determina el emoji meteorológico según el cambio porcentual
    
    Args:
        change_percent: Cambio porcentual del índice
        
    Returns:
        Emoji correspondiente al rendimiento
    """
    if change_percent > 2:
        return WEATHER_EMOJIS["strong_gain"]
    elif change_percent > 0.5:
        return WEATHER_EMOJIS["moderate_gain"] 
    elif change_percent > 0:
        return WEATHER_EMOJIS["slight_gain"]
    elif change_percent > -0.5:
        return WEATHER_EMOJIS["neutral"]
    elif change_percent > -1:
        return WEATHER_EMOJIS["slight_loss"]
    elif change_percent > -2.5:
        return WEATHER_EMOJIS["moderate_loss"]
    else:
        return WEATHER_EMOJIS["strong_loss"]

def get_market_status(timezone_str: str, market_open: int, market_close: int) -> Dict:
    """
    Determina si el mercado está abierto o cerrado
    
    Args:
        timezone_str: Zona horaria del mercado
        market_open: Hora de apertura (24h format)
        market_close: Hora de cierre (24h format)
        
    Returns:
        Diccionario con estado del mercado y hora local
    """
    try:
        tz = pytz.timezone(timezone_str)
        local_time = datetime.now(tz)
        current_hour = local_time.hour
        is_weekend = local_time.weekday() >= 5
        
        if is_weekend:
            status = "Cerrado (Fin de semana)"
            is_open = False
        elif market_open <= current_hour < market_close:
            status = "Abierto"
            is_open = True
        else:
            status = "Cerrado"
            is_open = False
            
        return {
            "is_open": is_open,
            "status": status,
            "local_time": local_time.strftime("%H:%M"),
            "local_date": local_time.strftime("%d/%m/%Y")
        }
        
    except Exception as e:
        logger.error(f"Error calculando estado del mercado: {str(e)}")
        return {
            "is_open": False,
            "status": "Error",
            "local_time": "N/A",
            "local_date": "N/A"
        }

def format_number(number: float, currency: str = "") -> str:
    """
    Formatea números para mostrar de manera legible
    
    Args:
        number: Número a formatear
        currency: Moneda (opcional)
        
    Returns:
        Número formateado como string
    """
    if abs(number) >= 1_000_000:
        return f"{number/1_000_000:.1f}M {currency}".strip()
    elif abs(number) >= 1_000:
        return f"{number/1_000:.1f}K {currency}".strip()
    else:
        return f"{number:.2f} {currency}".strip()

def create_world_map_visualization(market_data: Dict) -> None:
    """
    Crea visualización tipo mapa mundial con emojis meteorológicos
    
    Args:
        market_data: Diccionario con datos de todos los mercados
    """
    st.markdown("### 🌍 Mapa Mundial de Mercados Financieros")
    
    # Organizar por continentes
    continents = {}
    for symbol, market_info in GLOBAL_MARKETS.items():
        continent = market_info["continent"]
        if continent not in continents:
            continents[continent] = []
        
        # Agregar datos del mercado si están disponibles
        if symbol in market_data and market_data[symbol]:
            data = market_data[symbol]
            weather_emoji = get_weather_emoji(data["change_percent"])
            market_status = get_market_status(
                market_info["timezone"],
                market_info["market_open"], 
                market_info["market_close"]
            )
            
            continents[continent].append({
                "symbol": symbol,
                "info": market_info,
                "data": data,
                "weather": weather_emoji,
                "status": market_status
            })
    
    # Mostrar cada continente
    for continent, markets in continents.items():
        if not markets:
            continue
            
        st.markdown(f"#### {continent}")
        
        # Crear columnas para los mercados del continente
        cols = st.columns(min(len(markets), 4))
        
        for idx, market in enumerate(markets):
            with cols[idx % len(cols)]:
                create_market_card(market)
        
        st.markdown("---")

def create_market_card(market: Dict) -> None:
    """
    Crea una tarjeta individual para cada mercado
    
    Args:
        market: Diccionario con información del mercado
    """
    info = market["info"]
    data = market["data"]
    weather = market["weather"]
    status = market["status"]
    
    # Color de fondo basado en rendimiento
    if data["change_percent"] > 0:
        border_color = "#28a745"  # Verde
    elif data["change_percent"] < 0:
        border_color = "#dc3545"  # Rojo
    else:
        border_color = "#6c757d"  # Gris
    
    # Status emoji
    status_emoji = "🟢" if status["is_open"] else "🔴"
    
    with st.container():
        st.markdown(f"""
        <div style="border-left: 4px solid {border_color}; padding: 15px; margin: 10px 0; background-color: #f8f9fa; border-radius: 5px;">
            <h4 style="margin: 0 0 10px 0;">{weather} {info['flag']} {info['name']} {status_emoji}</h4>
            <p style="margin: 0; color: #666; font-size: 14px;">{info['country']} • {info['description']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Métricas principales
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="💰 Precio Actual",
                value=f"{data['current_price']:,.2f} {info['currency']}",
                delta=f"{data['change_percent']:+.2f}%"
            )
        
        with col2:
            trend_emoji = "📈" if data["ma50_trend"] == "alcista" else "📉"
            st.metric(
                label="📊 Tendencia MA50",
                value=f"{trend_emoji} {data['ma50_trend'].title()}",
                delta=f"Volume: {format_number(data['volume'])}"
            )
        
        # Información adicional en expander
        with st.expander(f"ℹ️ Detalles de {info['name']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**🕐 Hora local:** {status['local_time']} ({status['local_date']})")
                st.write(f"**📊 Estado:** {status['status']}")
                st.write(f"**💱 Moneda:** {info['currency']}")
                
            with col2:
                st.write(f"**📈 Cierre anterior:** {data['previous_close']:,.2f}")
                st.write(f"**📊 MA50:** {data['ma50']:,.2f}" if data['ma50'] else "**📊 MA50:** N/A")
                st.write(f"**🔄 Actualizado:** {data['last_updated']}")
            
            st.write(f"**📡 Fuente:** {data['data_source']}")

def create_global_summary(market_data: Dict) -> None:
    """
    Crea resumen global de todos los mercados
    
    Args:
        market_data: Diccionario con datos de todos los mercados
    """
    valid_data = [data for data in market_data.values() if data is not None]
    
    if not valid_data:
        st.warning("⚠️ No se pudieron obtener datos de mercados")
        return
    
    # Calcular estadísticas globales
    total_markets = len(valid_data)
    positive_markets = sum(1 for data in valid_data if data["change_percent"] > 0)
    negative_markets = sum(1 for data in valid_data if data["change_percent"] < 0)
    neutral_markets = total_markets - positive_markets - negative_markets
    
    avg_performance = sum(data["change_percent"] for data in valid_data) / total_markets
    
    # Contar mercados abiertos
    open_markets = 0
    for symbol, market_info in GLOBAL_MARKETS.items():
        if symbol in market_data and market_data[symbol]:
            status = get_market_status(
                market_info["timezone"],
                market_info["market_open"],
                market_info["market_close"]
            )
            if status["is_open"]:
                open_markets += 1
    
    # Contar fuentes de datos reales
    real_data_sources = sum(1 for data in valid_data if "🟢" in data.get("data_source", ""))
    
    st.markdown("### 📊 Resumen Global de Mercados")
    
    # Métricas principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="📈 Mercados Positivos",
            value=positive_markets,
            delta=f"{(positive_markets/total_markets)*100:.1f}%"
        )
    
    with col2:
        st.metric(
            label="📉 Mercados Negativos", 
            value=negative_markets,
            delta=f"{(negative_markets/total_markets)*100:.1f}%"
        )
    
    with col3:
        st.metric(
            label="📊 Promedio Global",
            value=f"{avg_performance:+.2f}%",
            delta="Rendimiento general"
        )
    
    with col4:
        st.metric(
            label="🟢 Mercados Abiertos",
            value=f"{open_markets}/{total_markets}",
            delta=f"{(open_markets/total_markets)*100:.0f}% activos"
        )
    
    with col5:
        # Determinar sentimiento global
        if avg_performance > 0.5:
            sentiment = "🌟 Optimista"
        elif avg_performance > -0.5:
            sentiment = "⚖️ Neutral"
        else:
            sentiment = "🌧️ Pesimista"
            
        st.metric(
            label="🌡️ Sentimiento Global",
            value=sentiment,
            delta=f"{real_data_sources} datos reales"
        )

def create_performance_chart(market_data: Dict) -> None:
    """
    Crea gráfico de rendimiento usando matplotlib nativo de Streamlit
    
    Args:
        market_data: Diccionario con datos de todos los mercados
    """
    # Preparar datos para el gráfico
    chart_data = []
    
    for symbol, data in market_data.items():
        if data is not None and symbol in GLOBAL_MARKETS:
            info = GLOBAL_MARKETS[symbol]
            chart_data.append({
                "Mercado": f"{info['flag']} {info['name']}",
                "País": info["country"],
                "Continente": info["continent"],
                "Rendimiento (%)": data["change_percent"],
                "Precio": data["current_price"],
                "Moneda": info["currency"]
            })
    
    if not chart_data:
        st.warning("⚠️ No hay datos suficientes para crear el gráfico")
        return
    
    df = pd.DataFrame(chart_data)
    df = df.sort_values("Rendimiento (%)", ascending=True)
    
    # Crear gráfico de barras usando Streamlit nativo
    st.markdown("### 📊 Rendimiento Diario de Índices Globales")
    st.bar_chart(df.set_index("Mercado")["Rendimiento (%)"], height=400)
    
    # Mostrar tabla complementaria
    st.dataframe(
        df[["Mercado", "País", "Rendimiento (%)", "Precio", "Moneda"]],
        use_container_width=True,
        hide_index=True
    )

def create_sidebar_content(market_data: Dict) -> Tuple[str, str]:
    """
    Crea contenido del sidebar con información adicional
    
    Args:
        market_data: Diccionario con datos de todos los mercados
        
    Returns:
        Tupla con filtros seleccionados
    """
    st.sidebar.header("🎛️ Panel de Control")
    
    # Botón de actualización
    if st.sidebar.button("🔄 Actualizar Datos", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Leyenda de emojis meteorológicos
    st.sidebar.subheader("🌤️ Leyenda de Rendimiento")
    st.sidebar.markdown("""
    **Emojis Meteorológicos:**
    - ☀️ **Ganancia Fuerte** (>2%)
    - 🌤️ **Ganancia Moderada** (0.5% - 2%)
    - ⛅ **Ganancia Leve** (0% - 0.5%)
    - ☁️ **Neutral** (-0.5% - 0%)
    - 🌧️ **Pérdida Leve** (-0.5% - -1%)
    - ⛈️ **Pérdida Moderada** (-1% - -2.5%)
    - 🌩️ **Pérdida Fuerte** (<-2.5%)
    """)
    
    st.sidebar.markdown("---")
    
    # Filtros (bonus feature)
    st.sidebar.subheader("🔍 Filtros")
    
    continents = ["Todos"] + list(set(info["continent"] for info in GLOBAL_MARKETS.values()))
    selected_continent = st.sidebar.selectbox("Continente:", continents)
    
    performance_filter = st.sidebar.selectbox(
        "Rendimiento:",
        ["Todos", "Solo Positivos", "Solo Negativos", "Solo Neutros"]
    )
    
    # Estadísticas rápidas en sidebar
    valid_data = [data for data in market_data.values() if data is not None]
    if valid_data:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📈 Estadísticas Rápidas")
        
        best_performer = max(valid_data, key=lambda x: x["change_percent"])
        worst_performer = min(valid_data, key=lambda x: x["change_percent"])
        
        # Encontrar nombres de los mejores y peores
        best_symbol = best_performer["symbol"]
        worst_symbol = worst_performer["symbol"]
        
        best_name = GLOBAL_MARKETS[best_symbol]["name"] if best_symbol in GLOBAL_MARKETS else "N/A"
        worst_name = GLOBAL_MARKETS[worst_symbol]["name"] if worst_symbol in GLOBAL_MARKETS else "N/A"
        
        st.sidebar.success(f"🏆 **Mejor:** {best_name}\n+{best_performer['change_percent']:.2f}%")
        st.sidebar.error(f"📉 **Peor:** {worst_name}\n{worst_performer['change_percent']:.2f}%")
        
        # Estadísticas de fuentes de datos
        real_data_count = sum(1 for data in valid_data if "🟢" in data.get("data_source", ""))
        simulated_count = len(valid_data) - real_data_count
        
        st.sidebar.info(f"""
        **📡 Calidad de Datos:**
        - Datos reales: {real_data_count}
        - Simulados: {simulated_count}
        - Total: {len(valid_data)}
        """)
    
    # Información técnica
    st.sidebar.markdown("---")
    st.sidebar.subheader("ℹ️ Información Técnica")
    st.sidebar.info("""
    **📊 Fuentes de Datos:**
    - 🟢 Yahoo Finance API (datos reales)
    - 🟡 Simulación realista (fallback)
    
    **🔄 Actualización:** Cada 5 minutos
    
    **📈 Análisis Técnico:**
    - MA50: Media móvil de 50 períodos
    - Tendencias: Alcista/Bajista
    
    **🕐 Horarios:** 
    - Tiempo local de cada mercado
    - Estado: Abierto/Cerrado
    """)
    
    # Reloj mundial
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌍 Reloj Mundial")
    
    key_timezones = [
        ("🇺🇸 Nueva York", "America/New_York"),
        ("🇬🇧 Londres", "Europe/London"), 
        ("🇩🇪 Frankfurt", "Europe/Berlin"),
        ("🇯🇵 Tokio", "Asia/Tokyo"),
        ("🇨🇳 Shanghai", "Asia/Shanghai"),
        ("🇦🇺 Sydney", "Australia/Sydney")
    ]
    
    for city_name, tz_str in key_timezones:
        try:
            tz = pytz.timezone(tz_str)
            local_time = datetime.now(tz)
            st.sidebar.text(f"{city_name}: {local_time.strftime('%H:%M')}")
        except:
            st.sidebar.text(f"{city_name}: Error")
    
    return selected_continent, performance_filter

def create_detailed_table(market_data: Dict) -> None:
    """
    Crea tabla detallada con todos los datos de mercados
    
    Args:
        market_data: Diccionario con datos de todos los mercados
    """
    st.markdown("### 📋 Tabla Detallada de Mercados")
    
    # Crear datos para la tabla
    table_data = []
    for symbol, data in market_data.items():
        if data is not None and symbol in GLOBAL_MARKETS:
            info = GLOBAL_MARKETS[symbol]
            status = get_market_status(info["timezone"], info["market_open"], info["market_close"])
            weather = get_weather_emoji(data["change_percent"])
            
            table_data.append({
                "🌤️": weather,
                "🏛️ Mercado": f"{info['flag']} {info['name']}",
                "🌍 País": info["country"],
                "💰 Precio": f"{data['current_price']:,.2f} {info['currency']}",
                "📊 Cambio": f"{data['change_percent']:+.2f}%",
                "📈 Tendencia": f"{'📈' if data['ma50_trend'] == 'alcista' else '📉'} {data['ma50_trend'].title()}",
                "🕐 Estado": f"{'🟢' if status['is_open'] else '🔴'} {status['status']}",
                "🌐 Hora Local": f"{status['local_time']}",
                "📊 Volumen": format_number(data['volume']),
                "📡 Fuente": data['data_source'],
                "🔄 Actualizado": data['last_updated']
            })
    
    if table_data:
        df_table = pd.DataFrame(table_data)
        # Ordenar por cambio porcentual descendente
        df_table = df_table.sort_values("📊 Cambio", key=lambda x: x.str.replace('%', '').str.replace('+', '').astype(float), ascending=False)
        st.dataframe(df_table, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No hay datos disponibles para mostrar en la tabla")

# 5. FUNCIÓN PRINCIPAL
# ====================================================================

def main():
    """
    Función principal de la aplicación
    """
    # Título principal
    st.title("🌍 Mercados Financieros Globales")
    st.markdown("### 📊 Monitor en tiempo real de los principales índices bursátiles mundiales")
    
    # Hora actual UTC
    current_utc = datetime.now(pytz.UTC)
    st.info(f"🕐 **Hora UTC:** {current_utc.strftime('%Y-%m-%d %H:%M:%S')} | 🔄 **Última actualización:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Mostrar spinner mientras se cargan los datos
    with st.spinner("📡 Obteniendo datos de los mercados globales..."):
        # Obtener datos de todos los mercados
        market_data = {}
        progress_bar = st.progress(0)
        total_markets = len(GLOBAL_MARKETS)
        
        for idx, symbol in enumerate(GLOBAL_MARKETS.keys()):
            progress_bar.progress((idx + 1) / total_markets)
            market_data[symbol] = fetch_market_data(symbol)
            time.sleep(0.1)  # Pequeña pausa para evitar rate limiting
        
        progress_bar.empty()
    
    # Mostrar estado de conexión de datos
    valid_data = [data for data in market_data.values() if data is not None]
    real_data_count = sum(1 for data in valid_data if "🟢" in data.get("data_source", ""))
    
    if real_data_count > 0:
        st.success(f"✅ Datos obtenidos exitosamente: {real_data_count} fuentes reales, {len(valid_data) - real_data_count} simuladas")
    else:
        st.info("ℹ️ Usando datos simulados realistas - API externa no disponible")
    
    # Crear sidebar con filtros
    selected_continent, performance_filter = create_sidebar_content(market_data)
    
    # Aplicar filtros si es necesario
    filtered_data = market_data.copy()
    
    if selected_continent != "Todos":
        filtered_symbols = [
            symbol for symbol, info in GLOBAL_MARKETS.items() 
            if info["continent"] == selected_continent
        ]
        filtered_data = {k: v for k, v in market_data.items() if k in filtered_symbols}
    
    if performance_filter != "Todos":
        if performance_filter == "Solo Positivos":
            filtered_data = {k: v for k, v in filtered_data.items() if v and v["change_percent"] > 0}
        elif performance_filter == "Solo Negativos":
            filtered_data = {k: v for k, v in filtered_data.items() if v and v["change_percent"] < 0}
        elif performance_filter == "Solo Neutros":
            filtered_data = {k: v for k, v in filtered_data.items() if v and v["change_percent"] == 0}
    
    # Mostrar resumen global
    create_global_summary(market_data)
    
    st.markdown("---")
    
    # Mostrar mapa mundial
    create_world_map_visualization(filtered_data)
    
    # Mostrar gráfico de rendimiento
    st.markdown("### 📈 Análisis Comparativo de Rendimiento")
    create_performance_chart(filtered_data)
    
    # Mostrar tabla detallada
    create_detailed_table(filtered_data)
    
    # Footer informativo mejorado
    st.markdown("---")
    
    # Estadísticas finales
    total_real = sum(1 for data in valid_data if "🟢" in data.get("data_source", ""))
    total_sim = len(valid_data) - total_real
    success_rate = (total_real / len(valid_data) * 100) if valid_data else 0
    
    st.markdown(f"""
    <div style='text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 15px; margin: 20px 0;'>
        <h3>🚀 Widget de Mercados Financieros Globales v3.0</h3>
        <p><strong>📊 Monitoreo de {len(GLOBAL_MARKETS)} índices bursátiles principales</strong></p>
        <p>📡 <em>Datos reales: {total_real} | Simulados: {total_sim} | Tasa de éxito: {success_rate:.1f}%</em></p>
        <p>🌤️ <em>Visualización meteorológica intuitiva</em></p>
        <p>📈 <em>Análisis técnico con MA50</em></p>
        <p>🌍 <em>Horarios precisos globales</em></p>
        
        <div style="margin: 20px 0;">
            <span style="background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 20px; margin: 0 5px; font-size: 12px;">
                📡 HÍBRIDO REAL/SIM
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 20px; margin: 0 5px; font-size: 12px;">
                🌤️ CLIMA FINANCIERO
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 20px; margin: 0 5px; font-size: 12px;">
                📊 ANÁLISIS TÉCNICO
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 20px; margin: 0 5px; font-size: 12px;">
                🔍 FILTROS INTELIGENTES
            </span>
            <span style="background: rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 20px; margin: 0 5px; font-size: 12px;">
                🕐 TIEMPO REAL
            </span>
        </div>
        
        <p style='font-size: 12px; margin-top: 20px; opacity: 0.9;'>
            <strong>🌟 Características Principales:</strong><br>
            • Intentos de conexión a Yahoo Finance API para datos reales<br>
            • Sistema de fallback con simulación ultra-realista<br>
            • 7 niveles de emojis meteorológicos por rendimiento<br>
            • Análisis de tendencias con Media Móvil 50 períodos<br>
            • Horarios de mercado precisos por zona horaria<br>
            • Filtrado avanzado por continente y rendimiento<br>
            • Reloj mundial integrado en sidebar<br>
            • Estadísticas globales y mejores/peores performers
        </p>
        
        <p style='font-size: 11px; margin-top: 15px; opacity: 0.8;'>
            ⚠️ <strong>Aviso Legal:</strong> Herramienta educativa e informativa únicamente. 
            No constituye asesoramiento financiero. Las decisiones de inversión requieren análisis profesional.
        </p>
        
        <p style='font-size: 10px; margin-top: 10px; opacity: 0.7;'>
            Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} | 
            Desarrollado con Streamlit | Compatible con Streamlit Cloud
        </p>
    </div>
    """, unsafe_allow_html=True)

# 6. EJECUCIÓN PRINCIPAL
# ====================================================================

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Error ejecutando la aplicación: {str(e)}")
        logger.error(f"Error en main(): {str(e)}")
        
        # Mostrar información de debug en modo de desarrollo
        with st.expander("🔧 Información de Debug"):
            st.exception(e)
            st.write("**Variables del sistema:**")
            st.write(f"- Python version: {st.__version__ if hasattr(st, '__version__') else 'N/A'}")
            st.write(f"- Timestamp: {datetime.now()}")
            st.write(f"- Mercados configurados: {len(GLOBAL_MARKETS)}")
            st.write(f"- Timezone UTC: {datetime.now(pytz.UTC)}")
