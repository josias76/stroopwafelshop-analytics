with stg_promotions as (

    select *
    from {{ ref('stg_promotions') }}
)

select
    promotion_id,
    product_id,
    promotion_name,
    description,
    promotion_start_date,
    promotion_end_date,
    discount_rate,
    is_holiday,
    (promotion_end_date - promotion_start_date) + 1 as promotion_duration_days
from stg_promotions
