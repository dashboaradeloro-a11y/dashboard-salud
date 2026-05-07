import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Control de Inventario MSP - El Oro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1d4ed8; }
    .stSelectbox label, .stMultiSelect label { font-weight: bold; color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_inventario():
    sheet_id = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    pestañas = [
        "HOSPITAL", "07OT06 - SANTA ROSA - SALUD", 
        "07OT05 - ARENILLAS-HUAQUILLAS-LAS LAJAS - SALUD", 
        "07OT01 - PASAJE", "07OT02 - MACHALA", 
        "07OT03 - ATAHUALPA-PORTOVELO-ZARUMA", 
        "07OT04 - BALSAS-MARCABELI-PI0S - SALUD"
    ]
    
    dataframes = []
    for p in pestañas:
        p_url = p.replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p_url}"
        try:
            df_temp = pd.read_csv(url)
            if not df_temp.empty:
                # Estandarizar nombres de columnas eliminando espacios y pasando a mayúsculas
                df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
                # Inyectar el nombre de la Oficina Técnica
                df_temp['OFICINA TECNICA'] = p
                dataframes.append(df_temp)
        except Exception as e:
            continue
            
    return pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

# --- PROCESAMIENTO DE DATOS ---
try:
    df_base = cargar_inventario()

    if df_base.empty:
        st.error("⚠️ No se encontraron datos. Verifique los permisos del Sheets.")
    else:
        # TÍTULO
        st.title("🏥 Gestión de Medicamentos e Insumos - El Oro")
        st.info("Consolidado Provincial basado en Matriz de Stock")

        # --- SECCIÓN DE FILTROS (SIDEBAR) ---
        st.sidebar.header("🔍 Filtros de Búsqueda")

        # 1. Filtro Oficina Técnica
        ots = sorted(df_base['OFICINA TECNICA'].unique())
        ot_sel = st.sidebar.selectbox("Oficina Técnica", ["TODAS"] + ots)
        
        df_f1 = df_base.copy()
        if ot_sel != "TODAS":
            df_f1 = df_f1[df_f1['OFICINA TECNICA'] == ot_sel]

        # 2. Filtro Unidad Operativa (En cascada)
        col_unidad = "UNIDAD OPERATIVA" if "UNIDAD OPERATIVA" in df_f1.columns else "UNIDAD"
        if col_unidad in df_f1.columns:
            unidades = sorted(df_f1[col_unidad].dropna().unique())
            unidad_sel = st.sidebar.selectbox("Unidad Operativa", ["TODAS"] + unidades)
            if unidad_sel != "TODAS":
                df_f1 = df_f1[df_f1[col_unidad] == unidad_sel]

        # 3. Filtro Categoría
        if "CATEGORIA" in df_f1.columns:
            categorias = sorted(df_f1['CATEGORIA'].dropna().unique())
            cat_sel = st.sidebar.multiselect("Categoría", categorias, default=categorias)
            df_f1 = df_f1[df_f1['CATEGORIA'].isin(cat_sel)]

        # --- LIMPIEZA DE COLUMNA STOCK ---
        # Buscamos la columna stock y la convertimos a número
        if "STOCK" in df_f1.columns:
            df_f1['STOCK'] = pd.to_numeric(df_f1['STOCK'], errors='coerce').fillna(0)

        # --- KPIs ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Items Registrados", len(df_f1))
        m2.metric("Total Stock Físico", f"{int(df_f1['STOCK'].sum() if 'STOCK' in df_f1.columns else 0):,}")
        m3.metric("Unidades Operativas", df_f1[col_unidad].nunique() if col_unidad in df_f1.columns else 0)
        m4.metric("Categorías", df_f1['CATEGORIA'].nunique() if 'CATEGORIA' in df_f1.columns else 0)

        st.markdown("---")

        # --- TABLA PRINCIPAL ---
        st.subheader("📋 Detalle de Inventario")
        
        # Seleccionamos las columnas que pediste para mostrar en orden
        columnas_visibles = [
            'OFICINA TECNICA', col_unidad, 'CATEGORIA', 
            'MEDICAMENTO O INSUMO', 'FORMA FARMACÉUTICA', 
            'CONCENTRACION', 'STOCK'
        ]
        
        # Filtrar solo las columnas que existan realmente en el DF para evitar errores
        cols_finales = [c for c in columnas_visibles if c in df_f1.columns]
        
        st.dataframe(df_f1[cols_finales], use_container_width=True, hide_index=True)

        # --- GRÁFICO DE ANÁLISIS ---
        st.markdown("---")
        st.subheader("📊 Análisis de Stock por Categoría")
        if "CATEGORIA" in df_f1.columns and "STOCK" in df_f1.columns:
            fig = px.bar(df_f1.groupby('CATEGORIA')['STOCK'].sum().reset_index(), 
                         x='CATEGORIA', y='STOCK', color='CATEGORIA',
                         text_auto='.2s', template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
    st.info("Asegúrese de que los nombres de las columnas en el Excel coincidan exactamente con lo solicitado.")
