

-- item_properties is a changelog of arbitrary property codes; only 'categoryid' and
-- 'available' are named (documented) properties in this dataset, everything else is an
-- obfuscated numeric code. Pivot just those two into one row per item.
select
    item_id,
    max(case when property = 'categoryid' then try_cast(value as bigint) end) as category_id,
    max(case when property = 'available' then value end) = '1'                as is_available
from `clickstream`.`silver`.`silver_item_properties_current`
where property in ('categoryid', 'available')
group by item_id