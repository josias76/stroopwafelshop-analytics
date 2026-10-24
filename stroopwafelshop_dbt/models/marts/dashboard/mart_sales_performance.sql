with mart_sales_detail as (

    select *
    from {{ ref('mart_sales_detail') }}
)

select
    md5(
        concat_ws(
            '|',
            sold_date::text,
            employee_id::text,
            product_id::text,
            coalesce(promotion_id::text, 'no_promotion'),
            payment_type
        )
    ) as sales_performance_key,
    sold_date,
    sold_weekday,
    employee_id,
    employee_name,
    product_id,
    product_name,
    promotion_id,
    promotion_name,
    promotion_bucket,
    payment_type,
    sum(quantity_sold) as quantity_sold,
    sum(revenue) as revenue,
    sum(total_discount) as total_discount,
    sum(gross_profit) as gross_profit,
    count(*) as sales_line_count
from mart_sales_detail
group by
    sold_date,
    sold_weekday,
    employee_id,
    employee_name,
    product_id,
    product_name,
    promotion_id,
    promotion_name,
    promotion_bucket,
    payment_type
