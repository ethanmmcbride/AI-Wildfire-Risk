#!/usr/bin/env python3
"""Create a deterministic DuckDB fixture for E2E tests."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import duckdb


SEED_INSERT_SQL = """
INSERT INTO fires VALUES
    (34.05, -118.25, 360.0, 300.0, 55.0, '2025-06-01', '1210', 'high'),
    (36.77, -119.41, 333.0, 295.0, 22.0, '2025-06-01', '1115', 'nominal'),
    (38.58, -121.49, 310.0, 280.0, 10.0, '2025-06-01', '1030', 'low'),
    (31.00, -100.00, 345.0, 302.0, 35.0, '2025-06-01', '0915', 'high'),
    (28.50, -82.40, 305.0, 270.0, 12.0, '2025-06-01', '0830', 'low'),
    (55.20, -120.50, 390.0, 320.0, 70.0, '2025-06-01', '1400', 'high')
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed DuckDB data for E2E tests")
    parser.add_argument(
        "--db-path",
        default="backend/tests/e2e/e2e_wildfire.db",
        help="Path to the DuckDB database file to create.",
    )
    return parser.parse_args()


def seed_database(db_path: str) -> None:
    target = Path(db_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists():
        target.unlink()

    con = duckdb.connect(str(target))
    try:
        con.execute(
            """
            CREATE TABLE fires (
                latitude DOUBLE,
                longitude DOUBLE,
                bright_ti4 DOUBLE,
                bright_ti5 DOUBLE,
                frp DOUBLE,
                acq_date VARCHAR,
                acq_time VARCHAR,
                confidence VARCHAR
            )
            """
        )
        con.execute(SEED_INSERT_SQL)
    finally:
        con.close()


def main() -> None:
    args = parse_args()
    seed_database(args.db_path)
    print(f"Seeded E2E DuckDB at {os.path.abspath(args.db_path)}")


if __name__ == "__main__":
    main()
