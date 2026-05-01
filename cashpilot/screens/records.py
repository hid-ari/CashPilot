from __future__ import annotations

import pandas as pd
import streamlit as st

from ..business import (
    MP_EXPENSE_CATEGORIES,
    MP_INCOME_CATEGORIES,
    MP_SAVINGS_CATEGORIES,
    get_all_expense_categories,
    get_all_income_categories,
    get_all_savings_categories,
    new_id,
    save_user_rows,
)


def mp_csv_download_button(df, file_name, label="Guardar CSV", drop_cols=None):
    export_df = df.drop(columns=drop_cols or [], errors="ignore").copy()
    csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label,
        data=csv_data,
        file_name=file_name,
        mime="text/csv",
    )


def mp_add_blank_expense_row(state_key):
    blank_row = pd.DataFrame(
        [
            {
                "row_id": new_id(),
                "Categoria": "",
                "Descripcion": "",
                "Presupuesto": 0.0,
                "Actual": 0.0,
            }
        ]
    )
    st.session_state[state_key] = pd.concat([st.session_state[state_key], blank_row], ignore_index=True)


def mp_add_blank_income_row(state_key):
    blank_row = pd.DataFrame(
        [
            {
                "row_id": new_id(),
                "Categoria": "",
                "Descripcion": "",
                "Ingreso": 0.0,
            }
        ]
    )
    st.session_state[state_key] = pd.concat([st.session_state[state_key], blank_row], ignore_index=True)


def mp_add_blank_savings_row(state_key):
    blank_row = pd.DataFrame(
        [
            {
                "row_id": new_id(),
                "Categoria": "",
                "Descripcion": "",
                "Ahorro": 0.0,
            }
        ]
    )
    st.session_state[state_key] = pd.concat([st.session_state[state_key], blank_row], ignore_index=True)


def mp_merge_rows(full_df, updated_rows):
    updated_df = pd.DataFrame(updated_rows)
    if updated_df.empty:
        return full_df
    updated_df = updated_df.set_index("row_id")
    merged = full_df.copy().set_index("row_id")
    for row_id, values in updated_df.to_dict(orient="index").items():
        if row_id in merged.index:
            for col, value in values.items():
                merged.at[row_id, col] = value
    return merged.reset_index()


