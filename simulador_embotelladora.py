import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import time
import random
import requests
import json

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="HMI Avanzado Embotelladora", page_icon="🏭", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #F4F6F9; color: #333333; font-family: 'Arial', sans-serif; }
        .stMetric { background-color: #FFFFFF; padding: 15px; border-radius: 10px; border: 1px solid #DEE2E6; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. INTEGRACIÓN POWER BI WEB (API STREAMING)
# ==========================================
POWER_BI_API_URL = "" 

def push_to_power_bi(data_dict):
    if not POWER_BI_API_URL: return
    try:
        payload = [{
            "Fecha": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "OEE": float(data_dict['oee']),
            "Brix": float(data_dict['brix']),
            "Temp": float(data_dict['temp']),
            "Botellas_OK": int(data_dict['ok']),
            "Defectos": int(data_dict['malas'])
        }]
        headers = {"Content-Type": "application/json"}
        requests.post(POWER_BI_API_URL, data=json.dumps(payload), headers=headers, timeout=1)
    except Exception:
        pass 

# ==========================================
# 2. MOTOR GRÁFICO SVG (SCADA REDONDEADO Y ALTO CONTRASTE)
# ==========================================
def render_scada_continuo(v, m, is_es):
    c_on = "#39A900"; c_off = "#95A5A6"; c_warn = "#F1C40F"; c_err = "#E74C3C"
    pwr = v['main_pwr']
    
    # Tuberías dinámicas con el color de los fluidos activos
    c_pipe_agua = "#3498DB" if (v['v_agua'] > 0 and pwr) else "#BDC3C7"
    c_pipe_conc = "#E67E22" if (v['v_conc'] > 0 and pwr) else "#BDC3C7"
    c_pipe_salida = "#2ECC71" if (v['banda'] and v['bpm'] > 0 and v['nivel'] > 0 and pwr) else "#BDC3C7"
    
    # Altura del tanque (0 a 100% -> 0 a 120px)
    h_liq = (v['nivel'] / 100.0) * 120
    y_liq = 220 - h_liq
    
    # Color del fluido dentro del tanque según calidad
    c_liq = "#2ECC71" 
    if v['temp'] < 85 or v['temp'] > 95 or v['brix'] < 11 or v['brix'] > 13:
        c_liq = c_err
        
    anim_banda = "move_belt 0.5s linear infinite" if (v['banda'] and pwr and v['nivel'] > 0 and v['bpm'] > 0) else "none"
    anim_agit = "spin 1s linear infinite" if (v['agitador'] and pwr) else "none"

    svg = f"""
    <style>
        @keyframes move_belt {{ 100% {{ stroke-dashoffset: -20; }} }}
        @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
        .txt {{ font-family: Arial, sans-serif; font-size: 12px; font-weight: bold; fill: #000000; }}
        .val {{ font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; fill: #00324D; }}
        .pipe {{ stroke-width: 8; fill: none; stroke-linecap: round; }}
    </style>
    <svg viewBox="0 0 900 450" width="100%" height="100%" style="background-color: #FFFFFF; border: 2px solid #BDC3C7; border-radius: 15px; padding: 10px;">
        <rect x="0" y="0" width="900" height="40" fill="#00324D" rx="10"/>
        <text x="20" y="25" class="txt" fill="#FFF" font-size="14px">HMI EN TIEMPO REAL: LÍNEA DE EMBOTELLADO CONTINUO</text>
        
        <path d="M 50,80 L 220,80 L 220,100" class="pipe" stroke="{c_pipe_agua}"/>
        <text x="20" y="70" class="txt">AGUA</text>
        <circle cx="120" cy="80" r="15" fill="{c_on if v['v_agua']>0 else c_off}" stroke="#333" stroke-width="2"/>
        
        <path d="M 50,130 L 250,130 L 250,100" class="pipe" stroke="{c_pipe_conc}"/>
        <text x="20" y="120" class="txt">CONCENTRADO</text>
        <circle cx="120" cy="130" r="15" fill="{c_on if v['v_conc']>0 else c_off}" stroke="#333" stroke-width="2"/>

        <rect x="200" y="100" width="100" height="120" fill="#ECF0F1" stroke="#333" stroke-width="3" rx="10"/>
        <rect x="202" y="{y_liq}" width="96" height="{h_liq}" fill="{c_liq}" rx="5" opacity="0.8"/>
        
        <line x1="250" y1="100" x2="250" y2="180" stroke="#333" stroke-width="4"/>
        <g style="transform-box: fill-box; transform-origin: center; animation: {anim_agit};">
            <ellipse cx="250" cy="180" rx="30" ry="8" fill="#7F8C8D" stroke="#333"/>
        </g>
        
        <rect x="310" y="90" width="90" height="40" fill="#FFFFFF" stroke="#000000" stroke-width="2" rx="5"/>
        <text x="315" y="105" class="txt" fill="#000000">LIQ-01 (%)</text>
        <text x="315" y="125" class="val" fill="{c_err if v['nivel'] > 95 or v['nivel'] < 5 else '#00324D'}">{v['nivel']:.1f}%</text>

        <rect x="310" y="145" width="90" height="40" fill="#FFFFFF" stroke="#000000" stroke-width="2" rx="5"/>
        <text x="315" y="160" class="txt" fill="#000000">BRIX-01</text>
        <text x="315" y="180" class="val" fill="{c_err if v['brix'] < 11 or v['brix'] > 13 else '#39A900'}">{v['brix']:.1f}</text>

        <path d="M 250,220 L 250,280 L 450,280 L 450,220" class="pipe" stroke="#95A5A6"/>
        
        <rect x="400" y="100" width="120" height="120" fill="{c_warn if v['v_vapor']>0 else c_off}" stroke="#333" stroke-width="3" rx="10"/>
        <text x="410" y="90" class="txt">PASTEURIZADOR</text>
        
        <rect x="415" y="145" width="90" height="40" fill="#FFFFFF" stroke="#000000" stroke-width="2" rx="5"/>
        <text x="420" y="160" class="txt" fill="#000000">TIC-01 (°C)</text>
        <text x="420" y="180" class="val" fill="{c_err if v['temp'] > 95 or v['temp'] < 85 else '#39A900'}">{v['temp']:.1f}°C</text>

        <path d="M 460,150 L 680,150 L 680,300" class="pipe" stroke="{c_pipe_salida}"/>
        <rect x="650" y="320" width="200" height="20" fill="#7F8C8D" rx="5"/>
        <line x1="650" y1="330" x2="850" y2="330" stroke="{c_pipe_salida}" stroke-width="6" stroke-dasharray="10,5" style="animation: {anim_banda};"/>
        <text x="650" y="360" class="txt">LÍNEA DE LLENADO</text>
    </svg>
    """
    return svg

# ==========================================
# 3. INICIALIZACIÓN DE ESTADO ROBUSTA
# ==========================================
if 'sim_active' not in st.session_state:
    st.session_state.update({
        'sim_active': False, 'login': False, 'nombre': '', 'lang': 'es',
        'last_time': time.time(), 'tiempo_simulado': 0, 'mutiplicador_tiempo': 1,
        'last_log_time': -1, 'historico': [],
        'vars': {
            'main_pwr': False, 'agitador': False, 'banda': False,
            'v_agua': 0, 'v_conc': 0, 'v_vapor': 0, 'bpm': 0,
            'nivel': 10.0, 'brix': 0.0, 'temp': 25.0, 'masa_agua': 10.0, 'masa_conc': 0.0
        },
        'metrics': {
            'ok': 0, 'malas': 0, 'teoria': 0, 'op_fallos': 0, 'seg_fallos': 0, 't_paro': 0,
            'perturbacion': 1.0 
        }
    })

if 'last_log_time' not in st.session_state:
    st.session_state.last_log_time = -1
    st.session_state.historico = []

is_es = st.session_state.lang == 'es'

# ==========================================
# 4. PANTALLA DE INGRESO
# ==========================================
if not st.session_state.login:
    st.title("⚙️ HMI Entrenamiento: Operación Continua (1 Hora)")
    st.info("Este simulador funciona en **TIEMPO REAL**. Deberás estabilizar las variables manteniendo el proceso en marcha sin interrupciones.")
    st.session_state.nombre = st.text_input("Nombre del Operador:")
    
    col1, col2 = st.columns(2)
    st.session_state.mutiplicador_tiempo = col1.selectbox("Velocidad de Simulación:", [1, 5, 10, 60], format_func=lambda x: f"{x}x (1 seg real = {x} seg simulados)")
    
    if st.button("INICIAR TURNO", type="primary") and st.session_state.nombre:
        st.session_state.login = True
        st.session_state.sim_active = True
        st.session_state.last_time = time.time()
        st.rerun()
    st.stop()

# ==========================================
# 5. LÓGICA DE FÍSICA Y TIEMPO REAL
# ==========================================
if st.session_state.sim_active:
    
    now = time.time()
    dt_real = now - st.session_state.last_time
    st.session_state.last_time = now
    
    dt_sim = dt_real * st.session_state.mutiplicador_tiempo 
    st.session_state.tiempo_simulado += dt_sim
    
    v = st.session_state.vars
    m = st.session_state.metrics

    if v['main_pwr']:
        if random.random() < 0.1: 
            m['perturbacion'] = random.uniform(0.9, 1.1)

        # Llenado y vaciado
        flujo_in_agua = (v['v_agua'] / 100.0) * 0.15 * m['perturbacion'] * dt_sim
        flujo_in_conc = (v['v_conc'] / 100.0) * 0.05 * m['perturbacion'] * dt_sim
        flujo_out = (v['bpm'] / 60.0) * 0.5 * dt_sim if v['banda'] and v['nivel'] > 0 else 0
        
        v['masa_agua'] += flujo_in_agua - (flujo_out * (v['masa_agua']/(v['nivel']+0.1)))
        v['masa_conc'] += flujo_in_conc - (flujo_out * (v['masa_conc']/(v['nivel']+0.1)))
        
        v['masa_agua'] = max(0.0, v['masa_agua'])
        v['masa_conc'] = max(0.0, v['masa_conc'])
        v['nivel'] = v['masa_agua'] + v['masa_conc']
        
        # Seguro anti-vacío absoluto
        if v['nivel'] <= 0.1:
             v['nivel'] = 0.0
             v['masa_agua'] = 0.0
             v['masa_conc'] = 0.0
        
        # Alarma de desborde
        if v['nivel'] > 100:
            m['seg_fallos'] += 1
            prop_agua = v['masa_agua'] / v['nivel']
            prop_conc = v['masa_conc'] / v['nivel']
            v['nivel'] = 100.0
            v['masa_agua'] = 100.0 * prop_agua
            v['masa_conc'] = 100.0 * prop_conc

        # Lógica Brix
        if v['nivel'] > 0.1:
            brix_teorico = (v['masa_conc'] / v['nivel']) * 60.0
            if v['agitador']:
                v['brix'] += (brix_teorico - v['brix']) * 0.1 * dt_sim
        else:
            v['brix'] = 0.0
            
        if v['brix'] < 0:
            v['brix'] = 0.0

        # Lógica de calor
        calor_in = (v['v_vapor'] / 100.0) * 10.0 * dt_sim
        perdida_calor = ((v['temp'] - 25.0) * 0.05 + flujo_out * 1.5) * dt_sim
        v['temp'] += calor_in - perdida_calor
        v['temp'] = min(150.0, max(25.0, v['temp']))

        # Acumulación de producción exacta
        if v['banda'] and v['bpm'] > 0:
            prod_actual = (v['bpm'] / 60.0) * dt_sim
            if v['nivel'] <= 0:
                m['op_fallos'] += 1
                m['t_paro'] += dt_sim
            else:
                if 85 <= v['temp'] <= 95 and 11 <= v['brix'] <= 13:
                    m['ok'] += prod_actual
                else:
                    m['malas'] += prod_actual
        else:
            m['t_paro'] += dt_sim

        # REGISTRO HISTÓRICO TIME-SERIES PARA ANÁLISIS EN POWER BI
        current_sec = int(st.session_state.tiempo_simulado)
        if current_sec % 10 == 0 and current_sec != st.session_state.last_log_time:
            st.session_state.last_log_time = current_sec
            st.session_state.historico.append({
                "Timestamp_Real": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Tiempo_Simulado_Seg": current_sec,
                "Reloj_Planta": f"{current_sec // 60:02d}:{current_sec % 60:02d}",
                "Nivel_LIQ01": round(v['nivel'], 2),
                "Brix_BRIX01": round(v['brix'], 2),
                "Temp_TIC01": round(v['temp'], 2),
                "Velocidad_BPM": v['bpm'],
                "Botellas_OK_Acumulado": int(m['ok']),
                "Defectos_Acumulado": int(m['malas']),
                "Fallos_Operativos": m['op_fallos'],
                "Errores_Seguridad": m['seg_fallos']
            })
    else:
        m['t_paro'] += dt_sim
        v['temp'] = max(25.0, v['temp'] - (0.5 * dt_sim))

# ==========================================
# 6. INTERFAZ LATERAL (PANEL DE CONTROL)
# ==========================================
mins_sim, secs_sim = divmod(int(st.session_state.tiempo_simulado), 60)

st.sidebar.markdown(f"### ⏱️ RELOJ PLANTA: {mins_sim:02d}:{secs_sim:02d}")
st.sidebar.markdown("---")

v = st.session_state.vars

v['main_pwr'] = st.sidebar.toggle("⚡ ENERGÍA PRINCIPAL", value=v['main_pwr'])
st.sidebar.markdown("### 🎛️ ACTUADORES DISCRETOS")
v['agitador'] = st.sidebar.toggle("⚙️ Agitador Tanque", value=v['agitador'])
v['banda'] = st.sidebar.toggle("📦 Banda Llenadora", value=v['banda'])

st.sidebar.markdown("### 🎚️ CONTROL ANÁLOGO (VÁLVULAS)")
v['v_agua'] = st.sidebar.slider("💧 Válvula Agua (%)", 0, 100, int(v['v_agua']), 5)
v['v_conc'] = st.sidebar.slider("🍯 Válvula Concentrado (%)", 0, 100, int(v['v_conc']), 5)
v['v_vapor'] = st.sidebar.slider("🔥 Válvula Vapor (%)", 0, 100, int(v['v_vapor']), 5)
v['bpm'] = st.sidebar.slider("⚡ Velocidad Llenado (BPM)", 0, 120, int(v['bpm']), 10)

if st.sidebar.button("🛑 PARO DE EMBOTELLADO (FINALIZAR TURNO)"):
    st.session_state.sim_active = False

# ==========================================
# 7. RENDERIZADO PRINCIPAL
# ==========================================
components.html(render_scada_continuo(st.session_state.vars, st.session_state.metrics, is_es), height=460)

# Métrica KPI Superior
m = st.session_state.metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Botellas OK", f"{int(m['ok'])}", "Calidad Aprobada")
c2.metric("Botellas Rechazadas", f"{int(m['malas'])}", "- Defectos", delta_color="inverse")
c3.metric("Fallos Operativos", m['op_fallos'])
c4.metric("Errores Seguridad", m['seg_fallos'])

# ==========================================
# BUCLE DE REFRESCO ESTABILIZADO
# ==========================================
if st.session_state.sim_active:
    t_total = max(1.0, st.session_state.tiempo_simulado)
    t_op = t_total - m['t_paro']
    disp = t_op / t_total
    rend = (m['ok'] + m['malas']) / ((120/60) * t_op) if t_op > 0 else 0
    cal = m['ok'] / (m['ok'] + m['malas']) if (m['ok'] + m['malas']) > 0 else 0
    oee_live = disp * rend * cal * 100

    if int(st.session_state.tiempo_simulado) % 5 == 0:
        push_to_power_bi({'oee': oee_live, 'brix': v['brix'], 'temp': v['temp'], 'ok': m['ok'], 'malas': m['malas']})

    # LA SOLUCIÓN: Pausa larga justo antes de reiniciar el bucle
    time.sleep(3.0) 
    st.rerun()
else:
    if st.session_state.login:
        st.error("🚨 TURNO DE TRABAJO FINALIZADO POR EL OPERADOR 🚨")
        st.markdown("### 📊 REPORTE DE RENDIMIENTO INDUSTRIAL")
        
        df_summary = pd.DataFrame([{"Operador": st.session_state.nombre, "Botellas_OK": int(m['ok']), "Defectos": int(m['malas']), "Fallos": m['op_fallos']}])
        st.dataframe(df_summary)
        
        if st.session_state.historico:
            st.markdown("### 📈 DATASET HISTÓRICO GENERADO (Para análisis temporal en Power BI)")
            df_full = pd.DataFrame(st.session_state.historico)
            st.write(f"Filas totales registradas durante el turno: {len(df_full)}")
            st.dataframe(df_full.tail(10)) 
            
            csv_bytes = df_full.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Dataset Histórico (.CSV)",
                data=csv_bytes,
                file_name=f"dataset_powerbi_{st.session_state.nombre}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.warning("No se registraron datos en el historial. Asegúrese de arrancar el proceso con la Energía Principal antes de finalizar.")
