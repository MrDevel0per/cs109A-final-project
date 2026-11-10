# SnowPredict correctness and requirements audit

Audited **2026-11-09 ET**, starting from commit `419d753542206cacfc7660f722de9ea69a9d35e1` and a clean working tree.
Scope: all eight `src/*.py` modules, the prefetch script, all four test modules, every source cell in all four notebooks,
their executed outputs, the processed tables and dictionaries, raw-data integrity, project documentation, staff comments,
the original proposal, and the Milestone 2 specification. This is a correctness and scientific-method review, not a dedicated security scan.

## Assessment

The existing pipeline reproduces its results exactly and gets the central date, composite, label, and baseline calculations right.
**The project is not submission-ready, and its end-to-end causal/untouched-test claims are stronger than the evidence supports.**
The most valuable next work is to finish the submission, correct feature availability and evaluation practice, and simplify the feature set.
More data sources or more model families would not resolve the identified problems.

**Milestone boundary:** trained models, model tuning, final model comparisons and robustness model experiments are **not Milestone 2 requirements**.
The specification explicitly places EDA and a baseline model in Milestone 3. For Milestone 2, explain the data/cleaning limitations and planned
remedies, state the revised question, and finish the notebook, slides PDF and revised proposal PDF. The model-related findings below are safeguards
for subsequent work, not a request to train models before submitting Milestone 2.

### Verification completed

| Check | Observed result |
|---|---|
| Existing offline tests | **64 passed** |
| `src/verify_raw.py` | **135 cached files, 0 problems** |
| Fresh kernels, with `SNOWPREDICT_OFFLINE=1` | **All four notebooks passed**, in order 01 → 01b → 02 → 03 |
| Rebuilt processed outputs | **All six files byte-identical** to the originals, including both parquet tables and `baseline_scores.csv` |
| Station table / modelling table | **285,778 × 49 / 14,319 × 61** |
| Unique resort/issue-date keys | No duplicates |
| Label accounting | **14,231 non-null labels**, with imputed targets excluded |
| Dictionaries | Both match their corresponding saved table columns, without duplicate entries |

Fresh execution used copied source, tests and notebooks, a link to the existing raw cache, and separate processed/figure directories under a temporary project.
The original raw data, tables, figures and numerical notebook outputs were not overwritten. Notebook 01b's subprocess outputs also confirmed
24 parser/lineage tests passed and the integrity check passed. A successful notebook execution alone would not prove those subprocesses passed.

## Findings that should drive the next work

### A-01 — High: the designated test set has already been examined and scored

**Evidence:** notebook 03 §3.2 and §6 plot and rank test-winter targets; §7 computes test baseline errors, plots errors by target month,
and overlays individual test winters; §7.1 explicitly fits an illustrative climatology including test winters. The closing paragraph uses
the test errors to frame the next modelling task. D-032 says the test set is touched once after choices are frozen; D-035 records its scores.

The ordinary climatology scores correctly exclude test winters from fitting. The separate leaky illustration is clearly labelled and is not
the reported proper baseline. **This finding does not mean those baseline arithmetic results are invalid.** It means 2021–2026 can no longer
be represented as an unseen test set: its performance and outcomes are already known, and there is still modelling and feature selection to do.
The revised question's generalization claim needs this qualification.

**Smallest useful remedy:** keep the fixed calendar split, disclose the previous exploratory access, freeze the modelling protocol now,
and make every subsequent model/feature choice using development winters only. Remove further test scoring from ordinary development runs
or gate it behind an explicit final-evaluation option. Do not repeatedly move the split to obtain better results or claim deleting plots restores blindness.
A future truly prospective winter can be an optional independent confirmation; it is not needed to complete this course project.

### A-02 — High: the accepted short-gap fill is not causal as a transformation

**Location:** `src/clean.py::ffill_short_gaps`, lines 69–83; `tests/test_clean.py::test_ffill_is_causal_in_values`; notebook 02 §6.

For `[5, NaN, NaN, 7]`, full-series processing returns `[5, 5, 5, 7]`. Processing the prefix available on the third day returns
`[5, NaN, NaN]`, because that gap is still trailing. If the future gap instead continues past three days, those same past dates also remain missing.
The values used for a fill are historical, but **both availability and imputation flags reveal future missingness**. The current causality test
changes future numerical values while keeping their presence unchanged, so it cannot detect this failure.

Notebook 03 already acknowledges this caveat and counts 48 affected SNWD/WTEQ station-values across its four stations and Oct–Apr period.
That is not a bound on downstream affected feature rows: a filled state also enters 7/30-day changes and potentially a season peak.
There is no completed model experiment establishing the effect on error is negligible.

