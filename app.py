import streamlit as st
import pandas as pd
import plotly.express as px

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
        .st-emotion-cache-10o143l {
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- CONTENIDO DEL SIDEBAR (MENÚ) ---
with st.sidebar:
    # Logo o Texto Institucional
    st.markdown("## EL NUEVO \n # ECUADOR")
    st.markdown("### Ministerio de Salud Pública")
    st.write("---")
    st.markdown("#### 💻 Visor de Disponibilidad y Abastecimiento Provincial")
    st.write("---")
    
    # Menú de Navegación
    opcion_menu = st.radio(
        "Seleccione una opción:",
        ["Abastecimiento Médico", "Disponibilidad de Camas", "Talento Humano"],
        index=0
    )

# --- LÓGICA DE NAVEGACIÓN ---

if opcion_menu == "Abastecimiento Médico":
    # Aquí va el código que ya teníamos del Dashboard de Abastecimiento
    st.title("🏥 Abastecimiento Médico")
    
    # URL de tu Google Sheet
    SHEET_ID = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

    @st.cache_data(ttl=60)
    def load_data():
        df = pd.read_csv(SHEET_URL)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        # Limpieza de texto
        for col in ['OFICINA TECNICA', 'UNIDAD OPERATIVA', 'CATEGORIA']:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', 'SIN DATO').str.strip()
        
        # Limpieza de Porcentaje
        col_p = 'PORCENTAJE DE ABASTECIMIENTO'
        if col_p in df.columns:
            df[col_p] = df[col_p].astype(str).str.replace('%','').str.replace(',','.').str.strip()
            df[col_p] = pd.to_numeric(df[col_p], errors='coerce').fillna(0)
        return df

    try:
        df = load_data()
        
        # Filtros en la parte superior del contenido principal
        c1, c2 = st.columns(2)
        with c1:
            oficina = st.selectbox("Oficina Técnica", sorted(df['OFICINA TECNICA'].unique()))
        with c2:
            unidad = st.selectbox("Unidad Operativa", sorted(df[df['OFICINA TECNICA'] == oficina]['UNIDAD OPERATIVA'].unique()))

        df_f = df[(df['OFICINA TECNICA'] == oficina) & (df['UNIDAD OPERATIVA'] == unidad)]
        
        # Métrica
        val = df_f['PORCENTAJE DE ABASTECIMIENTO'].mean()
        st.markdown(f"<h1 style='text-align: center; color: #6f2da8;'>{val:.2f} %</h1>", unsafe_allow_html=True)
        
        # Gráfico
        fig = px.bar(df_f, x='CATEGORIA', y='PORCENTAJE DE ABASTECIMIENTO', text='PORCENTAJE DE ABASTECIMIENTO', color_discrete_sequence=['#6f2da8'])
        fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error("Error al cargar datos de Abastecimiento.")

elif opcion_menu == "Disponibilidad de Camas":
    st.title("🛏️ Disponibilidad de Camas")
    st.info("Sección en desarrollo. Conecte su base de datos de hospitalización aquí.")

elif opcion_menu == "Talento Humano":
    st.title("👥 Talento Humano")
    st.info("Sección en desarrollo. Conecte su base de datos de personal aquí.")
