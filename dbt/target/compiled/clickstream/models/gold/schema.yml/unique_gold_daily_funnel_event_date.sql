
    
    

select
    event_date as unique_field,
    count(*) as n_records

from `clickstream`.`gold`.`gold_daily_funnel`
where event_date is not null
group by event_date
having count(*) > 1


