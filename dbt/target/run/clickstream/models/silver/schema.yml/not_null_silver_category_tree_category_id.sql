
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select category_id
from `clickstream`.`silver`.`silver_category_tree`
where category_id is null



  
  
      
    ) dbt_internal_test