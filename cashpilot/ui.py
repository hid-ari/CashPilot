from __future__ import annotations

import streamlit as st

from .business import is_admin_user

MAIN_NAVIGATION_OPTIONS = ["Home", "Gastos fijos", "Gastos variables", "Ingresos", "Ahorros", "Transacciones", "Metas", "Perfil"]


def render_sidebar_navigation(current_user: str | None):
    options = list(MAIN_NAVIGATION_OPTIONS)
    if is_admin_user(current_user):
        options.append("Admin")

    # Support programmatic navigation override (e.g. from CTA buttons)
    nav_override = st.session_state.pop("nav_override", None)
    default_idx = 0
    if nav_override and nav_override in options:
        default_idx = options.index(nav_override)

    st.sidebar.title("Navegación")
    return st.sidebar.radio(
        "Ir a",
        options,
        index=default_idx,
        label_visibility="collapsed",
    )
