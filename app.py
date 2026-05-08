import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Dashboard MSP El Oro - Abastecimiento", layout="wide")

# Estilos CSS para mejorar la interfaz
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; color: #1d4ed8; }
    .stDataFrame { border-radius: 10px; }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIÓN DE CARGA Y NORMALIZACIÓN
@st.cache_data(ttl=300)
def cargar_datos_completos():
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
                # Normalización agresiva: Quitar tildes, espacios y a Mayúsculas
                df_temp.columns = [str(c).strip().upper()
                                   .replace('Á', 'A').replace('É', 'E')
                                   .replace('Í', 'I').replace('Ó', 'O')
                                   .replace('Ú', 'U') for c in df_temp.columns]
                df_temp['OFICINA TECNICA'] = p
                lista_df.append(df_temp)
        except:
            continue
    
    if not lista_df:
        return pd.DataFrame()
    
    df_consolidado = pd.concat(lista_df, ignore_index=True)
    
    # Asegurar que STOCK sea numérico para cálculos
    if 'STOCK' in df_consolidado.columns:
        df_consolidado['STOCK'] = pd.to_numeric(df_consolidado['STOCK'], errors='coerce').fillna(0)
    
    return df_consolidado

# 3. LÓGICA DEL DASHBOARD
try:
    df = cargar_datos_completos()

    if df.empty:
        st.error("❌ No se pudieron cargar datos. Verifica el acceso público al link de Google Sheets.")
    else:
        st.title("🏥 Control Provincial de Inventarios - El Oro")
        
        # --- BUSCADOR GLOBAL ---
        st.markdown("### 🔍 Buscador de Medicamentos e Insumos")
        query = st.text_input("", placeholder="Escriba el nombre, concentración o ítem a buscar...")

        # --- PANEL LATERAL (FILTROS) ---
        st.sidebar.header("📍 Filtros de Selección")
        
        # Filtro Oficina Técnica
        lista_ot = sorted(df['OFICINA TECNICA'].unique())
        ot_sel = st.sidebar.selectbox("Oficina Técnica", ["TODAS"] + lista_ot)
        df_f = df.copy()
        if ot_sel != "TODAS":
            df_f = df_f[df_f['OFICINA TECNICA'] == ot_sel]

        # Filtro Unidad Operativa (Detección automática de nombre de columna)
        col_uni = next((c for c in df_f.columns if "UNIDAD" in c), "UNIDAD OPERATIVA")
        if col_uni in df_f.columns:
            lista_uni = sorted(df_f[col_uni].dropna().unique())
            uni_sel = st.sidebar.selectbox("Unidad Operativa", ["TODAS"] + lista_uni)
            if uni_sel != "TODAS":
                df_f = df_f[df_f[col_uni] == uni_sel]

        # Filtro Categoría
        col_cat = next((c for c in df_f.columns if "CATEGORIA" in c), "CATEGORIA")
        if col_cat in df_f.columns:
            lista_cat = sorted(df_f[col_cat].dropna().unique())
            cat_sel = st.sidebar.multiselect("Filtrar por Categoría", lista_cat, default=lista_cat)
            df_f = df_f[df_f[col_cat].isin(cat_sel)]

        # APLICAR BÚSQUEDA
        if query:
            # Búsqueda en todas las columnas para evitar errores de KeyError
            mask = df_f.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)
            df_f = df_f[mask]

        # --- CÁLCULO DE KPIs EN % ---
        total_items = len(df_f)
        items_con_stock = len(df_f[df_f['STOCK'] > 0])
        pct_abastecimiento = (items_con_stock / total_items * 100) if total_items > 0 else 0
        
        # Porcentaje de stock crítico (items con menos de 100 unidades)
        items_criticos = len(df_f[(df_f['STOCK'] > 0) & (df_f['STOCK'] < 100)])
        pct_critico = (items_criticos / total_items * 100) if total_items > 0 else 0

        # Mostrar KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Abastecimiento (%)", f"{pct_abastecimiento:.1f}%")
        c2.metric("Nivel Crítico (%)", f"{pct_critico:.1f}%", delta="Riesgo", delta_color="inverse")
        c3.metric("Total Ítems Mostrados", total_items)

        st.markdown("---")

        # --- SECCIÓN DE GRÁFICOS ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("📊 Distribución por Categoría (%)")
            if col_cat in df_f.columns and 'STOCK' in df_f.columns:
                df_cat = df_f.groupby(col_cat)['STOCK'].sum().reset_index()
                total_s = df_cat['STOCK'].sum()
                df_cat['PORCENTAJE'] = (df_cat['STOCK'] / total_s * 100) if total_s > 0 else 0
                
                fig_cat = px.bar(
                    df_cat, x='PORCENTAJE', y=col_cat, orientation='h',
                    text=df_cat['PORCENTAJE'].apply(lambda x: f'{x:.1f}%'),
                    color=col_cat, color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_cat.update_traces(textposition='inside', textfont_size=14)
                fig_cat.update_layout(showlegend=False, xaxis_title="Porcentaje (%)")
                st.plotly_chart(fig_cat, use_container_width=True)

        with col_g2:
            st.subheader("🔝 Top 10 Unidades con Mayor Stock")
            resumen_uni = df_f.groupby(col_uni)['STOCK'].sum().reset_index().nlargest(10, 'STOCK')
            fig_bar = px.bar(
                resumen_uni, x='STOCK', y=col_uni, orientation='h',
                text='STOCK', color='STOCK', color_continuous_scale='Blues'
            )
            fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- TABLA DE DATOS FINAL (SOLO LO PEDIDO) ---
        st.subheader("📋 Detalle de Inventario")
        # Columnas exactas solicitadas
        cols_finales = [
            'OFICINA TECNICA', col_uni, col_cat, 
            'MEDICAMENTO O INSUMO', 'FORMA FARMACEUTICA', 
            'CONCENTRACION', 'STOCK'
        ]
        
        # Filtramos para mostrar solo las que existan
        tab_mostrar = [c for c in cols_finales if c in df_f.columns]
        st.dataframe(df_f[tab_mostrar], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Se detectó un error: {e}")
