# Data sources — what exists, what we tested, what we found

All probes were run on 2026-11-09. "St. Anton" = 47.13, 10.27. "Independence Pass" = SNOTEL 542:CO:SNTL (39.07543, -106.61154, 10,570 ft / 3222 m).

---

## 1. Open-Meteo Historical Weather API (primary source; required by staff)

Endpoint: `https://archive-api.open-meteo.com/v1/archive`. Docs: https://open-meteo.com/en/docs/historical-weather-api
No API key is needed. Data is daily or hourly for any lat/lon.

### 1.1 Models (`models=` parameter), as tested

| Model | Coverage observed | Resolution | Snow depth | Snowfall | Sunshine/wind | Notes |
|---|---|---|---|---|---|---|
| `era5` | 1940 → ~5 days ago (last value 2026-11-03) | 0.25° (~25 km) | **no** | yes | yes | Consistent over the whole period |
| `era5_land` | 1950 → ~5 days ago | 0.1° (~9 km) | **yes** | no | no | Land-surface variables only (temp, snow depth) |
| `era5_seamless` | 1940 → present | mix | yes | yes | yes | Merges ERA5 + ERA5-Land. Stable, no switch in 2017 |
| `ecmwf_ifs` | **2017 →** present | ~9 km | only recent | yes | yes | Operational model, not a reanalysis |
| `cerra` | 1985 → **2021-06-30** | 5.5 km, **Europe only** | yes | yes | yes | Best resolution, but stops in 2021 |
| `best_match` | 1940 → present | varies | yes | yes | yes | **Switches to IFS in 2017. Do not use.** |

### 1.2 Variables confirmed returning values (`era5_seamless`, daily)
`weather_code, temperature_2m_max/min/mean, apparent_temperature_mean, precipitation_sum, rain_sum,
snowfall_sum, snowfall_water_equivalent_sum, precipitation_hours, sunshine_duration, daylight_duration,
wind_speed_10m_max, wind_gusts_10m_max, wind_direction_10m_dominant, shortwave_radiation_sum,
cloud_cover_mean, relative_humidity_2m_mean, pressure_msl_mean`
Hourly: `snow_depth` (m), `cloud_cover_low`, `boundary_layer_height`.
Returned **null** in the archive: `freezing_level_height`, `visibility`, `snow_depth_water_equivalent`.
**Correction (session 2):** snow depth is *also* available as daily `snow_depth_mean` / `snow_depth_max` (era5_land). Verified at 39.2, -106.9 on 2020-01-15: 0.70 / 0.71 m. The session-1 validation (§2.2) used hourly `snow_depth` at 12:00 local; later work uses the daily mean.

**Rate limits:** the free tier allows about 10k calls/day. Long date ranges and many variables count as multiple calls. We cache every response (D-011), so re-runs cost nothing.

### 1.3 ⚠ `best_match` has a structural break in 2017
St. Anton, Jan 15 daily mean temperature:

| Year | best_match | era5_land | ecmwf_ifs |
|---|---|---|---|
| 2016 | -8.2 | -8.2 | null |
| 2018 | **-1.9** | -9.3 | -1.9 |
| 2022 | **+9.6** | +1.3 | +9.6 |

From 2017 on, `best_match` equals IFS; before that it equals ERA5-Land. A model trained on 2005–2016 and tested on 2018+ would be learning a change in data source, not a change in weather. Hence the rule: pin the model.
Same day (2021-01-10, St. Anton): IFS gives -4.2°C and ERA5 gives -14.4°C. The disagreement between models is large in complex terrain.

### 1.4 The `elevation=` parameter
Open-Meteo applies a lapse-rate correction to **temperature only**. St. Anton, 2020-01-15, `era5_seamless`:

| elevation | T mean | snow_depth |
|---|---|---|
| 1300 m | -3.6 | 1.16 m |
| 2000 m | -8.1 | 1.16 m |
| 2800 m | -13.3 | 1.16 m |

