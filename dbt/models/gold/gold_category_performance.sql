{{ config(materialized='table') }}

-- rolled up at the item's directly-tagged category (one level, not full ancestry)
with item_perf as (
    select * from {{ ref('gold_item_performance') }}
),

categories as (
    select * from {{ ref('silver_category_tree') }}
)

select
    c.category_id,
    c.parent_category_id,
    count(distinct ip.item_id)                                    as item_count,
    coalesce(sum(ip.views), 0)                                    as views,
    coalesce(sum(ip.addtocarts), 0)                                as addtocarts,
    coalesce(sum(ip.transactions), 0)                              as transactions,
    round(sum(ip.transactions) / nullif(sum(ip.views), 0), 4)     as conversion_rate
from categories c
left join item_perf ip on ip.category_id = c.category_id
group by c.category_id, c.parent_category_id
