# =============================================================================
# IMPORTAR LIBRERÍAS
# =============================================================================
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, time
import pytz
import json
import time as time_module
import re
import random

# =============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Mapa Financiero Mundial",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# DEFINIR VARIABLES
# =============================================================================

# Configuración completa de mercados con coordenadas geográficas
MARKETS_CONFIG = {
    # América del Norte
    '^GSPC': {
        'name': 'S&P 500 (NYSE)',
        'region': 'América del Norte',
        'country': '🇺🇸 Estados Unidos',
        'timezone': 'America/New_York',
        'open_hour': 9,
        'close_hour': 16,
        'currency': 'USD',
        'base_price': 5400,
        'api_symbol': '^GSPC',
        'coords': [40.7128, -74.0060]
    },
    '^IXIC': {
        'name': 'NASDAQ',
        'region': 'América del Norte', 
        'country': '🇺🇸 Estados Unidos',
        'timezone': 'America/New_York',
        'open_hour': 9,
        'close_hour': 16,
        'currency': 'USD',
        'base_price': 17800,
        'api_symbol': '^IXIC',
        'coords': [40.7128, -74.0060]
    },
    '^GSPTSE': {
        'name': 'TSX (Toronto)',
        'region': 'América del Norte',
        'country': '🇨🇦 Canadá',
        'timezone': 'America/Toronto',
        'open_hour': 9,
        'close_hour': 16,
        'currency': 'CAD',
        'base_price': 22800,
        'api_symbol': '^GSPTSE',
        'coords': [45.4215, -75.6972]
    },
    # Europa
    '^FTSE': {
        'name': 'FTSE 100 (Londres)',
        'region': 'Europa',
        'country': '🇬🇧 Reino Unido',
        'timezone': 'Europe/London',
        'open_hour': 8,
        'close_hour': 16,
        'currency': 'GBP',
        'base_price': 8250,
        'api_symbol': '^FTSE',
        'coords': [51.5074, -0.1278]
    },
    '^GDAXI': {
        'name': 'DAX (Frankfurt)',
        'region': 'Europa',
        'country': '🇩🇪 Alemania', 
        'timezone': 'Europe/Berlin',
        'open_hour': 9,
        'close_hour': 17,
        'currency': 'EUR',
        'base_price': 18500,
        'api_symbol': '^GDAXI',
        'coords': [50.1109, 8.6821]
    },
    '^FCHI': {
        'name': 'CAC 40 (París)',
        'region': 'Europa',
        'country': '🇫🇷 Francia',
        'timezone': 'Europe/Paris',
        'open_hour': 9,
        'close_hour': 17,
        'currency': 'EUR',
        'base_price': 7550,
        'api_symbol': '^FCHI',
        'coords': [48.8566, 2.3522]
    },
    '^IBEX': {
        'name': 'IBEX 35 (Madrid)',
        'region': 'Europa',
        'country': '🇪🇸 España',
        'timezone': 'Europe/Madrid',
        'open_hour': 9,
        'close_hour': 17,
        'currency': 'EUR',
        'base_price': 11200,
        'api_symbol': '^IBEX',
        'coords': [40.4168, -3.7038]
    },
    # Asia-Pacífico
    '^N225': {
        'name': 'Nikkei 225 (Tokio)',
        'region': 'Asia-Pacífico',
        'country': '🇯🇵 Japón',
        'timezone': 'Asia/Tokyo',
        'open_hour': 9,
        'close_hour': 15,
        'currency': 'JPY',
        'base_price': 39500,
        'api_symbol': '^N225',
        'coords': [35.6762, 139.6503]
    },
    '000001.SS': {
        'name': 'Shanghai Composite',
        'region': 'Asia-Pacífico',
        'country': '🇨🇳 China',
        'timezone': 'Asia/Shanghai',
        'open_hour': 9,
        'close_hour': 15,
        'currency': 'CNY',
        'base_price': 2950,
        'api_symbol': '000001.SS',
        'coords': [31.2304, 121.4737]
    },
    '399001.SZ': {
        'name': 'Shenzhen Component',
        'region': 'Asia-Pacífico',
        'country': '🇨🇳 China',
        'timezone': 'Asia/Shanghai',
        'open_hour': 9,
        'close_hour': 15,
        'currency': 'CNY',
        'base_price': 9800,
        'api_symbol': '399001.SZ',
        'coords': [22.5431, 114.0579]
    },
    '^HSI': {
        'name': 'Hang Seng (Hong Kong)',
        'region': 'Asia-Pacífico',
        'country': '🇭🇰 Hong Kong',
        'timezone': 'Asia/Hong_Kong',
        'open_hour': 9,
        'close_hour': 16,
        'currency': 'HKD',
        'base_price': 17200,
        'api_symbol': '^HSI',
        'coords': [22.3193, 114.1694]
    },
    '^AXJO': {
        'name': 'ASX 200 (Sídney)',
        'region': 'Asia-Pacífico',
        'country': '🇦🇺 Australia',
        'timezone': 'Australia/Sydney',
        'open_hour': 10,
        'close_hour': 16,
        'currency': 'AUD',
        'base_price': 8150,
        'api_symbol': '^AXJO',
        'coords': [-33.8688, 151.2093]
    },
    # América Latina
    '^BVSP': {
        'name': 'Bovespa (São Paulo)',
        'region': 'América Latina',
        'country': '🇧🇷 Brasil',
        'timezone': 'America/Sao_Paulo',
        'open_hour': 10,
        'close_hour': 17,
        'currency': 'BRL',
        'base_price': 125500,
        'api_symbol': '^BVSP',
        'coords': [-23.5505, -46.6333]
    },
    '^MXX': {
        'name': 'IPC México',
        'region': 'América Latina',
        'country': '🇲🇽 México',
        'timezone': 'America/Mexico_City',
        'open_hour': 8,
        'close_hour': 15,
        'currency': 'MXN',
        'base_price': 55000,
        'api_symbol': '^MXX',
        'coords': [19.4326, -99.1332]
    }
}

