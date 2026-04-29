from __future__ import annotations

import os

import streamlit as st

from ..business import get_user_profile, save_user_profile, delete_current_user_data
from ..data_access import DATA_FILE, SETTINGS_FILE


def render_profile_panel():
    st.header("Perfil")

    current_user = st.session_state.get("current_user")
    st.info(f"Sesión iniciada como: **{current_user}**")

    logout_col = st.columns([0.5, 5])[0]
    if logout_col.button("Cerrar sesión", type="secondary"):
        st.session_state.current_user = None
        st.success("Sesión cerrada.")
        st.rerun()

    st.divider()
    profile = get_user_profile(current_user)
    name = st.text_input("Nombre de usuario", value=profile.get("name", ""))
    currency = st.selectbox("Moneda", options=["DOP", "USD", "EUR", "ARS", "CLP"], index=["DOP", "USD", "EUR", "ARS", "CLP"].index(profile.get("currency", "DOP")))
    cols = st.columns([1, 1])
    if cols[0].button("Guardar perfil"):
        profile["name"] = name
        profile["currency"] = currency
        save_user_profile(current_user, profile)
        st.session_state.profile = profile
        st.success("Perfil guardado.")
        st.rerun()

    st.divider()
    st.subheader("Eliminar datos")
    st.warning("Esta acción borra los datos guardados del dashboard y no se puede deshacer.")
    confirmation = st.text_input("Escribe borrar para confirmar", key="delete_data_confirmation")
    delete_button = st.button("Eliminar datos", type="primary", disabled=confirmation.strip().lower() != "borrar")
    if delete_button:
        delete_current_user_data(current_user)
        for file_path in [DATA_FILE, SETTINGS_FILE]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        st.success("Datos eliminados.")
        st.rerun()
