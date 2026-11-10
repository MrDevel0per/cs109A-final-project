# SnowPredict

**Can machine learning predict ski-resort snow depth 30 days ahead more accurately than historical averages for
the same time of year?** CS1090A final project.

- **Weather inputs:** [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
  (ERA5 / ERA5-Land reanalysis; model pinned, see `docs/DECISIONS.md` D-002).
- **Ground truth:** measured snow depth from [NRCS SNOTEL](https://www.nrcs.usda.gov/resources/data-and-reports/snow-and-climate-monitoring-predictive-tools)
  stations on or near the resorts, via the [AWDB REST API](https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html).
- **Resorts:** Aspen CO (fixed Kiln + Brumley composite), Brighton UT, and Heavenly CA (Sierra, lee side of Tahoe).
- **Evaluation:** models are trained on earlier winters and tested on later ones. The climatology baseline is computed from the training winters only.

## Run it

```bash
uv sync                               # Python 3.12 environment from pyproject.toml / uv.lock
uv run jupyter lab                    # open notebooks/
uv run pytest -q                     # offline unit tests
uv run python src/verify_raw.py       # check data/raw is byte-identical to what was downloaded
```

The notebooks read cached raw data from `data/raw/`. Set `SNOWPREDICT_OFFLINE=1` to prevent downloads;
notebooks 02 and 03 set this themselves. Run notebooks in order: 01, 01b, 02, then 03.
The target is station-measured depth near each resort; it does not measure groomed piste conditions or skiing quality.

## Data lineage

Every external request goes through `src/lineage.py`, which:
- stores the response body unmodified in `data/raw/`,
- logs the URL, time, size, SHA-256, HTTP status and User-Agent in `data/raw/MANIFEST.csv`,
- identifies itself with an honest User-Agent that points back to this repo.

## Where things are documented

| File | What's in it |
|---|---|
| `docs/DECISIONS.md` | every project decision: options, rationale, evidence, status |
| `docs/DATA_SOURCES.md` | what each API provides, quirks we found, and reproducible queries |
| `docs/MS2_CHECKLIST.md` | Milestone 2 requirements, where each is met, and its status |
| `docs/LOG.md` | dated work log |
| `docs/CODE_AUDIT.md` | correctness audit, requirement gaps, and recommended simplifications |
| `AGENTS.md` | working rules for humans and AI assistants in this repo |
| `notebooks/01_data_source_eda.ipynb` | reproduces every data-source check behind the decisions |
| `notebooks/01b_source_verification.ipynb` | independent parser and date-alignment checks |
| `notebooks/02_cleaning_snotel.ipynb` | cleaning, provenance, and the clean station table |
| `notebooks/03_modelling_table.ipynb` | features, labels, winter split, and exploratory baselines |
