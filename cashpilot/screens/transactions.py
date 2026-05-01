from __future__ import annotations

import io
from datetime import date, datetime

import pandas as pd
import streamlit as st

from ..business import (
    MP_EXPENSE_CATEGORIES,
    MP_INCOME_CATEGORIES,
    MP_TRANSACTION_COLUMNS,
    format_currency,
    get_all_expense_categories,
    get_all_income_categories,
    get_user_transactions,
    new_id,
    save_user_transactions,
)

TRANSACTION_TYPES = ["Gasto", "Ingreso"]


def _mp_currency(amount: float) -> str:
    currency = "DOP"
    try:
        currency = st.session_state.get("profile", {}).get("currency", "DOP")
    except Exception:
        pass
    return format_currency(amount, currency)


def render_transactions_page():
    st.header("💳 Transacciones")
    st.caption("Registra movimientos individuales día a día con fecha, categoría y monto.")

    username = st.session_state.get("current_user")
    expense_cats = get_all_expense_categories(username) if username else MP_EXPENSE_CATEGORIES
    income_cats = get_all_income_categories(username) if username else MP_INCOME_CATEGORIES

    # ── Add transaction ───────────────────────────────────────────────────────────
    with st.expander("➕ Agregar transacción", expanded=False):
        with st.form("add_transaction_form", clear_on_submit=True):
            f1, f2 = st.columns(2)
            tx_date = f1.date_input("Fecha", value=date.today(), key="tx_date")
            tx_type = f2.selectbox("Tipo", TRANSACTION_TYPES, key="tx_type")

            f3, f4 = st.columns(2)
            if tx_type == "Gasto":
                cat_options = [""] + expense_cats
            else:
                cat_options = [""] + income_cats
            tx_cat = f3.selectbox("Categoría", cat_options, key="tx_cat")
            tx_monto = f4.number_input("Monto", min_value=0.0, step=1.0, key="tx_monto")
            tx_desc = st.text_input("Descripción (opcional)", key="tx_desc")
            submit_tx = st.form_submit_button("Guardar transacción")

        if submit_tx:
            if tx_monto <= 0:
                st.warning("El monto debe ser mayor a cero.")
            else:
                df = get_user_transactions(username)
                new_row = pd.DataFrame([{
                    "id": new_id(),
                    "Fecha": str(tx_date),
                    "Tipo": tx_type,
                    "Categoria": tx_cat,
                    "Descripcion": tx_desc,
                    "Monto": float(tx_monto),
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_user_transactions(username, df)
                st.success("Transacción guardada.")
                st.rerun()

    # ── Import CSV ────────────────────────────────────────────────────────────────
    with st.expander("📂 Importar CSV", expanded=False):
        st.caption(
            "El CSV debe tener columnas: **Fecha, Tipo, Categoria, Descripcion, Monto**. "
            "Tipo debe ser 'Gasto' o 'Ingreso'."
        )
        uploaded_file = st.file_uploader("Seleccionar archivo CSV", type=["csv"], key="tx_csv_upload")
        if uploaded_file is not None:
            if st.button("Importar", key="import_csv_btn"):
                try:
                    import_df = pd.read_csv(uploaded_file)
                    required_cols = {"Fecha", "Tipo", "Categoria", "Descripcion", "Monto"}
                    missing = required_cols - set(import_df.columns)
                    if missing:
                        st.error(f"Faltan columnas: {', '.join(missing)}")
                    else:
                        import_df["id"] = [new_id() for _ in range(len(import_df))]
                        import_df["Monto"] = pd.to_numeric(import_df["Monto"], errors="coerce").fillna(0.0)
                        import_df["Fecha"] = import_df["Fecha"].astype(str)
                        import_df["Tipo"] = import_df["Tipo"].fillna("Gasto").astype(str)
                        import_df["Categoria"] = import_df["Categoria"].fillna("").astype(str)
                        import_df["Descripcion"] = import_df["Descripcion"].fillna("").astype(str)
                        existing = get_user_transactions(username)
                        combined = pd.concat([existing, import_df[MP_TRANSACTION_COLUMNS]], ignore_index=True)
                        save_user_transactions(username, combined)
                        st.success(f"Importadas {len(import_df)} transacciones.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al leer el CSV: {e}")

    # ── Filters ───────────────────────────────────────────────────────────────────
    df = get_user_transactions(username)

    if df.empty:
        st.info("Aún no tienes transacciones registradas. Usa el formulario de arriba para agregar una.")
        return

    st.divider()
    st.subheader("🔍 Filtros")
    fc1, fc2, fc3 = st.columns(3)
    filter_type = fc1.selectbox("Tipo", ["Todos"] + TRANSACTION_TYPES, key="filter_type")
    all_cats = sorted(df["Categoria"].dropna().unique().tolist())
    filter_cat = fc2.selectbox("Categoría", ["Todas"] + all_cats, key="filter_cat")
    filter_search = fc3.text_input("Buscar descripción", key="filter_search")

    date_col1, date_col2 = st.columns(2)
    try:
        min_date = pd.to_datetime(df["Fecha"], errors="coerce").min()
        max_date = pd.to_datetime(df["Fecha"], errors="coerce").max()
        min_date = min_date.date() if pd.notna(min_date) else date.today()
        max_date = max_date.date() if pd.notna(max_date) else date.today()
    except Exception:
        min_date = max_date = date.today()
    filter_from = date_col1.date_input("Desde", value=min_date, key="filter_from")
    filter_to = date_col2.date_input("Hasta", value=max_date, key="filter_to")

    # Apply filters
    filtered = df.copy()
    if filter_type != "Todos":
        filtered = filtered[filtered["Tipo"] == filter_type]
    if filter_cat != "Todas":
        filtered = filtered[filtered["Categoria"] == filter_cat]
    if filter_search.strip():
        q = filter_search.strip().lower()
        filtered = filtered[filtered["Descripcion"].str.lower().str.contains(q, na=False)]
    try:
        filtered["_fecha_dt"] = pd.to_datetime(filtered["Fecha"], errors="coerce")
        filtered = filtered[
            (filtered["_fecha_dt"].dt.date >= filter_from) &
            (filtered["_fecha_dt"].dt.date <= filter_to)
        ]
        filtered = filtered.drop(columns=["_fecha_dt"])
    except Exception:
        pass

    # ── Summary ───────────────────────────────────────────────────────────────────
    total_gastos = filtered[filtered["Tipo"] == "Gasto"]["Monto"].sum() if not filtered.empty else 0.0
    total_ingresos = filtered[filtered["Tipo"] == "Ingreso"]["Monto"].sum() if not filtered.empty else 0.0
    sm1, sm2, sm3 = st.columns(3)
    sm1.metric("💸 Total gastos", _mp_currency(total_gastos))
    sm2.metric("💰 Total ingresos", _mp_currency(total_ingresos))
    sm3.metric("⚖️ Balance", _mp_currency(total_ingresos - total_gastos))

    # ── Table ─────────────────────────────────────────────────────────────────────
    st.divider()
    if filtered.empty:
        st.info("No hay transacciones con los filtros aplicados.")
        return

    display_df = filtered.copy().sort_values("Fecha", ascending=False).reset_index(drop=True)
    display_df["Monto (fmt)"] = display_df["Monto"].apply(_mp_currency)
    st.dataframe(
        display_df[["Fecha", "Tipo", "Categoria", "Descripcion", "Monto (fmt)"]],
        use_container_width=True,
        hide_index=True,
    )

    # ── Download ──────────────────────────────────────────────────────────────────
    csv_data = filtered.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Descargar CSV", data=csv_data, file_name="transacciones.csv", mime="text/csv")

    # ── Delete ────────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🗑️ Eliminar transacciones")
    st.caption("Selecciona índices de la tabla anterior (0, 1, 2…) separados por coma para eliminar.")
    del_idx_input = st.text_input("Índices a eliminar", key="tx_del_idx", placeholder="Ej: 0,3")
    if st.button("Eliminar seleccionados", key="tx_del_btn"):
        try:
            idx_list = [int(x.strip()) for x in del_idx_input.split(",") if x.strip()]
            if idx_list:
                ids_to_remove = display_df.iloc[idx_list]["id"].tolist()
                all_df = get_user_transactions(username)
                all_df = all_df[~all_df["id"].isin(ids_to_remove)].reset_index(drop=True)
                save_user_transactions(username, all_df)
                st.success(f"Eliminadas {len(ids_to_remove)} transacciones.")
                st.rerun()
        except (ValueError, IndexError):
            st.error("Formato inválido. Usa números separados por coma.")
