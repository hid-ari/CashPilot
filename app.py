import json
import os
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px


CATEGORIES = {
    "Vivienda": [
        "Renta / Hipoteca",
        "Mantenimiento",
        "Reparaciones",
        "Seguro",
        "Impuestos",
        "Condominio",
    ],
    "Servicios": [
        "Electricidad",
        "Agua",
        "Gas",
        "Internet",
        "Teléfono móvil",
        "Teléfono fijo",
        "TV / Streaming",
    ],
    "Alimentación": ["Supermercado", "Compras mayoristas", "Delivery", "Restaurantes"],
    "Transporte": [
        "Transporte público",
        "Combustible",
        "Taxi / Apps",
        "Mantenimiento auto",
        "Seguro auto",
        "Estacionamiento",
        "Peajes",
        "Licencias",
    ],
    "Salud": ["Seguro médico", "Medicamentos", "Consultas", "Terapias", "Dentista", "Exámenes"],
    "Finanzas": ["Préstamos", "Tarjetas de crédito", "Ahorro", "Inversiones", "Comisiones"],
    "Educación": ["Universidad", "Cursos", "Material", "Suscripciones"],
    "Cuidado": ["Higiene", "Peluquería", "Cosméticos"],
    "Entretenimiento": ["Salidas", "Suscripciones", "Gimnasio", "Hobbies", "Viajes"],
    "Familia": ["Colegiatura", "Pensión", "Mascotas"],
    "Otros": ["Ropa", "Regalos", "Donaciones", "Servicios profesionales"],
}

DEFAULT_ROWS = [
    {"Categoria": "Alimentación", "Gasto": "Supermercado", "Descripcion": "", "Presupuesto": 213.00, "Actual": 222.00},
    {"Categoria": "Finanzas", "Gasto": "Tarjetas de crédito", "Descripcion": "", "Presupuesto": 0.00, "Actual": 0.00},
    {"Categoria": "Educación", "Gasto": "Material", "Descripcion": "", "Presupuesto": 1312.00, "Actual": 313.00},
    {"Categoria": "Salud", "Gasto": "Exámenes", "Descripcion": "", "Presupuesto": 1312.00, "Actual": 22223.00},
]

DATA_FILE = "gastos.json"


def rows_to_frame(rows):
    frame = pd.DataFrame(rows, columns=["Categoria", "Gasto", "Descripcion", "Presupuesto", "Actual"])
    if frame.empty:
        frame = pd.DataFrame(columns=["Categoria", "Gasto", "Descripcion", "Presupuesto", "Actual"])
    frame["Categoria"] = frame.get("Categoria", pd.Series(dtype=str)).fillna("").astype(str)
    frame["Gasto"] = frame.get("Gasto", pd.Series(dtype=str)).fillna("").astype(str)
    frame["Descripcion"] = frame.get("Descripcion", pd.Series(dtype=str)).fillna("").astype(str)
    frame["Presupuesto"] = pd.to_numeric(frame.get("Presupuesto", 0), errors="coerce").fillna(0.0)
    frame["Actual"] = pd.to_numeric(frame.get("Actual", 0), errors="coerce").fillna(0.0)
    return frame[["Categoria", "Gasto", "Descripcion", "Presupuesto", "Actual"]]


def load_rows():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return rows_to_frame(data)
        except Exception:
            pass
    return rows_to_frame(DEFAULT_ROWS)


def save_rows(df):
    with open(DATA_FILE, "w", encoding="utf-8") as fh:
        json.dump(df.to_dict(orient="records"), fh, ensure_ascii=False, indent=2)


def format_currency(amount):
    return f"DOP {amount:,.2f}"


def init_state():
    if "rows_df" not in st.session_state:
        st.session_state.rows_df = load_rows()


def add_blank_row():
    blank_row = pd.DataFrame(
        [
            {
                "Categoria": "",
                "Gasto": "",
                "Descripcion": "",
                "Presupuesto": 0.0,
                "Actual": 0.0,
            }
        ]
    )
    st.session_state.rows_df = pd.concat([st.session_state.rows_df, blank_row], ignore_index=True)


