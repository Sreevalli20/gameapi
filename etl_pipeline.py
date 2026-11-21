"""ETL pipeline: parses SportRadar Tennis v3-style JSON snapshots from
data/raw_snapshots/ and loads them into the SQL database.

Usage:
    python etl_pipeline.py            # seeds the default database
    python etl_pipeline.py --reset    # wipes and re-seeds
"""
import argparse
import json
import sys
from pathlib import Path

import sqlalchemy
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent
SNAPSHOT_DIR = BASE_DIR / "data" / "raw_snapshots"


def _read_json(name: str):
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _insert(conn, dialect, table, columns, values_sql, params):
    """Dialect-aware INSERT ... IGNORE (SQLite) / INSERT IGNORE (MySQL)."""
    ignore = " OR IGNORE" if dialect == "sqlite" else " IGNORE"
    sql = f"INSERT{ignore} INTO {table} ({columns}) VALUES ({values_sql})"
    conn.execute(text(sql), params)


def load_snapshots(engine) -> dict:
    competitions_payload = _read_json("competitions.json")
    complexes_payload = _read_json("complexes.json")
    rankings_payload = _read_json("double_competitors_rankings.json")

    dialect = engine.dialect.name
    stats = {"categories": 0, "competitions": 0, "complexes": 0, "venues": 0,
             "competitors": 0, "rankings": 0}

    with engine.begin() as conn:
        for cat in competitions_payload.get("categories", []):
            _insert(conn, dialect, "Categories",
                    "category_id, category_name", ":id, :name",
                    {"id": cat["category_id"], "name": cat["category_name"]})
            stats["categories"] += 1

        # Parents before children so the self-referencing FK is satisfied.
        comps = competitions_payload.get("competitions", [])
        comps.sort(key=lambda c: 0 if c.get("parent_id") is None else 1)
        for comp in comps:
            _insert(conn, dialect, "Competitions",
                    "competition_id, competition_name, parent_id, type, gender, category_id",
                    ":id, :name, :parent, :type, :gender, :cat",
                    {"id": comp["competition_id"], "name": comp["competition_name"],
                     "parent": comp.get("parent_id"), "type": comp["type"],
                     "gender": comp["gender"], "cat": comp["category_id"]})
            stats["competitions"] += 1

        for complex_ in complexes_payload.get("complexes", []):
            _insert(conn, dialect, "Complexes", "complex_id, complex_name",
                    ":id, :name",
                    {"id": complex_["complex_id"], "name": complex_["complex_name"]})
            stats["complexes"] += 1
            for venue in complex_.get("venues", []):
                _insert(conn, dialect, "Venues",
                        "venue_id, venue_name, city_name, country_name, country_code, timezone, complex_id",
                        ":id, :name, :city, :country, :cc, :tz, :cx",
                        {"id": venue["venue_id"], "name": venue["venue_name"],
                         "city": venue["city_name"], "country": venue["country_name"],
                         "cc": venue["country_code"], "tz": venue["timezone"],
                         "cx": complex_["complex_id"]})
                stats["venues"] += 1

        for ranking in rankings_payload.get("rankings", []):
            _insert(conn, dialect, "Competitors",
                    "competitor_id, name, country, country_code, abbreviation",
                    ":id, :name, :country, :cc, :abbr",
                    {"id": ranking["competitor_id"], "name": ranking["name"],
                     "country": ranking["country"], "cc": ranking["country_code"],
                     "abbr": ranking["abbreviation"]})
            _insert(conn, dialect, "Competitor_Rankings",
                    "rank, movement, points, competitions_played, competitor_id",
                    ":rank, :movement, :points, :played, :cid",
                    {"rank": ranking["rank"], "movement": ranking["movement"],
                     "points": ranking["points"], "played": ranking["competitions_played"],
                     "cid": ranking["competitor_id"]})
            stats["competitors"] += 1
            stats["rankings"] += 1

    return stats


def main() -> int:
    import database

    parser = argparse.ArgumentParser(description="Seed the tennis analytics database.")
    parser.add_argument("--reset", action="store_true", help="wipe all tables before loading")
    args = parser.parse_args()

    engine = database.get_engine()
    database.apply_schema(engine)
    if args.reset or not database.is_seeded(engine):
        stats = database.run_etl(engine) if args.reset else load_snapshots(engine)
        print("ETL complete:", stats)
        print("Table counts:", database.table_counts(engine))
    else:
        print("Database already seeded:", database.table_counts(engine))
    return 0


if __name__ == "__main__":
    sys.exit(main())
