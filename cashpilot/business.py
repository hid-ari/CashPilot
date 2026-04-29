from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

from .data_access import (
    PROJECT_ROOT,
    delete_user_data,
    get_user_data_file,
    get_user_data_files,
    get_user_settings_file,
    load_monthly_rows,
    load_rows,
    load_user_settings,
    load_users_raw,
    save_monthly_rows,
    save_rows,
    save_user_settings,
    save_users_raw,
)

ADMIN_ROLE = "admin"
USER_ROLE = "user"

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
MP_MONTHLY_COLUMNS = ["Mes", "Día", "Ingresos", "Gastos fijos", "Gastos variables", "Ahorros", "Presupuesto", "Balance", "Guardado"]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def normalize_user_record(username: str, record):
    default_role = ADMIN_ROLE if username.lower() == "admin" else USER_ROLE
    if isinstance(record, str):
        return {"password_hash": record, "role": default_role, "created_at": ""}
    if isinstance(record, dict):
        return {
            "password_hash": record.get("password_hash", ""),
            "role": record.get("role", default_role),
            "created_at": record.get("created_at", ""),
        }
    return {"password_hash": "", "role": default_role, "created_at": ""}


def get_users_normalized():
    raw_users = load_users_raw()
    normalized = {}
    changed = False
    for username, record in raw_users.items():
        normalized_record = normalize_user_record(username, record)
        normalized[username] = normalized_record
        if record != normalized_record:
            changed = True
    if changed:
        save_users_raw(normalized)
    return normalized


def is_admin_user(username: str | None) -> bool:
    if not username:
        return False
    return get_users_normalized().get(username, {}).get("role") == ADMIN_ROLE


def register_user(username: str, password: str):
    if not username or not password:
        return False, "Usuario y contraseña no pueden estar vacíos."
    users = get_users_normalized()
    if username in users:
        return False, "El usuario ya existe."
    role = ADMIN_ROLE if not users or username.lower() == "admin" else USER_ROLE
    users[username] = {"password_hash": hash_password(password), "role": role, "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")}
    save_users_raw(users)
    return True, "Usuario registrado exitosamente."


def login_user(username: str, password: str):
    users = get_users_normalized()
    if username not in users:
        return False, "Usuario no encontrado."
    if users[username].get("password_hash") != hash_password(password):
        return False, "Contraseña incorrecta."
    return True, "Bienvenido"


def change_user_password(users: dict, username: str, new_password: str):
    users[username]["password_hash"] = hash_password(new_password)
    save_users_raw(users)


def change_user_role(users: dict, username: str, role: str):
    users[username]["role"] = role
    save_users_raw(users)


def delete_user_account(username: str, users: dict):
    users.pop(username, None)
    save_users_raw(users)
    delete_user_data(username)


def get_user_profile(username: str):
    return load_user_settings(username)


def save_user_profile(username: str, settings: dict):
    save_user_settings(username, settings)


def delete_current_user_data(username: str):
    delete_user_data(username)


def new_id():
    return uuid.uuid4().hex


def normalize_expense_rows(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["row_id", "Categoria", "Descripcion", "Presupuesto", "Actual"])
    if "row_id" not in df.columns:
        df.insert(0, "row_id", [new_id() for _ in range(len(df))])
    df["Categoria"] = df.get("Categoria", pd.Series(dtype=str)).fillna("").astype(str)
    df["Descripcion"] = df.get("Descripcion", pd.Series(dtype=str)).fillna("").astype(str)
    df["Presupuesto"] = pd.to_numeric(df.get("Presupuesto", 0), errors="coerce").fillna(0.0)
    df["Actual"] = pd.to_numeric(df.get("Actual", 0), errors="coerce").fillna(0.0)
    return df[["row_id", "Categoria", "Descripcion", "Presupuesto", "Actual"]]


def normalize_income_rows(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["row_id", "Categoria", "Descripcion", "Ingreso"])
    if "row_id" not in df.columns:
        df.insert(0, "row_id", [new_id() for _ in range(len(df))])
    df["Categoria"] = df.get("Categoria", pd.Series(dtype=str)).fillna("").astype(str)
    df["Descripcion"] = df.get("Descripcion", pd.Series(dtype=str)).fillna("").astype(str)
    df["Ingreso"] = pd.to_numeric(df.get("Ingreso", 0), errors="coerce").fillna(0.0)
    return df[["row_id", "Categoria", "Descripcion", "Ingreso"]]


def normalize_savings_rows(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["row_id", "Categoria", "Descripcion", "Ahorro"])
    if "row_id" not in df.columns:
        df.insert(0, "row_id", [new_id() for _ in range(len(df))])
    df["Categoria"] = df.get("Categoria", pd.Series(dtype=str)).fillna("").astype(str)
    df["Descripcion"] = df.get("Descripcion", pd.Series(dtype=str)).fillna("").astype(str)
    df["Ahorro"] = pd.to_numeric(df.get("Ahorro", 0), errors="coerce").fillna(0.0)
    return df[["row_id", "Categoria", "Descripcion", "Ahorro"]]


def get_user_rows(username: str, file_key: str, default_rows, normalizer):
    return load_rows(get_user_data_file(username, file_key), normalizer, default_rows)


def save_user_rows(username: str, file_key: str, df: pd.DataFrame, drop_cols=None):
    save_rows(get_user_data_file(username, file_key), df, drop_cols)


def get_monthly_rows(username: str):
    df = load_monthly_rows(get_user_data_file(username, "monthly"), MP_MONTHLY_COLUMNS)
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


def save_monthly_rows_for_user(username: str, df: pd.DataFrame):
    save_monthly_rows(get_user_data_file(username, "monthly"), df, MP_MONTHLY_COLUMNS)


def format_currency(amount: float, currency: str = "DOP") -> str:
    return f"{currency} {amount:,.2f}"


def get_all_users_documents_status(users):
    rows = []
    for username in sorted(users.keys()):
        for doc_key, doc_label in [("settings", "Perfil"), ("fixed", "Gastos fijos"), ("variable", "Gastos variables"), ("income", "Ingresos"), ("savings", "Ahorros"), ("monthly", "Resumen mensual")]:
            file_path = get_user_settings_file(username) if doc_key == "settings" else get_user_data_file(username, doc_key)
            exists = file_path.exists()
            if exists:
                size_bytes = file_path.stat().st_size
                modified = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                try:
                    with open(file_path, "r", encoding="utf-8") as fh:
                        data = __import__("json").load(fh)
                    if isinstance(data, list):
                        records = len(data)
                    elif isinstance(data, dict):
                        records = len(data.keys())
                    else:
                        records = 1
                    status = "OK"
                except Exception:
                    records = 0
                    status = "Inválido"
            else:
                size_bytes = 0
                modified = "-"
                records = 0
                status = "Falta"
            rows.append({
                "Usuario": username,
                "Documento": doc_label,
                "Estado": status,
                "Registros": records,
                "Tamaño": format_file_size(size_bytes),
                "Actualizado": modified,
            })
    return rows


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def build_monthly_record(month_name: str, day_value: int, incomes: float, fixed_expenses: float, variable_expenses: float, savings: float, budget: float, balance: float, saved_at: str):
    return {
        "Mes": month_name,
        "Día": int(day_value),
        "Ingresos": incomes,
        "Gastos fijos": fixed_expenses,
        "Gastos variables": variable_expenses,
        "Ahorros": savings,
        "Presupuesto": budget,
        "Balance": balance,
        "Guardado": saved_at,
    }
