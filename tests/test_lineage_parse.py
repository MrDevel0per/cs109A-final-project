"""Tests for lineage (fetch/caching/manifest/offline/migration), verify_raw, lineage_text and parse.

No network: requests.get is monkeypatched; data/raw is redirected to a pytest tmp dir.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import lineage  # noqa: E402
import lineage_text  # noqa: E402
import parse  # noqa: E402
import verify_raw  # noqa: E402


# ----------------------------------------------------------------------------- fixtures
class FakeResp:
    def __init__(self, status=200, body=b'{"ok": 1}'):
        self.status_code, self.content = status, body
        self.text = body.decode()


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point lineage + verify_raw at an empty temp project; count HTTP calls; no sleeping."""
    raw = tmp_path / "data" / "raw"
    for mod in (lineage, verify_raw):
        monkeypatch.setattr(mod, "ROOT", tmp_path)
        monkeypatch.setattr(mod, "RAW", raw)
        monkeypatch.setattr(mod, "MANIFEST", raw / "MANIFEST.csv")
    monkeypatch.setattr(lineage_text, "ROOT", tmp_path)
    monkeypatch.setattr(lineage_text, "RAW", raw)
    monkeypatch.setattr(lineage.time, "sleep", lambda s: None)
    monkeypatch.delenv("SNOWPREDICT_OFFLINE", raising=False)
    calls = []

    def install(*responses):
        seq = list(responses)

        def fake_get(url, headers=None, timeout=None):
            calls.append({"url": url, "headers": headers})
            return seq.pop(0) if len(seq) > 1 else seq[0]
        monkeypatch.setattr(lineage.requests, "get", fake_get)
        monkeypatch.setattr(lineage_text.requests, "get", fake_get)
    install(FakeResp())
    return {"root": tmp_path, "raw": raw, "calls": calls, "install": install}


def read_manifest(raw):
    with (raw / "MANIFEST.csv").open(newline="") as f:
        return list(csv.DictReader(f))


# ----------------------------------------------------------------------------- canonical_url
def test_canonical_url_is_order_independent_and_joins_lists():
    a = lineage.canonical_url("https://x/api", {"b": 2, "a": ["t", "u"], "c": "1:2:*"})
    b = lineage.canonical_url("https://x/api", {"c": "1:2:*", "a": ("t", "u"), "b": 2})
    assert a == b == "https://x/api?a=t,u&b=2&c=1:2:*"


def test_canonical_url_distinguishes_values():
    assert lineage.canonical_url("u", {"a": 1}) != lineage.canonical_url("u", {"a": 2})


# ----------------------------------------------------------------------------- fetch
def test_fetch_caches_raw_bytes_and_logs_manifest(sandbox):
    body = b'{"daily": {"time": ["2020-01-01"]}}'
    sandbox["install"](FakeResp(200, body))
    out = lineage.fetch("https://x/api", {"q": 1}, source="s", name="n")
    assert out == json.loads(body)
    rows = read_manifest(sandbox["raw"])
    assert len(rows) == 1
    r = rows[0]
    f = sandbox["root"] / r["file"]
    assert f.read_bytes() == body                                   # stored unmodified
    assert r["sha256"] == hashlib.sha256(body).hexdigest()
    assert r["http_status"] == "200" and r["bytes"] == str(len(body))
    assert r["user_agent"] == lineage.USER_AGENT
    assert sandbox["calls"][0]["headers"]["User-Agent"] == lineage.USER_AGENT
    # second call is served from cache: no new HTTP call, no new manifest row
    assert lineage.fetch("https://x/api", {"q": 1}, source="s", name="n") == json.loads(body)
    assert len(sandbox["calls"]) == 1 and len(read_manifest(sandbox["raw"])) == 1


def test_user_agent_is_honest():
    ua = lineage.USER_AGENT
    assert "automated" in ua and "github.com/MrDevel0per/cs109A-final-project" in ua
    assert "@" not in ua  # no personal email in request headers


