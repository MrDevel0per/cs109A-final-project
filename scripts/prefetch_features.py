"""Warm the data/raw cache with Open-Meteo features for the modelling resorts (src/features.py defines the requests).

    uv run python scripts/prefetch_features.py

Safe to re-run: cached chunks are skipped. Rate limits: per-minute 429s are retried inside lineage.fetch; an
HOURLY limit makes this script sleep 15 min and retry; a DAILY limit stops it (exit 2) — re-run tomorrow.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import features  # noqa: E402
import sites  # noqa: E402
from lineage import snotel  # noqa: E402

meta = {s["stationTriplet"]: s for s in snotel("stations", {"stationTriplets": ",".join(sites.CANDIDATE_STATIONS),
                                                            "returnStationElements": "true"},
                                               name="stations_candidates_elements")}
stations = [t for r in sites.RESORTS.values() for t in r["stations"]]

for trip in stations:
    m = meta[trip]
    while True:
        try:
            df = features.fetch_station(trip, m["latitude"], m["longitude"], m["elevation"] * 0.3048)
            print(f"OK {trip} {m['name']}: {df.shape[0]} days x {df.shape[1]} vars, "
                  f"{df.index.min().date()}..{df.index.max().date()}, NaN cells {int(df.isna().sum().sum())}", flush=True)
            break
        except RuntimeError as e:
            msg = str(e)
            if "Daily" in msg:
                print(f"DAILY LIMIT at {trip}; re-run tomorrow. {msg[:160]}", flush=True)
                sys.exit(2)
            if "Hourly" in msg or "Minutely" in msg:
                print(f"rate limited at {trip}; sleeping 15 min. {msg[-90:]}", flush=True)
                time.sleep(900)
                continue
            print(f"ERROR {trip}: {msg[:300]}", flush=True)
            sys.exit(1)
print("DONE all stations", flush=True)
