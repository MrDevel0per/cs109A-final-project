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
**Status:** ACCEPTED · 2026-11-10 (user: measured SNWD is the primary target; the SWE/density extension is D-026)
**Context:** The original proposal predicted several weather variables and combined them into a composite ski-condition index. With SNOTEL available, we can predict a *measured* quantity instead of a reanalysis estimate.
**Options:**
1. **SNWD** (snow depth, inches). This is what skiers feel. Record starts around 1997–98 at the best stations, giving up to ~28 winters; at many stations it starts around 2004–07.
2. **WTEQ** (snow water equivalent). Records start 1979+ (up to ~46 winters) and come from a pillow sensor, so they are typically cleaner. It is less directly "skiable".
3. Open-Meteo reanalysis snow depth (not measured; grid-cell value; ~21% low at Independence Pass).
**Leaning:** (1) SNWD at time *t*+30 days as the target. Open-Meteo supplies the weather features; it remains the primary weather source, as staff require. WTEQ is kept as a fallback or secondary target if the SNWD record proves too short.
**Resolved 2026-11-10:** the composite ski-condition index is kept as a SECONDARY output (see D-026). Measured SNWD on day *t*+30 is the primary target. Evaluation uses measured, non-imputed SNWD only.

## D-006 — Use as many winters as possible
**Status:** ACCEPTED · 2026-11-09 (user)
**Implication:** Each station uses its full usable SNWD record (no common start year is imposed across resorts). The train/test split is by winter, with the later winters as the test set. Climatology is computed from training winters only (staff condition).

## D-007 — Separate model per resort; 3 resorts
**Status:** ACCEPTED · 2026-11-10 (separate models: user 2026-11-09; maritime pick: user "choose the one with the best data")
**Final resorts:**
- **Aspen CO** (continental): fixed composite of Kiln + Brumley, 2004–2026, 23 winters (D-008)
- **Brighton UT** (intermountain): 366:UT:SNTL, 1998–2026, 29 winters
- **Heavenly CA** (Sierra): 518:CA:SNTL, 2000–2026, 27 good winters with no gaps; best agreement with ERA5-Land (r 0.955, bias −35 %)

**Why Heavenly for the maritime slot:** it has the best data, as the user asked. Palisades Tahoe has 24 winters (2003+, no gaps, r 0.91, −40 %). Stevens Pass has 23 (2003+, a gap in 2004, a low 3,940 ft station, and the sensor issues found in notebook 01 §2.6).
**Limitation (state it in the revised proposal):** Heavenly is on the east/lee side of Lake Tahoe, so it is drier and less "maritime" than Palisades. It is still a Sierra snow climate distinct from CO/UT.

**History of this decision:**
**Proposed resorts** (one per snow climate):
- **Aspen**, continental Colorado (see D-008)
- **Brighton UT**, intermountain (366:UT:SNTL). SNWD from 1997, a longer record than Snowbird's (~2003)
- **Palisades Tahoe CA**, maritime (784:CA:SNTL). SNWD from 1998 ← **corrected by notebook 01 §5: the first good winter is 2003 (24 good winters); the sensor exists from 1998 but early winters are too gappy.**

**Update 2026-11-10 (notebook 01 §5 evidence):**

| Station | Climate | Good SNWD winters | First | r vs ERA5-Land | bias |
|---|---|---|---|---|---|
| Brighton 366:UT | intermountain | 29 | 1998 | 0.91 | −26 % |
| Thaynes Canyon 814:UT (Park City) | intermountain | 29 | 1998 | 0.90 | −33 % |
| Heavenly Valley 518:CA | Sierra (east/rain-shadow) | 27 | 2000 | 0.955 | −35 % |
| Palisades Tahoe 784:CA | Sierra (west crest, maritime) | 24 | 2003 | 0.91 | −40 % |
| Stevens Pass 791:WA | Cascades maritime | 23 | 2003 | 0.958 | +8 % (3,940 ft, low) |

Brighton is confirmed as the intermountain choice. For the maritime slot, **the group must pick**: Palisades (the most typical maritime ski
climate, 24 winters) or Heavenly (3 more winters, best agreement with ERA5-Land, but drier and on the lee side). Stevens Pass is a
genuinely maritime alternative, but its station is low (1,200 m) and it has the sensor issues found in §2.6 (40 cases of depth < SWE, 82 extreme temperatures).

