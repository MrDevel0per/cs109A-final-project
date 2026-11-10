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

from lineage import RAW, ROOT, USER_AGENT, get_with_retry, store_and_log  # noqa: F401


def fetch_text(url: str, *, source: str, name: str, ext: str = "csv", refresh: bool = False,
               pause: float = 0.3, retries: int = 5) -> str:
    """GET `url` exactly as given; cache raw bytes to data/raw/<source>/<name>__<hash>.<ext>; return text."""
    h = hashlib.sha1(url.encode()).hexdigest()[:10]
    path = RAW / source / f"{name}__{h}.{ext}"
    if path.exists() and not refresh:
        return path.read_bytes().decode("utf-8")
    if os.environ.get("SNOWPREDICT_OFFLINE") == "1":
        raise FileNotFoundError(f"offline mode: {name} not in data/raw cache (url: {url})")

    r = get_with_retry(url, retries=retries, pause=pause)
    store_and_log(r, url=url, path=path, source=source, name=name)  # same crash-safe path as lineage.fetch
    return r.content.decode("utf-8")


REPORT_GENERATOR = "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily"


def report_generator_url(triplet: str, elements: list[str]) -> str:
    """Period-of-record daily CSV for one station (values only). '|' and '"' are percent-encoded."""
    els = ",".join(f"{e}::value" for e in elements)
    return f"{REPORT_GENERATOR}/{triplet}%7Cid=%22%22%7Cname/POR_BEGIN,POR_END/{els}"
