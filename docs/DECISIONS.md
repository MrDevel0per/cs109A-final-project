# Decision log

Every entry is a decision the group made. Each has an ID, date, context, options, decision, rationale and evidence.
Proposals that were never adopted are not listed. The few items still open for Milestone 3 are at the end.

---

## D-001 — Weather source: Open-Meteo Historical Weather API
**Date:** 2026-11-09 (required by staff)
**Context:** Staff comments say the proposal named Open-Meteo but linked to Meteostat.
**Decision:** Open-Meteo is the primary weather source. Correct link: https://open-meteo.com/en/docs/historical-weather-api
**Rationale:** Staff requirement. Free, global, no key, 1940 to present.

## D-002 — Pin Open-Meteo models; never use `best_match`
**Date:** 2026-11-09
**Context:** `best_match` changes its underlying model in 2017 (ERA5-Land → ECMWF IFS). That produces up to ~8°C jumps on the same date (DATA_SOURCES §1.3). Our test set is the later winters, so a source change would land exactly on the train/test boundary.
**Options:** (a) `best_match` · (b) `era5_seamless` · (c) `era5` for atmosphere + `era5_land` for temperature and snow depth · (d) `cerra` (Europe only, ends June 2021)
**Decision:** (c): ERA5 (0.25°) for snowfall, sunshine, wind and cloud; ERA5-Land (0.1°) for temperature and snow depth. All model features use these two pinned models. (`era5_seamless` appears only in the one-day `elevation=` probe in notebook §1.3.)
**Rationale:** Consistent reanalysis across the whole period, so no source break. CERRA is rejected because it ends in 2021, which leaves no recent test winters, and it is Europe only.

## D-003 — Where to collect data: US West, anchored on Aspen, instead of the three European resorts
**Date:** 2026-11-09 (Owen: go US West, Aspen as anchor, Aspen treated as ONE resort; which other resorts is decided in D-007)
**Context:** The proposal used St. Anton, Grandvalira and Val di Fassa. Open-Meteo's snow depth is a grid-cell value and does not follow the slopes' elevation (DATA_SOURCES §1.4). Without ground-truth snow observations we can't tell whether reanalysis snow resembles what skiers experience. The milestone grades our reasoning about data quality.
**Options:**
1. Keep the three European resorts. Open-Meteo only. CERRA gives better resolution but ends in 2021. No easy ground truth.
2. Switch to US western resorts. Open-Meteo is still the primary source, and SNOTEL on-mountain stations add measured snow depth, SWE and temperature (~20 winters of depth; 40+ of SWE and temperature).
3. Hybrid: US resorts as the core plus St. Anton as a single unvalidated comparison.

**Decision:** Option 2, with Aspen as the anchor. A group member is from Aspen, which gives us local knowledge and a motivating story. The Aspen area has 5+ SNOTEL stations with 40+ winters. Contrast resorts were drawn from different snow climates; candidates considered:
  - Continental CO: Aspen area (Independence Pass, Kiln, Brumley, Ivanhoe, Nast Lake), plus Vail Mountain or Copper Mountain
  - Intermountain UT: Snowbird or Brighton
  - Maritime: Palisades Tahoe (CA) and/or Stevens Pass (WA)
  - Northern Rockies: Lone Mountain / Big Sky (MT)

The final three are in D-007.
**Rationale:**
- SNOTEL is free, has a REST API and needs no key. Several stations sit on the resorts themselves at ski-terrain elevation.
- Lets us **validate** Open-Meteo against measurements. The first check gave r = 0.94 for snow depth with a 21% low bias (DATA_SOURCES §2.2), a concrete data-quality finding for the presentation.
- Different snow climates let us answer the proposal's secondary question: does accuracy differ by resort?

**Cost:** The revised proposal must explain the change of region. The staff conditions (Open-Meteo; climatology from training years; test on later winters) are all unaffected.

