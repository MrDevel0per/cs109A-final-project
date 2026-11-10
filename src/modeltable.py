"""Modelling table for SnowPredict: one row = (resort, issue date t); target = measured SNOTEL snow depth at t + 30 d.

Leakage contract (enforced by tests/test_modeltable.py):
  * every FEATURE dated t is a function of rows dated <= t of the (already cleaned) resort frame: trailing windows,
    backward differences, cumulative sums/maxima within the water year. Given those inputs, data after t can change
    nothing in a feature row; this is tested by truncating and by perturbing the future. Upstream steps that use later
    information (NRCS's after-the-fact edits, which <=3-day gaps get filled) are listed in the notebook's leakage
    section (D-024, CODE_AUDIT A-02/A-03);
  * the ONLY forward-looking operation in the project is `labels()`, which looks up the target at t + HORIZON;
  * the only fitted object here is `climatology()`, which takes an explicit list of winters and ignores all others.

Conventions (AGENTS.md): SNOTEL SNWD dated d = end-of-day-d reading; Open-Meteo daily values dated d are local-calendar-
day aggregates (timezone=auto). Weather dated d pairs with SNWD dated d, so on issue date t the forecaster knows
weather through day t and the end-of-day-t snow reading.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

import parse

HORIZON = 30                       # days ahead (D-005 / revised question)
WINDOWS = (7, 30)                  # trailing windows for weather / snow-change features (D-031)
SEASON_MONTHS = (11, 12, 1, 2, 3, 4)   # target dates Nov 1 – Apr 30 (D-023, D-029)

# Split by winter (labelled by the year the season ends). Proposed in D-032.
SPLIT_BOUNDS = {"train": (None, 2016), "val": (2017, 2020), "test": (2021, 2026)}

# Open-Meteo column -> short feature-source name, plus SI conversion factor (raw units stay in data/raw).
OM_RENAME = {
    "era5__temperature_2m_max": ("tmax", 1.0), "era5__temperature_2m_min": ("tmin", 1.0),
    "era5__temperature_2m_mean": ("tmean", 1.0), "era5__precipitation_sum": ("precip", 1.0),       # mm
    "era5__snowfall_sum": ("snowfall", 1.0),                                                          # cm
    "era5__sunshine_duration": ("sun_h", 1 / 3600),                                                   # s -> h
    "era5__wind_speed_10m_max": ("wind_max", 1.0), "era5__cloud_cover_mean": ("cloud", 1.0),          # km/h, %
    "era5__relative_humidity_2m_mean": ("rh", 1.0), "era5__pressure_msl_mean": ("pmsl", 1.0),         # %, hPa
    "era5_land__temperature_2m_mean": ("land_tmean", 1.0), "era5_land__temperature_2m_max": ("land_tmax", 1.0),
    "era5_land__temperature_2m_min": ("land_tmin", 1.0),
    "era5_land__snow_depth_mean": ("land_sd", 100.0),                                                 # m -> cm
}
# ---------------------------------------------------------------------------------------------------------------
# resort-level daily series
# ---------------------------------------------------------------------------------------------------------------
def _daily_index(frames: list[pd.Series | pd.DataFrame]) -> pd.DatetimeIndex:
    lo = min(f.index.min() for f in frames)
    hi = max(f.index.max() for f in frames)
    return pd.date_range(lo, hi, freq="D", name="date")


def resort_snotel(clean: pd.DataFrame, stations: list[str]) -> pd.DataFrame:
    """Resort-level daily SNOTEL series from the clean table (notebook §3).

    Fixed-membership composite (D-008): the value is the mean over member stations on days when ALL members have a
    value, else NaN, so the composite never silently changes composition. `snwd_measured` is True only if every
    member's SNWD is present and NOT imputed (D-022): only such days may be labels or evaluation truth.
    """
    per = {}
    for t in stations:
        s = clean[clean.station == t].set_index("date").sort_index()
        if s.index.duplicated().any():
            raise ValueError(f"duplicate dates for {t}")
        per[t] = s
    idx = _daily_index(list(per.values()))
    per = {t: s.reindex(idx) for t, s in per.items()}

    def composite(col: str) -> pd.Series:
        f = pd.concat([per[t][col].astype(float) for t in stations], axis=1)
        return f.mean(axis=1).where(f.notna().all(axis=1))

    out = pd.DataFrame(index=idx)
    out["snwd"] = composite("SNWD_cm")
    out["wteq"] = composite("WTEQ_cm")
    out["prcp"] = composite("PRCP_mm")
    imp = pd.concat([per[t]["SNWD_imputed"].fillna(False).astype(bool) for t in stations], axis=1).any(axis=1)
    out["snwd_imputed"] = imp & out.snwd.notna()
    out["snwd_measured"] = out.snwd.notna() & ~imp
    return out


def resort_weather(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Mean of member stations' Open-Meteo daily features (each requested at its own station lat/lon/elevation),
    renamed to short names and converted to SI (cm, h). Open-Meteo returns no NaN for these variables (notebook §3.7),
    so the mean is over a fixed set of members on every day."""
    idx = _daily_index(frames)
    stack = pd.concat([f.reindex(idx) for f in frames], keys=range(len(frames)))
    m = stack.groupby(level=1).mean()
    m = m[[c for c in OM_RENAME if c in m.columns]]
    m = m.rename(columns={c: OM_RENAME[c][0] for c in m.columns})
    for short, k in OM_RENAME.values():
        if short in m:
            m[short] = m[short] * k
    m.index.name = "date"
    return m


