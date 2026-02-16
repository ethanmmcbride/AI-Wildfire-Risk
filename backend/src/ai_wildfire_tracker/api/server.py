from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MODIFIED: Allow env var override for testing
DB_PATH = os.getenv("TEST_DB_PATH", "wildfire.db")

@app.get("/fires")
def get_fires():
    # Handling if DB doesn't exist yet
    if not os.path.exists(DB_PATH):
        return []

    con = duckdb.connect(DB_PATH)
    try:
        rows = con.execute("""
            SELECT latitude, longitude, bright_ti4, frp, confidence
            FROM fires
            ORDER BY acq_date DESC, acq_time DESC
            LIMIT 1000
        """).fetchall()
    except duckdb.CatalogException:
        # Table doesn't exist yet
        return []
    finally:
        con.close()

    return [
        {
            "lat": r[0],
            "lon": r[1],
            "brightness": r[2],
            "frp": r[3],
            "confidence": r[4],
        }
        for r in rows
    ]