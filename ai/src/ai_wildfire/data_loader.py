import duckdb

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


def load_fires_with_weather(limit=None):
    """Load fires LEFT JOINed with weather_observations.

    Joins on rounded lat/lon (2 decimals) and date so that fire rows
    are enriched with wind_speed_kmh, humidity_pct, and temp_c when
    available.  Falls back to load_firms_table() if the
    weather_observations table does not exist yet.
    """
    con = duckdb.connect(DB_PATH)
    try:
        q = """
            SELECT f.*,
                   w.wind_speed_kmh,
                   w.humidity_pct,
                   w.temp_c
            FROM fires f
            LEFT JOIN weather_observations w
                ON ROUND(f.latitude, 2) = w.latitude
               AND ROUND(f.longitude, 2) = w.longitude
               AND f.acq_date = w.obs_date
        """
        if limit:
            q += f" LIMIT {int(limit)}"
        df = con.execute(q).df()
        con.close()
        return df
    except duckdb.CatalogException:
        con.close()
        return load_firms_table(limit=limit)