# ---------------------------------------------------------------------------------------------------------------
# features (causal) and labels (the only look-ahead)
# ---------------------------------------------------------------------------------------------------------------
def water_year_start(dates: pd.DatetimeIndex) -> pd.DatetimeIndex:
    y = dates.year - (dates.month < 10)
    return pd.to_datetime(pd.DataFrame({"year": y, "month": 10, "day": 1}))


def day_of_water_year(dates: pd.DatetimeIndex) -> np.ndarray:
    """Days since Oct 1 of the water year (Oct 1 = 0). In leap winters dates after Feb 28 shift by one day."""
    return (dates - pd.DatetimeIndex(water_year_start(dates))).days.to_numpy()


def _trailing(s: pd.Series, w: int, how: str) -> pd.Series:
    r = s.rolling(w, min_periods=w)          # strict: any missing day in the window -> NaN (never a partial sum)
    return getattr(r, how)()


def build_features(d: pd.DataFrame) -> pd.DataFrame:
    """Feature rows for every date in `d` (continuous daily index). Each row uses rows dated <= its date only."""
    idx = d.index
    if not (isinstance(idx, pd.DatetimeIndex) and idx.is_monotonic_increasing and idx.is_unique
            and (len(idx) < 2 or (idx[1:] - idx[:-1] == pd.Timedelta(days=1)).all())):
        raise ValueError("build_features needs a continuous, unique, increasing daily DatetimeIndex")
    f = pd.DataFrame(index=idx)
    wy = pd.Series(np.asarray(water_year_start(idx)), index=idx)

    # calendar (known in advance; not data)
    f["dowy"] = day_of_water_year(idx)
    f["target_dowy"] = f["dowy"] + HORIZON
    ang = 2 * np.pi * idx.day_of_year.to_numpy() / 365.25
    f["doy_sin"], f["doy_cos"] = np.sin(ang), np.cos(ang)

    # SNOTEL state at t (cleaned; causal <=3-day forward fill allowed as a feature, D-022)
    f["snwd_t"] = d["snwd"]
    f["wteq_t"] = d["wteq"]
    f["snwd_t_imputed"] = d["snwd_imputed"].astype(float)
    for k in WINDOWS:
        f[f"d_snwd_{k}"] = d["snwd"] - d["snwd"].shift(k)
        f[f"d_wteq_{k}"] = d["wteq"] - d["wteq"].shift(k)
        f[f"prcp_sum_{k}"] = _trailing(d["prcp"], k, "sum")
    f["snwd_peak_wy"] = d["snwd"].groupby(wy).cummax()     # running max since Oct 1 (NaN days skipped)
    f["wteq_peak_wy"] = d["wteq"].groupby(wy).cummax()

    # Open-Meteo weather (ERA5 0.25°; ERA5-Land 0.1°)
    for c in ["tmax", "tmin", "tmean", "snowfall", "precip"]:
        f[f"{c}_t"] = d[c]
    pdd = d["tmean"].clip(lower=0)                          # positive degree-days (melt proxy)
    for k in WINDOWS:
        for c in ["precip", "snowfall", "sun_h"]:
            f[f"{c}_sum_{k}"] = _trailing(d[c], k, "sum")
        f[f"pdd_sum_{k}"] = _trailing(pdd, k, "sum")
        for c in ["tmean", "tmax", "tmin", "wind_max", "cloud", "rh", "pmsl"]:
            f[f"{c}_mean_{k}"] = _trailing(d[c], k, "mean")
    f["pmsl_t"] = d["pmsl"]
    f["d_pmsl_3"] = d["pmsl"] - d["pmsl"].shift(3)
    for c, src in [("snowfall_wy", d["snowfall"]), ("precip_wy", d["precip"]), ("pdd_wy", pdd)]:
        f[c] = src.groupby(wy).cumsum()
    f["land_sd_t"] = d["land_sd"]
    for k in WINDOWS:
        f[f"d_land_sd_{k}"] = d["land_sd"] - d["land_sd"].shift(k)
    f["land_tmean_mean_7"] = _trailing(d["land_tmean"], 7, "mean")
    return f


