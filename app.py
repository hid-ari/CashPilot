import json
import os
import shutil
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px


DATA_FILE = "gastos.json"
SETTINGS_FILE = "settings.json"
USERS_FILE = "users.json"

import hashlib

ADMIN_ROLE = "admin"
USER_ROLE = "user"


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}


def normalize_user_record(username, record):
    default_role = ADMIN_ROLE if username.lower() == "admin" else USER_ROLE

    if isinstance(record, str):
        return {
            "password_hash": record,
            "role": default_role,
            "created_at": "",
        }

    if isinstance(record, dict):
        return {
            "password_hash": record.get("password_hash", ""),
            "role": record.get("role", default_role),
            "created_at": record.get("created_at", ""),
        }

    return {
        "password_hash": "",
        "role": default_role,
        "created_at": "",
    }


def get_users_normalized():
    raw_users = load_users()
    normalized = {}
    changed = False

    for username, record in raw_users.items():
        normalized_record = normalize_user_record(username, record)
        normalized[username] = normalized_record
        if record != normalized_record:
            changed = True

    if changed:
        save_users(normalized)

    return normalized


def is_admin_user(username):
    if not username:
        return False
    users = get_users_normalized()
    return users.get(username, {}).get("role") == ADMIN_ROLE


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as fh:
        json.dump(users, fh, ensure_ascii=False, indent=2)


def get_user_data_dir(username):
    user_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data_{username}")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def get_user_settings_file(username):
    return os.path.join(get_user_data_dir(username), "settings.json")


def get_user_data_file(username, file_key):
    user_dir = get_user_data_dir(username)
    file_mapping = {
        "fixed": "gastos_fijos.json",
        "variable": "gastos_variables.json",
        "income": "ingresos.json",
        "savings": "ahorros.json",
        "monthly": "resumen_mensual.json",
    }
    return os.path.join(user_dir, file_mapping.get(file_key, f"{file_key}.json"))


def register_user(username, password):
    if not username or not password:
        return False, "Usuario y contraseña no pueden estar vacíos."
    users = get_users_normalized()
    if username in users:
        return False, "El usuario ya existe."
    role = ADMIN_ROLE if not users or username.lower() == "admin" else USER_ROLE
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    save_users(users)
    return True, "Usuario registrado exitosamente."


def login_user(username, password):
    users = get_users_normalized()
    if username not in users:
        return False, "Usuario no encontrado."
    if users[username].get("password_hash") != hash_password(password):
        return False, "Contraseña incorrecta."
    return True, "Bienvenido"


def delete_user_account(username, users):
    users.pop(username, None)
    save_users(users)

    user_data_dir = get_user_data_dir(username)
    if os.path.exists(user_data_dir):
        try:
            shutil.rmtree(user_data_dir)
        except Exception:
            pass





def apply_space_mono_font():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');

        html, body, .stApp {
            font-family: 'Space Mono', monospace !important;
        }

        .stMarkdown p,
        .stMarkdown h1,
        .stMarkdown h2,
        .stMarkdown h3,
        .stMarkdown h4,
        .stMarkdown h5,
        .stMarkdown h6,
        .stMarkdown ul,
        .stMarkdown ol,
        .stMarkdown li,
        .stText,
        .stCaption,
        .stButton > button {
            font-family: 'Space Mono', monospace !important;
        }

        .stMarkdown ul,
        .stMarkdown ol {
            padding-left: 1.4rem;
        }

        .stMetricValue {
            font-size: 1.85rem;
            line-height: 1.1;
            font-family: 'Space Mono', monospace !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )





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

MONTH_NAME_OPTIONS = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

MP_DEFAULT_FIXED_ROWS = []

MP_DEFAULT_VARIABLE_ROWS = []

MP_DEFAULT_INCOME_ROWS = []

MP_DEFAULT_SAVINGS_ROWS = []

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ADMIN_DATA_DOCUMENTS = [
    ("settings", "Perfil"),
    ("fixed", "Gastos fijos"),
    ("variable", "Gastos variables"),
    ("income", "Ingresos"),
    ("savings", "Ahorros"),
    ("monthly", "Resumen mensual"),
]


def get_mp_data_files():
    username = st.session_state.get("current_user")
    if not username:
        return {}
    return {
        "fixed": get_user_data_file(username, "fixed"),
        "variable": get_user_data_file(username, "variable"),
        "income": get_user_data_file(username, "income"),
        "savings": get_user_data_file(username, "savings"),
        "monthly": get_user_data_file(username, "monthly"),
    }


