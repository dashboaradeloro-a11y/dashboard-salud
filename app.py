import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Dashboard Provincial MSP - El Oro", layout="wide")

# Estilos para que los KPIs resalten
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #003087; font-size: 36px; }
    .main { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300)
def cargar_datos_graficos():
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
                df_temp.columns = [str(c).strip().upper().replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U') for c in df_temp.columns]
                df_temp['OFICINA TECNICA'] = p
                lista_df.append(df_temp)
        except: continue
    return pd.concat(lista_df, ignore_index=True) if lista_df else pd.DataFrame()

try:
    df = cargar_datos_graficos()
    
    # Normalización de columnas críticas
    col_uni = next((c for c in df.columns if "UNIDAD" in c), "UNIDAD OPERATIVA")
    col_cat = next((c for c in df.columns if "CATEGORIA" in c), "CATEGORIA")
    if 'STOCK' in df.columns:
        df['STOCK'] = pd.to_numeric(df['STOCK'], errors='coerce').fillna(0)

    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros de Reporte")
    ot_sel = st.sidebar.selectbox("Oficina Técnica", ["TODAS"] + sorted(df['OFICINA TECNICA'].unique()))
    df_f = df[df['OFICINA TECNICA'] == ot_sel] if ot_sel != "TODAS" else df.copy()

    uni_list = sorted(df_f[col_uni].dropna().unique()) if col_uni in df_f.columns else []
    uni_sel = st.sidebar.selectbox("Unidad Operativa", ["TODAS"] + uni_list)
    if uni_sel != "TODAS": df_f = df_f[df_f[col_uni] == uni_sel]

    cat_list = sorted(df_f[col_cat].dropna().unique()) if col_cat in df_f.columns else []
    cat_sel = st.sidebar.multiselect("Categoría", cat_list, default=cat_list)
    df_f = df_f[df_f[col_cat].isin(cat_sel)]

    busqueda = st.text_input("🔎 Buscar Medicamento o Insumo...")
    if busqueda:
        df_f = df_f[df_f.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)]

    # --- CÁLCULO DE PORCENTAJES (KPIs) ---
    # Lógica: Asumimos que un item está "Abastecido" si el stock es > 0.
    # En una matriz real, esto se compararía contra el Stock de Reserva.
    total_items = len(df_f)
    items_con_stock = len(df_f[df_f['STOCK'] > 0])
    porcentaje_abastecimiento = (items_con_stock / total_items * 100) if total_items > 0 else 0
    
    # Items en stock crítico (menos de 50 unidades como ejemplo)
    items_criticos = len(df_f[(df_f['STOCK'] > 0) & (df_f['STOCK'] < 50)])
    porcentaje_critico = (items_criticos / total_items * 100) if total_items > 0 else 0

    # --- VISUALIZACIÓN DE KPIs ---
    st.title("📊 Dashboard de Gestión de Insumos")
    c1, c2, c3 = st.columns(3)
    c1.metric("Disponibilidad Total", f"{porcentaje_abastecimiento:.1f}%", delta="Abastecido")
    c2.metric("Riesgo de Quiebre", f"{porcentaje_critico:.1f}%", delta="- Crítico", delta_color="inverse")
    c3.metric("Ítems Sin Stock (Cero)", f"{total_items - items_con_stock}", delta="Faltantes", delta_color="inverse")

    st.markdown("---")

    # --- SECCIÓN DE GRÁFICOS ---
    g1, g2 = st.columns(2)
    
    with g1:
        st.subheader("Distribución por Categoría")
        fig_pie = px.pie(df_f, names=col_cat, values='STOCK', hole=0.4, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        st.subheader("Top 10 Unidades con Mayor Stock")
        resumen_uni = df_f.groupby(col_uni)['STOCK'].sum().reset_index().nlargest(10, 'STOCK')
        fig_bar = px.bar(resumen_uni, x='STOCK', y=col_uni, orientation='h', color='STOCK',
                         color_continuous_scale='Blues')
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABLA SOLICITADA ---
    st.subheader("📋 Matriz de Datos")
    cols_pedidas = ['OFICINA TECNICA', col_uni, col_cat, 'MEDICAMENTO O INSUMO', 'FORMA FARMACEUTICA', 'CONCENTRACION', 'STOCK']
    st.dataframe(df_f[[c for c in cols_pedidas if c in df_f.columns]], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error en el Dashboard: {e}")