# Data dictionary for build_features' columns: (regex, group, source, definition, unit). A standalone "k" in a
# definition is replaced by the window length captured by the regex. Keep this next to build_features: every new feature needs an entry.
FEATURE_DOCS = [
    (r"dowy", "calendar", "—", "days since Oct 1 of the water year, at issue date t", "d"),
    (r"target_dowy", "calendar", "—", "dowy + 30 (the target's day of season; used to look up climatology)", "d"),
    (r"doy_(sin|cos)", "calendar", "—", "sin/cos of 2π·day-of-year/365.25", "—"),
    (r"snwd_t", "snow state", "SNOTEL", "snow depth at end of day t (cleaned; ≤3-day causal fill allowed)", "cm"),
    (r"wteq_t", "snow state", "SNOTEL", "snow-water equivalent at end of day t", "cm"),
    (r"snwd_t_imputed", "snow state", "SNOTEL", "1 if snwd_t was forward-filled (D-022)", "0/1"),
    (r"d_snwd_(\d+)", "snow state", "SNOTEL", "snwd_t − snwd_(t−k)", "cm"),
    (r"d_wteq_(\d+)", "snow state", "SNOTEL", "wteq_t − wteq_(t−k)", "cm"),
    (r"prcp_sum_(\d+)", "snow state", "SNOTEL", "station precipitation, sum over t−k+1..t (strict)", "mm"),
    (r"(snwd|wteq)_peak_wy", "snow state", "SNOTEL", "season maximum from Oct 1 to t", "cm"),
    (r"(tmax|tmin|tmean)_t", "weather, day t", "ERA5", "day-t temperature", "°C"),
    (r"snowfall_t", "weather, day t", "ERA5", "day-t snowfall", "cm"),
    (r"precip_t", "weather, day t", "ERA5", "day-t precipitation", "mm"),
    (r"pmsl_t", "weather, day t", "ERA5", "day-t mean sea-level pressure", "hPa"),
    (r"d_pmsl_3", "weather, day t", "ERA5", "pressure tendency pmsl_t − pmsl_(t−3)", "hPa"),
    (r"precip_sum_(\d+)", "weather, trailing", "ERA5", "precipitation, sum over t−k+1..t", "mm"),
    (r"snowfall_sum_(\d+)", "weather, trailing", "ERA5", "snowfall, sum over t−k+1..t", "cm"),
    (r"sun_h_sum_(\d+)", "weather, trailing", "ERA5", "sunshine hours, sum over t−k+1..t", "h"),
    (r"pdd_sum_(\d+)", "weather, trailing", "ERA5", "positive degree-days Σ max(tmean, 0) over t−k+1..t (melt proxy)", "°C·d"),
    (r"(tmean|tmax|tmin)_mean_(\d+)", "weather, trailing", "ERA5", "temperature, mean over t−k+1..t", "°C"),
    (r"wind_max_mean_(\d+)", "weather, trailing", "ERA5", "daily max wind, mean over t−k+1..t", "km/h"),
    (r"(cloud|rh)_mean_(\d+)", "weather, trailing", "ERA5", "cloud cover / relative humidity, mean over t−k+1..t", "%"),
    (r"pmsl_mean_(\d+)", "weather, trailing", "ERA5", "sea-level pressure, mean over t−k+1..t", "hPa"),
    (r"snowfall_wy", "weather, season-to-date", "ERA5", "snowfall, running total from Oct 1 to t", "cm"),
    (r"precip_wy", "weather, season-to-date", "ERA5", "precipitation, running total from Oct 1 to t", "mm"),
    (r"pdd_wy", "weather, season-to-date", "ERA5", "positive degree-days, running total from Oct 1 to t", "°C·d"),
    (r"land_sd_t", "reanalysis snow", "ERA5-Land", "modelled snow depth on day t (feature only, never truth)", "cm"),
    (r"d_land_sd_(\d+)", "reanalysis snow", "ERA5-Land", "land_sd_t − land_sd_(t−k)", "cm"),
    (r"land_tmean_mean_7", "reanalysis snow", "ERA5-Land", "7-day mean ERA5-Land temperature (0.1° grid)", "°C"),
]