def build_editor_panel():
    st.subheader("Gastos fijos")
    top_actions = st.columns([1, 5])
    if top_actions[0].button("＋", help="Agregar una fila vacía"):
        add_blank_row()
        st.rerun()

    df = st.session_state.rows_df.copy().reset_index(drop=True)

    filtro = st.text_input("Filtrar por categoría", value="")
    if filtro.strip():
        q = filtro.strip().lower()
        df = df[df["Categoria"].str.lower().str.contains(q, na=False)]

    if df.empty:
        st.info("No hay registros para mostrar.")
        return

    header_cols = st.columns([1.1, 1.7, 2.0, 1.1, 1.1, 0.6])
    header_cols[0].markdown("**Categoría**")
    header_cols[1].markdown("**Gasto**")
    header_cols[2].markdown("**Descripción opcional**")
    header_cols[3].markdown("**Presupuesto**")
    header_cols[4].markdown("**Actual**")
    header_cols[5].markdown("**Quitar**")

    updated_rows = []
    rows_to_remove = []

    for idx, row in df.iterrows():
        cols = st.columns([1.1, 1.7, 2.0, 1.1, 1.1, 0.6])

        current_category = row["Categoria"] if row["Categoria"] in CATEGORIES else ""
        category_options = list(CATEGORIES.keys())
        category_select_options = [""] + category_options
        category_index = category_select_options.index(current_category) if current_category in category_select_options else 0
        categoria = cols[0].selectbox(
            "Categoría",
            category_select_options,
            index=category_index,
            key=f"edit_categoria_{idx}",
            label_visibility="collapsed",
        )

        gasto_options = [""] + CATEGORIES.get(categoria, []) if categoria else [""]
        current_gasto = row["Gasto"] if row["Gasto"] in gasto_options else ""
        gasto_index = gasto_options.index(current_gasto) if current_gasto in gasto_options else 0
        gasto = cols[1].selectbox(
            "Gasto",
            gasto_options,
            index=gasto_index,
            key=f"edit_gasto_{idx}",
            label_visibility="collapsed",
        )

        descripcion = cols[2].text_input(
            "Descripción opcional",
            value=str(row.get("Descripcion", "")),
            key=f"edit_descripcion_{idx}",
            label_visibility="collapsed",
        )

        presupuesto = cols[3].number_input(
            "Presupuesto",
            min_value=0.0,
            value=float(row["Presupuesto"]),
            step=1.0,
            key=f"edit_presupuesto_{idx}",
            label_visibility="collapsed",
        )
        actual = cols[4].number_input(
            "Actual",
            min_value=0.0,
            value=float(row["Actual"]),
            step=1.0,
            key=f"edit_actual_{idx}",
            label_visibility="collapsed",
        )

        remove = cols[5].checkbox("Quitar", key=f"edit_remove_{idx}", label_visibility="collapsed")
        if remove:
            rows_to_remove.append(idx)

        updated_rows.append(
            {
                "Categoria": categoria,
                "Gasto": gasto,
                "Descripcion": descripcion,
                "Presupuesto": float(presupuesto),
                "Actual": float(actual),
            }
        )

    actions = st.columns([1, 1, 4])
    if actions[0].button("Aplicar cambios"):
        result = pd.DataFrame(updated_rows)
        if rows_to_remove:
            result = result.drop(index=rows_to_remove).reset_index(drop=True)
        st.session_state.rows_df = rows_to_frame(result.to_dict(orient="records"))
        st.success("Cambios aplicados.")
        st.rerun()

    if actions[1].button("Eliminar marcados"):
        result = pd.DataFrame(updated_rows)
        if rows_to_remove:
            result = result.drop(index=rows_to_remove).reset_index(drop=True)
        st.session_state.rows_df = rows_to_frame(result.to_dict(orient="records"))
        st.success("Registros eliminados.")
        st.rerun()


def build_summary_panel():
    df = st.session_state.rows_df.copy()
    if df.empty:
        budget = actual = diff = 0.0
    else:
        budget = float(df["Presupuesto"].sum())
        actual = float(df["Actual"].sum())
        diff = budget - actual

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Presupuesto total", format_currency(budget))
    c2.metric("Gasto total", format_currency(actual))
    c3.metric("Diferencia", format_currency(diff))
    c4.metric("Registros", f"{len(df)}")

    if not df.empty:
        chart_df = df.groupby("Categoria", as_index=True)[["Presupuesto", "Actual"]].sum()
        st.bar_chart(chart_df)