def render_expense_page(title, state_key, file_key, default_rows):
    st.header(title)
    if title == "Gastos fijos":
        st.caption("💡 Gastos que se repiten cada mes con un monto fijo: alquiler, cuotas, suscripciones, etc.")
    else:
        st.caption("💡 Gastos que varían mes a mes: comida, transporte, entretenimiento, etc.")

    username = st.session_state.get("current_user")
    expense_categories = get_all_expense_categories(username) if username else MP_EXPENSE_CATEGORIES

    action_cols = st.columns([0.7, 1.2, 3.0])
    if action_cols[0].button("＋", key=f"{state_key}_add", help="Agregar fila vacía"):
        mp_add_blank_expense_row(state_key)
        st.rerun()
    with action_cols[1]:
        mp_csv_download_button(st.session_state[state_key], f"{state_key}.csv", "Guardar CSV", ["row_id"])

    filtro = st.text_input("Filtrar por categoría", key=f"{state_key}_filter")
    full_df = st.session_state[state_key].copy().reset_index(drop=True)
    if filtro.strip():
        q = filtro.strip().lower()
        display_df = full_df[full_df["Categoria"].str.lower().str.contains(q, na=False)]
    else:
        display_df = full_df

    if display_df.empty:
        st.info("No hay registros para mostrar.")
        return

    head = st.columns([1.35, 2.2, 1.15, 1.15, 0.7])
    head[0].markdown("**Categoría**")
    head[1].markdown("**Descripción opcional**")
    head[2].markdown("**Presupuesto**")
    head[3].markdown("**Actual**")
    head[4].markdown("**Quitar**")

    updated_rows = []
    rows_to_remove = []

    for _, row in display_df.iterrows():
        row_id = row["row_id"]
        cols = st.columns([1.35, 2.2, 1.15, 1.15, 0.7])

        category_options = [""] + expense_categories
        current_category = row["Categoria"] if row["Categoria"] in expense_categories else ""
        category_index = category_options.index(current_category) if current_category in category_options else 0
        categoria = cols[0].selectbox(
            "Categoría",
            category_options,
            index=category_index,
            key=f"{state_key}_cat_{row_id}",
            label_visibility="collapsed",
        )

        descripcion = cols[1].text_input(
            "Descripción",
            value=str(row.get("Descripcion", "")),
            key=f"{state_key}_desc_{row_id}",
            label_visibility="collapsed",
        )

        presupuesto = cols[2].number_input(
            "Presupuesto",
            min_value=0.0,
            value=float(row.get("Presupuesto", 0.0)),
            step=1.0,
            key=f"{state_key}_budget_{row_id}",
            label_visibility="collapsed",
        )
        actual = cols[3].number_input(
            "Actual",
            min_value=0.0,
            value=float(row.get("Actual", 0.0)),
            step=1.0,
            key=f"{state_key}_actual_{row_id}",
            label_visibility="collapsed",
        )
        remove = cols[4].checkbox("Quitar", key=f"{state_key}_remove_{row_id}", label_visibility="collapsed")

        if remove:
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
    save_user_rows(st.session_state.get("current_user"), file_key, st.session_state[state_key], ["row_id"])

    bottom_cols = st.columns([1, 1, 4])
    if bottom_cols[0].button("Eliminar marcados", key=f"{state_key}_delete"):
        st.session_state[state_key] = st.session_state[state_key][~st.session_state[state_key]["row_id"].isin(rows_to_remove)].reset_index(drop=True)
        save_user_rows(st.session_state.get("current_user"), file_key, st.session_state[state_key], ["row_id"])
        st.success("Registros eliminados.")
        st.rerun()


def render_income_page():
    state_key = "mp_income_rows_df"
    st.header("Ingresos")
    st.caption("💡 Registra todas tus fuentes de ingresos del mes: salario, freelance, negocios, etc.")

    username = st.session_state.get("current_user")
    income_categories = get_all_income_categories(username) if username else MP_INCOME_CATEGORIES

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

    head = st.columns([1.35, 2.6, 1.25, 0.7])
    head[0].markdown("**Categoría**")
    head[1].markdown("**Descripción**")
    head[2].markdown("**Ingreso**")
    head[3].markdown("**Quitar**")

    updated_rows = []
    rows_to_remove = []

    for _, row in display_df.iterrows():
        row_id = row["row_id"]
        cols = st.columns([1.35, 2.6, 1.25, 0.7])

        category_options = [""] + income_categories
        current_category = row["Categoria"] if row["Categoria"] in income_categories else ""
        category_index = category_options.index(current_category) if current_category in category_options else 0
        categoria = cols[0].selectbox(
            "Categoría",
            category_options,
            index=category_index,
            key=f"income_cat_{row_id}",
            label_visibility="collapsed",
        )

        descripcion = cols[1].text_input(
            "Descripción",
            value=str(row.get("Descripcion", "")),
            key=f"income_desc_{row_id}",
            label_visibility="collapsed",
        )

        ingreso = cols[2].number_input(
            "Ingreso",
            min_value=0.0,
            value=float(row.get("Ingreso", 0.0)),
            step=1.0,
            key=f"income_value_{row_id}",
            label_visibility="collapsed",
        )
        remove = cols[3].checkbox("Quitar", key=f"income_remove_{row_id}", label_visibility="collapsed")

        if remove:
            rows_to_remove.append(row_id)

        updated_rows.append(
            {
                "row_id": row_id,
                "Categoria": categoria,
                "Descripcion": descripcion,
                "Ingreso": float(ingreso),
            }
        )

    st.session_state[state_key] = mp_merge_rows(full_df, updated_rows)
    save_user_rows(st.session_state.get("current_user"), "income", st.session_state[state_key], ["row_id"])

    if st.button("Eliminar marcados", key="income_delete"):
        st.session_state[state_key] = st.session_state[state_key][~st.session_state[state_key]["row_id"].isin(rows_to_remove)].reset_index(drop=True)
        save_user_rows(st.session_state.get("current_user"), "income", st.session_state[state_key], ["row_id"])
        st.success("Registros eliminados.")
        st.rerun()