def feature_dictionary(columns) -> pd.DataFrame:
    """One documented row per feature column; raises KeyError for an undocumented column."""
    rows = []
    for col in columns:
        for pat, group, source, definition, unit in FEATURE_DOCS:
            m = re.fullmatch(pat, col)
            if m:
                k = next((g for g in m.groups() if g and g.isdigit()), None)
                rows.append((col, group, source, re.sub(r"\bk\b", k, definition) if k else definition, unit))
                break
        else:
            raise KeyError(f"feature {col!r} has no FEATURE_DOCS entry")
    return pd.DataFrame(rows, columns=["column", "group", "source", "definition", "unit"])


def labels(d: pd.DataFrame, horizon: int = HORIZON) -> pd.DataFrame:
    """THE ONLY LOOK-AHEAD: target = SNWD at t + horizon (by date lookup, not by position)."""
    tgt = d.index + pd.Timedelta(days=horizon)
    out = pd.DataFrame(index=d.index)
    out["target_date"] = tgt
    # y is NaN unless the target is MEASURED (not imputed, all members present): imputed depths can never be truth
    out["y"] = d["snwd"].where(d["snwd_measured"].astype(bool)).reindex(tgt).to_numpy()
    out["y_measured"] = d["snwd_measured"].reindex(tgt).fillna(False).astype(bool).to_numpy()
    return out


def model_table(d: pd.DataFrame, resort: str, first_winter: int, last_winter: int) -> pd.DataFrame:
    """Features + labels for issue dates whose TARGET date falls in Nov–Apr of winters first..last."""
    t = build_features(d).join(labels(d))
    t = t[t.target_date.dt.month.isin(SEASON_MONTHS)].copy()
    t["winter"] = parse.winter_of(t.target_date)
    issue_winter = parse.winter_of(t.index)
    if not (issue_winter == t["winter"].to_numpy()).all():
        raise AssertionError("issue date and target date fall in different winters")
    t = t[t.winter.between(first_winter, last_winter)]
    t.insert(0, "resort", resort)
    t["split"] = split_of(t["winter"])
    t.index.name = "date"
    return t


def _check_split_bounds() -> None:
    spans = sorted(((lo if lo is not None else -10**9), hi) for lo, hi in SPLIT_BOUNDS.values())
    if any(a_hi >= b_lo for (_, a_hi), (b_lo, _) in zip(spans, spans[1:])):
        raise ValueError(f"SPLIT_BOUNDS overlap: {SPLIT_BOUNDS}")


_check_split_bounds()


def split_of(winters) -> np.ndarray:
    """'train' / 'val' / 'test' by winter label (SPLIT_BOUNDS); '' for winters outside every split."""
    w = np.asarray(winters)
    out = np.full(w.shape, "", dtype=object)
    for name, (lo, hi) in SPLIT_BOUNDS.items():
        out[(w >= (lo if lo is not None else -10**9)) & (w <= hi)] = name
    return out


# ---------------------------------------------------------------------------------------------------------------
# baseline: day-of-season climatology, fitted on an explicit set of winters only
# ---------------------------------------------------------------------------------------------------------------
def climatology(d: pd.DataFrame, winters, halfwidth: int = 7, stat: str = "mean") -> pd.Series:
    """Climatological SNWD by day of water year, from MEASURED (non-imputed) SNWD in `winters` only.

    For each day-of-water-year k, pools all measured values with |dowy - k| <= halfwidth across the given winters and
    takes their mean (staff: "historical averages") or median (the MAE-optimal constant). Rows of any other winter
    are dropped before anything is computed, so test-winter data can never enter (staff condition 4)."""
    winters = set(int(w) for w in winters)
    m = d[d["snwd_measured"]].copy()
    m = m[(m.index.month >= 10) | (m.index.month <= 6)]               # Oct 1 – Jun 30: water year == winter label
    m = m[np.isin(parse.winter_of(m.index), list(winters))]
    dowy = day_of_water_year(m.index)
    vals = m["snwd"].to_numpy()
    ks = np.arange(0, 273)                                           # Oct 1 .. Jun 30
    res = []
    for k in ks:
        v = vals[np.abs(dowy - k) <= halfwidth]
        res.append(np.nan if v.size == 0 else (v.mean() if stat == "mean" else np.median(v)))
    return pd.Series(res, index=pd.Index(ks, name="dowy"), name=f"clim_{stat}")