def build_actions():
    st.caption("Los datos base de la tabla inicial se mantienen solo para compatibilidad; las páginas principales se guardan automáticamente.")


MP_EXPENSE_CATEGORIES = [
    "Vivienda",
    "Servicios",
    "Alimentación",
    "Transporte",
    "Salud",
    "Finanzas",
    "Educación",
    "Cuidado",
    "Entretenimiento",
    "Familia",
    "Otros",
]

MP_INCOME_CATEGORIES = ["Trabajo", "Mesada", "Negocio", "Inversiones", "Regalos", "Otros"]

MP_SAVINGS_CATEGORIES = ["Emergencia", "Viajes", "Inversión", "Meta personal", "Otros"]

MP_DEFAULT_FIXED_ROWS = []

MP_DEFAULT_VARIABLE_ROWS = []

MP_DEFAULT_INCOME_ROWS = []

MP_DEFAULT_SAVINGS_ROWS = []

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MP_DATA_FILES = {
    "fixed": os.path.join(BASE_DIR, "gastos_fijos.json"),
    "variable": os.path.join(BASE_DIR, "gastos_variables.json"),
    "income": os.path.join(BASE_DIR, "ingresos.json"),
    "savings": os.path.join(BASE_DIR, "ahorros.json"),
    "monthly": os.path.join(BASE_DIR, "resumen_mensual.json"),
}


def mp_new_id():
    return uuid.uuid4().hex


def mp_normalize_expense_rows(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["row_id", "Categoria", "Descripcion", "Presupuesto", "Actual"])
    if "row_id" not in df.columns:
        df.insert(0, "row_id", [mp_new_id() for _ in range(len(df))])
    df["Categoria"] = df.get("Categoria", pd.Series(dtype=str)).fillna("").astype(str)
    df["Descripcion"] = df.get("Descripcion", pd.Series(dtype=str)).fillna("").astype(str)
    df["Presupuesto"] = pd.to_numeric(df.get("Presupuesto", 0), errors="coerce").fillna(0.0)
    df["Actual"] = pd.to_numeric(df.get("Actual", 0), errors="coerce").fillna(0.0)
    return df[["row_id", "Categoria", "Descripcion", "Presupuesto", "Actual"]]


def mp_normalize_income_rows(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["row_id", "Categoria", "Descripcion", "Ingreso"])
    if "row_id" not in df.columns:
        df.insert(0, "row_id", [mp_new_id() for _ in range(len(df))])
    df["Categoria"] = df.get("Categoria", pd.Series(dtype=str)).fillna("").astype(str)
    df["Descripcion"] = df.get("Descripcion", pd.Series(dtype=str)).fillna("").astype(str)
    df["Ingreso"] = pd.to_numeric(df.get("Ingreso", 0), errors="coerce").fillna(0.0)
    return df[["row_id", "Categoria", "Descripcion", "Ingreso"]]


def mp_normalize_savings_rows(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["row_id", "Categoria", "Descripcion", "Ahorro"])
    if "row_id" not in df.columns:
        df.insert(0, "row_id", [mp_new_id() for _ in range(len(df))])
    df["Categoria"] = df.get("Categoria", pd.Series(dtype=str)).fillna("").astype(str)
    df["Descripcion"] = df.get("Descripcion", pd.Series(dtype=str)).fillna("").astype(str)
    df["Ahorro"] = pd.to_numeric(df.get("Ahorro", 0), errors="coerce").fillna(0.0)
    return df[["row_id", "Categoria", "Descripcion", "Ahorro"]]


def mp_load_rows(file_key, default_rows, normalizer):
    file_path = MP_DATA_FILES[file_key]
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                return normalizer(json.load(fh))
        except Exception:
            pass
    return normalizer(default_rows)


