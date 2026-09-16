# Running the full pipeline with one command

`run_pipeline.py` chains the 4-5 manual steps into one command:

```
python run_pipeline.py --count 2000 --function-key <key>
```

## What it does, in order

1. **Ingest** - generates `--count` genuinely new synthetic events with Faker
   (`producer/generate_fake_events.py`) -> Azure Function -> Event Hubs -> ADLS Gen2 Bronze.
   `events.csv` is a fixed historical file, not a live feed - replaying it just re-sends the
   same rows every run, which Silver's dedup then filters right back out, so nothing new
   actually reaches ML Training. Faker generation instead samples real visitor/item IDs from
   `events.csv` (so features like "previously purchased item count" still have real history to
   reference) and generates new events matching the real dataset's event-type distribution
   (96.67% view / 2.52% addtocart / 0.82% transaction), mixing in ~30% brand-new visitor IDs.
   Every run adds real new rows. The old CSV-replay behavior is still available via
   `--replay-csv` (see Options below).
2. **Trigger Auto Loader** (Bronze -> `clickstream.staging`), waits for it to finish
3. **`dbt run` + `dbt test`** (Staging -> Silver -> Gold -> ML Feature -> ML Training) - all 12 models, all 25 tests
4. **Trigger model training** (10-candidate comparison + isotonic calibration), waits for it to finish, registers a new version of `clickstream.ml_models.purchase_propensity`
5. **Fivetran -> Salesforce sync** - optional, see below
6. **Restart the Streamlit UI** - kills any existing process on the target port and launches a fresh one in the background, so it's guaranteed to load the model version just registered in step 4 (see "Why Streamlit restarts" below)

## Verified

Ran end-to-end on 2026-08-27 with `--max-rows 2000 --rate 500` (old replay-based flow at the
time): steps 1-4 completed successfully (step 5 skipped, not requested), 12/12 dbt models
built, 25/25 tests passed, new model registered as version 9, independently verified to give
the same sensible predictions as the manually-run version 7. Total runtime: **38.4 minutes**
(mostly step 4 - the model training job spins up its own cluster and trains 10 candidates plus
a 5-fold calibration refit).

The Faker-based generator itself (`producer/generate_fake_events.py`) was separately verified
with a live `--count 100` run against the real Function endpoint (100/100 events accepted,
realistic 97/2/1 view/addtocart/transaction split).

## Requirements

- `databricks` CLI on PATH, authenticated (`DATABRICKS_AUTH_TYPE=azure-cli`, i.e. logged in via `az login`)
- `dbt` installed (`pip install -r dbt/requirements.txt`)
- `DATABRICKS_TOKEN` env var set to a PAT - dbt needs this even though the `databricks` CLI itself uses azure-cli auth
- A Function key for the ingest endpoint (`--function-key`, or set `INGEST_FUNCTION_KEY`)

### `.env` file (no more manual `export` every session)

`run_pipeline.py` auto-loads a `.env` file from the repo root at startup (see `load_dotenv()`
near the top of the script) - any `KEY=VALUE` line in it becomes an env var, without overriding
a real env var you already set. `.env` is gitignored, so secrets never live in tracked source.

Create `.env` at the repo root:
```
DATABRICKS_TOKEN=<a PAT>
INGEST_FUNCTION_KEY=<the function key>
```

Get a PAT (Databricks PATs expire - this project uses long-lived ones, e.g. 90 days, to avoid
regenerating every session):
```
databricks tokens create --comment "pipeline" --lifetime-seconds 7776000
```

Get the Function key:
```
az functionapp keys list --name clickstream-func-yp6pon7lzod3o --resource-group rg-clickstream-bronze
```

Once `.env` has both values, plain `python run_pipeline.py` works with no flags and no `export`
- until the PAT's 90-day lifetime runs out, at which point regenerate it and update `.env`.

## Options

| Flag | What it does |
|---|---|
| `--count N` | Number of new synthetic (Faker) events to generate (default 2000) |
| `--replay-csv` | Use the old behavior: replay real `events.csv` instead of generating new data |
| `--max-rows N` | [`--replay-csv` only] Cap replayed rows (omit for the full 2.75M-row file - takes hours) |
| `--rate N` | [`--replay-csv` only] Ingestion rate, rows/sec (default 500) |
| `--skip-ingestion` | Skip step 1, re-run steps 2-4 on whatever's already in Bronze |
| `--skip-training` | Skip step 4 - training runs every time by default (like steps 1-3), so the registered model always reflects the latest ingested data |
| `--trigger-fivetran` | Attempt step 5 - see below |
| `--skip-streamlit` | Skip step 6 - Streamlit restarts every run by default, so the UI always reflects the just-registered model |
| `--streamlit-port N` | Port to run the Streamlit UI on (default 8501) |

## Why Streamlit restarts every run (`step_streamlit`)

The model load in `streamlit_app/app.py` is wrapped in `@st.cache_resource` with no `ttl` - once
a Streamlit process loads a model version, it keeps serving that exact version forever, even
after a newer one is registered. If step 6 just launched Streamlit without checking for an
existing instance, re-running the pipeline would silently leave the UI showing stale
predictions from the *previous* model version.

So `step_streamlit`:
1. Finds and force-kills whatever's already listening on `--streamlit-port` (`netstat` + `taskkill`, Windows-only, best-effort - fine if nothing was running).
2. Launches a fresh `streamlit run streamlit_app/app.py` in the background (`subprocess.Popen`, detached - it keeps running after `run_pipeline.py` exits), logging to `streamlit_app/streamlit.log`.
3. Prints the URL (`http://localhost:<port>`) - open it yourself, the script doesn't launch a browser.

Verified live on 2026-08-27: ran `step_streamlit(8501)` against an already-running instance,
confirmed it killed the old PID and a new process was listening on 8501 within a few seconds.

## Fivetran step (`--trigger-fivetran`)

**Not verified against a live Fivetran API key in this project** - included as a best-effort,
clearly-documented placeholder, not a tested integration. Without credentials it's skipped with
a message; the Fivetran -> Salesforce sync still runs independently on its own daily schedule
(09:00 UTC) regardless of whether this script triggers it.

To actually enable on-demand triggering, three env vars are needed:
- `FIVETRAN_API_KEY` / `FIVETRAN_API_SECRET` - from Fivetran account settings (Basic Auth to their REST API)
- `FIVETRAN_SYNC_ID` - the Activation sync's resource ID

The script calls `POST https://api.fivetran.com/v1/connectors/{sync_id}/force`, which is
Fivetran's documented endpoint for standard Connectors - **Activations (reverse ETL) may use a
different endpoint shape**, since it's a newer, separate product line, and this was never
tested against a real key. **Test this step manually and confirm it actually triggers a sync in
the Fivetran UI before relying on it** - if the endpoint is wrong, the script will report a
clear warning and continue (it does not fail the whole pipeline), but it also won't have
actually triggered anything.
