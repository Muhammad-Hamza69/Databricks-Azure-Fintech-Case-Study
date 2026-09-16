

-- current-value snapshot per (item, property), derived from the deduped history table
with ranked as (
    select
        *,
        row_number() over (
            partition by item_id, property
            order by event_ts desc, ingested_at desc
        ) as rn
    from `clickstream`.`silver`.`silver_item_properties_history`
)

select
    item_id,
    property,
    value,
    event_ts as as_of
from ranked
where rn = 1