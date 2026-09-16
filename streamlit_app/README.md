# Purchase Propensity - Streamlit app

A UI that scores real (visitor, item) interactions against `clickstream.ml_models.purchase_propensity`
(the registered Unity Catalog model) and shows who's most likely to convert, ranked - instead of
running a notebook every time you want this.

## Run it

```
cd streamlit_app
pip install -r requirements.txt

export DATABRICKS_HOST=adb-7405616477706025.5.azuredatabricks.net
export DATABRICKS_TOKEN=<personal access token>   # databricks tokens create --comment "streamlit" --lifetime-seconds 7776000

streamlit run app.py
```

On PowerShell, set the env vars with `$env:DATABRICKS_HOST = "..."` / `$env:DATABRICKS_TOKEN = "..."`
instead of `export`. On Command Prompt (cmd.exe), use `set DATABRICKS_HOST=...` (no `export`,
no quotes).

Opens at `http://localhost:8501`. The model is loaded once (cached) on first load, pulled
directly from Unity Catalog via `mlflow.sklearn.load_model` - no Databricks Model Serving
endpoint needed, since the model is small enough to load client-side. It always resolves the
*latest* registered version automatically (no hardcoded version number), so retraining and
re-registering a new model is picked up without editing this file.

## What it does

Queries `clickstream.ml_feature.ml_feature_visitor_item` for (visitor, item) interactions that
were viewed or added to cart but never bought, pre-filtered in SQL to the top 20,000 by
add-to-cart/view activity (the full unconverted pool is 2.1M+ rows at current data scale -
scoring all of it client-side would be far too slow for an interactive app), scores every one
with the model, and displays **all** of them in one table, sorted highest-probability first:
Name, View Count, Add-to-Cart Count, Days Since Last Interaction, Previously Purchased Item
Count, Item Name (item ID - this dataset has no real product names), Probability, and Meaning
(a plain-language bucket - "Higher purchase tendency" / "Medium" / "Lower" / "Very low" - based
on quartile rank, kept as an internal ranking helper even though the underlying percentile
column isn't shown).

**Probability is genuinely calibrated** (see "Model history" below) - a shown value is meant
to match the real-world observed conversion rate at that score, not just rank candidates
relative to each other the way earlier model versions' raw output did.

Four features feed the model: `view_count`, `addtocart_count`, `days_since_last_interaction`,
`item_is_available`. `item_category_id` is deliberately excluded - it's a nominal ID with no
real ordering, and feeding it in as a raw number caused early model versions to learn nonsense
(see `databricks/notebooks/train_purchase_propensity.py` for the full story). `transaction_count`
is never a feature either, since that's what the model predicts.

## Model history (why version 7)

The model went through several real iterations, not just one training run:

- **v1-v2**: `class_weight='balanced'` on ~20 training positives saturated the model's output
  near 100% for almost any input - a calibration bug caught by manually testing the app.
- **v3**: added a stress test (hand-built "clearly disengaged" vs "clearly engaged" examples),
  which caught that every candidate failed it - Random Forest's direction was fully inverted.
  Traced to `item_category_id` being fed in as a raw number; removed it as a feature.
- **v4**: same fix, still failed the stress test - the real problem was data volume, not feature
  engineering. Only 20 real purchases isn't enough to calibrate any model reliably.
- **v5**: re-ran the ingestion producer against the *full* `events.csv` (2,756,101 rows, all
  22,457 real transactions) instead of the original 5,000-row demo sample.
  `ml_training_purchase_propensity` went from ~4.6k rows / ~20 positives to **2,144,652 rows /
  20,743 positives**. Every candidate now passes both checks with the correct direction.
  PR-AUC: 0.07 -> **0.39**. ROC-AUC: 0.75 -> **0.97**. `random_forest_depth6` won this round.
- **v6**: widened the comparison from 2 algorithm families (Logistic Regression,
  Random Forest) to 6 - added **Extra Trees**, **XGBoost**, **LightGBM**, and **Naive Bayes**,
  10 candidates total. All 10 now pass both checks at this data volume. Full comparison,
  sorted by PR-AUC:

  | Candidate | PR-AUC | ROC-AUC |
  |---|---|---|
  | **lightgbm_depth6 (winner)** | **0.3916** | 0.9726 |
  | xgboost_depth6 | 0.3893 | 0.9720 |
  | random_forest_depth6 | 0.3890 | 0.9741 |
  | random_forest_depth3 | 0.3657 | 0.9724 |
  | logistic_regression (C=0.1/1.0) | 0.3421 | 0.9699 |
  | logistic_regression (C=0.01) | 0.3416 | 0.9717 |
  | logistic_regression (C=0.001) | 0.3414 | 0.9717 |
  | extra_trees_depth6 | 0.3240 | 0.9702 |
  | naive_bayes | 0.2825 | 0.9685 |

  A genuine three-way near-tie at the top (LightGBM/XGBoost/Random Forest within 0.003 of each
  other) - gradient-boosted trees edged out plain Random Forest, as expected for tabular data,
  but not by a dramatic margin. Naive Bayes and plain Logistic Regression trail, also as
  expected given they can't model feature interactions the way tree-based methods can.

**Local environment note**: loading a LightGBM- or XGBoost-based model outside Databricks
(e.g. running this app locally) requires the `lightgbm`/`xgboost` packages installed locally
too, pinned to match the Databricks ML runtime's versions (`lightgbm==4.5.0`,
`xgboost==2.0.3`) - already in `requirements.txt`. Without them, `mlflow.sklearn.load_model`
fails with `ModuleNotFoundError` while unpickling, since the model object itself is an
`LGBMClassifier`/`XGBClassifier` instance, not a generic sklearn model.

- **v7 (current) - real probability calibration**: the winning `lightgbm_depth6`'s raw
  `predict_proba` - like every version before it - was not an honest probability.
  `class_weight='balanced'` systematically inflates it: an independent check showed rows scored
  90-100% only converted ~31% of the time in reality. Wrapped the winner in
  `CalibratedClassifierCV` (isotonic regression, 5-fold, rebuilding the model architecture from
  scratch rather than reusing the already-fitted instance, to avoid leaking the test set into
  calibration). The fix worked - verified with the same bucket-check methodology that caught
  the problem:

  | Predicted score | Actual observed rate |
  |---|---|
  | 0-10% | 0.09% |
  | 30-40% | 35.5% |
  | 40-50% | 42.4% |
  | 60-70% | 65.6% |

  Predicted and actual now track closely across every band. The maximum probability the
  calibrated model produces across the **entire real 20,000-row candidate pool** is **84%** -
  it no longer claims 99% for anything, because that was never a true reflection of the data.
  PR-AUC after calibration: 0.395 (calibration is a monotonic transform, so it didn't cost any
  ranking quality - if anything the 5-fold refit improved it slightly over the single-fit
  original).

This is genuinely a much better, more honest model than the original, not just a bigger
number - verified independently at every step: loading it fresh and checking sensible varied
predictions, and a real calibration check on data the calibration step never saw.
