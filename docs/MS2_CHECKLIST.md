# Milestone 2 checklist

Source: `Original Proposal/Milestone 2.md`. Due **Fri 2026-11-13, 9:59 pm ET** (presentation during the week of Nov 9).
Status key: ✅ done · 🟡 in progress · ⬜ todo · N/A not applicable. Last updated 2026-11-10.

**Group 37:** Nat Toms, Owen Cruz-Abrams, Martha le Huray.

## Deliverables
| Requirement | Where | Status | Notes |
|---|---|---|---|
| 8–10 min presentation + Q&A (25 min total), every member presents | — | ⬜ | Schedule with the TF. Split speaking time roughly equally |
| Slides PDF, numbered, one point per slide, readable plots | `slides/` (to create) | ⬜ | |
| Notebook (.ipynb) that gets, loads and cleans the data | `notebooks/01_data_source_eda.ipynb`, `01b_source_verification.ipynb`, `02_cleaning_snotel.ipynb` | 🟡 | All three run clean. Still to do: an Open-Meteo feature fetch + clean for the 3 resorts; possibly merge into one submission notebook |
| Revised proposal PDF, 1–2 pages | `docs/` (to create) | ⬜ | |
| One member uploads all three to Canvas | — | ⬜ | |

## Notebook contents (in this order)
| Requirement | Where | Status | Notes |
|---|---|---|---|
| Canvas group number + member names at the top | notebook headers | ✅ | Group 37: Nat Toms, Owen Cruz-Abrams, Martha le Huray, in the headers of notebooks 01, 01b and 02 |
| Getting the data: code that downloads/queries | 01 §1–3 via `src/lineage.py` | ✅ | All fetches are cached and logged in MANIFEST.csv (D-011), with an honest User-Agent (D-014) |
| Total data size in MB/GB | 01 §6; 02 §1 | ✅ | 157.5 MB raw JSON (81 requests); SNOTEL 148.5 MB for the 20 stations |
| What one row represents | 02 | ✅ | Clean table: one row = (SNOTEL station, date). The modelling table will have one row = (resort, date *t*), target = SNWD at *t*+30 |
| What each column represents | 02 + `data/processed/snotel_clean_columns.csv` | ✅ | Data dictionary |
| Shape, dtypes, summary stats (mean/min/max) | 02 | ✅ | 285,778 × 49 |
| Cleaning steps, each with a reason | 02 + `data/processed/cleaning_log.csv` | ✅ | 39 logged rules (D-016 to D-025) |
| Revised project question, stated so it is answerable | 02 / revised proposal | 🟡 | Proposed wording below |
| A few labelled plots (response distribution, missingness) | 01, 02 | ✅ | Coverage heatmaps, validation, missingness heatmap, spikes before/after, target distribution |

### Proposed revised question
> For three ski areas in distinct snow climates (Aspen CO, using the Kiln + Brumley SNOTEL composite; Brighton UT; and Heavenly CA), can a
> model using only information available on day *t* predict SNOTEL-measured snow depth on day *t*+30 (Nov–Apr) with lower MAE
> than (a) a day-of-season climatology computed from training winters only and (b) persistence, on held-out later winters?

## Issues to check during cleaning
| Issue | Status | Where / result |
|---|---|---|
| Missing data | ✅ | 02 §3, §6. SNWD is 40.5 % NaN, but 39.8 % is before the sensor was installed. Missing while installed: 1.19 % (0.75 % after a causal ≤3-day fill). Gaps cluster in each sensor's first winters (2003–2010), are mostly NRCS S removals, and do not depend on depth (D-022) |
| Unusual values | ✅ | 02 §4–5: flag policy and physical rules for spikes, density, summer noise, negatives and temperature (D-016 to D-021), each with counts |
| Class imbalance | N/A | Regression task. 02 §8 reports the target distribution instead: 84,261 usable target station-days, 2.5 % zeros, skew 1.07 |
| Feature scale | ✅ (SNOTEL) / ⬜ (Open-Meteo) | 02 §9 range table. Scalers will be fit on training winters only |
| Information leakage | ✅ | 02 §10. Causal imputation (D-022); climatology from training winters only; NRCS normals excluded (D-010); PREC reset handled; post-hoc NRCS edits (D-024) checked with a robustness run on raw readings |

## Remaining work
- [ ] Open-Meteo feature fetch for the 3 resorts (ERA5 + ERA5-Land, pinned models, station lat/lon/elevation, `timezone=auto`), plus cleaning and range table.
- [ ] Build the Aspen composite (Kiln + Brumley, both present) and the modelling table (resort, *t*, target = SNWD at *t*+30). Align dates: SNWD dated *d* is the end-of-day-*d* reading.
- [ ] Re-run notebook 01b §3b (the Open-Meteo temperature daily-vs-hourly check, blocked by the hourly rate limit).
- [x] Put the group number and names in every notebook header.
- [ ] Restart and run every notebook top to bottom (fresh kernel) before submitting.
- [ ] Slides (PDF, numbered).
- [ ] Revised proposal PDF (1–2 pages).

## Revised proposal (1–2 pages)
| Item | Status | Notes |
|---|---|---|
| Revised question, plus how and why it changed | 🟡 | Wording above. Europe → US West/Aspen (D-003); target is measured SNWD (D-005); 3 resorts (D-007); ski-condition index kept as a secondary output (D-026) |
| Data source with link; rows × columns after cleaning | 🟡 | Open-Meteo: https://open-meteo.com/en/docs/historical-weather-api. SNOTEL: https://wcc.sc.egov.usda.gov/awdbRestApi/. Clean SNOTEL table 285,778 × 49. The modelling table is still to build |
| What we learned that changes the plan | ✅ | `best_match` break (D-002); snow ignores elevation; no forecast hindcasts (D-004); ~⅓ of values edited by NRCS (D-009/D-024); SNWD record length (D-005/D-006); ERA5-Land depth biased low (−4 % to −59 %) |
| Plan: features, models, evaluation | 🟡 | Linear regression and random forest, one model per resort (D-007); MAE/RMSE/R² against climatology and persistence; optional SWE→density two-stage model (D-026) |

## Staff conditions (approved, with conditions)
| Condition | How we meet it | Status |
|---|---|---|
| Name the weather source and fix the link (Meteostat → Open-Meteo) | D-001; correct link above | ✅ decided; fix in the revised proposal ⬜ |
| Keep the comparison against historical averages for the same time of year | D-004: day-of-season climatology baseline | ✅ planned |
| Test on later winters | D-006: split by winter, later winters as test | ✅ planned |
| Averages computed from training years only | D-004, D-010 (NRCS normals excluded); D-026's density model is also fit on training winters only | ✅ planned; enforce in modelling |
