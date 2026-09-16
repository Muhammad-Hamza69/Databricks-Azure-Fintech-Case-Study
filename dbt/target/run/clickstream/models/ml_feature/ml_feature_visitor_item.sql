
  
    
        create or replace table `clickstream`.`ml_feature`.`ml_feature_visitor_item`
      
      
    using delta
  
      
      
      
      
      
      
      
      
      as
      -- (visitor_id, item_id) grain feature table for a purchase-propensity model. Deliberately
-- excludes transaction_count from the exposed features (see ml_training) - it's only used
-- there to derive the label, never as a feature, to avoid leakage.
with interactions as (
    select
        visitor_id,
        item_id,
        count(*) filter (where event = 'view')          as view_count,
        count(*) filter (where event = 'addtocart')      as addtocart_count,
        count(*) filter (where event = 'transaction')    as transaction_count,
        min(event_ts)                                    as first_interaction_ts,
        max(event_ts)                                    as last_interaction_ts
    from `clickstream`.`silver`.`silver_events`
    group by visitor_id, item_id
),

dataset_max_ts as (
    select max(event_ts) as max_ts from `clickstream`.`silver`.`silver_events`
),

attrs as (
    select * from `clickstream`.`silver`.`int_item_attributes`
)

select
    concat(cast(i.visitor_id as string), '-', cast(i.item_id as string)) as visitor_item_key,
    i.visitor_id,
    i.item_id,
    i.view_count,
    i.addtocart_count,
    i.transaction_count,
    i.first_interaction_ts,
    i.last_interaction_ts,
    datediff(m.max_ts, i.last_interaction_ts) as days_since_last_interaction,
    a.category_id                             as item_category_id,
    a.is_available                            as item_is_available
from interactions i
cross join dataset_max_ts m
left join attrs a on a.item_id = i.item_id
  