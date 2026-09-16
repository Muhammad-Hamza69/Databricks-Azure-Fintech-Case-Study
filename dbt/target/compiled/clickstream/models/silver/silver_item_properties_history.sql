

with staged as (
    select * from `clickstream`.`staging`.`item_properties`
),

valid as (
    select *
    from staged
    where item_id is not null
      and property is not null
      and event_ts is not null
),

deduped as (
    -- collapse exact re-deliveries of the same (item, property, value) change record
    select
        *,
        row_number() over (
            partition by item_id, property, event_ts, value
            order by ingested_at desc
        ) as rn
    from valid
)

select
    item_id,
    property,
    value,
    event_ts,
    ingested_at
from deduped
where rn = 1