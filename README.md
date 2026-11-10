# SnowPredict

**Can machine learning predict ski-resort snow depth 30 days ahead more accurately than historical averages for
the same time of year?** CS1090A final project.

- **Weather inputs:** [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
  (ERA5 / ERA5-Land reanalysis; model pinned, see `docs/DECISIONS.md` D-002).
- **Ground truth:** measured snow depth from [NRCS SNOTEL](https://www.nrcs.usda.gov/resources/data-and-reports/snow-and-climate-monitoring-predictive-tools)
  stations on or near the resorts, via the [AWDB REST API](https://wcc.sc.egov.usda.gov/awdbRestApi/swagger-ui/index.html).
- **Resorts:** Aspen (treated as one resort), plus two contrasting snow climates (proposed: Brighton UT and Palisades Tahoe CA).
- **Evaluation:** models are trained on earlier winters and tested on later ones. The climatology baseline is computed from the training winters only.

## Run it

```bash
uv sync                               # Python 3.12 environment from pyproject.toml / uv.lock
uv run jupyter lab                    # open notebooks/
uv run python src/verify_raw.py       # check data/raw is byte-identical to what was downloaded
```

The notebooks read cached raw data from `data/raw/`, so they run offline. Delete a raw file to re-download it.

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
| `AGENTS.md` | working rules for humans and AI assistants in this repo |
| `notebooks/01_data_source_eda.ipynb` | reproduces every data-source check behind the decisions |
