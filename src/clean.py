"""Reusable, pure cleaning functions for SNOTEL data (used by notebooks/02_cleaning_snotel.ipynb).

Nothing here does I/O. Every rule returns a boolean mask so the notebook can count rows affected and
write them to the cleaning log before applying an action.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

IN_TO_CM = 2.54
IN_TO_MM = 25.4


def f_to_c(f):
    """Degrees Fahrenheit -> Celsius."""
    return (f - 32.0) * 5.0 / 9.0


def long_to_wide(sn: pd.DataFrame, elements: list[str]) -> pd.DataFrame:
    """Long SNOTEL table (parse.snotel_to_long) -> one row per (station, date).

    For each element E: E (NRCS value), E_nrcs_qc, E_nrcs_qa, E_nrcs_orig (value before NRCS edit).
    """
    parts = []
    for col, suffix in [("value", ""), ("qc_flag", "_nrcs_qc"), ("qa_flag", "_nrcs_qa"), ("orig_value", "_nrcs_orig")]:
        p = sn.pivot(index=["station", "date"], columns="element", values=col)
        p = p.reindex(columns=elements)
        p.columns = [f"{e}{suffix}" for e in p.columns]
        parts.append(p)
    w = pd.concat(parts, axis=1).sort_index()
    # numeric columns may come back as object when a whole element is missing for a station
    for e in elements:
        for c in (e, f"{e}_nrcs_orig"):
            w[c] = pd.to_numeric(w[c], errors="coerce")
    return w


def complete_calendar(w: pd.DataFrame) -> pd.DataFrame:
    """Reindex each station to a continuous daily calendar (first..last date it reports anything),
    so missing days become explicit NaN rows instead of silently absent rows."""
    out = []
    for st, d in w.groupby(level="station"):
        dates = d.index.get_level_values("date")
        idx = pd.MultiIndex.from_product([[st], pd.date_range(dates.min(), dates.max(), freq="D")],
                                         names=["station", "date"])
        out.append(d.reindex(idx))
    return pd.concat(out)


def rolling_median_residual(s: pd.Series, window: int = 7) -> pd.Series:
    """Per-station residual from a centred rolling median. A one/two-day spike leaves a large residual;
    a genuine step change (storm, melt-out) does not, because the median follows it within window/2 days."""
    med = s.groupby(level="station").transform(
        lambda x: x.rolling(window, center=True, min_periods=3).median())
    return s - med


def nan_run_lengths(s: pd.Series) -> pd.Series:
    """For each NaN, the length of the consecutive-NaN run it belongs to (0 for non-NaN). Per station."""
    def one(x: pd.Series) -> pd.Series:
        isna = x.isna().to_numpy()
        run_id = np.cumsum(~isna)              # same id within a NaN run
        lengths = pd.Series(isna.astype(int)).groupby(run_id).transform("sum").to_numpy()
        return pd.Series(np.where(isna, lengths, 0), index=x.index)
    return s.groupby(level="station", group_keys=False).apply(one)


def ffill_short_gaps(s: pd.Series, max_gap: int) -> tuple[pd.Series, pd.Series]:
    """CAUSAL gap fill: per station, forward-fill (carry the last valid value) across INTERIOR NaN runs of
    length <= max_gap. Runs longer than max_gap stay entirely NaN (never partially filled); leading and
    trailing NaNs stay NaN. Returns (filled series, imputed mask).

    Every filled VALUE equals the last observation at or before that date, so it carries no future
    information and is safe to use as a feature. (Whether a gap qualifies — "it ends within max_gap days" —
    is decided from the missingness pattern; no future values enter the fill.)
    """
    runs = nan_run_lengths(s)
    ffilled = s.groupby(level="station").ffill()
    bfilled = s.groupby(level="station").bfill()           # only used to test "a later value exists"
    interior = s.isna() & ffilled.notna() & bfilled.notna()
    imputed = interior & (runs <= max_gap)
    return s.where(~imputed, ffilled), imputed


def in_season(dates) -> np.ndarray:
    """True for Nov 1 – Apr 30 (the project's ski-season window)."""
    m = pd.DatetimeIndex(dates).month
    return np.asarray((m >= 11) | (m <= 4))


def water_year(dates) -> np.ndarray:
    """USGS/NRCS water year: Oct 1 – Sep 30, labelled by the year it ends. SNOTEL PREC resets each Oct 1."""
    d = pd.DatetimeIndex(dates)
    return (d.year + (d.month >= 10).astype(int)).to_numpy()


def constant_run_lengths(s: pd.Series) -> pd.Series:
    """For each value, the length of the run of IDENTICAL consecutive values it belongs to (per station).
    NaN breaks runs. Used to detect flat-lined ("stuck") loggers."""
    def one(x: pd.Series) -> pd.Series:
        v = x.to_numpy()
        new = np.ones(len(v), dtype=bool)
        new[1:] = ~((v[1:] == v[:-1]) & ~np.isnan(v[1:]))
        rid = np.cumsum(new)
        return pd.Series(pd.Series(rid).groupby(rid).transform("size").to_numpy(), index=x.index)
    return s.groupby(level="station", group_keys=False).apply(one)
