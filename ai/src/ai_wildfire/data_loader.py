import duckdb

from . import configs


def load_firms_table(limit=None):
    """Load the `fires` table from wildfire.db produced by backend ingestion."""
    con = duckdb.connect(configs.DB_PATH)
    q = "SELECT * FROM fires"
    if limit:
        q += f" LIMIT {int(limit)}"
    df = con.execute(q).df()
    con.close()
    return df
