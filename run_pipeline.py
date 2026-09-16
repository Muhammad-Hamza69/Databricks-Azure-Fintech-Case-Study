#!/usr/bin/env python
"""
Orchestrates the full clickstream pipeline end-to-end, one command instead of six manual
steps in six different tools:

    1. Generate genuinely new synthetic events with Faker -> Azure Function -> Event Hubs ->
       ADLS Gen2 Bronze (producer/generate_fake_events.py). events.csv is a fixed historical
       file, not a live feed - replaying it just re-sends the same rows every run, which Silver
       then dedupes right back out. Faker generation means every run actually adds new data.
    2. Trigger the Auto Loader job (Bronze -> Staging), wait for it to finish
    3. dbt run + dbt test (Staging -> Silver -> Gold -> ML Feature -> ML Training)
    4. Trigger the model training job, wait for it to finish
    5. (optional, best-effort) Trigger the Fivetran -> Salesforce sync
    6. Restart the Streamlit UI in the background, so it loads the just-registered model
       (st.cache_resource has no TTL on the model load, so a Streamlit instance already
       running would keep serving a stale model version otherwise - see step_streamlit())

Usage:
    python run_pipeline.py                                 # generates 2000 fake events (default)
    python run_pipeline.py --count 10000                    # generate more fake events
    python run_pipeline.py --replay-csv --max-rows 2000     # old behavior: replay real
                                                              # events.csv instead of generating
    python run_pipeline.py --replay-csv                     # replay the full 2.75M-row file
                                                              # (takes ~1-3 hours)
    python run_pipeline.py --skip-ingestion                  # re-run steps 2-4 only, on whatever
                                                              # is already in Bronze
    python run_pipeline.py --trigger-fivetran                # also attempt step 5 (needs
                                                              # FIVETRAN_API_KEY / FIVETRAN_API_SECRET
                                                              # / FIVETRAN_SYNC_ID env vars)
    python run_pipeline.py --skip-streamlit                  # skip step 6, leave Streamlit alone

Requires on PATH (or at the default install location this repo used):
    - the `databricks` CLI, authenticated (this repo used `DATABRICKS_AUTH_TYPE=azure-cli`)
    - `dbt` (installed via `pip install -r dbt/requirements.txt`)
    - DATABRICKS_TOKEN env var set (a PAT - dbt needs this even though the CLI itself can use
      azure-cli auth)
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def load_dotenv(path: Path) -> None:
    """Minimal .env loader - populates os.environ from KEY=VALUE lines so DATABRICKS_TOKEN and
    INGEST_FUNCTION_KEY don't need to be `export`-ed by hand every terminal session. Real env
    vars already set take priority (never overwritten). The .env file itself is gitignored -
    secrets live there, never hardcoded in this script."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv(REPO_ROOT / ".env")

DATABRICKS_HOST = "https://adb-7405616477706025.5.azuredatabricks.net"
AUTOLOADER_JOB_ID = "614669053635065"
TRAIN_JOB_SPEC = REPO_ROOT / "databricks" / "jobs" / "train_purchase_propensity_submit.json"
INGEST_URL = "https://clickstream-func-yp6pon7lzod3o.azurewebsites.net"
POLL_SECONDS = 15


def log(msg: str) -> None:
    print(f"[run_pipeline] {msg}", flush=True)


def find_databricks_cli() -> str:
    found = shutil.which("databricks")
    if found:
        return found
    fallback = Path.home() / "databricks-cli" / "databricks.exe"
    if fallback.exists():
        return str(fallback)
    sys.exit("ERROR: 'databricks' CLI not found on PATH and not at the expected fallback location.")


DATABRICKS = find_databricks_cli()


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    log(f"$ {' '.join(cmd)}")
    env = {**os.environ, "DATABRICKS_HOST": DATABRICKS_HOST, "DATABRICKS_AUTH_TYPE": "azure-cli"}
    result = subprocess.run(cmd, env=env, text=True, capture_output=True, **kwargs)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(f"ERROR: command failed with exit code {result.returncode}")
    return result


def wait_for_run(run_id: str, label: str) -> None:
    log(f"Waiting for {label} (run_id={run_id})...")
    while True:
        result = subprocess.run(
            [DATABRICKS, "jobs", "get-run", run_id, "-o", "json"],
            env={**os.environ, "DATABRICKS_HOST": DATABRICKS_HOST, "DATABRICKS_AUTH_TYPE": "azure-cli"},
            text=True, capture_output=True,
        )
        stdout = "\n".join(
            line for line in result.stdout.splitlines() if "Databricks skills" not in line
        )
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            log(f"  (transient poll error, retrying) {result.stdout[:200]}")
            time.sleep(POLL_SECONDS)
            continue

        state = data.get("state", {})
        life_cycle = state.get("life_cycle_state")
        if life_cycle == "TERMINATED":
            result_state = state.get("result_state")
            if result_state == "SUCCESS":
                log(f"{label}: SUCCESS")
                return
            sys.exit(f"ERROR: {label} finished with result_state={result_state}: {state.get('state_message')}")
        if life_cycle in ("SKIPPED", "INTERNAL_ERROR"):
            sys.exit(f"ERROR: {label} failed - life_cycle_state={life_cycle}")
        log(f"  {label}: {life_cycle}...")
        time.sleep(POLL_SECONDS)


