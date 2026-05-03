import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Abastecimiento", layout="wide")

# URL de tu Google Sheet
SHEET_ID = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    
    # 1. Limpieza de nombres de columnas
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    
    # 2. Asegurar que las columnas de texto no tengan errores
    columnas_texto = ['OFICINA TECNICA', 'UNIDAD OPERATIVA', 'CATEGORIA']
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).replace('nan', 'SIN DATO').str.strip()
    
    # 3. LIMPIEZA REFORZADA DE PORCENTAJE (Para evitar el error de 'string dtype')
    col_porcentaje = 'PORCENTAJE DE ABASTECIMIENTO'
    if col_porcentaje in df.columns:
        # Convertimos todo a string primero para poder limpiar símbolos
        df[col_porcentaje] = df[col_porcentaje].astype(str)
        # Quitamos %, espacios, cambiamos comas por puntos
        df[col_porcentaje] = (
            df[col_porcentaje]
            .str.replace('%', '', regex=False)
            .str.replace(',', '.', regex=False)
            .str.strip()
        )
        # Convertimos a número real. Si algo no es número, se vuelve NaN (vacio)
        df[col_porcentaje] = pd.to_numeric(df[col_porcentaje], errors='coerce')
        # Llenamos los vacíos con 0
        df[col_porcentaje] = df[col_porcentaje].fillna(0)
        
    return df

try:
    df = load_data()

    st.markdown("<h1 style='text-align: center;'>📊 Control de Abastecimiento</h1>", unsafe_allow_html=True)
    st.divider()

    # --- FILTROS ---
    col1, col2 = st.columns(2)
    
    with col1:
        # Filtrar para no mostrar "SIN DATO" en el menú
        opciones_oficina = sorted([x for x in df['OFICINA TECNICA'].unique() if x != 'SIN DATO' and x != 'nan'])
        oficina_sel = st.selectbox("Seleccione Oficina Técnica:", options=opciones_oficina)

    with col2:
        # Unidades dependientes de la oficina
        df_sub = df[df['OFICINA TECNICA'] == oficina_sel]
        opciones_unidad = sorted([x for x in df_sub['UNIDAD OPERATIVA'].unique() if x != 'SIN DATO' and x != 'nan'])
        unidad_sel = st.selectbox("Seleccione Unidad Operativa:", options=opciones_unidad)

    # --- FILTRADO FINAL ---
    df_filtrado = df[(df['OFICINA TECNICA'] == oficina_sel) & (df['UNIDAD OPERATIVA'] == unidad_sel)].copy()

    # --- MÉTRICA ---
    # Ahora 'PORCENTAJE DE ABASTECIMIENTO' es garantizado tipo float
    promedio_total = df_filtrado['PORCENTAJE DE ABASTECIMIENTO'].mean()
    
    st.markdown(f"<h3 style='text-align: center;'>PORCENTAJE DE ABASTECIMIENTO</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; color: #6f2da8; font-size: 60px;'>{promedio_total:.2f} %</h1>", unsafe_allow_html=True)

    # --- GRÁFICO ---
    fig = px.bar(
        df_filtrado,
        x='CATEGORIA',
        y='PORCENTAJE DE ABASTECIMIENTO',
        text='PORCENTAJE DE ABASTECIMIENTO',
        color_discrete_sequence=['#6f2da8']
    )

    fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
    fig.update_layout(
        yaxis_range=[0, 110],
        xaxis_title="",
        yaxis_title="Porcentaje (%)",
        plot_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("Se encontró un problema con el formato de los datos.")
    st.info("Revisa que en tu Sheets la columna de porcentajes solo tenga números.")
    st.exception(e)