## D-004 — No real 30-day forecast benchmark; baselines are climatology and persistence
**Date:** 2026-11-09
**Context:** The Open-Meteo seasonal API (ECMWF SEAS5) only covers 2025-09 onward, with no hindcasts. The historical-forecast and previous-runs APIs cover only short lead times.
**Decision:** The baselines are (1) day-of-season climatology computed from training seasons only (staff requirement), and (2) persistence (today's value carried forward 30 days). Optionally, log SEAS5 forecasts for the current 2026-27 season as a live, out-of-sample bonus.

## D-005 — Target: SNOTEL measured snow depth (SNWD) as ground truth
**Date:** 2026-11-10 (Owen: measured SNWD is the primary target)
**Context:** The original proposal predicted several weather variables and combined them into a composite ski-condition index. With SNOTEL available, we can predict a *measured* quantity instead of a reanalysis estimate.
**Options:**
1. **SNWD** (snow depth, inches). This is what skiers feel. Record starts around 1997–98 at the best stations, giving up to ~28 winters; at many stations it starts around 2004–07.
2. **WTEQ** (snow water equivalent). Records start 1979+ (up to ~46 winters) and come from a pillow sensor, so they are typically cleaner. It is less directly "skiable".
3. Open-Meteo reanalysis snow depth (not measured; grid-cell value; ~21% low at Independence Pass).

**Decision:** (1): measured SNWD on day *t*+30 is the primary target. Open-Meteo supplies the weather features; it remains the primary weather source, as staff require. The composite ski-condition index is kept as a SECONDARY output (D-026). Evaluation uses measured, non-imputed SNWD only.

## D-006 — Use as many winters as possible
**Date:** 2026-11-09 (Owen)
**Implication:** Each station uses its full usable SNWD record (no common start year is imposed across resorts). The train/test split is by winter, with the later winters as the test set. Climatology is computed from training winters only (staff condition).

## D-007 — Separate model per resort; 3 resorts
**Date:** 2026-11-10 (separate models: Owen 2026-11-09; maritime pick: Owen, "choose the one with the best data")
**Final resorts:**
- **Aspen CO** (continental): fixed composite of Kiln + Brumley, 2004–2026, 23 winters (D-008)
- **Brighton UT** (intermountain): 366:UT:SNTL, 1998–2026, 29 winters
- **Heavenly CA** (Sierra): 518:CA:SNTL, 2000–2026, 27 good winters with no gaps; best agreement with ERA5-Land (r 0.955, bias −35 %)

**Why Heavenly for the third slot:** it has the best data, as Owen asked. Palisades Tahoe has 24 winters (2003+, no gaps, r 0.91, −40 %). Stevens Pass has 23 (2003+, a gap in 2004, a low 3,940 ft station, and the sensor issues found in the exploratory notebook 01 §2.6).
**Limitation (state it in the revised proposal):** Heavenly is on the east/lee side of Lake Tahoe, so it is drier and less "maritime" than Palisades. It is still a Sierra snow climate distinct from CO/UT.

**Evidence** (exploratory notebook 01 §5, commit `eca1c57`):

| Station | Climate | Good SNWD winters | First | r vs ERA5-Land | bias |
|---|---|---|---|---|---|
| Brighton 366:UT | intermountain | 29 | 1998 | 0.91 | −26 % |
| Thaynes Canyon 814:UT (Park City) | intermountain | 29 | 1998 | 0.90 | −33 % |
| Heavenly Valley 518:CA | Sierra (east/rain-shadow) | 27 | 2000 | 0.955 | −35 % |
| Palisades Tahoe 784:CA | Sierra (west crest, maritime) | 24 | 2003 | 0.91 | −40 % |
| Stevens Pass 791:WA | Cascades maritime | 23 | 2003 | 0.958 | +8 % (3,940 ft, low) |

**History:** the first plan was Aspen, Brighton (SNWD from 1997, longer than Snowbird's ~2003) and Palisades Tahoe (784:CA). Notebook 01 §5 showed Palisades' first good winter is 2003, not 1998 (early winters too gappy), so the maritime slot was put to the group: Palisades (most typical maritime climate), Heavenly (3 more winters, best agreement with ERA5-Land, but drier), or Stevens Pass (genuinely maritime, but a low station with sensor issues: 40 cases of depth < SWE, 82 extreme temperatures). Owen chose the best data: Heavenly.

## D-008 — How to represent Aspen as one resort
**Date:** 2026-11-10 (Owen: "Aspen, let's do 2004-on")
**Decision:** Aspen = a **fixed composite of Kiln (556:CO) + Brumley (369:CO), winters 2004–2026 (23 winters)**.
- The composite SNWD is the mean of the two stations on days when **both** are present, and NaN otherwise. A day with one station missing never becomes a one-station "composite".
- The number of in-season days with both stations present is printed in notebook §4.1.
- The two stations correlate r = 0.93 (Dec–Mar daily SNWD).

**Evidence:** cleaned data, Dec–Mar winters with ≥ 100 good days, 2004–2026:

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
- Adding Nast Lake / Ivanhoe / Independence Pass to the composite: each has missing winters, so the membership would change and create artificial jumps.
- Schofield, Butte, North Lost Trail: wrong side of the range or noisy sensors.

**Limitation:** no SNOTEL station sits on an Aspen ski area; the composite is 23–26 km from Aspen Mountain.

## D-009 — SNOTEL fetch parameters: get everything, filter ourselves
**Date:** 2026-11-09
**Decision:** Every SNOTEL `/data` request uses `returnFlags=true`, `returnOriginalValues=true`, `returnSuspectData=true`, with `periodRef=END` stated explicitly.
**Rationale:**
- The API default `returnSuspectData=false` silently drops suspect values. That is a hidden filter we would not otherwise know about.
- Original values reveal sensor spikes. Ivanhoe (547:CO), 2010-01-02: original 204 in (`origQcFlag` S), edited to 31 in (`qcFlag` E).
- The flags only add information; nothing is removed at fetch time. All filtering happens in documented cleaning steps.

**Evidence:** Ivanhoe SNWD 1998–2026 (qcFlag, qaFlag) tally: (V,–) 6426, (E,–) 2598, (V,A) 422, (E,A) 253, (V,P) 185, (K,A) 56, (E,P) 56, (K,P) 33. About ⅓ of values are edited or estimated (E/K).

## D-010 — Do not use NRCS-provided normals
**Date:** 2026-11-09
**Decision:** Never request or use `centralTendencyType` (NRCS 30-year averages/medians).
**Rationale:** Those normals span years that include our test winters. Using them would leak test information and violate staff condition 4 (climatology from training years only).

## D-011 — Data lineage
**Date:** 2026-11-09
**Decision:** All external data enters through `src/lineage.py::fetch()`.
- Raw response bytes are stored unmodified in `data/raw/<source>/<name>__<hash>.json`.
- Each fetch appends a row to `data/raw/MANIFEST.csv`: UTC time, canonical URL, file, bytes, sha256, HTTP status.
- Re-runs read the cache instead of re-downloading.
- Transient errors (429/5xx) are logged but not cached. Deterministic errors (e.g. 400) are cached as evidence.
- Site and station definitions live in `src/sites.py`; production requests are defined once in `src/sources.py`.

## D-012 — Environment
**Date:** 2026-11-09
**Decision:** A uv project (`pyproject.toml` + `uv.lock`) with Python 3.12, matching the course homework workflow. Run with `uv sync`, then `uv run jupyter lab`.

## D-013 — Public GitHub repo
**Date:** 2026-11-10
**Decision:** Public repo `MrDevel0per/cs109A-final-project`, with collaborators mlehuray246 and nxt-txms.
**Exclusion:** `Original Proposal/` (course spec, staff comments, and a PDF containing the author's email) is excluded from the public repo. It is easy to add later if the group agrees.

---

## D-014 — Honest, identifiable User-Agent on every request
**Date:** 2026-11-10 (course requirement, per Owen)
**Decision:** `src/lineage.py` sends
`SnowPredict/0.2 (automated data collection for a Harvard CS1090A student final project; non-commercial; contact: https://github.com/MrDevel0per/cs109A-final-project) python-requests/<ver>`.
It says who we are, that we are automated, why, and how to reach us. The contact is the public repo; no personal email goes in headers.
**Lineage:** MANIFEST.csv has a `user_agent` column. The 62 requests made before this change (2026-11-10 00:2x UTC) used `snowpredict-course-project/0.1 (DataSci1 final project)`. The migration back-fills exactly that string; it doesn't guess. We kept that data rather than re-fetching it (Owen: "if you already queried it that's fine").
The ad-hoc exploratory `curl` probes in session 1 (pre-repo, results only in DATA_SOURCES.md) used curl's default `curl/<ver>` UA. All of them were reproduced through `lineage.fetch` in notebook 01.

## D-015 — Commit raw data to git
**Date:** 2026-11-10
**Context:** `data/raw/` is ~145 MB (SNOTEL ~142 MB, 20 files ≤ 9 MB each; Open-Meteo ~3.5 MB). This is under GitHub's 100 MB per-file limit, and the JSON compresses ~15× (8.8 MB → 0.58 MB gzip).
**Options:** (a) plain git · (b) Git LFS · (c) Google Drive / external storage plus a download script · (d) don't store, re-fetch from the APIs.
**Decision:** (a) Commit `data/raw/` and MANIFEST.csv to plain git.
**Rationale:** Durability. The exact bytes we analyzed are preserved even if NRCS revises edits (it does: QA flags move from P to A) or Open-Meteo reprocesses data. Collaborators can run the notebook offline with no API quota. sha256 values in the manifest let anyone verify the files.
**Why not the others:** (b) LFS's free tier caps storage and bandwidth at 1 GB, and each collaborator clone counts against it; it's only needed for files over 100 MB, and ours are ≤ 9 MB. (c) Drive separates data from the code and commit history, so lineage depends on a link staying alive. (d) Upstream data changes over time, so a re-fetch would not reproduce our results.
**Revisit if:** a single file gets close to 50 MB (GitHub's warning size), or the total passes ~500 MB.

## D-016 — SNOTEL flag policy
**Date:** 2026-11-10 (notebook §3.3)
**Decision:**
- NRCS suspect (S) values become NaN, and the suspect original is never restored.
- Edited, estimated and corrected values (E/K/C) are kept, with their flags carried per row.
- Undocumented G/T flags are kept and judged by the physical rules.

**Evidence:**
- The originals behind S are implausible (snow depth −280 to +269 in).
- E/K/C covers 804k rows; C is on about 57 % of temperature values.
- The G rows (Vail 1985, about 3000 °F) are removed by the bounds rule.
- Suspect values include physically impossible ones (Ivanhoe TMIN = 2148.6 °F).

## D-017 — Spike rule
**Date:** 2026-11-10 (notebook §3.4b)
**Decision:** residual from a centred 7-day rolling median: snow depth > 20 in becomes NaN (28 rows); SWE > 5 in becomes NaN (2 rows).
**Evidence:**
- The residual histogram has its minimum at 20–30 in.
- NRCS edits can be wrong: at Vail in 2008, raw readings of about 199 in were edited to 0 in, and this rule caught them.

**Caveat:** the window is centred, so whether day *t*'s reading is removed depends on days *t*+1 to *t*+3. This is a small look-ahead in the cleaned *inputs* (28 depth rows across all 20 stations), of the same kind as D-022's gap rule. It never changes a value, only whether one is NaN.

## D-018 — Depth/SWE consistency
**Date:** 2026-11-10 (notebook §3.4c)
**Decision:**
- Depth < SWE (density > 1, with SWE ≥ 1 in) sets depth to NaN (134 rows).
- Density 0.7–1 is flagged only (82 rows).
- In-season depth of 0 with SWE > 4 in becomes NaN (0 found; kept as a guard).

**Evidence:** density median is 0.28; the 99.9th percentile is 0.70.

## D-019 — Summer noise
**Date:** 2026-11-10 (notebook §3.4d)
**Decision:** in Jul–Sep, SWE = 0 with depth > 0 sets depth to 0 (878 rows).
**Evidence:** median 3 in, max 24 in of "snow" over an empty pillow. The ultrasonic sensor is seeing vegetation.

## D-020 — Negative depth (guard)
**Date:** 2026-11-10 (notebook §3.4a)
**Decision:** values in [−4, 0) in become 0; values below −4 in become NaN.
**Evidence:** all 59 raw negatives were already removed as suspect (D-016), so 0 rows changed. The rule is kept as a guard.

## D-021 — Temperature rules
**Date:** 2026-11-10 (notebook §3.4e)
**Context:** SNOTEL temperatures are secondary; Open-Meteo is the only temperature source for model features (D-031).
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
**Date:** 2026-11-10 (notebook §3.5; replaces the first draft's two-sided linear interpolation, which looked ahead)
**Decision:**
- Forward-fill interior gaps of ≤ 3 days in SNWD, WTEQ, TAVG, TMAX and TMIN, per station, flagged `*_imputed`. Longer gaps stay entirely NaN (never partially filled), as do leading and trailing gaps.
- No precipitation imputation.
- Filled values never contain future information, so they are safe as features.
- **Imputed target rows are excluded from training labels and evaluation.**

**Evidence:**
- 88 % of snow-depth gaps are ≤ 3 days (44 % of gap-days); longer gaps (up to 79 days) are left NaN.
- Causality is unit-tested (`tests/test_clean.py`).

**Caveat:** no future *value* ever enters a filled cell. But deciding *whether* a gap qualifies ("it ends within 3 days") uses the missingness pattern after day *t* (CODE_AUDIT A-02). A fully causal alternative, `ffill(limit=3)`, would also partially fill long gaps, so it was not used. The effect is small: it determines only which rows are filled, never what value they get. Replacing it with a fully causal rule is an open item for Milestone 3 (end of this file).

## D-023 — Calendar and season labels
**Date:** 2026-11-10 (notebook §3.1)
**Decision:**
- Continuous daily calendar per station.
- Season window Nov 1 – Apr 30 (`in_season`).
- `winter` is the year the winter ends (Jul–Dec count toward the next year).
- `water_year` (Oct–Sep) is used for PREC, which resets each Oct 1.

**Evidence:** 38 absent days were inserted; otherwise the API returns explicit null rows.

## D-024 — Leakage from NRCS's after-the-fact edits
**Date:** 2026-11-10 (notebook §3.10)
**Context:** on a real prediction date, a forecaster would have only the raw, provisional reading.
- NRCS later edits 29 % of snow-depth and 34 % of SWE values (median change 1.0 in / 0.2 in).
- It approves values months later. Recent winters are mostly provisional (P), and there are no QA flags at all before about 2023.

**Decision:** Milestone 3 includes a robustness run whose day-*t* features are rebuilt from `*_nrcs_orig` (the raw readings) instead of the edited values. **Every** SNOTEL-derived feature must be rebuilt (depth, SWE, their changes, season peak, station precipitation), not just today's depth (CODE_AUDIT A-03).

## D-025 — Keep everything in the clean table
**Date:** 2026-11-10 (notebook §3.6)
**Decision:** all 20 candidate stations and the full period stay in `data/processed/snotel_clean.parquet`. Resort and station selection (D-007/D-008) happens downstream by filtering rows.
**Evidence:** 285,778 rows × 49 columns, 4.51 MB parquet.

## D-026 — Ski-condition index as a secondary output
**Date:** 2026-11-10 (Owen asked whether a formula could estimate both depth and SWE, or a two-pass model could produce a quality score)
**Decision:** the original proposal's transparent ski-condition index is kept as a **secondary** output. It is computed from *predicted* depth plus Open-Meteo weather known on day *t* (sunshine, temperature, wind), and reported with sensitivity to the weights, as the proposal promised. It is never evaluation truth, and any weights are fixed using training winters only.
**Not in the current plan:** a snow-density model (depth = SWE / density; Sturm et al. 2010, *J. Hydrometeorology*; Hill et al. 2019, *The Cryosphere*) to reconstruct depth from SWE back to ~1980, or a two-stage SWE→depth model. It would add another fitted model and synthetic training targets, and the primary question can be answered without it (CODE_AUDIT A-05).

## Group (recorded 2026-11-10)
- Canvas project group **37**. Members: **Nat Toms, Owen Cruz-Abrams, Martha le Huray**.
- GitHub: MrDevel0per (repo owner), mlehuray246, nxt-txms (collaborators).
- The original proposal (Milestone 0) lists Tomer Burstein as author.

## D-027 — Open-Meteo feature set: 10 ERA5 + 4 ERA5-Land daily variables
**Date:** 2026-11-10
**Context:** Open-Meteo's fair-use accounting charges about (variables ÷ 10) × (days ÷ 14) calls per request. Limits are about 5,000 per hour and 10,000 per day per client. With 14 ERA5 variables, the 4 resort stations × 1997–2026 would cost about 7,300 calls. Notebook 01 had already used about 5,000 that UTC day, so the fetch would have spilled into the next day.
**Decision:**
- **ERA5 (10):** temperature max/min/mean, precipitation_sum, snowfall_sum, sunshine_duration, wind_speed_10m_max, cloud_cover_mean, relative_humidity_2m_mean, pressure_msl_mean.
- **ERA5-Land (4):** temperature mean/max/min, snow_depth_mean (used as a *feature* only).
- **Window:** 1997-07-01 → 2026-06-30, at each station's lat/lon/elevation, `timezone=auto`, in 5-year chunks. Total cost ≈ 6,000 calls.

**Dropped, as redundant or derivable:**
- `daylight_duration`: deterministic from date and latitude; we compute it ourselves if needed.
- `rain_sum`: dropped (D-030 shows it can *not* be derived from precipitation − snowfall).
- `wind_gusts_10m_max`: ≈ max wind speed.
- `shortwave_radiation_sum`: ≈ sunshine + cloud cover.

**Not done:** spreading downloads across group members' machines or IPs to get around per-client limits. That would circumvent the provider's fair-use limits, so we wait for the limits to reset instead. Defined in `src/sources.py`.

## D-028 — Disconnect- and crash-safe data collection
**Date:** 2026-11-10 (Owen: "make it robust to disconnects")
- **Atomic, crash-safe writes.** `lineage.store_and_log` writes `<file>.part`, fsyncs it, appends and fsyncs the manifest row, then renames atomically. A crash never leaves a partial file that looks cached. A re-run re-fetches, and the newer manifest row supersedes the old one (`verify_raw` checks the latest row per URL).
- **Network errors retried.** `lineage.get_with_retry` retries ConnectionError, Timeout and ChunkedEncodingError with back-off (10 s → 5 min). A minutely 429 is retried after 65 s. Hourly and daily 429s return immediately to the caller.
- **Unattended prefetch.** `scripts/prefetch_features.py` is idempotent. It sleeps to the next hour or to 00:05 UTC on hourly/daily limits, waits 2 min on network loss and retries indefinitely, removes stale `.part` files, and writes UTC-timestamped progress to `data/prefetch_features.log`.
- **Detached run.** It runs under `nohup` and `caffeinate -i`, so it survives the editor or Claude session closing and macOS idle sleep. Closing the lid still pauses it; it resumes on wake.
- **Tested:** `tests/test_robustness.py` covers Wi-Fi drop then recovery, a persistent outage, the hourly limit, a crash before the rename, and re-running after a crash.

## D-029 — Modelling-table rows: target date in Nov 1 – Apr 30; labels are measured targets only
**Date:** 2026-11-10 (notebook §4.3)
**Context:** the revised question asks for depth on day *t* + 30 during the season, so the season could constrain either the issue date or the target date.
**Options:** (a) issue date in Nov–Apr, so targets run to May 30; (b) **target date in Nov–Apr**, so issue dates run Oct 2 – Mar 31.
**Decision:** (b). It matches the question's "depth on day *t* + 30 (Nov–Apr)", and the issue and target date always fall in the same winter (asserted in `modeltable.model_table`).
- A row is a **label** only if the target is measured: present, not imputed, and every composite member present (`y_measured`).
- The single look-ahead in the project is `modeltable.labels()`.

**Evidence:** 14,319 rows × 58 columns; 14,231 measured labels; 13,862 complete-case rows (§4.3 funnel).

## D-030 — No cleaning of Open-Meteo values; snowfall and precipitation are not mutually consistent
**Date:** 2026-11-10 (notebook §3.7)
**Decision:** no imputation, outlier removal or capping for Open-Meteo inputs.
**Evidence:**
- Complete calendars at all 4 stations: 10,592 days, 0 NaN, no duplicate days at chunk seams.
- Zero violations of the temperature-ordering, non-negativity, RH/cloud bounds, pressure, and sunshine ≤ astronomical day-length checks.
- The largest precipitation days are documented storms, e.g. Heavenly 2017-01-08, 2021-10-24 and 2022-12-31 atmospheric rivers.

**Finding:** `snowfall_sum` (cm) exceeds 0.7 × `precipitation_sum` (mm) on 9–24 % of wet days, depending on station and precipitation band, with ratios up to 2.45. On 127–321 days per station there is snowfall with 0 precipitation (tiny amounts; minimum 0.07 cm = 0.1 mm × 0.7). The two variables are derived separately. **Never derive rain as precipitation − snowfall/0.7.**

## D-031 — Feature set (causal), Aspen weather, temperature source
**Date:** 2026-11-10 (notebook §4.2; `src/modeltable.py::build_features`)
**Decision:**
- **51 feature columns**, every one computed from rows dated ≤ *t* (`modeltable.FEATURE_DOCS`):
  - calendar (4, including `target_dowy`, which is used only to look up climatology, so 50 model inputs);
  - SNOTEL snow state: depth/SWE at *t*, 7/30-day changes, season peak, station precipitation sums (11);
  - ERA5 day-*t* values (7) and trailing 7/30-day sums/means (22);
  - season-to-date snowfall, precipitation and positive degree-days (3);
  - ERA5-Land snow depth and its changes, plus 7-day ERA5-Land temperature (4).
- Trailing windows are **strict**: one missing day makes the feature NaN.
- **Temperatures come from Open-Meteo only.** SNOTEL temperatures carry sensor drift (Aspen SNOTEL − ERA5 shifts about −1 °C from ~2013, DATA_SOURCES §2.0c), and their stuck-sensor rule looks ahead.
- **Aspen weather** = mean of the Kiln and Brumley requests, each at its own lat/lon/elevation. They are in **different** ERA5 and ERA5-Land cells.

**Evidence:** causality is proved by truncation and future-perturbation tests (`tests/test_modeltable.py`). This holds **given the cleaned inputs**; upstream look-ahead (NRCS edits, D-024; D-017's centred spike rule; D-022's gap rule) is disclosed in notebook §3.10.

## D-032 — Split by winter, common calendar for all resorts
**Date:** 2026-11-10 (notebook §4.4)
**Decision:** **train ≤ 2016, validation 2017–2020, test 2021–2026.** From now on every model choice uses train and validation only; the test winters are scored once, after every choice is frozen (see D-039 for the earlier exploratory access). Final models are refit on train + validation.
**Why:**
- Staff condition 3 (test on later winters).
- A common calendar keeps comparisons between resorts fair.
- Six test winters (1,087 rows per resort, 21–26 % of rows) span the extremes: 2023 is deepest on record at Heavenly and 2nd at Brighton; 2026 is the **shallowest on record** at Aspen and Brighton.
- A summer separates every winter, so no 30-day target window crosses a split.

**Stated caveat:** distribution shift. Test-winter mean depth is lower than training at Aspen (63 vs 70 cm) and Brighton (91 vs 100), equal at Heavenly, and more variable everywhere.

## D-033 — Cross-validation folds are whole winters
**Date:** 2026-11-10 (notebook §4.4)
**Decision:** hyper-parameter tuning uses folds grouped by winter, or expanding-window folds. Days are never shuffled.
**Evidence:** on train + validation winters only, the same ridge model's MAE looks 15–24 % smaller with shuffled 5-fold CV than with winter-grouped 5-fold CV. Neighbouring rows are near-duplicates. Owen asked to keep this demonstration in the notebook.

## D-034 — Hindcast caveat: reanalysis latency
**Date:** 2026-11-10
**Context:** ERA5 is published about 5 days behind real time. Day-*t* reanalysis stands in for what a real-time analysis would know.
**Decision:** state this as a hindcast assumption. Milestone 3 adds a sensitivity run with every weather feature lagged 5 days.

## D-035 — Baseline definitions; how models must handle collinearity
**Date:** 2026-11-10 (notebook §4.5; `modeltable.climatology`)
**Decision:**
- **Climatology** = mean measured SNWD at the target's day of the water year, pooled ±7 days, across training winters only. It is fitted on train for validation scoring and on train + validation for test scoring.
- **Persistence** = `snwd_t`.
- **Persistence + climatological change** = `snwd_t + clim(target day) − clim(t)`, clipped ≥ 0. This is the strongest simple reference, and we report it as a harder bar than the two baselines named in the question.
- All baselines are scored on the same rows: measured target and known `snwd_t`.

**Evidence (validation winters 2017–2020, climatology fitted on train; MAE in cm, n = 725 per resort; `data/processed/baseline_scores.csv`):**

| Resort | Persistence + clim. change | Climatology | Persistence |
|---|---|---|---|
| Aspen | 12.5 | 16.9 | 24.1 |
| Brighton | 18.7 | 28.1 | 31.7 |
| Heavenly | 36.2 | 56.5 | 44.0 |

- The pooling half-width barely matters: under 0.3 cm of validation MAE between ±0 and ±15 days.

**Collinearity:** 31 feature pairs have |ρ| > 0.95. Milestone 3 uses ridge/lasso and/or one representative per correlated group; random forests are unaffected.

## D-036 — Open-Meteo grid-cell selection
**Date:** 2026-11-10
**Finding:** we did not pass `cell_selection`, so Open-Meteo's default `land` applied. That default picks a nearby land cell with terrain elevation close to the requested `elevation=`, not necessarily the nearest cell. The returned cells are 1.5–13 km from the stations and identical across all chunks. The returned elevation equals the one we sent.
**Decision:** accept and record the cells (DATA_SOURCES). Any future request passes `cell_selection=land` explicitly. Existing requests are not re-issued, because that would cost about 6,000 calls and change nothing.

## Independent audit of the modelling code (2026-11-10)
A separate reviewer audited `src/modeltable.py`, its tests and the modelling notebook for leakage. It found **no leak** in the features, labels, split or baselines that affects any result; all scores are unchanged. The fixes it prompted:
1. `labels()` now sets `y` to NaN unless the target is measured. Previously, 39 imputed Aspen training targets were kept in `y`, guarded only by the `y_measured` flag.
2. The autocorrelation check now uses train + validation winters only, with pairs inside the same winter and the lag in days. The earlier version included the test winters and paired days across winters.
3. The wording of the leakage claims now says "given the cleaned inputs". Upstream look-ahead (NRCS edits and S-flags; which ≤3-day gaps get filled) is disclosed.
4. Several captions were tightened:
   - "training winters" for the final test fit means train + validation;
   - "measured" means "an NRCS value we did not impute" (which includes NRCS E and K values).
5. More tests: splits don't overlap, the winter filter works, and climatology ignores poisoned `snwd_measured` flags.

A second audit (`docs/CODE_AUDIT.md`, A-01 to A-05) led to D-039 and D-042.

## D-039 — Disclose test access; freeze the evaluation protocol
**Date:** 2026-11-10 (adopted with D-042)
**Context:** an exploratory notebook (commit `eca1c57`) plotted, ranked and scored the baselines on winters 2021–2026, while D-032 called them touched once after choices are frozen (CODE_AUDIT A-01).
**Options:** (a) keep calling this an untouched test set; (b) keep the fixed calendar, disclose the exploratory access, and freeze future choices using development winters only; (c) collect future independent outcomes.
**Decision:** (b). The notebook discloses it (§3, §4.4), baselines are scored on validation winters only, and the test winters are not plotted or scored again until the final run. We do not change year boundaries to chase a better score. Model–baseline comparisons use identical resort/date rows.
**Why:** fitting baselines without the test years is correct, but it does not undo having looked at them. The cleaning thresholds (D-017 to D-021) were also chosen on all winters; they never see the target and are applied identically everywhere.

## D-042 — One submission notebook; simpler code; validation-only baselines
**Date:** 2026-11-10 (Owen: "LGTM"; asked for simplicity and readability as absolute priorities)
**Context:** the Milestone 2 spec asks for one notebook that gets, understands and cleans the data, then states the question. We had four
(01, 01b, 02, 03; ~200 cells), much of it exploration whose findings are already recorded here and in DATA_SOURCES.md. Audit A-05 asked for one
ordered submission notebook; A-01 for no further test-winter scoring; A-03 found the `rob_*` robustness inputs incomplete.
**Options:** (a) submit all four; (b) concatenate them; (c) one new notebook with only what the spec asks for, citing docs for the rest.
**Decision:** (c), `notebooks/snowpredict.ipynb` (runs offline in ~10 s). Alongside it:
- Kept: the source checks behind key decisions (`best_match` break, `elevation=` effect, snow-depth coverage), every SNOTEL cleaning rule (D-016 to D-023, unchanged), the Open-Meteo checks, missingness, target distribution, scale, leakage, the modelling table, the split, and an explicit revised-question cell.
- Dropped from the notebook (evidence stays at commit `eca1c57` and in DATA_SOURCES.md): model-by-model probes, other-API probes, the ERA5-Land validation and lag tables, the 01b parser/aggregation cross-checks, the Open-Meteo grid-cell, homogeneity and agreement tables, feature-correlation EDA, and the originals QC calibration. The random-split demonstration was kept (§4.4, Owen): a random split flatters the same ridge model by 15–24 %.
- Baselines are scored on **validation winters only** (fitted on train); the test winters are no longer scored or plotted (D-039).
- The partial `rob_*` columns and an exploratory originals spike filter were removed. D-024's robustness run is still required in Milestone 3 and must rebuild *every* SNOTEL feature from originals, so the three partial columns were not reusable.
- Code: `src/lineage_text.py` (only used by 01b) and the one-time manifest migration were removed; `src/features.py` became `src/sources.py`, the single definition of every production request; the feature data dictionary moved next to `build_features` (`modeltable.FEATURE_DOCS`, with a test that every feature is documented).

**Evidence of no numerical change:** `snotel_clean.parquet` is byte-identical; `model_table.parquet` is identical except for the 3 dropped `rob_*` columns (14,319 × 58); all 40 cleaning-log counts are identical; the validation baseline scores equal the old notebook's. 59 tests pass.

## D-043 — Kept from the original proposal: 30-day horizon, regression, linear regression and random forest, MAE
**Date:** 2026-11-13 (recorded; these were carried over from Milestone 0 and never changed)
**Context:** the original proposal (`Original Proposal/`) asked whether ML can predict ski conditions **30 days in advance** better than historical seasonal averages. It planned **regression**, comparing **linear regression and random forest regression** against historical-average baselines, trained on earlier winters, tested on held-out later winters, and scored by **MAE, RMSE and R²**. D-003 and D-005 changed *where* and *what* we predict; these parts were kept.
**Decision:**
- **Horizon:** 30 days (issue date *t*, target *t* + 30). It matches a traveller booking a ski trip about a month ahead, the proposal's motivation.
- **Models:** linear regression (regularised, ridge/lasso, because of collinearity, D-035) and random forest, one per resort (D-007), tuned with whole-winter folds (D-033).
- **Metrics:** **MAE (cm) is the primary metric**, because it is in the target's units and robust to Heavenly's long right tail (notebook §3.8). RMSE, bias and R² are reported alongside. Because depth depends strongly on the month (§3.8), MAE is also reported by month. Models and baselines are always scored on identical rows.
- **Secondary question kept:** does accuracy differ by resort, and through the season?

## D-044 — Complete-case modelling rows; no imputation to rescue rows
**Date:** 2026-11-10 (notebook §4.3)
**Context:** after the label filter, some rows still have a NaN feature, mostly from strict trailing windows over SNOTEL gaps.
**Options:** (a) drop incomplete rows (complete case); (b) fit an imputer on training winters; (c) let a model handle NaN natively.
**Decision:** (a). Nothing is imputed to keep rows beyond D-022's ≤ 3-day forward fill. Every model and baseline is scored on the same eligible rows.
**Why:** an imputer is another fitted component that can leak or hide bad data. The losses are small (13,862 complete-case rows of 14,231 measured labels), except that SNOTEL precipitation gaps (`prcp_sum_7/30`) remove Aspen's whole 2021 winter. Dropping those two features (Open-Meteo precipitation covers them) is an open item below.

---

## Open for Milestone 3 (not yet decided)
These come from `docs/CODE_AUDIT.md`. None has been adopted; the current notebook does not implement them.
- **Fully causal gap filling** (A-02): a fill rule that depends only on how long a gap has lasted so far, replacing D-022's "gap ends within 3 days" rule.
- **Drop `prcp_sum_7` / `prcp_sum_30` from the model inputs** (A-04): restores Aspen's 2021 winter (complete rows 3,747 → 3,977). The decision must be made on coverage, not test error.
- **Robustness run from NRCS originals** (D-024, A-03): needs a causal QC for raw readings, because raw originals contain multi-day glitches (e.g. Brighton 208 in on a 10 in day, 2023-11-23).
- **5-day weather lag sensitivity run** (D-034).
