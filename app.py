import streamlit as st
import json
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Configurador de Ruteo y Titularidad", layout="wide")

# =====================================================================
# 1. REPOSITORIOS DE DATOS
# =====================================================================

bancos_principales = {
    "psp_w13k323ed23dmd01": "(BCP) - Banco de Crédito del Perú",
    "psp_w13k12312341md02": "(BBVA) - BBVA Continental",
    "psp_w0328223930dmd04": "(Interbank) - Banco International del Perú",
    "psp_w191433107454": "Banco de la Nación",
    "psp_w133203223m3md03": "(Scotiabank)- Scotiabank"
}

billeteras_principales = {
    "psp_w156838159753": "Yape",
    "psp_3e74133b10bb44e6bd81": "PLIN",
    "psp_c6bee88b7b7e49bab8d4": "BIM",
    "psp_258a4fc095414c3b9c44": "LIGO",
    "psp_3f7ac8c5a4c8433288bd": "DALE",
    "psp_12f35441df4e426991e9": "PREXPE",
    "psp_28ed3cdabcbe49b098ee": "OH!"
}

todos_los_psps_dict = {**bancos_principales, **billeteras_principales}

psps_titularidad_habilitados = {
    "psp_w13k323ed23dmd01": "(BCP) - Banco de Crédito del Perú",
    **billeteras_principales
}


def init_session_state():
    if "custom_routing" not in st.session_state:
        st.session_state.custom_routing = {}
    if "custom_titularidad" not in st.session_state:
        st.session_state.custom_titularidad = {}


init_session_state()

st.title("⚙️ Ruteo y Titularidad")

col1, col2 = st.columns(2)

# =====================================================================
# COLUMNA 1: RUTEO
# =====================================================================
with col1:
    st.header("1. Configuración de Ruteo")

    # --- 1.1 SECCIÓN BANK TRANSFER ---
    with st.expander("1.1 Bank Transfer", expanded=True):
        st.subheader("Ruteo Global (Bancos)")
        has_default_routing_bancos = st.checkbox("Activar canal de ruteo por defecto", value=True, key="chk_def_bank")
        default_channel_bancos = None
        if has_default_routing_bancos:
            default_channel_bancos = st.selectbox("Canal por defecto:", ["GMONEY", "BATCH", "ALFIN"],
                                                  key="sel_def_bank")

        st.markdown("---")
        st.subheader("Ruteo Específico (Bancos)")
        banco_id = st.selectbox(
            "Seleccionar Banco:",
            options=list(bancos_principales.keys()),
            format_func=lambda x: bancos_principales[x],
            key="sel_spec_bank"
        )

        canales_bancos = ["GMONEY", "BATCH", "ALFIN"]
        if banco_id == "psp_w13k323ed23dmd01":
            canales_bancos.append("BCP")
        elif banco_id == "psp_w13k12312341md02":
            canales_bancos.append("BBVA")

        canal_bank_spec = st.selectbox("Canal de dispersión:", canales_bancos, key="sel_ch_bank")
        if st.button("Agregar Excepción de Banco", key="btn_add_bank"):
            st.session_state.custom_routing[banco_id] = canal_bank_spec

    # --- 1.2 SECCIÓN BILLETERAS ---
    with st.expander("1.2 Billeteras", expanded=True):
        st.subheader("Ruteo Global (Billeteras)")
        has_default_routing_billeteras = st.checkbox("Activar canal de ruteo por defecto", value=False,
                                                     key="chk_def_wall")
        default_channel_billeteras = None
        if has_default_routing_billeteras:
            default_channel_billeteras = st.selectbox("Canal por defecto:", ["GMONEY"], key="sel_def_wall")

        st.markdown("---")
        st.subheader("Ruteo Específico (Solo Billeteras)")
        wallet_id = st.selectbox(
            "Seleccionar Billetera:",
            options=list(billeteras_principales.keys()),
            format_func=lambda x: billeteras_principales[x],
            key="sel_spec_wall"
        )

        canales_billeteras = ["GMONEY"]
        if wallet_id == "psp_w156838159753":  # YAPE
            canales_billeteras.append("YAPE")

        canal_wall_spec = st.selectbox("Canal de dispersión:", canales_billeteras, key="sel_ch_wall")
        if st.button("Agregar Excepción de Billetera", key="btn_add_wall"):
            st.session_state.custom_routing[wallet_id] = canal_wall_spec

    if st.button("Limpiar Todo el Ruteo Específico"):
        st.session_state.custom_routing = {}
        st.rerun()

    st.divider()
    st.subheader("Configuraciones Adicionales")
    validate_interbranch = st.checkbox("Solicitar ruteo para interplaza (BATCH)", value=False)

    yape_validation = False
    if st.session_state.custom_routing.get("psp_w156838159753") == "YAPE":
        yape_validation = True
        yape_merchant_id = st.text_input("Yape Merchant ID", value="0000")
        yape_category_code = st.text_input("Yape Category Code", value="16")

