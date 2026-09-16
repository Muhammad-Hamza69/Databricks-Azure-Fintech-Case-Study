
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select item_id
from `clickstream`.`silver`.`silver_item_properties_history`
where item_id is null



  
  
      
    ) dbt_internal_test