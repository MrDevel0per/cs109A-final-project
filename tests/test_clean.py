import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import clean  # noqa: E402
import parse  # noqa: E402


def _series(vals, start="2020-01-01", station="X"):
    idx = pd.MultiIndex.from_product([[station], pd.date_range(start, periods=len(vals))], names=["station", "date"])
    return pd.Series(vals, index=idx, dtype=float)


def test_f_to_c():
    assert clean.f_to_c(32) == 0
    assert abs(clean.f_to_c(-40) + 40) < 1e-12


def test_winter_and_water_year_labels():
    d = pd.to_datetime(["2024-09-30", "2024-10-01", "2024-11-01", "2025-04-30", "2025-07-01"])
    assert list(parse.winter_of(d)) == [2025, 2025, 2025, 2025, 2026]  # Jul–Dec -> next year
    assert list(clean.water_year(d)) == [2024, 2025, 2025, 2025, 2025]
    assert list(clean.in_season(d)) == [False, False, True, True, False]


def test_spike_detected_but_step_is_not():
    spike = _series([30, 30, 30, 200, 30, 30, 30])
    assert clean.rolling_median_residual(spike).abs().idxmax()[1] == pd.Timestamp("2020-01-04")
    assert clean.rolling_median_residual(spike).abs().max() > 100
    step = _series([30, 30, 30, 60, 60, 60, 60, 60])
    assert clean.rolling_median_residual(step).abs().max() <= 30  # step edge only, not a spike
    assert (clean.rolling_median_residual(step).abs() > 20).sum() <= 1


def test_ffill_fills_short_interior_gaps_with_previous_value():
    s = _series([np.nan, 1, np.nan, np.nan, 4, np.nan, np.nan, np.nan, np.nan, 9, np.nan])
    filled, imp = clean.ffill_short_gaps(s, max_gap=3)
    v = filled.to_numpy()
    assert np.isnan(v[0]) and np.isnan(v[-1])           # leading / trailing untouched
    assert v[2] == 1 and v[3] == 1                       # 2-day gap filled with the PREVIOUS value
    assert np.isnan(v[5:9]).all()                        # 4-day gap untouched (not partially filled)
    assert imp.sum() == 2 and list(np.flatnonzero(imp.to_numpy())) == [2, 3]


def test_ffill_is_causal_in_values():
    a = _series([5, np.nan, np.nan, 7, 8])
    b = _series([5, np.nan, np.nan, 100, -3])            # same past, different values after the gap
    fa, _ = clean.ffill_short_gaps(a, max_gap=3)
    fb, _ = clean.ffill_short_gaps(b, max_gap=3)
    assert list(fa.to_numpy()[:3]) == list(fb.to_numpy()[:3]) == [5, 5, 5]


def test_ffill_does_not_cross_stations():
    a = _series([1, np.nan], station="A")
    b = _series([np.nan, 5], station="B")
    filled, imp = clean.ffill_short_gaps(pd.concat([a, b]), max_gap=3)
    assert imp.sum() == 0


def test_complete_calendar_adds_missing_days():
    idx = pd.MultiIndex.from_tuples([("A", pd.Timestamp("2020-01-01")), ("A", pd.Timestamp("2020-01-04"))],
                                    names=["station", "date"])
    w = pd.DataFrame({"SNWD": [1.0, 2.0]}, index=idx)
    out = clean.complete_calendar(w)
    assert len(out) == 4 and out["SNWD"].isna().sum() == 2


def test_constant_run_lengths():
    s = _series([1, 1, 1, 2, np.nan, np.nan, 3, 3])
    assert list(clean.constant_run_lengths(s)) == [3, 3, 3, 1, 1, 1, 2, 2]
