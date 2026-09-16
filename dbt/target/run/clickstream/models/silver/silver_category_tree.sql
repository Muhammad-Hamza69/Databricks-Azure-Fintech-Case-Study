
  
    
        create or replace table `clickstream`.`silver`.`silver_category_tree`
      
      
    using delta
  
      
      
      
      
      
      
      
      
      as
      with staged as (
    select * from `clickstream`.`staging`.`category_tree`
),

valid as (
    select *
    from staged
    where category_id is not null
      and (parent_category_id is null or parent_category_id != category_id)
),

deduped as (
    select
        *,
        row_number() over (partition by category_id order by ingested_at desc) as rn
    from valid
)

select
    category_id,
    parent_category_id,
    ingested_at
from deduped
where rn = 1
  