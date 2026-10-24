select
    cast(id as integer) as product_id,
    trim(product_name) as product_name,
    cast(unit_cost as numeric(10, 3)) as unit_cost,
    cast(unit_price as numeric(10, 2)) as unit_price
from {{ source('raw', 'products') }}