def test_fetch_caches_deterministic_errors(sandbox):
    sandbox["install"](FakeResp(400, b'{"error": true, "reason": "out of range"}'))
    out = lineage.fetch("https://x/api", {"q": 1}, source="s", name="bad")
    assert out["reason"] == "out of range"
    assert read_manifest(sandbox["raw"])[0]["file"] != ""          # 400 kept as evidence


def test_fetch_transient_error_logged_not_cached(sandbox):
    sandbox["install"](FakeResp(429, b'{"error": true, "reason": "Minutely limit"}'))
    with pytest.raises(RuntimeError):
        lineage.fetch("https://x/api", {"q": 1}, source="s", name="rl", retries=2)
    rows = read_manifest(sandbox["raw"])
    assert [r["http_status"] for r in rows] == ["429"] and rows[0]["file"] == ""
    assert not list((sandbox["raw"]).rglob("rl__*"))
    # a later successful attempt fetches again
    sandbox["install"](FakeResp(200, b'{"ok": 2}'))
    assert lineage.fetch("https://x/api", {"q": 1}, source="s", name="rl") == {"ok": 2}


def test_fetch_retries_then_succeeds(sandbox):
    sandbox["install"](FakeResp(503, b"{}"), FakeResp(200, b'{"ok": 3}'))
    assert lineage.fetch("https://x/api", {}, source="s", name="retry") == {"ok": 3}
    assert len(sandbox["calls"]) == 2


def test_offline_mode_raises_without_network(sandbox, monkeypatch):
    monkeypatch.setenv("SNOWPREDICT_OFFLINE", "1")
    with pytest.raises(FileNotFoundError):
        lineage.fetch("https://x/api", {"q": 9}, source="s", name="off")
    with pytest.raises(FileNotFoundError):
        lineage_text.fetch_text("https://x/r.csv", source="s", name="off")
    assert sandbox["calls"] == []


def test_offline_mode_still_reads_cache(sandbox, monkeypatch):
    lineage.fetch("https://x/api", {"q": 1}, source="s", name="n")
    monkeypatch.setenv("SNOWPREDICT_OFFLINE", "1")
    assert lineage.fetch("https://x/api", {"q": 1}, source="s", name="n") == {"ok": 1}


