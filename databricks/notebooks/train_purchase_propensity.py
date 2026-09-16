# Databricks notebook source
# MAGIC %md
# MAGIC # ML Training Dataset -> purchase-propensity model
# MAGIC
# MAGIC Trains binary classifiers on `clickstream.ml_training.ml_training_purchase_propensity`:
# MAGIC one row per (visitor, item) interaction, `label_purchased` = whether it converted to a
# MAGIC transaction.
# MAGIC
# MAGIC **v3 fix**: v1 used `class_weight='balanced'` and saturated near 1.0 for almost every
# MAGIC input. v2 tried excluding degenerate candidates by test-set probability std alone, but that
# MAGIC wasn't strict enough - the *registered* v2 model still predicted ~100% for a hand-built
# MAGIC "clearly disengaged" example (0 views, 60 days stale, item unavailable), because
# MAGIC `class_weight='balanced'` on 15 positives still fits large-magnitude coefficients that
# MAGIC saturate the moment an input drifts outside the training distribution - exactly what
# MAGIC happens with manually-entered inputs (e.g. from the Streamlit app), even though metrics on
# MAGIC the specific held-out test split looked fine.
# MAGIC
# MAGIC v3 adds a stress test, and it caught something the v2 fix missed: **every** candidate
# MAGIC failed it, and Random Forest's direction was fully inverted (the "clearly disengaged"
# MAGIC stress row scored *higher* than the "clearly engaged" one: 0.60 vs 0.11). That traced back
# MAGIC to a real feature-engineering bug, not a tuning problem: `item_category_id` is a nominal ID
# MAGIC (1, 442, 1204, ...) with no meaningful ordering, but was fed to the models as a raw number.
# MAGIC Linear models read magnitude as signal ("category 1204 = more x than category 1"); trees
# MAGIC split on arbitrary numeric thresholds over it. With only 15 positives to fit on, both
# MAGIC latched onto that noise instead of the genuinely meaningful features. **v3 drops
# MAGIC `item_category_id` from the model's feature set** - there isn't enough data to properly
# MAGIC encode a several-hundred-value categorical (one-hot would be hopeless at this sample size),
# MAGIC so the honest fix is to not feed it in as if it were ordinal. It stays in `ml_feature`/
# MAGIC `ml_training` for reporting - only the model's input features changed.
# MAGIC
# MAGIC Also keeps v2's fixes: regularization strength (`C`) as a tuned hyperparameter to prevent
# MAGIC sigmoid saturation, and the stress test itself - every candidate is scored on a hand-built
# MAGIC "low engagement" and "high engagement" row, and only accepted if the low-engagement
# MAGIC prediction stays below 50% *and* the gap to high-engagement is at least 30 points.
# MAGIC
# MAGIC **v5 - data-scale caveat resolved**: the producer was re-run against the full
# MAGIC `events.csv` (2,756,101 rows, all 22,457 real transactions) instead of the original
# MAGIC 5,000-row demo sample, giving `ml_training_purchase_propensity` **2,144,652 rows with
# MAGIC 20,743 positives** (up from ~4.6k rows / ~20 positives). The difference is not subtle:
# MAGIC PR-AUC went from 0.07 to **0.39**, ROC-AUC from 0.75 to **0.97**, and every candidate now
# MAGIC passes both the degenerate-spread check and the stress test with the correct direction
# MAGIC (low-engagement scores low, high-engagement scores high) - none of that was true at the
# MAGIC demo-data scale, no matter how the model was tuned. `random_forest_depth6` won this round
# MAGIC (PR-AUC 0.389) and is registered as version 5.
# MAGIC
# MAGIC **v6 - wider algorithm comparison**: v1-v5 only compared Logistic Regression and Random
# MAGIC Forest. v6 adds four more algorithm families - **XGBoost**, **LightGBM**, **Extra Trees**,
# MAGIC and **Naive Bayes** - so the winner is chosen from a genuinely broad comparison (10
# MAGIC candidates total) rather than just two families. Same selection rule as before: PR-AUC
# MAGIC among whichever candidates pass the degenerate-spread check and the stress test.
# MAGIC `lightgbm_depth6` won (PR-AUC 0.392) and was registered as version 6 - but its raw
# MAGIC `predict_proba` output, like every version before it, was **not actually calibrated**: an
# MAGIC independent check (bucket predicted score vs. real observed purchase rate on a fresh
# MAGIC sample) showed rows scored 90-100% only converted ~31% of the time in reality, not
# MAGIC ~97-100%. `class_weight='balanced'` inflates the raw output systematically; it helps
# MAGIC ranking (which is what PR-AUC/ROC-AUC measure) but breaks the *literal* probability meaning.
# MAGIC
# MAGIC **v7 - real probability calibration**: wraps the winning model in
# MAGIC `CalibratedClassifierCV` (isotonic regression, 5-fold) so the number the app displays as
# MAGIC "Probability" is actually trustworthy as a probability - a row calibrated to 30% should
# MAGIC genuinely convert about 30% of the time, verified below with the same bucket-check
# MAGIC methodology used to catch the problem in the first place. This is what actually answers
# MAGIC "how can this be 99.8%?" correctly: after calibration, it mostly can't be, and where a
# MAGIC score is genuinely high, the calibrated number reflects that honestly instead of an
# MAGIC inflated raw model output.

