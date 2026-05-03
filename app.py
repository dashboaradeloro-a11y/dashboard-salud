import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Abastecimiento", layout="wide")

# URL de tu Google Sheet (formato exportación CSV)
SHEET_ID = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=60)
def load_data():
    # Leer el CSV directamente desde Google
    df = pd.read_csv(SHEET_URL)
    
    # Limpieza de nombres de columnas: eliminar espacios al inicio/final y saltos de línea
    df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
    
    # Convertir la columna de porcentaje a número (por si tiene el símbolo % o comas)
    col_porcentaje = 'PORCENTAJE DE ABASTECIMIENTO'
    if col_porcentaje in df.columns:
        if df[col_porcentaje].dtype == object:
            df[col_porcentaje] = (
                df[col_porcentaje]
                .str.replace('%', '', regex=False)
                .str.replace(',', '.', regex=False)
                .astype(float)
            )
    return df

try:
    df = load_data()

    # Título del Dashboard
    st.markdown("<h1 style='text-align: center;'>📊 Control de Abastecimiento</h1>", unsafe_allow_html=True)
    st.divider()

    # --- FILTROS ---
    col1, col2 = st.columns(2)
    
    with col1:
        lista_oficinas = sorted(df['OFICINA TECNICA'].unique())
        oficina_sel = st.selectbox("Seleccione Oficina Técnica:", options=lista_oficinas)

    with col2:
        # Filtrar unidades operativas basadas en la oficina seleccionada
        unidades_disponibles = sorted(df[df['OFICINA TECNICA'] == oficina_sel]['UNIDAD OPERATIVA'].unique())
        unidad_sel = st.selectbox("Seleccione Unidad Operativa:", options=unidades_disponibles)

    # --- FILTRADO DE DATOS ---
    df_filtrado = df[(df['OFICINA TECNICA'] == oficina_sel) & (df['UNIDAD OPERATIVA'] == unidad_sel)]

    # --- MÉTRICA PRINCIPAL ---
    # Calculamos el promedio de abastecimiento de la selección
    promedio_total = df_filtrado['PORCENTAJE DE ABASTECIMIENTO'].mean()
    
    st.markdown(f"<h3 style='text-align: center;'>PORCENTAJE DE ABASTECIMIENTO</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center; color: #6f2da8; font-size: 60px;'>{promedio_total:.2f} %</h1>", unsafe_allow_html=True)

    # --- GRÁFICO DE BARRAS ---
    # Colores y orden de categorías para que sea idéntico a tu diseño
    fig = px.bar(
        df_filtrado,
        x='CATEGORIA',
        y='PORCENTAJE DE ABASTECIMIENTO',
        text='PORCENTAJE DE ABASTECIMIENTO',
        color_discrete_sequence=['#6f2da8']  # Color morado de tu referencia
    )

    fig.update_traces(
        texttemplate='%{text:.2f}%', 
        textposition='outside',
        marker_line_width=0
    )

    fig.update_layout(
        yaxis_range=[0, 100],
        xaxis_title="",
        yaxis_title="Porcentaje (%)",
        plot_bgcolor='rgba(0,0,0,0)',
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("Error al cargar los datos.")
    st.write("Verifica que las columnas en el Sheets se llamen exactamente:")
    st.code("OFICINA TECNICA, UNIDAD OPERATIVA, CATEGORIA, PORCENTAJE DE ABASTECIMIENTO")
    st.exception(e)