**Snow depth and snowfall are grid-cell values and do not respond to elevation.** By default, the API uses the grid-cell terrain height (St. Anton = 1286 m, which is village level, not the slopes). This is the main weakness of reanalysis for ski conditions.

### 1.5 Other Open-Meteo APIs checked

| API | What it is | Usable for us? |
|---|---|---|
| Seasonal (`seasonal-api.open-meteo.com/v1/seasonal`) | ECMWF SEAS5 ensemble (51 members), 6+ months ahead | **Only from 2025-09-01 onward** (`start_date` error). No historical hindcasts, so we can't backtest against a real 30-day forecast over 20 winters. Could still serve as a one-season "live" comparison for 2025-26/2026-27. |
| Historical Forecast (`historical-forecast-api`) | Archived short-range forecast output | Starts ~2017 (null in 2016). Same values as IFS. Only short lead times, so not relevant at 30 days. |
| Previous Runs (`previous-runs-api`) | Forecasts issued N days before | Returned null for lags of 7/14 days in Jan 2024. Lags are at most a few days and coverage is recent only. Not useful. |
| Climate (`climate-api`, CMIP6) | Climate-model simulations, 1950–2050 | Free-running simulations, not tied to real weather dates. Not useful as observations. |

**Implication:** a real 30-day forecast product to compare against does not exist historically in Open-Meteo. Our baselines are climatology (required) and persistence.

---

## 2. NRCS SNOTEL (ground-truth station observations; supplementary)

REST API: `https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/` (no key). Info: https://www.nrcs.usda.gov/wps/portal/wcc/home/
Automated stations in US western mountains: **919** SNOTEL stations (UT 141, CO 118, MT 96, WY 90, ID 87, OR 82, WA 79, AK 78, NV 58, CA 36, NM 29, AZ 23).
Daily elements: `WTEQ` snow water equivalent (in), `SNWD` snow depth (in), `TAVG/TMAX/TMIN` (°F), `PREC` accumulated precipitation (in), `PRCP` increment.

Example: `.../data?stationTriplets=542:CO:SNTL&elements=SNWD,WTEQ,TAVG,PREC&duration=DAILY&beginDate=1980-10-01&endDate=2026-05-31`
Station list: `.../stations?stationTriplets=*:*:SNTL` (adding `returnStationElements=true` for all stations fails with a 400 "too many elements" error. Request it for a short list instead.)

⚠ The `beginDate` in station-element metadata is **not reliable** for record length. Snowbird's metadata says WTEQ starts in 2016, yet it returns values for 2000. Always count actual non-null values.

### 2.0 AWDB `/data` parameters that matter (from `https://wcc.sc.egov.usda.gov/awdbRestApi/v3/api-docs`)
| Param | Default | We use | Why |
|---|---|---|---|
| `returnFlags` | false | **true** | QC/QA flag per value |
| `returnOriginalValues` | false | **true** | adds `origValue`/`origQcFlag`, the value before NRCS edited it |
| `returnSuspectData` | **false** | **true** | the default silently drops suspect values, a hidden filter (D-009) |
| `periodRef` | END | END (explicit) | timestamp convention; alignment with Open-Meteo is checked via lag correlation |
| `centralTendencyType` | NONE | **never** | NRCS 30-yr normals include test years, so using them leaks (D-010) |

Example of an edit: Ivanhoe 547:CO, SNWD, 2010-01-02. The original value was 204 in (`origQcFlag` S); it was edited to 31 in (`qcFlag` E).

