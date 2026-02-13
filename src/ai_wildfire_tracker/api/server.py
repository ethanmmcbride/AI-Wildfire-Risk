from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import duckdb

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "wildfire.db"

@app.get("/fires")
def get_fires():
    con =duckdb.connect(DB_PATH)
    con.execute("""
    CREATE TABLE IF NOT EXISTS fires (
    latitude DOUBLE,
    longitude DOUBLE,
    bright_ti4 DOUBLE,
    frp DOUBLE,
    confidence VARCHAR,
    acq_date DATE,
    acq_time VARCHAR
)
""")
    rows = con.execute("""
        SELECT latitude, longitude, bright_ti4, frp, confidence
        FROM fires
        ORDER BY acq_date DESC, acq_time DESC
        LIMIT 1000  
     """).fetchall()
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