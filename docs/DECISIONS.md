# Decision log

Format: each entry has an ID, status (`PROPOSED` / `ACCEPTED` / `SUPERSEDED by D-x`), date, context, options, decision, rationale, evidence.
Only a group member changes an entry's status to `ACCEPTED`.

---

## D-001 — Weather source: Open-Meteo Historical Weather API
**Status:** ACCEPTED (required by staff) · 2026-11-09
**Context:** Staff comments say the proposal named Open-Meteo but linked to Meteostat.
**Decision:** Open-Meteo is the primary weather source. Correct link: https://open-meteo.com/en/docs/historical-weather-api
**Rationale:** Staff requirement. Free, global, no key, 1940 to present.

## D-002 — Pin Open-Meteo models; never use `best_match`
**Status:** PROPOSED · 2026-11-09
**Context:** `best_match` changes its underlying model in 2017 (ERA5-Land → ECMWF IFS). That produces up to ~8°C jumps on the same date (DATA_SOURCES §1.3). Our test set is the later winters, so a source change would land exactly on the train/test boundary.
**Options:** (a) `best_match` · (b) `era5_seamless` · (c) `era5` for atmosphere + `era5_land` for temperature and snow depth · (d) `cerra` (Europe only, ends June 2021)
**Decision:** (c), or equivalently (b): ERA5 (0.25°) for snowfall, sunshine, wind and cloud; ERA5-Land (0.1°) for temperature and snow depth.
**Rationale:** Consistent reanalysis across the whole period, so no source break. CERRA is rejected because it ends in 2021, which leaves no recent test winters, and it is Europe only.

## D-003 — Where to collect data: US West, anchored on Aspen, instead of the three European resorts
**Status:** ACCEPTED · 2026-11-09 (user: go US West, Aspen as anchor, Aspen treated as ONE resort; which other resorts is decided in D-007)
**Context:** The proposal used St. Anton, Grandvalira and Val di Fassa. Open-Meteo's snow depth is a grid-cell value and does not follow the slopes' elevation (DATA_SOURCES §1.4). Without ground-truth snow observations we can't tell whether reanalysis snow resembles what skiers experience. The milestone grades our reasoning about data quality.
**Options:**
1. Keep the three European resorts. Open-Meteo only. CERRA gives better resolution but ends in 2021. No easy ground truth.
2. Switch to US western resorts. Open-Meteo is still the primary source, and SNOTEL on-mountain stations add measured snow depth, SWE and temperature (~20 winters of depth; 40+ of SWE and temperature).
3. Hybrid: US resorts as the core plus St. Anton as a single unvalidated comparison.
**Recommendation:** Option 2, with Aspen as the anchor. A group member is from Aspen, which gives us local knowledge and a motivating story. The Aspen area has 5+ SNOTEL stations with 40+ winters. Add 3–5 contrast resorts covering different snow climates:
  - Continental CO: Aspen area (Independence Pass, Kiln, Brumley, Ivanhoe, Nast Lake), plus Vail Mountain or Copper Mountain
  - Intermountain UT: Snowbird or Brighton
  - Maritime: Palisades Tahoe (CA) and/or Stevens Pass (WA)
  - Northern Rockies: Lone Mountain / Big Sky (MT)
**Rationale:**
- SNOTEL is free, has a REST API and needs no key. Several stations sit on the resorts themselves at ski-terrain elevation.
- Lets us **validate** Open-Meteo against measurements. The first check gave r = 0.94 for snow depth with a 21% low bias (DATA_SOURCES §2.2), a concrete data-quality finding for the presentation.
- Different snow climates let us answer the proposal's secondary question: does accuracy differ by resort?
**Cost:** The revised proposal must explain the change of region. The staff conditions (Open-Meteo; climatology from training years; test on later winters) are all unaffected.

