from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from ..business import MONTH_NAME_OPTIONS, MP_MONTHLY_COLUMNS, build_monthly_record, format_currency, get_monthly_rows, save_monthly_rows_for_user
from .records import mp_csv_download_button


def mp_currency(amount):
    currency = "DOP"
    try:
        currency = st.session_state.get("profile", {}).get("currency", "DOP")
    except Exception:
        currency = "DOP"
    return format_currency(amount, currency)


def render_home_page():
    fixed_df = st.session_state.mp_fixed_rows_df.copy()
    variable_df = st.session_state.mp_variable_rows_df.copy()
    income_df = st.session_state.mp_income_rows_df.copy()
    savings_df = st.session_state.mp_savings_rows_df.copy()

    fixed_budget = float(fixed_df["Presupuesto"].sum()) if not fixed_df.empty else 0.0
    fixed_actual = float(fixed_df["Actual"].sum()) if not fixed_df.empty else 0.0
    variable_budget = float(variable_df["Presupuesto"].sum()) if not variable_df.empty else 0.0
    variable_actual = float(variable_df["Actual"].sum()) if not variable_df.empty else 0.0
    income_total = float(income_df["Ingreso"].sum()) if not income_df.empty else 0.0
    savings_total = float(savings_df["Ahorro"].sum()) if not savings_df.empty else 0.0

    total_budget = fixed_budget + variable_budget
    total_expenses = fixed_actual + variable_actual
    balance = income_total - total_expenses

    current_datetime = datetime.now()
    current_month_name = MONTH_NAME_OPTIONS[current_datetime.month - 1]
    current_day = int(current_datetime.strftime("%d"))
    current_saved_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    st.title("CashPilot")
    st.caption("Dashboard financiero personal")
    st.header("Dashboard")
    dashboard_metrics = [
        ("Ingresos", mp_currency(income_total)),
        ("Gastos fijos", mp_currency(fixed_actual)),
        ("Gastos variables", mp_currency(variable_actual)),
        ("Presupuesto", mp_currency(total_budget)),
        ("Ahorros", mp_currency(savings_total)),
        ("Balance", mp_currency(balance)),
    ]
    for start in range(0, len(dashboard_metrics), 2):
        metric_cols = st.columns(2)
        for col, (label, value) in zip(metric_cols, dashboard_metrics[start:start + 2]):
            col.metric(label, value)

    save_col, info_col = st.columns([1, 4])
    with save_col:
        if st.button("Guardar mes", key="save_month_button"):
            username = st.session_state.get("current_user")
            existing_monthly = get_monthly_rows(username).to_dict(orient="records") if username else []
            new_record = build_monthly_record(
                current_month_name,
                int(current_day),
                income_total,
                fixed_actual,
                variable_actual,
                savings_total,
                total_budget,
                balance,
                current_saved_at,
            )
            existing_monthly.append(new_record)
            if username:
                save_monthly_rows_for_user(username, pd.DataFrame(existing_monthly))
            st.session_state.mp_monthly_rows_df = get_monthly_rows(username) if username else pd.DataFrame(columns=MP_MONTHLY_COLUMNS)
            st.success("Mes guardado en el historial.")
            st.rerun()
    with info_col:
        st.info(f"Fecha utilizada: {current_day} de {current_month_name}")

    st.divider()
    st.subheader("Gráfica resumen")
    expenses_all = pd.concat(
        [
            fixed_df[["Categoria", "Actual"]].rename(columns={"Actual": "Valor"}),
            variable_df[["Categoria", "Actual"]].rename(columns={"Actual": "Valor"}),
        ],
        ignore_index=True,
    ) if (not fixed_df.empty or not variable_df.empty) else pd.DataFrame(columns=["Categoria", "Valor"])

    expenses_by_cat = expenses_all.groupby("Categoria", as_index=False)["Valor"].sum() if not expenses_all.empty else pd.DataFrame(columns=["Categoria", "Valor"])
    income_by_cat = income_df.groupby("Categoria", as_index=False)[["Ingreso"]].sum() if not income_df.empty else pd.DataFrame(columns=["Categoria", "Ingreso"])

    budget_all = pd.concat(
        [
            fixed_df[["Categoria", "Presupuesto"]].rename(columns={"Presupuesto": "Valor"}),
            variable_df[["Categoria", "Presupuesto"]].rename(columns={"Presupuesto": "Valor"}),
        ],
        ignore_index=True,
    ) if (not fixed_df.empty or not variable_df.empty) else pd.DataFrame(columns=["Categoria", "Valor"])

    budget_by_cat = budget_all.groupby("Categoria", as_index=False)["Valor"].sum() if not budget_all.empty else pd.DataFrame(columns=["Categoria", "Valor"])
    savings_by_cat = savings_df.groupby("Categoria", as_index=False)[["Ahorro"]].sum() if not savings_df.empty else pd.DataFrame(columns=["Categoria", "Ahorro"])

    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        st.markdown("**Gastos (Actual)**")
        if not expenses_by_cat.empty and expenses_by_cat["Valor"].sum() > 0:
            fig1 = px.pie(expenses_by_cat, names="Categoria", values="Valor", title="Gastos por categoría (Actual)")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No hay gastos registrados.")

    with row1_col2:
        st.markdown("**Ingresos**")
        if not income_by_cat.empty and income_by_cat["Ingreso"].sum() > 0:
            fig2 = px.pie(income_by_cat, names="Categoria", values="Ingreso", title="Ingresos por categoría")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay ingresos registrados.")

    with row2_col1:
        st.markdown("**Presupuesto**")
        if not budget_by_cat.empty and budget_by_cat["Valor"].sum() > 0:
            fig3 = px.pie(budget_by_cat, names="Categoria", values="Valor", title="Presupuesto por categoría")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No hay presupuesto registrado.")

    with row2_col2:
        st.markdown("**Ahorros**")
        if not savings_by_cat.empty and savings_by_cat["Ahorro"].sum() > 0:
            fig4 = px.pie(savings_by_cat, names="Categoria", values="Ahorro", title="Ahorros por categoría")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No hay ahorros registrados.")

    st.divider()
    st.subheader("Resumen mensual guardado")
    monthly_df = get_monthly_rows(st.session_state.get("current_user"))
    if monthly_df.empty:
        st.info("Todavía no has guardado ningún mes.")
    else:
        mp_csv_download_button(monthly_df, "resumen_mensual.csv", "Guardar CSV")
        display_monthly = monthly_df.copy()
        if "Ahorros" not in display_monthly.columns:
            display_monthly["Ahorros"] = 0.0
        if "Día" not in display_monthly.columns:
            display_monthly["Día"] = 1
        display_monthly = display_monthly.reindex(columns=MP_MONTHLY_COLUMNS)
        for col in ["Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Presupuesto", "Balance"]:
            display_monthly[col] = display_monthly[col].apply(mp_currency)
        st.dataframe(display_monthly.sort_values(by="Guardado", ascending=False), use_container_width=True, hide_index=True)
