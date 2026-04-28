import json
import os

import pandas as pd
import streamlit as st


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
    {"Categoria": "Alimentación", "Gasto": "Supermercado", "Presupuesto": 213.00, "Actual": 222.00},
    {"Categoria": "Finanzas", "Gasto": "Tarjetas de crédito", "Presupuesto": 0.00, "Actual": 0.00},
    {"Categoria": "Educación", "Gasto": "Material", "Presupuesto": 1312.00, "Actual": 313.00},
    {"Categoria": "Salud", "Gasto": "Exámenes", "Presupuesto": 1312.00, "Actual": 22223.00},
]

DATA_FILE = "gastos.json"


def rows_to_frame(rows):
    frame = pd.DataFrame(rows, columns=["Categoria", "Gasto", "Presupuesto", "Actual"])
    if frame.empty:
        frame = pd.DataFrame(columns=["Categoria", "Gasto", "Presupuesto", "Actual"])
    frame["Categoria"] = frame.get("Categoria", pd.Series(dtype=str)).fillna("Otros").astype(str)
    frame["Gasto"] = frame.get("Gasto", pd.Series(dtype=str)).fillna("").astype(str)
    frame["Presupuesto"] = pd.to_numeric(frame.get("Presupuesto", 0), errors="coerce").fillna(0.0)
    frame["Actual"] = pd.to_numeric(frame.get("Actual", 0), errors="coerce").fillna(0.0)
    return frame[["Categoria", "Gasto", "Presupuesto", "Actual"]]


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
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "Alimentación"


def build_catalog_panel():
    st.subheader("Catálogo de categorías")
    category = st.selectbox("Categoría", list(CATEGORIES.keys()), key="selected_category")
    st.write(f"Elementos de {category}")
    st.markdown("\n".join(f"- {item}" for item in CATEGORIES.get(category, [])))


def build_add_form():
    st.subheader("Nuevo gasto fijo")
    with st.form("add_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 1])
        with col1:
            categoria = st.selectbox("Categoría", list(CATEGORIES.keys()), index=list(CATEGORIES.keys()).index(st.session_state.selected_category))
            gasto_opciones = CATEGORIES.get(categoria, [])
            gasto = st.selectbox("Gasto", gasto_opciones + ["Otro"], index=0 if gasto_opciones else 0)
            gasto_custom = st.text_input("Si elegiste Otro, escribe el gasto", value="") if gasto == "Otro" else ""
        with col2:
            presupuesto = st.number_input("Presupuesto", min_value=0.0, value=0.0, step=1.0)
            actual = st.number_input("Actual", min_value=0.0, value=0.0, step=1.0)

        submitted = st.form_submit_button("Agregar")

    if submitted:
        gasto_final = gasto_custom.strip() if gasto == "Otro" else gasto
        if not gasto_final:
            st.warning("Escribe un gasto válido.")
            return
        new_row = pd.DataFrame([
            {
                "Categoria": categoria,
                "Gasto": gasto_final,
                "Presupuesto": float(presupuesto),
                "Actual": float(actual),
            }
        ])
        st.session_state.rows_df = pd.concat([st.session_state.rows_df, new_row], ignore_index=True)
        st.success("Registro agregado.")


def build_editor_panel():
    st.subheader("Gastos fijos")
    df = st.session_state.rows_df.copy().reset_index(drop=True)

    filtro = st.text_input("Filtrar por categoría o gasto", value="")
    if filtro.strip():
        q = filtro.strip().lower()
        df = df[df["Categoria"].str.lower().str.contains(q, na=False) | df["Gasto"].str.lower().str.contains(q, na=False)]

    if df.empty:
        st.info("No hay registros para mostrar.")
        return

    header_cols = st.columns([1.2, 1.8, 1.2, 1.2, 0.6])
    header_cols[0].markdown("**Categoría**")
    header_cols[1].markdown("**Gasto**")
    header_cols[2].markdown("**Presupuesto**")
    header_cols[3].markdown("**Actual**")
    header_cols[4].markdown("**Quitar**")

    updated_rows = []
    rows_to_remove = []

    for idx, row in df.iterrows():
        cols = st.columns([1.2, 1.8, 1.2, 1.2, 0.6])

        current_category = row["Categoria"] if row["Categoria"] in CATEGORIES else "Otros"
        category_options = list(CATEGORIES.keys())
        category_index = category_options.index(current_category)
        categoria = cols[0].selectbox(
            "Categoría",
            category_options,
            index=category_index,
            key=f"edit_categoria_{idx}",
            label_visibility="collapsed",
        )

        gasto_options = CATEGORIES.get(categoria, [])
        current_gasto = row["Gasto"] if row["Gasto"] in gasto_options else (gasto_options[0] if gasto_options else "")
        gasto_index = gasto_options.index(current_gasto) if current_gasto in gasto_options else 0
        gasto = cols[1].selectbox(
            "Gasto",
            gasto_options,
            index=gasto_index,
            key=f"edit_gasto_{idx}",
            label_visibility="collapsed",
        )

        presupuesto = cols[2].number_input(
            "Presupuesto",
            min_value=0.0,
            value=float(row["Presupuesto"]),
            step=1.0,
            key=f"edit_presupuesto_{idx}",
            label_visibility="collapsed",
        )
        actual = cols[3].number_input(
            "Actual",
            min_value=0.0,
            value=float(row["Actual"]),
            step=1.0,
            key=f"edit_actual_{idx}",
            label_visibility="collapsed",
        )

        remove = cols[4].checkbox("Quitar", key=f"edit_remove_{idx}", label_visibility="collapsed")
        if remove:
            rows_to_remove.append(idx)

        updated_rows.append(
            {
                "Categoria": categoria,
                "Gasto": gasto,
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
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Guardar"):
            try:
                save_rows(st.session_state.rows_df)
                st.success(f"Datos guardados en {DATA_FILE}.")
            except Exception as exc:
                st.error(f"No se pudo guardar: {exc}")
    with col2:
        if st.button("Cargar"):
            st.session_state.rows_df = load_rows()
            st.success("Datos cargados.")
    with col3:
        if st.button("Restaurar datos iniciales"):
            st.session_state.rows_df = rows_to_frame(DEFAULT_ROWS)
            st.info("Datos iniciales restaurados.")


def main():
    st.set_page_config(page_title="Control de gastos", layout="wide")
    init_state()

    st.title("Control de gastos")
    st.caption("Organiza categorías, presupuesto y gasto real en una sola pantalla.")

    left, right = st.columns([1, 2])
    with left:
        build_catalog_panel()
        build_add_form()
    with right:
        build_summary_panel()
        st.divider()
        build_editor_panel()

    st.divider()
    build_actions()


if __name__ == "__main__":
    main()
