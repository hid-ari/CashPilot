from __future__ import annotations

import pandas as pd
import streamlit as st

from ..business import (
    MP_EXPENSE_CATEGORIES,
    MP_INCOME_CATEGORIES,
    SUPPORTED_CURRENCIES,
    get_user_profile,
    normalize_expense_rows,
    normalize_income_rows,
    save_user_profile,
    save_user_rows,
)


def render_onboarding() -> bool:
    """
    Renders the first-time onboarding wizard.
    Returns True when the user completes or skips the wizard.
    """
    username = st.session_state.get("current_user", "")
    step = st.session_state.get("onboarding_step", 0)

    st.title("👋 Bienvenido a CashPilot")
    st.caption("Vamos a configurar tu perfil en unos pocos pasos.")

    # Step indicator
    steps_labels = ["Perfil", "Ingresos", "Gastos fijos"]
    cols_indicator = st.columns(len(steps_labels))
    for idx, label in enumerate(steps_labels):
        icon = "✅" if idx < step else ("▶️" if idx == step else "⬜")
        cols_indicator[idx].markdown(f"**{icon} {label}**")

    st.divider()

    if step == 0:
        st.subheader("Paso 1 / 3 — Tu perfil")
        st.markdown("Dinos cómo llamarte y cuál moneda usar en la app.")
        name = st.text_input("Tu nombre", value=username, key="ob_name")
        currency_idx = SUPPORTED_CURRENCIES.index("DOP")
        currency = st.selectbox("Moneda principal", SUPPORTED_CURRENCIES, index=currency_idx, key="ob_currency")

        c1, c2 = st.columns([1, 1])
        if c1.button("Siguiente →", key="ob_step0_next"):
            profile = get_user_profile(username)
            profile["name"] = name.strip() or username
            profile["currency"] = currency
            save_user_profile(username, profile)
            st.session_state.profile = profile
            st.session_state["onboarding_step"] = 1
            st.rerun()
        if c2.button("Saltar configuración", key="ob_skip"):
            _mark_onboarding_complete(username)
            return True

    elif step == 1:
        st.subheader("Paso 2 / 3 — Tus ingresos")
        st.markdown("Agrega al menos un ingreso (puedes agregar más luego).")

        if "ob_income_rows" not in st.session_state:
            st.session_state["ob_income_rows"] = [{"Categoria": "", "Descripcion": "", "Ingreso": 0.0}]

        rows = st.session_state["ob_income_rows"]
        for i, row in enumerate(rows):
            r1, r2, r3 = st.columns([1.5, 2, 1.2])
            cat_options = [""] + MP_INCOME_CATEGORIES
            cat_idx = cat_options.index(row["Categoria"]) if row["Categoria"] in cat_options else 0
            rows[i]["Categoria"] = r1.selectbox("Categoría", cat_options, index=cat_idx, key=f"ob_inc_cat_{i}", label_visibility="visible")
            rows[i]["Descripcion"] = r2.text_input("Descripción", value=row["Descripcion"], key=f"ob_inc_desc_{i}", label_visibility="visible")
            rows[i]["Ingreso"] = r3.number_input("Monto", min_value=0.0, value=float(row["Ingreso"]), step=1.0, key=f"ob_inc_val_{i}", label_visibility="visible")

        if st.button("＋ Agregar fila", key="ob_inc_add"):
            st.session_state["ob_income_rows"].append({"Categoria": "", "Descripcion": "", "Ingreso": 0.0})
            st.rerun()

        c1, c2 = st.columns([1, 1])
        if c1.button("← Atrás", key="ob_step1_back"):
            st.session_state["onboarding_step"] = 0
            st.rerun()
        if c2.button("Siguiente →", key="ob_step1_next"):
            valid_rows = [r for r in rows if r["Ingreso"] > 0]
            if valid_rows:
                df = normalize_income_rows(valid_rows)
                save_user_rows(username, "income", df, ["row_id"])
                st.session_state["mp_income_rows_df"] = df
            st.session_state["onboarding_step"] = 2
            st.rerun()

    elif step == 2:
        st.subheader("Paso 3 / 3 — Gastos fijos")
        st.markdown("Agrega tus gastos fijos mensuales: alquiler, suscripciones, etc.")

        if "ob_fixed_rows" not in st.session_state:
            st.session_state["ob_fixed_rows"] = [{"Categoria": "", "Descripcion": "", "Presupuesto": 0.0, "Actual": 0.0}]

        rows = st.session_state["ob_fixed_rows"]
        for i, row in enumerate(rows):
            r1, r2, r3 = st.columns([1.5, 2, 1.2])
            cat_options = [""] + MP_EXPENSE_CATEGORIES
            cat_idx = cat_options.index(row["Categoria"]) if row["Categoria"] in cat_options else 0
            rows[i]["Categoria"] = r1.selectbox("Categoría", cat_options, index=cat_idx, key=f"ob_fix_cat_{i}", label_visibility="visible")
            rows[i]["Descripcion"] = r2.text_input("Descripción", value=row["Descripcion"], key=f"ob_fix_desc_{i}", label_visibility="visible")
            rows[i]["Presupuesto"] = r3.number_input("Presupuesto", min_value=0.0, value=float(row["Presupuesto"]), step=1.0, key=f"ob_fix_val_{i}", label_visibility="visible")

        if st.button("＋ Agregar fila", key="ob_fix_add"):
            st.session_state["ob_fixed_rows"].append({"Categoria": "", "Descripcion": "", "Presupuesto": 0.0, "Actual": 0.0})
            st.rerun()

        c1, c2 = st.columns([1, 1])
        if c1.button("← Atrás", key="ob_step2_back"):
            st.session_state["onboarding_step"] = 1
            st.rerun()
        if c2.button("✅ Finalizar configuración", key="ob_step2_finish"):
            valid_rows = [r for r in rows if r["Presupuesto"] > 0]
            if valid_rows:
                df = normalize_expense_rows(valid_rows)
                save_user_rows(username, "fixed", df, ["row_id"])
                st.session_state["mp_fixed_rows_df"] = df
            _mark_onboarding_complete(username)
            return True

    return False


def _mark_onboarding_complete(username: str):
    profile = get_user_profile(username)
    profile["onboarding_complete"] = True
    save_user_profile(username, profile)
    st.session_state.profile = profile
    st.session_state.pop("onboarding_step", None)
    st.session_state.pop("ob_income_rows", None)
    st.session_state.pop("ob_fixed_rows", None)
    st.rerun()
