"""Lineage-tracked fetching for NON-JSON (text/CSV) responses.

Same contract as `lineage.fetch` (raw bytes saved unmodified under data/raw/<source>/, one MANIFEST.csv row per
download, honest User-Agent, transient 429/5xx logged but not cached, offline mode honoured) — it reuses
lineage's internals so both helpers write identical manifest rows. Used for the NRCS Report Generator CSV
(an independent NRCS endpoint used to cross-check our AWDB parsing; notebook 01b).
"""
from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone

import requests

from lineage import RAW, ROOT, USER_AGENT, _log


def fetch_text(url: str, *, source: str, name: str, ext: str = "csv", refresh: bool = False,
               pause: float = 0.3, retries: int = 5) -> str:
    """GET `url` exactly as given; cache raw bytes to data/raw/<source>/<name>__<hash>.<ext>; return text."""
    h = hashlib.sha1(url.encode()).hexdigest()[:10]
    path = RAW / source / f"{name}__{h}.{ext}"
    if path.exists() and not refresh:
        return path.read_bytes().decode("utf-8")
    if os.environ.get("SNOWPREDICT_OFFLINE") == "1":
        raise FileNotFoundError(f"offline mode: {name} not in data/raw cache (url: {url})")

    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=180)
    for attempt in range(max(retries - 1, 0)):
        if r.status_code != 429 and r.status_code < 500:
            break
        time.sleep(65 if r.status_code == 429 else 5 * (attempt + 1))
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=180)
    time.sleep(pause)

    transient = r.status_code == 429 or r.status_code >= 500
    _log({
        "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source, "name": name, "url": url,
        "file": "" if transient else str(path.relative_to(ROOT)), "bytes": len(r.content),
        "sha256": hashlib.sha256(r.content).hexdigest(), "http_status": r.status_code,
    })
    if transient:
        raise RuntimeError(f"HTTP {r.status_code} for {url}: {r.text[:200]}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(r.content)
    return r.content.decode("utf-8")


REPORT_GENERATOR = "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily"


def report_generator_url(triplet: str, elements: list[str]) -> str:
    """Period-of-record daily CSV for one station (values only). '|' and '"' are percent-encoded."""
    els = ",".join(f"{e}::value" for e in elements)
    return f"{REPORT_GENERATOR}/{triplet}%7Cid=%22%22%7Cname/POR_BEGIN,POR_END/{els}"