def step_ingestion(count: int, function_key: str) -> None:
    log(f"STEP 1/6: Generating {count} new synthetic events with Faker -> Function -> Event Hubs -> Bronze")
    cmd = [
        sys.executable, str(REPO_ROOT / "producer" / "generate_fake_events.py"),
        "--count", str(count),
        "--ingest-url", INGEST_URL,
        "--function-key", function_key,
    ]
    result = subprocess.run(cmd, cwd=str(REPO_ROOT / "producer"), text=True)
    if result.returncode != 0:
        sys.exit(f"ERROR: ingestion failed with exit code {result.returncode}")


def step_ingestion_replay(max_rows: int | None, rate: float, function_key: str) -> None:
    log("STEP 1/6: Ingesting events.csv -> Function -> Event Hubs -> Bronze (replay mode)")
    cmd = [
        sys.executable, str(REPO_ROOT / "producer" / "stream_clickstream.py"),
        "--source", "events",
        "--ingest-url", INGEST_URL,
        "--function-key", function_key,
        "--rate", str(rate),
    ]
    if max_rows is not None:
        cmd += ["--max-rows", str(max_rows)]
    result = subprocess.run(cmd, cwd=str(REPO_ROOT / "producer"), text=True)
    if result.returncode != 0:
        sys.exit(f"ERROR: ingestion failed with exit code {result.returncode}")


def step_autoloader() -> None:
    log("STEP 2/6: Triggering Auto Loader job (Bronze -> Staging)")
    result = run([DATABRICKS, "jobs", "run-now", AUTOLOADER_JOB_ID, "--no-wait", "-o", "json"])
    stdout = "\n".join(l for l in result.stdout.splitlines() if "Databricks skills" not in l)
    run_id = str(json.loads(stdout)["run_id"])
    wait_for_run(run_id, "Auto Loader (Bronze -> Staging)")


def step_dbt() -> None:
    log("STEP 3/6: dbt run + dbt test (Staging -> Silver -> Gold -> ML Feature -> ML Training)")
    dbt_dir = REPO_ROOT / "dbt"
    if "DATABRICKS_TOKEN" not in os.environ:
        sys.exit("ERROR: DATABRICKS_TOKEN env var is required for dbt (a PAT - see dbt/profiles.yml)")
    for cmd in (["dbt", "run", "--profiles-dir", "."], ["dbt", "test", "--profiles-dir", "."]):
        result = subprocess.run(cmd, cwd=str(dbt_dir), text=True)
        if result.returncode != 0:
            sys.exit(f"ERROR: '{' '.join(cmd)}' failed with exit code {result.returncode}")


def step_train() -> None:
    log("STEP 4/6: Triggering model training job (retrains + registers a new model version)")
    result = run([
        DATABRICKS, "jobs", "submit", "--no-wait", "-o", "json",
        "--json", f"@{TRAIN_JOB_SPEC}",
    ])
    stdout = "\n".join(l for l in result.stdout.splitlines() if "Databricks skills" not in l)
    run_id = str(json.loads(stdout)["run_id"])
    wait_for_run(run_id, "Model training")