## D-008 — How to represent Aspen as one resort
**Status:** ACCEPTED · 2026-11-10 (user: "Aspen, let's do 2004-on")
**Decision:** Aspen = a **fixed composite of Kiln (556:CO) + Brumley (369:CO), winters 2004–2026 (23 winters)**.
- The composite SNWD is the mean of the two stations on days when **both** are present, and NaN otherwise. A day with one station missing never becomes a one-station "composite".
- Both-present coverage is ≥ 96.6 % of Dec–Mar days. That figure is for the 3-member set Kiln + Brumley + Ivanhoe; a 2-member set can only be higher. The exact value is computed in modelling.
- The two stations correlate r = 0.93 (Dec–Mar daily SNWD).

**Evidence:** cleaned data (notebook 02), Dec–Mar winters with ≥ 100 good days, 2004–2026:

| Station | Complete winters (of 23) | Missing | Notes |
|---|---|---|---|
| **Kiln** 556:CO | **23** | – | 9,610 ft, 22.7 km from Aspen Mtn, r 0.94 vs ERA5-Land, bias −4 % |
| **Brumley** 369:CO | **23** | – | 10,570 ft, 26.1 km, r 0.90, bias −8 % |
| Nast Lake 658:CO | 22 | 2005 | low (8,710 ft), +31 % bias, temperature r 0.67 |
| Butte 380:CO | 22 | 2005 | Crested Butte side, 34 km; temperature r 0.12 |
| Schofield Pass 737:CO | 22 | 2004 | Crested Butte/Marble side; −50 % bias (very snowy, not Aspen-typical) |
| North Lost Trail 669:CO | 21 | 2007, 2008 | noisy depth sensor (r 0.55) |
| Ivanhoe 547:CO | 19 | 2005–2008 | east of the Divide |
| Independence Pass 542:CO | 19 | 2004–06, 2010 | |

**Rationale:** only Kiln and Brumley are complete over 2004–2026. Fixed membership means the composite never changes which stations it contains. Both are at ski-terrain elevation and track ERA5-Land well with small bias.
**Rejected:**
- Ivanhoe alone, 1998+: longer record, but 4 missing winters in 2005–2008 and east of the Divide.
- Adding Nast Lake / Ivanhoe / Independence Pass to the composite: each has missing winters, so the membership would change.
- Schofield, Butte, North Lost Trail: wrong side of the range or noisy sensors.

**Original framing (2026-11-09):**
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
**Status:** ACCEPTED · 2026-11-10 (user confirmed the `Original Proposal/` exclusion)
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

## D-016 — SNOTEL flag policy
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §4)
**Decision:**
- NRCS suspect (S) values become NaN, and the suspect original is never restored.
- Edited, estimated and corrected values (E/K/C) are kept, with their flags carried per row.
- Undocumented G/T flags are kept and judged by the physical rules.

**Evidence:**
- The originals behind S are implausible (snow depth −280 to +269 in).
- E/K/C covers 804k rows; C is on about 57 % of temperature values.
- The G rows (Vail 1985, about 3000 °F) are removed by the bounds rule.
- Notebook 01b found suspect values include physically impossible ones (Ivanhoe TMIN = 2148.6 °F).

## D-017 — Spike rule
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §5)
**Decision:** residual from a centred 7-day rolling median: snow depth > 20 in becomes NaN (28 rows); SWE > 5 in becomes NaN (2 rows).
**Evidence:**
- The residual histogram has its minimum at 20–30 in.
- NRCS edits can be wrong: at Vail in 2008, raw readings of about 199 in were edited to 0 in, and this rule caught them.

## D-018 — Depth/SWE consistency
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §5)
**Decision:**
- Depth < SWE (density > 1, with SWE ≥ 1 in) sets depth to NaN (134 rows).
- Density 0.7–1 is flagged only (82 rows).
- In-season depth of 0 with SWE > 4 in becomes NaN (0 found; kept as a guard).

**Evidence:** density median is 0.28; the 99.9th percentile is 0.70.

