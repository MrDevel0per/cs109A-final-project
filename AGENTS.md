# AGENTS.md — SnowPredict (DataSci1 Final Project)

Instructions for any AI agent (or human) working in this repo. Read this first.

## Project in one paragraph

**SnowPredict:** can machine learning predict **SNOTEL-measured snow depth 30 days ahead** at three ski areas more
accurately than (a) a day-of-season climatology computed from training winters only and (b) persistence? Regression models (linear
regression, random forest), one per resort, use Open-Meteo weather and SNOTEL history available on day *t*. We train on earlier
winters and test on later ones. A transparent ski-condition index built from the predictions is a secondary output (D-026).
The original proposal (Europe, weather-index target) is in `Original Proposal/`. How and why the plan changed is in `docs/DECISIONS.md`.

**Group 37:** Nat Toms, Owen Cruz-Abrams, Martha le Huray. GitHub: MrDevel0per (owner), mlehuray246, nxt-txms.

**Final resorts (D-007, D-008; also `src/sites.py::RESORTS`):**
| Resort | SNOTEL station(s) | Winters | Climate |
|---|---|---|---|
| Aspen CO | Kiln 556:CO + Brumley 369:CO, fixed composite (mean on days both present, else NaN) | 2004–2026 | continental |
| Brighton UT | 366:UT | 1998–2026 | intermountain |
| Heavenly CA | 518:CA | 2000–2026 | Sierra (lee side of Tahoe) |

## Hard constraints from course staff (do not violate)

From `Original Proposal/Staff Comments.txt`:
1. **Weather source is Open-Meteo.** The original proposal linked to Meteostat by mistake. Fix that in the revised proposal and cite Open-Meteo with a correct link.
2. **Keep the baseline comparison:** compare against historical averages for the same time of year.
3. **Test on later winters:** split by time, never randomly.
4. **Compute the climatology baseline from the training years only.** Test-year data must never be used in it.

## Milestone 2 deliverables (due Fri 2026-11-13, 9:59 pm ET)

From `Original Proposal/Milestone 2.md`: slides (PDF), notebook (.ipynb), and a 1–2 page revised proposal (PDF).
The notebook must start with the Canvas group number and member names. It then covers, in order:
getting the data (including size in MB), understanding it, cleaning it, and the revised question.

## Documentation rule — EVERYTHING gets written down

We must be able to justify every choice in the presentation and the revised proposal. So:

- **Every decision** goes in `docs/DECISIONS.md` as a numbered entry: date, context, options considered, choice, why, and the evidence behind it. Only decisions the group has actually made are entries; ideas not yet decided go in its "Open for Milestone 3" list. If a decision changes, add a new entry that supersedes it.
- **Every data finding** (API behaviour, coverage, quirks, validation numbers) goes in `docs/DATA_SOURCES.md`, with the exact query or URL that produced it so anyone can reproduce it.
- **Every work session** gets a dated entry in `docs/LOG.md`: what was done, what was learned, and what's next.
- Cleaning steps live in the notebook, each with a one-line reason, because the rubric grades the reasoning.
- If a number is quoted anywhere (slides, proposal), its source must be traceable to a doc or notebook cell.

## Data conventions

- **Never use Open-Meteo `models=best_match`.** It silently switches from ERA5-Land to ECMWF IFS in 2017, which creates a fake structural break (see DATA_SOURCES.md §1.3). Always pin the model explicitly.
- Always pass `elevation=` explicitly to Open-Meteo, and record which elevation was used.
- Store raw API responses unchanged under `data/raw/` (never edit them). Store cleaned tables under `data/processed/`. Write fetch code as re-runnable scripts or cells that cache to disk.
- Units: keep source units in the raw files. Convert to SI (cm, °C, km/h) in processing. SNOTEL is in inches and °F.
- "Winter season" = Nov 1 to Apr 30, labelled by the year it ends (the 2024-25 season = 2025).
- Leakage: features for a prediction made on date *t* may use only data dated ≤ *t*. Climatology may use only training seasons.

