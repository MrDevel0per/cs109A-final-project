# AGENTS.md — SnowPredict (DataSci1 Final Project)

Instructions for any AI agent (or human) working in this repo. Read this first.

## Project in one paragraph

**SnowPredict:** can machine learning predict overall skiing conditions 30 days ahead more
accurately than historical averages for the same time of year? Regression models (linear
regression, random forest) predict weather/snow variables 30 days out. Those predictions are
combined into a transparent ski-condition index. We train on earlier winters and test on later ones.
The original proposal is in `Original Proposal/`.

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

- **Every decision** goes in `docs/DECISIONS.md` as a numbered entry: context, options considered, choice, why, and the evidence behind it. Mark each entry `PROPOSED` or `ACCEPTED`. Only a group member can mark an entry `ACCEPTED`. Never delete an entry; if a decision changes, add a new entry that supersedes it.
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
- All external data goes through `src/lineage.py::fetch()` (D-011). Never use ad-hoc `requests.get` in notebooks.

## How to run

```bash
uv sync                 # installs from pyproject.toml / uv.lock (Python 3.12)
uv run jupyter lab
```
Notebooks import from `src/` by adding `../src` to `sys.path`.

- `src/lineage.py` — `fetch()`, `open_meteo()`, `snotel()`, and `manifest()`. These cache raw responses and log every fetch to `data/raw/MANIFEST.csv`.
- `src/sites.py` — the single source of truth for ski areas, candidate SNOTEL stations, elements, and the date range. Log any change to it in DECISIONS.md.
- `docs/MS2_CHECKLIST.md` — every Milestone 2 requirement, where it is addressed, and its status. Keep it current.

## Layout

```
Original Proposal/   original proposal, milestone spec, staff comments (read-only; not in public repo, D-013)
docs/                DECISIONS.md, DATA_SOURCES.md, LOG.md, MS2_CHECKLIST.md
src/                 lineage.py (fetch + manifest), sites.py (locations)
data/raw/            untouched API pulls + MANIFEST.csv
data/processed/      cleaned tables
notebooks/           deliverable notebooks (01_data_source_eda, 02_cleaning, ...)
pyproject.toml, uv.lock   uv environment
```
