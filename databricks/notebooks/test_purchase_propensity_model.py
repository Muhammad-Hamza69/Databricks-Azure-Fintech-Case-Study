# Databricks notebook source
# MAGIC %md
# MAGIC # Manual test: clickstream.ml_models.purchase_propensity
# MAGIC
# MAGIC Loads the registered model from Unity Catalog and scores it against:
# MAGIC 1. A handful of real rows pulled from the training table (known label), to sanity-check
# MAGIC    predictions against ground truth.
# MAGIC 2. A few hand-built synthetic examples (clearly-engaged visitor vs. clearly-not) to check
# MAGIC    the model's predicted probability moves in the right direction.

# COMMAND ----------

import mlflow
import pandas as pd

mlflow.set_registry_uri("databricks-uc")
MODEL_URI = "models:/clickstream.ml_models.purchase_propensity/1"

model = mlflow.pyfunc.load_model(MODEL_URI)
print(f"Loaded {MODEL_URI}")

# COMMAND ----------

# MAGIC %md ## 1. Score real rows (with known labels) from the training table

# COMMAND ----------

real_examples = spark.sql("""
    select view_count, addtocart_count, days_since_last_interaction,
           item_category_id, item_is_available, label_purchased
    from clickstream.ml_training.ml_training_purchase_propensity
    order by rand()
    limit 10
""").toPandas()

feature_cols = ["view_count", "addtocart_count", "days_since_last_interaction",
                 "item_category_id", "item_is_available"]

X_real = real_examples[feature_cols].copy()
X_real["item_is_available"] = X_real["item_is_available"].fillna(False).astype(int)
X_real["item_category_id"] = X_real["item_category_id"].fillna(-1)
X_real["days_since_last_interaction"] = X_real["days_since_last_interaction"].fillna(0)

real_examples["predicted_label"] = model.predict(X_real)
print(real_examples.to_string(index=False))

# COMMAND ----------

# MAGIC %md ## 2. Score hand-built synthetic examples

# COMMAND ----------

synthetic = pd.DataFrame([
    # clearly engaged: many views, recent add-to-cart -> expect higher propensity
    {"view_count": 12, "addtocart_count": 2, "days_since_last_interaction": 0,
     "item_category_id": 1204, "item_is_available": 1},
    # single stale view, no cart activity -> expect lower propensity
    {"view_count": 1, "addtocart_count": 0, "days_since_last_interaction": 30,
     "item_category_id": 1204, "item_is_available": 1},
    # moderate engagement, item unavailable
    {"view_count": 4, "addtocart_count": 1, "days_since_last_interaction": 3,
     "item_category_id": 442, "item_is_available": 0},
])
# match the model's logged input schema exactly (pandas defaults ints to int64/float64,
# but the training data - via Spark - produced int32 days_since_last_interaction and
# float64 item_category_id)
synthetic["days_since_last_interaction"] = synthetic["days_since_last_interaction"].astype("int32")
synthetic["item_category_id"] = synthetic["item_category_id"].astype("float64")

predictions = model.predict(synthetic)
synthetic["predicted_label"] = predictions
print(synthetic.to_string(index=False))

# also print raw probabilities where the underlying sklearn model supports it
try:
    sk_model = mlflow.sklearn.load_model(MODEL_URI)
    proba = sk_model.predict_proba(synthetic[feature_cols])[:, 1]
    synthetic["purchase_probability"] = proba
    print("\nWith probabilities:")
    print(synthetic.to_string(index=False))
except Exception as e:
    print(f"Could not load raw sklearn probabilities: {e}")
