"""Verify data/raw against data/raw/MANIFEST.csv (lineage integrity check).

    uv run python src/verify_raw.py

Checks, for the latest manifest row of every URL that was cached:
  * the file exists and its sha256 matches the manifest  -> data are byte-identical to what was downloaded;
and reports files on disk that no manifest row accounts for (data that entered outside lineage.fetch).
Exit code 1 on any problem.
"""
from __future__ import annotations

import hashlib
import sys

from lineage import MANIFEST, RAW, ROOT, manifest


def main() -> int:
    m = manifest()
    cached = m[m["file"].fillna("") != ""].drop_duplicates("url", keep="last")
    bad = []
    for r in cached.itertuples():
        p = ROOT / r.file
        if not p.exists():
            bad.append(f"MISSING  {r.file}")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != r.sha256:
            bad.append(f"CHANGED  {r.file}")
    listed = {str(ROOT / f) for f in cached["file"]}
    orphans = [p for p in RAW.rglob("*.json") if str(p) not in listed]
    for p in orphans:
        bad.append(f"ORPHAN   {p.relative_to(ROOT)} (not in {MANIFEST.name})")
    print(f"{len(cached)} cached files checked, {len(bad)} problem(s)")
    print("\n".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
