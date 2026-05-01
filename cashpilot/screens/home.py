from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ..business import (
    MONTH_NAME_OPTIONS,
    MP_MONTHLY_COLUMNS,
    build_monthly_record,
    calculate_monthly_projection,
    calculate_savings_rate,
    format_currency,
    get_budget_alerts,
    get_days_in_month,
    get_monthly_rows,
    save_monthly_rows_for_user,
)
from .records import mp_csv_download_button


def mp_currency(amount):
    currency = "DOP"
    try:
        currency = st.session_state.get("profile", {}).get("currency", "DOP")
    except Exception:
        currency = "DOP"
    return format_currency(amount, currency)


def _health_color(actual: float, budget: float) -> str:
    if budget <= 0:
        return "normal"
    pct = actual / budget * 100
    if pct >= 100:
        return "inverse"
    if pct >= 80:
        return "off"
    return "normal"


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
    savings_rate = calculate_savings_rate(income_total, savings_total)

    current_datetime = datetime.now()
    current_month_name = MONTH_NAME_OPTIONS[current_datetime.month - 1]
    current_day = int(current_datetime.strftime("%d"))
    days_in_month = get_days_in_month(current_datetime.year, current_datetime.month)
    current_saved_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    projected_expenses = calculate_monthly_projection(total_expenses, current_day, days_in_month)

    st.title("CashPilot")
    st.caption("Dashboard financiero personal")
    st.header("Dashboard")

    # ── Budget alerts ────────────────────────────────────────────────────────────
    alerts = get_budget_alerts(fixed_df, variable_df)
    if alerts:
        with st.expander(f"⚠️ {len(alerts)} alerta(s) de presupuesto", expanded=True):
            for a in alerts:
                msg = f"**{a['name']}** ({a['label']}): {a['pct']:.0f}% del presupuesto usado"
                if a["level"] == "error":
                    st.error(f"🔴 {msg}")
                else:
                    st.warning(f"🟡 {msg}")

    # ── Main metrics ─────────────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m4, m5, m6 = st.columns(3)
    m1.metric("💰 Ingresos", mp_currency(income_total))
    m2.metric(
        "📌 Gastos fijos",
        mp_currency(fixed_actual),
        delta=f"{fixed_actual - fixed_budget:+,.0f} vs presupuesto" if fixed_budget > 0 else None,
        delta_color=_health_color(fixed_actual, fixed_budget),
    )
    m3.metric(
        "🔄 Gastos variables",
        mp_currency(variable_actual),
        delta=f"{variable_actual - variable_budget:+,.0f} vs presupuesto" if variable_budget > 0 else None,
        delta_color=_health_color(variable_actual, variable_budget),
    )
    m4.metric("📊 Presupuesto total", mp_currency(total_budget))
    m5.metric("🏦 Ahorros", mp_currency(savings_total))
    m6.metric(
        "⚖️ Balance",
        mp_currency(balance),
        delta_color="normal" if balance >= 0 else "inverse",
    )

    # ── Secondary metrics ─────────────────────────────────────────────────────────
    s1, s2, s3 = st.columns(3)
    s1.metric("💹 Tasa de ahorro", f"{savings_rate:.1f}%",
              help="Porcentaje de ingresos destinado a ahorros")
    s2.metric("📅 Proyección mensual (gastos)", mp_currency(projected_expenses),
              help=f"Estimación al cierre del mes basada en los primeros {current_day} días")
    s3.metric("📆 Día del mes", f"{current_day} / {days_in_month}")

    # ── Empty state call-to-action ────────────────────────────────────────────────
    has_data = income_total > 0 or total_expenses > 0 or savings_total > 0
    if not has_data:
        st.info("🚀 ¡Bienvenido! Empieza registrando tus ingresos y gastos para ver tu situación financiera aquí.")
        cta1, cta2, cta3 = st.columns(3)
        if cta1.button("➕ Agregar ingreso"):
            st.session_state["nav_override"] = "Ingresos"
            st.rerun()
        if cta2.button("➕ Gasto fijo"):
            st.session_state["nav_override"] = "Gastos fijos"
            st.rerun()
        if cta3.button("➕ Gasto variable"):
            st.session_state["nav_override"] = "Gastos variables"
            st.rerun()

    # ── Save month ────────────────────────────────────────────────────────────────
    st.divider()
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

    # ── Charts ────────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📊 Gráficas del mes")

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
        st.markdown("**Presupuesto vs Actual por categoría**")
        if not budget_by_cat.empty and budget_by_cat["Valor"].sum() > 0 and not expenses_by_cat.empty:
            merged = budget_by_cat.rename(columns={"Valor": "Presupuesto"}).merge(
                expenses_by_cat.rename(columns={"Valor": "Actual"}),
                on="Categoria",
                how="outer",
            ).fillna(0)
            merged_melted = merged.melt(id_vars="Categoria", var_name="Tipo", value_name="Monto")
            colors = {"Presupuesto": "#636EFA", "Actual": "#EF553B"}
            fig3 = px.bar(
                merged_melted,
                x="Monto",
                y="Categoria",
                color="Tipo",
                barmode="group",
                orientation="h",
                title="Presupuesto vs Actual",
                color_discrete_map=colors,
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No hay datos de presupuesto.")

    with row2_col2:
        st.markdown("**Ahorros**")
        if not savings_by_cat.empty and savings_by_cat["Ahorro"].sum() > 0:
            fig4 = px.pie(savings_by_cat, names="Categoria", values="Ahorro", title="Ahorros por categoría")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No hay ahorros registrados.")

    # ── Monthly history ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📅 Resumen mensual guardado")
    monthly_df = get_monthly_rows(st.session_state.get("current_user"))

    if monthly_df.empty:
        st.info("Todavía no has guardado ningún mes.")
    else:
        # ── Trend chart ───────────────────────────────────────────────────────────
        st.markdown("**Tendencia histórica**")
        trend_df = monthly_df.copy().sort_values("Guardado")
        numeric_cols = ["Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Balance"]
        for col in numeric_cols:
            trend_df[col] = pd.to_numeric(trend_df[col], errors="coerce").fillna(0)
        trend_df["Etiqueta"] = trend_df["Mes"] + " (día " + trend_df["Día"].astype(str) + ")"
        fig_trend = go.Figure()
        line_colors = {"Ingresos": "#00CC96", "Gastos fijos": "#EF553B", "Gastos variables": "#FF6692", "Ahorros": "#636EFA", "Balance": "#FFA15A"}
        for col in ["Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Balance"]:
            fig_trend.add_trace(go.Scatter(
                x=trend_df["Etiqueta"],
                y=trend_df[col],
                mode="lines+markers",
                name=col,
                line=dict(color=line_colors.get(col)),
            ))
        fig_trend.update_layout(title="Evolución mensual", xaxis_title="Mes", yaxis_title="Monto", legend_title="Categoría")
        st.plotly_chart(fig_trend, use_container_width=True)

        # ── Copy template ─────────────────────────────────────────────────────────
        copy_col, dl_col = st.columns([1, 1])
        with copy_col:
            if st.button("📋 Copiar gastos fijos del último mes guardado", help="Carga los gastos fijos del registro más reciente como plantilla para el mes actual"):
                st.session_state["copy_template_confirm"] = True
        if st.session_state.get("copy_template_confirm"):
            st.warning("¿Confirmar? Esto reemplazará los gastos fijos actuales con los del último mes guardado.")
            cc1, cc2 = st.columns(2)
            if cc1.button("✅ Confirmar copia", key="confirm_copy_template"):
                # Reset Actual column to 0 so the fixed expenses serve as a fresh template
                st.session_state.mp_fixed_rows_df["Actual"] = 0.0
                username = st.session_state.get("current_user")
                from ..business import save_user_rows
                save_user_rows(username, "fixed", st.session_state.mp_fixed_rows_df, ["row_id"])
                st.session_state["copy_template_confirm"] = False
                st.success("Gastos fijos copiados (montos actuales en cero para el nuevo mes).")
                st.rerun()
            if cc2.button("❌ Cancelar", key="cancel_copy_template"):
                st.session_state["copy_template_confirm"] = False
                st.rerun()

        # ── Download ──────────────────────────────────────────────────────────────
        with dl_col:
            mp_csv_download_button(monthly_df, "resumen_mensual.csv", "⬇️ Guardar CSV")

        # ── Table with delete ─────────────────────────────────────────────────────
        st.markdown("**Historial detallado**")
        display_monthly = monthly_df.copy()
        display_monthly = display_monthly.reindex(columns=MP_MONTHLY_COLUMNS)
        for col in ["Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Presupuesto", "Balance"]:
            display_monthly[col] = display_monthly[col].apply(mp_currency)
        st.dataframe(display_monthly.sort_values(by="Guardado", ascending=False), use_container_width=True, hide_index=True)

        st.markdown("**Eliminar registros del historial**")
        st.caption("Selecciona los índices (0, 1, 2…) de los registros a eliminar, separados por coma.")
        sorted_monthly = monthly_df.sort_values("Guardado", ascending=False).reset_index(drop=True)
        delete_idx_input = st.text_input("Índices a eliminar", key="monthly_delete_idx", placeholder="Ej: 0,2")
        if st.button("🗑️ Eliminar seleccionados", key="monthly_delete_btn"):
            try:
                idx_list = [int(x.strip()) for x in delete_idx_input.split(",") if x.strip()]
                if idx_list:
                    keep_mask = ~sorted_monthly.index.isin(idx_list)
                    new_monthly = sorted_monthly[keep_mask].reset_index(drop=True)
                    username = st.session_state.get("current_user")
                    save_monthly_rows_for_user(username, new_monthly)
                    st.session_state.mp_monthly_rows_df = get_monthly_rows(username)
                    st.success(f"Eliminados {len(idx_list)} registro(s).")
                    st.rerun()
            except ValueError:
                st.error("Formato inválido. Usa números separados por coma.")

