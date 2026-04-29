from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
USERS_FILE = PROJECT_ROOT / "users.json"
SETTINGS_FILE = PROJECT_ROOT / "settings.json"
DATA_FILE = PROJECT_ROOT / "gastos.json"


def read_json(path: Path, default: Any):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return default


def write_json(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def get_user_data_dir(username: str) -> Path:
    user_dir = PROJECT_ROOT / f"data_{username}"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_settings_file(username: str) -> Path:
    return get_user_data_dir(username) / "settings.json"


def get_user_data_file(username: str, file_key: str) -> Path:
    file_mapping = {
        "fixed": "gastos_fijos.json",
        "variable": "gastos_variables.json",
        "income": "ingresos.json",
        "savings": "ahorros.json",
        "monthly": "resumen_mensual.json",
    }
    return get_user_data_dir(username) / file_mapping.get(file_key, f"{file_key}.json")


def load_users_raw():
    return read_json(USERS_FILE, {})


def save_users_raw(users):
    write_json(USERS_FILE, users)


def load_user_settings(username: str):
    return read_json(get_user_settings_file(username), {"name": username, "currency": "DOP"})


def save_user_settings(username: str, settings: dict):
    write_json(get_user_settings_file(username), settings)


def get_user_data_files(username: str):
    return {
        "fixed": get_user_data_file(username, "fixed"),
        "variable": get_user_data_file(username, "variable"),
        "income": get_user_data_file(username, "income"),
        "savings": get_user_data_file(username, "savings"),
        "monthly": get_user_data_file(username, "monthly"),
    }


def load_rows(file_path: Path, normalizer: Callable, default_rows):
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                return normalizer(json.load(fh))
        except Exception:
            pass
    return normalizer(default_rows)


def save_rows(file_path: Path, df: pd.DataFrame, drop_cols=None):
    payload = df.drop(columns=drop_cols or [], errors="ignore").to_dict(orient="records")
    write_json(file_path, payload)


def load_monthly_rows(file_path: Path, monthly_columns: list[str]):
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            df = pd.DataFrame(data)
            if df.empty:
                return pd.DataFrame(columns=monthly_columns)
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=monthly_columns)


def save_monthly_rows(file_path: Path, df: pd.DataFrame, monthly_columns: list[str]):
    ordered_df = df.copy()
    for col in monthly_columns:
        if col not in ordered_df.columns:
            ordered_df[col] = ""
    write_json(file_path, ordered_df[monthly_columns].to_dict(orient="records"))


def delete_user_data(username: str):
    user_dir = get_user_data_dir(username)
    if user_dir.exists():
        try:
            shutil.rmtree(user_dir)
        except Exception:
            pass
