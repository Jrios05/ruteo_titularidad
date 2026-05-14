import streamlit as st
import json

# Configuración de la página
st.set_page_config(page_title="Configurador de Ruteo y Titularidad", layout="wide")

# Lista de bancos extraída del documento (truncada para legibilidad, puedes agregar todos si lo deseas)
bancos_raw = """
psp_w13k323ed23dmd01,(BCP) - Banco de Crédito del Perú
psp_w13k12312341md02,(BBVA) - BBVA Continental
psp_w0328223930dmd04,(Interbank) - Banco International del Perú
psp_w191433107454,Banco de la Nación
psp_w156838159753,Yape
psp_w133203223m3md03,(Scotiabank)- Scotiabank
psp_w191268187203,Mi Banco
"""
# Procesar la lista de bancos a un diccionario
bancos = {line.split(',')[0].strip(): line.split(',')[1].strip() for line in bancos_raw.strip().split('\n') if line}


def init_session_state():
    if "custom_routing" not in st.session_state:
        st.session_state.custom_routing = {}
    if "custom_titularidad" not in st.session_state:
        st.session_state.custom_titularidad = {}


init_session_state()

st.title("⚙️ Generador de JSON: Ruteo y Titularidad")
st.markdown("Configura los parámetros para generar el JSON de habilitación.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Configuración de Ruteo")

    # Ruteo Default
    has_default_routing = st.checkbox("¿Activar Bank Transfer para todos los bancos (DEFAULT)?", value=True)
    default_channel = None
    if has_default_routing:
        default_channel = st.selectbox("Canal de dispersión DEFAULT:", ["GMONEY", "BATCH", "ALFIN"])

    st.divider()

    # Ruteo Específico
    st.subheader("Ruteo por Banco Específico")

    banco_seleccionado = st.selectbox("Seleccionar Banco:", options=list(bancos.keys()),
                                      format_func=lambda x: f"{bancos[x]} ({x})")

    # Lógica de canales según el banco
    canales_disponibles = ["GMONEY", "BATCH", "ALFIN"]
    if banco_seleccionado == "psp_w13k323ed23dmd01":  # BCP
        canales_disponibles.append("BCP")
    elif banco_seleccionado == "psp_w13k12312341md02":  # BBVA
        canales_disponibles.append("BBVA")
    elif banco_seleccionado == "psp_w156838159753":  # YAPE
        canales_disponibles.append("YAPE")

    canal_especifico = st.selectbox("Canal de dispersión:", canales_disponibles)

    if st.button("Agregar a Ruteo"):
        st.session_state.custom_routing[banco_seleccionado] = canal_especifico
        st.success(f"Agregado: {bancos[banco_seleccionado]} -> {canal_especifico}")

    if st.session_state.custom_routing:
        st.write("Bancos configurados:")
        st.json(st.session_state.custom_routing)
        if st.button("Limpiar Ruteo Específico"):
            st.session_state.custom_routing = {}
            st.rerun()

    st.divider()

    # Configuraciones Adicionales
    st.subheader("Configuraciones Adicionales")
    yape_validation = False
    validate_interbranch = st.checkbox("Solicitar ruteo para interplaca (validate_interbranch)", value=False)

    # Revisar si Yape está en el ruteo por el canal YAPE
    if st.session_state.custom_routing.get("psp_w156838159753") == "YAPE":
        st.info("Se ha detectado YAPE en el ruteo. Configura los parámetros:")
        yape_validation = True
        yape_merchant_id = st.text_input("Yape Merchant ID", value="0000")
        yape_category_code = st.text_input("Yape Category Code", value="16")

with col2:
    st.header("2. Configuración de Titularidad")

    is_routing_active = has_default_routing or len(st.session_state.custom_routing) > 0
    only_yape_by_yape = len(st.session_state.custom_routing) == 1 and st.session_state.custom_routing.get(
        "psp_w156838159753") == "YAPE" and not has_default_routing

    activar_titularidad = st.checkbox("¿Activar Titularidad?", disabled=not is_routing_active)

    if not is_routing_active:
        st.warning("Debe existir alguna configuración de ruteo para activar titularidad.")
    elif only_yape_by_yape:
        st.warning("No aplica Titularidad: Solo existe ruteo de YAPE por el canal YAPE.")
        activar_titularidad = False

    if activar_titularidad and not only_yape_by_yape:
        has_default_tit = st.checkbox("¿Configurar Titularidad DEFAULT?", value=True)
        default_tit_provider = None
        if has_default_tit:
            default_tit_provider = st.selectbox("Proveedor DEFAULT:", ["GMONEY"])

        st.subheader("Titularidad por Banco Específico")
        banco_tit_seleccionado = st.selectbox("Seleccionar Banco para Titularidad:", ["psp_w13k323ed23dmd01"],
                                              format_func=lambda x: "BCP (psp_w13k323ed23dmd01)")
        prov_tit = st.selectbox("Validador de Titularidad:", ["BCP", "GMONEY"])

        if st.button("Agregar a Titularidad"):
            st.session_state.custom_titularidad[banco_tit_seleccionado] = prov_tit
            st.success(f"Agregado Titularidad: BCP -> {prov_tit}")

        if st.session_state.custom_titularidad:
            st.write("Titularidades configuradas:")
            st.json(st.session_state.custom_titularidad)
            if st.button("Limpiar Titularidad Específica"):
                st.session_state.custom_titularidad = {}
                st.rerun()

st.divider()

# ----------------- GENERACIÓN DEL JSON -----------------
st.header("3. JSON Resultante")


def generar_json():
    resultado = {}

    # Construir Ruteo
    routing = {}
    if has_default_routing:
        routing["DEFAULT"] = default_channel

    for banco, canal in st.session_state.custom_routing.items():
        routing[banco] = canal

    if routing:
        resultado["routing"] = routing

    # Construir configuraciones extras
    if yape_validation:
        resultado["yape_validation"] = True
        resultado["yape_configuration"] = {
            "yape_merchant_id": yape_merchant_id,
            "yape_category_code": yape_category_code
        }

    if validate_interbranch:
        resultado["validate_interbranch"] = True

    # Construir Titularidad
    if activar_titularidad and not only_yape_by_yape:
        provider = {}
        if has_default_tit:
            provider["DEFAULT"] = default_tit_provider

        for banco, prov in st.session_state.custom_titularidad.items():
            provider[banco] = prov

        resultado["account_holder"] = {
            "provider": provider,
            "validate": True,
            "audit_mode": False,
            "validate_cci": True,
            "validate_wallet": True,
            "validate_account": True
        }

    # Validar ALFIN
    alfin_in_default = (default_channel == "ALFIN" and has_default_routing)
    alfin_in_custom = any(canal == "ALFIN" for canal in st.session_state.custom_routing.values())
    if alfin_in_default or alfin_in_custom:
        resultado["alfin_v3_enabled"] = True

    return resultado


json_final = generar_json()
st.json(json_final)

# Botón para descargar el JSON
json_string = json.dumps(json_final, indent=4)
st.download_button(
    label="Descargar JSON",
    file_name="configuracion_ruteo.json",
    mime="application/json",
    data=json_string
)