def mp_save_rows(file_key, df, drop_cols):
    file_path = MP_DATA_FILES[file_key]
    payload = df.drop(columns=drop_cols, errors="ignore").to_dict(orient="records")
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def mp_load_monthly_rows():
    file_path = MP_DATA_FILES["monthly"]
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            df = pd.DataFrame(data)
            if df.empty:
                return pd.DataFrame(columns=["Mes", "Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Presupuesto", "Balance", "Guardado"])
            if "Ahorros" not in df.columns:
                df["Ahorros"] = 0.0
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=["Mes", "Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Presupuesto", "Balance", "Guardado"])


def mp_save_monthly_rows(df):
    file_path = MP_DATA_FILES["monthly"]
    payload = df.to_dict(orient="records")
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def mp_currency(amount):
    return f"DOP {amount:,.2f}"


def mp_init_state():
    if "mp_fixed_rows_df" not in st.session_state:
        st.session_state.mp_fixed_rows_df = mp_load_rows("fixed", MP_DEFAULT_FIXED_ROWS, mp_normalize_expense_rows)
    if "mp_variable_rows_df" not in st.session_state:
        st.session_state.mp_variable_rows_df = mp_load_rows("variable", MP_DEFAULT_VARIABLE_ROWS, mp_normalize_expense_rows)
    if "mp_income_rows_df" not in st.session_state:
        st.session_state.mp_income_rows_df = mp_load_rows("income", MP_DEFAULT_INCOME_ROWS, mp_normalize_income_rows)
    if "mp_savings_rows_df" not in st.session_state:
        st.session_state.mp_savings_rows_df = mp_load_rows("savings", MP_DEFAULT_SAVINGS_ROWS, mp_normalize_savings_rows)
    if "mp_monthly_rows_df" not in st.session_state:
        st.session_state.mp_monthly_rows_df = mp_load_monthly_rows()


