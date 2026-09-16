import logging
import time
import uuid

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("producer")


def post_batch(session: requests.Session, ingest_url: str, function_key: str, source: str,
                records: list, batch_id: str, max_retries: int = 5) -> dict:
    url = f"{ingest_url.rstrip('/')}/api/ingest/{source}"
    payload = {"batch_id": batch_id, "records": records}

    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(url, params={"code": function_key}, json=payload, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code in (429, 502, 503, 504):
                log.warning("batch %s got %s, retrying in %.1fs (attempt %d/%d)",
                            batch_id, resp.status_code, delay, attempt, max_retries)
            else:
                resp.raise_for_status()
        except requests.RequestException as exc:
            log.warning("batch %s request error: %s (attempt %d/%d)", batch_id, exc, attempt, max_retries)

        time.sleep(delay)
        delay = min(delay * 2, 30)

    raise RuntimeError(f"failed to send batch {batch_id} after {max_retries} attempts")


def new_batch_id() -> str:
    return uuid.uuid4().hex[:12]