## D-004 — No real 30-day forecast benchmark; baselines are climatology and persistence
**Status:** PROPOSED · 2026-11-09
**Context:** The Open-Meteo seasonal API (ECMWF SEAS5) only covers 2025-09 onward, with no hindcasts. The historical-forecast and previous-runs APIs cover only short lead times.
**Decision:** The baselines are (1) day-of-season climatology computed from training seasons only (staff requirement), and (2) persistence (today's value carried forward 30 days). Optionally, log SEAS5 forecasts for the current 2026-27 season as a live, out-of-sample bonus.

## D-005 — Target: SNOTEL measured snow depth (SNWD) as ground truth
**Status:** PROPOSED · 2026-11-09 (the user is leaning this way but "not sure")
**Context:** The original proposal predicted several weather variables and combined them into a composite ski-condition index. With SNOTEL available, we can predict a *measured* quantity instead of a reanalysis estimate.
**Options:**
1. **SNWD** (snow depth, inches). This is what skiers feel. Record starts around 1997–98 at the best stations, giving up to ~28 winters; at many stations it starts around 2004–07.
2. **WTEQ** (snow water equivalent). Records start 1979+ (up to ~46 winters) and come from a pillow sensor, so they are typically cleaner. It is less directly "skiable".
3. Open-Meteo reanalysis snow depth (not measured; grid-cell value; ~21% low at Independence Pass).
**Leaning:** (1) SNWD at time *t*+30 days as the target. Open-Meteo supplies the weather features; it remains the primary weather source, as staff require. WTEQ is kept as a fallback or secondary target if the SNWD record proves too short.
**Open:** keep the original composite ski-condition index as a secondary output, or drop it? Not decided.

## D-006 — Use as many winters as possible
**Status:** ACCEPTED · 2026-11-09 (user)
**Implication:** Each station uses its full usable SNWD record (no common start year is imposed across resorts). The train/test split is by winter, with the later winters as the test set. Climatology is computed from training winters only (staff condition).

## D-007 — Separate model per resort; 3 resorts
**Status:** Separate models ACCEPTED (user: "separate models, maybe 3 resorts"). Resort choice PROPOSED pending the coverage evidence in notebook 01 · 2026-11-09
**Proposed resorts** (one per snow climate):
- **Aspen**, continental Colorado (see D-008)
- **Brighton UT**, intermountain (366:UT:SNTL). SNWD from 1997, a longer record than Snowbird's (~2003)
- **Palisades Tahoe CA**, maritime (784:CA:SNTL). SNWD from 1998

## D-008 — How to represent Aspen as one resort
**Status:** PROPOSED / open · 2026-11-09
**Options:** (a) a single representative SNOTEL station; (b) a composite (e.g. the mean) of several Aspen-area stations.
**Risk with (b):** stations start in different years, so a simple mean changes composition over time and creates artificial jumps. A composite would need a fixed station set over the period it covers.
**Evidence to come:** notebook 01 §5, covering inter-station SNWD correlation, coverage by winter, and distance and elevation relative to Aspen's 4 ski areas (Aspen Mountain, Highlands, Buttermilk, Snowmass).

## D-009 — SNOTEL fetch parameters: get everything, filter ourselves
**Status:** ACCEPTED · 2026-11-09
**Decision:** Every SNOTEL `/data` request uses `returnFlags=true`, `returnOriginalValues=true`, `returnSuspectData=true`, with `periodRef=END` stated explicitly.
**Rationale:**
- The API default `returnSuspectData=false` silently drops suspect values. That is a hidden filter we would not otherwise know about.
- Original values reveal sensor spikes. Ivanhoe (547:CO), 2010-01-02: original 204 in (`origQcFlag` S), edited to 31 in (`qcFlag` E).
- The flags only add information; nothing is removed at fetch time. All filtering happens in documented cleaning steps.
**Evidence:** Ivanhoe SNWD 1998–2026 (qcFlag, qaFlag) tally: (V,–) 6426, (E,–) 2598, (V,A) 422, (E,A) 253, (V,P) 185, (K,A) 56, (E,P) 56, (K,P) 33. About ⅓ of values are edited or estimated (E/K).

## D-010 — Do not use NRCS-provided normals
**Status:** ACCEPTED · 2026-11-09
**Decision:** Never request or use `centralTendencyType` (NRCS 30-year averages/medians).
**Rationale:** Those normals span years that include our test winters. Using them would leak test information and violate staff condition 4 (climatology from training years only).

## D-011 — Data lineage
**Status:** ACCEPTED · 2026-11-09
**Decision:** All external data enters through `src/lineage.py::fetch()`.
- Raw response bytes are stored unmodified in `data/raw/<source>/<name>__<hash>.json`.
- Each fetch appends a row to `data/raw/MANIFEST.csv`: UTC time, canonical URL, file, bytes, sha256, HTTP status.
- Re-runs read the cache instead of re-downloading.
- Transient errors (429/5xx) are logged but not cached. Deterministic errors (e.g. 400) are cached as evidence.
- Site and station definitions live in `src/sites.py`.

## D-012 — Environment
**Status:** ACCEPTED · 2026-11-09
**Decision:** A uv project (`pyproject.toml` + `uv.lock`) with Python 3.12, matching the course homework workflow. Run with `uv sync`, then `uv run jupyter lab`.

## D-013 — Public GitHub repo
**Status:** PROPOSED (the exclusion is pending group confirmation) · 2026-11-09
**Decision:** Public repo `MrDevel0per/cs109A-final-project`, with collaborators mlehuray246 and nxt-txms.
**Exclusion:** `Original Proposal/` (course spec, staff comments, and a PDF containing the author's email) is excluded from the public repo by default. It is easy to add later if the group agrees.

---

## D-014 — Honest, identifiable User-Agent on every request
**Status:** ACCEPTED (course requirement, per user) · 2026-11-10
**Decision:** `src/lineage.py` sends
`SnowPredict/0.2 (automated data collection for a Harvard CS1090A student final project; non-commercial; contact: https://github.com/MrDevel0per/cs109A-final-project) python-requests/<ver>`.
It says who we are, that we are automated, why, and how to reach us. The contact is the public repo; no personal email goes in headers.
**Lineage:** MANIFEST.csv has a `user_agent` column. The 62 requests made before this change (2026-11-10 00:2x UTC) used `snowpredict-course-project/0.1 (DataSci1 final project)`. The migration back-fills exactly that string; it doesn't guess. We kept that data rather than re-fetching it (user: "if you already queried it that's fine").
The ad-hoc exploratory `curl` probes in session 1 (pre-repo, results only in DATA_SOURCES.md) used curl's default `curl/<ver>` UA. All of them are reproduced through `lineage.fetch` in notebook 01.

## D-015 — Commit raw data to git
**Status:** ACCEPTED · 2026-11-10 (answers former Q3)
**Context:** `data/raw/` is ~145 MB (SNOTEL ~142 MB, 20 files ≤ 9 MB each; Open-Meteo ~3.5 MB). This is under GitHub's 100 MB per-file limit, and the JSON compresses ~15× (8.8 MB → 0.58 MB gzip).
**Options:** (a) plain git · (b) Git LFS · (c) Google Drive / external storage plus a download script · (d) don't store, re-fetch from the APIs.
**Decision:** (a) Commit `data/raw/` and MANIFEST.csv to plain git (user agreed 2026-11-10).
**Rationale:** Durability. The exact bytes we analyzed are preserved even if NRCS revises edits (it does: QA flags move from P to A) or Open-Meteo reprocesses data. Collaborators can run the notebooks offline with no API quota. sha256 values in the manifest let anyone verify the files.
**Why not the others:** (b) LFS's free tier caps storage and bandwidth at 1 GB, and each collaborator clone counts against it; it's only needed for files over 100 MB, and ours are ≤ 9 MB. (c) Drive separates data from the code and commit history, so lineage depends on a link staying alive. (d) Upstream data changes over time, so a re-fetch would not reproduce our results.
**Revisit if:** a single file gets close to 50 MB (GitHub's warning size), or the total passes ~500 MB.

## Open questions for the group
- Q1: Target: SNWD (D-005) or WTEQ? Keep the original composite ski-condition index as a secondary output, or drop it?
- Q2: Aspen representation (D-008): one station, or a fixed-membership composite?
- Q4: Confirm excluding `Original Proposal/` from the public repo (D-013).
