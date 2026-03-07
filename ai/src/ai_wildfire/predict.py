import json
from .model_store import load_model
from .features import basic_preprocess
import pandas as pd
from .data_loader import load_firms_table

def predict_from_db(limit=10):
    df = load_firms_table(limit=limit)
    df_proc = basic_preprocess(df)
    X = df_proc[['bright_ti4','bright_ti5','frp','hour','lat_bin','lon_bin']].fillna(0)
    model = load_model()
    probs = None
    try:
        probs = model.predict_proba(X)[:,1]
    except Exception:
        probs = model.predict(X)
    df_out = df.copy()
    df_out['pred_score'] = probs
    print(df_out[['latitude','longitude','acq_date','acq_time','confidence','pred_score']].head(20))
    return df_out