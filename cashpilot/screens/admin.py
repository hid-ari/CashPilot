from __future__ import annotations

import pandas as pd
import streamlit as st

from ..business import (
    ADMIN_ROLE,
    USER_ROLE,
    change_user_password,
    change_user_role,
    delete_user_account,
    get_all_users_documents_status,
    get_users_normalized,
)
from ..data_access import PROJECT_ROOT


def render_admin_panel():
    st.title("Panel Admin")
    st.caption("Gestión de usuarios y permisos")

    users = get_users_normalized()
    total_users = len(users)
    total_admins = sum(1 for data in users.values() if data.get("role") == ADMIN_ROLE)
    data_dirs = [d for d in PROJECT_ROOT.iterdir() if d.is_dir() and d.name.startswith("data_")]

    metric_cols = st.columns(3)
    metric_cols[0].metric("Usuarios", total_users)
    metric_cols[1].metric("Admins", total_admins)
    metric_cols[2].metric("Carpetas de datos", len(data_dirs))

    st.divider()
    st.subheader("Usuarios registrados")

    user_rows = []
    for username, info in sorted(users.items()):
        user_rows.append(
            {
                "Usuario": username,
                "Rol": info.get("role", USER_ROLE),
                "Creado": info.get("created_at", ""),
            }
        )

    st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Estado de documentos de datos")
    st.caption("Muestra el estado de los archivos por usuario.")

    document_rows = get_all_users_documents_status(users)
    user_filter_options = ["Todos"] + sorted(users.keys())
    selected_user_filter = st.selectbox("Filtrar por usuario", options=user_filter_options, key="admin_docs_filter")

    document_df = pd.DataFrame(document_rows)
    if selected_user_filter != "Todos":
        document_df = document_df[document_df["Usuario"] == selected_user_filter]

    st.dataframe(document_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Acciones")

    if not users:
        st.info("No hay usuarios para administrar.")
        return

    selected_user = st.selectbox("Selecciona un usuario", options=sorted(users.keys()))
    selected_role = users[selected_user].get("role", USER_ROLE)
    current_user = st.session_state.get("current_user")
    is_current_user_selected = selected_user == current_user

    st.write(f"Rol actual: **{selected_role}**")

    st.markdown("**Cambiar contraseña**")
    new_password_key = f"admin_new_password_{selected_user}"
    confirm_password_key = f"admin_confirm_password_{selected_user}"
    password_cols = st.columns([1.2, 1.2, 1.0])
    new_password = password_cols[0].text_input("Nueva contraseña", type="password", key=new_password_key)
    confirm_password = password_cols[1].text_input("Confirmar contraseña", type="password", key=confirm_password_key)

    if password_cols[2].button("Actualizar contraseña", key=f"admin_update_password_{selected_user}"):
        if not new_password.strip():
            st.error("La contraseña no puede estar vacía.")
        elif len(new_password) < 4:
            st.error("La contraseña debe tener al menos 4 caracteres.")
        elif new_password != confirm_password:
            st.error("Las contraseñas no coinciden.")
        else:
            change_user_password(users, selected_user, new_password)
            st.session_state[new_password_key] = ""
            st.session_state[confirm_password_key] = ""
            st.success(f"Contraseña actualizada para {selected_user}.")
            st.rerun()

    st.divider()
    st.markdown("**Permisos y cuenta**")

    action_cols = st.columns(3)

    if is_current_user_selected:
        st.info("Puedes cambiar tu contraseña, pero no tus propios permisos ni eliminar tu cuenta desde el panel admin.")

    if selected_role == USER_ROLE:
        if action_cols[0].button("Promover a admin", type="primary", disabled=is_current_user_selected):
            change_user_role(users, selected_user, ADMIN_ROLE)
            st.success(f"{selected_user} ahora es admin.")
            st.rerun()
    else:
        disable_demote = total_admins <= 1
        if action_cols[1].button("Quitar admin", disabled=disable_demote or is_current_user_selected):
            change_user_role(users, selected_user, USER_ROLE)
            st.success(f"{selected_user} ahora es usuario.")
            st.rerun()
        if disable_demote:
            st.warning("Debe existir al menos un admin en el sistema.")

    is_last_admin = selected_role == ADMIN_ROLE and total_admins <= 1
    if action_cols[2].button("Eliminar usuario", type="secondary", disabled=is_last_admin or is_current_user_selected):
        delete_user_account(selected_user, users)
        st.success(f"Usuario {selected_user} eliminado.")
        st.rerun()
    if is_last_admin:
        st.warning("No puedes eliminar el último administrador.")
