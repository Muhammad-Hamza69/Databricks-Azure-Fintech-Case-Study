# Databricks notebook source
import json

tables = [
    "clickstream.raw.events_raw",
    "clickstream.raw.item_properties_raw",
    "clickstream.raw.category_tree_raw",
]
counts = {t: spark.table(t).count() for t in tables}
dbutils.notebook.exit(json.dumps(counts))
