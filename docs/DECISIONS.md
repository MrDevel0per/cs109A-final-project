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

## Open questions for the group
- None blocking as of 2026-11-10. D-002 and D-004 are still marked PROPOSED pending explicit group sign-off. D-026 is a proposed extension.