## D-019 — Summer noise
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §5)
**Decision:** in Jul–Sep, SWE = 0 with depth > 0 sets depth to 0 (878 rows).
**Evidence:** median 3 in, max 24 in of "snow" over an empty pillow. The ultrasonic sensor is seeing vegetation.

## D-020 — Negative depth (guard)
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §5)
**Decision:** values in [−4, 0) in become 0; values below −4 in become NaN.
**Evidence:** all 59 raw negatives were already removed as suspect (D-016), so 0 rows changed. The rule is kept as a guard.

## D-021 — Temperature rules
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §5)
**Context:** SNOTEL temperatures are secondary; Open-Meteo is the primary temperature source.
**Decision:**
- A value repeated for ≥ 5 consecutive days (stuck logger) becomes NaN: about 1,320 rows per variable.
- Bounds of [−50, 100] °F.
- Residual from the 7-day rolling median > 30 °F.
- TMIN > TMAX: both become NaN.
- TAVG outside [TMIN − 1, TMAX + 1] °F.
- Daily range > 35 °C: TMAX becomes NaN (179 rows).
- TAVG − TMIN > 20 °C: TAVG becomes NaN (122 rows).

**Evidence:**
- Repeated-value run counts level off from 5 to 10+ days.
- −60.3 °F repeats as a sensor floor.
- Both range tails flatten past their 99.9th percentiles.
- The Stevens Pass heat dome (37 °C, 2021-06-29) is verified kept.

## D-022 — Imputation (causal)
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §6; replaces the first draft's two-sided linear interpolation, which looked ahead)
**Decision:**
- Forward-fill interior gaps of ≤ 3 days in SNWD, WTEQ, TAVG, TMAX and TMIN, per station, flagged `*_imputed`. Longer gaps stay entirely NaN (never partially filled), as do leading and trailing gaps.
- No precipitation imputation.
- Filled values never contain future information, so they are safe as features.
- **Imputed target rows are excluded from training labels and evaluation.**

**Evidence:**
- 88 % of snow-depth gaps are ≤ 3 days (44 % of gap-days); longer gaps (up to 79 days) are left NaN.
- Causality is unit-tested (`tests/test_clean.py`).

**Caveat:** no future *value* ever enters a filled cell. But deciding *whether* a gap qualifies ("it ends within 3 days") uses the missingness pattern after day *t*. A fully causal alternative, `ffill(limit=3)`, would also partially fill long gaps, so it was not used. The effect is negligible: it determines only which rows are filled, never what value they get.

## D-023 — Calendar and season labels
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §2)
**Decision:**
- Continuous daily calendar per station.
- Season window Nov 1 – Apr 30 (`in_season`).
- `winter` is the year the winter ends (Jul–Dec count toward the next year).
- `water_year` (Oct–Sep) is used for PREC, which resets each Oct 1 (notebook 01b).

**Evidence:** 38 absent days were inserted; otherwise the API returns explicit null rows.

## D-024 — Leakage from NRCS's after-the-fact edits
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §10)
**Context:** on a real prediction date, a forecaster would have only the raw, provisional reading.
- NRCS later edits 29 % of snow-depth and 34 % of SWE values (median change 1.0 in / 0.2 in).
- It approves values months later. Recent winters are mostly provisional (P), and there are no QA flags at all before about 2023.

**Decision:** modelling must include a robustness run whose day-*t* features use `*_nrcs_orig` (the raw readings) instead of the edited values.

## D-025 — Keep everything in the clean table
**Status:** ACCEPTED · 2026-11-10 (notebook 02 §11)
**Decision:** all 20 candidate stations and the full period stay in `data/processed/snotel_clean.parquet`. Resort and station selection (D-007/D-008) happens downstream by filtering rows.
**Evidence:** 285,778 rows × 49 columns, 4.51 MB parquet.

## D-026 — Extension: SWE ↔ depth via snow density; ski-condition index as a secondary output
**Status:** PROPOSED · 2026-11-10 (user asked whether a formula could estimate both depth and SWE, or a two-pass model could produce a quality score)
**Physics:** depth = SWE / density. Snow density varies predictably with season, snowpack age, temperature and climate. Published models:
- Sturm et al. 2010, *J. Hydrometeorology*, "Estimating snow water equivalent using snow depth data and climate classes".
- Hill et al. 2019, *The Cryosphere*, "Converting snow depth to snow water equivalent using climatological variables".