def format_size_bytes(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_data_document_path(username, doc_key):
    if doc_key == "settings":
        return get_user_settings_file(username)
    return get_user_data_file(username, doc_key)


def get_document_record_count(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return len(data), "OK"
        if isinstance(data, dict):
            return len(data.keys()), "OK"
        return 1, "OK"
    except Exception:
        return 0, "Inválido"


def get_all_users_documents_status(users):
    rows = []
    for username in sorted(users.keys()):
        for doc_key, doc_label in ADMIN_DATA_DOCUMENTS:
            file_path = get_data_document_path(username, doc_key)
            exists = os.path.exists(file_path)

            if exists:
                size_text = format_size_bytes(os.path.getsize(file_path))
                modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                records, status = get_document_record_count(file_path)
            else:
                size_text = "0 B"
                modified = "-"
                records = 0
                status = "Falta"

            rows.append(
                {
                    "Usuario": username,
                    "Documento": doc_label,
                    "Estado": status,
                    "Registros": records,
                    "Tamaño": size_text,
                    "Actualizado": modified,
                }
            )

    return rows


MP_MONTHLY_COLUMNS = ["Mes", "Día", "Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Presupuesto", "Balance", "Guardado"]


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
    mp_data_files = get_mp_data_files()
    file_path = mp_data_files[file_key]
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                return normalizer(json.load(fh))
        except Exception:
            pass
    return normalizer(default_rows)


def mp_save_rows(file_key, df, drop_cols):
    mp_data_files = get_mp_data_files()
    file_path = mp_data_files[file_key]
    payload = df.drop(columns=drop_cols, errors="ignore").to_dict(orient="records")
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def mp_csv_download_button(df, file_name, label="Guardar CSV", drop_cols=None):
    export_df = df.drop(columns=drop_cols or [], errors="ignore").copy()
    csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label,
        data=csv_data,
        file_name=file_name,
        mime="text/csv",
    )


def mp_load_monthly_rows():
    mp_data_files = get_mp_data_files()
    file_path = mp_data_files["monthly"]
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            df = pd.DataFrame(data)
            if df.empty:
                return pd.DataFrame(columns=MP_MONTHLY_COLUMNS)
            if "Ahorros" not in df.columns:
                df["Ahorros"] = 0.0
            if "Día" not in df.columns:
                df["Día"] = 1
            for col in MP_MONTHLY_COLUMNS:
                if col not in df.columns:
                    if col in ["Mes", "Guardado"]:
                        df[col] = ""
                    elif col == "Día":
                        df[col] = 1
                    else:
                        df[col] = 0.0
            df["Día"] = pd.to_numeric(df["Día"], errors="coerce").fillna(1).astype(int).clip(1, 31)
            return df[MP_MONTHLY_COLUMNS]
        except Exception:
            pass
    return pd.DataFrame(columns=MP_MONTHLY_COLUMNS)


def mp_save_monthly_rows(df):
    mp_data_files = get_mp_data_files()
    file_path = mp_data_files["monthly"]
    ordered_df = df.copy()
    for col in MP_MONTHLY_COLUMNS:
        if col not in ordered_df.columns:
            if col in ["Mes", "Guardado"]:
                ordered_df[col] = ""
            elif col == "Día":
                ordered_df[col] = 1
            else:
                ordered_df[col] = 0.0
    ordered_df["Día"] = pd.to_numeric(ordered_df["Día"], errors="coerce").fillna(1).astype(int).clip(1, 31)
    ordered_df = ordered_df[MP_MONTHLY_COLUMNS]
    payload = ordered_df.to_dict(orient="records")
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def mp_currency(amount):
    currency = "DOP"
    try:
        currency = st.session_state.get("profile", {}).get("currency", "DOP")
    except Exception:
        currency = "DOP"
    return f"{currency} {amount:,.2f}"


def load_settings():
    username = st.session_state.get("current_user")
    if not username:
        return {"name": "Usuario", "currency": "DOP"}
    
    settings_file = get_user_settings_file(username)
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {"name": username, "currency": "DOP"}


def save_settings(settings):
    username = st.session_state.get("current_user")
    if not username:
        return
    
    settings_file = get_user_settings_file(username)
    with open(settings_file, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, ensure_ascii=False, indent=2)


def delete_app_data():
    mp_data_files = get_mp_data_files()
    data_files = list(mp_data_files.values()) + [DATA_FILE, SETTINGS_FILE]
    for file_path in data_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

    st.session_state.profile = load_settings()
    st.session_state.mp_fixed_rows_df = mp_load_rows("fixed", MP_DEFAULT_FIXED_ROWS, mp_normalize_expense_rows)
    st.session_state.mp_variable_rows_df = mp_load_rows("variable", MP_DEFAULT_VARIABLE_ROWS, mp_normalize_expense_rows)
    st.session_state.mp_income_rows_df = mp_load_rows("income", MP_DEFAULT_INCOME_ROWS, mp_normalize_income_rows)
    st.session_state.mp_savings_rows_df = mp_load_rows("savings", MP_DEFAULT_SAVINGS_ROWS, mp_normalize_savings_rows)
    st.session_state.mp_monthly_rows_df = mp_load_monthly_rows()


def init_profile_state():
    current_user = st.session_state.get("current_user")
    if st.session_state.get("profile_owner") != current_user:
        st.session_state.profile = load_settings()
        st.session_state.profile_owner = current_user
        return

    if "profile" not in st.session_state:
        st.session_state.profile = load_settings()
        st.session_state.profile_owner = current_user


def build_profile_panel():
    init_profile_state()
    st.header("Perfil")
    
    current_user = st.session_state.get("current_user")
    st.info(f"Sesión iniciada como: **{current_user}**")
    
    logout_col = st.columns([0.5, 5])[0]
    if logout_col.button("Cerrar sesión", type="secondary"):
        st.session_state.current_user = None
        st.success("Sesión cerrada.")
        st.rerun()
    
    st.divider()
    name = st.text_input("Nombre de usuario", value=st.session_state.profile.get("name", ""))
    currency = st.selectbox("Moneda", options=["DOP", "USD", "EUR", "ARS", "CLP"], index=["DOP", "USD", "EUR", "ARS", "CLP"].index(st.session_state.profile.get("currency", "DOP")))
    cols = st.columns([1, 1])
    if cols[0].button("Guardar perfil"):
        st.session_state.profile["name"] = name
        st.session_state.profile["currency"] = currency
        save_settings(st.session_state.profile)
        st.success("Perfil guardado.")
        st.experimental_rerun()

    st.divider()
    st.subheader("Eliminar datos")
    st.warning("Esta acción borra los datos guardados del dashboard y no se puede deshacer.")
    confirmation = st.text_input("Escribe borrar para confirmar", key="delete_data_confirmation")
    delete_button = st.button("Eliminar datos", type="primary", disabled=confirmation.strip().lower() != "borrar")
    if delete_button:
        delete_app_data()
        st.success("Datos eliminados.")
        st.rerun()


def mp_init_state():
    current_user = st.session_state.get("current_user")
    if st.session_state.get("mp_state_owner") != current_user:
        st.session_state.mp_fixed_rows_df = mp_load_rows("fixed", MP_DEFAULT_FIXED_ROWS, mp_normalize_expense_rows)
        st.session_state.mp_variable_rows_df = mp_load_rows("variable", MP_DEFAULT_VARIABLE_ROWS, mp_normalize_expense_rows)
        st.session_state.mp_income_rows_df = mp_load_rows("income", MP_DEFAULT_INCOME_ROWS, mp_normalize_income_rows)
        st.session_state.mp_savings_rows_df = mp_load_rows("savings", MP_DEFAULT_SAVINGS_ROWS, mp_normalize_savings_rows)
        st.session_state.mp_monthly_rows_df = mp_load_monthly_rows()
        st.session_state.mp_state_owner = current_user
        return

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
    st.session_state.mp_state_owner = current_user


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
            # ALWAYS load fresh from file to preserve all history
            mp_data_files = get_mp_data_files()
            file_path = mp_data_files["monthly"]
            existing_monthly = []
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as fh:
                        existing_monthly = json.load(fh)
                except Exception:
                    existing_monthly = []
            
            # Add new record
            new_record = {
                "Mes": current_month_name,
                "Día": int(current_day),
                "Ingresos": income_total,
                "Gastos fijos": fixed_actual,
                "Gastos variables": variable_actual,
                "Ahorros": savings_total,
                "Presupuesto": total_budget,
                "Balance": balance,
                "Guardado": current_saved_at,
            }
            existing_monthly.append(new_record)
            
            # Save everything to file
            with open(file_path, "w", encoding="utf-8") as fh:
                json.dump(existing_monthly, fh, ensure_ascii=False, indent=2)
            
            # Reload session state from file
            st.session_state.mp_monthly_rows_df = mp_load_monthly_rows()
            st.success("Mes guardado en el historial.")
            st.rerun()
    with info_col:
        st.info(f"Fecha utilizada: {current_day} de {current_month_name}")

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

    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    # Gastos pie (by actual)
    with row1_col1:
        st.markdown("**Gastos (Actual)**")
        if not expenses_by_cat.empty and expenses_by_cat["Valor"].sum() > 0:
            fig1 = px.pie(expenses_by_cat, names="Categoria", values="Valor", title="Gastos por categoría (Actual)")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No hay gastos registrados.")

    # Ingresos pie
    with row1_col2:
        st.markdown("**Ingresos**")
        if not income_by_cat.empty and income_by_cat["Ingreso"].sum() > 0:
            fig2 = px.pie(income_by_cat, names="Categoria", values="Ingreso", title="Ingresos por categoría")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay ingresos registrados.")

    # Presupuesto pie
    with row2_col1:
        st.markdown("**Presupuesto**")
        if not budget_by_cat.empty and budget_by_cat["Valor"].sum() > 0:
            fig3 = px.pie(budget_by_cat, names="Categoria", values="Valor", title="Presupuesto por categoría")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No hay presupuesto registrado.")

    # Ahorros pie
    with row2_col2:
        st.markdown("**Ahorros**")
        if not savings_by_cat.empty and savings_by_cat["Ahorro"].sum() > 0:
            fig4 = px.pie(savings_by_cat, names="Categoria", values="Ahorro", title="Ahorros por categoría")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No hay ahorros registrados.")

    st.divider()
    st.subheader("Resumen mensual guardado")
    # ALWAYS load fresh from file
    monthly_df = mp_load_monthly_rows()
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


def mp_sidebar_page():
    is_admin = is_admin_user(st.session_state.get("current_user"))
    options = ["Home", "Gastos fijos", "Gastos variables", "Ingresos", "Ahorros", "Perfil"]
    if is_admin:
        options.append("Admin")

    st.sidebar.title("Navegación")
    return st.sidebar.radio(
        "Ir a",
        options,
        index=0,
        label_visibility="collapsed",
    )


def build_admin_panel():
    st.title("Panel Admin")
    st.caption("Gestión de usuarios y permisos")

    users = get_users_normalized()
    total_users = len(users)
    total_admins = sum(1 for data in users.values() if data.get("role") == ADMIN_ROLE)
    data_dirs = [d for d in os.listdir(BASE_DIR) if d.startswith("data_") and os.path.isdir(os.path.join(BASE_DIR, d))]

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
            users[selected_user]["password_hash"] = hash_password(new_password)
            save_users(users)
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
            users[selected_user]["role"] = ADMIN_ROLE
            save_users(users)
            st.success(f"{selected_user} ahora es admin.")
            st.rerun()
    else:
        disable_demote = total_admins <= 1
        if action_cols[1].button("Quitar admin", disabled=disable_demote or is_current_user_selected):
            users[selected_user]["role"] = USER_ROLE
            save_users(users)
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


def login_register_page():
    st.title("CashPilot")
    st.caption("Dashboard financiero personal")
    
    tab1, tab2 = st.tabs(["Iniciar sesión", "Registrarse"])
    
    with tab1:
        st.subheader("Iniciar sesión")
        login_username = st.text_input("Usuario", key="login_username")
        login_password = st.text_input("Contraseña", type="password", key="login_password")
        
        if st.button("Entrar", key="login_button"):
            success, message = login_user(login_username, login_password)
            if success:
                st.session_state.current_user = login_username
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with tab2:
        st.subheader("Crear nueva cuenta")
        register_username = st.text_input("Usuario", key="register_username")
        register_password = st.text_input("Contraseña", type="password", key="register_password")
        register_password_confirm = st.text_input("Confirmar contraseña", type="password", key="register_password_confirm")
        
        if st.button("Registrarse", key="register_button"):
            if register_password != register_password_confirm:
                st.error("Las contraseñas no coinciden.")
            else:
                success, message = register_user(register_username, register_password)
                if success:
                    st.success(message)
                    st.info("Ahora puedes iniciar sesión con tu nueva cuenta.")
                else:
                    st.error(message)


def main():
    st.set_page_config(page_title="CashPilot", layout="wide")
    apply_space_mono_font()
    
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    
    if not st.session_state.current_user:
        login_register_page()
        return
    
    mp_init_state()
    init_profile_state()

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
    elif page == "Perfil":
        build_profile_panel()
    elif page == "Admin":
        if is_admin_user(st.session_state.get("current_user")):
            build_admin_panel()
        else:
            st.error("No tienes permisos para acceder a esta sección.")


if __name__ == "__main__":
    main()
