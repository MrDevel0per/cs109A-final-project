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

**Next** (as of the end of session 2)
- Finish notebook 01.
- Settle D-005, D-007 and D-008 with evidence from 01.
- Start notebook 02 (cleaning). See the checklist.

## 2026-11-10 — Session 3: EDA results, verification, cleaning, final site choices
**Done**
- **Notebook 01 executed in full** (81 requests, 157.5 MB raw). Findings in §7:
  - The `best_match` break is exact: 100 % ERA5-Land through 2016, 100 % IFS from 2017.
  - ERA5-Land depth r 0.85–0.96 vs SNOTEL, biased low by −4 % to −59 %.
  - SNOTEL date *t* lines up with Open-Meteo day *t*+1.
  - Palisades' usable SNWD starts in 2003, not 1998 (D-007 corrected).
- **Honest User-Agent** (D-014). The manifest now has a `user_agent` column, back-filled with the exact legacy UA. Raw data is committed to git (D-015).
- **Verification fork → notebook 01b + tests:**
  - Our AWDB parser matches the independent NRCS Report Generator CSV 100 % (PREC 99.73 %), with 0 unexplained mismatches.
  - SNWD dated *d* is the end-of-day-*d* reading. PREC resets each Oct 1.
  - Open-Meteo daily values are local-day aggregates when `timezone=auto` is set.
  - The temperature version of that check is pending (hourly rate limit).
  - Added `src/lineage_text.py`; `verify_raw` now scans all file types.
- **Cleaning fork → notebook 02 + `src/clean.py`:** 39 logged rules (D-016 to D-025). The first draft's two-sided linear interpolation was replaced by a **causal forward fill** (D-022), with a causality unit test. 32 tests pass.
- Offline mode (`SNOWPREDICT_OFFLINE=1`) for downstream notebooks.
- Commits: `7909c97` (scaffolding), `5d80831` (notebook 01 + raw data).

**User decisions this session**
- D-005 ACCEPTED: measured SNWD is the primary target.
- The user asked about estimating both depth and SWE, or a two-pass model with a quality score. That became D-026 (PROPOSED): depth = SWE / density, plus the ski-condition index as a secondary output.
- D-008 ACCEPTED: Aspen = Kiln + Brumley, 2004–2026 (the only complete Aspen-area stations).
- D-007 ACCEPTED: maritime slot = "the one with the best data" → Heavenly (27 winters, r 0.955). Final resorts: Aspen, Brighton, Heavenly.
- D-013 ACCEPTED: `Original Proposal/` stays out of the public repo.
- Group 37: Nat Toms, Owen Cruz-Abrams, Martha le Huray.

**Next**
- Open-Meteo feature fetch for the 3 resorts, then the modelling table.
- Group names in every notebook header; re-run 01b §3b; fresh-kernel run of all notebooks.
- Slides and the revised proposal. See MS2_CHECKLIST.md.

## 2026-11-10 — Session 3b: Open-Meteo feature download, robustness
- The feature download was blocked by Open-Meteo's **hourly** limit, which notebook 01's run had exhausted. Trimmed ERA5 to 10 variables (D-027) to cut the cost from about 7,300 to about 6,000 calls.
- Made collection disconnect- and crash-safe (D-028): atomic writes, network retries, an unattended prefetch that sleeps through rate limits, and a detached `nohup caffeinate` run. 37 tests pass.
- Check progress with `tail data/prefetch_features.log`. Restart (safe at any time) with `caffeinate -i nohup uv run python scripts/prefetch_features.py >> data/prefetch_features.log 2>&1 &`.
- **Download complete (2026-11-10 01:12Z).** After one hourly-limit wait (00:50→01:02Z) it fetched all 4 stations (Kiln, Brumley, Brighton, Heavenly) in about 10 minutes. Each station has 10,592 days (1997-07-01 to 2026-06-30) × 14 variables and 0 NaN cells. That is 48 raw chunk files, 4.0 MB. `verify_raw`: 133 files, 0 problems. 37 tests pass. My estimate of a spill past the daily reset was too pessimistic.
- Next: notebook 03 (modelling table, offline).
