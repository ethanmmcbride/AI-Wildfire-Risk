import os

import duckdb
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "wildfire.db")


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
    print("Fetching NASA FIRMS data...")
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

    con = duckdb.connect(DB_PATH)

    ensure_fires_table(con)

    con.execute("INSERT INTO fires SELECT * FROM df")
    con.close()

    print(f"Inserted {len(df)} fire records into {DB_PATH}")


if __name__ == "__main__":
    ingest_firms()