Our own data: density median 0.28, 99.9th percentile 0.70 (notebook 02).
**Proposal:**
1. Fit a per-station density model (e.g. density ~ day-of-season + recent temperature + SWE) on **training winters only**, using days where both SNWD and WTEQ were measured (not imputed).
2. (a) **Reconstruct depth from SWE back to ~1980**, for training augmentation only. Reconstructed depth is **never evaluation truth**.
3. (b) **Two-stage model:** predict SWE at *t*+30 (longer, cleaner record), convert it with the density model, and compare against direct depth prediction on the same held-out winters.
4. **Quality score:** the original proposal's transparent ski-condition index, computed from predicted depth plus Open-Meteo weather (sunshine, temperature, wind). It is a **secondary** output, reported with sensitivity to the weights, as the proposal promised.

**Guardrails:** the density model and any index weights are fit on training winters only. Evaluation uses measured, non-imputed SNWD.

## Group (recorded 2026-11-10)
- Canvas project group **37**. Members: **Nat Toms, Owen Cruz-Abrams, Martha le Huray**.
- GitHub: MrDevel0per (repo owner), mlehuray246, nxt-txms (collaborators).
- The original proposal (Milestone 0) lists Tomer Burstein as author.

## D-027 — Open-Meteo feature set: 10 ERA5 + 4 ERA5-Land daily variables
**Status:** ACCEPTED · 2026-11-10
**Context:** Open-Meteo's fair-use accounting charges about (variables ÷ 10) × (days ÷ 14) calls per request. Limits are about 5,000 per hour and 10,000 per day per client. With 14 ERA5 variables, the 4 resort stations × 1997–2026 would cost about 7,300 calls. Notebook 01 had already used about 5,000 that UTC day, so the fetch would have spilled into the next day.
**Decision:**
- **ERA5 (10):** temperature max/min/mean, precipitation_sum, snowfall_sum, sunshine_duration, wind_speed_10m_max, cloud_cover_mean, relative_humidity_2m_mean, pressure_msl_mean.
- **ERA5-Land (4):** temperature mean/max/min, snow_depth_mean (used as a *feature* only).
- **Window:** 1997-07-01 → 2026-06-30, at each station's lat/lon/elevation, `timezone=auto`, in 5-year chunks. Total cost ≈ 6,000 calls.
**Dropped, as redundant or derivable:**
- `daylight_duration`: deterministic from date and latitude; we compute it ourselves if needed.
- `rain_sum`: ≈ precipitation − snowfall water equivalent.
- `wind_gusts_10m_max`: ≈ max wind speed.
- `shortwave_radiation_sum`: ≈ sunshine + cloud cover.
**Not done:** spreading downloads across group members' machines or IPs to get around per-client limits. That would circumvent the provider's fair-use limits, so we wait for the limits to reset instead. Defined in `src/features.py`.

## D-028 — Disconnect- and crash-safe data collection
**Status:** ACCEPTED · 2026-11-10 (user: "make it robust to disconnects")
- **Atomic, crash-safe writes.** `lineage.store_and_log` writes `<file>.part`, fsyncs it, appends and fsyncs the manifest row, then renames atomically. A crash never leaves a partial file that looks cached. A re-run re-fetches, and the newer manifest row supersedes the old one (`verify_raw` checks the latest row per URL).
- **Network errors retried.** `lineage.get_with_retry` retries ConnectionError, Timeout and ChunkedEncodingError with back-off (10 s → 5 min). A minutely 429 is retried after 65 s. Hourly and daily 429s return immediately to the caller.
- **Unattended prefetch.** `scripts/prefetch_features.py` is idempotent. It sleeps to the next hour or to 00:05 UTC on hourly/daily limits, waits 2 min on network loss and retries indefinitely, removes stale `.part` files, and writes UTC-timestamped progress to `data/prefetch_features.log`.
- **Detached run.** It runs under `nohup` and `caffeinate -i`, so it survives the editor or Claude session closing and macOS idle sleep. Closing the lid still pauses it; it resumes on wake.
- **Tested:** `tests/test_robustness.py` covers Wi-Fi drop then recovery, a persistent outage, the hourly limit, a crash before the rename, and re-running after a crash.

