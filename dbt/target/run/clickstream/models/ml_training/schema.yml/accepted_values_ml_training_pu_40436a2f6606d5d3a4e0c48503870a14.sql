
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

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



  
  
      
    ) dbt_internal_test