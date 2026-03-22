import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
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
    st.caption("v0.2 - Módulo Superficies")
    st.divider()

    with st.expander("🪵 1. Materiales y Espesores", expanded=True):
        espesor_tapa = st.selectbox("Espesor de la Tapa (mm)", [15, 18, 25, 36, 38], index=1, help="36mm equivale a placa de 18 regruesada. 38mm es formato Tamburato.")
        espesor_estruc = st.selectbox("Espesor Estructura (Patas/Faldón)", [15, 18, 25], index=1)
        zocalo = st.number_input("Altura Patines/Base (mm)", value=10, step=5, help="Luz para despegar la madera del piso")
        veta_frentes = st.radio("Veta Visual Frentes", ["↔️ Horizontal", "↕️ Vertical"], index=0)
    
    st.info("💡 Construcción 100% en placas. Seleccioná el espesor de la tapa independiente de la estructura.")

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
        st.caption("📏 Vuelos (Cuánto sobresale la tapa de la estructura)")
        c_v1, c_v2 = st.columns(2)
        vuelo_frontal = c_v1.number_input("Vuelo Frontal (mm)", value=20, step=5)
        vuelo_trasero = c_v2.number_input("Vuelo Trasero (mm)", value=50, step=5, help="Espacio para cables/pasacables")
        
        c_v3, c_v4 = st.columns(2)
        vuelo_izq = c_v3.number_input("Vuelo Izquierdo (mm)", value=10, step=5)
        vuelo_der = c_v4.number_input("Vuelo Derecho (mm)", value=10, step=5)

    # --- TARJETA 2: ESTRUCTURA DE APOYO ---
    st.subheader("2. Estructura y Apoyos")
    
    # Faldón Estructural
    with st.container(border=True):
        st.markdown("🧱 **Faldón Trasero (Anti-pandeo)**")
        c_f1, c_f2 = st.columns([2, 1])
        h_faldon = c_f1.slider("Altura del Faldón (mm)", 150, 700, 300, step=10)
        remetido_faldon = c_f2.number_input("Remetido (mm)", value=100, step=10, help="Distancia desde el borde trasero de la pata")

    # Selección de Patas/Bases
    c_p1, c_p2 = st.columns(2)
    with c_p1.container(border=True):
        st.markdown("⬅️ **Apoyo Izquierdo**")
        tipo_izq = st.selectbox("Tipo", ["Panel Simple", "Pata en 'L'", "Módulo Caja"], key="t_izq", label_visibility="collapsed")
        
        ancho_l_izq = 150 # Valor por defecto
        if tipo_izq == "Pata en 'L'":
            ancho_l_izq = st.number_input("Ancho L Frontal (mm)", value=150, step=10, key="w_l_izq")
        elif tipo_izq == "Módulo Caja":
            st.number_input("Ancho Caja (mm)", value=400, step=10, key="w_c_izq")
            st.caption("Configuración interna de caja próximamente.")

    with c_p2.container(border=True):
        st.markdown("➡️ **Apoyo Derecho**")
        tipo_der = st.selectbox("Tipo", ["Panel Simple", "Pata en 'L'", "Módulo Caja"], key="t_der", label_visibility="collapsed")
        
        ancho_l_der = 150
        if tipo_der == "Pata en 'L'":
            ancho_l_der = st.number_input("Ancho L Frontal (mm)", value=150, step=10, key="w_l_der")
        elif tipo_der == "Módulo Caja":
            st.number_input("Ancho Caja (mm)", value=400, step=10, key="w_c_der")
            st.caption("Configuración interna de caja próximamente.")