# =====================================================================
# COLUMNA 2: TITULARIDAD
# =====================================================================
with col2:
    st.header("2. Configuración de Titularidad")

    is_routing_active = has_default_routing_bancos or has_default_routing_billeteras or len(
        st.session_state.custom_routing) > 0
    activar_titularidad = st.checkbox("¿Activar Titularidad?", disabled=not is_routing_active)

    if activar_titularidad:
        # --- 2.1 TITULARIDAD GLOBAL ---
        with st.expander("2.1 Configuración Global de Titularidad", expanded=True):
            has_default_tit = st.checkbox("Activar proveedor por defecto", value=True)
            default_tit_provider = None
            if has_default_tit:
                default_tit_provider = st.selectbox("Proveedor por defecto:", ["GMONEY"])

        # --- 2.2 TITULARIDAD ESPECÍFICA ---
        with st.expander("2.2 Titularidad Específica", expanded=True):
            tipo_tit = st.radio("Categoría de PSP:", ["Bancos", "Billeteras"], horizontal=True)

            lista_tit = bancos_principales if tipo_tit == "Bancos" else billeteras_principales

            psp_tit_id = st.selectbox(
                f"Seleccionar {tipo_tit[:-1]}:",
                options=list(lista_tit.keys()),
                format_func=lambda x: lista_tit[x]
            )

            opciones_validadores = ["GMONEY"]  # Validador base para todos

            if tipo_tit == "Bancos":
                if psp_tit_id == "psp_w13k323ed23dmd01":  # Excepción para BCP
                    opciones_validadores.append("BCP")

            elif tipo_tit == "Billeteras":
                pass

            prov_tit = st.selectbox("Proveedor de Titularidad:", opciones_validadores)

            if st.button(f"Agregar Titularidad a {tipo_tit[:-1]}"):
                st.session_state.custom_titularidad[psp_tit_id] = prov_tit

        if st.button("Limpiar Titularidad Específica"):
            st.session_state.custom_titularidad = {}
            st.rerun()

st.divider()

# =====================================================================
# TABLA RESUMEN
# =====================================================================
st.header("📋 Resumen de Configuración")


