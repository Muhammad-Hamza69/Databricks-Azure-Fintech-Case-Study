
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select visitor_id
from `clickstream`.`gold`.`gold_visitor_summary`
where visitor_id is null



  
  
      
    ) dbt_internal_test