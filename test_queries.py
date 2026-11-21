"""Verification script: ensures all 6 tables and all 20 queries return data."""
import sys

import database
import queries as qmod

REQUIRED_TABLES = ["Categories", "Competitions", "Complexes", "Venues",
                   "Competitors", "Competitor_Rankings"]

DEFAULT_PARAMS = {
    4: {"category_name": "ITF Men"},
    10: {"country_name": "Chile"},
    14: {"complex_name": "Nacional"},
    18: {"country_name": "Croatia"},
    20: {"top_n": 10},
}


def main() -> int:
    engine = database.get_engine()
    database.ensure_database(engine)

    counts = database.table_counts(engine)
    print("Table counts:", counts)
    missing = [t for t in REQUIRED_TABLES if counts.get(t, 0) == 0]
    assert not missing, f"Empty tables: {missing}"

    all_q = qmod.load_queries()
    assert len(all_q) == 20, f"Expected 20 queries, found {len(all_q)}"

    failures = []
    for q in all_q:
        try:
            df = qmod.run_query(engine, q["num"], DEFAULT_PARAMS.get(q["num"], {}))
            status = f"{len(df)} rows"
            if df.empty:
                failures.append(q["num"])
            print(f"Q{q['num']:>2}  {q['label'][:60]:<62} -> {status}")
        except Exception as e:
            failures.append(q["num"])
            print(f"Q{q['num']:>2}  {q['label'][:60]:<62} -> ERROR: {e}")

    if failures:
        print("FAILED queries:", failures)
        return 1
    print("All 20 queries returned non-empty results.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