def preparar_datos_tabla():
    filas = []

    # --- Lógica de visualización para Bancos Default ---
    if has_default_routing_bancos:
        tit_bancos_def = "N/A"
        if activar_titularidad:
            # Si el canal default es ALFIN, en la tabla forzamos a mostrar ALFIN como titularidad
            tit_bancos_def = "ALFIN" if default_channel_bancos == "ALFIN" else (
                default_tit_provider if has_default_tit else "N/A")

        filas.append({"Categoría": "Bank Transfer", "Banco/PSP": "POR DEFECTO", "Canal": default_channel_bancos,
                      "Titularidad": tit_bancos_def})

    # --- Lógica de visualización para Billeteras Default ---
    if has_default_routing_billeteras:
        is_merged = has_default_routing_bancos and default_channel_bancos == default_channel_billeteras
        canal_val = f"{default_channel_billeteras}" if is_merged else default_channel_billeteras

        tit_wall_def = "N/A"
        if activar_titularidad:
            tit_wall_def = "ALFIN" if default_channel_billeteras == "ALFIN" else (
                default_tit_provider if has_default_tit else "N/A")

        filas.append({"Categoría": "Billeteras", "Banco/PSP": "POR DEFECTO", "Canal": canal_val,
                      "Titularidad": tit_wall_def})

    # --- Lógica de visualización para Excepciones ---
    psps_con_override = set(
        list(st.session_state.custom_routing.keys()) + list(st.session_state.custom_titularidad.keys()))

    for psp in psps_con_override:
        cat = "Bank Transfer" if psp in bancos_principales else "Billeteras"
        nombre = todos_los_psps_dict.get(psp, psp)

        if psp in st.session_state.custom_routing:
            ruteo = st.session_state.custom_routing[psp]
        elif psp in bancos_principales:
            ruteo = default_channel_bancos if has_default_routing_bancos else "N/A"
        else:
            ruteo = default_channel_billeteras if has_default_routing_billeteras else "N/A"

        if activar_titularidad:
            # AJUSTE: Muestra ALFIN visualmente si el ruteo de este PSP va por ALFIN
            if ruteo == "ALFIN":
                tit = "ALFIN"
            elif psp == "psp_w156838159753" and ruteo == "YAPE":
                tit = "YAPE"
            elif psp in st.session_state.custom_titularidad:
                tit = st.session_state.custom_titularidad[psp]
            elif has_default_tit:
                tit = default_tit_provider
            else:
                tit = "N/A"
        else:
            tit = "N/A"

        filas.append({"Categoría": cat, "Banco/PSP": nombre, "Canal": ruteo, "Titularidad": tit})

    # --- Lógica de Interplaza ---
    if validate_interbranch:
        val_int = default_tit_provider if (activar_titularidad and has_default_tit) else "N/A"
        filas.append({"Categoría": "Interplaza", "Banco/PSP": "Interplaza", "Canal": "BATCH", "Titularidad": val_int})

    return pd.DataFrame(filas)


st.dataframe(preparar_datos_tabla(), use_container_width=True, hide_index=True)

st.divider()

# =====================================================================
# GENERACIÓN DE JSON
# =====================================================================
st.header("3. JSON Resultante")


def generar_json():
    resultado = {}
    routing = {}

    if has_default_routing_bancos:
        routing["DEFAULT"] = default_channel_bancos

    if has_default_routing_billeteras:
        if has_default_routing_bancos and default_channel_bancos == default_channel_billeteras:
            pass
        else:
            for psp_w in billeteras_principales.keys():
                if psp_w not in st.session_state.custom_routing:
                    routing[psp_w] = default_channel_billeteras

    for psp, canal in st.session_state.custom_routing.items():
        routing[psp] = canal

    if routing: resultado["routing"] = routing

    if yape_validation:
        resultado["yape_validation"] = True
        resultado["yape_configuration"] = {"yape_merchant_id": yape_merchant_id,
                                           "yape_category_code": yape_category_code}

    if validate_interbranch: resultado["validate_interbranch"] = True

    only_yape_by_yape_local = (len(st.session_state.custom_routing) == 1 and
                               st.session_state.custom_routing.get("psp_w156838159753") == "YAPE" and
                               not (has_default_routing_bancos or has_default_routing_billeteras))

    # --- Lógica Titularidad ---
    if activar_titularidad and not only_yape_by_yape_local:
        provider = {}
        if has_default_tit: provider["DEFAULT"] = default_tit_provider
        for psp, prov in st.session_state.custom_titularidad.items():
            provider[psp] = prov

        resultado["account_holder"] = {
            "provider": provider, "validate": True, "audit_mode": False,
            "validate_cci": True, "validate_wallet": True, "validate_account": True
        }

    # --- AJUSTE: Lógica ALFIN condicionada a Titularidad ---
    alfin_esta_ruteado = (
            (has_default_routing_bancos and default_channel_bancos == "ALFIN") or
            (has_default_routing_billeteras and default_channel_billeteras == "ALFIN") or
            any(c == "ALFIN" for c in st.session_state.custom_routing.values())
    )

    # Solo inyecta el flag si ALFIN está en el ruteo Y la titularidad está activada
    if alfin_esta_ruteado and activar_titularidad:
        resultado["alfin_v3_enabled"] = True

    return resultado


json_final = generar_json()
st.code(json.dumps(json_final, indent=4, ensure_ascii=False), language='json')
st.download_button(label="Descargar JSON", file_name="config.json", mime="application/json",
                   data=json.dumps(json_final, indent=4))