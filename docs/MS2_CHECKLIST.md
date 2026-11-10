# Milestone 2 checklist

Source: `Original Proposal/Milestone 2.md`. Due **Fri 2026-11-13, 9:59 pm ET** (presentation during the week of Nov 9).
Status key: ✅ done · 🟡 in progress · ⬜ todo · N/A not applicable. Last updated 2026-11-10.

**Group 37:** Nat Toms, Owen Cruz-Abrams, Martha le Huray.

## Deliverables
| Requirement | Where | Status | Notes |
|---|---|---|---|
| 8–10 min presentation + Q&A (25 min total), every member presents | — | ⬜ | Schedule with the TF. Split speaking time roughly equally |
| Slides PDF, numbered, one point per slide, readable plots | `slides/` (to create) | ⬜ | |
| Notebook (.ipynb) that gets, loads and cleans the data | `notebooks/01_data_source_eda.ipynb`, `01b_source_verification.ipynb`, `02_cleaning_snotel.ipynb`, `03_modelling_table.ipynb` | 🟡 | All four run clean. Still to do: decide whether to submit four notebooks or one combined notebook; fresh-kernel rerun |
| Revised proposal PDF, 1–2 pages | `docs/` (to create) | ⬜ | |
| One member uploads all three to Canvas | — | ⬜ | |

## Notebook contents (in this order)
| Requirement | Where | Status | Notes |
|---|---|---|---|
| Canvas group number + member names at the top | notebook headers | ✅ | Group 37: Nat Toms, Owen Cruz-Abrams, Martha le Huray, in the headers of notebooks 01, 01b and 02 |
| Getting the data: code that downloads/queries | 01 §1–3 via `src/lineage.py` | ✅ | All fetches are cached and logged in MANIFEST.csv (D-011), with an honest User-Agent (D-014) |
| Total data size in MB/GB | 01 §6; 02 §1 | ✅ | 157.5 MB raw JSON (81 requests); SNOTEL 148.5 MB for the 20 stations |
| What one row represents | 02, 03 §5 | ✅ | Clean table: one row = (SNOTEL station, date). Modelling table (`data/processed/model_table.parquet`, 14,319 × 61): one row = (resort, issue date *t*); target = measured SNWD at *t*+30, with the target date in Nov–Apr (D-029) |
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
| Feature scale | ✅ | 02 §9 (SNOTEL) and 03 §8.2 (all 54 features, training winters). Scalers will be fit on training rows only, inside the CV pipeline |
| Information leakage | ✅ | 03 §4.2: truncation and future-perturbation audit on real data (max |Δ| = 0); 03 §4.3: every non-causal upstream step quantified; 03 §6.1: a random split flatters the error by 15–24 % (D-033); unit tests in `tests/test_modeltable.py`. 02 §10. Causal imputation (D-022); climatology from training winters only; NRCS normals excluded (D-010); PREC reset handled; post-hoc NRCS edits (D-024) checked with a robustness run on raw readings |

## Remaining work
- [x] Open-Meteo feature fetch for the 3 resorts, plus quality checks (03 §1–2; D-030, D-036). Done 2026-11-10.
- [x] Aspen composite, modelling table, split by winter (D-032), baselines (D-035). Done 2026-11-10 in notebook 03.
- [ ] Group review of D-029 to D-037 (PROPOSED). The split and baseline definitions are the ones TFs will ask about.
- [x] Re-run notebook 01b §3b (the Open-Meteo temperature daily-vs-hourly check). Done 2026-11-10. Daily `temperature_2m_mean` = local-day mean of hourly values: max |diff| 0.071 °C, 100 % within 0.1 °C, 80–86 % within 0.05 °C. The UTC-day mean agrees on only 4–5 % of days. The residual is a constant +0.02 °C precision bias (DATA_SOURCES §5).
- [x] Put the group number and names in every notebook header.
- [ ] Restart and run every notebook top to bottom (fresh kernel) before submitting.
- [ ] Slides (PDF, numbered).
- [ ] Revised proposal PDF (1–2 pages).

## Revised proposal (1–2 pages)
| Item | Status | Notes |
|---|---|---|
| Revised question, plus how and why it changed | 🟡 | Wording above. Europe → US West/Aspen (D-003); target is measured SNWD (D-005); 3 resorts (D-007); ski-condition index kept as a secondary output (D-026) |
| Data source with link; rows × columns after cleaning | 🟡 | Open-Meteo: https://open-meteo.com/en/docs/historical-weather-api. SNOTEL: https://wcc.sc.egov.usda.gov/awdbRestApi/. Clean SNOTEL table 285,778 × 49. Modelling table 14,319 × 61 (54 features; 14,231 measured labels; 13,862 complete-case rows) |
| What we learned that changes the plan | ✅ | `best_match` break (D-002); snow ignores elevation; no forecast hindcasts (D-004); ~⅓ of values edited by NRCS (D-009/D-024); SNWD record length (D-005/D-006); ERA5-Land depth biased low (−4 % to −59 %) |
| Plan: features, models, evaluation | 🟡 | Regularised linear regression (ridge/lasso) and random forest, one model per resort (D-007, D-035), tuned with winter-grouped CV (D-033). MAE/RMSE/bias against climatology, persistence, and persistence + climatological change. Test MAE (cm) to beat: Aspen 11.3, Brighton 23.3, Heavenly 31.5. Robustness runs: NRCS originals (D-024/D-037) and weather lagged 5 days (D-034). Optional SWE→density two-stage model (D-026) |

## Staff conditions (approved, with conditions)
| Condition | How we meet it | Status |
|---|---|---|
| Name the weather source and fix the link (Meteostat → Open-Meteo) | D-001; correct link above | ✅ decided; fix in the revised proposal ⬜ |
| Keep the comparison against historical averages for the same time of year | D-004, D-035: day-of-season climatology baseline | ✅ implemented (03 §7) |
| Test on later winters | D-032: train ≤ 2016, validation 2017–2020, test 2021–2026 | ✅ implemented (03 §6) |
| Averages computed from training years only | D-004, D-010, D-035: `modeltable.climatology` drops every non-training winter before computing (unit test poisons the test winters) | ✅ implemented (03 §7) |
