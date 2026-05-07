import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN INICIAL
st.set_page_config(page_title="Dashboard MSP El Oro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIÓN ROBUSTA DE CARGA
@st.cache_data(ttl=60)
def cargar_datos_seguro():
    # ID real de tu documento
    sheet_id = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    
    pestañas = [
        "HOSPITAL", "07OT01 - PASAJE", "07OT02 - MACHALA", 
        "07OT03 - ATAHUALPA-PORTOVELO-ZARUMA", "07OT04 - BALSAS-MARCABELI-PI0S - SALUD",
        "07OT05 - ARENILLAS-HUAQUILLAS-LAS LAJAS - SALUD", "07OT06 - SANTA ROSA - SALUD"
    ]
    
    lista_consolidada = []
    
    for p in pestañas:
        # Codificamos el nombre de la pestaña para la URL
        p_encoded = p.replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p_encoded}"
        
        try:
            # Leemos intentando forzar que todo sea texto al inicio para evitar errores de tipos
            df_temp = pd.read_csv(url)
            
            if not df_temp.empty:
                # Limpiamos nombres de columnas: Mayúsculas y sin espacios
                df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
                # Guardamos de qué pestaña viene
                df_temp['OFICINA_ORIGEN'] = p
                lista_consolidada.append(df_temp)
        except Exception as e:
            continue # Si una pestaña falla, pasamos a la siguiente

    if not lista_consolidada:
        return pd.DataFrame()
    
    return pd.concat(lista_consolidada, ignore_index=True)

# 3. LÓGICA DEL DASHBOARD
try:
    df = cargar_datos_seguro()

    if df.empty:
        st.error("❌ No se pudieron extraer datos.")
        st.info("Revisa que el Google Sheets esté compartido como: 'Cualquier persona con el enlace puede leer'.")
    else:
        st.title("🏥 Monitoreo de Abastecimiento - El Oro")
        
        # --- FILTROS ---
        st.sidebar.header("Filtros")
        ot_sel = st.sidebar.selectbox("Seleccione Oficina Técnica:", ["TODAS"] + list(df['OFICINA_ORIGEN'].unique()))
        
        df_f = df.copy()
        if ot_sel != "TODAS":
            df_f = df_f[df_f['OFICINA_ORIGEN'] == ot_sel]

        # Intentar detectar columnas clave automáticamente
        # Buscamos columnas que contengan palabras clave
        col_unidad = next((c for c in df_f.columns if "UNIDAD" in c), "UNIDAD")
        col_item = next((c for c in df_f.columns if "ITEM" in c or "PRODUCTO" in c or "MEDICAMENTO" in c), "ITEM")
        col_stock = next((c for c in df_f.columns if "STOCK" in c or "CANTIDAD" in c or "EXISTENCIA" in c), None)

        # Convertir stock a número (por si viene como texto)
        if col_stock and col_stock in df_f.columns:
            df_f[col_stock] = pd.to_numeric(df_f[col_stock], errors='coerce').fillna(0)

        # --- MÉTRICAS ---
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total Ítems", len(df_f))
        with c2:
            val_stock = df_f[col_stock].sum() if col_stock else 0
            st.metric("Existencias Totales", f"{int(val_stock):,}")
        with c3:
            unidades = df_f[col_unidad].nunique() if col_unidad in df_f.columns else 0
            st.metric("Unidades Operativas", unidades)

        st.markdown("---")

        # --- TABLA Y GRÁFICO ---
        col_tabla, col_graf = st.columns([2, 1])

        with col_tabla:
            st.subheader("📋 Detalle de Inventario")
            # Mostramos la tabla completa
            st.dataframe(df_f, use_container_width=True, hide_index=True)

        with col_graf:
            st.subheader("📊 Resumen por Oficina")
            resumen = df.groupby('OFICINA_ORIGEN').size().reset_index(name='CANTIDAD')
            fig = px.pie(resumen, values='CANTIDAD', names='OFICINA_ORIGEN', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Ocurrió un error inesperado: {e}")
