import duckdb
import pandas as pd
from .configs import DB_PATH

def load_firms_table(limit=None):
    """Load the `fires` table from wildfire.db produced by backend ingestion."""
    con = duckdb.connect(DB_PATH)
    q = "SELECT * FROM fires"
    if limit:
        q += f" LIMIT {int(limit)}"
    df = con.execute(q).df()
    con.close()
    return df