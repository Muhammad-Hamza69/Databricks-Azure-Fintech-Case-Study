
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select property
from `clickstream`.`silver`.`silver_item_properties_history`
where property is null



  
  
      
    ) dbt_internal_test