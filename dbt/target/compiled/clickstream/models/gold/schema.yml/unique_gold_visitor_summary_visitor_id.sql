
    
    

select
    visitor_id as unique_field,
    count(*) as n_records

from `clickstream`.`gold`.`gold_visitor_summary`
where visitor_id is not null
group by visitor_id
having count(*) > 1


