"""Raw JSON -> tidy pandas. Pure functions, no I/O, no cleaning (cleaning is a separate, documented step)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def snotel_to_long(payload: list) -> pd.DataFrame:
    """AWDB /data response -> one row per (station, element, date).

    Columns: station, element, date, value, qc_flag, qa_flag, orig_value, orig_qc_flag, unit.
    Values are left in source units (inches / degF). Nothing is filtered.
    """
    rows = []
    for st in payload:
        for el in st.get("data", []):
            meta = el["stationElement"]
            for v in el.get("values", []):
                rows.append({
                    "station": st["stationTriplet"], "element": meta["elementCode"],
                    "date": v["date"], "value": v.get("value"),
                    "qc_flag": v.get("qcFlag"), "qa_flag": v.get("qaFlag"),
                    "orig_value": v.get("origValue"), "orig_qc_flag": v.get("origQcFlag"),
                    "unit": meta.get("storedUnitCode"),
                })
    df = pd.DataFrame(rows)
    if len(df):
        df["date"] = pd.to_datetime(df["date"])
    return df


def open_meteo_daily(payload: dict) -> pd.DataFrame:
    """Open-Meteo response -> daily DataFrame indexed by date (source units, see payload['daily_units'])."""
    df = pd.DataFrame(payload["daily"])
    df["time"] = pd.to_datetime(df["time"])
    return df.set_index("time")


def winter_of(dates) -> np.ndarray:
    """Season label = calendar year in which the winter ENDS (Nov 2024–Apr 2025 -> 2025).
    Months Jul–Dec belong to the next year's winter."""
    d = pd.DatetimeIndex(dates)
    return (d.year + (d.month >= 7).astype(int)).to_numpy()
