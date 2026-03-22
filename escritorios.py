import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA - PRO UI STYLE
# ==============================================================================
st.set_page_config(page_title="CarpinterIA Superficies", page_icon="🪑", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .stNumberInput, .stSelectbox, .stSlider { margin-bottom: -10px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. BARRA LATERAL (AJUSTES DE MATERIAL)
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063080.png", width=60)
    st.title("CarpinterIA")
    st.caption("v0.1 - Módulo Superficies (Concepto)")
    st.divider()

    with st.expander("🪵 1. Parámetros de Placa", expanded=True):
        espesor = st.selectbox("Espesor Melamina (mm)", [18, 15], index=0)
        zocalo = st.number_input("Altura Patines/Base (mm)", value=10, step=5, help="Pequeña altura para despegar el lateral del piso")
        veta_frentes = st.radio("Veta Visual Frentes", ["↔️ Horizontal", "↕️ Vertical"], index=0)
    
    st.info("Este módulo conceptual asume construcción 100% en melamina. No incluye patas metálicas.")

# ==============================================================================
# LAYOUT PRINCIPAL A DOS COLUMNAS
# ==============================================================================
col_controles, col_visual = st.columns([1.1, 1.9], gap="large")

# ------------------------------------------------------------------------------
# ZONA IZQUIERDA: CONTROLES Y DISEÑO DE ESCRITORIO
# ------------------------------------------------------------------------------
with col_controles:
    st.header("📐 Diseño de Escritorio")
    
    # --- TARJETA 1: DIMENSIONES DE LA TAPA ---
    with st.container(border=True):
        st.subheader("1. La Tapa (Superficie)")
        c_dim1, c_dim2 = st.columns(2)
        largo_tapa = c_dim1.number_input("Largo Total (mm)", value=1500, min_value=600, step=10)
        prof_tapa = c_dim2.number_input("Profundidad Total (mm)", value=700, min_value=400, step=10)
        
        st.divider()
        tiene_regrueso = st.toggle("🔨 Regrueso Perimetral (Visual 36mm)", value=True, help="Agrega tiras por debajo para duplicar el espesor visual en los bordes")
        
        st.caption("📏 Vuelos (Overhang - Cuánto sobresale la tapa)")
        c_v1, c_v2 = st.columns(2)
        vuelo_frontal = c_v1.number_input("Vuelo Frontal (mm)", value=20, step=5)
        vuelo_trasero = c_v2.number_input("Vuelo Trasero (mm)", value=50, step=5, help="Espacio para cables/zócalos")
        
        c_v3, c_v4 = st.columns(2)
        vuelo_izq = c_v3.number_input("Vuelo Izquierdo (mm)", value=10, step=5)
        vuelo_der = c_v4.number_input("Vuelo Derecho (mm)", value=10, step=5)

    # --- TARJETA 2: ESTRUCTURA DE APOYO ---
    st.subheader("2. Estructura y Apoyos")
    
    # Faldón Estructural
    with st.container(border=True):
        st.markdown("🧱 **Faldón Trasero (Anti-pandeo)**")
        c_f1, c_f2 = st.columns([2, 1])
        h_faldon = c_f1.slider("Altura del Faldón (mm)", 150, 600, 300, step=10, help="Pieza vertical trasera que une las patas y rigidiza la tapa")
        remetido_faldon = c_f2.number_input("Remetido (mm)", value=100, step=10, help="Distancia desde el borde trasero de la estructura")

    # Selección de Patas/Bases
    c_p1, c_p2 = st.columns(2)
    with c_p1.container(border=True):
        st.markdown("⬅️ **Apoyo Izquierdo**")
        tipo_izq = st.selectbox("Tipo", ["Panel Simple", "Pata en 'L'", "Módulo Caja"], key="t_izq", label_visibility="collapsed")
        
        ancho_apoyo_izq = espesor # Default Panel Simple
        if tipo_izq == "Pata en 'L'":
            ancho_apoyo_izq = st.number_input("Ancho L (mm)", value=100, step=10, key="w_l_izq")
        elif tipo_izq == "Módulo Caja":
            ancho_apoyo_izq = st.number_input("Ancho Caja (mm)", value=400, step=10, key="w_c_izq")
            st.caption("Logic for drawers/doors will go here later.")

    with c_p2.container(border=True):
        st.markdown("➡️ **Apoyo Derecho**")
        tipo_der = st.selectbox("Tipo", ["Panel Simple", "Pata en 'L'", "Módulo Caja"], key="t_der", label_visibility="collapsed")
        
        ancho_apoyo_der = espesor # Default Panel Simple
        if tipo_der == "Pata en 'L'":
            ancho_apoyo_der = st.number_input("Ancho L (mm)", value=100, step=10, key="w_l_der")
        elif tipo_der == "Módulo Caja":
            ancho_apoyo_der = st.number_input("Ancho Caja (mm)", value=400, step=10, key="w_c_der")
            st.caption("Logic for drawers/doors will go here later.")

# ------------------------------------------------------------------------------
# ZONA DERECHA: VISUALIZADOR 3D CONCEPTUAL
# ------------------------------------------------------------------------------
with col_visual:
    st.header("👁️ Vista Previa")
    
    # Cálculos Geométricos para la visualización
    # Coordenadas de la Tapa (Centrada en X=0, Y=0 por simplicidad conceptual)
    tapa_x0 = -largo_tapa / 2
    tapa_x1 = largo_tapa / 2
    tapa_y0 = -prof_tapa / 2
    tapa_y1 = prof_tapa / 2
    
    espesor_visual_tapa = espesor * 2 if tiene_regrueso else espesor
    total_alto = 750 # Altura estándar de escritorio para la visualización
    
    # Coordenadas de la estructura (restando vuelos)
    estructura_x0 = tapa_x0 + vuelo_izq
    estructura_x1 = tapa_x1 - vuelo_der
    estructura_y0 = tapa_y0 + vuelo_frontal
    estructura_y1 = tapa_y1 - vuelo_trasero
    
    estructura_ancho = estructura_x1 - estructura_x0
    estructura_prof = estructura_y1 - estructura_y0
    estructura_alto = total_alto - espesor_visual_tapa - zocalo
    
    # Gráfico
    fig = go.Figure()
    
    # 1. DIBUJAR TAPA (Placa horizontal superior)
    # Color madera claro
    color_tapa = "#DEB887"
    color_linea = "#5D4037"
    
    # Tapa Principal
    fig.add_trace(go.Mesh3d(
        x=[tapa_x0, tapa_x1, tapa_x1, tapa_x0, tapa_x0, tapa_x1, tapa_x1, tapa_x0],
        y=[tapa_y0, tapa_y0, tapa_y1, tapa_y1, tapa_y0, tapa_y0, tapa_y1, tapa_y1],
        z=[total_alto-espesor_visual_tapa, total_alto-espesor_visual_tapa, total_alto-espesor_visual_tapa, total_alto-espesor_visual_tapa, total_alto, total_alto, total_alto, total_alto],
        i=[7, 0, 0, 0, 4, 4, 3, 3, 7, 2, 6, 6],
        j=[3, 4, 1, 2, 5, 6, 2, 3, 6, 7, 1, 2],
        k=[0, 7, 2, 3, 6, 7, 1, 0, 2, 5, 5, 1],
        opacity=1, color=color_tapa, flatshading=True, name="Tapa"
    ))

    # 2. DIBUJAR APOYO IZQUIERDO (Conceptual)
    color_estructura = "#A0522D" # Madera más oscura siena
    
    def dibujar_cubo_coords(x0, x1, y0, y1, z0, z1, color, nombre):
        fig.add_trace(go.Mesh3d(
            x=[x0, x1, x1, x0, x0, x1, x1, x0],
            y=[y0, y0, y1, y1, y0, y0, y1, y1],
            z=[z0, z0, z0, z0, z1, z1, z1, z1],
            i=[7, 0, 0, 0, 4, 4, 3, 3, 7, 2, 6, 6],
            j=[3, 4, 1, 2, 5, 6, 2, 3, 6, 7, 1, 2],
            k=[0, 7, 2, 3, 6, 7, 1, 0, 2, 5, 5, 1],
            opacity=1, color=color, flatshading=True, name=nombre
        ))

    # Apoyo Izq (Simplificado a un bloque según ancho)
    dibujar_cubo_coords(estructura_x0, estructura_x0 + ancho_apoyo_izq, estructura_y0, estructura_y1, zocalo, total_alto-espesor_visual_tapa, color_estructura, "Apoyo Izq")
    
    # Apoyo Der (Simplificado a un bloque según ancho)
    dibujar_cubo_coords(estructura_x1 - ancho_apoyo_der, estructura_x1, estructura_y0, estructura_y1, zocalo, total_alto-espesor_visual_tapa, color_estructura, "Apoyo Der")

    # 3. DIBUJAR FALDÓN TRASERO
    y_faldon_trasero = estructura_y1 - remetido_faldon
    dibujar_cubo_coords(estructura_x0 + ancho_apoyo_izq, estructura_x1 - ancho_apoyo_der, y_faldon_trasero - espesor, y_faldon_trasero, total_alto-espesor_visual_tapa-h_faldon, total_alto-espesor_visual_tapa, color_estructura, "Faldón")

    # Configuración de escena
    max_dim = max(largo_tapa, total_alto)
    fig.update_layout(
        scene=dict(
            xaxis=dict(nticks=4, range=[-max_dim/2-100, max_dim/2+100], backgroundcolor="rgb(200, 200, 230)", gridcolor="white", showbackground=True, zerolinecolor="white"),
            yaxis=dict(nticks=4, range=[-max_dim/2-100, max_dim/2+100], backgroundcolor="rgb(230, 200, 230)", gridcolor="white", showbackground=True, zerolinecolor="white"),
            zaxis=dict(nticks=4, range=[0, max_dim+100], backgroundcolor="rgb(230, 230, 200)", gridcolor="white", showbackground=True, zerolinecolor="white"),
            aspectmode='data' # Mantiene proporciones reales
        ),
        margin=dict(r=10, l=10, b=10, t=30),
        scene_camera=dict(eye=dict(x=1.5, y=-1.5, z=1)) # Ángulo de cámara por defecto
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- ZONA DE RESULTADOS CONCEPTUALES ---
    st.markdown("---")
    st.subheader("📋 Resumen de Materiales (Concepto)")
    
    # Generación de "Despiece" simplificado
    despiece = []
    
    # Tapa
    nota_tapa = "Regrueso 36mm" if tiene_regrueso else "Simple 18mm"
    despiece.append({"Pieza": "Tapa Escritorio", "Cant": 1, "Largo": largo_tapa, "Ancho": prof_tapa, "Nota": nota_tapa})
    
    if tiene_regrueso:
        despiece.append({"Pieza": "Tiras Regrueso Largo", "Cant": 2, "Largo": largo_tapa, "Ancho": 70, "Nota": "Pegar debajo"})
        despiece.append({"Pieza": "Tiras Regrueso Corto", "Cant": 2, "Largo": prof_tapa - 140, "Ancho": 70, "Nota": "Pegar debajo"})

    # Estructura (Muy simplificado por ser concepto)
    h_estructura = total_alto - espesor_visual_tapa - zocalo
    despiece.append({"Pieza": f"Apoyo Izq ({tipo_izq})", "Cant": 1, "Largo": h_estructura, "Ancho": estructura_prof, "Nota": f"W: {ancho_apoyo_izq}mm"})
    despiece.append({"Pieza": f"Apoyo Der ({tipo_der})", "Cant": 1, "Largo": h_estructura, "Ancho": estructura_prof, "Nota": f"W: {ancho_apoyo_der}mm"})
    despiece.append({"Pieza": "Faldón Estructural", "Cant": 1, "Largo": estructura_ancho - ancho_apoyo_izq - ancho_apoyo_der, "Ancho": h_faldon, "Nota": "Trasero"})

    st.dataframe(pd.DataFrame(despiece), use_container_width=True, hide_index=True)