**Smallest useful remedy:** use a forward fill limited by elapsed days since the last observation, including the first three days of a longer gap,
or use no imputation for model inputs. Keeping long gaps entirely empty while filling their early days only if they later end is incompatible
with issue-date availability. Retain the non-imputed label mask. Add a prefix-invariance test and a test changing future missingness, and rebuild
the tables if the policy changes. D-038 proposes this correction without changing the accepted D-022 entry.

**Related limit:** the centered spike and whole-run stuck-sensor rules also use future data. The real-data audit correctly finds zero centered
SNWD/WTEQ spike removals in the relevant four-station Oct–Apr period, and the temperature columns are not model features. Do not describe the
whole cleaning library as causal, even though this particular centered filter did not remove relevant snow-state rows in the audited period.

### A-03 — High before operational claims: the proposed originals robustness run leaves revised inputs in place

**Location:** `src/modeltable.py::resort_snotel`, lines 106–118, and `build_features`, lines 171–204; notebook 03 §9.

Only three originals features exist: `rob_snwd_t`, `rob_d_snwd_7`, `rob_d_snwd_30`. Replacing the corresponding main columns, as §9 proposes,
still leaves `snwd_peak_wy` derived from revised depth; `wteq_t`, both SWE changes and `wteq_peak_wy` derived from revised SWE;
and both `prcp_sum_*` features derived from revised station precipitation. The primary features also inherit the gap-selection issue above.
A forecast can recover hindsight information through those remaining variables.

The robustness *inputs* have been built; **the model robustness experiment has not been implemented or scored**. The checklist previously described
post-hoc edits as already checked by a robustness run, which conflated these stages.

**Smallest useful remedy:** define the robustness feature list explicitly. Rebuild every retained SNOTEL-derived state and history from original
readings with causal QC, or omit the unreconstructed columns from that experiment. Recompute the original-depth season peak as well.
Compare primary and robustness models/baselines on a common measured-target set and report coverage separately. Distinguish retraining on originals
from simply substituting originals into a model trained on edited inputs; they answer different questions.

