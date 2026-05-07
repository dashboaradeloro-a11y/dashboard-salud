import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Dashboard MSP El Oro - Abastecimiento", layout="wide")

# Estilos personalizados para un look profesional (MSP Style)
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stMetricValue"] { font-size: 35px; color: #1e3a8a; }
    .stSelectbox label { font-weight: bold; color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300) # Actualiza los datos cada 5 minutos
def cargar_datos_provinciales():
    # ID del documento extraído de tu link
    sheet_id = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    
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
        # Codificar espacios para la URL
        p_url = p.replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p_url}"
        
        try:
            df_temp = pd.read_csv(url)
            # Limpieza estándar: Columnas a Mayúsculas y sin espacios laterales
            df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
            
            if not df_temp.empty:
                df_temp['OT_ORIGEN'] = p # Etiqueta para saber de qué pestaña viene
                lista_df.append(df_temp)
        except Exception as e:
            # Si una pestaña falla, avisamos pero continuamos con las demás
            st.sidebar.warning(f"No se pudo leer la pestaña: {p}")
            
    return pd.concat(lista_df, ignore_index=True) if lista_df else pd.DataFrame()

# --- INICIO DE PROCESAMIENTO ---
try:
    df_base = cargar_datos_provinciales()

    if not df_base.empty:
        # HEADER
        col_logo, col_tit = st.columns([1, 5])
        with col_logo:
            st.image("https://logodownload.org/wp-content/uploads/2018/10/ministerio-da-saude-logo.png", width=120) # Logo genérico salud
        with col_tit:
            st.title("Sistema Provincial de Abastecimiento - El Oro")
            st.caption("Consolidación en tiempo real de Oficinas Técnicas y Hospitales")

        # --- FILTROS LATERALES ---
        st.sidebar.header("📍 Navegación Local")
        
        # Filtro 1: Oficina Técnica (Pestaña)
        ot_lista = ["TODAS"] + list(df_base['OT_ORIGEN'].unique())
        ot_sel = st.sidebar.selectbox("Seleccione Oficina Técnica:", ot_lista)
        
        df_filtrado = df_base.copy()
        if ot_sel != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['OT_ORIGEN'] == ot_sel]
        
        # Filtro 2: Unidad Operativa (Dinámico)
        unidades_disponibles = ["TODAS"] + list(df_filtrado['UNIDAD'].unique() if 'UNIDAD' in df_filtrado.columns else [])
        unidad_sel = st.sidebar.selectbox("Seleccione Unidad Específica:", unidades_disponibles)
        
        if unidad_sel != "TODAS":
            df_filtrado = df_filtrado[df_filtrado['UNIDAD'] == unidad_sel]

        # --- KPIs ---
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total de Ítems", len(df_filtrado))
        with k2:
            # Buscamos la columna de stock (intentamos varios nombres comunes)
            col_stock = next((c for c in ['STOCK', 'CANTIDAD', 'EXISTENCIA'] if c in df_filtrado.columns), None)
            total_stock = df_filtrado[col_stock].sum() if col_stock else 0
            st.metric("Stock Físico Total", f"{int(total_stock):,}")
        with k3:
            unidades_n = df_filtrado['UNIDAD'].nunique() if 'UNIDAD' in df_filtrado.columns else 0
            st.metric("Unidades Operativas", unidades_n)
        with k4:
            st.metric("OT Seleccionada", "Provincial" if ot_sel == "TODAS" else ot_sel.split("-")[0])

        st.markdown("---")

        # --- GRÁFICOS INTERACTIVOS ---
        c_left, c_right = st.columns([1, 1])

        with c_left:
            st.subheader("📦 Distribución por Categoría")
            if 'CATEGORIA' in df_filtrado.columns:
                fig_pie = px.pie(df_filtrado, names='CATEGORIA', hole=0.5, 
                                 color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Agregue la columna 'CATEGORIA' para ver este gráfico.")

        with c_right:
            st.subheader("🚨 Top 10 Ítems (Mayor Stock)")
            if col_stock and 'ITEM' in df_filtrado.columns:
                # Top 10 por cantidad
                df_top = df_filtrado.nlargest(10, col_stock)
                fig_bar = px.bar(df_top, x=col_stock, y='ITEM', orientation='h',
                                 color=col_stock, color_continuous_scale='Blues')
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)

        # --- TABLA DE DATOS FINAL ---
        st.subheader("📋 Detalle de Inventario")
        st.dataframe(df_filtrado, use_container_width=True)
        
        # BOTÓN DE DESCARGA
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte en CSV", data=csv, file_name="reporte_abastecimiento.csv", mime="text/csv")

    else:
        st.warning("⚠️ No se detectaron datos en las pestañas. Revisa que el archivo de Sheets tenga información y las columnas correctas.")

except Exception as e:
    st.error(f"Error de conexión: {e}")
    st.info("Asegúrate de que el Sheets esté compartido con 'Cualquier persona con el enlace'.")
