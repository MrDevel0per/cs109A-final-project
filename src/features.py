"""Open-Meteo feature requests for the modelling resorts — ONE definition used by the prefetch script and notebooks.

Model choice (D-002): pinned, never best_match.
  * era5      (0.25°): atmospheric drivers — precipitation/snowfall, sunshine, wind, cloud, humidity, pressure, temps
  * era5_land (0.1°) : temperature (finer grid) + reanalysis snow depth (as a FEATURE, never the target)
Location: each SNOTEL station's own lat/lon with elevation = station elevation (m), timezone=auto (local calendar
day; verified in notebook 01b). Requests are chunked by ~5 winters to stay under Open-Meteo's per-request weight.
"""
from __future__ import annotations

import pandas as pd

import parse
from lineage import open_meteo

# 10 variables = weight 1.0 per (14 days) under Open-Meteo's fair-use accounting (D-027). Dropped as redundant /
# derivable: daylight_duration (deterministic from date+lat), rain_sum (~ precipitation - snowfall water eq.),
# wind_gusts_10m_max (~ wind_speed_10m_max), shortwave_radiation_sum (~ sunshine_duration + cloud cover).
ERA5_DAILY = ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "precipitation_sum",
              "snowfall_sum", "sunshine_duration", "wind_speed_10m_max", "cloud_cover_mean",
              "relative_humidity_2m_mean", "pressure_msl_mean"]
ERA5_LAND_DAILY = ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min", "snow_depth_mean"]
MODEL_VARS = {"era5": ERA5_DAILY, "era5_land": ERA5_LAND_DAILY}

# Feature window: from the summer before the earliest target winter (Brighton 1998) so 60+ day lags exist.
FEATURE_START, FEATURE_END = "1997-07-01", "2026-06-30"


def chunks(start: str = FEATURE_START, end: str = FEATURE_END, years: int = 5):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    while s <= e:
        nxt = min(s + pd.DateOffset(years=years) - pd.Timedelta(days=1), e)
        yield s.date().isoformat(), nxt.date().isoformat()
        s = nxt + pd.Timedelta(days=1)


def station_request(trip: str, lat: float, lon: float, elev_m: float, model: str, start: str, end: str) -> dict:
    return dict(latitude=lat, longitude=lon, elevation=round(float(elev_m)), start_date=start, end_date=end,
                daily=MODEL_VARS[model], models=model, timezone="auto")


def fetch_station(trip: str, lat: float, lon: float, elev_m: float) -> pd.DataFrame:
    """All feature chunks for one station -> one daily DataFrame, columns prefixed by model (era5__x, era5_land__x)."""
    parts = []
    for model in MODEL_VARS:
        frames = []
        for start, end in chunks():
            p = station_request(trip, lat, lon, elev_m, model, start, end)
            j = open_meteo(p, name=f"feat_{model}_{trip.replace(':', '_')}_{start[:4]}")
            frames.append(parse.open_meteo_daily(j))
        parts.append(pd.concat(frames).add_prefix(f"{model}__"))
    out = pd.concat(parts, axis=1)
    out.index.name = "date"
    return out
