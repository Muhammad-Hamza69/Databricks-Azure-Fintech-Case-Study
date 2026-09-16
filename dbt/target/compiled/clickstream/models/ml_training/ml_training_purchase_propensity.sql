

-- Labeled training set for "will this visitor purchase this item": every (visitor, item)
-- pair with at least a view or add-to-cart is a training row, label = whether it converted
-- to a transaction. transaction_count itself is intentionally left out of the feature set
-- above and only read here to derive the label.
select
    visitor_id,
    item_id,
    view_count,
    addtocart_count,
    days_since_last_interaction,
    item_category_id,
    item_is_available,
    case when transaction_count > 0 then 1 else 0 end as label_purchased
from `clickstream`.`ml_feature`.`ml_feature_visitor_item`
where view_count > 0 or addtocart_count > 0