def step_fivetran() -> None:
    log("STEP 5/6: Fivetran -> Salesforce sync")
    api_key = os.environ.get("FIVETRAN_API_KEY")
    api_secret = os.environ.get("FIVETRAN_API_SECRET")
    sync_id = os.environ.get("FIVETRAN_SYNC_ID")
    if not (api_key and api_secret and sync_id):
        log(
            "  Skipped - FIVETRAN_API_KEY / FIVETRAN_API_SECRET / FIVETRAN_SYNC_ID not set. "
            "The sync still runs on its own daily schedule independently of this script; "
            "set those env vars to trigger it on demand here instead. NOTE: this project never "
            "verified Fivetran's Activations-specific trigger endpoint against a live API key - "
            "test this step manually the first time before relying on it."
        )
        return
    import base64
    import urllib.request

    auth = base64.b64encode(f"{api_key}:{api_secret}".encode()).decode()
    req = urllib.request.Request(
        f"https://api.fivetran.com/v1/connectors/{sync_id}/force",
        method="POST",
        headers={"Authorization": f"Basic {auth}"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            log(f"  Fivetran trigger response: {resp.status} {resp.read().decode()}")
    except Exception as e:
        log(f"  WARNING: Fivetran trigger failed ({e}) - sync will still run on its daily schedule.")


STREAMLIT_APP = REPO_ROOT / "streamlit_app" / "app.py"


def kill_process_on_port(port: int) -> None:
    """Best-effort (Windows): kill whatever's already listening on `port`, so a fresh
    Streamlit instance can bind there. Needed because Streamlit caches the loaded model with
    @st.cache_resource and no ttl (see streamlit_app/app.py) - an already-running instance
    would keep serving a stale model version instead of the one step_train() just registered."""
    try:
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        pids = set()
        for line in result.stdout.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                pid = line.split()[-1]
                if pid.isdigit():
                    pids.add(pid)
        for pid in pids:
            subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, text=True)
            log(f"  Killed existing process on port {port} (PID {pid})")
    except Exception as e:
        log(f"  (couldn't check/kill existing process on port {port}: {e})")


def step_streamlit(port: int) -> None:
    log(f"STEP 6/6: Restarting Streamlit UI on port {port} (fresh instance picks up the new model)")
    kill_process_on_port(port)
    log_path = REPO_ROOT / "streamlit_app" / "streamlit.log"
    log_file = open(log_path, "w", encoding="utf-8")
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    # streamlit_app/app.py reads DATABRICKS_HOST/DATABRICKS_TOKEN from its own process env - a
    # bare Popen() only inherits os.environ, which never actually has DATABRICKS_HOST set (it's
    # just a Python constant here, only injected into ad-hoc env dicts for `databricks` CLI
    # calls elsewhere in this script), so it must be added explicitly here.
    env = {**os.environ, "DATABRICKS_HOST": DATABRICKS_HOST}
    subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(STREAMLIT_APP),
         "--server.port", str(port), "--server.headless", "true"],
        cwd=str(REPO_ROOT / "streamlit_app"),
        stdout=log_file, stderr=subprocess.STDOUT,
        creationflags=creationflags, env=env,
    )
    log(f"  Streamlit launching in background -> http://localhost:{port}  (logs: {log_path})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=2000,
                         help="Number of new synthetic events to generate with Faker (default 2000)")
    parser.add_argument("--replay-csv", action="store_true",
                         help="Old behavior: replay real events.csv instead of generating new Faker data")
    parser.add_argument("--max-rows", type=int, default=None,
                         help="[--replay-csv only] Cap replayed rows (default: full file)")
    parser.add_argument("--rate", type=float, default=500.0,
                         help="[--replay-csv only] Ingestion rate, rows/sec (default 500)")
    parser.add_argument("--function-key", default=os.environ.get("INGEST_FUNCTION_KEY"),
                         help="Function key for the ingest endpoint (or set INGEST_FUNCTION_KEY)")
    parser.add_argument("--skip-ingestion", action="store_true", help="Skip step 1, start from Auto Loader")
    parser.add_argument("--skip-training", action="store_true",
                         help="Skip step 4 (model training) - training runs every time by default, "
                              "same as steps 1-3, so the registered model always reflects the latest data.")
    parser.add_argument("--trigger-fivetran", action="store_true", help="Attempt step 5 (Fivetran sync)")
    parser.add_argument("--skip-streamlit", action="store_true",
                         help="Skip step 6 - Streamlit restarts every run by default, so the UI "
                              "always reflects the just-registered model.")
    parser.add_argument("--streamlit-port", type=int, default=8501,
                         help="Port to run the Streamlit UI on (default 8501)")
    args = parser.parse_args()

    start = time.monotonic()

    if not args.skip_ingestion:
        if not args.function_key:
            sys.exit("ERROR: --function-key or INGEST_FUNCTION_KEY env var required (or pass --skip-ingestion)")
        if args.replay_csv:
            step_ingestion_replay(args.max_rows, args.rate, args.function_key)
        else:
            step_ingestion(args.count, args.function_key)
    else:
        log("STEP 1/6: SKIPPED (--skip-ingestion)")

    step_autoloader()
    step_dbt()

    if not args.skip_training:
        step_train()
    else:
        log("STEP 4/6: SKIPPED (--skip-training)")

    if args.trigger_fivetran:
        step_fivetran()
    else:
        log("STEP 5/6: SKIPPED (pass --trigger-fivetran to attempt it; runs on its own daily schedule regardless)")

    if not args.skip_streamlit:
        step_streamlit(args.streamlit_port)
    else:
        log("STEP 6/6: SKIPPED (--skip-streamlit)")

    elapsed = time.monotonic() - start
    log(f"Pipeline complete in {elapsed / 60:.1f} minutes.")


if __name__ == "__main__":
    main()