- **SNOTEL is always fetched with `returnFlags=true`, `returnOriginalValues=true`, `returnSuspectData=true`, and `periodRef=END` stated explicitly** (D-009). Never request NRCS normals (`centralTendencyType`) (D-010).
- All external data goes through `src/lineage.py::fetch()` (D-011). Never use ad-hoc `requests.get` in notebooks. Production requests are defined once in `src/sources.py`. The notebook runs with `SNOWPREDICT_OFFLINE=1` by default, so it can only use logged raw data.
- **Imputation must be causal** (D-022): only forward-fill short interior gaps, never interpolate using later values. Any new imputation needs a causality unit test.
- **The split is by winter: train ≤ 2016, validation 2017–2020, test 2021–2026 (D-032).** Touch the test winters once, at the end. CV folds are whole winters (D-033).
- **Evaluation uses measured, non-imputed SNWD only.** Imputed rows (`SNWD_imputed`) and any reconstructed depth (D-026) are never evaluation truth.
- Date semantics: SNOTEL SNWD/WTEQ dated *d* is the **end-of-day-*d*** reading. Weather on day *d* pairs with SNWD dated *d*. PREC resets each Oct 1, so use PRCP or difference PREC within a water year.
- Anything fit to data (scalers, climatology, density model, index weights) is fit on **training winters only**.

## How to run

```bash
uv sync                 # installs from pyproject.toml / uv.lock (Python 3.12)
uv run jupyter lab                    # open notebooks/snowpredict.ipynb (the one Milestone 2 notebook)
uv run pytest -q                      # offline unit tests (lineage, parse, clean, modeltable)
uv run python src/verify_raw.py       # raw-data integrity vs MANIFEST sha256
```
Notebooks import from `src/` by adding `../src` to `sys.path`.

- `src/lineage.py` — HOW we download: `fetch()`, `open_meteo()`, `snotel()`, and `manifest()`. These cache raw responses and log every fetch to `data/raw/MANIFEST.csv`.
- `src/sources.py` — WHAT we download: station metadata, SNOTEL daily data (D-009 parameters) and the Open-Meteo feature requests (D-027).
- `src/sites.py` — the single source of truth for ski areas, candidate SNOTEL stations, the final `RESORTS`, elements, and the date range. Log any change to it in DECISIONS.md.
- `src/parse.py` — raw JSON → tidy tables (no cleaning). `src/clean.py` — pure cleaning functions used by the notebook's §3.
- `src/modeltable.py` — resort series, causal features and their data dictionary (`FEATURE_DOCS`), labels (the ONLY look-ahead), climatology and the split (D-029 to D-035). Its leakage guarantees are tested in `tests/test_modeltable.py`; keep them passing.
- `src/verify_raw.py` — checks every raw file's sha256 against the manifest and flags orphan files.
- `docs/MS2_CHECKLIST.md` — every Milestone 2 requirement, where it is addressed, and its status. Keep it current.

## Layout

```
Original Proposal/   original proposal, milestone spec, staff comments (read-only; not in public repo, D-013)
docs/                DECISIONS.md, DATA_SOURCES.md, LOG.md, MS2_CHECKLIST.md
src/                 lineage.py (fetch + manifest), sources.py (request definitions), sites.py, parse.py, clean.py, modeltable.py, verify_raw.py
tests/               pytest, offline
data/raw/            untouched API pulls + MANIFEST.csv
data/processed/      snotel_clean.parquet, cleaning_log.csv, snotel_clean_columns.csv,
                     model_table.parquet, model_table_columns.csv, baseline_scores.csv
figures/             PNGs saved by the notebook for the slides
scripts/             prefetch_features.py (unattended, resumable Open-Meteo download)
notebooks/           snowpredict.ipynb — the single notebook (D-042). The earlier notebooks 01/01b/02/03 cited in docs are at commit eca1c57
pyproject.toml, uv.lock   uv environment
```
