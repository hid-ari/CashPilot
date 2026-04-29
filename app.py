import json
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from cashpilot.business import (
    ADMIN_ROLE,
    MP_DEFAULT_FIXED_ROWS,
    MP_DEFAULT_INCOME_ROWS,
    MP_DEFAULT_SAVINGS_ROWS,
    MP_DEFAULT_VARIABLE_ROWS,
    MP_EXPENSE_CATEGORIES,
    MP_INCOME_CATEGORIES,
    MP_MONTHLY_COLUMNS,
    MP_SAVINGS_CATEGORIES,
    MONTH_NAME_OPTIONS,
    build_monthly_record,
    change_user_password,
    change_user_role,
    delete_current_user_data,
    delete_user_account,
    format_currency,
    get_all_users_documents_status,
    get_monthly_rows,
    get_user_profile,
    get_user_rows,
            rows_to_remove.append(row_id)

        updated_rows.append(
            {
                "row_id": row_id,
                "Categoria": categoria,
                "Descripcion": descripcion,
                "Presupuesto": float(presupuesto),
                "Actual": float(actual),
            }
        )

    st.session_state[state_key] = mp_merge_rows(full_df, updated_rows)
    mp_save_rows(file_key, st.session_state[state_key], ["row_id"])

    bottom_cols = st.columns([1, 1, 4])
    if bottom_cols[0].button("Eliminar marcados", key=f"{state_key}_delete"):
        st.session_state[state_key] = st.session_state[state_key][~st.session_state[state_key]["row_id"].isin(rows_to_remove)].reset_index(drop=True)
        mp_save_rows(file_key, st.session_state[state_key], ["row_id"])
        st.success("Registros eliminados.")
        st.rerun()


def mp_income_page():
    state_key = "mp_income_rows_df"
    st.header("Ingresos")

    action_cols = st.columns([0.7, 1.2, 3.0])
    if action_cols[0].button("＋", key="income_add", help="Agregar fila vacía"):
        mp_add_blank_income_row(state_key)
        st.rerun()
    with action_cols[1]:
        mp_csv_download_button(st.session_state[state_key], "ingresos.csv", "Guardar CSV", ["row_id"])

    filtro = st.text_input("Filtrar por categoría", key="income_filter")
    full_df = st.session_state[state_key].copy().reset_index(drop=True)
    if filtro.strip():
        q = filtro.strip().lower()
        display_df = full_df[full_df["Categoria"].str.lower().str.contains(q, na=False)]
    else:
        display_df = full_df

    if display_df.empty:
        st.info("No hay ingresos para mostrar.")
        return
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
