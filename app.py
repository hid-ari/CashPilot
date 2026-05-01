import os
from datetime import datetime

import streamlit as st

from cashpilot.business import (
    MP_DEFAULT_FIXED_ROWS,
    MP_DEFAULT_INCOME_ROWS,
    MP_DEFAULT_SAVINGS_ROWS,
    MP_DEFAULT_TRANSACTION_ROWS,
    MP_DEFAULT_VARIABLE_ROWS,
    SESSION_TIMEOUT_OPTIONS,
    delete_current_user_data,
    format_currency,
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
    render_goals_page,
    render_home_page,
    render_income_page,
    render_onboarding,
    render_profile_panel,
    render_savings_page,
    render_transactions_page,
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


def check_session_timeout():
    """Auto-logout if the user has been idle longer than their configured timeout."""
    profile = st.session_state.get("profile", {})
    timeout_minutes = profile.get("session_timeout_minutes", 0)
    if timeout_minutes <= 0:
        # Update last activity even when timeout is disabled so it's ready if changed
        st.session_state["last_activity"] = datetime.now().isoformat()
        return

    last = st.session_state.get("last_activity")
    now = datetime.now()
    if last:
        try:
            elapsed = (now - datetime.fromisoformat(last)).total_seconds() / 60
            if elapsed > timeout_minutes:
                username = st.session_state.get("current_user")
                st.session_state.current_user = None
                st.warning(f"Sesión cerrada por inactividad ({timeout_minutes} min).")
                st.rerun()
        except Exception:
            pass
    st.session_state["last_activity"] = now.isoformat()


def show_login_summary():
    """Show a quick summary of the current month at the top of the sidebar after login."""
    username = st.session_state.get("current_user")
    if not username:
        return
    monthly_df = get_monthly_rows(username)
    if monthly_df.empty:
        return
    profile = st.session_state.get("profile", {})
    currency = profile.get("currency", "DOP")
    latest = monthly_df.sort_values("Guardado").iloc[-1]
    gastos = float(latest.get("Gastos fijos", 0)) + float(latest.get("Gastos variables", 0))
    presupuesto = float(latest.get("Presupuesto", 0))
    pct = gastos / presupuesto * 100 if presupuesto > 0 else 0
    st.sidebar.divider()
    st.sidebar.caption(f"**Último guardado:** {latest.get('Mes', '')} día {latest.get('Día', '')}")
    st.sidebar.caption(f"Gastos: {format_currency(gastos, currency)} ({pct:.0f}% presupuesto)")


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
                st.session_state["last_activity"] = datetime.now().isoformat()
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


def mp_transactions_page():
    return render_transactions_page()


def mp_goals_page():
    return render_goals_page()


def build_profile_panel():
    return render_profile_panel()


def build_admin_panel():
    return render_admin_panel()


def mp_sidebar_page():
    return render_sidebar_navigation(st.session_state.get("current_user"))


def needs_onboarding() -> bool:
    profile = st.session_state.get("profile", {})
    return not profile.get("onboarding_complete", False)


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
    check_session_timeout()

    # First-time onboarding wizard
    if needs_onboarding():
        done = render_onboarding()
        if not done:
            return

    page = mp_sidebar_page()
    show_login_summary()

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
    elif page == "Transacciones":
        mp_transactions_page()
    elif page == "Metas":
        mp_goals_page()
    elif page == "Perfil":
        build_profile_panel()
    elif page == "Admin":
        if is_admin_user(st.session_state.get("current_user")):
            build_admin_panel()
        else:
            st.error("No tienes permisos para acceder a esta sección.")


if __name__ == "__main__":
    main()

