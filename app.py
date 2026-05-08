import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Dashboard MSP El Oro - Abastecimiento", layout="wide")

# Estilos CSS personalizados para un acabado profesional
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    [data-testid="stMetricValue"] { font-size: 32px; font-weight: bold; color: #1d4ed8; }
    .stDataFrame { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNCIÓN PARA CARGAR Y CONSOLIDAR DATOS
@st.cache_data(ttl=300) # Actualiza cada 5 minutos
def cargar_datos_provinciales():
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
                # Normalización de nombres de columnas (Quitar tildes, espacios y a Mayúsculas)
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
    
    df_unificado = pd.concat(lista_df, ignore_index=True)
    
    # Asegurar que STOCK sea numérico
    if 'STOCK' in df_unificado.columns:
        df_unificado['STOCK'] = pd.to_numeric(df_unificado['STOCK'], errors='coerce').fillna(0)
    
    return df_unificado

# 3. LÓGICA PRINCIPAL DEL DASHBOARD
try:
    df = cargar_datos_provinciales()

    if df.empty:
        st.error("❌ No se pudieron cargar los datos. Verifica el acceso al Sheets.")
    else:
        st.title("🏥 Sistema de Monitoreo de Insumos y Medicamentos - El Oro")
        
        # --- BUSCADOR GLOBAL ---
        st.markdown("### 🔍 Buscador de Medicamentos")
        query = st.text_input("", placeholder="Escriba el nombre, concentración o forma farmacéutica...")

        # --- BARRA LATERAL (FILTROS) ---
        st.sidebar.header("📍 Panel de Filtros")
        
        # Filtro 1: Oficina Técnica
        lista_ot = sorted(df['OFICINA TECNICA'].unique())
        ot_sel = st.sidebar.selectbox("Seleccione Oficina Técnica", ["TODAS"] + lista_ot)
        df_f = df.copy()
        if ot_sel != "TODAS":
            df_f = df_f[df_f['OFICINA TECNICA'] == ot_sel]

        # Filtro 2: Unidad Operativa (Cascada)
        col_uni = next((c for c in df_f.columns if "UNIDAD" in c), "UNIDAD OPERATIVA")
        if col_uni in df_f.columns:
            lista_uni = sorted(df_f[col_uni].dropna().unique())
            uni_sel = st.sidebar.selectbox("Seleccione Unidad Operativa", ["TODAS"] + lista_uni)
            if uni_sel != "TODAS":
                df_f = df_f[df_f[col_uni] == uni_sel]

        # Filtro 3: Categoría
        col_cat = next((c for c in df_f.columns if "CATEGORIA" in c), "CATEGORIA")
        if col_cat in df_f.columns:
            lista_cat = sorted(df_f[col_cat].dropna().unique())
            cat_sel = st.sidebar.multiselect("Filtrar por Categoría", lista_cat, default=lista_cat)
            df_f = df_f[df_f[col_cat].isin(cat_sel)]

        # APLICAR BUSCADOR
        if query:
            mask = df_f.astype(str).apply(lambda x: x.str.contains(query, case=False)).any(axis=1)
            df_f = df_f[mask]

        # --- CÁLCULO DE KPIs ---
        total_items = len(df_f)
        items_con_stock = len(df_f[df_f['STOCK'] > 0])
        pct_disponibilidad = (items_con_stock / total_items * 100) if total_items > 0 else 0
        
        # Stock Crítico (ejemplo: menos de 50 unidades)
        items_criticos = len(df_f[(df_f['STOCK'] > 0) & (df_f['STOCK'] < 50)])
        pct_critico = (items_criticos / total_items * 100) if total_items > 0 else 0

        # Mostrar KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Disponibilidad Catálogo", f"{pct_disponibilidad:.1f}%")
        c2.metric("Ítems en Stock Crítico", f"{pct_critico:.1f}%", delta="Riesgo", delta_color="inverse")
        c3.metric("Total de Ítems", total_items)

        st.markdown("---")

        # --- SECCIÓN DE GRÁFICOS ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("📦 Distribución por Categoría")
            fig_pie = px.pie(df_f, names=col_cat, values='STOCK', hole=0.4, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            st.subheader("🔝 Top 10 Unidades con Mayor Stock")
            resumen_uni = df_f.groupby(col_uni)['STOCK'].sum().reset_index().nlargest(10, 'STOCK')
            fig_bar = px.bar(
                resumen_uni, x='STOCK', y=col_uni, orientation='h',
                text='STOCK', # Muestra el valor
                color='STOCK', color_continuous_scale='Blues'
            )
            fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- TABLA DE DATOS FINAL ---
        st.subheader("📋 Matriz Detallada de Disponibilidad")
        cols_finales = [
            'OFICINA TECNICA', col_uni, col_cat, 
            'MEDICAMENTO O INSUMO', 'FORMA FARMACEUTICA', 
            'CONCENTRACION', 'STOCK'
        ]
        
        # Filtramos solo las columnas que existan para evitar errores
        tab_mostrar = [c for c in cols_finales if c in df_f.columns]
        st.dataframe(df_f[tab_mostrar], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en el procesamiento: {e}")
