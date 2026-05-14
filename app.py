import streamlit as st
import json
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Configurador de Ruteo y Titularidad", layout="wide")

# 1. Diccionarios de configuración escalable
bancos_principales = {
    "psp_w13k323ed23dmd01": "(BCP) - Banco de Crédito del Perú",
    "psp_w13k12312341md02": "(BBVA) - BBVA Continental",
    "psp_w0328223930dmd04": "(Interbank) - Banco International del Perú",
    "psp_w191433107454": "Banco de la Nación",
    "psp_w133203223m3md03": "(Scotiabank)- Scotiabank",
    "psp_w156838159753": "Yape"
}

# Lista de bancos habilitados para Titularidad Específica (Escalable)
bancos_titularidad_habilitados = {
    "psp_w13k323ed23dmd01": "(BCP) - Banco de Crédito del Perú"
}


def init_session_state():
    if "custom_routing" not in st.session_state:
        st.session_state.custom_routing = {}
    if "custom_titularidad" not in st.session_state:
        st.session_state.custom_titularidad = {}


init_session_state()

st.title("⚙️ Generador de JSON: Ruteo y Titularidad")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Configuración de Ruteo")
    has_default_routing = st.checkbox("¿Activar Bank Transfer y Billeteras para todos los bancos?", value=True)
    default_channel = None
    if has_default_routing:
        opciones_ruteo_default = ["GMONEY", "BATCH", "ALFIN"]
        default_channel = st.selectbox("Canal de dispersión por defecto:", opciones_ruteo_default)

    st.divider()
    st.subheader("Ruteo por Banco Específico")
    banco_id_seleccionado = st.selectbox(
        "Seleccionar Banco para Ruteo:",
        options=list(bancos_principales.keys()),
        format_func=lambda x: bancos_principales[x]
    )

    canales_disponibles = ["GMONEY", "BATCH", "ALFIN"]
    if banco_id_seleccionado == "psp_w13k323ed23dmd01":
        canales_disponibles.append("BCP")
    elif banco_id_seleccionado == "psp_w13k12312341md02":
        canales_disponibles.append("BBVA")
    elif banco_id_seleccionado == "psp_w156838159753":
        del canales_disponibles [1:3]
        canales_disponibles.append("YAPE")

    canal_especifico = st.selectbox("Canal de dispersión:", canales_disponibles, key="canal_route")

    if st.button("Agregar a Ruteo"):
        st.session_state.custom_routing[banco_id_seleccionado] = canal_especifico

    if st.button("Limpiar Ruteo Específico"):
        st.session_state.custom_routing = {}
        st.rerun()

    st.divider()
    st.subheader("Configuraciones Adicionales")
    yape_validation = False
    validate_interbranch = st.checkbox("Solicitar ruteo para interplaza (BATCH)", value=False)

    if st.session_state.custom_routing.get("psp_w156838159753") == "YAPE":
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
        # Titularidad DEFAULT
        has_default_tit = st.checkbox("¿Configurar Titularidad para todos los bancos?", value=True)
        default_tit_provider = None
        if has_default_tit:
            opciones_tit_default = ["GMONEY","ALFIN"]
            default_tit_provider = st.selectbox("Proveedor de Titularidad por defecto:", opciones_tit_default)

        st.divider()

        # Titularidad Específica
        st.subheader("Titularidad por Banco Específico")
        banco_tit_id = st.selectbox(
            "Seleccionar Banco para Titularidad:",
            options=list(bancos_titularidad_habilitados.keys()),
            format_func=lambda x: bancos_titularidad_habilitados[x]
        )

        opciones_validadores = ["BCP", "GMONEY"]
        prov_tit = st.selectbox("Validador de Titularidad:", opciones_validadores, key="val_tit")

        if st.button("Agregar a Titularidad"):
            st.session_state.custom_titularidad[banco_tit_id] = prov_tit

        if st.button("Limpiar Titularidad Específica"):
            st.session_state.custom_titularidad = {}
            st.rerun()

st.divider()

# --- TABLA RESUMEN ---
st.header("📋 Resumen de Configuración")


def preparar_datos_tabla():
    filas = []
    # Fila Default
    if has_default_routing:
        filas.append({
            "Banco / Criterio": "Bancos/Billeteras",
            "Canal de Ruteo": default_channel,
            "Validador Titularidad": default_tit_provider if activar_titularidad and has_default_tit else "N/A"
        })

    # Combinar bancos de ruteo y titularidad para la tabla
    todos_los_psps = set(
        list(st.session_state.custom_routing.keys()) + list(st.session_state.custom_titularidad.keys()))

    for psp in todos_los_psps:
        nombre = bancos_principales.get(psp, psp)
        ruteo = st.session_state.custom_routing.get(psp, default_channel if has_default_routing else "No configurado")

        if activar_titularidad:
            if psp == "psp_w156838159753" and ruteo == "YAPE":
                tit = "YAPE"
            elif has_default_tit:
                tit = st.session_state.custom_titularidad.get(psp, default_tit_provider)
            else:
                tit = st.session_state.custom_titularidad.get(psp, "N/A")
        else:
            tit = "N/A"

        filas.append({"Banco / Criterio": nombre, "Canal de Ruteo": ruteo, "Validador Titularidad": tit})

    # CORRECCIÓN AQUÍ: Interplaza ahora valida si debe mostrar el proveedor por defecto
    if validate_interbranch:
        validador_interplaza = default_tit_provider if (activar_titularidad and has_default_tit) else "N/A"
        filas.append({
            "Banco / Criterio": "Interplaza",
            "Canal de Ruteo": "BATCH",
            "Validador Titularidad": validador_interplaza
        })

    return pd.DataFrame(filas)


df_resumen = preparar_datos_tabla()
if not df_resumen.empty:
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
else:
    st.info("No hay configuraciones activas.")

st.divider()

# --- GENERACIÓN Y VISUALIZACIÓN DEL JSON ---
st.header("3. JSON Resultante")


def generar_json():
    resultado = {}
    routing = {}
    if has_default_routing: routing["DEFAULT"] = default_channel
    for psp, canal in st.session_state.custom_routing.items(): routing[psp] = canal
    if routing: resultado["routing"] = routing

    if yape_validation:
        resultado["yape_validation"] = True
        resultado["yape_configuration"] = {"yape_merchant_id": yape_merchant_id,
                                           "yape_category_code": yape_category_code}

    if validate_interbranch: resultado["validate_interbranch"] = True

    if activar_titularidad and not only_yape_by_yape:
        provider = {}
        if has_default_tit: provider["DEFAULT"] = default_tit_provider
        for psp, prov in st.session_state.custom_titularidad.items(): provider[psp] = prov
        resultado["account_holder"] = {
            "provider": provider, "validate": True, "audit_mode": False,
            "validate_cci": True, "validate_wallet": True, "validate_account": True
        }

    # ALFIN check
    if (default_channel == "ALFIN" and has_default_routing) or any(
            c == "ALFIN" for c in st.session_state.custom_routing.values()):
        resultado["alfin_v3_enabled"] = True

    return resultado


json_final = generar_json()
json_string = json.dumps(json_final, indent=4, ensure_ascii=False)
st.code(json_string, language='json')

st.download_button(label="Descargar archivo .json", file_name="configuracion_ruteo.json", mime="application/json",
                   data=json_string)