def mp_add_blank_expense_row(state_key):
    blank_row = pd.DataFrame(
        [
            {
                "row_id": mp_new_id(),
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
                "row_id": mp_new_id(),
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
                "row_id": mp_new_id(),
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


def mp_expense_page(title, state_key, file_key, default_rows):
    st.header(title)

    action_cols = st.columns([0.7, 3.6])
    if action_cols[0].button("＋", key=f"{state_key}_add", help="Agregar fila vacía"):
        mp_add_blank_expense_row(state_key)
        st.rerun()

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

        category_options = [""] + MP_EXPENSE_CATEGORIES
        current_category = row["Categoria"] if row["Categoria"] in MP_EXPENSE_CATEGORIES else ""
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

    action_cols = st.columns([0.7, 3.6])
    if action_cols[0].button("＋", key="income_add", help="Agregar fila vacía"):
        mp_add_blank_income_row(state_key)
        st.rerun()

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

        category_options = [""] + MP_INCOME_CATEGORIES
        current_category = row["Categoria"] if row["Categoria"] in MP_INCOME_CATEGORIES else ""
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
    mp_save_rows("income", st.session_state[state_key], ["row_id"])

    if st.button("Eliminar marcados", key="income_delete"):
        st.session_state[state_key] = st.session_state[state_key][~st.session_state[state_key]["row_id"].isin(rows_to_remove)].reset_index(drop=True)
        mp_save_rows("income", st.session_state[state_key], ["row_id"])
        st.success("Registros eliminados.")
        st.rerun()


def mp_savings_page():
    state_key = "mp_savings_rows_df"
    st.header("Ahorros")

    action_cols = st.columns([0.7, 3.6])
    if action_cols[0].button("＋", key="savings_add", help="Agregar fila vacía"):
        mp_add_blank_savings_row(state_key)
        st.rerun()

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

        category_options = [""] + MP_SAVINGS_CATEGORIES
        current_category = row["Categoria"] if row["Categoria"] in MP_SAVINGS_CATEGORIES else ""
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
    mp_save_rows("savings", st.session_state[state_key], ["row_id"])

    if st.button("Eliminar marcados", key="savings_delete"):
        st.session_state[state_key] = st.session_state[state_key][~st.session_state[state_key]["row_id"].isin(rows_to_remove)].reset_index(drop=True)
        mp_save_rows("savings", st.session_state[state_key], ["row_id"])
        st.success("Registros eliminados.")
        st.rerun()


def mp_home_page():
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

    current_month = datetime.now().strftime("%Y-%m")
    current_saved_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    st.title("CashPilot")
    st.caption("Dashboard financiero personal")
    st.header("Dashboard")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Ingresos", mp_currency(income_total))
    c2.metric("Gastos fijos", mp_currency(fixed_actual))
    c3.metric("Gastos variables", mp_currency(variable_actual))
    c4.metric("Presupuesto", mp_currency(total_budget))
    c5.metric("Ahorros", mp_currency(savings_total))
    c6.metric("Balance", mp_currency(balance))

    save_col, info_col = st.columns([1, 4])
    with save_col:
        if st.button("Guardar mes", key="save_month_button"):
            monthly_df = st.session_state.mp_monthly_rows_df.copy()
            record = {
                "Mes": current_month,
                "Ingresos": income_total,
                "Gastos fijos": fixed_actual,
                "Gastos variables": variable_actual,
                "Ahorros": savings_total,
                "Presupuesto": total_budget,
                "Balance": balance,
                "Guardado": current_saved_at,
            }
            if not monthly_df.empty and "Mes" in monthly_df.columns and current_month in monthly_df["Mes"].astype(str).values:
                monthly_df = monthly_df[monthly_df["Mes"].astype(str) != current_month]
            monthly_df = pd.concat([monthly_df, pd.DataFrame([record])], ignore_index=True)
            st.session_state.mp_monthly_rows_df = monthly_df
            mp_save_monthly_rows(monthly_df)
            st.success("Mes guardado en el historial.")
    with info_col:
        st.info(f"Mes actual: {current_month}")

    st.divider()
    st.subheader("Gráfica resumen")
    # Prepare data for pies
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

    col1, col2, col3, col4 = st.columns(4)

    # Gastos pie (by actual)
    with col1:
        st.markdown("**Gastos (Actual)**")
        if not expenses_by_cat.empty and expenses_by_cat["Valor"].sum() > 0:
            fig1 = px.pie(expenses_by_cat, names="Categoria", values="Valor", title="Gastos por categoría (Actual)")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No hay gastos registrados.")

    # Ingresos pie
    with col2:
        st.markdown("**Ingresos**")
        if not income_by_cat.empty and income_by_cat["Ingreso"].sum() > 0:
            fig2 = px.pie(income_by_cat, names="Categoria", values="Ingreso", title="Ingresos por categoría")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay ingresos registrados.")

    # Presupuesto pie
    with col3:
        st.markdown("**Presupuesto**")
        if not budget_by_cat.empty and budget_by_cat["Valor"].sum() > 0:
            fig3 = px.pie(budget_by_cat, names="Categoria", values="Valor", title="Presupuesto por categoría")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No hay presupuesto registrado.")

    # Ahorros pie
    with col4:
        st.markdown("**Ahorros**")
        if not savings_by_cat.empty and savings_by_cat["Ahorro"].sum() > 0:
            fig4 = px.pie(savings_by_cat, names="Categoria", values="Ahorro", title="Ahorros por categoría")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No hay ahorros registrados.")

    st.divider()
    st.subheader("Resumen mensual guardado")
    monthly_df = st.session_state.mp_monthly_rows_df.copy()
    if monthly_df.empty:
        st.info("Todavía no has guardado ningún mes.")
    else:
        display_monthly = monthly_df.copy()
        if "Ahorros" not in display_monthly.columns:
            display_monthly["Ahorros"] = 0.0
        for col in ["Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Presupuesto", "Balance"]:
            display_monthly[col] = display_monthly[col].apply(mp_currency)
        st.dataframe(display_monthly.sort_values(by="Mes", ascending=False), use_container_width=True, hide_index=True)


def mp_sidebar_page():
    st.sidebar.title("Navegación")
    return st.sidebar.radio("Ir a", ["Home", "Gastos fijos", "Gastos variables", "Ingresos", "Ahorros"], index=0, label_visibility="collapsed")


def main():
    st.set_page_config(page_title="CashPilot", layout="wide")
    mp_init_state()

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


if __name__ == "__main__":
    main()
