# Milestone 2 checklist

Source: `Original Proposal/Milestone 2.md`. Due **Fri 2026-11-13, 9:59 pm ET** (presentation during the week of Nov 9).
Status key: ✅ done · 🟡 in progress · ⬜ todo · N/A not applicable.

## Deliverables
| Requirement | Where | Status | Notes |
|---|---|---|---|
| 8–10 min presentation + Q&A (25 min total), every member presents | — | ⬜ | Schedule with the TF |
| Slides PDF, numbered, one point per slide, readable plots | `slides/` (to create) | ⬜ | |
| Notebook (.ipynb) that gets, loads and cleans the data | `notebooks/01_data_source_eda.ipynb`, `notebooks/02_*` (cleaning) | 🟡 | 01 is in progress. **02 (cleaning) does not exist yet.** |
| Revised proposal PDF, 1–2 pages | `docs/` (to create) | ⬜ | |
| One member uploads all three to Canvas | — | ⬜ | |

## Notebook contents (in this order)
| Requirement | Where | Status | Notes |
|---|---|---|---|
| Canvas group number + member names at the top | notebook header | ⬜ | **TODO: fill in.** Proposal author: Tomer Burstein. GitHub collaborators: MrDevel0per, mlehuray246, nxt-txms (real names not yet recorded). |
| Getting the data: code that downloads/queries | 01 §2–4 via `src/lineage.py` | 🟡 | All fetches are cached and logged in MANIFEST.csv (D-011) |
| Total data size in MB/GB | Sum of `bytes` in `data/raw/MANIFEST.csv` | ⬜ | Report in the notebook |
| What one row represents | 02 | ⬜ | Planned: one row = (resort, date *t*); target = SNWD at *t*+30 |
| What each column represents | 02 | ⬜ | Data dictionary table |
| Shape, dtypes, summary stats (mean/min/max) | 02 | ⬜ | |
| Cleaning steps, each with a reason | 02 | ⬜ | See the list below |
| Revised project question, stated so it is answerable | 02 + revised proposal | ⬜ | Depends on D-005 |
| A few labelled plots (response distribution, missingness) | 01 / 02 | 🟡 | 01 has coverage and validation plots |

## Issues to check during cleaning
| Issue | Status | What remains |
|---|---|---|
| Missing data | 🟡 | Coverage by station × winter is in 01. Still to do in 02: missingness patterns by station, winter and month; the policy (drop, interpolate short gaps, or exclude a winter) and why |
| Unusual values | ⬜ | Flag-handling policy for S/E/K and orig-vs-edited values (D-009). Physically impossible values (SNWD < SWE, negative values). Spikes (e.g. 204 in at Ivanhoe). Error or real: decide case by case and document |
| Class imbalance | N/A | Regression task. Note it, and report the target distribution instead (many near-zero values early and late in the season) |
| Feature scale | ⬜ | Range table for every numeric feature. Standardize for linear/regularized models |
| Information leakage | ⬜ | Features use only data ≤ *t*. Climatology is computed from training winters only. NRCS normals are excluded (D-010). The split is by winter, with later winters as the test set |

## Concrete cleaning work still needed (notebook 02)
- [ ] Unit conversion: inches → cm; °F → °C (SNOTEL). Open-Meteo m → cm.
- [ ] Flag policy: which qcFlag/qaFlag values to keep, and how to use `origValue`.
- [ ] Impossible values: SNWD < SWE, negative values, implausible jumps or spikes.
- [ ] Season window: Nov 1 to Apr 30, labelled by the end year.
- [ ] Date alignment between SNOTEL (`periodRef=END`) and Open-Meteo daily, checked with lag correlation (−1/0/+1 day).
- [ ] Missing-data patterns by station and winter, plus the handling policy.
- [ ] Aspen representation (D-008).
- [ ] Temperature-sensor bias (Oyler et al. 2015): prefer Open-Meteo temperature.
- [ ] Leakage audit: features ≤ *t*; climatology from training winters only.
- [ ] Scale/range table.
- [ ] Data size in MB from MANIFEST.

## Revised proposal (1–2 pages)
| Item | Status | Notes |
|---|---|---|
| Revised question, plus how and why it changed | ⬜ | Europe → US West/Aspen (D-003); target is measured SNWD (D-005) |
| Data source with link; rows × columns after cleaning | ⬜ | Open-Meteo: https://open-meteo.com/en/docs/historical-weather-api. SNOTEL: https://wcc.sc.egov.usda.gov/awdbRestApi/ |
| What we learned that changes the plan | 🟡 | `best_match` break (D-002); snow ignores elevation; no forecast hindcasts (D-004); ~⅓ of SNWD edited (D-009); SNWD record length (D-005/D-006) |
| Plan: features, models, evaluation | ⬜ | Linear regression and random forest, one model per resort (D-007); MAE/RMSE/R² against climatology and persistence |

## Staff conditions (approved, with conditions)
| Condition | How we meet it | Status |
|---|---|---|
| Name the weather source and fix the link (Meteostat → Open-Meteo) | D-001; correct link above | ✅ decided; fix in the revised proposal ⬜ |
| Keep the comparison against historical averages for the same time of year | D-004: day-of-season climatology baseline | ✅ planned |
| Test on later winters | D-006: split by winter, later winters as test | ✅ planned |
| Averages computed from training years only | D-004, D-010 (NRCS normals excluded) | ✅ planned; verify in 02 |