# ------------------------------------------------------------------------------
# ZONA DERECHA: VISUALIZADOR 3D AVANZADO
# ------------------------------------------------------------------------------
with col_visual:
    st.header("👁️ Vista Previa 3D")
    
    # Coordenadas maestras
    tapa_x0 = -largo_tapa / 2
    tapa_x1 = largo_tapa / 2
    tapa_y0 = -prof_tapa / 2
    tapa_y1 = prof_tapa / 2
    
    total_alto = 750 # Altura estándar de escritorio terminado
    h_estructura = total_alto - espesor_tapa - zocalo
    
    # Restando vuelos para saber dónde empieza la estructura de patas
    estructura_x0 = tapa_x0 + vuelo_izq
    estructura_x1 = tapa_x1 - vuelo_der
    estructura_y0 = tapa_y0 + vuelo_frontal
    estructura_y1 = tapa_y1 - vuelo_trasero
    
    fig = go.Figure()
    
    # Colores
    color_tapa = "#DEB887"
    color_estructura = "#A0522D" 
    color_caja = "#85C1E9"
    
    # Función base para dibujar cualquier placa en 3D
    def dibujar_placa(x0, x1, y0, y1, z0, z1, color, nombre):
        fig.add_trace(go.Mesh3d(
            x=[x0, x1, x1, x0, x0, x1, x1, x0],
            y=[y0, y0, y1, y1, y0, y0, y1, y1],
            z=[z0, z0, z0, z0, z1, z1, z1, z1],
            i=[7, 0, 0, 0, 4, 4, 3, 3, 7, 2, 6, 6],
            j=[3, 4, 1, 2, 5, 6, 2, 3, 6, 7, 1, 2],
            k=[0, 7, 2, 3, 6, 7, 1, 0, 2, 5, 5, 1],
            opacity=1, color=color, flatshading=True, name=nombre
        ))

    # 1. DIBUJAR TAPA
    dibujar_placa(tapa_x0, tapa_x1, tapa_y0, tapa_y1, total_alto-espesor_tapa, total_alto, color_tapa, "Tapa")

    # 2. DIBUJAR APOYO IZQUIERDO
    if tipo_izq == "Panel Simple":
        dibujar_placa(estructura_x0, estructura_x0 + espesor_estruc, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "Lateral Izq")
    elif tipo_izq == "Pata en 'L'":
        # Placa paralela al lateral
        dibujar_placa(estructura_x0, estructura_x0 + espesor_estruc, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "L-Lat Izq")
        # Placa frontal formando la L (hacia adentro)
        dibujar_placa(estructura_x0 + espesor_estruc, estructura_x0 + ancho_l_izq, estructura_y0, estructura_y0 + espesor_estruc, zocalo, total_alto-espesor_tapa, color_estructura, "L-Front Izq")
    elif tipo_izq == "Módulo Caja":
        w_caja_i = st.session_state.get("w_c_izq", 400)
        dibujar_placa(estructura_x0, estructura_x0 + w_caja_i, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_caja, "Cajonera Izq")

    # 3. DIBUJAR APOYO DERECHO
    if tipo_der == "Panel Simple":
        dibujar_placa(estructura_x1 - espesor_estruc, estructura_x1, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "Lateral Der")
    elif tipo_der == "Pata en 'L'":
        dibujar_placa(estructura_x1 - espesor_estruc, estructura_x1, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "L-Lat Der")
        dibujar_placa(estructura_x1 - ancho_l_der, estructura_x1 - espesor_estruc, estructura_y0, estructura_y0 + espesor_estruc, zocalo, total_alto-espesor_tapa, color_estructura, "L-Front Der")
    elif tipo_der == "Módulo Caja":
        w_caja_d = st.session_state.get("w_c_der", 400)
        dibujar_placa(estructura_x1 - w_caja_d, estructura_x1, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_caja, "Cajonera Der")

    # 4. DIBUJAR FALDÓN TRASERO
    y_faldon_trasero = estructura_y1 - remetido_faldon
    
    # Calcular dónde empieza y termina el faldón dependiendo de los apoyos elegidos
    inicio_faldon = estructura_x0 + (espesor_estruc if tipo_izq != "Módulo Caja" else st.session_state.get("w_c_izq", 400))
    fin_faldon = estructura_x1 - (espesor_estruc if tipo_der != "Módulo Caja" else st.session_state.get("w_c_der", 400))
    
    dibujar_placa(inicio_faldon, fin_faldon, y_faldon_trasero - espesor_estruc, y_faldon_trasero, total_alto-espesor_tapa-h_faldon, total_alto-espesor_tapa, color_estructura, "Faldón")

    # Configuración de escena 3D
    max_dim = max(largo_tapa, total_alto)
    fig.update_layout(
        scene=dict(
            xaxis=dict(nticks=4, range=[-max_dim/2-100, max_dim/2+100], backgroundcolor="rgb(240, 240, 245)", gridcolor="white", showbackground=True),
            yaxis=dict(nticks=4, range=[-max_dim/2-100, max_dim/2+100], backgroundcolor="rgb(245, 240, 245)", gridcolor="white", showbackground=True),
            zaxis=dict(nticks=4, range=[0, max_dim+100], backgroundcolor="rgb(245, 245, 240)", gridcolor="white", showbackground=True),
            aspectmode='data'
        ),
        margin=dict(r=0, l=0, b=0, t=0),
        scene_camera=dict(eye=dict(x=1.8, y=-1.5, z=0.8)) # Ángulo isométrico mejorado
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- ZONA DE RESULTADOS ---
    st.markdown("---")
    st.subheader("📋 Despiece Inicial (Superficies)")
    
    despiece = []
    
    # Tapa
    nota_tapa = "Tamburato / Especial" if espesor_tapa >= 36 else "Melamina Estándar"
    despiece.append({"Pieza": "Tapa Escritorio", "Cant": 1, "Largo": largo_tapa, "Ancho": prof_tapa, "Espesor": espesor_tapa, "Nota": nota_tapa})

    # Estructura
    w_lateral = estructura_y1 - estructura_y0
    
    if tipo_izq == "Panel Simple":
        despiece.append({"Pieza": "Apoyo Izq (Panel)", "Cant": 1, "Largo": h_estructura, "Ancho": w_lateral, "Espesor": espesor_estruc})
    elif tipo_izq == "Pata en 'L'":
        despiece.append({"Pieza": "Apoyo Izq (Lateral L)", "Cant": 1, "Largo": h_estructura, "Ancho": w_lateral, "Espesor": espesor_estruc})
        despiece.append({"Pieza": "Apoyo Izq (Frente L)", "Cant": 1, "Largo": h_estructura, "Ancho": ancho_l_izq - espesor_estruc, "Espesor": espesor_estruc})
        
    if tipo_der == "Panel Simple":
        despiece.append({"Pieza": "Apoyo Der (Panel)", "Cant": 1, "Largo": h_estructura, "Ancho": w_lateral, "Espesor": espesor_estruc})
    elif tipo_der == "Pata en 'L'":
        despiece.append({"Pieza": "Apoyo Der (Lateral L)", "Cant": 1, "Largo": h_estructura, "Ancho": w_lateral, "Espesor": espesor_estruc})
        despiece.append({"Pieza": "Apoyo Der (Frente L)", "Cant": 1, "Largo": h_estructura, "Ancho": ancho_l_der - espesor_estruc, "Espesor": espesor_estruc})

    largo_faldon = fin_faldon - inicio_faldon
    despiece.append({"Pieza": "Faldón Anti-pandeo", "Cant": 1, "Largo": largo_faldon, "Ancho": h_faldon, "Espesor": espesor_estruc})

    st.dataframe(pd.DataFrame(despiece), use_container_width=True, hide_index=True)
