

with events as (
    select
        item_id,
        count(*) filter (where event = 'view')          as views,
        count(*) filter (where event = 'addtocart')      as addtocarts,
        count(*) filter (where event = 'transaction')    as transactions,
        count(distinct visitor_id)                       as unique_visitors,
        min(event_ts)                                    as first_seen,
        max(event_ts)                                    as last_seen
    from `clickstream`.`silver`.`silver_events`
    group by item_id
),

attrs as (
    select * from `clickstream`.`silver`.`int_item_attributes`
)

select
    e.item_id,
    a.category_id,
    a.is_available,
    e.views,
    e.addtocarts,
    e.transactions,
    e.unique_visitors,
    round(e.transactions / nullif(e.views, 0), 4) as conversion_rate,
    e.first_seen,
    e.last_seen
from events e
left join attrs a on a.item_id = e.item_id