# COMMAND ----------

import mlflow
import mlflow.sklearn
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from xgboost import XGBClassifier

mlflow.set_registry_uri("databricks-uc")
EXPERIMENT_PATH = "/Shared/clickstream/purchase_propensity"
MODEL_NAME = "clickstream.ml_models.purchase_propensity"

mlflow.set_experiment(EXPERIMENT_PATH)

# COMMAND ----------

df = spark.table("clickstream.ml_training.ml_training_purchase_propensity").toPandas()

n_rows = len(df)
n_positive = int(df["label_purchased"].sum())
print(f"Training rows: {n_rows}, positives: {n_positive} ({n_positive / n_rows:.2%})")
if n_positive < 50:
    print(
        f"CAVEAT: only {n_positive} positive examples - this is a demo-scale sample "
        "(producer was run with --max-rows 5000, not the full dataset). Metrics below are "
        "real but have wide confidence intervals; re-ingest the full CSVs for a production-grade "
        "model."
    )

# COMMAND ----------

# item_category_id deliberately excluded - see v3 note above: it's a nominal ID with no
# meaningful numeric ordering, and there's nowhere near enough data (15 positives) to properly
# one-hot encode a several-hundred-value categorical. Feeding it in as a raw number caused
# Random Forest's stress test to invert direction entirely.
feature_cols = [
    "view_count",
    "addtocart_count",
    "days_since_last_interaction",
    "item_is_available",
]
target_col = "label_purchased"


def prep_features(raw: pd.DataFrame) -> pd.DataFrame:
    X = raw[feature_cols].copy()
    X["item_is_available"] = X["item_is_available"].fillna(False).astype(int)
    X["days_since_last_interaction"] = X["days_since_last_interaction"].fillna(0).astype("int32")
    return X


X = prep_features(df)
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)
print(f"Train: {len(X_train)} rows ({y_train.sum()} positive) | Test: {len(X_test)} rows ({y_test.sum()} positive)")

# COMMAND ----------

# Stress test: a human plausibly typing values into a UI (e.g. the Streamlit app) will enter
# inputs that don't necessarily resemble the training distribution's own rows. A model that
# only looks well-calibrated on held-out i.i.d. test rows can still saturate badly here.
STRESS_ROWS = prep_features(pd.DataFrame([
    # clearly disengaged: never viewed more than once, long stale, unavailable item
    {"view_count": 0, "addtocart_count": 0, "days_since_last_interaction": 60,
     "item_is_available": 0},
    # clearly engaged: many views, recent cart-add, available item
    {"view_count": 15, "addtocart_count": 3, "days_since_last_interaction": 0,
     "item_is_available": 1},
]))

MIN_PROBA_STD = 0.02   # test-set probability spread below this = degenerate
MAX_STRESS_LOW = 0.50  # the "clearly disengaged" stress row must predict below this
MIN_STRESS_GAP = 0.30  # and must differ from the "clearly engaged" row by at least this much


