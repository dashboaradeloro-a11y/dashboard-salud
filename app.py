import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 1. Configuración de la página
st.set_page_config(page_title="Visor Provincial - MSP", layout="wide")

# 2. Estilo Visual (Morado Institucional)
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #6f2da8; }
        [data-testid="stSidebar"] * { color: white !important; }
        .stMetric { 
            background-color: #f8f9fa; 
            padding: 15px; 
            border-radius: 10px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
            border: 1px solid #ddd;
        }
    </style>
""", unsafe_allow_html=True)

# 3. IDs de los Google Sheets
ID_ABASTECIMIENTO = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
ID_CAMAS = "1pBAjzXUCrlhFdQsj7foG41vhLMcAKjtRyUsf3_avYdE"

# --- FUNCIONES DE CARGA ---

@st.cache_data(ttl=60)
def load_abastecimiento():
    url = f"https://docs.google.com/spreadsheets/d/{ID_ABASTECIMIENTO}/export?format=csv&gid=0"
    df = pd.read_csv(url)
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    for col in ['OFICINA TECNICA', 'UNIDAD OPERATIVA', 'CATEGORIA']:
        if col in df.columns: df[col] = df[col].astype(str).replace('nan', 'SIN DATO').str.strip()
    col_p = 'PORCENTAJE DE ABASTECIMIENTO'
    if col_p in df.columns:
        df[col_p] = pd.to_numeric(df[col_p].astype(str).str.replace('%','').str.replace(',','.').str.strip(), errors='coerce').fillna(0)
    return df

@st.cache_data(ttl=60)
def load_camas():
    # Nota: Se usa gid=0 para la primera pestaña del segundo sheet
    url = f"https://docs.google.com/spreadsheets/d/{ID_CAMAS}/export?format=csv&gid=0"
    df = pd.read_csv(url)
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    for col in ['Hospital', 'Servicio']:
        if col in df.columns: df[col] = df[col].astype(str).str.strip()
    
    # Conversión de números según tus columnas: Camas Asignadas, Camas Ocupadas, Camas Disponibles
    for col in ['Camas Asignadas', 'Camas Ocupadas', 'Camas Disponibles']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

# --- SIDEBAR (MENÚ) ---
with st.sidebar:
    if os.path.exists("logo_ecuador.png"):
        st.image("logo_ecuador.png", use_container_width=True)
    st.markdown("<h3 style='text-align: center;'>Ministerio de Salud Pública</h3>", unsafe_allow_html=True)
    st.write("---")
    opcion = st.radio("MENÚ PRINCIPAL:", ["💊 Abastecimiento Médico", "🛏️ Disponibilidad de Camas", "👥 Talento Humano"])

# --- LÓGICA DE NAVEGACIÓN ---

if "Abastecimiento Médico" in opcion:
    st.title("🏥 Abastecimiento Médico")
    df = load_abastecimiento()
    
    col1, col2 = st.columns(2)
    with col1:
        oficina = st.selectbox("Oficina Técnica", sorted(df['OFICINA TECNICA'].unique()))
    with col2:
        unidad = st.selectbox("Unidad Operativa", sorted(df[df['OFICINA TECNICA'] == oficina]['UNIDAD OPERATIVA'].unique()))
    
    df_f = df[(df['OFICINA TECNICA'] == oficina) & (df['UNIDAD OPERATIVA'] == unidad)]
    val = df_f['PORCENTAJE DE ABASTECIMIENTO'].mean()
    
    st.markdown(f"<h3 style='text-align: center;'>PORCENTAJE DE ABASTECIMIENTO</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; color: #6f2da8; font-size: 60px;'>{val:.2f} %</h1>", unsafe_allow_html=True)
    
    fig = px.bar(df_f, x='CATEGORIA', y='PORCENTAJE DE ABASTECIMIENTO', text='PORCENTAJE DE ABASTECIMIENTO', color_discrete_sequence=['#6f2da8'])
    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

elif "Disponibilidad de Camas" in opcion:
    st.title("🛏️ Disponibilidad de Camas")
    df_c = load_camas()

    f1, f2 = st.columns(2)
    with f1:
        hosp = st.selectbox("Hospital", options=["TODOS"] + sorted(df_c['Hospital'].unique().tolist()))
    with f2:
        serv = st.selectbox("Servicio", options=["TODOS"] + sorted(df_c['Servicio'].unique().tolist()))

    df_f = df_c.copy()
    if hosp != "TODOS": df_f = df_f[df_f['Hospital'] == hosp]
    if serv != "TODOS": df_f = df_f[df_f['Servicio'] == serv]

    # Métricas
    m1, m2, m3 = st.columns(3)
    t_asig = df_f['Camas Asignadas'].sum()
    t_ocup = df_f['Camas Ocupadas'].sum()
    p_ocu = (t_ocup / t_asig * 100) if t_asig > 0 else 0

    with m1: st.metric("Camas Asignadas", int(t_asig))
    with m2: st.metric("Camas Ocupadas", int(t_ocup))
    with m3: st.metric("% Ocupación", f"{p_ocu:.2f} %")

    # Gráfico Agrupado
    resumen = df_f.groupby('Servicio').sum(numeric_only=True).reset_index()
    fig_camas = go.Figure()
    fig_camas.add_trace(go.Bar(name='Camas Disponibles', x=resumen['Servicio'], y=resumen['Camas Disponibles'], marker_color='#0097a7', text=resumen['Camas Disponibles'], textposition='outside'))
    fig_camas.add_trace(go.Bar(name='Camas Asignadas', x=resumen['Servicio'], y=resumen['Camas Asignadas'], marker_color='#6f2da8', text=resumen['Camas Asignadas'], textposition='outside'))
    
    fig_camas.update_layout(barmode='group', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_camas, use_container_width=True)

elif "Talento Humano" in opcion:
    st.title("👥 Talento Humano")
    st.info("Módulo en fase de diseño.")
