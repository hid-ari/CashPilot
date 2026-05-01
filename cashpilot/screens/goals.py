from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import streamlit as st

from ..business import (
    MP_SAVINGS_CATEGORIES,
    format_currency,
    get_all_savings_categories,
    get_user_goals,
    new_id,
    save_user_goals,
)


def _mp_currency(amount: float) -> str:
    currency = "DOP"
    try:
        currency = st.session_state.get("profile", {}).get("currency", "DOP")
    except Exception:
        pass
    return format_currency(amount, currency)


def render_goals_page():
    st.header("🎯 Metas financieras")
    st.caption("Define objetivos de ahorro con montos y fechas límite. Sigue tu progreso con barras visuales.")

    username = st.session_state.get("current_user")
    savings_cats = get_all_savings_categories(username) if username else MP_SAVINGS_CATEGORIES

    # ── Add goal ──────────────────────────────────────────────────────────────────
    with st.expander("➕ Nueva meta", expanded=False):
        with st.form("add_goal_form", clear_on_submit=True):
            g1, g2 = st.columns(2)
            goal_name = g1.text_input("Nombre de la meta", placeholder="Ej: Vacaciones Cancún")
            goal_cat = g2.selectbox("Categoría", [""] + savings_cats)
            g3, g4 = st.columns(2)
            goal_target = g3.number_input("Monto objetivo", min_value=0.0, step=100.0)
            goal_actual = g4.number_input("Monto ahorrado hasta ahora", min_value=0.0, step=100.0)
            goal_deadline = st.date_input("Fecha límite (opcional)", value=None)
            submit_goal = st.form_submit_button("Crear meta")

        if submit_goal:
            if not goal_name.strip():
                st.warning("El nombre de la meta no puede estar vacío.")
            elif goal_target <= 0:
                st.warning("El monto objetivo debe ser mayor a cero.")
            else:
                df = get_user_goals(username)
                deadline_str = str(goal_deadline) if goal_deadline else ""
                new_row = pd.DataFrame([{
                    "id": new_id(),
                    "Nombre": goal_name.strip(),
                    "Categoria": goal_cat,
                    "Meta": float(goal_target),
                    "Actual": float(goal_actual),
                    "Fecha_limite": deadline_str,
                    "Creado": datetime.now().strftime("%Y-%m-%d"),
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_user_goals(username, df)
                st.success(f"Meta '{goal_name}' creada.")
                st.rerun()

    # ── List goals ────────────────────────────────────────────────────────────────
    df = get_user_goals(username)

    if df.empty:
        st.info("Aún no tienes metas financieras. ¡Crea una con el botón de arriba!")
        return

    today = date.today()
    st.divider()

    for i, row in df.iterrows():
        goal_name = str(row["Nombre"])
        meta = float(row["Meta"])
        actual = float(row["Actual"])
        categoria = str(row["Categoria"])
        deadline_str = str(row["Fecha_limite"])
        goal_id = str(row["id"])

        pct = min(actual / meta * 100, 100) if meta > 0 else 0
        remaining = max(meta - actual, 0)

        # Check deadline alert
        deadline_alert = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                days_left = (deadline - today).days
                if days_left < 0:
                    deadline_alert = ("error", f"⛔ Plazo vencido el {deadline_str}")
                elif days_left <= 30:
                    deadline_alert = ("warning", f"⚠️ Quedan {days_left} días (vence {deadline_str})")
                else:
                    deadline_alert = ("info", f"📅 Vence el {deadline_str} ({days_left} días)")
            except ValueError:
                pass

        with st.container():
            col_title, col_del = st.columns([5, 1])
            col_title.markdown(f"### {goal_name}" + (f" · _{categoria}_" if categoria else ""))
            if col_del.button("🗑️", key=f"del_goal_{goal_id}", help="Eliminar meta"):
                new_df = df[df["id"] != goal_id].reset_index(drop=True)
                save_user_goals(username, new_df)
                st.success(f"Meta '{goal_name}' eliminada.")
                st.rerun()

            if deadline_alert:
                level, msg = deadline_alert
                if level == "error":
                    st.error(msg)
                elif level == "warning":
                    st.warning(msg)
                else:
                    st.info(msg)

            prog_col1, prog_col2 = st.columns([3, 1])
            with prog_col1:
                st.progress(pct / 100, text=f"{pct:.1f}% completado")
            with prog_col2:
                st.caption(f"{_mp_currency(actual)} / {_mp_currency(meta)}")

            st.caption(f"Falta: **{_mp_currency(remaining)}**")

            # ── Edit section ──────────────────────────────────────────────────────
            with st.expander("✏️ Editar meta", expanded=False):
                with st.form(f"edit_goal_{goal_id}"):
                    e1, e2 = st.columns(2)
                    new_actual = e1.number_input(
                        "Monto ahorrado hasta ahora",
                        min_value=0.0,
                        value=actual,
                        step=100.0,
                        key=f"edit_actual_{goal_id}",
                    )
                    new_meta = e2.number_input(
                        "Nuevo monto objetivo",
                        min_value=0.0,
                        value=meta,
                        step=100.0,
                        key=f"edit_meta_{goal_id}",
                    )
                    new_deadline = st.date_input(
                        "Nueva fecha límite",
                        value=datetime.strptime(deadline_str, "%Y-%m-%d").date() if deadline_str else None,
                        key=f"edit_deadline_{goal_id}",
                    )
                    save_edit = st.form_submit_button("Guardar cambios")
                if save_edit:
                    df.at[i, "Actual"] = float(new_actual)
                    df.at[i, "Meta"] = float(new_meta)
                    df.at[i, "Fecha_limite"] = str(new_deadline) if new_deadline else ""
                    save_user_goals(username, df)
                    st.success("Meta actualizada.")
                    st.rerun()

            st.divider()
