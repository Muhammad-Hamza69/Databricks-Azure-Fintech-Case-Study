

-- Stable contract for the Fivetran reverse-ETL sync into Salesforce. Syncs onto the standard
-- Account object (not a custom object) - the target org's Starter edition caps custom objects
-- very low, already consumed by the platform's own Knowledge_kav object, so this adds custom
-- *fields* to Account instead, which doesn't count against that limit.
-- account_name feeds Account's required standard Name field. visitor_id is the upsert/match key
-- (mapped to the Visitor_Id__c external ID field in Salesforce).
select
    visitor_id,
    'Visitor ' || cast(visitor_id as string) as account_name,
    total_views,
    total_addtocarts,
    total_transactions,
    distinct_items_viewed,
    first_seen,
    last_seen,
    is_converted
from `clickstream`.`gold`.`gold_visitor_summary`