import json
import logging
import os
from datetime import datetime, timezone

import azure.functions as func
from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import DefaultAzureCredential

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

EVENTHUB_FQDN = os.environ.get("EVENTHUB_FQDN")

# source (URL segment) -> event hub name, resolved from app settings so the
# Function code never hard-codes infra names.
SOURCE_TO_EVENTHUB = {
    "events": os.environ.get("EVENTHUB_EVENTS_NAME", "events"),
    "item-properties": os.environ.get("EVENTHUB_ITEM_PROPERTIES_NAME", "item-properties"),
    "category-tree": os.environ.get("EVENTHUB_CATEGORY_TREE_NAME", "category-tree"),
}

_credential = None
_producer_clients: dict[str, EventHubProducerClient] = {}


def _get_producer(eventhub_name: str) -> EventHubProducerClient:
    # Cache producer clients across warm invocations of the same worker instead
    # of reconnecting to Event Hubs on every request.
    global _credential
    if eventhub_name not in _producer_clients:
        if _credential is None:
            _credential = DefaultAzureCredential()
        _producer_clients[eventhub_name] = EventHubProducerClient(
            fully_qualified_namespace=EVENTHUB_FQDN,
            eventhub_name=eventhub_name,
            credential=_credential,
        )
    return _producer_clients[eventhub_name]


@app.route(route="ingest/{source}", methods=["POST"])
def ingest(req: func.HttpRequest) -> func.HttpResponse:
    source = req.route_params.get("source")
    eventhub_name = SOURCE_TO_EVENTHUB.get(source)
    if eventhub_name is None:
        return func.HttpResponse(
            json.dumps({"error": f"unknown source '{source}', expected one of {list(SOURCE_TO_EVENTHUB)}"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "request body must be JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    records = body.get("records")
    if not isinstance(records, list) or not records:
        return func.HttpResponse(
            json.dumps({"error": "body must contain a non-empty 'records' array"}),
            status_code=400,
            mimetype="application/json",
        )

    ingested_at = datetime.now(timezone.utc).isoformat()
    batch_id = body.get("batch_id")

    producer = _get_producer(eventhub_name)
    batches_sent = 0
    events_sent = 0
    try:
        event_batch = producer.create_batch()
        for record in records:
            record["_ingested_at"] = ingested_at
            record["_source"] = source
            if batch_id:
                record["_batch_id"] = batch_id

            event_data = EventData(json.dumps(record))
            try:
                event_batch.add(event_data)
            except ValueError:
                # current batch is full - flush it and start a new one
                producer.send_batch(event_batch)
                batches_sent += 1
                event_batch = producer.create_batch()
                event_batch.add(event_data)
            events_sent += 1

        if len(event_batch) > 0:
            producer.send_batch(event_batch)
            batches_sent += 1
    except Exception:
        logging.exception("failed sending batch to event hub '%s'", eventhub_name)
        return func.HttpResponse(
            json.dumps({"error": "failed to send to Event Hub"}),
            status_code=502,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps({
            "source": source,
            "eventhub": eventhub_name,
            "records_received": len(records),
            "events_sent": events_sent,
            "eventhub_batches": batches_sent,
        }),
        status_code=200,
        mimetype="application/json",
    )
