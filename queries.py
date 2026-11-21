"""Loads the 20 SQL queries from sql_queries.sql and provides execution helpers."""
import re
from pathlib import Path

import pandas as pd
from sqlalchemy import text

SQL_FILE = Path(__file__).resolve().parent / "sql_queries.sql"


def load_queries() -> list[dict]:
    """Split sql_queries.sql on '-- Q<n>:' comment markers."""
    raw = SQL_FILE.read_text(encoding="utf-8")
    # Split keeping the Qn markers.
    parts = re.split(r"(--\s*Q\d+:.*)", raw, flags=re.MULTILINE)
    queries = []
    for i in range(1, len(parts), 2):
        marker = parts[i].strip()
        body = parts[i + 1]
        # Strip trailing comment blocks belonging to the *next* query.
        body = re.split(r"\n\s*--\s*Q\d+:", body)[0]
        sql = body.strip().rstrip(";").strip()
        num = int(re.search(r"Q(\d+)", marker).group(1))
        label = marker.split(":", 1)[1].strip()
        queries.append({"num": num, "label": label, "sql": sql})
    queries.sort(key=lambda q: q["num"])
    return queries


def query_names() -> list[str]:
    return [f"Q{q['num']} — {q['label']}" for q in load_queries()]


def run_query(engine, query_num: int, params: dict | None = None) -> pd.DataFrame:
    queries = {q["num"]: q for q in load_queries()}
    q = queries[query_num]
    with engine.connect() as conn:
        return pd.read_sql(text(q["sql"]), conn, params=params or {})


def run_named(engine, name: str, params: dict | None = None) -> pd.DataFrame:
    for q in load_queries():
        if q["label"] == name or q["num"] == int(name.lstrip("Q").split(" ")[0].split("—")[0]):
            with engine.connect() as conn:
                return pd.read_sql(text(q["sql"]), conn, params=params or {})
    raise ValueError(f"Unknown query: {name}")
