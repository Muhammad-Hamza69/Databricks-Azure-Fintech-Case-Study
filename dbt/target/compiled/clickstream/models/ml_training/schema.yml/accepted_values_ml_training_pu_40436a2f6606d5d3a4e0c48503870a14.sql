
    
    

with all_values as (

    select
        label_purchased as value_field,
        count(*) as n_records

    from `clickstream`.`ml_training`.`ml_training_purchase_propensity`
    group by label_purchased

)

select *
from all_values
where value_field not in (
    '0','1'
)


