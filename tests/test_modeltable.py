"""Leakage and correctness tests for src/modeltable.py (offline, synthetic data).

The central guarantee: a feature row dated t depends on data dated <= t only. We check it two independent ways:
truncation (recompute on data cut at t) and perturbation (scramble everything after t).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import modeltable as mt  # noqa: E402

WEATHER = ["tmax", "tmin", "tmean", "precip", "snowfall", "sun_h", "wind_max", "cloud", "rh", "pmsl",
           "land_tmean", "land_tmax", "land_tmin", "land_sd"]


def synthetic_daily(start="2000-07-01", end="2004-06-30", seed=0, gaps=True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end, freq="D", name="date")
    n = len(idx)
    d = pd.DataFrame({c: rng.normal(size=n) for c in WEATHER}, index=idx)
    d["snwd"] = np.abs(rng.normal(80, 30, n))
    d["wteq"] = d["snwd"] * 0.3
    d["prcp"] = np.abs(rng.normal(2, 1, n))
    d["snwd_orig"] = d["snwd"] + rng.normal(0, 1, n)
    if gaps:                                         # realistic NaN gaps in SNOTEL columns
        for c in ["snwd", "wteq", "prcp", "snwd_orig"]:
            d.loc[d.sample(frac=0.03, random_state=seed).index, c] = np.nan
    d["snwd_imputed"] = False
    d["snwd_measured"] = d["snwd"].notna()
    return d


def frames_equal(a: pd.Series, b: pd.Series) -> bool:
    a, b = a.astype(float).to_numpy(), b.astype(float).to_numpy()
    return bool(np.all((a == b) | (np.isnan(a) & np.isnan(b)) | np.isclose(a, b, rtol=1e-12, atol=1e-9)))


ISSUE_DATES = ["2001-10-02", "2001-12-31", "2002-02-28", "2003-03-01", "2003-10-01", "2004-03-31"]


@pytest.mark.parametrize("t", ISSUE_DATES)
def test_features_invariant_to_truncation(t):
    d = synthetic_daily()
    full = mt.build_features(d).loc[t]
    cut = mt.build_features(d.loc[:t]).loc[t]
    for c in full.index:
        assert frames_equal(pd.Series([full[c]]), pd.Series([cut[c]])), c


@pytest.mark.parametrize("t", ISSUE_DATES)
def test_features_invariant_to_future_perturbation(t):
    d = synthetic_daily()
    d2 = d.copy()
    future = d2.index > pd.Timestamp(t)
    rng = np.random.default_rng(42)
    for c in WEATHER + ["snwd", "wteq", "prcp", "snwd_orig"]:
        d2.loc[future, c] = rng.normal(500, 100, future.sum())     # wildly different future
    a, b = mt.build_features(d).loc[:t], mt.build_features(d2).loc[:t]
    for c in a.columns:
        assert frames_equal(a[c], b[c]), c


def test_labels_are_exactly_horizon_ahead_and_only_lookahead():
    d = synthetic_daily(gaps=False)
    lab = mt.labels(d)
    t = pd.Timestamp("2002-01-15")
    assert lab.loc[t, "target_date"] == t + pd.Timedelta(days=mt.HORIZON)
    assert lab.loc[t, "y"] == d.loc[t + pd.Timedelta(days=mt.HORIZON), "snwd"]
    # perturbing the target date changes the label (labels DO look ahead, by design) ...
    d2 = d.copy()
    d2.loc[t + pd.Timedelta(days=mt.HORIZON), "snwd"] = -1.0
    assert mt.labels(d2).loc[t, "y"] == -1.0
    # ... but changes nothing in that day's features
    assert frames_equal(mt.build_features(d).loc[t], mt.build_features(d2).loc[t])


def test_labels_past_end_of_data_are_missing_not_wrapped():
    d = synthetic_daily(gaps=False)
    lab = mt.labels(d)
    tail = lab[lab.target_date > d.index.max()]
    assert len(tail) == mt.HORIZON and tail.y.isna().all() and not tail.y_measured.any()


def test_imputed_target_is_not_measured():
    d = synthetic_daily(gaps=False)
    t = pd.Timestamp("2002-01-15")
    tgt = t + pd.Timedelta(days=mt.HORIZON)
    d.loc[tgt, ["snwd_imputed", "snwd_measured"]] = [True, False]
    lab = mt.labels(d).loc[t]
    assert not lab.y_measured and np.isnan(lab.y)          # imputed depth never appears as a target value


def test_build_features_rejects_gappy_index():
    d = synthetic_daily().drop(pd.Timestamp("2002-01-10"))
    with pytest.raises(ValueError):
        mt.build_features(d)


def test_trailing_windows_are_strict():
    d = synthetic_daily(gaps=False)
    d.loc["2002-01-10", "prcp"] = np.nan
    f = mt.build_features(d)
    assert np.isnan(f.loc["2002-01-10", "prcp_sum_7"]) and np.isnan(f.loc["2002-01-16", "prcp_sum_7"])
    assert not np.isnan(f.loc["2002-01-17", "prcp_sum_7"])
    assert np.isclose(f.loc["2002-01-17", "prcp_sum_7"], d.loc["2002-01-11":"2002-01-17", "prcp"].sum())


def test_water_year_accumulators_reset_on_oct1():
    d = synthetic_daily(gaps=False)
    d["snowfall"] = 1.0
    f = mt.build_features(d)
    assert f.loc["2001-10-01", "snowfall_wy"] == 1.0 and f.loc["2001-09-30", "snowfall_wy"] == 365.0
    assert f.loc["2001-10-01", "dowy"] == 0 and f.loc["2002-04-30", "dowy"] == 211


def test_model_table_target_window_and_same_winter():
    d = synthetic_daily(gaps=False)
    t = mt.model_table(d, "X", 2001, 2004)
    assert t.target_date.dt.month.isin(mt.SEASON_MONTHS).all()
    assert (t.index.min() == pd.Timestamp("2000-10-02"))          # first issue date for a Nov 1 target
    assert ((t.target_date - t.index) == pd.Timedelta(days=mt.HORIZON)).all()
    from parse import winter_of
    assert (winter_of(t.index) == t.winter.to_numpy()).all()
    assert set(t.winter) == {2001, 2002, 2003, 2004}
    assert set(mt.model_table(d, "X", 2002, 2003).winter) == {2002, 2003}


def test_climatology_ignores_other_winters():
    d = synthetic_daily(gaps=False)
    train = [2001, 2002]
    c1 = mt.climatology(d, train)
    d2 = d.copy()
    from parse import winter_of
    other = np.isin(winter_of(d2.index), [2003, 2004])
    d2.loc[other, "snwd"] = 9999.0                                       # poison the non-training winters ...
    d2.loc[other, "snwd_measured"] = ~d2.loc[other, "snwd_measured"]      # ... and their measured flags
    c2 = mt.climatology(d2, train)
    assert np.allclose(c1, c2, equal_nan=True)
    assert c1.max() < 9999


def test_climatology_uses_measured_only():
    d = synthetic_daily(gaps=False)
    d.loc["2001-12-01":"2001-12-31", ["snwd_measured"]] = False
    d.loc["2001-12-01":"2001-12-31", "snwd"] = 9999.0
    assert mt.climatology(d, [2002]).max() < 9999


def test_split_assignment_disjoint():
    spans = sorted(((lo or -10**9), hi) for lo, hi in mt.SPLIT_BOUNDS.values())
    assert all(a[1] < b[0] for a, b in zip(spans, spans[1:]))            # bounds do not overlap
    s = mt.split_of(np.arange(1998, 2027))
    assert set(s) == {"train", "val", "test"}
    assert list(s[np.arange(1998, 2027) == 2016]) == ["train"] and list(s[np.arange(1998, 2027) == 2021]) == ["test"]


def test_composite_requires_all_members():
    idx = pd.date_range("2005-01-01", periods=4, freq="D")
    rows = []
    for st, vals, imp in [("A", [10, 20, np.nan, 40], [False, True, False, False]),
                          ("B", [30, 40, 50, np.nan], [False, False, False, False])]:
        for dt, v, i in zip(idx, vals, imp):
            rows.append({"station": st, "date": dt, "SNWD_cm": v, "WTEQ_cm": v, "PRCP_mm": 1.0,
                         "SNWD_imputed": i, "SNWD_nrcs_orig": v / 2.54 if v == v else np.nan})
    r = mt.resort_snotel(pd.DataFrame(rows), ["A", "B"])
    assert r.snwd.tolist()[:2] == [20.0, 30.0] and r.snwd.iloc[2:].isna().all()
    assert r.snwd_measured.tolist() == [True, False, False, False]      # day 2 has an imputed member
    assert np.allclose(r.snwd_orig.iloc[:2], [20.0, 30.0])


def test_orig_same_day_guard():
    idx = pd.date_range("2005-01-01", periods=4, freq="D")
    rows = [{"station": "A", "date": dt, "SNWD_cm": 0.0, "WTEQ_cm": 0.0, "PRCP_mm": 0.0, "SNWD_imputed": False,
             "SNWD_nrcs_orig": o} for dt, o in zip(idx, [-1.0, -8190.0, 10.0, 999.0])]
    r = mt.resort_snotel(pd.DataFrame(rows), ["A"])
    assert r.snwd_orig.iloc[0] == 0.0 and np.isnan(r.snwd_orig.iloc[1]) and np.isclose(r.snwd_orig.iloc[2], 25.4)
    assert np.isnan(r.snwd_orig.iloc[3])


def _orig_rows(vals):
    idx = pd.date_range("2005-01-01", periods=len(vals), freq="D")
    return pd.DataFrame([{"station": "A", "date": dt, "SNWD_cm": 0.0, "WTEQ_cm": 0.0, "PRCP_mm": 0.0,
                          "SNWD_imputed": False, "SNWD_nrcs_orig": o} for dt, o in zip(idx, vals)])


def test_orig_causal_spike_rule():
    vals = [10.0] * 8 + [208.0] + [11.0] * 5            # one glitch on day 8
    r = mt.resort_snotel(_orig_rows(vals), ["A"])
    assert np.isnan(r.snwd_orig.iloc[8]) and r.snwd_orig.drop(r.index[8]).notna().all()
    for n in (4, 10, 25):                                # glitches persisting 4, 10, 25 days are all rejected
        vals = [10.0] * 8 + [208.0] * n + [11.0] * 10
        r = mt.resort_snotel(_orig_rows(vals), ["A"])
        assert r.snwd_orig.iloc[8:8 + n].isna().all() and r.snwd_orig.iloc[8 + n:].notna().all(), n


def test_orig_spike_filter_reanchors_after_long_gap():
    s = pd.Series([10.0] * 5 + [np.nan] * 40 + [80.0] * 5)   # new level after a 40-day gap is accepted
    assert mt.causal_spike_filter(s).iloc[45:].notna().all()


def test_orig_cleaning_is_causal():
    rng = np.random.default_rng(3)
    vals = list(np.abs(rng.normal(40, 5, 60)))
    base = mt.resort_snotel(_orig_rows(vals), ["A"]).snwd_orig
    vals2 = vals[:30] + list(rng.normal(300, 50, 30))     # garbage after day 29
    pert = mt.resort_snotel(_orig_rows(vals2), ["A"]).snwd_orig
    assert frames_equal(base.iloc[:30], pert.iloc[:30])
