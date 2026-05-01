from __future__ import annotations

import io
import os
import zipfile

import streamlit as st

from ..business import (
    SESSION_TIMEOUT_OPTIONS,
    SUPPORTED_CURRENCIES,
    change_user_password,
    delete_current_user_data,
    get_all_expense_categories,
    get_all_income_categories,
    get_all_savings_categories,
    get_user_custom_categories,
    get_user_profile,
    get_users_normalized,
    hash_password,
    save_user_custom_categories,
    save_user_profile,
)
from ..data_access import (
    DATA_FILE,
    SETTINGS_FILE,
    get_user_data_files,
    load_user_avatar,
    save_user_avatar,
)


def _build_export_zip(username: str) -> bytes:
    import pandas as pd
    from ..business import (
        get_monthly_rows,
        get_user_goals,
        get_user_rows,
        get_user_transactions,
        normalize_expense_rows,
        normalize_income_rows,
        normalize_savings_rows,
        MP_DEFAULT_FIXED_ROWS,
        MP_DEFAULT_INCOME_ROWS,
        MP_DEFAULT_SAVINGS_ROWS,
        MP_DEFAULT_TRANSACTION_ROWS,
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        fixed_df = get_user_rows(username, "fixed", MP_DEFAULT_FIXED_ROWS, normalize_expense_rows)
        variable_df = get_user_rows(username, "variable", [], normalize_expense_rows)
        income_df = get_user_rows(username, "income", MP_DEFAULT_INCOME_ROWS, normalize_income_rows)
        savings_df = get_user_rows(username, "savings", MP_DEFAULT_SAVINGS_ROWS, normalize_savings_rows)
        monthly_df = get_monthly_rows(username)
        transactions_df = get_user_transactions(username)
        goals_df = get_user_goals(username)

        datasets = [
            ("gastos_fijos.csv", fixed_df.drop(columns=["row_id"], errors="ignore")),
            ("gastos_variables.csv", variable_df.drop(columns=["row_id"], errors="ignore")),
            ("ingresos.csv", income_df.drop(columns=["row_id"], errors="ignore")),
            ("ahorros.csv", savings_df.drop(columns=["row_id"], errors="ignore")),
            ("resumen_mensual.csv", monthly_df),
            ("transacciones.csv", transactions_df.drop(columns=["id"], errors="ignore")),
            ("metas.csv", goals_df.drop(columns=["id"], errors="ignore")),
        ]
        for filename, df in datasets:
            zf.writestr(filename, df.to_csv(index=False))
    return buf.getvalue()


def render_profile_panel():
    st.header("Perfil")

    current_user = st.session_state.get("current_user")
    st.info(f"Sesión iniciada como: **{current_user}**")

    logout_col = st.columns([0.5, 5])[0]
    if logout_col.button("Cerrar sesión", type="secondary"):
        st.session_state.current_user = None
        st.success("Sesión cerrada.")
        st.rerun()

    # ── Avatar ────────────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📸 Foto de perfil")
    avatar_bytes = load_user_avatar(current_user)
    av_col1, av_col2 = st.columns([1, 3])
    with av_col1:
        if avatar_bytes:
            st.image(avatar_bytes, width=100)
        else:
            st.markdown("👤")
    with av_col2:
        uploaded_avatar = st.file_uploader("Subir imagen (PNG/JPG)", type=["png", "jpg", "jpeg"], key="avatar_uploader")
        if uploaded_avatar is not None:
            if st.button("Guardar foto", key="save_avatar"):
                save_user_avatar(current_user, uploaded_avatar.read())
                st.success("Foto de perfil actualizada.")
                st.rerun()

    # ── General settings ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("⚙️ Preferencias")
    profile = get_user_profile(current_user)
    name = st.text_input("Nombre de usuario", value=profile.get("name", ""))
    currency_options = SUPPORTED_CURRENCIES
    current_currency = profile.get("currency", "DOP")
    currency_idx = currency_options.index(current_currency) if current_currency in currency_options else 0
    currency = st.selectbox("Moneda", options=currency_options, index=currency_idx)

    timeout_label = profile.get("session_timeout_label", "Nunca")
    timeout_options = list(SESSION_TIMEOUT_OPTIONS.keys())
    timeout_idx = timeout_options.index(timeout_label) if timeout_label in timeout_options else timeout_options.index("Nunca")
    selected_timeout = st.selectbox(
        "Tiempo de sesión inactiva",
        options=timeout_options,
        index=timeout_idx,
        help="La sesión se cerrará automáticamente si no hay actividad en este tiempo.",
    )

    cols = st.columns([1, 1])
    if cols[0].button("Guardar preferencias"):
        profile["name"] = name
        profile["currency"] = currency
        profile["session_timeout_label"] = selected_timeout
        profile["session_timeout_minutes"] = SESSION_TIMEOUT_OPTIONS[selected_timeout]
        save_user_profile(current_user, profile)
        st.session_state.profile = profile
        st.success("Preferencias guardadas.")
        st.rerun()

    # ── Change password ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🔑 Cambiar contraseña")
    with st.form("change_password_form"):
        current_pw = st.text_input("Contraseña actual", type="password", key="cp_current")
        new_pw = st.text_input("Nueva contraseña", type="password", key="cp_new")
        confirm_pw = st.text_input("Confirmar nueva contraseña", type="password", key="cp_confirm")
        submit_pw = st.form_submit_button("Actualizar contraseña")
    if submit_pw:
        users = get_users_normalized()
        stored_hash = users.get(current_user, {}).get("password_hash", "")
        if stored_hash != hash_password(current_pw):
            st.error("La contraseña actual es incorrecta.")
        elif len(new_pw) < 4:
            st.error("La nueva contraseña debe tener al menos 4 caracteres.")
        elif new_pw != confirm_pw:
            st.error("Las contraseñas nuevas no coinciden.")
        else:
            change_user_password(users, current_user, new_pw)
            st.success("Contraseña actualizada exitosamente.")

    # ── Custom categories ─────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🏷️ Categorías personalizadas")
    st.caption("Agrega categorías propias que aparecerán junto a las predefinidas en cada sección.")
    custom_cats = get_user_custom_categories(current_user)

    for cat_type, label in [("expense", "Gastos"), ("income", "Ingresos"), ("savings", "Ahorros")]:
        with st.expander(f"Categorías de {label}"):
            existing = custom_cats.get(cat_type, [])
            if existing:
                st.write("Actuales: " + ", ".join(existing))
            new_cat = st.text_input(f"Nueva categoría de {label.lower()}", key=f"new_cat_{cat_type}")
            add_col, del_col = st.columns(2)
            if add_col.button(f"Agregar a {label}", key=f"add_cat_{cat_type}"):
                new_cat_clean = new_cat.strip()
                if new_cat_clean and new_cat_clean not in existing:
                    existing.append(new_cat_clean)
                    custom_cats[cat_type] = existing
                    save_user_custom_categories(current_user, custom_cats)
                    st.success(f"Categoría '{new_cat_clean}' agregada.")
                    st.rerun()
                elif not new_cat_clean:
                    st.warning("El nombre no puede estar vacío.")
                else:
                    st.warning("Esa categoría ya existe.")
            if existing:
                to_remove = st.selectbox(f"Eliminar de {label}", [""] + existing, key=f"remove_cat_{cat_type}")
                if del_col.button(f"Eliminar", key=f"del_cat_{cat_type}"):
                    if to_remove:
                        existing.remove(to_remove)
                        custom_cats[cat_type] = existing
                        save_user_custom_categories(current_user, custom_cats)
                        st.success(f"Categoría '{to_remove}' eliminada.")
                        st.rerun()

    # ── Export all data ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("📦 Exportar todos mis datos")
    st.caption("Descarga un archivo ZIP con todos tus registros en formato CSV.")
    if st.button("Preparar ZIP", key="export_zip_btn"):
        with st.spinner("Generando archivo…"):
            zip_bytes = _build_export_zip(current_user)
        st.download_button(
            label="⬇️ Descargar ZIP",
            data=zip_bytes,
            file_name=f"cashpilot_{current_user}.zip",
            mime="application/zip",
            key="download_zip_btn",
        )

    # ── Delete data ───────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("🗑️ Eliminar datos")
    st.warning("Esta acción borra los datos guardados del dashboard y no se puede deshacer.")
    confirmation = st.text_input("Escribe borrar para confirmar", key="delete_data_confirmation")
    delete_button = st.button("Eliminar datos", type="primary", disabled=confirmation.strip().lower() != "borrar")
    if delete_button:
        delete_current_user_data(current_user)
        for file_path in [DATA_FILE, SETTINGS_FILE]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
        st.success("Datos eliminados.")
        st.rerun()

