import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Control de Medicamentos MSP", layout="wide")

@st.cache_data(ttl=300)
def cargar_datos():
    sheet_id = "1Tt5BPmaOIPCwg8IAiJ1_RCc11D9ruZwvpiLSHWvAspU"
    pestañas = [
        "HOSPITAL", "07OT06 - SANTA ROSA - SALUD", 
        "07OT05 - ARENILLAS-HUAQUILLAS-LAS LAJAS - SALUD", 
        "07OT01 - PASAJE", "07OT02 - MACHALA", 
        "07OT03 - ATAHUALPA-PORTOVELO-ZARUMA", 
        "07OT04 - BALSAS-MARCABELI-PI0S - SALUD"
    ]
    lista_df = []
    for p in pestañas:
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={p.replace(' ', '%20')}"
        try:
            df_temp = pd.read_csv(url)
            if not df_temp.empty:
                # Normalización agresiva de columnas: Mayúsculas, sin tildes y sin espacios
                df_temp.columns = [str(c).strip().upper()
                                   .replace('Á', 'A').replace('É', 'E')
                                   .replace('Í', 'I').replace('Ó', 'O')
                                   .replace('Ú', 'U') for c in df_temp.columns]
                df_temp['OFICINA TECNICA'] = p
                lista_df.append(df_temp)
        except:
            continue
    return pd.concat(lista_df, ignore_index=True) if lista_df else pd.DataFrame()

try:
    df = cargar_datos()

    if not df.empty:
        st.title("🏥 Control Provincial de Medicamentos e Insumos")
        
        # --- BUSCADOR ---
        st.markdown("### 🔍 Buscador Rápido")
        query = st.text_input("Buscar por nombre o concentración...", placeholder="Ej: Levonorgestrel")

        # --- FILTROS LATERALES ---
        st.sidebar.header("📍 Filtros Principales")
        
        # 1. Filtro OT
        ot_sel = st.sidebar.selectbox("Oficina Técnica", ["TODAS"] + sorted(df['OFICINA TECNICA'].unique()))
        df_f = df.copy()
        if ot_sel != "TODAS":
            df_f = df_f[df_f['OFICINA TECNICA'] == ot_sel]

        # 2. Filtro Categoría (Verificamos si existe la columna)
        col_cat = next((c for c in df_f.columns if "CATEGORIA" in c), None)
        if col_cat:
            cat_list = sorted(df_f[col_cat].dropna().unique())
            cat_sel = st.sidebar.multiselect("Categoría", cat_list, default=cat_list)
            df_f = df_f[df_f[col_cat].isin(cat_sel)]

        # 3. Filtro Unidad Operativa
        col_uni = next((c for c in df_f.columns if "UNIDAD" in c), None)
        if col_uni:
            uni_list = sorted(df_f[col_uni].dropna().unique())
            uni_sel = st.sidebar.selectbox("Unidad Operativa", ["TODAS"] + uni_list)
            if uni_sel != "TODAS":
                df_f = df_f[df_f[col_uni] == uni_sel]

        # --- APLICAR BUSQUEDA ---
        if query:
            # Buscamos en todas las columnas de texto para evitar el error de 'KeyError'
            mask = df_f.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)
            df_f = df_f[mask]

        # --- KPIs ---
        k1, k2, k3 = st.columns(3)
        k1.metric("Resultados", len(df_f))
        col_stock = next((c for c in df_f.columns if "STOCK" in c), None)
        if col_stock:
            df_f[col_stock] = pd.to_numeric(df_f[col_stock], errors='coerce').fillna(0)
            k2.metric("Stock Total", f"{int(df_f[col_stock].sum()):,}")
        k3.metric("Unidades", df_f[col_uni].nunique() if col_uni else 0)

        # --- TABLA FINAL ---
        st.subheader("📋 Detalle de Inventario")
        st.dataframe(df_f, use_container_width=True, hide_index=True)

    else:
        st.error("No se pudieron cargar los datos. Revisa la conexión al Sheets.")

except Exception as e:
    st.error(f"Error detectado: {e}")
    st.info("Sugerencia: Verifica que los encabezados del Excel estén en la primera fila.")