def render_savings_page():
    state_key = "mp_savings_rows_df"
    st.header("Ahorros")
    st.caption("💡 Registra los montos que apartas cada mes para distintos objetivos de ahorro.")

    username = st.session_state.get("current_user")
    savings_categories = get_all_savings_categories(username) if username else MP_SAVINGS_CATEGORIES

    action_cols = st.columns([0.7, 1.2, 3.0])
    if action_cols[0].button("＋", key="savings_add", help="Agregar fila vacía"):
        mp_add_blank_savings_row(state_key)
        st.rerun()
    with action_cols[1]:
        mp_csv_download_button(st.session_state[state_key], "ahorros.csv", "Guardar CSV", ["row_id"])

    filtro = st.text_input("Filtrar por categoría", key="savings_filter")
    full_df = st.session_state[state_key].copy().reset_index(drop=True)
    if filtro.strip():
        q = filtro.strip().lower()
        display_df = full_df[full_df["Categoria"].str.lower().str.contains(q, na=False)]
    else:
        display_df = full_df

    if display_df.empty:
        st.info("No hay ahorros para mostrar.")
        return

    head = st.columns([1.35, 2.6, 1.25, 0.7])
    head[0].markdown("**Categoría**")
    head[1].markdown("**Descripción**")
    head[2].markdown("**Ahorro**")
    head[3].markdown("**Quitar**")

    updated_rows = []
    rows_to_remove = []

    for _, row in display_df.iterrows():
        row_id = row["row_id"]
        cols = st.columns([1.35, 2.6, 1.25, 0.7])

        category_options = [""] + savings_categories
        current_category = row["Categoria"] if row["Categoria"] in savings_categories else ""
        category_index = category_options.index(current_category) if current_category in category_options else 0
        categoria = cols[0].selectbox(
            "Categoría",
            category_options,
            index=category_index,
            key=f"savings_cat_{row_id}",
            label_visibility="collapsed",
        )

        descripcion = cols[1].text_input(
            "Descripción",
            value=str(row.get("Descripcion", "")),
            key=f"savings_desc_{row_id}",
            label_visibility="collapsed",
        )

        ahorro = cols[2].number_input(
            "Ahorro",
            min_value=0.0,
            value=float(row.get("Ahorro", 0.0)),
            step=1.0,
            key=f"savings_value_{row_id}",
            label_visibility="collapsed",
        )
        remove = cols[3].checkbox("Quitar", key=f"savings_remove_{row_id}", label_visibility="collapsed")

        if remove:
            rows_to_remove.append(row_id)

        updated_rows.append(
            {
                "row_id": row_id,
                "Categoria": categoria,
                "Descripcion": descripcion,
                "Ahorro": float(ahorro),
            }
        )

    st.session_state[state_key] = mp_merge_rows(full_df, updated_rows)
    save_user_rows(st.session_state.get("current_user"), "savings", st.session_state[state_key], ["row_id"])

    if st.button("Eliminar marcados", key="savings_delete"):
        st.session_state[state_key] = st.session_state[state_key][~st.session_state[state_key]["row_id"].isin(rows_to_remove)].reset_index(drop=True)
        save_user_rows(st.session_state.get("current_user"), "savings", st.session_state[state_key], ["row_id"])
        st.success("Registros eliminados.")
        st.rerun()

