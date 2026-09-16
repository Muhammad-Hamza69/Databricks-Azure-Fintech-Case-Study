
    
    

select
    category_id as unique_field,
    count(*) as n_records

from `clickstream`.`gold`.`gold_category_performance`
where category_id is not null
group by category_id
having count(*) > 1