def evaluate_and_log(run_name: str, model_factory, X_train, y_train, X_test, y_test, params: dict):
    model = model_factory()
    with mlflow.start_run(run_name=run_name) as run:
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[:, 1]
        preds = model.predict(X_test)

        pr_auc = average_precision_score(y_test, proba)
        roc_auc = roc_auc_score(y_test, proba)
        report = classification_report(y_test, preds, output_dict=True, zero_division=0)
        cm = confusion_matrix(y_test, preds)

        proba_min, proba_max = float(proba.min()), float(proba.max())
        proba_mean, proba_std = float(proba.mean()), float(proba.std())

        stress_proba = model.predict_proba(STRESS_ROWS)[:, 1]
        stress_low, stress_high = float(stress_proba[0]), float(stress_proba[1])
        stress_gap = stress_high - stress_low

        is_degenerate = proba_std < MIN_PROBA_STD
        fails_stress_test = stress_low > MAX_STRESS_LOW or stress_gap < MIN_STRESS_GAP
        is_usable = not is_degenerate and not fails_stress_test

        mlflow.log_params(params)
        mlflow.log_param("features", ",".join(feature_cols))
        mlflow.log_metric("pr_auc", pr_auc)
        mlflow.log_metric("roc_auc", roc_auc)
        mlflow.log_metric("precision_positive", report["1"]["precision"])
        mlflow.log_metric("recall_positive", report["1"]["recall"])
        mlflow.log_metric("f1_positive", report["1"]["f1-score"])
        mlflow.log_metric("train_rows", len(X_train))
        mlflow.log_metric("train_positives", int(y_train.sum()))
        mlflow.log_metric("proba_min", proba_min)
        mlflow.log_metric("proba_max", proba_max)
        mlflow.log_metric("proba_mean", proba_mean)
        mlflow.log_metric("proba_std", proba_std)
        mlflow.log_metric("stress_low_engagement_proba", stress_low)
        mlflow.log_metric("stress_high_engagement_proba", stress_high)
        mlflow.log_metric("stress_gap", stress_gap)

        mlflow.sklearn.log_model(model, artifact_path="model", input_example=X_train.head(5))

        print(f"[{run_name}] PR-AUC={pr_auc:.4f}  ROC-AUC={roc_auc:.4f}")
        print(
            f"[{run_name}] test-set probability spread: min={proba_min:.4f} "
            f"max={proba_max:.4f} mean={proba_mean:.4f} std={proba_std:.4f}"
        )
        print(
            f"[{run_name}] stress test: low-engagement={stress_low:.4f} "
            f"high-engagement={stress_high:.4f} gap={stress_gap:.4f}"
            f"{'  <-- FAILS STRESS TEST' if fails_stress_test else ''}"
            f"{'  <-- DEGENERATE TEST-SET SPREAD' if is_degenerate else ''}"
        )
        print(f"[{run_name}] confusion matrix (rows=actual, cols=predicted):\n{cm}")

        return {
            "run_id": run.info.run_id,
            "name": run_name,
            "pr_auc": pr_auc,
            "proba_std": proba_std,
            "stress_gap": stress_gap,
            "is_usable": is_usable,
        }


# COMMAND ----------

SCALE_POS_WEIGHT = (y_train == 0).sum() / (y_train == 1).sum()

# name -> (factory that builds a *fresh, unfitted* instance, logged params). A factory (not a
# pre-built instance) is needed because the winning model gets rebuilt and recalibrated after
# selection - reusing an already-fitted instance would leak the test set into calibration.
MODEL_FACTORIES = {
    "logistic_regression_C1.0": (
        lambda: LogisticRegression(class_weight="balanced", C=1.0, max_iter=1000, random_state=42),
        {"model_type": "LogisticRegression", "class_weight": "balanced", "C": 1.0},
    ),
    "logistic_regression_C0.1": (
        lambda: LogisticRegression(class_weight="balanced", C=0.1, max_iter=1000, random_state=42),
        {"model_type": "LogisticRegression", "class_weight": "balanced", "C": 0.1},
    ),
    "logistic_regression_C0.01": (
        lambda: LogisticRegression(class_weight="balanced", C=0.01, max_iter=1000, random_state=42),
        {"model_type": "LogisticRegression", "class_weight": "balanced", "C": 0.01},
    ),
    "logistic_regression_C0.001": (
        lambda: LogisticRegression(class_weight="balanced", C=0.001, max_iter=1000, random_state=42),
        {"model_type": "LogisticRegression", "class_weight": "balanced", "C": 0.001},
    ),
    "random_forest_depth6": (
        lambda: RandomForestClassifier(n_estimators=200, max_depth=6, class_weight="balanced", random_state=42),
        {"model_type": "RandomForestClassifier", "n_estimators": 200, "max_depth": 6, "class_weight": "balanced"},
    ),
    "random_forest_depth3": (
        lambda: RandomForestClassifier(n_estimators=200, max_depth=3, class_weight="balanced", random_state=42),
        {"model_type": "RandomForestClassifier", "n_estimators": 200, "max_depth": 3, "class_weight": "balanced"},
    ),
    "extra_trees_depth6": (
        lambda: ExtraTreesClassifier(n_estimators=200, max_depth=6, class_weight="balanced", random_state=42),
        {"model_type": "ExtraTreesClassifier", "n_estimators": 200, "max_depth": 6, "class_weight": "balanced"},
    ),
    "xgboost_depth6": (
        lambda: XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            scale_pos_weight=SCALE_POS_WEIGHT, eval_metric="logloss", random_state=42,
        ),
        {"model_type": "XGBClassifier", "n_estimators": 200, "max_depth": 6, "learning_rate": 0.1, "scale_pos_weight": "balanced"},
    ),
    "lightgbm_depth6": (
        lambda: LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            class_weight="balanced", random_state=42, verbose=-1,
        ),
        {"model_type": "LGBMClassifier", "n_estimators": 200, "max_depth": 6, "learning_rate": 0.1, "class_weight": "balanced"},
    ),
    "naive_bayes": (lambda: GaussianNB(), {"model_type": "GaussianNB"}),
}