## D-029 — Modelling-table rows: target date in Nov 1 – Apr 30; labels are measured targets only
**Status:** PROPOSED · 2026-11-10 (notebook 03 §5)
**Context:** the revised question asks for depth on day *t* + 30 during the season, so the season could constrain either the issue date or the target date.
**Options:** (a) issue date in Nov–Apr, so targets run to May 30; (b) **target date in Nov–Apr**, so issue dates run Oct 2 – Mar 31.
**Decision:** (b). It matches the question's "depth on day *t* + 30 (Nov–Apr)", and the issue and target date always fall in the same winter (asserted in `modeltable.model_table`).
- A row is a **label** only if the target is measured: present, not imputed, and every composite member present (`y_measured`).
- The single look-ahead in the project is `modeltable.labels()`.
**Evidence:** 14,319 rows × 61 columns; 14,231 measured labels; 13,862 complete-case rows (§5 funnel).

## D-030 — No cleaning of Open-Meteo values; snowfall and precipitation are not mutually consistent
**Status:** PROPOSED · 2026-11-10 (notebook 03 §2)
**Decision:** no imputation, outlier removal or capping for Open-Meteo inputs.
**Evidence:**
- Complete calendars at all 4 stations: 10,592 days, 0 NaN, no duplicate days at chunk seams.
- Zero violations of the temperature-ordering, non-negativity, RH/cloud bounds, pressure, and sunshine ≤ astronomical day-length checks.
- The largest precipitation days are documented storms, e.g. Heavenly 2017-01-08, 2021-10-24 and 2022-12-31 atmospheric rivers.

**Finding that revises D-027:** `snowfall_sum` (cm) exceeds 0.7 × `precipitation_sum` (mm) on 9–24 % of wet days, depending on station and precipitation band, with ratios up to 2.45. On 127–321 days per station there is snowfall with 0 precipitation (tiny amounts; minimum 0.07 cm = 0.1 mm × 0.7). The two variables are derived separately. **Never derive rain as precipitation − snowfall/0.7.** D-027's remark that `rain_sum` is approximately derivable is therefore withdrawn. The variable was dropped anyway.

## D-031 — Feature set (causal), Aspen weather, temperature source
**Status:** PROPOSED · 2026-11-10 (notebook 03 §4; `src/modeltable.py::build_features`)
**Decision:**
- **54 feature columns**, every one computed from rows dated ≤ *t*:
  - calendar (4);
  - SNOTEL snow state: depth/SWE at *t*, 7/30-day changes, season peak, station precipitation sums (11);
  - ERA5 day-*t* values (7) and trailing 7/30-day sums/means (22);
  - season-to-date snowfall, precipitation and positive degree-days (3);
  - ERA5-Land snow depth and its changes, plus 7-day ERA5-Land temperature (4);
  - `rob_*` robustness columns (3; D-024; excluded from the main feature set).
- Trailing windows are **strict**: one missing day makes the feature NaN.
- **Temperatures come from Open-Meteo only.** SNOTEL temperatures carry sensor drift (Aspen SNOTEL − ERA5 shifts about −1 °C from ~2013, notebook 03 §2.5), and their stuck-sensor rule looks ahead.
- **Aspen weather** = mean of the Kiln and Brumley requests, each at its own lat/lon/elevation. They are in **different** ERA5 and ERA5-Land cells.

**Evidence:** causality is proved by truncation and future-perturbation tests (`tests/test_modeltable.py`) and re-checked on real data for 40 dates per resort, with max |Δ| = 0 (notebook 03 §4.2). This holds **given the cleaned inputs**; upstream look-ahead is quantified in §4.3.

## D-032 — Split by winter, common calendar for all resorts
**Status:** PROPOSED · 2026-11-10 (notebook 03 §6)
**Decision:** **train ≤ 2016, validation 2017–2020, test 2021–2026.** The test set is touched once, after every choice is frozen. Final models are refit on train + validation.
**Why:**
- Staff condition 3 (test on later winters).
- A common calendar keeps comparisons between resorts fair.
- Six test winters (1,087 rows per resort, 21–26 % of rows) span the extremes: 2023 is deepest on record at Heavenly and 2nd at Brighton; 2026 is the **shallowest on record** at Aspen and Brighton.
- A summer separates every winter, so no 30-day target window crosses a split.

