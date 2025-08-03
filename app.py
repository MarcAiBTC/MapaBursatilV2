import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone, time
import pytz

# Configuración de la página
st.set_page_config(
    page_title="Mapa Financiero Mundial",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de mercados principales
MARKETS_CONFIG = {
    '^GSPC': {  # S&P 500
        'name': 'S&P 500 (NYSE)',
        'country': 'United States',
        'timezone': 'America/New_York',
        'lat': 40.7128,
        'lon': -74.0060,
        'region': 'América del Norte'
    },
    '^IXIC': {  # NASDAQ
        'name': 'NASDAQ',
        'country': 'United States',
        'timezone': 'America/New_York',
        'lat': 40.7589,
        'lon': -73.9851,
        'region': 'América del Norte'
    },
    '^FTSE': {  # FTSE 100
        'name': 'FTSE 100 (Londres)',
        'country': 'United Kingdom',
        'timezone': 'Europe/London',
        'lat': 51.5074,
        'lon': -0.1278,
        'region': 'Europa'
    },
    '^GDAXI': {  # DAX
        'name': 'DAX (Frankfurt)',
        'country': 'Germany',
        'timezone': 'Europe/Berlin',
        'lat': 50.1109,
        'lon': 8.6821,
        'region': 'Europa'
    },
    '^FCHI': {  # CAC 40
        'name': 'CAC 40 (París)',
        'country': 'France',
        'timezone': 'Europe/Paris',
        'lat': 48.8566,
        'lon': 2.3522,
        'region': 'Europa'
    },
    '^IBEX': {  # IBEX 35
        'name': 'IBEX 35 (Madrid)',
        'country': 'Spain',
        'timezone': 'Europe/Madrid',
        'lat': 40.4168,
        'lon': -3.7038,
        'region': 'Europa'
    },
    '^N225': {  # Nikkei 225
        'name': 'Nikkei 225 (Tokio)',
        'country': 'Japan',
        'timezone': 'Asia/Tokyo',
        'lat': 35.6762,
        'lon': 139.6503,
        'region': 'Asia-Pacífico'
    },
    '000001.SS': {  # Shanghai Composite
        'name': 'Shanghai Composite',
        'country': 'China',
        'timezone': 'Asia/Shanghai',
        'lat': 31.2304,
        'lon': 121.4737,
        'region': 'Asia-Pacífico'
    },
    '^HSI': {  # Hang Seng
        'name': 'Hang Seng (Hong Kong)',
        'country': 'Hong Kong',
        'timezone': 'Asia/Hong_Kong',
        'lat': 22.3193,
        'lon': 114.1694,
        'region': 'Asia-Pacífico'
    },
    '^BVSP': {  # Bovespa
        'name': 'Bovespa (São Paulo)',
        'country': 'Brazil',
        'timezone': 'America/Sao_Paulo',
        'lat': -23.5505,
        'lon': -46.6333,
        'region': 'América Latina'
    },
    '^GSPTSE': {  # TSX
        'name': 'TSX (Toronto)',
        'country': 'Canada',
        'timezone': 'America/Toronto',
        'lat': 43.6532,
        'lon': -79.3832,
        'region': 'América del Norte'
    },
    '^AXJO': {  # ASX 200
        'name': 'ASX 200 (Sídney)',
        'country': 'Australia',
        'timezone': 'Australia/Sydney',
        'lat': -33.8688,
        'lon': 151.2093,
        'region': 'Asia-Pacífico'
    }
}

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_single_market_data(symbol):
    """Obtiene datos de un mercado específico"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Obtener datos históricos
        hist = ticker.history(period="1y")
        
        if hist.empty:
            return None
        
        # Datos actuales
        current_price = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        # Calcular cambio porcentual
        change_percent = ((current_price - previous_close) / previous_close) * 100
        
        # Calcular MA200 si hay suficientes datos
        if len(hist) >= 200:
            ma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
            ma200_trend = "📈 Alcista" if current_price > ma200 else "📉 Bajista"
        else:
            ma200_trend = "📊 Sin datos"
        
        return {
            'price': float(current_price),
            'change_percent': float(change_percent),
            'ma200_trend': ma200_trend,
            'volume': float(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0,
            'last_update': datetime.now().strftime('%H:%M:%S')
        }
        
    except Exception as e:
        st.error(f"Error obteniendo datos para {symbol}: {str(e)}")
        return None

def get_market_data():
    """Obtiene datos de todos los mercados configurados"""
    market_data = {}
    
    # Crear barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_markets = len(MARKETS_CONFIG)
    successful_requests = 0
    
    for i, symbol in enumerate(MARKETS_CONFIG.keys()):
        status_text.text(f'📡 Obteniendo datos de {MARKETS_CONFIG[symbol]["name"]}...')
        progress_bar.progress((i + 1) / total_markets)
        
        data = get_single_market_data(symbol)
        if data:
            market_data[symbol] = data
            successful_requests += 1
        else:
            market_data[symbol] = None
    
    # Limpiar elementos de progreso
    progress_bar.empty()
    status_text.empty()
    
    # Mostrar resultado
    if successful_requests > 0:
        st.success(f"✅ Datos obtenidos exitosamente de {successful_requests}/{total_markets} mercados")
    else:
        st.error("❌ No se pudieron obtener datos de ningún mercado")
    
    return market_data

def get_market_status(timezone_str):
    """Determina si un mercado está abierto o cerrado"""
    try:
        # Zona horaria del mercado
        market_tz = pytz.timezone(timezone_str)
        now_market = datetime.now(market_tz)
        
        # Obtener día de la semana (0=lunes, 6=domingo)
        weekday = now_market.weekday()
        
        # Mercados cerrados en fin de semana
        if weekday >= 5:  # Sábado o domingo
            return {
                'is_open': False,
                'status': 'Cerrado (Fin de semana)',
                'next_action': 'Abre el lunes'
            }
        
        # Horarios aproximados (9:00 - 17:00)
        current_hour = now_market.hour
        
        if 9 <= current_hour <= 17:
            return {
                'is_open': True,
                'status': 'Abierto',
                'next_action': f'Cierra a las 17:00'
            }
        elif current_hour < 9:
            return {
                'is_open': False,
                'status': 'Pre-mercado',
                'next_action': f'Abre a las 09:00'
            }
        else:
            return {
                'is_open': False,
                'status': 'Post-mercado',
                'next_action': f'Abre mañana a las 09:00'
            }
            
    except Exception as e:
        return {
            'is_open': False,
            'status': 'Estado desconocido',
            'next_action': 'Verificar zona horaria'
        }

def get_emoji_by_change(change_pct):
    """Determina el emoji según el cambio porcentual"""
    if change_pct > 1:
        return "☀️"  # Subida fuerte
    elif change_pct > 0:
        return "🌤️"  # Subida leve
    elif change_pct > -1:
        return "☁️"  # Bajada leve
    else:
        return "🌩️"  # Bajada fuerte

def get_color_by_change(change_pct):
    """Determina el color según el cambio porcentual"""
    if change_pct > 1:
        return "#00C851"  # Verde fuerte
    elif change_pct > 0:
        return "#7CB342"  # Verde claro
    elif change_pct > -1:
        return "#FF8A65"  # Naranja claro
    else:
        return "#FF1744"  # Rojo fuerte

def create_world_map_alternative(market_data):
    """Mapa mundial simplificado usando emojis y HTML"""
    
    st.markdown("### 🌍 Vista Global de Mercados")
    
    # Crear un mapa de texto estilizado
    map_html = """
    <div style="background: linear-gradient(180deg, #e3f2fd 0%, #bbdefb 100%); 
                border-radius: 15px; padding: 30px; margin: 20px 0;">
        <h3 style="text-align: center; color: #1976d2; margin-bottom: 30px;">
            🌍 Estado Global de Mercados Bursátiles
        </h3>
    """
    
    # Organizar por regiones
    regions = {
        "🌅 Asia-Pacífico": ["^N225", "000001.SS", "^HSI", "^AXJO"],
        "🌍 Europa": ["^FTSE", "^GDAXI", "^FCHI", "^IBEX"],
        "🌎 América": ["^GSPC", "^IXIC", "^GSPTSE", "^BVSP"]
    }
    
    for region_name, symbols in regions.items():
        map_html += f"""
        <div style="margin: 20px 0; padding: 20px; background: rgba(255,255,255,0.7); 
                    border-radius: 10px; border-left: 5px solid #1976d2;">
            <h4 style="color: #1976d2; margin-bottom: 15px;">{region_name}</h4>
            <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center;">
        """
        
        for symbol in symbols:
            if symbol in market_data and market_data[symbol]:
                data = market_data[symbol]
                config = MARKETS_CONFIG[symbol]
                
                change_pct = data['change_percent']
                weather_emoji = get_emoji_by_change(change_pct)
                color = get_color_by_change(change_pct)
                market_status = get_market_status(config['timezone'])
                status_emoji = "🟢" if market_status['is_open'] else "🔴"
                
                market_name = config['name'].split('(')[0].strip()[:10]
                
                map_html += f"""
                <div style="background: white; border-radius: 8px; padding: 15px; 
                           min-width: 140px; text-align: center; border: 2px solid {color};
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1); cursor: pointer;
                           transition: transform 0.2s;"
                           onmouseover="this.style.transform='scale(1.05)'"
                           onmouseout="this.style.transform='scale(1)'">
                    <div style="font-size: 28px; margin-bottom: 5px;">{weather_emoji}</div>
                    <div style="font-weight: bold; font-size: 12px; color: #333; margin-bottom: 5px;">
                        {market_name}
                    </div>
                    <div style="color: {color}; font-weight: bold; font-size: 16px; margin-bottom: 5px;">
                        {change_pct:+.2f}%
                    </div>
                    <div style="font-size: 12px; color: #666; margin-bottom: 3px;">
                        ${data['price']:,.0f}
                    </div>
                    <div style="font-size: 10px; color: #888;">
                        {status_emoji} {market_status['status'][:8]}
                    </div>
                </div>
                """
        
        map_html += """
            </div>
        </div>
        """
    
    map_html += "</div>"
    
    st.markdown(map_html, unsafe_allow_html=True)

def create_summary_cards(market_data):
    """Crea tarjetas resumen de los mercados"""
    
    valid_data = [data for data in market_data.values() if data]
    
    if not valid_data:
        st.warning("⚠️ No hay datos disponibles para mostrar resumen")
        return
    
    # Contar mercados por estado
    strong_up = sum(1 for data in valid_data if data['change_percent'] > 1)
    light_up = sum(1 for data in valid_data if 0 < data['change_percent'] <= 1)
    light_down = sum(1 for data in valid_data if -1 <= data['change_percent'] < 0)
    strong_down = sum(1 for data in valid_data if data['change_percent'] < -1)
    
    # Mercados abiertos
    open_markets = sum(1 for symbol in market_data.keys() 
                      if symbol in MARKETS_CONFIG and market_data[symbol] and
                      get_market_status(MARKETS_CONFIG[symbol]['timezone'])['is_open'])
    
    total_markets = len(valid_data)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="☀️ Subida Fuerte",
            value=f"{strong_up} mercados",
            delta=f"{strong_up/total_markets*100:.1f}%" if total_markets > 0 else "0%"
        )
    
    with col2:
        st.metric(
            label="🌤️ Subida Leve",
            value=f"{light_up} mercados",
            delta=f"{light_up/total_markets*100:.1f}%" if total_markets > 0 else "0%"
        )
    
    with col3:
        st.metric(
            label="☁️ Bajada Leve",
            value=f"{light_down} mercados",
            delta=f"-{light_down/total_markets*100:.1f}%" if total_markets > 0 else "0%"
        )
    
    with col4:
        st.metric(
            label="🌩️ Bajada Fuerte",
            value=f"{strong_down} mercados",
            delta=f"-{strong_down/total_markets*100:.1f}%" if total_markets > 0 else "0%"
        )
    
    with col5:
        st.metric(
            label="🟢 Mercados Abiertos",
            value=f"{open_markets}/{len(MARKETS_CONFIG)}",
            delta=f"{open_markets/len(MARKETS_CONFIG)*100:.1f}%"
        )

def create_detailed_table(market_data):
    """Crea tabla detallada de mercados"""
    
    table_data = []
    
    for symbol, data in market_data.items():
        if data and symbol in MARKETS_CONFIG:
            config = MARKETS_CONFIG[symbol]
            market_status = get_market_status(config['timezone'])
            
            table_data.append({
                'Mercado': config['name'],
                'Región': config['region'],
                'Clima': get_emoji_by_change(data['change_percent']),
                'Precio': f"${data['price']:,.2f}",
                'Cambio (%)': f"{data['change_percent']:+.2f}%",
                'MA200': data['ma200_trend'],
                'Estado': "🟢 Abierto" if market_status['is_open'] else "🔴 Cerrado",
                'Próxima Acción': market_status['next_action']
            })
    
    if not table_data:
        st.warning("⚠️ No hay datos disponibles para mostrar la tabla")
        return
    
    # Ordenar por cambio porcentual (descendente)
    table_data.sort(key=lambda x: float(x['Cambio (%)'].replace('%', '').replace('+', '')), reverse=True)
    
    df = pd.DataFrame(table_data)
    
    # Mostrar tabla con estilo
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Clima': st.column_config.TextColumn('🌤️', width="small"),
            'Cambio (%)': st.column_config.TextColumn('📈 Cambio (%)', width="medium"),
            'MA200': st.column_config.TextColumn('📊 MA200', width="medium"),
            'Estado': st.column_config.TextColumn('🚦 Estado', width="medium")
        }
    )

def main():
    """Función principal de la aplicación"""
    
    # Título principal
    st.title("🌍 Mapa Financiero Mundial")
    st.markdown("### Tu radar bursátil global en tiempo real")
    
    # Sidebar con información
    with st.sidebar:
        st.header("📊 Cómo Interpretar")
        
        st.markdown("""
        **🌤️ Emoticonos Climáticos:**
        - ☀️ Subida fuerte (>1%)
        - 🌤️ Subida leve (0-1%)
        - ☁️ Bajada leve (0 a -1%)
        - 🌩️ Bajada fuerte (<-1%)
        
        **📈 Indicadores:**
        - **Precio**: Valor actual del índice
        - **MA200**: Media móvil 200 períodos
        - **Estado**: Mercado abierto/cerrado
        
        **🎯 Utilidad:**
        Identifica rápidamente oportunidades y riesgos globales para optimizar tu estrategia de inversión.
        """)
        
        st.markdown("---")
        st.info("💡 **Versión Estable**: Funciona completamente con dependencias mínimas.")
        
        # Botón de actualización
        if st.button("🔄 Actualizar Datos", type="primary"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown(f"**⏰ Última actualización:**  \n{datetime.now().strftime('%H:%M:%S')}")
    
    # Mostrar mensaje de carga
    with st.spinner("📡 Conectando con mercados financieros globales..."):
        market_data = get_market_data()
    
    # Verificar si hay datos
    valid_data_count = sum(1 for data in market_data.values() if data)
    
    if valid_data_count == 0:
        st.error("❌ No se pudieron obtener datos de mercado. Intenta nuevamente en unos minutos.")
        st.info("💡 Esto puede deberse a limitaciones de la API o problemas de conectividad.")
        return
    
    # Tarjetas resumen
    st.markdown("### 📊 Resumen Global")
    create_summary_cards(market_data)
    
    st.markdown("---")
    
    # Mapa visual alternativo
    create_world_map_alternative(market_data)
    
    # Leyenda explicativa
    st.markdown("---")
    st.markdown("""
    **💡 Cómo interpretar el mapa:**
    - **Colores y emoticonos**: Representan el rendimiento actual
    - **Tamaños**: Indican la importancia relativa del mercado
    - **Estados**: Muestran si el mercado está operando (🟢/🔴)
    - **Hover**: Pasa el cursor sobre las tarjetas para mejor visualización
    """)
    
    st.markdown("---")
    
    # Tabla detallada
    st.markdown("### 📋 Análisis Detallado por Mercado")
    create_detailed_table(market_data)
    
    # Footer informativo
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px; background: #f8f9fa; border-radius: 10px;'>
        🚀 <b>Mapa Financiero Mundial v2.0</b><br>
        📊 Datos en tiempo real proporcionados por Yahoo Finance<br>
        💡 Herramienta diseñada para inversores inteligentes<br>
        ⚠️ <i>Solo para fines educativos e informativos - No constituye asesoramiento financiero</i>
    </div>
    """, unsafe_allow_html=True)
    
    # Información técnica
    with st.expander("ℹ️ Información Técnica"):
        st.markdown(f"""
        **📊 Estadísticas de esta sesión:**
        - Mercados configurados: {len(MARKETS_CONFIG)}
        - Datos obtenidos exitosamente: {valid_data_count}
        - Tasa de éxito: {valid_data_count/len(MARKETS_CONFIG)*100:.1f}%
        - Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        **🔧 Características técnicas:**
        - Cache inteligente de 5 minutos
        - Manejo robusto de errores
        - Interfaz responsive
        - Sin dependencias problemáticas
        """)

if __name__ == "__main__":
    main()
