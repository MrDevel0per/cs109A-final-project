# Work log

## 2026-11-09 — Session 1: data-source exploration
**Done**
- Read the original proposal, the Milestone 2 spec and the staff comments. Recorded the staff constraints in AGENTS.md.
- Probed the Open-Meteo archive API: compared models (best_match, era5, era5_land, era5_seamless, ecmwf_ifs, cerra), date coverage, the effect of the elevation parameter, and which variables are available.
- Probed the other Open-Meteo APIs (seasonal, historical-forecast, previous-runs, climate).
- Found NRCS SNOTEL as a ground-truth source. Inventoried stations near ski resorts and near Aspen, and counted the usable winters for each.
- First validation: Open-Meteo vs SNOTEL at Independence Pass.

**Learned** (details in DATA_SOURCES.md)
- `best_match` has a model switch in 2017, so we must pin models (D-002).
- Reanalysis snow depth ignores the elevation parameter.
- No historical 30-day forecast exists to benchmark against (D-004).
- SNOTEL has about 20 winters of snow depth and 40+ of SWE and temperature at Aspen-area stations. ERA5-Land snow depth tracks Independence Pass with r = 0.94 but runs about 21% low.

**Created:** AGENTS.md, CLAUDE.md (imports AGENTS.md), docs/DATA_SOURCES.md, docs/DECISIONS.md (D-001…D-004), docs/LOG.md.
Throwaway probe outputs were in the session scratchpad, not the repo. The queries needed to reproduce every finding are recorded in DATA_SOURCES.md.

**Next** (as of the end of session 1)
- Group decides D-003 and Q1–Q4.
- Write the fetch script/notebook section: Open-Meteo (pinned models) plus SNOTEL for the chosen sites, cached to data/raw/.

## 2026-11-09 — Session 2: decisions + lineage infrastructure
**User decisions this session**
- Target: leaning toward SNOTEL measured snow depth (SNWD) as ground truth, but "not sure" → D-005 (PROPOSED).
- Use as many winters as possible → D-006 (ACCEPTED).
- Separate models, maybe 3 resorts → D-007 (separate models accepted; resort choice proposed).
- Aspen treated as one resort → D-003 ACCEPTED. How to represent it → D-008 (open).
- Data lineage is crucial: track absolutely everything → D-011.
- Public GitHub repo MrDevel0per/cs109A-final-project, with collaborators mlehuray246 and nxt-txms → D-013.
- Use subagents where helpful.

**Done**
- `src/lineage.py`: cached, manifest-logged fetching. Raw bytes are stored unmodified; 429/5xx responses are logged but not cached.
- `src/sites.py`: ski-area reference points, 20 candidate SNOTEL stations, elements, and date range.
- uv environment (`pyproject.toml`, `uv.lock`, Python 3.12) → D-012.
- Investigated SNOTEL flags. Found that `returnSuspectData` defaults to false (a hidden filter), found the `origValue` field, and found the official flag definitions → D-009. NRCS normals are excluded → D-010.
- Corrected DATA_SOURCES: Open-Meteo has daily `snow_depth_mean`/`snow_depth_max`.
- Added the SNOTEL temperature-sensor bias caveat (Oyler et al. 2015).
- Created `docs/MS2_CHECKLIST.md`, which maps every MS2 requirement to its status.
- In progress: `notebooks/01_data_source_eda.ipynb`, which reproduces every session-1 probe as notebook code.

**Next**
- Finish notebook 01.
- Settle D-005, D-007 and D-008 with evidence from 01.
- Start notebook 02 (cleaning). See the checklist.
