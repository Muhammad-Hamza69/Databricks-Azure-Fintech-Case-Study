import os

import mlflow
import pandas as pd
import streamlit as st
from databricks import sql
from mlflow.tracking import MlflowClient

MODEL_NAME = "clickstream.ml_models.purchase_propensity"
WAREHOUSE_HTTP_PATH = "/sql/1.0/warehouses/3ae0ca482ea10df2"
# item_category_id deliberately excluded from the model's features - it's a nominal ID with no
# meaningful numeric ordering, and there's nowhere near enough training data (20 positives) to
# properly one-hot encode it. Feeding it in as a raw number caused Random Forest's stress test
# to invert direction entirely (see databricks/notebooks/train_purchase_propensity.py).
FEATURE_COLS = ["view_count", "addtocart_count", "days_since_last_interaction", "item_is_available"]

st.set_page_config(page_title="Purchase Propensity", page_icon="🛒")


def _require_credentials():
    if "DATABRICKS_HOST" not in os.environ or "DATABRICKS_TOKEN" not in os.environ:
        st.error(
            "Set DATABRICKS_HOST and DATABRICKS_TOKEN environment variables before "
            "running this app (a Databricks PAT - see streamlit_app/README.md)."
        )
        st.stop()


@st.cache_resource(show_spinner="Loading model from Unity Catalog...")
def load_model():
    _require_credentials()
    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")
    # always resolve the latest registered version rather than hardcoding one, so a
    # retrained/re-registered model is picked up without editing this file
    client = MlflowClient()
    latest_version = max(
        int(v.version) for v in client.search_model_versions(f"name='{MODEL_NAME}'")
    )
    model_uri = f"models:/{MODEL_NAME}/{latest_version}"
    return mlflow.sklearn.load_model(model_uri), latest_version


def prep_features(df: pd.DataFrame) -> pd.DataFrame:
    """Match the model's logged input schema exactly (int32 recency)."""
    X = df[FEATURE_COLS].copy()
    X["item_is_available"] = X["item_is_available"].apply(lambda v: 1 if v else 0)
    X["days_since_last_interaction"] = (
        X["days_since_last_interaction"].fillna(0).astype("int32")
    )
    return X


CANDIDATE_POOL_SIZE = 20_000  # ml_feature_visitor_item has 2.1M+ unconverted rows at full
# data scale - pulling all of them into the app and scoring every one would be far too slow
# for an interactive UI. Pre-filter in SQL on the features that actually drive the score
# (addtocart_count is the dominant signal - see train_purchase_propensity.py) so the app stays
# fast without dropping the candidates that would realistically rank highest anyway.


@st.cache_data(ttl=300, show_spinner="Querying clickstream.ml_feature...")
def load_non_purchasers() -> pd.DataFrame:
    _require_credentials()
    query = f"""
        with visitor_purchase_history as (
            select visitor_id, count(distinct item_id) as previously_purchased_item_count
            from clickstream.ml_feature.ml_feature_visitor_item
            where transaction_count > 0
            group by visitor_id
        )
        select
            f.visitor_id,
            concat('Visitor ', cast(f.visitor_id as string)) as name,
            f.view_count,
            f.addtocart_count,
            f.days_since_last_interaction,
            coalesce(h.previously_purchased_item_count, 0) as previously_purchased_item_count,
            f.item_id,
            f.item_is_available
        from clickstream.ml_feature.ml_feature_visitor_item f
        left join visitor_purchase_history h on h.visitor_id = f.visitor_id
        where f.transaction_count = 0
        order by f.addtocart_count desc, f.view_count desc
        limit {CANDIDATE_POOL_SIZE}
    """
    with sql.connect(
        server_hostname=os.environ["DATABRICKS_HOST"],
        http_path=WAREHOUSE_HTTP_PATH,
        access_token=os.environ["DATABRICKS_TOKEN"],
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall_arrow().to_pandas()


st.title("🛒 Purchase Propensity")

model, model_version = load_model()
st.caption(f"Using `clickstream.ml_models.purchase_propensity` version **{model_version}**.")

st.subheader("Visitors who haven't purchased (scored)")
st.caption(
    "One row per (visitor, item) interaction where that specific item was viewed or "
    "added to cart but never bought. **Previously purchased item count** is that visitor's "
    "total distinct items bought *historically* (any item) - so a nonzero value here means a "
    "repeat buyer who just hasn't bought *this* item yet. There are no product names in this "
    "dataset (RetailRocket anonymizes items to numeric IDs only), so **item name** shows the "
    "item ID instead."
)

candidates = load_non_purchasers()
scored = candidates.copy()
scored["prediction"] = model.predict_proba(prep_features(scored))[:, 1]
# always keep rows ordered highest probability first
scored = scored.sort_values("prediction", ascending=False).reset_index(drop=True)

# Meaning is still bucketed by quartile rank rather than a fixed probability cutoff, since
# that stays correct regardless of exactly where the calibrated distribution's mass sits -
# it's an internal ranking helper, not a displayed column (see the removed Percentile column).
_quartile = (scored.index + 1) / len(scored)


def meaning_label(q: float) -> str:
    if q <= 0.25:
        return "Higher purchase tendency"
    elif q <= 0.50:
        return "Medium"
    elif q <= 0.75:
        return "Lower"
    return "Very low"


scored["meaning"] = _quartile.map(meaning_label)

scored["item_availability_label"] = scored["item_is_available"].apply(
    lambda v: "Available" if v else ("Unknown" if pd.isna(v) else "Unavailable")
)

display_df = scored[
    [
        "name",
        "view_count",
        "addtocart_count",
        "days_since_last_interaction",
        "previously_purchased_item_count",
        "item_id",
        "item_availability_label",
        "prediction",
        "meaning",
    ]
].rename(
    columns={
        "name": "Name",
        "view_count": "View Count",
        "addtocart_count": "Add-to-Cart Count",
        "days_since_last_interaction": "Days Since Last Interaction",
        "previously_purchased_item_count": "Previously Purchased Item Count",
        "item_id": "Item Name",
        "item_availability_label": "Item Availability",
        "prediction": "Probability",
        "meaning": "Meaning",
    }
)
st.dataframe(
    display_df.style.format({"Probability": "{:.1%}"}),
    use_container_width=True,
    hide_index=True,
)
st.caption(
    f"All {len(candidates):,} scored (visitor, item) interactions shown (pre-filtered in SQL "
    "to the top candidates by add-to-cart/view activity out of 2.1M+ total unconverted "
    "interactions - see the code for why the full 2.1M isn't pulled client-side), sorted "
    "highest probability first, using "
    f"`clickstream.ml_models.purchase_propensity` version {model_version}. This model's "
    "output is **isotonic-calibrated** - unlike earlier versions, a shown probability is meant "
    "to match the real observed conversion rate at that score, not just rank candidates (see "
    "streamlit_app/README.md for the calibration check and the full 10-algorithm comparison)."
)
