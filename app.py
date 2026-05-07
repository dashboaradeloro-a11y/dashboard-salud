import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN
st.set_page_config(page_title="MSP El Oro - Filtros Dinámicos", layout="wide")

@st.cache_data(ttl=300)
def cargar_y_unificar():
    sheet_id = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    pestañas = [
        "HOSPITAL", "07OT01 - PASAJE", "07OT02 - MACHALA", 
        "07OT03 - ATAHUALPA-PORTOVELO-ZARUMA", "07OT04 - BALSAS-MARCABELI-PI0S - SALUD",
        "07OT05 - ARENILLAS-HUAQUILLAS-LAS LAJAS - SALUD", "07OT06 - SANTA ROSA - SALUD"
    ]
    
    lista_final = []
    for p in pestañas:
        p_enc = p.replace(" ", "%20")
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p_enc}"
        try:
            temp_df = pd.read_csv(url)
            if not temp_df.empty:
                # Normalizar nombres de columnas (Sin espacios, todo mayúsculas)
                temp_df.columns = [str(c).strip().upper() for c in temp_df.columns]
                temp_df['OFICINA_TECNICA'] = p
                lista_final.append(temp_df)
        except:
            continue
    return pd.concat(lista_final, ignore_index=True) if lista_final else pd.DataFrame()

# --- LÓGICA DE FILTROS ---
try:
    df = cargar_y_unificar()

    if df.empty:
        st.error("No se detectaron datos. Revisa los permisos del Sheets.")
    else:
        st.sidebar.header("🎯 Panel de Control")

        # --- FILTRO 1: OFICINA TÉCNICA ---
        lista_ot = sorted(df['OFICINA_TECNICA'].unique())
        ot_sel = st.sidebar.selectbox("1. Seleccione Oficina Técnica", ["TODAS"] + lista_ot)
        
        df_f1 = df.copy()
        if ot_sel != "TODAS":
            df_f1 = df_f1[df_f1['OFICINA_TECNICA'] == ot_sel]

        # --- FILTRO 2: UNIDAD OPERATIVA (Depende de OT) ---
        # Buscamos la columna de unidad (puede llamarse UNIDAD o UNIDAD OPERATIVA)
        col_u = next((c for c in df_f1.columns if "UNIDAD" in c), None)
        if col_u:
            lista_unidades = sorted(df_f1[col_u].dropna().unique())
            unidad_sel = st.sidebar.selectbox("2. Seleccione Unidad Operativa", ["TODAS"] + lista_unidades)
            
            df_f2 = df_f1.copy()
            if unidad_sel != "TODAS":
                df_f2 = df_f2[df_f2[col_u] == unidad_sel]
        else:
            df_f2 = df_f1.copy()
            st.sidebar.warning("Columna 'UNIDAD' no encontrada.")

        # --- FILTRO 3: CATEGORÍA (Depende de los anteriores) ---
        col_c = next((c for c in df_f2.columns if "CATEGORIA" in c or "TIPO" in c), None)
        if col_c:
            lista_cat = sorted(df_f2[col_c].dropna().unique())
            cat_sel = st.sidebar.multiselect("3. Filtrar por Categoría", lista_cat, default=lista_cat)
            
            df_final = df_f2[df_f2[col_c].isin(cat_sel)]
        else:
            df_final = df_f2.copy()
            st.sidebar.info("Columna 'CATEGORIA' no encontrada.")

        # --- VISUALIZACIÓN ---
        st.title("📊 Reporte de Abastecimiento Consolidado")
        
        # Métricas rápidas
        m1, m2, m3 = st.columns(3)
        m1.metric("Registros Filtrados", len(df_final))
        
        col_stock = next((c for c in df_final.columns if "STOCK" in c or "CANTIDAD" in c), None)
        if col_stock:
            df_final[col_stock] = pd.to_numeric(df_final[col_stock], errors='coerce').fillna(0)
            m2.metric("Total Unidades Físicas", f"{int(df_final[col_stock].sum()):,}")
        
        m3.metric("Unidades Mostradas", df_final[col_u].nunique() if col_u else 0)

        # Gráfico Dinámico
        if col_c and col_stock:
            fig = px.bar(df_final.groupby(col_c)[col_stock].sum().reset_index(), 
                         x=col_c, y=col_stock, color=col_c, title="Stock por Categoría")
            st.plotly_chart(fig, use_container_width=True)

        # Tabla de resultados
        st.subheader("📋 Detalle de la Selección")
        st.dataframe(df_final, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en el procesamiento: {e}")
