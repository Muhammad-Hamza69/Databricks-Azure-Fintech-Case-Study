
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    visitor_item_key as unique_field,
    count(*) as n_records

from `clickstream`.`ml_feature`.`ml_feature_visitor_item`
where visitor_item_key is not null
group by visitor_item_key
having count(*) > 1



  
  
      
    ) dbt_internal_test