
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select visitor_item_key
from `clickstream`.`ml_feature`.`ml_feature_visitor_item`
where visitor_item_key is null



  
  
      
    ) dbt_internal_test