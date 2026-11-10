"""Disconnect / crash robustness of lineage (no network)."""
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_lineage_parse import FakeResp, read_manifest, sandbox  # noqa: E402,F401
import lineage  # noqa: E402


def _seq_get(monkeypatch, items):
    """requests.get that yields items in order; an Exception instance is raised instead of returned."""
    seq = list(items)

    def fake_get(url, headers=None, timeout=None):
        x = seq.pop(0)
        if isinstance(x, Exception):
            raise x
        return x
    monkeypatch.setattr(lineage.requests, "get", fake_get)


def test_network_drop_then_recovery_is_retried(sandbox, monkeypatch):
    _seq_get(monkeypatch, [requests.exceptions.ConnectionError("wifi off"), requests.exceptions.Timeout("slow"),
                           FakeResp(200, b'{"v": 7}')])
    assert lineage.fetch("https://x.test/a", {"q": 1}, source="t", name="n") == {"v": 7}
    rows = read_manifest(sandbox["raw"])
    assert len(rows) == 1 and rows[0]["http_status"] == "200"


def test_persistent_network_failure_raises_and_caches_nothing(sandbox, monkeypatch):
    _seq_get(monkeypatch, [requests.exceptions.ConnectionError("down")] * 5)
    with pytest.raises(requests.exceptions.ConnectionError):
        lineage.fetch("https://x.test/a", {"q": 1}, source="t", name="n", retries=5)
    assert not sandbox["raw"].exists() or not any(sandbox["raw"].rglob("*.json"))


def test_hourly_limit_returns_immediately_without_in_process_retries(sandbox, monkeypatch):
    calls = []

    def fake_get(url, headers=None, timeout=None):
        calls.append(1)
        return FakeResp(429, b'{"error":true,"reason":"Hourly API request limit exceeded."}')
    monkeypatch.setattr(lineage.requests, "get", fake_get)
    with pytest.raises(RuntimeError, match="Hourly"):
        lineage.fetch("https://x.test/a", {"q": 1}, source="t", name="n")
    assert len(calls) == 1  # no pointless 65 s retries inside the hour


def test_crash_before_rename_leaves_no_valid_cache_entry(sandbox, monkeypatch):
    def boom(src, dst):
        raise KeyboardInterrupt("power loss between manifest write and rename")
    monkeypatch.setattr(lineage.os, "replace", boom)
    with pytest.raises(KeyboardInterrupt):
        lineage.fetch("https://x.test/a", {"q": 1}, source="t", name="n")
    assert not list(sandbox["raw"].rglob("*.json"))          # nothing that looks cached
    assert len(list(sandbox["raw"].rglob("*.json.part"))) == 1  # only a .part leftover
    monkeypatch.undo()  # restore os.replace etc.


def test_rerun_after_crash_refetches_and_supersedes(sandbox, monkeypatch):
    real_replace = lineage.os.replace
    monkeypatch.setattr(lineage.os, "replace", lambda s, d: (_ for _ in ()).throw(KeyboardInterrupt()))
    with pytest.raises(KeyboardInterrupt):
        lineage.fetch("https://x.test/a", {"q": 1}, source="t", name="n")
    monkeypatch.setattr(lineage.os, "replace", real_replace)
    assert lineage.fetch("https://x.test/a", {"q": 1}, source="t", name="n") == {"ok": 1}
    rows = read_manifest(sandbox["raw"])
    assert len(rows) == 2 and rows[0]["url"] == rows[1]["url"]   # latest row wins in verify_raw
    assert len(list(sandbox["raw"].rglob("*.json"))) == 1
