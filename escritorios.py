import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(page_title="CarpinterIA Superficies V0.3", page_icon="🪑", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .stNumberInput, .stSelectbox, .stSlider { margin-bottom: -10px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# HELPERS LOGICOS (REUTILIZADOS/ADAPTADOS DE V25)
# ==============================================================================
def get_limit_cajones(h_util):
    return max(1, int(h_util / 75)) if h_util > 70 else 1

# Helper específico para la configuración de la caja de apoyo
def ui_config_caja(key_prefix, h_util_caja):
    st.caption("🔧 Configuración Interna del Apoyo")
    
    # 1. Función Principal
    funcion = st.radio("Función", ["Cajonera", "Puerta"], key=f"{key_prefix}_func", horizontal=True)
    
    d = {"funcion": funcion}
    
    if funcion == "Cajonera":
        # Cálculo físico limitante
        mc = get_limit_cajones(h_util_caja)
        # Suministrar valor sugerido según posición (abajo suele ser ollero, medio std)
        val_sug = min(3 if "izq" in key_prefix else 2, mc)
        d["cant"] = st.number_input("Cantidad Cajones", 1, mc, val_sug, key=f"{key_prefix}_q_caj")
    
    elif funcion == "Puerta":
        st.caption("🔍 Interior (Apertura Lateral)")
        t = st.radio("Tipo Interior", ["Vacío", "Estantes"], horizontal=True, key=f"{key_prefix}_t_int")
        d_int = {}
        if t == "Estantes": 
            d_int = {"tipo": "Estantes", "cant": st.number_input("Cant.", 1, 10, 2, key=f"{key_prefix}_e")}
        d["interior"] = d_int
        
    return d

# ==============================================================================
# 1. BARRA LATERAL (AJUSTES DE MATERIAL)
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063080.png", width=60)
    st.title("CarpinterIA")
    st.caption("v0.3 - Módulos Integrados")
    st.divider()

    with st.expander("🪵 1. Materiales y Espesores", expanded=True):
        espesor_tapa = st.selectbox("Espesor de la Tapa (mm)", [15, 18, 25, 36, 38], index=1)
        espesor_estruc = st.selectbox("Espesor Estructura (Patas/Cajas)", [15, 18, 25], index=1)
        zocalo = st.number_input("Altura Patines/Base (mm)", value=10, step=5)
    
    st.info("💡 Construcción 100% en placas. Los módulos de apoyo (Cajas) se integran matemáticamente a la tapa.")

configuracion_apoyos = {}

# ==============================================================================
# LAYOUT PRINCIPAL A DOS COLUMNAS
# ==============================================================================
col_controles, col_visual = st.columns([1.1, 1.9], gap="large")

# ------------------------------------------------------------------------------
# ZONA IZQUIERDA: CONTROLES Y DISEÑO DE ESCRITORIO
# ------------------------------------------------------------------------------
with col_controles:
    st.header("📐 Diseño de Escritorio gerencial")
    
    # --- TARJETA 1: DIMENSIONES DE LA TAPA ---
    with st.container(border=True):
        st.subheader("1. La Tapa (Superficie)")
        c_dim1, c_dim2 = st.columns(2)
        largo_tapa = c_dim1.number_input("Largo Total (mm)", value=1800, min_value=600, step=10)
        prof_tapa = c_dim2.number_input("Profundidad Total (mm)", value=800, min_value=400, step=10)
        
        st.divider()
        st.caption("📏 Vuelos (Overhang)")
        c_v1, c_v2 = st.columns(2)
        vuelo_frontal = c_v1.number_input("Vuelo Frontal (mm)", value=50, step=5, help="Espacio para las piernas")
        vuelo_trasero = c_v2.number_input("Vuelo Trasero (mm)", value=20, step=5)
        
        c_v3, c_v4 = st.columns(2)
        vuelo_izq = c_v3.number_input("Vuelo Izquierdo (mm)", value=10, step=5)
        vuelo_der = c_v4.number_input("Vuelo Derecho (mm)", value=10, step=5)

    # --- TARJETA 2: ESTRUCTURA Y APOYOS ---
    st.subheader("2. Estructura y Apoyos")
    
    # Cálculos previos necesarios para límites físicos
    total_alto = 750
    estructura_prof = prof_tapa - vuelo_frontal - vuelo_trasero
    # h_util de la caja = Alto total - Tapa - Zocalo - Espesor Techo Caja - Espesor Piso Caja
    h_util_caja_apoyo = total_alto - espesor_tapa - zocalo - (espesor_estruc * 2)

    # Faldón Estructural
    with st.container(border=True):
        st.markdown("🧱 **Faldón Trasero (Anti-pandeo)**")
        c_f1, c_f2 = st.columns([2, 1])
        h_faldon = c_f1.slider("Altura del Faldón (mm)", 150, 700, 400, step=10)
        remetido_faldon = c_f2.number_input("Remetido (mm)", value=50, step=10, help="Distancia desde el borde trasero de la pata")

    # Selección de Patas/Bases
    c_p1, c_p2 = st.columns(2)
    with c_p1.container(border=True):
        st.markdown("⬅️ **Apoyo Izquierdo**")
        tipo_izq = st.selectbox("Tipo", ["Panel Simple", "Pata en 'L'", "Módulo Caja"], key="t_izq", label_visibility="collapsed")
        
        data_izq = {"tipo": tipo_izq}
        if tipo_izq == "Pata en 'L'":
            data_izq["ancho_l"] = st.number_input("Ancho L Frontal (mm)", value=150, step=10, key="w_l_izq")
        elif tipo_izq == "Módulo Caja":
            data_izq["ancho_caja"] = st.number_input("Ancho Caja (mm)", value=450, step=10, key="w_c_izq")
            # INTEGRACIÓN INTELIGENTE V25
            data_izq["config"] = ui_config_caja("izq", h_util_caja_apoyo)
        
        configuracion_apoyos["izq"] = data_izq

    with c_p2.container(border=True):
        st.markdown("➡️ **Apoyo Derecho**")
        tipo_der = st.selectbox("Tipo", ["Panel Simple", "Pata en 'L'", "Módulo Caja"], key="t_der", label_visibility="collapsed")
        
        data_der = {"tipo": tipo_der}
        if tipo_der == "Pata en 'L'":
            data_der["ancho_l"] = st.number_input("Ancho L Frontal (mm)", value=150, step=10, key="w_l_der")
        elif tipo_der == "Módulo Caja":
            data_der["ancho_caja"] = st.number_input("Ancho Caja (mm)", value=450, step=10, key="w_c_der")
            # INTEGRACIÓN INTELIGENTE V25
            data_der["config"] = ui_config_caja("der", h_util_caja_apoyo)
        
        configuracion_apoyos["der"] = data_der

# ------------------------------------------------------------------------------
# ZONA DERECHA: VISUALIZADOR 3D AVANZADO E INTEGRADO
# ------------------------------------------------------------------------------
with col_visual:
    st.header("👁️ Vista Previa 3D Integrada")
    
    # Coordenadas maestras
    tapa_x0 = -largo_tapa / 2
    tapa_x1 = largo_tapa / 2
    tapa_y0 = -prof_tapa / 2
    tapa_y1 = prof_tapa / 2
    
    # Restando vuelos para saber dónde empieza la estructura de patas
    estructura_x0 = tapa_x0 + vuelo_izq
    estructura_x1 = tapa_x1 - vuelo_der
    estructura_y0 = tapa_y0 + vuelo_frontal
    estructura_y1 = tapa_y1 - vuelo_trasero
    
    fig = go.Figure()
    
    # Colores
    color_tapa = "#DEB887"
    color_estructura = "#A0522D" 
    color_caja_carcasa = "#8B4513" # Madera oscura para carcasa
    color_caja_frente = "#AED6F1" # Azul claro para frentes
    
    # Función base para dibujar cualquier placa en 3D
    def dibujar_placa(x0, x1, y0, y1, z0, z1, color, nombre, opacidad=1):
        fig.add_trace(go.Mesh3d(
            x=[x0, x1, x1, x0, x0, x1, x1, x0],
            y=[y0, y0, y1, y1, y0, y0, y1, y1],
            z=[z0, z0, z0, z0, z1, z1, z1, z1],
            i=[7, 0, 0, 0, 4, 4, 3, 3, 7, 2, 6, 6],
            j=[3, 4, 1, 2, 5, 6, 2, 3, 6, 7, 1, 2],
            k=[0, 7, 2, 3, 6, 7, 1, 0, 2, 5, 5, 1],
            opacity=opacidad, color=color, flatshading=True, name=nombre
        ))

    # 1. DIBUJAR TAPA
    dibujar_placa(tapa_x0, tapa_x1, tapa_y0, tapa_y1, total_alto-espesor_tapa, total_alto, color_tapa, "Tapa")

    # Función conceptual para dibujar el interior visible detrás de Rayos X (frentes)
    def interior_conceptual(x0, x1, y0, y1, z_base, h_util, config):
        func = config.get("funcion")
        nota = ""
        
        if func == "Cajonera":
            cant = config.get("cant", 1)
            hu_frente = h_util / cant
            # Dibujar frentes conceptuales translúcidos
            for k in range(cant):
                z_f_0 = z_base + (k * hu_frente) + 2
                z_f_1 = z_base + ((k+1) * hu_frente) - 2
                dibujar_placa(x0, x1, y0-2, y0+5, z_f_0, z_f_1, color_caja_frente, f"Frente Caj C{k+1}", 0.7)
            nota = f"{cant} Cajones"

        elif func == "Puerta":
            # Un solo frente grande translúcido
            dibujar_placa(x0, x1, y0-2, y0+5, z_base+2, z_base+h_util-2, color_caja_frente, "Frente Puerta", 0.7)
            
            # Dibujar estantes interiores conceptuales si existen
            din = config.get("interior", {})
            if din.get("tipo") == "Estantes":
                cant_e = din.get("cant", 1)
                p = h_util / (cant_e + 1)
                for k in range(cant_e):
                    y_e = z_base + (p * (k+1))
                    # Estantes líneas sutiles
                    fig.add_shape(type="line", x0=x0+5, y0=y0+10, x1=x1-5, y1=y1-10, xref="x", yref="y")
                    # No soporta líneas 3D mesh, dibujar placas finas
                    dibujar_placa(x0+5, x1-5, y0+10, y1-10, y_e, y_e+ espsor_estruc if 'espsor_estruc' in locals() else y_e+18, color_estructura, f"Estante {k+1}", 0.5)
            nota = "Puerta + Interior"
        return nota

    # 2. DIBUJAR APOYO IZQUIERDO Integrado
    data_izq = configuracion_apoyos["izq"]
    t_izq = data_izq["tipo"]
    nota_izq = ""
    
    if t_izq == "Panel Simple":
        dibujar_placa(estructura_x0, estructura_x0 + espesor_estruc, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "Lateral Izq")
    
    elif t_izq == "Pata en 'L'":
        ancho_l = data_izq["ancho_l"]
        # Placa paralela al lateral
        dibujar_placa(estructura_x0, estructura_x0 + espesor_estruc, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "L-Lat Izq")
        # Placa frontal formando la L (hacia adentro)
        dibujar_placa(estructura_x0 + espesor_estruc, estructura_x0 + ancho_l, estructura_y0, estructura_y0 + espesor_estruc, zocalo, total_alto-espesor_tapa, color_estructura, "L-Front Izq")
    
    elif t_izq == "Módulo Caja":
        w_caja = data_izq["ancho_caja"]
        # Carcasa (Techo, Piso, Laterales oscuros)
        # Piso
        dibujar_placa(estructura_x0, estructura_x0 + w_caja, estructura_y0, estructura_y1, zocalo, zocalo + espesor_estruc, color_caja_carcasa, "Piso Caja Izq")
        # Techo
        dibujar_placa(estructura_x0, estructura_x0 + w_caja, estructura_y0, estructura_y1, total_alto-espesor_tapa-espesor_estruc, total_alto-espesor_tapa, color_caja_carcasa, "Techo Caja Izq")
        # Lateral Externo
        dibujar_placa(estructura_x0, estructura_x0 + espesor_estruc, estructura_y0, estructura_y1, zocalo + espesor_estruc, total_alto-espesor_tapa-espesor_estruc, color_caja_carcasa, "Lat Ext Caja Izq")
        # Lateral Interno
        dibujar_placa(estructura_x0 + w_caja - espesor_estruc, estructura_x0 + w_caja, estructura_y0, estructura_y1, zocalo + espesor_estruc, total_alto-espesor_tapa-espesor_estruc, color_caja_carcasa, "Lat Int Caja Izq")
        
        # FRENTES Y RAYOS X
        conf_interna = data_izq.get("config", {})
        nota_izq = interior_conceptual(estructura_x0 + espesor_estruc, estructura_x0 + w_caja - espesor_estruc, estructura_y0, estructura_y1, zocalo + espesor_estruc, h_util_caja_apoyo, conf_interna)

    # 3. DIBUJAR APOYO DERECHO Integrado
    data_der = configuracion_apoyos["der"]
    t_der = data_der["tipo"]
    nota_der = ""
    
    if t_der == "Panel Simple":
        dibujar_placa(estructura_x1 - espesor_estruc, estructura_x1, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "Lateral Der")
    
    elif t_der == "Pata en 'L'":
        ancho_l = data_der["ancho_l"]
        dibujar_placa(estructura_x1 - espesor_estruc, estructura_x1, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "L-Lat Der")
        dibujar_placa(estructura_x1 - ancho_l, estructura_x1 - espesor_estruc, estructura_y0, estructura_y0 + espesor_estruc, zocalo, total_alto-espesor_tapa, color_estructura, "L-Front Der")
    
    elif t_der == "Módulo Caja":
        w_caja = data_der["ancho_caja"]
        # Carcasa
        dibujar_placa(estructura_x1 - w_caja, estructura_x1, estructura_y0, estructura_y1, zocalo, zocalo + espesor_estruc, color_caja_carcasa, "Piso Caja Der")
        dibujar_placa(estructura_x1 - w_caja, estructura_x1, estructura_y0, estructura_y1, total_alto-espesor_tapa-espesor_estruc, total_alto-espesor_tapa, color_caja_carcasa, "Techo Caja Der")
        dibujar_placa(estructura_x1 - w_caja, estructura_x1 - w_caja + espesor_estruc, estructura_y0, estructura_y1, zocalo + espesor_estruc, total_alto-espesor_tapa-espesor_estruc, color_caja_carcasa, "Lat Int Caja Der")
        dibujar_placa(estructura_x1 - espesor_estruc, estructura_x1, estructura_y0, estructura_y1, zocalo + espesor_estruc, total_alto-espesor_tapa-espesor_estruc, color_caja_carcasa, "Lat Ext Caja Der")
        
        # FRENTES Y RAYOS X
        conf_interna = data_der.get("config", {})
        nota_der = interior_conceptual(estructura_x1 - w_caja + espesor_estruc, estructura_x1 - espesor_estruc, estructura_y0, estructura_y1, zocalo + espesor_estruc, h_util_caja_apoyo, conf_interna)

    # 4. DIBUJAR FALDÓN TRASERO
    y_faldon_trasero = estructura_y1 - remetido_faldon
    
    # Calcular dónde empieza y termina el faldón dependiendo de los apoyos elegidos
    width_izq = espesor_estruc if t_izq != "Módulo Caja" else data_izq["ancho_caja"]
    width_der = espesor_estruc if t_der != "Módulo Caja" else data_der["ancho_caja"]
    
    inicio_faldon = estructura_x0 + width_izq
    fin_faldon = estructura_x1 - width_der
    
    dibujar_placa(inicio_faldon, fin_faldon, y_faldon_trasero - espesor_estruc, y_faldon_trasero, total_alto-espesor_tapa-h_faldon, total_alto-espesor_tapa, color_estructura, "Faldón")

    # Configuración de escena 3D e Isometría
    max_dim = max(largo_tapa, total_alto)
    fig.update_layout(
        scene=dict(
            xaxis=dict(nticks=4, range=[-max_dim/2-100, max_dim/2+100], backgroundcolor="rgb(240, 240, 245)", gridcolor="white", showbackground=True),
            yaxis=dict(nticks=4, range=[-max_dim/2-100, max_dim/2+100], backgroundcolor="rgb(245, 240, 245)", gridcolor="white", showbackground=True),
            zaxis=dict(nticks=4, range=[0, max_dim+100], backgroundcolor="rgb(245, 245, 240)", gridcolor="white", showbackground=True),
            aspectmode='data'
        ),
        margin=dict(r=0, l=0, b=0, t=0),
        scene_camera=dict(eye=dict(x=1.8, y=-1.8, z=0.8)) # Ángulo isométrico optimizado
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- ZONA DE RESULTADOS CON DESPIECE INTELIGENTE ---
    st.markdown("---")
    st.subheader("📋 Despiece Inicial Integrado")
    
    despiece = []
    
    # Tapa
    nota_tapa = f"Espesor {espesor_tapa}mm"
    despiece.append({"Pieza": "Tapa Escritorio", "Cant": 1, "Largo": largo_tapa, "Ancho": prof_tapa, "Espesor": espesor_tapa, "Material": "Tapa", "Nota": nota_tapa})
    
    # Estructura general
    w_lateral_estructura = estructura_y1 - estructura_y0
    prof_caja_apoyo = w_lateral_estructura # Por simplicidad conceptual, la caja ocupa toda la profundidad estructural
    h_estructura = total_alto - espesor_tapa - zocalo  # <--- Esta es la línea que faltaba
    # Función auxiliar para calcular despiece de Carcasa de Caja
    def despiece_carcasa_caja(pos, w, h_int, prof, espesor):
        # Piso y Techo
        despiece.append({"Pieza": f"Piso Caja {pos}", "Cant": 1, "Largo": w, "Ancho": prof, "Espesor": espesor, "Material": "Estruct", "Nota": "Carcasa"})
        despiece.append({"Pieza": f"Techo Caja {pos}", "Cant": 1, "Largo": w, "Ancho": prof, "Espesor": espesor, "Material": "Estruct", "Nota": "Carcasa"})
        # Laterales
        despiece.append({"Pieza": f"Lat Ext Caja {pos}", "Cant": 1, "Largo": h_int, "Ancho": prof, "Espesor": espesor, "Material": "Estruct", "Nota": "Carcasa"})
        despiece.append({"Pieza": f"Lat Int Caja {pos}", "Cant": 1, "Largo": h_int, "Ancho": prof, "Espesor": espesor, "Material": "Estruct", "Nota": "Carcasa"})
        # Fondo (Conceptual)
        despiece.append({"Pieza": f"Fondo Caja {pos}", "Cant": 1, "Largo": h_int, "Ancho": w, "Espesor": 3, "Material": "Fibro 3", "Nota": "Conceptual"})

    # Apoyo Izquierdo
    if t_izq == "Panel Simple":
        despiece.append({"Pieza": "Apoyo Izq (Panel)", "Cant": 1, "Largo": h_estructura, "Ancho": w_lateral_estructura, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": ""})
    elif t_izq == "Pata en 'L'":
        despiece.append({"Pieza": "Apoyo Izq (Lat. L)", "Cant": 1, "Largo": h_estructura, "Ancho": w_lateral_estructura, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": ""})
        despiece.append({"Pieza": "Apoyo Izq (Front. L)", "Cant": 1, "Largo": h_estructura, "Ancho": data_izq["ancho_l"] - espesor_estruc, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": ""})
    elif t_izq == "Módulo Caja":
        w_c = data_izq["ancho_caja"]
        despiece_carcasa_caja("Izq", w_c, h_util_caja_apoyo, prof_caja_apoyo, espesor_estruc)
        
        # INTERIOR INTELIGENTE IZQ
        conf = data_izq.get("config", {})
        w_frente_caja = w_c - (espesor_estruc * 2) - 4 # 4mm de luz total
        
        if conf.get("funcion") == "Cajonera":
            cant = conf.get("cant", 1)
            hf = (h_util_caja_apoyo - ((cant - 1) * 3)) / cant
            despiece.append({"Pieza": f"Frente Cajón Izq", "Cant": cant, "Largo": w_frente_caja, "Ancho": hf, "Espesor": espesor_estruc, "Material": "Frentes", "Nota": nota_izq})
            # (Aquí faltaría despiece interno de caja de cajón, guías, etc., igual que en V25)
            
        elif conf.get("funcion") == "Puerta":
            despiece.append({"Pieza": f"Puerta Caja Izq", "Cant": 1, "Largo": w_frente_caja, "Ancho": h_util_caja_apoyo, "Espesor": espesor_estruc, "Material": "Frentes", "Nota": nota_izq})
            din = conf.get("interior", {})
            if din.get("tipo") == "Estantes":
                despiece.append({"Pieza": f"Estante Int. Izq", "Cant": din["cant"], "Largo": w_c - (espesor_estruc * 2) - 2, "Ancho": prof_caja_apoyo - 20, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": "Móvil"})

    # Apoyo Derecho
    if t_der == "Panel Simple":
        despiece.append({"Pieza": "Apoyo Der (Panel)", "Cant": 1, "Largo": h_estructura, "Ancho": w_lateral_estructura, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": ""})
    elif t_der == "Pata en 'L'":
        despiece.append({"Pieza": "Apoyo Der (Lat. L)", "Cant": 1, "Largo": h_estructura, "Ancho": w_lateral_estructura, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": ""})
        despiece.append({"Pieza": "Apoyo Der (Front. L)", "Cant": 1, "Largo": h_estructura, "Ancho": data_der["ancho_l"] - espesor_estruc, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": ""})
    elif t_der == "Módulo Caja":
        w_c = data_der["ancho_caja"]
        despiece_carcasa_caja("Der", w_c, h_util_caja_apoyo, prof_caja_apoyo, espesor_estruc)
        
        # INTERIOR INTELIGENTE DER
        conf = data_der.get("config", {})
        w_frente_caja = w_c - (espesor_estruc * 2) - 4
        
        if conf.get("funcion") == "Cajonera":
            cant = conf.get("cant", 1)
            hf = (h_util_caja_apoyo - ((cant - 1) * 3)) / cant
            despiece.append({"Pieza": f"Frente Cajón Der", "Cant": cant, "Largo": w_frente_caja, "Ancho": hf, "Espesor": espesor_estruc, "Material": "Frentes", "Nota": nota_der})
            
        elif conf.get("funcion") == "Puerta":
            despiece.append({"Pieza": f"Puerta Caja Der", "Cant": 1, "Largo": w_frente_caja, "Ancho": h_util_caja_apoyo, "Espesor": espesor_estruc, "Material": "Frentes", "Nota": nota_der})
            din = conf.get("interior", {})
            if din.get("tipo") == "Estantes":
                despiece.append({"Pieza": f"Estante Int. Der", "Cant": din["cant"], "Largo": w_c - (espesor_estruc * 2) - 2, "Ancho": prof_caja_apoyo - 20, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": "Móvil"})

    # 4. DIBUJAR FALDÓN TRASERO (Despiece)
    largo_faldon_real = fin_faldon - inicio_faldon
    despiece.append({"Pieza": "Faldón Anti-pandeo", "Cant": 1, "Largo": largo_faldon_real, "Ancho": h_faldon, "Espesor": espesor_estruc, "Material": "Estruct", "Nota": "Trasero"})

    st.dataframe(pd.DataFrame(despiece), use_container_width=True, hide_index=True)