candidates = [
    evaluate_and_log(name, factory, X_train, y_train, X_test, y_test, params=params)
    for name, (factory, params) in MODEL_FACTORIES.items()
]

# COMMAND ----------

# MAGIC %md ## Comparison summary - all 10 candidates, sorted by PR-AUC

# COMMAND ----------

summary = (
    pd.DataFrame(candidates)
    .sort_values("pr_auc", ascending=False)
    .reset_index(drop=True)
)
print(summary[["name", "pr_auc", "proba_std", "stress_gap", "is_usable"]].to_string(index=False))

# COMMAND ----------

usable = [c for c in candidates if c["is_usable"]]

if not usable:
    print(
        "WARNING: no candidate passed both the degenerate-spread check and the stress test - "
        "falling back to the best PR-AUC among all candidates anyway, but its probabilities "
        "should not be trusted for individual predictions, only for coarse ranking."
    )
    pool = candidates
else:
    pool = usable

best = max(pool, key=lambda c: c["pr_auc"])
print(
    f"Best model by PR-AUC: {best['name']} "
    f"(PR-AUC={best['pr_auc']:.4f}, proba_std={best['proba_std']:.4f}, "
    f"stress_gap={best['stress_gap']:.4f}) -> calibrating before registering"
)

# COMMAND ----------

# MAGIC %md ## Calibrate the winner
# MAGIC
# MAGIC The raw model's `predict_proba` is not a real probability - `class_weight='balanced'`
# MAGIC systematically inflates it (verified: rows scored 90-100% only convert ~31% of the time in
# MAGIC reality). `CalibratedClassifierCV` (isotonic regression, 5-fold) rebuilds the winning
# MAGIC model's architecture from scratch and learns a correction mapping from raw score to true
# MAGIC observed frequency, so the number registered and served is an actual probability.

# COMMAND ----------

from sklearn.calibration import CalibratedClassifierCV

winning_factory, winning_params = MODEL_FACTORIES[best["name"]]

with mlflow.start_run(run_name=f"{best['name']}_calibrated") as run:
    calibrated_model = CalibratedClassifierCV(
        estimator=winning_factory(), method="isotonic", cv=5
    )
    calibrated_model.fit(X_train, y_train)

    proba = calibrated_model.predict_proba(X_test)[:, 1]
    preds = calibrated_model.predict(X_test)
    pr_auc = average_precision_score(y_test, proba)
    roc_auc = roc_auc_score(y_test, proba)

    # the real check: does a calibrated score actually match the observed rate at that score?
    calib_df = pd.DataFrame({"proba": proba, "actual": y_test.values})
    calib_df["bucket"] = pd.cut(
        calib_df["proba"], bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        include_lowest=True,
    )
    calib_table = calib_df.groupby("bucket", observed=True).agg(
        n=("actual", "size"), predicted_avg=("proba", "mean"), actual_rate=("actual", "mean")
    ).reset_index()

    mlflow.log_params({**winning_params, "calibration": "isotonic_cv5", "base_model": best["name"]})
    mlflow.log_param("features", ",".join(feature_cols))
    mlflow.log_metric("pr_auc", pr_auc)
    mlflow.log_metric("roc_auc", roc_auc)
    mlflow.sklearn.log_model(calibrated_model, artifact_path="model", input_example=X_train.head(5))

    print(f"Calibrated {best['name']}: PR-AUC={pr_auc:.4f}  ROC-AUC={roc_auc:.4f}")
    print("Calibration check (predicted score bucket vs. actual observed rate - should now be close):")
    print(calib_table.to_string(index=False))

model_uri = f"runs:/{run.info.run_id}/model"
registered = mlflow.register_model(model_uri, MODEL_NAME)
print(f"Registered {MODEL_NAME} version {registered.version} from run {run.info.run_id} (calibrated {best['name']})")
