
  
    
        create or replace table `clickstream`.`gold`.`gold_visitor_summary`
      
      
    using delta
  
      
      
      
      
      
      
      
      
      as
      select
    visitor_id,
    count(*) filter (where event = 'view')             as total_views,
    count(*) filter (where event = 'addtocart')          as total_addtocarts,
    count(*) filter (where event = 'transaction')        as total_transactions,
    count(distinct item_id)                              as distinct_items_viewed,
    min(event_ts)                                        as first_seen,
    max(event_ts)                                        as last_seen,
    count(*) filter (where event = 'transaction') > 0    as is_converted
from `clickstream`.`silver`.`silver_events`
group by visitor_id
  