from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import Text, create_engine, text
from sqlalchemy.engine import URL


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_CANDIDATES = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT.parent / ".env",
]
DATA_DIRECTORY = PROJECT_ROOT / "data"
TARGET_DATABASE = "stroopwafelshop_db"
RAW_SCHEMA = "raw"

FILE_TABLE_MAPPING = {
    "Employees.csv": "employees",
    "Products.csv": "products",
    "Promotions.csv": "promotions",
    "Sales.csv": "sales",
    "Sales_lines.csv": "sales_lines",
    "Shifts.csv": "shifts",
}


def load_environment() -> None:
    for env_path in ENV_CANDIDATES:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break


def require_environment(name: str) -> str:
    import os

    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"La variable d'environnement {name} est requise.")
    return value.strip()


def make_connection_url(database: str) -> URL:
    return URL.create(
        "postgresql+psycopg2",
        username=require_environment("DB_USER"),
        password=require_environment("DB_PASSWORD"),
        host=require_environment("DB_HOST"),
        port=int(require_environment("DB_PORT")),
        database=database,
    )


def normalize_identifier(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower())
    return cleaned.strip("_")


def discover_csv_files() -> Iterable[Path]:
    return sorted(DATA_DIRECTORY.glob("*.csv"))


def create_database_if_needed() -> None:
    admin_connection = psycopg2.connect(
        host=require_environment("DB_HOST"),
        port=require_environment("DB_PORT"),
        user=require_environment("DB_USER"),
        password=require_environment("DB_PASSWORD"),
        dbname="postgres",
    )
    admin_connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    with admin_connection.cursor() as cursor:
        cursor.execute(
            "select 1 from pg_database where datname = %s",
            (TARGET_DATABASE,),
        )
        database_exists = cursor.fetchone() is not None
        if not database_exists:
            cursor.execute(f'create database "{TARGET_DATABASE}"')
            print(f"Base créée: {TARGET_DATABASE}")
        else:
            print(f"Base déjà présente: {TARGET_DATABASE}")

    admin_connection.close()


def prepare_schema(engine) -> None:
    with engine.begin() as connection:
        connection.execute(text(f"create schema if not exists {RAW_SCHEMA}"))


def load_csv_to_raw(engine, csv_path: Path, table_name: str) -> None:
    dataframe = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    dataframe.columns = [normalize_identifier(column) for column in dataframe.columns]
    dataframe = dataframe.replace({"": None})

    dtype_mapping = {column: Text() for column in dataframe.columns}
    dataframe.head(0).to_sql(
        name=table_name,
        con=engine,
        schema=RAW_SCHEMA,
        if_exists="replace",
        index=False,
        dtype=dtype_mapping,
    )
    dataframe.to_sql(
        name=table_name,
        con=engine,
        schema=RAW_SCHEMA,
        if_exists="append",
        index=False,
        dtype=dtype_mapping,
        chunksize=1_000,
        method="multi",
    )

    print(f"Table raw.{table_name} chargée avec {len(dataframe):,} lignes")


def main() -> None:
    load_environment()
    create_database_if_needed()

    engine = create_engine(make_connection_url(TARGET_DATABASE))
    prepare_schema(engine)

    for csv_path in discover_csv_files():
        table_name = FILE_TABLE_MAPPING[csv_path.name]
        load_csv_to_raw(engine, csv_path, table_name)

    print("Chargement terminé.")
    print(f"Base cible: {TARGET_DATABASE}")
    print(f"Schéma prêt: {RAW_SCHEMA}")


if __name__ == "__main__":
    main()