### 2.0b Flag definitions
Sources: the header of the NRCS Report Generator CSV (https://wcc.sc.egov.usda.gov/reportGenerator/) and the hourly SNOTEL dataset documentation (https://zenodo.org/records/7820056).

**QC flags (`qcFlag`)**
| Flag | Meaning |
|---|---|
| V | Valid: validated data |
| N | No profile for automated validation |
| E | Edit: minor adjustment for sensor noise |
| K | Estimate |
| C | Correction: a different equation was applied to the sensor voltage |
| B | Back-estimate: regression to homogenize snow-course and snow-pillow data |
| X | External estimate |
| S | Suspect |
| M | Missing |

**QA flags (`qaFlag`)**
| Flag | Meaning |
|---|---|
| P | Provisional: preliminary human review |
| A | Approved: processing and final review complete |
| R | Raw: no human review (reported by other sources) |
| F | Flagged: automated QC flag assigned (reported by other sources) |

Ivanhoe SNWD 1998–2026 (qcFlag, qaFlag) tally:

| (qcFlag, qaFlag) | Count |
|---|---|
| (V, –) | 6426 |
| (E, –) | 2598 |
| (V, A) | 422 |
| (E, A) | 253 |
| (V, P) | 185 |
| (K, A) | 56 |
| (E, P) | 56 |
| (K, P) | 33 |

About ⅓ of the values are edited or estimated.

### 2.0c Known caveat: SNOTEL temperature sensor change
In the mid-2000s, SNOTEL's temperature sensor change introduced an artificial warm bias at high elevations. See Oyler et al. (2015), *Geophysical Research Letters*, "Artificial amplification of warming trends across the mountains of the western United States." This is another structural-break risk, comparable to `best_match` (§1.3). We therefore prefer Open-Meteo temperature for features. NRCS issued a bias correction (the NOAA9 polynomial), which the Zenodo hourly dataset applies.

### 2.1 Usable record length: count of "good winters" (≥100 of 121 Dec–Mar days non-null)

**Aspen area** (distance from Aspen town):

| Station | Elev (ft) | km | WTEQ | SNWD | TAVG |
|---|---|---|---|---|---|
| 542 Independence Pass | 10,570 | 22 | 1981–2026 (46) | 2007–2026 (19) | 1986–2026 (40) |
| 556 Kiln | 9,610 | 23 | 1981–2026 (46) | 2004–2026 (23) | 1986–2026 (40) |
| 369 Brumley | 10,570 | 26 | 1981–2026 (46) | 2004–2026 (23) | 1986–2026 (41) |
| 547 Ivanhoe | 10,540 | 26 | 1992–2026 (35) | 1998–2026 (25) | 1992–2026 (33) |
| 658 Nast Lake | 8,710 | 22 | 1986–2026 (41) | 2004–2026 (22) | 1986–2026 (40) |
| 737 Schofield Pass | 10,640 | 28 | 1986–2026 (41) | 1998–2026 (28) | 1986–2026 (40) |
| 669 North Lost Trail | 9,190 | 31 | 1986–2026 (41) | 2004–2026 (21) | 1986–2026 (40) |
| 380 Butte (Crested Butte) | 10,190 | 35 | 1981–2026 (46) | 2004–2026 (22) | 1986–2026 (40) |
| 1101 Chapman Tunnel | 10,090 | 18 | 2008–2026 (19) | 2010–2026 (17) | 2008–2026 (19) |
| 1141 Upper Taylor | 10,710 | 23 | 2010–2026 (17) | 2010–2026 (17) | 2010–2026 (17) |
| 1326 Castle Peak | 11,510 | 21 | 2025 only | — | — |

**Other resort stations** (counted from 2001 onward only):

| Station | Resort | WTEQ | SNWD | TAVG |
|---|---|---|---|---|
| 766:UT Snowbird | Snowbird | 26 | 24 | 23 |
| 366:UT Brighton | Brighton | 26 | 26 | 20 |
| 842:CO Vail Mountain | Vail | 26 | 20 | 26 |
| 415:CO Copper Mountain | Copper | 26 | 21 | 26 |
| 784:CA Palisades Tahoe | Palisades | 26 | 24 | 25 |
| 590:MT Lone Mountain | Big Sky | 26 | 24 | 26 |
| 791:WA Stevens Pass | Stevens Pass | 26 | 23 | 25 |
| 1082:WY Grand Targhee | Targhee | 19 | 20 | 18 |

Other active stations named after resorts: Loveland Basin (602:CO), Tower/Steamboat (825:CO), Berthoud Summit (335:CO), Heavenly Valley (518:CA), Thaynes Canyon/Park City (814:UT), Mt Hood Test Site (651:OR), Wells Creek/Mt Baker (909:WA), Schweitzer Basin (738:ID).
**Pattern:** SWE and precipitation go back to roughly 1980. Snow-depth sensors were added around 1998–2007, so depth gives about 20 winters.

### 2.2 Validation: Open-Meteo vs SNOTEL at Independence Pass (Dec–Mar, 2007–2026)
Open-Meteo queried at the station's lat/lon with `elevation=3222`; snow depth taken at 12:00 local.

| Comparison | n days | Pearson r | Mean obs | Mean model |
|---|---|---|---|---|
| SNWD vs ERA5-Land `snow_depth` (inches) | 2271 | **0.936** | 39.2 | 30.8 (≈21% low) |
| TAVG vs ERA5-Land T2m (°C) | 2268 | 0.925 | -8.9 | -8.2 |
| TAVG vs ERA5 T2m (°C) | 2268 | 0.938 | -8.9 | -7.8 |

At this site Open-Meteo's reanalysis tracks real snow depth well, but it is biased low. We have checked one station only so far; the rest should be checked in the notebook.

---

## 3. Not pursued (and why)
- **Meteostat:** linked by mistake in the original proposal. Staff require Open-Meteo.
- **European in-situ snow data** (e.g. Austrian/Swiss/Italian station networks): fragmented across national agencies, often with access requests or non-English portals. No single free API equivalent to SNOTEL.
- **Resort-reported snow reports (OnTheSnow, etc.):** no historical API. Scraping is fragile, and resort figures are marketing numbers.

---

## 4. Notebook 01 results (2026-11-10). Full evidence is in `notebooks/01_data_source_eda.ipynb` §7
- `/stations?stationTriplets=*:*:SNTL` returns **only active stations** (919, all with endDate 2100). Use the `activeOnly=false` parameter (if needed) to see retired ones.
- Flag codes seen in the data but missing from our NRCS definition list: QC `G`, `T` (in `orig_qc_flag`) and QA `U`. They appear on missing/null rows (e.g. `M`/`U` on pre-record PRCP). Treat them as unknown and do not use them as quality evidence.
- QC flag `C` (sensor equation correction) is on ~56 % of SNOTEL temperature values. This is consistent with NRCS's temperature re-processing.
- Validation (Dec–Mar, 1995–2026, ERA5-Land at station lat/lon/elevation): depth r 0.85–0.96 except North Lost Trail 0.55; bias −4 % (Kiln) to −59 % (Snowbird); temperature r ≈ 0.9 except Butte 0.12, Nast Lake 0.67.
- **Date alignment:** SNOTEL value dated *t* best matches Open-Meteo `snow_depth_mean` of day *t+1* (19 of 20 stations; lag correlation of daily changes).
- Elevation test at Aspen: snow depth 0.69 → 0.73 m at 3400 m (an otherwise constant snow field). Possibly a different grid cell is chosen. Unverified.

## 5. Independent verification (notebook 01b, 2026-11-10)

**SNOTEL: our parser vs the NRCS Report Generator CSV** (an independent NRCS endpoint, fetched via `src/lineage_text.py`).
Checked at Ivanhoe (547:CO, ~12.7k days) and Palisades Tahoe (784:CA, ~16.7k days):
- 100 % exact match for WTEQ, SNWD, TAVG, TMAX, TMIN and PRCP, and 99.73 % for PREC. **0 unexplained mismatches.**
- The leftover differences are fully explained:
  - (a) **PREC resets to 0 at the start of each water year (Oct 1)**, so difference it within a water year or use PRCP.
  - (b) **Suspect (S) values**, which AWDB returns only because we set `returnSuspectData=true` and which the Report Generator hides. Some are physically impossible, e.g. Ivanhoe TMIN = 2148.6 °F on 1994-10-01, so cleaning must drop S values.
- Report Generator URL format: `https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/customSingleStationReport/daily/<triplet>%7Cid=%22%22%7Cname/POR_BEGIN,POR_END/<EL>::value,...`
- NRCS's own CSV header warns that data are "subject to revision regardless of indicated Quality Assurance level" and that "SNOTEL air temperature data contains a known bias".

**SNOTEL date semantics (checked directly).**
- SNWD, WTEQ and PREC are instantaneous midnight readings. With `periodRef=END`, the AWDB value dated *d* is the reading at the **end of day *d*** (SNWD END(*d*) = START(*d*+1)). The Report Generator labels the same reading "start of day *d*+1".
- Daily aggregates (TAVG/TMAX/TMIN/PRCP) carry the same date under either setting.
- **For modelling:** weather on day *d* pairs with SNWD dated *d*, and "depth 30 days after *t*" is SNWD dated *t*+30.
- This explains notebook 01's lag result: the end-of-day reading leads Open-Meteo's daily *mean* by about a day.
- SNOTEL stamps are in local *standard* time all year, while `timezone=auto` switches to daylight time in mid-March. The resulting ≤1 h offset is negligible for daily depth.

**Open-Meteo: daily vs hourly.** With `timezone=auto`, daily `snow_depth_mean/max` equal the **local-calendar-day** mean/max of the hourly `snow_depth` on 100 % of 182 days (ERA5-Land and ERA5-seamless, Aspen 2023-24). Aggregating by UTC day would disagree on 34–50 % of days, so always request `timezone=auto`.
- *The temperature version of this check is pending.* Open-Meteo's **hourly** request limit was hit. Re-run 01b §3b later.

**Rate limits.** Besides the per-minute limit, Open-Meteo has an **hourly** limit ("Hourly API request limit exceeded"). A full notebook-01 run can reach it, and a 65 s back-off does not clear it. The cache means re-runs cost nothing.

**pandas 3 note:** missing flag strings come back as NaN, not None. Use `pd.isna`, never `is None`.

**Tests:** `uv run pytest` runs 24 offline tests covering lineage, offline mode, manifest migration, verify_raw, parse and `winter_of`.

## 6. Cleaning (notebook 02, 2026-11-10)
Evidence and rules are in `notebooks/02_cleaning_snotel.ipynb`. Each rule's rows affected are in `data/processed/cleaning_log.csv`. Decisions: D-016 to D-025.

**Missingness (SNWD)**
- 40.5 % of station-days are NaN, but 39.8 % are days before the sensor was installed.
- Missing while installed: 1.19 % (2,043 days; 1.36 % in Nov–Apr). After the causal ≤3-day fill: 0.75 %.
- Gaps cluster in each sensor's first winters (~2003–2010) and are near zero after 2011.
- They are mostly NRCS suspect (S) removals.
- They are **not depth-dependent**: depth the day before a gap is 42.1 in vs an in-season mean of 41.1 in.
- Only 35 % coincide with a temperature gap.
- Temperature: ~14 % before install, ~1.7 % missing while installed. SWE and precipitation are almost complete.

**Output:** `data/processed/snotel_clean.parquet`
- 285,778 rows × 49 columns, 4.51 MB; 20 stations, 1978-10-01 to 2026-07-31.
- SI units, plus provenance columns per variable: `_clean_flag`, `_imputed`, `_nrcs_qc`, `_nrcs_qa`, `_nrcs_orig`.
- 84,261 usable target station-days (in season, measured, not imputed); 2.5 % zeros; skew 1.07.

**Surprises**
- **NRCS edits can be wrong.** At Vail on 2008-03-17 and 2008-04-10, raw readings of ~199 in were "edited" to 0 in. The spike rule caught both.
- **Stuck temperature loggers:** ~1,300 flat-lined days per temperature variable, mostly 1985–1991 at Palisades, Stevens Pass, Heavenly and Brumley.
- **−60.3 °F sentinel:** appears ~187 times in the original readings, 131 of them at Independence Pass.
- **No QA flags before ~2023.** Recent winters are mostly provisional (P), so NRCS may still revise them (D-024).
