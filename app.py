import streamlit as st
import pandas as pd
import plotly.express as px

# 1. CARGA DE DATOS (Mantenemos tu lógica de conexión)
# ... (Aquí iría tu función cargar_datos_graficos) ...

try:
    # --- PROCESAMIENTO DE KPIs EN % ---
    # Supongamos una meta de stock por ítem para el cálculo del % de abastecimiento
    # Si no hay meta, calculamos disponibilidad: (Items con Stock > 0 / Total Items)
    total_items = len(df_f)
    items_disponibles = len(df_f[df_f['STOCK'] > 0])
    pct_disponibilidad = (items_disponibles / total_items * 100) if total_items > 0 else 0
    
    # KPI 2: Porcentaje de Stock Crítico (Menos de 100 unidades)
    items_criticos = len(df_f[(df_f['STOCK'] > 0) & (df_f['STOCK'] < 100)])
    pct_critico = (items_criticos / total_items * 100) if total_items > 0 else 0

    st.title("📊 Control de Abastecimiento Provincial")
    
    # Visualización de KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Disponibilidad de Catálogo", f"{pct_disponibilidad:.1f}%", help="Porcentaje de ítems que tienen al menos 1 unidad")
    c2.metric("Ítems en Nivel Crítico", f"{pct_critico:.1f}%", delta="Riesgo", delta_color="inverse")
    c3.metric("Total de Registros", total_items)

    st.markdown("---")

    # --- SECCIÓN DE GRÁFICOS ---
    g1, g2 = st.columns(2)

    with g1:
        st.subheader("Distribución por Categoría")
        fig_pie = px.pie(df_f, names=col_cat, values='STOCK', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        st.subheader("Top 10 Unidades con Mayor Stock")
        # Agrupamos y obtenemos el top 10
        resumen_uni = df_f.groupby(col_uni)['STOCK'].sum().reset_index().nlargest(10, 'STOCK')
        
        # CREACIÓN DEL GRÁFICO CON VALORES INTERNOS
        fig_bar = px.bar(
            resumen_uni, 
            x='STOCK', 
            y=col_uni, 
            orientation='h', 
            color='STOCK',
            text='STOCK',  # <--- ESTO ACTIVA LOS VALORES
            color_continuous_scale='Blues',
            labels={'STOCK': 'Unidades Físicas', col_uni: 'Unidad Operativa'}
        )
        
        # Ajuste de posición del texto para que salga dentro o al final de la barra
        fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='outside') 
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TABLA ESTRICTA ---
    st.subheader("📋 Matriz de Datos")
    cols_pedidas = ['OFICINA TECNICA', col_uni, col_cat, 'MEDICAMENTO O INSUMO', 'FORMA FARMACEUTICA', 'CONCENTRACION', 'STOCK']
    st.dataframe(df_f[[c for c in cols_pedidas if c in df_f.columns]], use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error al generar visualizaciones: {e}")
