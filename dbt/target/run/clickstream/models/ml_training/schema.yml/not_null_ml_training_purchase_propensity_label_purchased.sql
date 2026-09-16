
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select label_purchased
from `clickstream`.`ml_training`.`ml_training_purchase_propensity`
where label_purchased is null



  
  
      
    ) dbt_internal_test