**Stated caveat:** distribution shift. Test-winter mean depth is lower than training at Aspen (63 vs 70 cm) and Brighton (91 vs 100), equal at Heavenly, and more variable everywhere.

## D-033 — Cross-validation folds are whole winters
**Status:** PROPOSED · 2026-11-10 (notebook 03 §6.1)
**Decision:** hyper-parameter tuning uses folds grouped by winter, or expanding-window folds. Days are never shuffled.
**Evidence:** on train + validation winters only, the same ridge model's MAE looks 15–24 % smaller with shuffled 5-fold CV than with winter-grouped 5-fold CV. Neighbouring rows are near-duplicates.

## D-034 — Hindcast caveat: reanalysis latency
**Status:** PROPOSED · 2026-11-10 (notebook 03 §4.3)
**Context:** ERA5 is published about 5 days behind real time. Day-*t* reanalysis stands in for what a real-time analysis would know.
**Decision:** state this as a hindcast assumption. Milestone 3 adds a sensitivity run with every weather feature lagged 5 days.

## D-035 — Baseline definitions; how models must handle collinearity
**Status:** PROPOSED · 2026-11-10 (notebook 03 §7–8; `modeltable.climatology`)
**Decision:**
- **Climatology** = mean measured SNWD at the target's day of the water year, pooled ±7 days, across training winters only. It is fitted on train for validation scoring and on train + validation for test scoring. A median variant is reported alongside.
- **Persistence** = `snwd_t`.
- **Persistence + climatological change** = `snwd_t + clim(target day) − clim(t)`, clipped ≥ 0. This is the strongest simple reference.
- All baselines are scored on the same rows: measured target and known `snwd_t`.

**Evidence (test MAE, cm):**

| Resort | Persistence + clim. change | Climatology | Persistence |
|---|---|---|---|
| Aspen | 11.3 | 14.0 | 22.4 |
| Brighton | 23.3 | 36.5 | 34.0 |
| Heavenly | 31.5 | 51.0 | 41.8 |

- The pooling half-width barely matters: under 0.3 cm of validation MAE between ±0 and ±15 days.
- A leaky climatology that includes the test winters would flatter itself by only 1–5 %; variability between winters dominates.

**Collinearity:** 31 feature pairs have |ρ| > 0.95. `target_dowy` = `dowy` + 30 is used only to look up climatology. Milestone 3 uses ridge/lasso and/or one representative per correlated group; random forests are unaffected.

## D-036 — Open-Meteo grid-cell selection
**Status:** PROPOSED · 2026-11-10 (notebook 03 §2.1)
**Finding:** we did not pass `cell_selection`, so Open-Meteo's default `land` applied. That default picks a nearby land cell with terrain elevation close to the requested `elevation=`, not necessarily the nearest cell. The returned cells are 1.5–13 km from the stations and identical across all chunks. The returned elevation equals the one we sent.
**Decision:** accept and record the cells (notebook 03 §2.1 table). Any future request passes `cell_selection=land` explicitly. Existing requests are not re-issued, because that would cost about 6,000 calls and change nothing.

## D-037 — Causal QC for NRCS original readings (D-024 robustness inputs)
**Status:** SUPERSEDED by D-042 (code removed; the Milestone 3 robustness run follows D-038) · 2026-11-10 (notebook 03 §9; `modeltable.causal_spike_filter`)
**Context:** raw NRCS readings contain frequent, often multi-day, sensor glitches (e.g. Brighton 208 in on a 10 in day, 2023-11-23). Kiln has 447 such days since 1998. Notebook 02's spike rule uses a centred window, so it cannot be used for a real-time input.
**Options:**
1. Bounds only: glitches pass through.
2. A plain trailing-median rule: wrongly rejects real readings after a multi-day glitch.
3. **A recursive rule: compare with the median of the last 7 *accepted* readings, re-anchoring after 30 days with nothing accepted.**

