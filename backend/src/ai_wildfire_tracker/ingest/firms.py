import os
from dotenv import load_dotenv
import pandas as pd
import duckdb

load_dotenv()
API_KEY = os.getenv("FIRMS_API_KEY")
if not API_KEY:
    raise RuntimeError("Missing FIRMS_API_KEY in .env")

FIRMS_URL = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{API_KEY}/VIIRS_SNPP_NRT/world/1"
DB_PATH = "wildfire.db"

def ingest_firms():
    print("Fetching NASA FIRMS data...")
    df = pd.read_csv(FIRMS_URL)

    df = df[[
        "latitude",
        "longitude",
        "bright_ti4",
        "bright_ti5",
        "frp",
        "acq_date",
        "acq_time",
        "confidence"
    ]]

    con = duckdb.connect(DB_PATH)

    con.execute("""
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
    """)

    con.execute("INSERT INTO fires SELECT * FROM df")
    con.close()

    print(f"Inserrted {len(df)} fire records into {DB_PATH}")
    
if __name__ == "__main__":
    ingest_firms()