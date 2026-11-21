"""Database connection and schema management for the Tennis Analytics app.

Defaults to a zero-config SQLite database (tennis_analytics.db) so the app
runs instantly locally and on Streamlit Community Cloud. If MySQL
credentials are provided via .env / environment variables, a MySQL engine
is used instead.
"""
import os
from pathlib import Path

import sqlalchemy
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"
SQLITE_PATH = BASE_DIR / "tennis_analytics.db"

TABLES = ["Categories", "Competitions", "Complexes", "Venues", "Competitors", "Competitor_Rankings"]


def _mysql_url() -> str | None:
    host = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST")
    user = os.getenv("MYSQL_USER") or os.getenv("DB_USER")
    password = os.getenv("MYSQL_PASSWORD") or os.getenv("DB_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE") or os.getenv("DB_NAME")
    port = os.getenv("MYSQL_PORT", "3306")
    if host and user and database:
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    return None


def get_database_url() -> str:
    return _mysql_url() or f"sqlite:///{SQLITE_PATH}"


def get_engine():
    url = get_database_url()
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return sqlalchemy.create_engine(url, **kwargs)


def _schema_sql_for(dialect: str) -> str:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    if dialect == "mysql":
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "INTEGER AUTO_INCREMENT PRIMARY KEY")
    return sql


def apply_schema(engine) -> None:
    dialect = engine.dialect.name
    statements = [s.strip() for s in _schema_sql_for(dialect).split(";") if s.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
        conn.execute(text("PRAGMA foreign_keys=ON") if dialect == "sqlite" else text("SET FOREIGN_KEY_CHECKS=1"))


def table_counts(engine) -> dict:
    counts = {}
    with engine.connect() as conn:
        for table in TABLES:
            counts[table] = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
    return counts


def is_seeded(engine) -> bool:
    counts = table_counts(engine)
    return all(counts[t] > 0 for t in TABLES)


def run_etl(engine) -> dict:
    """Drop & recreate all tables, then load the raw SportRadar snapshots."""
    import etl_pipeline

    with engine.begin() as conn:
        for table in TABLES:
            conn.execute(text(f"DELETE FROM {table}"))
    apply_schema(engine)
    stats = etl_pipeline.load_snapshots(engine)
    return stats


def ensure_database(engine) -> bool:
    """Create schema and seed data if empty. Returns True if seeded."""
    apply_schema(engine)
    if is_seeded(engine):
        return False
    run_etl(engine)
    return True
