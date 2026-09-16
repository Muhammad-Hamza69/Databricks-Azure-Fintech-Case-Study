"""
Simulated clickstream producer.

Reads the raw source CSVs (events.csv, item_properties_part1.csv, category_tree.csv)
and replays them as a live stream against the ingestion Function App, which forwards
each batch to the matching Event Hub. Event Hubs Capture then lands the raw data in
ADLS Gen2 under the 'bronze' container - this script never talks to storage directly,
matching the Data Sources -> Python Scripts -> Azure Function -> Event Hub -> ADLS Gen2
architecture.

Usage:
    python stream_clickstream.py --source events --ingest-url https://<app>.azurewebsites.net --function-key <key>
    python stream_clickstream.py --source item-properties --max-rows 5000 --rate 20
    python stream_clickstream.py --source category-tree --ingest-url ... --function-key ...

--max-rows caps how many rows are replayed (omit for the full file).
--rate is the target rows/second for the simulated stream (batches are paced to hit it).
--batch-size is how many rows are sent per HTTP call to the Function (Event Hub is a
batching service, so the Function fans a batch out to Event Hub in one call).
"""
import argparse
import csv
import math
import time
from pathlib import Path

import requests

from common import log, new_batch_id, post_batch

DATA_DIR = Path(__file__).resolve().parent.parent

SOURCE_CONFIG = {
    "events": {
        "file": DATA_DIR / "events.csv",
        "columns": ["timestamp", "visitorid", "event", "itemid", "transactionid"],
    },
    "item-properties": {
        "file": DATA_DIR / "item_properties_part1.csv",
        "columns": ["timestamp", "itemid", "property", "value"],
    },
    "category-tree": {
        "file": DATA_DIR / "category_tree.csv",
        "columns": ["categoryid", "parentid"],
    },
}


def row_stream(path: Path, max_rows: int | None):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_rows is not None and i >= max_rows:
                return
            yield row


def chunked(iterable, size):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def main():
    parser = argparse.ArgumentParser(description="Replay clickstream CSVs through the ingest Function into Event Hubs")
    parser.add_argument("--source", required=True, choices=list(SOURCE_CONFIG))
    parser.add_argument("--ingest-url", required=True, help="Function App base URL, e.g. https://clickstream-func-xxx.azurewebsites.net")
    parser.add_argument("--function-key", required=True, help="Function key for the ingest endpoint")
    parser.add_argument("--max-rows", type=int, default=None, help="Cap the number of rows replayed (default: whole file)")
    parser.add_argument("--batch-size", type=int, default=250, help="Rows per HTTP call to the Function")
    parser.add_argument("--rate", type=float, default=200.0, help="Target rows/second for the simulated stream")
    args = parser.parse_args()

    cfg = SOURCE_CONFIG[args.source]
    if not cfg["file"].exists():
        raise SystemExit(f"source file not found: {cfg['file']}")

    batch_interval = args.batch_size / args.rate if args.rate > 0 else 0

    session = requests.Session()
    total_rows = 0
    total_batches = 0
    start = time.monotonic()

    for batch in chunked(row_stream(cfg["file"], args.max_rows), args.batch_size):
        batch_start = time.monotonic()
        batch_id = new_batch_id()

        result = post_batch(session, args.ingest_url, args.function_key, args.source, batch, batch_id)

        total_rows += len(batch)
        total_batches += 1
        log.info("source=%s batch=%s rows=%d total_rows=%d eventhub=%s",
                  args.source, batch_id, len(batch), total_rows, result.get("eventhub"))

        elapsed = time.monotonic() - batch_start
        sleep_for = batch_interval - elapsed
        if sleep_for > 0:
            time.sleep(sleep_for)

    duration = time.monotonic() - start
    log.info("done: source=%s total_rows=%d total_batches=%d duration=%.1fs (%.1f rows/s)",
              args.source, total_rows, total_batches, duration,
              total_rows / duration if duration > 0 else math.inf)


if __name__ == "__main__":
    main()