# ----------------------------------------------------------------------------- manifest migration
def test_manifest_migration_backfills_legacy_user_agent(sandbox):
    raw = sandbox["raw"]
    raw.mkdir(parents=True)
    old_cols = [c for c in lineage.MANIFEST_COLS if c != "user_agent"]
    with (raw / "MANIFEST.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=old_cols)
        w.writeheader()
        w.writerow({c: f"old_{c}" for c in old_cols})
    lineage.fetch("https://x/api", {"q": 1}, source="s", name="n")
    rows = read_manifest(raw)
    assert list(rows[0].keys()) == lineage.MANIFEST_COLS
    assert rows[0]["user_agent"] == lineage.LEGACY_USER_AGENT and rows[0]["url"] == "old_url"
    assert rows[1]["user_agent"] == lineage.USER_AGENT


# ----------------------------------------------------------------------------- lineage_text
def test_fetch_text_matches_lineage_contract(sandbox):
    body = b"# header\nDate,SNWD\n2020-01-01,40\n"
    sandbox["install"](FakeResp(200, body))
    url = lineage_text.report_generator_url("547:CO:SNTL", ["SNWD", "WTEQ"])
    assert url.endswith('/547:CO:SNTL%7Cid=%22%22%7Cname/POR_BEGIN,POR_END/SNWD::value,WTEQ::value')
    assert lineage_text.fetch_text(url, source="rg", name="t") == body.decode()
    r = read_manifest(sandbox["raw"])[0]
    assert r["url"] == url and r["file"].endswith(".csv") and r["user_agent"] == lineage.USER_AGENT
    assert (sandbox["root"] / r["file"]).read_bytes() == body
    lineage_text.fetch_text(url, source="rg", name="t")
    assert len(sandbox["calls"]) == 1


# ----------------------------------------------------------------------------- verify_raw
def test_verify_raw_detects_changed_missing_and_orphan(sandbox, capsys):
    lineage.fetch("https://x/api", {"q": 1}, source="s", name="a")
    lineage.fetch("https://x/api", {"q": 2}, source="s", name="b")
    assert verify_raw.main() == 0
    files = [sandbox["root"] / r["file"] for r in read_manifest(sandbox["raw"])]
    files[0].write_bytes(b'{"tampered": true}')
    assert verify_raw.main() == 1 and "CHANGED" in capsys.readouterr().out
    files[0].unlink()
    assert verify_raw.main() == 1 and "MISSING" in capsys.readouterr().out
    lineage.fetch("https://x/api", {"q": 1}, source="s", name="a", refresh=True)
    (sandbox["raw"] / "s" / "stray.json").write_text("{}")
    assert verify_raw.main() == 1 and "ORPHAN" in capsys.readouterr().out


# ----------------------------------------------------------------------------- parse
@pytest.mark.parametrize("date,winter", [
    ("2024-06-30", 2024), ("2024-07-01", 2025), ("2024-11-01", 2025), ("2024-12-31", 2025),
    ("2025-01-01", 2025), ("2024-02-29", 2024), ("2025-04-30", 2025), ("1979-10-01", 1980),
])
def test_winter_of(date, winter):
    assert parse.winter_of(pd.to_datetime([date]))[0] == winter


def test_winter_of_accepts_series_and_returns_array():
    s = pd.Series(pd.to_datetime(["2020-12-01", "2021-03-01", "2021-08-01"]))
    out = parse.winter_of(s)
    assert isinstance(out, np.ndarray) and out.tolist() == [2021, 2021, 2022]


SNOTEL_FIXTURE = [{
    "stationTriplet": "547:CO:SNTL",
    "data": [
        {"stationElement": {"elementCode": "SNWD", "storedUnitCode": "in"},
         "values": [{"date": "2010-01-01", "value": 28, "qcFlag": "V", "origValue": 28, "origQcFlag": "V"},
                    {"date": "2010-01-02", "value": 31, "qcFlag": "E", "qaFlag": "A", "origValue": 204, "origQcFlag": "S"}]},
        {"stationElement": {"elementCode": "TAVG", "storedUnitCode": "degF"},
         "values": [{"date": "2010-01-01", "value": 12.5}]},
    ]}]


def test_snotel_to_long_keeps_everything_unfiltered():
    df = parse.snotel_to_long(SNOTEL_FIXTURE)
    assert list(df.columns) == ["station", "element", "date", "value", "qc_flag", "qa_flag",
                                "orig_value", "orig_qc_flag", "unit"]
    assert len(df) == 3 and pd.api.types.is_datetime64_any_dtype(df["date"])
    edited = df[(df.element == "SNWD") & (df.date == "2010-01-02")].iloc[0]
    assert (edited.value, edited.orig_value, edited.qc_flag, edited.orig_qc_flag, edited.qa_flag) == (31, 204, "E", "S", "A")
    t = df[df.element == "TAVG"].iloc[0]
    assert t.unit == "degF" and pd.isna(t.qc_flag) and pd.isna(t.orig_value)


def test_snotel_to_long_empty():
    assert parse.snotel_to_long([]).empty
    assert parse.snotel_to_long([{"stationTriplet": "x", "data": []}]).empty


def test_open_meteo_daily():
    df = parse.open_meteo_daily({"daily": {"time": ["2020-01-01", "2020-01-02"], "snow_depth_mean": [0.7, None]}})
    assert isinstance(df.index, pd.DatetimeIndex) and df.loc["2020-01-01", "snow_depth_mean"] == 0.7
    assert np.isnan(df.loc["2020-01-02", "snow_depth_mean"])
