import logging
import os

import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "wildfire.db")
US_BOUNDS = {
    "min_lat": 24.0,
    "max_lat": 49.5,
    "min_lon": -125.0,
    "max_lon": -66.5,
}

logger = logging.getLogger(__name__)


def ensure_fires_table(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS fires (
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


def ingest_firms() -> None:
    api_key = os.getenv("FIRMS_API_KEY")
    if not api_key:
        raise RuntimeError("Missing FIRMS_API_KEY in .env")

    firms_url = (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{api_key}/VIIRS_SNPP_NRT/world/1"
    )

    logger.info("Fetching NASA FIRMS data...")
    df = pd.read_csv(firms_url)

    df = df[
        [
            "latitude",
            "longitude",
            "bright_ti4",
            "bright_ti5",
            "frp",
            "acq_date",
            "acq_time",
            "confidence",
        ]
    ]
    df = df[
        (df["latitude"].between(US_BOUNDS["min_lat"], US_BOUNDS["max_lat"]))
        & (df["longitude"].between(US_BOUNDS["min_lon"], US_BOUNDS["max_lon"]))
    ]

    con = duckdb.connect(DB_PATH)

    try:
        ensure_fires_table(con)
        row = con.execute("SELECT COUNT(*) FROM fires").fetchone()
        count_before = row[0] if row is not None else 0
        con.execute(
            """
            INSERT INTO fires
            SELECT d.* FROM df d
            WHERE NOT EXISTS (
                SELECT 1 FROM fires f
                WHERE f.latitude = d.latitude
                  AND f.longitude = d.longitude
                  AND f.acq_date = d.acq_date
                  AND f.acq_time = d.acq_time
            )
            """
        )
        row = con.execute("SELECT COUNT(*) FROM fires").fetchone()
        inserted = (row[0] if row is not None else 0) - count_before
        logger.info(
            "Inserted %d new fire records (skipped %d duplicates) into %s",
            inserted,
            len(df) - inserted,
            DB_PATH,
        )
        logger.info("Inserted %d fire records into %s", len(df), DB_PATH)
    finally:
        con.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    ingest_firms()
