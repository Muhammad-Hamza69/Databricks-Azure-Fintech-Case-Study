

select
    event_date,
    count(*) filter (where event = 'view')            as views,
    count(*) filter (where event = 'addtocart')        as addtocarts,
    count(*) filter (where event = 'transaction')      as transactions,
    count(distinct visitor_id)                         as unique_visitors,
    round(
        count(*) filter (where event = 'transaction') / nullif(count(*) filter (where event = 'view'), 0),
        4
    ) as view_to_purchase_rate
from `clickstream`.`silver`.`silver_events`
group by event_date