Day-t reanalysis is also unavailable on day t: Open-Meteo documents a five-day update delay for both pinned products.
The planned weather-lag sensitivity is still needed before any real-time claim. Apply the lag to every weather-derived feature, including
ERA5-Land depth and season totals, with an explicit definition at the Oct 1 reset. This remains a hindcast even after a lag, because this repository
does not contain historical as-of release snapshots. [Open-Meteo documentation](https://open-meteo.com/en/docs/historical-weather-api).

### A-04 — High before model comparison: complete cases discard the entire Aspen 2021 winter

**Evidence:** the saved modelling table has 1,087 baseline-eligible Aspen test rows, but only **906** complete-main-feature rows. Every one of the
**181** rows from winter **2021** is incomplete because of the two station precipitation windows. Validation loses another **49** rows in winter 2020.
There is currently no final ML score, so no unfair model-versus-baseline comparison has yet been reported.

| Resort | Baseline-eligible rows, all splits | Complete main features | Complete after omitting `prcp_sum_7`, `prcp_sum_30` |
|---|---:|---:|---:|
| Aspen | 4,036 | 3,747 | **3,977** |
| Brighton | 5,251 | 5,221 | 5,221 |
| Heavenly | 4,894 | 4,894 | 4,894 |

**Recommendation:** omit those two station precipitation features from the initial models. Open-Meteo precipitation already supplies both windows;
the reduction restores **230 Aspen rows**, including all of winter 2021, without adding an imputer or another data source. Retain the columns in the
provenance table if useful. Make this a coverage-driven decision, not a choice based on test errors. D-040 records the proposal.

When comparing models, re-score all baselines on the exact same eligible resort/date keys as that model, or define one common comparison set in
advance. Report full-coverage baseline scores separately. Otherwise apparent skill could reflect dropping an entire winter.

### A-05 — High for Milestone 2: required submission artifacts are missing

No slides PDF or revised proposal PDF exists. Four analytical notebooks exist, but the submitted notebook/package has not been chosen.
The specification asks for one coherent progression: get data → understand it → clean it → state the revised question. Notebook 02 ends with a
decision table, not an explicit revised question; notebook 03's last paragraph frames the question indirectly. Add a final standalone question cell
to the chosen submission notebook. Keep detailed probes and modelling EDA as supporting material.

The initial audit also found notebook 01b still said `Canvas project group: TODO / Members: TODO` despite the checklist marking all headers done.
**That header is fixed in this audit.** The README's outdated Palisades choice is also fixed.

The due time is **November 13, 2026 at 9:59 pm ET, or the start of the presentation if earlier**. The presentation booking, equal participation,
member responsibilities, and Canvas upload cannot be confirmed from the repository. The revised proposal must explicitly address all four staff
conditions and the changed geography, target and interpretation. See `Original Proposal/Milestone 2.md` and `Staff Comments.txt`.

## Smaller corrections and safeguards

### A-06 — Medium: integrity failures can be printed without stopping execution

`lineage.fetch` and `lineage_text.fetch_text` return an existing cache file without checking that it has a matching manifest row/hash.
A reproduced offline call successfully loaded a fabricated unlogged cache file. Offline mode prevents network access; it does not establish provenance.
Notebook 02 §1 prints the SHA checks but does not assert they pass. Notebook 01b's test and integrity subprocesses print output without checking
return codes. Notebook 03's raw weather hash assertions are stronger, but its clean parquet hash is only printed.

The audited cache is intact; this is a fail-open safeguard defect, not evidence of corrupted current results. A simple integrity gate before
downstream execution, an assertion for notebook 02's hashes, and `check=True`/return-code assertions for subprocesses are sufficient.
There is no need for a new data-platform dependency.

### A-07 — Medium for the final tuning implementation: inner ridge tuning is not winter-grouped

Notebook 03 §6.1 wraps `StandardScaler` and `RidgeCV(alphas=...)` in an outer `GroupKFold`. The **outer evaluation** is held out by winter and is
valid for that fitted procedure. However, the inner `RidgeCV` uses its default leave-one-out/generalized CV, not winter folds, and defaults to
an MSE criterion. Scaling is also outside that inner tuning step. Thus it is not an implementation of the promised fully winter-grouped,
MAE-driven hyperparameter procedure. The shuffled comparison remains a diagnostic, not the final modelling method.

For Milestone 3, use a small `Ridge` pipeline with a winter-aware parameter search, putting scaling inside each fold; prefer expanding windows
when the claim concerns prediction into later winters. Tune on the declared development pool and keep a consistent account of whether validation
is an untouched selection window or part of the CV pool. A small grid is enough. No broad model search is warranted.

### A-08 — Medium interpretation issue: some “measured” labels are NRCS estimates

`snwd_measured` means present and not filled by this project; it does not exclude NRCS `K` (estimate) flags. The target joins contain **16 Aspen
test station-days** flagged K (not necessarily 16 distinct composite dates), and **6 Brighton target station-days** (4 train, 1 validation, 1 test).
Heavenly has none. Notebook 03 explains this definition, and D-016 explicitly retains NRCS estimates, so it is not a hidden implementation discrepancy.
Nevertheless, “independently measured truth” is too strong for these rows. Keep the definition visible and report an optional sensitivity excluding
K targets if claiming accuracy against strictly measured observations. Edited E observations do not automatically need exclusion.

### A-09 — Low: filling can reintroduce physical inconsistencies after the checks

Across the full candidate clean table, post-fill checks find **7** depth<SWE rows with SWE ≥1 inch, **4** TMIN>TMAX rows, and **73** TAVG-outside-range
rows using the notebook's ±1 °F tolerance. All seven depth<SWE rows have imputed SNWD and are outside the final four stations; they cannot be
evaluation labels under the existing mask. SNOTEL temperatures are not final model features. This is not a current primary-label corruption.

Re-check joint constraints after filling, flag the inconsistent fills, and avoid advertising the whole clean table as satisfying every constraint.
Do not add more elaborate imputation to repair a handful of unused candidate rows.

### A-10 — Low: weather composites silently change membership if a member becomes missing

`resort_weather`, lines 126–128, uses a group mean that skips NaNs. A two-station temperature example `[0, 0]` and `[10, NaN]` yields `[5, 0]`;
the second day changes to a single-station estimate. All currently cached weather inputs are complete, so this does not affect current outputs.
Require all expected member values or fail on incompleteness to preserve the intended fixed composite on future inputs.

### Documentation claims to tighten

- A similar mean snow depth before gaps does not establish missing-at-random or prove dropping rows is unbiased. Keep the comparison as a descriptive check.
- “Random forests are unaffected by collinearity” is too broad: they can predict with redundant columns, but feature importance is diluted and the
  extra columns still increase search/noise. Prune exact duplicates; do not promise identifiable importances.
- Remove `target_dowy` from model predictors; it duplicates `dowy + 30` and is needed only for climatology lookup. Notebook 03's current `BASE` still includes it.
- Leap winters shift the water-year day after February by one. The code documents this; it is a small deliberate approximation for climatology,
  not a 30-day target alignment error. Keep the caveat; a more elaborate seasonal calendar is low priority.
- D-036 says future requests pass `cell_selection=land`, but `station_request` still omits it. Updating request parameters changes cache keys, so do
  not casually force a re-download of all historical chunks. Preserve the recorded requests and address explicit defaults in the next fetch revision.
- The checklist's data volume, fetch count, and log count were stale. Current cache: **163.09 MB**, **135 cached files**, **142 manifest rows**;
  the 20 daily SNOTEL files alone total **147.88 MB**; the cleaning log has **40 entries**. Those quantities have different denominators.
- The original station-choice exploration uses default elevation and `best_match` intentionally as comparison probes, and 01b's START/END probe
  omits two production flags. The production feature and SNOTEL extraction requests use the required conventions. Label the controlled probes as
  exceptions rather than making an unqualified “every request” claim.

## Requirements verdict

| Requirement | Verdict |
|---|---|
| Weather source Open-Meteo, correct link | Implemented/documented; required revised proposal is still missing |
| Historical seasonal-average comparison | Implemented correctly; mean climatology retained |
| Later winters for evaluation | Implemented; lack of test blindness must be disclosed (A-01) |
| Climatology fitted without evaluation winters | Pass for proper baselines; train for validation, train+validation for final test |
| Cache raw unchanged, record lineage | Current integrity passes; fail-open checks need tightening (A-06) |
| Explicit model/elevation, SNOTEL flags, no NRCS normals | Production requests pass; diagnostic probes are documented exceptions |
| Fixed Aspen composite | Pass for SNOTEL and current complete weather inputs |
| Features dated ≤t | Pass conditional on cleaned inputs; end-to-end availability fails strict causality (A-02/A-03) |
| Non-imputed evaluation truth | Project-filled targets excluded; NRCS estimate qualification in A-08 |
| Group metadata, size, dictionary, cleaning reasons | Present; 01b header corrected, stale counts corrected in checklist |
| Explicit revised question in ordered submission notebook | Incomplete |
| Slides PDF and 1–2-page revised proposal PDF | Missing |
| Presentation, equal speaking time, roles, upload | External/manual requirements, unverified |
| Final ridge/random forest results | Not yet implemented; **not required for Milestone 2**, whose spec puts EDA/baselines in Milestone 3 |

## Recommended scope

**Keep:** three resorts, one model per resort, measured-depth primary outcome, ridge and random forest, MAE with RMSE/bias, the three simple
baselines (mean climatology, persistence, persistence + seasonal change), causal input checks, and the existing cached dataset.

**For Milestone 2:** finish one clear submission notebook and the two PDFs; explain the cleaning and availability caveats and the planned evaluation.
No model training is needed for this milestone.

**For Milestone 3:** correct the causal-input policy; freeze and disclose the evaluation protocol; omit redundant station precipitation windows;
implement the two model families with small winter-aware searches; compare on identical rows.
Add per-winter/per-month errors and a simple weather ablation (snow state + calendar versus plus weather) to show whether the required weather
source adds predictive value. If uncertainty is reported, resample whole winters and describe the small number of seasons, rather than treating
daily errors as independent observations. These are Milestone 3 tasks, not reasons to delay the Milestone 2 package.

**Defer:** back-to-1980 SWE→density depth reconstruction and the two-stage model. They add estimated training targets, another fitted model,
and more leakage controls to a project with only 13–19 initial training winters per resort. The primary question is already answerable without them.
Do not add live seasonal-forecast collection, more resorts, a dashboard, or another model family now.

Keep any condition index a clearly labelled secondary illustration. Day-t sun, wind and temperature cannot be presented as weather at t+30;
using realized future weather would leak the outcome period. A simple depth-based indicator is safer until future-weather components are actually
predicted. Staff approval conditions do not require the density extension; changes to the broader proposal should be explained in the revised proposal.

## Changes made during this audit

Only the 01b group header, README, checklist and audit documentation were edited. Numerical code, splits, raw data, processed tables and figures
were left unchanged. Proposed remediation/scope decisions are D-038–D-041; none was marked ACCEPTED. Reproducible data checks are recorded in
`DATA_SOURCES.md` §8, and the session is recorded in `LOG.md`.
