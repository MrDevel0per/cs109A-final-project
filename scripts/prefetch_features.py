"""Warm the data/raw cache with Open-Meteo features for the modelling resorts (src/sources.py defines the requests).

    caffeinate -i nohup uv run python scripts/prefetch_features.py >> data/prefetch_features.log 2>&1 &

Unattended and disconnect-safe:
  * idempotent — cached chunks are skipped, so killing and re-running just resumes;
  * network drop / laptop sleep -> lineage retries, then this loop waits 2 min and tries again (forever);
  * Open-Meteo HOURLY limit -> sleep to the top of the next hour (+2 min); DAILY limit -> sleep to 00:05 UTC;
  * every download is crash-safe (lineage.store_and_log: .part file -> manifest row -> atomic rename).
Progress lines are timestamped (UTC) for the log.
"""
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import lineage  # noqa: E402
import sites  # noqa: E402
import sources  # noqa: E402


def say(msg: str) -> None:
    print(f"{datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ} {msg}", flush=True)


def sleep_until(t: datetime, why: str) -> None:
    secs = max((t - datetime.now(timezone.utc)).total_seconds(), 60)
    say(f"{why}; sleeping {secs / 60:.0f} min until {t:%H:%M}Z")
    time.sleep(secs)


for stale in lineage.RAW.rglob("*.part"):  # leftovers from a crash mid-write are never valid cache entries
    say(f"removing stale partial file {stale.name}")
    stale.unlink()

meta = {s["stationTriplet"]: s for s in sources.station_metadata()}
stations = [t for r in sites.RESORTS.values() for t in r["stations"]]
say(f"start: {len(stations)} stations, models {list(sources.MODEL_VARS)}, {sources.FEATURE_START}..{sources.FEATURE_END}")

for trip in stations:
    m = meta[trip]
    while True:
        try:
            df = sources.fetch_station(trip, m["latitude"], m["longitude"], m["elevation"] * 0.3048)
            say(f"OK {trip} {m['name']}: {df.shape[0]} days x {df.shape[1]} vars, "
                f"{df.index.min().date()}..{df.index.max().date()}, NaN cells {int(df.isna().sum().sum())}")
            break
        except RuntimeError as e:  # HTTP 429 / 5xx surfaced by lineage
            msg, now = str(e), datetime.now(timezone.utc)
            if "Daily" in msg:
                sleep_until((now + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0),
                            f"daily limit at {trip}")
            elif "Hourly" in msg:
                sleep_until((now + timedelta(hours=1)).replace(minute=2, second=0, microsecond=0),
                            f"hourly limit at {trip}")
            else:
                say(f"server error at {trip}: {msg[:200]}; retry in 5 min")
                time.sleep(300)
        except lineage.NETWORK_ERRORS as e:
            say(f"network unavailable at {trip} ({type(e).__name__}); retry in 2 min")
            time.sleep(120)
say("DONE all stations")