**Decision:** option 3, with a 40 in threshold, plus bounds [−4, 400] in and D-020's negative-depth rule.
**Evidence** (calibrated on **training winters 1998–2016 only**, per the audit below):
- At 40 in: Kiln has 137 rejections, Brighton 293, with none wrong and none missed at either. Heavenly has 3 wrong and 31 missed.
  At 30 in Heavenly would have 104 wrong rejections (real storm days); at 20 in, 364.
- Brumley has 30 wrong rejections at every threshold: the reference itself was a glitch, at the record start or after a re-anchor.
- Causality and multi-day glitches (4, 10 and 25 days) are unit-tested.

**Revision (same day, after an independent audit).** The first version used readings accepted *within* the previous 7 days, so it adopted glitches lasting 7 days or more and then rejected the true readings that followed. It was also calibrated on all winters, test winters included. Both are fixed.

## Independent audit of notebook 03 (2026-11-10)
A separate reviewer audited `src/modeltable.py`, its tests and notebook 03 for leakage. It found **no leak** in the features, labels, split or baselines that affects any result; all scores are unchanged. The fixes it prompted:
1. `labels()` now sets `y` to NaN unless the target is measured. Previously, 39 imputed Aspen training targets were kept in `y`, guarded only by the `y_measured` flag.
2. The §6.1 autocorrelation now uses train + validation winters only, with pairs inside the same winter and the lag in days. The earlier version included the test winters and paired days across winters.
3. The wording of the leakage claims now says "given the cleaned inputs". Upstream look-ahead (NRCS edits and S-flags; which ≤3-day gaps get filled) is quantified in §4.3.
4. The spike filter for the D-037 robustness inputs was fixed and re-calibrated on training winters only.
5. Several captions were tightened:
   - "training winters" for the final test fit means train + validation;
   - test winters appear in §2, §3 and §6 only for input QC and description;
   - "measured" means "an NRCS value we did not impute" (which includes NRCS E and K values).
6. More tests: splits don't overlap, the winter filter works, climatology ignores poisoned `snwd_measured` flags, and multi-day glitches are rejected.

## Open questions for the group
- None blocking as of 2026-11-10. D-002 and D-004 are still marked PROPOSED pending explicit group sign-off. D-026 is a proposed extension.
- D-029 to D-037 (notebook 03) need group review. The most consequential are the split (D-032) and the baseline definitions (D-035).

## D-038 — Audit proposal: causal model-input preprocessing and complete robustness coverage
**Status:** PROPOSED · 2026-11-09 ET
**Context:** Audit A-02 reproduces a prefix-invariance failure in D-022: whether a gap is filled depends on future missingness.
Audit A-03 finds that replacing the three `rob_*` columns leaves revised depth peaks, SWE and station precipitation features in the robustness model.
**Options:** (a) retain the retrospective cleaned inputs and restrict claims to that setting; (b) rebuild inputs using elapsed-gap-limited causal filling and originals for every retained SNOTEL feature; (c) use no input imputation and a reduced originals feature set.
**Proposed choice:** (b), with (c) as the simpler fallback. Preserve the non-imputed target mask; test future missingness as well as future values.
**Why/evidence:** a feature's presence is information too. The full and truncated `[5, NaN, NaN, 7]` example differs before the fourth day.
The originals experiment must replace or omit every revised-input path, not just current depth and two changes. See CODE_AUDIT A-02/A-03 and DATA_SOURCES §8.
**Effect:** would supersede D-022's gap-selection policy for model inputs if accepted. D-022 and existing numerical outputs are unchanged by this audit.

## D-039 — Audit proposal: disclose test access and freeze an evaluation protocol
**Status:** PROPOSED · 2026-11-09 ET
**Context:** notebook 03 already plots, ranks and scores winters 2021–2026 while D-032 calls them touched once after choices are frozen.
**Options:** (a) continue calling this an untouched test set; (b) keep the fixed calendar, disclose exploratory access and freeze future choices using development winters only; (c) collect future independent outcomes.
**Proposed choice:** (b); (c) can be an optional future confirmation. Do not change year boundaries to pursue a better score.
**Why/evidence:** proper baseline fitting excludes test years, but that does not undo prior inspection. Use exact common resort/date keys for model–baseline comparisons and report coverage.
**Effect:** corrects the untouched-test claim in D-032 without changing its implemented split. See CODE_AUDIT A-01/A-04.

