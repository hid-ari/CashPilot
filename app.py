import os

import streamlit as st

from cashpilot.business import (
    MP_DEFAULT_FIXED_ROWS,
    MP_DEFAULT_INCOME_ROWS,
    MP_DEFAULT_SAVINGS_ROWS,
    MP_DEFAULT_VARIABLE_ROWS,
    delete_current_user_data,
    get_monthly_rows,
    get_user_profile,
    get_user_rows,
    is_admin_user,
    login_user,
    normalize_expense_rows,
    normalize_income_rows,
    normalize_savings_rows,
    register_user,
    save_user_profile,
)
from cashpilot.data_access import DATA_FILE, SETTINGS_FILE
from cashpilot.screens import (
    render_admin_panel,
    render_expense_page,
    render_home_page,
    render_income_page,
    render_profile_panel,
    render_savings_page,
)
from cashpilot.ui import render_sidebar_navigation


def apply_space_mono_font():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

        html, body, .stApp {
            font-family: 'Space Mono', monospace !important;
        }

        .stMarkdown p,
        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4,
        .stMarkdown h5,
        .stMarkdown h6,
        .stMarkdown ul,
        .stMarkdown ol,
        .stMarkdown li,
        .stText,
        .stCaption,
        .stButton > button {
            font-family: 'Space Mono', monospace !important;
        }

        .stMarkdown ul,
        .stMarkdown ol {
            padding-left: 1.4rem;
        }

        .stMetricValue {
            font-size: 1.85rem;
            line-height: 1.1;
            font-family: 'Space Mono', monospace !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_settings():
    username = st.session_state.get("current_user")
    if not username:
        return {"name": "Usuario", "currency": "DOP"}
    return get_user_profile(username)


def init_profile_state():
    current_user = st.session_state.get("current_user")
    if st.session_state.get("profile_owner") != current_user:
        st.session_state.profile = load_settings()
        st.session_state.profile_owner = current_user
        return
    if "profile" not in st.session_state:
        st.session_state.profile = load_settings()
        st.session_state.profile_owner = current_user


def mp_init_state():
    current_user = st.session_state.get("current_user")
    if st.session_state.get("mp_state_owner") != current_user:
        st.session_state.mp_fixed_rows_df = get_user_rows(current_user, "fixed", MP_DEFAULT_FIXED_ROWS, normalize_expense_rows)
        st.session_state.mp_variable_rows_df = get_user_rows(current_user, "variable", MP_DEFAULT_VARIABLE_ROWS, normalize_expense_rows)
        st.session_state.mp_income_rows_df = get_user_rows(current_user, "income", MP_DEFAULT_INCOME_ROWS, normalize_income_rows)
        st.session_state.mp_savings_rows_df = get_user_rows(current_user, "savings", MP_DEFAULT_SAVINGS_ROWS, normalize_savings_rows)
        st.session_state.mp_monthly_rows_df = get_monthly_rows(current_user)
        st.session_state.mp_state_owner = current_user


def delete_app_data():
    username = st.session_state.get("current_user")
    if username:
        delete_current_user_data(username)

    for file_path in [DATA_FILE, SETTINGS_FILE]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


def login_register_page():
    st.title("CashPilot")
    st.caption("Dashboard financiero personal")

    tab1, tab2 = st.tabs(["Iniciar sesión", "Registrarse"])

    with tab1:
        st.subheader("Iniciar sesión")
        login_username = st.text_input("Usuario", key="login_username")
        login_password = st.text_input("Contraseña", type="password", key="login_password")

        if st.button("Entrar", key="login_button"):
            success, message = login_user(login_username, login_password)
            if success:
                st.session_state.current_user = login_username
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with tab2:
        st.subheader("Crear nueva cuenta")
        register_username = st.text_input("Usuario", key="register_username")
        register_password = st.text_input("Contraseña", type="password", key="register_password")
        register_password_confirm = st.text_input("Confirmar contraseña", type="password", key="register_password_confirm")

        if st.button("Registrarse", key="register_button"):
            if register_password != register_password_confirm:
                st.error("Las contraseñas no coinciden.")
            else:
                success, message = register_user(register_username, register_password)
                if success:
                    st.success(message)
                    st.info("Ahora puedes iniciar sesión con tu nueva cuenta.")
                else:
                    st.error(message)


def mp_home_page():
    return render_home_page()


def mp_expense_page(title, state_key, file_key, default_rows):
    return render_expense_page(title, state_key, file_key, default_rows)


def mp_income_page():
    return render_income_page()


def mp_savings_page():
    return render_savings_page()


def build_profile_panel():
    return render_profile_panel()


def build_admin_panel():
    return render_admin_panel()


def mp_sidebar_page():
    return render_sidebar_navigation(st.session_state.get("current_user"))


def main():
    st.set_page_config(page_title="CashPilot", layout="wide")
    apply_space_mono_font()

    if "current_user" not in st.session_state:
        st.session_state.current_user = None

    if not st.session_state.current_user:
        login_register_page()
        return

    mp_init_state()
    init_profile_state()

    page = mp_sidebar_page()

    if page == "Home":
        mp_home_page()
    elif page == "Gastos fijos":
        mp_expense_page("Gastos fijos", "mp_fixed_rows_df", "fixed", MP_DEFAULT_FIXED_ROWS)
    elif page == "Gastos variables":
        mp_expense_page("Gastos variables", "mp_variable_rows_df", "variable", MP_DEFAULT_VARIABLE_ROWS)
    elif page == "Ingresos":
        mp_income_page()
    elif page == "Ahorros":
        mp_savings_page()
    elif page == "Perfil":
        build_profile_panel()
    elif page == "Admin":
        if is_admin_user(st.session_state.get("current_user")):
            build_admin_panel()
        else:
            st.error("No tienes permisos para acceder a esta sección.")


if __name__ == "__main__":
    main()
