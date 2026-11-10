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