## D-040 — Audit proposal: omit station precipitation windows from initial model predictors
**Status:** PROPOSED · 2026-11-09 ET
**Context:** `prcp_sum_7` and `prcp_sum_30` make every Aspen winter-2021 row incomplete; Open-Meteo precipitation windows are already available.
**Options:** (a) drop incomplete rows; (b) add a fitted imputer; (c) omit the two redundant predictors, preserving their provenance columns.
**Proposed choice:** (c). Keep baseline and model scores on identical eligible dates.
**Why/evidence:** coverage alone motivates this simplification: Aspen complete rows rise from 3,747 to 3,977 across all splits, restoring all 181 winter-2021 rows and 49 validation rows. No test-error comparison was used to recommend it.
**Effect:** proposed reduction of D-031's model feature list, not a change to the saved table. See CODE_AUDIT A-04 and DATA_SOURCES §8.

## D-041 — Audit proposal: defer density reconstruction and keep the primary experiment compact
**Status:** PROPOSED · 2026-11-09 ET
**Context:** the Milestone 2 submission is unfinished; the primary measured-depth question can be answered with the existing records.
**Options:** (a) add SWE→density reconstruction and a two-stage model now; (b) defer them and prioritize the required artifacts, ridge/random forest, baselines and availability checks.
**Proposed choice:** (b). Retain any condition index as a clearly qualified secondary illustration, with no realized future-weather inputs.
**Why/evidence:** D-026 adds another fitted model and synthetic training targets; audit A-01 to A-05 identify higher-value work. The staff conditions require seasonal averages and time-based evaluation, not density reconstruction.
**Effect:** a scope recommendation for the proposed D-026 extension; no group decision is marked ACCEPTED here.

## D-042 — One submission notebook; simpler code; deferred robustness inputs; validation-only baselines
**Status:** ACCEPTED · 2026-11-10 (Owen: "LGTM"; asked for simplicity and readability as absolute priorities)
**Context:** the Milestone 2 spec asks for one notebook that gets, understands and cleans the data, then states the question. We had four
(01, 01b, 02, 03; ~200 cells), much of it exploration whose findings are already recorded here and in DATA_SOURCES.md. Audit A-05 asked for one
ordered submission notebook; A-01 for no further test-winter scoring; A-03 found the `rob_*` robustness inputs incomplete.
**Options:** (a) submit all four; (b) concatenate them; (c) one new notebook with only what the spec asks for, citing docs for the rest.
**Decision:** (c), `notebooks/snowpredict.ipynb` (70 cells, runs offline in ~10 s). Alongside it:
- Kept: the source checks behind key decisions (`best_match` break, `elevation=` effect, snow-depth coverage), every SNOTEL cleaning rule (D-016 to D-023, unchanged), the Open-Meteo checks, missingness, target distribution, scale, leakage, the modelling table, the split, and an explicit revised-question cell.
- Dropped from the notebook (evidence stays at commit `eca1c57` and in DATA_SOURCES.md): model-by-model probes, other-API probes, the ERA5-Land validation and lag tables, the 01b parser/aggregation cross-checks, the Open-Meteo grid-cell, homogeneity and agreement tables, feature-correlation EDA, and the originals calibration. The random-split demonstration was kept (§4.4, Owen): a random split flatters the same ridge model by 15–24 %.
- Baselines are scored on **validation winters only** (fitted on train); the test winters are no longer scored or plotted (D-039).
- The `rob_*` columns and `modeltable.causal_spike_filter` are removed. D-024's robustness run is still required in Milestone 3 and must rebuild *every* SNOTEL feature from originals (D-038), so the three partial columns were not reusable (D-037 is not adopted for now).
- Code: `src/lineage_text.py` (only used by 01b) and the one-time manifest migration were removed; `src/features.py` became `src/sources.py`, the single definition of every production request (the SNOTEL request had been copied in three notebooks); the feature data dictionary moved next to `build_features` (`modeltable.FEATURE_DOCS`, with a test that every feature is documented).
**Evidence of no numerical change:** `snotel_clean.parquet` is byte-identical; `model_table.parquet` is identical except for the 3 dropped `rob_*` columns (14,319 × 58); all 40 cleaning-log counts are identical; the validation baseline scores equal the old notebook's. 59 tests pass.

