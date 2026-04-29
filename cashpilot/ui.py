from __future__ import annotations

import streamlit as st

from .business import is_admin_user

MAIN_NAVIGATION_OPTIONS = ["Home", "Gastos fijos", "Gastos variables", "Ingresos", "Ahorros", "Perfil"]


def render_sidebar_navigation(current_user: str | None):
    options = list(MAIN_NAVIGATION_OPTIONS)
    if is_admin_user(current_user):
        options.append("Admin")

    st.sidebar.title("Navegación")
    return st.sidebar.radio(
        "Ir a",
        options,
        index=0,
        label_visibility="collapsed",
    )