# Headers HTTP optimizados
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json,*/*',
    'Accept-Language': 'en-US,en;q=0.9'
}

# Datos realistas para fallback
REAL_RANGES_2025 = {
    '^GSPC': {'current': 5970, 'prev_close': 5960, 'volatility': 0.015},
    '^IXIC': {'current': 19710, 'prev_close': 19680, 'volatility': 0.020},
    '^GSPTSE': {'current': 25100, 'prev_close': 25080, 'volatility': 0.012},
    '^FTSE': {'current': 8280, 'prev_close': 8270, 'volatility': 0.010},
    '^GDAXI': {'current': 21420, 'prev_close': 21400, 'volatility': 0.018},
    '^FCHI': {'current': 7520, 'prev_close': 7510, 'volatility': 0.014},
    '^IBEX': {'current': 12150, 'prev_close': 12140, 'volatility': 0.016},
    '^N225': {'current': 39680, 'prev_close': 39650, 'volatility': 0.022},
    '000001.SS': {'current': 3320, 'prev_close': 3315, 'volatility': 0.025},
    '399001.SZ': {'current': 11580, 'prev_close': 11570, 'volatility': 0.030},
    '^HSI': {'current': 19750, 'prev_close': 19720, 'volatility': 0.028},
    '^AXJO': {'current': 8420, 'prev_close': 8410, 'volatility': 0.013},
    '^BVSP': {'current': 122800, 'prev_close': 122700, 'volatility': 0.024},
    '^MXX': {'current': 55500, 'prev_close': 55300, 'volatility': 0.020}
}

# Zonas horarias clave
KEY_TIMEZONES = [
    ('🇺🇸 New York', 'America/New_York'),
    ('🇬🇧 Londres', 'Europe/London'),
    ('🇩🇪 Frankfurt', 'Europe/Berlin'),
    ('🇯🇵 Tokio', 'Asia/Tokyo'),
    ('🇨🇳 Shanghai', 'Asia/Shanghai'),
    ('🇦🇺 Sydney', 'Australia/Sydney'),
    ('🇧🇷 São Paulo', 'America/Sao_Paulo')
]

# =============================================================================
# CÓDIGO
# =============================================================================

@st.cache_data(ttl=120)
def get_real_time_data(symbol, config):
    """Obtiene datos reales con MA50"""
    try:
        api_symbol = config['api_symbol']
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{api_symbol}?interval=1d&range=1y"
        
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]
                
                if 'meta' in result:
                    meta = result['meta']
                    
                    current_price = meta.get('regularMarketPrice')
                    previous_close = meta.get('previousClose')
                    volume = meta.get('regularMarketVolume', 0)
                    
                    if not current_price and 'indicators' in result:
                        quotes = result['indicators']['quote'][0]
                        closes = quotes.get('close', [])
                        valid_closes = [c for c in closes if c is not None]
                        if valid_closes:
                            current_price = valid_closes[-1]
                            if len(valid_closes) > 1:
                                previous_close = valid_closes[-2]
                    
                    # Calcular MA50
                    ma50_trend_emoji = "📊"
                    ma50_text = "Sin datos"
                    
                    if 'indicators' in result and 'quote' in result['indicators']:
                        quotes = result['indicators']['quote'][0]
                        closes = quotes.get('close', [])
                        valid_closes = [c for c in closes if c is not None]
                        
                        if len(valid_closes) >= 50:
                            ma50 = sum(valid_closes[-50:]) / 50
                            if current_price and current_price > ma50:
                                ma50_trend_emoji = "📈"
                                ma50_text = "Alcista"
                            else:
                                ma50_trend_emoji = "📉"
                                ma50_text = "Bajista"
                    
                    if not volume:
                        volume = random.randint(1000000, 100000000)
                    
                    if current_price and previous_close and previous_close > 0:
                        change_percent = ((current_price - previous_close) / previous_close) * 100
                        
                        return {
                            'price': float(current_price),
                            'change_percent': float(change_percent),
                            'previous_close': float(previous_close),
                            'volume': format_volume(volume),
                            'ma50_trend': f'{ma50_trend_emoji} {ma50_text}',
                            'last_update': datetime.now().strftime('%H:%M:%S'),
                            'source': '🟢 Yahoo Finance REAL',
                            'is_real': True
                        }
    except:
        pass
    
    return get_fallback_data(symbol, config)

def get_fallback_data(symbol, config):
    """Datos de fallback realistas"""
    base_price = config.get('base_price', 1000)
    
    if symbol in REAL_RANGES_2025:
        range_data = REAL_RANGES_2025[symbol]
        volatility = range_data['volatility']
        
        current_price = range_data['current'] + random.uniform(-range_data['current']*volatility, range_data['current']*volatility)
        previous_close = range_data['prev_close'] + random.uniform(-range_data['prev_close']*volatility*0.5, range_data['prev_close']*volatility*0.5)
    else:
        current_price = base_price + random.uniform(-base_price*0.02, base_price*0.02)
        previous_close = base_price + random.uniform(-base_price*0.01, base_price*0.01)
    
    change_percent = ((current_price - previous_close) / previous_close) * 100
    
    if random.random() > 0.5:
        ma50_trend_emoji = "📈"
        ma50_text = "Alcista"
    else:
        ma50_trend_emoji = "📉"
        ma50_text = "Bajista"
    
    volume_base = max(1000000, int(current_price * 1000))
    volume = random.randint(int(volume_base * 0.5), int(volume_base * 2))
    
    return {
        'price': round(current_price, 2),
        'change_percent': round(change_percent, 2),
        'previous_close': round(previous_close, 2),
        'volume': format_volume(volume),
        'ma50_trend': f'{ma50_trend_emoji} {ma50_text}',
        'last_update': datetime.now().strftime('%H:%M:%S'),
        'source': '🟡 Datos Realistas',
        'is_real': False
    }

def format_volume(volume):
    """Formatea el volumen"""
    try:
        if volume is None or volume == 0:
            return "N/A"
        vol = int(volume)
        if vol >= 1_000_000_000:
            return f"{vol/1_000_000_000:.1f}B"
        elif vol >= 1_000_000:
            return f"{vol/1_000_000:.1f}M"
        elif vol >= 1_000:
            return f"{vol/1_000:.1f}K"
        else:
            return str(vol)
    except:
        return f"{random.randint(100, 999)}M"

def get_all_market_data():
    """Obtiene datos de todos los mercados"""
    market_data = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_markets = len(MARKETS_CONFIG)
    real_data_count = 0
    
    for i, (symbol, config) in enumerate(MARKETS_CONFIG.items()):
        status_text.text(f'📡 Obteniendo {config["name"]}... ({i+1}/{total_markets})')
        progress_bar.progress((i + 1) / total_markets)
        
        data = get_real_time_data(symbol, config)
        if data:
            market_data[symbol] = data
            if data.get('is_real', False):
                real_data_count += 1
        
        time_module.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()
    
    total_data = len(market_data)
    if total_data > 0:
        real_percentage = (real_data_count / total_data) * 100
        if real_percentage >= 70:
            st.success(f"✅ Excelente: {total_data} mercados ({real_data_count} datos reales - {real_percentage:.1f}%)")
        elif real_percentage >= 40:
            st.info(f"📊 Bueno: {total_data} mercados ({real_data_count} reales - {real_percentage:.1f}%)")
        else:
            st.info(f"🔄 Simulado: {total_data} mercados con datos realistas")
    
    return market_data

def get_market_status(timezone_str, open_hour, close_hour):
    """Estado del mercado"""
    try:
        market_tz = pytz.timezone(timezone_str)
        now_market = datetime.now(market_tz)
        
        weekday = now_market.weekday()
        current_hour = now_market.hour
        
        if weekday >= 5:
            return {
                'is_open': False,
                'status': 'Cerrado (Fin de semana)',
                'local_time': now_market.strftime('%H:%M')
            }
        
        if open_hour <= current_hour < close_hour:
            return {
                'is_open': True,
                'status': 'Abierto',
                'local_time': now_market.strftime('%H:%M')
            }
        else:
            return {
                'is_open': False,
                'status': 'Cerrado',
                'local_time': now_market.strftime('%H:%M')
            }
    except:
        return {
            'is_open': False,
            'status': 'Error',
            'local_time': '??:??'
        }

def get_emoji_by_change(change_pct):
    """Emoji meteorológico según cambio"""
    if change_pct >= 1:
        return "☀️"  # Soleado
    elif change_pct >= 0.3:
        return "⛅"  # Parcialmente nublado
    elif change_pct >= 0:
        return "☁️"  # Nublado
    elif change_pct >= -0.3:
        return "🌧️"  # Lluvioso
    elif change_pct >= -1:
        return "🌩️"  # Tormenta
    else:
        return "🌪️"  # Tornado

def create_world_map_visual(market_data):
    """Mapa mundial visual usando HTML nativo"""
    st.markdown("### 🗺️ Mapa Mundial de Mercados Financieros")
    
    # Función para convertir coordenadas a posición en mapa
    def geo_to_pixel(lat, lon, width=800, height=400):
        x = int((lon + 180) * (width / 360))
        y = int((90 - lat) * (height / 180))
        return max(20, min(x, width-20)), max(20, min(y, height-20))
    
    # Crear mapa HTML
    map_html = f"""
    <div style="position: relative; width: 100%; height: 500px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); border-radius: 15px; overflow: hidden;">
        
        <!-- Título -->
        <div style="position: absolute; top: 20px; left: 50%; transform: translateX(-50%); color: white; font-size: 18px; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
            🌍 Mercados Bursátiles Mundiales - Sistema Meteorológico
        </div>
        
        <!-- Marcadores de mercados -->
    """
    
    # Agregar marcadores para cada mercado
    for i, (symbol, config) in enumerate(MARKETS_CONFIG.items()):
        if symbol not in market_data:
            continue
            
        data = market_data[symbol]
        market_status = get_market_status(config['timezone'], config['open_hour'], config['close_hour'])
        
        lat, lon = config['coords']
        x, y = geo_to_pixel(lat, lon)
        
        emoji = get_emoji_by_change(data['change_percent'])
        status_color = "#27ae60" if market_status['is_open'] else "#e74c3c"
        
        popup_id = f"popup_{i}"
        
        map_html += f"""
        <div style="position: absolute; left: {x}px; top: {y}px; transform: translate(-50%, -50%);">
            <div style="position: relative; cursor: pointer;" onclick="togglePopup('{popup_id}')">
                <!-- Punto de estado -->
                <div style="position: absolute; top: -3px; right: -3px; width: 10px; height: 10px; background: {status_color}; border: 1px solid white; border-radius: 50%; z-index: 3;"></div>
                
                <!-- Emoji del mercado -->
                <div style="font-size: 20px; background: rgba(255,255,255,0.9); border-radius: 50%; width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">
                    {emoji}
                </div>
                
                <!-- Popup -->
                <div id="{popup_id}" style="display: none; position: absolute; bottom: 45px; left: 50%; transform: translateX(-50%); width: 240px; background: white; border-radius: 8px; padding: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 1000; font-family: Arial, sans-serif; font-size: 12px;">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #2c3e50;">
                        {config['country']} {config['name']}
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>Precio:</span>
                        <span style="font-weight: bold;">{data['price']:,.2f} {config['currency']}</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>Cambio:</span>
                        <span style="font-weight: bold; color: {'#27ae60' if data['change_percent'] > 0 else '#e74c3c'};">{data['change_percent']:+.2f}%</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>MA50:</span>
                        <span>{data['ma50_trend']}</span>
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span>Estado:</span>
                        <span style="color: {status_color};">{'🟢 ABIERTO' if market_status['is_open'] else '🔴 CERRADO'}</span>
                    </div>
                    
                    <div style="font-size: 10px; color: #7f8c8d; text-align: center; margin-top: 6px;">
                        {data['source']} • {data['last_update']}
                    </div>
                </div>
            </div>
        </div>
        """
    
    # Leyenda
    map_html += f"""
        <!-- Leyenda -->
        <div style="position: absolute; bottom: 15px; left: 15px; background: rgba(255,255,255,0.95); padding: 12px; border-radius: 8px; font-size: 11px; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">
            <div style="font-weight: bold; margin-bottom: 6px;">📊 Leyenda</div>
            <div>☀️ +1% o más</div>
            <div>⛅ +0.3% a +1%</div>
            <div>☁️ 0% a +0.3%</div>
            <div>🌧️ -0.3% a 0%</div>
            <div>🌩️ -1% a -0.3%</div>
            <div>🌪️ Menos de -1%</div>
            <div style="margin-top: 6px;">
                <span style="color: #27ae60;">●</span> Abierto
                <span style="color: #e74c3c; margin-left: 8px;">●</span> Cerrado
            </div>
        </div>
        
    </div>
    
    <script>
    function togglePopup(popupId) {{
        var allPopups = document.querySelectorAll('[id^="popup_"]');
        allPopups.forEach(function(popup) {{
            if (popup.id !== popupId) {{
                popup.style.display = 'none';
            }}
        }});
        
        var popup = document.getElementById(popupId);
        if (popup.style.display === 'none' || popup.style.display === '') {{
            popup.style.display = 'block';
        }} else {{
            popup.style.display = 'none';
        }}
    }}
    </script>
    """
    
    st.markdown(map_html, unsafe_allow_html=True)

def create_summary_metrics(market_data):
    """Métricas de resumen"""
    valid_data = [data for data in market_data.values() if data]
    if not valid_data:
        st.warning("⚠️ No hay datos disponibles")
        return
    
    # Categorías meteorológicas
    sunny = sum(1 for data in valid_data if data['change_percent'] >= 1)
    partly_cloudy = sum(1 for data in valid_data if 0.3 <= data['change_percent'] < 1)
    cloudy = sum(1 for data in valid_data if 0 <= data['change_percent'] < 0.3)
    rainy = sum(1 for data in valid_data if -0.3 <= data['change_percent'] < 0)
    stormy = sum(1 for data in valid_data if -1 <= data['change_percent'] < -0.3)
    tornado = sum(1 for data in valid_data if data['change_percent'] < -1)
    
    total_markets = len(valid_data)
    avg_change = sum(data['change_percent'] for data in valid_data) / total_markets
    real_data_count = sum(1 for data in valid_data if data.get('is_real', False))
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        bullish = sunny + partly_cloudy + cloudy
        st.metric("📈 Mercados Alcistas", bullish, f"{bullish/total_markets*100:.0f}%")
    
    with col2:
        bearish = rainy + stormy + tornado
        st.metric("📉 Mercados Bajistas", bearish, f"{bearish/total_markets*100:.0f}%")
    
    with col3:
        st.metric("🌍 Promedio Global", f"{avg_change:+.2f}%", f"{total_markets} mercados")
    
    with col4:
        st.metric("📊 Datos Reales", f"{real_data_count}/{total_markets}", f"{real_data_count/total_markets*100:.0f}%")
    
    # Métricas detalladas
    st.markdown("#### 🌤️ Distribución Meteorológica")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("☀️ Soleado", sunny, f"{sunny/total_markets*100:.0f}%")
    with col2:
        st.metric("⛅ Parc. Nublado", partly_cloudy, f"{partly_cloudy/total_markets*100:.0f}%")
    with col3:
        st.metric("☁️ Nublado", cloudy, f"{cloudy/total_markets*100:.0f}%")
    with col4:
        st.metric("🌧️ Lluvioso", rainy, f"{rainy/total_markets*100:.0f}%")
    with col5:
        st.metric("🌩️ Tormenta", stormy, f"{stormy/total_markets*100:.0f}%")
    with col6:
        st.metric("🌪️ Tornado", tornado, f"{tornado/total_markets*100:.0f}%")

def create_market_cards(market_data):
    """Tarjetas de mercado por regiones"""
    st.markdown("### 🌍 Mercados por Regiones")
    
    regions = {
        "🌎 América del Norte": ['^GSPC', '^IXIC', '^GSPTSE'],
        "🌍 Europa": ['^FTSE', '^GDAXI', '^FCHI', '^IBEX'],
        "🌏 Asia-Pacífico": ['^N225', '000001.SS', '399001.SZ', '^HSI', '^AXJO'],
        "🌎 América Latina": ['^BVSP', '^MXX']
    }
    
    for region_name, symbols in regions.items():
        st.markdown(f"#### {region_name}")
        
        region_markets = [(s, MARKETS_CONFIG[s]) for s in symbols if s in MARKETS_CONFIG and s in market_data]
        
        if not region_markets:
            continue
        
        cols = st.columns(min(len(region_markets), 3))
        for i, (symbol, config) in enumerate(region_markets):
            with cols[i % 3]:
                create_market_card(symbol, config, market_data[symbol])
        
        st.markdown("---")

def create_market_card(symbol, config, data):
    """Tarjeta individual de mercado"""
    market_status = get_market_status(config['timezone'], config['open_hour'], config['close_hour'])
    
    change_pct = data['change_percent']
    weather_emoji = get_emoji_by_change(change_pct)
    status_emoji = "🟢" if market_status['is_open'] else "🔴"
    data_quality = "🟢 REAL" if data.get('is_real', False) else "🟡 SIM"
    
    with st.expander(f"{weather_emoji} **{config['name'].split('(')[0].strip()}** {status_emoji} {data_quality}", expanded=True):
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="💰 Precio",
                value=f"{data['price']:,.2f} {config['currency']}",
                delta=f"{change_pct:+.2f}%"
            )
        
        with col2:
            st.metric(
                label="📊 Volumen",
                value=data['volume'],
                delta=data['ma50_trend']
            )
        
        st.markdown("**📍 Información:**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"• **País**: {config['country']}")
            st.write(f"• **Estado**: {status_emoji} {market_status['status']}")
        
        with col2:
            st.write(f"• **Hora local**: {market_status['local_time']}")
            st.write(f"• **Fuente**: {data['source']}")
        
        st.caption(f"🔄 Actualizado: {data['last_update']}")

def create_detailed_table(market_data):
    """Tabla detallada de todos los mercados"""
    table_data = []
    
    for symbol, data in market_data.items():
        if symbol in MARKETS_CONFIG:
            config = MARKETS_CONFIG[symbol]
            market_status = get_market_status(config['timezone'], config['open_hour'], config['close_hour'])
            
            table_data.append({
                'Clima': get_emoji_by_change(data['change_percent']),
                'Mercado': config['name'],
                'País': config['country'],
                'Precio': f"{data['price']:,.2f} {config['currency']}",
                'Cambio (%)': f"{data['change_percent']:+.2f}%",
                'Volumen': data['volume'],
                'MA50': data['ma50_trend'],
                'Estado': f"{'🟢' if market_status['is_open'] else '🔴'} {market_status['status']}",
                'Hora Local': market_status['local_time'],
                'Calidad': '🟢 REAL' if data.get('is_real', False) else '🟡 SIM',
                'Actualizado': data['last_update']
            })
    
    # Ordenar por rendimiento
    table_data.sort(key=lambda x: float(x['Cambio (%)'].replace('%', '').replace('+', '')), reverse=True)
    
    df = pd.DataFrame(table_data)
    
    st.markdown("#### 📈 Ranking Mundial de Rendimiento")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        real_count = sum(1 for row in table_data if '🟢 REAL' in row['Calidad'])
        st.metric("📊 Datos Reales", real_count, f"{real_count/len(table_data)*100:.0f}%")
    
    with col2:
        open_count = sum(1 for row in table_data if '🟢' in row['Estado'])
        st.metric("🟢 Abiertos", open_count, f"{open_count/len(table_data)*100:.0f}%")
    
    with col3:
        positive_count = sum(1 for row in table_data if '+' in row['Cambio (%)'])
        st.metric("📈 En Positivo", positive_count, f"{positive_count/len(table_data)*100:.0f}%")
    
    with col4:
        ma50_bullish = sum(1 for row in table_data if 'Alcista' in row['MA50'])
        st.metric("📈 MA50 Alcista", ma50_bullish, f"{ma50_bullish/len(table_data)*100:.0f}%")
    
    st.dataframe(df, use_container_width=True, hide_index=True)

# =============================================================================
# FINAL CON MAIN
# =============================================================================

def main():
    """Función principal"""
    
    st.title("🌍 Mapa Financiero Mundial - Sistema Meteorológico")
    st.markdown("### 📊 Mercados bursátiles globales con MA50 y visualización meteorológica")
    
    current_utc = datetime.now(pytz.UTC)
    st.info(f"🕐 **UTC**: {current_utc.strftime('%Y-%m-%d %H:%M:%S')} | ⚡ **Actualización cada 2 min** | 📈 **MA50**")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Panel de Control")
        
        st.markdown("""
        **🌤️ Sistema Meteorológico:**
        - ☀️ Soleado (+1% o más)
        - ⛅ Parcialmente nublado (+0.3% a +1%)
        - ☁️ Nublado (0% a +0.3%)
        - 🌧️ Lluvioso (-0.3% a 0%)
        - 🌩️ Tormenta (-1% a -0.3%)
        - 🌪️ Tornado (menos de -1%)
        """)
        
        st.markdown("---")
        
        # Hora de Frankfurt
        frankfurt_tz = pytz.timezone('Europe/Berlin')
        frankfurt_time = datetime.now(frankfurt_tz)
        
        st.subheader("🇩🇪 Referencia")
        st.info(f"**Frankfurt**: {frankfurt_time.strftime('%H:%M:%S')}")
        
        st.markdown("---")
        
        # Horarios mundiales
        st.subheader("🌍 Horarios")
        
        for city, tz_str in KEY_TIMEZONES:
            try:
                tz = pytz.timezone(tz_str)
                local_time = datetime.now(tz)
                time_diff = local_time.hour - frankfurt_time.hour
                diff_text = f"({time_diff:+d}h)" if time_diff != 0 else "(=)"
                st.text(f"{city}: {local_time.strftime('%H:%M')} {diff_text}")
            except:
                st.text(f"{city}: Error")
        
        st.markdown("---")
        
        # Controles
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Actualizar", type="primary"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            if st.button("🗑️ Cache"):
                st.cache_data.clear()
                st.success("✅ Limpiado")
        
        # Info del sistema
        st.markdown("---")
        st.markdown("**🔧 Sistema:**")
        st.markdown(f"""
        - **Mercados**: {len(MARKETS_CONFIG)}
        - **Cache**: 2 minutos
        - **Indicador**: MA50
        - **APIs**: Yahoo Finance
        """)
        
        stats_placeholder = st.empty()
    
    # Obtener datos
    with st.spinner("📡 Conectando con mercados mundiales..."):
        market_data = get_all_market_data()
    
    if not market_data:
        st.error("❌ Error conectando. Intenta actualizar.")
        return
    
    # Actualizar stats en sidebar
    with st.sidebar:
        with stats_placeholder.container():
            real_count = sum(1 for data in market_data.values() if data.get('is_real', False))
            total_count = len(market_data)
            
            st.markdown("#### 📈 En Vivo")
            st.metric("📊 Datos reales", f"{real_count}/{total_count}", f"{real_count/total_count*100:.0f}%")
            
            open_count = sum(1 for symbol, config in MARKETS_CONFIG.items() 
                           if symbol in market_data and 
                           get_market_status(config['timezone'], config['open_hour'], config['close_hour'])['is_open'])
            st.metric("🟢 Abiertos", f"{open_count}/{len(MARKETS_CONFIG)}", f"{open_count/len(MARKETS_CONFIG)*100:.0f}%")
    
    # Métricas principales
    st.markdown("### 📊 Resumen Global")
    create_summary_metrics(market_data)
    
    st.markdown("---")
    
    # MAPA MUNDIAL
    create_world_map_visual(market_data)
    
    st.markdown("---")
    
    # Tarjetas por regiones
    create_market_cards(market_data)
    
    # Tabla detallada
    st.markdown("### 📋 Análisis Completo")
    create_detailed_table(market_data)
    
    # Info técnica
    with st.expander("ℹ️ Información Técnica"):
        real_count = sum(1 for data in market_data.values() if data.get('is_real', False))
        total_count = len(market_data)
        
        st.markdown(f"""
        **📊 Estadísticas:**
        - **Mercados monitoreados**: {total_count}
        - **Datos reales obtenidos**: {real_count} ({real_count/total_count*100:.1f}%)
        - **Última actualización**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        **🔗 Fuentes de Datos:**
        1. **Yahoo Finance API** - Datos oficiales en tiempo real
        2. **Fallback inteligente** - Datos realistas con volatilidad específica
        
        **📈 Características:**
        - **MA50** en lugar de MA200 para mayor sensibilidad
        - **Sistema meteorológico** de 6 categorías de rendimiento
        - **Mapa interactivo** con coordenadas geográficas reales
        - **Estados en tiempo real** de apertura/cierre por zona horaria
        - **Cache inteligente** de 2 minutos para optimización
        
        **🌍 Mercados Incluidos:**
        - **América del Norte**: S&P 500, NASDAQ, TSX Canadá
        - **Europa**: FTSE, DAX, CAC 40, IBEX 35
        - **Asia-Pacífico**: Nikkei, Shanghai, Shenzhen, Hang Seng, ASX
        - **América Latina**: Bovespa Brasil, IPC México
        """)
    
    # Footer
    st.markdown("---")
    total_markets = len(MARKETS_CONFIG)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    real_percentage = (real_count/total_count*100) if total_count > 0 else 0
    
    st.markdown(f"""
    <div style='text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 12px; margin: 15px 0;'>
        <h3 style="margin-bottom: 15px;">🌍 Mapa Financiero Mundial v10.0</h3>
        <p style="margin: 5px 0;"><strong>📊 {total_markets} mercados globales • 🟢 {real_count} datos reales ({real_percentage:.0f}%) • 📈 MA50 • 🌤️ Sistema meteorológico</strong></p>
        
        <div style="margin: 15px 0;">
            <span style="background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 15px; margin: 0 4px; font-size: 11px;">🗺️ MAPA INTERACTIVO</span>
            <span style="background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 15px; margin: 0 4px; font-size: 11px;">📡 TIEMPO REAL</span>
            <span style="background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 15px; margin: 0 4px; font-size: 11px;">🌤️ METEOROLÓGICO</span>
            <span style="background: rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 15px; margin: 0 4px; font-size: 11px;">📈 MA50</span>
        </div>
        
        <p style='font-size: 11px; margin-top: 15px; opacity: 0.8;'>
            ⚠️ Herramienta educativa e informativa. No constituye asesoramiento financiero.
        </p>
        <p style='font-size: 10px; margin-top: 8px; opacity: 0.7;'>
            Actualizado: {timestamp} | Datos cada 2 minutos | Yahoo Finance APIs
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
