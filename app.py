import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Buscador de Medicamentos - MSP El Oro", layout="wide")

# Estilos personalizados
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: 700; color: #1d4ed8; }
    .stTextInput>div>div>input { background-color: #ffffff; border: 2px solid #1d4ed8; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_inventario_completo():
    sheet_id = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    pestañas = [
        "HOSPITAL", "07OT06 - SANTA ROSA - SALUD", 
        "07OT05 - ARENILLAS-HUAQUILLAS-LAS LAJAS - SALUD", 
        "07OT01 - PASAJE", "07OT02 - MACHALA", 
        "07OT03 - ATAHUALPA-PORTOVELO-ZARUMA", 
        "07OT04 - BALSAS-MARCABELI-PI0S - SALUD"
    ]
    
    dfs = []
    for p in pestañas:
        p_url = p.replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p_url}"
        try:
            temp = pd.read_csv(url)
            if not temp.empty:
                # Limpiar nombres de columnas
                temp.columns = [str(c).strip().upper() for c in temp.columns]
                temp['OFICINA TECNICA'] = p
                dfs.append(temp)
        except:
            continue
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# --- CARGA Y FILTRADO ---
try:
    df_base = cargar_inventario_completo()

    if not df_base.empty:
        st.title("🏥 Control Provincial de Medicamentos e Insumos")
        
        # --- BUSCADOR PRINCIPAL ---
        st.markdown("### 🔍 Buscador Rápido")
        query = st.text_input("Escriba el nombre del medicamento, insumo o concentración (Ej: Paracetamol, Gasa, 500mg)...")

        # --- SIDEBAR (FILTROS DE ESTRUCTURA) ---
        st.sidebar.header("📍 Filtros de Ubicación")
        ot_sel = st.sidebar.selectbox("Oficina Técnica", ["TODAS"] + sorted(df_base['OFICINA TECNICA'].unique()))
        
        df_f = df_base.copy()
        
        # Aplicar Filtro de OT
        if ot_sel != "TODAS":
            df_f = df_f[df_f['OFICINA TECNICA'] == ot_sel]

        # Aplicar Filtro de Unidad Operativa
        col_unidad = "UNIDAD OPERATIVA" if "UNIDAD OPERATIVA" in df_f.columns else "UNIDAD"
        if col_unidad in df_f.columns:
            unidades = sorted(df_f[col_unidad].dropna().unique())
            unidad_sel = st.sidebar.selectbox("Unidad Operativa", ["TODAS"] + unidades)
            if unidad_sel != "TODAS":
                df_f = df_f[df_f[col_unidad] == unidad_sel]

        # --- APLICAR BUSCADOR ---
        if query:
            # Buscamos en las columnas de texto (Medicamento, Concentración, Forma Farmacéutica)
            # El buscador ignora mayúsculas/minúsculas
            df_f = df_f[
                df_f['MEDICAMENTO O INSUMO'].astype(str).str.contains(query, case=False, na=False) |
                df_f['FORMA FARMACÉUTICA'].astype(str).str.contains(query, case=False, na=False) |
                df_f['CONCENTRACION'].astype(str).str.contains(query, case=False, na=False)
            ]

        # --- KPIs ---
        st.markdown("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("Resultados encontrados", len(df_f))
        
        if 'STOCK' in df_f.columns:
            df_f['STOCK'] = pd.to_numeric(df_f['STOCK'], errors='coerce').fillna(0)
            m2.metric("Stock Total en Selección", f"{int(df_f['STOCK'].sum()):,}")
        
        m3.metric("OTs Involucradas", df_f['OFICINA TECNICA'].nunique())

        # --- TABLA DE RESULTADOS ---
        st.subheader("📋 Lista de Existencias")
        
        cols_finales = [
            'OFICINA TECNICA', col_unidad, 'CATEGORIA', 
            'MEDICAMENTO O INSUMO', 'FORMA FARMACÉUTICA', 
            'CONCENTRACION', 'STOCK'
        ]
        
        # Mostrar solo las columnas que existan en el Sheets
        cols_a_mostrar = [c for c in cols_finales if c in df_f.columns]
        
        st.dataframe(df_f[cols_a_mostrar], use_container_width=True, hide_index=True)

        # --- GRÁFICO ---
        if not df_f.empty and 'STOCK' in df_f.columns:
            st.markdown("---")
            st.subheader("📊 Distribución de Stock")
            fig = px.bar(df_f.groupby('CATEGORIA')['STOCK'].sum().reset_index(), 
                         x='CATEGORIA', y='STOCK', color='CATEGORIA', template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No se encontraron datos en el enlace de Google Sheets.")

except Exception as e:
    st.error(f"Error al procesar los datos: {e}")
