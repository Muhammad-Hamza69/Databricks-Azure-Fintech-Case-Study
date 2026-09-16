
    
    

with all_values as (

    select
        event as value_field,
        count(*) as n_records

    from `clickstream`.`silver`.`silver_events`
    group by event

)

select *
from all_values
where value_field not in (
    'view','addtocart','transaction'
)


