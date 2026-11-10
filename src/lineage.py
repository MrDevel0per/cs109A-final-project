"""Data-lineage helpers for SnowPredict.

Every byte of external data enters the project through `fetch()`:

* the exact request (base URL + sorted query params) is canonicalised into one URL,
* the raw response body is written UNMODIFIED to data/raw/<source>/<name>__<hash>.json,
* one row is appended to data/raw/MANIFEST.csv: when, what URL, which file, size, sha256, HTTP status.

Re-running a notebook reads the cached file instead of re-downloading (unless refresh=True), so
results are reproducible even if the upstream API changes; MANIFEST.csv tells you exactly where and
when each file came from. Error responses (e.g. HTTP 400) are saved and logged too — they are
evidence for findings such as "the seasonal API has no data before 2025-09".
"""
from __future__ import annotations

import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "MANIFEST.csv"
MANIFEST_COLS = ["fetched_utc", "source", "name", "url", "file", "bytes", "sha256", "http_status", "user_agent"]

# Honest, identifiable User-Agent (course requirement): says what we are, that we are automated, why, and how to
# reach us. Contact is the public project repo (no personal email in request headers).
USER_AGENT = (f"SnowPredict/0.2 (automated data collection for a Harvard CS1090A student final project; "
              f"non-commercial; contact: https://github.com/MrDevel0per/cs109A-final-project) "
              f"python-requests/{requests.__version__}")
# The UA used for requests made before 2026-11-10 (rows logged before the user_agent column existed).
LEGACY_USER_AGENT = "snowpredict-course-project/0.1 (DataSci1 final project)"


def canonical_url(base: str, params: dict) -> str:
    """Deterministic URL: params sorted, lists joined with commas."""
    flat = {k: ",".join(map(str, v)) if isinstance(v, (list, tuple)) else v for k, v in params.items()}
    return f"{base}?{urlencode(sorted(flat.items()), safe=',:*')}"


def _migrate_manifest() -> None:
    """Add columns introduced after the manifest was created, back-filling known values (never guessing)."""
    if not MANIFEST.exists():
        return
    with MANIFEST.open(newline="") as f:
        rows = list(csv.DictReader(f))
        header = rows and list(rows[0].keys()) or []
    if "user_agent" in header or not rows:
        return
    for r in rows:
        r["user_agent"] = LEGACY_USER_AGENT
    with MANIFEST.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLS)
        w.writeheader()
        w.writerows(rows)


def _log(row: dict) -> None:
    _migrate_manifest()
    row = {**row, "user_agent": USER_AGENT}
    new = not MANIFEST.exists()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLS)
        if new:
            w.writeheader()
        w.writerow(row)


def fetch(base: str, params: dict, *, source: str, name: str, refresh: bool = False,
          pause: float = 0.3, retries: int = 5) -> dict | list:
    """GET a JSON API with on-disk caching + manifest logging. Returns parsed JSON (errors included)."""
    url = canonical_url(base, params)
    h = hashlib.sha1(url.encode()).hexdigest()[:10]
    path = RAW / source / f"{name}__{h}.json"
    if path.exists() and not refresh:
        return json.loads(path.read_bytes())

    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=180)
    for attempt in range(max(retries - 1, 0)):
        if r.status_code != 429 and r.status_code < 500:
            break
        # Open-Meteo's free tier has per-minute/hour/day limits; a minutely 429 clears after ~60 s.
        time.sleep(65 if r.status_code == 429 else 5 * (attempt + 1))
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=180)
    time.sleep(pause)

    transient = r.status_code == 429 or r.status_code >= 500
    row = {
        "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source, "name": name, "url": url,
        "file": "" if transient else str(path.relative_to(ROOT)), "bytes": len(r.content),
        "sha256": hashlib.sha256(r.content).hexdigest(), "http_status": r.status_code,
    }
    _log(row)  # transient failures are logged but NOT cached, so a re-run fetches again
    if transient:
        raise RuntimeError(f"HTTP {r.status_code} for {url}: {r.text[:200]}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return json.loads(r.content)


# ---- thin wrappers for the two sources -------------------------------------------------------
OM_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
AWDB = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"


def open_meteo(params: dict, name: str, base: str = OM_ARCHIVE, **kw):
    return fetch(base, params, source="open_meteo", name=name, **kw)


def snotel(endpoint: str, params: dict, name: str, **kw):
    return fetch(f"{AWDB}/{endpoint}", params, source="snotel", name=name, **kw)


def manifest():
    import pandas as pd
    return pd.read_csv(MANIFEST) if MANIFEST.exists() else pd.DataFrame(columns=MANIFEST_COLS)
