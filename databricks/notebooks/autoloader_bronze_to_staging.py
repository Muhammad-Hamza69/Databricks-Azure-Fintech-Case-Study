# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze -> Staging: Auto Loader ingestion
# MAGIC
# MAGIC Incrementally ingests the Event Hubs Capture Avro files landed in ADLS Gen2
# MAGIC (`abfss://bronze@csbrzyp6pon7l.dfs.core.windows.net/<source>/...`) directly into
# MAGIC typed, managed Delta tables under `clickstream.staging` - one per clickstream
# MAGIC source. This is the direct sink of the streaming read: Bronze holds the files
# MAGIC exactly as captured, Staging is the first queryable Delta representation of
# MAGIC them (typed columns, no cleaning/dedup yet). Uses Auto Loader (`cloudFiles`)
# MAGIC with `trigger(availableNow=True)` so each run drains whatever new capture
# MAGIC files have shown up since the last run and then stops - safe to schedule on a
# MAGIC recurring Databricks Job instead of keeping a cluster running 24/7.
# MAGIC
# MAGIC Unity Catalog governs storage access: the external location `clickstream_bronze`
# MAGIC (backed by the `clickstream-dbx-ac` Access Connector) grants this cluster read
# MAGIC access to the bronze container with no keys or SAS tokens in this notebook.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

BRONZE_ACCOUNT = "csbrzyp6pon7l"
BRONZE_BASE = f"abfss://bronze@{BRONZE_ACCOUNT}.dfs.core.windows.net"
CATALOG = "clickstream"
CHECKPOINT_VOLUME = f"/Volumes/{CATALOG}/staging/checkpoints"

# Event Hubs Capture wraps every batch of events in an Avro envelope; the payload
# our ingest Function sent is the UTF-8 JSON string in `Body`, with every field a
# JSON string (it came from Python's csv.DictReader). Parse as all-string columns,
# then cast to real types in the same streaming write - that's the one and only
# place raw-string -> typed-column casting happens.
SOURCES = {
    "events": {
        "table": f"{CATALOG}.staging.events",
        "raw_schema": StructType([
            StructField("timestamp", StringType()),
            StructField("visitorid", StringType()),
            StructField("event", StringType()),
            StructField("itemid", StringType()),
            StructField("transactionid", StringType()),
            StructField("_ingested_at", StringType()),
            StructField("_source", StringType()),
            StructField("_batch_id", StringType()),
        ]),
        "select": lambda data: [
            data["timestamp"].cast("bigint").alias("event_epoch_ms"),
            F.timestamp_millis(data["timestamp"].cast("bigint")).alias("event_ts"),
            data["visitorid"].cast("bigint").alias("visitor_id"),
            data["event"].alias("event"),
            data["itemid"].cast("bigint").alias("item_id"),
            data["transactionid"].cast("bigint").alias("transaction_id"),
            data["_batch_id"].alias("batch_id"),
            F.to_timestamp(data["_ingested_at"]).alias("ingested_at"),
        ],
    },
    "item-properties": {
        "table": f"{CATALOG}.staging.item_properties",
        "raw_schema": StructType([
            StructField("timestamp", StringType()),
            StructField("itemid", StringType()),
            StructField("property", StringType()),
            StructField("value", StringType()),
            StructField("_ingested_at", StringType()),
            StructField("_source", StringType()),
            StructField("_batch_id", StringType()),
        ]),
        "select": lambda data: [
            data["timestamp"].cast("bigint").alias("event_epoch_ms"),
            F.timestamp_millis(data["timestamp"].cast("bigint")).alias("event_ts"),
            data["itemid"].cast("bigint").alias("item_id"),
            data["property"].alias("property"),
            data["value"].alias("value"),
            data["_batch_id"].alias("batch_id"),
            F.to_timestamp(data["_ingested_at"]).alias("ingested_at"),
        ],
    },
    "category-tree": {
        "table": f"{CATALOG}.staging.category_tree",
        "raw_schema": StructType([
            StructField("categoryid", StringType()),
            StructField("parentid", StringType()),
            StructField("_ingested_at", StringType()),
            StructField("_source", StringType()),
            StructField("_batch_id", StringType()),
        ]),
        "select": lambda data: [
            data["categoryid"].cast("bigint").alias("category_id"),
            F.nullif(data["parentid"], F.lit("")).cast("bigint").alias("parent_category_id"),
            data["_batch_id"].alias("batch_id"),
            F.to_timestamp(data["_ingested_at"]).alias("ingested_at"),
        ],
    },
}

# COMMAND ----------

def ingest_source(source: str, cfg: dict):
    source_path = f"{BRONZE_BASE}/{source}/"
    checkpoint_base = f"{CHECKPOINT_VOLUME}/{source}"

    raw = (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "avro")
        .option("cloudFiles.schemaLocation", f"{checkpoint_base}/_schema")
        .load(source_path)
    )

    data = F.from_json(F.col("Body").cast("string"), cfg["raw_schema"])
    typed = raw.select(
        *cfg["select"](data),
        F.col("EnqueuedTimeUtc").alias("eh_enqueued_time_utc"),
        F.col("SequenceNumber").alias("eh_sequence_number"),
        F.col("Offset").alias("eh_offset"),
    )

    query = (
        typed.writeStream.format("delta")
        .option("checkpointLocation", f"{checkpoint_base}/_checkpoint")
        .option("mergeSchema", "true")
        .outputMode("append")
        .trigger(availableNow=True)
        .toTable(cfg["table"])
    )
    query.awaitTermination()
    return spark.table(cfg["table"]).count()


# COMMAND ----------

for source, cfg in SOURCES.items():
    count = ingest_source(source, cfg)
    print(f"{source} -> {cfg['table']}: {count} total rows")
