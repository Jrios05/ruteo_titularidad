import streamlit as st
import json

# Configuración de la página
st.set_page_config(page_title="Configurador de Ruteo y Titularidad", layout="wide")

# 1. Definición de los bancos principales (Ajuste solicitado)
# Mantenemos el PSP internamente para el JSON, pero solo mostraremos el Nombre en la UI
bancos_principales = {
    "psp_w0328223930dmd04": "(Interbank) - Banco International del Perú",
    "psp_w191433107454": "Banco de la Nación",
    "psp_w133203223m3md03": "(Scotiabank)- Scotiabank",
    "psp_w156838159753": "Yape",
    "psp_w13k323ed23dmd01": "(BCP) - Banco de Crédito del Perú",
    "psp_w13k12312341md02": "(BBVA) - BBVA Continental"
}


def init_session_state():
    if "custom_routing" not in st.session_state:
        st.session_state.custom_routing = {}
    if "custom_titularidad" not in st.session_state:
        st.session_state.custom_titularidad = {}


init_session_state()

st.title("⚙️ Ruteo y Titularidad")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Configuración de Ruteo")

    # Ruteo Default
    has_default_routing = st.checkbox("¿Activar Bank Transfer para todos los bancos?", value=True)
    default_channel = None
    if has_default_routing:
        default_channel = st.selectbox("Canal de dispersión por defecto:", ["GMONEY", "BATCH", "ALFIN"])

    st.divider()

    # Ruteo Específico
    st.subheader("Ruteo por Banco Específico")

    # 2. Ajuste: Solo mostrar el nombre del banco en el desplegable
    banco_id_seleccionado = st.selectbox(
        "Seleccionar Banco:",
        options=list(bancos_principales.keys()),
        format_func=lambda x: bancos_principales[x]
    )

    # Lógica de canales según el banco
    canales_disponibles = ["GMONEY", "BATCH", "ALFIN"]
    if banco_id_seleccionado == "psp_w13k323ed23dmd01":  # BCP
        canales_disponibles.append("BCP")
    elif banco_id_seleccionado == "psp_w13k12312341md02":  # BBVA
        canales_disponibles.append("BBVA")
    elif banco_id_seleccionado == "psp_w156838159753":  # YAPE
        canales_disponibles.append("YAPE")

    canal_especifico = st.selectbox("Canal de dispersión:", canales_disponibles)

    if st.button("Agregar a Ruteo"):
        st.session_state.custom_routing[banco_id_seleccionado] = canal_especifico
        st.success(f"Agregado: {bancos_principales[banco_id_seleccionado]} -> {canal_especifico}")

    if st.session_state.custom_routing:
        # Mostramos una lista amigable de lo configurado
        st.write("Configuración actual:")
        for k, v in st.session_state.custom_routing.items():
            st.text(f"• {bancos_principales[k]}: {v}")
        if st.button("Limpiar Ruteo Específico"):
            st.session_state.custom_routing = {}
            st.rerun()

    st.divider()

    # Configuraciones Adicionales
    st.subheader("Configuraciones Adicionales")
    yape_validation = False
    validate_interbranch = st.checkbox("Ruteo para interplaza (BATCH)", value=False)

    if st.session_state.custom_routing.get("psp_w156838159753") == "YAPE":
        st.info("Configuración de parámetros YAPE:")
        yape_validation = True
        yape_merchant_id = st.text_input("Yape Merchant ID", value="0000")
        yape_category_code = st.text_input("Yape Category Code", value="16")

with col2:
    st.header("2. Configuración de Titularidad")

    is_routing_active = has_default_routing or len(st.session_state.custom_routing) > 0
    only_yape_by_yape = (len(st.session_state.custom_routing) == 1 and
                         st.session_state.custom_routing.get("psp_w156838159753") == "YAPE" and
                         not has_default_routing)

    activar_titularidad = st.checkbox("¿Activar Titularidad?", disabled=not is_routing_active)

    if activar_titularidad and not only_yape_by_yape:
        has_default_tit = st.checkbox("¿Configurar Titularidad para todos los bancos?", value=True)
        default_tit_provider = None
        if has_default_tit:
            default_tit_provider = st.selectbox("Proveedor por defecto:", ["GMONEY"])

        st.subheader("Titularidad Específica")
        # Solo para BCP según el documento
        prov_tit = st.selectbox("Validador para BCP:", ["BCP", "GMONEY"])

        if st.button("Agregar Titularidad BCP"):
            st.session_state.custom_titularidad["psp_w13k323ed23dmd01"] = prov_tit
            st.success(f"Configurado: BCP -> {prov_tit}")

st.divider()

# ----------------- 3. GENERACIÓN Y VISUALIZACIÓN DEL JSON (Ajuste solicitado) -----------------
st.header("3. JSON Resultante")


def generar_json():
    resultado = {}

    # Ruteo
    routing = {}
    if has_default_routing:
        routing["DEFAULT"] = default_channel
    for psp, canal in st.session_state.custom_routing.items():
        routing[psp] = canal
    if routing:
        resultado["routing"] = routing

    # Yape
    if yape_validation:
        resultado["yape_validation"] = True
        resultado["yape_configuration"] = {
            "yape_merchant_id": yape_merchant_id,
            "yape_category_code": yape_category_code
        }

    # Interbranch
    if validate_interbranch:
        resultado["validate_interbranch"] = True

    # Titularidad
    if activar_titularidad and not only_yape_by_yape:
        provider = {}
        if has_default_tit:
            provider["DEFAULT"] = default_tit_provider
        for psp, prov in st.session_state.custom_titularidad.items():
            provider[psp] = prov

        resultado["account_holder"] = {
            "provider": provider,
            "validate": True,
            "audit_mode": False,
            "validate_cci": True,
            "validate_wallet": True,
            "validate_account": True
        }

    # ALFIN check
    if (default_channel == "ALFIN" and has_default_routing) or any(
            c == "ALFIN" for c in st.session_state.custom_routing.values()):
        resultado["alfin_v3_enabled"] = True

    return resultado


json_final = generar_json()
json_string = json.dumps(json_final, indent=4, ensure_ascii=False)

# Uso de st.code para permitir la copia fácil y ver las comas/formato real
st.code(json_string, language='json')

st.download_button(
    label="Descargar archivo .json",
    file_name="configuracion_ruteo.json",
    mime="application/json",
    data=json_string
)