import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuración de la página
st.set_page_config(page_title="Visor Provincial - MSP", layout="wide")

# --- ESTILO PERSONALIZADO PARA EL SIDEBAR ---
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #6f2da8;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        /* Color de la opción seleccionada en el menú radio */
        div.ststr-emotion-cache-1n76uvy e1nzilvr4 {
            background-color: rgba(255, 255, 255, 0.2);
        }
    </style>
""", unsafe_allow_html=True)

# --- CONTENIDO DEL SIDEBAR (MENÚ) ---
with st.sidebar:
    # Cargar Imagen del Logo
    # Si la imagen está en tu GitHub, se cargará así:
    if os.path.exists("logo_ecuador.png"):
        st.image("logo_ecuador.png", use_container_width=True)
    else:
        # Texto de respaldo si la imagen no se encuentra
        st.markdown("## EL NUEVO \n # ECUADOR")
    
    st.markdown("<h3 style='text-align: center;'>Ministerio de Salud Pública</h3>", unsafe_allow_html=True)
    st.write("---")
    st.markdown("<p style='text-align: center; font-weight: bold;'>Visor de Disponibilidad y Abastecimiento Provincial</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Menú de Navegación con nombres de tu imagen image_feae1d.png
    opcion_menu = st.radio(
        "MENÚ PRINCIPAL:",
        ["💊 Abastecimiento Médico", "🛏️ Disponibilidad de Camas", "👥 Talento Humano"],
        index=0
    )

# --- LÓGICA DE NAVEGACIÓN ---

if "Abastecimiento Médico" in opcion_menu:
    st.title("🏥 Abastecimiento Médico")
    
    SHEET_ID = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    @st.cache_data(ttl=60)
    def load_data():
        df = pd.read_csv(SHEET_URL)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        for col in ['OFICINA TECNICA', 'UNIDAD OPERATIVA', 'CATEGORIA']:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', 'SIN DATO').str.strip()
        col_p = 'PORCENTAJE DE ABASTECIMIENTO'
        if col_p in df.columns:
            df[col_p] = df[col_p].astype(str).str.replace('%','').str.replace(',','.').str.strip()
            df[col_p] = pd.to_numeric(df[col_p], errors='coerce').fillna(0)
        return df

    try:
        df = load_data()
        
        # Filtros
        c1, c2 = st.columns(2)
        with c1:
            lista_oficinas = sorted([x for x in df['OFICINA TECNICA'].unique() if x not in ['SIN DATO', 'nan']])
            oficina = st.selectbox("Oficina Técnica", lista_oficinas)
        with c2:
            df_sub = df[df['OFICINA TECNICA'] == oficina]
            lista_unidades = sorted([x for x in df_sub['UNIDAD OPERATIVA'].unique() if x not in ['SIN DATO', 'nan']])
            unidad = st.selectbox("Unidad Operativa", lista_unidades)

        df_f = df[(df['OFICINA TECNICA'] == oficina) & (df['UNIDAD OPERATIVA'] == unidad)]
        
        # Métrica Principal
        val = df_f['PORCENTAJE DE ABASTECIMIENTO'].mean()
        st.markdown(f"<h3 style='text-align: center;'>PORCENTAJE DE ABASTECIMIENTO</h3>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='text-align: center; color: #6f2da8; font-size: 60px;'>{val:.2f} %</h1>", unsafe_allow_html=True)
        
        # Gráfico de Barras
        fig = px.bar(
            df_f, 
            x='CATEGORIA', 
            y='PORCENTAJE DE ABASTECIMIENTO', 
            text='PORCENTAJE DE ABASTECIMIENTO',
            color_discrete_sequence=['#6f2da8']
        )
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig.update_layout(yaxis_range=[0, 110], xaxis_title="", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error("Error al cargar los datos.")

elif "Disponibilidad de Camas" in opcion_menu:
    st.title("🛏️ Disponibilidad de Camas")
    st.info("Conecte aquí su base de datos de hospitalización.")

elif "Talento Humano" in opcion_menu:
    st.title("👥 Talento Humano")
    st.info("Conecte aquí su base de datos de personal.")
