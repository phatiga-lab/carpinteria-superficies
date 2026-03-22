import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import math

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(page_title="CarpinterIA Superficies V0.6", page_icon="🪑", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding-top: 2rem; }
    .stNumberInput, .stSelectbox, .stSlider { margin-bottom: -10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding-top: 10px; padding-bottom: 10px; border-radius: 4px 4px 0 0; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# HELPERS LOGICOS
# ==============================================================================
def get_limit_cajones(h_util):
    return max(1, int(h_util / 75)) if h_util > 70 else 1

def ui_config_caja(key_prefix, h_util_caja):
    st.caption("🔧 Configuración Interna")
    funcion = st.radio("Función", ["Cajonera", "Puerta"], key=f"{key_prefix}_func", horizontal=True)
    d = {"funcion": funcion}
    
    if funcion == "Cajonera":
        mc = get_limit_cajones(h_util_caja)
        val_sug = min(3 if "izq" in key_prefix else 2, mc)
        d["cant"] = st.number_input("Cantidad Cajones", 1, mc, val_sug, key=f"{key_prefix}_q_caj")
    elif funcion == "Puerta":
        t = st.radio("Tipo Interior", ["Vacío", "Estantes"], horizontal=True, key=f"{key_prefix}_t_int")
        d_int = {}
        if t == "Estantes": 
            d_int = {"tipo": "Estantes", "cant": st.number_input("Cant.", 1, 10, 2, key=f"{key_prefix}_e")}
        d["interior"] = d_int
    return d

# ==============================================================================
# 1. BARRA LATERAL (AJUSTES DE MATERIAL Y COSTOS)
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063080.png", width=60)
    st.title("CarpinterIA")
    st.caption("v0.6 - Colisiones y Cantos")
    st.divider()

    with st.expander("🪵 1. Materiales y Espesores", expanded=True):
        espesor_tapa = st.selectbox("Espesor Tapa (mm)", [15, 18, 25, 36, 38], index=1)
        espesor_estruc = st.selectbox("Espesor Estructura", [15, 18, 25], index=1)
        tipo_canto = st.selectbox("Tipo de Canto", ["Melamínico 0.45mm", "PVC 0.45mm", "PVC 2mm ABS"], index=1)
        zocalo = st.number_input("Altura Patines (mm)", value=10, step=5)
        veta_frentes = st.radio("Veta Frentes", ["↔️ Horizontal", "↕️ Vertical"], index=0)
    
    with st.expander("🔩 2. Herrajes Estándar", expanded=False):
        tipo_corredera = st.selectbox("Correderas Cajón/Bandeja", ["Telescópicas", "Comunes (Z)", "Push / Tip-On"])
        es_push = "Push" in tipo_corredera
        descuento_guia = 26 if ("Telescópicas" in tipo_corredera or es_push) else 25
        costo_guia_ref = 6500 if ("Telescópicas" in tipo_corredera or es_push) else 2500
        tipo_bisagra = st.selectbox("Bisagras Lateral", ["Codo 0 (Ext)", "Codo 9 (Media)", "Codo 18 (Int)", "Push"])

    with st.expander("💲 3. Costos y Precios", expanded=False):
        precio_placa = st.number_input("Placa Melamina ($)", value=85000, step=1000)
        precio_fondo = st.number_input("Placa Fondo ($)", value=25000, step=1000)
        precio_canto = st.number_input(f"Metro Canto {tipo_canto[:3]} ($)", value=800, step=50)
        c_bis = st.number_input("Bisagra ($)", value=2500, step=100)
        c_guia = st.number_input("Par Guías ($)", value=costo_guia_ref, step=500)
        margen = st.number_input("Ganancia (Multiplicador)", value=2.5, step=0.1)

configuracion_apoyos = {}

# ==============================================================================
# LAYOUT PRINCIPAL A DOS COLUMNAS
# ==============================================================================
col_controles, col_visual = st.columns([1.1, 1.9], gap="large")

# ------------------------------------------------------------------------------
# ZONA IZQUIERDA: CONTROLES Y DISEÑO DE ESCRITORIO
# ------------------------------------------------------------------------------
with col_controles:
    st.header("📐 Diseño de Escritorio")
    
    with st.container(border=True):
        st.subheader("1. La Tapa y Altura")
        c_dim1, c_dim2, c_dim3 = st.columns(3)
        largo_tapa = c_dim1.number_input("Largo Total (mm)", value=1500, min_value=600, step=10)
        prof_tapa = c_dim2.number_input("Prof. Total (mm)", value=700, min_value=400, step=10)
        total_alto = c_dim3.number_input("Alto Final (mm)", value=750, min_value=500, max_value=1200, step=10)
        
        st.divider()
        st.caption("📏 Vuelos (Overhang)")
        c_v1, c_v2, c_v3, c_v4 = st.columns(4)
        vuelo_frontal = c_v1.number_input("V. Frontal", value=50, step=5)
        vuelo_trasero = c_v2.number_input("V. Trasero", value=20, step=5)
        vuelo_izq = c_v3.number_input("V. Izq", value=10, step=5)
        vuelo_der = c_v4.number_input("V. Der", value=10, step=5)

    st.subheader("2. Estructura y Apoyos")
    
    estructura_prof = prof_tapa - vuelo_frontal - vuelo_trasero
    h_util_caja_apoyo = total_alto - espesor_tapa - zocalo - (espesor_estruc * 2)
    h_estructura = total_alto - espesor_tapa - zocalo 

    c_p1, c_p2 = st.columns(2)
    with c_p1.container(border=True):
        st.markdown("⬅️ **Apoyo Izquierdo**")
        tipo_izq = st.selectbox("Tipo", ["Panel Simple", "Pata en 'L'", "Módulo Caja"], key="t_izq", label_visibility="collapsed")
        data_izq = {"tipo": tipo_izq}
        if tipo_izq == "Pata en 'L'": data_izq["ancho_l"] = st.number_input("Ancho L Frontal", 150, step=10, key="w_l_izq")
        elif tipo_izq == "Módulo Caja":
            data_izq["ancho_caja"] = st.number_input("Ancho Caja", 400, step=10, key="w_c_izq")
            data_izq["config"] = ui_config_caja("izq", h_util_caja_apoyo)
        configuracion_apoyos["izq"] = data_izq

    with c_p2.container(border=True):
        st.markdown("➡️ **Apoyo Derecho**")
        tipo_der = st.selectbox("Tipo", ["Panel Simple", "Pata en 'L'", "Módulo Caja"], key="t_der", label_visibility="collapsed")
        data_der = {"tipo": tipo_der}
        if tipo_der == "Pata en 'L'": data_der["ancho_l"] = st.number_input("Ancho L Frontal", 150, step=10, key="w_l_der")
        elif tipo_der == "Módulo Caja":
            data_der["ancho_caja"] = st.number_input("Ancho Caja", 400, step=10, key="w_c_der")
            data_der["config"] = ui_config_caja("der", h_util_caja_apoyo)
        configuracion_apoyos["der"] = data_der

    with st.container(border=True):
        st.markdown("🧱 **Accesorios y Faldón**")
        
        # LOGICA DE BANDEJA TECLADO
        st.markdown("**Bandeja Portateclado**")
        pata_L_presente = (tipo_izq == "Pata en 'L'" or tipo_der == "Pata en 'L'")
        
        if pata_L_presente:
            st.warning("⚠️ La bandeja no es compatible con Patas en 'L' porque chocan con las correderas.")
            tiene_bandeja = False
        else:
            tiene_bandeja = st.toggle("Agregar bandeja retráctil bajo la tapa", value=False)
            
        st.divider()
        c_f1, c_f2 = st.columns([2, 1])
        h_faldon = c_f1.slider("Altura Faldón Trasero (mm)", 150, int(h_estructura), 300, step=10)
        
        # CÁLCULO DE LÍMITE FÍSICO DE COLISIÓN (REMETIDO)
        max_remetido_base = int(prof_tapa / 2) # Como máximo hasta la mitad de la tapa
        
        if tiene_bandeja:
            # estructura_prof es el espacio total de las patas.
            # 350mm bandeja + 20mm luz seguridad
            max_remetido_bandeja = int(estructura_prof - 370)
            max_remetido_permitido = min(max_remetido_base, max_remetido_bandeja)
            
            if max_remetido_permitido < 0:
                st.error("❌ El escritorio es muy poco profundo para acomodar bandeja y faldón. Achique vuelos o aumente profundidad.")
                max_remetido_permitido = 0
        else:
            max_remetido_permitido = max_remetido_base
            
        remetido_faldon = c_f2.number_input("Remetido (mm)", min_value=0, max_value=max_remetido_permitido, value=min(50, max_remetido_permitido), step=10, help="El sistema restringe automáticamente este valor para evitar colisiones.")

# ------------------------------------------------------------------------------
# ZONA DERECHA: VISUALIZADOR 3D
# ------------------------------------------------------------------------------
with col_visual:
    st.header("👁️ Vista Previa 3D")
    
    tapa_x0 = -largo_tapa / 2; tapa_x1 = largo_tapa / 2
    tapa_y0 = -prof_tapa / 2; tapa_y1 = prof_tapa / 2
    estructura_x0 = tapa_x0 + vuelo_izq; estructura_x1 = tapa_x1 - vuelo_der
    estructura_y0 = tapa_y0 + vuelo_frontal; estructura_y1 = tapa_y1 - vuelo_trasero
    
    fig = go.Figure()
    
    color_tapa = "#DEB887"; color_estructura = "#A0522D" 
    color_caja_carcasa = "#8B4513"; color_caja_frente = "#AED6F1"
    
    def dibujar_placa(x0, x1, y0, y1, z0, z1, color, nombre, opacidad=1):
        fig.add_trace(go.Mesh3d(x=[x0,x1,x1,x0,x0,x1,x1,x0], y=[y0,y0,y1,y1,y0,y0,y1,y1], z=[z0,z0,z0,z0,z1,z1,z1,z1],
            i=[7,0,0,0,4,4,3,3,7,2,6,6], j=[3,4,1,2,5,6,2,3,6,7,1,2], k=[0,7,2,3,6,7,1,0,2,5,5,1],
            opacity=opacidad, color=color, flatshading=True, name=nombre))

    # Tapa
    dibujar_placa(tapa_x0, tapa_x1, tapa_y0, tapa_y1, total_alto-espesor_tapa, total_alto, color_tapa, "Tapa")

    def interior_conceptual(x0, x1, y0, y1, z_base, h_util, config):
        func = config.get("funcion")
        if func == "Cajonera":
            cant = config.get("cant", 1); hu_frente = h_util / cant
            for k in range(cant):
                z_f_0 = z_base + (k * hu_frente) + 2; z_f_1 = z_base + ((k+1) * hu_frente) - 2
                dibujar_placa(x0, x1, y0-2, y0+5, z_f_0, z_f_1, color_caja_frente, f"Frente Caj C{k+1}", 0.7)
        elif func == "Puerta":
            dibujar_placa(x0, x1, y0-2, y0+5, z_base+2, z_base+h_util-2, color_caja_frente, "Frente Puerta", 0.7)
            din = config.get("interior", {})
            if din.get("tipo") == "Estantes":
                cant_e = din.get("cant", 1); p = h_util / (cant_e + 1)
                for k in range(cant_e):
                    y_e = z_base + (p * (k+1))
                    fig.add_shape(type="line", x0=x0+5, y0=y0+10, x1=x1-5, y1=y1-10, xref="x", yref="y")
                    dibujar_placa(x0+5, x1-5, y0+10, y1-10, y_e, y_e+espesor_estruc, color_estructura, f"Estante {k+1}", 0.5) 

    # Izq
    if tipo_izq == "Panel Simple": dibujar_placa(estructura_x0, estructura_x0 + espesor_estruc, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "Lat Izq")
    elif tipo_izq == "Pata en 'L'":
        dibujar_placa(estructura_x0, estructura_x0 + espesor_estruc, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "L-Lat Izq")
        dibujar_placa(estructura_x0 + espesor_estruc, estructura_x0 + data_izq["ancho_l"], estructura_y0, estructura_y0 + espesor_estruc, zocalo, total_alto-espesor_tapa, color_estructura, "L-Front Izq")
    elif tipo_izq == "Módulo Caja":
        w_c = data_izq["ancho_caja"]
        dibujar_placa(estructura_x0, estructura_x0 + w_c, estructura_y0, estructura_y1, zocalo, zocalo + espesor_estruc, color_caja_carcasa, "Piso Izq")
        dibujar_placa(estructura_x0, estructura_x0 + w_c, estructura_y0, estructura_y1, total_alto-espesor_tapa-espesor_estruc, total_alto-espesor_tapa, color_caja_carcasa, "Techo Izq")
        dibujar_placa(estructura_x0, estructura_x0 + espesor_estruc, estructura_y0, estructura_y1, zocalo + espesor_estruc, total_alto-espesor_tapa-espesor_estruc, color_caja_carcasa, "Lat Ext Izq")
        dibujar_placa(estructura_x0 + w_c - espesor_estruc, estructura_x0 + w_c, estructura_y0, estructura_y1, zocalo + espesor_estruc, total_alto-espesor_tapa-espesor_estruc, color_caja_carcasa, "Lat Int Izq")
        interior_conceptual(estructura_x0 + espesor_estruc, estructura_x0 + w_c - espesor_estruc, estructura_y0, estructura_y1, zocalo + espesor_estruc, h_util_caja_apoyo, data_izq.get("config", {}))

    # Der
    if tipo_der == "Panel Simple": dibujar_placa(estructura_x1 - espesor_estruc, estructura_x1, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "Lat Der")
    elif tipo_der == "Pata en 'L'":
        dibujar_placa(estructura_x1 - espesor_estruc, estructura_x1, estructura_y0, estructura_y1, zocalo, total_alto-espesor_tapa, color_estructura, "L-Lat Der")
        dibujar_placa(estructura_x1 - data_der["ancho_l"], estructura_x1 - espesor_estruc, estructura_y0, estructura_y0 + espesor_estruc, zocalo, total_alto-espesor_tapa, color_estructura, "L-Front Der")
    elif tipo_der == "Módulo Caja":
        w_c = data_der["ancho_caja"]
        dibujar_placa(estructura_x1 - w_c, estructura_x1, estructura_y0, estructura_y1, zocalo, zocalo + espesor_estruc, color_caja_carcasa, "Piso Der")
        dibujar_placa(estructura_x1 - w_c, estructura_x1, estructura_y0, estructura_y1, total_alto-espesor_tapa-espesor_estruc, total_alto-espesor_tapa, color_caja_carcasa, "Techo Der")
        dibujar_placa(estructura_x1 - w_c, estructura_x1 - w_c + espesor_estruc, estructura_y0, estructura_y1, zocalo + espesor_estruc, total_alto-espesor_tapa-espesor_estruc, color_caja_carcasa, "Lat Int Der")
        dibujar_placa(estructura_x1 - espesor_estruc, estructura_x1, estructura_y0, estructura_y1, zocalo + espesor_estruc, total_alto-espesor_tapa-espesor_estruc, color_caja_carcasa, "Lat Ext Der")
        interior_conceptual(estructura_x1 - w_c + espesor_estruc, estructura_x1 - espesor_estruc, estructura_y0, estructura_y1, zocalo + espesor_estruc, h_util_caja_apoyo, data_der.get("config", {}))

    # Faldón y Espacios
    y_faldon_trasero = estructura_y1 - remetido_faldon
    inicio_faldon = estructura_x0 + (espesor_estruc if tipo_izq != "Módulo Caja" else data_izq["ancho_caja"])
    fin_faldon = estructura_x1 - (espesor_estruc if tipo_der != "Módulo Caja" else data_der["ancho_caja"])
    dibujar_placa(inicio_faldon, fin_faldon, y_faldon_trasero - espesor_estruc, y_faldon_trasero, total_alto-espesor_tapa-h_faldon, total_alto-espesor_tapa, color_estructura, "Faldón")

    # Bandeja 3D
    if tiene_bandeja:
        z_bandeja = total_alto - espesor_tapa - 60 
        dibujar_placa(inicio_faldon + 20, fin_faldon - 20, estructura_y0, estructura_y0 + 350, z_bandeja, z_bandeja + espesor_tapa, color_tapa, "Bandeja")

    max_dim = max(largo_tapa, total_alto)
    fig.update_layout(
        scene=dict(
            xaxis=dict(nticks=4, range=[-max_dim/2-100, max_dim/2+100], backgroundcolor="rgb(240, 240, 245)", gridcolor="white", showbackground=True),
            yaxis=dict(nticks=4, range=[-max_dim/2-100, max_dim/2+100], backgroundcolor="rgb(245, 240, 245)", gridcolor="white", showbackground=True),
            zaxis=dict(nticks=4, range=[0, max_dim+100], backgroundcolor="rgb(245, 245, 240)", gridcolor="white", showbackground=True),
            aspectmode='data'
        ),
        margin=dict(r=0, l=0, b=0, t=0), scene_camera=dict(eye=dict(x=1.5, y=-1.5, z=0.8))
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ------------------------------------------------------------------------------
    # MOTOR DE CÁLCULO E INSUMOS (CANTOS 3L CORREGIDO)
    # ------------------------------------------------------------------------------
    st.markdown("---")
    
    pz = []; buy = []
    
    def add_p(nombre, cant, largo, ancho, espesor, mat, nota=""):
        canto = "-"
        # Tapa, Frentes, Puertas y Bandeja llevan cantos en todo su perímetro
        if any(palabra in nombre for palabra in ["Tapa", "Frente", "Puerta", "Bandeja"]): 
            canto = "4L"
        # Patas, Laterales y Apoyos apoyan en tapa (1 lado ciego) -> 3 lados cantos
        elif any(palabra in nombre for palabra in ["Apoyo", "Lat "]): 
            canto = "3L"
        # Estantes, pisos y faldón solo el frente visible
        elif any(palabra in nombre for palabra in ["Piso", "Techo", "Estante", "Faldón"]): 
            canto = "1L"
            
        pz.append({"Pieza": nombre, "Cant": cant, "Largo": largo, "Ancho": ancho, "Espesor": espesor, "Mat": mat, "Cantos": canto, "Nota": nota})

    # Tapa
    add_p("Tapa Escritorio", 1, largo_tapa, prof_tapa, espesor_tapa, "Tapa", f"Espesor {espesor_tapa}mm")

    w_lateral_estructura = estructura_y1 - estructura_y0
    prof_caja_apoyo = w_lateral_estructura 

    def despiece_carcasa_caja(pos, w, h_int, prof, espesor):
        add_p(f"Piso Caja {pos}", 1, w, prof, espesor, "Estruct", "Carcasa")
        add_p(f"Techo Caja {pos}", 1, w, prof, espesor, "Estruct", "Carcasa")
        add_p(f"Lat Ext Caja {pos}", 1, h_int, prof, espesor, "Estruct", "Carcasa")
        add_p(f"Lat Int Caja {pos}", 1, h_int, prof, espesor, "Estruct", "Carcasa")
        pz.append({"Pieza": f"Fondo Caja {pos}", "Cant": 1, "Largo": h_int, "Ancho": w, "Espesor": 3, "Mat": "Fibro 3", "Cantos": "-", "Nota": "Carcasa"})

    def calcular_interior(pos, w_c, conf):
        w_frente_caja = w_c - (espesor_estruc * 2) - 4
        if conf.get("funcion") == "Cajonera":
            cant = conf.get("cant", 1)
            hf = (h_util_caja_apoyo - ((cant - 1) * 3)) / cant
            add_p(f"Frente Cajón {pos}", cant, w_frente_caja, hf, espesor_estruc, "Frentes", "")
            
            l_guia = min(500, max(250, int((prof_caja_apoyo - 15) // 50) * 50))
            buy.append({"Item": f"Guías {tipo_corredera} {l_guia}mm", "Cant": cant, "Unidad": "par", "Costo": c_guia})
            
        elif conf.get("funcion") == "Puerta":
            add_p(f"Puerta Caja {pos}", 1, w_frente_caja, h_util_caja_apoyo, espesor_estruc, "Frentes", "")
            buy.append({"Item": f"Bisagras {tipo_bisagra}", "Cant": 2, "Unidad": "u.", "Costo": c_bis})
            
            din = conf.get("interior", {})
            if din.get("tipo") == "Estantes":
                add_p(f"Estante Int. {pos}", din["cant"], w_c - (espesor_estruc * 2) - 2, prof_caja_apoyo - 20, espesor_estruc, "Estruct", "Móvil")

    # Procesar Izq
    if tipo_izq == "Panel Simple": add_p("Apoyo Izq (Panel)", 1, h_estructura, w_lateral_estructura, espesor_estruc, "Estruct")
    elif tipo_izq == "Pata en 'L'":
        add_p("Apoyo Izq (Lat. L)", 1, h_estructura, w_lateral_estructura, espesor_estruc, "Estruct")
        add_p("Apoyo Izq (Front. L)", 1, h_estructura, data_izq["ancho_l"] - espesor_estruc, espesor_estruc, "Estruct")
    elif tipo_izq == "Módulo Caja":
        despiece_carcasa_caja("Izq", data_izq["ancho_caja"], h_util_caja_apoyo, prof_caja_apoyo, espesor_estruc)
        calcular_interior("Izq", data_izq["ancho_caja"], data_izq.get("config", {}))

    # Procesar Der
    if tipo_der == "Panel Simple": add_p("Apoyo Der (Panel)", 1, h_estructura, w_lateral_estructura, espesor_estruc, "Estruct")
    elif tipo_der == "Pata en 'L'":
        add_p("Apoyo Der (Lat. L)", 1, h_estructura, w_lateral_estructura, espesor_estruc, "Estruct")
        add_p("Apoyo Der (Front. L)", 1, h_estructura, data_der["ancho_l"] - espesor_estruc, espesor_estruc, "Estruct")
    elif tipo_der == "Módulo Caja":
        despiece_carcasa_caja("Der", data_der["ancho_caja"], h_util_caja_apoyo, prof_caja_apoyo, espesor_estruc)
        calcular_interior("Der", data_der["ancho_caja"], data_der.get("config", {}))

    # Faldón
    largo_interior_libre = fin_faldon - inicio_faldon
    add_p("Faldón Anti-pandeo", 1, largo_interior_libre, h_faldon, espesor_estruc, "Estruct", "Trasero")

    # Bandeja
    if tiene_bandeja:
        w_bandeja = largo_interior_libre - (descuento_guia * 2)
        add_p("Bandeja Teclado", 1, w_bandeja, 350, espesor_tapa, "Tapa", "Bandeja")
        buy.append({"Item": f"Guías {tipo_corredera} 350mm (Teclado)", "Cant": 1, "Unidad": "par", "Costo": c_guia})

    # Insumos Generales
    buy.insert(0, {"Item": "Tornillos 4x50 / Minifix", "Cant": len(pz)*4, "Unidad": "u.", "Costo": 15})
    
    # Cálculo aprox de metros de tapacanto con lógica 3L
    m_canto_mm = 0
    for p in pz:
        if p["Cantos"] == "4L":
            m_canto_mm += (p["Largo"]*2 + p["Ancho"]*2) * p["Cant"]
        elif p["Cantos"] == "3L":
            m_canto_mm += (p["Largo"]*2 + p["Ancho"]) * p["Cant"] # 2 filos largos (verticales) y 1 corto (apoyo piso)
        elif p["Cantos"] == "1L":
            m_canto_mm += p["Largo"] * p["Cant"]
            
    buy.append({"Item": f"Canto {tipo_canto}", "Cant": math.ceil((m_canto_mm/1000)*1.2), "Unidad": "m", "Costo": precio_canto})

    # TABS DE RESULTADOS
    t1, t2, t3 = st.tabs(["📝 Despiece y Cantos", "🔩 Herrajes", "💰 Presupuesto"])
    with t1: 
        df = pd.DataFrame(pz)
        st.dataframe(df.style.format({"Largo": "{:.0f}", "Ancho": "{:.0f}"}), use_container_width=True, hide_index=True)
        st.download_button("📥 Exportar CSV", df.to_csv(index=False).encode(), "corte_escritorio.csv")
    with t2: 
        st.dataframe(pd.DataFrame(buy).groupby(["Item","Unidad"], as_index=False).sum(), use_container_width=True, hide_index=True)
    with t3: 
        placas = math.ceil((sum([p["Largo"]*p["Ancho"]*p["Cant"] for p in pz if p["Mat"]!="Fibro 3"])/1e6*1.3)/4.75)
        c_mat = (placas * precio_placa)
        c_herr = sum([c["Costo"]*c["Cant"] for c in buy])
        st.write(f"- Melamina base (estructura/tapa): ~{placas} placas (${c_mat:,.0f})")
        st.write(f"- Total Insumos (Herrajes/Cantos): ${c_herr:,.0f}")
        st.metric("PRECIO SUGERIDO VENTA", f"${(c_mat + c_herr) * margen:,.0f}")
