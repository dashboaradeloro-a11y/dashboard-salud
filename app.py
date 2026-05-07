import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Dashboard MSP El Oro - Abastecimiento", layout="wide")

# Estilos CSS para mejorar la apariencia
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; color: #003087; }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600) # El cache se actualiza cada 10 min
def cargar_datos_completos():
    sheet_id = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    
    # Lista exacta de tus pestañas
    pestañas = [
        "HOSPITAL", 
        "07OT06 - SANTA ROSA - SALUD", 
        "07OT05 - ARENILLAS-HUAQUILLAS-LAS LAJAS - SALUD", 
        "07OT01 - PASAJE", 
        "07OT02 - MACHALA", 
        "07OT03 - ATAHUALPA-PORTOVELO-ZARUMA", 
        "07OT04 - BALSAS-MARCABELI-PI0S - SALUD"
    ]
    
    lista_df = []
    
    for p in pestañas:
        # Reemplazar espacios para la URL
        p_url = p.replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p_url}"
        
        try:
            df_temp = pd.read_csv(url)
            # Limpieza de nombres de columnas
            df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
            
            # Solo agregar si la pestaña tiene datos
            if not df_temp.empty:
                df_temp['ORIGEN_OT'] = p
                lista_df.append(df_temp)
        except Exception as e:
            st.error(f"Error cargando pestaña {p}: {e}")
            
    return pd.concat(lista_df, ignore_index=True) if lista_df else pd.DataFrame()

# --- CARGA DE DATOS ---
try:
    df_raw = cargar_datos_completos()
    
    if not df_raw.empty:
        # TÍTULO Y LOGO
        col_t1, col_t2 = st.columns([1, 4])
        with col_t1:
            st.image("https://www.salud.gob.ec/wp-content/uploads/2021/05/logo-msp.png", width=150)
        with col_t2:
            st.title("Monitoreo Provincial de Abastecimiento - El Oro")
            st.markdown(f"Consolidado de **{len(df_raw)}** registros de insumos y medicamentos.")

        # --- FILTROS IZQUIERDA ---
        st.sidebar.header("Control de Filtros")
        
        # Filtro de OT
        ot_opciones = ["TODAS"] + list(df_raw['ORIGEN_OT'].unique())
        ot_sel = st.sidebar.selectbox("Seleccione Oficina Técnica:", ot_opciones)
        
        df_filtrado = df_raw.copy()
        if ot_sel != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['ORIGEN_OT'] == ot_sel]
        
        # Filtro de Unidad (dinámico según la OT)
        unidad_opciones = ["TODAS"] + list(df_filtrado['UNIDAD'].unique())
        unidad_sel = st.sidebar.selectbox("Seleccione Unidad Operativa:", unidad_opciones)
        
        if unidad_sel != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['UNIDAD'] == unidad_sel]

        # --- KPIs ---
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Ítems", len(df_filtrado))
        with m2:
            # Si tienes columna STOCK o % (Ajustar según nombre real en tu Excel)
            col_valor = 'STOCK' if 'STOCK' in df_filtrado.columns else df_filtrado.columns[2]
            promedio = df_filtrado[col_valor].mean() if pd.api.types.is_numeric_dtype(df_filtrado[col_valor]) else 0
            st.metric("Promedio Existencias", f"{promedio:.1f}")
        with m3:
            unidades_count = df_filtrado['UNIDAD'].nunique()
            st.metric("Unidades en Pantalla", unidades_count)
        with m4:
            st.metric("Estado", "🟢 Operativo" if promedio > 50 else "🟡 Alerta")

        st.markdown("---")

        # --- GRÁFICOS ---
        g1, g2 = st.columns([1, 1])

        with g1:
            st.subheader("Distribución por Categoría")
            if 'CATEGORIA' in df_filtrado.columns:
                fig_pie = px.sunburst(df_filtrado, path=['ORIGEN_OT', 'CATEGORIA'], values=None,
                                      color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Columna 'CATEGORIA' no encontrada para el gráfico.")

        with g2:
            st.subheader("Stock Crítico por Unidad")
            # Mostrar los 15 items con menos stock
            if col_valor in df_filtrado.columns and 'ITEM' in df_filtrado.columns:
                df_critico = df_filtrado.nsmallest(15, col_valor)
                fig_bar = px.bar(df_critico, x=col_valor, y='ITEM', orientation='h',
                                 color=col_valor, color_continuous_scale='Reds_r')
                st.plotly_chart(fig_bar, use_container_width=True)

        # --- TABLA DETALLADA ---
        st.subheader("📋 Matriz Detallada")
        st.dataframe(df_filtrado, use_container_width=True)

    else:
        st.error("No se encontraron datos. Revisa que las pestañas tengan información.")

except Exception as e:
    st.error(f"Error crítico en el Dashboard: {e}")
