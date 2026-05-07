import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Control de Inventario MSP", layout="wide")

@st.cache_data(ttl=300)
def cargar_datos_estrictos():
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
                # Normalización de nombres de columnas para que coincidan con tu pedido
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
    df = cargar_datos_estrictos()

    if not df.empty:
        st.title("🏥 Reporte Detallado de Stock - El Oro")
        
        # --- BUSCADOR ---
        query = st.text_input("🔍 Buscar Medicamento o Insumo...", placeholder="Escriba aquí para filtrar la tabla...")

        # --- FILTROS LATERALES ---
        st.sidebar.header("Filtros de Control")
        
        # 1. Oficina Técnica
        ot_sel = st.sidebar.selectbox("Oficina Técnica", ["TODAS"] + sorted(df['OFICINA TECNICA'].unique()))
        df_f = df.copy()
        if ot_sel != "TODAS":
            df_f = df_f[df_f['OFICINA TECNICA'] == ot_sel]

        # 2. Unidad Operativa
        col_uni = next((c for c in df_f.columns if "UNIDAD" in c), "UNIDAD OPERATIVA")
        uni_list = sorted(df_f[col_uni].dropna().unique()) if col_uni in df_f.columns else []
        unidad_sel = st.sidebar.selectbox("Unidad Operativa", ["TODAS"] + uni_list)
        if unidad_sel != "TODAS":
            df_f = df_f[df_f[col_uni] == unidad_sel]

        # 3. Categoría (FILTRO SOLICITADO)
        col_cat = next((c for c in df_f.columns if "CATEGORIA" in c), "CATEGORIA")
        if col_cat in df_f.columns:
            cat_list = sorted(df_f[col_cat].dropna().unique())
            cat_sel = st.sidebar.multiselect("Categoría", cat_list, default=cat_list)
            df_f = df_f[df_f[col_cat].isin(cat_sel)]

        # --- APLICAR BUSQUEDA ---
        if query:
            mask = df_f.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)
            df_f = df_f[mask]

        # --- SELECCIÓN ESTRICTA DE COLUMNAS ---
        # Definimos exactamente lo que pediste
        columnas_finales = [
            'OFICINA TECNICA',
            col_uni,                    # Unidad Operativa
            col_cat,                    # Categoria
            'MEDICAMENTO O INSUMO',
            'FORMA FARMACEUTICA',       # Sin tilde por la normalización
            'CONCENTRACION',
            'STOCK'
        ]

        # Verificamos cuáles de estas existen en el DF actual para no dar error
        cols_a_mostrar = [c for c in columnas_finales if c in df_f.columns]

        # --- PRESENTACIÓN ---
        st.markdown("---")
        # KPIs rápidos
        k1, k2 = st.columns(2)
        k1.metric("Items en pantalla", len(df_f))
        if 'STOCK' in df_f.columns:
            df_f['STOCK'] = pd.to_numeric(df_f['STOCK'], errors='coerce').fillna(0)
            k2.metric("Stock Total Seleccionado", f"{int(df_f['STOCK'].sum()):,}")

        # LA TABLA QUE SALGA SOLO LO PEDIDO
        st.subheader("📋 Matriz de Disponibilidad")
        st.dataframe(df_f[cols_a_mostrar], use_container_width=True, hide_index=True)

    else:
        st.error("No se encontraron datos. Verifique el enlace de Google Sheets.")

except Exception as e:
    st.error(f"Error: {e}")
