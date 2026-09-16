"""
Generates *genuinely new* synthetic clickstream events with Faker, instead of replaying the
same static events.csv from row 1 every time (see run_pipeline.py's --help for why that was a
problem: repeat runs of the CSV replay never actually add new data, since events.csv is a fixed
historical file, not a live feed).

Event-type distribution (view/addtocart/transaction) matches the real dataset's observed rates
so downstream tables (Silver/Gold/ML Feature/ML Training) keep seeing realistic data, not a
degenerate distribution. Visitor and item IDs are mostly sampled from real existing IDs (so
features like "previously purchased item count" have real history to reference), with a
minority of brand-new IDs mixed in (so the pipeline sees genuinely new visitors too, not just
repeat activity on a closed set).

Usage:
    python generate_fake_events.py --count 2000 --ingest-url https://<app>.azurewebsites.net --function-key <key>
"""
import argparse
import random
import time
import uuid
from pathlib import Path

from faker import Faker

from common import log, new_batch_id, post_batch

DATA_DIR = Path(__file__).resolve().parent.parent
EVENTS_CSV = DATA_DIR / "events.csv"

# matches the real dataset's observed rates (2,664,312 view / 69,332 addtocart / 22,457
# transaction out of 2,756,102 total events) - keeps synthetic data realistic rather than
# generating a degenerate all-transactions or all-views stream
EVENT_TYPES = ["view", "addtocart", "transaction"]
EVENT_WEIGHTS = [0.9667, 0.02515, 0.00815]


def load_reference_ids(sample_size: int = 20000) -> tuple[list[str], list[str]]:
    """Sample real visitor_id/item_id values from events.csv, so synthetic events reference IDs
    that already have real history in the pipeline (existing ml_feature rows, previous
    purchases, etc.) rather than pure noise IDs with nothing to join against."""
    import csv

    visitor_ids: set[str] = set()
    item_ids: set[str] = set()
    if not EVENTS_CSV.exists():
        return [], []
    with open(EVENTS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= sample_size:
                break
            visitor_ids.add(row["visitorid"])
            item_ids.add(row["itemid"])
    return list(visitor_ids), list(item_ids)


def generate_events(
    count: int,
    visitor_pool: list[str],
    item_pool: list[str],
    new_visitor_ratio: float = 0.3,
    window_hours: float = 24.0,
) -> list[dict]:
    fake = Faker()
    now_ms = int(time.time() * 1000)
    window_ms = int(window_hours * 3600 * 1000)
    next_txn_id = random.randint(10_000_000, 99_000_000)

    rows = []
    for _ in range(count):
        if not visitor_pool or random.random() < new_visitor_ratio:
            visitor_id = str(fake.random_int(min=1, max=1_500_000))
        else:
            visitor_id = random.choice(visitor_pool)

        item_id = random.choice(item_pool) if item_pool else str(fake.random_int(min=1, max=470_000))
        event = random.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]
        # spread across the trailing window rather than all at exactly "now", to simulate a
        # trickle of live activity rather than one synchronous burst
        timestamp = now_ms - random.randint(0, window_ms)

        transaction_id = ""
        if event == "transaction":
            transaction_id = str(next_txn_id)
            next_txn_id += 1

        rows.append({
            "timestamp": str(timestamp),
            "visitorid": visitor_id,
            "event": event,
            "itemid": item_id,
            "transactionid": transaction_id,
        })
    return rows


def generate_and_ingest(
    count: int,
    ingest_url: str,
    function_key: str,
    batch_size: int = 250,
    new_visitor_ratio: float = 0.3,
) -> int:
    """Generates `count` fake events and posts them to the ingest Function. Returns the number
    of rows actually sent."""
    import requests

    visitor_pool, item_pool = load_reference_ids()
    log.info("reference pool: %d visitor_ids, %d item_ids sampled from events.csv",
              len(visitor_pool), len(item_pool))

    rows = generate_events(count, visitor_pool, item_pool, new_visitor_ratio=new_visitor_ratio)
    n_transactions = sum(1 for r in rows if r["event"] == "transaction")
    log.info("generated %d synthetic events (%d view, %d addtocart, %d transaction)",
              len(rows), sum(1 for r in rows if r["event"] == "view"),
              sum(1 for r in rows if r["event"] == "addtocart"), n_transactions)

    session = requests.Session()
    total_sent = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        batch_id = new_batch_id()
        result = post_batch(session, ingest_url, function_key, "events", batch, batch_id)
        total_sent += len(batch)
        log.info("batch=%s rows=%d total_sent=%d eventhub=%s", batch_id, len(batch), total_sent, result.get("eventhub"))
    return total_sent


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=2000, help="Number of synthetic events to generate (default 2000)")
    parser.add_argument("--ingest-url", required=True)
    parser.add_argument("--function-key", required=True)
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--new-visitor-ratio", type=float, default=0.3,
                         help="Fraction of events from brand-new visitor IDs vs. existing ones (default 0.3)")
    args = parser.parse_args()

    total = generate_and_ingest(
        args.count, args.ingest_url, args.function_key,
        batch_size=args.batch_size, new_visitor_ratio=args.new_visitor_ratio,
    )
    log.info("done: sent %d synthetic events", total)


if __name__ == "__main__":
    main()
