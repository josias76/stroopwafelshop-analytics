with stg_products as (

    select *
    from {{ ref('stg_products') }}
)

select
    product_id,
    product_name,
    unit_cost,
    unit_price,
    round(unit_price - unit_cost, 3) as gross_margin_per_unit
from stg_products
