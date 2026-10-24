with stg_sales as (

    select *
    from {{ ref('stg_sales') }}
),

dim_employees as (

    select *
    from {{ ref('dim_employees') }}
),

sales_line_counts as (

    select
        sales_id,
        count(*) as sales_line_count
    from {{ ref('fct_sales') }}
    group by sales_id
)

select
    s.sales_id as transaction_key,
    s.sales_id,
    s.sold_date,
    s.sold_at,
    s.sold_weekday,
    s.employee_id,
    e.full_name as employee_name,
    s.payment_type,
    s.sale_total_price as revenue,
    s.sale_total_discount as total_discount,
    coalesce(line_stats.sales_line_count, 0) as sales_line_count,
    coalesce(line_stats.sales_line_count, 0) > 0 as has_line_items
from stg_sales as s
left join dim_employees as e
    on s.employee_id = e.employee_id
left join sales_line_counts as line_stats
    on s.sales_id = line_stats.sales_id
