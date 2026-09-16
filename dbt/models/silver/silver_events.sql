{{ config(materialized='table') }}

with staged as (
    select * from {{ source('staging', 'events') }}
),

valid as (
    -- drop rows that fail basic referential/quality checks before they reach silver
    select *
    from staged
    where visitor_id is not null
      and item_id is not null
      and event_ts is not null
      and event in ('view', 'addtocart', 'transaction')
),

deduped as (
    -- Event Hub / Auto Loader give at-least-once delivery; collapse exact re-deliveries
    -- of the same business event, keeping the most recently ingested copy
    select
        *,
        row_number() over (
            partition by visitor_id, item_id, event, event_ts, transaction_id
            order by ingested_at desc
        ) as rn
    from valid
)

select
    visitor_id,
    item_id,
    event,
    event_ts,
    cast(event_ts as date)                                as event_date,
    transaction_id,
    event = 'transaction' and transaction_id is not null   as is_purchase,
    ingested_at
from deduped
where rn = 1
